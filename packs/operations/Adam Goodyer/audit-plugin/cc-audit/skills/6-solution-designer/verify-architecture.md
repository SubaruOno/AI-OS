---
name: verify-architecture
description: Verify architecture coverage against pain points, optimisations, and interactivity requirements. Generate coverage report and prototype brief.
menu-code: VA
---

# Verify Architecture (VA)

> **Idempotent.** First run performs full verification. Re-runs regenerate from current architecture and compare against previous results.

> **INTERNAL DOCUMENTATION ONLY.** Verification results are never shown to clients. They are for validating the architecture before prototype generation.

## Purpose

Cross-reference `architecture_doc` against every pain point and optimisation from the audit to ensure nothing fell through. Audit interactivity to catch screens that render but can't be acted on. Check for unnecessary complexity. Produce a structured `prototype_brief` that tells [BP] exactly how each screen should demonstrate pain point resolution.

---

## Stage 0: Pre-flight

1. Load audit data:
   - Check for `clients/{slug}/03-audit/data/audit-manifest.json`. If present (v4): read domain files directly:
     - `clients/{slug}/03-audit/data/meta.json`
     - `clients/{slug}/03-audit/data/opportunities.json`
     - `clients/{slug}/03-audit/data/architecture.json`
     - Do NOT load `extraction.json`, `findings.json`, or `strategy.json`
   - For v3 files (no manifest, `_schema_version` starts with "3"): load `meta`, `opportunities`, and `architecture` domains from `audit-data.json`.
   - For v2 files: load the full `audit-data.json`.

   Check `architecture_doc` exists (`architecture.architecture_doc` in v3/v4, top-level in v2).
   - If missing: warn and suggest running [BA] first.

2. Check `requirements_spec` exists (`architecture.requirements_spec` in v3/v4, top-level in v2).
   - If missing: warn and suggest running [RE] first.

3. Check `pain_points[]` and `optimisations[]` exist and are non-empty.

4. Check `proposed_changes[]` exist with `linked_pain_point_ids` and `linked_optimisation_ids` populated.

5. If `architecture_verification` already exists in audit-data.json, ask:
   ```
   Previous verification found ({date}).
   Options:
     A) Full re-verification — re-check everything against current architecture
     B) Delta verification — only re-check items flagged as gaps last time
     C) Cancel
   ```

6. Show readiness summary:
   ```
   ARCHITECTURE VERIFICATION — {company_name}
   Pain points:       {n} total across {n} stages
   Optimisations:     {n} total across {n} stages
   Proposed changes:  {n} with {n} linked pain points, {n} linked optimisations
   Requirements:      {n} requirements with {n} user stories
   User journeys:     {n} journeys with {n} total steps
   Pages:             {n} in page structure

   Previous verification: {present|absent}
   ```

---

## Stage 1: Pain Point Coverage Matrix

For every `pain_points[]` item, trace the full chain to a concrete prototype action.

### 1a. Trace algorithm

For each `pain_points[i]`:

1. **Find linked proposed changes.** Scan `proposed_changes[]` where `linked_pain_point_ids` includes this `pain_point_id`. Collect matching `change_id` values.

2. **Find linked requirements.** For each `change_id` found, scan `requirements_spec.requirements[]` where `change_id` matches. Collect `requirement_id` values and their `user_stories[]`.

3. **Find linked user journey steps.** For each `change_id`, scan `architecture_doc.user_journeys[]` where `change_ids[]` includes this `change_id`. For each matching journey, collect all `steps[]` with their `screen`, `action`, `data_shown`, `data_input`.

4. **Find linked screens.** For each screen ID referenced in journey steps, look up the page in `architecture_doc.page_structure.pages[]` to get the `route`, `components[]`, and `roles[]`.

### 1b. Coverage classification

Classify each pain point:

| Status | Criteria |
|--------|----------|
| `fully_covered` | Traces to at least one journey step with interactive action (`data_input[]` non-empty OR action verb is interactive) |
| `view_only` | Traces to journey steps but ALL steps have empty `data_input[]` and passive action verbs only |
| `partial` | Traces to proposed changes and/or requirements but has no corresponding journey steps |
| `missing` | No proposed changes link to this pain point at all |
| `deferred` | All linked proposed changes have `phase` > current prototype scope |

**Interactive action verbs:** create, assign, edit, drag, move, approve, send, upload, submit, configure, delete, remove, update, add, schedule, publish, confirm, reject, reassign, override.

**Passive action verbs:** view, see, check, review, browse, monitor, receive.

**The definitive signal is `data_input[]`.** If it's non-empty, the step is interactive regardless of verb. Verb analysis is a secondary check when `data_input[]` is empty.

### 1c. Build trace record

For each pain point, produce:

```json
{
  "pain_point_id": "PP-008",
  "description": "Jordan spends 3-5 hours per day building schedule",
  "stage": "fulfilment",
  "coverage_status": "fully_covered",
  "trace": {
    "proposed_change_ids": ["CH-006"],
    "requirement_ids": ["REQ-005"],
    "user_story_ids": ["US-010", "US-011"],
    "journey_refs": [
      {
        "journey_name": "Daily scheduling workflow",
        "role": "operations_manager",
        "step_index": 1,
        "screen": "SCR-SCHED-001",
        "action": "Review auto-generated roster with conflict flags",
        "has_interaction": true,
        "interaction_type": ["drag_reassign", "shift_assignments"]
      }
    ],
    "prototype_screens": [
      {
        "screen_id": "SCR-SCHED-001",
        "route": "/scheduling/roster",
        "resolution_description": "Drag-and-drop roster replaces manual 3-5hr daily spreadsheet rebuild. Auto-generates schedule from recurring shifts and availability, Jordan reviews and adjusts exceptions."
      }
    ]
  },
  "resolution_summary": "Scheduling Engine auto-generates roster from rules. Jordan reviews on /scheduling/roster with drag-drop reassignment. Reduces 3-5hr daily rebuild to 30-min review."
}
```

### 1d. Flag gaps

After processing all pain points, list:
- All `view_only` items — architecture shows data but user can't act on it
- All `partial` items — change exists but no journey step represents it
- All `missing` items — no proposed change addresses this pain point
- All `deferred` items — note that these are intentionally out of scope

For each gap, generate a specific recommendation for what to add to `architecture_doc`.

---

## Stage 2: Optimisation Coverage

Same trace algorithm as Stage 1, but using `optimisations[]` and `linked_optimisation_ids`.

### 2a. Trace algorithm

Identical to Stage 1a, substituting `optimisation_id` and `linked_optimisation_ids`.

### 2b. Additional classification

Beyond the base coverage statuses, optimisations get additional flags:

| Status | Criteria |
|--------|----------|
| `addressed_this_phase` | Optimisation is covered by a change in Phase 1 / current scope |
| `addressed_later_phase` | Optimisation is linked to a change in Phase 2+ |
| `addressable_but_missing` | Not linked to any proposed change, but architecture has the entities/modules to support it |
| `not_addressable` | Would require new modules/entities not in current architecture |

### 2c. Addressability check

For `missing` optimisations, determine if the current architecture could address them:

1. Match the optimisation's `stage` field to modules in `architecture_doc.module_inventory[]` (acquisition → CRM Module, fulfilment → Scheduling Engine, etc.)
2. Check if relevant entities exist in `architecture_doc.data_models[]` (keyword matching: "lead"/"pipeline" → Lead entity, "scheduling"/"roster" → Shift entity, "invoice"/"payment" → Invoice entity, etc.)
3. If both a matching module and relevant entities exist → `addressable_but_missing`
4. Otherwise → `not_addressable`

### 2d. Generate recommendations

For `addressable_but_missing` items:

```json
{
  "optimisation_id": "OPT-010",
  "flag": "addressable_but_missing",
  "recommendation": "Auto-generated progress reports from shift notes. The architecture already has CaseNote entity and AI Report Engine module. Consider adding a journey step for auto-generating participant progress reports.",
  "suggested_module": "AI Report Engine",
  "suggested_change_id": "CH-016",
  "effort_estimate": "low"
}
```

---

## Stage 3: Interactivity Audit

For each user journey step, verify it supports the level of interaction the pain points and acceptance criteria require.

### 3a. Classify step interaction level

For each `architecture_doc.user_journeys[i].steps[j]`:

| Level | Criteria |
|-------|----------|
| `interactive` | `data_input[]` is non-empty (user enters/modifies data) |
| `navigational` | `data_input[]` is empty but `next` points to another screen |
| `view_only` | `data_input[]` is empty AND action uses passive verb |

### 3b. Cross-reference with acceptance criteria

For each journey step:
1. Find the parent requirement via `change_ids[]` on the journey → `requirements_spec.requirements[]` where `change_id` matches
2. Read `acceptance_criteria[]` on linked user stories
3. If any criterion's `when` clause implies user action ("user updates", "user creates", "user assigns", "user drags") but the journey step is `view_only` or `navigational` → flag

### 3c. Cross-reference with pain point descriptions

If a journey step's linked pain point description contains manual-work keywords ("manually", "rebuild", "re-enter", "copy-paste", "type in", "hours per day", "hours per week", "from scratch") but the step is `view_only` → flag as high severity.

### 3d. Component-specific checks

| Screen pattern | Required interaction | Flag if missing |
|----------------|---------------------|-----------------|
| Screens with `Table` component | Row click actions AND at least one bulk/row-level action (`Dropdown` or `Button`) | "Table without action capabilities" |
| Screens with `DatePicker` / calendar | `data_input[]` for date selection or shift assignment | "Calendar renders but cannot be edited" |
| Dashboard screens | Action cards/buttons to navigate to key workflows | "Dashboard is passive — no action shortcuts" |
| Form screens | `data_input[]` fields present | "Form screen with no input fields" |
| Detail screens | Edit capability for at least some fields | "Detail view is read-only — cannot edit record" |

### 3e. Build interactivity issue list

```json
{
  "issue_id": "INT-001",
  "journey_name": "Daily scheduling workflow",
  "role": "operations_manager",
  "step_index": 0,
  "screen": "SCR-SCHED-003",
  "action": "Check staff availability for next week",
  "current_level": "view_only",
  "expected_level": "interactive",
  "reason": "Acceptance criteria US-011 states 'when Jordan flags a worker as unavailable' but this step has no data_input for availability override",
  "recommendation": "Add data_input: ['availability_override', 'override_reason'] to enable manual availability flagging from this screen",
  "severity": "high",
  "linked_pain_point_ids": ["PP-008"],
  "linked_acceptance_criteria": ["US-011 AC-001"]
}
```

**Severity classification:**

| Severity | Criteria |
|----------|----------|
| `high` | User cannot complete a core workflow action that directly resolves a pain point |
| `medium` | User can complete the workflow but needs to navigate away (extra clicks, lost context) |
| `low` | Nice-to-have interaction that would improve UX but isn't blocking |

---

## Stage 4: Simplicity Check

Review the architecture for unnecessary complexity.

### 4a. Journey length

For each journey, count distinct screens. If >5 screens to complete one task, flag as potentially over-engineered. Compare against the number of logical steps in the original process (from `processes[].steps[]` via `affected_step_ids`).

### 4b. Redundant data entry

Scan all journey steps across all journeys. If the same `data_input` field appears in multiple journey steps targeting different screens, flag as potential redundant entry point. Suggest pre-filling from context.

### 4c. Screen consolidation opportunities

For each module, check for:
- Two list pages for the same entity type → suggest merging with tabs or filters
- A create page AND a detail/edit page with identical fields → suggest modal instead of separate page
- A detail page that only shows 3-4 fields → suggest inline expansion on list view

### 4d. Navigation depth

Check `page_structure.pages[].route` hierarchy. If any screen is nested >3 levels deep, flag.

### 4e. Role journey overlap

If two roles have nearly identical journeys (>80% shared screens and same actions), suggest consolidating into one journey with role-conditional visibility.

### 4f. Build recommendations

```json
{
  "rec_id": "SIMP-001",
  "type": "screen_consolidation",
  "description": "SCR-SCHED-002 (Shift Detail) and SCR-SCHED-004 (Shift Edit) share identical fields. Combine into one screen with view/edit mode toggle.",
  "affected_screens": ["SCR-SCHED-002", "SCR-SCHED-004"],
  "affected_journeys": ["Daily scheduling workflow"],
  "impact": "Reduces page count by 1, simplifies navigation",
  "severity": "low"
}
```

**Recommendation types:** `screen_consolidation`, `redundant_entry`, `depth_reduction`, `journey_overlap`, `over_engineered`.

---

## Stage 5: Prototype Brief

For every pain point that is `fully_covered` or `view_only` (after fixes), produce a structured resolution card. This becomes the explicit brief for [BP] — every screen the prototype builds must demonstrate a specific pain point resolution.

### 5a. Build resolution cards

```json
{
  "pain_point_id": "PP-008",
  "headline": "Scheduling: 3-5hr daily rebuild -> 30-min review",
  "screen_route": "/scheduling/roster",
  "screen_name": "Weekly Roster",
  "primary_action": "Drag-and-drop shift reassignment with conflict detection",
  "data_the_user_sees": ["weekly_roster", "conflict_indicators", "participant_preferences", "staff_availability_matrix"],
  "data_the_user_enters": ["shift_assignments", "drag_reassign", "time", "location", "notes"],
  "interaction_model": "Calendar grid with draggable shift cards. Click shift to expand detail. Drag to reassign worker. Red flags on conflicts.",
  "demo_scenario": "Jordan opens roster Monday morning. Auto-generated schedule shows 12 shifts. 1 conflict flagged (worker double-booked). Jordan drags shift to available worker. Confirms. Notifications sent.",
  "linked_optimisation_ids": ["OPT-005"],
  "original_quote": "it takes me between three and five hours a day to get it done"
}
```

### 5b. Group by screen

Multiple pain points may resolve on the same screen. Group `prototype_brief[]` entries by `screen_route` so [BP] can see everything a single screen needs to demonstrate.

### 5c. Include optimisation-only cards

For optimisations classified as `addressed_this_phase` that don't directly resolve a pain point, create separate brief cards with `pain_point_id: null` and an `optimisation_id` field instead.

---

## Stage 6: Write to Audit Data

Write `architecture_verification` to the audit data:
- v4: load `clients/{slug}/03-audit/data/architecture.json`, merge `architecture_verification` into the existing dict, write the full dict back to `clients/{slug}/03-audit/data/architecture.json`, then update `audit-manifest.json`: set `domains.architecture.updated_at` and root `updated_at`.
- v3: write into `architecture.architecture_verification` in `audit-data.json`
- v2: write to top-level `architecture_verification` in `audit-data.json`

```json
{
  "architecture_verification": {
    "generated_at": "ISO timestamp",
    "run_count": 1,
    "architecture_doc_timestamp": "architecture_doc.generated_at value at verification time",

    "pain_point_coverage": [
      {
        "pain_point_id": "PP-001",
        "description": "copied from pain_points[] for readability",
        "stage": "acquisition",
        "coverage_status": "fully_covered|view_only|partial|missing|deferred",
        "trace": {
          "proposed_change_ids": [],
          "requirement_ids": [],
          "user_story_ids": [],
          "journey_refs": [],
          "prototype_screens": []
        },
        "resolution_summary": "human-readable explanation"
      }
    ],

    "optimisation_coverage": [
      {
        "optimisation_id": "OPT-001",
        "description": "copied from optimisations[]",
        "stage": "acquisition",
        "coverage_status": "addressed_this_phase|addressed_later_phase|addressable_but_missing|not_addressable|fully_covered|view_only|partial|missing",
        "phase": 1,
        "trace": {
          "proposed_change_ids": [],
          "requirement_ids": [],
          "journey_refs": []
        },
        "resolution_summary": "",
        "recommendation": "null or recommendation text",
        "suggested_module": "null or module name",
        "suggested_change_id": "null or change ID",
        "effort_estimate": "null or low|medium|high"
      }
    ],

    "interactivity_issues": [
      {
        "issue_id": "INT-001",
        "journey_name": "",
        "role": "",
        "step_index": 0,
        "screen": "SCR-xxx",
        "action": "",
        "current_level": "interactive|navigational|view_only",
        "expected_level": "interactive",
        "reason": "why interaction is expected",
        "recommendation": "specific fix to architecture_doc",
        "severity": "high|medium|low",
        "linked_pain_point_ids": [],
        "linked_acceptance_criteria": []
      }
    ],

    "simplicity_recommendations": [
      {
        "rec_id": "SIMP-001",
        "type": "screen_consolidation|redundant_entry|depth_reduction|journey_overlap|over_engineered",
        "description": "",
        "affected_screens": [],
        "affected_journeys": [],
        "impact": "",
        "severity": "high|medium|low"
      }
    ],

    "prototype_brief": [
      {
        "pain_point_id": "PP-001 or null for optimisation-only",
        "optimisation_id": "null or OPT-xxx",
        "headline": "short tagline for resolution",
        "screen_route": "/crm/leads",
        "screen_name": "Lead Pipeline",
        "primary_action": "key thing the user does",
        "data_the_user_sees": [],
        "data_the_user_enters": [],
        "interaction_model": "how the user interacts",
        "demo_scenario": "step-by-step scenario for prototype demo",
        "linked_optimisation_ids": [],
        "original_quote": "client's own words about the pain"
      }
    ],

    "summary": {
      "total_pain_points": 0,
      "pain_points_fully_covered": 0,
      "pain_points_view_only": 0,
      "pain_points_partial": 0,
      "pain_points_missing": 0,
      "pain_points_deferred": 0,
      "total_optimisations": 0,
      "optimisations_this_phase": 0,
      "optimisations_later_phase": 0,
      "optimisations_addressable_now": 0,
      "optimisations_not_addressable": 0,
      "total_interactivity_issues": 0,
      "interactivity_high": 0,
      "interactivity_medium": 0,
      "interactivity_low": 0,
      "total_simplicity_recommendations": 0,
      "prototype_brief_items": 0,
      "verification_pass": false,
      "blocking_issues": []
    }
  }
}
```

**Verification pass criteria:** `verification_pass = true` when:
- Zero `missing` pain points (all have at least a proposed change)
- Zero `high` severity interactivity issues
- Zero `view_only` pain points that were not intentionally deferred

Update `architect_metadata`:
```json
{
  "last_va_run": "ISO timestamp",
  "total_va_runs": 1,
  "last_va_pass": true,
  "va_blocking_issues": 0
}
```

---

## Stage 7: Display Summary

```
ARCHITECTURE VERIFIED — {company_name}

PAIN POINT COVERAGE:
  Fully covered:    {n}/{total} ({pct}%)
  View-only gaps:   {n} (architecture shows data but user can't act)
  Partial:          {n} (change exists but no journey step)
  Missing:          {n} (no proposed change addresses this)
  Deferred:         {n} (Phase 2+)

OPTIMISATION COVERAGE:
  This phase:       {n}/{total}
  Later phase:      {n}
  Addressable now:  {n} (could be added with minimal effort)
  Not addressable:  {n} (needs new modules)

INTERACTIVITY ISSUES:
  High severity:    {n}
  Medium severity:  {n}
  Low severity:     {n}

SIMPLICITY:
  Recommendations:  {n} ({n} screen consolidation, {n} redundant entry, {n} depth reduction)

PROTOTYPE BRIEF:
  Pain point resolutions mapped: {n}
  Screens with demo scenarios:   {n}

{If gaps found:}
  ACTION REQUIRED: Fix {n} gaps in architecture_doc before running [BP].
  Re-run [VA] after fixes to verify resolution.

{If no gaps:}
  READY FOR PROTOTYPE: All pain points resolve to concrete prototype actions.
  Run [BP] to generate clickable prototype from this verified architecture.
```
