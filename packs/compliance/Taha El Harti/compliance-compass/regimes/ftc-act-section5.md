---
id: ftc-act-section5
name: FTC Act Section 5 cluster (unfair/deceptive practices + ROSCA subscriptions + Health Breach Notification Rule)
jurisdiction: US
tier: full
enforcer: regulator (Federal Trade Commission); no private right of action
last_verified: 2026-07-28
volatile:
  - "$53,088 per-violation civil penalty (Jan 2025 adjustment, frozen through 2026 — see below; expect movement Jan 2027)"
  - "FTC enforcement posture and priorities (leadership-dependent; Ferguson-era focus list as of 2026-07-28)"
  - "status of Click-to-Cancel rule reissuance (vacated Jul 2025)"
flip_dates:
  - "2027-01: next federal civil-penalty inflation adjustment expected (2026 round was cancelled government-wide)"
---

## Does this apply to you? (triggers)

**Essentially every US-market business.** "Unfair or deceptive acts or practices in or
affecting commerce" — no thresholds, no registration, no size exemption, no opt-out.
This is the regime founders least expect and are most universally subject to. There is
no NOT APPLICABLE outcome here for a company selling to US consumers.

The four founder-relevant patterns (all with recent enforcement, verified 2026-07-28):

1. **Privacy-policy violations = deception.** Saying "we never share your data" while
   running ad pixels is a case regardless of any privacy statute (GoodRx, BetterHelp,
   Cerebral line; 2025–26 actions continue against data brokers / location sellers).
2. **Dark patterns / negative-option billing (ROSCA).** Applies to any subscription or
   auto-renew flow. Amazon: **$2.5B settlement (Sept 25, 2025)** — $1B civil penalty
   (largest ever for an FTC rule violation) + $1.5B redress, over Prime enrollment and
   cancellation dark patterns. Note: the separate "Click-to-Cancel" rule was vacated
   (8th Cir., Jul 2025), but ROSCA itself is intact and is what Amazon was charged
   under. State auto-renewal laws (esp. CA) add another layer.
3. **AI washing.** "Operation AI Comply" (launched Sept 2024) survived the
   administration change: ~a dozen AI-claims cases in 2025 (DoNotPay order finalized
   2025; Air AI, Aug 2025 — likely first agentic-AI-claims case). The test: are your
   specific claims about what the AI does substantiated?
4. **Data security as unfairness.** Inadequate security practices are an "unfair
   practice" — long line of cases, continuing under current leadership.
5. **Health Breach Notification Rule (HBNR)** — for health/wellness products NOT
   covered by HIPAA (the 2024 update, effective Jul 29, 2024, swept in most health
   apps and connected devices). "Breach" includes **unauthorized disclosure** — e.g.,
   ad-tracker sharing of health data without authorization, not just hacking.
   Full decision tree lives in `hipaa-hbnr.md`.

## Who can punish you, and how

The FTC only — no private lawsuits under this act. Mechanics worth teaching plainly:

- **Bare §5 first violation** → injunctive order + (limited post-*AMG*) redress —
  no automatic fine.
- **Violation of a trade rule** (ROSCA, HBNR, COPPA, TSR) **or of an existing FTC
  order** → civil penalties up to **$53,088 per violation** (verified 2026-07-28).
- One-liner: *the first pure-deception hit is an order; rule violations and second
  strikes are fines.*

Penalty-figure note: $53,088 is the Jan 2025 inflation adjustment, **frozen through
2026** — the routine 2026 adjustment was cancelled government-wide (OMB M-26-11,
Apr 17, 2026; the Oct 2025 shutdown blocked the required CPI data). Expect the figure
to move in Jan 2027.

## Penalties & enforcement reality

- Rule violations: up to $53,088/violation (per email, per child, per day depending on
  the rule — theoretical totals get large fast). Frozen-2026 note above applies.
- HBNR/health-privacy track record: GoodRx $1.5M (first HBNR action, Feb 2023), Easy
  Healthcare/Premom (2023), plus companion §5 cases BetterHelp $7.8M (2023) and
  Cerebral $7M (2024) — all ad-pixel/health-data sharing cases.
- Posture as of 2026-07-28: Chair Ferguson; fewer commissioners; publicly stated pivot
  away from novel §5 theories toward established statutes (COPPA, ROSCA, HBNR) where
  penalties attach; sustained activity on children's privacy, data security, deceptive
  data practices, health claims, and AI claims. Ferguson has said (MLex) privacy case
  volume will jump in late 2026. The catch-all is not dormant; it re-centered on
  rule-based cases.
- **Honesty statement:** enforcement is complaint- and headline-driven; the recent
  penalty cases named here are mid-size to giant companies, but the underlying
  patterns (pixel-vs-policy mismatch, hard-to-cancel subscriptions, unsubstantiated
  AI claims) are exactly what small companies do — and rule violations carry
  first-strike fines. No small-company fine list was established in source research.

## Gap-check questions

1. Does your privacy policy match your actual data flows — have you audited what your
   pixels and SDKs really send, against what the policy says?
2. Can a subscriber cancel as easily as they signed up, in the same channel?
3. Is your renewal/billing disclosed clearly before checkout (no pre-ticked boxes,
   no buried terms)?
4. Can you substantiate every AI capability claim on your landing page with evidence
   you could show a regulator?
5. Does your actual security (MFA, encryption, access controls) match your "we take
   security seriously" marketing claim?
6. If you handle health-ish data outside a doctor/insurer relationship: would an
   ad-tracker on your site count as disclosing that data without permission?
7. Are your testimonials, endorsements, and "results" claims real and typical?

## First steps

1. Pixel/SDK audit against the privacy policy; fix the policy or the pixels (hours–days).
2. Walk your own cancellation flow as a customer; make it symmetric with signup (hours).
3. Inventory marketing claims (AI, security, results) and attach substantiation to each;
   delete what you can't back up (hours–days).
4. Baseline security hygiene: MFA everywhere, encryption at rest/in transit, access
   controls (days).
5. If health-adjacent and not HIPAA-covered: read `hipaa-hbnr.md` and add the breach-
   notification path to your incident plan (hours).

## Cost baselines

Not established in source research.

## Sources

All accessed 2026-07-28: FTC Amazon/ROSCA case page; Alston & Bird (Amazon settlement);
Benesch (Operation AI Comply one year in); DLA Piper (Air AI); IAPP (FTC next
priorities); MLex (Ferguson late-2026 statement); ZwillGen (Ferguson FTC); FTC business
guidance on consumer health information and HBNR; 16 CFR Part 318; Federal Register
2026 inflation-adjustment notices (frozen-adjustment note).
