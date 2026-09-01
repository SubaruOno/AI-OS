# 03-audit — Audit Project

All audit pipeline outputs live here.

| Subfolder | Contents | Written by |
|-----------|----------|------------|
| data/ | v4 audit domain files | Extractor, Researcher, Designer |
| deliverables/ | Generated HTML deliverables (numbered: 1- through 5-) | Generator [GP/GF/GV/GB/GW] |
| handoff/ | Versioned client handoff zips (v1/, v2/, ...) | Generator [GH] |
| prototype/ | Clickable prototype built by Solution Designer | Solution Designer [BP] |
| reviews/ | Feedback review rounds (RR-001/, RR-002/, ...) | Feedback Reviewer [IF] |

## data/

v4 audit data schema — one file per domain:

| File | Owner | What goes in it |
|------|-------|-----------------|
| audit-manifest.json | All | Index: version, checksums, domain timestamps, audit_status |
| meta.json | Extractor | Client info, CRM IDs, contact details, blended_hourly_rate |
| extraction.json | Extractor | Processes, tools, staff, sessions, quotes |
| findings.json | Extractor | Pain points, waste items, optimisations, questions |
| opportunities.json | Researcher [EI/RI] | Proposed changes, ROI items, risk register |
| strategy.json | Researcher [SA/BO/BR] | Strategic approaches, service tier recommendation, transformation blueprint |
| architecture.json | Designer [RE/BA/BP] | Requirements spec, architecture doc, prototype reference |
| reviews.json | Feedback Reviewer [IF/AF] | All review rounds, corrections with audit trail |
| ingestion-manifest.json | Extractor | Materials ingestion log |

Read `audit-manifest.json` to check current audit_status and which domains have been populated before running any agent.

Each domain file is **append-only** — agents enrich their own files, never delete fields written by another agent.

## deliverables/

Generated HTML outputs from `generate.py`. Never edit these files directly — re-run the generator if changes are needed.

| File | Generator | When |
|------|-----------|------|
| 1-client-website.html | GW | After every session (progressive unlock) |
| 2-process-map.html | GP | After every session |
| 3-findings.html | GF | After every session |
| 4-waste.html | GV | After waste items identified |
| 5-blueprint.html | GB | After Researcher [BR] pass |
| processes/ | GP | BPMN level 1/2 drill-down pages (subfolder, multiple files) |

All files are self-contained single-page HTML (inline CSS, JS, assets).

## handoff/

Versioned client handoff packages. Each Generator [GH] run creates a new version directory.

```
handoff/
  v1/
    {Company} - Bosar Audit.zip
  v2/
    {Company} - Bosar Audit.zip
  v3/
    {Company} - Bosar Audit.zip
```

Previous versions are never deleted. The zip contains: the 5 numbered deliverables and the BPMN process map drill-downs.

## prototype/

Clickable prototype built by Solution Designer [BP]. Contains the built Next.js app or a ZIP package.

## reviews/

One subfolder per review round, named `RR-{NNN}/` (zero-padded to 3 digits):

```
reviews/
  RR-001/
    transcript.txt        (from Loom or meeting recording)
    metadata.json         (reviewer, date, round number)
    screen-context/       (extracted frames from video)
    feedback-items.json   (structured feedback, before approval)
```

Review round data is also written to `data/reviews.json` once approved.
