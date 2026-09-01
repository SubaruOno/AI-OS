#!/usr/bin/env python3
"""Backfill BPMN 2.0 fields on extraction.json for a client.

Reads raw JSON (bypasses audit_reader normalization) to fill:
  - lane_id (role-based, from owner field)
  - element_type (default: task)
  - task_type (default: user_task, with send/receive overrides)
  - annotations (default: [])
  - Converts legacy decision_nodes[] to inline gateway steps
  - Generates sequence_flows[] per process
  - Splits estimating flow at D-005

Usage:
    python3 backfill_bpmn_fields.py --client-slug acme-trades [--dry-run]
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from _paths import get_client_path

OWNER_TO_LANE = {
    "Matt Taylor": "Matt Taylor",
    "Darren Hall": "Darren Hall",
    "Paul Armstrong": "Paul Armstrong",
    "Matt Taylor, Darren Hall": "Matt Taylor",
    "Matt Taylor, Darren Hall, Paul Armstrong": "Matt Taylor",
    "Matt Taylor, Site Supervisors, Paul Armstrong": "Paul Armstrong",
    "Site Supervisors, Paul Armstrong": "Paul Armstrong",
    "Site Supervisors / Project Manager": "Senior Project Manager",
    "Estimating / Operations": "Darren Hall",
    "Operations / Site Supervisors": "Paul Armstrong",
    "Site Supervisors": "Site Supervisors",
    "Site Staff": "Site Supervisors",
    "Equipment Tracker": "Equipment Tracker",
    "External Bookkeeper": "External: Bookkeeper",
    "External H&S Consultant": "External: H&S Consultant",
}

SEND_TASK_STEPS = {"ACQ-012", "ACQ-018", "ACQ-022", "ACQ-023"}
RECEIVE_TASK_STEPS = {"DOC-001", "DOC-002"}

ANNOTATION_DECISION_NODES = {"D-004", "D-006"}
GATEWAY_DECISION_NODES = {"D-001", "D-002", "D-003", "D-005"}


def derive_lane_id(owner):
    if not owner:
        return "Manual"
    owner = owner.strip()
    if owner in OWNER_TO_LANE:
        return OWNER_TO_LANE[owner]
    first = owner.split(",")[0].strip()
    if first in OWNER_TO_LANE:
        return OWNER_TO_LANE[first]
    return first


def backfill_steps(data):
    changes = []
    for proc in data.get("processes", []):
        for step in proc.get("steps", []):
            step_id = step.get("step_id", "")

            old_et = step.get("element_type")
            if old_et == "receiveTask":
                step["element_type"] = "task"
                changes.append(f"  {step_id}: element_type receiveTask -> task")
            elif "element_type" not in step or old_et is None:
                step["element_type"] = "task"
                changes.append(f"  {step_id}: element_type -> task")

            if "lane_id" not in step or step.get("lane_id") is None:
                lane = derive_lane_id(step.get("owner"))
                step["lane_id"] = lane
                changes.append(f"  {step_id}: lane_id -> {lane}")

            if "annotations" not in step or step.get("annotations") is None:
                step["annotations"] = []
                changes.append(f"  {step_id}: annotations -> []")

            if "task_type" not in step or step.get("task_type") is None:
                if step.get("element_type") in ("exclusive_gateway", "parallel_gateway"):
                    pass
                elif step_id in SEND_TASK_STEPS:
                    step["task_type"] = "send_task"
                    changes.append(f"  {step_id}: task_type -> send_task")
                elif step_id in RECEIVE_TASK_STEPS:
                    step["task_type"] = "receive_task"
                    changes.append(f"  {step_id}: task_type -> receive_task")
                else:
                    step["task_type"] = "user_task"
                    changes.append(f"  {step_id}: task_type -> user_task")

    return changes


def convert_decision_nodes(data):
    changes = []
    decision_nodes = data.get("decision_nodes") or []
    if not decision_nodes:
        return changes

    step_lookup = {}
    for proc in data.get("processes", []):
        for step in proc.get("steps", []):
            step_lookup[step["step_id"]] = (proc, step)

    for dn in decision_nodes:
        node_id = dn.get("node_id", "")
        after_step = dn.get("after_step_id", "")
        condition = dn.get("condition", "")

        if node_id in ANNOTATION_DECISION_NODES:
            if after_step in step_lookup:
                _, target_step = step_lookup[after_step]
                desc = target_step.get("description", "")
                annotation_text = f"\n[Decision: {condition}] Yes: {dn.get('yes_path', '')} / No: {dn.get('no_path', '')}"
                target_step["description"] = desc + annotation_text
                changes.append(f"  {node_id}: merged as annotation into {after_step}")
            continue

        if node_id not in GATEWAY_DECISION_NODES:
            continue

        if after_step not in step_lookup:
            changes.append(f"  {node_id}: SKIP - after_step {after_step} not found")
            continue

        proc, anchor_step = step_lookup[after_step]
        gw_num = node_id.split("-")[1]
        gw_id = f"ACQ-GW-{gw_num}"

        sources = []
        src_entry = {
            "quote": dn.get("source_quote", ""),
            "speaker": dn.get("owner", ""),
            "confidence": dn.get("confidence", "HIGH"),
        }
        session_raw = dn.get("source_session")
        ts_raw = dn.get("source_timestamp_seconds")
        if session_raw is not None and str(session_raw) != "None":
            src_entry["kind"] = "fathom"
            src_entry["session_id"] = int(session_raw)
            if ts_raw is not None and str(ts_raw) != "None":
                src_entry["timestamp_seconds"] = int(ts_raw)
        else:
            src_entry["kind"] = "document"
            src_entry["document_path"] = "decision_node_migration"
        sources.append(src_entry)

        gw_step = {
            "step_id": gw_id,
            "element_type": "exclusive_gateway",
            "annotations": [],
            "label": condition,
            "description": condition,
            "owner": dn.get("owner", ""),
            "lane_id": derive_lane_id(dn.get("owner", "")),
            "flow_id": anchor_step.get("flow_id"),
            "confidence": dn.get("confidence", "HIGH"),
            "sources": sources,
        }

        steps = proc.get("steps", [])
        insert_idx = None
        for i, s in enumerate(steps):
            if s["step_id"] == after_step:
                insert_idx = i + 1
                break
        if insert_idx is not None:
            steps.insert(insert_idx, gw_step)
            step_lookup[gw_id] = (proc, gw_step)
            changes.append(f"  {node_id}: inserted gateway {gw_id} after {after_step}")
        else:
            changes.append(f"  {node_id}: SKIP - insertion point not found")

    return changes


def build_sequence_flows(data):
    changes = []
    decision_nodes = data.get("decision_nodes") or []
    dn_lookup = {dn.get("node_id", ""): dn for dn in decision_nodes}

    for proc in data.get("processes", []):
        stage = proc["stage"]
        existing = proc.get("sequence_flows")
        if existing and len(existing) > 0:
            changes.append(f"  {stage}: already has {len(existing)} flows, skipping")
            continue

        steps = proc.get("steps", [])
        if len(steps) < 2:
            continue

        flows_by_fid = {}
        for s in steps:
            fid = s.get("flow_id") or "__main__"
            flows_by_fid.setdefault(fid, []).append(s)

        all_flows = []
        seen = set()

        def add_flow(src_id, tgt_id, condition=None):
            key = (src_id, tgt_id, condition)
            if key not in seen:
                seen.add(key)
                f = {"from": src_id, "to": tgt_id}
                if condition:
                    f["condition"] = condition
                all_flows.append(f)

        for fid, fsteps in flows_by_fid.items():
            gw_ids = {s["step_id"] for s in fsteps if s.get("element_type") == "exclusive_gateway"}
            gw_after_map = {}
            for s in fsteps:
                if s.get("element_type") == "exclusive_gateway":
                    gw_num = s["step_id"].split("-")[-1]
                    dn_id = f"D-{gw_num}"
                    dn = dn_lookup.get(dn_id)
                    if dn:
                        gw_after_map[dn.get("after_step_id", "")] = s["step_id"]

            for i in range(len(fsteps) - 1):
                src = fsteps[i]
                tgt = fsteps[i + 1]
                src_id = src["step_id"]
                tgt_id = tgt["step_id"]

                if src_id in gw_after_map:
                    gw_id = gw_after_map[src_id]
                    add_flow(src_id, gw_id)

                    gw_num = gw_id.split("-")[-1]
                    dn = dn_lookup.get(f"D-{gw_num}")
                    if dn:
                        yes_ids = dn.get("yes_branch_step_ids")
                        if isinstance(yes_ids, str):
                            try:
                                yes_ids = json.loads(yes_ids.replace("'", '"'))
                            except (json.JSONDecodeError, ValueError):
                                yes_ids = []
                        no_ids = dn.get("no_branch_step_ids")
                        if isinstance(no_ids, str):
                            try:
                                no_ids = json.loads(no_ids.replace("'", '"'))
                            except (json.JSONDecodeError, ValueError):
                                no_ids = []

                        gw_idx = next((j for j, st in enumerate(fsteps) if st["step_id"] == gw_id), None)
                        if yes_ids:
                            add_flow(gw_id, yes_ids[0], "Yes")
                        elif gw_idx is not None and gw_idx + 1 < len(fsteps):
                            next_after_gw = fsteps[gw_idx + 1]
                            if next_after_gw.get("element_type") != "exclusive_gateway":
                                add_flow(gw_id, next_after_gw["step_id"], "Yes")

                        if no_ids:
                            add_flow(gw_id, no_ids[0], "No")
                        else:
                            no_text = (dn.get("no_path") or "").lower()
                            if "end" in no_text or "decline" in no_text:
                                pass
                    continue

                if src.get("element_type") == "exclusive_gateway":
                    continue

                add_flow(src_id, tgt_id)

        proc["sequence_flows"] = all_flows
        changes.append(f"  {stage}: generated {len(all_flows)} sequence flows")

    return changes


def split_estimating_at_d005(data):
    changes = []
    acq = None
    for proc in data.get("processes", []):
        if proc["stage"] == "acquisition":
            acq = proc
            break
    if not acq:
        return changes

    flows = acq.get("flows") or []
    branch_steps = {"ACQ-020", "ACQ-021"}
    handover_steps = {"ACQ-007"}
    all_handover = branch_steps | handover_steps

    for step in acq.get("steps", []):
        if step["step_id"] in all_handover:
            old_fid = step.get("flow_id")
            step["flow_id"] = "acquisition_estimating_handover"
            changes.append(f"  {step['step_id']}: flow_id {old_fid} -> acquisition_estimating_handover")

    for f in flows:
        if "estimating" in f.get("label", "").lower():
            old_ids = f.get("step_ids", [])
            f["step_ids"] = [sid for sid in old_ids if sid not in branch_steps]
            if old_ids != f["step_ids"]:
                changes.append(f"  Updated estimating flow step_ids (removed post-award steps)")

    existing_labels = {f.get("label", "").lower() for f in flows}
    if "post-award handover" not in existing_labels:
        flows.append({
            "label": "Post-Award Handover",
            "cadence": "Per awarded tender",
            "step_ids": sorted(list(all_handover)),
        })
        acq["flows"] = flows
        changes.append("  Added 'Post-Award Handover' flow")

    return changes


def run(client_slug, dry_run=False):
    print(f"Backfilling BPMN fields for: {client_slug}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    client_path = get_client_path(client_slug)
    ext_path = client_path / "audit" / "extraction.json"
    findings_path = client_path / "audit" / "findings.json"
    manifest_path = client_path / "audit" / "audit-manifest.json"

    if not ext_path.exists():
        print(f"ERROR: {ext_path} not found")
        sys.exit(1)

    with open(ext_path) as f:
        data = json.load(f)

    print("=== Step backfill ===")
    step_changes = backfill_steps(data)
    for c in step_changes:
        print(c)
    print(f"Total: {len(step_changes)} changes")

    print("\n=== Decision node conversion ===")
    dn_changes = convert_decision_nodes(data)
    for c in dn_changes:
        print(c)
    print(f"Total: {len(dn_changes)} changes")

    print("\n=== Sequence flow generation ===")
    sf_changes = build_sequence_flows(data)
    for c in sf_changes:
        print(c)

    print("\n=== Estimating flow split at D-005 ===")
    split_changes = split_estimating_at_d005(data)
    for c in split_changes:
        print(c)

    total = len(step_changes) + len(dn_changes) + len(sf_changes) + len(split_changes)
    print(f"\nTotal changes: {total}")

    if dry_run:
        print("\nDRY RUN complete. No files written.")
        return

    if total == 0:
        print("\nNo changes needed.")
        return

    print("\nWriting extraction.json...")
    with open(ext_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Written: {ext_path}")

    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest = json.load(f)
        now = datetime.now(timezone.utc).isoformat()
        manifest["updated_at"] = now
        if "domains" in manifest and "extraction" in manifest["domains"]:
            manifest["domains"]["extraction"]["updated_at"] = now
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"  Updated manifest: {manifest_path}")

    print("Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill BPMN fields on extraction.json")
    parser.add_argument("--client-slug", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(args.client_slug, args.dry_run)
