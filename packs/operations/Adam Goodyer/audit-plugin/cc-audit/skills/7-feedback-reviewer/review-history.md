---
name: review-history
description: Display all review rounds for a client. Internal view shows full detail with old/new values and quotes. Client-facing view shows a clean timeline as proof of human QA.
menu-code: RH
---

# Review History (RH)

Displays the complete review history for a client. Two output modes: internal (full detail) and client-facing (clean proof of human review).

---

## Process

### 1. Load reviews.json

Read `clients/{slug}/03-audit/data/reviews.json`. If it does not exist, report "No review rounds recorded for {company_name} yet."

### 2. Ask for view mode

```
REVIEW HISTORY -- {company_name}
{n} review rounds recorded

  [I] Internal view    -- full detail: all changes, old/new values, quotes
  [C] Client-facing    -- clean timeline for proof of human review
  [E] Export markdown  -- save internal view to clients/{slug}/03-audit/reviews/review-history.md

Select view:
```

---

## Internal View

```
REVIEW HISTORY -- {company_name}
══════════════════════════════════════════════════════════════

ROUND 1 — RR-001
  Reviewer: Adam Goodyer (Internal PM)
  Source: Loom video | {title}
  Recorded: {date} | Duration: {n}m {n}s
  Ingested: {date}
  Status: Applied

  ITEMS APPLIED ({n})
  ─────────────────────────────────────────────────────────────
  [FB-001] HIGH | correction — findings.json > W-003
    Title: Manual data entry during onboarding
    hours_per_week:     10   →   1.5
    annual_waste_aud:   $27,040   →   $4,056  (cascaded)
    monthly_waste_aud:  $2,253    →   $338    (cascaded)
    Quote: "this waste item, the ten hours a week for data entry, that's way off"
    Timestamp: 0:45

  [FB-002] MEDIUM | clarification — findings.json > PP-007
    Title: Invoice follow-up is manual
    description: "Staff manually chase overdue invoices via phone each week"
              → "Staff call clients 7 days overdue; 14-day cases escalated to director"
    Quote: "it's not just manual, there's a specific process"
    Timestamp: 3:12

  [FB-003] LOW | endorsement — opportunities.json > CH-005
    Title: Automated invoice generation
    Reviewer confirmed this change is accurate. No field changes.
    Quote: "yeah that one's spot on, that's exactly what we need"
    Timestamp: 4:30

  ITEMS REJECTED ({n})
  ─────────────────────────────────────────────────────────────
  [FB-008] LOW | correction — findings.json > W-007
    PM rejected: "Reviewer was describing a future state, not a correction to current data"

  UNRESOLVED ITEMS ({n})
  ─────────────────────────────────────────────────────────────
  [UR-001] Quote: "and that pricing one, it's off" (2:03)
    Not mapped — manually identified as CH-003 (pricing card) after review
    Deferred for next round.

ROUND 2 — RR-002
  ...

══════════════════════════════════════════════════════════════
TOTALS ACROSS ALL ROUNDS
  Total items reviewed: {n}
  Corrections applied: {n}
  Items removed: {n}
  Items added: {n}
  Endorsements: {n}
  Items rejected/deferred: {n}
  Domains corrected: findings, opportunities, extraction

PATTERN SIGNALS
  {any patterns detected across rounds for this client}
```

---

## Client-Facing View

```
HUMAN REVIEW RECORD — {company_name}
══════════════════════════════════════════════════════════════

This document confirms that all AI-generated audit analysis has been reviewed
by a qualified human analyst before delivery.

REVIEW TIMELINE

  ROUND 1 — {date}
  Reviewer: Adam Goodyer, Senior Process Analyst, APG Software
  Source: Video walkthrough ({n} minutes)
  Items reviewed: {n}
  Corrections applied: {n}  |  Confirmed accurate: {n}

  CORRECTIONS SUMMARY
  ─────────────────────────────────────────────────────────────
  • Manual data entry time estimate corrected from initial analysis
  • Invoice follow-up process description refined for accuracy
  • [n other corrections summarized without exposing raw data]

  ENDORSEMENTS
  ─────────────────────────────────────────────────────────────
  The following items were explicitly confirmed as accurate during review:
  • Automated invoice generation opportunity
  • [n other endorsed items]

  ROUND 2 — {date}  (if applicable)
  ...

══════════════════════════════════════════════════════════════
REVIEW STATUS: {n} rounds completed
FINAL REVIEW DATE: {date of last applied round}
DELIVERABLES UPDATED: {list of regenerated HTML files}

All financial calculations, time estimates, and process descriptions in this
audit have been cross-checked by a human analyst and reflect the most accurate
available information from client sessions.
```

Note: the client-facing view does not expose raw reviewer quotes, old/new values, or specific item IDs. It is a summary of the human review process.

---

## Export Markdown

If `[E]` selected, save the internal view to `clients/{slug}/03-audit/reviews/review-history.md`. Confirm save path.
