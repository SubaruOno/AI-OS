---
name: diagram
description: >
  Create and update workspace architecture diagrams using D2. System diagrams, architecture diagrams,
  data flow diagrams, flowcharts, visual maps, process diagrams. Render diagrams to SVG.
  Workspace color scheme, diagram conventions.
---

# D2 Workspace Diagrams

Architecture diagrams authored in D2, rendered to SVG for portable viewing.

## Quick Start

1. Create/edit `.d2` file in `diagrams/`
2. Render: `d2 --layout elk --theme 0 --pad 40 your-diagram.d2 your-diagram.svg`
3. Validate: inspect the rendered SVG with the current harness's image or browser tool
4. Iterate if needed

**Install:** macOS may use `brew install d2`; on Windows use the current D2 release or a supported package manager from the official D2 instructions.
**Render command:** `d2 --layout elk --theme 0 --pad 40 input.d2 output.svg`

## Creating Your First Diagram

```bash
# Create a new .d2 file in diagrams/
# Render: d2 --layout elk --theme 0 --pad 40 your-diagram.d2 your-diagram.svg
```

## D2 Syntax Quick Reference

```d2
# Shapes
server: Web Server { shape: rectangle }
db: Database { shape: cylinder }
user: User { shape: person }

# Connections
server -> db: queries
user -> server: requests

# Nested containers
parent: Parent Label {
  child1: Child One
  child2: Child Two
}

# Cross-container connections
parent1.child -> parent2.child: label

# Styling
node: Label {
  style.fill: "#2980b9"
  style.font-color: "#ffffff"
  style.stroke-dash: 5
  style.bold: true
}

# Layout
direction: down  # or right

# Line breaks in labels
node: "Line One\nLine Two"
```

**Dollar sign warning:** `$` is reserved for variable substitution. Avoid using `$` in labels.

## Color Scheme

Suggested defaults (customize for your brand):

| Element | Color | Hex |
|---------|-------|-----|
| Primary business | Blue | `#2980b9` |
| Secondary area | Purple | `#8e44ad` |
| Revenue/Sales | Green | `#27ae60` |
| Content/Marketing | Red | `#e74c3c` |
| Infrastructure/Data | Dark | `#1a1a2e` |
| External/Partners | Orange | `#f39c12` |
| Third parties | Gray | `#95a5a6` |

## Render Options

```bash
d2 --layout elk --theme 0 --pad 40 input.d2 output.svg   # ELK layout (default)
d2 --layout dagre --theme 0 --pad 40 input.d2 output.svg # Dagre layout
d2 --layout elk --theme 6 --pad 40 input.d2 output.svg   # Grape Soda theme
```

## Visual Validation Loop

After rendering, inspect each SVG with the current harness to verify:
- Accurate content and correct connections
- Readable layout (no overlaps)
- Correct color coding

## When to Update Diagrams

Update when workspace structure changes:
- New integration connected
- New workflow or command added
- New automation built
- Business structure changes

> **Full D2 conventions and examples:** `references/conventions.md`

---

## Maintenance

> **Self-improvement rule:** If you used this skill and discovered something not documented here — a gotcha, API quirk, new pattern, or better approach — add it below before finishing your task.

### Known Gotchas

(none yet)
