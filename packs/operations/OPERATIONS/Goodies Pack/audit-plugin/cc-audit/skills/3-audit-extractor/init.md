---
name: init
description: First-run setup for APG Analyst
menu-code: INIT
---

# First-Run Setup for APG Analyst ⚡

Welcome! Setting up your workspace.

## Memory Location

Creating `${CLAUDE_PLUGIN_ROOT}/_memory/apg-analyst-sidecar/` for persistent memory.

## Initial Structure

Creating:
- `index.md` — active audit engagements, current work, configuration
- `patterns.md` — audit patterns learned across clients and industries
- `chronology.md` — session timeline
- `access-boundaries.md` — read/write/deny zones

## Setup Questions

One quick confirmation to get started:

1. **Completeness checklist** — The analyst uses a per-stage checklist to track audit coverage across whatever business areas are discovered during transcript analysis. Industry-specific variants exist for NDIS, home-services, construction, and real estate. Confirm you want these defaults, or provide overrides.

   *(Default: use per-stage checklist + industry variants)*

## Creating Memory Files

Once confirmed, create the following files:

### `${CLAUDE_PLUGIN_ROOT}/_memory/apg-analyst-sidecar/index.md`

```markdown
# APG Analyst — Session Index

## Active Engagements
(none yet)

## Configuration
- Completeness checklist: standard 5-stage + NDIS/home-services/construction variants
- Blended hourly rate: fixed at $50/hr by convention. Never extracted from transcripts or per-staff pay data.

## Last Session
(none)
```

### `${CLAUDE_PLUGIN_ROOT}/_memory/apg-analyst-sidecar/access-boundaries.md`

```markdown
# Access Boundaries for APG Analyst ⚡

## Read Access
- clients/
- assets/
- ${CLAUDE_PLUGIN_ROOT}/_memory/apg-analyst-sidecar/

## Write Access
- clients/
- ${CLAUDE_PLUGIN_ROOT}/_memory/apg-analyst-sidecar/

## Deny Zones
- .claude/
- _bmad/core/
- _bmad/bmb/
```

### `${CLAUDE_PLUGIN_ROOT}/_memory/apg-analyst-sidecar/patterns.md`

```markdown
# Audit Patterns

## Industry Patterns
(accumulates across audits — NDIS, home services, construction, real estate)

## Common Tool Stacks by Industry
(which tools appear together, typical integration gaps)

## Frequent Pain Point Patterns
(which pain points repeat across similar businesses)

## Follow-Up Question Effectiveness
(which questions reliably surface the deepest waste data)
```

### `${CLAUDE_PLUGIN_ROOT}/_memory/apg-analyst-sidecar/chronology.md`

```markdown
# Session Chronology

(Sessions logged here as they accumulate)
```

## Ready

Setup complete! Ready to analyze your first audit session.
