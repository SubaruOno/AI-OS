# Start here, Table 07: Compliance

> Written 29 July 2026, Operator Day, Porto Montenegro.
>
> This file is addressed to Claude, not to the person who downloaded it. If you're the person: drop this whole folder into the workspace you built this morning, then tell Claude "read Table-07-Compliance/START-HERE.md and take me through it."

---

## What this folder is, and what it isn't

Taha El Harti handed over Compliance Compass: an engine that works out which compliance rules actually apply to a specific business by interviewing the person who runs it, researching live where it needs to, and producing a ranked queue of what to do, what to skip, and what to take to a lawyer.

This pack is different from the others on one axis. Most packs in this room are shaped around the author's business and need reshaping around the reader's. This one was built to adapt itself, because the whole point is that compliance burden is a function of facts about a specific company. The interview is the adaptation.

So your job here shifts. Less rebuilding, more making the interview sharper by feeding it everything the workspace already knows, and being clear-eyed about where its knowledge has a shelf life.

**Say this before anything else, and mean it:** this is triage, not legal advice. It tells them where to look and what to ask. It doesn't certify anything, and green never means legally compliant. Taha's own README says exactly that, and if the person walks away thinking otherwise, the session did harm rather than good.

---

## The rule

**Adapt, don't install blindly.** Three honest outcomes:

1. **Run it as-is, with their context loaded.** The most likely outcome here, and a good one.
2. **Take the model, apply it narrowly.** Sometimes they only need one regime answered properly rather than the full sweep.
3. **Take nothing, keep the note.** They're pre-revenue, no customer data, no marketing list. The honest answer is "not yet, and here's the trigger that changes it."

---

## Step 1: load the business first

Read quietly before opening anything:

- `CLAUDE.md`
- `context/business.md`, `context/you.md`, `context/offer.md`
- `context/strategy.md`, `context/numbers.md`, `context/team.md`
- `context/tech-stack.md`

Taha's README names the eight facts that drive almost everything, and you can pre-answer several of them from context. Work out what you already know about:

- **What data they touch.** Emails, payments, health information, children's data, biometrics.
- **Where the people are.** Their users, customers and staff, not where the company is registered. A US company with EU users owes EU law.
- **Where the company is established.** Registration, offices, team locations. `team.md` often answers this without anyone realising.
- **What industry.** Health, finance, education and children's products carry their own regimes.
- **Who buys.** Consumers, businesses, or government. Enterprise buyers bring contracts that demand more than the law does.
- **Whether they build or deploy AI**, and whether they built the model or use someone else's.
- **Scale.** Many laws only switch on above a revenue or user threshold.
- **How they market.** Cookies, tracking, marketing email and texts each have rules.

Bring those into the interview as things you already believe, and ask them to correct you. That turns a thirty-minute interview into a ten-minute one and makes it more accurate, because people are better at correcting a wrong statement than answering an open question.

If those context files don't exist, run the interview cold as designed. It works fine that way, it just takes longer.

---

## Step 2: survey what's actually in here

`Taha El Harti/compliance-compass/` is a full workspace. Read `README.md` for the thinking, then `HOW-TO-USE.md` for the three steps.

**The three-bucket model** is the best idea in the pack and worth explaining before you run anything, because it reframes the whole subject:

| Bucket | Who comes after you | Examples |
|---|---|---|
| Law-mandated | Regulators, with fines and orders, sometimes private lawsuits | GDPR, CCPA, COPPA, HIPAA, EU AI Act |
| Contract-mandated | Counterparties: customers, card networks, insurers. Lost deals, fees, rescinded cover | DPAs, PCI DSS, security addenda, cyber-insurance terms |
| Market-expected | Nobody, but enterprise deals die without them | SOC 2, ISO 27001, HITRUST |

And the observation most founders get wrong: a framework moves buckets. SOC 2 is market-expected until a customer contract names it, and then it's contract-mandated for that deal. For a lot of B2B founders the contract bucket is the real number one risk, not fines.

**`regimes/`** holds 24 reference files: GDPR and UK GDPR, the GDPR family pattern, CCPA/CPRA and the US state privacy pattern, COPPA, HIPAA and HBNR, PCI DSS, SOC 2, ISO 27001 and ISO 42001, HITRUST, the EU AI Act, EU Data Act, EU Accessibility Act, NIS2 and DORA, ePrivacy and cookies, CAN-SPAM, TCPA, FTC Act Section 5, PIPEDA, US breach notification, Washington MHMD and Illinois BIPA, DPAs and security questionnaires, and cyber insurance. There's a `_SCHEMA.md` explaining the shape, which matters if you end up adding one.

**`.claude/skills/`** holds the interview skill (with an interview guide and research rules) and the report generator (with scoring rules and design guidance).

**`lite/MEGA-PROMPT.md`** is the no-terminal version: paste it into a chat at claude.ai and get the same interview with the report as a downloadable artifact. Useful for a teammate or a co-founder who isn't in Claude Code.

**`what-is-compliance-compass-workless.html`** is a plain explainer to open in a browser.

*Assumes:* live web search during the interview, which the person will be asked to approve. Tell them in advance that it's checking laws, not checking them.

---

## Step 3: name the gap out loud

The gap here isn't about their stack. It's about which regimes are live for them and how fresh the reference material is.

Something like:

> Before we run this, three things I already know from your context that will shape the answer. Your customers are in the UK, Germany and the US, so you're in UK GDPR and GDPR territory whatever your company registration says. You take payments through Stripe, which changes what PCI actually means for you and it's less than people fear. And from `offer.md` you're selling to two enterprise accounts next quarter, which means SOC 2 is about to move from market-expected to contract-mandated for those deals. That's the finding I'd expect to matter most.
>
> One honest caveat on the reference files. Compliance moves, and the EU AI Act in particular has been moving fast. Where a finding is load-bearing for a real decision, the engine will check the current position live rather than trusting what's written down here. Anything it can't verify, we mark as "ask a lawyer" rather than guessing.

---

## Step 4: run it properly

Run the interview. Answer what you can from context, ask the rest, and let "I don't know" be a fine answer, which the pack explicitly allows.

Don't rush to generate the report. It's designed to hold until the person says the picture is complete, and a report built on a thin interview is worse than none because it looks authoritative.

If the full sweep is too much for the time available, pick the two regimes most likely to bite and go properly deep on those instead. A real answer on two beats a shallow pass on twenty.

---

## Step 5: adapt and build

- **Verify anything load-bearing.** The regime files are a starting map, not a current legal position. Where a finding drives a real decision, check it live.
- **Keep the triage framing in the output.** If the report ends up in front of a client or an investor, the "this is not legal advice" line goes with it.
- **Put the findings somewhere they'll be seen again.** A report in `output/` that nobody opens is the failure mode here. Better: pull the top three actions into their workspace as real tasks with owners.
- **Sensitive answers go in `private/`.** Interviews like this surface things about contracts, breaches and data handling that shouldn't sit in a shared folder. Watch for it and offer to move it.
- **Note the trigger conditions.** Compliance changes when the business changes: first EU customer, first enterprise contract, first health or children's data, crossing a revenue threshold. Write those triggers down. That's what makes this re-runnable rather than a one-off.
- **Update `CLAUDE.md`** so future sessions know the assessment exists and when it was run.

---

## Step 6: record what happened

Write a row into `ledger/`: what came from this table, what got assessed, and the top findings.

Date the assessment explicitly. Compliance answers have a shelf life, and in six months the most useful thing in the record will be knowing exactly when this picture was true.

---

## If they're doing this at home

Same process, and this is one of the better packs to do alone since the engine drives the conversation. Load the context first. Set aside a proper block, thirty minutes for the deep version, and have any privacy policy, DPA or security questionnaire to hand, since the pack can read them.

If they're not in Claude Code, point them at `lite/MEGA-PROMPT.md`.

---

*Table 07, Compliance. Speakers: Jannis Moore, Ethan Monkhouse, Taha El Harti. Pack from Taha.*
*From Liam Ottley's AI Makeover, youtube.com/@LiamOttley*
