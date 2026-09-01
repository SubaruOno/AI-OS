---
name: run-pipeline
description: RA capability — orchestrate the entire Process Analyst pipeline end-to-end (TR → EI → RI → BR → BO → TS → VR). Auto-selects scope, checkpoints between steps, halts on hard failure, and produces one consolidated report. Each step's own sub-agent batching does the parallel work.
menu-code: RA
---

# Run Analyst Pipeline (RA)

> **Orchestration capability.** This is the single command that runs the whole Process Analyst agent so a human does not have to fire each capability by hand. It chains the underlying capabilities in dependency order, auto-selects the "all unprocessed" scope at each step, checkpoints after every step, and halts the moment a step fails.
>
> **Where the parallelism is.** The capabilities themselves are a strict sequential chain — each one reads the JSON files the previous one wrote (`opportunities.json`, `extraction.json`, `strategy.json`), so they cannot overlap. The real parallel speed-up already lives *inside* each capability: RI/BR/TS each dispatch one sub-agent per change in batches, and VR dispatches four review-lens sub-agents at once. RA does not add parallelism across steps; it removes the manual hand-offs between them and lets each step's batching run.

## When to use

Run RA when a client's audit is data-complete (all extraction sessions done) and you want the full analyst pass — research, value, blueprint, technical specs, verification — without standing over each step. For surgical re-runs of a single capability, use that capability's own menu code instead.

---

## The pipeline (execution order)

```
TR  Research Tool Stack      writes extraction.tools[] integration fields
 │
EI  Extract Improvements     writes opportunities.proposed_changes[] + roi_items[]
 │
RI  Research Improvements     writes research{}, plugin_candidate, plugin_bundles[], extraction.plugin_scope
 │
BR  Build & Rate              writes implementation{}, value{}, modal_content{}, payback_months
 │
BO  Build Outlook             writes strategy.transformation_blueprint (phases, outlook, risks)
 │
TS  Build Technical Specs     writes opportunities.proposed_changes[].technical_spec
 │
VR  Verify Research           audits + corrects everything across all domain files
```

**Why BR runs before BO (this differs from the menu's listed order, on purpose).** BO groups changes into Quick Wins / Core Builds / Future Sprints using each change's top-level `payback_months`, and it sizes the Gantt bars from `implementation.weeks_estimate`. Both of those fields are written by **BR**. If BO runs first, `payback_months` is unset, so every change collapses into the "Future Sprints" tier and the durations are heuristics. BR does not read `strategy.json`, so moving it ahead of BO is safe and strictly better. RA always runs BR → BO.

**BO's save triggers HTML regen.** Writing `strategy.json` fires the `auto-regen-deliverables.sh` hook, which regenerates `blueprint.html`. RA does not call the Generator (Skill 5) itself — deliverable regen is left to the hook.

**Dependency facts used by the gates below:**
- EI needs extraction complete (`proposed_changes[]` must end up populated).
- RI needs `proposed_changes[]` populated. Benefits from TR (uses `tools[].api_available` to find untapped integrations).
- BR needs `research.status` of `complete`/`needs_review` on changes.
- BO needs `payback_months` + `weeks_estimate` (from BR) for a correct blueprint; refuses to run unless `audit_status == "process_map_complete"`.
- TS needs `implementation` + `value` (from BR).
- VR reads opportunities **and** strategy, so it must be last.

---

## Stage 0: Pre-flight and execution plan

### 0a. Parse arguments

Optional args passed after the menu code:
- `--from <CODE>` — start at this step (e.g. `--from RI`), skip everything before it. Use when earlier steps are known-good.
- `--force` — re-run every step from the start regardless of current state (full refresh).
- `--no-gate` — skip the single confirmation gate and execute immediately (unattended mode).

Default (no args): start at the first step that is not already complete, run through VR.

### 0b. Load state

Load the v4 domain files for `{client_slug}`:
- `03-audit/data/audit-manifest.json`, `meta.json`, `extraction.json`, `findings.json`, `opportunities.json`, `strategy.json`

Determine the completion state of each step from the data (not from CRM):

| Step | "Complete" detector |
|---|---|
| TR | every software tool in `extraction.tools[]` has `integration_openness` set (non-null, not `"unknown"`) |
| EI | `opportunities.proposed_changes[]` is non-empty |
| RI | every change has `research.status == "complete"` and `plugin_candidate`/`initiative_type` set; `plugin_bundles[]` present |
| BR | every research-complete change has `implementation`, `value`, and `modal_content` |
| BO | `strategy.transformation_blueprint.phases[]` is non-empty and `last_built` is newer than the last BR write |
| TS | every plugin-bundled `skills[].change_id` resolves to a change with a non-failed `technical_spec` |
| VR | `strategy.strategic_approaches.verification` exists with a recent `verified_at` |

### 0c. Gate check — audit_status

If `meta.audit_status != "process_map_complete"`:
- This is the same gate BO enforces. Surface it loudly:
  ```
  ⚠ audit_status is "{value}", not "process_map_complete".
    BO will refuse to run under its own pre-flight unless this is set.
    Either the extraction is not finished, or it was set manually earlier (as EI was for this client).
  ```
- Do NOT silently flip the flag. Ask the user explicitly whether to set `audit_status = "process_map_complete"` for this run. If they decline, RA can still run TR→EI→RI→BR→TS but must **skip BO and VR** and say so in the plan.

### 0d. Build and show the plan

Render the execution plan and the per-step state:

```
RUN ANALYST PIPELINE — {company_name}
Path: {client_dir}/

Current state:
  TR  Research Tool Stack    [ done | needs run | n/a ]
  EI  Extract Improvements   [ done | needs run ]   ({n} changes)
  RI  Research Improvements  [ done | needs run ]   ({n}/{n} researched)
  BR  Build & Rate           [ done | needs run ]   ({n}/{n} rated)
  BO  Build Outlook          [ done | needs run | BLOCKED: audit_status ]
  TS  Build Technical Specs  [ done | needs run ]   ({n}/{n} specced)
  VR  Verify Research        [ done | needs run | BLOCKED: audit_status ]

Plan for this run ({mode}):
  → will run:   {ordered list of steps RA will execute}
  → will skip:  {steps already complete, or blocked}

Sub-agent load (rough): RI ~{n} agents, BR ~{n}, TS ~{n}, VR 4.
Failure policy: HALT on the first sub-agent failure or hard error.
```

Unless `--no-gate` was passed, ask once: **"Proceed with this plan? (Y / adjust)"** Wait for confirmation. This is the only gate.

---

## Stage 1: Execute the chain

Run each planned step in order. For every step:

1. **Announce** the step: `▶ STEP {i}/{total}: {CODE} — {name}`.
2. **Load** that capability's `.md` file from this skill directory and execute its full procedure:
   - TR → `research-tool-stack.md`
   - EI → `extract-improvements.md`
   - RI → `research-improvements.md`
   - BR → `build-and-rate.md`
   - BO → `build-outlook.md`
   - TS → `build-technical-specs.md`
   - VR → `verify-research.md`
3. **Auto-select scope.** When a capability's pre-flight asks for a scope (RI/BR/TS offer A/B/C/D, TR auto-batches), always choose **"all unprocessed"** (scope A) on a default run, or **"full refresh / all"** (scope D) when `--force` is active. Do not stop to ask.
4. **Suppress the per-step feedback epilogue.** The "Anything to adjust, or good to go?" prompt in SKILL.md is skipped for intermediate steps — RA does one consolidated review at the very end (Stage 3). CRM task updates per step are best-effort and stay on (they are silent).
5. **Checkpoint.** Each capability already writes its domain file(s) and updates `audit-manifest.json` after its batches. Confirm the write happened before moving on.
6. **Inter-step gate.** Before starting the next step, verify the current step produced what the next step needs (see the table in "Dependency facts"). If the precondition is missing, treat it as a hard failure (Stage 2).

Print a one-line result after each step:
```
  ✓ {CODE} complete — {short metric, e.g. "23 changes researched, 5 bundles" / "total $X/yr" / "3 phases, 14 wks"}
```

---

## Stage 2: Failure handling — HALT

The failure policy for RA is **halt immediately**. Do not retry, do not continue downstream.

A step is failed if any of these occur:
- A capability reports any sub-agent with `parse_error` / `status: "sub_agent_failed"` / a failed VR lens.
- A pre-flight blocks (e.g. RI finds `proposed_changes[]` empty, BO refuses on `audit_status`).
- An inter-step gate finds a required field absent.
- A required file write throws.

On failure:
1. Stop the chain. Do not start any further step.
2. Keep all partial work already written to disk (each completed step is checkpointed).
3. Report precisely:
   ```
   ✗ HALTED at STEP {i}: {CODE} — {name}
     Reason: {what failed}
     Failed items: {change IDs / lens names, if applicable}
     Completed and saved: {list of steps that finished}
     Not run: {remaining steps}

   To resume after fixing: re-run [RA] (it will skip completed steps),
   or run the failed capability directly, e.g. [{CODE}] scope B on {ids}.
   ```
4. Hand back to the user. Do not attempt the consolidated review.

---

## Stage 3: Consolidated report and single feedback epilogue

Only reached if every planned step completed without halting.

Print one combined summary:

```
PIPELINE COMPLETE — {company_name}
Ran: {ordered steps}   |   Skipped: {steps}

  Proposed changes:   {n}  ({n} client, {n} analyst)
  Plugin bundles:     {n}
  Total annual value: ${total}/yr
  Blueprint:          {n} phases over {weeks} weeks
  Technical specs:    {n}/{n} bundled skills covered
  Verification:       {confidence} — {n} findings, {n} resolved, {n} deferred

Deliverables: blueprint.html regenerated via auto-regen hook on BO save.
Next in the engagement: Solution Designer [RE] (Skill 6), or generate/deploy deliverables.
```

Then run the **feedback epilogue once** for the whole run (per SKILL.md): show the summary, ask "Anything to adjust, or good to go?", and log a single record with `capability: "RA"` and `output_type: "pipeline_run"`. If the user requests an adjustment, route it to the relevant capability's re-run rather than patching by hand.

---

## Notes

- **Idempotent and resumable.** RA detects completed steps and skips them, so a second `[RA]` after a halt-and-fix picks up where it stopped. `--force` overrides this for a clean full refresh.
- **RA stays inside Skill 4.** It never calls the Generator (Skill 5) or Solution Designer (Skill 6). HTML regen happens through the auto-regen hook when domain files are written.
- **CRM.** Per-step CRM task updates (from each capability) remain on and best-effort. If `meta.crm.project_id` is null they are skipped silently — RA does not depend on CRM.
