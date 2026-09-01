---
id: gdpr
name: General Data Protection Regulation (Regulation (EU) 2016/679)
jurisdiction: EU (extraterritorial reach)
tier: full
enforcer: national data protection authorities (fines, orders); enterprise customers via procurement (DPAs, vendor security reviews)
last_verified: 2026-07-28
volatile:
  - cumulative fine statistics (≈€7.1B / ~2,685 cases; ~€1.2B in 2025; >€600M H1 2026)
  - EU–US Data Privacy Framework status (litigation-exposed — re-verify at every report generation)
  - all cost baselines (vendor-sourced)
flip_dates:
  - "late 2026/early 2027 (expected, not fixed): data/GDPR Digital Omnibus final text — proposes breach-notification threshold changes, AI-training/legitimate-interest clarification, and cookie consent moved into GDPR as Arts 88a/88b. In trilogue as of mid-2026; current GDPR text fully in force until then."
---

## Does this apply to you? (triggers)
- Established in the EU and processing personal data → applies.
- Outside the EU → applies if you either:
  - offer goods/services to people in the EU (even free), or
  - monitor behavior of people in the EU.
  - Classic extraterritorial triggers: analytics on EU visitors, ads retargeting, EU-language or EU-currency storefronts.
- Founder-level test: any EU users, EU customers, EU employees, or EU-visitor analytics → in scope.
- Non-EU companies in scope generally must also appoint an **EU representative** — widely ignored in practice, but a standalone obligation with its own exposure. Exemption: occasional, low-risk processing.
- Gate: no EU users/customers/employees/analytics at all → NOT APPLICABLE. Re-check whenever EU traffic or sales start.
- Common scoping notes (verified 2026-07-28):
  - Records of processing: the under-250-employee exemption is narrow — it falls away if processing is non-occasional, risky, or involves special categories. Almost every SaaS with a user database effectively needs records.
  - DPO: mandatory only if core activities involve large-scale regular monitoring or large-scale special-category data. Most small SaaS do NOT legally need one — a common over-compliance point; many appoint one voluntarily or per customer demand.

## Who can punish you, and how
- National data protection authorities: fines, processing bans, orders to delete data, mandatory audits.
  - Complaint-driven — a single user complaint (free to file) can open a case.
- Enterprise customers: B2B procurement pushes data processing agreements and security terms onto vendors.
  - A startup selling B2B meets this regime via contract long before a regulator appears; failed vendor security reviews mean lost deals.
- (Bucket — law vs contract — is assigned per founder in the report; both channels are real here.)

## Penalties & enforcement reality
- Statutory maxima (verified 2026-07-28):
  - up to €20M or 4% of global annual turnover (whichever higher): core principles, lawful basis, data subject rights, transfers.
  - up to €10M or 2%: controller/processor duties (records, security, breach notification, DPO).
- Scale (verified 2026-07-28):
  - cumulative fines since 2018 ≈ €7.1B across ~2,685 published cases.
  - ~€1.2B issued in 2025; >€600M in H1 2026; over 60% of total fine value imposed since Jan 2023 — accelerating, not plateauing.
  - breach notifications average ~443/day EU-wide.
- Realistic small-company exposure: a five-to-six-figure fine plus a corrective order, not a €100M headline. Headline fines hit big tech; volume enforcement hits ordinary companies.
- Non-fine consequences founders underweight: processing bans, deletion orders, mandatory audits, B2B deal loss.
- **Honesty statement:** complaint-driven volume enforcement demonstrably reaches small companies — Spain's AEPD alone has >1,000 published fines, many in the €1k–€100k range against SMEs; Italy, Romania, and Poland each have hundreds (verified 2026-07-28). Ignored deletion/access requests are a top driver of SME-level cases.

## Gap-check questions
1. Do you know every system and vendor that stores your users' or employees' personal data? (does an inventory exist?)
2. For each thing you do with user data, can you name the legal justification you're relying on? (marketing justified only by "our legitimate interest", with nothing documented, is the common gap)
3. Do you have a signed data processing agreement with each vendor that touches personal data — cloud, email, analytics, AI APIs?
4. If you're outside the EU: have you appointed a representative inside the EU?
5. If a user emailed "delete my data" today, is there a process that answers within a month? (extendable +2 months for complexity — but only with a process)
6. If your database leaked tonight, who decides within 72 hours whether to notify a regulator — and would you even detect it in time? (the clock starts at awareness; no detection/escalation process makes 72h impossible)
7. Are you sending EU user data to the US or other non-EU countries, and do you know under what mechanism?
8. Do you do anything higher-risk — tracking/profiling, health data, children's data — that would need a documented risk assessment before you do it?

## First steps
1. Data inventory + vendor list — spreadsheet-grade. (one afternoon)
2. Countersign each vendor's standard data processing agreement; fix the privacy notice to match what you actually do. (hours–days)
3. Stand up a deletion/access-request inbox + a one-page breach playbook with the 72-hour decision point. (hours)
4. Decide the DPO question explicitly — usually "not required — documented why". (hours)
5. Map international transfers; confirm Data Privacy Framework or standard-contractual-clause coverage per US vendor. Non-Framework US vendors and other third countries need standard clauses + a transfer impact assessment. (hours–days)

## Cost baselines
All vendor/consultancy-sourced — rough signals with 5–10x spread; verify before quoting (as of 2026-07-28):
- Small SaaS (≤50 people), steady-state: commonly cited €20k–50k/yr all-in; bootstrap-minimal setups far less.
- Outsourced/fractional DPO: ~€5k–15k/yr at the low end; €20k–50k+/yr for fuller coverage; in-house DPO salary €50k–120k.
- Tooling (consent platform, request handling, policy generators): low hundreds €/month.
- One-time setup (policies, records, agreements, notice): a few thousand € with templates/counsel-light. One US source quotes $20.5k–$102.5k for "small startups" — high-end consulting framing.

## Sources
- Statutory text: EUR-Lex, Regulation 2016/679 (accessed 2026-07-28).
- Fine statistics (accessed 2026-07-28): CMS GDPR Enforcement Tracker Report 2025/2026 (cms.law); privacyengine.io GDPR statistics 2026; uniconsent.com enforcement 2026; kiteworks.com (€7.1B cumulative figure).
  - Note: cumulative totals vary by tracker — quote one named source per number.
- Cost signals (accessed 2026-07-28): usercentrics.com, sprinto.com, vistainfosec.com, captaincompliance.com, complydog.com (vendor content).
- Pending-change status — data Digital Omnibus in trilogue (accessed 2026-07-28): secureprivacy.ai, nixondigital, Kennedys analyses.
