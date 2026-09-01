---
name: sync-and-update
description: Fetch new meetings and emails from CRM, scan client materials, build the ingestion manifest, then dispatch sub-agents to extract each unprocessed source. The one command to run after every session.
menu-code: SU
---

# Sync & Update

## Purpose

One command to run after every session. Fetches new meetings, emails, SMS, and calls from the CRM, scans client-provided materials for new files, then dispatches a focused sub-agent for each unprocessed source — one at a time, in chronological order. Each sub-agent extracts into structured JSON; the parent merges the results and checkpoints to disk after each one. Creates the audit data file from schema if it doesn't exist yet.

Every finding gets a confidence score and a verbatim quote. Every gap becomes a follow-up question.

## Source Attribution Gate — Hard Rule

> **Every extracted item (process step, pain_point, waste_item, optimisation, tool, staff role, decision node, business metric, constraint, strategic note, contradiction) MUST carry a `sources[]` array with at least one entry.**
>
> Each entry is a discriminated union by `kind`:
>
> ```jsonc
> {
>   "kind": "fathom" | "document",
>   "quote": "verbatim text",
>   "speaker": "Adam",                  // null OK only for documents without a clear author
>   "confidence": "HIGH" | "MEDIUM" | "LOW",
>   // kind == "fathom":
>   "session_id": 1,
>   "timestamp_seconds": 1422,
>   // kind == "document":
>   "document_path": "clients/{slug}/01-materials/documents/..."
> }
> ```
>
> 1. **Fathom meeting transcripts** → `kind: "fathom"`, with `session_id` and `timestamp_seconds`. Deep-links to the recording in client-facing renderers.
> 2. **Non-Fathom sources** (Loom transcripts, admin folder analyses, emails, docx text extracts) → `kind: "document"` with `document_path` relative to repo root. Renderers show a "View source" document button.
>
> **Retraction-as-success rule.** If a finding cannot be attributed (no verbatim quote, no identifiable speaker on Fathom, no clear timestamp, or no resolvable document path), the sub-agent MUST NOT emit the item. Instead, it emits a `new_follow_up_questions[]` entry with `category: "client_required"` so the consultant can re-ask next session. A retracted item is a successful extraction — it puts a follow-up question in front of the consultant.
>
> **Three-layer enforcement.** The gate runs at:
> 1. **Pre-emission (sub-agent prompt).** `sub-agent-extract.md` instructs the sub-agent to refuse and retract.
> 2. **Pre-merge (`validate_sub_agent_output.py`).** Runs against every sub-agent response in `merge-extraction.md` Step 1. Any empty `sources[]` aborts the merge for that source — no partial writes.
> 3. **Write-time (`audit_reader.save_domain()`).** Raises `CitationGateError` if any item in the payload still has an empty `sources[]`. Structurally impossible to commit an unattributed item.
>
> Rationale: the #1 client objection on the presentation is "where did you get this from?". Every downstream deliverable (findings.html, blueprint.html, waste.html, the comprehensive-report PDF, the prototype) renders these citations as either a "▶ Open recording at MM:SS" Fathom button or a "📄 View source: <filename>" document button. A finding without any attribution is a finding the client can reject — so it never reaches disk.

**Architecture:** Two parallelization layers: (1) Stage 1 data fetching dispatches 4 parallel sub-agents (meetings, SMS/calls, emails, filesystem scan) since they hit independent CRM endpoints and write to non-overlapping directories; (2) Stage 4 transcript extraction remains sequential — one sub-agent per source in chronological order — because each merge updates the context packet (ID sequences, dedup state) that the next sub-agent needs. Each extraction sub-agent has an isolated context window (~40-90KB vs the previous 300-500KB single window).

---

## Pipeline

Client slug is already set from activation (`{client_slug}`). Run all stages autonomously. Do not pause for user input between stages.

---

### Stage 1 — Parallel Data Fetch

**Prerequisite: Resolve `crm.contact_id`.** All CRM fetch sub-stages need the contact ID. Resolve it once before dispatching:

1. Read `crm.contact_id` from `meta.json`. If already set, proceed to parallel dispatch.
2. If not set, look it up:
   - `search_contacts(query: "{company_name}")` → store `contact_id` in `crm.contact_id`
   - If no match: `search_contacts(query: "{contact.emails[0]}")` → store `contact_id`
   - If still no match: warn and skip CRM-dependent fetch stages (1a, 1c, 1d). Stage 1e still runs.
3. Save `crm.contact_id` to `meta.json` immediately so parallel sub-agents share the resolved value.

**Parallel dispatch:** After contact_id is resolved, dispatch Stages 1a, 1c, 1d, and 1e as 4 parallel sub-agents in a single message. They hit independent CRM endpoints, write to non-overlapping directories, and have no data dependencies on each other.

Each sub-agent receives: `client_slug`, `crm.contact_id`, the clients directory path, and its stage-specific instructions from the relevant section below.

Wait for all 4 sub-agents to complete, then collect their status summaries and print the combined status tables before proceeding to Stage 2.

**Failure handling:** If any sub-agent fails, log a warning and continue with results from the others. A failed Stage 1a does not block 1c, 1d, or 1e. Print: `"⚠ {stage} fetch failed — proceeding with available data. Re-run SU to retry."`

---

### Stage 1a — Fetch CRM Meetings (parallel sub-agent)

Fetch new meetings via the APG CRM. See `references/mcp-integration.md` for full field details.

1. Call `list_contact_meetings(contact_id: "{crm.contact_id}")`. The full transcript is returned inline — no second call needed.
2. Scan existing `clients/{client_slug}/01-materials/meetings/*/metadata.json` files and collect all known `recording_id` values.
3. For each meeting whose `id` is NOT already saved as a `recording_id`:
   a. Transcript is inline in `transcript[]`. Each segment: `{text, speaker: {display_name}, timestamp: "HH:MM:SS"}`.
   b. Convert to transcript.txt format: for each segment, parse `HH:MM:SS` → `MM:SS` (drop the hours component if under 60 minutes, else keep `H:MM:SS`). Format as `[MM:SS] {speaker.display_name}: {text}`.
   c. Derive folder name: `{YYYY-MM-DD}-{title-slug}` from `started_at` date.
   d. Write `transcript.txt`:
      ```
      Meeting: {title}
      Date: {started_at}

      [00:00] Jordan Lee: Hi Adam.
      [00:04] Adam Goodyer: Good thanks.
      ```
   e. Write `metadata.json`:
      ```json
      {
        "recording_id": "{meeting.id}",
        "title": "{meeting.title}",
        "date": "{meeting.started_at}",
        "duration_seconds": {meeting.duration_seconds},
        "participants": [{"name": "{a.name}", "email": "{a.email}"} for a in meeting.attendees],
        "fathom_url": "{meeting.recording_url}",
        "share_url": "{meeting.recording_url}"
      }
      ```
   f. If video download is appropriate for this run: `yt-dlp -o "clients/{client_slug}/01-materials/meetings/{folder}/recording.mp4" "{meeting.recording_url}"`

Return a summary to the parent: list of meeting folders written, count of new vs already-saved recordings.

> **Parent-only steps (run in post-parallel reconciliation after all Stage 1 sub-agents complete):**
>
> 1. Rescan `clients/{client_slug}/01-materials/meetings/` for all subdirectories containing `transcript.txt`. For each, read its `metadata.json` to get `recording_id` (the CRM meeting UUID).
> 2. Check for `audit-manifest.json` in `clients/{client_slug}/03-audit/data/`. If present, v4 client: read domain files directly. If absent, fall back to `audit-data.json` as v3/v2.
> 3. **v4 bootstrap (no audit data exists yet):** If neither `audit-manifest.json` nor `audit-data.json` exist:
>    1. Create directory `clients/{client_slug}/03-audit/data/`
>    2. Copy `CLAUDE.md` from `references/schema-v4/audit-dir-claude.md` into the audit directory
>    3. Create `audit-manifest.json` from template at `references/schema-v4/01-manifest-schema.md`
>    4. Create all 6 domain files (`meta.json`, `extraction.json`, `findings.json`, `opportunities.json`, `strategy.json`, `architecture.json`) with empty structures
>    5. Populate `meta.json` with client details (slug, company name, contact)
> 4. **v4 write convention:** Write each domain's data to its own file. After writing domain files, update `audit-manifest.json`: set `domains.{domain}.updated_at` for each changed domain and set root `updated_at`.
> 5. Cross-reference meeting folders against `sessions[]` by `fathom_meeting_id`:
>    - **New** — folder exists, no matching session
>    - **Unanalyzed** — session exists with `analyzed: false`
>    - **Done** — session exists with `analyzed: true`
> 6. Print status table:
>    ```
>    MEETING SYNC — {company_name}
>    ─────────────────────────────────────────────────────
>      Folder                          Date        Status
>      ──────────────────────────────  ──────────  ──────────
>      {folder}                        {date}      NEW
>      {folder}                        {date}      UNANALYZED
>      {folder}                        {date}      DONE
>    ─────────────────────────────────────────────────────
>      New: {n}  |  Unanalyzed: {n}  |  Done: {n}
>    ```

---

### Stage 1b — Client Materials (Manual)

Google Drive files are managed manually by dragging files into `clients/{client_slug}/01-materials/documents/` via Drive for Desktop. No automated sync. Skip to Stage 1c.

---

### Stage 1c — Fetch CRM SMS and Calls (parallel sub-agent)

Fetch SMS messages and phone call transcripts via the APG CRM. These are supplementary data sources extracted as document-kind materials.

1. Call `list_contact_sms(contact_id: "{crm.contact_id}")`.
2. Scan existing `clients/{client_slug}/01-materials/documents/crm-sms/*/metadata.json` for known `sms_id` values.
3. For each SMS message not already saved:
   a. Derive folder name: `{YYYY-MM-DD}-sms` (group by date — all messages on same date go in one folder).
   b. Append to `sms.txt`: `[{sent_at}] {direction}: {body}`
   c. Write `metadata.json` with `sms_id`, `sent_at`, `direction`, `body`.
4. Call `list_contact_calls(contact_id: "{crm.contact_id}")`.
5. Scan existing `clients/{client_slug}/01-materials/documents/crm-calls/*/metadata.json` for known `call_id` values.
6. For each call not already saved:
   a. Transcript text is inline in the call log response. If not present, call `get_call_transcript(call_log_id: "{call.id}")` for the timed-segment version.
   b. Derive folder name: `{YYYY-MM-DD}-call-{index}`.
   c. Write `transcript.txt` formatted as `[HH:MM:SS] Speaker: text`.
   d. Write `metadata.json` with `call_id`, `started_at`, `duration_seconds`, `direction`.

Save to `clients/{client_slug}/01-materials/documents/crm-sms/` and `clients/{client_slug}/01-materials/documents/crm-calls/`. Stage 1e picks these up as unprocessed materials automatically.

Print status:

```
SMS SYNC — {company_name}
─────────────────────────────────────────────────────
  New messages: {n}  |  Already saved: {n}

CALL SYNC — {company_name}
─────────────────────────────────────────────────────
  New transcripts: {n}  |  Already saved: {n}
```

If no SMS or calls exist for this contact, print counts of zero and continue.

---

### Stage 1d — Fetch CRM Emails (parallel sub-agent)

Fetch emails via the APG CRM.

1. Call `list_contact_emails(contact_id: "{crm.contact_id}")`. Full body text is returned inline — no second call needed.
2. Scan existing `clients/{client_slug}/01-materials/emails/*/metadata.json` for known `email_id` values.
3. For each email not already saved:
   a. Extract from `from_email`, `to_emails[]`, `cc_emails[]`, `subject`, `received_at`, `body_text`, `attachments[]`.
   b. Derive folder name: `{YYYY-MM-DD}-{subject-slug}` from `received_at`.
   c. Write `email.txt`:
      ```
      From: {from_email}
      To: {to_emails joined by ", "}
      CC: {cc_emails joined by ", "}
      Date: {received_at}
      Subject: {subject}

      {body_text}
      ```
   d. Write `metadata.json`:
      ```json
      {
        "email_id": "{email.id}",
        "thread_id": "{email.thread_id}",
        "from": "{email.from_email}",
        "to": ["{email.to_emails}"],
        "cc": ["{email.cc_emails}"],
        "subject": "{email.subject}",
        "date": "{email.received_at formatted as YYYY-MM-DD}",
        "date_iso": "{email.received_at}",
        "attachments": [{"filename": "...", "size_bytes": ..., "mime_type": "...", "attachment_id": "..."}]
      }
      ```
   e. For each attachment: call `get_email_attachment(attachment_id: "{attachment.id}")` to get a signed download URL (1hr expiry), then `curl -L -o "clients/{client_slug}/01-materials/emails/{folder}/{filename}" "{url}"`.

After fetching, rescan `clients/{client_slug}/01-materials/emails/` for new subdirectories. Cross-reference against `extracted_materials[]` by `source_file`.

Print status:

```
EMAIL SYNC — {company_name}
─────────────────────────────────────────────────────
  Folder                          Date        Status
  ──────────────────────────────  ──────────  ──────────
  {folder}                        {date}      NEW
  {folder}                        {date}      ALREADY EXTRACTED
─────────────────────────────────────────────────────
  New: {n}  |  Already extracted: {n}
```

If CRM returns no emails for this contact, print zero counts and continue.

---

### Stage 1e — Scan Client-Provided Materials (parallel sub-agent)

Scan `clients/{client_slug}/01-materials/documents/` for all files.

For each file found, check whether it is already referenced in `extracted_materials[]` (matching `source_file` field). Files not referenced are **unprocessed materials**.

Print materials status:

```
CLIENT-PROVIDED MATERIALS — {company_name}
─────────────────────────────────────────────────────
  File                            Status
  ──────────────────────────────  ──────────────────
  {filename}                      UNPROCESSED
  {filename}                      ALREADY EXTRACTED
─────────────────────────────────────────────────────
  Unprocessed: {n}  |  Already extracted: {n}
```

**Post-parallel reconciliation (parent agent):** After all 4 sub-agents return:

1. **v4 bootstrap check** — if neither `audit-manifest.json` nor `audit-data.json` exist, create the v4 scaffold (directory, CLAUDE.md, manifest, 6 domain files, populate `meta.json`). This runs once in the parent after Stage 1a completes, using the meeting folders 1a wrote to disk.
2. **Meeting-to-session cross-reference** — rescan `clients/{client_slug}/01-materials/meetings/` for all subdirectories containing `transcript.txt`. Read each `metadata.json` to get `recording_id`. Cross-reference against `sessions[]` by `fathom_meeting_id` and print the MEETING SYNC status table (NEW / UNANALYZED / DONE).
3. **Print all status tables** — meetings (from 1a), SMS/calls (from 1c), emails (from 1d), materials (from 1e) — in sequence.

---

### Stage 2 — Build Ingestion Manifest

Load or create `clients/{client_slug}/03-audit/data/ingestion-manifest.json`.

**If the manifest does not exist:** build it from scratch by cross-referencing:
- Meeting folders on disk against `sessions[]` in `extraction.json` (v4) or `audit-data.json` (v2/v3) (using `fathom_meeting_id`)
- Files in `01-materials/documents/` against `extracted_materials[]` in `extraction.json` (v4) or `audit-data.json` (v2/v3)

For each meeting, compute:
- `transcript_hash` — SHA-256 of `transcript.txt` content (use Python hashlib or equivalent)
- `transcript_size_bytes` — file size
- `status` — `"extracted"` if matching session with `analyzed: true`; `"pending"` otherwise
- `extracted_at` — from session entry date if available; null otherwise

For each material file, compute:
- `hash` — SHA-256 of file content
- `size_bytes` — file size
- `status` — `"extracted"` if in `extracted_materials[]`; `"skipped"` if it matches auto-skip rules (see IM); `"pending"` otherwise

**If the manifest exists:** reconcile it against the current filesystem:
- Add any new meeting folders not yet in the manifest
- Add any new material files not yet in the manifest
- Flag any extracted transcript whose `transcript_hash` has changed since last extraction (set `status: "changed"` — triggers re-extraction)
- Update the `summary` block

Print manifest status:

```
INGESTION MANIFEST — {company_name}
─────────────────────────────────────────────────────
  Meetings:  {extracted}/{total} extracted | {pending} pending | {failed} failed
  Materials: {extracted}/{total} extracted | {pending} pending | {skipped} skipped
  Last sync: {timestamp}
─────────────────────────────────────────────────────
```

Save the updated manifest.

**Work queue:** Collect all sources with `status: "pending"` or `status: "failed"` or `status: "changed"`. Sort chronologically (oldest first). This is the extraction queue.

If the work queue is empty:
```
Nothing to extract — all inputs already processed.
```
Skip to Stage 5.

**Single resource mode:** If the user explicitly asks to extract just one resource, list all available inputs and let them pick. Extract only that one.

---

### Stage 3 — Build Context Packet

Before dispatching sub-agents, build a lightweight context packet from the current audit data. For v4 clients, read `meta.json` and `extraction.json` directly. For v2/v3 clients, read from `audit-data.json`. This replaces passing the full audit data to each sub-agent.

The context packet contains:

```json
{
  "client_slug": "{client_slug}",
  "company_name": "{company_name}",
  "existing_stages": ["acquisition", "quoting"],
  "id_sequences": {
    "last_step_ids": { "acquisition": "ACQ-015", "quoting": "QUO-003" },
    "last_pain_point_id": "PP-025",
    "last_waste_id": "W-009",
    "last_optimisation_id": "OPT-015",
    "last_decision_node_id": "D004",
    "last_fq_id": "FQ-025",
    "last_kpi_id": "KPI-039",
    "last_contradiction_id": "CTR-002"
  },
  "existing_tool_names": ["HubSpot", "Xero"],
  "blended_hourly_rate_aud": 50,
  "sessions_summary": [
    { "session": 1, "date": "2026-03-23", "stages": ["acquisition"] }
  ],
  "existing_pain_point_summaries": ["4-system cross-referencing"],
  "existing_contradiction_topics": ["annual sales volume"]
}
```

**How to build each field:**
- `existing_stages` — list all `stage` keys in `processes[]`
- `last_step_ids` — for each stage, find the highest step number from its `steps[].step_id`
- `last_pain_point_id` — highest `pain_point_id` in `pain_points[]`
- `last_waste_id` — highest `waste_id` in `waste_items[]`
- `last_optimisation_id` — highest `optimisation_id` in `optimisations[]`
- `last_decision_node_id` — highest `node_id` in `decision_nodes[]`
- `last_fq_id` — highest `fq_id` in `follow_up_questions[]`
- `last_kpi_id` — highest `metric_id` in `business_metrics[]`
- `last_contradiction_id` — highest `contradiction_id` in `contradictions[]`
- `existing_tool_names` — all `tool_name` values in `tools[]`
- `blended_hourly_rate_aud` — always `50` (canonical assumed blended team rate, never extracted from transcripts)
- `sessions_summary` — one entry per session in `sessions[]`: just `session_number`, `date`, `stages_covered`
- `existing_pain_point_summaries` — first 8 words of each `title` in `pain_points[]` (for dedup awareness)
- `existing_contradiction_topics` — all `topic` values in `contradictions[]`

Keep the context packet under 10KB. If `existing_pain_point_summaries` would exceed this, truncate to the most recent 30 entries.

---

### Stage 3b — Source Triage

Purpose: Route each source to the right handler before full extraction. Protects the expensive extraction layer from noise.

For each source in the work queue (meetings, emails, documents):

### Classification

Classify as one of three categories:

**process_relevant** — The source directly describes HOW work is done: steps, actors, tools, decisions, timings. A meeting transcript where the client walks through their process. A procedure document. A workflow description.
→ Route to: full extraction sub-agent (existing pipeline)

**context_relevant** — The source provides background, numbers, or constraints but does not describe process steps. Company overview, pricing schedule, staff list, metric reports, email threads about a specific problem but not the process behind it.
→ Route to: lightweight context extraction (only populates new_business_metrics[], staff_updates[], tool_updates[] — no steps)

**noise** — Logistics, signatures, calendar invites, acknowledgements, spam, document headers/footers.
→ Route to: skip. Log in ingestion manifest as status: "skipped", skip_reason: "noise"

### Chunk-level triage for large documents

For any document over 5000 words (approximately 35KB of text):
1. Split into chunks of approximately 2000 words each
2. Classify each chunk independently
3. Forward only process_relevant chunks to the full extraction sub-agent
4. Combine context_relevant chunks into a single context brief (summary only)
5. Log skipped chunks in the ingestion manifest with chunk reference

### Output

After triage, update the work queue with classifications. Display summary before proceeding:
```
SOURCE TRIAGE COMPLETE
  {n} sources → full extraction
  {n} sources → context only
  {n} sources → skipped (noise)
  {n} chunks extracted from {m} large documents
```

Proceed to Stage 4 using only the process_relevant sources.

---

### Stage 3c — KIQ Injection

1. Read industry_tag from meta.json (or identify from company name/description)
2. Load references/kiq-library.md
3. Identify which KIQs are ALREADY answered:
   - For each KIQ's expected_fields, check if those fields exist in current extraction.json with non-null values
   - If expected fields exist: mark KIQ as "answered"
   - Otherwise: mark as "open"
4. Add to the context packet:
   ```json
   {
     "open_kiq_ids": ["KIQ-ACQ-001", "KIQ-QUO-003"],
     "industry": "construction"
   }
   ```
5. Sub-agents receive this as part of their context and output kiq_evidence[] (see sub-agent-extract.md Output Format)
6. After all sub-agents complete: any KIQ still in open_kiq_ids with no kiq_evidence entry → confirmed Type A gap → create gaps_register entry

---

### Stage 4 — Sequential Sub-Agent Extraction

For each source in the work queue (chronological order):

#### 4a — Dispatch Sub-Agent

Read the transcript or material file content.

Spawn a sub-agent using the Agent tool:

```
Agent({
  description: "Extract {folder_or_filename} — {client_slug}",
  model: "sonnet",
  prompt: [
    "Read and follow the extraction schema in sub-agent-extract.md:",
    "[full content of sub-agent-extract.md]",
    "",
    "Gold-standard BPMN examples (match this quality bar):",
    "[full content of references/bpmn-examples.md]",
    "",
    "Context packet for this extraction:",
    "[context_packet as JSON]",
    "",
    "Source material details:",
    "Type: {source_type}",
    "Path: {source_path}",
    "Date: {source_date}",
    "Session Number: {session_number or null}",
    "Fathom Meeting ID: {fathom_meeting_id or null}",
    "Participants: {participants}",
    "",
    "Transcript/material content:",
    "[full transcript or material content]"
  ].join("\n")
})
```

Wait for the sub-agent to return. Do not continue to the next source until this one completes.

#### 4b — Merge Results

Load `merge-extraction.md`. Follow all merge steps in order, applying the sub-agent's returned JSON to the in-memory audit data.

Print per-source result as each completes:
```
  EXTRACTED — {folder or filename}
    Steps: +{n}  |  Pain points: +{n}  |  Waste: +{n}  |  Tools: +{n}/{updated}
```

#### 4b-ii — Post-Merge Semantic Check (advisory)

After merge-extraction.md completes, run the semantic quality check on the just-merged stages:

```bash
python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_extraction_quality.py \
    --extraction-json clients/{client_slug}/03-audit/data/extraction.json \
    --stages {comma-joined list of stages touched by this source} \
    --partial-ok \
    --verbose
```

For v2/v3 clients, pass `--extraction-json clients/{client_slug}/audit/audit-data.json` instead.

- Exit 0: no findings, continue silently.
- Exit 1 (advisory): print findings in the per-source summary block, continue.
- Exit 2 (warning): print `SEMANTIC QUALITY WARNING: {n} findings for {source_path}`. Mark the source with `quality_warnings: {count}` in the ingestion manifest. Continue (does not block).
- Exit 3 (error): log and continue (never block on tooling errors).

#### 4c — Checkpoint Save

Write audit-data.json to disk. Update the ingestion manifest for this source.

**Update the context packet** for the next sub-agent (update ID sequences, tool names, etc. — see merge-extraction.md Step 17). For v4, re-read updated `meta.json` and `extraction.json` to refresh the packet.

---

#### Stage 4d — Semantic Review Sub-Agent

Runs once, after all sources have been extracted and checkpointed. Skipped if the work queue had zero sources (nothing to review).

Load `semantic-review.md`. Build a slim review context packet:
- `company_name`, `client_slug`
- For each process in `extraction.json`: `stage`, `name`, `steps[]` (trimmed to `step_id`, `title`, `description` first 80 chars, `element_type`, `annotations`), `sequence_flows[]`
- Keep under 15KB total

Spawn a sub-agent:

```
Agent({
  description: "Semantic review — {client_slug}",
  model: "sonnet",
  prompt: [full content of semantic-review.md with {context_packet} and {processes_json} replaced]
})
```

Wait for the review to complete. Parse the returned JSON.

**Apply corrections:**

1. **Reclassifications:** For each item in `reclassifications[]`:
   - Remove the step from `extraction.json` processes[].steps[]
   - Transfer its `sources[]` to a new pain_point in `findings.json`
   - Apply the flow reconnection (remove flows involving the step, add the bridging flow)

2. **Journey gaps:** For each item in `journey_gaps[]`:
   - Create a new `follow_up_question` entry in `findings.json` with `priority: "HIGH"`, `category: "process_gap"`, `answered: false`

3. **Label improvements:** For each item in `label_improvements[]`:
   - Update the step's `title` in `extraction.json` to the `proposed_title`

4. **Duplicate candidates:** Show to the user for confirmation before applying any merge or rename.

5. **Control gaps:** For each item in `control_gaps[]`:
   - Append to `control_gaps[]` in `findings.json` (create the array if absent). Use the `control_gap_id`, `stage`, `category`, `description`, `severity`, and `affected_step_ids` from the review output.
   - Do not remove or modify any steps — control gaps are structural observations, not extraction errors.

After applying corrections, write updated domain files and update `audit-manifest.json`.

Print the review summary:

```
SEMANTIC REVIEW — {company_name}
─────────────────────────────────────────────────────
  Steps reviewed:          {n}
  Reclassified as PP:      {n} (applied)
  Journey gaps flagged:    {n} (added as follow-up questions)
  Labels improved:         {n} (applied)
  Duplicate candidates:    {n} (awaiting confirmation)
  Control gaps detected:   {n} (added to findings.json)
─────────────────────────────────────────────────────
```

---

### Stage 5 — Validate & Save

```bash
python3 scripts/validate_audit_data.py --file clients/{client_slug}/03-audit/data/audit-data.json --verbose
```

For v4 clients, pass the manifest path instead: `--manifest clients/{client_slug}/03-audit/data/audit-manifest.json`.

Fix any CRITICAL or HIGH severity issues. Save final domain files (v4) or audit-data.json (v2/v3).

---

### Stage 6 — Summary

Display combined summary across all inputs processed this run:

```
SYNC & UPDATE COMPLETE — {company_name}
══════════════════════════════════════════════════════

  Resources synced:          {n new meetings} + {n new materials}
  Resources extracted:       {n}  |  Failed: {n}
  Process steps extracted:   {n} (cumulative in audit data)
  New pain points:           {n}
  New optimisations:         {n}
  New waste items:           {n} (${total_annual_waste_aud}/yr)
  Follow-up questions:       {n} (HIGH: {n} / MEDIUM: {n} / LOW: {n})
  Contradictions found:      {n}

══════════════════════════════════════════════════════

COMPLETENESS:
  Acquisition:  {covered%}  Quoting: {covered%}  Onboarding: {covered%}
  Fulfilment:   {covered%}  Retention: {covered%}

TOP FOLLOW-UP QUESTIONS (HIGH):
  • {question} [{stage}]
  ...
```

If any sources failed extraction, list them:
```
FAILED SOURCES (retry on next SU run):
  • {folder_or_filename} — {failure_reason}
```

Ask: **"Save this to memory and confirm? [Y / corrections]"**

On Y: update sidecar memory files (`${CLAUDE_PLUGIN_ROOT}/_memory/{skillName}-sidecar/index.md` and the active client's detail file at `${CLAUDE_PLUGIN_ROOT}/_memory/{skillName}-sidecar/clients/{client_slug}.md`, and `chronology.md`) with new session data, then confirm saved.

On corrections: apply corrections to audit data in memory, re-display summary, ask again before saving.

---

### Stage 7 — CRM Sync

**Best-effort.** If any CRM call fails, log a warning and continue. Never block the pipeline.

#### 7a. Find or Create Project

If `crm.project_id` is already set in `meta.json` (v4) or `audit-data.json` (v2/v3), skip to 7b.

1. Check if `crm.contact_id` is set. If not:
   - `search_contacts(query: "{company_name}")` → store `contact_id`
   - If no match: `search_contacts(query: "{contact.domain}")` → store `contact_id`
   - If still no match: `create_contact(name: "{company_name}", email_address: "{contact.emails[0]}", is_customer: true)` → store `contact_id`
2. Check if `crm.lead_id` is set. If not:
   - `search_leads(query: "{company_name}")` → store `lead_id`, preferring match linked to `contact_id`
3. `list_projects()` → filter results where `contact_id` matches `crm.contact_id`
   - If found: store `project_id`. Prefer project with "Audit" in name if multiple.
   - If NOT found: `create_project(name: "{company_name} Audit", contact_id: "{crm.contact_id}", status: "active", budget: 3000)` → store `project_id`
4. If lead exists and stage is not "Won": `update_lead(lead_id, stage: "Won")` — only if current stage is in {"Negotiation", "Proposal", "Discovery Call - Completed"}. Otherwise add a lead comment noting audit has started.

#### 7b. Create Task Lists (First Run Only)

`list_tasks(project_id: "{crm.project_id}")` — if empty, create the full task board:

**Create 4 task lists and seed tasks:**

List 1 — **Extraction** (`task_list_id` → `crm.task_list_ids.extraction`):
- `create_task(title: "Session Extraction — Complete all sessions", project_id, task_list_id, priority: 3, status: "In Progress")`
- `create_task(title: "Process Map Complete — All stages covered", project_id, task_list_id, priority: 2)`

List 2 — **Analysis** (`task_list_id` → `crm.task_list_ids.analysis`):
- `create_task(title: "Extract Improvements (EI)", project_id, task_list_id, priority: 2)`
- `create_task(title: "Research Improvements (RI)", project_id, task_list_id, priority: 1)`
- `create_task(title: "Build Strategic Approaches (SA)", project_id, task_list_id, priority: 1)`
- `create_task(title: "Build & Rate (BR)", project_id, task_list_id, priority: 1)`
- `create_task(title: "Verify Research (VR)", project_id, task_list_id, priority: 1)`
- `create_task(title: "Build Transformation Blueprint (TB)", project_id, task_list_id, priority: 1)`

List 3 — **Deliverables** (`task_list_id` → `crm.task_list_ids.deliverables`):
- `create_task(title: "Generate Deliverables", project_id, task_list_id, priority: 1)`

List 4 — **Solution Design** (`task_list_id` → `crm.task_list_ids.solution_design`):
- `create_task(title: "Extract Requirements (RE)", project_id, task_list_id, priority: 1)`
- `create_task(title: "Build Architecture (BA)", project_id, task_list_id, priority: 1)`
- `create_task(title: "Build Prototype (BP)", project_id, task_list_id, priority: 1)`

Store all `task_list_id` values in `crm.task_list_ids`.

**Note:** If `create_task` requires a `task_list_id` but the CRM doesn't support creating task lists via MCP, create all tasks as a flat list on the project and use title prefixes instead. Skip storing `task_list_ids`.

#### 7c. Update Tasks

1. `list_tasks(project_id: "{crm.project_id}")` → find "Session Extraction" task by title match
2. `create_task_comment(task_id, content)` with extraction summary:
   ```
   SU run {date}: {n} resources extracted.
   Sessions: {sessions_completed} | Steps: {n} | Pain points: {n} | Waste: {n} (${annual}/yr)
   Completeness: Acquisition {%} | Quoting {%} | Onboarding {%} | Fulfilment {%} | Retention {%}
   ```
3. If `audit_status` = `process_map_complete`:
   - Find "Session Extraction" task → `update_task_status(task_id, status: "Done")`
   - Find "Process Map Complete" task → `update_task_status(task_id, status: "Done")`
   - Find "Extract Improvements (EI)" task → `update_task_status(task_id, status: "In Progress")`

#### 7d. Save CRM IDs

Update `crm.last_synced` to current ISO 8601 timestamp. For v4 clients: save `meta.json` with all CRM IDs populated and update `audit-manifest.json` (`domains.meta.updated_at` and root `updated_at`). For v2/v3: save `audit-data.json`.

Print:
```
CRM SYNC — {company_name}
─────────────────────────────────────────────────────
  Project: {project_id} ({found|created})
  Tasks: {n} on board | {n} comments added
  Lead stage: {current_stage}
─────────────────────────────────────────────────────
```
