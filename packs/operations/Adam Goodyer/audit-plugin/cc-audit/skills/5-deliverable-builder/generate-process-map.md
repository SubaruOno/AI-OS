---
name: generate-process-map
description: Generate BPMN 3-level process map hierarchy with swim-lane diagrams, citation panels, and Fathom deep-links
menu-code: GP
---

# Generate Process Map

## Purpose

Produce a 3-level BPMN process map hierarchy showing current-state business operations:
- **Level 0** `2-process-map.html`: landscape with stage cards and quick stats
- **Level 1** `processes/{stage}/index.html`: subprocess cards within each stage
- **Level 2** `processes/{stage}/{id}.html` + `.bpmn`: interactive bpmn-js viewer with swim lanes, performer chips, pain indicators, and citation sidebar with Fathom deep-links

## Process

### Step 1: Pre-flight Check

Client slug is set from activation. Verify audit data exists:

```bash
python3 apg-audit-plugin/scripts/validate_audit_data.py \
  --file clients/{client_slug}/03-audit/data/audit-data.json
```

If the validation fails with critical/high findings, show the findings and ask: "The audit data has issues that may affect the process map. Proceed anyway, or fix these first?"

Check which stages have data in `processes[]`. Note any stages with no steps.

### Step 2: Generate

```bash
python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py \
  --client-slug {client_slug} \
  --output process-map
```

Output is saved to:
- `clients/{client_slug}/03-audit/deliverables/process-map.html` (landscape entry point)
- `clients/{client_slug}/03-audit/deliverables/processes/{stage}/{id}.bpmn` + `.html`

### Step 3: Report

```
BPMN PROCESS MAP GENERATED — {company_name}
Landscape: clients/{client_slug}/03-audit/deliverables/2-process-map.html

Stages generated:
  • {stage_label} — {n} sub-processes, {n} steps
  ...

Pain points: {total} identified across {n} processes
Sub-processes: {total} generated across {n} stages

All files are self-contained HTML, open directly from file://, no server needed.
Legacy zone map backed up as: process-map-legacy.html (if existed)
```

Open the landscape in a browser to review. Ask: "Ready to generate findings [GF], waste [GV], or client website [GW]?"
