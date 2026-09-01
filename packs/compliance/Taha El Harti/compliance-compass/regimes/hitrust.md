---
id: hitrust
name: HITRUST CSF (certifiable framework harmonizing HIPAA, NIST, ISO, PCI)
jurisdiction: US (healthcare enterprise buyers)
tier: quick-ref
enforcer: counterparty — large US payers/hospital systems via BAAs and vendor programs
last_verified: 2026-07-28
volatile:
  - all tier cost bands (e1/i1/r2)
flip_dates:
  - none known (CSF v11.7.0 released Dec 2025; already mandatory for new e1/i1 since 2026-03-31)
---

## Does this apply to you? (triggers)

**Only when a buyer names it.** Demanded almost exclusively by US healthcare enterprise
buyers — large payers, hospital systems, some pharma — often as a hard requirement in a
BAA (Business Associate Agreement, the HIPAA vendor contract) or vendor program. Some
large payers (historically the UnitedHealth/Optum and Anthem/Elevance orbit) effectively
mandate it. Not selling to US healthcare enterprises, or no buyer has named it → NOT
APPLICABLE (re-check when a payer or hospital deal appears). Default health-tech path
without a named demand: HIPAA (mandatory law) + SOC 2 Type 2 covers most sales.

## Who can punish you, and how

No legal force. The named buyer blocks or terminates the deal. **Bucket note:** HITRUST
straddles market-expected and contract-mandated — when demanded, it is nearly always
written into a specific contract or vendor program; the report assigns the bucket per
founder. Unlike SOC 2, there IS a central certifying body (HITRUST itself QA's and
certifies assessments performed by authorized external assessors).

## Penalties & enforcement reality

Commercial only: lost payer/hospital contracts. Honesty statement: no legal exposure
exists for lacking it; the only question is whether a specific deal requires it and pays
for it.

## Cost baselines — tiers (2026, verified 2026-07-28; assessor/consultancy figures — skew high)

- **e1** (Essentials, 44 controls, 1-yr cert): ~$35k–$50k all-in first year; annual
  reassessment.
- **i1** (Implemented, ~180 controls, 1-yr cert): ~$70k–$120k all-in; annual reassessment
  with a lighter "rapid recert" in alternating years.
- **r2** (Risk-based, 2-yr cert): ~$100k–$500k+ all-in; the "payer-grade" cert most people
  mean by "HITRUST." Interim assessment at year 1. **Never pursue speculatively.**
- A combined engagement with a qualified firm can yield HITRUST cert + SOC 2 report.

## Gap-check questions

1. Do you sell to US healthcare organizations — insurers, hospital systems, or pharma?
2. Has any buyer named "HITRUST" in a contract, vendor program, or questionnaire?
3. If yes: would they accept an entry tier (e1/i1), or does the paper say certified r2?
4. Is the deal large enough to justify the tier's cost band?
5. Do you already have HIPAA compliance and a SOC 2 report (the default stack that covers
   most health-tech sales without HITRUST)?

## First steps

1. Confirm the demand in writing and which tier satisfies it. 2. Escalation ladder:
HIPAA → SOC 2 → e1/i1 (buyer accepts entry tier) → r2 (contract explicitly requires it
and the deal justifies six figures). 3. If proceeding, ask assessors about a combined
HITRUST + SOC 2 engagement.

## Sources

All accessed 2026-07-28: complyjet.com/blog/hitrust-certification; intuitionlabs.ai
HIPAA/SOC 2/HITRUST guide; integralhs.com HITRUST FAQ; kleapcybersecurity.com
prioritization guide.
