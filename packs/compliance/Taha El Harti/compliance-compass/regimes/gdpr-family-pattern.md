---
id: gdpr-family-pattern
name: GDPR-family pattern (LGPD, POPIA confirm; PIPL, DPDP deviate) — engine pattern file
jurisdiction: global (pattern for GDPR-skeleton jurisdictions)
tier: quick-ref
enforcer: regulator (varies by jurisdiction — see each entry)
last_verified: 2026-07-28
volatile:
  - all fine figures and enforcement statistics below
  - DPDP phase-in status
flip_dates:
  - "~2027-05-13: India DPDP — most operative obligations (notice/consent, breach notification, rights handling) become enforceable; advice flips from 'prepare' to 'comply'"
  - "~2026-11: India DPDP consent-manager registration deadline"
---

## What this file is

Not one regime — a **pattern** the engine uses when a founder names a jurisdiction with no
regime file. Many national privacy laws copy the GDPR skeleton: lawful bases, data-subject
rights, a DPO-like officer, breach notification, transfer rules, a central regulator.
Where the skeleton holds, GDPR-style triage transfers with local numbers swapped in.
**Validated for LGPD, POPIA, UK GDPR (`uk-gdpr.md`), broadly Canada. Known to mislead for
China and India.** Bucket note: all law-bucket where applicable; signed DPAs can stack
stricter contractual duties on top — the report assigns buckets per founder.

## Confirmations (verified 2026-07-28)

**LGPD (Brazil) — CONFIRMS.** GDPR-skeleton law (lawful bases incl. legitimate interest,
DPO, rights, transfer rules). ANPD now actively enforces: >BRL 98m (~US$20m) cumulative
fines 2023–2025, published penalty methodology, public dashboard (Nov 2025); priorities:
children's data, AI/biometrics, scraping. Skeleton flag: fines are 2% of *Brazil* revenue
capped BRL 50m/infraction — not GDPR's global-turnover model.

**POPIA (South Africa) — CONFIRMS, local flavor.** GDPR-family structure (operator ≈
processor, Information Officer registration, breach notification via mandatory eServices
portal since Apr 2025). Regulator active but modestly resourced: enforcement notices
(WhatsApp, Apr 2025); two R5m fines to date, both for ignoring enforcement notices;
priorities: direct marketing, breach management. Max fine R10m and/or criminal liability
— a low ceiling for the family.

## The two named deviants (the skeleton misleads here)

**PIPL (China) — WEAK FIT. Lead with transfers.** GDPR vocabulary, but the dominant
practical issue is the **cross-border transfer regime** (CAC security assessment / SCC
filing / certification) — no GDPR analogue in mechanics. 2024–2026: easing via exemptions
(contract necessity, HR data, <100k individuals/yr), narrowly construed per CAC (Oct
2025); new certification route from 1 Jan 2026; amended Cybersecurity Law penalties 2026.
Plus separate-consent requirements and a state-security overlay. China triage starts with
"does data leave China, and under which mechanism?"

**DPDP (India) — PARTIAL FIT, phased.** Rules notified 14 Nov 2025; consent-manager
registration by ~Nov 2026; **most operative obligations enforceable ~13 May 2027** — as
of Jul 2026 the advice is "prepare," flipping to "comply" at the flip date. Deviations:
consent-centric with narrow "legitimate uses" — **no legitimate-interest basis**; a novel
Consent Manager institution (registered intermediaries for managing consent); government
exemptions; penalties to INR 250 crore (~US$30m) per breach category. Skeleton works for
rights/consent/breach concepts; misleads on lawful bases and timing.

## Instructions to the engine: using this pattern for live research

1. Unfamiliar jurisdiction → the skeleton is the *hypothesis*, never the answer.
   Live-research against the `_SCHEMA.md` checklist.
2. Verify the four break-points where the known deviants failed: (a) does a
   legitimate-interest-style basis exist? (b) fully in force, or phasing in? (c) do
   transfer rules dominate practice? (d) fine model — global turnover, local revenue, or
   flat cap?
3. If the skeleton holds, transfer GDPR-style gap-checks with local names/numbers; state
   local enforcement reality honestly (POPIA-scale modest regulators are common).
4. Check for a stricter sub-national overlay (the Quebec Law 25 lesson).
5. Offer — never silently — to save results as a new file marked
   `source: live-research (unreviewed)`.

## Gap-check questions (pattern templates — gloss local terms in plain language)

1. Do you have users or operations in [jurisdiction]?
2. Does personal data leave [jurisdiction], and under which legal route? (In China this
   comes first.)
3. Do you have a lawful reason on record for each use of personal data — noting some
   countries (India) accept only consent or a short fixed list?
4. Could you notify the local regulator of a breach through its required channel?
5. Is the law actually in force yet, or still phasing in?

## Sources

Accessed 2026-07-28: agent-a3 research memo §7 (LGPD/ANPD, POPIA/Information Regulator,
PIPL/CAC, DPDP Rules commencement), all claims verified via web search on that date.
