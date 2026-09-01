#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""
validate_bpmn_json.py — Validates BPMN structural integrity of extraction.json.

Checks process graph connectivity, event uniqueness, flow references, gateway
branching, and lane assignments at the JSON level (before BPMN XML generation).

Usage:
  python3 validate_bpmn_json.py --extraction-json path/to/extraction.json [--partial-ok] [--verbose]

Exit codes:
  0 — pass (no HIGH severity findings)
  1 — fail (HIGH severity findings present)
  2 — error (file not found, invalid JSON, etc.)
"""

import argparse
import json
import sys
from pathlib import Path

_START_TYPES = {"start_event", "start"}
_END_TYPES = {"end_event", "end"}
_EVENT_TYPES = _START_TYPES | _END_TYPES


def _get_element_type(step: dict) -> str:
    return step.get("element_type") or step.get("type", "task")


def validate_bpmn_json(extraction: dict, partial_ok: bool = False) -> list[dict]:
    findings: list[dict] = []
    processes = extraction.get("processes") or []

    all_step_ids_by_stage: dict[str, str] = {}
    for proc in processes:
        stage = proc.get("stage", "?")
        for s in proc.get("steps", []):
            sid = s.get("step_id", "")
            if sid:
                all_step_ids_by_stage[sid] = stage

    for pi, proc in enumerate(processes):
        stage = proc.get("stage", "?")
        prefix = f"processes[{pi}]"
        steps = proc.get("steps") or []
        flows = proc.get("sequence_flows") or []
        lanes = proc.get("lanes") or []
        step_ids = {s.get("step_id", "") for s in steps if s.get("step_id")}

        # BJ05: No duplicate step_ids within a process
        seen_ids: dict[str, int] = {}
        for s in steps:
            sid = s.get("step_id", "")
            if sid:
                seen_ids[sid] = seen_ids.get(sid, 0) + 1
        for sid, count in seen_ids.items():
            if count > 1:
                findings.append({
                    "severity": "high", "process": stage, "rule": "BJ05",
                    "field": f"{prefix}.steps",
                    "message": f"Duplicate step_id '{sid}' appears {count} times in process '{stage}'"
                })

        # BJ01: At most one start event (BLOCKER — a process with multiple start events cannot be walked)
        start_steps = [s for s in steps if _get_element_type(s) in _START_TYPES]
        if len(start_steps) > 1:
            ids = [s.get("step_id", "?") for s in start_steps]
            findings.append({
                "severity": "blocker", "process": stage, "rule": "BJ01",
                "field": f"{prefix}.steps",
                "message": f"Multiple start events ({len(start_steps)}) in process '{stage}': {ids}"
            })

        # BJ02: At least one end event (BLOCKER — multiple end events are valid BPMN 2.0 for processes with distinct terminal outcomes)
        end_steps = [s for s in steps if _get_element_type(s) in _END_TYPES]
        if len(end_steps) == 0:
            findings.append({
                "severity": "blocker", "process": stage, "rule": "BJ02",
                "field": f"{prefix}.steps",
                "message": f"No end event found in process '{stage}' — every process must have at least one end event"
            })

        # BJ09: No duplicate sequence_flow IDs
        seen_flow_ids: dict[str, int] = {}
        for f in flows:
            fid = f.get("id", "")
            if fid:
                seen_flow_ids[fid] = seen_flow_ids.get(fid, 0) + 1
        for fid, count in seen_flow_ids.items():
            if count > 1:
                findings.append({
                    "severity": "medium", "process": stage, "rule": "BJ09",
                    "field": f"{prefix}.sequence_flows",
                    "message": f"Duplicate sequence_flow id '{fid}' appears {count} times in '{stage}'"
                })

        # BJ03/BJ04: Flow references
        for fi, f in enumerate(flows):
            f_from = f.get("from", "")
            f_to = f.get("to", "")
            fid = f.get("id", f"flow[{fi}]")

            if f_from and f_from not in step_ids:
                if f_from in all_step_ids_by_stage:
                    other_stage = all_step_ids_by_stage[f_from]
                    findings.append({
                        "severity": "medium", "process": stage, "rule": "BJ03",
                        "field": f"{prefix}.sequence_flows[{fi}]",
                        "message": f"Flow '{fid}' source '{f_from}' is in process '{other_stage}', not '{stage}' (cross-process flow)"
                    })
                else:
                    findings.append({
                        "severity": "high", "process": stage, "rule": "BJ03",
                        "field": f"{prefix}.sequence_flows[{fi}]",
                        "message": f"Flow '{fid}' source '{f_from}' not found in any process"
                    })

            if f_to and f_to not in step_ids:
                if f_to in all_step_ids_by_stage:
                    other_stage = all_step_ids_by_stage[f_to]
                    findings.append({
                        "severity": "medium", "process": stage, "rule": "BJ04",
                        "field": f"{prefix}.sequence_flows[{fi}]",
                        "message": f"Flow '{fid}' target '{f_to}' is in process '{other_stage}', not '{stage}' (cross-process flow)"
                    })
                else:
                    findings.append({
                        "severity": "high", "process": stage, "rule": "BJ04",
                        "field": f"{prefix}.sequence_flows[{fi}]",
                        "message": f"Flow '{fid}' target '{f_to}' not found in any process"
                    })

        if partial_ok and (len(steps) < 3 or not flows):
            continue

        # BJ06: Every non-event step has at least one incoming flow
        if not partial_ok and flows:
            incoming = {f.get("to") for f in flows if f.get("to") in step_ids}
            for s in steps:
                sid = s.get("step_id", "")
                et = _get_element_type(s)
                if et in _START_TYPES:
                    continue
                if sid and sid not in incoming:
                    findings.append({
                        "severity": "medium", "process": stage, "rule": "BJ06",
                        "field": f"{prefix}.steps",
                        "message": f"Step '{sid}' in '{stage}' has no incoming sequence flow (orphan sink)"
                    })

            # Also check outgoing
            outgoing = {f.get("from") for f in flows if f.get("from") in step_ids}
            for s in steps:
                sid = s.get("step_id", "")
                et = _get_element_type(s)
                if et in _END_TYPES:
                    continue
                if sid and sid not in outgoing:
                    findings.append({
                        "severity": "medium", "process": stage, "rule": "BJ06",
                        "field": f"{prefix}.steps",
                        "message": f"Step '{sid}' in '{stage}' has no outgoing sequence flow (orphan source)"
                    })

        # BJ07: Exclusive gateways have 2+ outgoing flows
        if not partial_ok:
            outgoing_counts: dict[str, int] = {}
            for f in flows:
                src = f.get("from", "")
                if src:
                    outgoing_counts[src] = outgoing_counts.get(src, 0) + 1
            for s in steps:
                sid = s.get("step_id", "")
                et = _get_element_type(s)
                if et == "exclusive_gateway" and outgoing_counts.get(sid, 0) < 2:
                    findings.append({
                        "severity": "medium", "process": stage, "rule": "BJ07",
                        "field": f"{prefix}.steps",
                        "message": f"Exclusive gateway '{sid}' in '{stage}' has {outgoing_counts.get(sid, 0)} outgoing flow(s), need 2+"
                    })

        # BJ08: Lane assignment matches lanes[] (only when lanes is non-empty)
        if not partial_ok and lanes:
            lane_ids = {l.get("id") or l.get("name", "") for l in lanes}
            for s in steps:
                lid = s.get("lane_id", "")
                if lid and lid not in lane_ids:
                    findings.append({
                        "severity": "medium", "process": stage, "rule": "BJ08",
                        "field": f"{prefix}.steps",
                        "message": f"Step '{s.get('step_id', '?')}' lane_id '{lid}' not in lanes[] of '{stage}'"
                    })

        # BJ10: Parallel gateway fork/join pairing
        if not partial_ok:
            pg_steps = [s for s in steps if _get_element_type(s) == "parallel_gateway"]
            if len(pg_steps) >= 2:
                outgoing_counts_pg: dict[str, int] = {}
                incoming_counts_pg: dict[str, int] = {}
                for f in flows:
                    src = f.get("from", "")
                    tgt = f.get("to", "")
                    if src:
                        outgoing_counts_pg[src] = outgoing_counts_pg.get(src, 0) + 1
                    if tgt:
                        incoming_counts_pg[tgt] = incoming_counts_pg.get(tgt, 0) + 1
                forks = sum(1 for s in pg_steps if outgoing_counts_pg.get(s.get("step_id", ""), 0) >= 2)
                joins = sum(1 for s in pg_steps if incoming_counts_pg.get(s.get("step_id", ""), 0) >= 2)
                if forks != joins:
                    findings.append({
                        "severity": "low", "process": stage, "rule": "BJ10",
                        "field": f"{prefix}.steps",
                        "message": f"Parallel gateway imbalance in '{stage}': {forks} fork(s), {joins} join(s)"
                    })

    # BJ11, BJ14, BJ15, BJ16: Walkability checks
    if not partial_ok:
        findings.extend(check_process_walkability(processes))

    return findings


# BJ11: Gateway anatomy completeness
def check_bj11_gateway_anatomy(processes):
    """
    MEDIUM: Every exclusive_gateway should have at least 'condition' in gateway_anatomy.
    """
    issues = []
    for process in processes:
        for step in process.get("steps", []):
            if step.get("element_type") in {"exclusive_gateway", "decision"}:
                anatomy = step.get("gateway_anatomy") or {}
                if not anatomy.get("condition"):
                    issues.append({
                        "rule": "BJ11",
                        "severity": "medium",
                        "step_id": step.get("step_id"),
                        "process": process.get("stage", "?"),
                        "message": "Exclusive gateway has no condition in gateway_anatomy"
                    })
    return issues


# BJ14: Every non-start/end node has a lane_id
def check_bj14_lane_assignment(processes):
    """
    HIGH: Every task/gateway must have a lane_id assigned.
    """
    MUST_HAVE_LANE = {
        "task", "user_task", "service_task", "send_task", "receive_task",
        "manual_task", "business_rule_task", "exclusive_gateway", "parallel_gateway"
    }
    issues = []
    for process in processes:
        lanes = {l["id"] for l in process.get("lanes", [])}
        if not lanes:
            continue  # skip processes without lane definitions
        for step in process.get("steps", []):
            if step.get("element_type") in MUST_HAVE_LANE:
                lane_id = step.get("lane_id")
                if not lane_id:
                    issues.append({
                        "rule": "BJ14",
                        "severity": "high",
                        "step_id": step.get("step_id"),
                        "process": process.get("stage", "?"),
                        "message": "Step has no lane_id assigned"
                    })
    return issues


# BJ15: Every exclusive gateway has labelled outgoing flows
def check_bj15_gateway_labelled_flows(processes):
    """
    HIGH: Every outgoing flow from an exclusive_gateway must have a condition label.
    """
    issues = []
    for process in processes:
        gateways = {
            s["step_id"]: s for s in process.get("steps", [])
            if s.get("element_type") in {"exclusive_gateway", "decision"}
        }
        for flow in process.get("sequence_flows", []):
            if flow.get("from") in gateways:
                if not flow.get("condition"):
                    default_flow = gateways[flow["from"]].get("default_flow_id")
                    if flow.get("id") != default_flow:
                        issues.append({
                            "rule": "BJ15",
                            "severity": "high",
                            "flow_id": flow.get("id"),
                            "process": process.get("stage", "?"),
                            "message": f"Outgoing flow from gateway {flow['from']} has no condition label"
                        })
    return issues


# BJ16: No dead ends (non-end steps must have outgoing flows)
def check_bj16_no_dead_ends(processes):
    """
    HIGH: Every step except end_events must have at least one outgoing sequence flow.
    """
    END_TYPES = {"end_event", "end"}
    issues = []
    for process in processes:
        steps_with_outflow = {f.get("from") for f in process.get("sequence_flows", [])}
        for step in process.get("steps", []):
            if step.get("element_type") not in END_TYPES:
                if step.get("step_id") not in steps_with_outflow:
                    issues.append({
                        "rule": "BJ16",
                        "severity": "high",
                        "step_id": step.get("step_id"),
                        "process": process.get("stage", "?"),
                        "message": "Step has no outgoing sequence flows — dead end"
                    })
    return issues


def check_bj17_forward_reachability(processes):
    """HIGH: Every step must be reachable from the start event via sequence flows."""
    issues = []
    for process in processes:
        steps = process.get("steps") or []
        flows = process.get("sequence_flows") or []
        step_ids = {s.get("step_id") for s in steps if s.get("step_id")}
        starts = [s["step_id"] for s in steps if _get_element_type(s) in _START_TYPES]
        if not starts or len(step_ids) < 2:
            continue
        adj: dict[str, list[str]] = {}
        for f in flows:
            src, tgt = f.get("from", ""), f.get("to", "")
            if src in step_ids and tgt in step_ids:
                adj.setdefault(src, []).append(tgt)
        visited: set[str] = set()
        queue = list(starts)
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            queue.extend(adj.get(node, []))
        unreachable = step_ids - visited
        for sid in sorted(unreachable):
            issues.append({
                "rule": "BJ17", "severity": "high",
                "step_id": sid, "process": process.get("stage", "?"),
                "message": f"Step '{sid}' is not reachable from any start event"
            })
    return issues


def check_bj18_backward_reachability(processes):
    """HIGH: Every step must have a path to at least one end event."""
    issues = []
    for process in processes:
        steps = process.get("steps") or []
        flows = process.get("sequence_flows") or []
        step_ids = {s.get("step_id") for s in steps if s.get("step_id")}
        ends = [s["step_id"] for s in steps if _get_element_type(s) in _END_TYPES]
        if not ends or len(step_ids) < 2:
            continue
        rev_adj: dict[str, list[str]] = {}
        for f in flows:
            src, tgt = f.get("from", ""), f.get("to", "")
            if src in step_ids and tgt in step_ids:
                rev_adj.setdefault(tgt, []).append(src)
        visited: set[str] = set()
        queue = list(ends)
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            queue.extend(rev_adj.get(node, []))
        unreachable = step_ids - visited
        for sid in sorted(unreachable):
            issues.append({
                "rule": "BJ18", "severity": "high",
                "step_id": sid, "process": process.get("stage", "?"),
                "message": f"Step '{sid}' has no path to any end event"
            })
    return issues


def check_process_walkability(processes):
    """
    Run all walkability checks (BJ11, BJ14, BJ15, BJ16, BJ17, BJ18) and return combined findings.
    When audit_status is 'process_map_complete', any HIGH or BLOCKER finding from these
    rules should prevent the status change.
    """
    issues = []
    issues.extend(check_bj11_gateway_anatomy(processes))
    issues.extend(check_bj14_lane_assignment(processes))
    issues.extend(check_bj15_gateway_labelled_flows(processes))
    issues.extend(check_bj16_no_dead_ends(processes))
    issues.extend(check_bj17_forward_reachability(processes))
    issues.extend(check_bj18_backward_reachability(processes))
    return issues


def main():
    parser = argparse.ArgumentParser(description="Validate BPMN structure in extraction.json")
    parser.add_argument("--extraction-json", required=True, help="Path to extraction.json")
    parser.add_argument("--partial-ok", action="store_true",
                        help="Suppress connectivity checks for partial extractions")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    path = Path(args.extraction_json)
    if not path.exists():
        print(json.dumps({"status": "error", "message": f"File not found: {path}"}))
        sys.exit(2)

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(2)

    extraction = data
    if "extraction" in data and isinstance(data["extraction"], dict):
        extraction = data["extraction"]
    if "processes" not in extraction and "processes" in data:
        extraction = data

    findings = validate_bpmn_json(extraction, partial_ok=args.partial_ok)

    blocker_count = sum(1 for f in findings if f["severity"] == "blocker")
    high_count = sum(1 for f in findings if f["severity"] == "high")
    medium_count = sum(1 for f in findings if f["severity"] == "medium")
    low_count = sum(1 for f in findings if f["severity"] == "low")

    fail = blocker_count > 0 or high_count > 0
    result = {
        "status": "fail" if fail else "pass",
        "file": str(path),
        "summary": {"blocker": blocker_count, "high": high_count, "medium": medium_count, "low": low_count},
        "findings": findings,
    }

    if args.verbose or fail:
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(result))

    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
