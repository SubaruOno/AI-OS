---
name: init
description: First-run setup for APG Generator
menu-code: INIT
---

# First-Run Setup for APG Generator ⚡

Welcome! Setting up your workspace.

## Memory Location

Creating `${CLAUDE_PLUGIN_ROOT}/_memory/apg-generator-sidecar/` for persistent memory.

## Creating Memory Files

### `${CLAUDE_PLUGIN_ROOT}/_memory/apg-generator-sidecar/index.md`

```markdown
# APG Generator — Session Index

## Active Engagements
(none yet)

## Configuration
- Output path: clients/{slug}/03-audit/deliverables/
- Design tokens: APG orange #FF6B35, white background, Inter/system-ui font

## Last Session
(none)
```

### `${CLAUDE_PLUGIN_ROOT}/_memory/apg-generator-sidecar/access-boundaries.md`

```markdown
# Access Boundaries for APG Generator ⚡

## Read Access
- clients/
- ${CLAUDE_PLUGIN_ROOT}/_memory/apg-generator-sidecar/

## Write Access
- clients/
- ${CLAUDE_PLUGIN_ROOT}/_memory/apg-generator-sidecar/

## Deny Zones
- .claude/
- _bmad/core/
- _bmad/bmb/
```

## Ready

Setup complete! Ready to generate HTML deliverables.
