---
name: merge-extraction
description: Rules for the parent SU orchestrator to merge sub-agent JSON extraction results into the audit domain files. Load this after each sub-agent returns before writing to disk.
---

# Merge Extraction Results

## Purpose

After a sub-agent returns its JSON extraction result, the parent agent uses these rules to merge it into the in-memory audit data. Apply rules in the order listed. Checkpoint-save after each successful merge.

---

## Step 1 — Source Attribution Gate (abort on failure)

Before merging, run the Source Attribution Gate. This is a hard gate — if any check fails, the merge is aborted, the source is marked `failed` in `ingestion-manifest.json`, and the SU loop continues to the next source. No partial writes.

### 1a — Structural validation

- Parse the sub-agent response as JSON. On parse failure: mark source as `failed` with `failure_reason: "json_parse_error"` and skip.
- Confirm `extraction_stats` is present and an object. Otherwise mark `failed` with `failure_reason: "missing_extraction_stats"`.

### 1b — Source Attribution Gate (pre-merge validator)

Write the sub-agent JSON to a temporary file, then run:

```bash
python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_sub_agent_output.py \
    --extraction-json <tmp-file> \
    --source-type {source_type} \
    --source-path {source_path} \
    --session-number {session_number_or_null}
```

The validator iterates every item in `new_steps`, `new_pain_points`, `new_waste_items`, `new_optimisations`, `new_business_metrics`, `tool_updates` (action=create), `staff_updates` (action=create), and `new_contradictions`. `new_sequence_flows[]` entries are not gated (they inherit attribution from connected steps). For each gated item it enforces:

- `len(sources) >= 1` (for contradictions: `>= 2`)
- Each entry has `kind` ∈ {`"fathom"`, `"document"`}, non-empty `quote`, valid `confidence`
- `kind == "fathom"`: integer `session_id`, numeric `timestamp_seconds`, non-empty `speaker`
- `kind == "document"`: non-empty `document_path`
- At least one entry's `kind` matches the expected form for `{source_type}` (`fathom_meeting` → `fathom`; everything else → `document`)

**On exit code != 0:** the validator prints a structured JSON failure report listing every offending item. Mark this source as `failed` in `ingestion-manifest.json` with `failure_reason: "source_attribution_gate"` and `failure_detail` set to the count + first 3 failures. Print the failure report verbatim to stdout prefixed by `SOURCE ATTRIBUTION GATE — FAIL ({n} items) — {source_path}`. Do NOT proceed to Steps 2–18. Continue to the next source.

**On exit code 0:** continue to Step 1c.

### 1c — ID format check

Check all IDs in the result follow the expected format (PP-###, W-###, etc.). Fix any that don't.

---

## Step 2 — Merge Stages

For each entry in `new_stages[]`:
- If `stage` key not in `processes[]`: append a new processes entry with `stage`, `name`, `description`, empty `steps[]`, and `parallel_tracks` (write the `parallel_tracks` array from the sub-agent output; omit the key if empty or null).
- If `stage` key already exists: skip stage-level fields (stage already known, steps will be added in Step 3). If the existing stage has no `parallel_tracks` and the sub-agent provided them, write `parallel_tracks` onto the existing stage entry now.

## Step 2b — Merge Stage Parallel Track Updates

For each entry in `stage_track_updates[]` (may be absent — skip silently if not present):
- Find the matching stage in `processes[]` by `stage` key.
- If the stage has no `parallel_tracks` key yet: write the provided `parallel_tracks` array.
- If the stage already has `parallel_tracks`: merge — add any tracks whose `label` is not already present. Do not remove or overwrite existing tracks. For existing tracks with the same label, merge `step_ids` (union, no duplicates).

---

## Step 3 — Merge Process Steps

For each entry in `new_steps[]`:
1. **Find or verify the target stage** in `processes[]` by `stage` key.
2. **Dedup check** — scan existing steps in that stage for high similarity (>80% description overlap). If a near-duplicate exists: enrich the existing step with new quotes/timestamps rather than appending a duplicate. Log as "enriched existing step {step_id}".
3. **ID validation** — verify `step_id` doesn't already exist anywhere in `processes[]`. If collision: auto-increment the suffix (e.g. ACQ-016 → ACQ-017) until unique.
4. **Append** the step to `processes[].steps[]` for the correct stage.

### Merge rules for IATO fields

When a sub-agent extracts a step that already exists (matched by step_id):
- For each IATO field (input, action, actor, output):
  - If existing value is null and new value is non-null: UPDATE (fill the gap)
  - If existing value is non-null and new value is non-null AND new confidence is higher: UPDATE
  - If existing value is non-null and new value is non-null AND same confidence: KEEP EXISTING
- If a field was previously null (_gaps.missing_* = true) and is now filled: set _gaps.missing_* = false

### Merge rules for _gaps

- If new sub-agent fills a previously gapped field: set missing_* = false, clear gap_note
- If new sub-agent cannot fill a gap either: keep existing _gaps (do not overwrite with same information)
- Never set missing_* from false to true (do not un-fill a field)

### Merge rules for handoff

- If existing step has no handoff and new sub-agent provides one: ADD
- If existing step has handoff with mechanism="unknown" and new sub-agent provides a specific mechanism: UPDATE
- Otherwise: KEEP EXISTING

### Merge rules for volume_split on sequence flows

- If a sequence flow has no volume_split and new sub-agent provides one: ADD
- If existing volume_split has confidence="LOW" and new sub-agent provides MEDIUM or HIGH: UPDATE
- Otherwise: KEEP EXISTING

### Merge rules for subject_traces[]

- subject_traces is stored at the process level (inside processes[])
- When merging: add new traces from the sub-agent that don't overlap with existing traces (by subject name)
- If a trace already exists for the same subject: update entry_step_id, exit_step_ids, and steps_in_trace if the new version is more complete (completeness rank: complete > partial > fragment)

### Step 3c: Merge gaps_register[]

The gaps_register is stored in findings.json under the key `"gaps_register"`.

When merging:
1. Match existing gaps by `affected_step_id` + `affected_field` (unique key)
2. If gap already exists: check if the new sub-agent fills the gap (i.e., the corresponding `_gaps.missing_*` is now false on the step)
   - If filled: update gap status to `"resolved"`, set `resolved_at` timestamp
   - If still missing: keep existing gap, do not duplicate
3. If gap is new: append to `gaps_register[]`, assign next `gap_id` (GAP-NNN sequential)
4. After merge, link `gap_id` to any newly generated `follow_up_questions` via `fq_id`

Also ensure the `category: "extraction_gap"` value is respected on `follow_up_questions[]` entries for Type C gaps — these are excluded from the follow-up PPTX and handled by the [RQ] capability instead.

---

## Step 4 — Merge Tools

For each entry in `tool_updates[]`:

**If `action: "create"`:**
1. Dedup check — scan `tools[]` for case-insensitive `tool_name` match. If found, treat as `update_existing` instead.
2. Assign next `tool_id` if not set (use `T-{next}` format or match existing convention).
3. Append to `tools[]`.

**If `action: "update_existing"`:**
1. Find the existing tool in `tools[]` by `tool_name` (case-insensitive).
2. Merge `meeting_references[]` — append the new entry, do not overwrite existing.
3. If new `use_case` is more specific than existing: update `use_case`.
4. If new `monthly_cost_aud` differs from existing and confidence is higher: update with note.
5. If `workarounds` are new: append to existing `workarounds`.

---

## Step 5 — Merge Pain Points

For each entry in `new_pain_points[]`:
1. **Dedup check** — compare `description` against existing `pain_points[]` in the same stage. If >80% semantic overlap: enrich the existing entry (add the new quote, update source_session if more recent). Log as "enriched existing PP-{id}".
2. **ID validation** — verify `pain_point_id` doesn't already exist. If collision: auto-increment.
3. **Append** to `pain_points[]`.
4. Update `pain_points_summary.total_count` and `by_stage[{stage}]`.

---

## Step 6 — Merge Waste Items

For each entry in `new_waste_items[]`:
1. **Dedup check** — compare `activity` against existing `waste_items[]` in same stage. If near-duplicate: enrich (add meeting_references, update hours if more specific).
2. **ID validation** — verify `waste_id` doesn't already exist. If collision: auto-increment.
3. **Verify `annual_waste_aud` is populated.** If null: calculate `hours_per_week × headcount_affected × 50 × 52`. Always use the canonical $50/hr blended rate. Per-item rate fields, if present in legacy data, are ignored.
4. **Append** to `waste_items[]`.

---

## Step 7 — Merge Optimisations

For each entry in `new_optimisations[]`:
1. **ID validation** — verify `optimisation_id` doesn't exist. If collision: auto-increment.
2. **Append** to `optimisations[]`.

---

## Step 8 — Merge Sequence Flows

For each entry in `new_sequence_flows[]`:
1. **Identify target process** — find the process in `processes[]` whose steps contain the `from` step_id.
2. **Dedup check** — if `sequence_flows[]` on that process already has a flow with the same `(from, to)` pair, skip.
3. **Auto-assign ID** — if the flow entry has no `id`, assign `SF-{next_id}` based on the current count of flows in that process.
4. **Append** to `processes[].sequence_flows[]` on the correct process.

Note: `new_decision_nodes[]` is deprecated. Decision gateways are now inline steps in `new_steps[]` with `element_type: "exclusive_gateway"`, connected via `new_sequence_flows[]`.

---

## Step 9 — Merge Contradictions

For each entry in `new_contradictions[]`:
1. **Dedup check** — scan `contradictions[]` for same `topic`. If match: skip (already recorded).
2. **ID validation** — verify `contradiction_id` doesn't exist. If collision: auto-increment.
3. **Append** to `contradictions[]`.

---

## Step 10 — Merge Follow-Up Questions

For each entry in `new_follow_up_questions[]`:
1. **ID validation** — verify `fq_id` doesn't exist in `follow_up_questions[]`. If collision: auto-increment.
2. **Append** to `follow_up_questions[]`.
3. Update `follow_up_summary.total_count`, `by_priority`, `by_stage`.

---

## Step 11 — Merge Data Gaps

For each string in `new_data_gaps[]`:
- If not already in `data_gaps[]` (case-insensitive): append.

---

## Step 12 — Merge Business Metrics

For each entry in `new_business_metrics[]`:
1. **Dedup check** — scan `business_metrics[]` for same `name`. If match: update value if new one has higher confidence or more recent session.
2. **ID validation** — verify `metric_id` doesn't exist. If collision: auto-increment.
3. **Append** to `business_metrics[]`.

---

## Step 13 — Update Staff Roster

For each entry in `staff_updates[]`:

**If `action: "create"`:**
- Scan `staff_roster[]` for same `name` (case-insensitive). If match: treat as update.
- Append to `staff_roster[]`.

**If `action: "update"`:**
- Find by name, merge non-null fields.

---

## Step 14 — Blended Rate (No-Op)

The blended rate is fixed at `$50/hr` by convention and is never updated by extraction. Any `blended_rate_update` field on incoming sub-agent output is ignored. `meta.blended_hourly_rate_aud` must remain `50`.

---

## Step 15 — Update Session Entry (Fathom Only)

If `session_entry` is not null:
- Find existing session by `fathom_meeting_id` in `sessions[]`. If found: update `analyzed: true`, merge `stages_covered`, update `key_findings`.
- If not found: append as new session entry.
- Increment `sessions_completed` top-level counter.

---

## Step 16 — Update Extracted Materials (Non-Fathom Only)

If `extracted_material_entry` is not null:
- Append to `extracted_materials[]`.

---

## Step 17 — Update Context Packet for Next Sub-Agent

After merging, rebuild the context packet from the updated in-memory audit data so the next sub-agent has accurate ID sequences and dedup context:
- Update all `id_sequences` with new last IDs
- Update `existing_tool_names` with newly added tools
- Update `sessions_summary` with the just-merged session
- Update `existing_pain_point_summaries` with brief descriptions of new pain points
- Update `existing_contradiction_topics` with new contradictions

---

## Step 18 — Checkpoint Save

For v4 clients (detected by presence of `audit-manifest.json`): write each domain's data to its own file. Write processes, steps, tools, and extracted_materials into `clients/{slug}/03-audit/data/extraction.json`. Write pain_points, waste_items, optimisations, follow_up_questions, contradictions, and follow_up_summary into `clients/{slug}/03-audit/data/findings.json`. Write session entries and blended rate into `clients/{slug}/03-audit/data/meta.json`. After writing, update `audit-manifest.json`: set `domains.{domain}.updated_at` for each changed domain, and set root `updated_at`. Never write these to top-level keys in v4 files.

For v3 files: write merged data into the correct domain objects — processes, steps, tools, and extracted_materials into `extraction`; pain_points, waste_items, optimisations, follow_up_questions, contradictions, and follow_up_summary into `findings`; session entries and blended rate into `meta`. Never write these to top-level keys in v3 files.

For v2 files: write to top-level keys as before.

Write the updated audit data to disk. Print:
```
  CHECKPOINT — {folder or filename}: {n} steps, {n} PPs, {n} waste, {n} tools
```

Then update the ingestion manifest: set `status: "extracted"`, `extracted_at`, and `extraction_stats` for this source.

---

## On Sub-Agent Failure

If a sub-agent returns an error, malformed JSON, or fails to complete:
1. Log the failure to the ingestion manifest (`status: "failed"`, error message in a `failure_reason` field).
2. Continue to the next transcript. Do not halt.
3. Failed transcripts are retried on the next SU run (manifest shows `status: "failed"` → treated as pending).
4. At the end of the run, report which sources failed and why.
