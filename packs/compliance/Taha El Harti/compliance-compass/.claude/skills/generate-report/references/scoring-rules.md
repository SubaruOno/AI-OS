# Scoring rules — deterministic, closed-vocabulary

The same profile MUST always produce the same statuses and queue order. Every step below
is a boolean check over interview facts or a table lookup — never a felt judgment, never
arithmetic, never a percentage.

## Stage 0 — applicability gate (per regime, before any scoring)

`APPLIES | NOT_APPLICABLE | UNKNOWN` from the regime file's trigger conditions.
- NOT_APPLICABLE is a real finding: record WHY + the "becomes relevant if…" condition
  (e.g., CCPA: "below all three thresholds — re-check annually"). **It is rendered as
  N/A, never as green.**
- UNKNOWN (a gating fact is missing) → status GRAY with the specific question attached.

## Stage 1 — driver levels (LOW | MED | HIGH | UNKNOWN per driver)

**D1 — Enforcement likelihood at this profile.** From the regime file's enforcement-reality
section, keyed to profile facts. Fixed anchors:
- Child-directed product (any size) → HIGH · Consumer health data app → HIGH ·
  EU personal data + consumer-facing or any EU employees → MED (complaint-driven
  enforcement reaches small companies) · Covered under CCPA and consumer-facing → MED ·
  Generic small B2B, no sensitive data → LOW.

**D2 — Trigger cheapness.** Free individual complaints exist (GDPR, OCR, FTC, state AGs)
AND the profile has a complaint surface (consumers, employees in-jurisdiction, parents,
patients) → HIGH. Free-complaint regime but small/purely-B2B data-subject pool → MED.
Regime triggered only by breach or audit (PCI pre-breach) → LOW.

**D3 — Counterparty pressure.** HIGH if EITHER:
(a) a counterparty has **explicitly demanded** the artifact (security questionnaire sent,
SOC 2 requested, SAQ required by a signed processor agreement, insurer application), OR
(b) an **existing counterparty relationship already legally or contractually requires an
artifact that is absent** — e.g., live EU business customers with no signed DPAs (Art 28
makes them mandatory, demand or no demand), a BAA-requiring customer without a BAA, a
processor agreement whose SAQ was never filed, signed contract clocks the founder cannot
meet. Existing-obligation-absent counts as HIGH even when nobody has asked yet.
MED: neither (a) nor (b), but the profile targets enterprise/regulated buyers who will
demand it within ~12 months. LOW: none of the above.
Tie-break principle for every driver: when two readings of a rule are possible, the
reading keyed to EXISTING relationships and obligations wins over stated-demand-only.

**D4 — Calendar deadlines.** A dated obligation applying to this profile ≤90 days → HIGH.
≤12 months → MED. None → LOW. (Dates come from regime files' flip_dates + obligations —
verify volatile dates live before relying on them.)

Any driver whose input fact is missing → that driver is UNKNOWN → regime status GRAY +
question. Never guess a level.

## Stage 2 — status lookup (first match wins)

1. **ACTION REQUIRED (red)** if D3=HIGH, or D4=HIGH, or (D1=HIGH and D2=HIGH).
2. **SCHEDULE (amber)** if any single driver is HIGH, or ≥2 drivers are MED.
3. **NO ACTION IDENTIFIED (green)** otherwise.

Queue-item tier labels are exactly: `FIND OUT FIRST` (gray) / `ACT NOW` (red) /
`SCHEDULE` (amber) — greens are never queue items, so there is no green queue label.
Regime statuses: `ACTION REQUIRED` / `ATTENTION` / `NO ACTION IDENTIFIED` /
`NOT APPLICABLE` / `NEEDS ANSWER`. The word "compliant" never appears anywhere.

**Shared-artifact ownership (anti-double-counting):** when one missing artifact would
fire D3(b) in more than one regime (missing DPAs touch both GDPR and the
DPA/questionnaire category; a missing BAA touches both HIPAA and the category), the
D3=HIGH belongs to the MOST SPECIFIC regime (the category file for contract paper; HIPAA
for BAAs). Other regimes score the same gap only through their own drivers (for GDPR,
missing DPAs still feed D1/D2 and its missing-items list — but not a second D3 red).

## Queue ordering (deterministic tiebreak)

1. All UNKNOWN-blocking items first as "Find out first" entries (multiple grays: order
   by regime id alphabetically).
2. Reds, ordered by: nearest D4 date → then D3 level → then D1 level → then regime id
   alphabetically (final tiebreak so order is total).
3. Ambers (same tiebreak), then greens are not queue items (they appear only as regime
   cards and in the summary count).

## Per-regime honesty lines

Each regime card states its enforcement reality in one evidence-based sentence taken from
the regime file — never a global "regulators don't chase small companies" claim. Where no
reliable base rate exists (fine probability by company size — true for every regime), the
card says that plainly.

## Breach stress test (consolidated timeline)

One merged timeline built ONLY from regimes that passed the applicability gate, using
these verified clocks (all verified 2026-07-28; re-verify if stale):

| Clock | Obligation |
|---|---|
| T0 | Awareness starts every clock. Preserve evidence; counsel; **notify insurer day one** (late notice + misrepresented controls are the two common denial grounds) |
| T0+24–72h | Contractual notices per signed DPAs/BAAs (market standard 48–72h, often 24h) — for B2B, every enterprise customer learns at once |
| T0+72h | GDPR: notification decision to the supervisory authority made and filed if required (phased filing allowed) |
| T0+5 business days | Cards: acquirer/Visa notified; PCI Forensic Investigator engagement clock running (Visa WTDIC) |
| T0+15–30 days | First US state consumer-notice deadlines (CA 30 days + AG within 15 days of consumer notice if >500 CA residents); state AG thresholds 250–1,000 residents |
| T0+60 days | HIPAA outer limit: individuals + HHS (+media if ≥500 in a state); remaining state clocks |
| T0+months | Regulator follow-up examines PRE-breach posture — missing risk analyses, DPAs, and policies become findings independent of the breach |

Frame as logistics under time pressure — a list of clocks the founder would have to hit
with today's artifacts — never as catastrophe narrative. Unsourceable figures (e.g., PCI
fine schedules) are described by mechanism, not invented numbers.

## Out-of-model note (must appear in the report method section)

This model scores likelihood-flavored drivers. Regimes with criminal, strict-liability, or
personal-liability character (sanctions/export controls, trust-fund taxes, corporate
filings) are OUTSIDE the model — the report lists them as unscored flags when the profile
plausibly touches them, with "cheap to check, ask your lawyer/accountant" framing.
