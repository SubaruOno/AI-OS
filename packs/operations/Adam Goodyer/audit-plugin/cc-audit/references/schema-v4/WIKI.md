# audit-data.json v4 Schema Migration Wiki

> Load this file first whenever you are working on the v4 schema migration.
> It tells you what's done, what's next, and where the detailed instructions live.

**Migration status: COMPLETE as of 2026-05-12.** Both target clients migrated. All tooling, scripts, agent prompts, hooks, and documentation updated. Plugin wiki refreshed.

## What This Is

We are splitting the single `audit-data.json` file (v3: nested 6-domain object, 6K-13K lines) into 7 separate per-domain files with a manifest index. This eliminates context dilution: each agent reads and writes only its own domain file(s) instead of loading the full file and writing it back.

The manifest file (`audit-manifest.json`) replaces `_section_index` as the index. Domain files contain raw domain dicts (no wrapper). Backward compatibility is maintained: `audit_reader.py` auto-detects v2, v3, and v4 formats and presents the same flat dict interface.

## Migration Scope

| Client | Slug | Migrate? | Status |
|---|---|---|---|
| Brightside Services | `brightside-services` | YES | `[x] migrated 2026-05-12` |
| Riverside Dental | `riverside-dental` | YES | `[x] migrated 2026-05-12` |
| All earlier clients | various | NO | stays on v2/v3 indefinitely |

Future clients start on v4 directly (Agent 3 SU creates all 7 files from scratch on first run).

## Migration Steps Checklist

| Step | Session | Description | Status |
|---|---|---|---|
| 1a | 1 | Create this wiki folder (WIKI.md + 6 reference files) | `[x] done 2026-05-12` |
| 2a | 2 | Extend `audit_reader.py` with v4 functions | `[x] done 2026-05-12` |
| 2b | 2 | Write `migrate_v3_to_v4.py` | `[x] done 2026-05-12` |
| 2c | 2 | Test roundtrip: flatten v3 -> split v4 -> reassemble -> compare | `[x] done 2026-05-12` |
| 3a | 3 | Update `generate.py` load point to use audit_reader | `[x] done 2026-05-12` |
| 3b | 3 | Update `validate_audit_data.py` to use audit_reader | `[x] done 2026-05-12` |
| 3c | 3 | Update `extract_report_content.py` to use audit_reader | `[x] done 2026-05-12` |
| 3d | 3 | Update root scripts (fetch-transcripts, fetch-emails, fetch-drive-folder, generate-team-portfolio) | `[x] done 2026-05-12` |
| 3e | 3 | Update PM plugin scripts (generate_developer_portal, generate_handoff, generate_dev_brief) | `[x] done 2026-05-12` |
| 3f | 3 | Regression test: generate.py --output all on both v3 clients, checksums unchanged | `[x] done 2026-05-12` |
| 4a | 4 | Run `migrate_v3_to_v4.py --client-slug brightside-services` | `[x] done 2026-05-12` |
| 4b | 4 | Verify JLR: generate.py produces identical HTML on v4 data | `[x] done 2026-05-12` |
| 4c | 4 | Verify JLR: validate_audit_data.py passes | `[x] done 2026-05-12` |
| 5a | 4 | Run `migrate_v3_to_v4.py --client-slug riverside-dental` | `[x] done 2026-05-12` |
| 5b | 4 | Verify omniderm same as step 4b-4c | `[x] done 2026-05-12` |
| 6a | 5 | Update Agent 3 capability prompts (SU, GQ, AC, etc.) | `[x] done 2026-05-12` |
| 6b | 5 | Update Agent 4 capability prompts (EI, RI, SA, BR, VR) | `[x] done 2026-05-12` |
| 6c | 5 | Update Agent 6 capability prompts (RE, BA, VA, BP, BC) | `[x] done 2026-05-12` |
| 7a | 6 | Update hooks (settings.json, hooks.json) | `[x] done 2026-05-12` |
| 7b | 6 | Update shell scripts (auto-regen-deliverables, auto-regen-after-python, protect-client-data) | `[x] done 2026-05-12` |
| 7c | 6 | Update documentation (audit-data-schema.md, CLAUDE.md, root CLAUDE.md) | `[x] done 2026-05-12` |
| 7d | 6 | Run `/refresh-plugin-wiki apg-audit-plugin` | `[x] done 2026-05-12` |

## Files in This Folder

| File | What It Contains |
|---|---|
| `WIKI.md` | This file. Index and status tracker. |
| `01-manifest-schema.md` | Full `audit-manifest.json` template with field types and update rules |
| `02-audit-reader-v4.md` | New function signatures for v4 multi-file support |
| `03-generate-py-v4.md` | Updated `load_audit_data()` with three-branch version detection |
| `04-migration-runbook.md` | Ordered execution steps by session with verification commands |
| `05-agent-prompt-updates.md` | Per-capability diffs: remove `_section_index`, use domain file reads/writes |
| `06-hook-updates.md` | Before/after diffs for hooks and shell scripts |
| `audit-dir-claude.md` | Template CLAUDE.md copied into each new client's `audit/` directory during bootstrap |

## Where New Scripts Live

| Script | Path | Purpose |
|---|---|---|
| `audit_reader.py` | `apg-audit-plugin/scripts/audit_reader.py` | Extended with v4 multi-file functions (Session 2) |
| `migrate_v3_to_v4.py` | `apg-audit-plugin/scripts/migrate_v3_to_v4.py` | Convert v3 single file to v4 multi-file |

## v4 Target Directory Layout

```
clients/{slug}/audit/
├── audit-manifest.json       # index: schema version, domain checksums, timestamps
├── meta.json                 # ~2KB, always loaded (client info, CRM, audit_status)
├── extraction.json           # processes, tools, sessions, staff (Extractor writes)
├── findings.json             # pain points, waste, questions (Extractor writes)
├── opportunities.json        # proposed changes, ROI (Researcher writes)
├── strategy.json             # strategic approaches, blueprint (Researcher writes)
├── architecture.json         # requirements, architecture, prototype (Designer writes)
├── audit-data.json           # KEPT as read-only backup after migration
├── audit-data-v3-backup.json # copy created by migration script
└── ingestion-manifest.json   # unchanged (separate concern)
```

## v4 Domain Summary

| Domain | File | Write Owner | Context Use Cases |
|---|---|---|---|
| `meta` | `meta.json` | Extractor | Always loaded, all agents (~2KB) |
| `extraction` | `extraction.json` | Extractor | Process map, solutions overview, extractor work |
| `findings` | `findings.json` | Extractor | Findings page, waste page, process map heatmap, blueprint |
| `opportunities` | `opportunities.json` | Researcher | Solutions overview, blueprint, architecture |
| `strategy` | `strategy.json` | Researcher (SA) | Blueprint, comprehensive report |
| `architecture` | `architecture.json` | Designer | Comprehensive report, designer work |

## Schema Improvements (post-migration)

Applied after the v4 migration was complete:

| Date | Change | Files |
|---|---|---|
| 2026-05-12 | Added `research_summary` (200-300 char) field to `proposed_changes[]` — written by RI sub-agents, used by BR/VR/Designer for cross-change reasoning without loading full research data | `audit-data-schema.md`, `sub-agent-research.md`, `research-improvements.md` |
| 2026-05-12 | Added `meeting_references[]` to process `steps[]` output — schema already had the field, sub-agent now emits it | `sub-agent-extract.md` |
| 2026-05-12 | Documented sub-agent context packet cap convention (~10KB max) | `CLAUDE.md`, this file |

## Key Design Decisions

- **Multi-file split.** Each domain is its own JSON file. No more `_section_index` or line-range parsing. Agents read `clients/{slug}/audit/{domain}.json` directly.
- **Manifest is the commit point.** `audit-manifest.json` is written last after all domain files are updated. Auto-regen hook fires only on manifest writes.
- **Backward compatibility via audit_reader.py.** Three-way version detection (v2/v3/v4). All callers get the same flat dict. `generate.py` and other consumers never see the difference.
- **Write domains are strict.** Same ownership as v3. One agent owns each domain file. No cross-domain writes.
- **Domain files contain raw dicts.** No wrapper object. `extraction.json` directly contains `{"processes": [...], "tools": [...], ...}`.
- **save_domain() is the only write path.** Writes domain file, computes SHA-256, updates manifest. Callers must load-merge-save (no partial updates).
- **Migration scope is limited.** Only `brightside-services` and `riverside-dental`. Same allowlist pattern as v3.
- **audit-data.json is kept as backup.** After migration, the v3 file remains but is read-only. Future sessions should never read it when the manifest exists.
