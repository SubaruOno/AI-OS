---
id: eprivacy-cookies
name: ePrivacy / cookie rules (Directive 2002/58/EC as amended, national transpositions)
jurisdiction: EU (enforced per member state)
tier: full
enforcer: national data protection authorities (CNIL, AEPD, Garante…) acting under national ePrivacy transpositions — often without GDPR's one-stop-shop, so any member state's DPA can act directly
last_verified: 2026-07-28
volatile:
  - CNIL fine totals and named fines (2025/2026 figures)
  - consent-platform price points (vendor-sourced)
  - trilogue status of the data/GDPR Digital Omnibus
flip_dates:
  - "late 2026/early 2027 (expected, not fixed): data/GDPR Digital Omnibus proposes moving cookie consent into GDPR as Arts 88a/88b, incl. legally binding browser-level consent signals. In trilogue as of mid-2026. Current rules fully in force until then — this file needs a mid-life update when it lands."
---

Context (verified 2026-07-28): the long-stalled ePrivacy Regulation (intended replacement) was formally withdrawn 11 Feb 2025. The live reform track is now the data/GDPR Digital Omnibus above — a separate instrument from the AI Omnibus, though both share the "Digital Omnibus" name.

## Does this apply to you? (triggers)
- Any website or app that **stores or reads anything on a user's device** in the EU:
  - cookies, localStorage, SDK identifiers, fingerprinting.
  - Bites on the device access itself — applies even where the data isn't "personal" (narrower trigger than GDPR, broader on this axis).
- Consent required **before** setting non-essential cookies/trackers:
  - needs consent: analytics, ads, most third-party embeds.
  - exempt as "strictly necessary": session, cart, consent-choice storage, security.
- Consent standard = GDPR-grade: freely given, specific, informed, unambiguous; reject as easy as accept.
- Relationship to GDPR: these rules govern the device access; GDPR governs the subsequent processing of any personal data collected.
- Gate: no EU visitors, or truly zero non-essential storage/reading on devices → NOT APPLICABLE. Re-check whenever a new tag, SDK, or embed is added.
- Country nuance: DPA positions diverge — some accept audience-measurement exemptions for analytics in approved configurations (e.g., CNIL). Country-dependent, not EU-wide.

## Who can punish you, and how
- National DPAs under ePrivacy transpositions: fines at GDPR-like scale, formal notices, corrective orders.
- No one-stop-shop in the usual case — any member state's authority where you have users can act directly.
- (Bucket assigned per founder in the report. Teaching note: cookie banners are the one compliance artifact every founder has seen — the natural on-ramp for explaining law-mandated vs market-expected.)

## Penalties & enforcement reality
- Fine levels are national, but DPAs fine at GDPR-like scale. France's CNIL is the world leader (all verified 2026-07-28):
  - 3 Sep 2025: **Google €325M total** (Google LLC €200M + Google Ireland €125M — the split explains the conflicting secondary reports; verified against CNIL 2026-07-28) — ads in Gmail without consent + cookies set at account creation without valid consent.
  - 3 Sep 2025: **Shein €150M** — cookies set before any choice; "Reject all" click accepted while tracking cookies continued anyway.
  - CNIL 2025 totals: 83 sanctions ≈ €486.8M, bulk from cookies/ad trackers.
  - Early 2026: Amex €1.5M (cookies). CNIL confirmed cookies remain a 2026 priority alongside AI and cybersecurity.
- Pattern shift worth encoding: regulators now do **technical verification** — testing at network level whether "reject" actually suppresses tracking, not whether the banner looks symmetrical.
  - The target is second-generation failures: dark patterns, non-enforced rejection, hard-to-withdraw consent.
- **Honesty statement:** enforcement is real below big-tech scale — CNIL runs formal-notice sweeps against smaller sites, not just giants, and of the regimes in this library this is the one where a given founder most probably has a detectable, cheaply fixable gap today (verified 2026-07-28).

## Gap-check questions
1. Does anything load or fire before the visitor makes a consent choice? (checkable right now: open devtools on your own homepage and watch the network tab)
2. Is "Reject all" one click and as prominent as "Accept all"?
3. If a visitor rejects, do the trackers actually stay silent at network level — or does tracking continue behind the banner?
4. Can users withdraw consent as easily as they gave it (e.g., a persistent link)?
5. For analytics: are you collecting consent, or relying on a claimed measurement exemption — and is that exemption actually accepted in the countries where your users are?
6. Do you have a current inventory of every cookie, SDK, and third-party embed on your site or app?

## First steps
1. Tracker inventory: crawl your own site/app; classify essential vs non-essential. (hours)
2. Install/configure a consent management platform with prior blocking; verify with a network-tab test that nothing non-essential fires pre-consent. (hours–days — the Shein fine is precisely this gap)
3. Make accept/reject symmetric; add a consent-withdrawal link in the footer. (hours)

## Cost baselines
- Consent management platform: free tiers to ~€50–150/month for typical startup traffic (vendor-sourced signal, as of 2026-07-28).
- The real cost is configuration honesty: ensuring tags actually don't fire pre-consent is an engineering task — hours to days.

## Sources
All accessed 2026-07-28:
- cnil.fr (Shein decision; 2026 priorities); privacylaws.com (PL&B — Google €325M / Shein €150M primary figures).
- Bird & Bird, Slaughter and May, Lewis Silkin cookie-enforcement analyses.
- flowconsent/kukie enforcement roundups (CNIL 2025 totals ≈ €486.8M; Amex €1.5M).
- secureprivacy.ai, nixondigital, Kennedys on Digital Omnibus Arts 88a/88b status (trilogue, mid-2026).
