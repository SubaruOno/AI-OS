---
name: build-and-rate
description: Estimate implementation weeks, calculate value with visible formulas, and write client-facing modal content for the priority matrix. Uses sub-agents for parallel processing.
menu-code: BR
---

# Build & Rate (BR)

> **Idempotent.** First run estimates everything. Re-runs review and update existing estimates, fill gaps.
>
> **Sub-agent architecture.** Each proposed_change is rated by an independent sub-agent with its own context window, dispatched in parallel batches of 5. This prevents context degradation when writing modal content for 10-15+ changes.

## Purpose

For each proposed_change with research, estimate how many weeks it takes to implement, calculate the annual value with transparent formulas the client can verify, and write the 5-section modal content that appears when they click a bubble in the priority matrix.

---

## Stage 1: Pre-flight

1. Load audit data: check for `clients/{client_slug}/03-audit/data/audit-manifest.json`. If present (v4), read domain files directly:
   - Read `clients/{client_slug}/03-audit/data/meta.json`
   - Read `clients/{client_slug}/03-audit/data/extraction.json`
   - Read `clients/{client_slug}/03-audit/data/findings.json`
   - Read `clients/{client_slug}/03-audit/data/opportunities.json`
   - Do NOT read `strategy.json` or `architecture.json`
   If `audit-manifest.json` does not exist, fall back to v3/v2 behavior: load the full `audit-data.json` file.

   Check audit data is loaded and `proposed_changes[]` is populated.

2. Scan changes for readiness:
   ```
   BUILD & RATE STATUS -- {company_name}
   Total proposed changes: {n}
     research complete:     {n} -- ready for estimation
     research needs_review: {n} -- can estimate with caveats
     research not_started:  {n} -- SKIP (run RI first)
     sub_agent_failed:      {n} -- SKIP (retry RI first)

   Already rated (has implementation + value + modal_content):
     complete: {n}
     partial:  {n}
     none:     {n}
   ```

3. Select scope:
   ```
   Scope options:
     A) All unrated changes with research -- {n} changes
     B) Specific change by ID
     C) Re-rate specific ID (update existing estimates)
     D) All changes (including already-rated -- full refresh)
   ```

---

## Stage 2: Build Rating Context via Sub-Agents

### 2a. Load shared rating context (once)

Assemble a `rate_context` JSON object:

```json
{
  "company_name": "{from audit data}",
  "client_name": "{from contact}",
  "blended_hourly_rate_aud": "{from audit data}",
  "blended_rate_confidence": "{from audit data}",
  "staff_roster": ["{full staff_roster[] array, if present}"],
  "dev_rate_aud": 150,
  "pm_rate_aud": 120
}
```

### 2b. Load references (once)

Read these files once and hold their content as strings:
- `${CLAUDE_PLUGIN_ROOT}/context/pricing/apg-pricing.md` (pricing reference)
- `references/effort-estimation-guide.md` (if it exists; otherwise the estimation logic is in the sub-agent schema)

### 2c. Load sub-agent schema (once)

Read `sub-agent-rate.md` from this skill directory. Hold its full content as a string.

### 2d. Build per-change context packets

For each proposed_change in scope that has `research.status` of `"complete"` or `"needs_review"`, build a `change_packet` JSON object:

```json
{
  "change": {
    "change_id": "CH-003",
    "title": "...",
    "change_type": "automate",
    "source": "client",
    "proposed_solution": "...",
    "proposed_tools": ["Twilio"],
    "affected_step_ids": ["OPS-012", "OPS-013"],
    "linked_pain_point_ids": ["PP-018", "PP-019"],
    "stage": "operations",
    "value_type": "time_saving",
    "solution_type": "cowork_plugin",
    "research": { "...full research sub-object from RI..." }
  },
  "linked_pain_points": [
    {"pain_point_id": "PP-018", "title": "...", "description": "...", "source_quote": "...", "speaker": "...", "source_session": 2, "source_timestamp_seconds": 1680, "meeting_references": ["..."]}
  ],
  "linked_waste_items": [
    {"waste_id": "W-007", "activity": "...", "hours_per_week": 3.5, "headcount_affected": 1, "hourly_rate_aud": 50, "annual_waste_aud": 9100, "waste_type": "manual_data_entry", "meeting_references": ["..."]}
  ],
  "affected_steps": [
    {"step_id": "OPS-012", "title": "...", "owner": "Jordan", "time_estimate_hours_per_week": 3.5, "meeting_references": ["..."]}
  ],
  "roi_item": {
    "roi_item_id": "ROI-003",
    "annual_saving_aud": null
  }
}
```

**Filtering rules:**
- `linked_pain_points`: filter by `linked_pain_point_ids` -- include `source_quote`, `speaker`, `source_session`, `source_timestamp_seconds`, `meeting_references`
- `linked_waste_items`: filter by stage match -- include `hours_per_week`, `hourly_rate_aud`, `annual_waste_aud`, `source_quote`, `source_session`, `source_timestamp_seconds`, `meeting_references`
- `affected_steps`: filter by `affected_step_ids` -- include `owner`, `time_estimate_hours_per_week`, `meeting_references`
- `roi_item`: the matching entry from `roi_items[]` by `linked_roi_item_id`

**Source validation before dispatch**: For each context packet, verify that at least one linked_pain_point or linked_waste_item has a non-null `source_quote`. If all linked items have null source_quote, log a warning: `"⚠ CH-{id}: no source quotes available in any linked extraction item — modal meeting_references will be empty."` The sub-agent will still run, but the BR summary must flag this change as having no meeting references.

### 2e. Dispatch sub-agents in batches

Group the changes in scope into batches of 5. For each batch, dispatch all sub-agents simultaneously in a single message:

```
Agent({
  description: "BR rate -- {change_id} {title} -- {client_slug}",
  model: "sonnet",
  prompt: [
    "[full content of sub-agent-rate.md]",
    "",
    "## Shared Rating Context",
    "[rate_context as JSON]",
    "",
    "## Effort Estimation Reference",
    "[effort guide content, or 'See estimation logic in procedure below']",
    "",
    "## Pricing Reference",
    "[apg-pricing.md content]",
    "",
    "## This Proposed Change",
    "[change_packet as JSON]"
  ].join("\n")
})
```

**Wait for all sub-agents in the batch to complete before dispatching the next batch.**

Print progress after each batch:
```
  BATCH {n}/{total_batches} COMPLETE
    {change_id}: value ${combined_annual_value_aud}/yr, {weeks_label}, modal: yes
    {change_id}: value ${combined_annual_value_aud}/yr, {weeks_label}, modal: yes
    ...
```

### 2f. Merge sub-agent results

After each batch completes, for each sub-agent result:

1. **Parse the returned JSON.** If unparseable or `parse_error` is not null:
   - Log the failure
   - Add to the failed list
   - Continue with remaining results

2. **Merge onto proposed_change** by `change_id`:
   - Set `implementation` from the returned object (includes `effort_band: S|M|L`)
   - Set `value` from the returned object
   - Set `modal_content` from the returned object
   - Set `value_type` from `proposed_change_fields.value_type`
   - Set `build_cost_range_aud` from `proposed_change_fields` (internal use, not rendered on blueprint)
   - Set `payback_months` from `proposed_change_fields`
   - Set `risk_label` from `proposed_change_fields`

3. **Update roi_items[]**: find the matching entry by `roi_item_update.roi_item_id` and apply:
   - `annual_saving_aud`, `monthly_saving_aud`, `payback_months`, `payback_tag`

4. **Validate meeting_references**: for each merged change, check that `modal_content.meeting_references` (or equivalent evidence/fathom_references field) is not empty. If it is empty and the change has linked_pain_point_ids with non-null source_quotes, log: `"⚠ CH-{id}: modal_content has no meeting_references despite source quotes being available."` Add to the list of changes flagged in Stage 4.

5. **Checkpoint save** after each batch completes. For v4 files: write the full updated `opportunities` dict to `clients/{client_slug}/03-audit/data/opportunities.json`. Update `audit-manifest.json`: set `domains.opportunities.updated_at` and the root `updated_at`. For v2 fallback: write to top-level keys in `audit-data.json` as before.

---

## Stage 3: Handle Failures

After all batches complete, if any sub-agents failed:

```
FAILED CHANGES -- require retry:
  {change_id}: {error description}

Re-run [BR] scope B on each failed change to retry.
```

---

## Stage 4: Display Summary

```
BUILD & RATE COMPLETE -- {company_name}

Sub-agents dispatched: {total} in {batch_count} batches
  Successful: {n}  |  Failed: {n}

| # | ID     | Title                          | Value Type    | Annual Value | Weeks | Confidence | Modal |
|---|--------|--------------------------------|---------------|-------------|-------|------------|-------|
| 1 | CH-001 | Automate onboarding pack       | time_saving   | $9,100/yr   | 1.5   | HIGH       | yes   |
| 2 | CH-007 | AI call analysis for BDMs      | productivity  | $12,000/yr  | 2.0   | LOW        | yes   |
...

Total annual value: ${total}/yr across {n} changes
Quick wins (<1 wk): {n} changes worth ${total}/yr
Short builds (1-2 wks): {n} changes worth ${total}/yr

Changes without modal content: {n} (run BR on these)
Changes without value calculation: {n} (missing data -- check VR)
Changes without meeting_references: {n} ⚠ (modal has no Fathom links — source quotes missing from extraction)

Next step: Run [VR] to verify research, then generate deliverables.
```

---

## Stage 5: Save

1. Write the full updated `opportunities` dict to `clients/{client_slug}/03-audit/data/opportunities.json` — includes all `proposed_changes[]` with `implementation`, `value`, `modal_content`, `build_cost_range_aud`, `payback_months`, and `risk_label` fields, plus `roi_items[]` and `risk_register[]`. For v2 fallback: write to top-level keys in `audit-data.json` as before.
2. Update `clients/{client_slug}/03-audit/data/audit-manifest.json`: set `domains.opportunities.updated_at` and the root `updated_at` to the current ISO datetime. Skip for v2 fallback.
3. Update `analyst_metadata`:
   ```json
   {
     "analyst_metadata": {
       "last_br_run": "{ISO datetime}",
       "total_br_runs": "{n}",
       "changes_rated": "{n}",
       "sub_agents_dispatched": "{n}",
       "sub_agents_failed": "{n}",
       "total_annual_value_aud": "{sum}"
     }
   }
   ```
4. Confirm save
