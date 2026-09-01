---
name: research-improvements
description: Web research for tools, APIs, feasibility per proposed_change + generate new opportunities. Uses sub-agents for parallel research. Idempotent.
menu-code: RI
---

# Research Improvements (RI)

> **Idempotent.** First run researches everything + generates new opportunities. Re-runs only target items with `research.status != "complete"` or `research.gaps[]` entries.
>
> **Sub-agent architecture.** Each proposed_change is researched by an independent sub-agent with its own context window, dispatched in parallel batches of 3. This prevents context degradation when researching 10-15+ changes.

## Purpose

For each proposed_change in the audit data, research what's actually possible: which tools exist, what their APIs support, how they integrate with the client's existing stack, and what similar businesses have done. Then scan the audit data for new opportunities the client didn't mention.

---

## Stage 1: Pre-flight

1. Check audit data is loaded and `proposed_changes[]` is populated. If empty:
   ```
   ✗ proposed_changes[] is empty. Run [EI] Extract Improvements first.
   ```

2. Scan research status across all proposed_changes:
   ```
   RESEARCH STATUS — {company_name}
   Total proposed changes: {n}
     complete:         {n}
     needs_review:     {n}
     in_progress:      {n}
     not_started:      {n}
     sub_agent_failed: {n}
   ```

3. Select scope:
   ```
   Scope options:
     A) All unresearched (status != "complete") — {n} changes
     B) Specific change by ID (e.g., CH-003)
     C) Re-research specific ID (force re-run even if complete)
     D) Generate new opportunities only (skip existing changes)
   ```
   Wait for user selection.

---

## Stage 2: Research Existing Changes via Sub-Agents

> **Sub-agent architecture.** Each proposed_change is researched by an independent sub-agent with its own context window. Sub-agents are dispatched in parallel batches of 3 to balance speed with WebFetch capacity. The parent orchestrates: builds context packets, dispatches, collects results, and merges.
>
> **Classification model.** Sub-agents use a parallel 4-bucket scoring model (Plugin / Automation / Migration / Custom Build) rather than a sequential decision tree. A single finding can produce up to 2 initiatives. The `initiative_type` enum values are unchanged: `cowork_plugin`, `automation`, `data_migration`, `custom_build`, `process`. Migration items now return a `research.migration_diagnostic` object instead of `research.migration_research` — they are diagnostic recommendations, not buildable initiatives.

### 2a. Load shared context (once)

Check for `clients/{client_slug}/03-audit/data/audit-manifest.json`. If present (v4), read domain files directly:
- Read `clients/{client_slug}/03-audit/data/meta.json`
- Read `clients/{client_slug}/03-audit/data/extraction.json`
- Read `clients/{client_slug}/03-audit/data/findings.json`
- Read `clients/{client_slug}/03-audit/data/opportunities.json`
- Do NOT read `strategy.json` or `architecture.json`

If `audit-manifest.json` does not exist, fall back to v3/v2 behavior: load the full `audit-data.json` file.

Read the following from the loaded data and assemble a `shared_context` JSON object:

```json
{
  "company_name": "{from audit data}",
  "industry_tag": "{from audit data}",
  "headcount": "{from audit data}",
  "company_size_category": "{small / small-medium / medium / large}",
  "blended_hourly_rate_aud": "{from audit data}",
  "blended_rate_confidence": "{from audit data}",
  "current_year": 2026,
  "tools": ["{full tools[] array — ensure integration_openness and migration_research_flag fields are included for each tool}"],
  "business_metrics": ["{full business_metrics[] array}"],
  "staff_roster": ["{full staff_roster[] array, if present}"],
  "risk_register_last_id": "{highest RSK-xxx ID in risk_register[], or RSK-000 if empty}"
}
```

### 2b. Load pricing references (once)

Read these three files once and hold their content as strings:
- `${CLAUDE_PLUGIN_ROOT}/context/pricing/apg-custom-build.md`
- `${CLAUDE_PLUGIN_ROOT}/context/pricing/apg-service-tiers.md`
- `${CLAUDE_PLUGIN_ROOT}/context/pricing/apg-pricing.md`

Concatenate them into a single `pricing_references` string with section headers:
```
### APG Custom Build Options
[content of apg-custom-build.md]

### APG Service Tiers
[content of apg-service-tiers.md]

### APG Pricing
[content of apg-pricing.md]
```

### 2c. Load sub-agent schema (once)

Read `sub-agent-research.md` from this skill directory. Hold its full content as a string.

### 2d. Build per-change context packets

For each proposed_change in scope, build a `change_packet` JSON object containing only the data this sub-agent needs:

```json
{
  "change_id": "CH-003",
  "title": "...",
  "change_type": "automate",
  "source": "client",
  "proposed_solution": "...",
  "proposed_tools": ["Twilio"],
  "affected_step_ids": ["OPS-012", "OPS-013"],
  "linked_pain_point_ids": ["PP-018", "PP-019"],
  "linked_optimisation_ids": ["OPT-003"],
  "linked_waste_item_ids": ["W-007"],
  "source_evidence": [
    {"ref_id": "PP-018", "ref_type": "pain_point", "quote": "...", "speaker": "...", "source_session": 2, "source_timestamp_seconds": 1142, "fathom_url": "https://fathom.video/calls/<id>?t=1142"}
  ],
  "stage": "operations",
  "value_type": "time_saving",
  "solution_type": "cowork_plugin",
  "confidence": "MEDIUM",
  "time_saving_minutes_per_occurrence": null,
  "frequency": null,

  "linked_pain_points": [
    {"pain_point_id": "PP-018", "title": "...", "description": "...", "source_quote": "...", "speaker": "...", "risk_signal": false, "meeting_references": ["..."]}
  ],
  "affected_steps": [
    {"step_id": "OPS-012", "title": "...", "description": "...", "owner": "...", "tool_ids": ["T-004"], "time_estimate_hours_per_week": 3.5, "meeting_references": ["..."]}
  ],
  "linked_waste_items": [
    {"waste_id": "W-007", "activity": "...", "hours_per_week": 3.5, "headcount_affected": 1, "hourly_rate_aud": 50, "annual_waste_aud": 9100, "waste_type": "manual_data_entry", "meeting_references": ["..."]}
  ]
}
```

**New fields to add to change_packet:**

After building the existing change_packet fields, add:

**affected_flows** (if `source_handoff_ids[]` is non-empty on the change):
- Load `sequence_flows` from `extraction.json` where `flow_id` is in `source_handoff_ids[]`
- Filter to flows that have a `handoff` object
- For each: include `{flow_id, from_step_id, to_step_id, handoff: {source_tool, mechanism, destination_tool, data_transferred}}`
- Cap: maximum 5 flows per packet (most changes have 1-2)

**volume_context** (if `volume_weight < 1.0` on the change):
- Walk backwards through `sequence_flows` from the first `affected_step_id`
- Find the nearest upstream `exclusive_gateway` with `volume_split` annotations on its outgoing flows
- Include: `{upstream_gateway_id, branch_label, branch_volume_pct, total_process_volume_note}`
- If not found: `volume_context = null`

**blocked_by_gaps** (copy directly from `proposed_change.blocked_by_gaps[]`):
- Pass as-is. If empty array: still include as `[]`

**control_gap_ids** (copy from `proposed_change.control_gap_ids[]`):
- Pass as-is.

**affected_steps_iato** (if `iato` fields present in extraction):
- For each `affected_step_id`, include: `{step_id, iato: {...}, _gaps: {...}}`
- Filter to steps that actually exist in `extraction.json`
- Cap: maximum 10 steps

**Packet size guard:**

After adding new fields, estimate packet size:
- If packet exceeds 12KB: drop `affected_steps_iato` first, then `volume_context`
- The 10KB cap is the target; 12KB is the hard limit

**Filtering rules:**
- `linked_pain_points`: filter `pain_points[]` to only entries whose `pain_point_id` is in `linked_pain_point_ids`
- `affected_steps`: filter all `processes[].steps[]` to only steps whose `step_id` is in `affected_step_ids`
- `linked_waste_items`: filter `waste_items[]` to entries whose `waste_id` is in `linked_waste_item_ids` (if `linked_waste_item_ids[]` is absent on a legacy change, fall back to stage matching and **also opportunistically populate `linked_waste_item_ids[]` on the change before save**)
- `source_evidence`: pass through as-is from the change (already de-duped by EI). If EI did not populate it (legacy change), reconstruct it on the parent before save by walking `linked_pain_point_ids` + `linked_waste_item_ids` and resolving the citation tuple from findings + the `sessions[]` Fathom map.

### 2e. Dispatch sub-agents in batches

Group the changes in scope into batches of 3. For each batch, dispatch all sub-agents simultaneously in a single message:

```
Agent({
  description: "RI research -- {change_id} {title} -- {client_slug}",
  model: "sonnet",
  prompt: [
    "[full content of sub-agent-research.md]",
    "",
    "## Client Context",
    "[shared_context as JSON]",
    "",
    "## Pricing References",
    "[pricing_references string]",
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
    {change_id}: {status} -- {tool_count} tools researched, plugin: {yes/no}
    {change_id}: {status} -- {tool_count} tools researched, plugin: {yes/no}
    {change_id}: {status} -- {tool_count} tools researched, plugin: {yes/no}
```

### 2f. Merge sub-agent results

After each batch completes, for each sub-agent result:

1. **Parse the returned JSON.** If the JSON is unparseable or `parse_error` is not null:
   - Log the failure
   - Set `research.status: "sub_agent_failed"` on the change
   - Add the change_id to the failed list
   - Continue with remaining results

2. **Merge the `research` sub-object** onto the matching proposed_change by `change_id`. Overwrite the entire `research` field.

3. **Set `initiative_type`**, **`plugin_candidate`**, and **`research_summary`** on the proposed_change root from the returned values.

4. **Merge `risk_register_entries[]`** into the top-level `risk_register[]`:
   - Replace placeholder IDs (`RSK-NEW-1`, `RSK-NEW-2`, etc.) with real sequential IDs continuing from `risk_register_last_id`
   - Update `risk_register_last_id` in the shared context for the next batch

5. **Merge `business_metrics_updates[]`** into `business_metrics[]`:
   - Match by `metric_id` and update benchmark fields

6. **Collect `process_plugin_scope_update`** entries (don't write to processes[] yet, aggregate across all batches first)

7. **Checkpoint save** after each batch completes. For v4 files: write the full updated `opportunities` dict to `clients/{client_slug}/03-audit/data/opportunities.json` (includes `proposed_changes` with updated `research` and `plugin_candidate` fields), and write the full updated `extraction` dict to `clients/{client_slug}/03-audit/data/extraction.json` (includes `processes[].plugin_scope` updates from `process_plugin_scope_update` entries). Update `audit-manifest.json`: set `domains.opportunities.updated_at` and `domains.extraction.updated_at` and the root `updated_at` to the current ISO datetime. For v2 fallback: write to top-level keys in `audit-data.json` as before.

### 2g-bis. Source Evidence Backfill (mandatory before save)

After all batches complete and before writing process-scoped plugin assessments, scan all proposed_changes[] for empty source_evidence:

1. For each change where `source_evidence` is null, missing, or `[]`:
   - Walk `linked_pain_point_ids`: for each, pull `(source_quote, speaker, source_session, source_timestamp_seconds)` from `pain_points[]`. Skip entries where `source_quote` is null or empty.
   - Walk `linked_waste_item_ids`: same from `waste_items[]` (using `source_quote` field).
   - Walk `linked_optimisation_ids`: pull `(quote, speaker, source_session, source_timestamp_seconds)` from `optimisations[]`. Skip entries where `quote` is null or empty.
   - Resolve `fathom_url = sessions[source_session].fathom_url + "?t=" + source_timestamp_seconds` for each valid entry.
   - De-dupe by `(source_session, source_timestamp_seconds)`, keep ≤8 entries.
   - If entries were found: populate `source_evidence[]` and log `"Backfilled source_evidence for CH-{id}: {n} entries from linked extraction items."`
   - If still empty after backfill: log `"⚠ CH-{id}: source_evidence[] still empty after backfill. No citations in any linked extraction item."` Downgrade confidence to LOW if not already.

2. Report backfill results in Stage 4 summary:

```
SOURCE EVIDENCE BACKFILL
  Backfilled:        {n} changes (source_evidence rebuilt from linked IDs)
  Still empty:       {n} changes ⚠ (no citations available in linked items)
  Already populated: {n} changes (no action needed)
```

Any change still with empty source_evidence after backfill is a data quality issue — flag these clearly in the Stage 4 display.

### 2g. Write process-scoped plugin assessments

After ALL batches are complete, aggregate the `process_plugin_scope_update` entries collected in 2f. For each process that has at least one plugin-candidate change:

Write a `plugin_scope` object on `processes[i]`:

```json
{
  "plugin_candidate": true,
  "covered_change_ids": ["CH-002", "CH-019"],
  "complexity_tier": "<MAX across covered changes: simple < standard < complex>",
  "time_saved_weekly_hrs": "<sum across covered changes>",
  "annual_saving_aud": "<sum>",
  "price_range_low_aud": "<see pricing rules>",
  "price_range_high_aud": "<see pricing rules>",
  "tool_connections": ["<union, de-duplicated>"],
  "mcp_wrapper_needed": "<true if any>",
  "confidence": "<MIN across covered changes: LOW < MEDIUM < HIGH>",
  "data_layer": "<if all agree: that value. If mixed: 'mixed'>",
  "data_layer_tool": "<consolidated or comma-separated if mixed>"
}
```

Process plugin pricing rules (load `${CLAUDE_PLUGIN_ROOT}/context/pricing/apg-service-tiers.md` to confirm exact current bounds):
- 1 covered change: use that change's per-assessment price range
- 2-3 covered changes: use the aggregate complexity tier bound (standard: $4,500-$8,000; complex: $6,500-$8,000)
- 4+ covered changes: $6,500-$12,000

### 2h. Handle failures

After all batches complete, if any sub-agents failed:

```
FAILED CHANGES — require retry:
  {change_id}: {error description}
  {change_id}: {error description}

Re-run [RI] scope B on each failed change to retry.
```

---

## Stage 3: Generate New Opportunities (source: analyst)

> This stage runs in the parent orchestrator after all research sub-agents complete. It benefits from seeing the full picture of what was just researched.

After enriching existing client-stated changes, scan the audit data for untapped opportunities the client didn't mention:

### 3a. Unlinked pain points

Scan `pain_points[]` for entries whose `pain_point_id` does not appear in any `proposed_changes[].linked_pain_point_ids`. For each:
- Can this pain point be addressed by automation, tool replacement, or AI enablement?
- If yes: create a new proposed_change with `source: "analyst"`

### 3b. Unused API potential and migration flags

Scan `tools[]` for entries with `api_available: true`. Cross-reference against `proposed_changes[].proposed_tools`. For tools with APIs that no change leverages:
- What automations could this API enable?
- What manual steps currently use this tool that could be automated?

Also scan `tools[]` for entries with `migration_research_flag: true`. For flagged tools that no existing change addresses with `initiative_type: "data_migration"`:
- Is there a proposed change that depends on this tool but was classified as a plugin with `access_method: "manual_upload"`? If so, note that migrating to an API-accessible alternative could upgrade this from manual-upload plugin to a fully connected plugin.
- Are there processes that are entirely blocked by this tool's lack of API? If so, create an analyst-sourced proposed change with `initiative_type: "data_migration"`.

### 3c. AI enablement opportunities

Based on the client's processes and industry, identify opportunities for:
- **AI call transcription/analysis** -- if they have sales calls, support calls, or client meetings
- **AI document processing** -- if they handle forms, applications, or compliance docs
- **AI-assisted decision making** -- if they have manual triage, scoring, or matching processes
- **AI content generation** -- if they produce reports, emails, or marketing content
- **AI sales coaching** -- if they have BDMs or sales teams

These are `value_type: "productivity_enhancement"` -- same hours, more output.

### 3d. Create new entries

For each new opportunity:

1. Assign next sequential `change_id` (e.g., if last is CH-006, start at CH-007)
2. Set `source: "analyst"`
3. Determine `change_type` (automate, replace, eliminate, consolidate)
4. Link to relevant `pain_point_ids`, `linked_waste_item_ids`, and `affected_step_ids`
5. Create a matching `roi_items[]` entry with `roi_item_id` assigned sequentially
6. Set `linked_roi_item_id` on the proposed_change
7. **Build `source_evidence[]`** the same way EI does — for each linked pain point / waste item / optimisation, pull its citation tuple `(quote, speaker, source_session, source_timestamp_seconds)`, resolve `fathom_url` from `extraction.sessions[].fathom_url + "?t=" + source_timestamp_seconds`, de-dupe by `(source_session, source_timestamp_seconds)`, keep ≤8. **A new analyst-sourced change with zero usable citations is a red flag — drop it or downgrade to LOW confidence.**
8. **Dispatch a sub-agent** to research this new change (same pattern as Stage 2e, using the same schema and pricing references already loaded)
9. Set `value_type` based on whether this saves time, enhances productivity, or both

### 3e. Assemble Plugin Bundles

After all proposed_changes (client-stated and analyst-generated) have their `skill_definition` fields, group them into `plugin_bundles[]`. This replaces the SA-level process-grouping logic with a single authoritative bundle definition.

**Grouping rules:**
1. Collect all proposed_changes where `plugin_candidate: true` and `skill_definition` is not null
2. Group by `skill_definition.suggested_plugin_group`
3. For groups with 2+ changes, the group becomes one plugin bundle containing multiple skills
4. For groups with only 1 change, the change still becomes a bundle (single-skill plugin)

**Build each bundle:**

```json
{
  "bundle_id": "PLG-001",
  "plugin_name": "{client_slug}-{suggested_plugin_group}",
  "plugin_title": "{human-readable title, 2-4 words, process-level}",
  "description": "{one sentence: what business process this plugin automates}",
  "skills": [
    {
      "skill_id": "SK-001",
      "change_id": "CH-002",
      "skill_name": "{skill_definition.skill_name}",
      "skill_title": "{skill_definition.skill_title}",
      "trigger": "{skill_definition.trigger}",
      "inputs": "{skill_definition.inputs}",
      "workflow_steps": "{skill_definition.workflow_steps}",
      "outputs": "{skill_definition.outputs}"
    }
  ],
  "connectors": [
    {
      "name": "{tool_name} MCP",
      "purpose": "{how this connector is used across the plugin's skills}"
    }
  ],
  "shared_data_layer": "{the shared Google Sheet, SaaS, or DB that multiple skills read from}",
  "covered_change_ids": ["CH-002", "CH-003"],
  "complexity_tier": "{MAX across covered changes: simple < standard < complex}",
  "price_range_low_aud": "{see process plugin pricing rules below}",
  "price_range_high_aud": "{see process plugin pricing rules below}",
  "combined_annual_value_aud": "{sum of combined_annual_value_aud across all covered changes, or sum of plugin_assessment.annual_saving_aud if value not yet calculated}",
  "confidence": "{MIN across covered changes: LOW < MEDIUM < HIGH}",
  "generated_at": "{ISO datetime}"
}
```

**Connector de-duplication:** Union the `skill_definition.inputs[].access_method` values across all skills in the bundle. Map each to a connector name:
- `sheets_mcp` → "Google Sheets MCP"
- `gmail_mcp` → "Gmail MCP"
- `xero_api` → "Xero API (via MCP wrapper)"
- `manual_upload` → (no connector needed, human-supplied)
- `human_text_input` → (no connector needed)

**Plugin title guidelines:** Process-level, not task-level.
- Good: "Financial Reconciliation", "Operations & Scheduling", "Client Invoicing", "Communications"
- Bad: "Invoice Checker", "Job Matcher Plugin", "Automate reconciliation"

**skill_id assignment:** Sequential within each bundle: SK-001, SK-002, etc. Reset per bundle.

**bundle_id assignment:** Sequential across all bundles: PLG-001, PLG-002, etc.

**Write to opportunities.json:** After assembling all bundles, write `plugin_bundles[]` as a top-level key on the opportunities dict alongside `proposed_changes[]`. Also write `plugin_bundle_id` on each cowork_plugin proposed_change to link it to its parent bundle (e.g. `"PLG-001"`). Proposed_changes that are not plugin candidates get `plugin_bundle_id: null`.

Display bundle summary:
```
PLUGIN BUNDLES ASSEMBLED
  {n} bundles from {n} plugin-candidate changes

  PLG-001  Financial Reconciliation       2 skills (CH-002, CH-003)   $4,500-$8,000   $4,502/yr
  PLG-002  Operations & Scheduling        3 skills (CH-009, CH-012, CH-015) $6,500-$12,000  $17,738/yr
  ...
```

---

## Stage 4: Display Summary

```
RESEARCH COMPLETE -- {company_name}
Run #{run_count} -- {datetime}

Sub-agents dispatched: {total_dispatched} in {batch_count} batches
  Successful: {n}
  Failed: {n}

Existing changes researched: {n}/{total}
New opportunities generated: {n}

CLIENT-STATED CHANGES (source: client)
| # | ID     | Title                          | Initiative Type | Plugin? | Complexity | Price Range       | Annual Saving | Custom Build | Status       | Gaps |
|---|--------|--------------------------------|-----------------|---------|------------|-------------------|---------------|--------------|--------------|------|
| 1 | CH-001 | Automate onboarding pack       | automation      | no      | --         | --                | $12,000/yr    | feasible     | complete     | 0    |
| 2 | CH-006 | Voice scheduling engine        | cowork_plugin   | YES     | simple     | $3,000-$4,500     | $45,500/yr    | feasible     | complete     | 0    |
...

ANALYST-GENERATED OPPORTUNITIES (source: analyst)
| # | ID     | Title                          | Initiative Type | Plugin? | Complexity | Price Range       | Annual Saving | Custom Build | Status       | Gaps |
|---|--------|--------------------------------|-----------------|---------|------------|-------------------|---------------|--------------|--------------|------|
| 1 | CH-007 | AI call analysis for BDMs      | cowork_plugin   | YES     | standard   | $4,500-$6,500     | $31,200/yr    | feasible     | complete     | 0    |
...

Plugin summary:
  Plugin candidates: {n} of {total} changes
  Total indicative plugin range: ${low_sum}-${high_sum}
  Education bundle: {YES if total >= $15,000 -> "Education included free"; else "Available as $2,500 add-on"}

Changes with gaps:
  * CH-008: "Need to confirm ShiftCare API rate limits for batch roster updates"

Tool specificity check:
  v All tool names are specific products: {pass_count}/{total_count}
  x Generic tool names found: {list any generic names that need fixing}

!! BLOCKED -- Generic tool names detected (see above). Fix these before saving.

Next step: Run [BO] to build the outlook and risks, then [BR] to estimate weeks and calculate value.
```

### Generic Name Detection

Scan every `proposed_tools[]` entry across all changes. **BLOCK the save** if any match these patterns (case-insensitive):
- "scheduling platform", "scheduling tool", "scheduling system"
- "rostering tool", "rostering platform", "rostering system"
- "CRM system", "CRM platform", "CRM tool"
- "automation platform", "automation tool"
- "SMS API integration", "SMS platform"
- "invoicing platform", "invoicing tool"
- Any entry containing "platform", "tool", "system", or "provider" as a standalone word without a specific product name prefix

If generic names are found, go back and research specific alternatives before proceeding.

---

## Stage 5: Save

**Pre-save: Sync `proposed_tools[]` from research**

Before writing, for each proposed_change that has a `research.tools_researched[]` array:
1. Find the entry where `is_recommended: true`
2. Set `proposed_tools[]` to the recommended tool's `tool_name` (plus any secondary tools)
3. If `proposed_tools[]` still contains generic names (see Generic Name Detection above), **do not save** -- go back and fix

**Save:**

1. Write the full updated `opportunities` dict to `clients/{client_slug}/03-audit/data/opportunities.json` (includes all `proposed_changes[]` with final research and `plugin_candidate` values, all `roi_items[]`, and `risk_register[]`). Write the full updated `extraction` dict to `clients/{client_slug}/03-audit/data/extraction.json` (includes all `processes[].plugin_scope` updates). For v2 fallback: write to top-level keys in `audit-data.json` as before.
2. Update `clients/{client_slug}/03-audit/data/audit-manifest.json`: set `domains.opportunities.updated_at` and `domains.extraction.updated_at` and the root `updated_at` to the current ISO datetime. Skip for v2 fallback.
3. Update `analyst_metadata` on the audit data:
   ```json
   {
     "analyst_metadata": {
       "last_analysis_run": "{ISO datetime}",
       "total_runs": "{n}",
       "changes_researched": "{n}",
       "changes_with_gaps": "{n}",
       "new_opportunities_generated": "{n}",
       "sub_agents_dispatched": "{n}",
       "sub_agents_failed": "{n}"
     }
   }
   ```
4. Confirm save with summary
