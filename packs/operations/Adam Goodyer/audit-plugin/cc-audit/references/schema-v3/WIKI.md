# audit-data.json v3 Schema Migration Wiki

> Load this file first whenever you are working on the v3 schema migration.
> It tells you what's done, what's next, and where the detailed instructions live.

**Migration status: Functionally complete as of 2026-05-12.** Both target clients (brightside-services and riverside-dental) are on v3. All tooling and documentation are updated. One step remains: run `/refresh-plugin-wiki apg-audit-plugin` manually to regenerate `apg-audit-plugin/CLAUDE.md` with the updated schema info.

## What This Is

We are restructuring `audit-data.json` from a flat 39-key object to a nested 6-domain object. This gives agents selective context loading: instead of loading a 713KB file, each agent loads only the domains it needs (savings range from 34% to 94% depending on the use case).

The single file is preserved (hooks, deploy, CRM sync all work unchanged). The 19K-line `generate.py` gets a 10-line flattener at its load point so all downstream code works unchanged.

## Migration Scope

| Client | Slug | Migrate? | Status |
|---|---|---|---|
| Brightside Services | `brightside-services` | YES | `[x] migrated 2026-05-12` |
| Riverside Dental | `riverside-dental` | YES | `[x] migrated 2026-05-12` |
| All earlier clients | various | NO | stays on v2 indefinitely |

Future clients start on v3 directly (write nested structure from first SU run).

## Migration Steps Checklist

| Step | Session | Description | Status |
|---|---|---|---|
| 1a | 1 | Create this wiki folder (WIKI.md + 6 reference files) | `[x] done` |
| 2a | 2 | Write `audit_reader.py` | `[x] done 2026-05-12` |
| 2b | 2 | Write `migrate_audit_data.py` | `[x] done 2026-05-12` |
| 2c | 2 | Test roundtrip: flatten JLR v2 -> nest -> flatten -> compare | `[x] done 2026-05-12` |
| 3a | 3 | Update `generate.py:237` (`load_audit_data`) | `[x] done 2026-05-12` |
| 3b | 3 | Update `validate_audit_data.py` | `[x] done 2026-05-12` |
| 3c | 3 | Regression: `generate.py --output all` on JLR (still v2), confirm identical HTML | `[x] done 2026-05-12` |
| 4a | 4 | Run `migrate_audit_data.py --client-slug brightside-services` | `[x] done 2026-05-12` |
| 4b | 4 | Verify JLR: generate.py produces identical HTML on v3 data | `[x] done 2026-05-12` |
| 4c | 4 | Verify JLR: validate_audit_data.py passes | `[x] done 2026-05-12` |
| 5a | 5 | Run `migrate_audit_data.py --client-slug riverside-dental` | `[x] done 2026-05-12` |
| 5b | 5 | Verify omniderm same as step 4b-4c | `[x] done 2026-05-12` |
| 6a | 6 | Update Agent 3 capability prompts (SU, GQ, AC) | `[x] done 2026-05-12` |
| 6b | 6 | Update Agent 4 capability prompts (EI, RI, SA, BR, VR) | `[x] done 2026-05-12` |
| 6c | 6 | Update Agent 6 capability prompts (RE, BA, VA, BP, BC) | `[x] done 2026-05-12` |
| 7a | 7 | Update `references/audit-data-schema.md` canonical schema + per-agent thin pointers | `[x] done 2026-05-12` |
| 7b | 7 | Run `/refresh-plugin-wiki apg-audit-plugin` | `[ ] pending — run manually` |

## Files in This Folder

| File | What It Contains |
|---|---|
| `WIKI.md` | This file. Index and status tracker. |
| `01-domain-mapping.md` | Exact mapping of all 39 current flat keys to their v3 domain |
| `02-audit-reader.md` | Full spec for `audit_reader.py` — function signatures, profiles, CLI, tests |
| `03-generate-py-integration.md` | Exact `load_audit_data()` replacement with before/after diff |
| `04-validation-integration.md` | Exact `validate_audit_data.py` change with before/after diff |
| `05-agent-prompt-updates.md` | Per-capability instructions for all 14 capability files |
| `06-schema-reference.md` | Full v3 JSON schema template (replaces current audit-data-schema.md) |
| `07-migration-runbook.md` | Ordered execution steps by session with checkpoint verification |

## Where New Scripts Live

| Script | Path | Purpose |
|---|---|---|
| `audit_reader.py` | `apg-audit-plugin/scripts/audit_reader.py` | Load selective domains, predefined profiles, flatten/nest conversion |
| `migrate_audit_data.py` | `apg-audit-plugin/scripts/migrate_audit_data.py` | Convert v2 flat files to v3 nested for specific clients |

## v3 Domain Summary

| Domain | Keys (count) | Write Owner | Context Use Cases |
|---|---|---|---|
| `meta` | 13 | Extractor | Always loaded, all agents |
| `extraction` | 9 | Extractor | Process map, solutions overview, extractor work |
| `findings` | 12 | Extractor | Findings page, waste page, process map heatmap, blueprint |
| `opportunities` | 3 | Researcher | Solutions overview, blueprint, architecture |
| `strategy` | 2 | Researcher | Blueprint, comprehensive report |
| `architecture` | 5 | Designer | Comprehensive report, designer work |

## Key Design Decisions

- **Single file preserved.** No multi-file split. Hooks, deploy, CRM sync unchanged.
- **Flattener at load point.** `generate.py:237` detects v3 and flattens to the same dict all 19K lines expect. Zero changes to generation logic.
- **Write domains are strict.** One agent owns each domain. Extractor never writes to `opportunities`. Researcher never writes to `extraction`. This prevents data corruption.
- **`waste_items` lives in `findings`.** It is evidence extracted from transcripts (Extractor writes it). The process map profile loads `findings` to get it. No duplication.
- **`_section_index` extended with line ranges.** Enables agents to use `Read(path, offset, limit)` to load only specific sections without parsing the full file.
- **Schema version bump: 2.0.0 -> 3.0.0.** Version detected at load time. Both versions supported by flattener.
- **Earlier clients NOT migrated.** They stay on v2 and the flattener handles them transparently. Only `brightside-services` and `riverside-dental` are migrated.
