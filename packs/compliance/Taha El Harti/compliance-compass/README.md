# Compliance Compass

**A local engine that figures out which compliance rules actually apply to YOUR business —
by talking to you.** You run it in Claude Code, it interviews you (researching live where
it needs to), and when *you* say the picture is complete, it generates a personalized HTML
report: a ranked queue of what to do, what to skip, and what to ask a lawyer.

> **This is triage, not legal advice.** It tells you where to look and what to ask.
> It does not certify anything, and green never means "legally compliant."

To run it: see **HOW-TO-USE.md** (three steps). This file explains the thinking so the report makes sense.

---

## The map: what determines your compliance burden

Almost everything flows from a handful of facts about your business:

1. **What data you touch** — emails? payments? health info? kids? biometrics?
2. **Where the *people* are** — the users, customers, and employees whose data it is.
   (Not where your company is. A US company with EU users owes EU law.)
3. **Where the company is established** — registration, offices, team locations.
4. **What industry you're in** — health, finance, education, and children's products
   carry their own regimes.
5. **Who your buyers are** — consumers, businesses, or government. Enterprise buyers
   bring contracts that demand more than the law does.
6. **Whether you build or deploy AI** — and whether you built the model or use someone
   else's (the obligations differ).
7. **Your scale** — many laws only switch on above revenue/user thresholds; a few apply
   at any size.
8. **How you market** — cookies, tracking, marketing emails and texts each have rules.

The interview exists to establish these facts. Everything else is derived.

## The three buckets: who can punish you, and how

Not all "compliance" is the same animal. The report sorts every finding by enforcement
mechanism:

| Bucket | Who comes after you | Examples |
|---|---|---|
| **Law-mandated** | Regulators (fines, orders) — and sometimes private lawsuits | GDPR, CCPA, COPPA, HIPAA, EU AI Act |
| **Contract-mandated** | Counterparties: customers, card networks, insurers (lost deals, fees, rescinded coverage) | DPAs, PCI DSS, security addenda, cyber-insurance terms |
| **Market-expected** | Nobody — but enterprise deals die without them | SOC 2, ISO 27001, HITRUST |

A framework can move buckets: SOC 2 is market-expected until a customer contract names
it — then it's contract-mandated for that deal. For many B2B founders the contract bucket
is the *real* #1 risk, not fines.

## The mindset

- **Most rules won't apply to you.** Half the value of the report is the "Not applicable —
  and why" section: what you can safely not spend money on today, and what would change that.
- **Regulator risk is uneven.** Some regimes demonstrably reach small companies (free-to-file
  GDPR complaints, children's apps, health apps); others almost never do. The report says
  which is which, per regime, with evidence — not vibes.
- **A breach changes everything at once.** The report includes a "if you were breached
  tomorrow" timeline: every notification clock you'd be on, simultaneously.
- **Facts go stale.** Every number in your report carries a verification date, and the
  engine re-checks time-sensitive numbers live before quoting them. If your report is
  months old, regenerate it.

## What's in this folder

```
HOW-TO-USE.md      ← how to run it (read this first)
CLAUDE.md          ← the engine's standing instructions (loaded automatically)
.claude/skills/    ← the engine itself: the interview + the report generator
regimes/           ← the regime library (one file per law/framework — readable, editable)
knowledge/         ← drop your documents here (optional)
output/            ← your generated reports
lite/MEGA-PROMPT.md← fallback for claude.ai if you can't run Claude Code
```

## Compatibility

- **Claude Code** (terminal or desktop app): full experience — this is the target.
- **claude.ai** (browser): use `lite/MEGA-PROMPT.md` — same interview, report as an
  artifact, no folder features.
- **Claude Cowork**: untested. It can read this folder's files if you grant it the folder
  and tell it "read CLAUDE.md and README.md and follow them", but folder skills don't load
  there — expect a rougher experience.

## Keeping it current

The regime library was last verified on the date stamped inside each file in `regimes/`.
The engine re-verifies time-sensitive numbers live during interviews, and flags anything
it couldn't verify. For a fresh library, re-download this package.

---

*Compliance Compass provides general information for triage purposes only. It is not
legal advice, no attorney-client relationship is created, and its output should be
reviewed with qualified counsel before you rely on it.*
