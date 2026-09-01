---
name: process-review
description: Deep QA of the process map using per-subprocess sub-agents. Validates BPMN notation, swim lanes, sequence flow integrity, gateway completeness, and structural validity for each subprocess independently. Also runs cross-cutting checks for team names, duplicates, time estimates, source evidence, and text quality. Presents all findings for approval before modifying data.
menu-code: PR
---

# Process Review

## Purpose

A thorough quality check on all `processes[]` in extraction.json, validated against BPMN 2.0 notation rules. Run this after extraction sessions are mostly done and before marking `audit_status: process_map_complete`.

**Sub-agent architecture.** Each process is split into subprocess groups (matching how `generate_bpmn.py` renders them), then one sub-agent per subprocess validates its BPMN structure independently. This prevents context degradation when reviewing 10+ processes with complex subprocess structures. The parent runs cross-cutting checks (name normalisation, duplicates, time estimates, source evidence, text quality) that need cross-process visibility.

Output is a numbered list of proposed changes. Nothing is modified until you confirm.

---

## Process

### Step 1: Load and Inventory

Check for `audit-manifest.json` in the client's `03-audit/data/` folder on the mounted Drive. If present (v4), read `meta.json` and `extraction.json` directly. If absent, fall back to reading `audit-data.json` as v3/v2.

Extract into working variables:
- `processes[]` with `steps[]`, `sequence_flows[]`, `parallel_tracks[]`, `lanes[]`
- `staff_roster[]`
- `waste_items[]`

Display the opening inventory:

```
PROCESS REVIEW -- {company_name}
===============================================
Stages:                          {n}
Total steps:                     {total}
  Task steps:                    {n} (user_task: {n}, service_task: {n}, send_task: {n}, receive_task: {n})
  Exclusive gateways:            {n}
  Parallel gateways:             {n}

Sequence flows:                  {n} total across all stages
Steps with lane_id assigned:     {n}/{total}
Steps with a time estimate:      {n}/{total}
Steps with sources[]:            {n}/{total}

Unique lane_id values:           {list of distinct lane_id strings}

Running {n} checks (Steps 2-3 global, Step 4 via sub-agents, Steps 5-7 cross-cutting)...
```

---

### Step 2: Team Member Name Cleanup

Build a name registry from two sources:
1. `staff_roster[].name` — the standard names
2. All `lane_id` and `owner` field values across every step in every stage

Look for name variations:

- **Shortened names** — "Morgan" vs "Morgan Reed" (same person, different levels of detail)
- **Steps shared between two people** — "Morgan / Priya" as a single lane_id vs "Morgan" and "Priya" listed separately. Flag if the same step could be owned by one person only.
- **Names with job descriptions attached** — "Priya (coordination)" vs "Priya"
- **Names not on the team list** — lane_id values that don't match any `staff_roster[].name` or known variation (excluding "Automated" and "External: *" prefixed values)

For each cluster of name variations, propose a standard name (prefer the staff_roster name). List all affected steps:

```
TEAM MEMBER NAME CLEANUP
--------------------------------------------------------------
[NM-1] "Morgan" / "Morgan Reed" -- 2 variations, 18 steps
  Standard name: "Morgan Reed" (from staff roster)
  Variations found:
    "Morgan"          -> 14 steps: ACQ-002, ACQ-005, FUL-001, FUL-003...
    "Morgan Reed"  -> 4 steps: ACQ-008, QUO-001...
  Action: Update all "Morgan" to "Morgan Reed" across 14 steps (both lane_id and owner)
--------------------------------------------------------------
Name variations found: {n} clusters | Steps affected: {n}
```

If all names are already consistent, state "Team member names are consistent. No changes needed."

---

### Step 2b: Non-Step Observation Detection

Scan all `processes[].steps[]` where `annotations` contains `"pain"` or `"optimisation"`. Apply the **Action Test** to each: "Does someone currently perform this as a discrete action in their workflow?"

**Patterns that indicate an observation, not a step:**
- Title starts with "No ", "Lack of", "Missing", "Absence of" — describes a missing capability
- Title contains "misalignment", "inconsistency", "gap", "siloed" — describes a structural condition
- Description says "there is no process for" or "nobody currently" — confirms absence
- Title cannot be rewritten as "[Person] [verb]s [object]" without inventing an action nobody performs

For each flagged item:

```
NON-STEP OBSERVATION DETECTION
--------------------------------------------------------------
[OBS-1] {STEP-ID} "{title}" — OBSERVATION, NOT A STEP
  Stage: {stage} | Annotation: {annotations}
  Description: "{description[:120]}..."
  Source: "{sources[0].quote[:80]}..."
  Reason: {explanation of why this is not a workflow action}
  Recommendation: Reclassify as pain point / optimisation.
    Action: Remove {STEP-ID} from processes[{stage}].steps[].
            Create entry in findings.json:
              pain_point_id / optimisation_id: {next_id}
              stage: {stage}
              title: {step.title}
              description: {step.description}
              sources: {transfer step.sources[]}
              source: "reclassified"
            Update sequence_flows[]: reconnect the surrounding steps
              (connect the previous step's outgoing flow directly to
               the step that followed {STEP-ID}).
--------------------------------------------------------------
```

**Edge case:** If the removed step is the only step in a gateway branch, removing it creates an empty branch. Flag this for manual resolution: propose removing the empty branch from the gateway (or collapsing the gateway if only one branch remains) rather than silently leaving a dead-end flow.

If no observations are detected, state "All pain/optimisation annotated steps pass the action test. No reclassification needed."

---

### Step 3: Duplicate Step Removal

Compare every pair of steps within the same stage for overlap:

1. **Same activity, different wording** — same process described from two sessions with slightly different phrasing.
2. **Same owner, similar description** — steps by the same person in the same stage covering the same task.
3. **Same source quote referenced** — two steps that cite the same word-for-word quote in their `sources[]`.

For each duplicate pair, present a side-by-side comparison and recommendation. Keep the richer item: prefer higher confidence, more complete `sources[]`, more detailed description.

```
DUPLICATE CANDIDATES
--------------------------------------------------------------
[DUP-1] {STEP-ID-A} <-> {STEP-ID-B}  -- LIKELY DUPLICATE
  {STEP-ID-A}: "{title}"
    Lane: {lane_id} | Session: {sources[0].session_id} | Confidence: {confidence}
    Quote: "{sources[0].quote[:80]}..."
  {STEP-ID-B}: "{title}"
    Lane: {lane_id} | Session: {sources[0].session_id} | Confidence: {confidence}
    Quote: "{sources[0].quote[:80]}..."
  Reason: {explanation}
  Recommendation: Keep {STEP-ID-B} (more complete description / higher confidence).
    Action: Remove {STEP-ID-A}. Transfer sources[] entries to {STEP-ID-B}.
            Add merge_note to {STEP-ID-B}.
            Update sequence_flows[]: redirect any flow referencing {STEP-ID-A} to {STEP-ID-B}.
--------------------------------------------------------------
```

If no duplicates are found, state "No duplicate steps detected."

---

### Step 4: BPMN Validation via Sub-Agents

This step dispatches one sub-agent per subprocess group to validate BPMN structural integrity, notation correctness, lane assignments, gateway completeness, and spec compliance. It replaces the old per-process sequential checks (old Steps 4-6 and 8b).

---

#### 4a: Build Shared Context (once)

Read `apg-audit-plugin/skills/5-deliverable-builder/references/bpmn-spec-reference.md` and extract the validation rules table (V01-V19) from Section 2.

Assemble a `shared_context` object:

```json
{
  "company_name": "{company_name}",
  "staff_roster_summary": [
    {"name": "Morgan Reed", "role": "Operations Manager"}
  ],
  "tool_names": ["{list of tools[].tool_name from extraction.json}"],
  "all_lane_ids_across_processes": ["{all unique lane_id values found in any process}"],
  "bpmn_rules_v01_to_v15": "V01: Every sequenceFlow.sourceRef must reference an existing element id in the same process (ERROR)\nV02: Every sequenceFlow.targetRef must reference an existing element id in the same process (ERROR)\nV03: No duplicate id values anywhere in the document (ERROR)\nV05: Every lane.flowNodeRef must reference an existing element id in the same process (ERROR)\nV06: A process with lanes must have exactly one laneSet (ERROR)\nV07: startEvent must have zero incoming sequence flows (ERROR)\nV08: startEvent must have at least one outgoing sequence flow (WARNING)\nV09: endEvent must have zero outgoing sequence flows (ERROR)\nV10: endEvent must have at least one incoming sequence flow (WARNING)\nV13: exclusiveGateway.default (if set) must reference an outgoing sequence flow ID (ERROR)\nV14: parallelGateway used as fork should have a corresponding join downstream (WARNING)\nV15: Gateways must have at least one incoming and one outgoing sequence flow (WARNING)"
}
```

Keep `staff_roster_summary` to name + role only (not full staff_roster objects). Keep `tool_names` to tool names only (not full tool objects).

---

#### 4b: Split Processes into Subprocess Groups

Apply Step 3's in-memory duplicate removals to `processes[]` before splitting (so sub-agents don't validate deleted steps).

For each process in `processes[]`:

**If the process has ≤ 20 steps:** create one group covering all steps. Set `is_full_process: true`.

**If the process has > 20 steps:** split into subprocess groups using this priority order:

1. **`flow_id` on steps** — if any steps have a `flow_id` field set, group steps by their `flow_id`. Steps without `flow_id` form a "General" group.

2. **`parallel_tracks[]` on the stage** — if the process has `parallel_tracks[]` populated and each track has `step_ids[]`, group steps by track. Steps not assigned to any track form a "General" group. Use `track.label` or `track.name` as the subprocess name.

3. **Role-boundary chunking (fallback)** — if neither `flow_id` nor `parallel_tracks[]` is available:
   - Walk steps in array order
   - When the `lane_id` changes AND the new lane persists for 3+ consecutive steps, mark a split point
   - Target group size: 12 steps. Hard limit: 20 steps (split regardless if reached)
   - Merge groups with fewer than 4 steps into their neighbour
   - Name each group after its dominant `lane_id` (most frequent lane in the group), falling back to the first step's title truncated to 40 chars

After grouping, for each group:
- Build `entry_step_ids`: steps in this group that have incoming flows from steps in OTHER groups (or, for the first group, the step with no incoming flows in this process)
- Build `exit_step_ids`: steps in this group that have outgoing flows to steps in OTHER groups (or, for the last group, the step with no outgoing flows)
- Filter `sequence_flows[]`: keep only flows where BOTH `from`/`source_ref` AND `to`/`target_ref` are `step_id`/`bpmn_id` values within this group's steps — these are the intra-group flows the sub-agent validates
- Collect the remaining flows as cross-subprocess flows (validated by parent in Step 4f)

Set `is_full_process: false` for all groups when splitting.

---

#### 4c: Build Per-Subprocess Packets

For each subprocess group, build a slim packet by stripping BPMN-irrelevant fields from steps:

**Keep on each step:** `step_id`, `bpmn_id`, `title` (or `label`), `element_type`, `task_type`, `lane_id`, `owner`, `tool_ids`, `annotations`, `confidence`, `default_flow_id`, `time_estimate_hours_per_week`, `flow_id`

**Strip from each step:** `sources[]`, `meeting_references[]`, `source_evidence`

**Truncate:** `description` → keep first 120 chars as `description_short` (needed for element type inference in Check Group 4d). Drop the full `description`.

**Include on the packet:**
- `lanes_in_scope`: the `lanes[]` entries for this process (full lane objects — include `id`, `name`, `type`, `order`)
- `entry_step_ids` and `exit_step_ids` computed in Step 4b
- `sequence_flows`: intra-group flows only

```json
{
  "process_stage": "finance_brokerage",
  "process_name": "Finance Brokerage",
  "subprocess_name": "Post-Sale Finance Settlement",
  "subprocess_slug": "post-sale-finance-settlement",
  "is_full_process": false,
  "lanes_in_scope": [{"id": "Lane_Finance_Broker", "name": "Finance Broker", "type": "system", "order": 0}],
  "steps": [{"step_id": "FIN-001", "bpmn_id": "Task_FIN_001", "title": "...", "element_type": "task", "task_type": "user_task", "lane_id": "Finance Broker", "owner": "John Boctor", "tool_ids": ["HubSpot"], "annotations": [], "description_short": "first 120 chars of description", "confidence": "HIGH"}],
  "sequence_flows": [{"id": "SF-001", "from": "FIN-001", "to": "FIN-002", "condition": null}],
  "entry_step_ids": ["FIN-001"],
  "exit_step_ids": ["FIN-005"]
}
```

---

#### 4d: Read Sub-Agent Schema (once)

Read `apg-audit-plugin/skills/3-audit-extractor/sub-agent-process-review.md`. Hold its full content as a string.

---

#### 4e: Dispatch All Sub-Agents in Parallel

Dispatch all subprocess packets across all processes simultaneously in a single message — one Agent call per subprocess, all launched at once:

```
Agent({
  description: "PR BPMN validation -- {process_stage}/{subprocess_slug} -- {client_slug}",
  model: "sonnet",
  prompt: [
    "[full content of sub-agent-process-review.md with {shared_context} replaced by the shared_context JSON]",
    "[with {subprocess_packet} replaced by the subprocess_packet JSON]"
  ].join("\n")
})
```

Inject the context by replacing the `{shared_context}` and `{subprocess_packet}` placeholders in the sub-agent schema with their actual JSON values before dispatching.

**All sub-agents run in parallel. Do not batch — dispatch every subprocess packet in one message and wait for all to complete.**

Print a summary once all sub-agents return:

```
  ALL SUB-AGENTS COMPLETE ({n} subprocesses)
    {process_stage}/{subprocess_slug}: {check_status} -- {n} HIGH, {n} MEDIUM, {n} LOW
    {process_stage}/{subprocess_slug}: {check_status} -- {n} HIGH, {n} MEDIUM, {n} LOW
    ...
```

---

#### 4f: Validate Cross-Subprocess Flows (Parent)

For each process, validate the flows that were filtered out as cross-subprocess in Step 4b:

1. **Both endpoints exist** — verify the `from`/`source_ref` step_id exists in one of this process's subprocess groups, and the `to`/`target_ref` exists in another subprocess group in the same process. Flag missing refs as HIGH.
2. **Gateway conditions on cross-subprocess exits** — if a cross-subprocess flow originates from an exclusive gateway, verify it has a `condition` label. Flag missing conditions as MEDIUM.
3. **No duplicate cross-subprocess flows** — same `from` + `to` + `condition` combination appearing twice. Flag as MEDIUM.

---

#### 4g: Collect and Merge Sub-Agent Results

After all batches complete, for each sub-agent result:

1. **Parse the JSON.** If unparseable or `check_status: "failed"`:
   - Log: "Process {process_stage}/{subprocess_slug}: sub-agent failed — {parse_error}. BPMN checks skipped for this subprocess."
   - Add to the failed list
   - Continue with remaining results

2. **Assign global finding IDs.** Replace each sub-agent's `F-001`, `F-002`, etc. with globally unique IDs across all processes: `SA-001`, `SA-002`, etc. (SA prefix = sub-agent, to distinguish from parent-level findings).

3. **Collect `parallel_tracks_proposed`** entries from each sub-agent result. These become `[PARALLEL TRACKS]` changes in the summary.

4. **Collect `convergence_points`** entries. These become `[ADD GATEWAY]` changes in the summary.

Display a consolidated summary:

```
BPMN VALIDATION -- SUB-AGENT RESULTS
================================================================
{PROCESS_NAME} ({n} subprocesses)
  {subprocess_name}: {n} HIGH, {n} MEDIUM, {n} LOW
  {subprocess_name}: clean
  Cross-subprocess flows: {n} issues / valid
  
{PROCESS_NAME} ({n} subprocesses, or "full process, ≤20 steps")
  ...

Batches: {n}/{n} complete, {n} sub-agents failed
================================================================
Total: {n} subprocesses validated | {n} findings ({n} HIGH, {n} MEDIUM, {n} LOW)
Failed: {list of process_stage/subprocess_slug that need retry}
```

If any sub-agents failed, state: "Re-run PR with scope B (specific process) to retry failed subprocesses."

---

### Step 5: Checking Time Estimates Make Sense

Sum `time_estimate_hours_per_week` per lane_id per stage. Flag anything that doesn't add up:

1. **More hours than one person can work in a week** — if a single person's steps sum to more than 40 hours per week in one stage, flag it.
2. **Compare with waste items** — for steps that have a matching waste_item (same stage, similar activity), check whether the step's time estimate lines up with the waste item's `hours_per_week` (within 15%).

```
CHECKING TIME ESTIMATES MAKE SENSE
--------------------------------------------------------------
Lane summary (across all stages):
  Morgan Reed:     {total} hrs/wk  -> OK / OVER CAPACITY
  Priya:            {total} hrs/wk  -> OK / OVER CAPACITY

Waste item comparisons:
  ACQ-004 (time_estimate: 1.0 hrs/wk) vs W-004 (hours_per_week: 3.0)
    MISMATCH -- step implies 1.0 hrs/wk, waste item says 3.0 hrs/wk.
--------------------------------------------------------------
Over capacity flags: {n} | Waste mismatches: {n}
```

If no time estimates exist, state "No time estimates populated, skip this check."

---

### Step 6: Checking Every Step Has a Source

Load `references/source-verification.md` and follow the procedures in that file for all sub-checks below.

#### Step 6a: Rating the Evidence for Each Step

For each step, rate the evidence quality based on `sources[]`:

- **CONFIRMED** — `sources[]` has at least one entry with a `quote` that directly supports the step's described activity.
- **VAGUE QUOTE** — `sources[]` exists but the quote is too general or only loosely related.
- **NO SOURCE** — `sources[]` is empty or missing.

```
RATING THE EVIDENCE FOR EACH STEP
--------------------------------------------------------------
By stage:
  Acquisition:    CONFIRMED: 6  VAGUE QUOTE: 1  NO SOURCE: 1
  Quoting:        CONFIRMED: 8  VAGUE QUOTE: 2  NO SOURCE: 2
  ...
--------------------------------------------------------------
CONFIRMED: {n}  |  VAGUE QUOTE: {n}  |  NO SOURCE: {n}
```

#### Step 6b: Checking the Numbers Come From Real Quotes

For every step with `time_estimate_hours_per_week` or headcount populated, verify the number appears in a `sources[].quote` entry using the procedure in `source-verification.md` Section 6.

#### Step 6c: Confirming Quotes Exist in Transcripts

For all steps rated CONFIRMED or VAGUE QUOTE, read the actual transcript file and verify the quote is really there. Read each transcript file once per session and reuse it.

#### Step 6d: Checking Source Completeness

For every step where `sources[]` is not empty, verify each source entry has all required fields (`session_id`, `timestamp_seconds`, `speaker`, `quote` for fathom; `document_path`, `quote` for document). Propose corrections where incomplete.

---

### Step 7: Text Quality

Client-facing text in process steps flows directly into HTML deliverables. Load `${CLAUDE_PLUGIN_ROOT}/context/brand/brand-voice.md`, specifically the "Master Forbidden Words List", "Forbidden Phrases" table, and "Structural Anti-Patterns" sections.

Scan `processes[].name`, `processes[].steps[].label` (or `title`), `processes[].steps[].description` for:

1. **Em dashes** — never used in APG output. Replace with a comma, colon, or rewrite.
2. **Forbidden words** — leverage, utilize, facilitate, comprehensive, seamless, innovative, groundbreaking, furthermore, additionally, moreover, ecosystem, synergy, necessitate, elevate, streamline, "it is important to", "not just X but Y".
3. **Overly formal language** — "necessitates manual intervention" → "requires manual work".
4. **Repetitive patterns** — 3+ consecutive steps with identical sentence structures. Flag and propose variation.

Each issue becomes a `[WORDING FIX]` change in the summary.

---

### Step 8: Summary and Approval

Present all findings in a single view. Sub-agent findings (SA-xxx) and parent-level findings appear in one numbered list, grouped by category, ordered by severity.

```
PROCESS REVIEW COMPLETE -- {company_name}
=================================================================

FINDINGS
  Name variations cleaned up:        {n} clusters ({n} steps affected)
  Duplicate steps:                    {n} pairs proposed for removal
  Observation steps to reclassify:   {n} steps flagged as non-actions (OBS-N)
  Sub-agent BPMN findings:
    HIGH severity:                    {n} (broken flows, orphaned steps, missing lanes, start/end events)
    MEDIUM severity:                  {n} (gateway issues, label format, lane assignments)
    LOW severity:                     {n} (label rephrasing, element type refinements)
  Cross-subprocess flow issues:       {n}
  Parallel tracks detected:          {n} stages with multiple tracks
  Convergence points:                 {n}
  Time estimate flags:               {n}
  Waste item mismatches:             {n}
  Vague or missing sources:          {n}
  Numbers without source evidence:   {n}
  Quotes missing from transcripts:   {n}
  Text quality issues:               {n}
  Failed sub-agents:                 {n} (subprocesses not validated)

PROPOSED CHANGES ({n} total):
  1. [NAME FIX] Update "Morgan" to "Morgan Reed" across 14 steps (NM-1)
  2. [REMOVE DUPLICATE] Remove FUL-008b, duplicate of FUL-008. Transfer sources. (DUP-1)
  3. [RECLASSIFY] Remove ACQ-007 "No social media presence" — observation, not a workflow action. Create PP-{next} in findings.json (stage: acquisition). Reconnect sequence flows around removed step. (OBS-1)
  4. [FIX FLOW] FIN-003: no incoming flow, not in entry steps. Add flow from FIN-002. (SA-001, HIGH)
  4. [FIX LANE] FIN-005: lane_id "John Boctor" is a person name. Assign to role lane. (SA-002, MEDIUM)
  5. [FIX GATEWAY] ACQ-D01: gateway has only 1 outgoing flow. Add missing branch. (SA-003, HIGH)
  6. [PARALLEL TRACKS] finance_brokerage: 2 parallel tracks proposed (Post-Sale and New Application) (SA-004)
  7. [ADD GATEWAY] Add parallel_gateway join before FIN-020 (convergence point) (SA-005)
  8. [FIX LABEL] FUL-022: rename to verb-noun format "Reconcile weekly timesheet" (SA-006, LOW)
  9. [MISSING SOURCE] FUL-022: time_estimate 20.0 hrs/wk, no source quote for this figure
  10. [WORDING FIX] FUL-011: remove em dash in description
  ...

Apply changes? Enter a number range (e.g. 1-4), specific numbers (e.g. 1,3,5), ALL, or NONE.
Note: changes marked with {confirmation required} will be skipped in ALL unless individually numbered.
```

---

### Step 9: Apply Changes

Wait for user input. Do not proceed until confirmed.

**ALL** — apply every change not marked `requires_confirmation`.
**NONE** — discard all, exit without modifying data.
**Specific** — user enters numbers or ranges; apply only those.

Execute in this order:

1. **Name fixes** — update `lane_id` and `owner` fields on each affected step.
2. **Duplicate removal** — remove the duplicate step; transfer `sources[]` entries to the kept step; add `merge_note`; redirect `sequence_flows[]` references.
2b. **Observation reclassification** — for each approved `[RECLASSIFY]` change: (a) remove the step from `processes[].steps[]`; (b) create a new `pain_point` or `optimisation` entry in `findings.json` (v4) with the step's `title`, `description`, `stage`, and transferred `sources[]`, plus `source: "reclassified"`; (c) reconnect `sequence_flows[]` around the gap (connect the preceding step's outgoing flow to the following step); (d) if the removed step was the sole step in a gateway branch, collapse or remove the empty branch. For v4 clients: write both `extraction.json` and `findings.json`, then update both domains in `audit-manifest.json`.
3. **Parallel track assignment** — set `parallel_tracks[]` on the stage with track labels, cadences, and step_ids.
4. **Gateway additions** — add new parallel_gateway or exclusive_gateway steps where convergence or missing branches were identified.
5. **Sequence flow fixes** — add new flows, remove broken ones, add condition labels to gateway outgoing flows.
6. **Label fixes** — update step labels to verb-noun format.
7. **Lane fixes** — move tool names from lane_id to tool_ids, set lane_id to the correct role.
8. **Type fixes** — update task_type where description implies a different BPMN type.
9. **BPMN structural fixes** — synthesise missing start/end events, sanitise `bpmn_id` values, default missing `task_type` to `user_task`, repair orphan flow refs. Lane splits and structural reshapes only execute when explicitly approved by number — never as part of ALL.
10. **Source fixes** — populate missing session_id, timestamp_seconds, speaker on source entries.
11. **Wording fixes** — apply approved text replacements.

After all changes are applied, write back to the audit data. For v4: write the full updated `extraction.json`, then update `audit-manifest.json` (`domains.extraction.updated_at` and root `updated_at`). For v3/v2: write to the appropriate nested or top-level keys.

Report:

```
Process review applied.
  Names updated:              {n} steps
  Duplicates removed:         {n} steps removed
  Observations reclassified:  {n} steps moved to findings.json as pain_points/optimisations
  Tracks assigned:            {n} stages with parallel_tracks[]
  Gateways added:             {n}
  Sequence flows fixed:       {n} (added: {n}, removed: {n}, updated: {n})
  Labels updated:             {n}
  Lanes corrected:            {n}
  Task types corrected:       {n}
  Sources fixed:              {n}
  Wording fixes applied:      {n}

Run the validator to confirm data integrity:
  python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py \
    clients/{client_slug}/03-audit/data/extraction.json
```
