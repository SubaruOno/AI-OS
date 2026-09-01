# Audit Data Schema — Generator Reference

> Canonical schema: `apg-audit-plugin/references/audit-data-schema.md`
> This file defines what Agent 5 (Builder/Generator) reads. The Generator does not write to audit-data.json; it reads it to produce HTML deliverables.
>
> **Schema v3.0.0** — fields now nested in domains. Use `domain.field` paths when referencing data (e.g. `findings.pain_points[]`, `opportunities.proposed_changes[]`). `generate.py` handles both v2 and v3 automatically via the flattener in `audit_reader.py` — no changes to generation logic needed.

## Fields the Generator Reads (v3 domain paths)

### process-map.html [GP]
- `extraction.processes[]` -- stages, steps (all fields: type, tool_ids, data_flow, meeting_references, parallel groups, branch_only)
- `extraction.decision_nodes[]` -- yes/no branches, step_id links
- `extraction.tools[]` -- tool_name, meeting_references (for recording badges)
- `findings.waste_items[]` -- hours_per_week (for waste heatmap overlay)
- `findings.pain_points_summary` -- top_themes (for summary section)

### findings.html [GF]
- `findings.pain_points[]` -- title, description, source_quote, speaker, stage, source_session, source_timestamp_seconds
- `findings.optimisations[]` -- description, source_quote, speaker, stage, opportunity_type
- `extraction.sessions[]` -- for session grouping
- `findings.contradictions[]` -- for "Data Integrity Flags" section

### waste.html [GV]
- `findings.waste_items[]` -- all fields (annual_waste_aud, hours_per_week, headcount_affected, hourly_rate_aud, rate_is_estimated, waste_type, source_quote, speaker, meeting_references, confidence)
- `meta.blended_hourly_rate_aud` -- fallback for items missing hourly_rate_aud

### solutions-overview.html [GS]
- `opportunities.proposed_changes[]` with `.research` sub-object (tools_researched[], custom_build_option, plugin_assessment)
- `extraction.processes[]` -- sidebar structure, process-to-change mapping via stage prefix
- `findings.pain_points[]` -- problem summary quotes
- `opportunities.proposed_changes[].value.formula_summary` -- value formula rows

### blueprint.html [GB]
- `findings.waste_items[].annual_waste_aud` -- summed for waste anchor hero
- `opportunities.proposed_changes[]` -- title, solution_type, value.combined_annual_value_aud, build_cost_range_aud, payback_months, risk_label, proposed_solution
- `findings.pain_points[]` -- cross-referenced via linked_pain_point_ids for "You said this" quotes
- `extraction.business_metrics[]` -- industry benchmarking section (metric_id, name, current_value, industry_benchmark, top_quartile, delta_narrative)

### strategic-approaches.html [GA] (legacy)
- `strategy.strategic_approaches.service_tier_recommendation` -- full three-tier model
- `opportunities.proposed_changes[].value`, `.implementation`, `.modal_content`
- `findings.waste_items[]`, `opportunities.risk_register[]`, `findings.positive_signals[]`, `extraction.tools[]`, `extraction.staff_roster[]`

### comprehensive-report.pdf [GC]
- Union of all above sections
- `architecture.requirements_spec` (if populated) -- Appendix A
- `architecture.architecture_doc` (if populated) -- Appendix B
- `extraction.client_context.constraints` -- Implementation Constraints section
- `findings.change_readiness` -- Change Readiness Assessment section

### client-website.html [GW]
- `meta.audit_status`, `meta.sessions_completed` -- progressive section unlock
- `meta.company_name`, `meta.contact` -- hero
- `findings.pain_points[]`, `findings.optimisations[]`, `findings.waste_items[]`, `opportunities.proposed_changes[]`, `extraction.processes[]`
