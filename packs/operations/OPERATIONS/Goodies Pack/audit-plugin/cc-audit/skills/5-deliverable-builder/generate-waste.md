---
name: generate-waste
description: "Generate waste.html — quantified waste breakdown with hours and annual costs per item."
menu-code: GV
---

# Generate Waste

## Purpose

Produce `4-waste.html` from audit-data.json using `generate.py --output waste`. 

**New card-based layout:** Each opportunity gets its own card with the annual cost prominently displayed, a "You said this in Session N:" quote attributed back to the client's own words (with Fathom recording link if available), hours/week, headcount, and a confidence badge. The total sum appears at the bottom after the client has connected emotionally to each individual line item. Opportunities by category (bars chart) follows the total.

**Data quality matters:** Every item should have `annual_waste_aud` calculated. If any items are missing this, the card will attempt to derive it (`hours_per_week × headcount × hourly_rate × 52`) — but explicit values always look more credible on screen. Run SU to ensure all items are calculated before generating.

## Process

### Step 1: Pre-flight Check

Client slug is set from activation. Load `clients/{client_slug}/03-audit/data/audit-data.json`.

Check that `waste_items[]` is non-empty with at least one item that has `annual_waste_aud` calculated.

```
✗ waste_items[] is empty or no items have annual_waste_aud calculated. Run more mapping sessions to identify waste.
```

Also count items missing `calculation_note`. If more than 25% are empty, warn before generating:

```
⚠ {n}/{total} waste items are missing calculation_note.
The waste report will auto-generate formula breakdowns for time-based items where
hours_per_week and hourly_rate are present, but items with an explicit calculation_note
show more credibly to the client. Consider re-running the extractor (SU) to backfill.
```

If the check passes, note the count of opportunities and total annual hidden costs.

### Step 2: Generate

```bash
python3 .claude/skills/bmad-apg-agent-generator/scripts/generate.py \
  --client-slug {client_slug} \
  --output waste
```

Output is saved to: `clients/{client_slug}/03-audit/deliverables/waste.html`

### Step 3: Post-generation

Confirm the file was created. Report the file path and size.

```
WASTE GENERATED — {company_name}
File: clients/{client_slug}/03-audit/deliverables/4-waste.html
Size: {size}

Opportunities: {n}
Total annual hidden costs: ${total_annual_waste_aud}
Confidence breakdown: {n} HIGH, {n} MEDIUM, {n} LOW
```

Suggest opening in browser to review.
