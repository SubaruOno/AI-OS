---
name: init
description: First-run setup for APG Process Analyst
menu-code: INIT
---

# First-Run Setup for APG Process Analyst

Welcome! Setting up your workspace.

## Memory Location

Creating `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-process-analyst-sidecar/` for persistent memory.

## Initial Structure

Creating:
- `index.md` — active research engagements, current work, configuration
- `patterns.md` — research patterns learned across clients and industries
- `chronology.md` — research session timeline
- `access-boundaries.md` — read/write/deny zones

## Creating Memory Files

### `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-process-analyst-sidecar/index.md`

```markdown
# APG Process Analyst — Session Index

## Active Engagements
(none yet)

## Configuration
- Default dev rate: $150/hr (internal, not shown to client)
- Default PM rate: $120/hr (internal, not shown to client)
- Value calculation: time_saving (hrs × rate × 52) + productivity_enhancement (metric × improvement %)

## Last Session
(none)
```

### `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-process-analyst-sidecar/access-boundaries.md`

```markdown
# Access Boundaries for APG Process Analyst

## Read Access
- clients/
- assets/
- ${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-process-analyst-sidecar/

## Write Access
- clients/
- ${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-process-analyst-sidecar/

## Deny Zones
- .claude/
- _bmad/core/
- _bmad/bmb/
```

### `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-process-analyst-sidecar/patterns.md`

```markdown
# Research Patterns

## Industry Patterns
(accumulates across audits — tool recommendations, integration paths, common automation opportunities)

## Common Tool Stacks by Industry
(which tools appear together, typical API integration opportunities)

## Effective Research Strategies
(which search queries, tool categories, and comparison approaches produce the best results)

## Value Estimation Patterns
(typical time savings by automation type, typical productivity improvements by AI use case)
```

### `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-process-analyst-sidecar/chronology.md`

```markdown
# Research Chronology

(Research sessions logged here as they accumulate)
```

## Ready

Setup complete! Ready to analyze your first completed audit.
