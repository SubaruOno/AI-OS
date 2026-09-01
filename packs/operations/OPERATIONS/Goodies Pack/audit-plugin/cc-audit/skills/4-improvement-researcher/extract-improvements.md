---
name: extract-improvements
description: Synthesise proposed_changes[] and roi_items[] from completed audit data. First capability to run after audit_status = process_map_complete.
menu-code: EI
---

# Extract Improvements (EI)

> **Idempotent.** First run synthesises all proposed changes. Re-runs regenerate from source data — analyst enrichments (research, value, modal_content) on entries with matching change_ids are preserved.

## Purpose

Scan the completed audit data and synthesise `proposed_changes[]` from `optimisations[]`, `pain_points[]`, and `waste_items[]`. Each proposed change represents a concrete opportunity the client either stated directly or that clusters naturally from their pain points. This capability also creates or updates `roi_items[]` entries linked to each change.

**This is the bridge between extraction (Process Mapper) and analysis (RI/BR).** It runs once after `audit_status == "process_map_complete"` and must complete before any other analyst capability.

---

## Stage 1: Pre-flight

1. Load audit data for selective context:
   - Check for `clients/{client_slug}/03-audit/data/audit-manifest.json`. If present (v4), read domain files directly:
     - Read `clients/{client_slug}/03-audit/data/audit-manifest.json` to check `audit_status` (duplicated at the manifest root for quick access)
     - Read `clients/{client_slug}/03-audit/data/meta.json`
     - Read `clients/{client_slug}/03-audit/data/extraction.json`
     - Read `clients/{client_slug}/03-audit/data/findings.json`
     - Do NOT read `opportunities.json`, `strategy.json`, or `architecture.json` (EI creates opportunities fresh)
   - If `audit-manifest.json` does not exist, fall back to v3/v2 behavior: load the full `audit-data.json` file
   - Check `audit_status` in `meta` (or top-level for v2) — must be "process_map_complete" or halt

2. Check `audit_status`:
   ```
   ✗ audit_status is "{status}" — must be "process_map_complete" before running EI.
     Run Process Mapper until all sessions are analyzed and audit is marked process_map_complete.
   ```

3. Check source arrays are populated:
   ```
   SOURCE DATA — {company_name}
   Pain points:    {n}  (by stage: {stage_counts})
   Optimisations:  {n}  (by stage: {stage_counts})
   Waste items:    {n}  (total annual waste: ${total}/yr)
   ROI items:      {n}
   Process steps:  {n}  across {n} stages
   ```
   If `pain_points[]` AND `optimisations[]` are both empty, halt:
   ```
   ✗ No pain points or optimisations found. The Process Mapper needs to extract these first.
   ```

4. If `proposed_changes[]` is already populated:
   ```
   ⚠ proposed_changes[] already has {n} entries.

   Options:
     A) Regenerate all — rebuild from source data (preserves analyst enrichments on matching IDs)
     B) Show existing — display current proposed changes and exit
     C) Cancel
   ```
   Wait for user selection. On "A", proceed. On "B", display the summary table from Stage 4 and stop.

---

## Stage 2-alpha: Transfer Mechanism Scan

[Guard: Legacy Data]
Before running this stage, check: does any `sequence_flows[]` entry in extraction.json have a `handoff` object? If no flows have handoff objects, log "[Stage 2-alpha] Skipped — no handoff data in extraction (legacy format)" and proceed directly to Stage 2.

If handoff objects exist:

### Step 2a-1: Walk all handoffs

For each process in extraction.json:
  For each sequence_flow with a `handoff` object:
    Load: source_tool, mechanism, destination_tool, data_transferred

### Step 2a-2: Classify automation signal

| mechanism | action |
|-----------|--------|
| copy_paste | STRONG signal → create proposed_change (change_type: "automate") |
| manual_export_import | STRONG signal → create proposed_change (change_type: "automate") |
| email_forward | MODERATE signal → create proposed_change if both tools have APIs |
| verbal | WEAK signal → create proposed_change (change_type: "consolidate") |
| paper | WEAK signal → create proposed_change (change_type: "consolidate") |
| unknown | CHECK — look at from_step and to_step iato fields for clues |
| api_sync | SKIP — already automated |
| automated_sync | SKIP — already automated |

### Step 2a-3: Create proposed_change for each signal

For each handoff with a strong/moderate signal:

```json
{
  "change_id": "CH-{next_id}",
  "source": "analyst",
  "change_type": "automate",
  "affected_step_ids": ["from_step_id", "to_step_id"],
  "source_handoff_ids": ["flow_id"],
  "stage": "{process_stage of the from_step}",
  "proposed_solution": "Automate the transfer of {handoff.data_transferred} from {handoff.source_tool} to {handoff.destination_tool}, replacing the current {handoff.mechanism} process.",
  "proposed_tools": ["{handoff.source_tool}", "{handoff.destination_tool}"],
  "confidence": "MEDIUM",
  "source_evidence": []
}
```

Add source_evidence from the sources[] of the from_step and to_step.

### Step 2a-4: Set volume_weight

For each new proposed_change:
  Walk backwards through sequence_flows from the `from` step
  Find the nearest upstream exclusive_gateway with volume_split on its outgoing flows
  If found AND the path to this change's from_step has a volume_split:
    volume_weight = volume_split.percentage / 100
  Else:
    volume_weight = 1.0

### Step 2a-5: De-duplicate against Stage 2 candidates

If an optimisation from Stage 2 already describes the same handoff (same source_tool + destination_tool + stage):
  Merge: add handoff metadata to the existing change rather than creating a duplicate
  Specifically: add source_handoff_ids and set volume_weight on the existing change

---

## Stage 2: Synthesise from Optimisations

Each `optimisations[]` entry becomes a proposed_change candidate. The client explicitly asked for these.

For each optimisation:

### 2a. Determine change_type

Infer from the optimisation description:
- **automate** — "automated", "one-click", "self-service", "bulk", "AI-assisted", "system does X"
- **replace** — "switch to", "use [tool] instead", "centralised platform"
- **eliminate** — "remove", "stop doing", "no longer need"
- **consolidate** — "combine", "single system", "merge", "centralised" (when merging multiple existing tools/steps)

When ambiguous, default to `automate`.

### 2b. Find affected steps

Scan `processes[].steps[]` for steps that:
- Are in the same `stage` as the optimisation
- Have `type: "pain"` or `type: "optimisation"` related to this change
- Use tools mentioned in the optimisation
- Describe the activity the optimisation addresses

Collect matching `step_id` values into `affected_step_ids[]`.

### IATO Data Lineage Matching (new — runs if iato fields present)

After the existing step matching, also check:

1. For each proposed_change, look at the affected steps' iato.output fields
2. Find steps in adjacent positions (next step in sequence_flows) where iato.input differs substantially from the previous step's iato.output
   - "Substantially different" means: one is a physical document, the other is a system field; or one is structured data, the other is manually typed/copied
3. Steps where this format mismatch exists are automatic additional affected_step_ids
4. A format mismatch is itself a signal — add a note to the proposed_change's `proposed_solution` if this pattern is found: "Note: data format changes between steps ({step_A}: {iato.output} → {step_B}: {iato.input}), suggesting manual re-entry."

### 2c. Link pain points

Scan `pain_points[]` for entries that:
- Are in the same `stage`
- Describe problems that this optimisation directly addresses (semantic match on description)
- Reference the same tools or activities

Collect matching `pain_point_id` values into `linked_pain_point_ids[]`.

### 2d. Link waste items

Scan `waste_items[]` for entries that:
- Are in the same `stage`
- Track time spent on the activity this optimisation would improve

Collect matching `waste_id` values into `linked_waste_item_ids[]`. When linked, use the waste item's `hours_per_week` and `hourly_rate_aud` to populate `time_saving_minutes_per_occurrence` and `frequency`.

### 2d-bis. Build source_evidence (mandatory — source trail)

Build `source_evidence[]` from the linked pain points, optimisations, and waste items. For each linked entity, look up its citation tuple (`source_quote`, `speaker`, `source_session`, `source_timestamp_seconds`) and resolve `fathom_url` via `extraction.sessions[]`:

```
fathom_url = sessions[source_session].fathom_url + "?t=" + str(source_timestamp_seconds)
```

Then de-dupe by `(source_session, source_timestamp_seconds)` and keep at most ~8 entries (prefer HIGH-confidence ones; prefer the originating optimisation/pain-point quote that drove the change). If a linked entity has no quote/timestamp, **skip it** — never fabricate a citation. If the entire change has zero usable citations, downgrade `confidence` to LOW and leave a note in `proposed_solution` flagging it for RI to re-check.

**This step is mandatory.** After processing all linked entities for a change, verify that `source_evidence[]` is not empty. If it is still empty, log a warning: `"⚠ CH-{id}: source_evidence[] is empty after processing all linked entities. No citations available."` Do not proceed silently — the warning must appear in the Stage 7 display. A change with zero citations is a data integrity issue.

### 2e. Build the proposed_change entry

```json
{
  "change_id": "CH-{sequential, zero-padded to 3 digits}",
  "title": "{concise action title derived from optimisation description}",
  "change_type": "{inferred from 2a}",
  "source": "client",
  "affected_step_ids": ["{from 2b}"],
  "linked_roi_item_id": "ROI-{matching or new}",
  "linked_pain_point_ids": ["{from 2c}"],
  "linked_waste_item_ids": ["{from 2d}"],
  "source_evidence": [
    {
      "ref_id": "PP-008",
      "ref_type": "pain_point",
      "quote": "verbatim utterance",
      "speaker": "Jordan Lee",
      "source_session": 1,
      "source_timestamp_seconds": 1302,
      "fathom_url": "https://fathom.video/calls/<id>?t=1302"
    }
  ],
  "proposed_solution": "{the optimisation description, cleaned up as a concrete solution statement}",
  "proposed_tools": ["{tools mentioned in optimisation or inferred from context}"],
  "time_saving_minutes_per_occurrence": null,
  "frequency": "{from waste item or optimisation context}",
  "stage": "{optimisation stage}",
  "confidence": "{inherit from optimisation}",
  "initiative_type": null,
  "plugin_candidate": null,
  "parent_finding_ids": []
}
```

**Title guidelines:**
- Start with a verb: "Automate...", "Replace...", "Build...", "Consolidate..."
- Be specific: "Automate payment collection with EFT portal" not "Improve payments"
- Keep under 60 characters

---

## Stage 3: Synthesise from Unlinked Pain Points

After processing all optimisations, scan `pain_points[]` for entries whose `pain_point_id` does NOT appear in any proposed_change's `linked_pain_point_ids[]`.

For each unlinked pain point (or cluster of related unlinked pain points in the same stage):

### 3a. Cluster related pain points

Group unlinked pain points by:
- Same `stage`
- Same theme (from `pain_points_summary.top_themes` if available)
- Addressing the same underlying problem

A cluster of 2-3 related pain points becomes ONE proposed_change, not three.

### 3b. Determine if actionable

Not every pain point needs a proposed_change. Skip if:
- It's a constraint that can't be changed (e.g., "industry regulation requires X")
- It's already addressed by an optimisation-derived change (double-check)
- It's a symptom of another pain point that already has a change

### 3c. Create proposed_change

Same structure as Stage 2e. Set:
- `source: "client"` — the pain point came from the client's own words
- `linked_pain_point_ids` — the cluster of pain point IDs
- `proposed_solution` — synthesise a solution from the pain point description and context
- Title should reflect what we'd build/do, not the problem

### 3d-multi. Multi-initiative spawning (applies to Stage 2 and Stage 3)

A single finding can spawn **more than one proposed_change** when it clearly maps to two different initiative types. Hard cap: 2 initiatives per finding.

**When to spawn two:** The finding contains two distinct, separable opportunities — e.g., "quoting is slow AND we need to auto-push the won deal to SharePoint." The first is a Plugin (human-invoked quoting workflow), the second is an Automation (background event trigger).

**When NOT to spawn two:** The finding is ambiguous, or the second opportunity is a minor sub-step of the first. In doubt, one change.

**How to link related initiatives:** Set `parent_finding_ids` to the same source ID(s) on both changes. Use:
- For optimisation-sourced changes: `["{optimisation_id}"]`
- For pain-point-sourced changes: `["{pain_point_id}", ...]`
- For handoff-sourced changes: `["{flow_id}"]`

Linked changes (sharing a `parent_finding_id`) will be presented as a group on the blueprint under the heading "This addresses the same bottleneck."

---

## Stage 3e: Control Gap Scan

[Guard: Legacy Data]
Before running, check: does findings.json contain a non-empty control_gaps[] array? If absent or empty, log "[Stage 3e] Skipped — no control_gaps[] in findings (legacy format or not yet extracted)" and proceed.

For each control gap in findings.json control_gaps[]:

### Control gap types and their proposed changes:

**"no_approval"** (no approval step before financial transaction or client-facing output):
  proposed_solution: "Add automated approval workflow with configurable threshold. Approvals below threshold auto-approve; above threshold route to {relevant_role} for review."
  change_type: "automate" (if a tool can handle it) or "consolidate" (if manual process needed first)
  value_type: "risk_reduction"

**"no_quality_check"** (no verification before customer-facing output):
  proposed_solution: "Add structured quality verification checklist before {deliverable} is sent to client. Verification logged automatically."
  change_type: "consolidate"
  value_type: "risk_reduction"

**"no_audit_trail"** (financial or compliance activity with no logging):
  proposed_solution: "Add automated logging and audit trail for {process}. All actions timestamped with actor and outcome."
  change_type: "automate"
  value_type: "risk_reduction"

Create the proposed_change:

```json
{
  "change_id": "CH-{next_id}",
  "source": "control_gap",
  "change_type": "{as above}",
  "control_gap_ids": ["{control_gap.control_gap_id}"],
  "affected_step_ids": ["{control_gap.step_id}"],
  "stage": "{process_stage of the affected step}",
  "proposed_solution": "{as above, with {placeholders} filled from control_gap fields}",
  "confidence": "{inherit from control_gap.severity: 'high' → 'HIGH', 'medium' → 'MEDIUM'}",
  "value_type": "risk_reduction",
  "volume_weight": 1.0
}
```

De-duplicate: if an existing proposed_change already covers the same step, add the control_gap_id to that change's control_gap_ids[] rather than creating a duplicate.

---

## Stage 4: Deduplication Pass

Review all proposed_change candidates for overlap:

### 4a. Same affected steps

If two candidates share >50% of their `affected_step_ids`, they likely address the same process bottleneck. Merge into one change that covers both.

### 4b. Same waste items

If two candidates share any entries in `linked_waste_item_ids[]`, consider merging — the waste saving should only be counted once. When merging, union `linked_pain_point_ids`, `linked_waste_item_ids`, `affected_step_ids`, and `source_evidence[]` (re-de-dupe the merged `source_evidence` by `(source_session, source_timestamp_seconds)`).

### 4c. Subsumption

If one candidate (e.g., "Centralised platform replacing Excel, TeamUp, and Wix") subsumes another (e.g., "Replace TeamUp with better scheduling tool"), keep the broader one and absorb the narrower one's pain_point links.

When merging: combine `linked_pain_point_ids`, `affected_step_ids`, and keep the broader title and solution.

---

## Stage 4.5: Source Evidence Validation

After deduplication and before creating ROI items, run a source evidence check across all proposed_changes:

1. **Scan for empty source_evidence[]**: For each proposed_change, check if `source_evidence` is null, missing, or `[]`.

2. **Attempt reconstruction for empty entries**: For any change with empty source_evidence:
   - Walk `linked_pain_point_ids`: for each, pull `(source_quote, speaker, source_session, source_timestamp_seconds)` from `pain_points[]`. Skip entries where `source_quote` is null.
   - Walk `linked_waste_item_ids`: same from `waste_items[]`.
   - Walk `linked_optimisation_ids`: pull `(quote, speaker, source_session, source_timestamp_seconds)` from `optimisations[]`. Skip entries where `quote` is null.
   - Resolve `fathom_url = sessions[source_session].fathom_url + "?t=" + source_timestamp_seconds` for each.
   - De-dupe by `(source_session, source_timestamp_seconds)`, keep ≤8. Populate `source_evidence[]`.
   - Log: `"Reconstructed source_evidence for CH-{id}: {n} entries"`

3. **Report**: display a count of changes with populated vs empty source_evidence after reconstruction.

4. **If source_evidence is still empty after reconstruction**: downgrade `confidence` to LOW. Append to `proposed_solution`: `"[Source trail incomplete — no citations found in linked extraction items. RI should search for direct quotes.]"` Do not block the save — flag it prominently in the display.

```
SOURCE EVIDENCE VALIDATION
──────────────────────────────────────────────────────────────────
Total changes:              {n}
With source_evidence:       {n}  (populated by 2d-bis)
Empty — reconstructed:      {n}  (rebuilt from linked IDs)
Empty — no citations found: {n}  ⚠ confidence downgraded to LOW

⚠ Changes with zero citations: {list CH-IDs}
──────────────────────────────────────────────────────────────────
```

If more than half the changes have empty source_evidence after reconstruction, emit a WARNING before proceeding:

```
!! WARNING: {n}/{total} proposed changes have no source citations.
   This indicates a systemic issue with the extraction data source_quote fields.
   Run Process Review (PR), Findings Review (FR), and Waste Review (WR) to audit
   source traceability before proceeding.
```

---

## Stage 4.7: Gap Blocker Check

[Guard: Legacy Data]
Before running, check: does findings.json contain a non-empty gaps_register[] array? If absent, log "[Stage 4.7] Skipped — no gaps_register[] in findings (legacy format)" and proceed.

### Step 4.7a: Find overlaps

For each unresolved Type A gap in gaps_register[] (status != "resolved", gap_type == "A"):
  For each proposed_change in current session's proposed_changes[]:
    Check: does any of the gap's affected_step_ids appear in the change's affected_step_ids?
    If yes: match found

### Step 4.7b: Classify impact

For each matched (gap, change) pair:
  Count: what percentage of the change's affected_step_ids are covered by unresolved Type A gaps?
  If > 50%: serious impact — downgrade change confidence to "LOW", add gap_id to blocked_by_gaps[]
  If 1-50%: partial impact — keep confidence, add gap_id to blocked_by_gaps[] with note

### Step 4.7c: Display summary

Show before proceeding to the save stage:

```
GAP BLOCKER SUMMARY
  Type A gaps (unresolved): {n}
  Proposed changes affected: {n}
  
  Seriously blocked (>50% steps affected):
  - CH-003: {title} — blocked by GAP-001 ({gap description})
  - CH-007: {title} — blocked by GAP-005 ({gap description})
  Confidence downgraded to LOW for these changes.

  Partially affected:
  - CH-012: {title} — GAP-002 affects 1 of 3 steps (noted, confidence unchanged)
```

### Output

Add to each affected proposed_change:
  "blocked_by_gaps": ["GAP-001", "GAP-005"]
(empty array [] if no gaps affect this change — always present as an array, never null)

---

## Stage 5: Create/Update ROI Items

For each proposed_change, ensure a matching `roi_items[]` entry exists:

1. If an existing `roi_items[]` entry clearly matches (same activity, same stage): link it via `linked_roi_item_id`
2. If no match: create a new entry:

```json
{
  "roi_item_id": "ROI-{sequential}",
  "activity": "{derived from change title}",
  "annual_saving_aud": null,
  "monthly_saving_aud": null,
  "suggested_tier": "{complexity heuristic}",
  "build_cost_aud": null,
  "payback_months": null,
  "payback_tag": null,
  "quote": "{best source quote from linked pain points or optimisation}",
  "source_session": "{from source data}",
  "confidence": "{inherit}"
}
```

**Suggested tier heuristic** (preliminary — refined by RI Stage 2e quick win qualification):
- `micro` — single tool config or simple automation (e.g., email template, N8N trigger). Note: not all micro items are quick wins — RI will validate with a concrete <10hr implementation plan
- `standard` — single tool integration or moderate custom work (e.g., API connection, form builder)
- `complex` — multi-tool integration or significant custom development (e.g., custom portal, platform migration)
- `sprint` — full platform build or major system overhaul (e.g., centralised admin system with roles)
If linked waste items have `annual_waste_aud` calculated, initialise `annual_saving_aud` with that value (BR will refine later).

---

## Stage 6: Preserve Analyst Enrichments (Re-run Only)

On re-run (when `proposed_changes[]` was already populated):

For each new proposed_change candidate, check if an existing entry has:
- The same `change_id`, OR
- The same `title` (fuzzy match), OR
- Overlapping `linked_pain_point_ids` (>50% overlap)

If matched, **preserve** these fields from the existing entry:
- `research` (entire sub-object)
- `implementation` (entire sub-object)
- `value` (entire sub-object)
- `modal_content` (entire sub-object)
- `phase`, `phase_label`, `sequence_order`, `depends_on`
- `future_step_description`, `future_step_owner`, `future_step_tools`, `future_step_type`

Update only the EI-owned fields: `title`, `change_type`, `affected_step_ids`, `linked_pain_point_ids`, `linked_waste_item_ids`, `source_evidence`, `proposed_solution`, `proposed_tools`, `stage`, `source`.

---

## Stage 7: Display Summary

```
EI COMPLETE — {company_name}
Proposed changes created: {n}
ROI items created/updated: {n}

| # | ID     | Title                              | Type        | Stage       | Source        | Vol.Weight | Blocked | Ctrl Gaps | Pain Points    | Waste Linked | ROI Item |
|---|--------|------------------------------------|-------------|-------------|---------------|------------|---------|-----------|----------------|--------------|----------|
| 1 | CH-001 | Automate payment collection...     | automate    | onboarding  | client        | 1.0        | —       | —         | PP-002, PP-003 | W-001        | ROI-001  |
| 2 | CH-002 | Self-service makeup booking...     | automate    | fulfilment  | analyst       | 0.6        | GAP-003 | —         | PP-008         | —            | ROI-002  |
| 3 | CH-003 | Add approval workflow...           | automate    | invoicing   | control_gap   | 1.0        | —       | CG-001    | —              | —            | ROI-003  |
...

Deduplication: {n} candidates merged into {n} changes
Transfer mechanism scan (Stage 2-alpha): {n} handoff signals → {n} new changes
Control gap scan (Stage 3e): {n} control gaps → {n} new changes
Gap blocker check (Stage 4.7): {n} changes blocked (confidence downgraded), {n} partially affected
Unlinked pain points addressed: {n}
Pain points still unlinked: {n} (will be scanned by RI for new opportunities)

Source evidence: {n}/{total} changes have populated source_evidence[]
{If any empty: ⚠ {n} changes have no citations — flagged in proposed_solution. Run RI with extra attention to these.}

Next step: Run [RI] to research tools/APIs and generate new analyst opportunities.
```

---

## Stage 8: Save

1. Write the full `opportunities` domain to `clients/{client_slug}/03-audit/data/opportunities.json` — include `proposed_changes`, `roi_items`, and `risk_register` (initialise as empty array if not present). For v2 fallback: write `proposed_changes` and `roi_items` to top-level keys in `audit-data.json` as before.

   Each proposed_change must include these new fields (write defaults when not set by earlier stages):
   ```json
   {
     "volume_weight": 1.0,
     "blocked_by_gaps": [],
     "source_handoff_ids": [],
     "control_gap_ids": [],
     "source": "client"
   }
   ```
   Valid values for `source`: `"client"`, `"analyst"`, `"control_gap"`.
   `blocked_by_gaps` must always be an array, never null.

2. Update `clients/{client_slug}/03-audit/data/audit-manifest.json`: set `domains.opportunities.updated_at` to current ISO datetime and update the root `updated_at` field. Skip manifest update for v2 fallback.
3. Confirm save with file path and entry counts
4. Remind: "Run [RI] next to research each proposed change and generate new opportunities."
