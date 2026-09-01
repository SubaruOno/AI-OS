---
name: audit-check
description: Re-run completeness and contradiction checks across all audit data. Show coverage gaps, contradictions, and prioritised follow-up questions.
menu-code: AC
---

# Audit Check

## Purpose

Unified quality check across all audit data. Runs the completeness checklist per stage, detects contradictions between sessions/speakers, and generates prioritised follow-up questions for unresolved gaps. Contradictions are recorded but not auto-resolved — they become HIGH-priority follow-up questions.

## Process

### Step 1: Load Current State

Client slug is set from activation. Check for `audit-manifest.json` in `clients/{client_slug}/03-audit/data/`. If present, this is a v4 client: read `clients/{client_slug}/03-audit/data/meta.json`, `clients/{client_slug}/03-audit/data/extraction.json`, and `clients/{client_slug}/03-audit/data/findings.json` directly. If `audit-manifest.json` does not exist, fall back to reading `audit-data.json` as v3/v2.

Load `references/completeness-checklist.md`. Identify which industry variant to apply based on `industry_tag`.

If fewer than 2 sessions have been analyzed, note this — single-session contradictions (same session, different speakers) are still worth detecting.

---

### Step 2: Completeness Assessment

For each of the 5 stages, check every item in the checklist against the audit data:

**Item status:**
- **CONFIRMED (HIGH)** — item has a verbatim quote and explicit data (times, names, counts)
- **INFERRED (MEDIUM)** — item can be reasonably inferred from context, but not explicitly stated
- **NOT CONFIRMED (LOW)** — item mentioned but without enough specifics to rely on
- **MISSING** — no data at all for this item across all sessions

For each stage, calculate:
- `confirmed_count` / `total_items` = coverage %
- Overall stage confidence = worst confidence across confirmed items

**Tool Coverage Check:**
- Count steps with non-empty `tool_ids[]` vs total steps across all stages
- Flag steps where description implies a tool ("enter", "update", "send", "log", "export", "import", "sync") but `tool_ids` is empty
- Report: "Tool coverage: X/Y steps (Z%)"

**Data Flow Coverage Check:**
- Count steps with `data_flow` populated vs total eligible steps (exclude first step per stage)
- Count `mechanism: "unknown"` entries separately
- Report: "Data flow coverage: X/Y handoffs documented (Z%). Unknown mechanisms: N"

**BPMN Notation Coverage Check:**
- Count exclusive gateways (`element_type: "exclusive_gateway"`) with complete branch documentation: 2+ outgoing sequence flows, all with `condition` labels, all with at least one downstream task step. Report: "Gateway coverage: X/Y gateways fully documented (Z%)"
- Count steps connected via `sequence_flows[]` (has at least one incoming or outgoing flow) vs total steps. Report: "Step connectivity: X/Y steps connected (Z%)"
- Count parallel gateway forks without corresponding joins. Report: "Unbalanced parallel gateways: N"
- Count steps with no `lane_id`. Report: "Unassigned lanes: N steps"

### Step 2b: Industry Archetype Structural Check

1. Read `industry_tag` from `meta.json`
2. Load `references/industry-archetypes.md`
3. Select the closest archetype: exact match on `industry_tag`, or "SME Services" as fallback
4. For each archetype required stage, check binary: does the extracted data have a process or step that plausibly covers this stage?
   - Yes = stage present
   - No = stage missing (flag as MEDIUM priority gap)
5. Display archetype coverage summary:
   ```
   ARCHETYPE COVERAGE: {n}/{total} archetype stages present
   Missing: [list of missing stage names]
   ```
6. Missing archetype stages that have no corresponding extracted process: add to `follow_up_questions[]` as compound questions (one per missing stage), unless the client has explicitly stated this stage is out of scope

---

### Step 3: Gap Analysis

#### Critical Gap: Mandatory IATO Fields Missing

Process cannot be marked ready for BPMN generation until every task-type step has at minimum:
- `iato.actor` non-null
- `iato.action` non-null
- `iato.output` non-null

Run this check before any other gap analysis:

1. Load `extraction.json` `processes[]`
2. For each step with `element_type` in `task`, `user_task`, `service_task`, `send_task`, `receive_task`, `manual_task`, `business_rule_task`:
   - Check `iato.actor`, `iato.action`, `iato.output`
   - Any null field → add to critical_gaps list
3. If critical_gaps is non-empty:
   - Display: `"MANDATORY FIELD GATE: {n} steps missing required IATO fields"`
   - List each step_id and which fields are missing
   - `"Resolve these before proceeding to BPMN generation"`
4. If critical_gaps is empty: proceed to other gap checks

---

Identify the highest-value gaps — missing items that would materially change the waste calculation or ROI model:

**Critical gaps** (blocking ROI calculation):
- No time figures for any waste item in a stage
- No headcount mentioned for staff doing manual work
- No tools named for a stage that should have tooling

**Important gaps** (would strengthen recommendations):
- Processes described but not timed
- Tools named but workarounds not explored
- Pain points mentioned but not quantified

**Minor gaps** (context, not blocking):
- Revenue range not stated
- Company size approximate only

**Critical Coverage Gaps** (blocking process map quality):
- Any stage with <50% tool coverage -- tool mapping incomplete
- Any stage with <50% data flow coverage -- handoff mechanisms undocumented
- Any step flagged as tool-implied but `tool_ids` empty
- Any exclusive gateway with <2 outgoing sequence flows -- incomplete decision tree
- Any stage with <50% step connectivity -- steps not connected via sequence flows
- Any parallel gateway fork without a matching join -- unbalanced parallel structure

---

### Step 4: Contradiction Scan

Run four contradiction checks:

**Check A — Cross-Session Speaker Conflicts**

For each topic that appears in more than one session's extractions:
- Compare statements made by different speakers or in different sessions
- Flag when the same process, tool, or activity is described differently

Pattern: "Speaker A said X in Session N. Speaker B said Y in Session M. These cannot both be true."

**Check B — Stated Process vs. Stated Tools**

Compare `processes[]` steps against `tools[]` usage:
- Does the process description mention a manual step that the named tool should handle automatically?
- Does the tool inventory include a tool that is never mentioned in any process step?

**Check C — Volume/Time Internal Consistency**

Check that numeric figures are internally consistent:
- If they handle X jobs per week and Y staff each spend Z hours per job, does the total add up?
- If they said lead volume is 50/month but also that "we contact every lead within 24 hours" with 1 admin — is that plausible?

Flag implausibility as a MEDIUM confidence contradiction.

**Check D — Confidence Drift**

For any item marked HIGH confidence that is contradicted by a MEDIUM or LOW confidence statement, flag it. HIGH confidence should not be assumed when conflicting data exists.

Downgrade confidence: if a HIGH confidence item is contradicted, mark the item as MEDIUM pending resolution.

---

### Step 5: Record Contradictions

For each contradiction found:

```json
{
  "contradiction_id": "C001",
  "topic": "",
  "statement_a": {
    "session": 1,
    "speaker": "",
    "quote": "",
    "timestamp_seconds": null,
    "meeting_id": ""
  },
  "statement_b": {
    "session": 2,
    "speaker": "",
    "quote": "",
    "timestamp_seconds": null,
    "meeting_id": ""
  },
  "resolution": "",
  "status": "unresolved"
}
```

Merge into `contradictions[]` in the audit data. Do NOT auto-resolve — all contradictions start as `unresolved`.

---

### Step 6: Generate Follow-Up Questions

For each gap (from Step 3) and each unresolved contradiction (from Step 5), generate a specific, answerable question:

**Format rules:**
- Reference their own words where possible ("You mentioned X — can you tell me...")
- Ask for exactly what's missing (a number, a name, a process step)
- Never ask compound questions (one gap = one question)
- Frame around their experience, not data collection ("How long does that typically take?" not "What is the duration?")

**For contradictions:** "In Session {n1} you mentioned [{statement_a}]. In Session {n2}, [{speaker_b}] said [{statement_b}]. Which reflects the actual process?"

**Prioritise by:**
1. HIGH — blocks ROI calculation, or a HIGH confidence process step is missing data, or contradiction between sessions
2. MEDIUM — would upgrade a MEDIUM confidence item to HIGH
3. LOW — context enrichment, not blocking

---

### Step 7: Present Combined Report

```
AUDIT CHECK — {company_name}
Sessions analyzed: {n} | Industry: {industry_tag}

┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ STAGE COVERAGE                                                                               │
├─────────────────┬────────────┬───────────┬─────────┬─────────┬───────────┬───────────────────┤
│ Stage           │ Coverage % │ Confidence│ Tool %  │ Flow %  │ Gateway % │ Connected %       │
├─────────────────┼────────────┼───────────┼─────────┼─────────┼───────────┼───────────────────┤
│ Acquisition     │ 62%        │ MEDIUM    │ 80%     │ 60%     │ 100%      │ 90%               │
│ Quoting         │ 45%        │ LOW       │ 30%     │ 20%     │ 50%       │ 60%               │
│ Onboarding      │ 80%        │ HIGH      │ 90%     │ 75%     │ 100%      │ 95%               │
│ Fulfilment      │ 30%        │ LOW       │ 20%     │ 10%     │ 0%        │ 40%               │
│ Retention       │ 10%        │ LOW       │ 0%      │ 0%      │ n/a       │ 0%                │
└─────────────────┴────────────┴───────────┴─────────┴─────────┴───────────┴───────────────────┘

TOOL COVERAGE: X/Y steps have tools mapped (Z%)
  {n} steps imply tool usage but have no tool_ids
DATA FLOW COVERAGE: X/Y handoffs documented (Z%)
  {n} handoffs have mechanism: "unknown"
BPMN COVERAGE: X/Y gateways fully documented (Z%), X/Y steps connected (Z%)
  {n} unbalanced parallel gateways | {n} steps with no lane_id

CRITICAL GAPS (blocking ROI):
  • No time figures for quoting process — cannot calculate quote waste
  • Fulfilment step-by-step process not described — no process map possible

CONTRADICTIONS ({count} found):
  C001 — {topic}
    Session {n1}, {speaker_a}: "{quote_a}"
    Session {n2}, {speaker_b}: "{quote_b}"
    Status: UNRESOLVED → Follow-up question added (HIGH)
  (or: "No contradictions detected — all statements internally consistent.")

FOLLOW-UP QUESTIONS ({total} questions)

  HIGH PRIORITY ({n}):
  1. [{stage}] "{question}"
  2. [{stage}] "{question}"

  MEDIUM PRIORITY ({n}):
  3. [{stage}] "{question}"

  LOW PRIORITY ({n}):
  4. [{stage}] "{question}"
```

Flag any HIGH priority gap that has been in follow_up_questions for more than one session as "Overdue."

---

### Step 8: Save

Merge any new follow-up questions into the audit data (avoid duplicates — check existing questions first). Save contradictions.

For v4 clients: write the full `findings.json` with updated `follow_up_questions` and `contradictions`, then update `audit-manifest.json` (`domains.findings.updated_at` and root `updated_at`). For v3 files: write new follow-up questions and contradictions into the `findings` domain object (`findings.follow_up_questions`, `findings.contradictions`). For v2 files: write to top-level keys as before.

Save the updated audit data file.

Report: "Audit check complete. {n} gaps identified. {n} contradictions found. {n} new follow-up questions added. Next session should prioritise: {top 3 HIGH priority questions}."
