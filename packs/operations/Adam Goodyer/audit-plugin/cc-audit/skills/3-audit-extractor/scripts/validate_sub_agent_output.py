#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""
validate_sub_agent_output.py — Source Attribution Gate (pre-merge, v1).

Validates a sub-agent's extraction JSON BEFORE merge. Refuses any item lacking
a valid sources[] array. Called by merge-extraction.md Step 1.

Every emitted item in:
  new_steps, new_pain_points, new_waste_items, new_optimisations,
  new_tools (action=create only), staff_updates (action=create only),
  new_decision_nodes, new_business_metrics, new_contradictions

MUST carry a sources[] array with at least one entry. Each entry MUST satisfy:
  - kind: "fathom" | "document"
  - quote: non-empty string (verbatim)
  - speaker: non-empty string (null allowed only when kind == "document")
  - confidence: HIGH | MEDIUM | LOW
  - kind == "fathom": session_id (int), timestamp_seconds (int|float)
  - kind == "document": document_path (non-empty string)

Items that cannot be attributed must be retracted into new_follow_up_questions[]
with category: "client_required".

Usage:
  python3 validate_sub_agent_output.py --extraction-json path/to/output.json \\
      --source-type fathom_meeting|email|pdf|document|loom_transcript|other \\
      [--source-path clients/{slug}/...] \\
      [--session-number {n_or_null}]

Exit codes:
  0 — pass (every item has valid sources[])
  1 — gate failure (at least one item violates the invariant)
  2 — file / argument error
"""

import argparse
import json
import re
import sys
from pathlib import Path


# Each tuple: (array_key, id_key, action_filter_or_None)
# action_filter: if set, only items with that `action` value need full attribution
ITEM_ARRAYS = [
    ("new_steps", "step_id", None),
    ("new_pain_points", "pain_point_id", None),
    ("new_waste_items", "waste_id", None),
    ("new_optimisations", "optimisation_id", None),
    ("new_decision_nodes", "node_id", None),
    ("new_business_metrics", "metric_id", None),
    ("tool_updates", "tool_name", "create"),
    ("staff_updates", "name", "create"),
]

VALID_CONFIDENCE = ("HIGH", "MEDIUM", "LOW")


def _make_failure(array_name: str, idx: int, item: dict, id_key: str,
                  reason: str, missing_fields=None):
    """Build a structured failure report entry."""
    snippet = (
        item.get("description")
        or item.get("title")
        or item.get("activity")
        or item.get("topic")
        or ""
    )
    if isinstance(snippet, str) and len(snippet) > 120:
        snippet = snippet[:117] + "..."
    return {
        "array": array_name,
        "index": idx,
        "item_id": item.get(id_key) or "<no id>",
        "reason": reason,
        "missing_fields": missing_fields or [],
        "snippet": snippet,
    }


def _validate_source_entry(src, kind_hint_from_source_type: str = None) -> list:
    """Return list of missing/invalid fields for a single sources[] entry."""
    if not isinstance(src, dict):
        return ["entry_not_object"]
    missing = []
    kind = src.get("kind")
    if kind not in ("fathom", "document"):
        missing.append("kind")
        return missing  # without a valid kind, the rest is undefined

    quote = src.get("quote")
    if not (isinstance(quote, str) and quote.strip()):
        missing.append("quote")

    confidence = src.get("confidence")
    if confidence not in VALID_CONFIDENCE:
        missing.append("confidence")

    if kind == "fathom":
        if not isinstance(src.get("session_id"), int):
            missing.append("session_id")
        if not isinstance(src.get("timestamp_seconds"), (int, float)):
            missing.append("timestamp_seconds")
        speaker = src.get("speaker")
        if not (isinstance(speaker, str) and speaker.strip()):
            missing.append("speaker")
    elif kind == "document":
        doc = src.get("document_path")
        if not (isinstance(doc, str) and doc.strip()):
            missing.append("document_path")

    return missing


def _validate_item_sources(item: dict, expected_kind: str = None) -> tuple:
    """Return (ok, reason, missing_fields_list)."""
    sources = item.get("sources")
    if not isinstance(sources, list) or len(sources) == 0:
        return (False, "no_sources", ["sources"])
    bad = []
    for si, src in enumerate(sources):
        missing = _validate_source_entry(src)
        if missing:
            bad.append(f"sources[{si}]:{','.join(missing)}")
    if bad:
        return (False, "invalid_source_entries", bad)
    # Optional: enforce form-matching against source_type
    if expected_kind in ("fathom", "document"):
        # At least one source should match expected_kind (multi-source items
        # can corroborate with the other kind — only require one match).
        kinds = {s.get("kind") for s in sources}
        if expected_kind not in kinds:
            return (False, f"wrong_form_expected_{expected_kind}", ["sources[].kind"])
    return (True, "ok", [])


def _expected_kind_for_source_type(source_type: str):
    if source_type == "fathom_meeting":
        return "fathom"
    if source_type in ("email", "pdf", "document", "loom_transcript", "other"):
        return "document"
    return None  # unknown — don't enforce


def validate(payload: dict, source_type: str = None) -> tuple:
    """Validate a sub-agent extraction payload. Returns (items_checked, failures)."""
    expected_kind = _expected_kind_for_source_type(source_type)
    failures = []
    checked = 0

    for array_name, id_key, action_filter in ITEM_ARRAYS:
        items = payload.get(array_name) or []
        if not isinstance(items, list):
            continue
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            if action_filter is not None and item.get("action") != action_filter:
                continue
            checked += 1
            ok, reason, missing = _validate_item_sources(item, expected_kind)
            if not ok:
                failures.append(_make_failure(array_name, i, item, id_key, reason, missing))

    # Contradictions are different: each needs sources[] of length >= 2
    for ci, contradiction in enumerate(payload.get("new_contradictions") or []):
        if not isinstance(contradiction, dict):
            continue
        checked += 1
        sources = contradiction.get("sources")
        if not isinstance(sources, list) or len(sources) < 2:
            failures.append(_make_failure(
                "new_contradictions", ci, contradiction, "contradiction_id",
                "contradiction_needs_two_sources",
                ["sources (need >= 2)"],
            ))
            continue
        bad = []
        for si, src in enumerate(sources):
            missing = _validate_source_entry(src)
            if missing:
                bad.append(f"sources[{si}]:{','.join(missing)}")
        if bad:
            failures.append(_make_failure(
                "new_contradictions", ci, contradiction, "contradiction_id",
                "invalid_source_entries", bad,
            ))

    # BPMN structural checks on new_steps
    _FORBIDDEN_EVENT_TYPES = {"start_event", "end_event", "start", "end"}
    new_steps = payload.get("new_steps") or []
    if isinstance(new_steps, list) and new_steps:
        step_ids_seen: dict[str, int] = {}
        for si, step in enumerate(new_steps):
            if not isinstance(step, dict):
                continue
            sid = step.get("step_id", "")
            if sid:
                step_ids_seen[sid] = step_ids_seen.get(sid, 0) + 1

            et = step.get("element_type") or step.get("type", "")
            if et in _FORBIDDEN_EVENT_TYPES:
                failures.append({
                    "array": "new_steps", "index": si,
                    "item_id": sid or "<no id>",
                    "reason": "forbidden_event_type",
                    "missing_fields": [f"element_type: '{et}' (start/end events are synthetic)"],
                    "snippet": (step.get("description") or step.get("title") or "")[:120],
                })

        for sid, count in step_ids_seen.items():
            if count > 1:
                failures.append({
                    "array": "new_steps", "index": -1,
                    "item_id": sid,
                    "reason": "duplicate_step_id",
                    "missing_fields": [f"step_id '{sid}' appears {count} times"],
                    "snippet": "",
                })

    # IATO presence check
    TASK_ELEMENT_TYPES = {
        "task", "user_task", "service_task", "send_task",
        "receive_task", "manual_task", "business_rule_task"
    }
    iato_warnings = []
    for stage in payload.get("new_stages", []):
        for step in stage.get("steps", []):
            et = step.get("element_type", "")
            if et in TASK_ELEMENT_TYPES:
                iato = step.get("iato")
                if iato is None:
                    iato_warnings.append(
                        f"Step {step.get('step_id', '?')}: iato object missing on task-type step"
                    )
                elif not iato.get("action"):
                    iato_warnings.append(
                        f"Step {step.get('step_id', '?')}: iato.action is required but null"
                    )
    # Also check new_steps[] (steps may be emitted outside new_stages in some extractions)
    for step in payload.get("new_steps", []):
        et = step.get("element_type", "")
        if et in TASK_ELEMENT_TYPES:
            iato = step.get("iato")
            if iato is None:
                iato_warnings.append(
                    f"Step {step.get('step_id', '?')}: iato object missing on task-type step"
                )
            elif not iato.get("action"):
                iato_warnings.append(
                    f"Step {step.get('step_id', '?')}: iato.action is required but null"
                )

    if iato_warnings:
        for w in iato_warnings:
            print(f"[IATO-WARNING] {w}")
        # Warnings only — do not fail the gate for missing IATO in Sprint 1
        # Sprint 2+ will escalate specific fields to errors

    # Gaps register basic structure check
    gaps_register = payload.get("gaps_register", [])
    for i, gap in enumerate(gaps_register):
        if not gap.get("gap_id"):
            print(f"[GAP-WARNING] gaps_register[{i}] missing gap_id")
        if not gap.get("affected_field"):
            print(f"[GAP-WARNING] gaps_register[{i}] missing affected_field")
        gtype = gap.get("gap_type")
        if gtype is not None and gtype not in {"A", "B", "C"}:
            print(f"[ENUM-WARNING] gaps_register[{i}]: gap_type '{gtype}' must be A, B, or C")

    # Enum validation on step fields — warnings only (not gate failures)
    _VALID_GAP_TYPES = {None, "A", "B", "C"}
    _VALID_MECHANISMS = {
        "api_sync", "automated_sync", "manual_export_import",
        "copy_paste", "email_forward", "verbal", "paper", "unknown",
    }
    _RELIABILITY_RE = re.compile(r'^[A-F][1-6]$')

    def _iter_all_new_steps(p: dict):
        for stage in p.get("new_stages", []):
            yield from stage.get("steps", [])
        yield from p.get("new_steps", [])

    for step in _iter_all_new_steps(payload):
        sid = step.get("step_id", "?")
        gaps_obj = step.get("_gaps") or {}
        gtype = gaps_obj.get("gap_type")
        if gtype not in _VALID_GAP_TYPES:
            print(f"[ENUM-WARNING] Step {sid}: _gaps.gap_type '{gtype}' must be A, B, C, or null")
        handoff = step.get("handoff") or {}
        mech = handoff.get("mechanism")
        if mech is not None and mech not in _VALID_MECHANISMS:
            print(f"[ENUM-WARNING] Step {sid}: handoff.mechanism '{mech}' not in valid set")
        for si, src in enumerate(step.get("sources") or []):
            rel = src.get("reliability") if isinstance(src, dict) else None
            if rel is not None and not _RELIABILITY_RE.match(str(rel)):
                print(f"[ENUM-WARNING] Step {sid}: sources[{si}].reliability '{rel}' must match ^[A-F][1-6]$")

    return checked, failures


def main():
    parser = argparse.ArgumentParser(
        description="Source Attribution Gate (pre-merge validator)."
    )
    parser.add_argument("--extraction-json", required=True,
                        help="Path to the sub-agent's returned JSON (or '-' for stdin)")
    parser.add_argument("--source-type",
                        choices=("fathom_meeting", "email", "pdf", "document",
                                 "loom_transcript", "other"),
                        help="Type of the source material being extracted")
    parser.add_argument("--source-path", help="Path of the source (for diagnostic output)")
    parser.add_argument("--session-number", help="Fathom session number (for diagnostic output)")
    args = parser.parse_args()

    try:
        if args.extraction_json == "-":
            payload = json.load(sys.stdin)
        else:
            p = Path(args.extraction_json)
            if not p.exists():
                print(json.dumps({"status": "error", "message": f"File not found: {p}"}))
                sys.exit(2)
            payload = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(2)

    if not isinstance(payload, dict):
        print(json.dumps({"status": "error", "message": "Payload must be a JSON object"}))
        sys.exit(2)

    checked, failures = validate(payload, source_type=args.source_type)

    status = "pass" if not failures else "fail"
    report = {
        "status": status,
        "gate_version": "v1",
        "source_type": args.source_type,
        "source_path": args.source_path,
        "session_number": args.session_number,
        "items_checked": checked,
        "items_failed": len(failures),
        "failures": failures,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if status == "pass" else 1)


if __name__ == "__main__":
    main()
