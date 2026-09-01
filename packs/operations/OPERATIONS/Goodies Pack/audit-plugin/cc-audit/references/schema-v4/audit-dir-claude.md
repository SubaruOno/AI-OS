# Audit Data Directory (v4)

This directory contains structured audit data split into per-domain files. Each file is owned by one agent.

## Files

| File | Owner | What it contains |
|---|---|---|
| `audit-manifest.json` | System | Index: schema version, domain checksums, timestamps. Written last after any domain save. |
| `meta.json` | Extractor | Client info, CRM IDs, contact, blended hourly rate, audit_status. Always read first. |
| `extraction.json` | Extractor | Processes, decision nodes, tools, staff roster, sessions, business metrics. |
| `findings.json` | Extractor | Pain points, waste items, optimisations, contradictions, follow-up questions. |
| `opportunities.json` | Researcher | Proposed changes, ROI items, risk register. |
| `strategy.json` | Researcher | Strategic approaches, transformation blueprint. |
| `architecture.json` | Designer | Requirements spec, architecture doc, verification, prototypes, branding. |
| `ingestion-manifest.json` | Extractor | Tracks which source files have been ingested. Separate concern. |

## Reading

Read domain files directly: `Read clients/{slug}/audit/{domain}.json`. No offset/limit needed.

Check `audit-manifest.json` for quick access to `audit_status` and `company_name` without loading `meta.json`.

## Writing

1. Read the domain file you need to update
2. Merge your changes into the existing dict
3. Write the full dict back to the domain file
4. Update `audit-manifest.json`: set `domains.{domain}.updated_at` and root `updated_at`

For Python scripts, use `save_domain(slug, domain, data)` from `audit_reader.py` which handles steps 3-4 automatically.

## Ownership Rules

- Extractor writes: `meta.json`, `extraction.json`, `findings.json`
- Researcher writes: `opportunities.json`, `strategy.json`
- Designer writes: `architecture.json`
- Exception: Researcher RI also writes `extraction.json` (processes[].plugin_scope only)

Never write to a domain file you don't own.

## Legacy

The `legacy/` subfolder contains pre-v4 backup files (v2 flat, v3 nested single-file formats). These are read-only archives, not used by any active agent or script.
