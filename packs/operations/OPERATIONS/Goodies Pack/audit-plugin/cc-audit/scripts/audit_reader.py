#!/usr/bin/env python3
"""
audit_reader.py — Selective domain loader and format converter for audit-data.json.

Provides three capabilities:
1. Selective loading  — read only the domains an agent needs
2. Predefined profiles — named read sets mapped to deliverables/capabilities
3. Format conversion  — flatten v3 nested structure to v2 flat dict and back

Works with both v2 (flat) and v3 (nested) audit-data.json files.

Usage:
  python3 audit_reader.py <path> --profile <name>
  python3 audit_reader.py <path> --sections meta findings
  python3 audit_reader.py <path> --list-profiles
  python3 audit_reader.py <path> --version
"""

import json
import sys
import argparse
import hashlib
import warnings
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Domain routing tables
# ---------------------------------------------------------------------------

DOMAIN_ROUTING = {
    # extraction domain
    "processes": "extraction",
    "decision_nodes": "extraction",
    "tools": "extraction",
    "staff_roster": "extraction",
    "business_metrics": "extraction",
    "business_metrics_list": "extraction",   # legacy — merge or discard in nest()
    "business_stages_covered": "extraction",
    "sessions": "extraction",
    "extracted_materials": "extraction",
    "client_context": "extraction",
    "constraints": "extraction",             # legacy — nested under client_context
    "strategic_notes": "extraction",         # legacy — nested under client_context

    # findings domain
    "pain_points": "findings",
    "pain_points_summary": "findings",
    "optimisations": "findings",
    "waste_items": "findings",
    "contradictions": "findings",
    "follow_up_questions": "findings",
    "follow_up_summary": "findings",
    "completeness_checklist": "findings",
    "change_readiness": "findings",
    "objections": "findings",
    "positive_signals": "findings",
    "data_gaps": "findings",
    "quick_wins": "findings",                # legacy

    # opportunities domain
    "proposed_changes": "opportunities",
    "roi_items": "opportunities",
    "risk_register": "opportunities",

    # strategy domain
    "strategic_approaches": "strategy",
    "transformation_blueprint": "strategy",

    # architecture domain
    "requirements_spec": "architecture",
    "architecture_doc": "architecture",
    "architecture_verification": "architecture",
    "cowork_demos": "architecture",
    "branding": "architecture",
}

# Root-level keys — not nested in any domain
ROOT_KEYS = {
    "_schema_version",
    "_section_index",
    "analyst_metadata",
    "architect_metadata",
}

# Meta domain keys
META_KEYS = {
    "client_slug",
    "company_name",
    "industry_tag",
    "audit_start_date",
    "audit_status",
    "sessions_completed",
    "google_drive_folder_url",
    "crm",
    "contact",
    "blended_hourly_rate_aud",
    "blended_rate_confidence",
    "blended_rate_source",
}

# Keys to drop entirely during nest()
DROP_KEYS = {"ingestion_manifest"}

# Domain names in merge-priority order (architecture wins over meta on collision)
DOMAIN_ORDER = ["meta", "extraction", "findings", "opportunities", "strategy", "architecture"]

# ---------------------------------------------------------------------------
# Predefined profiles
# ---------------------------------------------------------------------------

PROFILES = {
    # Always load everything
    "full": ["meta", "extraction", "findings", "opportunities", "strategy", "architecture"],

    # Process map: swim lanes, tools, waste heatmap overlay — GP capability, Agent 3
    "process_map": ["meta", "extraction", "findings"],

    # Findings page: pain points, optimisations, contradictions, session grouping — GF
    "findings_page": ["meta", "findings", "extraction"],

    # Waste page: waste_items breakdown with hourly rate — GV
    "waste": ["meta", "findings"],

    # Solutions overview: proposed_changes.research, process sidebar, pain point quotes — GS
    "solutions": ["meta", "extraction", "findings", "opportunities"],

    # AI Blueprint: waste anchor, proposed_changes with value/cost, benchmarks — GB
    "blueprint": ["meta", "findings", "opportunities", "strategy"],

    # Strategic approaches (legacy GA / strategic-approaches-landing)
    "strategic": ["meta", "opportunities", "strategy", "architecture"],

    # Comprehensive report — needs everything
    "report": ["meta", "extraction", "findings", "opportunities", "strategy", "architecture"],

    # Agent 3 (Extractor) — read existing data before merge
    "extractor": ["meta", "extraction", "findings"],

    # Agent 4 EI — synthesise improvements from extraction evidence
    "researcher_ei": ["meta", "extraction", "findings"],

    # Agent 4 RI/SA/BR/VR — need opportunities too
    "researcher_analysis": ["meta", "extraction", "findings", "opportunities"],

    # Agent 4 VR — verifies everything including strategy
    "researcher_verify": ["meta", "extraction", "findings", "opportunities", "strategy"],

    # Agent 6 (Designer) — needs full picture
    "designer": ["meta", "extraction", "findings", "opportunities", "strategy", "architecture"],
}


# ---------------------------------------------------------------------------
# Path resolution (config-driven; falls back to monorepo auto-detect)
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
from _paths import get_clients_dir as _get_clients_dir, get_client_path as _get_client_path  # noqa: E402


# ---------------------------------------------------------------------------
# Source Attribution Gate — unified sources[] citation invariant
# ---------------------------------------------------------------------------

class CitationGateError(Exception):
    """Raised by save_domain() when any gated item has an empty sources[]."""
    pass


# Gated arrays per domain. The gate enforces len(sources) >= 1 for every item
# in these arrays. Domains not listed have no gated items.
_GATED_FLAT_PATHS = [
    # (top_key,) for arrays at the root; ("client_context", "key") for nested.
    # processes[].steps[] handled specially.
    ("tools",),
    ("staff_roster",),
    ("decision_nodes",),
    ("business_metrics",),
    ("client_context", "constraints"),
    ("client_context", "strategic_notes"),
    ("pain_points",),
    ("waste_items",),
    ("optimisations",),
    ("contradictions",),
]

# Which keys live in which domain — used when walking a v4 per-domain payload
_DOMAIN_GATED_KEYS = {
    "extraction": {
        "tools", "staff_roster", "decision_nodes", "business_metrics",
        "client_context", "processes",
    },
    "findings": {
        "pain_points", "waste_items", "optimisations", "contradictions",
    },
}


def _iter_gated_items(data: dict):
    """Yield (item, path_str) for every item the source-gate covers in a flat
    or per-domain dict. Items can be either at the top-level keys (e.g.
    `pain_points`) or nested (e.g. `client_context.constraints`).
    """
    # processes[].steps[] — only place where we descend two levels
    processes = data.get("processes")
    if isinstance(processes, list):
        for pi, proc in enumerate(processes):
            if not isinstance(proc, dict):
                continue
            for si, step in enumerate(proc.get("steps") or []):
                if isinstance(step, dict):
                    yield step, f"processes[{pi}].steps[{si}]"

    for path in _GATED_FLAT_PATHS:
        if len(path) == 1:
            items = data.get(path[0])
            if not isinstance(items, list):
                continue
            for i, item in enumerate(items):
                if isinstance(item, dict):
                    yield item, f"{path[0]}[{i}]"
        else:
            parent = data.get(path[0])
            if not isinstance(parent, dict):
                continue
            items = parent.get(path[1])
            if not isinstance(items, list):
                continue
            for i, item in enumerate(items):
                if isinstance(item, dict):
                    yield item, f"{path[0]}.{path[1]}[{i}]"


def _coerce_quote(value) -> str:
    """source_quote / quote may be str or list[str]. Return joined non-empty string."""
    if isinstance(value, list):
        return " ".join(str(v) for v in value if v).strip()
    if isinstance(value, str):
        return value.strip()
    return ""


def _coerce_confidence(value) -> str:
    """Normalize confidence to HIGH/MEDIUM/LOW, default MEDIUM."""
    if isinstance(value, str) and value.upper() in ("HIGH", "MEDIUM", "LOW"):
        return value.upper()
    return "MEDIUM"


def _build_legacy_source_entry(item: dict, kind_hint: str = None) -> dict:
    """Construct one sources[] entry from legacy flat fields. Returns None if
    the item has insufficient information to build any valid entry.
    """
    quote = _coerce_quote(item.get("source_quote") or item.get("quote"))
    if not quote:
        return None

    speaker = (item.get("source_speaker") or item.get("speaker")) or None
    if isinstance(speaker, str):
        speaker = speaker.strip() or None
    confidence = _coerce_confidence(item.get("confidence"))

    sess = item.get("source_session")
    ts = item.get("source_timestamp_seconds")
    doc = (item.get("source_document") or "").strip() if isinstance(item.get("source_document"), str) else ""

    # Coerce session_id to int if possible
    if isinstance(sess, str) and sess.startswith("S"):
        try:
            sess = int(sess[1:])
        except ValueError:
            sess = None
    if not isinstance(sess, int):
        sess = None

    is_fathom = kind_hint == "fathom" or (sess is not None and not doc)
    is_document = kind_hint == "document" or (doc and sess is None)

    if is_fathom and sess is not None:
        return {
            "kind": "fathom",
            "quote": quote,
            "speaker": speaker,
            "confidence": confidence,
            "session_id": sess,
            "timestamp_seconds": ts if isinstance(ts, (int, float)) else 0,
        }
    if is_document and doc:
        return {
            "kind": "document",
            "quote": quote,
            "speaker": speaker,
            "confidence": confidence,
            "document_path": doc,
        }
    # If both fields are populated, prefer the explicit kind_hint, otherwise
    # prefer fathom (timestamp deep-link is higher fidelity).
    if sess is not None:
        return {
            "kind": "fathom",
            "quote": quote,
            "speaker": speaker,
            "confidence": confidence,
            "session_id": sess,
            "timestamp_seconds": ts if isinstance(ts, (int, float)) else 0,
        }
    if doc:
        return {
            "kind": "document",
            "quote": quote,
            "speaker": speaker,
            "confidence": confidence,
            "document_path": doc,
        }
    return None


def _backfill_legacy_from_sources(item: dict) -> None:
    """Populate legacy flat fields from sources[0] so downstream code that
    still reads `source_quote`, `source_session`, etc. keeps working during
    the 30-day hybrid period. Only writes fields not already populated.
    """
    sources = item.get("sources") or []
    if not sources:
        return
    primary = sources[0]
    if not isinstance(primary, dict):
        return
    quote = primary.get("quote") or ""
    speaker = primary.get("speaker") or ""
    if not item.get("source_quote"):
        item["source_quote"] = quote
    if not item.get("quote"):
        item["quote"] = quote
    if not item.get("speaker"):
        item["speaker"] = speaker
    if not item.get("source_speaker"):
        item["source_speaker"] = speaker
    if primary.get("kind") == "fathom":
        if item.get("source_session") in (None, "", []):
            item["source_session"] = primary.get("session_id")
        if item.get("source_timestamp_seconds") is None:
            item["source_timestamp_seconds"] = primary.get("timestamp_seconds")
    elif primary.get("kind") == "document":
        if not item.get("source_document"):
            item["source_document"] = primary.get("document_path", "")


def _normalize_citations(item: dict, kind_hint: str = None) -> dict:
    """In-place normalize one item's citations to the canonical sources[]
    array. If sources[] already present, only back-fill legacy fields for
    downstream readers. If absent, build sources[] from legacy fields and
    meeting_references[]. Sets `_citation_format: legacy_normalized_v1`
    when sources[] was synthesized.
    """
    if not isinstance(item, dict):
        return item
    sources = item.get("sources")
    if isinstance(sources, list) and len(sources) > 0:
        _backfill_legacy_from_sources(item)
        return item

    built = []
    primary = _build_legacy_source_entry(item, kind_hint=kind_hint)
    if primary is not None:
        built.append(primary)

    seen = set()
    for entry in built:
        if entry.get("kind") == "fathom":
            seen.add(("fathom", entry.get("session_id"), entry.get("timestamp_seconds")))
        elif entry.get("kind") == "document":
            seen.add(("document", entry.get("document_path")))

    for ref in (item.get("meeting_references") or []):
        if not isinstance(ref, dict):
            continue
        ref_sess = ref.get("session_id") or ref.get("session_number") or ref.get("session")
        if isinstance(ref_sess, str) and ref_sess.startswith("S"):
            try:
                ref_sess = int(ref_sess[1:])
            except ValueError:
                ref_sess = None
        if not isinstance(ref_sess, int):
            continue
        ref_ts = ref.get("timestamp_seconds")
        key = ("fathom", ref_sess, ref_ts)
        if key in seen:
            continue
        seen.add(key)
        quote = primary.get("quote") if primary else _coerce_quote(item.get("source_quote") or item.get("quote"))
        if not quote:
            continue
        built.append({
            "kind": "fathom",
            "quote": quote,
            "speaker": primary.get("speaker") if primary else None,
            "confidence": primary.get("confidence") if primary else "MEDIUM",
            "session_id": ref_sess,
            "timestamp_seconds": ref_ts if isinstance(ref_ts, (int, float)) else 0,
        })

    if built:
        item["sources"] = built
        item["_citation_format"] = "legacy_normalized_v1"
    else:
        item["sources"] = []
    return item


def _infer_kind_hint(item: dict) -> str:
    """Decide whether legacy item is more naturally fathom-attributed or
    document-attributed based on which legacy fields are populated.
    """
    has_doc = isinstance(item.get("source_document"), str) and item.get("source_document").strip() != ""
    has_sess = isinstance(item.get("source_session"), int) or (
        isinstance(item.get("source_session"), str) and item.get("source_session").startswith("S")
    )
    if has_doc and not has_sess:
        return "document"
    if has_sess and not has_doc:
        return "fathom"
    return None


def normalize_audit_citations(data: dict) -> dict:
    """Walk every gated item in a flat or per-domain dict and normalize to
    sources[]. Idempotent — safe to call multiple times. Returns the same
    dict reference for convenience.
    """
    if not isinstance(data, dict):
        return data
    for item, _path in _iter_gated_items(data):
        _normalize_citations(item, kind_hint=_infer_kind_hint(item))
    return data


def _gate_check_payload(domain: str, data: dict) -> list:
    """Return a list of violation strings — one per gated item with empty
    sources[]. Empty list means the payload is gate-clean.
    """
    if domain not in _DOMAIN_GATED_KEYS:
        return []
    violations = []
    for item, path in _iter_gated_items(data):
        sources = item.get("sources")
        if not isinstance(sources, list) or len(sources) == 0:
            ident = (
                item.get("id")
                or item.get("step_id")
                or item.get("waste_id")
                or item.get("optimisation_id")
                or item.get("pain_point_id")
                or item.get("tool_name")
                or item.get("name")
                or item.get("title")
                or "<no id>"
            )
            violations.append(f"  - {path} ({ident}): sources[] empty or missing")
    return violations


# ---------------------------------------------------------------------------
# BPMN 2.0 alignment normalizer (v4.0 -> v4.1 shape)
# ---------------------------------------------------------------------------

_TYPE_TO_ELEMENT = {
    "step": ("task", []),
    "decision": ("exclusive_gateway", []),
    "parallel_group": ("parallel_gateway", []),
    "pain": ("task", ["pain"]),
    "optimisation": ("task", ["optimisation"]),
    "automation": ("task", ["automation"]),
}

_TASK_TYPE_KEYWORDS = {
    "send_task": ["send", "email out", "sms to", "notify", "alert"],
    "receive_task": ["receive", "incoming", "arrives"],
}


def _infer_task_type_from_step(step: dict) -> str:
    owner = (step.get("owner") or "").lower()
    desc = (step.get("description") or "").lower()
    old_type = step.get("type", "step")
    if "automated" in owner or old_type == "automation":
        for kw in _TASK_TYPE_KEYWORDS["send_task"]:
            if kw in desc:
                return "send_task"
        return "service_task"
    for kw in _TASK_TYPE_KEYWORDS["receive_task"]:
        if kw in desc:
            return "receive_task"
    for kw in ["send", "email out", "sms to"]:
        if kw in desc:
            return "send_task"
    return "user_task"


def _derive_lane_id(step: dict, tools_lookup: dict = None) -> str:
    tool_ids = step.get("tool_ids") or []
    if tool_ids:
        tid = tool_ids[0]
        if tools_lookup and tid in tools_lookup:
            return tools_lookup[tid]
        return tid
    return "Manual"


def _synthesize_sequence_flows(steps: list) -> list:
    """Generate sequence flows from step array ordering, handling decision
    branches (branch_only) and parallel groups. Operates on raw extraction
    step_ids, not BPMN IDs.
    """
    flows = []
    fc = [0]

    def nid():
        fc[0] += 1
        return f"SF-{fc[0]:03d}"

    i = 0
    while i < len(steps) - 1:
        current = steps[i]
        cur_id = current.get("step_id", "")
        cur_type = current.get("type", "step")
        cur_etype = current.get("element_type", "")

        is_decision = cur_type == "decision" or cur_etype == "exclusive_gateway"

        if is_decision:
            branch_targets = []
            j = i + 1
            while j < len(steps) and steps[j].get("branch_only"):
                branch_targets.append(steps[j])
                j += 1
            next_main = steps[j] if j < len(steps) else None

            if branch_targets:
                for bt in branch_targets:
                    flows.append({"id": nid(), "from": cur_id, "to": bt["step_id"]})
                    if next_main:
                        flows.append({"id": nid(), "from": bt["step_id"], "to": next_main["step_id"]})
                if next_main:
                    flows.append({"id": nid(), "from": cur_id, "to": next_main["step_id"], "condition": "No"})
            elif next_main:
                flows.append({"id": nid(), "from": cur_id, "to": next_main["step_id"]})
            i = j
        else:
            next_step = steps[i + 1]
            if not next_step.get("branch_only"):
                flows.append({"id": nid(), "from": cur_id, "to": next_step["step_id"]})
            i += 1

    return flows


def _convert_decision_nodes_to_steps_and_flows(decision_nodes: list, processes: list):
    """Convert root-level decision_nodes[] entries into gateway steps within
    their respective processes and synthesize sequence flows. Modifies
    processes in place.
    """
    if not decision_nodes:
        return

    stage_map = {}
    for proc in processes:
        stage_map[proc.get("stage", "")] = proc

    for dn in decision_nodes:
        stage = dn.get("stage", "")
        proc = stage_map.get(stage)
        if not proc:
            continue

        step_id = dn.get("step_id") or dn.get("node_id", "")
        existing = any(s.get("step_id") == step_id for s in proc.get("steps", []))
        if existing:
            continue

        gateway_step = {
            "step_id": step_id,
            "element_type": "exclusive_gateway",
            "annotations": [],
            "label": dn.get("label") or dn.get("condition", ""),
            "description": dn.get("condition", ""),
            "owner": dn.get("owner", ""),
            "confidence": dn.get("confidence", "MEDIUM"),
            "sources": dn.get("sources", []),
            "lane_id": "Manual",
            "tool_ids": [],
        }
        after_step_id = dn.get("after_step_id")
        steps = proc.get("steps", [])
        insert_idx = len(steps)
        if after_step_id:
            for idx, s in enumerate(steps):
                if s.get("step_id") == after_step_id:
                    insert_idx = idx + 1
                    break
        steps.insert(insert_idx, gateway_step)

        seq_flows = proc.setdefault("sequence_flows", [])
        fc = len(seq_flows)
        yes_next = dn.get("yes_next")
        no_next = dn.get("no_next")
        if yes_next:
            fc += 1
            seq_flows.append({"id": f"SF-DN-{fc:03d}", "from": step_id, "to": yes_next, "condition": dn.get("yes_label", "Yes")})
        if no_next:
            fc += 1
            seq_flows.append({"id": f"SF-DN-{fc:03d}", "from": step_id, "to": no_next, "condition": dn.get("no_label", "No")})


def normalize_to_bpmn(data: dict) -> dict:
    """Normalize extraction data to BPMN-aligned v4.1 shape. Idempotent:
    skips steps that already have element_type. Works on flat dicts (from
    load_all/flatten) or per-domain dicts (from load_domain).

    Adds: element_type, annotations[], lane_id, task_type on each step.
    Adds: sequence_flows[] on each process.
    Converts: decision_nodes[] into inline gateway steps.
    """
    if not isinstance(data, dict):
        return data

    processes = data.get("processes")
    if not isinstance(processes, list):
        return data

    tools_list = data.get("tools") or []
    tools_lookup = {}
    for t in tools_list:
        if isinstance(t, dict):
            tid = t.get("tool_id") or t.get("tool_name", "")
            name = t.get("tool_name", tid)
            if tid:
                tools_lookup[tid] = name

    needs_flow_synthesis = set()
    for i, proc in enumerate(processes):
        if not proc.get("sequence_flows"):
            needs_flow_synthesis.add(i)

    decision_nodes = data.get("decision_nodes") or []
    if decision_nodes:
        _convert_decision_nodes_to_steps_and_flows(decision_nodes, processes)

    for i, proc in enumerate(processes):
        steps = proc.get("steps") or []

        for step in steps:
            if not step.get("element_type"):
                old_type = step.get("type", "step")
                etype, annots = _TYPE_TO_ELEMENT.get(old_type, ("task", []))
                step["element_type"] = etype
                step["annotations"] = annots
            elif "annotations" not in step:
                step["annotations"] = []

            if not step.get("lane_id"):
                step["lane_id"] = _derive_lane_id(step, tools_lookup)

            if not step.get("task_type") and step.get("element_type") == "task":
                step["task_type"] = _infer_task_type_from_step(step)

        if i in needs_flow_synthesis:
            dn_flows = proc.get("sequence_flows") or []
            synthesized = _synthesize_sequence_flows(steps)
            seen = {(f["from"], f["to"]) for f in dn_flows}
            for sf in synthesized:
                if (sf["from"], sf["to"]) not in seen:
                    dn_flows.append(sf)
                    seen.add((sf["from"], sf["to"]))
            proc["sequence_flows"] = dn_flows

        if "flows" in proc and "parallel_tracks" not in proc:
            proc["parallel_tracks"] = proc.pop("flows")

    return data


# ---------------------------------------------------------------------------
# Core detection
# ---------------------------------------------------------------------------

def is_v3(data: dict) -> bool:
    """Return True if data is v3 nested format."""
    version = data.get("_schema_version", "")
    return version.startswith("3") or "meta" in data


# ---------------------------------------------------------------------------
# Conversion: nested v3 -> flat v2
# ---------------------------------------------------------------------------

def flatten(nested: dict) -> dict:
    """
    Convert v3 nested structure to v2 flat dict.

    Merges meta, extraction, findings, opportunities, strategy, architecture
    into a single dict. Preserves root-level keys at the top level.

    Also un-nests legacy sub-keys that nest() merged into client_context:
    extraction.client_context.constraints  -> constraints (top-level)
    extraction.client_context.strategic_notes -> strategic_notes (top-level)

    Safe to call on a v2 flat dict — detects by absence of domain keys and
    returns as-is (with a defensive copy).
    """
    if not is_v3(nested):
        # Already flat — return a copy unchanged
        return dict(nested)

    result = {}

    # Root-level keys first
    for key in ROOT_KEYS:
        if key in nested:
            result[key] = nested[key]

    # Merge domains in priority order (later domains overwrite earlier on collision)
    for domain in DOMAIN_ORDER:
        if domain in nested and isinstance(nested[domain], dict):
            result.update(nested[domain])

    # Un-nest legacy sub-keys from client_context so roundtrip works
    client_context = result.get("client_context")
    if isinstance(client_context, dict):
        if "constraints" in client_context:
            result["constraints"] = client_context.pop("constraints")
            # If client_context is now empty (was created solely to hold these), leave it out
            if not client_context:
                del result["client_context"]
        if "strategic_notes" in client_context:
            result["strategic_notes"] = client_context.pop("strategic_notes")
            if not client_context:
                del result["client_context"]

    return result


# ---------------------------------------------------------------------------
# Conversion: flat v2 -> nested v3
# ---------------------------------------------------------------------------

def nest(flat: dict) -> dict:
    """
    Convert v2 flat structure to v3 nested dict.

    Routes each key using DOMAIN_ROUTING, META_KEYS, ROOT_KEYS, and DROP_KEYS.
    Handles legacy keys: constraints, strategic_notes, business_metrics_list.
    Sets _schema_version to "3.0.0".
    """
    if is_v3(flat):
        # Already nested — return a copy unchanged (version is already 3.x)
        return dict(flat)

    result = {
        "_schema_version": "3.0.0",
        "meta": {},
        "extraction": {},
        "findings": {},
        "opportunities": {},
        "strategy": {},
        "architecture": {
            "requirements_spec": {},
            "architecture_doc": {},
            "architecture_verification": {},
            "cowork_demos": [],
            "branding": {},
        },
    }

    # Preserve _section_index and other root keys
    for key in ROOT_KEYS - {"_schema_version"}:
        if key in flat:
            result[key] = flat[key]

    # Track legacy keys for special handling
    has_constraints = "constraints" in flat
    has_strategic_notes = "strategic_notes" in flat
    has_business_metrics_list = "business_metrics_list" in flat
    has_business_metrics = "business_metrics" in flat

    for key, value in flat.items():
        # Skip drop keys
        if key in DROP_KEYS:
            continue

        # Skip root keys (already handled above)
        if key in ROOT_KEYS:
            continue

        # Handle legacy extraction sub-keys
        if key == "constraints":
            # Will be merged into client_context after main loop
            continue
        if key == "strategic_notes":
            # Will be merged into client_context after main loop
            continue
        if key == "business_metrics_list":
            if not has_business_metrics:
                # No canonical business_metrics — promote this as business_metrics
                result["extraction"]["business_metrics"] = value
            else:
                # Canonical business_metrics exists — store business_metrics_list as a
                # separate key in extraction so flatten() can round-trip it.
                # Migration scripts can drop it explicitly if desired.
                result["extraction"]["business_metrics_list"] = value
            continue

        # Route to domain via DOMAIN_ROUTING
        if key in DOMAIN_ROUTING:
            domain = DOMAIN_ROUTING[key]
            result[domain][key] = value
            continue

        # Route to meta via META_KEYS
        if key in META_KEYS:
            result["meta"][key] = value
            continue

        # Catch-all: unknown key defaults to meta with a warning
        warnings.warn(
            f"nest(): unknown key '{key}' not in DOMAIN_ROUTING, META_KEYS, or ROOT_KEYS — "
            f"routing to meta domain. Add it to the routing table if this is intentional.",
            stacklevel=2,
        )
        result["meta"][key] = value

    # Post-loop: merge constraints and strategic_notes into extraction.client_context
    if has_constraints or has_strategic_notes:
        if "client_context" not in result["extraction"]:
            result["extraction"]["client_context"] = {}
        elif not isinstance(result["extraction"]["client_context"], dict):
            # client_context exists but is not a dict — wrap it
            result["extraction"]["client_context"] = {"value": result["extraction"]["client_context"]}

        if has_constraints:
            result["extraction"]["client_context"]["constraints"] = flat["constraints"]
        if has_strategic_notes:
            result["extraction"]["client_context"]["strategic_notes"] = flat["strategic_notes"]

    return result


# ---------------------------------------------------------------------------
# v4 multi-file support
# ---------------------------------------------------------------------------

def resolve_audit_dir(slug_or_path: str) -> Path:
    """Resolve a client slug or file path to the audit directory."""
    p = str(slug_or_path)
    if "/" in p or p.endswith(".json"):
        path = Path(p)
        if path.is_file():
            return path.parent
        if path.is_dir():
            return path
        return path.parent if path.suffix else path
    client = _get_client_path(slug_or_path)
    new_path = client / "03-audit" / "data"
    if new_path.exists():
        return new_path
    return client / "audit"


def detect_version(slug_or_path: str) -> str:
    """
    Detect the schema version for a client's audit data.

    Returns '4', '3', '2', or 'none'.
    """
    audit_dir = resolve_audit_dir(slug_or_path)

    if (audit_dir / "audit-manifest.json").exists():
        return "4"

    single = audit_dir / "audit-data.json"
    if not single.exists():
        return "none"

    data = json.loads(single.read_text())
    if is_v3(data):
        return "3"
    return "2"


def _compute_checksum(content: bytes) -> str:
    """SHA-256 hex digest of file content."""
    return hashlib.sha256(content).hexdigest()


def _load_manifest(slug: str) -> dict:
    """Load audit-manifest.json for a client."""
    manifest_path = resolve_audit_dir(slug) / "audit-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No v4 manifest for client '{slug}' at {manifest_path}")
    return json.loads(manifest_path.read_text())


def _save_manifest(slug: str, manifest: dict) -> None:
    """Write audit-manifest.json."""
    manifest_path = resolve_audit_dir(slug) / "audit-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def _inject_extraction_defaults(extraction: dict) -> dict:
    """Inject defaults for Sprint 1-4 fields when reading legacy extraction data."""
    for process in extraction.get("processes", []):
        for step in process.get("steps", []):
            # Sprint 1 defaults
            if "iato" not in step:
                step["iato"] = None
            if "_gaps" not in step:
                step["_gaps"] = None
            if "display_label" not in step:
                step["display_label"] = step.get("label", "")
            if "handoff" not in step:
                step["handoff"] = None
            # Sprint 2 defaults
            if "gateway_anatomy" not in step:
                step["gateway_anatomy"] = None

        for flow in process.get("sequence_flows", []):
            # Sprint 1 defaults
            if "volume_split" not in flow:
                flow["volume_split"] = None
            if "handoff" not in flow:
                flow["handoff"] = None

        # Sprint 1 defaults at process level
        if "subject_traces" not in process:
            process["subject_traces"] = []

    return extraction


def _inject_findings_defaults(findings: dict) -> dict:
    """Inject defaults for Sprint 2-4 fields when reading legacy findings data."""
    # Sprint 2 defaults
    if "gaps_register" not in findings:
        findings["gaps_register"] = []
    if "control_gaps" not in findings:
        findings["control_gaps"] = []
    # Sprint 4 defaults
    if "kiq_status" not in findings:
        findings["kiq_status"] = []
    return findings


def _inject_opportunities_defaults(opportunities: dict) -> dict:
    """Inject defaults for Sprint 5-7 fields when reading legacy opportunities data."""
    for change in opportunities.get("proposed_changes", []):
        # Sprint 5 defaults
        if "volume_weight" not in change:
            change["volume_weight"] = 1.0
        if "blocked_by_gaps" not in change:
            change["blocked_by_gaps"] = []
        if "source_handoff_ids" not in change:
            change["source_handoff_ids"] = []
        if "control_gap_ids" not in change:
            change["control_gap_ids"] = []
        # Sprint 6 defaults inside research
        research = change.get("research") or {}
        if research:
            if "transfer_mechanism_addressed" not in research:
                research["transfer_mechanism_addressed"] = None
            if "integration_pair" not in research:
                research["integration_pair"] = None
            if "gap_status" not in research:
                research["gap_status"] = "clear"
            if "gap_blockers" not in research:
                research["gap_blockers"] = []
            change["research"] = research
    return opportunities


def load_domain(slug: str, domain: str) -> dict:
    """
    Load a single domain file for a v4 client.

    Returns the domain dict (e.g., {"client_slug": "...", ...} for meta).
    Falls back to v3/v2 single-file loading if no manifest exists.

    Items in gated arrays are normalized to the canonical `sources[]` shape
    (legacy flat fields are converted on read; new-format items also get
    legacy fields back-filled during the hybrid period).
    """
    audit_dir = resolve_audit_dir(slug)
    manifest_path = audit_dir / "audit-manifest.json"

    if manifest_path.exists():
        domain_path = audit_dir / f"{domain}.json"
        if not domain_path.exists():
            raise FileNotFoundError(f"Domain file not found: {domain_path}")
        result = json.loads(domain_path.read_text())
        result = normalize_audit_citations(result)
        if domain == "extraction":
            result = normalize_to_bpmn(result)
            result = _inject_extraction_defaults(result)
        elif domain == "findings":
            result = _inject_findings_defaults(result)
        elif domain == "opportunities":
            result = _inject_opportunities_defaults(result)
        return result

    single = audit_dir / "audit-data.json"
    if not single.exists():
        raise FileNotFoundError(f"No audit data found for client '{slug}'")

    data = json.loads(single.read_text())
    if is_v3(data):
        result = data.get(domain, {}) if domain != "meta" else data.get("meta", {})
        result = normalize_audit_citations(result)
        if domain == "extraction":
            result = normalize_to_bpmn(result)
            result = _inject_extraction_defaults(result)
        elif domain == "findings":
            result = _inject_findings_defaults(result)
        elif domain == "opportunities":
            result = _inject_opportunities_defaults(result)
        return result

    flat = data
    if domain == "meta":
        return {k: flat[k] for k in META_KEYS if k in flat}
    result = {k: flat[k] for k in flat if DOMAIN_ROUTING.get(k) == domain}
    result = normalize_audit_citations(result)
    if domain == "extraction":
        result = normalize_to_bpmn(result)
        result = _inject_extraction_defaults(result)
    elif domain == "findings":
        result = _inject_findings_defaults(result)
    elif domain == "opportunities":
        result = _inject_opportunities_defaults(result)
    return result


def save_domain(slug: str, domain: str, data: dict, bypass_gate: bool = False) -> None:
    """
    Write a domain file and update the manifest.

    Steps:
    1. Run the Source Attribution Gate (unless bypass_gate=True). Any item
       in a gated array with empty sources[] raises CitationGateError before
       any write occurs. Use bypass_gate=True only for migration scripts that
       intentionally write legacy-shaped data.
    2. Write clients/{slug}/audit/{domain}.json
    3. Compute SHA-256
    4. Update manifest checksum, timestamps, convenience fields
    5. Write manifest (commit point)
    """
    audit_dir = resolve_audit_dir(slug)
    domain_path = audit_dir / f"{domain}.json"
    manifest_path = audit_dir / "audit-manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"No v4 manifest for client '{slug}'. Cannot save_domain on non-v4 client.")

    if not bypass_gate:
        violations = _gate_check_payload(domain, data)
        if violations:
            raise CitationGateError(
                f"Source Attribution Gate blocked save_domain('{slug}', '{domain}'): "
                f"{len(violations)} item(s) lack sources[] attribution.\n"
                + "\n".join(violations[:20])
                + ("\n  ...(and more)" if len(violations) > 20 else "")
                + "\n\nFix: ensure every gated item carries `sources[]` with at least one "
                "valid entry, OR pass bypass_gate=True for migration scripts."
            )

    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    content_bytes = content.encode("utf-8")
    domain_path.write_bytes(content_bytes)

    checksum = _compute_checksum(content_bytes)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    manifest = json.loads(manifest_path.read_text())
    if domain in manifest.get("domains", {}):
        manifest["domains"][domain]["checksum"] = checksum
        manifest["domains"][domain]["updated_at"] = now
    manifest["updated_at"] = now

    if domain == "meta":
        manifest["audit_status"] = data.get("audit_status", manifest.get("audit_status", "in_progress"))
        manifest["company_name"] = data.get("company_name", manifest.get("company_name", ""))

    _save_manifest(slug, manifest)


def load_all(slug: str) -> dict:
    """
    Reassemble a full flat dict from all audit data files.

    Auto-detects v4 (manifest + domain files), v3 (nested single file),
    or v2 (flat single file) and returns the same flat dict interface.
    """
    audit_dir = resolve_audit_dir(slug)
    manifest_path = audit_dir / "audit-manifest.json"

    if manifest_path.exists():
        # Build a v3-style nested dict, then flatten for consistent output
        nested = {"_schema_version": "4.0.0"}
        for domain in DOMAIN_ORDER:
            domain_path = audit_dir / f"{domain}.json"
            if domain_path.exists():
                nested[domain] = json.loads(domain_path.read_text())
            else:
                nested[domain] = {}
        manifest = json.loads(manifest_path.read_text())
        for key in ("analyst_metadata", "architect_metadata"):
            if key in manifest:
                nested[key] = manifest[key]
        result = normalize_audit_citations(flatten(nested))
        return normalize_to_bpmn(result)

    single = audit_dir / "audit-data.json"
    if not single.exists():
        raise FileNotFoundError(f"No audit data found for client '{slug}' at {audit_dir}")

    data = json.loads(single.read_text())
    if is_v3(data):
        result = normalize_audit_citations(flatten(data))
        return normalize_to_bpmn(result)
    result = normalize_audit_citations(data)
    return normalize_to_bpmn(result)


# ---------------------------------------------------------------------------
# Selective loading
# ---------------------------------------------------------------------------

def load_sections(path_or_slug, sections: list) -> dict:
    """
    Load specific domain groups from audit data.

    Supports v4 (manifest + domain files), v3 (nested single file),
    and v2 (flat single file). Returns a flat dict matching the v2 interface.

    If path_or_slug is a slug and the client is on v4, loads only the
    requested domain files. Otherwise loads from the single file.

    Always includes meta domain regardless of sections specified.
    """
    slug = str(path_or_slug)
    is_slug = "/" not in slug and not slug.endswith(".json")

    if is_slug:
        version = detect_version(slug)
        if version == "4":
            load_domains = set(sections) | {"meta"}
            nested = {"_schema_version": "4.0.0"}
            audit_dir = resolve_audit_dir(slug)
            for domain in DOMAIN_ORDER:
                if domain in load_domains:
                    domain_path = audit_dir / f"{domain}.json"
                    if domain_path.exists():
                        nested[domain] = json.loads(domain_path.read_text())
            result = normalize_audit_citations(flatten(nested))
            return normalize_to_bpmn(result)

    path = Path(path_or_slug) if not is_slug else resolve_audit_dir(slug) / "audit-data.json"
    data = json.loads(path.read_text())

    if not is_v3(data):
        result = normalize_audit_citations(data)
        return normalize_to_bpmn(result)

    partial = {}
    for key in ROOT_KEYS:
        if key in data:
            partial[key] = data[key]

    for domain in sections:
        if domain in data and isinstance(data[domain], dict):
            partial[domain] = data[domain]

    result = normalize_audit_citations(flatten(partial))
    return normalize_to_bpmn(result)


def load_profile(path, profile: str) -> dict:
    """
    Load a predefined read profile by name.
    Calls load_sections() internally with the profile's domain list.
    Raises ValueError if profile name not recognized.
    """
    if profile not in PROFILES:
        raise ValueError(
            f"Unknown profile '{profile}'. Available profiles: {sorted(PROFILES.keys())}"
        )
    return load_sections(path, PROFILES[profile])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Load and convert audit data (supports v2, v3, and v4 formats)."
    )
    parser.add_argument("path", nargs="?", help="Path to audit-data.json (optional if --slug is used)")
    parser.add_argument("--slug", help="Client slug (alternative to path, auto-detects version)")
    parser.add_argument("--profile", help="Load a predefined profile")
    parser.add_argument("--sections", nargs="+", help="Load specific domain names (space-separated)")
    parser.add_argument("--domain", help="Load a single domain (v4 clients)")
    parser.add_argument("--list-profiles", action="store_true", help="Print all available profiles")
    parser.add_argument("--version", action="store_true", help="Print the schema version")
    parser.add_argument("--detect-version", metavar="SLUG", help="Detect schema version for a client slug")
    parser.add_argument("--all", action="store_true", help="Load all domains, return flat dict (v4 clients)")

    args = parser.parse_args()

    if args.list_profiles:
        for name, domains in sorted(PROFILES.items()):
            print(f"  {name:<25} {', '.join(domains)}")
        return

    if args.detect_version:
        v = detect_version(args.detect_version)
        print(v)
        return

    identifier = args.slug or args.path
    if not identifier:
        parser.error("Either a path or --slug is required")

    if args.slug:
        if args.version:
            v = detect_version(args.slug)
            print(f"4.0.0" if v == "4" else f"detected: {v}")
            return

        if args.domain:
            result = load_domain(args.slug, args.domain)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return

        if args.all:
            result = load_all(args.slug)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return

        if args.profile:
            result = load_profile(args.slug, args.profile)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return

        if args.sections:
            result = load_sections(args.slug, args.sections)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return

        result = load_all(args.slug)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    path = Path(args.path)
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(path.read_text())

    if args.version:
        version = data.get("_schema_version", "not set")
        print(version)
        return

    if args.profile:
        result = load_profile(path, args.profile)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if args.sections:
        result = load_sections(path, args.sections)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if is_v3(data):
        print(json.dumps(flatten(data), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
