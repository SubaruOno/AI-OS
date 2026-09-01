---
id: canada-pipeda
name: Canada — PIPEDA (current law) + Bill C-36 (pending) + Quebec Law 25
jurisdiction: Canada (federal), with provincial overlays (QC/AB/BC)
tier: quick-ref
enforcer: regulator — OPC federally (weak fining power); Quebec's CAI under Law 25 (strong)
last_verified: 2026-07-28
volatile:
  - Bill C-36 status (pending as of 2026-07-28 — if passed, this file's enforcement headline inverts)
flip_dates:
  - "unknown date: Bill C-36 passage would replace PIPEDA Part 1, create a new regulator (Digital Safety and Data Protection Commission), and raise fines to the greater of C$25m or 5% of global revenue"
---

## Does this apply to you? (triggers)

Applies if you handle personal information in the course of commercial activity involving
people in Canada. Broadly fits the GDPR-family skeleton (see `gdpr-family-pattern.md`).
No Canadian customers or operations → NOT APPLICABLE (re-check on Canadian expansion).

**Triage headline: a company doing business Canada-wide should triage against Quebec's
Law 25, not just PIPEDA** — Law 25 is fully in force and currently the strictest regime
in Canada (fines up to C$25m/4%). Alberta and BC also have substantially similar
provincial laws.

## Who can punish you, and how

- Federal: the OPC (Office of the Privacy Commissioner) — **weak direct fining power**;
  enforcement is reputational and complaint-driven. Mandatory breach reporting since 2018.
- Quebec: the CAI under Law 25, with real fining power.
**Bucket note:** law bucket where applicable; contracts (DPAs) can stack stricter duties
on top — the report assigns buckets per founder.

## Penalties & enforcement reality (verified 2026-07-28)

- PIPEDA today: consent-based; the OPC's practical levers are findings, publicity, and
  court referral — not fines. Honesty statement: federal enforcement against small
  companies is complaint-driven and reputational; the real monetary exposure today is
  Quebec (up to C$25m/4% under Law 25).
- **Reform status — state this precisely:** Bill C-27 died at prorogation (Jan 2025).
  Third attempt, **Bill C-36 ("Protecting Privacy and Consumer Data Act"), introduced
  15 Jun 2026 — pending, not law, as of 2026-07-28.** It would replace PIPEDA Part 1,
  create a new regulator, recognize privacy as a fundamental right, and carry fines up to
  the greater of C$25m or 5% of global revenue. AI regulation is expected to travel
  separately. If C-36 passes, the "weak enforcement" headline above inverts.

## Gap-check questions

1. Do you have customers or users in Canada? In Quebec specifically?
2. Do you ask for meaningful agreement (consent) before collecting personal information —
   the core of Canadian federal law?
3. If a data breach happened, do you know it must be reported (mandatory federally since
   2018) and who would file the report?
4. If you serve Quebec: have you checked Law 25's extra duties (the strictest rules in
   Canada)?
5. Is someone watching Bill C-36's progress, since it would raise Canadian fines to
   GDPR-scale?

## First steps

1. If you serve Quebec, triage against Law 25 first — it sets the practical bar. (Day.)
2. Confirm a breach-reporting path exists (federal reporting is mandatory). (Hours.)
3. Set a re-check on Bill C-36 status; content written against PIPEDA has a shelf life.
   (Minutes.)

## Cost baselines

Not established in source research.

## Sources

Accessed 2026-07-28: agent-a3 research memo §7 (PIPEDA/OPC posture, C-27 death, C-36
introduction 2026-06-15, Quebec Law 25 status), verified via web search on that date.
Note: detailed Law 25 obligations were outside the memo's scope — not established in
source research beyond the fine ceiling and "strictest in Canada" finding.
