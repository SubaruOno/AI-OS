# Start here, Table 06: Operations

> Written 29 July 2026, Operator Day, Porto Montenegro.
>
> This file is addressed to Claude, not to the person who downloaded it. If you're the person: drop this whole folder into the workspace you built this morning, then tell Claude "read Table-06-Operations/START-HERE.md and take me through it."

---

## What this folder is, and what it isn't

The biggest pack of the day, and the one most likely to be mistaken for a product. Four things are in here: a client audit plugin that a working agency bills real money with, a monthly client reporting engine, a proposal deck generator, and two different approaches to building an operations hub.

Every one of them came out of a specific agency serving specific clients. The audit plugin knows how one firm prices and packages. The reporting engine knows what one agency's clients care about. Neither of those is automatically true here.

**Treat this folder as a signal bank.** These are the strongest artifacts in the room precisely because they're battle-worn, and battle-worn means shaped by a business that probably isn't this one.

*One practical note before you start:* `Adam Goodyer/audit-plugin.zip` and `OPERATIONS/Goodies Pack/audit-plugin.zip` are byte-identical. Same file, two homes. Don't analyse it twice.

---

## The rule

**Adapt, don't install.** Three honest outcomes:

1. **Take it as-is.** Realistic only if they run a service business shaped like the one it came from.
2. **Take the idea, rebuild the piece.** The common one, and most of these were written expecting it. Emil's kits in particular say so explicitly: they interview first and build around the person's own nouns.
3. **Take nothing, keep the note.** They don't have clients, or their operation is too small to need this yet. Say so.

---

## Step 1: load the business first

Read quietly before opening anything:

- `CLAUDE.md`
- `context/business.md`, `context/you.md`, `context/offer.md`
- `context/strategy.md`, `context/numbers.md`, `context/team.md`
- `context/tech-stack.md`

Five things decide the session:

- **Do they have clients, or customers?** A roster of named accounts with ongoing relationships is a different world from a stream of one-off buyers. Half this pack assumes the first.
- **How many, and how do they track them?** Spreadsheet, CRM, memory, notebook. From `tech-stack.md`.
- **Do they sell anything with a proposal?** That decides whether the deck generator is relevant.
- **Do they report to clients today, and how painful is it?** From `you.md`. Monthly reporting is one of the great quiet time sinks and people rarely name it unprompted.
- **What actually eats their week?** This is the question `explore-operations.md` was built to answer, and you should have a working hypothesis before you run it.

If those files don't exist, ask five short questions and carry on.

---

## Step 2: survey what's actually in here

### `OPERATIONS/-explore-operations/explore-operations.md`

An interactive command that finds where a person's time actually goes, picks the one or two things worth systemizing first, understands exactly how they work today, and shapes them into a project ready to hand to a planner.

Read its Stage 0 carefully. It says: read whatever workspace context exists first, and **never ask a question the context already answers.** Then make every later question specific to their business, "your client onboarding" rather than "a hypothetical process". That instruction is the standard for this whole table, and honestly for this whole folder.

It'll also try to pull from a connected calendar or task manager if one's there, and it's explicit about not letting the session turn into an integration setup exercise if nothing's connected.

*Assumes:* a workspace with context, which they have as of this morning.

### `OPERATIONS/Goodies Pack/audit-plugin.zip` (Adam Goodyer, Bosar Agency)

A proper Claude Code plugin, the one APG Software and Bosar Agency use to deliver client AI audits. Five agents running in sequence: extract every process and pain point from meeting transcripts with a source quote for each, research automation opportunities with effort and ROI estimates, render client-ready HTML deliverables, produce a requirements spec and clickable prototype, then a human QA pass that maps corrections back to data fields with an audit trail.

The design idea worth taking even if they never run it: every finding is cited to a quote from the client's own mouth, and every ROI number is calculated from numbers the client gave in an interview. That's why the deliverable holds up in a room.

*Assumes:* they run audits for clients, they record client sessions, and they price by company revenue. The pricing files ship as clearly-labelled example figures with a note to replace them, so nothing sensitive is in here, but nothing usable is either. Those numbers must become theirs before it touches a live client.

### `OPERATIONS/Goodies Pack/client-reports.md` (Emil Faschang)

Builds a monthly client report machine: collectors that pull last month's data from wherever it lives, an engine that computes per-client numbers with month-over-month deltas, a brand interview that turns their logo and colours into the stylesheet, and Claude writing the narrative from the numbers.

The framing is right: retention is downstream of visibility. And it's explicit that this isn't a template to fill in. A bookkeeping firm reports filings completed, an ads agency reports spend and cost per lead, a coaching business reports sessions delivered. Same machinery, their metrics.

*Assumes:* recurring clients who'd read a monthly report, and data living somewhere reachable.

### `OPERATIONS/Goodies Pack/proposal-deck.zip`

One self-contained `proposal.html` the user edits inline in a browser and exports to PDF in one click. No server, no Python, no build step, works the same on Mac and Windows. First run does a brand setup, pulling logo, colours and font from their website via Firecrawl. Content can come from a recorded call or be written by hand with the skill asking follow-ups where the brief is thin.

*Assumes:* they send proposals, and they have a website worth scraping for brand.

### `OPERATIONS/Operations Hub/` (Emil Faschang and Liam Ottley)

Two routes to the same thing, and its own `START-HERE.md` explains the choice better than a summary can. Read that first.

Emil's kit builds a one-screen dashboard on a small local database and API, seeded with their real clients and numbers, usually inside an hour. The dashboard is read-only glass; Claude is the hands. Every change is a sentence, written through the API, recorded in an audit log.

Liam's bundle is the planning method plus a measured case study of the same thing built at larger scale, plus five design reference pages. Slower, more deliberate, better if they want to understand the shape before committing.

*Assumes:* a roster of something (clients, students, accounts) plus a handful of health numbers. Everything runs locally and costs nothing.

---

## Step 3: name the gap out loud

Show a ranked view in their language, using their client names and their numbers.

Something like:

> You've got eleven retainer clients tracked in one spreadsheet that three people edit. Emil's Ops Hub is the obvious first build and it's about an hour. Your nouns are clients, retainer value, renewal date and last touch, not his.
>
> The reporting engine is the second one and it's probably worth more money than the hub, because from `you.md` you lose the better part of two days a month to reporting and two clients churned last quarter without warning. But it needs your data reachable, and right now half of it is in a tool you haven't connected.
>
> Adam's audit plugin is the most impressive thing here and I don't think it's yours. It's built for firms that sell audits as a product. You sell retainers. The idea to steal is citing every finding to a quote from the client, which we can fold into your reporting.
>
> The proposal deck is a maybe. You send about one proposal a month, so it'd save you an hour a month. Not today.

Be willing to talk them out of the impressive one.

---

## Step 4: pick one and go deep

If they've got a roster and no single place it lives, build the ops hub. It's the fastest visible win on this table and it makes everything after it easier.

If reporting is the real pain, build that instead, and be honest that it's the longer session.

If they're not sure, run `explore-operations` and let the audit decide. That's exactly what it's for, and its answer will be better than a guess.

---

## Step 5: adapt and build

- **Replace every example number.** The audit plugin's pricing table is placeholder figures in AUD. Anything that touches a live client must carry their real numbers.
- **Use their nouns.** Both Emil kits interview first for exactly this reason. Don't shortcut the interview to save ten minutes; it's where the fit comes from.
- **Rebrand properly.** The reporting engine and the proposal deck both put output in front of clients. Nothing from anyone else's brand should survive into a document their client reads.
- **Keep client data local.** These kits all run on their machine on purpose. Don't move client data anywhere it doesn't need to go.
- **Take the citation discipline** even where you take nothing else. Findings tied to quotes, ROI tied to the client's own numbers.
- **Rewrite paths and trigger phrases.**
- **Update `CLAUDE.md`** with whatever landed.

---

## Step 6: record what happened

Write a row into `ledger/`: what came from this table, what got built, what got skipped and why.

If you ran `explore-operations`, its output doc is a real artifact. Note where it lives, because it's written to be handed straight to a planning step later.

---

## If they're doing this at home

Same process. Load the context first. Have their client list or spreadsheet open before you start, since almost everything on this table gets built around real rows rather than invented ones.

---

*Table 06, Operations. Speakers: Adam Goodyer, Liam Ottley, Emil Faschang, Riccardo Belli Contarini.*
*From Liam Ottley's AI Makeover, youtube.com/@LiamOttley*
