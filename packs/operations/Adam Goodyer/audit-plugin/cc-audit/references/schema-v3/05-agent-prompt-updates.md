# 05 — Agent Prompt Updates

> Per-capability changes for all agent files that read from or write to audit-data.json.
> This is Session 6 work. Do NOT execute until generate.py and validation are updated
> and both JLR and riverside-dental have been verified on v3.

## Why Update Agent Prompts

The nested structure exists in the file, but agents won't benefit from selective loading until their prompts tell them which domains to load. The `_section_index` block at the top of every v3 audit-data.json file provides line ranges for each domain, enabling agents to use `Read(path, offset, limit)` to load only what they need.

## Reading Pattern for v3 Files

For every agent, the pattern is:
1. Read the first ~60 lines of audit-data.json to get `_section_index` and `meta`
2. Identify which domains you need for this capability (see table below)
3. Use the `line_start` and `line_end` values from `_section_index` to read only those domain blocks

Example (loading `meta` + `findings` for waste page generation):
```
Read clients/brightside-services/audit/audit-data.json, lines 1-60 -> get _section_index
findings.line_start = 2101, findings.line_end = 6500
Read clients/brightside-services/audit/audit-data.json, offset=2101, limit=4399
```

## Writing Pattern for v3 Files

Agents write to the correct nested path, not to top-level keys. For example:
- **v2 write:** `ssad["pain_points"] = updated_list`
- **v3 write:** `ssad["findings"]["pain_points"] = updated_list`

When writing to a v3 file, the agent must preserve the domain structure. The safest approach is:
1. Load the full file
2. Update only the specific domain and keys that this capability owns
3. Write the full file back

## Capability Domain Requirements

| Agent | Capability File | Domains Needed (read) | Domains Written (write) |
|---|---|---|---|
| 3 Extractor | `sync-and-update.md` | meta, extraction, findings | meta, extraction, findings |
| 3 Extractor | `audit-check.md` | meta, extraction, findings | findings (contradictions, follow_up_questions) |
| 3 Extractor | `generate-questions.md` | meta, extraction, findings | findings (follow_up_questions, follow_up_summary) |
| 3 Extractor | `merge-extraction.md` | meta, extraction, findings | meta, extraction, findings |
| 3 Extractor | `process-review.md` | meta, extraction | extraction (processes) |
| 3 Extractor | `waste-review.md` | meta, findings | findings (waste_items) |
| 3 Extractor | `findings-review.md` | meta, findings | findings (pain_points, optimisations) |
| 3 Extractor | `ingest-materials.md` | meta, extraction | extraction (extracted_materials) |
| 3 Extractor | `resolve-questions.md` | meta, extraction, findings | findings (follow_up_questions) |
| 4 Researcher | `extract-improvements.md` | meta, extraction, findings | opportunities (proposed_changes, roi_items) |
| 4 Researcher | `research-improvements.md` | meta, extraction, findings, opportunities | opportunities (proposed_changes.research), extraction (processes.plugin_scope) |
| 4 Researcher | `build-strategic-approaches.md` | meta, extraction, findings, opportunities | strategy (strategic_approaches) |
| 4 Researcher | `build-and-rate.md` | meta, extraction, findings, opportunities | opportunities (proposed_changes.implementation, .value, .modal_content, .build_cost_range_aud, .payback_months, .risk_label) |
| 4 Researcher | `verify-research.md` | meta, extraction, findings, opportunities, strategy | opportunities (proposed_changes corrections), strategy (strategic_approaches.verification) |
| 6 Designer | `extract-requirements.md` | meta, extraction, findings, opportunities, strategy | architecture (requirements_spec) |
| 6 Designer | `build-architecture.md` | meta, extraction, opportunities, architecture | architecture (architecture_doc) |
| 6 Designer | `verify-architecture.md` | meta, opportunities, architecture | architecture (architecture_verification) |
| 6 Designer | `build-prototype.md` | meta, extraction, findings, opportunities, strategy, architecture | architecture (branding) |
| 6 Designer | `build-cowork-demo.md` | meta, extraction, findings, opportunities, strategy | architecture (cowork_demos) |

## Files That Do NOT Need Updating

The Builder (Agent 5) capability files do NOT need updating. `generate.py` handles the v3 flattening automatically. The builder agent simply calls `python3 scripts/generate.py --client-slug X --output Y` and the script handles everything.

Sub-agent files (`sub-agent-extract.md`, `sub-agent-research.md`, etc.) receive a JSON context packet, not the raw audit file, so they don't need updating either.

## Detailed Changes Per Capability

### Agent 3: sync-and-update.md

**File:** `apg-audit-plugin/skills/3-audit-extractor/sync-and-update.md`

**Current line 33:**
```
Load `clients/{client_slug}/audit/audit-data.json` (create fresh from `references/audit-data-schema.md` if it doesn't exist).
```

**Replace with:**
```
Load `clients/{client_slug}/audit/audit-data.json` (create fresh from `references/schema-v3/06-schema-reference.md` if it doesn't exist — new clients start on v3 schema).

If the file exists, check `_schema_version`:
- v3 (starts with "3"): the file has a nested domain structure. Read `meta` section using line ranges from `_section_index` to check client state, then load `extraction` and `findings` domains for merge operations.
- v2 (any other): load the full file as before.

When writing back: if v3, write into the correct domain objects (`meta`, `extraction`, `findings`). Never write pain_points, waste_items, processes etc. to the top level.
```

**Current line ~220** (context packet building):
```
- `blended_hourly_rate_aud`, `blended_rate_confidence` — from top-level audit-data.json fields
```

**Replace with:**
```
- `blended_hourly_rate_aud`, `blended_rate_confidence` — from `meta` domain (or top-level for v2 files)
```

### Agent 4: extract-improvements.md

**File:** `apg-audit-plugin/skills/4-improvement-researcher/extract-improvements.md`

**Current step 1 (around line 21):**
```
1. Verify audit data is loaded. If not loaded, halt with instructions.
```

**Replace with:**
```
1. Load audit data for selective context:
   - Read lines 1-60 of `clients/{client_slug}/audit/audit-data.json` to get `_section_index` and `meta`
   - Check `audit_status` in `meta` — must be "process_map_complete" or halt
   - Load `extraction` and `findings` domains using line ranges from `_section_index`
   - Do NOT load `opportunities`, `strategy`, or `architecture` (EI creates opportunities fresh)
```

**At the write step (around line 265):**
```
1. Write updated `proposed_changes[]` and `roi_items[]` to `clients/{client_slug}/audit/audit-data.json`
```

**Replace with:**
```
1. Load the full audit-data.json. For v3 files, write `proposed_changes` and `roi_items` into the `opportunities` domain object. For v2 files, write to top-level keys as before. Save the file.
```

### Agent 4: research-improvements.md

**File:** `apg-audit-plugin/skills/4-improvement-researcher/research-improvements.md`

**Current section 2a (around line 55) "Load shared context":**
```
Read the following from audit-data.json and assemble a `shared_context` JSON object:
```

**Add after "Read the following from audit-data.json":**
```
For v3 files (check `_schema_version`): load only `meta`, `extraction`, `findings`, and `opportunities` domains using `_section_index` line ranges. Do NOT load `strategy` or `architecture`.
For v2 files: load as before.
```

**At write steps:** Update any references to writing `proposed_changes[].research` to specify writing into `opportunities.proposed_changes[].research` for v3 files.

### Agent 4: build-strategic-approaches.md, build-and-rate.md

Same pattern: at the read step, load `meta + extraction + findings + opportunities`. At the write step, write into `strategy` (SA) or `opportunities` (BR) domain for v3 files.

### Agent 4: verify-research.md

Load all domains except `architecture` (`meta + extraction + findings + opportunities + strategy`). Write corrections back to the appropriate domain.

### Agent 6: extract-requirements.md

**Current line 21:**
```
1. Check audit data is loaded and `proposed_changes[]` has implementation + value populated.
```

**Replace with:**
```
1. Load audit data:
   - For v3: load `meta`, `extraction` (for staff_roster, processes.steps), `findings` (for change_readiness), `opportunities`, `strategy` using _section_index line ranges. Skip `architecture` (RE creates it fresh).
   - For v2: load full file.
   Verify `proposed_changes[]` has `implementation` and `value` populated.
```

**At write step (around line 257):**
```
Write the `requirements_spec` top-level object to audit-data.json:
```

**Replace with:**
```
Write the `requirements_spec` to audit-data.json:
- v3: write into `architecture.requirements_spec`
- v2: write to top-level `requirements_spec`
```

### Agent 6: build-architecture.md, verify-architecture.md, build-prototype.md, build-cowork-demo.md

Same pattern for all Designer capabilities:
- Read: load only what the capability needs (see table above)
- Write: write into `architecture` domain for v3 files

## Notes for Implementer

- The key read instruction to add to every capability is: **"For v3 files (check `_schema_version` starts with '3'), use `_section_index` line ranges to load only the domains listed above. For v2 files, load the full file as before."**
- The key write instruction: **"For v3 files, write results into the correct domain object (`meta`, `extraction`, `findings`, `opportunities`, `strategy`, or `architecture`). Never write to top-level keys in v3 files."**
- These are editorial changes to existing prompt files — they don't change the logic of what the agent does, only how it loads and saves data.
