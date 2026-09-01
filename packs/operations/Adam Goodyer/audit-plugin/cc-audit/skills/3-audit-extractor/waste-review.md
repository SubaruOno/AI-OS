---
name: waste-review
description: Deep QA of waste items — deduplicate, detect overlaps, verify math, check source traceability, link to pain points, and calculate adjusted totals. Presents all findings for approval before modifying data.
menu-code: WR
---

# Waste Review

## Purpose

Systematic quality assurance pass on all `waste_items[]` in audit-data.json. Run this after extraction sessions are substantially complete and before marking `audit_status: process_map_complete`. It catches issues that extraction sub-agents cannot catch: duplicates across sources, overlaps that inflate the total, math errors, figures that aren't traceable to a source quote, and unrealized revenue items that need quantification follow-up.

Output is a numbered list of proposed changes. Nothing is modified until you confirm.

## Process

### Step 1: Load and Inventory

Check for `audit-manifest.json` in `clients/{client_slug}/03-audit/data/`. If present, this is a v4 client: read `clients/{client_slug}/03-audit/data/meta.json` and `clients/{client_slug}/03-audit/data/findings.json` directly. If `audit-manifest.json` does not exist, fall back to reading `audit-data.json` as v3/v2.

Extract into working variables:
- `waste_items[]` — the full array
- `pain_points[]` — for cross-referencing in Step 6
- `follow_up_questions[]` — to avoid duplicating questions in Step 7
- `blended_hourly_rate_aud` (always `50` by convention)

Display the opening inventory:

```
WASTE REVIEW: {company_name}
═══════════════════════════════════════════════════
Waste items:         {total}
  Operational:       {n}  (activity + annual_waste_aud)
  Unrealized rev:    {n}  (waste_type: unrealized_revenue)
  Quantified:        {n}  (annual_waste_aud or annual_value populated)
  Unquantified:      {n}

Gross annual total:  ${sum} (naive, before dedup/overlap adjustments)
Blended rate:        $50/hr (assumed, canonical)

Running {n} checks…
```

---

### Step 2: Duplicate Detection

Compare every pair of waste items for semantic overlap. Focus on:

1. **Same activity, different wording** — the same process step described from two different source documents or sessions.
2. **Same stage + very similar hours** — items in the same process stage with `hours_per_week` within 10% of each other and overlapping descriptions.
3. **Same source data point** — two items whose `calculation_note` or `source_quote` references the same stated figure.

For each duplicate pair, present a side-by-side comparison:

```
DUPLICATE CANDIDATES
──────────────────────────────────────────────────────────────────
[DUP-1] W-XXX ↔ W-YYY  — LIKELY DUPLICATE
  W-XXX: "{activity}"
    Source: {source_session}/{source_document} | {hours_per_week} hrs/wk | ${annual_waste_aud}/yr | {confidence}
  W-YYY: "{activity}"
    Source: {source_session}/{source_document} | {hours_per_week} hrs/wk | ${annual_waste_aud}/yr | {confidence}
  Reason: {explanation of why these are duplicates}
  Recommendation: Keep W-YYY (reason). Merge W-XXX into it.
    Action: Delete W-XXX. Transfer W-XXX meeting_references to W-YYY.
             Add merge_note to W-YYY. Annual saving: -${amount}
──────────────────────────────────────────────────────────────────
```

Keep the item with higher confidence. If confidence is equal, keep the one with richer `calculation_note` or `source_quote`. Transfer all `meeting_references` from the removed item to the surviving item. Add `merge_note` to the surviving item: `"Merged from {removed_id}. Original source: {source_session/document}"`.

If no duplicates are found, state "No duplicate pairs detected."

---

### Step 3: Overlap Detection

Find items that are genuinely distinct activities but share a time component — summing both would double-count hours worked.

Look for:
1. **Superset/subset** — item A describes a broader time block that includes the specific time described by item B.
2. **Same staff, same time window** — two items both count the same person's hours in the same period.
3. **Self-documented overlaps** — items where `calculation_note` already contains phrases like "overlaps with", "net additional", or "excludes".

For each overlap group:

```
OVERLAP GROUPS
──────────────────────────────────────────────────────────────────
[OG-1] W-XXX ⊃ W-YYY  — SUPERSET/SUBSET
  W-XXX: "{activity}" — {hours_per_week} hrs/wk (${annual_waste_aud}/yr)
  W-YYY: "{activity}" — {hours_per_week} hrs/wk (${annual_waste_aud}/yr)
  Relationship: {explanation}
  Naive sum:   ${naive}/yr
  Adjusted:    ${adjusted}/yr  (W-YYY's hours are included in W-XXX)

  Both items are kept — they may map to different proposed_changes.
  Proposed fix: Set W-YYY.overlap_adjustment_aud = -${full_annual_waste} (fully subsumed)
    OR:         Set W-YYY.overlap_adjustment_aud = -${partial} (partially subsumed)
  Add overlap_group: "OG-1" to both items.
──────────────────────────────────────────────────────────────────
```

The `overlap_adjustment_aud` field is always negative. The deliverable generator uses it to compute the correct total without losing per-item detail.

If no overlaps are found, state "No overlapping item groups detected."

---

### Step 4: Math Verification

For every operational waste item (anything that is NOT `waste_type: unrealized_revenue`), verify the formula:

`annual_waste_aud = hours_per_week × headcount_affected × $50 × 52`

Where `headcount_affected` defaults to 1 if null, and the rate is always the canonical $50/hr blended team rate. Any per-item rate field in legacy data is ignored.

Steps:
1. Calculate expected value.
2. Compare to stored `annual_waste_aud`. A difference of ≤ $5 (rounding) is acceptable.
3. If `calculation_note` describes a custom formula, check whether the note is complete enough to reproduce the calculation without re-reading the transcript.
4. If `hours_per_week` is null but `annual_waste_aud` is populated, flag as custom/event-based: verify `calculation_note` explains the derivation.

Present a verification table:

```
MATH VERIFICATION
──────────────────────────────────────────────────────────────────
ID      hrs/wk  rate    head  Expected    Stored      Status
──────  ──────  ──────  ────  ──────────  ──────────  ──────────
W-001   0.08    $50     1     $208        $208        ✓
W-017   1.00    $50     1     $2,600      $5,200      ✗ MISMATCH
  → Stored is 2× expected. Check calculation_note.
W-028   null    $50     —     —           $1,992      ⚠ Custom
  → No hours_per_week. Needs calculation_note explaining derivation.
──────────────────────────────────────────────────────────────────
Verified: {n}  |  Rounding OK: {n}  |  Mismatches: {n}  |  Custom/unverifiable: {n}
```

For each mismatch, propose the corrected `annual_waste_aud` value (and `monthly_waste_aud` if present). For custom items with no `calculation_note`, generate a follow-up question (Step 7).

---

### Step 5: Source Traceability

Load `references/source-verification.md` and follow the procedures in that file for all sub-checks below.

#### Step 5a: Citation Quality Rating and Statistical Claim Verification

For each waste item, assess whether `source_quote` explicitly supports the specific numerical figures. This is a combined check — rate as:

- **TRACED** — `source_quote` exists AND explicitly contains or supports the specific `hours_per_week` figure (or verbal equivalent within 20% tolerance). Speaker and session/document identified. See `source-verification.md` Section 6b for tolerance rules.
- **WEAK** — `source_quote` exists but is vague: it describes the activity in general terms without mentioning the specific number. "It takes a while" does not support `hours_per_week: 3.5`. "This is tribal knowledge" does not support any figure. The figure was estimated without transcript backing.
- **UNTRACED** — `source_quote` is empty or null.

**The WEAK classification is intentionally strict for waste items.** A quote that does not contain the claimed hours, frequency, or a close verbal equivalent is WEAK — not TRACED — regardless of how well it describes the activity.

For `annual_waste_aud` specifically: the source_quote does not need to contain the dollar figure, but it must contain the hours or frequency figure that `calculation_note` uses to derive it. If neither input appears in the quote, classify as WEAK.

```
SOURCE TRACEABILITY — STATISTICAL VERIFICATION
──────────────────────────────────────────────────────────────────
ID      Claimed     Key Figure In Quote?               Status
──────  ──────────  ─────────────────────────────────  ──────────
W-001   2.0 hrs/wk  "about two hours every week"       TRACED
W-014   2.5 hrs/wk  "This is tribal knowledge"         WEAK
  → No time figure in quote. Follow-up needed: confirm 2.5 hrs/wk.
W-028   custom $    "it costs us quite a bit"          WEAK
  → No dollar or hours figure. calculation_note must explain derivation.
W-032   1.0 hrs/wk  (no source_quote)                  UNTRACED
  → No citation at all.
──────────────────────────────────────────────────────────────────
TRACED: {n}  |  WEAK: {n}  |  UNTRACED: {n}
```

WEAK and UNTRACED items get follow-up questions in Step 7, scoped to confirming the specific figure. Do not lower confidence ratings automatically — the user decides.

#### Step 5b: Source Existence Verification

For all items classified TRACED or WEAK (with a source_session or source_document), read the actual transcript or document file and verify the citation using the full procedure in `source-verification.md` Sections 1-5.

Read each transcript file once per session and reuse it across all waste items from that session.

```
SOURCE EXISTENCE VERIFICATION
──────────────────────────────────────────────────────────────────
Sessions verified: {n} transcript files read

Waste ID  Session  Result                    Notes
────────  ───────  ────────────────────────  ─────────────────────────────────────────
W-001     S1       VERIFIED                  Quote found at [23:42], speaker matches
W-014     S2       QUOTE_NOT_FOUND           "tribal knowledge" not in Session 2 transcript
W-022     S1       QUOTE_FOUND_WRONG_TIME    Quote at [44:10], cited timestamp was [12:00]
W-031     S3       SPEAKER_MISMATCH          Quote attributed to "Priya", transcript shows "Morgan"
──────────────────────────────────────────────────────────────────
VERIFIED: {n}  |  WRONG_TIME: {n}  |  NOT_FOUND: {n}  |  MISMATCH: {n}  |  MISSING: {n}
```

QUOTE_NOT_FOUND items are added to the follow-up question drafting in Step 7 (alongside WEAK and UNTRACED items already handled there). SPEAKER_MISMATCH items become `[SOURCE]` proposed changes. QUOTE_FOUND_WRONG_TIME items become timestamp correction proposals.

#### Step 5c: Source Linkage Verification

A waste item can pass citation quality (TRACED) while still being unlinked in the deliverable. This check catches items where `source_quote` is populated but the metadata needed to render a clickable Fathom link is missing.

For every waste item where `source_quote` is not null, verify these fields are populated:
- `source_session` — which session the quote came from (e.g., "S1", "S2")
- `source_timestamp_seconds` — the numeric timestamp in the recording
- `meeting_references[]` — at least one entry linking to the Fathom meeting

Flag as **TRACED_UNLINKED** when `source_quote` exists but any of `source_session`, `source_timestamp_seconds`, or `meeting_references` is null/empty.

For each TRACED_UNLINKED item:
1. Search the quote text against all transcript files (already loaded in Step 5b).
2. If found, propose the correct `source_session`, `source_timestamp_seconds`, and a `meeting_references` entry with the `meeting_id` from `sessions[]`.
3. If not found in any transcript, check whether the quote came from a document source (`source_document` field). Document-sourced items need `source_document` populated instead of `source_session`/`source_timestamp_seconds` — these are correctly unlinked from Fathom and should be classified as `DOCUMENT_SOURCED`, not flagged.

```
SOURCE LINKAGE VERIFICATION
──────────────────────────────────────────────────────────────────
Waste items with source_quote but missing linkage fields:

Waste ID  Has Quote  source_session  timestamp_seconds  meeting_refs  Status
────────  ─────────  ──────────────  ─────────────────  ────────────  ──────────────
W-001     ✓          S1              1422               1 entry       LINKED
W-014     ✓          null            null               []            TRACED_UNLINKED
  → Quote found in Session 2 at [31:05]. Propose: source_session="S2",
    source_timestamp_seconds=1865, meeting_references=[{meeting_id from sessions[]}]
W-013     ✓          null            null               []            TRACED_UNLINKED
  → Quote from developer brief. Propose: source_document="developer-brief.md"
    Reclassify as DOCUMENT_SOURCED.
──────────────────────────────────────────────────────────────────
LINKED: {n}  |  TRACED_UNLINKED: {n}  |  DOCUMENT_SOURCED: {n}
```

TRACED_UNLINKED items become `[SOURCE_LINK]` proposed changes in the summary. These are mechanical corrections (the quote exists, just needs the metadata populated) and are safe for auto-approval.

---

### Step 6: Pain Point Cross-Reference

Cross-reference `waste_items[]` against `pain_points[]`. For each waste item, identify semantically matching pain points and propose `related_pain_point_ids[]` links.

A match exists when:
- The waste item and pain point describe the same root activity (manual data entry, missing automation, communication gap, etc.)
- The waste item and pain point share the same stage and tool

Flag orphan waste items (no matching pain point) — these may need a new pain point created, or they may be legitimate standalone items.

```
PAIN POINT LINKAGE
──────────────────────────────────────────────────────────────────
W-001  Manual invoice push to Xero daily
  → PP-012 "Manual daily invoice process — no push from Timely"
W-004  Manual quote preparation per enquiry
  → PP-001 "No automation from lead form to quote"
     PP-003 "Quote preparation relies on memory and templates"
W-033  Dormant TikTok channel
  → ORPHAN — no matching pain point in acquisition stage
──────────────────────────────────────────────────────────────────
Linked: {n}  |  Multi-linked: {n}  |  Orphan: {n}
```

---

### Step 7: Unrealized Revenue Assessment

For each item with `waste_type: unrealized_revenue`:

1. Check whether `annual_waste_aud` (or `annual_value`) is populated.
2. If null, identify what specific data point is needed to estimate it.
3. Check `follow_up_questions[]` — is there already an open question targeting this gap?
4. If not, draft a new follow-up question.

```
UNREALIZED REVENUE STATUS
──────────────────────────────────────────────────────────────────
ID     Title                              Value        Gap / Status
──────  ─────────────────────────────────  ───────────  ────────────────────
W-029  Low lead-to-booking conversion     null         Need: monthly lead volume
  → FQ-030 (open) already covers this. No new question needed.
W-030  No follow-up for non-converts      null         Need: re-engagement rate
  → No existing FQ. Draft: "Of the leads who didn't book initially,
     do you have a sense of what percentage you've eventually converted
     when you've followed up manually?"
W-035  No proactive add-on upsell         $10,830      ✓ Quantified
W-036  Cancellation slot revenue leakage  $34,008      ✓ Quantified
──────────────────────────────────────────────────────────────────
Quantified: {n}/{total}  |  New FQs needed: {n}
```

---

### Step 8: Text Quality

Client-facing text in waste items flows directly into HTML deliverables. Run this check before the summary so any AI-sounding language is caught at the data layer.

Load `${CLAUDE_PLUGIN_ROOT}/context/brand/brand-voice.md` — specifically the "Master Forbidden Words List", "Forbidden Phrases" table, and "Structural Anti-Patterns" sections.

Scan these fields on every waste item:
- `activity`, `title`, `description`, `correction_note`, `annual_value_note`
- `calculation_note` — scan for em dashes and forbidden words only (math formulas are necessarily formulaic; don't flag formality in calculations)

Check for four issue types:

**1. Em dashes (`—`)** — never used in APG output. Replace with a comma, colon, or rewrite the clause.

**2. Forbidden words** — flag any instance from the brand voice list. Common offenders: leverage, utilize, facilitate, comprehensive, seamless, innovative, groundbreaking, furthermore, additionally, moreover, ecosystem, synergy, necessitate, elevate, streamline, "it is important to", "it is essential to", "not just X but Y".

**3. Overly formal phrasing** — language a business owner wouldn't use when describing their own operations. Flag and propose a plain-English replacement. Examples: "necessitates manual intervention" → "requires manual work", "facilitates the coordination of" → "coordinates", "subsequent to the initial engagement" → "after the first meeting".

**4. Parallel structure** — if 3 or more consecutive `activity` descriptions use identical sentence patterns (same length, same grammatical opener), flag them and propose variation for at least one.

Present findings grouped by issue type:

```
TEXT QUALITY
──────────────────────────────────────────────────────────────────
Em dashes:  {n}
  W-007 activity: "Manual upload to DVA portal — repeated for every clean"
    → "Manual upload to DVA portal, repeated for every clean"

Forbidden words:  {n}
  W-012 description: "…facilitates the manual reconciliation process…"
    → "…drives the manual reconciliation…"

Overly formal phrasing:  {n}
  W-019 activity: "Manual intervention required to resolve payment gateway exceptions"
    → "Manual work to resolve payment gateway errors"

Parallel structure:  {n}
  W-001, W-002, W-003 all open with "Manual process for…"
    → Keep W-001. Rewrite W-002: "{activity} is done by hand".
      Rewrite W-003: "Staff manually {verb}…".

Clean:  {W-IDs with no issues}
──────────────────────────────────────────────────────────────────
Total text issues:  {n} across {n} waste items
```

Each issue becomes a `[TEXT]` change in the summary. Group multiple fixes on the same item into one entry.

---

### Step 9: Summary and Adjusted Totals

Present all findings in a single consolidated view before any changes are made.

```
WASTE REVIEW COMPLETE — {company_name}
═══════════════════════════════════════════════════════════════════

FINDINGS
  Duplicates found:           {n} pairs
  Overlaps found:             {n} groups
  Math mismatches:            {n} items
  Weak/untraced sources:      {n} items
  Statistical claims untraced: {n} (hours/frequency not in source_quote)
  Quotes not found in transcripts: {n}
  Speaker mismatches:         {n}
  Timestamp corrections:      {n}
  Pain point links added:     {n} items
  Unquantified revenue:       {n} items  (${potential} potential)
  Text quality issues:        {n} items ({n} fields)

TOTALS
                     Before         After
  ────────────────────────────────────────
  Operational:       ${gross}        ${adjusted}
  Overlap deduct:    -              -${overlap_total}
  Items removed:     -              -{merged_count}
  ────────────────────────────────────────
  Net operational:   ${gross}        ${net}  ({pct_change})
  Unrealized rev:    ${rev}          ${rev}  (no change)

PROPOSED CHANGES ({n} total):
  {sequential numbered list — one line each}
  1. [MERGE] W-004 → W-016 (same manual quoting activity, different sources). Remove W-004, transfer references. Save -$2,797/yr.
  2. [OVERLAP] W-015/W-037 overlap group OG-1. Add overlap_adjustment_aud: -$5,395 to W-015.
  3. [MATH FIX] W-017: annual_waste_aud $4,316 → $2,158 (stored is 2× formula result).
  4. [SOURCE] W-014: "2.5 hrs/wk" not in source_quote — add follow-up question to confirm (WEAK)
  5. [SOURCE] W-031: speaker attribution mismatch — update speaker to "Morgan" (SPEAKER_MISMATCH)
  6. [SOURCE] W-022: update source_timestamp_seconds to {correct value} (QUOTE_FOUND_WRONG_TIME)
  7. [LINK] Add related_pain_point_ids to {n} items (see Step 6 table).
  8. [TEXT] W-007: remove em dash in activity description
  9. [TEXT] W-012: replace "facilitates" → "drives" in description
  ...

NEW FOLLOW-UP QUESTIONS ({n}):
  {list new questions drafted in Steps 5 and 7}

Apply changes? Enter a number range (e.g. 1-4), specific numbers (e.g. 1,3,5), ALL, or NONE.
```

---

### Step 10: Apply Changes

Wait for user input. Do not proceed until confirmed.

**ALL** — apply every proposed change.
**NONE** — discard all, exit without modifying data.
**Specific** — user enters numbers or ranges; apply only those.

For each approved change, execute in this order:

1. **Merges** — remove the duplicate item from `waste_items[]`; add `meeting_references` from removed item to surviving item; add `merge_note` to surviving item.
2. **Overlap adjustments** — add `overlap_group`, `overlap_adjustment_aud`, and `overlap_note` to the affected items.
3. **Math fixes** — update `annual_waste_aud` (and `monthly_waste_aud` if present) to the correct value; add a `calculation_note` if missing.
4. **Pain point links** — add `related_pain_point_ids[]` to each item identified in Step 6.
5. **New follow-up questions** — append to `follow_up_questions[]`. Format: same structure as existing FQs. Set `source: "WR"` inside the `reason` field to distinguish from GQ-generated questions. Increment `follow_up_summary` counts.
6. **Schema normalizations** (if any were proposed) — rename non-canonical field names to canonical equivalents.
7. **Text quality fixes** — apply the approved string replacements to the specified fields on each flagged waste item.

After all changes are applied, write back to the audit data. For v4 clients: write the full `findings.json` with updated waste_items (including overlap_adjustment_aud, merge_note, related_pain_point_ids) and any new follow_up_questions, then update `audit-manifest.json` (`domains.findings.updated_at` and root `updated_at`). For v3 files: write updated waste_items and follow_up_questions into the `findings` domain object in `audit-data.json`. For v2 files: write to top-level keys as before.

Report:

```
Waste review applied.
  Merged:          {n} duplicate items removed
  Overlaps tagged: {n} groups ({n} items)
  Math fixed:      {n} items
  Links added:     {n} items
  FQs added:       {n}

  Gross annual before: ${before}
  Net annual after:    ${after}  ({delta} adjustment)

Run the validator to confirm data integrity:
  python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py clients/{client_slug}/03-audit/data/audit-data.json
```

---

## New Fields Introduced

These fields are additive — they do not replace existing fields. Downstream agents that don't yet read them will safely ignore them.

| Field | Type | Scope | Purpose |
|---|---|---|---|
| `overlap_group` | string | waste_items | Groups overlapping items (e.g., "OG-1") |
| `overlap_adjustment_aud` | number (negative) | waste_items | Deduction to correct double-counting in totals |
| `overlap_note` | string | waste_items | Human-readable explanation of the overlap |
| `related_pain_point_ids` | string[] | waste_items | Pain point IDs this waste item links to |
| `merge_note` | string | waste_items | Records what duplicate was absorbed and from which source |

The deliverable generator (waste.html) should sum `annual_waste_aud + overlap_adjustment_aud` for each item when computing the displayed total, treating null `overlap_adjustment_aud` as 0.
