---
name: ingest-feedback
description: Ingest a Loom review video, local video, or typed feedback. Downloads and transcribes video, runs screen context analysis, maps each piece of feedback to specific audit data items, presents for approval.
menu-code: IF
---

# Ingest Feedback (IF)

> **Orchestration capability.** Downloads and transcribes a Loom video (or accepts typed feedback), runs screen context analysis to identify what's on screen at each timestamp, dispatches a sub-agent to map feedback to specific audit data items, then presents the mapped items for approval. Nothing is written to domain files here — that is [AF].

---

## Stage 1: Pre-flight

### 1a. Determine input type

Ask the user:

```
INGEST FEEDBACK -- {company_name}

How would you like to provide feedback?

  [L] Loom URL        -- paste a Loom share link
  [V] Local video     -- provide a path to a recorded video file
  [T] Text input      -- type or paste corrections directly

Select input type:
```

### 1b. Assign round ID

Check `clients/{slug}/03-audit/data/reviews.json`:
- If it does not exist, this is Round 1 (RR-001)
- If it exists, count existing `review_rounds[]` and set next round: RR-{n+1 padded to 3 digits}

Create round directory: `clients/{slug}/03-audit/reviews/{round_id}/`

### 1c. Load the audit item inventory (context packet)

Read the following domain files and build a flat inventory of addressable items. This is the lookup table the sub-agent uses to map reviewer narration to specific IDs.

Cap at ~10KB total. Include only `id` + `title` per item.

**From `findings.json`:**
```
waste_items:      [{waste_id, activity}]
pain_points:      [{pain_point_id, title}]
```

**From `opportunities.json`:**
```
proposed_changes: [{change_id, title, stage}]
roi_items:        [{roi_item_id, activity}]
```

**From `extraction.json`:**
```
processes:        [{stage, name, steps: [{step_id, title}]}]
tools:            [{tool_id, tool_name}]
```

**From `strategy.json`:**
```
strategic_tiers:  [{tier: "mid_ticket|high_ticket|low_ticket", name}]
plugin_cards:     [{process_id, title}]
```

Format the inventory as a compact JSON object. Confirm it is under 10KB before sending to the sub-agent.

---

## Stage 2: Acquire and Transcribe (video inputs only)

Skip this stage for text input — go directly to Stage 3.

### 2a. For Loom URL

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/download-loom.py \
  --url "{loom_url}" \
  --output-dir "clients/{slug}/03-audit/reviews/{round_id}"
```

Check the output. If `vtt_path` is returned and the VTT file exists, parse it to a plain text transcript. Each line format: `[MM:SS] {text}`.

If no VTT: proceed to 2b (manual transcript).

### 2b. For local video or when VTT unavailable

No automated transcription is available. Prompt the user:

```
No VTT subtitles were returned for this video. To proceed:
  [T] Switch to text input mode — type or paste your corrections directly
  [M] Provide a manual transcript file path — paste the path to a .txt transcript

Select:
```

If the user selects [M], read the file at the provided path and use it as the transcript source for Stage 3.

If the user selects [T], skip Stage 2c and go directly to Stage 3 with typed input.

### 2c. Screen context analysis

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/extract-frames.py \
  --video "clients/{slug}/03-audit/reviews/{round_id}/video.mp4" \
  --output-dir "clients/{slug}/03-audit/reviews/{round_id}/frames" \
  --interval 8 \
  --max-frames 24
```

Then dispatch `sub-agent-screen-context.md` as a sub-agent. Pass:
- `transcript_path`: path to transcript.txt
- `frames_dir`: path to frames directory
- `frame_index`: the frame-index.json content
- `audit_item_inventory`: the context packet from Stage 1c

The sub-agent returns a `screen_timeline` array (see feedback-schema.md). Save to `clients/{slug}/03-audit/reviews/{round_id}/screen-context.json`.

---

## Stage 3: Dispatch Feedback Extraction Sub-Agent

Build the context payload for `sub-agent-feedback-extract.md`:

```
source_content:         transcript text (or typed feedback text for text input)
screen_context:         screen_timeline from screen-context.json (null for text input)
audit_item_inventory:   the compact JSON inventory from Stage 1c
trust_level:            "full" for internal PM, "advisory" for client
round_id:               e.g. "RR-001"
round_number:           integer
```

Dispatch as a sub-agent. The sub-agent returns:
- `feedback_items[]` — structured items mapped to specific audit data IDs
- `unresolved_items[]` — fragments the sub-agent could not map to a specific target

---

## Stage 4: Present for Approval

Display results grouped by domain file.

```
FEEDBACK REVIEW -- {company_name} -- {round_id}
Source: {Loom title or "Text input"} | Reviewer: {name} | {n} items extracted

FINDINGS.JSON  ({n} items)
──────────────────────────────────────────────────────────
  [FB-001] HIGH | correction  |  W-003: Manual data entry during onboarding
    Current:  hours_per_week = 10
    Proposed: hours_per_week = 1.5
    Rationale: Reviewer confirms Jordan said 3 hours fortnightly
    Quote: "this waste item, the ten hours a week for data entry, that's way off, it's more like three hours every two weeks"
    Timestamp: 0:45
    Screen: waste.html row W-003 (confirmed by frame analysis)
    [ approve / reject / defer ]

  [FB-002] MEDIUM | clarification  |  PP-007: Invoice follow-up is manual
    Current:  description = "Staff manually chase overdue invoices via phone each week"
    Proposed: description = "Staff call clients 7 days overdue; 14-day cases escalated to director"
    Quote: "it's not just manual, there's a specific process — seven days gets a call, fourteen days goes to the director"
    Timestamp: 3:12
    Screen: findings.html PP-007 card
    [ approve / reject / defer ]

...

OPPORTUNITIES.JSON  ({n} items)
──────────────────────────────────────────────────────────
...

UNRESOLVED ITEMS  ({n} items)
──────────────────────────────────────────────────────────
  [UR-001] Could not identify specific target
    Quote: "and that pricing one, it's off"
    Timestamp: 2:03
    Screen: solutions-overview.html (section unclear)
    What item were they referring to? [enter item ID or "skip"]:
```

For each item, prompt: approve / reject / defer. For unresolved items, prompt for manual mapping.

Set `resolution.status` on each item based on the operator's response.

Display final summary:
```
  Approved: {n}  |  Rejected: {n}  |  Deferred: {n}  |  Manually mapped: {n}

  Run [AF] to apply the {n} approved items to domain files.
```

---

## Stage 5: Save Round

### 5a. Build round object

Construct the full round object following the schema in `references/feedback-schema.md`:
- `round_id`, `round_number`, `reviewer`, `source`, `ingested_at`, `status: "pending_approval"` (or "partially_applied" if some were approved)
- `feedback_items[]` with full detail and resolution statuses
- `unresolved_items[]` with any manual mappings filled in
- `summary` object with counts

### 5b. Write reviews.json

If `clients/{slug}/03-audit/data/reviews.json` does not exist, create it from the template in `references/feedback-schema.md`. Append or replace the round.

Write the file. Then update `audit-manifest.json`:
- If `domains.reviews` does not exist, add it (with `written_by: "reviewer"`)
- Update `domains.reviews.updated_at` and `domains.reviews.checksum`
- Update root `updated_at`

**Do NOT write to any other domain files here.** AF handles application.

### 5c. Confirm

```
Round {round_id} saved.
  {n} items approved — run [AF] to apply.
  {n} items deferred or rejected.
  Review history updated in clients/{slug}/03-audit/data/reviews.json
```

### 5d. CRM update (best-effort)

If `crm.project_id` is not null, create a task comment on the review task:
"Round {round_id} ingested: {n} feedback items ({n} HIGH, {n} MEDIUM, {n} LOW). {n} approved, ready to apply with [AF]."
