---
id: cyber-insurance
name: Cyber insurance underwriting requirements (de-facto security baseline)
jurisdiction: global (strongest documentation from US market)
tier: quick-ref
enforcer: counterparty — your insurer, via the policy contract and claims process
last_verified: 2026-07-28
volatile:
  - premium-increase bands (40–100%)
  - the baseline control list (underwriting requirements ratchet yearly)
flip_dates:
  - none known
---

## Does this apply to you? (triggers)

Applies if you hold, are buying, or are contractually required to hold cyber insurance
(customer MSAs often require it). It is a real fourth forcing function on small companies
that never see an enterprise questionnaire: the insurer's application *is* their security
audit. No policy and no requirement to get one → NOT APPLICABLE (re-check when a customer
contract demands coverage).

## Who can punish you, and how

Your insurer, through contract — **insurer-contract-mandated**, which doesn't fit the
three buckets cleanly (it is not law, not a customer contract, not a market expectation).
**Bucket note:** the report assigns the bucket per founder; like other frameworks here it
is contract-mandated once any counterparty paper (policy or customer MSA) names it.

Mechanisms: refusal to quote, 40–100% premium increases, coverage exclusions, denial into
surplus-lines pricing — and the sharpest one, **rescission**: misrepresenting your
controls on the application can void coverage precisely when you claim. Documented case:
*Travelers v. ICS* — policy rescinded where MFA was claimed on the application but was in
place only on the firewall. (Verified 2026-07-28.)

## Penalties & enforcement reality

Honesty statement: enforcement is at quote time and claim time, and it demonstrably
reaches small companies — the shift in 2026 underwriting is from questionnaire
self-attestation to *proof* (technical scans, evidence demanded when you claim). An
inaccurate application is worse than no policy: you pay premiums and discover at claim
time you were never covered.

## The 2026 underwriting baseline (verified 2026-07-28)

Effectively mandated: enforced MFA (multi-factor login — a second verification step) on
email, remote access, and admin accounts; EDR (endpoint detection and response — security
software on every laptop/server) on all endpoints; tested, immutable backups (copies that
ransomware can't alter); a written incident-response plan; security awareness training;
patch management. This list doubles as a generic security-baseline gap check even for the
uninsured.

## Gap-check questions

1. Do you hold a cyber policy, or does any customer contract require you to?
2. Who filled in the insurance application, and would every answer on it survive an
   auditor's visit today? (Wrong answers can void the policy.)
3. Is a second login step (MFA) enforced on email, remote access, and admin accounts —
   everywhere, not just somewhere?
4. Does every laptop and server run monitored security software (EDR)?
5. Do you have backups that ransomware can't alter, and have you tested restoring them?
6. Is there a written plan for what you do in the first 24 hours of an incident?

## First steps

1. Re-read your last insurance application against reality; fix either the controls or
   the answers before renewal. (Hours.) 2. Close the baseline in order: MFA → EDR →
   tested backups → written IR plan → training/patching. (Days to weeks.) 3. Keep
   evidence (screenshots, configs) — claims now require proof.

## Cost baselines

Premiums vary too widely by sector/size to band usefully (not established in source
research). The documented cost of a control-gap: **40–100% premium increases,
exclusions, or denial** into surplus-lines pricing at renewal (verified 2026-07-28) —
and rescinded coverage after a loss if the application misstated controls.

## Sources

All accessed 2026-07-28: moneygeek.com, consilien.com, and todyl.com cyber-insurance
requirement writeups (Travelers v. ICS discussed therein).
