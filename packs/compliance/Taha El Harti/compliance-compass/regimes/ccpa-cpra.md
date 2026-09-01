---
id: ccpa-cpra
name: California Consumer Privacy Act (as amended by the CPRA)
jurisdiction: US-CA
tier: full
enforcer: regulator (California Privacy Protection Agency + CA Attorney General); narrow private lawsuits for data breaches only
last_verified: 2026-07-28
volatile:
  - "$26,625,000 revenue threshold (CPPA adjusts by CPI every two years — expect a new figure for 2027)"
  - "$2,663 / $7,988 per-violation penalty amounts (inflation-adjusted; verified 2026-07-28)"
  - "enforcement-action list and 'largest settlement' figure (GM $12.75M as of May 2026)"
flip_dates:
  - "2027-01-01: automated decision-making (ADMT) rules — pre-use notice, opt-out, access rights — compliance deadline"
  - "2027-12-31: pre-existing processing must have documented risk assessments"
  - "2028-04-01: first risk-assessment attestation/summary due to CPPA; first cybersecurity audit certifications (>$100M revenue tier; $50–100M in 2029; <$50M in 2030)"
---

## Does this apply to you? (triggers)

A for-profit business "doing business in California" that meets **any one** of
(all figures verified 2026-07-28):

1. **Annual gross revenue over $26,625,000** — measured globally, not California-only.
   (Inflation-adjusted from a $25M baseline; current figure effective since Jan 2025.)
2. **Buys, sells, or shares personal information of 100,000+ California consumers or
   households per year.**
3. **Derives 50%+ of annual revenue from selling or sharing personal information.**

**The applicability gate (important):** most early-stage startups are below ALL three
thresholds. That result is **NOT APPLICABLE — with an annual re-check** (revenue grows,
user counts grow, the threshold figure itself moves). It is never recorded as "green":
nothing was checked, nothing was passed.

Watch-outs before concluding NOT APPLICABLE:
- Threshold 2 counts consumers/households whose data is bought/sold/**shared** — ad-tech
  pixels and data-broker-style sharing can trip 100k well before revenue does.
- **Ad-funded trap (threshold 3):** a free app whose revenue IS advertising can derive
  50%+ of revenue from "sharing" personal information with ad networks at ANY size —
  threshold 3 has no floor. Never screen an ad-supported product out on smallness alone.
- California is the only state where **employee and B2B contact data count** — no
  workforce/B2B exemption.
- **Bucket crossover:** sub-threshold B2B startups frequently meet this regime anyway as
  *contract-mandated* — enterprise customers push CCPA-style data processing terms
  downstream. Check contracts, not just thresholds.

## Who can punish you, and how

- **CPPA** — the only dedicated state privacy agency in the US; actively runs audits and
  sweeps (e.g., data broker registration sweeps).
- **California Attorney General** (plus local DAs have joined actions, e.g., GM).
- **Private lawsuits only for data breaches**: $100–$750 per consumer per incident
  (verified 2026-07-28) — the narrow exception to AG/agency-exclusive enforcement.
- Adjacent CA regime to flag: the **Delete Act / data broker registration** scheme
  (deletion mechanism "DROP" phasing in; SB 361 expansions effective Jan 1, 2026).

## Penalties & enforcement reality

- **$2,663 per violation / $7,988 per intentional or minor-involving violation**
  (inflation-adjusted from $2,500/$7,500, effective Jan 1, 2025; verified 2026-07-28).
  Violations count per consumer, so theoretical totals scale fast.
- Actual outcomes: Sephora $1.2M (2022), Honda $632K (CPPA, 2025), Healthline $1.55M
  (2025), Tractor Supply $1.35M, Disney $2.75M, PlayOn $1.1M, and **General Motors
  $12.75M (May 2026 — largest outcome to date**; driver location data). All figures
  verified 2026-07-28.
- The recurring finding in nearly every action: a **broken or incomplete opt-out /
  Global Privacy Control implementation**. For covered companies this is the single
  highest-yield gap check.
- **Honesty statement:** no small-startup fine is on record under this regime;
  enforcement sweeps to date target large or highly visible companies. For a
  sub-threshold startup the realistic exposure is contractual (enterprise customers)
  and breach lawsuits, not agency fines.

## Gap-check questions

1. Is your total annual revenue (worldwide) above roughly $26.6 million?
2. Do you buy, sell, or share personal information of more than 100,000 California
   residents or households a year — counting what your ad pixels and analytics tools
   send out, not just deliberate sales?
3. Does more than half your revenue come from selling or sharing personal data?
4. If yes to any: does your site honor the browser-level "don't sell or share my data"
   signal (Global Privacy Control), tested end to end including ad pixels?
5. If yes to any: can a California user actually find out what you hold, delete it, and
   correct it — is there a working intake process someone owns?
6. Have enterprise customers made you promise California-style privacy compliance in
   contracts, even though you're below the thresholds?
7. Do third-party ad or analytics SDKs in your product receive user data (that can
   count as "sharing")?
8. Do you use automated systems to make decisions that significantly affect people
   (hiring, lending, pricing)? — relevant to rules taking effect Jan 1, 2027.

## First steps

1. Confirm threshold status with real numbers (hours). Below all three → record
   NOT APPLICABLE with an annual re-check date, note any contractual obligations, stop.
2. If covered: privacy policy + notice at collection covering the required rights (days).
3. Make the opt-out of sale/sharing work end to end, including the Global Privacy
   Control signal and ad pixels — test it, don't assume it (days).
4. Stand up a rights-request (access/delete/correct) intake process with an owner (days).
5. Review vendor contracts for required service-provider terms (days).

## Cost baselines

Rough, for calibration only (memo figures; vendor pricing skews — verify current):
consent-management platforms run free to low hundreds $/month at startup scale;
rights-request handling is mostly process, not tooling, at low volume.

## Sources

All accessed 2026-07-28: CPPA penalty-adjustment announcement (cppa.ca.gov, Dec 2024);
CPPA press release on finalized regulations (Sept 2025); Hunton (staggered compliance
deadlines); Skadden (finalized CPPA regulations); Clym CCPA applicability guide;
Measured Collective CCPA/CPRA fines list; PrivacyLawMap state penalties guide.
