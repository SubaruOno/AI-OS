#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""
validate_extraction_quality.py — Semantic quality checks for extraction.json.

Validates that extracted process steps are genuine actions (not observations),
follow verb-noun naming conventions, form coherent journeys, and have clear
labels. Complements validate_bpmn_json.py (structural) with semantic checks.

Usage:
  python3 validate_extraction_quality.py --extraction-json path/to/extraction.json [--stages s1,s2] [--partial-ok] [--verbose]

Exit codes:
  0 — pass (no findings)
  1 — advisory findings present (non-blocking)
  2 — warning findings present (non-blocking, logged to ingestion manifest)
  3 — error (file not found, invalid JSON, etc.)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

VERSION = "v1"

_START_TYPES = {"start_event", "start"}
_END_TYPES = {"end_event", "end"}
_EVENT_TYPES = _START_TYPES | _END_TYPES
_GATEWAY_TYPES = {"exclusive_gateway", "parallel_gateway", "inclusive_gateway", "event_based_gateway"}

ACTION_VERBS = {
    "accept", "acknowledge", "add", "adjust", "allocate", "analyse", "analyze",
    "apply", "approve", "archive", "arrange", "assess", "assign", "associate",
    "attach", "attempt", "authorise", "authorize",
    "book", "brief", "build", "bundle",
    "calculate", "call", "cancel", "capture", "chase", "check", "claim",
    "classify", "close", "collect", "compare", "compile", "complete", "compose",
    "conduct", "confirm", "configure", "connect", "consolidate", "contact",
    "conduct", "confirm", "configure", "connect", "consolidate", "contact",
    "convert", "coordinate", "copy", "correct", "create", "cross-check",
    "customise", "customize", "cycle",
    "decide", "decline", "deduct", "define", "delegate", "delete", "deliver",
    "demolish", "deploy", "design", "designate", "detect", "determine", "develop",
    "discard", "discontinue", "discover", "discuss", "dispatch",
    "distribute", "document", "download", "draft", "duplicate",
    "edit", "email", "embed", "enable", "endorse", "engage", "enter",
    "escalate", "establish", "estimate", "evaluate", "examine", "execute",
    "expedite", "export", "extract",
    "facilitate", "file", "fill", "filter", "finalise", "finalize", "find",
    "flag", "follow", "follow-up", "forecast", "format", "formulate", "forward",
    "fulfil", "fulfill",
    "gather", "generate",
    "hold",
    "identify", "implement", "import", "initiate", "input", "inspect",
    "install", "instruct", "integrate", "interview", "introduce", "inventory",
    "investigate", "invoice", "issue",
    "join",
    "launch", "liaise", "list", "load", "locate", "log", "look",
    "maintain", "make", "map", "mark", "match", "measure", "meet", "merge",
    "migrate", "mobilise", "mobilize", "modify", "monitor", "move",
    "negotiate", "nominate", "normalise", "normalize", "note", "notify",
    "nurture",
    "obtain", "offer", "onboard", "open", "order", "organise", "organize", "outline",
    "package", "pay", "perform", "photograph", "pick", "place", "plan",
    "populate", "post", "prepare", "present", "price", "print", "prioritise",
    "prioritize", "process", "procure", "produce", "program", "progress",
    "propose", "provide", "publish", "pull", "purchase", "push", "put",
    "qualify", "query", "queue", "quote",
    "raise", "read", "reassign", "receive", "recognise", "recognize",
    "recommend", "reconcile", "record", "recruit", "redirect", "reduce",
    "refer", "register", "reject", "release", "remind", "remove", "renew",
    "reorder", "repeat", "replace", "reply", "report", "request", "research",
    "reserve", "reset", "resolve", "respond", "restore", "retrieve",
    "return", "review", "revise", "revoke", "route", "run",
    "save", "scan", "schedule", "scope", "screen", "search", "secure",
    "select", "send", "separate", "sequence", "serve", "set", "settle", "share",
    "ship", "sign", "sort", "source", "split", "stage", "standardise",
    "standardize", "start", "store", "structure", "submit", "subscribe",
    "summarise", "summarize", "supersede", "supervise", "supply", "support",
    "suspend", "sync", "synchronise", "synchronize",
    "tabulate", "tag", "tender", "terminate", "test", "track", "train",
    "transcribe", "transfer", "transform", "translate", "transmit",
    "trigger", "troubleshoot",
    "unpack", "update", "upgrade", "upload", "use",
    "validate", "verify", "view", "visit",
    "wait", "walk", "weigh", "withdraw", "write",
}

BROAD_VERBS = {"handle", "manage", "do", "deal"}

OBSERVATION_TITLE_PATTERNS = [
    re.compile(r"^no\s", re.I),
    re.compile(r"^lack\s+of\b", re.I),
    re.compile(r"^missing\s", re.I),
    re.compile(r"^absence\s+of\b", re.I),
    re.compile(r"^there\s+(is|are)\b", re.I),
    re.compile(r"^it'?s\s", re.I),
    re.compile(r"^it\s+takes\b", re.I),
    re.compile(r"\bmisalignment\b", re.I),
    re.compile(r"\binconsisten", re.I),
    re.compile(r"\bsiloed?\b", re.I),
    re.compile(r"\bis\s+(slow|manual|broken|painful|difficult|clunky|messy|fragmented|outdated)\b", re.I),
    re.compile(r"\bdoes\s+not\s+(have|exist|happen)\b", re.I),
    re.compile(r"\bdon'?t\s+(have|do|track|use)\b", re.I),
]

OBSERVATION_DESC_PATTERNS = [
    re.compile(r"there is no (process|system|way|automation|tool)", re.I),
    re.compile(r"nobody (currently|does|tracks)", re.I),
    re.compile(r"we don'?t (have|do|track)", re.I),
    re.compile(r"no (one|process|system|automation|way) to\b", re.I),
    re.compile(r"not (currently|yet) (done|tracked|automated)", re.I),
]


def _get_element_type(step: dict) -> str:
    return step.get("element_type") or step.get("type", "task")


def _get_title(step: dict) -> str:
    return (step.get("title") or step.get("label") or "").strip()


_SKIP_PREFIXES = {"the", "a", "an", "manually", "automatically", "auto"}

_THIRD_PERSON_SUFFIXES = re.compile(r"^(\w+)(s|es)$")

_KNOWN_SUBJECTS = {
    "customer", "client", "dealer", "supplier", "vendor", "lender", "broker",
    "staff", "team", "manager", "admin", "user", "system", "platform",
    "lead", "prospect", "finance", "sales", "owner", "operator",
    "vehicle", "insurance", "deal", "application", "invoice", "payment",
    "order", "request", "record", "document",
}


def _first_word(title: str) -> str:
    words = title.lower().split()
    if not words:
        return ""
    idx = 0
    while idx < len(words) - 1 and words[idx].rstrip(",") in _SKIP_PREFIXES:
        idx += 1
    return words[idx]


def _find_action_verb(title: str) -> tuple[str, bool]:
    """Find the action verb in a title, handling subject-verb-object patterns.

    Returns (verb_candidate, found_in_verb_set).
    """
    words = title.lower().split()
    if not words:
        return ("", False)

    idx = 0
    while idx < len(words) - 1 and words[idx].rstrip(",") in _SKIP_PREFIXES:
        idx += 1

    fw = words[idx]
    if fw in ACTION_VERBS:
        return (fw, True)
    if fw in BROAD_VERBS:
        return (fw, True)

    for scan_start in range(idx, min(idx + 3, len(words))):
        if words[scan_start].rstrip(",") not in _KNOWN_SUBJECTS and scan_start > idx:
            break
        verb_idx = scan_start + 1
        if verb_idx >= len(words):
            break
        candidate = words[verb_idx]
        if candidate in ACTION_VERBS or candidate in BROAD_VERBS:
            return (candidate, True)
        m = _THIRD_PERSON_SUFFIXES.match(candidate)
        if m:
            base = m.group(1)
            if base in ACTION_VERBS or base in BROAD_VERBS:
                return (base, True)
            if candidate.endswith("ies"):
                base2 = candidate[:-3] + "y"
                if base2 in ACTION_VERBS:
                    return (base2, True)

    if fw.startswith("auto-") and len(fw) > 5:
        verb_part = fw[5:]
        if verb_part in ACTION_VERBS:
            return (verb_part, True)

    return (fw, fw in ACTION_VERBS)


def _is_task_type(element_type: str) -> bool:
    return element_type not in (_EVENT_TYPES | _GATEWAY_TYPES)


def check_sq01(step: dict, stage: str) -> list[dict]:
    """SQ01: Verb-noun test for task steps."""
    et = _get_element_type(step)
    if not _is_task_type(et):
        return []

    title = _get_title(step)
    if not title:
        return []

    sid = step.get("step_id", "?")
    verb, found = _find_action_verb(title)
    findings = []

    if found and verb in BROAD_VERBS:
        findings.append({
            "rule": "SQ01", "severity": "advisory", "stage": stage,
            "step_id": sid, "title": title,
            "message": f"Step title uses broad verb '{verb}'. Be more specific about the business action (e.g. 'Handle invoice' -> 'Verify invoice line items').",
        })
    elif not found:
        findings.append({
            "rule": "SQ01", "severity": "advisory", "stage": stage,
            "step_id": sid, "title": title,
            "message": f"Step title does not start with an action verb. If this describes a real action, rewrite as verb-noun (e.g. 'Invoice' -> 'Process invoice'). If it describes a pain, move to pain_points[].",
        })

    return findings


def check_sq02(step: dict, stage: str) -> list[dict]:
    """SQ02: Observation language patterns in step titles and descriptions."""
    et = _get_element_type(step)
    if not _is_task_type(et):
        return []

    title = _get_title(step)
    desc = (step.get("description") or "")[:120]
    sid = step.get("step_id", "?")
    findings = []

    for pattern in OBSERVATION_TITLE_PATTERNS:
        if pattern.search(title):
            findings.append({
                "rule": "SQ02", "severity": "advisory", "stage": stage,
                "step_id": sid, "title": title,
                "message": f"Step title matches observation pattern '{pattern.pattern}'. This describes a state or complaint, not a discrete action. Should likely be in pain_points[].",
            })
            break

    if not findings and desc:
        for pattern in OBSERVATION_DESC_PATTERNS:
            if pattern.search(desc):
                findings.append({
                    "rule": "SQ02", "severity": "advisory", "stage": stage,
                    "step_id": sid, "title": title,
                    "message": f"Step description contains observation language ('{pattern.pattern}'). Verify this step describes an action someone performs, not a gap or complaint.",
                })
                break

    return findings


def check_sq03(proc: dict, stage: str) -> list[dict]:
    """SQ03: Flow coherence via connected components."""
    steps = proc.get("steps") or []
    flows = proc.get("sequence_flows") or []

    step_ids = {s.get("step_id", "") for s in steps if s.get("step_id")}
    if len(step_ids) < 3 or not flows:
        return []

    adjacency: dict[str, set[str]] = {sid: set() for sid in step_ids}
    for f in flows:
        src = f.get("from") or f.get("source_ref", "")
        tgt = f.get("to") or f.get("target_ref", "")
        if src in adjacency and tgt in adjacency:
            adjacency[src].add(tgt)
            adjacency[tgt].add(src)

    visited: set[str] = set()
    components = 0
    for sid in step_ids:
        if sid in visited:
            continue
        components += 1
        queue = [sid]
        while queue:
            node = queue.pop()
            if node in visited:
                continue
            visited.add(node)
            queue.extend(adjacency[node] - visited)

    if components > 1 and len(step_ids) > 5:
        return [{
            "rule": "SQ03", "severity": "warning", "stage": stage,
            "step_id": None, "title": None,
            "message": f"Process '{stage}' has {components} disconnected clusters across {len(step_ids)} steps. Steps may be observations that broke the flow, or sequence flows are missing.",
        }]
    elif components > 1:
        return [{
            "rule": "SQ03", "severity": "advisory", "stage": stage,
            "step_id": None, "title": None,
            "message": f"Process '{stage}' has {components} disconnected clusters ({len(step_ids)} steps). May resolve as more sessions are extracted.",
        }]

    return []


def check_sq04(step: dict, stage: str) -> list[dict]:
    """SQ04: Label quality checks."""
    et = _get_element_type(step)
    if et in _EVENT_TYPES:
        return []

    title = _get_title(step)
    if not title:
        return []

    sid = step.get("step_id", "?")
    findings = []
    words = title.split()

    if len(words) == 1 and _is_task_type(et):
        findings.append({
            "rule": "SQ04", "severity": "advisory", "stage": stage,
            "step_id": sid, "title": title,
            "message": f"Single-word title '{title}' is ambiguous. Add a noun to clarify (e.g. 'Review' -> 'Review quote against scope').",
        })

    if len(words) > 12:
        findings.append({
            "rule": "SQ04", "severity": "advisory", "stage": stage,
            "step_id": sid, "title": title,
            "message": f"Title is {len(words)} words (max recommended: 12). Shorten to a concise verb-noun phrase and move detail to description.",
        })

    if re.search(r"\((if applicable|sometimes|ad.?hoc|manual|occasionally|when needed|as required)\)", title, re.I):
        findings.append({
            "rule": "SQ04", "severity": "advisory", "stage": stage,
            "step_id": sid, "title": title,
            "message": "Title contains a hedging qualifier. Remove the qualifier and note the condition in the description or model as a gateway branch.",
        })

    if title.endswith("...") or title.lower().endswith("etc") or title.lower().endswith("etc."):
        findings.append({
            "rule": "SQ04", "severity": "advisory", "stage": stage,
            "step_id": sid, "title": title,
            "message": "Title appears incomplete. Write the full action.",
        })

    return findings


def check_sq05(proc: dict, stage: str) -> list[dict]:
    """SQ05: Journey completeness heuristic."""
    steps = proc.get("steps") or []
    flows = proc.get("sequence_flows") or []

    task_steps = [s for s in steps if _is_task_type(_get_element_type(s))]
    if len(task_steps) < 3:
        return []

    step_ids = {s.get("step_id", "") for s in steps if s.get("step_id")}
    incoming = set()
    outgoing = set()
    for f in flows:
        src = f.get("from") or f.get("source_ref", "")
        tgt = f.get("to") or f.get("target_ref", "")
        if tgt in step_ids:
            incoming.add(tgt)
        if src in step_ids:
            outgoing.add(src)

    roots = [s for s in steps
             if s.get("step_id") and s.get("step_id") not in incoming
             and _get_element_type(s) not in _END_TYPES]
    sinks = [s for s in steps
             if s.get("step_id") and s.get("step_id") not in outgoing
             and _get_element_type(s) not in _START_TYPES]

    findings = []
    if len(roots) > 2:
        root_ids = [s.get("step_id", "?") for s in roots[:5]]
        findings.append({
            "rule": "SQ05", "severity": "advisory", "stage": stage,
            "step_id": None, "title": None,
            "message": f"Process '{stage}' has {len(roots)} entry points (steps with no incoming flow): {root_ids}. Expected 1 clear start. Some may be observations without flow connections.",
        })

    if len(sinks) > 2:
        sink_ids = [s.get("step_id", "?") for s in sinks[:5]]
        findings.append({
            "rule": "SQ05", "severity": "advisory", "stage": stage,
            "step_id": None, "title": None,
            "message": f"Process '{stage}' has {len(sinks)} exit points (steps with no outgoing flow): {sink_ids}. Expected 1 clear end. Some may be observations without flow connections.",
        })

    return findings


# SQ06: IATO completeness
def check_sq06_iato_completeness(extraction, findings):
    """
    Advisory check: steps with 3+ null IATO fields are poorly characterised.
    """
    TASK_TYPES = {"task", "user_task", "service_task", "send_task",
                  "receive_task", "manual_task", "business_rule_task"}
    issues = []
    for process in extraction.get("processes", []):
        stage = process.get("stage", "?")
        for step in process.get("steps", []):
            if step.get("element_type") not in TASK_TYPES:
                continue
            iato = step.get("iato") or {}
            null_count = sum(1 for f in ["input", "action", "actor", "output"] if not iato.get(f))
            if null_count >= 3:
                issues.append({
                    "rule": "SQ06",
                    "severity": "ADVISORY",
                    "step_id": step.get("step_id"),
                    "process": stage,
                    "message": f"Step has {null_count}/4 IATO fields null — barely characterised"
                })
    return issues


# SQ07: Subject trace coherence
def check_sq07_subject_trace_coherence(extraction, findings):
    """
    Advisory check: subject traces should start at a start_event and end at an end_event.
    """
    issues = []
    for process in extraction.get("processes", []):
        step_map = {s["step_id"]: s for s in process.get("steps", []) if s.get("step_id")}
        for trace in process.get("subject_traces", []):
            entry_id = trace.get("entry_step_id")
            if entry_id and entry_id in step_map:
                entry_step = step_map[entry_id]
                if entry_step.get("element_type") not in {"start_event", "start"}:
                    issues.append({
                        "rule": "SQ07",
                        "severity": "ADVISORY",
                        "message": f"Subject trace '{trace.get('subject')}' starts at non-start-event {entry_id}"
                    })
            for exit_id in trace.get("exit_step_ids", []):
                if exit_id in step_map:
                    exit_step = step_map[exit_id]
                    if exit_step.get("element_type") not in {"end_event", "end"}:
                        issues.append({
                            "rule": "SQ07",
                            "severity": "ADVISORY",
                            "message": f"Subject trace '{trace.get('subject')}' exits at non-end-event {exit_id}"
                        })
    return issues


# SQ08: Single-source confidence ceiling
def check_sq08_single_source_confidence(extraction, findings):
    """
    Advisory check: steps marked HIGH confidence with only one source should be MEDIUM.
    """
    issues = []
    for process in extraction.get("processes", []):
        for step in process.get("steps", []):
            if step.get("confidence") == "HIGH":
                sources = step.get("sources", [])
                if len(sources) <= 1:
                    issues.append({
                        "rule": "SQ08",
                        "severity": "ADVISORY",
                        "step_id": step.get("step_id"),
                        "message": "Step marked HIGH confidence with only 1 source — should be MEDIUM unless corroborated"
                    })
    return issues


def validate_extraction_quality(
    extraction: dict,
    stages_filter: list[str] | None = None,
    partial_ok: bool = False,
) -> dict:
    processes = extraction.get("processes") or []
    all_findings: list[dict] = []
    stages_checked: list[str] = []
    items_checked = 0

    for proc in processes:
        stage = proc.get("stage", "?")
        if stages_filter and stage not in stages_filter:
            continue

        stages_checked.append(stage)
        steps = proc.get("steps") or []
        stage_sq02_fails = 0
        stage_task_count = 0

        for step in steps:
            et = _get_element_type(step)
            if _is_task_type(et):
                stage_task_count += 1
            items_checked += 1

            all_findings.extend(check_sq01(step, stage))

            sq02_results = check_sq02(step, stage)
            if sq02_results:
                stage_sq02_fails += 1
            all_findings.extend(sq02_results)

            all_findings.extend(check_sq04(step, stage))

        if stage_task_count > 0 and stage_sq02_fails / stage_task_count > 0.3:
            all_findings.append({
                "rule": "SQ02", "severity": "warning", "stage": stage,
                "step_id": None, "title": None,
                "message": f"Stage '{stage}' has {stage_sq02_fails}/{stage_task_count} steps ({100*stage_sq02_fails//stage_task_count}%) matching observation patterns. Suggests systematic misclassification from source material.",
            })

        if not partial_ok:
            all_findings.extend(check_sq03(proc, stage))
            all_findings.extend(check_sq05(proc, stage))

    # SQ06, SQ07, SQ08 run at the full-extraction level (not per-step loop)
    sq06_findings = check_sq06_iato_completeness(extraction, all_findings)
    # Normalise severity casing so the count logic below works consistently
    for f in sq06_findings:
        f["severity"] = f["severity"].lower()
    all_findings.extend(sq06_findings)

    sq07_findings = check_sq07_subject_trace_coherence(extraction, all_findings)
    for f in sq07_findings:
        f["severity"] = f["severity"].lower()
    all_findings.extend(sq07_findings)

    sq08_findings = check_sq08_single_source_confidence(extraction, all_findings)
    for f in sq08_findings:
        f["severity"] = f["severity"].lower()
    all_findings.extend(sq08_findings)

    advisory_count = sum(1 for f in all_findings if f["severity"] == "advisory")
    warning_count = sum(1 for f in all_findings if f["severity"] == "warning")

    if warning_count > 0:
        status = "warning"
    elif advisory_count > 0:
        status = "advisory"
    else:
        status = "pass"

    return {
        "status": status,
        "validator_version": VERSION,
        "stages_checked": stages_checked,
        "items_checked": items_checked,
        "summary": {"advisory": advisory_count, "warning": warning_count},
        "findings": all_findings,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate semantic quality of extraction.json"
    )
    parser.add_argument(
        "--extraction-json", required=True,
        help="Path to extraction.json (or audit-data.json for v2/v3)"
    )
    parser.add_argument(
        "--stages", default=None,
        help="Comma-separated list of stage keys to validate (default: all)"
    )
    parser.add_argument(
        "--partial-ok", action="store_true",
        help="Suppress flow coherence and journey completeness checks"
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    path = Path(args.extraction_json)
    if not path.exists():
        print(json.dumps({"status": "error", "message": f"File not found: {path}"}))
        sys.exit(3)

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(3)

    extraction = data
    if "extraction" in data and isinstance(data["extraction"], dict):
        extraction = data["extraction"]
    if "processes" not in extraction and "processes" in data:
        extraction = data

    stages_filter = None
    if args.stages:
        stages_filter = [s.strip() for s in args.stages.split(",") if s.strip()]

    result = validate_extraction_quality(
        extraction,
        stages_filter=stages_filter,
        partial_ok=args.partial_ok,
    )

    if args.verbose or result["summary"]["warning"] > 0:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))

    if result["summary"]["warning"] > 0:
        sys.exit(2)
    elif result["summary"]["advisory"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
