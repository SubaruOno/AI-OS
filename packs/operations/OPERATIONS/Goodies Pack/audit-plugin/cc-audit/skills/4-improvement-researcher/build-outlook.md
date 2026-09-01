---
name: build-outlook
description: Build the transformation blueprint phases, short-term and long-term outlook narratives, and risks summary that power the Gantt chart and 'Where this takes you.' section on blueprint.html.
menu-code: BO
---

# Build Outlook (BO)

> **Idempotent.** First run authors `transformation_blueprint` from scratch. Re-runs refresh the phases, narratives, and risks against the current audit data, preserving nothing (the blueprint is fully recomputed each time).
>
> **Runs after RI, before BR.** BO consumes the full audit data (including `plugin_bundles[]` from RI) and synthesises the three-tier phased rollout, the short-term and long-term narrative, and the risks the plan mitigates. BR can run before or after BO, but if BR has run, phase durations come from real `implementation.weeks_estimate` rather than heuristics.

## Purpose

Author `strategy.transformation_blueprint` so the blueprint deliverable can render:
1. A Gantt chart of the phased rollout (Quick Wins, Core Builds, Future Sprints).
2. A short-term outlook (0-3 months) and long-term outlook (6-18 months) tailored to the company.
3. A risks narrative grounded in real client data, covering data flow & context access, data storage & ownership, and AI training & adoption.

This is a narrative authoring capability. The goal is plain-English text the client can read out loud and recognise as their situation.

---

## Stage 1: Pre-flight

1. Load audit data. If `clients/{client_slug}/03-audit/data/audit-manifest.json` exists (v4), read domain files directly:
   - `clients/{client_slug}/03-audit/data/meta.json`
   - `clients/{client_slug}/03-audit/data/extraction.json`
   - `clients/{client_slug}/03-audit/data/findings.json`
   - `clients/{client_slug}/03-audit/data/opportunities.json`
   - `clients/{client_slug}/03-audit/data/strategy.json`

   For v3/v2 clients, fall back to reading `clients/{client_slug}/03-audit/data/audit-data.json` and use the same field paths via `audit_reader.load_all()`.

2. Refuse to run if any of the following are true:
   - `proposed_changes[]` is empty (run EI first)
   - `meta.audit_status` is not `process_map_complete`

3. Warn (do not block) if:
   - Any `proposed_changes[].implementation.weeks_estimate` is unset (Gantt durations will be heuristics based on `payback_months`).
   - `risk_register[]` is empty and no `pain_points[].risk_signal=true` (the risks narrative will have less to anchor on).

4. Print a readiness summary:
   ```
   BUILD OUTLOOK STATUS -- {company_name}
   Proposed changes: {n} ({n_quick} quick wins, {n_core} core builds, {n_future} future)
   BR has run: {yes|no}   ({n_with_weeks}/{n} changes have weeks_estimate)
   Risk register entries: {n}
   Pain points flagged as risks: {n}
   ```

---

## Stage 2: Build phases

Group `proposed_changes[]` into three tiers using each change's top-level `payback_months` field (i.e. `proposed_changes[].payback_months`, NOT `value.payback_months` — payback lives at the change root):
- **Quick Wins** (`tier_code: QUICK_WIN`): `payback_months < 6`
- **Core Builds** (`tier_code: CORE_BUILD`): `6 <= payback_months <= 12`
- **Future Sprints** (`tier_code: FUTURE`): `payback_months > 12` or `payback_months` unset

For each phase, compute:

| Field | How |
|---|---|
| `phase_number` | 1, 2, 3 in tier order |
| `label` | `Quick Wins`, `Core Builds`, `Future Sprints` |
| `tier_code` | as above |
| `change_ids` | list of `proposed_changes[].change_id` in this tier |
| `effective_duration_weeks` | If all member changes have `implementation.weeks_estimate`: `max(2, ceil(sum(weeks_estimate) * 0.65))` (the 0.65 factor caps parallel work). If any are missing: fall back to `len(change_ids) * 1.5` weeks, clamped to `[3, 16]` for Quick Wins, `[4, 24]` for Core Builds, `[4, 32]` for Future Sprints. Round to nearest integer. |
| `start_week` | Phase 1 starts at week 1. Phase 2 starts at `phase_1.start_week + phase_1.effective_duration_weeks`. Phase 3 follows phase 2. |
| `timeframe` | Human-readable string. For phase 1: `"Weeks 1-{end}"`. For phase 2 and 3: if start_week > 12, render as `"Months {start_month}-{end_month}"` using `ceil(week/4)`. |
| `description` | Single sentence tailored to the client: what gets built in this phase, in plain English. Reference the strongest 1-2 themes. |
| `total_annual_value_aud` | Sum of `value.combined_annual_value_aud` across `change_ids`. Use 0 for changes missing the value. |

Skip any phase whose `change_ids` would be empty.

Also compute root-level:
- `total_phases` = number of non-empty phases
- `estimated_total_weeks` = last phase's `start_week + effective_duration_weeks - 1`
- `total_annual_value_aud` = sum of `phases[].total_annual_value_aud`

---

## Stage 3: Build the short-term outlook

Write `short_term_outlook.summary` (2 to 4 sentences) covering:
- What gets shipped in the first 0-3 months (point to the Quick Wins phase).
- What measurable thing the team will feel quickly (cite a specific pain point or waste item by name).
- Why these come first (typically: foundations or fast payback).

Write `short_term_outlook.highlights[]` (exactly 3 bullets, each one short sentence). Each bullet MUST reference at least one client-specific noun from the audit data: a tool name from `extraction.tools[]`, a staff name from `extraction.staff_roster[]`, a `change_id` (CH-XXX), a pain point ID (PP-XXX), or a quoted figure from `findings.pain_points[]` (e.g. "13 hrs/wk", "722 clients").

**Materiality filter:** For each bullet, ask: *Is this consequential to the business — real money, customers, headcount, or time?* Keep anything consequential, even if obvious. Drop only the banal.

**Causal chain requirement:** Go 2-3 steps deep where the data supports it. Pattern: Surface signal → What happens because of it → Downstream cost. Single-step bullets are forbidden if deeper data exists. Example: "The quoting plugin ships in week 3. Sam's 4 hrs/wk of manual quote assembly drops to 30 min. This frees the Friday afternoon bottleneck that currently delays job starts by 1-2 days."

> **DO NOT copy the patterns below verbatim into output.** They are illustrative structures only. Every bullet you write must substitute THIS client's actual tools, roles, change IDs, and numbers. If you cannot anchor a bullet in a specific entity in the audit data, drop it and write a different one.

Pattern shapes (substitute the bracketed slots with real values from this client's audit data):
- "[Plugin name / change_id] ships in [week N] and [specific person or role] goes from [current manual process] to [new state] in [time reduction]."
- "[Named waste item activity, N hrs/wk] drops to [target state] once [skill or change] is live — [downstream effect]."
- "[Specific bottleneck in the audit] is resolved by [week N], which means [observable downstream change, e.g., 'jobs start on Monday instead of Wednesday']."

Sanity check before writing: every bullet must contain at least one of — tool name, staff name, change_id, pain_point_id, or a numeric figure from the audit data. Bullets without any of those are forbidden and must be rewritten.

Avoid generic phrases like "increased efficiency" or "better workflows".

---

## Stage 4: Build the long-term outlook

Write `long_term_outlook.summary` (2 to 4 sentences) covering:
- What the business looks like in 6-18 months once foundations are in place.
- The shift in how data flows (the system has context the team currently has to assemble manually).
- The capabilities AI can take on once data is unified.
- The flexibility kept for future AI updates (vendor-agnostic foundations, easy swap of models or tools).

Write `long_term_outlook.highlights[]` (exactly 3 bullets). At least one bullet must touch each of: data unification, AI-enabled capability, future flexibility. Tie each bullet back to a Core Build or Future Sprint phase initiative.

**Materiality filter:** Same test as Stage 3 — keep anything consequential, drop only the banal.

**Causal chain requirement:** Same as Stage 3 — 2-3 steps deep where the data supports it.

**Measurable proof requirement (mandatory for long-term bullets):** Every long-term bullet MUST include one of:
- A target metric: "quote turnaround drops from 4 hrs to 45 min by week 16"
- An observable behaviour change: "Sam no longer reconciles HubSpot to Sheets on Friday afternoons"
- A removed manual artefact: "the materials master spreadsheet is retired"

Pure narrative bullets ("the business becomes more data-driven", "the team operates more efficiently") are **forbidden**. If you cannot attach a specific metric, behaviour, or removed artefact to a bullet, rewrite it or drop it.

> **DO NOT copy the patterns below verbatim into output.** They are illustrative structures only. Every bullet must substitute THIS client's actual tools, roles, change IDs, and numbers from `extraction.tools[]`, `extraction.staff_roster[]`, `extraction.processes[]`, and `opportunities.proposed_changes[]`.

Pattern shapes (substitute the bracketed slots with real values from this client's audit data):
- Data unification: "[Named lists/registries the client maintains today across N tools] become queryable in one place — [named role] no longer reconciles [specific manual activity] every [frequency]."
- AI-enabled capability: "[Named staff member] can ask Claude '[a question they currently spend N minutes answering by hand]' instead of [current manual process]. [Downstream effect on their time or output quality]."
- Future flexibility: "Every workflow is a [skill / plugin] that reads [the shared data layer], so [a named tool or LLM] can be swapped without rewriting [a named team's day-to-day]. The [specific integration] built in Phase [N] becomes the connector layer for future [AI capability]."

Sanity check before writing: every bullet must contain at least one of — tool name, staff name, change_id, pain_point_id, or a numeric figure from the audit data. Bullets without any of those are forbidden and must be rewritten.

---

## Stage 5: Build the risks outlook

Write `risk_outlook.summary` (2 to 4 sentences) framing the top risks this plan mitigates and why the staging protects the business.

### 5a. Select risk categories dynamically

Do NOT use a fixed set of three categories. Instead, select **3 to 5 categories** from the catalogue below based on which signals fire strongest from this client's audit data. Score each category against the signals listed — choose the highest-scoring ones.

| Category slug | Trigger signals to look for |
|---|---|
| `data_flow_context` | Tools that don't talk; manual re-entry across systems; pain points where staff can't see context; `tools[].integration_openness: "closed"` or "limited"; `optimisations[]` about unifying data |
| `data_storage_ownership` | Vendor lock-in; proprietary formats; key data only one person can access; `tools[].data_accessibility: "locked"` or `"closed_api"`; `pain_points[].risk_signal=true` related to single point of failure |
| `ai_training_adoption` | Staff readiness gaps; team size vs change ask; pain points about tool underuse; `findings.change_readiness` signals |
| `mission_critical_fragility` | Processes where `criticality == "mission_critical"` (if extracted); high `revenue_exposure_aud`; pain points describing system-failure consequences; business-critical workflows with single points of failure |
| `compliance_exposure` | `steps[].data_sensitivity` in [pii, financial, health, regulated] (if extracted); industry signals from `meta.industry_tag`; mention of regulations or audits in pain points |
| `key_person_dependency` | One person in `staff_roster[]` appears as `owner` across multiple processes; pain points about "when X is away"; reliance on undocumented tribal knowledge |
| `vendor_concentration` | Sum of `tools[].monthly_cost_aud` for one vendor exceeds ~30% of total tool spend; heavy reliance on one platform for multiple processes |
| `external_collaborator_block` | `tools[].external_collaborator_blocker: true` (if extracted); pain points about contractors/subcontractors unable to use systems; data shared via workarounds (email, USB, WhatsApp) because the primary tool blocks external access |
| `change_fatigue` | Multiple in-flight process changes mentioned; recent system migrations; team capacity concerns in pain points; high number of proposed changes relative to team size |
| `hidden_integration_debt` | High `workarounds` count across tools; spreadsheets used as databases; brittle scripts mentioned; pain points about manual fixes after data exports |
| `customer_facing_exposure` | Pain points or waste items in stages that touch customers directly (sales, delivery, support, invoicing); risk of errors reaching clients |

**Selection rule:** Pick the 3-5 categories with the strongest evidence signal in this client's data. Include `data_flow_context` or `data_storage_ownership` only if there is a real anchor (not by default). Include the new categories only when the audit data explicitly supports them.

### 5b. Materiality filter

Before writing any risk bullet, apply this test: *Is this consequential to the business? Could it cost real money, real customers, real headcount, or real time?*

Keep: anything consequential, even if obvious. A well-known problem is still worth including if it has real business impact.
Drop: only the banal — observations with no meaningful consequence (e.g., "the team uses email").

### 5c. Causal chain requirement

Every risk bullet must go **2-3 steps deep** where the audit data supports it. Pattern:

> **Surface signal** → **What happens because of it** → **Downstream business cost or risk**

Example: "HubSpot data lives in 3 places. Sam reconciles manually each Friday. When she takes leave, quote accuracy drops and the gap shows up in invoicing disputes 3 weeks later — which finance currently writes off without flagging."

Single-step bullets ("X is fragmented across tools") are forbidden if the audit data supports going deeper.

### 5d. Write each risk item

```json
{
  "category": "{slug from catalogue}",
  "title": "Short label, max 8 words",
  "description": "1 to 3 sentences. MUST cite a specific tool, person, process, or pain point by name. MUST go 2-3 steps deep where data supports it.",
  "mitigation": "1 sentence on how the plan addresses it. Reference a phase by name where relevant."
}
```

If a category truly has no anchor in the audit data, omit it. Do not invent risks.

### 5e. Optional: Surface top-2 risk ranking

After writing all risk items, optionally add to `risk_outlook`:

```json
"top_risks": [
  { "rank": 1, "category": "{slug}", "reason": "One sentence: biggest exposure / fastest deteriorating / hardest recovery." },
  { "rank": 2, "category": "{slug}", "reason": "..." }
]
```

Include this only if two risks are clearly worse than the others. Omit if the risks are similar in severity.

---

## Stage 6: Persist

Assemble the full `transformation_blueprint` block:

```json
{
  "phases": [...],
  "total_phases": N,
  "estimated_total_weeks": N,
  "total_annual_value_aud": N,
  "short_term_outlook": {...},
  "long_term_outlook": {...},
  "risk_outlook": {
    "summary": "...",
    "risks": [...],
    "top_risks": [...]
  },
  "last_built": "ISO-8601 timestamp"
}
```

Write via `audit_reader.save_domain({slug}, "strategy", strategy_obj)` where `strategy_obj["transformation_blueprint"]` is replaced with the new block. This:
1. Updates `clients/{slug}/03-audit/data/strategy.json` for v4 clients (or `audit-data.json` for legacy).
2. Updates `audit-manifest.json` `domains.strategy.updated_at` and root `updated_at`.
3. Triggers the `auto-regen-deliverables.sh` hook, which re-runs GB and regenerates `blueprint.html`.

Sanity checks before writing:
- Every `phase.change_ids[]` entry must exist in `opportunities.proposed_changes[].change_id`. If not, drop it and log a warning.
- Every `risk.description` must reference at least one named tool or process from `extraction.tools[]` or `extraction.processes[]`. If not, ask yourself whether this risk is real, then either rewrite or drop.

---

## Stage 7: CRM task update

After writing, update the CRM task `Build Outlook (BO)`. Best-effort, never block.

1. Load `meta.crm.project_id`. If null, skip silently.
2. `list_tasks(project_id)` and find the BO task by title. If it does not exist (older projects), create it.
3. `update_task_status(task_id, status: "Done")`
4. `create_task_comment(task_id, content)` with: `"Authored transformation_blueprint: {N} phases over {estimated_total_weeks} weeks, total {total_annual_value_aud} AUD/yr. {n_risks} risks across {n_categories} categories."`
5. Move the next task to "In Progress":
   - If BR has not run yet: BR
   - Else: VR
6. Update `meta.crm.last_synced`.

---

## Stage 8: Report and recommend next

Print:
```
BUILD OUTLOOK COMPLETE -- {company_name}
  Phases:      {n} ({timeframe span})
  Total ROI:   ${total_annual_value_aud}/yr
  Outlook:     short-term {n_highlights} highlights, long-term {n_highlights} highlights
  Risks:       {n} risks across {n_categories} categories: {category_slugs}

blueprint.html regenerated. Next: {BR if not run, else VR}.
```

Recommend the next capability based on what has run.
