# Audit Data Schema — Process Analyst Reference

> Canonical schema: `apg-audit-plugin/references/audit-data-schema.md`
> This file defines what Agent 4 (Researcher) reads and writes. For full field definitions, see the canonical schema.
>
> **Schema v3.0.0** — fields now nested in domains. Use `domain.field` paths when reading or writing (e.g. `opportunities.proposed_changes[]`, `findings.pain_points[]`). v2 flat files are still supported via the backward-compat flattener in `audit_reader.py`.

## Fields the Analyst Reads (v3 domain paths)

| Field (v3 path) | Source | Used by |
|-------|--------|---------|
| `opportunities.proposed_changes[]` | Analyst EI | RI, BR, VR |
| `findings.pain_points[]` | Extractor SU | EI (synthesis), RI (unlinked scan) |
| `findings.waste_items[]` | Extractor SU | EI (linking), RI (unlinked scan), BR (value calc) |
| `findings.optimisations[]` | Extractor SU | EI (synthesis -- optimisations drive opportunity-sourced changes alongside pain points) |
| `extraction.tools[]` | Extractor SU | RI (API scan, existing stack, maturity assessment) |
| `extraction.processes[].steps[]` | Extractor SU | EI (step linking), BR (affected steps context) |
| `meta.blended_hourly_rate_aud` | Extractor SU | BR (value calculation fallback) |
| `extraction.staff_roster[]` | Extractor SU | BR (role-specific rate lookup) |
| `meta.industry_tag` | Extractor | RI (industry-specific research) |
| `extraction.sessions[]` | Extractor | BR (meeting references) |
| `opportunities.roi_items[]` | Analyst EI | BR (update with estimates) |
| `findings.pain_points_summary` | Extractor SU | EI (theme clustering) |
| `findings.change_readiness` | Extractor | BR (risk adjustment), VR (adoption risk) |
| `extraction.client_context.constraints` | Extractor | SA (strategy feasibility) |
| `extraction.business_metrics[]` | Extractor SU | RI (benchmark enrichment) |

## Fields the Analyst Writes (v3 domain paths)

### On `opportunities.proposed_changes[]` entries

**Written by EI:** `change_id`, `title`, `change_type`, `source`, `affected_step_ids`, `linked_roi_item_id`, `linked_pain_point_ids`, `linked_optimisation_ids`, `proposed_solution`, `proposed_tools`, `time_saving_minutes_per_occurrence`, `frequency`, `stage`, `confidence`, `value_type`, `solution_type`, `initiative_type` (null placeholder)

**Written by RI:** `.research` (sub-object), `.initiative_type` (authoritative classification), `.plugin_candidate`, `.research.plugin_assessment`, `.research.migration_diagnostic` (data_migration only — diagnostic shape, not buildable), `.research.custom_build_risk_flagged`, `.research.custom_build_risk_reason` (custom_build with mission-critical flag)

**Written by BR:** `.implementation` (includes `effort_band: S|M|L`), `.value` (with all value dimensions: time_saving, productivity_enhancement, risk_reduction, customer_experience, scalability), `.modal_content`, `.risk_label`, `.build_cost_range_aud` (internal use only — not rendered on blueprint), `.payback_months`

**Written by BO (build outlook):** `strategy.transformation_blueprint.phases[]`, `strategy.transformation_blueprint.short_term_outlook`, `strategy.transformation_blueprint.long_term_outlook`, `strategy.transformation_blueprint.risk_outlook` (dynamic 3-5 risk categories from catalogue, not fixed 3)

### Domain-level fields

- `opportunities.roi_items[]` -- updated by BR with annual_saving_aud, payback calculations
- `opportunities.risk_register[]` -- aggregated risks (RSK-xxx)
- `extraction.business_metrics[]` -- enriched with `industry_benchmark`, `top_quartile`, `benchmark_source`, `delta_narrative` by RI
- `strategy.transformation_blueprint` -- phase groupings + short-term/long-term outlook + risks narrative by BO (drives the "Where this takes you." section on blueprint.html)
- **Note:** `strategy.strategic_approaches` is no longer written by this agent. SA capability has been removed from the pipeline. The priority matrix grouping now reads from `opportunities.plugin_bundles[]` (written by RI), with fallback to `strategic_approaches.service_tier_recommendation.mid_ticket.plugin_cards[]` for backward compatibility with existing client data.
- `analyst_metadata` (root-level) -- run tracking

## Key Rules

- EI synthesises proposed changes from BOTH `findings.pain_points[]` AND `findings.optimisations[]`. Optimisations represent opportunities (better service, lead capture, revenue growth), not just efficiency fixes.
- `linked_optimisation_ids` must be populated when a change originates from or addresses an optimisation.
- `value.risk_reduction`, `value.customer_experience`, `value.scalability` are optional value dimensions. Populate when the change genuinely delivers that type of value.
- `value.combined_annual_value_aud` = sum of ALL populated value dimension annual values.
- `delta_narrative` on business_metrics must be factual only: "Your response time is 48 hours; industry average is 4 hours." Never judgmental language.

---

## New fields added by Sprint 1-7 redesign

### Agent 4 reads from extraction.json (new fields):
- `processes[].steps[].iato` — {input, action, actor, output} structured fields
- `processes[].steps[].handoff` — {source_tool, mechanism, destination_tool, data_transferred}
- `processes[].steps[].gateway_anatomy` — {condition, data_source, true_path_target, false_path_targets}
- `processes[].sequence_flows[].volume_split` — {percentage, confidence, note}
- `processes[].sequence_flows[].handoff` — same as step handoff
- `processes[].subject_traces[]` — {subject, entry_step_id, exit_step_ids, steps_in_trace, completeness}

### Agent 4 reads from findings.json (new fields):
- `gaps_register[]` — typed gap records (gap_type A/B/C, generates_fq, status)
- `control_gaps[]` — governance control gaps (no_approval, no_quality_check, no_audit_trail)

### Agent 4 writes to opportunities.json (new fields on proposed_changes[]):
- `volume_weight` — branch volume factor (default 1.0)
- `blocked_by_gaps` — gap IDs affecting scope (default [])
- `source_handoff_ids` — flow IDs from transfer mechanism scan (default [])
- `control_gap_ids` — control gap IDs addressed (default [])
- `source` — now accepts "control_gap" in addition to "client" and "analyst"
- `parent_finding_ids` — IDs linking two related initiatives that share a common finding (supports multi-initiative spawning from one finding, max 2 per finding)
- `research.transfer_mechanism_addressed` — the mechanism fixed
- `research.integration_pair` — specific integration research result
- `research.migration_diagnostic` — diagnostic shape for data_migration type: `{tool_name, problem_signals[], options[], recommended_option, risk_if_ignored}` (replaces `research.migration_research`)
- `research.custom_build_risk_flagged` — bool, true when custom build is downgraded to "flag as possibility" due to mission-critical process
- `research.custom_build_risk_reason` — explanation string for custom build risk flag
- `implementation.effort_band` — effort sizing: `S` (1-3 wks), `M` (4-8 wks), `L` (9+ wks). Written by BR sub-agent. Rendered on blueprint instead of per-initiative dollar amounts.

### strategy.transformation_blueprint.risk_outlook additions:
- `risk_outlook.risks[].category` — now supports 11 dynamic categories (not just 3 fixed). New categories: `mission_critical_fragility`, `compliance_exposure`, `key_person_dependency`, `vendor_concentration`, `external_collaborator_block`, `change_fatigue`, `hidden_integration_debt`, `customer_facing_exposure`. Unknown categories render with default gray styling in generate.py (backward-compatible).
- `risk_outlook.top_risks[]` — optional array of top 2 ranked risk items (rank, category, reason). Added by BO when two risks are clearly worse than others.
- `research.gap_status` — "clear" | "partially_blocked" | "blocked"
- `research.gap_blockers` — gap IDs that constrained research
