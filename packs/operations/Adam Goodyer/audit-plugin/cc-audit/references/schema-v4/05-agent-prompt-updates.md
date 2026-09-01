# 05 -- Agent Prompt Updates

> Per-capability changes for all agent files that read from or write to audit data.
> This is Session 5 work. Do NOT execute until migration is complete and verified.

## Why Update Agent Prompts

In v4, each domain is its own file. Agents no longer need `_section_index` line ranges or `Read(path, offset, limit)`. They simply `Read(clients/{slug}/audit/{domain}.json)` for each domain they need. Writes target individual domain files instead of writing into domain objects within a single file.

## Reading Pattern for v4 Files

For every agent, the pattern is:
1. Check for `audit-manifest.json` to confirm v4 layout
2. Read `audit-manifest.json` for `audit_status` check (pipeline gating) and `client_slug`
3. Read the specific domain files listed in the capability's requirements table

Example (loading `meta` + `findings` for waste page generation):
```
Read clients/brightside-services/audit/audit-manifest.json -> check audit_status
Read clients/brightside-services/audit/meta.json -> client info, blended rate
Read clients/brightside-services/audit/findings.json -> waste_items, pain_points
```

No offset/limit needed. Each file is a self-contained domain dict.

## Writing Pattern for v4 Files

Agents write directly to domain files:
1. Read the domain file
2. Merge your changes into the existing dict
3. Write the updated dict back to the domain file
4. The Claude Code hook on manifest writes triggers auto-regen (handled automatically when using `save_domain()` from scripts, or manually via Write tool for agent prompts)

For agent prompts that use the Write tool directly (not Python scripts):
```
Write clients/{slug}/audit/{domain}.json with the full domain dict
Then update audit-manifest.json: set domains.{domain}.updated_at to current ISO timestamp
```

## Capability Domain Requirements

| Agent | Capability File | Reads | Writes |
|---|---|---|---|
| 3 Extractor | `sync-and-update.md` | meta, extraction, findings | meta, extraction, findings |
| 3 Extractor | `audit-check.md` | meta, extraction, findings | findings |
| 3 Extractor | `generate-questions.md` | meta, extraction, findings | findings |
| 3 Extractor | `merge-extraction.md` | meta, extraction, findings | meta, extraction, findings |
| 3 Extractor | `process-review.md` | meta, extraction | extraction |
| 3 Extractor | `waste-review.md` | meta, findings | findings |
| 3 Extractor | `findings-review.md` | meta, findings | findings |
| 3 Extractor | `ingest-materials.md` | meta, extraction | extraction |
| 3 Extractor | `resolve-questions.md` | meta, extraction, findings | findings |
| 4 Researcher | `extract-improvements.md` | meta, extraction, findings | opportunities |
| 4 Researcher | `research-improvements.md` | meta, extraction, findings, opportunities | opportunities, extraction (plugin_scope only) |
| 4 Researcher | `build-strategic-approaches.md` | meta, extraction, findings, opportunities | strategy |
| 4 Researcher | `build-and-rate.md` | meta, extraction, findings, opportunities | opportunities |
| 4 Researcher | `verify-research.md` | meta, extraction, findings, opportunities, strategy | opportunities, strategy |
| 6 Designer | `extract-requirements.md` | meta, extraction, findings, opportunities, strategy | architecture |
| 6 Designer | `build-architecture.md` | meta, extraction, opportunities, architecture | architecture |
| 6 Designer | `verify-architecture.md` | meta, opportunities, architecture | architecture |
| 6 Designer | `build-prototype.md` | meta, extraction, findings, opportunities, strategy, architecture | architecture |
| 6 Designer | `build-cowork-demo.md` | meta, extraction, findings, opportunities, strategy | architecture |

## Files That Do NOT Need Updating

- **Builder (Agent 5)** capability files delegate to `generate.py`, which handles v4 loading automatically. No changes needed.
- **Sub-agent files** (`sub-agent-extract.md`, `sub-agent-research.md`, etc.) receive a JSON context packet, not raw audit files.

## Detailed Changes Per Capability

### Agent 3: sync-and-update.md

**File:** `apg-audit-plugin/skills/3-audit-extractor/sync-and-update.md`

**v3 loading instruction (find and replace):**
```
Check `_schema_version`: v3 — use line ranges from `_section_index` to load meta, extraction, findings
```

**v4 replacement:**
```
Check for `audit-manifest.json` in the audit directory:
- If present (v4): read domain files directly:
  - Read `clients/{slug}/audit/meta.json`
  - Read `clients/{slug}/audit/extraction.json`
  - Read `clients/{slug}/audit/findings.json`
- If absent: read `audit-data.json` as v3/v2 (existing behavior)
```

**v3 write instruction (find and replace):**
```
Write into the correct domain objects (meta, extraction, findings) in audit-data.json
```

**v4 replacement:**
```
Write each domain as a separate file:
- Write `clients/{slug}/audit/meta.json` (if meta fields changed)
- Write `clients/{slug}/audit/extraction.json` (processes, tools, sessions, etc.)
- Write `clients/{slug}/audit/findings.json` (pain_points, waste_items, etc.)
After all domain files are written, update `audit-manifest.json`:
  - Set `domains.{domain}.updated_at` for each changed domain
  - Set root `updated_at`
  - If meta changed, copy `audit_status` and `company_name` to manifest root
```

**New client creation (v4 from scratch):**
```
If no audit data exists for this client:
1. Create directory `clients/{slug}/audit/`
2. Create `audit-manifest.json` from template in `references/schema-v4/01-manifest-schema.md`
3. Create all 6 domain files from templates in the same reference
4. Populate `meta.json` with client details from discovery
5. Set `audit_status` to `"in_progress"` in both meta.json and manifest
```

### Agent 4: extract-improvements.md

**v3 loading instruction (find and replace):**
```
Read lines 1-60 of audit-data.json to get _section_index and meta
Load extraction and findings domains using line ranges from _section_index
```

**v4 replacement:**
```
Read `clients/{slug}/audit/audit-manifest.json` to check `audit_status`
- Must be "process_map_complete" or halt
Read domain files:
- `clients/{slug}/audit/meta.json`
- `clients/{slug}/audit/extraction.json`
- `clients/{slug}/audit/findings.json`
Do NOT read opportunities.json (EI creates it fresh)
```

**v3 write instruction (find and replace):**
```
Write proposed_changes and roi_items into the opportunities domain object
```

**v4 replacement:**
```
Write `clients/{slug}/audit/opportunities.json` with the full opportunities dict:
  {"proposed_changes": [...], "roi_items": [...], "risk_register": [...]}
Update `audit-manifest.json`: set domains.opportunities.updated_at
```

### Agent 4: research-improvements.md

Same read pattern as EI but also reads `opportunities.json`:
```
Read: meta.json, extraction.json, findings.json, opportunities.json
Write: opportunities.json (proposed_changes[].research), extraction.json (processes[].plugin_scope)
```

Note: RI is the one Researcher capability that also writes to `extraction` (specifically `processes[].plugin_scope`). This is an acknowledged cross-domain write that exists in v3 too.

### Agent 4: build-strategic-approaches.md

```
Read: meta.json, extraction.json, findings.json, opportunities.json
Write: strategy.json (strategic_approaches)
```

### Agent 4: build-and-rate.md

```
Read: meta.json, extraction.json, findings.json, opportunities.json
Write: opportunities.json (proposed_changes[].implementation, .value, .modal_content, etc.)
```

### Agent 4: verify-research.md

```
Read: meta.json, extraction.json, findings.json, opportunities.json, strategy.json
Write: opportunities.json (corrections), strategy.json (strategic_approaches.verification)
```

### Agent 6: extract-requirements.md

```
Read: meta.json, extraction.json, findings.json, opportunities.json, strategy.json
Write: architecture.json (requirements_spec)
```

### Agent 6: build-architecture.md

```
Read: meta.json, extraction.json, opportunities.json, architecture.json
Write: architecture.json (architecture_doc)
```

### Agent 6: verify-architecture.md

```
Read: meta.json, opportunities.json, architecture.json
Write: architecture.json (architecture_verification)
```

### Agent 6: build-prototype.md

```
Read: meta.json, extraction.json, findings.json, opportunities.json, strategy.json, architecture.json
Write: architecture.json (branding)
```

### Agent 6: build-cowork-demo.md

```
Read: meta.json, extraction.json, findings.json, opportunities.json, strategy.json
Write: architecture.json (cowork_demos)
```

## Notes for Implementer

- The key change in every capability: replace `_section_index` + `Read(path, offset, limit)` with direct `Read(clients/{slug}/audit/{domain}.json)` calls
- The key write change: instead of writing into domain objects within a single file, write each domain as its own file, then update the manifest
- Remove all references to `_section_index` from capability files
- Remove all `line_start`/`line_end` logic
- Keep backward compatibility instructions: "If `audit-manifest.json` does not exist, fall back to v3/v2 single-file behavior"
- These are editorial changes to prompt files, not code changes
