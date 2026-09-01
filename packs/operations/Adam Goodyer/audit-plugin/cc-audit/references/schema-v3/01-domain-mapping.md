# 01 — Domain Mapping: v2 Flat Keys to v3 Domains

> This file defines where every current top-level key in audit-data.json goes in v3.
> Use this as the authoritative reference when writing `migrate_audit_data.py`.

## Mapping Table

| v2 Flat Key | v3 Domain | v3 Path | Notes |
|---|---|---|---|
| `_schema_version` | root | `_schema_version` | Always at root, set to "3.0.0" after migration |
| `_section_index` | root | `_section_index` | Always at root, format extended to include domain line ranges |
| `client_slug` | meta | `meta.client_slug` | |
| `company_name` | meta | `meta.company_name` | |
| `industry_tag` | meta | `meta.industry_tag` | |
| `audit_start_date` | meta | `meta.audit_start_date` | |
| `audit_status` | meta | `meta.audit_status` | State machine gate, always loaded |
| `sessions_completed` | meta | `meta.sessions_completed` | |
| `google_drive_folder_url` | meta | `meta.google_drive_folder_url` | |
| `crm` | meta | `meta.crm` | Full crm object stays nested here |
| `contact` | meta | `meta.contact` | Full contact object stays nested here |
| `blended_hourly_rate_aud` | meta | `meta.blended_hourly_rate_aud` | Used by waste calculations, always loaded |
| `blended_rate_confidence` | meta | `meta.blended_rate_confidence` | |
| `blended_rate_source` | meta | `meta.blended_rate_source` | |
| `processes` | extraction | `extraction.processes` | Swim lanes with nested steps[] and flows[] |
| `decision_nodes` | extraction | `extraction.decision_nodes` | Branch point definitions |
| `tools` | extraction | `extraction.tools` | Tech stack with utilization and cost |
| `staff_roster` | extraction | `extraction.staff_roster` | Team members with roles and rates |
| `business_metrics` | extraction | `extraction.business_metrics` | KPIs; Researcher may enrich with benchmarks |
| `business_stages_covered` | extraction | `extraction.business_stages_covered` | Which pipeline stages have been mapped |
| `sessions` | extraction | `extraction.sessions` | Meeting metadata (fathom IDs, dates, analyzed flags) |
| `extracted_materials` | extraction | `extraction.extracted_materials` | Non-Fathom input tracking |
| `client_context` | extraction | `extraction.client_context` | Business overview, revenue streams, constraints |
| `pain_points` | findings | `findings.pain_points` | Cited problems with source quotes |
| `pain_points_summary` | findings | `findings.pain_points_summary` | Thematic clustering of pain points |
| `optimisations` | findings | `findings.optimisations` | Positive opportunities observed in transcripts |
| `waste_items` | findings | `findings.waste_items` | Quantified time/cost waste items |
| `contradictions` | findings | `findings.contradictions` | Conflicting statements between sessions |
| `follow_up_questions` | findings | `findings.follow_up_questions` | Gaps to fill in next session |
| `follow_up_summary` | findings | `findings.follow_up_summary` | Summary string of follow-up themes |
| `completeness_checklist` | findings | `findings.completeness_checklist` | Stage-by-stage extraction completeness |
| `change_readiness` | findings | `findings.change_readiness` | Client's appetite for change |
| `objections` | findings | `findings.objections` | Resistance signals |
| `positive_signals` | findings | `findings.positive_signals` | Enthusiasm signals |
| `data_gaps` | findings | `findings.data_gaps` | Missing data items |
| `proposed_changes` | opportunities | `opportunities.proposed_changes` | The big one: improvements with research, value, modal content |
| `roi_items` | opportunities | `opportunities.roi_items` | Financial projections linked to proposed_changes |
| `risk_register` | opportunities | `opportunities.risk_register` | Implementation risks (populated by RI) |
| `strategic_approaches` | strategy | `strategy.strategic_approaches` | Three-tier service recommendation |
| `transformation_blueprint` | strategy | `strategy.transformation_blueprint` | Phased implementation roadmap |
| `analyst_metadata` | root | `analyst_metadata` | At root level (not in a domain) |
| `architect_metadata` | root | `architect_metadata` | At root level (not in a domain) |

## Legacy / Drift Keys

These keys exist in some client files but are not in the canonical v2 schema. Map them as follows during migration:

| Legacy Key | Action | Destination |
|---|---|---|
| `business_metrics_list` | Merge into `extraction.business_metrics` if richer, else discard | `extraction.business_metrics` |
| `constraints` | Move to `extraction.client_context.constraints` (sub-key) | `extraction.client_context.constraints` |
| `strategic_notes` | Move to `extraction.client_context.strategic_notes` (sub-key) | `extraction.client_context.strategic_notes` |
| `quick_wins` | Move to `findings.quick_wins` | `findings.quick_wins` |
| `requirements_spec` | Move to `architecture.requirements_spec` | `architecture.requirements_spec` |
| `architecture_doc` | Move to `architecture.architecture_doc` | `architecture.architecture_doc` |
| `architecture_verification` | Move to `architecture.architecture_verification` | `architecture.architecture_verification` |
| `cowork_demos` | Move to `architecture.cowork_demos` | `architecture.cowork_demos` |
| `branding` | Move to `architecture.branding` | `architecture.branding` |
| `ingestion_manifest` | Do NOT include in audit-data.json — this is a separate file | Delete from audit-data.json |

## Architecture Domain Initial State

The `architecture` domain is empty for most clients (it's populated late in the pipeline). During migration, always include it as an empty object:

```json
"architecture": {
  "requirements_spec": {},
  "architecture_doc": {},
  "architecture_verification": {},
  "cowork_demos": [],
  "branding": {}
}
```

## Flattening Rules (v3 -> v2)

When flattening nested v3 back to a flat dict for backward compat:

1. Merge `meta`, `extraction`, `findings`, `opportunities`, `strategy`, `architecture` into a single flat dict using `dict.update()`
2. Preserve `_schema_version`, `_section_index`, `analyst_metadata`, `architect_metadata` at the top level
3. If a key appears in multiple domains (should not happen, but defensive), the last domain wins (architecture > strategy > opportunities > findings > extraction > meta)
4. `ingestion_manifest` is NOT included — it lives in a separate file `clients/{slug}/audit/ingestion-manifest.json`
