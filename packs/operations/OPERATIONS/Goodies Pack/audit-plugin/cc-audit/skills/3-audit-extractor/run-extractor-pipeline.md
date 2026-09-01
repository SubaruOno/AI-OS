---
name: run-extractor-pipeline
description: RX capability — run the entire Process Mapper extraction pipeline end-to-end (SU → IM → PR → FR → WR) in one trigger, so a human does not fire each capability by hand. Autonomous by default: auto-applies every review change, checkpoints between steps, halts on a hard extraction failure, and produces one consolidated report. Each step's own sub-agent fan-out does the parallel work.
menu-code: RX
---

# Run Extractor Pipeline (RX)

> **Orchestration capability.** This is the single command that runs the whole Process Mapper so a human does not have to fire each capability by hand. It chains the five extraction-stage capabilities in dependency order — **SU → IM → PR → FR → WR** — auto-selects the "all unprocessed / all" scope at each step, checkpoints after every step, and (by default) auto-applies every proposed review change. The goal is one trigger that takes a client from "new transcripts on disk" to "extraction QA'd and ready for `process_map_complete`."
>
> **Where the parallelism is.** The five capabilities are a near-strict sequential chain — SU bootstraps the data files IM needs, and all three reviews QA the data SU/IM wrote — so they cannot overlap. The real parallel speed-up already lives *inside* each capability: SU fans out four CRM/filesystem fetchers and one sub-agent per source; IM batches 6–8 materials across parallel sub-agents; PR dispatches one sub-agent per subprocess for BPMN validation. RX does not add parallelism *across* steps (it would corrupt shared files — see "Why the reviews are sequential"); it removes the manual hand-offs between them and lets each step's own batching run.

## Execution model — why some steps run inline and others as sub-agents

Claude Code sub-agents **cannot spawn their own sub-agents**. That single constraint dictates how RX runs each step, and it is also how RX keeps the *main* context window small:

| Step | Fans out internally? | How RX runs it | Why |
|---|---|---|---|
| SU | Yes (4 fetchers + 1 per source) | **Inline** (main thread) | Must run where it can dispatch its own sub-agents. Those sub-agents return compact summaries, so the heavy fetch/extract work never lands in the main context. |
| IM | Yes (batches of 6–8) | **Inline** (main thread) | Same — needs to dispatch its batch sub-agents. |
| PR | Yes (1 per subprocess, Step 4) | **Inline** (main thread) | Needs its per-subprocess BPMN fan-out. |
| FR | No | **Leaf sub-agent** | Flat procedure. Running it as an isolated sub-agent keeps its transcript-by-transcript source verification (Steps 6a–6d) **out of the main context** — this is the primary context-window win of RX. |
| WR | No | **Leaf sub-agent** | Same as FR. |

The rule: **fan-out steps run inline; flat steps run as leaf sub-agents.** Every step reuses its own capability file's apply logic verbatim — RX never re-implements merging, dedup, or math correction itself.

## When to use

Run RX when a client has new inputs to process and you want the full Mapper pass — sync, bulk ingest, and the three QA reviews — without standing over each step. For a surgical re-run of one capability (e.g. just re-review waste after a manual edit), use that capability's own menu code instead.

This pipeline is the QA that *precedes* `audit_status = "process_map_complete"`. It does **not** require that flag (unlike the Analyst's `[RA]`), and it never sets it automatically — Stage 4 offers it as the next step.

---

## The pipeline (execution order)

```
SU  Sync & Update          fetch new CRM meetings/emails/SMS/calls + scan docs, extract
 │                          → writes extraction.json + findings.json (creates files if absent)
IM  Ingest Materials        deep 4-pass extraction of unprocessed 01-materials/documents/
 │                          → writes extraction.json + findings.json   (skipped if nothing new)
PR  Process Review          QA the process map (BPMN, dedup, names, sources, reclassify)
 │                          → writes extraction.json  (+ findings.json for [RECLASSIFY] items)
FR  Findings Review         QA pain_points (dedup, overlap groups, stages, source links)
 │                          → writes findings.json
WR  Waste Review            QA waste_items (dedup, overlap, math, links, adjusted totals)
                            → writes findings.json
```

**Why the reviews are sequential (and not parallelised across steps).** Two hard dependencies forbid running PR/FR/WR concurrently:
1. **PR → FR ordering.** PR's `[RECLASSIFY]` changes remove observation-steps from the process map and *create new `pain_points` in `findings.json`*. If FR ran before or alongside PR, it would review an incomplete pain-point set. PR must fully complete first.
2. **FR ⟂ WR write conflict.** FR and WR both write `findings.json` (FR → `pain_points[]` + `follow_up_questions[]`; WR → `waste_items[]` + `follow_up_questions[]`). Two agents writing the same file concurrently corrupts it (last-write-wins). They are run one after another, each the sole writer at its moment.

So RX runs the reviews strictly **PR → FR → WR**. The parallel speed-up is *inside* each step, not across them.

---

## Idempotency — built to run after every session

RX is designed to be run **repeatedly** — once after each client meeting — over the *whole* dataset every time. Each run re-syncs only genuinely new inputs (SU/IM dedup), then re-QAs everything, so issues introduced by the latest session get caught and the data converges rather than drifts. The convergence is not luck; it rests on how the capabilities are built:

| Operation | Why a re-run is safe |
|---|---|
| **Merges / duplicate removal** (PR, FR, WR) | A removed duplicate is gone, so it is never re-detected. Naturally idempotent. |
| **Waste overlap correction** (WR) | The deduction lives in a separate field `overlap_adjustment_aud` that is **assigned a recomputed value**, never subtracted from the base `annual_waste_aud`. Re-assigning the same figure leaves the adjusted total unchanged — it does **not** stack. |
| **Math fixes** (WR) | Once `annual_waste_aud` equals the formula result, there is no mismatch to fix. |
| **Text-quality fixes** (PR/FR/WR) | The em-dash / formal phrasing is already gone, so it is not re-flagged. |
| **Name normalization** (PR/FR) | "If all names are already consistent, no changes needed." |
| **Follow-up questions** (FR/WR) | Both check existing `follow_up_questions[]` before drafting, so the same gap is not re-asked. |
| **Cross-reference links** (FR/WR) | Added as a **set-union** (the dispatch prompt enforces this) — existing IDs are never duplicated. |
| **Overlap group labels** (FR/WR) | An existing `overlap_group` label is reused rather than re-minted. |
| **PR `[RECLASSIFY]`** | The observation-step is removed and turned into a pain point on the first run; on later runs the step is gone, so it is not reclassified again. |

The headline figure that an unattended run must never silently corrupt — the waste annual total — is protected by the separate-additive-field design above. The Stage 4 report prints the gross→adjusted delta every run so any unexpected movement is visible immediately.

---

## Stage 0: Pre-flight and execution plan

### 0a. Parse arguments

Optional args after the menu code:
- `--from <CODE>` — start at this step (`SU`/`IM`/`PR`/`FR`/`WR`), skip everything before it. Use when earlier steps are known-good.
- `--only <CODES>` — run only these steps (comma-separated, e.g. `--only FR,WR`).
- `--skip <CODES>` — run everything except these (e.g. `--skip IM`).
- `--force` — run every step regardless of current state (full refresh; passes "all" scope to each capability).
- `--gate` — **supervised mode.** Do not auto-apply. Run the reviews **inline** so each capability's native "Apply changes? (ALL / numbers / NONE)" prompt surfaces to the user. (Without this flag, RX is fully autonomous and answers ALL.)

Default (no args): run the full chain SU → IM → PR → FR → WR, autonomously, skipping steps that have nothing to do (see 0b).

### 0b. Load state and decide which steps run

Resolve the client exactly as the SKILL.md activation does (`{client_slug}` → `{client_dir}`). Load the v4 domain files: `03-audit/data/audit-manifest.json`, `meta.json`, `extraction.json`, `findings.json`. (Fall back to `audit-data.json` for v3/v2 clients.)

Determine each step's run/skip from the data, not from CRM:

| Step | Runs on a default pass when… | Skipped when… |
|---|---|---|
| SU | Always (it self-detects new CRM sources + new files; cheap no-op if nothing is new) | never (unless `--skip`/`--from`/`--only` excludes it) |
| IM | `01-materials/documents/` contains ≥1 file **not** present in `extracted_materials[]` | every document is already in `extracted_materials[]` |
| PR | `extraction.processes[]` is non-empty | no processes extracted yet |
| FR | `findings.pain_points[]` is non-empty | no pain points yet |
| WR | `findings.waste_items[]` is non-empty | no waste items yet |

`--force` overrides every "skipped" above and runs the step anyway. `--from`/`--only`/`--skip` are applied after this detection.

### 0c. Build and show the plan

Render the plan before executing:

```
RUN EXTRACTOR PIPELINE — {company_name}
Path: {client_dir}/
Mode: {autonomous | supervised (--gate)}

Plan for this run:
  SU  Sync & Update      [ run ]                    (inline)
  IM  Ingest Materials   [ run: {n} new docs | skip: all ingested ]   (inline)
  PR  Process Review     [ run: {n} processes | skip: none extracted ]   (inline)
  FR  Findings Review    [ run: {n} pain points | skip ]   (sub-agent)
  WR  Waste Review       [ run: {n} waste items | skip ]   (sub-agent)

Reviews run PR → FR → WR (sequential — shared findings.json + PR reclassify feeds FR).
Apply policy: {auto-apply ALL | pause at each review for your selection}.
Failure policy: HALT on a hard SU/IM/PR failure; a failed FR or WR is skipped and flagged, the run continues.
```

In **autonomous mode (default), do not wait — proceed straight to Stage 1.** Only in `--gate` mode, ask once: **"Proceed with this plan? (Y / adjust)"** and wait.

---

## Stage 1: Extract (SU → IM, inline)

Run each planned extract step in order, **inline on the main thread** (so its sub-agent fan-out works). For each:

1. **Announce:** `▶ STEP {i}/{total}: {CODE} — {name}`.
2. **Load and execute** the capability file's full procedure inline:
   - SU → `sync-and-update.md`
   - IM → `ingest-materials.md`
3. **Auto-select scope.** Whenever the capability asks for a scope, choose **"all unprocessed"** on a default run, or **"all / full refresh"** when `--force` is active. For IM, proceed autonomously even if the batch count exceeds its usual 20-unit confirmation threshold (this is an unattended run) — but log the batch count.
4. **Suppress the per-step feedback epilogue.** Skip each capability's "Anything to adjust, or good to go?" prompt — RX runs one consolidated epilogue at the very end (Stage 4). Per-step CRM task updates stay on and silent.
5. **Checkpoint.** SU and IM already write their domain files + `audit-manifest.json` after each source/batch. Confirm the write happened before moving on.
6. **One-line result:**
   ```
     ✓ SU complete — {n} new sources synced, {n} pain points / {n} waste items extracted
     ✓ IM complete — {n} materials ingested across {n} batches  (or:  ⃠ IM skipped — all documents already ingested)
   ```

Inter-step check: after SU + IM, `extraction.json` and `findings.json` must exist and be loadable. If not, that is a hard failure (Stage 3).

---

## Stage 2: Review (PR inline → FR sub-agent → WR sub-agent)

Run the planned reviews strictly in order. **Never dispatch two reviews at once** (they share `findings.json`).

### 2a. PR — Process Review (inline)

Run PR **inline** (it needs its Step 4 per-subprocess sub-agent fan-out):

1. Announce `▶ STEP {i}/{total}: PR — Process Review`.
2. Load and execute `process-review.md` fully, including its Step 4 sub-agent dispatch and its Step 9 apply.
3. **Apply policy:**
   - **Autonomous (default):** at PR's "Apply changes?" gate, answer **ALL**. Note PR's own rule: structural reshapes / lane splits marked `requires_confirmation` are *excluded* from ALL — that is correct and intended; they are reported as deferred, not applied blindly.
   - **`--gate`:** let PR's native prompt surface; apply the user's selection.
4. PR writes `extraction.json` (and `findings.json` for any `[RECLASSIFY]` items) + bumps `audit-manifest.json`. Confirm the write.
5. One-line result: `✓ PR complete — {n} steps cleaned, {n} duplicates removed, {n} reclassified to findings, {n} BPMN fixes`.
   - **Large process map caveat:** PR's per-subprocess fan-out is what lets it handle 10+ complex processes. It runs inline here precisely so that fan-out works. Do not attempt to run PR as a sub-agent.

### 2b. FR — Findings Review (leaf sub-agent)

Dispatch FR as a **single leaf sub-agent** so its transcript-by-transcript source verification stays out of the main context. Send one `Agent()` call and wait for it:

```
Agent({
  description: "FR Findings Review — {client_slug}",
  model: "sonnet",
  prompt: [
    "You are running the APG Process Mapper's Findings Review capability autonomously.",
    "Read and follow this capability file EXACTLY, every step:",
    "[full contents of findings-review.md]",
    "",
    "Context:",
    "  client_slug = {client_slug}",
    "  client_dir  = {client_dir}",
    "  Read the v4 domain files directly from {client_dir}/03-audit/data/ (meta.json, extraction.json, findings.json). Fall back to audit-data.json if no manifest.",
    "",
    "AUTONOMOUS RUN — overrides:",
    "  • At Step 9/Step 10 'Apply changes?', apply ALL proposed changes (treat the answer as ALL). Do NOT prompt; do NOT wait for input.",
    "  • Write the updated findings.json and bump audit-manifest.json exactly as Step 10 specifies.",
    "  • IDEMPOTENCY (this runs after every session, so it WILL re-process clean data): treat related_waste_ids / related_optimisation_ids additions as a SET-UNION — never duplicate an ID already in the array. If a pain point already has an overlap_group, REUSE that label rather than minting a new one. Already-merged/already-fixed items simply won't re-trigger — that is expected, not an error.",
    "  • Do NOT run any feedback epilogue.",
    "Return ONLY a compact summary (no file dumps): counts of duplicates merged, overlap groups, names normalized, stages corrected, source fixes, waste/opt links added, follow-up questions added, text fixes, and pain_point count before→after. If you could not complete, return { status: 'failed', reason: '...' }."
  ].join("\n")
})
```

- **`--gate` exception:** in supervised mode, do **not** dispatch FR as a sub-agent. Run `findings-review.md` inline so its native approval prompt reaches the user.
- One-line result from the returned summary: `✓ FR complete — {n} merged, {n} grouped, {n} links, {n} FQs added`.

### 2c. WR — Waste Review (leaf sub-agent, after FR)

Only after FR has fully returned and written `findings.json`, dispatch WR the same way (so it links against FR's cleaned pain points and there is no concurrent write):

```
Agent({
  description: "WR Waste Review — {client_slug}",
  model: "sonnet",
  prompt: [
    "You are running the APG Process Mapper's Waste Review capability autonomously.",
    "Read and follow this capability file EXACTLY, every step:",
    "[full contents of waste-review.md]",
    "",
    "Context: client_slug = {client_slug}; client_dir = {client_dir}. Read v4 domain files directly from {client_dir}/03-audit/data/.",
    "",
    "AUTONOMOUS RUN — overrides:",
    "  • At Step 10 'Apply changes?', apply ALL. Do NOT prompt or wait.",
    "  • Write findings.json and bump audit-manifest.json per Step 10.",
    "  • IDEMPOTENCY (this runs after every session, so it WILL re-process clean data): overlap_adjustment_aud is an ASSIGNMENT to a recomputed value, never an increment — if an item already carries an overlap_adjustment_aud, re-assign the same computed figure and REUSE the existing overlap_group label; never stack a second deduction. Treat related_pain_point_ids additions as a SET-UNION (no duplicate IDs). Already-merged/already-fixed items won't re-trigger — expected, not an error.",
    "  • Do NOT run any feedback epilogue.",
    "Return ONLY a compact summary: duplicates merged, overlap groups + total overlap_adjustment_aud, math fixes, pain-point links, FQs added, and the GROSS vs ADJUSTED operational annual total. If you could not complete, return { status: 'failed', reason: '...' }."
  ].join("\n")
})
```

- **`--gate` exception:** run `waste-review.md` inline in supervised mode.
- One-line result: `✓ WR complete — gross ${gross}/yr → adjusted ${adjusted}/yr ({delta})`.

---

## Stage 3: Failure handling

Two different policies, by step type:

**Hard extraction/process steps (SU, IM, PR) — HALT.** A step is failed if a capability reports a sub-agent `parse_error` / `status: "sub_agent_failed"`, a pre-flight blocks, a required file write throws, or the inter-step check finds `extraction.json`/`findings.json` missing. On failure:
1. Stop the chain. Do not start any further step.
2. Keep all partial work already written (every completed step is checkpointed to disk).
3. Report precisely:
   ```
   ✗ HALTED at STEP {i}: {CODE} — {name}
     Reason: {what failed}
     Completed and saved: {list}
     Not run: {remaining steps}

   To resume after fixing: re-run [RX] (it skips steps that are already done),
   or run the failed capability directly (e.g. [PR]).
   ```
4. Hand back to the user. Do not attempt the remaining reviews or the consolidated report.

**Reviews (FR, WR) — skip and flag, do not halt.** The reviews are independent of each other and of anything downstream, so a single failed review must not abort an otherwise-good run. If FR or WR returns `{ status: 'failed' }` (or its sub-agent errors):
1. Record the failure, leave that review's data untouched.
2. Continue to the next review (WR still runs even if FR failed — they touch disjoint arrays).
3. Flag it loudly in the Stage 4 report with the resume hint (`re-run [FR]` / `[WR]`).

---

## Stage 4: Consolidated report and single feedback epilogue

Reached when the extract steps succeeded (reviews may be individually flagged). Print one combined summary:

```
EXTRACTOR PIPELINE COMPLETE — {company_name}
Ran: {ordered steps}   |   Skipped: {steps}   |   Failed: {reviews, if any}

  Sources synced (SU):     {n} new ({n} meetings, {n} emails, {n} sms/calls)
  Materials ingested (IM): {n} files across {n} batches
  Process map (PR):        {n} steps · {n} duplicates removed · {n} reclassified · {n} BPMN fixes
  Pain points (FR):        {before} → {after}  ({n} merged, {n} overlap groups, {n} links)
  Waste (WR):              gross ${gross}/yr → adjusted ${adjusted}/yr  ({delta})
  Follow-up questions:     {n} added across the run

  ⚠ Failed/skipped reviews: {none | FR and/or WR with reason + resume hint}

Deliverables: regenerated via the auto-regen hook on each domain-file write.
Next in the engagement: confirm the map is complete, then set
  meta.audit_status = "process_map_complete"  and run the Analyst [RA] (Skill 4).
```

**Do not set `process_map_complete` automatically** — that is a human judgement (it gates the entire Analyst pipeline). Offer it; let the user confirm.

Then run the **feedback epilogue once** for the whole run (per SKILL.md): show the summary, ask "Anything to adjust, or good to go?", and log a single record with `capability: "RX"`, `output_type: "pipeline_run"`. If the user requests an adjustment, route it to the relevant capability's re-run rather than patching by hand.

---

## Notes

- **Idempotent and resumable.** RX skips steps that have nothing to do (0b) and reuses each capability's own idempotency (`extracted_materials[]` for IM; the reviews are safe to re-run). A second `[RX]` after a halt-and-fix picks up where it stopped. `--force` overrides for a clean full pass.
- **One trigger, five capabilities, lean main context.** The heavy work lives in sub-agents: SU/IM/PR's inline fan-out return summaries; FR/WR run entirely inside their own leaf contexts. The main thread holds only the plan, the one-line results, and the returned summaries.
- **Autonomous by default, auditable after the fact.** Every applied change is one a human would otherwise approve. The Stage 4 report surfaces the consequential deltas — especially the waste gross→adjusted total — so an unattended run is still reviewable. Use `--gate` when you want to eyeball each review's proposed changes before they apply.
- **Auto-regen hook.** Each step writes `audit-manifest.json` through its own apply logic, so deliverable regen may fire several times during a run; the final regen reflects the complete pipeline state. This is harmless (regeneration is idempotent) and RX does not suppress it.
- **RX stays inside Skill 3.** It never calls the Analyst (Skill 4) or Generator (Skill 5). It ends at a QA'd extraction, ready for `process_map_complete`.
