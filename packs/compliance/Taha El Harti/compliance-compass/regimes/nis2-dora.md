---
id: nis2-dora
name: NIS2 (Directive (EU) 2022/2555) + DORA (Regulation (EU) 2022/2554) — screen-out pair
jurisdiction: EU
tier: quick-ref
enforcer: national cybersecurity authorities (NIS2) / financial regulators (DORA) for the in-scope minority; for most startups, in-scope customers via supply-chain security questionnaires and mandatory ICT contract clauses
last_verified: 2026-07-28
volatile:
  - NIS2 national transposition status (uneven; several member states late)
flip_dates: []
---

Purpose of this file: these are **screen-out** regimes for most of the audience — the usual output is "not directly in scope, but expect it in customer contracts."

## Does this apply to you? (triggers)
**NIS2 — sector AND size:**
- In-scope sectors: energy, transport, health, digital infrastructure, cloud/DNS/data centers, managed service providers, digital providers incl. online marketplaces/search/social.
- AND ≥50 employees or ≥€10M turnover ("important"); ≥250 or ≥€50M ("essential").
- **Micro/small enterprises are generally OUT of scope** — except size-independent carve-ins: DNS providers, TLD registries, trust service providers, some telecom.
- Typical startup answer: NOT APPLICABLE directly; re-check on crossing 50 employees/€10M if in a listed sector.

**DORA — status, not size:**
- Applies from 17 Jan 2025, directly (no transposition), to 21 categories of financial entities — banks, insurers, payment/e-money institutions, investment firms, crypto-asset service providers — plus critical ICT third-party providers designated by regulators. **No general size exemption** (proportionality applies; scope does not).
- Typical startup answer: NOT APPLICABLE unless you *are* a regulated financial entity (fintech with a license, registered crypto-asset service provider) — then squarely in scope regardless of headcount. SaaS selling *to* financial entities isn't directly regulated unless designated critical.

## Who can punish you, and how
- In-scope minority: NIS2 national authorities (with management-liability provisions); DORA financial regulators.
- Everyone else: the transmission channel is **contracts** — in-scope customers must manage supply-chain security, so vendors face NIS2-flavored security questionnaires and DORA-mandated ICT contract clauses (audit rights, exit plans). (Bucket assigned per founder in the report.)

## Penalties & enforcement reality
- NIS2: up to €10M or 2% (essential) / €7M or 1.4% (important); verified 2026-07-28.
- DORA: penalties via financial-sector supervision (source research records no figures).
- **Honesty statement:** NIS2 enforcement reality is still forming — national transposition is uneven and no small-company enforcement is on record in the source research. The realistic startup exposure is losing a deal to a security questionnaire, not a fine.

## Gap-check questions
1. Is your business in any of these sectors: energy, transport, health, cloud/hosting/DNS/data centers, managed IT services, online marketplace/search/social?
2. Are you at or past 50 employees or €10M turnover?
3. Do you provide DNS, domain-registry, or trust/certificate services (in scope at any size)?
4. Do you hold any financial license or crypto-asset service registration?
5. Do you sell software or IT services to banks, insurers, or fintechs — and could you answer their security questionnaire and sign their ICT contract addenda today?

## First steps
1. Answer the five questions above; record the screen-out result and the re-check trigger (headcount/turnover threshold, or obtaining a financial license). (hours)
2. If selling into finance or critical sectors: prepare a reusable security-questionnaire answer pack and expect ICT contract addenda (audit rights, exit plans). (days)
3. If a financial license or a listed sector + size match applies: this file is insufficient — escalate to full research. (n/a)

## Cost baselines
Not established in source research.

## Sources
NIS2: Arthur Cox NIS2/SME guidance; ceeyu.io scope explainers; glocert/vanta comparisons. DORA: SANS, activeMind.legal, regulation-dora.eu comparisons (all accessed 2026-07-28).
