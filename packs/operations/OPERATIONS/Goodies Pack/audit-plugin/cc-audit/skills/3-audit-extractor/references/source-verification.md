# Source Verification Procedure

Shared procedure used by Process Review (PR), Findings Review (FR), and Waste Review (WR). Load this file at the start of any review agent's source traceability step and follow the procedures below verbatim.

> **Schema note:** All extracted items now carry a unified `sources[]` array (see the canonical schema's "Source Trail Convention"). Iterate `item.sources` and verify each entry; `audit_reader.py` normalizes legacy flat fields (`source_session`, `source_quote`, `source_document`, etc.) into `sources[]` on read, so this procedure works uniformly across v2/v3/v4 clients.

---

## 1. Resolving Source Paths

For each `sources[]` entry on an item:

**If `kind == "fathom"`:**
1. Read `clients/{client_slug}/03-audit/data/extraction.json` (v4) or the `extraction` domain from `audit-data.json` (v3).
2. In `sessions[]`, find the entry where `session_number == src.session_id`.
3. The transcript folder path is the directory component of the session's transcript reference (`transcript_file`, `folder_path`, or derive from `date` and the meeting slug: `clients/{client_slug}/01-materials/meetings/{YYYY-MM-DD}-{slug}/transcript.txt`).
4. If `sessions[]` has no matching entry: classify the entry as `TRANSCRIPT_MISSING` (cannot verify).

**If `kind == "document"`:**
- The path is taken directly from `src.document_path`. It should be relative to the repo root (typically begins with `clients/{client_slug}/`).
- Check the file exists using Read. If it does not: classify as `DOCUMENT_MISSING`.

An item is fully verified only when every entry in its `sources[]` resolves successfully. If any entry fails, classify the entry; the item-level classification is the worst of its entry classifications.

---

## 2. Fuzzy Quote Matching

When verifying that an entry's `quote` appears in its source:

1. Read the source file (transcript for `fathom`, document for `document`).
2. Search for the `quote` text. Allow for minor transcription variations:
   - Punctuation differences (comma vs period, missing apostrophe)
   - Filler word omissions ("um", "uh", "like")
   - Minor word order variations within a short phrase
3. A match is valid if at least **80% of the words** in `quote` appear in a contiguous passage of the source (within a 50-word window). Proper nouns and numbers must match exactly.
4. If `quote` is very short (fewer than 8 words), require an exact or near-exact match with the words present.
5. **Numbers must match exactly.** If `quote` contains a number (hours, dollars, percentage, headcount) and that number does not appear in the matched passage, the match is invalid regardless of word overlap.

---

## 3. Timestamp Proximity Verification (Fathom entries only)

Transcripts include `[MM:SS]` markers. For every `fathom` source entry on the item:

1. Convert `src.timestamp_seconds` to `[MM:SS]` format (e.g., 1422 seconds = `[23:42]`).
2. Find the closest `[MM:SS]` marker in the transcript that is at or before the matched quote passage.
3. Convert that marker to seconds.
4. A timestamp is **correct** if the gap between the marker and `src.timestamp_seconds` is ≤ 120 seconds.
5. If the gap is > 120 seconds: classify the entry as `QUOTE_FOUND_WRONG_TIME`.

`document` entries have no timestamp — skip this step for them.

---

## 4. Speaker Attribution Verification

Transcripts typically tag speakers as `[Speaker Name]:` or `[SPEAKER NAME]:` before each utterance.

For each `sources[]` entry:

1. Find the speaker tag on the line immediately before (or containing) the matched quote.
2. Normalize both the transcript speaker and `src.speaker`:
   - Case-insensitive
   - Strip role labels in parentheses (e.g., "Priya (coordination)" → "Priya")
   - Allow nickname/full-name equivalence (e.g., "Adam" matches "Adam Goodyer")
3. If the names match after normalization: speaker is correct.
4. If the names do not match: classify the entry as `SPEAKER_MISMATCH`.
5. For `document` entries, `speaker` may be `null` — this is valid; skip the check.

---

## 5. Classification Scheme

Apply one of the following classifications to each item after running the above checks:

| Classification | Meaning |
|---|---|
| `VERIFIED` | Quote found in transcript near the cited timestamp (within 120s). Speaker matches. |
| `QUOTE_FOUND_WRONG_TIME` | Quote found in transcript but the timestamp is off by more than 120 seconds. |
| `QUOTE_NOT_FOUND` | Quote text not found in the transcript (less than 80% word match). |
| `SPEAKER_MISMATCH` | Quote found and timestamp is correct, but speaker attribution is wrong. |
| `TRANSCRIPT_MISSING` | Transcript file not found at the derived path. Cannot verify. |
| `DOCUMENT_MISSING` | Non-Fathom source document not found at the stated path. Cannot verify. |
| `NO_SOURCES` | Item has empty or missing `sources[]`. Cannot verify — a pre-merge gate violation that should never reach this layer. |

---

## 6. Statistical Claim Verification

Run this check on every item that carries numerical fields (hours, costs, headcount, percentages).

### 6a. Identify numerical fields to check

| Item type | Fields to check |
|---|---|
| Process steps | `duration_minutes`, `time_estimate_hours_per_week`, `headcount` |
| Pain points | Any number in `description` or `impact` (hours, %, dollar amounts) |
| Waste items | `hours_per_week`, `headcount_affected`, `annual_waste_aud` |
| Optimisations | Any number in `description` |

### 6b. Verify the number appears in the source quote

For each number identified:
1. Check whether the `source_quote` contains the number itself, or a close verbal equivalent (e.g., "half an hour" for 0.5, "a couple hours" for ~2, "about three hours" for 3).
2. Numbers must be within 20% tolerance for verbal approximations (e.g., "about 3 hours" supports 2.5 to 3.5 hrs/week).
3. For `annual_waste_aud`: the source_quote does not need to contain the dollar figure — but it must contain the hours or frequency figure that the `calculation_note` uses to derive it. If the derivation inputs are in the quote, classify as `STAT_SUPPORTED`.

### 6c. Classify each numerical claim

| Classification | Meaning |
|---|---|
| `STAT_SUPPORTED` | The number (or verbal equivalent within 20%) appears in or is derivable from `source_quote`. |
| `STAT_UNSUPPORTED` | `source_quote` exists but does not contain or support the specific number. The quote may describe the activity in general terms but the number was estimated without transcript backing. |
| `STAT_NO_SOURCE` | `source_quote` is null or empty. No source at all. |

---

## 7. Proposed Changes for Source Issues

Items flagged during source verification should be surfaced as proposed changes in the review summary using category codes:

| Code | Category | Severity | Default action |
|---|---|---|---|
| `[SOURCE]` | QUOTE_NOT_FOUND | HIGH | Flag for follow-up question — extract or confirm the quote in the next session |
| `[SOURCE]` | SPEAKER_MISMATCH | MEDIUM | Correct speaker attribution if evidence is clear, otherwise flag |
| `[SOURCE]` | QUOTE_FOUND_WRONG_TIME | LOW | Update `source_timestamp_seconds` to the correct value |
| `[SOURCE]` | STAT_UNSUPPORTED | MEDIUM | Flag for follow-up question — confirm the specific figure with the client |
| `[SOURCE]` | STAT_NO_SOURCE | HIGH | Flag for follow-up question — item has no citation at all |
| `[SOURCE]` | TRANSCRIPT_MISSING | LOW | Note only — transcript file missing from local filesystem |
| `[SOURCE]` | DOCUMENT_MISSING` | LOW | Note only — source document not found |

For QUOTE_NOT_FOUND and STAT_NO_SOURCE items, draft a follow-up question targeted at confirming the specific claim. Add to `follow_up_questions[]` as a proposed change with `source: "{PR|FR|WR}"` in the reason field.

---

## 8. Efficiency Notes

- Read each transcript file once per session, then reuse the in-memory content for all items in that session.
- If a client has multiple sessions, read each session transcript once.
- For large transcripts (>5,000 words), search using sliding windows rather than reading the full file on each check.
- If the transcript file cannot be read (permissions, empty file), classify all items from that session as `TRANSCRIPT_MISSING` and note it in the summary.
