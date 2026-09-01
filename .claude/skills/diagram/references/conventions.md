# D2 Workspace Diagram Conventions

> Conventions for D2 diagrams in this workspace.

## Tool Configuration

- **Install:** on macOS, Homebrew may use `brew install d2`; on Windows, follow the current official D2 Windows installation instructions.
- **Layout engine:** ELK (Eclipse Layout Kernel) — cleaner than default Dagre
- **Theme:** 0 (Neutral Default)
- **Render command:** `d2 --layout elk --theme 0 --pad 40 input.d2 output.png`

## Authoring Model

The assistant writes D2 source files directly using workspace knowledge and represents relationships from its understanding of the workspace.

## D2 Syntax Patterns

### Shapes
```d2
server: Web Server { shape: rectangle }
db: Database { shape: cylinder }
doc: Document { shape: document }
hex: Process { shape: hexagon }
user: User { shape: person }
note: "Annotation" { shape: text }
```

### Nested Containers
```d2
ms_ed: Morningside Education {
  style.fill: "#8e44ad"
  style.font-color: "#ffffff"

  accelerator: AAA Accelerator
  skool: Skool Community
  coaching: Coaching Team
}
```

### Connections
```d2
# Simple
a -> b: label
# Cross-container
ms_content.youtube -> ms_ed.skool: "drives joins"
# Bidirectional
a <-> b: "two-way"
```

### Styling
```d2
node: Label {
  style.fill: "#2980b9"
  style.font-color: "#ffffff"
  style.stroke: "#1a5276"
  style.stroke-dash: 5      # dashed border
  style.bold: true
  style.border-radius: 8
}

connection -> target: label {
  style.stroke: "#e74c3c"
  style.stroke-width: 3
}
```

### Layout
```d2
direction: down   # top-to-bottom (default)
direction: right  # left-to-right
```

### Line Breaks
```d2
node: "Line One\nLine Two\nLine Three"
```

## Color Scheme

| Business/Element | Color | Hex |
|-----------------|-------|-----|
| MS Content | Red | `#e74c3c` |
| MS Education | Purple | `#8e44ad` |
| MS AI | Blue | `#2980b9` |
| MS Ventures | Green | `#27ae60` |
| Data/Infrastructure | Dark | `#1a1a2e` |
| Agencies | Orange | `#f39c12` |
| External/Users | Gray | `#95a5a6` |

## Dollar Sign Warning

`$` is reserved for D2 variable substitution. Never use dollar signs in labels:
- Write: `"9,500 NZD"` not `"$9,500 NZD"`
- Write: `"Revenue: 800K NZD"` not `"Revenue: $800K NZD"`

## Existing Diagrams

| File | Purpose | Key Elements |
|------|---------|-------------|
| `master-overview.d2` | Group overview | 4 businesses, flywheel, Liam, agencies, SMBs |
| `data-pipeline.d2` | Data architecture | 9 sources → collectors → SQLite → outputs |
| `automation-schedule.d2` | Cron schedule | Daily/4hr/hourly jobs, launchd, pipelines |
| `command-system.d2` | Slash commands | Commands grouped by function, data connections |
| `education-funnel.d2` | Education funnel | YouTube → Skool → QF Calls → Sales → Tiers |

## Render Script

```bash
bash scripts/generate_diagrams.sh          # Default: ELK, theme 0
bash scripts/generate_diagrams.sh dagre 0  # Alternative layout
bash scripts/generate_diagrams.sh elk 6    # Alternative theme
```

Auto-discovers all `.d2` files in `diagrams/`. Reports success/failure and file sizes.

## Adding a New Diagram

1. Create `diagrams/name.d2`
2. Run `bash scripts/generate_diagrams.sh`
3. Inspect the rendered SVG with the current harness to validate it visually
4. Iterate: edit `.d2` → re-render → re-validate
5. Run `/document diagrams` so the doc and the index stay current

## When to Update

Update diagrams when workspace structure changes:
- New data source connected
- New slash command or automation added
- New cron job or pipeline
- Business structure changes
- Education funnel changes
