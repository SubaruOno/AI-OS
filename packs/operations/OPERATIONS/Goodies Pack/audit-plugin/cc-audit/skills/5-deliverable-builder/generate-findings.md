---
name: generate-findings
description: "Generate findings.html — session findings summary showing what was discussed and discovered."
menu-code: GF
---

# Generate Findings

## Purpose

Produce `3-findings.html` from audit-data.json using the existing `generate.py --output findings` command. Shows pain points, optimisations, and key observations from each session.

## Process

### Step 1: Pre-flight Check

Client slug is set from activation. Load `clients/{client_slug}/03-audit/data/audit-data.json`.

Check that audit data has at least 1 session with `pain_points` or `optimisations` populated.

```
✗ No sessions found with pain_points or optimisations. Run at least one mapping session first.
```

If the check passes, note the session count and number of pain points / optimisations found.

### Step 2: Generate

```bash
python3 .claude/skills/bmad-apg-agent-generator/scripts/generate.py \
  --client-slug {client_slug} \
  --output findings
```

Output is saved to: `clients/{client_slug}/03-audit/deliverables/findings.html`

### Step 3: Post-generation

Confirm the file was created. Report the file path and size.

```
FINDINGS GENERATED — {company_name}
File: clients/{client_slug}/03-audit/deliverables/3-findings.html
Size: {size}

Sessions covered: {n}
Pain points: {n}
Optimisations: {n}
```

Suggest opening in browser to review.
