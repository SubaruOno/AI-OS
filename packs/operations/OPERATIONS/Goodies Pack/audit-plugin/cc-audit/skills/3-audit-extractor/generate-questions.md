---
name: generate-questions
description: Audit data against all deliverable requirements, cross-reference transcripts, generate targeted follow-up questions, research researchable ones, export branded follow-up PPTX.
menu-code: GQ
---

# Generate Questions (GQ)

> **Idempotent.** Re-running picks up new gaps and skips already-classified/researched questions. Safe to run after every extraction.

## Purpose

Single command for the post-extraction workflow. Audits the audit data against everything the deliverables need (waste.html, findings.html, process-map.html), cross-references transcripts to catch already-answered items, generates targeted follow-up questions for unresolved gaps, researches what's researchable via exa, and exports a branded PowerPoint to `03-audit/sessions/{date}-{label}/follow-up-questions.pptx`.

**When to run:** After every SU extraction. Also useful at any audit stage to see "what do we still need?"

> **Never ask about individual staff hourly rates, salaries, or wages.** The audit assumes a single canonical blended rate of $50/hr for all waste calculations. We care about hours and how long things take, not what each staff member earns. Any gap that resolves to a per-staff pay figure is ignored, not converted into a follow-up question.

---

## Step 1: Load & Inventory

1. Client slug from activation. Check for `audit-manifest.json` in `clients/{client_slug}/03-audit/data/`. If present, this is a v4 client: read `clients/{client_slug}/03-audit/data/meta.json`, `clients/{client_slug}/03-audit/data/extraction.json`, and `clients/{client_slug}/03-audit/data/findings.json` directly. If `audit-manifest.json` does not exist, fall back to reading `audit-data.json` as v3/v2.

2. Count and display:
   ```
   AUDIT DATA INVENTORY: {company_name}
   ══════════════════════════════════════════
   Audit status:      {audit_status}
   Sessions:          {sessions_completed}
   Process steps:     {count across all stages}
   Pain points:       {n}
   Optimisations:     {n}
   Waste items:       {n} ({quantified} quantified, {unquantified} unquantified)
   Staff roster:      {n} entries
   Follow-up Qs:      {pending} pending | {answered} answered | {researched} researched
   ```

---

## Step 2: Deliverable Readiness Audit

Check readiness across three deliverable dimensions. This is the core gap-finding logic.

### 2a. Opportunity Quantification Readiness (drives waste.html)

For each `waste_items[]` entry, classify into one of three categories:

**Time-based waste items** (the standard model: hours × $50/hr × 52). The rate is the canonical assumed blended team rate. We never ask the client to confirm or correct it.
- Check `hours_per_week` present (null = **hard gap**)
- Check `headcount_affected` present (null = gap, default 1 is acceptable if a single person was stated)
- Check `annual_waste_aud` derivable: both of the above must be non-null

**Revenue leakage items** (hours_per_week is null by design, these measure lost money rather than lost time):
- Identify by waste_type `"missing_automation"` or `"no_followup"` where the description references revenue, conversion, or financial loss
- Check if `annual_waste_aud` is populated with a custom formula
- If null, flag need for three data points: **volume metric** (occurrences per year, lost leads per month), **per-unit value** (avg plan value, avg customer value), **miss/loss rate** (% missed, % churned)

**One-off items** (not recurring waste):
- Identify items describing a one-time cleanup or retroactive fix
- Flag these separately so they don't inflate the annual waste figure
- Suggest removing from recurring waste or adding a `recurring: false` flag

Build a per-item status table:

```
OPPORTUNITY QUANTIFICATION READINESS
──────────────────────────────────────────────────────────────────────
ID     │ Type          │ hrs/wk │ headcount │ annual    │ Gaps
───────┼───────────────┼────────┼───────────┼───────────┼──────────────
W-001  │ Time-based    │ ✗      │ ✗         │ ✗         │ Need hrs/wk, headcount
W-005  │ Time-based    │ 15     │ 1         │ $39,000   │ none
W-010  │ Rev. leakage  │ n/a    │ n/a       │ ✗         │ Need volume, value, miss rate
W-012  │ Time-based    │ 20     │ 2         │ $104,000  │ none
W-019  │ One-off       │ n/a    │ n/a       │ ✗         │ Not recurring, flag
──────────────────────────────────────────────────────────────────────
Annual figures use the assumed $50/hr blended team rate.

Summary: {n}/{total} fully quantified | {n} revenue leakage unquantified | {n} one-off
```

### 2b. Findings Readiness (drives findings.html)

- Count `pain_points[]` by confidence: HIGH / MEDIUM / LOW
- Check which stages have zero pain points and flag as potential blind spots
- Count `optimisations[]` and check coverage
- findings.html doesn't require quantification, it's discovery data. Flag only if a stage has NO findings at all.

```
FINDINGS READINESS
  Pain points:    {n} (HIGH: {n}, MEDIUM: {n}, LOW: {n})
  Optimisations:  {n}
  Stages with no findings: {list or "none, all covered"}
```

### 2c. Process Map Readiness (drives process-map.html)

Run the same checks AC uses:

**Tool coverage:**
- Count steps with non-empty `tool_ids[]` vs total steps
- Flag steps where description implies a tool ("enter", "update", "send", "log", "export", "import", "sync") but `tool_ids` is empty

**Data flow coverage:**
- Count steps with `data_flow` populated vs total eligible steps (exclude first step per stage)
- Count `mechanism: "unknown"` entries

**Stage coverage:**
- Check for stages in `business_stages_covered` with zero process steps

```
PROCESS MAP READINESS
  Tool coverage:      {n}/{total} steps ({pct}%), {n} steps imply tools but have none
  Data flow coverage: {n}/{total} handoffs ({pct}%), {n} unknown mechanisms
  Empty stages:       {list or "none"}
```

### 2d. BPMN Notation Completeness (drives process-map.html)

BPMN structural gaps in the process data map directly to follow-up questions. An incomplete BPMN diagram means we're missing process knowledge, not just missing diagram elements.

**Gateway branch documentation:**
For every step with `element_type: "exclusive_gateway"`, check its outgoing entries in `sequence_flows[]`:

- Count outgoing flows (where `from` == this gateway's `step_id`)
- Flag gateways with <2 outgoing flows as **incomplete decisions** -- the client mentioned a decision point but only one path was documented
- Flag outgoing flows with no `condition` label as **undocumented branches** -- we know there's a branch but don't know the condition
- For each branch, follow the outgoing flow to the target step. If the branch leads directly to another gateway or to nothing (no further task steps), the branch path is **empty** -- we know the condition but not what happens

Each gap generates a specific question:
- Incomplete decision: "You mentioned {gateway label}. What are the possible outcomes?"
- Undocumented branch: "When {gateway label}, you described what happens when {known condition}. What happens in the other case?"
- Empty branch: "When {gateway label} and the answer is {condition}, what specific steps follow?"

**Sequence flow connectivity:**
- Count steps with no incoming sequence flow (orphaned, unreachable in the diagram). Exclude the first step per stage.
- Count steps with no outgoing sequence flow that aren't the last step in the stage (dead ends).
- Each orphaned or dead-end step may indicate a process segment the client mentioned but didn't connect to the rest.
- Question pattern: "You mentioned {step label} in {stage}. Where does this fit in the overall process? What comes before/after it?"

**Parallel gateway balance:**
- Count parallel gateway forks without corresponding joins.
- An unbalanced fork means the client described parallel tracks that converge somewhere, but we didn't capture where.
- Question pattern: "You described {track descriptions} happening in parallel. At what point do these come back together?"

**Lane coverage:**
- Count steps with no `lane_id` (unassigned ownership).
- Count steps where `lane_id` doesn't match any `staff_roster[].name` entry, "Automated", or "External: *" prefix.
- Question pattern: "Who is responsible for {step label}?"

```
BPMN NOTATION COMPLETENESS
──────────────────────────────────────────────────────────────────────
Gateways:           {n}/{total} exclusive gateways fully documented
  Incomplete decisions (< 2 branches):  {n}
  Undocumented branches (no condition):  {n}
  Empty branches (no downstream tasks):  {n}
Sequence flows:
  Orphaned steps (no incoming flow):     {n}
  Dead-end steps (no outgoing flow):     {n}
Parallel gateways:
  Unbalanced forks (no matching join):   {n}
Lanes:
  Steps with no lane_id:                 {n}
  Steps with unrecognised lane_id:       {n}
──────────────────────────────────────────────────────────────────────
```

---

## Step 3: Transcript Cross-Reference

For each gap identified in Step 2 AND each existing `follow_up_questions[]` with `status: "pending"`:

### 3a. Search transcripts

Use Grep to search `clients/{client_slug}/01-materials/meetings/*/transcript.txt` for key terms extracted from the question or gap description. For example:
- A gap about quote prep duration: search for "quote", "how long", "takes", "minutes", "hours"
- A gap about families per week: search for "families per week", "new families", "how many join", "per week"
- A gap about BDM bonus time: search for "bonus", "calculation", "hours", "how long"

Run 2-3 targeted searches per gap. Scan results for relevant context.

### 3b. Classify findings

For each gap/question searched:

**Found in transcript, data was stated:**
If the data point was explicitly stated (e.g., "we get about 10 new families a week"), flag as:
- "Data stated in Session {n} but not extracted into audit data"
- This is an **extraction gap**: recommend re-running EB on that session, not a follow-up question
- Quote the relevant transcript excerpt

**Found in transcript, mentioned but not answered:**
If the topic was discussed but the specific data wasn't given (e.g., they talked about quoting time but didn't state minutes per quote), note this and still generate the follow-up question, but reference the conversation: "You touched on X in session {n}, roughly how long does that usually take?"

**Not found in transcripts:**
Proceed to Step 4. This is a genuine gap that needs a follow-up question.

### 3c. Present findings

```
TRANSCRIPT CROSS-REFERENCE
──────────────────────────────────────────────────────────────
✓ FOUND, likely answered in transcripts:
  • "Quote prep duration", Session 3 [42:15]: "takes about an hour each time"
    → Extraction gap, re-run EB to capture this

⚠ DISCUSSED but not answered:
  • "Families per week", Session 2 [18:30]: discussed family onboarding volume
    but no specific number stated → still needs follow-up question

✗ NOT FOUND in any transcript:
  • "Reminder dispatch time", no mention of how long this takes in any session
  • "Time for pay-week reminders", process mentioned but time never discussed
──────────────────────────────────────────────────────────────
```

**Pause:** "I found {n} items that may already be answered in transcripts. Please confirm which ones are genuinely answered before I proceed."

Wait for user confirmation. Mark confirmed items as `status: "answered"` with `answered_in_session` set. Never auto-resolve.

---

## Step 4: Generate New Questions

### Step 4a: Source Questions from Gaps Register

Load `findings.json` `gaps_register[]`. Filter to entries where:
- `gap_type == "A"` (never communicated)
- `generates_fq == true`
- `status != "resolved"`

These are the ONLY gaps that generate client questions.

Do NOT generate questions from:
- Type B gaps (internal research resolves these)
- Type C gaps (re-scan of source material resolves these)
- Any gap where `generates_fq` is false
- Any gap that overlaps with an already-answered follow_up_question (check `fq_id` linkage)
- **Any gap that resolves to a per-staff hourly rate, salary, wage, or pay figure.** These are out of scope. Mark such gaps `status: "out_of_scope"` and move on. The audit assumes the canonical $50/hr blended rate for every staff member.

If `gaps_register[]` is empty or absent (legacy data without gaps_register support): fall back to the original question generation logic (scan `pain_points[]`, `optimisations[]`, and `follow_up_questions[]` directly as before, applying the format and quality gate rules below). The "no per-staff pay" rule applies in the fallback path too.

---

### Step 4b: Assign Resolution Target

Every question must resolve exactly one of these five field types:

1. **UPSTREAM_NODE**, "What happens before [step]?"
   - Use when: `iato.input` is null AND no incoming `sequence_flow` to the step
   - Question pattern: "What triggers [step label]? / What arrives at [step label] to begin the process?"

2. **DOWNSTREAM_CONDITION**, "After [step], what happens next and under what conditions?"
   - Use when: `gateway_anatomy.condition` is missing OR `gateway_anatomy.true_path_target` is missing
   - Question pattern: "After [step label], what determines which path the [subject] takes? What's the threshold/condition?"

3. **ACTOR**, "Who is responsible for [step]?"
   - Use when: `iato.actor` is null
   - Question pattern: "Who handles [step label]? Is it always the same person/role or does it vary?"

4. **TOOL_AND_FUNCTION**, "What tool do you use for [step] and specifically which feature?"
   - Use when: `tool_ids[]` is empty on a step where tool use is expected
   - Question pattern: "What system or tool do you use for [step label]? Which specific feature do you use?"

5. **DURATION**, "How long does [step] typically take?"
   - Use when: `time_estimate_hours_per_week` is null on a step with pain annotations or waste items
   - Question pattern: "How long does [step label] typically take? / How many hours per week does your team spend on [step label]?"

Note: there is no rate or cost resolution target. The audit assumes the canonical $50/hr blended rate, and never asks the client to confirm or correct it.

Assign one resolution target to each gap. If a gap touches multiple targets, pick the most impactful one using this priority: DOWNSTREAM_CONDITION > UPSTREAM_NODE > ACTOR > TOOL_AND_FUNCTION > DURATION.

Add to each question a `resolves` object:
```json
{
  "resolves": {
    "field": "gateway_anatomy.condition",
    "step_id": "QUO-D01",
    "process": "quoting_process"
  }
}
```

---

### Step 4c: Cluster by Process Area

Group all generated questions by their `affected_process` field (the stage/process name).

For each process area:
1. Count questions in the group
2. If 3 or more questions target consecutive `step_id`s within the same process area:
   - MERGE into a compound question:
     "Walk me through what happens in [process area] between [step A label] and [step B label]. A few specific things I'd love to understand: [bullet list of the merged questions]"
   - Set `merged_question: true`, `constituent_gap_ids: [list of gap_ids merged]`
3. If fewer than 3 questions in a group: keep as individual questions

The goal: a client should receive at most ONE question per process area per session.

---

### Step 4d: Apply Priority Stack and Hard Cap

Sort all questions (individual and compound) by priority:

Priority order (highest first):
1. DOWNSTREAM_CONDITION questions (blocking BPMN gateway completion)
2. UPSTREAM_NODE questions (blocking process start/entry)
3. ACTOR questions (blocking lane assignment)
4. TOOL_AND_FUNCTION questions (enrichment but blocks automation detection)
5. DURATION questions (enrichment, waste calculation)

Within each priority tier, sort by: number of downstream gaps the answer would unblock (descending).

**Hard cap: Maximum 8 questions per session.**

If more than 8 questions exist after clustering:
- Take the top 8 by priority
- Save remaining to `findings.json` as `pending_questions[]` with `status: "deferred_next_session"`
- Display: "Deferred {n} questions to next session, priority questions shown above"

Questions falling below the cap are still saved to `findings.json` but excluded from the PPTX slide deck.

---

### Step 4e: Quality Gate

Before finalising, each question must satisfy at least ONE of:
1. It has a `resolves` object mapping to a specific field and `step_id`
2. Its answer would unblock a waste calculation (linked `waste_item`)
3. Its answer would resolve a BPMN structural gap (BJ11-BJ16)
4. Its answer would complete a `subject_trace` (`trace.completeness != "complete"`)
5. It addresses a decision condition (`resolves.field` starts with `"gateway_anatomy"`)

Questions that fail all 5 criteria are saved to `findings.json` but excluded from the PPTX and marked `quality_gate_passed: false`.

---

### Question format rules

- Reference their own words where possible ("You mentioned X, can you tell me...")
- Ask for exactly what's missing (a number, a name, a process step)
- Frame around their experience ("How long does that typically take?" not "What is the duration?")
- Compound questions (4c merges) may include a bullet list. All other questions are single-focus
- **Never use em dashes (`—`).** Use a comma, a colon, or rewrite. Em dashes read as AI-generated in client-facing output
- **Never ask about pay.** No question may probe hourly rate, salary, wage, bonus value, or any per-staff dollar amount. The audit assumes $50/hr blended for everyone

### Deduplication

Before adding each question to the audit data:
- Check existing `follow_up_questions[]` for semantic matches (not just string matches)
- If a matching question exists with `status: "pending"`, skip. Don't create a duplicate
- If a matching question exists with `status: "answered"` or `"researched"`, skip. It's already resolved
- Assign `fq_id` continuing from the highest existing FQ-NNN

### Tag each question

Set on each new audit data entry:
```json
{
  "fq_id": "FQ-042",
  "question": "After the quote is reviewed by the office manager, what determines whether it goes to the director for sign-off or goes straight to the client? Is there a dollar threshold or another criteria?",
  "priority": "HIGH",
  "resolution_target": "DOWNSTREAM_CONDITION",
  "resolves": {
    "field": "gateway_anatomy.condition",
    "step_id": "QUO-D01",
    "process": "quoting_process"
  },
  "linked_gap_ids": ["GAP-003"],
  "merged_question": false,
  "constituent_gap_ids": [],
  "quality_gate_passed": true,
  "category": "client_required",
  "status": "pending",
  "slide_group": "quoting_process"
}
```

**Existing fields (preserved):** `fq_id`, `question`, `priority`, `category`, `status`

**New fields:** `resolution_target`, `resolves`, `linked_gap_ids`, `merged_question`, `constituent_gap_ids`, `quality_gate_passed`, `slide_group`

Also set:
- `deliverable_impact`: array of which deliverables this question affects: `["waste"]`, `["findings"]`, `["process_map"]`, or combinations
- `pptx_text`: a rewritten version of `question` for presentation use. Apply these rules:
  - Plain language. Would a 5-year-old understand it?
  - No jargon, no acronyms without explanation
  - **Conversational opener required.** Every `pptx_text` must start the way a human would ask the question on a call: "Walk me through...", "Roughly how long...", "Roughly how often...", "Who tends to handle...", "How does that usually...", "Tell me a bit about...". Avoid "What is...", "Provide...", "Specify...", "Please confirm...", "State the..." and any other analyst phrasing
  - **No em dashes anywhere in `pptx_text`.** Use commas, colons, parentheses, or a rewrite. This is client-facing copy and em dashes read as AI-generated
  - **No questions about pay.** `pptx_text` must never mention hourly rate, salary, wage, bonus value, or any individual staff member's pay
  - Reference what the client said where possible ("You mentioned X, roughly how often does that happen?")
  - No internal IDs (FQ-001, W-001, audit-data.json etc.)

**`slide_group` mapping:** Set to the `affected_process` value from the gap (e.g., `"quoting_process"`, `"onboarding_process"`). This replaces the old category-based mapping and groups PPTX slides by process area.

**Legacy `slide_group` values** (used when falling back to original question generation logic):
- `"volumes_frequency"`: "how many per week/month", "how often", volume multipliers
- `"time_estimates"`: "how long does X take", per-task durations
- `"revenue_financial"`: revenue figures, conversion rates, financial loss data
- `"process_clarification"`: process steps, decision branches, tool usage, handovers, BPMN gaps

The legacy `"costs_rates"` group is retired: we no longer collect staff cost or rate data from clients.

---

## Step 5: Classify & Research

Apply the classification and research logic below.

### Classification rules

**researchable**, answer findable via web search:
- Names a specific tool, API, platform, or software product
- Asks about pricing, features, integrations, or technical capabilities
- Asks about regulatory or compliance information publicly available
- Asks about industry benchmarks or publicly available data

**client_required**, only the client can answer:
- Asks about their specific internal process, timing, or headcount
- Asks about business decisions, preferences, or future plans
- Asks about revenue figures, conversion rates, or top-line financial metrics (not staff pay, which is out of scope)
- Asks about specific staff roles, names, or responsibilities
- Asks about how they personally use a tool (not what the tool can do)

### Research (for researchable questions)

Use `mcp__exa__web_search_exa` with API research discipline:
- For API questions: capture specific endpoints, HTTP methods, parameters, documentation URLs
- Confidence: HIGH = official docs with endpoints, MEDIUM = confirmed via third-party, LOW = no docs found
- Set `status: "researched"`, `research_answer`, `research_confidence`, `research_sources`, `researched_at`

**Skip** any questions already classified or researched from a prior GQ run.

---

## Step 6: Export Follow-Up PPTX

Generate a branded PowerPoint for the next session. This replaces the email export. No email is generated.

### 6a. Determine session folder

From `extraction.json` (or `audit-data.json` for v2/v3), get the latest session entry:
- `session_date` → the date component (YYYY-MM-DD)
- `sessions[].label` → slugify this for the folder name. If no label, use the first entry in `stages_covered[]` slugified
- Folder name: `{YYYY-MM-DD}-{label-slug}` (e.g., `2026-05-25-tendering`)
- Full path: `clients/{client_slug}/03-audit/sessions/{folder}/`

### 6b. Build questions-input.json

Write this JSON to `clients/{client_slug}/03-audit/sessions/{folder}/questions-input.json`:

```json
{
  "company_name": "{meta.company_name}",
  "contact_name": "{meta.contact.name or ''}",
  "session_number": {latest session_number or sessions_completed},
  "session_date": "{latest session date, YYYY-MM-DD}",
  "session_label": "{latest session label slugified}",
  "sessions_completed": {sessions_completed count},
  "session_recap": [
    {
      "label": "{stage name or key finding label, plain English}",
      "detail": "{one sentence describing what was discovered, plain language, no jargon}"
    }
  ],
  "question_groups": [
    {
      "title": "{group display name, see mapping below}",
      "subtitle": "{one sentence in plain language explaining why we need this group, optional, omit if obvious}",
      "questions": [
        {
          "number": {sequential across all groups},
          "text": "{pptx_text from audit data, simplified, plain language}",
          "context": "{one-line note on what this unlocks, or empty string}"
        }
      ],
      "gate_items": ["{the specific data point each question needs, extracted from reason field, plain noun phrases}"]
    }
  ],
  "researched_questions": [
    {
      "question": "{plain language version of the researched question}",
      "answer": "{research_answer, brief, factual}",
      "source": "{first research_source URL or domain}"
    }
  ]
}
```

**Group title mapping:**

When `slide_group` is a process area slug (e.g., `"quoting_process"`, `"onboarding_process"`): convert to title case and drop `_process` suffix for the display title (e.g., `"quoting_process"` → "Quoting", `"onboarding_process"` → "Onboarding").

When using legacy fallback `slide_group` values:

| slide_group | Title |
|-------------|-------|
| `costs_rates` | "Costs & Rates" |
| `volumes_frequency` | "Volumes & Frequency" |
| `time_estimates` | "How Long Things Take" |
| `revenue_financial` | "Revenue & Financial Data" |
| `process_clarification` | "Process Clarification" |

**Group rules:**
- Only include groups that have at least one gate-passed, client-required pending question
- Omit empty groups entirely
- Number questions sequentially across all groups (1, 2, 3... not restarting per group)
- Context line: include for HIGH priority questions only. One sentence max.
- Gate items: extract the specific noun phrases from each question's `reason` field. 3-6 items per group. Plain language, no jargon, no IDs.

**session_recap rules:**
- Pull from `sessions[latest].key_findings` if available, otherwise summarise from `stages_covered[]`
- 4-8 bullet points maximum
- Each point: bold label (2-4 words) + plain-English detail sentence
- No fancy lingo, no acronyms without explanation

### 6c. Run the PPTX script

```bash
python3 {project-root}/apg-audit-plugin/scripts/generate_follow_up_pptx.py \
  --client-slug {client_slug} \
  --session {latest_session_number} \
  --questions-json clients/{client_slug}/03-audit/sessions/{folder}/questions-input.json
```

Verify the PPTX was created at `clients/{client_slug}/03-audit/sessions/{folder}/follow-up-questions.pptx`.

### 6d. Clean up

Delete `questions-input.json` after successful PPTX generation.

---

## Step 7: Save & Summarise

1. Write all new/updated `follow_up_questions[]` back to the audit data. For v4 clients: write the full `findings.json` with updated `follow_up_questions` and `follow_up_summary`, then update `audit-manifest.json` (`domains.findings.updated_at` and root `updated_at`). For v3 files: write into `findings.follow_up_questions` and `findings.follow_up_summary`. For v2 files: write to top-level keys as before.

2. Display combined report:

```
GENERATE QUESTIONS COMPLETE: {company_name}
══════════════════════════════════════════════════════════════

DELIVERABLE READINESS
  waste.html:       {n}/{total} items fully quantified ({pct}%)
  findings.html:    {status: "ready" or "{n} stages with no findings"}
  process-map.html: {pct}% tool coverage, {pct}% data flow coverage

OPPORTUNITY QUANTIFICATION GAPS
  Missing hours/week:           {n}
  Missing headcount:            {n}
  Revenue leakage unquantified: {n}

TRANSCRIPT CROSS-REFERENCE
  Found in transcripts:  {n} (extraction gaps, re-run SU)
  Discussed not answered: {n}
  Not found:             {n}

QUESTIONS
  New generated:    {n}
  Gated out:        {n} (did not meet quality gate, saved but excluded from PPTX)
  Researched (exa): {n}
  Client-required:  {n} (in PPTX)
  Total pending:    {n}

Exported: clients/{client_slug}/03-audit/sessions/{folder}/follow-up-questions.pptx

Next steps:
  1. Review the PPTX and share with {contact.name or "the client"} if it's ready
  2. Use it to structure the next session conversation
  3. After receiving answers, run [SU] to re-extract and then [GQ] to check remaining gaps
```
