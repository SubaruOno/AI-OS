---
name: learn-patterns
description: Analyse feedback patterns across all clients. Surface systematic extraction errors and common reviewer corrections. Generate concrete process improvement recommendations.
menu-code: LP
---

# Learn Patterns (LP)

> **Cross-client analysis capability.** Reads reviews.json across all clients, identifies recurring feedback patterns, and generates targeted recommendations to improve the agent prompts that caused them. Never auto-patches — recommendations are for human review.

---

## Stage 1: Collect All Review Data

Scan `clients/*/audit/reviews.json` across all clients. For each, load:
- All `review_rounds[].feedback_items[]` with `resolution.status == "approved"`
- `round.source.type` (loom_video, text_input)
- Client slug and company name

Build a flat list of all applied corrections across all clients.

```
LP PRE-FLIGHT

Clients with review data: {n}
Total review rounds:       {n}
Total applied items:       {n}
  corrections:    {n}
  removals:       {n}
  additions:      {n}
  clarifications: {n}

Analysing patterns...
```

---

## Stage 2: Detect Patterns

Group applied corrections by type and look for recurrence.

### Pattern types to detect:

**`systematic_overcount`** — time or cost estimates consistently too high
- Signals: multiple corrections where `hours_per_week` or `annual_waste_aud` was reduced
- Check if overcount is concentrated in a specific stage (e.g., onboarding) or source type (self-reported vs observed)

**`systematic_undercount`** — estimates consistently too low
- Signals: multiple corrections increasing time or cost figures

**`hallucination`** — extraction creates items with no source support
- Signals: multiple `removal` corrections where the removed item had confidence LOW or MEDIUM
- Check if removals cluster around a specific capability (SU pass 3 vs pass 4)

**`misattribution`** — items assigned to wrong speaker or stage
- Signals: multiple clarifications correcting `speaker` or `stage` fields

**`missing_context`** — extraction consistently misses a category of data
- Signals: multiple `addition` corrections adding items of a similar type (e.g., consistently missing compliance-related pain points, or HR-related tools)

**`formatting_drift`** — text quality issues recurring
- Signals: multiple clarification corrections fixing similar wording patterns (em dashes, AI-sounding phrases, overly formal language)

### Threshold for reporting:

- Report any pattern with 3+ occurrences across 2+ clients
- Report any pattern with 5+ occurrences even within one client

---

## Stage 3: Generate Recommendations

For each pattern above threshold, generate a concrete recommendation:

```
PATTERN: systematic_overcount
Occurrences: 6 corrections across 3 clients
Concentration: findings.json > waste_items > hours_per_week field
Source: Staff self-reporting (source_type: fathom_meeting)

OBSERVATION
Time estimates extracted from staff self-reporting are consistently 2-4x higher
than actual confirmed values. PM review routinely corrects these downward.

ROOT CAUSE
Sub-agent-extract Pass 1 extracts time estimates as stated without confidence
downgrade for self-reported figures that lack corroboration.

RECOMMENDATION
Add to sub-agent-extract.md Pass 1 instructions:
  "When a staff member states a time estimate for their own task without a second
  source or concrete evidence (logs, timesheets, examples), set confidence: MEDIUM
  and add correction_note: 'Self-reported estimate — verify with actuals or a
  second source before accepting.' Do not use as HIGH confidence basis for
  annual_waste_aud calculations."

AFFECTED FILE: apg-audit-plugin/skills/3-audit-extractor/sub-agent-extract.md
AFFECTED SECTION: Pass 1 — time estimates
STATUS: observed (not yet applied)
```

---

## Stage 4: Display Results

```
PATTERN ANALYSIS -- all clients
══════════════════════════════════════════════════════════════

PATTERNS DETECTED ({n})

  1. systematic_overcount — {n} occurrences across {n} clients
     Most common in: waste_items > hours_per_week (self-reported)
     Recommendation: [see below]

  2. missing_context — {n} occurrences across {n} clients
     Most common in: pain_points — compliance/regulatory constraints missing
     Recommendation: [see below]

  ...

NO PATTERNS (below threshold)
  hallucination:   2 occurrences (threshold: 3)
  formatting_drift: 1 occurrence

══════════════════════════════════════════════════════════════
RECOMMENDATIONS

[Recommendation 1 — full text as per Stage 3 format]
[Recommendation 2 — full text]
...

══════════════════════════════════════════════════════════════
ACTIONS

  Apply a recommendation to the relevant agent prompt? [Y/N]

  If Y: display the specific file and section, show the proposed addition as a diff,
  confirm before writing. Log the application in the pattern record.

  Skip all: save patterns to sidecar memory for future reference.
```

---

## Stage 5: Update Sidecar Memory

Save detected patterns and recommendations to:
- `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-feedback-reviewer-sidecar/patterns.md`

Format:

```markdown
# Cross-Client Feedback Patterns

## {pattern_id}: {pattern_type}
**Observed in:** {client-slug-1}, {client-slug-2}
**Occurrences:** {n} corrections across {n} rounds
**Status:** observed | recommendation_generated | applied

**Description:** {pattern description}

**Recommendation:** {full recommendation text}

**Affected file:** {path}
**Affected section:** {section}
```

Update `chronology.md` with: "LP run {date}: {n} patterns detected, {n} above threshold, {n} recommendations generated."
