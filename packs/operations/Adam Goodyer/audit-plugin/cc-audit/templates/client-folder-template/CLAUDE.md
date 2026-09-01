# {client-slug} — Bosar Client Folder

Canonical folder structure for Bosar audit delivery. Each numbered folder corresponds to a pipeline phase.

| Folder | Contents | Written by |
|--------|----------|------------|
| 00-admin/ | Contracts, MSA, NDA | Manual |
| 01-materials/ | Meeting transcripts, documents, emails | Extractor [SU], fetch scripts |
| 02-sales/ | Proposals, close pages | Sales Closer |
| 03-audit/data/ | Audit domain files (meta, extraction, findings, opportunities, strategy, architecture) | Extractor, Researcher |
| 03-audit/deliverables/ | Numbered HTML outputs (1- through 5-) | Generator [GP/GF/GV/GB/GW] |
| 03-audit/handoff/ | Versioned zip packages (v1/, v2/, ...) | Generator [GH] |
| 03-audit/prototype/ | Clickable prototype | Solution Designer [BP] |
| 03-audit/reviews/ | Feedback review rounds (RR-001/) | Feedback Reviewer [IF] |
| _archive/ | Completed/superseded items | Manual |

## Naming conventions

- Meetings: `YYYY-MM-DD-title-slug/` containing `transcript.txt` + `metadata.json`
- Emails: `YYYY-MM-DD-subject-slug/` containing `email.html` + `metadata.json`
- Deliverables: `1-client-website.html`, `2-process-map.html`, `3-findings.html`, `4-waste.html`, `5-blueprint.html`
- Handoff zips: `v{N}/{Company} - Bosar Audit.zip` (each run creates a new version, previous versions are preserved)

## Audit data files (03-audit/data/)

The v4 schema splits audit data across domain files:

| File | Owner | Contents |
|------|-------|----------|
| audit-manifest.json | All | Version, checksums, file index |
| meta.json | Extractor | Client info, CRM IDs, audit_status, contact details |
| extraction.json | Extractor | Processes, tools, sessions, staff, quotes |
| findings.json | Extractor | Pain points, optimisations, waste items, questions |
| opportunities.json | Researcher | Proposed changes, ROI items |
| strategy.json | Researcher | Strategic approaches, service tier recommendation, blueprint |
| architecture.json | Designer | Requirements spec, architecture doc, prototype reference |

Never write directly to these files during generation — only Extractor and Researcher agents own them.
