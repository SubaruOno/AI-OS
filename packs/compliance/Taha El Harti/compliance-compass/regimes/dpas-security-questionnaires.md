---
id: dpas-security-questionnaires
name: DPAs, enterprise security addenda & security questionnaires (category file)
jurisdiction: global (attaches through whatever contract you sign)
tier: full
enforcer: counterparty — enterprise customers, via contract terms and procurement gates
last_verified: 2026-07-28
volatile:
  - questionnaire sizes and volumes (SIG tiers, CAIQ question count, exchange volume)
  - "market standard" breach-notification windows (drifting shorter)
flip_dates:
  - none known
---

## Does this apply to you? (triggers)

This is a **category**, not one instrument: the paper an enterprise customer attaches to a
deal — a Data Processing Agreement (**DPA**: the contract governing how you handle their
personal data), a security addendum/exhibit, and one or more security questionnaires.

Applies when: you sell B2B and handle customer data, and any customer large enough to have
a legal or procurement team is in your pipeline. The first DPA or questionnaire usually
arrives with the first mid-market deal.

Does NOT apply: consumer-only businesses, or B2B where you never touch customer data. NOT
APPLICABLE, not "green" — re-check at the first enterprise prospect.

## Who can punish you, and how

Your own customers, twice: **before signature** (procurement blocks the deal until the
questionnaire and addenda clear) and **after signature** (the signed DPA/addendum is
binding contract — missing a notification deadline or subprocessor obligation is breach of
contract, with whatever liability the contract sets).

**Bucket note:** this category *is* the connective tissue of the contract-mandated bucket
— it is how market-expected frameworks (SOC 2, ISO 27001) get written into contracts and
migrate buckets. The report assigns buckets per founder based on what they have signed.

## Penalties & enforcement reality

- No statutory penalties — the contract is the whole mechanism. Exposure = the contract's
  liability terms. **Breach-liability carve-outs (often uncapped or "super-capped") are
  the single most economically dangerous clause a startup signs** in this category.
- Honesty statement: enforcement is real but private — stalled deals, indemnity claims,
  and terminations, none of it visible in public records.

### What enterprise paper actually demands (2026 market norms, verified 2026-07-28)

- **Breach notification faster than law requires:** market standard 48–72h after
  confirming an incident; enterprises frequently push for 24–48h. Teaching point:
  contracts routinely exceed statutory duties — **the signed contract, not the law, is
  your binding clock**. Signing 24h while lacking the monitoring to detect a breach in
  24h is the classic self-inflicted gap: check what you *signed* against what you can
  *achieve*.
- **Audit rights:** well-negotiated = an annual SOC 2 report satisfies in the first
  instance, on-site audits only for cause with notice. Badly negotiated = open-ended
  audit rights.
- **Subprocessor management:** a maintained public list of subprocessors (other companies
  that process your customers' data on your behalf), advance notice of changes, customer
  objection rights.
- Also common: encryption standards, personnel/background checks, data residency and
  deletion SLAs, breach-liability carve-outs (above).

### The questionnaires (verified 2026-07-28)

- **SIG** (Shared Assessments) — the most widely used in enterprise procurement (100k+
  exchanged/yr). 2026 tiers: SIG Lite ~130 questions, SIG Core ~800, full/custom 1,000+
  across 20 risk domains. Expect Lite first; Core if you're flagged higher-risk.
- **CAIQ** (Cloud Security Alliance) — ~261 questions, cloud-focused. You can pre-publish
  a completed CAIQ via CSA STAR Level 1 self-assessment to short-circuit questionnaires.
- ~80% of questions overlap across formats (encryption, access management, vulnerability
  scanning, incident response, certifications).

**The answer-library strategy:** a SOC 2 report + a maintained library of past
questionnaire answers kills most questionnaires; AI questionnaire-answering tooling over
such a library is now standard practice. Build the library from questionnaire #1 — every
answer written twice is waste.

## Gap-check questions

1. Have you signed any customer contract with a data-protection addendum or security
   exhibit attached — and do you know where the signed copies live?
2. What is the shortest breach-notification deadline you have signed (the number of hours
   you promised to tell a customer about a security incident)? If you don't know, that is
   the gap.
3. Could you actually detect, confirm, and notify within that window today?
4. Do you keep a public, current list of your subprocessors (other companies that touch
   your customers' data), and do you notify customers before adding one?
5. Have you granted any customer open-ended audit rights, or is a SOC 2 report the agreed
   first answer?
6. Do any signed contracts make data-breach damages uncapped (a "carve-out" from the
   normal liability limit)? Has anyone checked?
7. Do you keep a reusable answer library from past security questionnaires, or start each
   one from a blank page?

## First steps

1. Collect every signed DPA and security addendum into one folder; extract the
   notification clocks, audit rights, and liability carve-outs into a one-page register.
   (Hours to a day.)
2. Compare the shortest signed notification clock to your actual detection capability;
   flag the gap for remediation or renegotiation. (Hours.)
3. Publish a subprocessor list and set up the change-notification channel your contracts
   require. (Hours.)
4. Start the answer library with your last completed questionnaire; consider a CSA STAR
   Level 1 self-assessment (a free-to-publish CAIQ) to preempt future ones. (Days.)
5. Draft a standard negotiation position for future paper: SOC 2 satisfies audits, 72h
   notification, liability caps intact. (Day, with counsel review.)

## Cost baselines

Not established in source research — no direct cost figures for DPA negotiation,
questionnaire tooling, or answer-library operation appear in the sources. (Indirect costs
run through SOC 2/ISO 27001 — see those files.)

## Sources

All accessed 2026-07-28: blog.promise.legal SaaS DPA requirements; secureprivacy.ai DPA
guide; workstreet.com CAIQ vs SIG; sparrowgenie.com SIG explainer; wolfia.com
questionnaire guide.
