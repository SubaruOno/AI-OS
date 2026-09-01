# APG Audit Pipeline — Complete Reference

This document explains the full APG audit pipeline end-to-end. For the authoritative agent/capability table see `context/pipeline/apg-pipeline.md`.

## 1. Pipeline Overview

The APG audit runs through six phases:

1. **Pre-Engagement** — Research prospect, run discovery call, generate close page
2. **Sessions 1–N** — Map processes, extract pain points, quantify waste
3. **Process Map Complete** — Synthesise proposed changes, research tools, estimate value
4. **Build Deliverables** — Generate strategic approaches, comprehensive report
5. **Presentation** — Walk client through `strategic-approaches.html`
6. **Post-Presentation** — Extract requirements, build architecture, generate prototype

## 2. Agents & Capabilities

| Skill | Code | Capability | Runs When |
|-------|------|------------|-----------|
| 3-audit-extractor | SU | sync-and-update | After every session |
| 3-audit-extractor | AC | audit-check | On demand |
| 3-audit-extractor | GQ | generate-questions | After SU |
| 4-improvement-researcher | EI | extract-improvements | audit_status = process_map_complete |
| 4-improvement-researcher | RI | research-improvements | After EI |
| 4-improvement-researcher | SA | build-strategic-approaches | After RI |
| 4-improvement-researcher | BR | build-and-rate | After SA |
| 4-improvement-researcher | VR | verify-research | After BR |
| 5-deliverable-builder | GP | generate-process-map | After SU |
| 5-deliverable-builder | GF | generate-findings | After SU |
| 5-deliverable-builder | GV | generate-waste | After waste items identified |
| 5-deliverable-builder | GS | generate-solutions-overview | After RI |
| 5-deliverable-builder | GA | generate-strategic-approaches | After SA |
| 5-deliverable-builder | GC | generate-comprehensive-report | After VR |
| 5-deliverable-builder | GW | generate-website | After any update |
| 6-solution-designer | RE | extract-requirements | After VR (pre-presentation) |
| 6-solution-designer | BA | build-architecture | After RE |
| 6-solution-designer | BP | build-prototype | After BA |

## 3. Data Flow

All agents read from and write to: `clients/{client_slug}/03-audit/data/` (v4 multi-file) or `clients/{client_slug}/03-audit/data/audit-data.json` (v3 legacy).

| From | To | What travels |
|------|----|-------------|
| Extractor [SU] | Researcher [EI] | processes[], tools[], pain_points[], optimisations[], waste_items[] |
| Researcher [EI] | Researcher [RI] | proposed_changes[], roi_items[] |
| Researcher [RI] | Researcher [SA] | proposed_changes[].research, new proposed_changes[] |
| Researcher [SA] | Builder [GA] | strategic_approaches.service_tier_recommendation |
| Researcher [BR] | Researcher [VR] | proposed_changes[].implementation, .value, .modal_content |
| Researcher [VR] | Solution Designer [RE] | verified proposed_changes[], strategic_approaches{} |
| Solution Designer [RE→BA→BP] | Builder [GC] | requirements_spec{}, architecture_doc{} |

## 4. Deliverables

| File | Generator | Description | When |
|------|-----------|-------------|------|
| `1-client-website.html` | GW | Progressive client portal with session unlocks | After every update |
| `2-process-map.html` | GP | Zone-based current-state process map with waste heatmap | After each session |
| `3-findings.html` | GF | Pain points and optimisations grouped by stage with quotes | After each session |
| `4-waste.html` | GV | Quantified waste breakdown with hours and annual costs | After waste items identified |
| `5-blueprint.html` | GB | AI Blueprint scroll journey: initiative cards, priority matrix, phased roadmap | After Researcher [BR] |

## 5. Client Folder Structure

```
clients/{client_slug}/
  00-admin/                  ← MSA, contracts
  01-materials/
    meetings/                ← Meeting transcripts + metadata (from CRM)
    documents/               ← client-provided PDFs, spreadsheets, Looms
    emails/                  ← fetched email threads
  02-sales/                  ← close page, proposals
  03-audit/
    data/                    ← audit domain files (meta.json, extraction.json, …)
    deliverables/            ← generated HTML files (1- through 5-)
    handoff/                 ← versioned client handoff zips (v1/, v2/, …)
    prototype/               ← clickable HTML prototype (Solution Designer)
    reviews/                 ← feedback review rounds (Agent 7)
  {04+}-{engagement-slug}/   ← numbered implementation engagements
  _archive/                  ← completed/superseded items
```

## 6. Design Tokens

All HTML outputs use these consistent design tokens:
- **Primary accent:** `#7DFF00` (APG lime)
- **Dark background:** `#0f1825`
- **Light background:** `#f7f9fc`
- **Font:** Inter (Google Fonts)
- All deliverables are self-contained single HTML files (no external dependencies beyond fonts)
