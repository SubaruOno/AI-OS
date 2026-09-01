---
name: resolve-questions
description: Deep-search all client materials using parallel sub-agents to find answers to pending follow-up questions. Presents findings for approval before modifying audit-data.json.
menu-code: RQ
---

# Resolve Questions

## Purpose

Many pending follow-up questions are actually already answered somewhere in the client's materials — a transcript session that touched on it obliquely, an email thread where the client stated a number, a Loom recording where they showed a specific tool. SU extraction focuses on what's new in each session; it doesn't look back at pending questions. GQ does shallow Grep which misses semantically equivalent answers.

This capability dispatches parallel sub-agents across all available materials and searches each one specifically against the pending FQ list. It surfaces what was already said but not captured, presents findings for your review, and updates audit-data.json with approved answers plus any supplementary data enrichment (rates, metrics, waste recalculations).

Nothing is modified until you approve.

---

## Pipeline

Run all stages autonomously. Pause only at Stage 6 for approval.

---

### Stage 1 — Load and Filter FQs

Check for `audit-manifest.json` in `clients/{client_slug}/03-audit/data/`. If present, this is a v4 client: read `clients/{client_slug}/03-audit/data/meta.json`, `clients/{client_slug}/03-audit/data/extraction.json`, and `clients/{client_slug}/03-audit/data/findings.json` directly. If `audit-manifest.json` does not exist, fall back to reading `audit-data.json` as v3/v2.

Identify all pending FQs using schema-aware logic:
- **Canonical schema:** `answered == false` (and `status` not in ["answered", "researched"] if status field exists)
- **Alt schema (northwind-co style):** `status == "pending"`
- Skip any FQ that has `answered: true`, `status: "answered"`, or `status: "researched"`

For ID resolution: use `fq.fq_id` if present, otherwise `fq.question_id`, otherwise `FQ-anon-{index}`.

Display the opening inventory:

```
RESOLVE QUESTIONS — {company_name}
══════════════════════════════════════════════════════
Total FQs:      {total}
  Pending:      {n}  (HIGH: {n} / MEDIUM: {n} / LOW: {n})
  Answered:     {n}
  Researched:   {n}
══════════════════════════════════════════════════════
```

If zero pending FQs, stop: "No pending questions to resolve. All FQs are answered or researched."

Store pending FQs as `{pending_fqs}`. Include these fields for each: `fq_id` (or `question_id`), `question`, `stage`, `priority`, `category` (or `classification`), `reason`.

---

### Stage 2 — Inventory Materials

Scan all material locations under `clients/{client_slug}/`:

**Transcripts:** `meetings/*/transcript.txt`
**Emails:** `01-materials/documents/emails/*/email.txt`
**Calls:** `01-materials/documents/calls/*/transcript.txt`
**Loom transcripts:** `01-materials/documents/loom-transcripts/**/*.md`
**Other text:** `01-materials/documents/**/*.{txt,md}` (excluding `metadata.json`, files in `analysis/` subdirectory, `.gitkeep`)
**Extracted documents:** `01-materials/documents/**/*.{txt}` in `text/` subdirectories (extracted content from PDFs/DOCX)

Skip: binary files (.png, .jpg, .pdf, .docx, .xlsx, .ics), metadata.json, analysis outputs, .gitkeep.

For each eligible file, use `wc -c` to get byte size.

Display:

```
MATERIAL INVENTORY
──────────────────────────────────────────────────
  Transcripts:      {n} files ({total_kb} KB)
  Emails:           {n} threads ({total_kb} KB)
  Calls:            {n} files ({total_kb} KB)
  Loom transcripts: {n} files ({total_kb} KB)
  Other materials:  {n} files ({total_kb} KB)
  Audit data self:  (processes, metrics, waste — internal search)
  ──────────────────────────────────────────────
  Total:            {n} files / {total_kb} KB
──────────────────────────────────────────────────
```

---

### Stage 3 — Build Batch Plan

Partition all materials into sub-agent batches targeting ~80 KB of source text each. This leaves room in each sub-agent's context for the instruction prompt (~15 KB) and the FQ list.

**Batching rules:**
1. Files larger than 40 KB get their own dedicated agent
2. Files between 5–40 KB are grouped together up to the 80 KB cap
3. Files smaller than 5 KB are bundled aggressively — pack as many as fit
4. Always add one "self-search" batch: the relevant sections of audit-data.json itself (processes, pain_points, optimisations, waste_items, business_metrics, staff_roster, contradictions — not meeting_references, data_flow, crm, or deliverable sections). This finds answers already extracted but not linked to FQs.

Assign a `batch_id` to each batch (batch-1, batch-2, …, batch-self).

Display:

```
BATCH PLAN — {n} sub-agents (running in parallel)
──────────────────────────────────────────────────
  {batch_id}: {description} ({total_kb} KB)
  ...
  batch-self: Audit data self-search (internal)
──────────────────────────────────────────────────
  Searching {n} pending FQs across {total_kb} KB
```

---

### Stage 4 — Dispatch Sub-Agents (Parallel)

Load the full content of `{project-root}/apg-audit-plugin/skills/3-audit-extractor/sub-agent-resolve.md` as `{sub_agent_instructions}`.

Build the pending FQ list as a compact JSON array. Include only: `fq_id` (or `question_id`), `question`, `stage`, `priority`, `reason`. Strip research fields and long quotes to keep the list compact.

**For each batch, build the material block:**

Read each file in the batch and concatenate with file-path delimiters:

```
=== FILE: {relative_path_from_client_root} ===
{file_content}

```

For the self-search batch, extract only these sections from audit-data.json: `processes`, `pain_points`, `optimisations`, `waste_items`, `business_metrics`, `staff_roster`, `contradictions`. Present them clearly labeled.

**Dispatch all sub-agents simultaneously** using the Agent tool:

```
Agent({
  description: "RQ {batch_id} — {batch_description} — {client_slug}",
  model: "sonnet",
  prompt: [sub_agent_instructions]
    .replace("{batch_id}", batch_id)
    .replace("{pending_fq_list}", JSON.stringify(pending_fqs))
    .replace("{batch_materials}", material_block)
})
```

Collect all results as they complete. If a sub-agent returns malformed JSON or fails, mark that batch as `parse_error` and continue — do not let one failed batch block the others.

---

### Stage 5 — Merge and Deduplicate Findings

Group all `fq_findings` from all batches by FQ ID.

For each FQ with findings from multiple batches:

**Verdict priority:** `answered` > `partial` > `context_only`

**Confidence priority:** `HIGH` > `MEDIUM` > `LOW`

**Merge rules:**
- If multiple batches return `answered` for the same FQ, keep the highest-confidence one as the primary finding. Note corroboration: "Confirmed in {n} sources."
- If one batch returns `answered` and another returns `partial`, use the `answered` finding as primary, note the partial as supporting evidence.
- If multiple `partial` findings together constitute a complete answer (e.g., one gives a count, another gives a rate that together enable the calculation), promote to `answered` with your combined reasoning.
- `context_only` findings are noted in the summary but do not upgrade an FQ's status.

Collect all `opportunistic_findings` from all batches into a single deduplicated list. Remove opportunistic findings that duplicate data already in the main FQ findings.

Track failed batches separately for reporting.

---

### Stage 6 — Present Findings for Approval

Display the full findings summary, grouped by verdict. Include enough context for each finding that you can judge it without re-reading the source.

```
FQ RESOLUTION FINDINGS — {company_name}
══════════════════════════════════════════════════════════════

LIKELY ANSWERED ({n})
──────────────────────────────────────────────────────────────
{fq_id}: "{question}"
  Answer:     {answer_text}
  Confidence: {confidence}
  Source:     {source_file} — {source_speaker} {source_timestamp}
  Quote:      "{source_quote}"
  {if corroborated} Also found in: {other_source_files}
  {if supplementary_updates} Also updates: {comma-separated target_section descriptions}

  [approve / reject / edit]

...

PARTIALLY ANSWERED ({n})
──────────────────────────────────────────────────────────────
{fq_id}: "{question}"
  Partial:    {answer_text}
  Confidence: {confidence}
  Source:     {source_file} — {source_speaker}
  Quote:      "{source_quote}"

  [mark partial / reject]

...

CONTEXT FOUND — NOT ANSWERED ({n})
──────────────────────────────────────────────────────────────
{fq_id}: "{question}"
  Context: {answer_text}
  (Noted only — FQ remains pending)

...

NOT FOUND ({n})
──────────────────────────────────────────────────────────────
{comma-separated list of fq_ids and their questions}

══════════════════════════════════════════════════════════════

OPPORTUNISTIC FINDINGS ({n}) — data found beyond the FQ list
──────────────────────────────────────────────────────────────
{index}. {type}: {description}
   Source: {source_file} — "{source_quote}"
   Confidence: {confidence}

...

{if failed_batches} FAILED BATCHES: {batch_ids} (parse error — those materials were not searched)

══════════════════════════════════════════════════════════════
```

**Pause.** Ask:

"Review the findings above. Reply with your approval instructions, for example:
- **APPROVE ALL** to accept all LIKELY ANSWERED and PARTIALLY ANSWERED findings
- **APPROVE FQ-005, FQ-012** to approve specific items
- **REJECT FQ-019** to skip specific items
- **EDIT FQ-012: [corrected answer]** to modify the proposed answer before saving
- **APPROVE OPPORTUNISTIC 1, 3** to apply specific opportunistic findings
- Or any combination of the above

Items you do not mention will be skipped."

---

### Stage 7 — Apply Approved Changes

Parse the approval instructions. For each approved finding, apply changes to the in-memory copy of audit-data.json.

**Updating FQ entries (schema-aware):**

Locate the FQ by matching `fq_id` or `question_id`. Then:

- If FQ has `answered` field: set `answered: true`
- If FQ has `status` field: set `status: "answered"` (or `"partial"` if verdict is `partial`)
- If FQ has `answered_in_session` field: set `answered_in_session: "materials_review"`
- Set `answer: "{final_answer_text}"` — combine `answer_text` with source attribution: `"{answer_text} — {source_speaker}, {source_file}{source_timestamp}"`
- For `partial` verdicts: prefix answer with `PARTIAL — ` to signal it needs confirmation

**Applying supplementary updates:**

For each approved finding with `supplementary_updates`:

- `business_metrics`: find existing entry by name match or create a new entry. Update `current_value`, `unit`, `source_session` (set to `"materials_review"`), `confidence`. Recalculate `annual_value` where applicable.
- `staff_roster`: find existing entry by name or role match. Update role, responsibilities, or headcount. Never update pay fields. Staff pay is out of scope.
- `waste_items`: if confirmed hours or headcount data was found, recalculate `annual_waste_aud` using the canonical $50/hr blended rate. Add a `calculation_note` suffix: " [Hours updated, materials_review {today's date}]"
- `blended_hourly_rate_aud`: fixed at $50/hr by convention, never recalculated.

**Applying opportunistic findings:**

For each approved opportunistic finding:
- `business_metric`: create or update entry in `business_metrics[]`
- `staff_update`: update `staff_roster[]` entry
- `tool_detail`: update matching `tools[]` entry (plan/cost/seats)

**Update follow_up_summary:**

Recalculate and update the `follow_up_summary` object:
```json
{
  "total_count": {total},
  "by_priority": {"HIGH": n, "MEDIUM": n, "LOW": n},
  "by_stage": {stage: count, ...}
}
```
Count only FQs that remain pending after this update.

For v4 clients: write the full `findings.json` with updated `follow_up_questions` and `follow_up_summary`; write any updated staff_roster or blended rate to `meta.json`; write any updated business_metrics to `extraction.json`; then update `audit-manifest.json` for each changed domain (`domains.{domain}.updated_at`) and set root `updated_at`. For v3 files: write updated follow_up_questions into `findings.follow_up_questions` and `findings.follow_up_summary`; write any updated staff_roster or business_metrics into the `meta` or `extraction` domain as appropriate. For v2 files: write to top-level keys as before.

**Save audit-data.json.**

**Run validation:**

```bash
python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py --file clients/{client_slug}/03-audit/data/audit-data.json
```

If validation fails with HIGH or CRITICAL findings, show the errors and stop — do not leave the file in a broken state. Revert affected changes if possible.

**Display final summary:**

```
RESOLVE QUESTIONS COMPLETE — {company_name}
══════════════════════════════════════════════════════
  FQs resolved:        {n} answered  +  {n} partial
  FQs still pending:   {n}  (HIGH: {n} / MEDIUM: {n} / LOW: {n})
  Waste recalculated:  {n} items  (new total: ${annual_total}/yr)
  Business metrics:    {n} added / {n} updated
  Staff rates:         {n} confirmed
  Opportunistic:       {n} enrichments applied
  Validation:          {PASS / FAIL}
══════════════════════════════════════════════════════
{if remaining_high_priority_fqs}
Remaining HIGH priority FQs:
  {fq_id}: {question}
  ...
{endif}
Recommended next step: {GQ to generate client email with resolved FQs | SU if a new session was recorded}
```
