---
name: ingest-materials
description: Systematically process all files in 01-materials/documents/ and extract structured data into the audit domain files. Handles large volumes in batches. Idempotent — already-processed files are skipped.
menu-code: IM
---

# Ingest Materials

## Purpose

Dedicated deep-extraction capability for client-provided materials. While SU does a lightweight scan of `01-materials/documents/` as part of its broader pipeline, IM is purpose-built for bulk ingestion: it runs the full 4-pass extraction model on every material, processes in batches of 6–8 units, saves after each batch, and is safe to interrupt and resume.

Use IM when a client sends a large batch of materials (shared Drive folder, ZIP archive, Loom training library) that warrants thorough, structured extraction. Running both SU and IM on the same client is safe — both use `extracted_materials[]` for idempotency.

Every finding gets a confidence score and a source path. Every gap becomes a data gap or follow-up question.

---

## Pipeline

Client slug is already set from activation (`{client_slug}`). Run all stages autonomously unless the batch count exceeds 20 units (in which case, present the batch plan and ask for confirmation before proceeding).

---

### Stage 1 — Inventory

Recursively scan `clients/{client_slug}/01-materials/documents/` for all files.

For each file found, determine its status:

1. **Check `extracted_materials[]`** in `audit-data.json` — if any entry has a matching `source_file` field → **DONE**
2. **Check auto-skip rules** (see below) → **SKIP**
3. Otherwise → **UNPROCESSED**

**Auto-skip rules:**

| Pattern | Reason |
|---------|--------|
| `*.ics` | Calendar invite — no audit data |
| `*.zip` | Archive — process extracted contents instead |
| `*/analysis/*.md`, `*/analysis/*.txt` | APG-generated analysis output — not raw client material |
| `*/text/*.txt` | Converted text version — prefer binary original. Exception: if the corresponding binary was deleted, process the `.txt` and note it as a converted version. |
| `metadata.json` inside `emails/` subdirectories | Processed as part of the email folder unit, not standalone |
| `.gitkeep` | Placeholder file |
| `*.gif` inside `emails/` directories | Email signature animation |
| `image*.png`, `image_*.png` inside `emails/` directories | Likely email inline image or signature. Exception: if filename implies real content (e.g. `offboarding-checklist.png`, `process-flow.png`), mark as UNPROCESSED instead. |

**Email folder grouping:** All files inside an `emails/{folder-name}/` directory are grouped as a single material unit. Do not list them individually — list the folder name once.

Print inventory table:

```
MATERIALS INVENTORY — {company_name}
───────────────────────────────────────────────────────────
  Material                                     Type             Status
  ───────────────────────────────────────────  ──────────────  ──────────
  emails/2026-04-21-thanks-adam/               email            DONE
  emails/2026-04-22-audit-of-bookings-inbox/   email            UNPROCESSED
  loom-transcripts/timely-01-staff-setup.md    loom_transcript  UNPROCESSED
  admin-folder-extracted/analysis/batch-1.md   analysis         SKIP
  Admin Folder/Staff Info - April 2026.docx    document         UNPROCESSED
  ...
───────────────────────────────────────────────────────────
  Unprocessed: {n}  |  Already done: {n}  |  Skipped: {n}
```

If no unprocessed materials: print "All materials already processed." and stop.

---

### Stage 2 — Batch Construction

Group unprocessed material units into batches of **6–8 units**. A "material unit" is:

- **Email folder**: The entire `emails/{folder}/` directory (email.txt + metadata.json + attachments) = 1 unit
- **Loom transcript**: One `.md` file = 1 unit
- **Standalone document** (`.docx`, `.pdf`, `.xlsx`, `.csv`, `.txt`, `.html`): 1 unit per file
- **Image with content value** (screenshots, process diagrams): 1 unit

**Grouping rules** — group by type/directory for coherence:
1. Email folders in chronological order (oldest first)
2. Loom transcripts grouped by tool series (all `timely-*` together, all `invoicing-*` together, all `pinch-*` together)
3. Documents from the same directory together
4. Standalone files and remaining items last

**Batch plan display:**

```
BATCH PLAN — {n} unprocessed material units
─────────────────────────────────────────────
  Batch 1/{total}: Emails (8 email folders)
  Batch 2/{total}: Loom Transcripts — Timely series (8 files)
  Batch 3/{total}: Loom Transcripts — Invoicing series (8 files)
  Batch 4/{total}: Admin Folder Documents (6 files)
  ...
─────────────────────────────────────────────
```

- **≤20 units**: Proceed automatically.
- **>20 units**: Present batch plan and ask "Proceed with all {n} batches? [Y / select batch numbers / STOP]"

---

### Stage 3 — Build Context Packet

Before dispatching sub-agents, build a lightweight context packet from the current `audit-data.json` following the same approach as SU Stage 3. Include existing stage keys, ID sequences, tool names, blended rate, sessions summary, and pain point summaries.

Check for `audit-manifest.json` in `clients/{client_slug}/03-audit/data/`. If present, this is a v4 client: read `clients/{client_slug}/03-audit/data/meta.json` and `clients/{client_slug}/03-audit/data/extraction.json` directly to build the context packet. If `audit-manifest.json` does not exist, fall back to reading `audit-data.json` as v3/v2.

Also load or update the ingestion manifest at `clients/{client_slug}/03-audit/data/ingestion-manifest.json` — add any new material files discovered in Stage 1 with `status: "pending"`.

**Context packet lifecycle:** The packet is built once before each batch and shared identically across all sub-agents in that batch. After the batch's sequential merge completes (Step C-merge), rebuild the packet from the updated audit data before dispatching the next batch. Sub-agents within a batch may produce overlapping IDs — the sequential merge resolves these via auto-increment. Never pass a stale packet from a previous batch to a new batch.

---

### Stage 4 — Per-Batch Sub-Agent Extraction

IM uses two levels of parallelism to maximise throughput:

**Level 1 — Inter-batch (batch-to-batch):**
- **Parallel by default** when consecutive batches are unrelated (different directories, different content types, different tool domains).
- **Sequential only** when batches form a related series requiring cross-file contradiction detection: e.g., `timely-01` through `timely-08` and `timely-09` through `timely-16` are one series; chronological email threads from the same sender on the same topic are a series.
- When in doubt, treat as sequential. The BATCH PLAN display (Stage 2) should annotate series vs independent batches so the rule is clear at dispatch time.

**Level 2 — Intra-batch (within a single batch):**
- After the parent reads all material content (Step A) and classifies audit value (Step B), dispatch sub-agents for all medium/high-value units in the batch simultaneously in a single Agent call (Step C).
- Cap parallel dispatch at 6 sub-agents. If a batch has more than 6 units, dispatch 6 first, wait for all to return and merge, then dispatch the remainder.
- All sub-agents in the same batch receive the SAME context packet. They may produce overlapping IDs — this is expected and resolved by the sequential merge (Step C-merge).

**Merge ordering within a batch:** After all sub-agents return, merge their results in chronological order by material date (oldest first) for deterministic ID assignment. Rebuild the context packet after each individual merge before the next merge begins.

#### Step A — Read Material Content (Parent Agent)

Before dispatching, the parent reads all file contents in the batch:

Detect type and read using the appropriate method:

| Material Type | Reading Approach |
|--------------|-----------------|
| **Email folder** (`emails/{folder}/`) | Read `metadata.json` first (sender, subject, date, attachments). Then read `email.txt`. Then read each non-image, non-ics attachment in the folder. Hold all in context as one unit. |
| **Loom transcript** (`.md` in `loom-transcripts/`) | Direct Read. Content is already structured step-by-step. |
| **PDF** (≤20 pages) | Read tool with PDF support. |
| **PDF** (>20 pages) | Read pages 1–5 first. If content-dense, continue with 6–15, then 16–20. Max 3 reads. Note remaining pages in `data_gaps[]`. |
| **Word doc** (`.docx`) | Read directly. If Read fails, check for `text/` sibling. |
| **Spreadsheet** (`.xlsx`, `.xlsm`, `.csv`) | Read directly. If Read returns binary/error, check for `text/` sibling. If no sibling, log `data_gaps[]` entry: "Spreadsheet unreadable: {filename}". |
| **HTML** (`.html`) | Direct Read. Parse for process steps, flowchart sequences. |
| **Standalone text** (`.txt` outside `emails/`) | Direct Read. |
| **Image** (`.png` with content-relevant filename) | Read with vision. Caption visible process info. |

#### Step A.1 — Capture External Source URLs (Parent Agent)

For every material unit, also capture its **external source URL** so each extracted item can link back to the original — not just the local file path. The URL is passed to the sub-agent in Step C and ends up in `sources[].source_url` on every emitted item.

| Material Type | Where the URL lives | Pattern to extract |
|--------------|--------------------|-------------------|
| **Loom transcript** (`.md`) | Frontmatter or first 30 lines of the file | `https://www.loom.com/share/{id}` or `https://www.loom.com/embed/{id}` |
| **Email folder** | `metadata.json` → `gmail_thread_url` / `permalink` / `message_url` (first key present wins) | Whatever URL is stored |
| **PDF / DOCX / XLSX** | Usually no external URL — leave unset | — |
| **HTML** (e.g. exported flowcharts) | `metadata.json` if present, or `<meta canonical>` tag in the HTML | First explicit URL found |
| **Image** | Usually no external URL — leave unset | — |

If no URL is found, leave the field unset on emitted items — `source_url` is optional. The local `document_path` still provides a clickable link via the rendered HTML in `deliverables/materials/`.

#### Step B — Classify Audit Value (Parent Agent)

**All material types** are classified using the three-category source taxonomy before dispatch:

- **process_relevant**: directly describes how work is done (step-by-step). Meeting transcripts where the client walks through their process. Procedure documents. Workflow descriptions. Loom training walkthroughs.
  → Route to: full extraction sub-agent (Steps C–D)
- **context_relevant**: provides background, numbers, or constraints but does not describe process steps. Company overview, pricing schedule, staff list, metric reports, email threads about a specific problem but not the process behind it.
  → Route to: lightweight context extraction only (populates new_business_metrics[], staff_updates[], tool_updates[] — no steps)
- **noise**: logistics, signatures, calendar invites, acknowledgements, spam, document headers/footers.
  → Route to: skip. Log in ingestion manifest as status: "skipped", skip_reason: "noise"

**For documents over 5000 words:** classify at chunk level (2000-word chunks). Only process_relevant chunks go to full extraction. Context_relevant chunks are combined into a single context brief (summary only). Log skipped chunks in the ingestion manifest with chunk reference.

**Email folders specifically:**

- **Low value / noise**: Calendar accept/decline, meeting logistics, no business content in body or attachments → classify as **noise**. Log as processed with `extracted: ["Meeting logistics: {subject}"]`. Do NOT run extraction.
- **Context only**: Substantive email threads about a problem, question, or status update but no process steps described → classify as **context_relevant**.
- **Medium/High value**: JDs, process descriptions, forwarded docs, workflow attachments, substantive threads with step-by-step content → classify as **process_relevant**. Proceed to Step C.

#### Step C — Parallel Sub-Agent Dispatch

Dispatch sub-agents (model: sonnet) for all medium/high-value units in the batch simultaneously in a single Agent call (up to the 6-agent ceiling). Each sub-agent receives:
- Full content of `sub-agent-extract.md` (the extraction schema)
- Full content of `references/bpmn-examples.md` (gold-standard BPMN examples — match this quality bar)
- The context packet built in Stage 3 — identical for all sub-agents in this batch
- Its specific material content read in Step A
- Source metadata: type, path, date, null session_number, null fathom_meeting_id
- **External source URL** captured in Step A.1 (Loom share URL, Gmail thread URL, etc.) — to be propagated onto every `sources[]` document entry as `source_url`. Omit the field if no URL was captured.

Wait for all sub-agents in the batch to return before proceeding to Step C-merge.

#### Step C-merge — Sequential Merge of Parallel Results

Sort the returned results by material date (oldest first). Then merge each result sequentially following `merge-extraction.md`:

1. Merge result #1 → checkpoint save → rebuild context packet (Step 17 of merge-extraction.md)
2. Merge result #2 → checkpoint save → rebuild context packet
3. Continue until all results for this batch are merged.

**ID collision handling:** Sub-agents sharing the same context packet may allocate the same IDs (e.g., two sub-agents both emit PP-026). The existing auto-increment logic in `merge-extraction.md` Steps 3, 5, 6, 7, 9, 10, and 12 handles this correctly during sequential merge — no changes needed.

**Failure isolation:** If one sub-agent fails (JSON parse error, source attribution gate rejection), mark that unit as `failed` in the ingestion manifest and continue merging the remaining successful results. A single failure does not block the batch.

After all merges for the batch complete, update the ingestion manifest status for all processed units.

The 4-pass extraction model used within the sub-agent covers the same passes documented below for reference. These are now executed by the sub-agent, not the parent.

**CRITICAL provenance rules for ALL extracted items:**
- `source_material`: `"01-materials/documents/{relative path from client folder}"` — the path relative to the client slug root
- `source_session`: `null`
- `source_timestamp_seconds`: `null`
- `meeting_references`: `[]`
- `source_quote`: verbatim text from the material (not paraphrased)
- `confidence`: HIGH (explicitly stated) | MEDIUM (implied/inferable) | LOW (assumed, needs confirmation)

For items sourced from email attachments, also populate `email_references`:
```json
{
  "filename": "{attachment filename}",
  "subject": "{email subject from metadata.json}",
  "excerpt": "{relevant excerpt}"
}
```

---

##### Pass 1 — Process Steps, Pain Points, Staff & Constraints

Extract:
- Process steps (how they currently do things, step by step)
- Explicit and implied pain points
- Staff named, roles described, headcounts mentioned → update or create `staff_roster[]` entries
- Constraints: timing, compliance requirements, geographic limits
- Optimisations: things the client says they want to change or automate

**For Loom transcripts:** The content is already step-by-step structured. Each documented step is a genuine process step — extract directly, do not paraphrase.

**Decomposition rules (same as SU):**
1. Parallel inputs → `type: "parallel_group"` with `items[]`
2. Sequential actions → separate steps
3. Tool alternatives → `decision` node with branch steps
4. Branch-only steps → `"branch_only": true`

**Merging with existing data:**
- If a process step already exists in `processes[]` (same stage, same activity), **enrich** the existing step with new details from the material rather than creating a duplicate. Add the material reference to the step.
- If the material reveals a step not yet captured, create a new step in the appropriate stage's `steps[]` array.
- New pain points: assign sequential `pain_point_id` (continue from highest existing PP-NNN).

---

##### Pass 2 — Tools & Tech Stack

Same inclusion/exclusion criteria as SU:
- **Include**: Currently subscribed/licensed and in active use, paid for and operational
- **Exclude**: Not yet in use, under evaluation, hypothetical, auditor suggestions

For each tool found:
- **Already in `tools[]`**: Update `use_case` and `workarounds` fields if new information found. Note new source in the tool's description (do not overwrite — append).
- **New tool**: Create full `tools[]` entry with `source_material` set and `source_session: null`.
- **Borderline**: Add to `data_gaps[]` as "Tool mentioned but active use unclear: {tool_name}".

Map new process steps to tools via `tool_ids[]`.

---

##### Pass 3 — Time, Waste & Metrics

Extract all quantifiable signals:
- Hours/week, frequencies, volumes (top-line revenue dollars only)
- Business KPIs → add to `business_metrics[]` with `source_material` instead of `source_session`

> **Do not extract staff pay.** Pay rates, salaries, wages, and bonus amounts are out of scope. If a document or spreadsheet contains pay data, skip it. Do not update `staff_roster[]` pay fields, do not recompute a blended rate. The blended rate is fixed at `$50/hr` by convention.

**Waste items:** Add to `waste_items[]` with:
- `source_session: null`
- `source_timestamp_seconds: null`
- `meeting_references: []`
- `source_material: "{path}"`

For HIGH and MEDIUM confidence waste items with calculable hours, calculate `annual_waste_aud = hours_per_week × headcount_affected × 50 × 52` inline. The rate is always the canonical $50/hr blended team assumption, never a role-specific or extracted rate.

**Risk signals:** When material content implies revenue risk, compliance concern, or client-expressed fear → tag relevant `pain_points[]` entry with `risk_signal: true` + `risk_note`.

**Business metrics:** Extract to `business_metrics[]` with neutral framing — do NOT characterize as good or bad:
```json
{
  "metric_id": "KPI-NNN",
  "name": "...",
  "current_value": null,
  "unit": "...",
  "period": "...",
  "source_session": null,
  "source_material": "01-materials/documents/...",
  "source_quote": "verbatim"
}
```

---

##### Pass 4 — Contradictions & Data Gaps

Compare material content against existing audit-data.json:
- **Cross-source contradictions**: Does this material contradict what was said in a Fathom meeting session or in a previously-processed material? If yes → add to `contradictions[]` with `status: "unresolved"`.
- **Internal contradictions**: Does this material contradict itself (e.g. different figures on different pages)?

For contradictions sourced from materials, the `statement_a` or `statement_b` entry should use:
```json
{
  "session": null,
  "speaker": "{document author or email sender}",
  "quote": "verbatim from material",
  "timestamp_seconds": null,
  "meeting_id": null,
  "source_material": "01-materials/documents/..."
}
```

**Data gaps:** Things that should have been mentioned but weren't, or partially-described processes → add to `data_gaps[]`.

---

#### Step D — Record in `extracted_materials[]` (handled by merge-extraction.md)

After all passes for a material unit, append an entry:

```json
{
  "source_file": "01-materials/documents/{relative path or folder name}",
  "date": "{YYYY-MM-DD from metadata.json, file date, or document header}",
  "type": "email|pdf|document|loom_transcript|spreadsheet|flowchart|image|other",
  "from": "{sender email, document author, or 'Client-provided'}",
  "extracted": [
    "Short sentence per meaningful finding",
    "e.g. '5 process steps added to scheduling_rostering stage'",
    "e.g. 'Blended rate updated to $41.50 HIGH from contractor spreadsheet'"
  ]
}
```

**Email folder units:** Use the folder path as `source_file` (e.g. `01-materials/documents/emails/2026-04-22-audit-of-bookings-inbox/`). If an attachment contains substantially distinct content from the email body, create a separate `extracted_materials[]` entry for that attachment file.

**Low-value emails:** Still add an entry with `extracted: ["Low value — meeting logistics only: {subject}"]` so the file is marked as processed and skipped on re-runs.

**Duplicate detection:** If two files across different paths have the same filename and content (e.g. a flowchart HTML exists both as a standalone file and inside an email folder), process it once. Mark the second occurrence with `extracted: ["Duplicate of {first-path} — no new data extracted"]`.

---

### Stage 5 — Batch Save

After completing all units in a batch:

1. **Structural validation:**
   - All new `tool_ids[]` on steps reference existing tool names in `tools[]`
   - All new `pain_point_id` values are sequential and non-duplicate
   - All new `optimisation_id` values are sequential and non-duplicate
   - All new `extracted_materials[]` entries have `source_file` populated

2. **Run validator:**
   ```bash
   python3 scripts/validate_audit_data.py --file clients/{client_slug}/03-audit/data/audit-data.json --verbose
   ```
   Fix any CRITICAL or HIGH severity issues before saving.

3. **Save** audit data. For v4 clients: write the full `extraction.json` with new processes, tools, and extracted_materials; write the full `findings.json` with new pain_points, waste_items, and optimisations; then update `audit-manifest.json` (`domains.extraction.updated_at`, `domains.findings.updated_at`, and root `updated_at`). For v3 files: write new processes, tools, and extracted_materials into the `extraction` domain object in `audit-data.json`; write new pain_points, waste_items, and optimisations into the `findings` domain. For v2 files: write to top-level keys as before.

4. **Print batch summary:**

```
BATCH {n}/{total} COMPLETE — {company_name}
─────────────────────────────────────────────────────
  Materials processed:     {n} ({list types})
  Process steps:           {n} added | {n} enriched
  Pain points:             {n} added (risk-flagged: {n})
  Optimisations:           {n} added
  Waste items:             {n} added (${annual}/yr)
  Tools:                   {n} new | {n} updated
  Staff roster:            {n} new | {n} updated
  Business metrics:        {n} added
  Contradictions:          {n} flagged
  Data gaps:               {n} added
─────────────────────────────────────────────────────
  Progress: {done}/{total} material units complete
  Remaining batches: {n}
```

5. Proceed to next batch. If user types STOP, save current progress and halt.

---

### Stage 6 — Post-Ingestion Summary

After all batches complete:

```
MATERIALS INGESTION COMPLETE — {company_name}
══════════════════════════════════════════════════════

  Materials processed:       {n} / {total discovered}
  Materials skipped:         {n} (calendar invites, signatures, analysis files)
  Materials unreadable:      {n} (binary files — see data_gaps[])

  Cumulative Extraction:
    Process steps:           {n} added | {n} enriched
    Pain points:             {n} added (risk-flagged: {n})
    Optimisations:           {n} added
    Waste items:             {n} added (${total_annual_waste_aud}/yr)
    Tools:                   {n} new | {n} updated
    Staff roster:            {n} entries
    Business metrics:        {n} added
    Contradictions:          {n} flagged
    Data gaps:               {n} added

  Blended rate:              $50/hr (assumed, canonical)

══════════════════════════════════════════════════════

COVERAGE UPDATE:
  {For each stage in processes[]:}
  {stage_name}: {step_count} steps | {tool_coverage}% tool coverage

TOP DATA GAPS FROM MATERIALS:
  • {data_gap_description}
  • ...

Recommended next: [GQ] Generate Questions — cross-reference material findings against transcript data.
```

---

### Post-Extraction Housekeeping

After all passes across all batches:

1. **Pain points summary:** Recompute `pain_points_summary` — `total_count`, `by_stage`, `top_themes[]`.
2. **Optimisations:** Ensure every `type: "optimisation"` process step has a matching `optimisations[]` entry.
3. **Completeness checklist:** Update `completeness_checklist` coverage for any stages that gained new steps.

---

## Re-Run Behavior

IM is designed to be run multiple times safely:

- **Already processed**: Files with matching `source_file` in `extracted_materials[]` show as DONE and are skipped entirely.
- **New files**: Files added to `01-materials/documents/` since last run appear as UNPROCESSED and are picked up.
- **Partial runs**: If a previous run was interrupted after batch 3 of 7, re-running picks up at batch 4 (batches 1–3 files are marked DONE via their `extracted_materials[]` entries).
- **Existing audit data**: All existing data in `audit-data.json` is preserved. New extractions are merged in — no data is overwritten or deleted.

---

## Relationship to SU

SU is not replaced. The two are complementary:

- **SU** handles ongoing ingestion — the 1–3 new files that arrive between sessions. Its Stage 1e/2b does a quick scan and lightweight extraction.
- **IM** handles bulk onboarding — the 30–60 files from a shared folder or ZIP archive that warrant structured, batched, deep extraction.

Both use `extracted_materials[]` as the idempotency mechanism. A file processed by SU will show as DONE when IM runs, and vice versa.
