---
id: pci-dss
name: PCI DSS (Payment Card Industry Data Security Standard), v4.0.1
jurisdiction: global (card-brand rules, not law)
tier: full
enforcer: counterparty — card brands → acquiring banks → your payment processor's contract with you
last_verified: 2026-07-28
volatile:
  - non-compliance fee band (~$20–$250/month for small merchants)
  - SAQ A eligibility wording and how much script-security work lands on iframe-only merchants
flip_dates:
  - none known (the last major flip, mandatory v4.x requirements, passed 2025-03-31)
---

## Does this apply to you? (triggers)

Applies if you accept card payments in any form — even entirely through Stripe, PayPal, or
a similar processor. The *amount* of work varies enormously with how card data touches
your systems; the obligation itself attaches the moment you take cards.

Does NOT apply: you take no card payments (invoice/bank-transfer/app-store only). That is
NOT APPLICABLE — re-check if you ever add card checkout.

## Who can punish you, and how

**This is contract, not law** (a few US states reference PCI DSS in statute, but for a
global founder audience the correct frame is contractual). The chain: card brands
(Visa/Mastercard/Amex/Discover/JCB) impose rules on acquiring banks → acquirers impose
them on merchants via merchant agreements → **your payment processor's terms of service
bind you**. Nobody goes to jail; you bleed fees or lose the ability to take cards.

**Bucket note:** PCI DSS sits in the contract-mandated bucket from day one — your
processor agreement names it. (Frameworks generally migrate from market-expected to
contract-mandated once a contract names them; the report assigns the bucket per founder.)

## Penalties & enforcement reality

Documented consequences only (verified 2026-07-28):

- **Non-compliance fees:** small merchants typically see **~$20–$250/month**, recurring
  until the missing self-assessment or attestation is filed. Triggers: missed SAQs,
  expired attestations, missing quarterly ASV scans where required. (Larger headline
  monthly-fine figures circulate but apply to sustained non-compliance at larger
  merchants and are not reliably verifiable — not quoted here.)
- **Breach while non-compliant:** forensic investigation costs, card-reissuance and fraud
  liability passed down the chain to you, mandatory upgrade to the strictest validation
  tier (Level 1 audits), higher processing fees, and possible termination of card
  processing — including MATCH-listing, which effectively blocks opening a new merchant
  account. (Specific Visa post-breach program mechanics beyond this: not established in
  source research.)
- Honesty statement: for a small merchant that files its SAQ, enforcement is essentially
  invisible; the machinery only bites on missed paperwork or a breach.

## The SAQ triage (where nearly all founders land)

Most founders never face an on-site QSA audit. Small merchants (Level 4) validate via an
annual **Self-Assessment Questionnaire (SAQ)** — a checklist filed with your processor.
Which SAQ depends on how card data touches your systems:

- **SAQ A** — payment fully outsourced (processor-hosted checkout, iframe elements, or a
  redirect to PayPal/Stripe). Shortest questionnaire. **The correct answer for most SaaS
  founders.**
- **SAQ A-EP** — your own site affects the payment flow (e.g., your code posts card data
  to the processor's API). Dramatically heavier.
- **SAQ D** — you store, process, or transmit card data yourself. Near-full PCI DSS.
  Triage message: **don't do this.**

**The 2025 nuance (fully in effect; verified 2026-07-28):** PCI DSS v4.0/4.0.1's
future-dated requirements became mandatory 31 March 2025. Anti-skimming requirements 6.4.3
(inventory and integrity of scripts on the payment page) and 11.6.1 (detecting tampering
with the payment page) became mandatory for e-commerce merchants. The **January 2025 SAQ A
revision removed those two items from SAQ A but added an eligibility criterion**: you must
confirm your site "is not susceptible to attacks from scripts that could affect the
merchant's e-commerce system(s)." In practice, iframe merchants get that confirmation via
their processor's conforming solution or address script risk on their own checkout page.
Net: **SAQ A is still the answer for processor-hosted flows, but "we use Stripe" no longer
ends the conversation** — your own checkout page carries a small, real obligation.
(Commentary is split on exactly how much work lands on an iframe-only merchant.)

## Gap-check questions

1. Do you accept card payments at all? (If no, stop — this file does not apply.)
2. When a customer pays, do they type their card number into a page or widget hosted by
   your payment provider (like Stripe Checkout or a PayPal redirect), or into a form your
   own code built?
3. Do card numbers ever touch your own servers, database, logs, or spreadsheets — even
   briefly?
4. Have you filed the annual self-assessment questionnaire (the "SAQ" — a compliance
   checklist your payment provider asks for) in the last 12 months? Do you know which
   type you filed?
5. Do you know what third-party scripts run on your checkout page, and would you notice
   if one changed?
6. Has your payment provider ever emailed you about a non-compliance fee, an expired
   attestation, or a missing scan?

## First steps

1. Map the card flow: exactly where do card numbers travel? Confirm nothing lands on your
   systems. (Hours.)
2. Confirm your SAQ type in your processor dashboard — Stripe and peers tell you which
   applies and host the filing flow. (Hours.)
3. If you're SAQ A, use the processor's script-security guidance/tooling to satisfy the
   eligibility confirmation about your checkout page. (Hours to a day.)
4. File the SAQ and calendar the annual renewal — the recurring fee band exists almost
   entirely to punish forgotten paperwork. (Hours.)
5. If you find card data on your own systems, treat removing it (re-architecting onto a
   hosted flow) as the project — it collapses SAQ D back toward SAQ A. (Days to weeks.)

## Cost baselines

- Steady-state for an SAQ A merchant: near zero beyond staff time; the main money risk is
  the ~$20–$250/month non-compliance fee for unfiled paperwork (verified 2026-07-28;
  sourced from processor/security-vendor explainers — vendor-published, treat as a band).
- SAQ A-EP / SAQ D remediation or QSA audit costs: not established in source research.

## Sources

All accessed 2026-07-28: blog.pcisecuritystandards.org (SAQ A update announcement;
post-31-March-2025 e-commerce guidance podcast); securitymetrics.com v4.0.1 FAQs;
cside.com Stripe/PCI analysis; clearlypayments.com and securitycompass.com non-compliance
fee explainers.
