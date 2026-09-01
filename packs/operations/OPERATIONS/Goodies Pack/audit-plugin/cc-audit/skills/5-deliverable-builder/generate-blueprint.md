---
name: generate-blueprint
description: "Generate blueprint.html — AI Blueprint scroll journey. Initiative cards with quote attribution, ROI, build cost, risk labels, payback, solution type badges, priority matrix, phased roadmap (Gantt when BO has run), and short-term/long-term outlook plus risks narrative."
menu-code: GB
---

# Generate AI Blueprint

## Purpose

Produce `5-blueprint.html` — the primary client-facing deliverable that presents all automation and AI opportunities as a scroll journey.

The page contains seven sections:
1. **Waste Anchor** — starts where the client's attention already is; references waste totals
2. **Solution Type Education** — four badge-card explainers (just-in-time, before recommendations)
3. **Initiative Cards** — each opportunity as a card with quote attribution, solution_type badge, ROI, build cost range, payback, risk label, timeframe. The Initiative Cards section also carries a short **R&D Tax Incentive** explainer beneath the indicative investment ranges, and bundle modals show the effective build cost after the conservative ~43.5% R&D offset (`price × 0.565`). This is automatic — no data field drives it — and framing is mandatory per `context/pricing/apg-pricing.md` (always show full + effective price, with the "verify with your accountant" caveat).
4. **Priority Matrix** — impact vs effort, high-impact/low-effort quadrant highlighted
5. **Plugin Demo Videos** — 3 embedded video thumbnails for relevant use cases
6. **Phased Roadmap** — Gantt SVG over weeks plus a per-phase summary strip when `transformation_blueprint.phases[]` is populated (run Analyst BO). Falls back to the legacy Quick Wins / Core Builds / Future Sprints 3-card layout when BO has not run.
7. **Outlook & risks** — short-term (0-3 months) and long-term (6-18 months) outlook articles plus risks narrative grouped by category (data flow & context, data storage & ownership, AI training & adoption). Renders only when `transformation_blueprint.short_term_outlook`, `long_term_outlook`, or `risk_outlook` are populated. The risks block falls back to flat `risk_label` chips when BO has not run.

**Requires:** `proposed_changes[]` in audit-data.json with at minimum `title`, `change_type`, `proposed_solution`, `stage`. Richer output when `solution_type`, `build_cost_range_aud`, `payback_months`, `risk_label`, and `value.combined_annual_value_aud` are populated (run Analyst EI and BR first).

**Optional but recommended:** `transformation_blueprint` populated by Analyst BO. This unlocks the Gantt timeline and the "Where this takes you." outlook + risks section.

## Process

### Step 1: Pre-flight Check

Read `clients/{client_slug}/03-audit/data/audit-data.json`.

Verify:
- `proposed_changes[]` is not empty
- At least one item has `title` populated

If `proposed_changes` is empty, stop and tell the user: run Analyst [EI] first to populate improvement opportunities.

Warn (don't block) if:
- Fewer than 3 items have `solution_type` set — blueprint will render with placeholder badges
- No items have `value.combined_annual_value_aud` — ROI pills will be empty
- No items have `build_cost_range_aud` — cost pills will be empty

### Step 2: Generate

```bash
python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py \
  --client-slug {client_slug} \
  --output blueprint
```

Output: `clients/{client_slug}/03-audit/deliverables/blueprint.html`

blueprint is also included in `--output all`.

### Step 3: Verify

Check the output JSON for `status: ok`. Report:
- Total annual value shown in hero
- Number of initiative cards rendered
- Whether `transformation_blueprint.phases[]` was rendered as a Gantt (BO has run), or whether the legacy 3-card fallback was used
- Whether the "Where this takes you." outlook + risks section is present
- File size (KB)

### Step 4: Recommend next

After [GB], the client portal needs updating — run [GW] to regenerate client-website.html with the correct link to blueprint.html in the Opportunity Preview section.

## Data Fields Used

| Field | Section | Notes |
|---|---|---|
| `waste_items[].annual_waste_aud` | Waste Anchor | Summed for total figure |
| `proposed_changes[].title` | Initiative Cards | Required |
| `proposed_changes[].solution_type` | Initiative Cards + Roadmap | cowork_plugin / n8n_automation / custom_build / data_migration |
| `proposed_changes[].value.combined_annual_value_aud` | Initiative Cards | Annual value pill |
| `proposed_changes[].build_cost_range_aud` | Initiative Cards | Cost range pill |
| `proposed_changes[].payback_months` | Initiative Cards + Roadmap | Timeframe tag + roadmap classification |
| `proposed_changes[].risk_label` | Initiative Cards | Risk pill |
| `proposed_changes[].proposed_solution` | Initiative Cards | Quote fallback |
| `pain_points[].quote` | Initiative Cards | "You said this" attribution |
| `pain_points[].pain_point_id` | Initiative Cards | Cross-referenced via linked_pain_point_ids |
| `transformation_blueprint.phases[]` | Phased Roadmap | Drives Gantt bars (`tier_code`, `start_week`, `effective_duration_weeks`, `change_ids`). Falls back to legacy 3-card layout when empty. |
| `transformation_blueprint.short_term_outlook` | Outlook & risks | Summary paragraph + highlights for the 0-3 month horizon |
| `transformation_blueprint.long_term_outlook` | Outlook & risks | Summary paragraph + highlights for the 6-18 month horizon |
| `transformation_blueprint.risk_outlook` | Outlook & risks | Narrative summary + risks grouped by `category` (`data_flow_context`, `data_storage_ownership`, `ai_training_adoption`) |
