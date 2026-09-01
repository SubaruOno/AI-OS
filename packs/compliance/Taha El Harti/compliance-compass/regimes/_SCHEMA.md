# Regime file schema

Every file in `regimes/` follows this structure. The engine also uses this schema as its
**checklist when live-researching a regime that has no file here** — and may offer (never
silently) to save the result as a new file marked `source: live-research (unreviewed)`.

```markdown
---
id: <kebab-case>
name: <full name>
jurisdiction: <EU | US | US-CA | global | ...>
tier: full | quick-ref
enforcer: <who actually comes after you: regulator / private lawsuits / counterparty / market>
last_verified: YYYY-MM-DD
volatile:            # values that MUST be re-verified live before quoting if >6 months old
  - <fine amounts, thresholds, deadlines, statistics...>
flip_dates:          # known future dates when the content below changes
  - "YYYY-MM-DD: <what changes>"
---

## Does this apply to you? (triggers)
Plain-language conditions. Include scale thresholds and exemptions — "does NOT apply" is
as valuable as "applies". State the applicability gate explicitly: below thresholds is
NOT APPLICABLE (with a re-check note), never "green".

## Who can punish you, and how
The real enforcement mechanism(s). Bucket (law / contract / market-expected) is assigned
PER FOUNDER in the report, based on how the regime reaches *them*.

## Penalties & enforcement reality
Statutory maxima AND what actually happens, especially to small companies. Include the
regime's one-line honesty statement (evidence-based, e.g. "complaint-driven enforcement
demonstrably reaches small companies here" or "no small-company enforcement on record").
Every number carries its verification date.

## Gap-check questions (5–8)
Artifact-existence level, plain language, answerable yes/no/partly from a founder's memory.

## First steps
1–5 numbered, concrete, cheapest-first. Tag rough effort (hours/days) where honest.

## Cost baselines
Ranges with source type labeled (vendor figures skew; say so). Omit rather than guess.

## Sources
Named sources with access dates. One named source per load-bearing number.
```

Rules for authors: no fear-mongering, no legal advice, plain language, no prose padding —
these files are reference data the engine loads mid-interview. Full-tier files ~80–150
lines; quick-refs ~30–60.
