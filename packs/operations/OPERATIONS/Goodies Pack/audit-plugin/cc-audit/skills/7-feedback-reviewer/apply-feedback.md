---
name: apply-feedback
description: Apply approved feedback items from the latest review round to audit domain files. Handles cascading recalculations, writes domain files, triggers auto-regen of deliverables via manifest update.
menu-code: AF
---

# Apply Feedback (AF)

> **Application capability.** Reads approved feedback items from reviews.json, applies changes to the correct domain files with cascading recalculations, writes files (triggering auto-regen), and marks items as applied in reviews.json.

---

## Stage 1: Load Approved Items

Read `clients/{slug}/03-audit/data/reviews.json`.

Find all feedback items across all rounds where `resolution.status == "approved"` and no `applied_at` timestamp (i.e., approved but not yet applied).

If no approved items exist: report and stop.

```
AF PRE-FLIGHT -- {company_name}

Approved items pending application: {n}
  From round RR-001: {n} items
  From round RR-002: {n} items (if applicable)

By domain:
  findings.json:      {n} items
  opportunities.json: {n} items
  extraction.json:    {n} items
  strategy.json:      {n} items
  architecture.json:  {n} items

Cascades detected: {n}
  {list cascades briefly}

Proceed? [y/n]
```

Wait for confirmation before proceeding.

---

## Stage 2: Group by Domain and Apply

Process one domain at a time in this order: extraction, findings, opportunities, strategy, architecture. This order matters: extraction changes may affect findings, findings changes may affect opportunities.

For each domain:

### 2a. Read the domain file

### 2b. Apply each change in order of severity (HIGH first)

**For `correction` type:**
- Navigate to `target_path` (e.g., `waste_items[waste_id=W-003]`)
- Update each field in `proposed_changes[]`: set `field` to `new_value`
- Preserve all other fields

**For `removal` type:**
- Navigate to the target array
- Remove the item with the matching ID
- Record the removed item for cascade checking

**For `addition` type:**
- Determine the correct array in the domain file
- Assign the next available ID in the sequence (check highest existing ID of that type)
- Append the new item with proper `source_quote`, `speaker: "reviewer"`, `source_document: "{round_id} review"`, `confidence: "HIGH"` (reviewer-confirmed)

**For `clarification` type:**
- Update the `description`, `title`, or `activity` field as specified

**For `endorsement` type:**
- No field changes. Add `reviewer_endorsed: true` and `endorsement_round: "{round_id}"` to the item

**For `priority_change` type:**
- Update the relevant category/tier/severity field

### 2c. Cascading recalculations

After applying all changes to a domain, run cascade checks:

**findings.json cascades:**
- For any waste_item where `hours_per_week` or `headcount_affected` changed:
  ```
  annual_waste_aud = hours_per_week * 52 * headcount_affected * hourly_rate_aud
  monthly_waste_aud = round(annual_waste_aud / 12)
  ```
  Show the recalculation: "W-003: annual_waste_aud updated from $27,040 to $4,056 (1.5 hrs/wk x 1 person x $52/hr x 52)"

- For any removed waste_item: check `opportunities.proposed_changes[].linked_roi_item_id`. If a change references the deleted waste/ROI, flag it.

- For any removed pain_point: check `opportunities.proposed_changes[].linked_pain_point_ids[]`. If a change's only linked pain point was removed, flag it.

**opportunities.json cascades:**
- After applying all opportunities changes, verify ROI totals are consistent with any waste changes applied in the findings step
- If `roi_items[].annual_saving_aud` was sourced from a waste item that was corrected: prompt to update the ROI figure

Show cascade summary before writing:
```
CASCADES
  W-003: annual_waste_aud: $27,040 -> $4,056
  W-003: monthly_waste_aud: $2,253 -> $338
  ROI item R-003 references W-003 — its annual_saving_aud ($27,040) may need updating.
  Update R-003.annual_saving_aud to $4,056? [y/n/skip]:
```

### 2d. Write the domain file

Write the updated domain file. Compute SHA-256.

### 2e. Update manifest for this domain

Update `domains.{domain}.checksum`, `domains.{domain}.updated_at` in `audit-manifest.json`. Do this for each domain file before moving to the next.

---

## Stage 3: Write audit-manifest.json

After all domain files are written, do a final write to `audit-manifest.json` updating the root `updated_at`.

This triggers `auto-regen-deliverables.sh` via the PostToolUse hook. Deliverables that already exist in `clients/{slug}/03-audit/deliverables/` will be regenerated automatically.

---

## Stage 4: Update reviews.json

For each applied item, set:
```json
{
  "resolution": {
    "status": "approved",
    "applied_at": "ISO8601 timestamp"
  }
}
```

Update the round's `summary.items_applied` count. If all items in the round are applied, set `round.status = "applied"`. If some remain pending, set `round.status = "partially_applied"`.

Write `reviews.json`. Update manifest checksum for the reviews domain.

---

## Stage 5: Confirm and Report

```
APPLY COMPLETE -- {company_name} -- {round_id}

Changes applied:
  findings.json:      {n} corrections, {n} removals, {n} additions
  opportunities.json: {n} corrections
  extraction.json:    {n} corrections
  strategy.json:      {n} corrections
  architecture.json:  {n} corrections

Cascades handled:
  {list}

Deliverables queued for regeneration:
  waste.html, findings.html, solutions-overview.html, client-website.html

Next steps:
  - Check regenerated deliverables in clients/{slug}/03-audit/deliverables/
  - Run [RH] to view the full review history
  - Run another [IF] round when ready for the next review pass
```

### 5a. CRM update (best-effort)

If `crm.project_id` is not null, create a task comment:
"Round {round_id} applied: {n} corrections across {n} domain files. {cascade_summary}. Deliverables auto-regenerated."
