---
id: soc2
name: SOC 2 (System and Organization Controls 2, AICPA Trust Services Criteria)
jurisdiction: global (US-origin; driven by US enterprise buyers)
tier: full
enforcer: counterparty / market — enterprise buyers and procurement teams; no regulator exists
last_verified: 2026-07-28
volatile:
  - all cost bands (audit fees, platform pricing, first-year all-in, ongoing maintenance)
  - platform pricing specifically (negotiated list prices, never published)
flip_dates:
  - none known
---

## Does this apply to you? (triggers)

SOC 2 is **buyer-driven, almost never proactive**. It applies when your buyers ask for it,
not because of what you build or where you operate.

Applies (start planning) when any of these is true:
- A mid-market or enterprise prospect has sent a security questionnaire.
- Procurement has stalled a deal pending "SOC 2 or equivalent."
- A partner or platform program you want to join requires it.
- You sell (or intend to sell within ~12 months) to companies of roughly 200+ employees.

Does NOT apply (yet): pre-revenue startups and companies selling only to consumers or
small businesses generally do not need it. That is NOT APPLICABLE, not "green" — re-check
whenever your target customer size moves upmarket or the first questionnaire arrives.

## Who can punish you, and how

No regulator, no law, no fine. The punishment is **lost or stalled deals**: procurement
teams refuse to onboard you, or a live deal dies waiting for a report. Once a signed MSA
says "vendor shall maintain a SOC 2 Type 2 report," missing it becomes breach of contract
for that customer.

**Bucket note:** SOC 2 starts in the market-expected bucket and **migrates to
contract-mandated the moment a contract names it**. The bucket describes how the regime
reaches *this founder*, so the report assigns it per founder, per deal.

## Penalties & enforcement reality

- Statutory maxima: none — this is not law anywhere.
- What actually happens: deals slow or die; a common contract compromise is "Type 1 now,
  Type 2 within 12 months." Sophisticated buyers increasingly treat Type 1 alone as a
  placeholder.
- Honesty statement: no one is fined or sued for lacking SOC 2; the entire enforcement
  mechanism is revenue you don't get.

**The anchor fact:** SOC 2 is a **CPA attestation, not a certification**. A licensed CPA
firm examines your controls against the AICPA Trust Services Criteria and issues an
*opinion report* (unqualified, qualified, or adverse). There is no "SOC 2 certified," no
logo, no public registry — anyone saying "certificate" is using marketing shorthand. The
deliverable is a confidential report you share with buyers under NDA. This reframes what
buyers actually want: **evidence, not a badge** (contrast: ISO 27001 is a real certificate
— see `iso-27001.md`).

- **Type 1:** controls suitably designed *at a point in time*. Achievable in 1–3 months,
  cheaper, increasingly a bridge rather than a destination.
- **Type 2:** controls *operated effectively over a period* (observation window typically
  3–12 months; 3-month first windows are common for startups). This is what enterprise
  buyers actually want.
- Scope is chosen: Security (Common Criteria) is mandatory; Availability, Confidentiality,
  Processing Integrity, and Privacy are optional. Most startups do Security only, or
  Security + Availability + Confidentiality.

## Gap-check questions

1. Has a prospect or customer asked for a SOC 2 report — or sent a security questionnaire
   (a long checklist about your security practices) — in the last 12 months?
2. Do you sell, or plan to sell soon, to companies bigger than about 200 employees?
3. Have you already signed a contract that promises a SOC 2 report by a certain date?
4. Do staff sign in to work tools through a single company login with a second
   verification step (SSO with MFA)?
5. Are work laptops centrally managed (you could lock or wipe one remotely)?
6. Does every code change get reviewed by a second person before it ships?
7. Do you run background checks on new hires?
8. Is there a live deal that a faster point-in-time report (Type 1) could unblock?

(Questions 4–7 are the controls that consume most of the readiness budget.)

## First steps

1. Confirm the trigger is real: identify which buyer/deal is asking, and whether Type 1
   would satisfy them as a bridge. (Hours.)
2. Pick scope — Security alone, or + Availability/Confidentiality if buyers demand it.
   (Hours.)
3. Trial a compliance-automation platform and run its gap scan against your stack. (Days.)
4. Fix the control gaps the scan surfaces (MFA/SSO, device management, code review,
   background checks). (Weeks — this is the real work.)
5. Choose the audit firm early — auditor lead times are a common schedule killer — and
   decide Type 1 first vs. straight to a 3-month-window Type 2. (Days to select.)

## Cost baselines (2026 bands, verified 2026-07-28)

All sources are auditors, platforms, or consultancies with pricing incentives: **auditors
publish high figures ("you need help"); automation platforms publish low ones ("easy with
us")**. Treat every number as a planning band, not a quote.

- Type 2 audit fee alone: ~$15k–$70k for startups at specialist firms (low end =
  Security-only, <50 employees); broader market typically $20k–$60k. Big-firm tail
  reaches $430k but is not startup-relevant. Type 1: from ~$5k–$10k, commonly $8k–$25k.
- First-year all-in (audit + platform + pentest + internal time): most startups $25k–$50k;
  up to ~$80k with broader scope. (Mixed vendor sources, 2026-07-28.)
- Ongoing maintenance (annual re-audit + platform + pentest): $15k–$40k/yr — carried from
  prior research, only directionally re-verified in 2026; treat as a soft band.
- Platform pricing (negotiated, unpublished — third-party writeups only): Vanta ~$10k/yr
  small SOC 2-only, $30k–$50k mid-market multi-framework, $80k–$120k+ enterprise; Drata
  ~$7.5k–$100k+/yr; Secureframe from ~$7.5k past $80k.
- Timeline: Type 1 in 1–3 months; first Type 2 report 6–12 months end-to-end.

## Sources

All accessed 2026-07-28: sprinto.com/blog/soc-2-audit-cost; soc2auditors.org/soc-2-audit-cost;
secureleap.tech/blog/soc-2-certification-cost (and its Vanta/Drata pricing reviews);
complyjet.com/blog/soc-2-compliance-cost; drata.com/learn/soc-2/cost; cavanex.com platform
comparison.
