---
id: us-breach-notification
name: US state breach-notification pattern (all 50 states + DC + territories)
jurisdiction: US (54 parallel regimes)
tier: quick-ref
enforcer: state Attorneys General (54 of them, in parallel); sector regulators via federal overlays
last_verified: 2026-07-28
volatile:
  - "per-state deadlines (~20 states with hard 30–60 day clocks; CA moved to 30 days Jan 1, 2026)"
  - "definitions of 'personal information' (states keep adding medical/biometric/credentials)"
flip_dates: []
---

## Does this apply to you? (triggers)

Every business holding US residents' personal information — no thresholds, no size
exemptions. Dormant until the day of an incident, then **all applicable states' laws
fire at once, keyed to where affected users live, not where the company is.** There
is no NOT APPLICABLE for a company with US user data; only "not yet."

## The pattern: one incident, many clocks

**All 50 states + DC + 3 territories = 54 regimes** (verified 2026-07-28). Common
skeleton, per-state variation in every joint:

1. "Personal information" = name + a sensitive element (SSN, driver's license,
   financial account — increasingly medical, biometric, login credentials).
2. Notify residents "without unreasonable delay" — **~20 states set hard 30–60 day
   deadlines** (**California moved to 30 days effective Jan 1, 2026**; Colorado and
   Florida 30; Texas 60). Verified 2026-07-28.
3. **~36 states also require AG/agency notice**, often above 500–1,000 residents.
4. **Encryption safe harbor is nearly universal** — encrypted data (key not
   compromised) usually means no notification duty. The cheapest pre-breach control.
5. Risk-of-harm exceptions common; AG-enforced penalties.
6. Federal overlays stack per sector: HIPAA breach rule, FTC HBNR (health apps),
   GLBA/Safeguards (fintech-adjacent), SEC 8-K (public companies).

Do not enumerate 54 statutes mid-incident — the play is counsel or a breach-response
service that maintains the state matrix.

## Who can punish you, and how

State attorneys general enforce nearly everywhere (civil penalties, consent decrees;
multi-state coordination on breaches is routine). California adds a narrow **private
right of action** for breaches ($100–$750 per consumer per incident; verified
2026-07-28). Contracts stack on top: customer DPAs/BAAs typically require notice to the
customer faster than any statute.

## Penalties & enforcement reality

**Honesty statement:** small-company enforcement specifics were not established in
source research; the operational risk is missing a hard clock in a state you didn't
think about. Multi-state AG coordination on breaches is routine.

## Gap-check questions

1. If you discovered a breach today, could you list which states your users live in?
2. Is your sensitive data encrypted at rest — and would you know whether the keys
   were also taken?
3. Do you have an incident-response plan naming who calls whom in the first 24 hours?
4. Do you have breach counsel or a response service lined up *before* needing one?
5. Would you know your regulator-notice duties as well as user-notice ones (health,
   finance, public-company overlays)?

## First steps

1. Encrypt personal data at rest — the near-universal safe harbor (days).
2. One-page incident-response plan: roles, first calls, evidence preservation (hours).
3. Line up breach counsel / IR service now; many cyber-insurance policies include one
   (hours).
4. Know your user-state distribution — same data need as `us-state-privacy-pattern.md`
   (hours).

## Cost baselines

Not established in source research.

## Sources

All accessed 2026-07-28: Jackson Lewis (state breach patchwork overview); IAPP state
breach-notification chart; Privacy Rights Clearinghouse 50-state survey (2026 ed.).
