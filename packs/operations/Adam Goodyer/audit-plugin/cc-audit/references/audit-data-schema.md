# Audit Data Schema (Canonical)

> Single source of truth for client audit data.
> All four agents reference this file. Agent-specific read/write views are thin pointers back here.
> Last updated: 2026-05-28. **Schema version: 4.2.0** (v4.1/v4.0/v3/v2 still supported via backward-compat adapter). Sprint 1-7 fields added.

**Path:** `clients/{client_slug}/03-audit/data/` (v4: 7 files, v3/v2: single `audit-data.json`)

---

## Schema v4.0.0 — Multi-File Domain Split

As of 2026-05-12, new clients use a **multi-file layout** where each domain is its own JSON file. An `audit-manifest.json` index replaces the v3 `_section_index`. Each agent reads/writes only its own domain file(s), eliminating context dilution.

### Directory layout

```
clients/{slug}/03-audit/data/
├── audit-manifest.json       # index: version, checksums, timestamps
├── meta.json                 # ~2KB, always loaded
├── extraction.json           # processes, tools, sessions (Extractor)
├── findings.json             # pain points, waste, questions (Extractor)
├── opportunities.json        # proposed changes, ROI (Researcher)
├── strategy.json             # strategic approaches (Researcher)
├── architecture.json         # requirements, architecture (Designer)
└── ingestion-manifest.json   # unchanged (separate concern)
```

### Version detection

`audit_reader.py` auto-detects: v4 (audit-manifest.json present), v3 (_schema_version starts with "3"), v2 (anything else). All callers get the same flat dict interface via `load_all(slug)`.

### Reading and writing

- **Read:** `Read clients/{slug}/03-audit/data/{domain}.json` directly. No offset/limit needed.
- **Write:** Use `save_domain(slug, domain, data)` from `audit_reader.py`, or write the domain file then update `audit-manifest.json` (commit point).
- **Auto-regen:** Hook fires on `audit-manifest.json` writes only (single trigger per save cycle).

### Manifest schema

See `references/schema-v4/01-manifest-schema.md` for the full template and update rules.

### Clients on v4

`brightside-services`, `riverside-dental`. All others remain on v3/v2.

---

## Schema v3.0.0 — Nested Domain Structure (Legacy)

Earlier clients may use the **v3 nested format**: a single `audit-data.json` file with 6 named domains. The `_section_index` provides line ranges for selective loading. `audit_reader.py` handles this transparently.

### Domain overview

| Domain | Keys | Write Owner | When to load |
|--------|------|-------------|--------------|
| `meta` | 13 | Extractor | Always — identity, CRM, contact, blended rate |
| `extraction` | 9 | Extractor | Process map, solutions overview, extractor work |
| `findings` | 12 | Extractor | Findings page, waste page, process map heatmap, blueprint |
| `opportunities` | 3 | Researcher | Solutions overview, blueprint, architecture |
| `strategy` | 2 | Researcher | Blueprint, comprehensive report |
| `architecture` | 5 | Designer | Comprehensive report, designer work only |

### Top-level v3 structure

```json
{
  "_schema_version": "3.0.0",
  "_section_index": {
    "meta":          { "key_count": 13, "line_start": 3,  "line_end": 55,  "written_by": "extractor" },
    "extraction":    { "key_count": 9,  "line_start": 56, "line_end": 0,   "written_by": "extractor" },
    "findings":      { "key_count": 12, "line_start": 0,  "line_end": 0,   "written_by": "extractor" },
    "opportunities": { "key_count": 3,  "line_start": 0,  "line_end": 0,   "written_by": "researcher" },
    "strategy":      { "key_count": 2,  "line_start": 0,  "line_end": 0,   "written_by": "researcher" },
    "architecture":  { "key_count": 5,  "line_start": 0,  "line_end": 0,   "written_by": "designer" }
  },
  "meta": { ... },
  "extraction": { ... },
  "findings": { ... },
  "opportunities": { ... },
  "strategy": { ... },
  "architecture": { ... },
  "analyst_metadata": {},
  "architect_metadata": {}
}
```

`line_start` / `line_end` in `_section_index` reflect actual line positions after every write. Set to 0 when unknown. Use these with `Read(path, offset, limit)` to load only the domain you need from large files.

### Backward-compat flattener (v2 clients)

`generate.py` and `validate_audit_data.py` detect `_schema_version` at load time. When the version is `"2.0.0"` (or absent), a 10-line flattener merges all domain keys into a single flat dict identical to what all downstream code expects. No changes to generation logic were needed. All earlier clients continue to work unchanged.

The flattener lives in `apg-audit-plugin/scripts/audit_reader.py` (written in Session 2 of the migration). It also provides selective domain loading: agents can call `load_audit_data(path, profile="extractor")` to get only the domains they need.

---

## How to use this reference

**For AI agents:** This file defines every field in audit-data.json. When you need to read or write audit data, check this schema first. Use `_section_index` (if present) to locate domains without parsing the full file. Fields are grouped by which agent writes them.

**Field path notation:** In v3, field paths use `domain.field` format. For example, `findings.pain_points[]` instead of just `pain_points[]`, and `meta.audit_status` instead of `audit_status`. The per-agent thin reference files at `skills/{N}-{name}/references/audit-data-schema.md` use this notation.

**For validation:** The validation script (`skills/3-audit-extractor/scripts/validate_audit_data.py`) enforces structural rules. Run it after every write.

---

## Source Trail Convention (must read)

Every audit deliverable must be able to answer the client's #1 objection — **"where did you get this from?"** — with one click into the original Fathom recording at the right timestamp or open the source document. To make this durable, every extracted item carries a unified **`sources[]`** array. Each entry is a discriminated union by `kind` (`fathom` or `document`) and is a self-contained citation anchor.

> **CRM data note (2026-05-27):** Meeting transcripts are now fetched via the APG CRM (`list_contact_meetings`) rather than the Fathom MCP directly. The CRM syncs from Fathom, so `kind: "fathom"` remains correct for meeting transcript sources. `fathom_url` and `recording_id` (now a CRM UUID) are populated from CRM meeting data. SMS and call transcript sources use `kind: "document"` with `document_path` pointing to the locally-saved file.

### Canonical `sources[]` shape

Every item in the layers listed below carries a `sources` array with at least one entry. Items that cannot satisfy this invariant are not extracted — the topic is moved to `follow_up_questions[]` instead.

```json
{
  "sources": [
    {
      "kind": "fathom",
      "quote": "verbatim text from the transcript",
      "speaker": "Adam",
      "confidence": "HIGH",
      "session_id": 3,
      "timestamp_seconds": 1422
    },
    {
      "kind": "document",
      "quote": "verbatim text from the document",
      "speaker": null,
      "confidence": "MEDIUM",
      "document_path": "clients/{slug}/01-materials/documents/loom-transcripts/2026-04-22.md",
      "source_url": "https://www.loom.com/share/abc123"
    }
  ]
}
```

**Per-entry required fields by `kind`:**

| Field | `fathom` | `document` | Notes |
|---|---|---|---|
| `kind` | required | required | discriminator — exactly one of `"fathom"` or `"document"` |
| `quote` | required | required | verbatim text, non-empty, no paraphrasing |
| `speaker` | required | optional (null OK) | person name; `null` allowed only on document sources without a clear author |
| `confidence` | required | required | `HIGH` | `MEDIUM` | `LOW` |
| `session_id` | required (int) | omit | matches `extraction.sessions[].session_number` |
| `timestamp_seconds` | required (int) | omit | derived from `[MM:SS]` in transcript |
| `document_path` | omit | required | relative path from repo root |
| `source_url` | omit | optional | external URL when the document has one (Loom share URL, Gmail thread URL, public PDF URL). Captured for provenance — renderers may surface this in addition to `document_path`. Omit when no external URL exists (e.g. internal admin PDFs). |
| `reliability` | optional | optional | Two-character code: axis1 (A-F source type) + axis2 (1-6 specificity). E.g., "A1", "C3". See `references/kiq-library.md` for rating guide. Added sprint-4. |

### Items the gate covers

| Layer | Items |
|---|---|
| extraction | `processes[].steps[]`, `processes[].sequence_flows[]`, `tools[]`, `staff_roster[]`, `business_metrics[]`, `client_context.constraints[]`, `client_context.strategic_notes[]` |
| findings | `pain_points[]`, `waste_items[]`, `optimisations[]`, `contradictions[]` (each contradiction carries `sources[]` of length 2 — one entry per conflicting statement) |
| opportunities | `proposed_changes[]` — uses `source_evidence[]` aggregated from upstream `sources[]` (flat de-duped tuples — separate shape, kept for renderer compatibility) |
| strategy | `plugin_cards[].source_quotes[]` — aggregated from upstream `sources[]` |
| architecture | `requirements[]` — uses `derived_from_change_ids[]` instead |

**Exempt:** `follow_up_questions[]` — by definition has no source yet (that is why they are questions).

### Gate enforcement (three layers)

The gate is enforced at emission, merge, and write time. Items without `sources[]` cannot reach disk:

1. **Pre-emission (sub-agent prompt).** Sub-agents are instructed to refuse emission and retract: if a finding cannot be attributed, the topic is moved to `new_follow_up_questions[]` with `category: "client_required"` instead of being emitted as an unattributed item.
2. **Pre-merge (`validate_sub_agent_output.py`).** The merge orchestrator runs this validator against every sub-agent response before merging. Empty `sources[]` aborts the merge for that source; no partial writes.
3. **Write-time (`audit_reader.save_domain()`).** Raises `CitationGateError` if any item in the payload has empty `sources[]`. Makes it structurally impossible for any code path — sub-agent merge, feedback corrections, manual scripts — to commit an unattributed item.

### Rules

1. **No item without a source.** `len(sources) >= 1` is the only invariant. Items that cannot be attributed are retracted into `follow_up_questions[]`.
2. **Multiple sources per item are encouraged.** One waste item can be grounded by a Fathom quote AND a corroborating document — both go in `sources[]`. The item-level `confidence` is the max of per-source confidences.
3. **Forbidden compensations.** Never fabricate a `session_id`, `timestamp_seconds`, `document_path`, or `quote` to "pass the schema". Retraction is the only valid alternative.
4. **De-dupe by source identity.** Within a single item's `sources[]`, de-dup by `(kind, session_id, timestamp_seconds)` for Fathom or `(kind, document_path)` for documents. Across items, a single utterance can ground multiple pain_points/waste_items — that is expected, not a duplicate.
5. **Renderers read `sources[]` directly.** Each downstream layer (Researcher, Builder, Designer) reads upstream `sources[]` and aggregates the relevant entries into its own `source_evidence[]` / `source_quotes[]` panel. Renderers do not join three files to surface a quote.
6. **The validator enforces this.** `validate_audit_data.py` returns exit code 1 (HIGH) for any extraction/findings item with empty `sources[]`. The pre-merge validator (`validate_sub_agent_output.py`) returns exit code 1 with a structured failure report listing every offending item.

### Backward compatibility (legacy flat fields)

Existing client data (riverside-dental, brightside-services, brightside-services, and ~28 v2/v3 clients) uses the legacy flat-field shape on disk: `source_session`, `source_timestamp_seconds`, `source_quote`, `source_speaker`/`speaker`, `source_document`, `meeting_references[]`. The legacy shape stays on disk for those clients; the gate governs **new extractions only**.

`audit_reader.py` normalizes legacy items to `sources[]` on read so downstream agents see a uniform shape. New writes use the canonical `sources[]` shape exclusively.

**Hybrid period (~30 days from 2026-05-14):** the reader also back-fills the legacy flat fields *from* `sources[]` on read for items that already use the new shape, so the existing generator/researcher/designer code keeps working with zero changes. After the hybrid period ends, downstream consumers will be migrated to read `sources[]` directly and the back-fill will be dropped.

---

## Section Index

When present, `_section_index` at the top of audit-data.json maps each domain to its key count and line range. Use this to decide which sections to read without parsing the full file (which can exceed 10,000 lines).

**v3 format (domain-based):**

```json
"_section_index": {
  "meta":          { "key_count": 13, "line_start": 3,  "line_end": 55,  "written_by": "extractor" },
  "extraction":    { "key_count": 9,  "line_start": 56, "line_end": 0,   "written_by": "extractor" },
  "findings":      { "key_count": 12, "line_start": 0,  "line_end": 0,   "written_by": "extractor" },
  "opportunities": { "key_count": 3,  "line_start": 0,  "line_end": 0,   "written_by": "researcher" },
  "strategy":      { "key_count": 2,  "line_start": 0,  "line_end": 0,   "written_by": "researcher" },
  "architecture":  { "key_count": 5,  "line_start": 0,  "line_end": 0,   "written_by": "designer" }
}
```

**v2 format (flat, still used by earlier clients):**

```json
"_section_index": {
  "processes": { "item_count": 6, "last_modified": "2026-04-28T10:00:00Z", "written_by": "extractor" },
  "tools": { "item_count": 23, "last_modified": "2026-04-28T10:00:00Z", "written_by": "extractor" },
  "pain_points": { "item_count": 54, "last_modified": "2026-04-28T10:00:00Z", "written_by": "extractor" },
  "waste_items": { "item_count": 37, "last_modified": "2026-04-28T10:00:00Z", "written_by": "extractor" },
  "proposed_changes": { "item_count": 10, "last_modified": null, "written_by": "researcher" },
  "strategic_approaches": { "item_count": 0, "last_modified": null, "written_by": "researcher" },
  "requirements_spec": { "item_count": 0, "last_modified": null, "written_by": "designer" }
}
```

---

## Schema Template — v3 Domains

### meta domain (written by Extractor)

Domain path: `meta.*`

```json
"meta": {
  "_schema_version": "3.0.0",
  "client_slug": "",
  "company_name": "",
  "industry_tag": "home-services|ndis|construction|real-estate|cleaning|trades|professional-services|other",
  "audit_start_date": "YYYY-MM-DD",
  "audit_status": "in_progress|process_map_complete",
  "sessions_completed": 0,
  "google_drive_folder_url": "",
  "crm": {
    "contact_id": null,
    "lead_id": null,
    "project_id": null,
    "task_list_ids": {
      "extraction": null,
      "analysis": null,
      "deliverables": null,
      "solution_design": null
    },
    "last_synced": null
  },
  "contact": {
    "name": "",
    "role": "",
    "company_size": "",
    "revenue_range": "",
    "domain": "",
    "emails": []
  },
  "blended_hourly_rate_aud": null,
  "blended_rate_confidence": "HIGH|MEDIUM|LOW",
  "blended_rate_source": ""
}
```

- `_schema_version` -- always "3.0.0" for new clients. The flattener uses this to detect format.
- `audit_status` -- state machine: `"in_progress"` (extraction sessions ongoing) or `"process_map_complete"` (all sessions done, unlocks analyst pipeline). Use `sessions_completed` to track session count.
- `google_drive_folder_url` -- optional. Reference link to the client's Drive folder (files sync locally via Drive for Desktop).
- `contact.emails` -- array used as CRM contact lookup keys. Add multiple if meetings are booked under different addresses.
- `crm.project_id` -- if null, all CRM updates are skipped silently.
- `blended_hourly_rate_aud` -- extracted from salary/pay rate data in transcripts (salary / 2,080 for annual; weighted average for multiple roles). Fallback: `50` with `confidence: LOW`.

---

## extraction domain (written by Extractor)

Domain path: `extraction.*`

```json
"extraction": {
  "processes": [ ... ],
  "decision_nodes": [ ... ],
  "tools": [ ... ],
  "staff_roster": [ ... ],
  "business_metrics": [ ... ],
  "business_stages_covered": [],
  "sessions": [ ... ],
  "extracted_materials": [ ... ],
  "client_context": { ... }
}
```

### extraction.sessions

```json
"sessions": [
  {
    "session_id": "S1",
    "fathom_meeting_id": "",
    "fathom_url": "",
    "date": "YYYY-MM-DD",
    "analyzed": false,
    "stages_covered": []
  }
]
```

- Sessions are for Fathom meetings ONLY. Emails, PDFs, and other materials go in `extracted_materials[]`.

### extraction.extracted_materials

```json
"extracted_materials": [
  {
    "source_file": "",
    "date": "",
    "type": "email|pdf|document",
    "from": "",
    "extracted": [],
    "extraction_stats": {}
  }
]
```

- Data from materials uses `"source_material"` (file path) instead of `"source_session"`.

### extraction.processes

```json
"processes": [
  {
    "stage": "scheduling",
    "label": "Scheduling & Dispatch",
    "owner": "",
    "steps": [ ... ],
    "sequence_flows": [
      {"id": "SF-001", "from": "step_id", "to": "step_id", "condition": ""}
    ],
    "parallel_tracks": [
      {"label": "Track Name", "cadence": "Per deal", "step_ids": ["SCH-001", "SCH-002"]}
    ],
    "plugin_scope": {}
  }
]
```

- `stage` -- snake_case key derived from transcript (e.g. `acquisition`, `quoting_proposals`)
- `label` -- display label for sidebar nav and zone headers (v3 uses `label`; v2 used `name`)

### subject_traces[] (added sprint-1)
Optional array at process level.

| Field | Type | Notes |
|-------|------|-------|
| subject_traces[].subject | string | What is being traced ("customer inquiry") |
| subject_traces[].entry_step_id | string | First step_id in the trace |
| subject_traces[].exit_step_ids | string[] | Terminal step_ids |
| subject_traces[].steps_in_trace | string[] | All step_ids in order |
| subject_traces[].completeness | "complete"\|"partial"\|"fragment" | |

#### Process Step Shape (v4.1.0)

```json
{
  "step_id": "SCH-001",
  "element_type": "task|exclusive_gateway|parallel_gateway|intermediate_catch_event|intermediate_throw_event",
  "annotations": ["pain", "optimisation", "automation"],
  "label": "",
  "description": "",
  "owner": "",
  "lane_id": "Operations Manager",
  "task_type": "user_task|service_task|send_task|receive_task",
  "event_definition": "timer|message|error|signal",
  "default_flow_id": null,
  "time_estimate_hours_per_week": null,
  "data_flow": "",
  "tool_ids": [],
  "confidence": "HIGH|MEDIUM|LOW",
  "sources": [
    {
      "kind": "fathom",
      "quote": "verbatim",
      "speaker": "Adam",
      "confidence": "HIGH",
      "session_id": 1,
      "timestamp_seconds": 1422
    }
  ]
}
```

- `sources[]` -- canonical citation array. Every step MUST have at least one entry. See "Source Trail Convention" above.

### IATO fields (added sprint-1)
Optional. Present on task-type steps (task, user_task, service_task, send_task, receive_task, manual_task, business_rule_task) when Sprint 1+ extraction is used.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| iato | object | No | null if not yet extracted |
| iato.input | string | No | What physically arrives at this step |
| iato.action | string | Yes if iato present | Transformation verb phrase — must start with a verb |
| iato.actor | string | No | Specific role, system, or person |
| iato.output | string | No | What leaves and where it goes |

### _gaps (added sprint-1, gap_type added sprint-2)
Optional. null if all IATO fields populated.

| Field | Type | Notes |
|-------|------|-------|
| _gaps.missing_input | boolean | true when iato.input is null |
| _gaps.missing_output | boolean | true when iato.output is null |
| _gaps.missing_actor | boolean | true when iato.actor is null |
| _gaps.missing_action | boolean | true when iato.action is null |
| _gaps.gap_type | "A"\|"B"\|"C"\|null | A=never communicated, B=industry shorthand, C=missed in extraction |
| _gaps.gap_note | string | One-sentence description of what was not found |

### display_label (added sprint-1)
Optional string. Plain-English version of label for jargon terms. Equals label if no jargon.

### handoff (added sprint-1)
Optional. Present on steps where tool_ids[] changes from the preceding step. null if no tool change.

| Field | Type | Notes |
|-------|------|-------|
| handoff.source_tool | string | Tool data leaves from |
| handoff.mechanism | string | api_sync \| automated_sync \| manual_export_import \| copy_paste \| email_forward \| verbal \| paper \| unknown |
| handoff.destination_tool | string | Tool data enters |
| handoff.data_transferred | string | Description of what moves |

### gateway_anatomy (added sprint-2)
Optional. Present on exclusive_gateway steps.

| Field | Type | Notes |
|-------|------|-------|
| gateway_anatomy.condition | string | Evaluable criterion |
| gateway_anatomy.data_source | string | System/document providing the evaluated value |
| gateway_anatomy.true_path_target | string | step_id of primary path |
| gateway_anatomy.false_path_targets | string[] | step_ids of alternate paths |
| gateway_anatomy._gaps | object | Same structure as step _gaps (missing_condition, missing_data_source, missing_path) |

- `element_type` -- BPMN 2.0 element class: `task` (standard box), `exclusive_gateway` (decision diamond), `parallel_gateway` (parallel fork/join), `intermediate_catch_event` (mid-process wait/trigger), `intermediate_throw_event` (mid-process signal). Maps directly to BPMN XML tags.
- `annotations[]` -- audit-specific markers overlaid on the element: `pain` (red highlight), `optimisation` (green), `automation` (blue). A task can have multiple annotations or none.
- `lane_id` -- the swim lane this step belongs to. Must be a **functional role**, not a person name (e.g., "Lead Estimator", "CEO / Founder", "Operations Administrator / PA"). Derived from `staff_roster[].role` by looking up the step's `owner`. For external party interactions, use `"External: <party>"` (e.g., "External: Client", "External: Supplier"). For fully automated steps, use `"Automated"`. Never use a person name (those belong in `owner`) or a tool name (those belong in `tool_ids[]`).
- `task_type` -- BPMN task variant (only for `element_type: "task"`): `user_task` (person icon, default), `service_task` (gear icon), `send_task` (filled envelope), `receive_task` (open envelope). Omit for gateways and events.
- `event_definition` -- (optional, only for intermediate events): `timer` (wait period, SLA delay), `message` (notification sent/received mid-process), `error` (exception handling), `signal` (cross-process signaling). bpmn-js renders the appropriate icon automatically.
- `default_flow_id` -- (optional, only for `exclusive_gateway`): references the `id` of one outgoing sequence flow that is the fallback path when no other condition matches. The default branch should not carry a `condition` label.
- `tool_ids` -- array of tool name strings matching `extraction.tools[].tool_name`. Used by the researcher for tool research; `lane_id` is used for BPMN lane assignment.
- `flow_id` (nullable string) -- groups independent sub-flows within a stage. Steps with the same `flow_id` form one logical flow. Steps with `null` are on the main sequential path.
- `depends_on_step_id` (nullable string) -- explicit upstream dependency for cross-flow convergence points.
- `merge_note` (nullable string) -- populated when duplicate steps are merged. Records which step was absorbed and from which source.

**Legacy fields (deprecated, normalized on read by `audit_reader.py`):** `type` (mapped to `element_type` + `annotations`), `branch_only` (replaced by explicit `sequence_flows`), `parallel_group` (replaced by `parallel_gateway` elements), `source_quote`, `source_speaker`, `meeting_references[]`.

#### Sequence Flows (v4.1.0)

Each process carries a `sequence_flows[]` array that defines step-to-step connections. Maps 1:1 to BPMN `sequenceFlow` elements.

```json
"sequence_flows": [
  { "id": "SF-001", "from": "SCH-001", "to": "SCH-002" },
  { "id": "SF-002", "from": "SCH-002", "to": "SCH-D01" },
  { "id": "SF-003", "from": "SCH-D01", "to": "SCH-003", "condition": "Approved" },
  { "id": "SF-004", "from": "SCH-D01", "to": "SCH-004", "condition": "Rejected" }
]
```

- `from` / `to` -- step_id strings referencing steps in the same process.
- `condition` (optional) -- label for conditional flows from exclusive gateways (e.g. "Yes", "No", "Approved").

### volume_split (added sprint-1)
Optional. Present on outgoing flows from exclusive_gateway when volume mentioned by client.

| Field | Type | Notes |
|-------|------|-------|
| volume_split.percentage | number | 0-100 |
| volume_split.confidence | "HIGH"\|"MEDIUM"\|"LOW" | |
| volume_split.note | string | Source of the estimate |

### extraction.decision_nodes (DEPRECATED in v4.1.0)

Decision gateways are now inline steps with `element_type: "exclusive_gateway"`. Branch wiring lives in `sequence_flows[]` via the `condition` field.

Existing data with root-level `decision_nodes[]` is converted on read by `audit_reader.py` into gateway steps + sequence flows. New extractions should not emit `decision_nodes[]`.

### extraction.tools

```json
"tools": [
  {
    "tool_id": "T-001",
    "tool_name": "",
    "category": "",
    "current_plan": "",
    "seats": null,
    "monthly_cost_aud": null,
    "use_case": "",
    "workarounds": [],
    "api_available": null,
    "api_docs_url": null,
    "mcp_available": null,
    "mcp_url": null,
    "integration_openness": "open|partial|closed|unknown",
    "migration_research_flag": false,
    "integration_notes": "",
    "maturity_level": "core|supplementary|underutilised|workaround",
    "utilization_pct": null,
    "maturity_notes": "",
    "confidence": "HIGH|MEDIUM|LOW",
    "sources": [
      {
        "kind": "fathom",
        "quote": "verbatim",
        "speaker": "Adam",
        "confidence": "HIGH",
        "session_id": 1,
        "timestamp_seconds": 1422
      }
    ]
  }
]
```

- `sources[]` -- canonical citation array. Every tool MUST have at least one entry. See "Source Trail Convention" above.
- `tool_name` is the canonical identifier. Process steps reference tools by name in `tool_ids[]`.
- `maturity_level` -- how well the client uses this tool:
  - `core` -- central to operations, well-utilised
  - `supplementary` -- used for secondary tasks alongside another tool
  - `underutilised` -- paying for features they don't use
  - `workaround` -- being used in a way it was not designed for
- `utilization_pct` -- estimated percentage of the tool's capabilities being used (0-100). Powers the "paying for features you don't use" conversation.
- `maturity_notes` -- e.g. "Using ServiceM8 for scheduling only, ignoring CRM, quoting, and reporting modules"

**Legacy fields (deprecated):** `source_quote`, `quote`, `meeting_references[]`. Normalized to `sources[]` by `audit_reader.py` on read.

### extraction.staff_roster

```json
"staff_roster": [
  {
    "name": "",
    "role": "",
    "employment_type": "employee|contractor|owner",
    "hourly_rate_aud": null,
    "hours_per_week": null,
    "primary_processes": [],
    "sources": [
      {
        "kind": "fathom",
        "quote": "verbatim",
        "speaker": "Adam",
        "confidence": "HIGH",
        "session_id": 1,
        "timestamp_seconds": 1422
      }
    ]
  }
]
```

- `sources[]` -- canonical citation array. Every staff entry MUST have at least one source attesting to their role and rate.
- Used by BR for role-specific rate lookup and by the Designer for user role identification.

### extraction.business_metrics

```json
"business_metrics": [
  {
    "metric_id": "BM-001",
    "name": "",
    "current_value": null,
    "unit": "hours|percent|days|dollars|count|minutes|ratio",
    "period": "average|per_week|per_month|annual|per_occurrence",
    "industry_benchmark": null,
    "top_quartile": null,
    "benchmark_source": "",
    "benchmark_source_url": "",
    "delta_narrative": "",
    "sources": [
      {
        "kind": "fathom",
        "quote": "It takes us about two days to get back to a new enquiry",
        "speaker": "Priya",
        "confidence": "HIGH",
        "session_id": 1,
        "timestamp_seconds": 873
      }
    ]
  }
]
```

- `sources[]` -- canonical citation array. Every metric MUST have at least one source. **Legacy fields:** `source_session`, `source_quote` (deprecated; normalized to `sources[]` on read).

- Always an array of KPI objects, never a flat dict.
- `industry_benchmark` and `top_quartile` -- populated by RI (Stage 2f) with industry comparison data.
- `delta_narrative` -- factual comparison ONLY. "Your response time is 48 hours; industry average is 4 hours." Never "this is bad" or "you need to improve."
- Powers an "Industry Benchmarking" section in deliverables.

### extraction.client_context

```json
"client_context": {
  "business_overview": "",
  "revenue_streams": [],
  "constraints": [
    {
      "constraint_id": "CON-001",
      "title": "",
      "description": "",
      "confidence": "HIGH|MEDIUM|LOW",
      "sources": [
        {
          "kind": "fathom",
          "quote": "verbatim",
          "speaker": "Adam",
          "confidence": "HIGH",
          "session_id": 1,
          "timestamp_seconds": 1422
        }
      ]
    }
  ],
  "strategic_notes": [
    {
      "note_id": "SN-001",
      "title": "",
      "description": "",
      "confidence": "HIGH|MEDIUM|LOW",
      "date_captured": "",
      "applies_to_stages": [],
      "sources": [
        {
          "kind": "document",
          "quote": "verbatim from document",
          "speaker": null,
          "confidence": "MEDIUM",
          "document_path": "clients/{slug}/01-materials/documents/strategy-doc.pdf"
        }
      ]
    }
  ]
}
```

- `sources[]` -- canonical citation array on each constraint and strategic note. **Legacy fields:** `source_quote`, `source_document`, `speaker` (deprecated; normalized to `sources[]` on read).
- Structured home for contextual information that doesn't fit the structured arrays.
- `constraints` -- surface in strategic approaches to show recommendations are realistic.

---

## findings domain (written by Extractor)

Domain path: `findings.*`

```json
"findings": {
  "pain_points": [ ... ],
  "pain_points_summary": { ... },
  "optimisations": [ ... ],
  "waste_items": [ ... ],
  "contradictions": [ ... ],
  "follow_up_questions": [ ... ],
  "follow_up_summary": "",
  "completeness_checklist": { ... },
  "change_readiness": { ... },
  "objections": [],
  "positive_signals": [],
  "data_gaps": []
}
```

### findings.pain_points

```json
"pain_points": [
  {
    "id": "PP-001",
    "title": "",
    "description": "",
    "impact": "",
    "owner": "",
    "risk_signal": false,
    "risk_note": null,
    "stage": "",
    "priority": "HIGH|MEDIUM|LOW",
    "overlap_group": null,
    "overlap_note": null,
    "merge_note": null,
    "related_waste_ids": null,
    "related_optimisation_ids": null,
    "sources": [
      {
        "kind": "fathom",
        "quote": "verbatim quote from transcript",
        "speaker": "Priya",
        "confidence": "HIGH",
        "session_id": 1,
        "timestamp_seconds": 1422
      }
    ]
  }
]
```

- `sources[]` -- canonical citation array. Every pain point MUST have at least one entry. See "Source Trail Convention" above.
- `title` -- short label for display (e.g. "No automation from lead form to quote")
- `impact` -- business impact statement (e.g. "Quote response delays, inconsistent handling")
- `risk_signal` -- true if this pain point indicates a material business risk
- `risk_note` -- explanation of the risk (e.g. "Revenue growth stalled during pricing model transition")
- `overlap_group` -- written by [FR] Findings Review. Groups pain points sharing the same root cause. Does not imply merging.
- `overlap_note` -- written by [FR] Findings Review. Human-readable explanation of the shared root cause.
- `merge_note` -- written by [FR] Findings Review when duplicate pain points are merged.
- `related_waste_ids` -- written by [FR] Findings Review. Waste item IDs this pain point links to.
- `related_optimisation_ids` -- written by [FR] Findings Review. Optimisation IDs describing the desired resolution.

**Legacy fields (deprecated):** `source_quote`, `speaker`, `source_session`, `source_timestamp_seconds`, `meeting_references[]`. Normalized to `sources[]` by `audit_reader.py` on read.

### findings.pain_points_summary

```json
"pain_points_summary": {
  "top_themes": [
    { "theme": "", "count": 0, "stages_affected": [], "example_quote": "" }
  ],
  "highest_priority_count": 0
}
```

### findings.optimisations

```json
"optimisations": [
  {
    "id": "OPT-001",
    "description": "",
    "opportunity_type": "automation|ai|integration|process|tool",
    "stage": "",
    "confidence": "HIGH|MEDIUM|LOW",
    "sources": [
      {
        "kind": "fathom",
        "quote": "verbatim",
        "speaker": "Adam",
        "confidence": "HIGH",
        "session_id": 1,
        "timestamp_seconds": 1422
      }
    ]
  }
]
```

- `sources[]` -- canonical citation array. Every optimisation MUST have at least one entry.
- Client-stated improvement wishes, desired automations, and future-state aspirations.
- `opportunity_type` -- categorises the opportunity: `automation`, `ai`, `integration`, `process`, `tool`.
- Rendered on findings.html with a green "OPTIMISATION" eyebrow.
- Used by EI alongside pain_points to synthesise proposed_changes (optimisations drive opportunity-sourced changes, not just pain-point-driven ones).

**Legacy fields (deprecated):** `source_quote`, `speaker`, `source_session`, `source_timestamp_seconds`, `meeting_references[]`.

### findings.waste_items

```json
"waste_items": [
  {
    "waste_id": "W-001",
    "title": "",
    "description": "",
    "waste_type": "manual-data-entry|duplicate-work|context-switching|communication-overhead|error-rework|waiting|manual-reporting|undocumented-process",
    "stage": "",
    "hours_per_week": null,
    "headcount_affected": null,
    "hourly_rate_aud": null,
    "rate_is_estimated": true,
    "annual_waste_aud": null,
    "monthly_waste_aud": null,
    "confidence": "HIGH|MEDIUM|LOW",
    "source_type": "meeting|email|document|loom|observation|calculated",
    "calculation_note": "",
    "linked_pain_point_ids": [],
    "linked_step_id": "",
    "corrected_in_session": null,
    "correction_note": "",
    "overlap_group": null,
    "overlap_adjustment_aud": null,
    "overlap_note": null,
    "merge_note": null,
    "sources": [
      {
        "kind": "fathom",
        "quote": "verbatim",
        "speaker": "Priya",
        "confidence": "HIGH",
        "session_id": 1,
        "timestamp_seconds": 1422
      }
    ]
  }
]
```

- `sources[]` -- canonical citation array. Every waste item MUST have at least one entry. See "Source Trail Convention" above.
- `hourly_rate_aud` -- prefers role-specific rate from transcript; falls back to `meta.blended_hourly_rate_aud` with `rate_is_estimated: true`.
- `annual_waste_aud` = `hours_per_week * headcount_affected * hourly_rate_aud * 52`
- `source_type`: always set. `calculated` when derived from data, no direct quote.
- `calculation_note`: **REQUIRED.** Full arithmetic showing how `annual_waste_aud` was derived, including the source of each input. Time-based: `"1.25 hrs/wk × 1 person × $41.50/hr × 52 wks = $2,697/yr. 1.25 hrs/wk is mid-point of stated '2–4 hours fortnightly'."` Unrealized revenue: `"722 clients × 10% uptake × $150 avg = $10,830/yr. Client count from Timely. Avg from price list."` Note: `annual_value_note` is a deprecated alias for this field — migrate to `calculation_note`.
- `overlap_group` -- groups overlapping items that share a time component.
- `overlap_adjustment_aud` (number, negative) -- deduction applied to this item when computing the correct total.
- `overlap_note` -- human-readable explanation of the overlap and how the adjustment was calculated.

**Legacy fields (deprecated):** `source_quote`, `speaker`, `source_session`, `source_timestamp_seconds`, `source_document`, `meeting_references[]`. Normalized to `sources[]` by `audit_reader.py` on read.

**Totalling waste items in deliverables:** Sum `annual_waste_aud + (overlap_adjustment_aud ?? 0)` per item.

### findings.contradictions

```json
"contradictions": [
  {
    "id": "CON-001",
    "description": "",
    "resolution_status": "unresolved|resolved",
    "resolution_note": "",
    "sources": [
      {
        "kind": "fathom",
        "quote": "first conflicting statement",
        "speaker": "Adam",
        "confidence": "HIGH",
        "session_id": 1,
        "timestamp_seconds": 1422
      },
      {
        "kind": "fathom",
        "quote": "second conflicting statement",
        "speaker": "Priya",
        "confidence": "HIGH",
        "session_id": 2,
        "timestamp_seconds": 873
      }
    ]
  }
]
```

- `sources[]` -- canonical citation array. Every contradiction MUST have **at least two** entries — one for each conflicting statement. The renderer pairs them in display order.
- Never auto-resolved. Status stays `unresolved` until the consultant explicitly confirms.
- Used by AC audit-check diagnostics. Should also surface in findings.html as "Data Integrity Flags".

**Legacy fields (deprecated):** `session_a`, `session_b`. Normalized to `sources[]` by `audit_reader.py` on read.

### findings.completeness_checklist

```json
"completeness_checklist": {
  "<stage_key>": {
    "status": "complete|partial|not_started",
    "gaps": [],
    "sources": [],
    "notes": ""
  }
}
```

- Dynamic: keys match `extraction.processes[].stage`, not hardcoded stages.
- `status: "complete"` only when the consultant confirms, not when items are inferred.

### findings.follow_up_questions

```json
"follow_up_questions": [
  {
    "id": "FQ-001",
    "question": "",
    "stage": "",
    "priority": "HIGH|MEDIUM|LOW",
    "category": "researchable|client_required",
    "source_session": "S1",
    "status": "open|answered",
    "answer": null,
    "research_answer": "",
    "research_confidence": "HIGH|MEDIUM|LOW",
    "research_sources": []
  }
]
```

- `category` -- `"researchable"` (answerable via web search) or `"client_required"` (needs business knowledge) or `"extraction_gap"` (Type C gaps needing re-scan, added sprint-2).
- `research_answer` -- for researchable questions: must lead with specific endpoint paths, HTTP methods, key parameters from official documentation.
- `research_sources` -- prioritise official API documentation pages over marketing pages.

### New fields on follow_up_questions[] entries (added sprint-3)

| Field | Type | Notes |
|-------|------|-------|
| resolution_target | string | UPSTREAM_NODE \| DOWNSTREAM_CONDITION \| ACTOR \| TOOL_AND_FUNCTION \| DURATION |
| resolves | object | {field: "dot.path", step_id: "XX-NNN", process: "stage_name"} |
| linked_gap_ids | string[] | Gap IDs from gaps_register[] this question addresses |
| merged_question | boolean | true if compound question merged from multiple gaps |
| constituent_gap_ids | string[] | Gap IDs merged into this compound question |
| quality_gate_passed | boolean | false if question failed the quality gate |
| slide_group | string | Process area for PPTX grouping |

### findings.change_readiness

```json
"change_readiness": {
  "score": "HIGH|MEDIUM|LOW",
  "tech_comfort": {
    "score": null,
    "notes": ""
  },
  "training_capacity": {
    "score": null,
    "notes": ""
  },
  "previous_change_attempts": [
    {
      "what": "",
      "outcome": "successful|partial|reverted|abandoned",
      "reason": ""
    }
  ],
  "evidence": [],
  "champions": [],
  "blockers": []
}
```

- `tech_comfort.score` / `training_capacity.score` -- 1-5 scale (1 = very low, 5 = very high)
- `champions` -- staff members who are early adopters or enthusiastic about change
- `blockers` -- staff members or factors that may resist change
- Informs `risk_label` and `research.risks[]` on proposed changes

### findings — other arrays

```json
"objections": [],
"positive_signals": [
  { "signal": "", "source_session": "S1" }
],
"data_gaps": []
```

- `objections` -- client objections from transcripts
- `positive_signals` -- buying signals, enthusiasm markers
- `data_gaps` -- known information gaps. Format quantitative gaps as strings; handoff gaps as `"HANDOFF GAP [STEP-A -> STEP-B]: description"`

### gaps_register[] (added sprint-2)
Optional array. One entry per missing field on a step (not per step).

| Field | Type | Notes |
|-------|------|-------|
| gap_id | string | Sequential GAP-NNN |
| gap_type | "A"\|"B"\|"C" | Classification |
| affected_step_id | string | step_id this gap is on |
| affected_process | string | process stage name |
| affected_field | string | Dot-notation field path (e.g., "iato.input") |
| description | string | What is not known and why it matters |
| recommended_action | string | How to resolve |
| generates_fq | boolean | true if this gap should generate a follow-up question |
| fq_id | string\|null | Linked follow_up_questions[] entry |
| status | "unresolved"\|"resolved" | |

### control_gaps[] (added sprint-2)
Optional array. Generated by QA agent when governance controls are absent.

| Field | Type | Notes |
|-------|------|-------|
| control_gap_id | string | Sequential CG-NNN |
| step_id | string | Step where control is absent |
| category | "no_approval"\|"no_quality_check"\|"no_audit_trail" | |
| description | string | What control is missing and where |
| severity | "high"\|"medium" | |

### kiq_status[] (added sprint-4)
Optional array. One entry per KIQ tracked during extraction.

| Field | Type | Notes |
|-------|------|-------|
| kiq_id | string | e.g., "KIQ-ACQ-001" |
| status | "answered"\|"partial"\|"not_found" | |
| resolved_by | string[] | Session or document IDs that provided evidence |
| answer_summary | string | Brief answer if answered/partial |

---

## opportunities domain (written by Researcher)

Domain path: `opportunities.*`

```json
"opportunities": {
  "proposed_changes": [ ... ],
  "roi_items": [ ... ],
  "risk_register": [ ... ],
  "plugin_bundles": [ ... ]
}
```

### opportunities.plugin_bundles

Written by RI (Stage 3e) after all sub-agent skill_definitions are collected. Each bundle is one recommended Claude plugin — a package of related skills that address a single business process domain. `proposed_changes[]` stays flat; `plugin_bundles[]` is the hierarchical view.

```json
"plugin_bundles": [
  {
    "bundle_id": "PLG-001",
    "plugin_name": "{client-slug}-financial-reconciliation",
    "plugin_title": "Financial Reconciliation",
    "description": "Automates fortnightly contractor and cash client reconciliation against Timely roster data",
    "skills": [
      {
        "skill_id": "SK-001",
        "change_id": "CH-002",
        "skill_name": "contractor-invoice-reconciliation",
        "skill_title": "Contractor Invoice Reconciliation",
        "trigger": "Fortnightly, when contractor invoices arrive via Gmail",
        "inputs": [
          {
            "name": "Timely CSV Export",
            "source": "Manual download from Timely (no REST API)",
            "format": "CSV",
            "access_method": "manual_upload"
          }
        ],
        "workflow_steps": [
          "Parse Timely CSV to extract hours per contractor per team for the pay period",
          "Read each invoice PDF via Claude vision to extract billed amounts and contractor name",
          "Cross-reference hours x contracted rate against each invoice total",
          "Flag discrepancies: green (match), amber (<5% variance), red (>5% or missing)"
        ],
        "outputs": [
          {
            "name": "Reconciliation Report",
            "destination": "Google Sheets tab 'Recon YYYY-MM'",
            "format": "Per-contractor rows with status, expected vs actual amounts"
          }
        ]
      }
    ],
    "connectors": [
      { "name": "Google Sheets MCP", "purpose": "Read/write reconciliation data" },
      { "name": "Gmail MCP", "purpose": "Read contractor invoices by label" }
    ],
    "shared_data_layer": "Google Sheets",
    "covered_change_ids": ["CH-002", "CH-003"],
    "complexity_tier": "standard",
    "price_range_low_aud": 4500,
    "price_range_high_aud": 8000,
    "combined_annual_value_aud": 4502,
    "confidence": "HIGH",
    "generated_at": "2026-05-14T..."
  }
]
```

- `bundle_id` -- sequential PLG-001, PLG-002, etc.
- `plugin_name` -- kebab-case, prefixed with client-slug so plugin names don't clash across clients
- `plugin_title` -- 2-4 words, process-level (not task-level)
- `skills[]` -- one entry per proposed_change bundled into this plugin. Ordered by logical workflow sequence.
- `skill_id` -- sequential within each bundle (SK-001, SK-002, etc.), resets per bundle
- `skill_definition.inputs[].access_method` -- one of: `sheets_mcp`, `gmail_mcp`, `drive_mcp`, `xero_api`, `manual_upload`, `human_text_input`, `other_mcp`
- `connectors[]` -- de-duplicated union of all skill input/output tool connections that need MCP access
- `shared_data_layer` -- the Google Sheet, SaaS, or DB that multiple skills read from (the common substrate)
- `covered_change_ids[]` -- must match exactly the `change_id` values of the skills in this bundle
- Write owner: RI (Stage 3e). SA reads this array directly to build plugin cards; SA does NOT re-derive groupings.

**Corresponding field on proposed_changes:** Each cowork_plugin change gets a `plugin_bundle_id` string (e.g. `"PLG-001"`) linking it to its parent bundle. Non-plugin changes have `plugin_bundle_id: null`. The `skill_definition` block (same structure as `skills[]` entries minus `skill_id` and `change_id`) is also stored on the proposed_change's `research` sub-object as `research.skill_definition` for easy access by BR sub-agents.

**Write pattern:** RI writes `plugin_bundles[]` to `opportunities.json`, then SA reads it. SA enriches each bundle with client-facing card content (what_it_does, inputs_summary, source_quotes, etc.) and writes the enriched cards into `strategy.json` as `service_tier_recommendation.mid_ticket.plugin_cards[]`.

### opportunities.proposed_changes

Initially populated by EI, then enriched by RI, SA, BR, VR. Each change maps to one or more `affected_step_ids` and links to pain points AND/OR optimisations.

```json
"proposed_changes": [
  {
    "change_id": "CHG-001",
    "title": "",
    "change_type": "automation|integration|ai|process|tool-replacement|custom-build",
    "source": "client|analyst",
    "initiative_type": "cowork_plugin|automation|data_migration|custom_build|process|null",
    "solution_type": "cowork_plugin|automation|data_migration|custom_build|process",
    "stage": "",
    "confidence": "HIGH|MEDIUM|LOW",
    "value_type": "time-saving|risk-reduction|revenue|compliance|customer-experience",
    "affected_step_ids": [],
    "linked_roi_item_id": "",
    "linked_pain_point_ids": [],
    "linked_optimisation_ids": [],
    "linked_waste_item_ids": [],
    "source_evidence": [
      {
        "ref_id": "PP-008",
        "ref_type": "pain_point|waste_item|optimisation",
        "quote": "verbatim utterance",
        "speaker": "",
        "source_session": 1,
        "source_timestamp_seconds": 1302,
        "fathom_url": "https://fathom.video/calls/.../?t=1302"
      }
    ],
    "proposed_solution": "",
    "proposed_tools": [],
    "time_saving_minutes_per_occurrence": null,
    "frequency": "",
    "phase": 1,
    "phase_label": "",
    "sequence_order": 1,
    "depends_on": [],
    "plugin_candidate": false,
    "research_summary": "",

    "research": { ... },
    "implementation": { ... },
    "value": { ... },
    "modal_content": { ... },

    "build_cost_range_aud": "",
    "payback_months": null,
    "risk_label": "LOW|MEDIUM|HIGH",

    "future_step_label": "",
    "future_step_description": "",
    "future_step_tool_ids": [],
    "future_step_owner": "",
    "future_step_time_estimate_hours_per_week": null
  }
]
```

- `source` -- `"client"` (from transcripts via EI), `"analyst"` (new opportunity generated by RI), or `"control_gap"` (generated from control_gaps[], added sprint-5).
- `research_summary` -- 200-300 char summary written by RI sub-agent after research completes.

### Sprint 5-6 fields on proposed_changes[]

| Field | Type | Notes |
|-------|------|-------|
| volume_weight | number | 0.0-1.0. From upstream gateway volume annotation. Default 1.0. |
| blocked_by_gaps | string[] | Gap IDs affecting this change's scope. Empty array if none. Always present. |
| source_handoff_ids | string[] | sequence_flow IDs that triggered this change via transfer mechanism scan. |
| control_gap_ids | string[] | control_gap IDs this change addresses. | Format: "Feasible via {tool}. {n} tools evaluated. Plugin: {yes/no}. Quick win: {yes/no}. Key risk: {one sentence}." Used by BR/VR/Designer for cross-change reasoning without loading the full `research` object.
- `linked_optimisation_ids` -- array of OPT-xxx IDs. Changes can originate from optimisations (opportunities) not just pain points.
- `linked_waste_item_ids` -- array of W-xxx IDs. Replaces the legacy pattern of regex-parsing `value.formula` for W-IDs. Written by EI on creation and kept in sync by RI/BR when waste links change.
- `source_evidence` -- **flat, de-duped list (typically 3–8 entries) of every quote that grounds this change**. Each entry carries the full citation tuple `(quote, speaker, source_session, source_timestamp_seconds, fathom_url)` so renderers and the PDF report can show "where this came from" without joining files. De-dupe key: `(source_session, source_timestamp_seconds)`. Written by EI on creation, refreshed by RI/BR when linked pain points / waste items change. `fathom_url` is the full deep-link including `?t={timestamp}` — pre-computed using `extraction.sessions[].fathom_url`.
- `change_type` semantics: `automation` (software replaces person), `integration` (connect existing tools), `tool-replacement` (swap tool/method), `custom-build` (bespoke development), `process` (change how work is done, no tech change)
- `value_type` -- `"multiple"` when the change delivers more than two value dimensions

#### research sub-object (written by RI)

```json
"research": {
  "status": "pending|complete",
  "tools_researched": [
    {
      "tool_name": "",
      "url": "",
      "pricing_aud": "",
      "per_user_monthly_aud": null,
      "flat_monthly_aud": null,
      "annual_cost_aud": null,
      "pricing_model": "per_user|flat|per_unit|free|usage_based|custom",
      "pricing_source_type": "official|aggregator|blog|estimated|training_knowledge",
      "pricing_verified_date": "",
      "pricing_is_estimated": false,
      "pricing_url": "",
      "docs_url": "",
      "api_available": null,
      "api_notes": "",
      "integrations": [],
      "hidden_costs": [
        {
          "type": "upsell|add_on|implementation|onboarding|data_migration|overage|minimum_commitment|support_tier|api_access",
          "description": "",
          "estimated_cost_aud": null,
          "estimated_annual_aud": null,
          "trigger": "",
          "likelihood": "likely|possible|unlikely",
          "source_url": ""
        }
      ],
      "total_cost_with_hidden_aud": null,
      "requires_paid_plan": false,
      "realistic_tier": "",
      "realistic_annual_cost_aud": null,
      "free_plan_limitations": [],
      "setup_cost_aud": null,
      "data_silo_risk": "",
      "pros": [],
      "cons": [],
      "integration_with_existing": "",
      "verdict": "recommended|viable|not-suitable",
      "notes": "",
      "confidence": "HIGH|MEDIUM|LOW"
    }
  ],
  "custom_build_option": {
    "modules": [],
    "estimated_weeks": null,
    "tech_stack": [],
    "scope_level": "configure_existing|medium_customisation|custom_build|heavy_custom",
    "feasible": true,
    "advantages": [],
    "disadvantages": [],
    "confidence": "HIGH|MEDIUM|LOW"
  },
  "plugin_assessment": {
    "is_plugin_candidate": false,
    "plugin_title": "",
    "plugin_rationale": "",
    "plugin_scope": "",
    "target_user": "",
    "complexity_tier": "simple|standard|complex",
    "price_range": { "low": null, "high": null },
    "annual_saving_aud": null,
    "data_layer": ""
  },
  "industry_landscape": {
    "common_approaches": "",
    "best_practice": "",
    "competitive_position": "",
    "quantitative_benchmarks": [
      {
        "metric": "",
        "client_value": null,
        "unit": "",
        "industry_avg": null,
        "top_quartile": null,
        "source": "",
        "source_url": "",
        "delta": ""
      }
    ]
  },
  "migration_research": {
    "current_tool": "",
    "current_tool_monthly_cost_aud": null,
    "migration_trigger": "closed_api|duplicate_records|cost_reduction",
    "alternative_tools": [
      {
        "tool_name": "",
        "api_available": true,
        "monthly_cost_aud": null,
        "migration_complexity": "simple|moderate|complex",
        "source_url": ""
      }
    ],
    "recommended_alternative": null,
    "migration_complexity": "simple|moderate|complex",
    "data_volume_estimate": "",
    "estimated_migration_weeks": null,
    "annual_cost_delta_aud": null
  },
  "feasibility_notes": "",
  "risks": [
    {
      "description": "",
      "severity": "low|medium|high",
      "category": "technical|adoption|operational|financial",
      "mitigation_hint": ""
    }
  ],
  "gaps": [],

  "transfer_mechanism_addressed": null,
  "integration_pair": null,
  "gap_status": "clear",
  "gap_blockers": []
}
```

Pricing confidence: HIGH = official/recent aggregator (< 3 months); MEDIUM = blog or older aggregator; LOW = training knowledge or "Contact sales".

### research sub-object additions (added sprint-6)

| Field | Type | Notes |
|-------|------|-------|
| research.transfer_mechanism_addressed | string | The specific mechanism this change fixes |
| research.integration_pair | object | {source_tool, destination_tool, integration_method, native_integration_available, integration_name, setup_url, data_mapped, estimated_dev_hours_if_custom} |
| research.gap_status | "clear"\|"partially_blocked"\|"blocked" | |
| research.gap_blockers | string[] | Gap IDs that affected research scope |

`hidden_costs[].likelihood`: `"likely"` costs feed into `total_cost_with_hidden_aud`. `"possible"` and `"unlikely"` are informational.

#### implementation sub-object (written by BR)

```json
"implementation": {
  "weeks_estimate": null,
  "weeks_label": "<1 week|1-2 weeks|2-4 weeks|4+ weeks",
  "dev_hours": null,
  "pm_hours": null,
  "effort_breakdown": {},
  "phase_placement": "",
  "confidence": "HIGH|MEDIUM|LOW"
}
```

- `weeks_estimate` -- decimal weeks for priority matrix X axis
- `dev_hours` / `pm_hours` -- internal effort, not shown to client

#### value sub-object (written by BR)

```json
"value": {
  "time_saving": {
    "hours_per_week": null,
    "hourly_rate_aud": null,
    "annual_saving_aud": null,
    "formula_summary": ""
  },
  "productivity_enhancement": {
    "description": "",
    "current_revenue_or_metric": null,
    "improvement_percentage": null,
    "estimated_annual_value_aud": null,
    "formula": "",
    "confidence": "HIGH|MEDIUM|LOW"
  },
  "risk_reduction": {
    "risk_type": "compliance|data_loss|key_person|revenue_exposure|safety",
    "current_exposure_aud": null,
    "mitigation_percentage": null,
    "estimated_annual_value_aud": null,
    "narrative": "",
    "confidence": "HIGH|MEDIUM|LOW"
  },
  "customer_experience": {
    "metric": "",
    "current_value": null,
    "improved_value": null,
    "unit": "",
    "revenue_impact_aud": null,
    "narrative": "",
    "confidence": "HIGH|MEDIUM|LOW"
  },
  "scalability": {
    "current_capacity_metric": "",
    "new_capacity_metric": "",
    "additional_staff_avoided": null,
    "avoided_salary_aud": null,
    "narrative": "",
    "confidence": "HIGH|MEDIUM|LOW"
  },
  "combined_annual_value_aud": null
}
```

- `combined_annual_value_aud` = sum of all value dimension annual values. Used for priority matrix Y axis.
- `risk_reduction` -- for compliance breaches, data loss exposure, key-person dependency.
- `customer_experience` -- response time improvement, error rate reduction, NPS impact.
- `scalability` -- "grow from 25 to 50 contractors without adding admin staff".
- All value dimensions are optional. Populate when the change genuinely delivers that type of value.

#### modal_content sub-object (written by BR)

```json
"modal_content": {
  "problem_statement": "",
  "current_state": "",
  "proposed_solution": "",
  "value_delivered": "",
  "implementation_path": "",
  "meeting_references": [
    { "session": "S1", "timestamp_seconds": null, "fathom_url": "", "transcript_excerpt": "" }
  ]
}
```

#### Other proposed_change fields (written by BR)

- `risk_label` -- max 40 characters, plain English (e.g. "touches live revenue flow")
- Build cost benchmarks by initiative_type: cowork_plugin $3K-$8K, automation $2K-$5K, custom_build $50K-$150K, data_migration $3K-$8K
- `payback_months` = `build_cost_range_aud.low / (combined_annual_value_aud / 12)`

### opportunities.roi_items

```json
"roi_items": [
  {
    "roi_id": "ROI-001",
    "linked_change_id": "CHG-001",
    "description": "",
    "annual_saving_aud": null,
    "one_time_cost_aud": null,
    "payback_months": null
  }
]
```

### opportunities.risk_register

```json
"risk_register": [
  {
    "risk_id": "RSK-001",
    "title": "",
    "description": "",
    "likelihood": "HIGH|MEDIUM|LOW",
    "impact": "HIGH|MEDIUM|LOW",
    "severity": "low|medium|high",
    "category": "technical|adoption|operational|financial",
    "mitigation": "",
    "mitigation_hint": "",
    "linked_change_ids": [],
    "source": "transcript|research|analyst"
  }
]
```

---

## strategy domain (written by Researcher)

Domain path: `strategy.*`

```json
"strategy": {
  "strategic_approaches": { ... },
  "transformation_blueprint": { ... }
}
```

### strategy.strategic_approaches (written by SA)

```json
"strategic_approaches": {
  "recommended_tier": "low_ticket|mid_ticket|high_ticket",
  "recommended_tier_rationale": "",
  "approach_rationale": {
    "evidence_items": [],
    "summary": ""
  },
  "service_tier_recommendation": {
    "low_ticket": {
      "label": "AI OS Setup",
      "price_range_aud": "$5,000 – $8,000",
      "description": "",
      "inclusions": []
    },
    "mid_ticket": {
      "label": "Plugin Suite",
      "price_range_aud": "$10,000 – $25,000",
      "description": "",
      "plugin_cards": [
        {
          "plugin_title": "",
          "plugin_scope": "",
          "target_user": "",
          "process": "",
          "pain_point_ids": [],
          "covered_change_ids": [],
          "estimated_weeks": null,
          "price_range_aud": "",
          "source_quotes": [
            {
              "quote": "",
              "speaker": "",
              "source_session": null,
              "source_timestamp_seconds": null,
              "fathom_url": "",
              "derived_from_change_id": "",
              "ref_id": "PP-008",
              "ref_type": "pain_point|waste_item|optimisation"
            }
          ]
        }
      ],
      "plugin_count": 0,
      "total_annual_saving_aud": null
    },
    "high_ticket": {
      "label": "Custom Build",
      "price_range_aud": "$60,000+",
      "description": "",
      "modules": [],
      "estimated_sprints": null
    }
  },
  "implementation_roadmap": {
    "foundation_layer": "",
    "starting_point": "",
    "stages": [],
    "end_state": ""
  },
  "total_annual_value_aud": null,
  "total_proposed_changes": 0,
  "plugin_candidate_count": 0,
  "verification": {}
}
```

- `plugin_cards[].source_quotes[]` -- **every entry must carry a populated `fathom_url` plus `source_session` and `source_timestamp_seconds`**. SA aggregates these from each `covered_change_ids[]` change's `source_evidence[]`, de-dupes by `(source_session, source_timestamp_seconds)`, and picks the 2–4 strongest quotes per card. `derived_from_change_id` is the proposed_change the quote was carried via — used by the renderer to group sources by initiative.
- `plugin_cards[].covered_change_ids[]` -- mandatory pointer to the proposed_changes this plugin bundles. Drives both ROI roll-up and source aggregation.

### strategy.transformation_blueprint (written by BO)

```json
"transformation_blueprint": {
  "phases": [
    {
      "phase_number": 1,
      "label": "Quick Wins",
      "tier_code": "QUICK_WIN",
      "timeframe": "Weeks 1-3",
      "start_week": 1,
      "effective_duration_weeks": 3,
      "description": "Short sentence on what gets done in this phase.",
      "total_annual_value_aud": 28000,
      "change_ids": ["CH-001", "CH-002"]
    }
  ],
  "total_phases": 3,
  "estimated_total_weeks": 12,
  "total_annual_value_aud": null,
  "short_term_outlook": {
    "summary": "Plain-English explanation of what the first 0-3 months look like and what the team will feel.",
    "highlights": [
      "Bullet on the first measurable win",
      "Bullet on what stops being painful",
      "Bullet on the foundation it sets up"
    ]
  },
  "long_term_outlook": {
    "summary": "Plain-English explanation of what the company looks like in 6 to 18 months once foundations are in place.",
    "highlights": [
      "Bullet on data unification outcome",
      "Bullet on what AI now does that it couldn't before",
      "Bullet on flexibility kept for future AI updates"
    ]
  },
  "risk_outlook": {
    "summary": "Plain-English narrative on the top risks this plan mitigates.",
    "risks": [
      {
        "category": "data_flow_context",
        "title": "Short risk title",
        "description": "Plain-English description grounded in the client's actual situation, citing a process or tool by name.",
        "mitigation": "How the plan addresses it."
      }
    ]
  },
  "last_built": ""
}
```

**Phase fields:**
- `tier_code` -- one of `QUICK_WIN`, `CORE_BUILD`, `FUTURE`. Drives Gantt bar colour in the renderer (`#22c55e`, `#3B82F6`, `#f97316`).
- `start_week` -- 1-indexed week the phase bar starts on. Phases run sequentially: phase 2 starts when phase 1 ends.
- `effective_duration_weeks` -- bar width in weeks. BO computes this from member changes' `implementation.estimated_weeks`, summed with reasonable parallel-execution caps.
- `total_annual_value_aud` -- ROI delivered by completing this phase (sum of `value.combined_annual_value_aud` for member `change_ids`).
- `timeframe` -- human-readable label (e.g. `"Weeks 1-3"`, `"Months 4-6"`).

**Outlook fields:**
- `short_term_outlook` -- 2 to 4 sentence narrative on the 0-3 month horizon (quick wins, what the team feels first, what foundation it sets).
- `long_term_outlook` -- 2 to 4 sentence narrative on the 6-18 month horizon (data unification, AI capability unlocked, future flexibility).
- Both outlook blocks include `highlights[]` (3 short bullets).

**Risk fields:**
- `risk_outlook.summary` -- 2 to 4 sentence narrative on top risks the plan mitigates and why the staging protects the business.
- `risk_outlook.risks[].category` -- one of `data_flow_context`, `data_storage_ownership`, `ai_training_adoption`. BO emits at least one risk per category that applies, grounded in real client data (cite tools/processes by name).
- `risk_outlook.risks[].mitigation` -- single sentence on how the plan addresses the risk (often by reference to a phase or initiative).

---

## architecture domain (written by Designer)

Domain path: `architecture.*`

```json
"architecture": {
  "requirements_spec": { ... },
  "architecture_doc": { ... },
  "architecture_verification": { ... },
  "cowork_demos": [ ... ],
  "branding": { ... }
}
```

### architecture.requirements_spec (written by RE)

```json
"requirements_spec": {
  "requirements": [
    {
      "requirement_id": "REQ-001",
      "change_id": "",
      "derived_from_change_ids": [],
      "package_id": "",
      "title": "",
      "user_stories": [
        { "story_id": "", "role": "", "action": "", "outcome": "", "acceptance_criteria": [] }
      ],
      "priority": "must-have|should-have|nice-to-have",
      "complexity": "low|medium|high",
      "notes": ""
    }
  ],
  "user_roles": [
    {
      "role_id": "ROLE-001",
      "name": "",
      "source": "staff_roster|end_user",
      "staff_members": [],
      "affected_packages": [],
      "permission_level": "admin|standard|read-only|external",
      "notes": ""
    }
  ],
  "screen_inventory": [
    {
      "screen_id": "SCR-001",
      "name": "",
      "type": "configuration|dashboard|input|notification|integration",
      "package_id": "",
      "requirement_ids": [],
      "platform": "",
      "description": "",
      "user_roles": [],
      "is_custom_build": false,
      "notes": ""
    }
  ],
  "data_model": {
    "entities": [
      { "entity_id": "", "name": "", "source_system": "", "key_fields": [], "relationships": [], "package_ids": [], "notes": "" }
    ],
    "data_flows": [
      { "flow_id": "", "name": "", "source_entity": "", "source_system": "", "destination_system": "", "trigger": "", "fields_mapped": [], "frequency": "", "package_id": "" }
    ]
  },
  "integrations": [
    {
      "integration_id": "INT-001",
      "name": "",
      "source_system": "",
      "target_system": "",
      "integration_method": "API|webhook|middleware|manual",
      "middleware": "",
      "package_id": "",
      "api_details": { "source_api": "", "target_api": "", "auth_method": "", "rate_limits": "" },
      "data_entities": [],
      "requirements": [],
      "risks": [],
      "notes": ""
    }
  ],
  "summary": {
    "total_requirements": 0,
    "total_user_stories": 0,
    "total_user_roles": 0,
    "total_screens": 0,
    "custom_build_screens": 0,
    "total_entities": 0,
    "total_integrations": 0,
    "total_data_flows": 0
  }
}
```

- `requirements[].derived_from_change_ids[]` -- **mandatory pointer** back to the proposed_changes this requirement implements. Single `change_id` is kept for backward compatibility; new requirements should also populate the array so a requirement can derive from multiple changes (e.g. a shared dashboard serving CH-002 and CH-004). The Designer prototype and the comprehensive-report PDF use this to trace any feature back through CH → PP/W → meeting.

### architecture.architecture_doc (written by BA)

```json
"architecture_doc": {
  "generated_at": "",
  "selected_strategy_id": "",
  "module_inventory": [],
  "user_journeys": [],
  "page_structure": { "pages": [], "navigation": [] },
  "data_models": [],
  "access_policies": [],
  "integration_architecture": [],
  "tech_stack": {}
}
```

See the Solution Architect agent reference for full sub-object shapes of `module_inventory`, `user_journeys`, `page_structure`, `data_models`, `access_policies`, `integration_architecture`, and `tech_stack`.

### architecture.architecture_verification (written by VA)

```json
"architecture_verification": {
  "coverage_matrix": [],
  "pain_point_coverage": [],
  "optimisation_coverage": [],
  "interactivity_issues": [],
  "simplicity_recommendations": [],
  "prototype_brief": [],
  "summary": {
    "total_pain_points": 0,
    "pain_points_fully_covered": 0,
    "pain_points_partial": 0,
    "pain_points_missing": 0,
    "total_optimisations": 0,
    "total_interactivity_issues": 0,
    "prototype_brief_items": 0,
    "verification_pass": false,
    "blocking_issues": []
  }
}
```

### architecture.cowork_demos (written by BC)

```json
"cowork_demos": [
  {
    "change_id": "",
    "scenario_title": "",
    "pain_point_id": "",
    "fathom_link": "",
    "output_files": [],
    "mcp_dependencies": [],
    "fabrication_flags": [],
    "generated_at": ""
  }
]
```

### architecture.branding

```json
"branding": {
  "primary_color": "",
  "secondary_color": "",
  "logo_url": "",
  "font": ""
}
```

---

## Root-Level Metadata Fields

```json
"analyst_metadata": {
  "last_run": "ISO-8601",
  "capabilities_run": [],
  "last_analysis_run": "",
  "total_runs": 0,
  "changes_researched": 0,
  "changes_with_gaps": 0,
  "new_opportunities_generated": 0,
  "notes": ""
},
"architect_metadata": {
  "last_run": "ISO-8601",
  "capabilities_run": [],
  "last_re_run": "",
  "total_re_runs": 0,
  "requirements_extracted": 0,
  "packages_covered": [],
  "last_ba_run": "",
  "total_ba_runs": 0,
  "last_va_run": "",
  "total_va_runs": 0,
  "last_va_pass": false,
  "va_blocking_issues": 0,
  "last_bp_run": "",
  "total_bp_runs": 0,
  "prototype_pages": 0,
  "prototype_path": "",
  "last_bc_run": "",
  "total_bc_runs": 0,
  "bc_demos_generated": 0,
  "notes": ""
}
```

---

## Agent Read/Write Summary

| Section (v3 path) | Extractor (3) | Researcher (4) | Builder (5) | Designer (6) |
|---------|:---:|:---:|:---:|:---:|
| `meta.*` (identity, CRM, contact, blended rate) | W | R | R | R |
| `extraction.sessions[]`, `extraction.extracted_materials[]` | W | R | R | R |
| `extraction.processes[]`, `extraction.decision_nodes[]` | W | R | R | R |
| `extraction.tools[]` | W | R | R | R |
| `extraction.staff_roster[]` | W | R | - | R |
| `extraction.business_metrics[]` | W | R/W | - | R |
| `extraction.client_context` | W | R | R | R |
| `findings.pain_points[]`, `findings.optimisations[]` | W | R | R | R |
| `findings.waste_items[]` | W | R | R | R |
| `findings.change_readiness` | W | R | R | R |
| `findings.contradictions[]` | W | - | R | - |
| `findings.completeness_checklist` | W | - | - | - |
| `findings.follow_up_questions[]` | W | - | - | - |
| `opportunities.roi_items[]` | - | W | R | - |
| `opportunities.proposed_changes[]` | - | W | R | R |
| `opportunities.risk_register[]` | - | W | R | R |
| `strategy.strategic_approaches` | - | W | R | R |
| `strategy.transformation_blueprint` | - | W | R | R |
| `analyst_metadata` | - | W | - | - |
| `architecture.requirements_spec` | - | - | R | W |
| `architecture.architecture_doc` | - | - | R | W |
| `architecture.architecture_verification` | - | - | R | W |
| `architecture.cowork_demos[]` | - | - | - | W |
| `architect_metadata` | - | - | - | W |

W = writes, R = reads, - = does not access
