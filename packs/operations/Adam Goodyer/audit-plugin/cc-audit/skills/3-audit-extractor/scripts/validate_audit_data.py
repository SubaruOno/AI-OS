#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""
validate-audit-data.py — Validates the audit data JSON file.

Usage:
  python3 validate_audit_data.py --file clients/slug/audit/audit-data.json [--verbose]

Exit codes:
  0 — pass (no critical or high severity findings)
  1 — fail (critical or high severity findings present)
  2 — error (file not found, invalid JSON, etc.)
"""

import argparse
import json
import re
import sys
from pathlib import Path

import sys as _sys
_reader_path = str(Path(__file__).resolve().parent.parent.parent.parent / "scripts")
if _reader_path not in _sys.path:
    _sys.path.insert(0, _reader_path)
from audit_reader import load_all, detect_version, flatten, is_v3


def load_audit_data(file_path: str) -> dict:
    """Load audit data from a file path. Supports v2, v3, and v4 formats."""
    audit_dir = Path(file_path).parent
    if (audit_dir / "audit-manifest.json").exists():
        # v4 — derive slug from path: clients/{slug}/audit/
        slug = audit_dir.parent.name
        try:
            return load_all(slug)
        except FileNotFoundError as e:
            print(json.dumps({"status": "error", "message": str(e)}))
            sys.exit(2)
    # v2 or v3 — load single file
    path = Path(file_path)
    if not path.exists():
        print(json.dumps({"status": "error", "message": f"File not found: {file_path}"}))
        sys.exit(2)
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(2)
    if is_v3(data):
        return flatten(data)
    return data


def validate(ssad: dict) -> list[dict]:
    findings = []

    def add(severity, field, message):
        findings.append({"severity": severity, "field": field, "message": message})

    def check_sources(item: dict, prefix: str):
        """Source Attribution Gate enforcement (sources[] invariant).

        HIGH: `sources[]` is missing or empty — true orphan. The item has no
          way to be cited and cannot satisfy the client's #1 objection
          ("where did you get this from?"). Fails the build (exit code 1).

        MEDIUM: `sources[]` is present and non-empty but at least one entry
          is malformed (missing kind/quote/speaker/confidence, or missing
          kind-specific required fields like session_id for fathom or
          document_path for document).

        Items reach this check after audit_reader.py has normalized legacy
        flat fields into `sources[]`, so failure here usually means the item
        has no quote AND no document AND no session — a true orphan.
        """
        sources = item.get("sources")
        if not isinstance(sources, list) or len(sources) == 0:
            add("high", f"{prefix}.sources",
                "Item is a true orphan — sources[] is empty or missing. Cannot show "
                "client where this came from. Move to follow_up_questions[] or supply "
                "a valid sources[] entry.")
            return
        for si, src in enumerate(sources):
            sprefix = f"{prefix}.sources[{si}]"
            if not isinstance(src, dict):
                add("medium", sprefix, "Source entry must be an object")
                continue
            kind = src.get("kind")
            if kind not in ("fathom", "document"):
                add("medium", f"{sprefix}.kind",
                    f"kind must be 'fathom' or 'document', got: '{kind}'")
            quote = src.get("quote")
            if not (isinstance(quote, str) and quote.strip()):
                add("medium", f"{sprefix}.quote", "Source entry missing verbatim quote")
            confidence = src.get("confidence")
            if confidence not in ("HIGH", "MEDIUM", "LOW"):
                add("low", f"{sprefix}.confidence",
                    f"confidence must be HIGH | MEDIUM | LOW, got: '{confidence}'")
            if kind == "fathom":
                if not isinstance(src.get("session_id"), int):
                    add("medium", f"{sprefix}.session_id",
                        "Fathom source missing integer session_id (cannot resolve recording URL)")
                if not isinstance(src.get("timestamp_seconds"), (int, float)):
                    add("medium", f"{sprefix}.timestamp_seconds",
                        "Fathom source missing timestamp_seconds (cannot deep-link)")
                if not src.get("speaker"):
                    add("medium", f"{sprefix}.speaker",
                        "Fathom source missing speaker attribution")
            elif kind == "document":
                doc = src.get("document_path")
                if not (isinstance(doc, str) and doc.strip()):
                    add("medium", f"{sprefix}.document_path",
                        "Document source missing document_path")

    # --- Schema version ---
    schema_version = ssad.get("_schema_version")
    if not schema_version:
        add("low", "_schema_version", "No _schema_version field — add '2.0.0' for schema governance")

    # --- Required top-level fields ---
    # blended_rate_confidence is no longer required; the blended rate is fixed at $50/hr by convention.
    required_fields = [
        "client_slug", "company_name", "industry_tag", "audit_status",
        "contact", "blended_hourly_rate_aud",
        "processes", "waste_items", "completeness_checklist", "sessions"
    ]
    for field in required_fields:
        if field not in ssad:
            add("critical", field, f"Required field '{field}' is missing")

    # --- Contact block ---
    contact = ssad.get("contact", {})
    if not contact.get("name"):
        add("high", "contact.name", "Contact name is empty")
    if not contact.get("role"):
        add("medium", "contact.role", "Contact role is empty")

    # --- Blended hourly rate ---
    # Canonical assumed blended team rate. Fixed at $50/hr by convention. Never derived from per-staff pay.
    rate = ssad.get("blended_hourly_rate_aud")
    if rate is None:
        add("high", "blended_hourly_rate_aud", "Blended hourly rate is null. Set it to 50 (canonical assumed blended team rate).")
    elif not isinstance(rate, (int, float)) or rate <= 0:
        add("high", "blended_hourly_rate_aud", f"Blended hourly rate must be a positive number, got: {rate}")

    # --- Audit status ---
    valid_statuses = ("in_progress", "process_map_complete")
    audit_status = ssad.get("audit_status", "")
    if audit_status not in valid_statuses:
        add("medium", "audit_status", f"audit_status must be one of {valid_statuses}, got: '{audit_status}'")

    # --- Processes ---
    processes = ssad.get("processes", [])
    valid_step_types = ("step", "decision", "pain", "optimisation", "automation", "parallel_group")
    valid_element_types = ("task", "exclusive_gateway", "parallel_gateway",
                           "intermediate_catch_event", "intermediate_throw_event")
    valid_event_definitions = ("timer", "message", "error", "signal")
    valid_confidence = ("HIGH", "MEDIUM", "LOW")

    if not isinstance(processes, list):
        add("critical", "processes", "processes must be an array")
    else:
        seen_stages = set()
        for i, process in enumerate(processes):
            stage = process.get("stage", "")
            if not stage:
                add("critical", f"processes[{i}].stage", "Stage key is empty")
            elif not re.match(r'^[a-z][a-z0-9_]*$', stage):
                add("medium", f"processes[{i}].stage", f"Stage key '{stage}' should be snake_case")
            elif stage in seen_stages:
                add("high", f"processes[{i}].stage", f"Duplicate stage '{stage}'")
            else:
                seen_stages.add(stage)
            if not process.get("name"):
                add("low", f"processes[{i}].name", f"Missing display name for stage '{stage}'")
            steps = process.get("steps", [])
            if not isinstance(steps, list):
                add("high", f"processes[{i}].steps", "steps must be an array")
                continue
            for j, step in enumerate(steps):
                if not step.get("description"):
                    add("high", f"processes[{i}].steps[{j}].description", "Step description is empty")
                element_type = step.get("element_type", "")
                step_type = step.get("type", "")
                if element_type:
                    if element_type not in valid_element_types:
                        add("medium", f"processes[{i}].steps[{j}].element_type", f"Invalid element_type '{element_type}'")
                    event_def = step.get("event_definition")
                    if event_def and event_def not in valid_event_definitions:
                        add("medium", f"processes[{i}].steps[{j}].event_definition", f"Invalid event_definition '{event_def}'")
                elif step_type and step_type not in valid_step_types:
                    add("medium", f"processes[{i}].steps[{j}].type", f"Invalid step type '{step_type}'")
                if step.get("confidence", "") not in valid_confidence:
                    add("medium", f"processes[{i}].steps[{j}].confidence", "confidence must be HIGH, MEDIUM, or LOW")
                check_sources(step, f"processes[{i}].steps[{j}]")
                annotations = step.get("annotations") or []
                if "pain" in annotations or "optimisation" in annotations:
                    title_lower = (step.get("title") or step.get("label") or "").lower()
                    obs_patterns = ("no ", "lack of", "missing", "absence of", "misalignment", "inconsisten", "gap in", "siloed")
                    for pattern in obs_patterns:
                        if title_lower.startswith(pattern) or f" {pattern}" in title_lower:
                            add("low", f"processes[{i}].steps[{j}].title",
                                f"Step title '{step.get('title') or step.get('label')}' matches observation patterns for annotation {annotations}. Consider running process review (PR) to evaluate reclassification as a finding.")
                            break
                depends_on = step.get("depends_on_step_id")
                if depends_on is not None and not isinstance(depends_on, str):
                    add("low", f"processes[{i}].steps[{j}].depends_on_step_id", "depends_on_step_id must be a string or null")

    # --- Waste items ---
    waste_items = ssad.get("waste_items", [])
    valid_waste_types = ("manual_data_entry", "manual_processing", "duplicate_work", "duplication", "no_followup", "communication_gap", "missing_automation", "unrealized_revenue")

    if not isinstance(waste_items, list):
        add("critical", "waste_items", "waste_items must be an array")
    else:
        for i, item in enumerate(waste_items):
            if not item.get("activity"):
                add("high", f"waste_items[{i}].activity", "Waste item activity description is empty")
            conf = item.get("confidence", "")
            if conf not in valid_confidence:
                add("medium", f"waste_items[{i}].confidence", "confidence must be HIGH, MEDIUM, or LOW")
            if conf in ("HIGH", "MEDIUM"):
                if item.get("annual_waste_aud") is None:
                    add("high", f"waste_items[{i}].annual_waste_aud",
                        f"HIGH/MEDIUM confidence opportunity '{item.get('activity', 'unknown')}' has no annual_waste_aud — run waste calculator")
                if item.get("hours_per_week") is None:
                    add("medium", f"waste_items[{i}].hours_per_week",
                        f"Opportunity '{item.get('activity', 'unknown')}' has no hours_per_week — calculation unverifiable")
            check_sources(item, f"waste_items[{i}]")
            waste_type = item.get("waste_type", "")
            if waste_type and waste_type not in valid_waste_types:
                add("low", f"waste_items[{i}].waste_type", f"Invalid waste_type '{waste_type}'")

    # --- Must have at least one HIGH confidence waste item if audit is beyond in_progress ---
    if audit_status == "process_map_complete":
        high_waste = [w for w in waste_items if w.get("confidence") == "HIGH"]
        if not high_waste:
            add("high", "waste_items", "No HIGH confidence opportunities — audit report cannot proceed without verified opportunity data")

    # --- Tools ---
    tools = ssad.get("tools", [])
    valid_integration_openness = ("open", "partial", "closed", "unknown")
    if isinstance(tools, list):
        for i, tool in enumerate(tools):
            if not tool.get("tool_name"):
                add("high", f"tools[{i}].tool_name", "Tool has no name")
            if not tool.get("source_quote") and not tool.get("quote"):
                add("low", f"tools[{i}].source_quote", "Tool has no source citation")
            openness = tool.get("integration_openness")
            if openness is not None and openness not in valid_integration_openness:
                add("medium", f"tools[{i}].integration_openness", f"integration_openness must be one of {valid_integration_openness}, got: '{openness}'")
            if tool.get("api_available") is True and not tool.get("api_docs_url"):
                add("low", f"tools[{i}].api_docs_url", "api_available is true but api_docs_url is empty — add the documentation URL")
            if tool.get("mcp_available") is True and not tool.get("mcp_url"):
                add("low", f"tools[{i}].mcp_url", "mcp_available is true but mcp_url is empty — add the MCP server URL")

    # --- Pain points ---
    pain_points = ssad.get("pain_points", [])
    if isinstance(pain_points, list):
        for i, pp in enumerate(pain_points):
            if not pp.get("pain_point_id"):
                add("high", f"pain_points[{i}].pain_point_id", "Pain point has no ID")
            if not pp.get("description"):
                add("high", f"pain_points[{i}].description", "Pain point has no description")
            if not pp.get("stage"):
                add("medium", f"pain_points[{i}].stage", "Pain point has no stage")
            check_sources(pp, f"pain_points[{i}]")
            # FR-written fields — validate types if present, accept null
            related_waste = pp.get("related_waste_ids")
            if related_waste is not None and not isinstance(related_waste, list):
                add("low", f"pain_points[{i}].related_waste_ids", "related_waste_ids must be an array or null")
            related_opts = pp.get("related_optimisation_ids")
            if related_opts is not None and not isinstance(related_opts, list):
                add("low", f"pain_points[{i}].related_optimisation_ids", "related_optimisation_ids must be an array or null")

    # --- Optimisations ---
    optimisations = ssad.get("optimisations", [])
    if isinstance(optimisations, list):
        for i, opt in enumerate(optimisations):
            if not opt.get("optimisation_id"):
                add("medium", f"optimisations[{i}].optimisation_id", "Optimisation has no ID")
            if not opt.get("description"):
                add("medium", f"optimisations[{i}].description", "Optimisation has no description")
            check_sources(opt, f"optimisations[{i}]")

    # --- Business metrics shape ---
    bm = ssad.get("business_metrics")
    if bm is not None:
        if isinstance(bm, dict) and not isinstance(bm, list):
            add("medium", "business_metrics", "business_metrics is a flat dict — should be an array of KPI objects per schema v2.0.0")
        elif isinstance(bm, list):
            for i, metric in enumerate(bm):
                if not metric.get("metric_id"):
                    add("low", f"business_metrics[{i}].metric_id", "KPI metric has no metric_id")

    # --- Contradictions ---
    contradictions = ssad.get("contradictions", [])
    unresolved = [c for c in contradictions if c.get("status") == "unresolved"]
    if unresolved:
        add("medium", "contradictions",
            f"{len(unresolved)} unresolved contradiction(s) — consultant must review before final deliverables")

    # --- Follow-up questions ---
    follow_ups = ssad.get("follow_up_questions", [])
    high_pending = [q for q in follow_ups if q.get("priority") == "HIGH" and q.get("status") == "pending"]
    if high_pending:
        add("medium", "follow_up_questions",
            f"{len(high_pending)} HIGH priority follow-up question(s) still pending — audit data may be incomplete")

    # --- Proposed changes (analyst enrichment) ---
    proposed_changes = ssad.get("proposed_changes", [])
    valid_sources = ("client", "analyst")
    valid_value_types = ("time_saving", "productivity_enhancement", "both")
    valid_research_statuses = ("not_started", "in_progress", "complete", "needs_review")
    valid_weeks_labels = ("<1 week", "1-2 weeks", "2-4 weeks", "4+ weeks")

    for i, change in enumerate(proposed_changes):
        prefix = f"proposed_changes[{i}]"
        # Optional analyst fields — validate if present
        source = change.get("source")
        if source is not None and source not in valid_sources:
            add("low", f"{prefix}.source", f"source must be 'client' or 'analyst', got: '{source}'")

        value_type = change.get("value_type")
        if value_type is not None and value_type not in valid_value_types:
            add("low", f"{prefix}.value_type", f"value_type must be one of {valid_value_types}, got: '{value_type}'")

        research = change.get("research")
        if research is not None:
            rs = research.get("status", "")
            if rs not in valid_research_statuses:
                add("low", f"{prefix}.research.status", f"research.status must be one of {valid_research_statuses}, got: '{rs}'")

        impl = change.get("implementation")
        if impl is not None:
            we = impl.get("weeks_estimate")
            if we is not None and (not isinstance(we, (int, float)) or we <= 0):
                add("low", f"{prefix}.implementation.weeks_estimate", f"weeks_estimate must be a positive number, got: {we}")
            wl = impl.get("weeks_label")
            if wl is not None and wl not in valid_weeks_labels:
                add("low", f"{prefix}.implementation.weeks_label", f"weeks_label must be one of {valid_weeks_labels}, got: '{wl}'")

        value = change.get("value")
        if value is not None:
            cav = value.get("combined_annual_value_aud")
            if cav is not None and (not isinstance(cav, (int, float)) or cav < 0):
                add("low", f"{prefix}.value.combined_annual_value_aud", f"combined_annual_value_aud must be non-negative, got: {cav}")

        # Source trail: source_evidence[] must be populated for client-sourced changes once EI has run
        ev = change.get("source_evidence")
        if change.get("linked_pain_point_ids") or change.get("linked_waste_item_ids"):
            if not ev or not isinstance(ev, list) or len(ev) == 0:
                add("medium", f"{prefix}.source_evidence",
                    "proposed_change has linked pain points / waste items but source_evidence[] is empty — renderer cannot show a Sources panel without a join")
            else:
                for k, e in enumerate(ev):
                    if not e.get("quote"):
                        add("medium", f"{prefix}.source_evidence[{k}].quote", "source_evidence entry has no quote")
                    if not e.get("fathom_url"):
                        add("medium", f"{prefix}.source_evidence[{k}].fathom_url",
                            "source_evidence entry has no fathom_url — required for one-click recording deep-link")

    # --- Strategy plugin_cards source_quotes ---
    strat = ssad.get("strategic_approaches") or {}
    tier_rec = strat.get("service_tier_recommendation") or {}
    for tier_name in ("low_ticket", "mid_ticket", "high_ticket"):
        tier = tier_rec.get(tier_name) or {}
        cards = tier.get("plugin_cards") or []
        if not isinstance(cards, list):
            continue
        for ci, card in enumerate(cards):
            sq = card.get("source_quotes")
            if sq is None:
                continue
            if not isinstance(sq, list):
                add("low", f"strategic_approaches.{tier_name}.plugin_cards[{ci}].source_quotes", "source_quotes must be an array")
                continue
            for qi, q in enumerate(sq):
                if not q.get("fathom_url"):
                    add("medium",
                        f"strategic_approaches.{tier_name}.plugin_cards[{ci}].source_quotes[{qi}].fathom_url",
                        "plugin_card source_quote has no fathom_url — chain breaks at strategy layer")
                if q.get("source_timestamp_seconds") is None:
                    add("medium",
                        f"strategic_approaches.{tier_name}.plugin_cards[{ci}].source_quotes[{qi}].source_timestamp_seconds",
                        "plugin_card source_quote has no timestamp — cannot deep-link recording")

    # --- Sessions ---
    sessions = ssad.get("sessions", [])
    unanalyzed = [s for s in sessions if not s.get("analyzed", False)]
    if unanalyzed:
        add("low", "sessions",
            f"{len(unanalyzed)} session(s) recorded but not analyzed: {[s.get('transcript_file') for s in unanalyzed]}")

    # --- Completeness checklist ---
    checklist = ssad.get("completeness_checklist", {})
    process_stages = {p.get("stage") for p in ssad.get("processes", []) if p.get("stage")}
    uncovered_stages = [stage for stage in process_stages
                        if not checklist.get(stage, {}).get("covered", False)]
    if process_stages and len(uncovered_stages) == len(process_stages):
        add("high", "completeness_checklist", "All stages show covered: false — completeness checklist not populated")
    elif uncovered_stages and audit_status == "process_map_complete":
        add("medium", "completeness_checklist",
            f"Stages not yet covered: {', '.join(uncovered_stages)}")

    # --- Volume split, handoff mechanism, and control gap enum checks ---
    _VALID_MECHANISMS = {
        "api_sync", "automated_sync", "manual_export_import",
        "copy_paste", "email_forward", "verbal", "paper", "unknown",
    }
    _VALID_CONTROL_GAP_CATEGORIES = {"no_approval", "no_quality_check", "no_audit_trail"}

    for pi, process in enumerate(ssad.get("processes", [])):
        stage = process.get("stage", f"[{pi}]")
        gateways_by_id = {}
        for step in process.get("steps", []):
            etype = step.get("element_type", "")
            stype = step.get("type", "")
            sid = step.get("step_id") or step.get("bpmn_id", "?")
            if etype == "exclusive_gateway" or stype == "decision":
                gateways_by_id[sid] = step
            # Handoff mechanism check
            handoff = step.get("handoff") or {}
            mech = handoff.get("mechanism")
            if mech is not None and mech not in _VALID_MECHANISMS:
                add("low", f"processes[{stage}].steps[{sid}].handoff.mechanism",
                    f"handoff.mechanism '{mech}' is not in the valid set: {sorted(_VALID_MECHANISMS)}")

        # Volume split check: outgoing flows from exclusive gateways should sum to ~100%
        for sf in process.get("sequence_flows", []):
            vs = sf.get("volume_split")
            if not isinstance(vs, dict):
                continue
            src_id = sf.get("source_ref") or sf.get("from")
            if src_id not in gateways_by_id:
                continue
        # Gather all outgoing flows per gateway that have volume_split
        gw_flows: dict[str, list] = {}
        for sf in process.get("sequence_flows", []):
            vs = sf.get("volume_split")
            if not isinstance(vs, dict):
                continue
            src_id = sf.get("source_ref") or sf.get("from")
            if src_id in gateways_by_id:
                gw_flows.setdefault(src_id, []).append(vs)
        for gw_id, splits in gw_flows.items():
            pcts = [s.get("percentage") for s in splits if isinstance(s.get("percentage"), (int, float))]
            if len(pcts) == len(splits) and pcts:
                total = sum(pcts)
                if not (90 <= total <= 110):
                    add("low", f"processes[{stage}].sequence_flows[volume_split from {gw_id}]",
                        f"volume_split percentages sum to {total}% (expected ~100%). Review the gateway outgoing flows.")

    # Control gaps category check
    for i, cg in enumerate(ssad.get("control_gaps", [])):
        cat = cg.get("category")
        if cat not in _VALID_CONTROL_GAP_CATEGORIES:
            add("medium", f"control_gaps[{i}].category",
                f"control_gaps category '{cat}' must be one of: {sorted(_VALID_CONTROL_GAP_CATEGORIES)}")

    # --- BPMN structural checks ---
    from validate_bpmn_json import validate_bpmn_json
    bpmn_partial = audit_status != "process_map_complete"
    bpmn_findings = validate_bpmn_json(ssad, partial_ok=bpmn_partial)
    for bf in bpmn_findings:
        severity = bf["severity"]
        if severity == "low":
            severity = "medium"
        add(severity, bf.get("field", "processes"), f"[{bf['rule']}] {bf['message']}")

    return findings


def main():
    parser = argparse.ArgumentParser(description="Validate an audit data JSON file")
    parser.add_argument("--file", required=True, help="Path to audit-data.json")
    parser.add_argument("--verbose", action="store_true", help="Show all findings")
    args = parser.parse_args()

    ssad = load_audit_data(args.file)
    findings = validate(ssad)

    critical = [f for f in findings if f["severity"] == "critical"]
    high = [f for f in findings if f["severity"] == "high"]
    medium = [f for f in findings if f["severity"] == "medium"]
    low = [f for f in findings if f["severity"] == "low"]

    status = "pass" if not critical and not high else "fail"

    result = {
        "status": status,
        "file": args.file,
        "client_slug": ssad.get("client_slug", "unknown"),
        "summary": {
            "critical": len(critical),
            "high": len(high),
            "medium": len(medium),
            "low": len(low),
            "total": len(findings)
        }
    }

    if args.verbose or status == "fail":
        result["findings"] = findings if args.verbose else critical + high

    print(json.dumps(result, indent=2))
    sys.exit(0 if status == "pass" else 1)


if __name__ == "__main__":
    main()
