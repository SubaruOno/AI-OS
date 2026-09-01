---
id: hipaa-hbnr
name: HIPAA + FTC Health Breach Notification Rule (the covered / not-covered boundary)
jurisdiction: US
tier: full
enforcer: HHS Office for Civil Rights (if HIPAA-covered); FTC (if health-adjacent but not covered); WA MHMD adds private lawsuits for consumer health data
last_verified: 2026-07-28
volatile:
  - "HIPAA penalty tiers ($145 min to ~$2.19M tier-4 annual cap; Federal Register Jan 28, 2026)"
  - "$53,088 HBNR per-violation-per-day penalty (Jan 2025 adjustment, frozen through 2026; expect movement Jan 2027)"
  - "status of proposed HIPAA Security Rule overhaul (NPRM Jan 2025 — MFA, encryption, asset inventories mandatory) — pending as of research date, verify before citing"
flip_dates:
  - "2027-01: next federal civil-penalty inflation adjustment expected (2026 round cancelled government-wide)"
---

## Does this apply to you? (triggers) — THE DECISION TREE

The single most common founder misconception (FTC-acknowledged): **health-adjacent
data ≠ HIPAA.** Walk this tree in order; stop at the first hit.

```
Q1. Are you a health plan, a healthcare clearinghouse, or a healthcare PROVIDER
    that transmits health info electronically for standard billing/insurance
    transactions?
    ├─ YES → COVERED ENTITY. HIPAA applies directly. (Note: a cash-pay
    │        therapist who never bills insurance electronically may not
    │        even be a covered entity.)
    └─ NO ↓

Q2. Do you create, receive, maintain, or transmit patient health info ON BEHALF
    OF a covered entity — e.g., SaaS analytics for clinics, a billing platform,
    hosting with PHI access? (Practical tells: "Do you sign BAAs?" /
    "Do any of your customers bill insurance?")
    ├─ YES → BUSINESS ASSOCIATE. HIPAA applies DIRECTLY to you (since HITECH).
    │        A signed Business Associate Agreement is mandatory BEFORE touching
    │        PHI, and your subcontractors need downstream BAAs.
    └─ NO ↓

Q3. Do you handle health-ish data anyway — fitness tracker, diet app, period
    tracker, mental-wellness app, DTC telehealth-adjacent product — with no
    covered-entity relationship?
    ├─ YES → NOT HIPAA. What applies instead:
    │        • FTC Act §5 (your privacy promises vs. your ad-SDK reality)
    │        • FTC Health Breach Notification Rule (HBNR) — the 2024 update
    │          (effective Jul 29, 2024) swept in most health/wellness apps and
    │          connected devices; "breach" includes UNAUTHORIZED DISCLOSURE,
    │          e.g. ad-tracker sharing, not just hacking (the GoodRx theory)
    │        • State privacy laws' "sensitive data" tiers
    │        • Washington My Health My Data — private lawsuits (see wa-mhmd-il-bipa.md)
    └─ NO → NOT APPLICABLE for this file. Re-check if you add health features,
            health customers, or start signing health-data agreements.
```

Interview shortcut: "Do you sign BAAs?" and "Do any of your customers bill insurance?"
separate HIPAA from non-HIPAA faster than "do you handle health data?"

## Who can punish you, and how

- **HIPAA-covered (CE or BA):** HHS Office for Civil Rights — investigations
  (ransomware incidents are the main trigger vector), resolution agreements,
  civil money penalties. Business associates are directly liable, not just via
  their customers.
- **Not covered but health-adjacent:** the FTC, under HBNR (a penalty-carrying rule)
  and §5. HBNR requires breach notification to individuals, the FTC, and — at 1,000+
  affected — the media.
- **Either way:** state AGs under state law, and private plaintiffs under WA MHMD if
  you touch Washington consumers' health data.

## Penalties & enforcement reality

- **HIPAA:** four culpability tiers (no knowledge / reasonable cause / willful neglect
  corrected / willful neglect uncorrected). Inflation-adjusted per-violation amounts
  range **$145 minimum to ~$2.19M** (tier-4 annual cap), updated in the Federal
  Register Jan 28, 2026. OCR still applies its 2019 enforcement-discretion caps for
  annual maxima on tiers 1–3 (~$25K / $100K / $250K, adjusted). Verified 2026-07-28.
- **HIPAA reality:** OCR settlements are frequent but mostly **five-to-low-six-figure
  for small entities** — entry-level settlements run **$5K–$100K**, not the headline
  millions. ~10 resolution agreements in the first five months of 2025 alone, with an
  explicit **Risk Analysis Initiative**: the recurring finding is failure to conduct
  and document a Security Rule risk analysis.
- **Honesty statement:** small practices are demonstrably NOT too small to be pursued —
  OCR's Right of Access Initiative (2019–present, 50+ actions) is heavily populated by
  small and solo practices, with settlements typically **$25K–$100K** (verified
  2026-07-28; in 2021, 12 of 14 OCR penalties were records-access cases). If you're
  covered, size is not a shield; the fines are just smaller.
- **HBNR:** civil penalties up to **$53,088 per violation per day** (verified
  2026-07-28; Jan 2025 adjustment, frozen through 2026 — the government-wide 2026
  adjustment was cancelled; expect movement Jan 2027). Actions: GoodRx $1.5M (first
  HBNR action, Feb 2023), Easy Healthcare/Premom (2023); companion §5 health-privacy
  cases BetterHelp $7.8M (2023), Cerebral $7M (2024) — all ad-pixel sharing cases.
  Health data remains on the FTC's short priority list (verified 2026-07-28).

## Gap-check questions

1. Do any of your customers bill insurance, or are you yourself a provider, plan, or
   claims intermediary?
2. Have you ever been asked to sign a business associate agreement (a health-data
   handling contract) — and did you sign it *before* receiving any patient data?
3. Does every vendor of yours that can touch patient data have the same agreement
   signed downstream?
4. Have you performed and *documented* a security risk analysis — could you produce
   it this week?
5. If you're health-adjacent but outside the insurance world: do your privacy promises
   match what your ad and analytics SDKs actually send out?
6. Does your incident-response plan include notifying individuals and the federal
   regulator on the correct clock for your category?
7. Do you serve Washington-state consumers with any health-related data? (Separate,
   higher-litigation-risk regime — see wa-mhmd-il-bipa.md.)

## First steps

1. Run the decision tree above and write the classification down — CE / BA / neither
   (hours). This one artifact drives everything else.
2. If CE/BA: inventory PHI-touching vendors; get BAAs signed everywhere (days —
   a BAA costs nothing but negotiation).
3. Do the documented risk analysis — HHS provides a free SRA tool (days).
4. Breach-response plan that includes the HBNR path for non-HIPAA products (hours–days).
5. If NOT covered: pixel/SDK audit against your privacy promises (hours–days).

## Cost baselines

Rough, from memo: HHS SRA tool is free; small-org HIPAA compliance tooling/attestation
typically low thousands $/yr; a BAA costs nothing but negotiation time.

## Sources

All accessed 2026-07-28: FTC business guidance "Collecting, Using, or Sharing Consumer
Health Information? Look Beyond HIPAA"; FTC "Complying with the HBNR"; 16 CFR Part 318;
HIPAA Journal penalties page (2026 figures); HHS resolution agreements index; Ogletree
(2025 enforcement trends — Risk Analysis Initiative); Nixon Peabody (2025 tally).
Solo-practice / records-access figures sourced from the Agent E enforcement-evidence memo (hipaajournal.com penalties page; hhs.gov; verified 2026-07-28) — verify case
details before quoting figures.
