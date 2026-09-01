# Audit Data Schema — Process Mapper Reference

> Canonical schema: `apg-audit-plugin/references/audit-data-schema.md`
> This file defines what Agent 3 (Extractor) reads and writes. For full field definitions, see the canonical schema.
>
> **Schema v3.0.0** — fields now nested in domains. Use `domain.field` paths when reading or writing (e.g. `meta.audit_status`, `findings.pain_points[]`). v2 flat files are still supported via the backward-compat flattener in `audit_reader.py`.

## Fields the Extractor Writes

All extraction-phase data, organized by v3 domain:

**`meta` domain:**
- `meta._schema_version`, `meta.client_slug`, `meta.company_name`, `meta.industry_tag`, `meta.audit_start_date`, `meta.audit_status`, `meta.sessions_completed`, `meta.google_drive_folder_url`
- `meta.crm` block (initial creation, updated by all agents)
- `meta.contact` block
- `meta.blended_hourly_rate_aud`, `meta.blended_rate_confidence`, `meta.blended_rate_source`

**`extraction` domain:**
- `extraction.sessions[]`
- `extraction.extracted_materials[]`
- `extraction.business_stages_covered`, `extraction.processes[]` (with nested `steps[]`)
- `extraction.decision_nodes[]`
- `extraction.tools[]` (including `maturity_level`, `utilization_pct`, `maturity_notes`)
- `extraction.staff_roster[]`
- `extraction.business_metrics[]` (array of KPI objects, never a flat dict)
- `extraction.client_context` block (business_overview, revenue_streams, constraints, strategic_notes)

**`findings` domain:**
- `findings.pain_points[]`, `findings.pain_points_summary`
- `findings.optimisations[]` (including `opportunity_type`)
- `findings.waste_items[]`
- `findings.contradictions[]`
- `findings.completeness_checklist` (dynamic stage keys)
- `findings.follow_up_questions[]`, `findings.follow_up_summary`
- `findings.change_readiness` block
- `findings.objections[]`, `findings.positive_signals[]`, `findings.data_gaps[]`

**Root:**
- `_section_index` (updated on every write, using v3 domain keys)

## Key Field Rules

- `meta.audit_status` is `"in_progress"` or `"process_map_complete"`. Use `meta.sessions_completed` for session count.
- **Source attribution is unified.** Every extracted item (process step, tool, staff role, decision node, business metric, constraint, strategic note, pain point, waste item, optimisation, contradiction) carries a canonical `sources[]` array. Each entry is a discriminated union by `kind`: `"fathom"` (with `session_id` + `timestamp_seconds`) or `"document"` (with `document_path`). Every entry includes `quote`, `speaker`, and `confidence`. `len(sources) >= 1` is the invariant — items that cannot be attributed are retracted into `findings.follow_up_questions[]` with `category: "client_required"`. See the canonical schema's "Source Trail Convention" for full per-entry field rules.
- The gate enforces `sources[]` at three layers: sub-agent prompt refusal, `validate_sub_agent_output.py` pre-merge check, and `audit_reader.save_domain()` write-time guard (raises `CitationGateError` on empty `sources[]`).
- **Legacy flat fields** (`source_quote`, `source_speaker`/`speaker`, `source_session`, `source_timestamp_seconds`, `source_document`, `meeting_references[]`) are deprecated. They remain on disk for legacy clients; `audit_reader.py` normalizes them to `sources[]` on read so all downstream code sees a uniform shape.
- `findings.follow_up_questions[].id` -- identifier field (v3 uses `id`, v2 used `fq_id`).
- `extraction.business_metrics` is always an array of `{metric_id, name, current_value, unit, ...}` objects, never a flat dict.
- `findings.completeness_checklist` uses dynamic stage keys matching `extraction.processes[].stage`, not hardcoded stages.
- `findings.optimisations[].opportunity_type` categorises the opportunity (v3): `automation`, `ai`, `integration`, `process`, `tool`.
- `extraction.tools[].maturity_level` assesses how well the client uses the tool (v3): `core`, `supplementary`, `underutilised`, `workaround`.
