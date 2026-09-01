---
name: verify-numbers
description: "Arithmetic verification of all dollar figures, hours, rates, payback periods, and ROI calculations across audit-data.json and generated HTML deliverables. Report-only — never auto-corrects unless explicitly requested."
menu-code: VN
---

# Verify Numbers (VN)

> **Post-generation QA gate.** Traces every dollar figure, hours estimate, payback period, and ROI calculation in the generated deliverables back to audit-data.json fields, formulas, or named constants. Produces a structured findings report. Report-only by default — corrections require explicit user confirmation.

## Purpose

By the time VN runs, all generators have produced HTML deliverables. These contain numbers that clients will scrutinise: "Where did this $92K figure come from? How did you calculate 32 hours/week freed?" Every number must trace to one of three sources:

1. **Stored field** — a value in audit-data.json written by the Analyst agents (BR, SA)
2. **Formula** — a computation using named audit-data.json inputs (e.g., `hrs × headcount × rate × 52`)
3. **Named constant** — a hardcoded value in generate.py with a known purpose

Any number that cannot be traced is flagged. Any formula that doesn't produce the stored result is flagged.

**When to run:** After generators (GV, GA, GS, GW) and before GC (comprehensive report). This is the last arithmetic gate before deliverables reach the client.

**Relationship to VR:** VR (Agent 4) checks research quality, sales framing, and data consistency at a qualitative level. VN checks arithmetic at a numerical level. They are complementary — VR runs pre-generation, VN runs post-generation.

---

## Stage 1: Pre-flight

### 1a. Load inputs

Read `clients/{client_slug}/03-audit/data/audit-data.json` in full. Extract and hold in working memory:

- `blended_hourly_rate_aud`
- `waste_items[]`
- `proposed_changes[]`
- `roi_items[]`
- `strategic_approaches` (including `service_tier_recommendation`, `strategies[]`)
- `processes[]`
- `tools[]`

### 1b. Declare constants

These are hardcoded in `generate.py` and must be stated here so you can verify against them:

```
SPRINT_PRICE_AUD     = 15,000    (per 2-week sprint)
HOSTING_ANNUAL       = 1,200     ($100/month)
RD_OFFSET            = 0.435     (43.5% R&D tax incentive offset)
WASTE_FORMULA        = hours_per_week × headcount_affected × hourly_rate_aud × 52
PAYBACK_FORMULA      = midpoint_price / (annual_saving / 12)
  where midpoint     = (price_range_low_aud + price_range_high_aud) / 2
```

### 1c. Scan deliverables

Check which HTML files exist in `clients/{client_slug}/03-audit/deliverables/`:
- `4-waste.html`
- `1-client-website.html`
- `2-process-map.html`
- `3-findings.html`

### 1d. Print inventory

```
VN PRE-FLIGHT — {company_name}

DATA INVENTORY
  blended_hourly_rate_aud:  ${rate}
  Waste items:              {n} ({n} with annual_waste_aud)
  Proposed changes:         {n} ({n} with combined_annual_value_aud)
  Plugin cards:             {n} (in service_tier_recommendation.mid_ticket)
  ROI items:                {n}
  Tools researched:         {n total across all changes}

DELIVERABLES PRESENT
  4-waste.html:                   {YES/NO}
  1-client-website.html:          {YES/NO}
  2-process-map.html:             {YES/NO}
  3-findings.html:                {YES/NO}
```

If no deliverables exist, warn that HTML cross-checks will be skipped (audit-data.json arithmetic only).

---

## Stage 2: Waste Item Arithmetic

### 2a. Per-item formula check

For each item in `waste_items[]`:

1. Extract: `hours_per_week`, `headcount_affected` (default to 1 if absent/null), `hourly_rate_aud` (fall back to top-level `blended_hourly_rate_aud` if absent), `annual_waste_aud`
2. Compute: `expected = round(hours_per_week × headcount_affected × hourly_rate_aud × 52)`
3. Compare: `diff = abs(annual_waste_aud - expected)`
4. Apply tolerance:
   - diff <= $20 → `rounding_error` (LOW)
   - $21–$200 → `formula_mismatch` (MEDIUM)
   - > $200 → `formula_mismatch` (HIGH)
5. **Headcount check:** If `headcount_affected > 1` and `annual_waste_aud` is approximately equal to `hours_per_week × 1 × hourly_rate_aud × 52` (within $50), flag as `headcount_ignored` (HIGH) — the stored value is per-person, not per-team.

### 2b. Monthly consistency

If `monthly_waste_aud` is present on any item: verify `monthly_waste_aud × 12` equals `annual_waste_aud` within $10. Flag mismatches as `formula_mismatch` (MEDIUM).

### 2c. Grand total reconciliation

1. Compute `sum_from_items = sum(annual_waste_aud for all waste_items)`
2. If `4-waste.html` exists, read it and extract the hero total (the main "total annual waste" figure displayed prominently)
3. Compare. Flag differences >$10 as `total_mismatch` (HIGH).

### 2d. Per-type subtotals

Group waste items by `waste_type`. For each type, compute sum of `annual_waste_aud`. If waste.html shows a breakdown by type (bar chart or category totals), compare each. Flag differences >$10 as `total_mismatch` (MEDIUM).

---

## Stage 3: Value / ROI Arithmetic

### 3a. Time-saving formula check

For each `proposed_change` with a `value.time_saving` block:

1. Extract: `hours_saved_per_week`, `hourly_rate_aud` (from the time_saving block; fall back to top-level `blended_hourly_rate_aud`), `annual_saving_aud`
2. Compute: `expected = round(hours_saved_per_week × hourly_rate_aud × 52)`
3. Flag mismatches: diff $21–$200 → MEDIUM, >$200 → HIGH

### 3b. Combined value component sum

For each `proposed_change` with `value.combined_annual_value_aud` populated:

1. Sum all sub-components:
   - `value.time_saving.annual_saving_aud` (default 0)
   - `value.productivity_enhancement.estimated_annual_value_aud` (default 0)
   - `value.error_reduction.estimated_annual_value_aud` (default 0)
   - `value.compliance.estimated_annual_value_aud` (default 0)
2. Compare sum to `combined_annual_value_aud`
3. Flag differences >$50 as `formula_mismatch` (MEDIUM if <$500, HIGH if >=$500)

### 3c. Blended rate consistency

Scan every `hourly_rate_aud` field across all waste items and proposed changes. If any item uses a rate that differs from `blended_hourly_rate_aud` without an explicit role-specific justification (check if `rate_source` or similar annotation exists), flag as `rate_inconsistency` (MEDIUM). List all distinct rates found.

### 3d. Plugin card savings vs covered changes

For each plugin card in `service_tier_recommendation.mid_ticket.plugin_cards[]`:

1. `card_annual = card.annual_saving_aud`
2. `covered_ids = card.covered_change_ids`
3. Sum `proposed_changes[id].value.combined_annual_value_aud` for each id in `covered_ids` (skip any that are null)
4. If `card_annual != sum_changes` (diff >$50): flag as `stale_card_value` (MEDIUM) with note: "generate.py overrides stored card value with computed sum from covered changes. Stored card value is cosmetic but may cause confusion if inspected in audit-data.json."

### 3e. Total annual value reconciliation

Compare these three values (where present):
1. `sum(card.annual_saving_aud for all plugin cards)`
2. `service_tier_recommendation.mid_ticket.total_annual_saving_aud`
3. `service_tier_recommendation.total_annual_value_aud`

If any pair differs by >$50, flag as `total_mismatch` (HIGH).

---

## Stage 4: Payback Calculations

### 4a. Plugin card payback

For each plugin card with `price_range_low_aud`, `price_range_high_aud`, `annual_saving_aud`, and `payback_months`:

1. `midpoint = (price_range_low_aud + price_range_high_aud) / 2`
2. `expected_payback = round(midpoint / annual_saving_aud * 12, 1)`
3. Compare to stored `payback_months`
4. Tolerance: diff <=0.5 months → LOW, 0.5–1 → MEDIUM, >1 → HIGH

### 4b. Core roadmap payback

If `implementation_roadmap.stages[]` exists, for each stage with `milestone_value_aud` and sprint data:

1. Compute expected payback from sprints and milestone value
2. Verify stage classification: payback <= 12 months should be `core`, >12 months should be `future`
3. Flag misclassifications as MEDIUM

### 4c. ROI items payback

For each entry in `roi_items[]` with `build_cost_aud` and `payback_months`:

1. Find the linked proposed change (by `change_id` or matching title)
2. If the change has `value.combined_annual_value_aud`: compute `expected = round(build_cost_aud / (combined_annual_value_aud / 12), 1)`
3. Compare to stored `payback_months`. Flag diff >1 month as MEDIUM.

---

## Stage 5: Cost Summary Reconciliation

### 5a. Tool cost reconciliation

If `strategic_approaches.strategies[]` exists with `tool_selections[]`:

1. Deduplicate by tool name — take `max(annual_cost_aud)` per unique tool (this matches generate.py's dedup logic)
2. Sum deduplicated tool costs
3. Compare to `cost_summary.ongoing_annual_total_aud` or equivalent
4. Flag differences >$100 as MEDIUM

### 5b. Total-with-hidden check

For each tool in any `proposed_change.research.tools_researched[]` that has `hidden_costs[]`:

1. `expected_total = annual_cost_aud + sum(hc.estimated_annual_aud for hc in hidden_costs where hc.likelihood == "likely")`
2. Compare to `total_cost_with_hidden_aud`
3. Flag differences >$50 as MEDIUM

### 5c. Constants in HTML

If `1-client-website.html` or `5-blueprint.html` exist, scan for:
- R&D offset percentage → should be 43.5% (matching `RD_OFFSET = 0.435`)
- Sprint price → should be $15,000 (matching `SPRINT_PRICE_AUD`)
- Hosting cost → should be $1,200/yr or $100/mo (matching `HOSTING_ANNUAL`)

If the HTML shows different values, flag as `constant_mismatch` (HIGH).

---

## Stage 6: Cross-Deliverable Consistency

### 6a. Waste total across pages

If both `4-waste.html` and `1-client-website.html` exist, the total annual waste figure should be the same on both pages (both should equal `sum(waste_items[].annual_waste_aud)`). Flag any mismatch >$10 as `total_mismatch` (HIGH).

### 6b. Annual value across pages

The total annual value / savings figure in `1-client-website.html` should trace to `service_tier_recommendation.total_annual_value_aud` or equivalent. If `5-blueprint.html` also shows a total value figure, both should match. Flag mismatches as `total_mismatch` (HIGH).

### 6c. Blended rate in HTML

Search all HTML deliverables for dollar-per-hour figures (e.g., "$50/hr"). Every rendered rate should match either `blended_hourly_rate_aud` or a role-specific rate documented in `waste_items[].hourly_rate_aud`. Flag unknown rates as `rate_inconsistency` (MEDIUM).

### 6d. Step count verification

If both `2-process-map.html` and `1-client-website.html` show "before/after" step counts:

1. Count actionable steps from `processes[]` in audit-data.json (step types: step, pain, decision, parallel_group)
2. Count eliminated/automated/consolidated steps from `proposed_changes[]`
3. Verify rendered "before" matches count from (1), "after" matches (1) minus (2)
4. Flag mismatches as `formula_mismatch` (MEDIUM)

---

## Stage 7: Source Tracing

### 7a. Untraceable number scan

For each HTML deliverable that exists, extract all significant numbers:
- Dollar figures > $500
- Percentages
- Payback periods (months)
- Hours/week figures

For each extracted number, attempt to trace it to:
- A specific field in audit-data.json (cite the field path)
- A formula using named inputs (state the formula)
- A hardcoded constant (name the constant)

Any number that cannot be traced → flag as `untraceable_number` (HIGH). Include the HTML context (surrounding text) so it can be located.

### 7b. Formula display consistency

In `4-waste.html` and `5-blueprint.html`, formula strings are rendered inline (e.g., "2.9 hrs/wk x 1 person x $50/hr x 52 wks"). For each rendered formula:

1. Parse the displayed inputs (hours, headcount, rate)
2. Compare to the stored fields on the corresponding waste item or proposed change
3. If the formula text says "2 people" but `headcount_affected = 1` (or vice versa), flag as `formula_mismatch` (HIGH)

---

## Stage 8: Compile and Report

### 8a. Assign finding IDs

Number all findings as VN-001, VN-002, etc., ordered by severity (HIGH first, then MEDIUM, then LOW).

### 8b. Finding format

Each finding:

```
VN-{NNN} [{severity}] {category}
  Location:    {audit-data.json | 4-waste.html | 5-blueprint.html | ...}
  Field:       {field_path, e.g. waste_items[2].annual_waste_aud}
  Expected:    {value}
  Actual:      {value}
  Formula:     {the formula that should produce the expected value}
  Description: {one sentence}
  Action:      {what to fix}
```

### 8c. Summary dashboard

```
VERIFY NUMBERS COMPLETE — {company_name}

━━━ WASTE ARITHMETIC ━━━
  Items checked:          {n}
  Formula mismatches:     {n} ({n} HIGH, {n} MEDIUM, {n} LOW)
  Headcount ignored:      {n} items — ${total_understatement} understated
  Grand total:            {PASS | FAIL}

━━━ VALUE / ROI ━━━
  Changes checked:        {n}
  Formula mismatches:     {n}
  Rate inconsistencies:   {n}
  Card value drift:       {n}

━━━ PAYBACK ━━━
  Cards checked:          {n}
  Payback mismatches:     {n}

━━━ COST RECONCILIATION ━━━
  Tool cost drift:        {$n or PASS}
  Hidden cost checks:     {n checked, n flagged}
  Constants:              {PASS | FAIL}

━━━ CROSS-DELIVERABLE ━━━
  Waste total consistent: {YES | NO — list which pages differ}
  Value total consistent: {YES | NO}
  Rate consistent:        {YES | NO}
  Step counts:            {PASS | N/A}

━━━ SOURCE TRACING ━━━
  Numbers scanned:        {n}
  Untraceable:            {n}

━━━━━━━━━━━━━━━━━━━━━━━━━
  HIGH:    {n}
  MEDIUM:  {n}
  LOW:     {n}
  TOTAL:   {n}
```

### 8d. Recommended action

```
If HIGH > 0:
  "ACTION REQUIRED: {n} HIGH findings must be resolved before client presentation.
   Fix the source values in audit-data.json, then re-run affected generators.
   Type 'apply fixes' to review and correct HIGH findings interactively."

If MEDIUM > 0 and HIGH == 0:
  "REVIEW RECOMMENDED: {n} MEDIUM findings. Some may be acceptable rounding
   or intentional conservative estimates. Review each before presenting."

If LOW only:
  "NUMBERS CLEAN: All figures trace correctly. Minor rounding differences
   are within tolerance. Deliverables are ready for client presentation."
```

---

## Stage 9: Fix Mode (Optional)

This stage ONLY runs if the user explicitly requests it (e.g., "apply fixes", "fix VN findings", "correct the HIGH findings").

### 9a. Scope

Only HIGH-severity findings with categories `formula_mismatch`, `headcount_ignored`, or `total_mismatch` are eligible for auto-fix. Untraceable numbers, rate inconsistencies, and stale card values require manual judgment.

### 9b. Interactive confirmation

For each eligible finding:

```
FIX VN-{NNN}: {field_path}
  Current:  ${actual}
  Proposed: ${expected}
  Formula:  {formula}
  Apply? [y/n]
```

Wait for user confirmation on each. Collect all approved fixes.

### 9c. Apply corrections

1. Load audit-data.json
2. Apply all approved corrections in a single write
3. Print summary: "{n} corrections applied to audit-data.json"
4. Advise which generators to re-run:
   - Waste item changes → re-run [GV] and [GW]
   - Value/ROI changes → re-run [GA], [GS], and [GW]
   - Cost changes → re-run [GA] and [GS]

### 9d. CRM update

If `crm.project_id` exists, add a task comment:
```
VN verification complete. {n} findings ({n} HIGH). {n} corrections applied.
```
