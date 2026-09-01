---
id: wa-mhmd-il-bipa
name: Washington My Health My Data + Illinois BIPA (the two private-lawsuit outliers)
jurisdiction: US-WA / US-IL
tier: quick-ref
enforcer: private lawsuits (both) — the outlier trait driving outsized founder risk; state AGs secondarily
last_verified: 2026-07-28
volatile:
  - "BIPA statutory damages ($1,000 negligent / $5,000 willful per violation; verified 2026-07-28)"
  - "MHMD litigation landscape (young law — case law still forming)"
flip_dates: []
---

## Does this apply to you? (triggers)

Neither is a "comprehensive" privacy law, but both carry a **private right of
action** — the trait that turns compliance gaps into class actions. For a
health-adjacent or biometrics-touching startup they can outrank several comprehensive
state laws in real risk.

**Washington My Health My Data (MHMD):** in effect since 2024 (verified 2026-07-28).
Covers "consumer health data" of Washington consumers with a **very low bar to
coverage** — no size threshold established in source research. Health-adjacent apps
(fitness, period, mental wellness) that escape HIPAA (see `hipaa-hbnr.md`) can land
squarely here; the private right of action makes it arguably higher litigation risk
than several comprehensive laws. Gate: no WA consumers AND no health-ish data → NOT
APPLICABLE; re-check when either changes. Detailed obligations: not established in
source research — research live before advising a covered founder.

**Illinois BIPA:** collecting biometric identifiers (fingerprints, face geometry,
voiceprints) from Illinois residents — including via vendor SDKs doing face-tagging
or voice ID. **$1,000 per negligent / $5,000 per willful violation** (verified
2026-07-28), private right of action — the highest-litigation-risk Illinois law for
anything touching biometrics. Adjacent IL flags: AI Video Interview Act; HB 3773 (AI
in employment decisions, eff. Jan 1, 2026). Gate: no biometric processing of IL
residents → NOT APPLICABLE; re-check when adding any face/voice/fingerprint feature.

## Who can punish you, and how

Private plaintiffs — class-action firms — are the primary adversary for both, with
per-person statutory damages doing the scaling. State AGs enforce secondarily. This is
the same risk shape as TCPA: nobody needs a regulator's permission to sue.

## Penalties & enforcement reality

**Honesty statement:** both regimes are litigation-driven; per-violation statutory
damages make small companies economically viable targets, as with TCPA. Specific
small-company case examples were not established in source research — the structural
risk (uncapped per-person damages + plaintiffs' bar) is the point.

## Gap-check questions

1. Do you have users in Washington state, and does any data you hold relate to their
   health, even loosely (fitness, cycles, mood, symptoms)?
2. Does any feature process face geometry, fingerprints, or voiceprints — yours or a
   vendor SDK's — for anyone who might be in Illinois?
3. If yes to either: do you obtain explicit written consent *before* collection?
4. Do you have a published retention-and-destruction schedule for biometric data?
5. Could you geo-gate the feature off in WA/IL faster than you could build compliance?

## First steps

1. Feature inventory: anything biometric, anything health-ish; map against WA/IL user
   presence (hours).
2. If exposed: consent-before-collection flow, written policy, retention schedule —
   or geo-gate the feature while you build it (days).
3. Vendor check: SDKs doing face/voice processing put you in scope too (hours).

## Cost baselines

Not established in source research.

## Sources

Accessed 2026-07-28: Agent A2 research memo §1.3 and §5 (MHMD in-effect status, PRA,
low coverage bar; BIPA damages and IL AI-law context). Detailed statutory obligations
for both were outside the memo's scope — live-research before relying on specifics.
