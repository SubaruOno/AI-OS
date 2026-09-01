# Transcript Deep Read — Reference

Pattern for re-reading raw Fathom transcripts to extract deep scene context before building a Cowork demo prompt. Used by BC Stage 2.5. Reusable by any future skill that needs richer client context than what audit-data.json captures.

---

## Why transcripts, not just audit-data

Audit-data is a lossy extraction. It captures structured data — pain points, proposed changes, tools, waste items — but loses the texture: the exact vocabulary the client uses, the order they described their workflow, the structure of their artefacts as they walked through them on screen, and the business rules they demonstrated rather than summarised. For a Cowork demo to achieve "that's us" recognition, you need the texture, not just the summary.

---

## Transcript Format

Files live at: `clients/{slug}/01-materials/meetings/{YYYY-MM-DD}-{folder}/transcript.txt`

```
Meeting: Jordan and Adam
Date: 2026-03-09T00:07:56Z

[MM:SS] Speaker Name: utterance text here
[MM:SS] Speaker Name: continuation of their turn
```

- Timestamps are `[MM:SS]` — minutes and seconds from call start
- Speaker-labelled per line
- Sliceable by regex on `[MM:SS]` prefix — any line where `int(MM)*60 + int(SS)` falls inside the window

---

## Step 1 — Collect anchor points

For the selected plugin, walk these linkages in audit-data.json and collect every `(meeting_id, timestamp_seconds, source, label)` tuple:

| Source | How to walk |
|---|---|
| Plugin source quotes | `selected_plugin.source_quotes[].pain_point_id` → `pain_points[pp].meeting_references[]` |
| Related pain points | `selected_plugin.change_ids[]` → `proposed_changes[pc].linked_pain_point_ids[]` → `pain_points[pp].meeting_references[]` |
| Process steps | `proposed_changes[pc].affected_step_ids[]` → `processes[].steps[step].meeting_references[]` (if present) or `steps[step].source_timestamp_seconds` + derive meeting_id from `sessions[step.source_session].fathom_url` |
| Tool references | `selected_plugin.tools_connected[]` → `tools[t].meeting_references[]` where the tool's use_case is relevant to the plugin |

Deduplicate on `(meeting_id, timestamp_seconds)`. Keep the highest-confidence entry when duplicates exist.

Result: a flat list of anchor points, each with `meeting_id`, `timestamp_seconds`, `confidence` (from the pain_point or tool record), and a human label for logging.

---

## Step 2 — Resolve meeting_id → transcript path

**CRITICAL GOTCHA:** `meeting_references[].meeting_id` stores the Fathom call URL tail (e.g. `"demo"`). The sibling `metadata.json` in each meeting folder stores a different internal `recording_id` (e.g. `"128074990"`). **These do NOT match.** Do not try to match `meeting_id` against `recording_id`.

**Correct lookup:**
```
For each meetings folder at clients/{slug}/01-materials/meetings/*/metadata.json:
  Parse metadata.json
  Extract the tail of metadata.fathom_url: fathom_url.split("/")[-1]
  If tail == anchor.meeting_id → this folder's transcript.txt is the match
```

Build a map `{ meeting_id → transcript_path }` in a single scan. Cache it for the BC run — don't re-scan for every anchor.

**Example:** meeting_id `"demo"` matches `clients/brightside-services/01-materials/meetings/2026-03-09-jordan-and-adam/transcript.txt` because `metadata.fathom_url` = `"https://fathom.video/calls/demo"`.

---

## Step 3 — Compute windows and merge

For each anchor, compute a reading window:

```
window_start = max(0, timestamp_seconds - 90)   # 1.5 min before — catches the lead-up
window_end   = timestamp_seconds + 300           # 5 min after — catches elaboration
```

Group anchors by `transcript_path`. Within each transcript, merge any overlapping windows (if two windows are within 180s of each other, union them into one). Merging prevents reading the same lines twice and keeps context contiguous.

**Context budget cap:** target ≤ 6000 tokens of raw transcript total across all windows. Each line of transcript is roughly 15–25 tokens. At ~20 tokens/line, 6000 tokens ≈ 300 lines ≈ 8–9 minutes of conversation. If the merged window list exceeds the cap:

1. Keep all HIGH confidence windows
2. Keep merged windows that span 2+ anchors
3. Drop LOW confidence singletons until under budget

---

## Step 4 — Read the transcript slices

Use the `Read` tool with `offset` and `limit` (in lines) to pull only the window.

**Computing line range from seconds:**

Transcript lines don't have a direct line-number-to-seconds index, so scan the file to find the first and last line in the window:

1. Read the full transcript once with a fast grep-equivalent (Grep tool with pattern `\[(\d+):(\d+)\]`) to get all timestamp lines and their line numbers.
2. For each window `[start_s, end_s]`, find: `first_line = smallest line_number where int(MM)*60+int(SS) >= start_s` and `last_line = largest line_number where int(MM)*60+int(SS) <= end_s`.
3. Read with `offset=first_line, limit=(last_line - first_line + 1)`.

**Alternative (simpler, slightly less precise):** estimate line rate. Transcripts run at roughly 1 line per 3–6 seconds on average. Use this to approximate the offset, then read a slightly wider range and trim mentally. Acceptable for scene extraction — you don't need exact precision.

---

## Step 5 — Structured extraction (scene_bundle)

After reading all transcript slices, Claude performs a single extraction pass over the combined raw text and writes the following `scene_bundle` object. This is not a summary — it is a structured extraction in the client's own words.

```
scene_bundle = {
  "client_vocabulary": [
    // Exact phrases and terms the client uses for things
    // Format: {"term": "run sheet", "used_for": "daily schedule per worker"}
    // Capture: tool names they use, what they call participants, what they call roles,
    //          how they refer to their schedule format, any NDIS/industry jargon they own
  ],

  "actual_workflow_steps": [
    // What they literally do, in the order they described or demonstrated it
    // Write as first-person present tense from their perspective:
    //   "Start with transport — you can't build anything else until transport is sorted"
    //   "Build the cafe schedule first — it's the biggest fixed block of the day"
    // Include sequencing dependencies they explicitly called out
  ],

  "observed_artefact_structure": {
    // The structure of the tool or document they use today — as they described or showed it
    "tool": "Google Sheets",
    "columns": [],             // Column headers in their sheet, if named
    "sections": [],            // Named sections or blocks, if present (e.g., "MORNING", "AFTERNOON", "FRIDAY")
    "notes_content_patterns": [], // Types of content in their notes fields (e.g., "medication", "pickup address", "behaviour flag")
    "layout": "",              // How it's laid out: row-per-person, row-per-time-slot, day-per-sheet, etc.
    "other_details": ""        // Anything else they described about how it's structured
  },

  "concrete_examples": [
    // Specific real examples they gave during the session — names, venues, times, amounts
    // Format: {"type": "participant|venue|staff|rule|amount", "value": "...", "constraint": "..."}
    // Examples: participant names with their specific requirements, actual venue names with suburb,
    //           real business rules they demonstrated (not just stated), actual time slots they used
  ],

  "business_rules_demonstrated": [
    // Rules they showed in action or explained in detail — richer than the pain point summary
    // Write as a rule statement: "Transport is always sorted first — nothing moves until transport is resolved"
    // Include edge cases they mentioned, workarounds they use, exceptions to their own rules
  ],

  "verbatim_quotes": [
    // The best 3–6 lines from the transcript windows — most vivid, most specific, most usable on a call
    // Format: {"quote": "...", "speaker": "Jordan Lee", "timestamp_mmss": "44:23", "context": "one sentence on what they were describing"}
    // Prefer lines that contain: concrete numbers, named things, expressed frustration, or demonstrated steps
  ],

  "gaps_and_unknowns": [
    // Things that came up but weren't clear — capture the uncertainty so Stage 3 doesn't invent details
    // Example: "Staff availability format not described — unclear if it's a shared sheet or verbal"
  ]
}
```

**Extraction discipline:**
- Use their words, not yours. If they say "run sheet," write "run sheet," not "schedule."
- Prefer demonstrated over described. If they showed a screen and pointed at columns, that's gold. If they only mentioned it in passing, note it with lower confidence.
- `gaps_and_unknowns` is as important as the rest — it prevents Stage 3 from fabricating details that aren't grounded in the transcript. Fabrication in demo data is permitted for scene realism (per `feedback_demo_data_fabrication_ok.md`), but it must be conscious, not accidental.

---

## Step 6 — Feed into Stage 3 (Write Demo Prompt)

Use `scene_bundle` as the primary source for prompt content:

| Prompt section | Source from scene_bundle |
|---|---|
| Section 1 — Role framing, current-state prose | `actual_workflow_steps` + `client_vocabulary` — write in their order, using their terms |
| Section 2 — Character list | `concrete_examples` (type: participant, staff) + fabricate only what's missing |
| Section 2 — "Today's situation" | `concrete_examples` (venues, times) + `business_rules_demonstrated` (real constraints) |
| Section 3 — Task: output column spec | `observed_artefact_structure.columns` + `notes_content_patterns` — mirror their actual sheet |
| Verbatim anchor in demo-brief.md talk track | `verbatim_quotes[0]` (best line from window, may be richer than the short pain-point quote) |

Where `scene_bundle` gaps exist (e.g., `columns` is empty because they didn't describe the headers), fall back to `audit-data.json` field as before, then fabricate reasonable industry defaults if both are absent.

---

## Caching the scene_bundle

After a BC run, persist `scene_bundle` inside the `cowork_demos[]` record in audit-data.json:

```json
{
  "plugin_title": "Scheduling & Staff SMS",
  "plugin_slug": "scheduling-staff-sms",
  ...
  "scene_bundle": { ... },
  "scene_bundle_generated_at": "2026-04-14T..."
}
```

On **re-run** (Full rebuild): always re-run deep-read to pick up any new sessions since last run. On **Add alongside** (second plugin, same client): check if any `cowork_demos[].scene_bundle` in the same record covers overlapping `change_ids` — if yes, reuse it. Otherwise run fresh for the new plugin's anchors only.

---

## Future skills — reusing this pattern

Any skill that needs rich client context beyond what audit-data captures can use this pattern:

1. Load this reference file
2. Collect anchors from whatever linkage is relevant to your task
3. Run Steps 2–5 unchanged
4. Use the `scene_bundle` for your own purposes

Candidate future consumers: BA (Build Architecture) for understanding current-state data flows from the transcript; BC second-run for additional scenarios; any skill that writes client-facing copy and wants to use their actual language.
