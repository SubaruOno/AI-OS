---
name: findings-review
description: Deep QA of pain points — deduplicate, detect root-cause overlaps, verify stage assignments, normalize team names, check source traceability, link to waste items and optimisations. Presents all findings for approval before modifying data.
menu-code: FR
---

# Findings Review

## Purpose

Systematic quality assurance pass on all `pain_points[]` in audit-data.json. Run this after extraction sessions are substantially complete and before marking `audit_status: process_map_complete`. It catches issues that per-session extraction misses: duplicate pain points from different sessions or speakers, overlapping root causes that inflate apparent scope, incorrect stage assignments, and unlinked relationships to waste items and optimisations.

Output is a numbered list of proposed changes. Nothing is modified until you confirm.

## Process

### Step 1: Load and Inventory

Check for `audit-manifest.json` in `clients/{client_slug}/03-audit/data/`. If present, this is a v4 client: read `clients/{client_slug}/03-audit/data/meta.json`, `clients/{client_slug}/03-audit/data/extraction.json` (for stage keys), and `clients/{client_slug}/03-audit/data/findings.json` directly. If `audit-manifest.json` does not exist, fall back to reading `audit-data.json` as v3/v2.

Extract into working variables:
- `pain_points[]` — the full array
- `processes[]` — valid stage keys for Step 5 verification (from `extraction.json` in v4, `extraction` domain in v3)
- `waste_items[]` — for cross-reference linking in Step 7
- `optimisations[]` — for cross-reference linking in Step 7
- `staff_roster[]` — for name normalization in Step 4
- `follow_up_questions[]` — to avoid duplicating questions

Display the opening inventory:

```
FINDINGS REVIEW — {company_name}
═══════════════════════════════════════════════════════════════════
Pain points:         {total}
  By stage:
    acquisition:     {n}
    quoting:         {n}
    [each stage]     {n}
    [ungrouped]:     {n}  (stage field missing or invalid)

Risk signals:        {n}
Confidence:
  HIGH:              {n}
  MEDIUM:            {n}
  LOW:               {n}

With source quote:   {n}/{total}
With owner:          {n}/{total}

Waste items:         {waste_total}  (for cross-reference)
Optimisations:       {opt_total}    (for cross-reference)

Running {n} checks…
```

---

### Step 2: Duplicate Detection

Compare every pair of pain points for semantic overlap. Focus on:

0. **Reclassified items** — pain points with `source: "reclassified"` were originally process steps moved here by the process review (PR). These often overlap with existing pain points extracted from the same transcript quote. Check these first before running the broader duplicate scan.

1. **Same stage + same root issue** — the same problem described from two different sessions or speakers.
2. **Same source quote referenced** — two pain points that cite the same verbatim extract.
3. **Symptom and re-statement** — one pain point describes "no automation" and another describes "manual entry takes 2 hrs" for the same activity (same thing, different framing).

For each duplicate pair:

```
DUPLICATE CANDIDATES
──────────────────────────────────────────────────────────────────
[DUP-1] PP-003 ↔ PP-019  — LIKELY DUPLICATE
  PP-003: "No automation from lead form to quote"
    Stage: acquisition | Session 1 | Speaker: Jordan | Confidence: HIGH
    Quote: "{source_quote[:80]}…"
  PP-019: "Lead enquiries require manual follow-up every time"
    Stage: acquisition | Session 3 | Speaker: Morgan | Confidence: HIGH
    Quote: "{source_quote[:80]}…"
  Reason: Both describe the manual effort gap between lead receipt and quote dispatch.
           Same root issue, different session framing.
  Recommendation: Keep PP-003 (richer description, Session 1 context).
    Action: Remove PP-019. Transfer meeting_references to PP-003.
            Add merge_note to PP-003.
──────────────────────────────────────────────────────────────────
```

Keep the richer item: prefer higher confidence, more specific impact statement, earlier session. Transfer all `meeting_references` from the removed item. Add `merge_note`: `"Merged from {removed_id}. Source: Session {n}, {speaker}"`.

If no duplicates are found, state "No duplicate pain points detected."

---

### Step 3: Root-Cause Overlap Detection

Find pain points that are genuinely distinct (different symptoms, different owners, different descriptions) but share the same root cause. Unlike duplicates — which should be merged — overlapping root causes should be grouped so the downstream analyst knows they all point to the same fix.

Overlap signals:
- Different symptoms of a missing integration (e.g., "manual invoice creation" and "payment status not visible" — both caused by no Xero-Timely sync)
- Cause and effect pairs (e.g., "quoting takes too long" and "clients drop off before receiving quote" — same root: slow quoting process)
- Same tool mentioned as the source of friction in multiple pain points

```
OVERLAP GROUPS
──────────────────────────────────────────────────────────────────
[RG-1] Root cause: "No Timely → Xero integration"
  PP-011 "Manual invoice creation from Timely jobs" — fulfilment
  PP-023 "Payment status not visible without logging into Xero" — administration
  PP-027 "Reconciliation done by exporting CSVs from both tools" — administration
  Relationship: All three are symptoms of no automated sync between Timely and Xero.
  Proposed: Add overlap_group "RG-1" to all three. Add overlap_note explaining root cause.
  Note: DO NOT merge — these are distinct pain points. The group label allows the
        Researcher to identify them as a single proposed_change.

[RG-2] Root cause: "Absence cover is undocumented"
  PP-014 "No documented process when Morgan is on leave" — administration
  PP-031 "Client communication drops during coordinator absence" — fulfilment
  PP-038 "Cleaner reassignment is ad hoc and verbal only" — fulfilment
  Relationship: All stem from no documented handover or cover protocol.
──────────────────────────────────────────────────────────────────
Overlap groups identified: {n} | Pain points grouped: {n}
```

If no overlaps are found, state "No root-cause overlap groups detected."

---

### Step 4: Team Member Consistency

Cross-reference `owner` and `speaker` field values in pain_points against `staff_roster[].name`.

Detect:
- Name variants (same pattern as Process Review Step 2)
- Speakers not on the staff roster (may be a new person or a transcription error)
- Pain points attributed to an owner who was not present in that session

```
TEAM MEMBER CONSISTENCY
──────────────────────────────────────────────────────────────────
Owner variants:
  "Morgan" / "Morgan Reed" — {n} pain points affected
    Canonical: "Morgan Reed"
    Action: Normalize {n} pain points

Speaker anomalies:
  PP-044 speaker: "Annette" — not on staff roster
    → Annette Coghill appears in session metadata (S5). Add to roster or confirm name.
  PP-052 speaker: "Unknown" — no speaker attributed
    → Flag — source cannot be traced to a specific team member.

OK: PP-001–PP-010 all use canonical names. No changes needed.
──────────────────────────────────────────────────────────────────
Variants found: {n} | Speaker anomalies: {n}
```

---

### Step 5: Stage Assignment Verification

For each pain point, verify the `stage` value matches an existing stage key in `processes[].stage`.

Then check for logical misassignment — pain points whose description clearly refers to activities in a different stage:

```
STAGE ASSIGNMENT VERIFICATION
──────────────────────────────────────────────────────────────────
Invalid stage keys (not in processes[]):
  PP-047 stage: "admin" — should be "administration"
  PP-051 stage: "onboarding" — no onboarding stage in processes[]
    → Closest match: "fulfilment" (first client visit). Propose reassignment.

Possible misassignments:
  PP-033 stage: "acquisition" — description: "Xero reconciliation is done weekly"
    → Reconciliation is an administration activity. Propose: reassign to "administration"
  PP-049 stage: "quoting" — description: "Cleaners aren't notified of schedule changes"
    → Notification to contractors is fulfilment. Propose: reassign to "fulfilment"

Stage coverage:
  acquisition:     {n} pain points  ✓
  quoting:         {n} pain points  ⚠ 0 — possible gap (check if coverage is genuinely low)
  fulfilment:      {n} pain points  ✓
  retention:       {n} pain points  ✓
  administration:  {n} pain points  ✓
──────────────────────────────────────────────────────────────────
Invalid keys: {n} | Misassignments: {n} | Empty stages: {n}
```

For stages with zero pain points, note whether this is expected (genuinely smooth process) or a gap in extraction.

---

### Step 6: Source Traceability

Load `references/source-verification.md` and follow the procedures in that file for all sub-checks below.

#### Step 6a: Citation Quality Rating

For each pain point, rate the citation quality:

- **TRACED** — `source_quote` exists and explicitly describes the pain. Speaker and session/document identified.
- **WEAK** — `source_quote` exists but is a general complaint or indirect statement that doesn't specifically name this pain.
- **UNTRACED** — `source_quote` is empty or null.

```
SOURCE TRACEABILITY
──────────────────────────────────────────────────────────────────
By stage:
  Acquisition:    TRACED: 8   WEAK: 2   UNTRACED: 0
  Quoting:        TRACED: 5   WEAK: 3   UNTRACED: 2
  Fulfilment:     TRACED: 16  WEAK: 5   UNTRACED: 3
  …

Untraced items (no source_quote):
  PP-038 "Cleaner reassignment is ad hoc and verbal only" — no source_quote
    → Flag for follow-up.
  PP-052 "No KPI tracking for BDM performance" — no source_quote
    → Flag for follow-up.

Weak citations:
  PP-029 "Communication is inconsistent" — too broad.
    Quote: "Sometimes things fall through the cracks."
    → Doesn't name a specific activity or channel. Flag.
──────────────────────────────────────────────────────────────────
TRACED: {n}  |  WEAK: {n}  |  UNTRACED: {n}
```

#### Step 6b: Statistical Claim Verification

Scan `description` and `impact` fields on every pain point for numerical claims (hours per week, dollar amounts, percentages, headcount, frequency counts). For each number found, verify it appears in (or is derivable from) the `source_quote` using the procedure in `source-verification.md` Section 6.

```
STATISTICAL CLAIM VERIFICATION
──────────────────────────────────────────────────────────────────
Pain Point  Field        Claimed Value  Source Quote Supports?  Status
──────────  ───────────  ─────────────  ──────────────────────  ──────────────
PP-011      description  2 hrs/day      "it takes ages"         STAT_UNSUPPORTED
PP-023      impact       $3,200/mo      "costs us a lot"        STAT_UNSUPPORTED
PP-001      description  50 leads/mo    "about 50 a month"      STAT_SUPPORTED
PP-038      description  (none)         (none)                  (no numbers — skip)
──────────────────────────────────────────────────────────────────
STAT_SUPPORTED: {n}  |  STAT_UNSUPPORTED: {n}  |  STAT_NO_SOURCE: {n}
```

STAT_UNSUPPORTED and STAT_NO_SOURCE items become `[SOURCE]` proposed changes in the summary.

#### Step 6c: Source Existence Verification

For all pain points classified TRACED or WEAK, read the actual transcript or document file and verify the citation using the full procedure in `source-verification.md` Sections 1-5.

Read each transcript file once per session and reuse it across all pain points from that session.

```
SOURCE EXISTENCE VERIFICATION
──────────────────────────────────────────────────────────────────
Sessions verified: {n} transcript files read

Pain Point  Session  Result                    Notes
──────────  ───────  ────────────────────────  ─────────────────────────────────────────
PP-001      S1       VERIFIED                  Quote found at [14:32], speaker matches
PP-011      S2       QUOTE_NOT_FOUND           Phrase not found in Session 2 transcript
PP-029      S1       QUOTE_FOUND_WRONG_TIME    Quote at [41:00], cited timestamp was [22:00]
PP-044      S3       SPEAKER_MISMATCH          Quote attributed to "Morgan", transcript shows "Adam"
──────────────────────────────────────────────────────────────────
VERIFIED: {n}  |  WRONG_TIME: {n}  |  NOT_FOUND: {n}  |  MISMATCH: {n}  |  MISSING: {n}
```

QUOTE_NOT_FOUND and SPEAKER_MISMATCH items become `[SOURCE]` proposed changes in the summary. For UNTRACED and QUOTE_NOT_FOUND items, draft a follow-up question to confirm the specific finding with the client — add these as `[SOURCE_FQ]` proposed changes. FR generates follow-up questions from source failures (unlike PR which only flags).

#### Step 6d: Source Linkage Verification

A pain point can pass citation quality (TRACED) while still being unlinked in the deliverable. This check catches items where `source_quote` is populated but the metadata needed to render a clickable Fathom link is missing.

For every pain point where `source_quote` is not null, verify these fields are populated:
- `source_session` — which session the quote came from (e.g., "S1", "S2")
- `source_timestamp_seconds` — the numeric timestamp in the recording
- `meeting_references[]` — at least one entry linking to the Fathom meeting

Flag as **TRACED_UNLINKED** when `source_quote` exists but any of `source_session`, `source_timestamp_seconds`, or `meeting_references` is null/empty.

For each TRACED_UNLINKED item:
1. Search the quote text against all transcript files (already loaded in Step 6c).
2. If found, propose the correct `source_session`, `source_timestamp_seconds`, and a `meeting_references` entry with the `meeting_id` from `sessions[]`.
3. If not found in any transcript, check whether the quote came from a document source (`source_document` field). Document-sourced items need `source_document` populated instead of `source_session`/`source_timestamp_seconds` — these are correctly unlinked from Fathom and should be classified as `DOCUMENT_SOURCED`, not flagged.

```
SOURCE LINKAGE VERIFICATION
──────────────────────────────────────────────────────────────────
Pain points with source_quote but missing linkage fields:

Pain Point  Has Quote  source_session  timestamp_seconds  meeting_refs  Status
──────────  ─────────  ──────────────  ─────────────────  ────────────  ──────────────
PP-001      ✓          S1              892                1 entry       LINKED
PP-029      ✓          null            null               []            TRACED_UNLINKED
  → Quote found in Session 2 at [41:00]. Propose: source_session="S2",
    source_timestamp_seconds=2460, meeting_references=[{meeting_id from sessions[]}]
PP-038      ✓          null            null               []            TRACED_UNLINKED
  → Quote from developer brief. Propose: source_document="developer-brief.md"
    Reclassify as DOCUMENT_SOURCED.
──────────────────────────────────────────────────────────────────
LINKED: {n}  |  TRACED_UNLINKED: {n}  |  DOCUMENT_SOURCED: {n}
```

TRACED_UNLINKED items become `[SOURCE_LINK]` proposed changes in the summary. These are mechanical corrections (the quote exists, just needs the metadata populated) and are safe for auto-approval.

---

### Step 7: Cross-Reference Linkage

**Waste item links** — For each pain point, find semantically matching waste items. A match exists when:
- Same stage and same root activity (manual data entry, missing automation, communication gap)
- Pain point describes the problem; waste item quantifies the cost

Propose `related_waste_ids[]` on the pain point.

**Optimisation links** — For each pain point, find matching optimisation items (client-stated desired improvements). A match exists when the optimisation describes the desired resolution of the pain.

Propose `related_optimisation_ids[]` on the pain point.

**Orphan detection** — Flag pain points with no waste item AND no optimisation linked. These may need a new waste item created, or they may be legitimate risk-only findings that don't have a time cost.

```
CROSS-REFERENCE LINKAGE
──────────────────────────────────────────────────────────────────
Pain point → Waste item links:
  PP-001 "No automation from lead form to quote"
    → W-004 "Manual quote preparation per enquiry" (acquisition)
  PP-011 "Manual invoice creation from Timely jobs"
    → W-022 "Manual daily invoice export" (fulfilment)
  PP-038 "Cleaner reassignment is ad hoc"
    → ORPHAN — no matching waste item. No time cost quantified yet.
       Note: This is a risk/quality concern. May not need a waste item.

Pain point → Optimisation links:
  PP-001 "No automation from lead form to quote"
    → OPT-003 "Automate quote generation from enquiry form data"
  PP-011 "Manual invoice creation from Timely jobs"
    → OPT-007 "Timely → Xero integration for automatic invoicing"
  PP-028 "No client retention dashboard"
    → ORPHAN — no matching optimisation stated. Client hasn't articulated desired fix.
──────────────────────────────────────────────────────────────────
Waste links proposed:  {n} pain points
Opt links proposed:    {n} pain points
Orphans (no waste):    {n}
Orphans (no opt):      {n}
```

---

### Step 8: Text Quality

Client-facing text in pain points flows directly into HTML deliverables. Run this check before the summary so any AI-sounding language is caught at the data layer.

Load `${CLAUDE_PLUGIN_ROOT}/context/brand/brand-voice.md` — specifically the "Master Forbidden Words List", "Forbidden Phrases" table, and "Structural Anti-Patterns" sections.

Scan these fields on every pain point:
- `title`, `description`, `impact`, `risk_note`, `overlap_note`

Check for four issue types:

**1. Em dashes (`—`)** — never used in APG output. Replace with a comma, colon, or rewrite the clause.

**2. Forbidden words** — flag any instance from the brand voice list. Common offenders: leverage, utilize, facilitate, comprehensive, seamless, innovative, groundbreaking, furthermore, additionally, moreover, ecosystem, synergy, necessitate, elevate, streamline, "it is important to", "it is essential to", "not just X but Y".

**3. Overly formal phrasing** — language a business owner wouldn't use when describing their own operations. Flag and propose a plain-English replacement. Examples: "necessitates manual intervention" → "requires manual work", "subsequent to the initial engagement" → "after the first meeting", "facilitates the coordination of" → "coordinates".

**4. Parallel structure** — if 3 or more consecutive titles or descriptions use identical sentence patterns (same length, same grammatical opener), flag them and propose variation for at least one.

Present findings grouped by issue type:

```
TEXT QUALITY
──────────────────────────────────────────────────────────────────
Em dashes:  {n}
  PP-011 description: "…data entry — which takes 2 hours…"
    → "…data entry, which takes 2 hours…"

Forbidden words:  {n}
  PP-004 title: "Comprehensive manual quoting process"
    → "Manual quoting process"
  PP-019 description: "…leverage the existing CRM…"
    → "…use the existing CRM…"

Overly formal phrasing:  {n}
  PP-031 description: "This necessitates manual intervention on a daily basis"
    → "This needs manual work every day"

Parallel structure:  {n}
  PP-008, PP-009, PP-010 all open with "No automated process for…"
    → Keep PP-008. Rewrite PP-009: "{activity} is done manually".
      Rewrite PP-010: "Staff handle {activity} by hand".

Clean:  PP-001, PP-002, … {list IDs with no issues}
──────────────────────────────────────────────────────────────────
Total text issues:  {n} across {n} pain points
```

Each issue becomes a `[TEXT]` change in the summary. Group multiple fixes on the same item into one entry.

---

### Step 9: Summary and Approval

Present all findings in a single consolidated view before any changes are made.

```
FINDINGS REVIEW COMPLETE — {company_name}
═══════════════════════════════════════════════════════════════════

FINDINGS
  Duplicates found:             {n} pairs
  Root-cause overlap groups:    {n} groups ({n} pain points grouped)
  Name variants normalized:     {n} clusters ({n} items affected)
  Invalid stage keys:           {n}
  Stage misassignments:         {n}
  Weak/untraced citations:      {n}
  Statistical claims unsupported: {n} (number in description not in source_quote)
  Quotes not found in transcripts: {n}
  Speaker mismatches:           {n}
  Timestamp corrections needed: {n}
  Source follow-up questions:   {n} (drafted for UNTRACED/QUOTE_NOT_FOUND items)
  Waste item links proposed:    {n}
  Optimisation links proposed:  {n}
  Orphan pain points:           {n}
  Text quality issues:          {n} items ({n} fields)

PROPOSED CHANGES ({n} total):
  1. [MERGE] Remove PP-019 — duplicate of PP-003. Transfer references.
  2. [MERGE] Remove PP-041 — duplicate of PP-033. Transfer references.
  3. [GROUP] Add overlap_group "RG-1" to PP-011, PP-023, PP-027 (no Timely→Xero sync)
  4. [GROUP] Add overlap_group "RG-2" to PP-014, PP-031, PP-038 (absence cover gap)
  5. [NORMALIZE] Normalize owner "Morgan" → "Morgan Reed" across {n} pain points
  6. [STAGE] Reassign PP-047 stage "admin" → "administration"
  7. [STAGE] Reassign PP-033 → "administration" (reconciliation is not acquisition)
  8. [LINK] Add related_waste_ids to {n} pain points (see Step 7 table)
  9. [LINK] Add related_optimisation_ids to {n} pain points (see Step 7 table)
  10. [SOURCE] PP-011: "2 hrs/day" not in source_quote — confirm figure with client (STAT_UNSUPPORTED)
  11. [SOURCE] PP-038: no source_quote — flag for follow-up (UNTRACED)
  12. [SOURCE_FQ] Draft follow-up question for PP-038: confirm cleaner reassignment is ad hoc
  13. [SOURCE_FQ] Draft follow-up question for PP-011: confirm "2 hrs/day" figure
  14. [TEXT] PP-011: remove em dash in description ("data entry — which" → "data entry, which")
  15. [TEXT] PP-004: drop "Comprehensive" from title
  ...

Apply changes? Enter a number range (e.g. 1-4), specific numbers (e.g. 1,3,5), ALL, or NONE.
```

---

### Step 10: Apply Changes

Wait for user input. Do not proceed until confirmed.

**ALL** — apply every proposed change.
**NONE** — discard all, exit without modifying data.
**Specific** — user enters numbers or ranges; apply only those.

Execute in this order:

1. **Merges** — remove the duplicate pain point from `pain_points[]`; transfer `meeting_references` from removed item to surviving item; add `merge_note` to surviving item; update `pain_points_summary.total_count` and `by_stage` counts.
2. **Overlap groups** — add `overlap_group` and `overlap_note` to each item in the group. Do not remove items.
3. **Name normalizations** — update `owner` and `speaker` fields on affected pain points.
4. **Stage corrections** — update `stage` field on misassigned items.
5. **Cross-reference links** — add `related_waste_ids[]` and `related_optimisation_ids[]` to each pain point identified in Step 7.
6. **Source follow-up questions** (`[SOURCE_FQ]`) — append drafted questions to `follow_up_questions[]`. Format: same structure as existing FQs. Set `source: "FR"` inside the `reason` field. Increment `follow_up_summary` counts.
7. **Text quality fixes** — apply the approved string replacements to the specified fields on each flagged pain point.

After all changes are applied, write back to the audit data. For v4 clients: write the full `findings.json` with updated pain_points (including overlap_group, overlap_note, merge_note, related_waste_ids, related_optimisation_ids), then update `audit-manifest.json` (`domains.findings.updated_at` and root `updated_at`). For v3 files: write updated pain_points into the `findings` domain object in `audit-data.json`. For v2 files: write to top-level keys as before.

Report:

```
Findings review applied.
  Merged:               {n} duplicate pain points removed
  Overlap groups tagged: {n} groups ({n} items)
  Names normalized:     {n} items
  Stages corrected:     {n} items
  Waste links added:    {n} items
  Opt links added:      {n} items

Run the validator to confirm data integrity:
  python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py \
    clients/{client_slug}/03-audit/data/audit-data.json
```

---

## New Fields Introduced

These fields are additive — they do not replace existing fields. Downstream agents that don't yet read them will safely ignore them.

| Field | Type | Scope | Purpose |
|---|---|---|---|
| `overlap_group` | string (nullable) | pain_points | Groups pain points sharing the same root cause (e.g., "RG-1"). Does not imply merging. |
| `overlap_note` | string (nullable) | pain_points | Human-readable explanation of the root cause shared across the group. |
| `merge_note` | string (nullable) | pain_points | Records what duplicate was absorbed and from which source. |
| `related_waste_ids` | string[] (nullable) | pain_points | Waste item IDs this pain point links to (reverse of WR's `related_pain_point_ids`). |
| `related_optimisation_ids` | string[] (nullable) | pain_points | Optimisation IDs that describe the desired resolution of this pain point. |

The Researcher (EI step) should read `overlap_group` when synthesising `proposed_changes[]` — pain points in the same group likely map to a single proposed change, not multiple.
