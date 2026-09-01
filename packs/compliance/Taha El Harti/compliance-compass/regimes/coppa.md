---
id: coppa
name: Children's Online Privacy Protection Act (2025 amended rule)
jurisdiction: US
tier: full
enforcer: regulator (FTC — currently its most actively enforced privacy statute); app stores add market-expected enforcement
last_verified: 2026-07-28
volatile:
  - "$53,088 per-violation civil penalty (Jan 2025 adjustment, frozen through 2026; expect movement Jan 2027)"
  - "enforcement-action list (Disney $10M Sept 2025; Apitor Sept 2025)"
flip_dates:
  - "2027-01: next federal civil-penalty inflation adjustment expected (2026 round cancelled government-wide)"
---

## Does this apply to you? (triggers)

Operators of sites/services that are either:

1. **Directed to children under 13** — a multi-factor test: subject matter, visuals,
   characters, music, audience evidence, how you market it. Not just "we say it's for
   kids"; the FTC decides from the totality.
2. **Have actual knowledge** they collect personal info from under-13s — this catches
   general-audience services. Age gates don't immunize you if you receive and ignore
   age signals. It also reaches **third parties** (e.g., ad SDKs) receiving child data.

If your service is genuinely general-audience, doesn't attract children, and you don't
receive age signals you're ignoring → NOT APPLICABLE, with a re-check whenever your
content, marketing, or audience shifts younger. Not "green" — the child-directed test
is about how your product actually lands, not your intent.

**Rule status (verified 2026-07-28): the amended rule is fully in force.** Final
amendments published Apr 22, 2025; effective Jun 23, 2025; general compliance deadline
Apr 22, 2026 (passed); safe-harbor-program provisions deadline Oct 22, 2025. This is
no longer an "upcoming change." Key changes now binding:

- **Separate opt-in parental consent for targeted advertising** / third-party
  disclosure — cannot be bundled with the base consent.
- **Biometric identifiers** added to "personal information."
- **Data retention limits + a required written retention policy** — no indefinite
  retention.
- Expanded direct-notice content; safe-harbor program transparency.

## Who can punish you, and how

- **FTC** — civil penalties in federal court. FTC leadership has named this its
  preferred vehicle over novel deception theories: kids' privacy is the *most*
  actively enforced privacy area in the US right now (verified 2026-07-28).
- **App stores (market-expected bucket):** Apple/Google kids-category rules are in
  places stricter than the law and are enforced by rejection/removal — often the
  first "enforcement" a small developer feels.

## Penalties & enforcement reality

- Civil penalties up to **$53,088 per violation** (verified 2026-07-28) — and the
  exposure math runs per child, per day, so theoretical totals get large fast.
  Figure note: Jan 2025 adjustment, frozen through 2026 (2026 government-wide
  adjustment cancelled — OMB M-26-11); expect movement Jan 2027.
- Recent actions (verified 2026-07-28): **Disney $10M** (Sept 2025 — mislabeled
  child-directed YouTube videos); **Apitor Technology** (Sept 2025 — robot-toy app
  sending kids' geolocation to a Chinese third party; $500K suspended penalty).
  Historical anchor: **Epic Games $275M** (2022) remains the record COPPA penalty.
  (A claimed "$520M settlement in 2026" circulating in secondary sources matches the
  *total* 2022 Epic package and could not be verified as a 2026 event — treat as
  unverified/conflated.)
- **Honesty statement:** small developers are demonstrably hit here — HyperBeard
  (indie studio, $4M penalty suspended to **$150K for inability to pay**, Jun 2020)
  and LAI Systems & Retro Dreamer (small game studios, **$60K and $300K**, Dec 2015)
  are on the FTC record (verified 2026-07-28). The suspension mechanism is the point:
  the FTC imposes beyond a small company's capacity and suspends it — the process and
  injunctive order are the real cost. This is not a big-tech-only statute.

## Gap-check questions

1. Could any part of your service be seen as aimed at kids under 13 — content,
   characters, art style, or how it's marketed?
2. Do you receive age information (birthdays, school grade, self-reported age, support
   emails from kids) that you're currently ignoring?
3. Do ad or analytics SDKs in your app collect device identifiers from users who might
   be children?
4. If you knowingly serve under-13s: do you get verifiable parental consent before
   collecting anything — and a *separate* opt-in before targeted ads?
5. Do you have a written data-retention policy, and do you actually delete children's
   data on schedule?
6. Do you collect anything biometric-adjacent (voice, face data) from young users?
7. If you're on app stores: are you meeting their kids-category rules (often stricter
   than the law)?

## First steps

1. Audience analysis: honestly assess whether any surface is child-directed; document
   the reasoning (hours).
2. Ad-SDK audit — what identifiers leave the app, to whom (hours–days).
3. If in scope: verifiable parental consent flow — safe-harbor/consent vendors exist —
   with the separate targeted-ads opt-in (days).
4. Write the retention policy and wire up actual deletion (days).
5. Check app-store kids-program requirements alongside the legal ones (hours).

## Cost baselines

Not established in source research (consent/safe-harbor vendors exist; pricing not
covered in the memo).

## Sources

All accessed 2026-07-28: Federal Register, COPPA final rule (Apr 22, 2025); Perkins
Coie (compliance deadlines); FTC press release (Disney, Sept 2025); Davis Polk (FTC
prioritizes COPPA); Finnegan (amended rule in full effect). Small-developer honesty
examples (HyperBeard, Retro Dreamer, LAI Systems) sourced from the Agent E enforcement-evidence memo (ftc.gov press releases 2015-12, 2020-06; verified 2026-07-28) —
verify case details before quoting numbers.
