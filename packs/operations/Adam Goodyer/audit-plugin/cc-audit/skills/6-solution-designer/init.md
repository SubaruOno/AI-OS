---
name: init
description: First-run setup for APG Solution Architect
menu-code: INIT
---

# First-Run Setup for APG Solution Architect

Welcome! Setting up your workspace.

## Memory Location

Creating `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-solution-architect-sidecar/` for persistent memory.

## Initial Structure

Creating:
- `index.md` — active engagements, current work, configuration
- `patterns.md` — packaging patterns learned across clients and industries
- `chronology.md` — session timeline
- `access-boundaries.md` — read/write/deny zones

## Creating Memory Files

### `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-solution-architect-sidecar/index.md`

```markdown
# APG Solution Architect — Session Index

## Active Engagements
(none yet)

## Configuration
- Pricing tiers: Micro $1,800 | Standard $3,800 | Complex $6,500 | Sprint $15,000
- Internal dev rate: $150/hr (never shown to client)
- Internal PM rate: $120/hr (never shown to client)
- Minimum target margin: 40%

## Last Session
(none)
```

### `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-solution-architect-sidecar/access-boundaries.md`

```markdown
# Access Boundaries for APG Solution Architect

## Read Access
- clients/
- assets/
- ${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-solution-architect-sidecar/

## Write Access
- clients/
- ${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-solution-architect-sidecar/

## Deny Zones
- .claude/
- _bmad/core/
- _bmad/bmb/
```

### `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-solution-architect-sidecar/patterns.md`

```markdown
# Packaging Patterns

## Platform Clustering Strategies
(accumulates across audits — which platforms group well, typical package sizes)

## Tier Mapping Decisions
(when to tier up/down, margin adjustment patterns, custom pricing triggers)

## Common Package Structures by Industry
(typical package combinations per industry — e.g., NDIS providers always have a rostering package)

## Value Narrative Templates
(effective waste-budget framing language that resonates with clients)
```

### `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-solution-architect-sidecar/chronology.md`

```markdown
# Session Chronology

(Sessions logged here as they accumulate)
```

## Ready

Setup complete! Ready to extract requirements and build architecture.
