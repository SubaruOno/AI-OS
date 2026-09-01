# Start here, Table 03: Development

> Written 29 July 2026, Operator Day, Porto Montenegro.
>
> This file is addressed to Claude, not to the person who downloaded it. If you're the person: drop this whole folder into the workspace you built this morning, then tell Claude "read Table-03-Development/START-HERE.md and take me through it."

---

## What this folder is, and what it isn't

Two speakers handed over material, and they're solving different problems. Dave Ebbelaar's pack is about building actual software without a dev team. Mark Kashef's is about the architecture of an AI operating system: how the layers stack, which ones move fast, which ones you should almost never touch.

Neither is a product to install. Dave's is a starting repo shaped by his opinions about what a non-technical person should and shouldn't be allowed to do. Mark's is a baseline runtime plus a conceptual model, and the model is arguably worth more than the files.

**Treat this folder as a signal bank.** Read both, work out which problem the person in front of you actually has, and build from there.

---

## The rule

**Adapt, don't install.** Three honest outcomes:

1. **Take it as-is.** Dave's template in particular is designed to be cloned and used directly, so this is a real option here in a way it isn't on most tables.
2. **Take the idea, rebuild the piece.** Most likely for Mark's runtime, which is a baseline meant to be shaped.
3. **Take nothing, keep the note.** They don't need software built, or they're not ready. Write down what's here and when it'd matter.

---

## Step 1: load the business first

Read quietly before opening anything:

- `CLAUDE.md`
- `context/business.md`, `context/you.md`, `context/offer.md`
- `context/strategy.md`, `context/numbers.md`, `context/team.md`
- `context/tech-stack.md`

Three questions decide the session:

- **Is there a real piece of software they need that doesn't exist?** Not "an app would be cool". A specific recurring job done by hand every week. If they can't name one, Dave's half of this table is a solution looking for a problem, and you should say so rather than inventing a project.
- **Is anyone technical involved?** A cofounder, a contractor, a dev they already pay. That changes who this material should go to.
- **How mature is the workspace they built this morning?** Mark's layer model is most useful to someone who's just built the bottom layers and is wondering what comes next. That's most people in the room today.

If those files don't exist, ask five short questions and carry on.

---

## Step 2: survey what's actually in here

### Mark Kashef, the Agentic OS field guide

Read this first, whatever else you do. It's the lens for everything else from the day.

`Agentic OS Field Guide - Six Layers.pptx` lays out six layers, each tagged with how fast its context goes stale:

| Layer | What it owns | Half-life |
|---|---|---|
| 01 Identity | Purpose, audience, principles, boundaries | ~240 days |
| 02 Substrate | Evidence, decisions, logs, memory | compounds |
| 03 Rules + Hooks | Guardrails, permissions, approvals, preflight, postflight | ~60 days |
| 04 Skills | Repeatable workflows that still need judgment | ~24 days |
| 05 Agents | Durable roles composed from proven skills | ~12 days |
| 06 Tools + Data | APIs, MCPs, CLIs, webhooks, live data | hours to days |

The operating principle: **build inside out, maintain outside in.** Stability starts at the centre, maintenance starts at the surface. His stated v0 is `identity.md` plus evidence plus two skills plus one role plus live tools.

Use this as a diagnostic. Where is this person's workspace thin? Most people who finished Session I have a strong Identity layer and a Substrate that's just starting, and no Rules layer at all. Naming that is genuinely useful to them.

`Portable Agent Runtime Pack/` is the baseline: 6 rule files, 8 skills, 8 agent roles, preflight and postflight hooks, substrate templates, and thin adapters for Claude, Codex and Gemini. Read `START-HERE.md` and `identity.md` inside it first.

*Assumes:* nothing heavy. This is markdown, so it's the most portable pack in the whole room. That's also its risk. It's easy to copy in wholesale and end up with eight agent roles nobody needed. Resist that.

`Agentic OS - Asset Links & Handoff.docx` points at public repos and a live interactive version of the field guide. Worth opening with them, the layered visualisation explains the model faster than the slides do.

### Dave Ebbelaar, project-template

A git repository you clone. The core idea is a four-level ladder:

| Level | What you get |
|---|---|
| 0 | A written recipe the assistant follows. No website. |
| 1 | One site behind one shared password. Everyone sees the same thing. |
| 2 | One site where everyone signs in and sees only their own records. |
| 3 | A site plus a separate engine for documents, schedules, or big files. |

The interview routes you to a level, quotes the question that decided it, and records it if you override. Level 0 is treated as a real answer, not a consolation, and that's the most valuable opinion in the pack: a lot of what people call an app is a job done by hand every week, and a recipe handles it for nothing.

`AGENTS.md` is worth reading closely even if they never build anything. Five rules, a policy of looking up prices and package versions rather than quoting the repo, Windows means Git Bash, ask one question at a time and give two named options in business language rather than code language.

*Assumes:* Supabase for the database, a git clone into a new folder, and eventually a paid tier once they outgrow free. It ships with its `.git` directory intact, which is deliberate.

---

## Step 3: name the gap out loud

Put both halves against what you know. Show a short ranked view in their language.

Something like:

> Mark's layer model says something specific about where you are. You've got a strong Identity layer from this morning and your Substrate is a day old. You have no Rules layer at all, which is why nothing stops me doing something you'd rather I didn't. That's a thirty-minute fix and it's probably the highest-value thing on this table for you.
>
> Dave's template solves building software, and from `strategy.md` you do have one: the weekly job where you pull the numbers for your three retainer clients by hand. His decision tree would probably put that at level 0 or 1, not the full app you were imagining, which is good news.
>
> His runtime pack has eight agent roles. You have a team of two. I'd take the hooks and two of the rule files and leave the rest, because eight roles for a two-person business is theatre.

---

## Step 4: pick one and go deep

If they have a real software problem, run Dave's interview properly and let it route them. Don't skip to a level because it sounds impressive; the whole value of that pack is that it talks people down the ladder.

If they don't, use Mark's model as a diagnostic on their own workspace and build whichever layer is thinnest. That's a better use of the hour than starting a project they don't need.

---

## Step 5: adapt and build

- **Take rules and hooks selectively.** Mark's rule files encode his boundaries. Some are near-universal (never blend client context, scan outbound work for personal data). Others are his. Go through them with the person and keep what they'd actually want enforced.
- **Don't copy in eight agent roles.** A role should exist when several proven skills have become a job. For most people in this room that's zero or one role today. Say so.
- **Respect Dave's five rules if you use his template.** They exist because his tested recipes break when improved on. If you're borrowing the structure into a different stack, keep the discipline and drop the specifics.
- **Look up current prices before quoting any.** Both packs say this and both are right. Anything written down about a free tier was true when it was written.
- **Rewrite paths and trigger phrases.**
- **Update `CLAUDE.md`** so future sessions know what landed.

---

## Step 6: record what happened

Write a row into `ledger/`: what came from this table, what got built, what got skipped and why.

If you used the six-layer model as a diagnostic, write the diagnosis down. "Identity strong, substrate a day old, no rules layer, one skill, no agents, four tools connected" is the kind of note that's genuinely useful three months from now, and it gives them something to re-run against later.

---

## If they're doing this at home

Same process. Load the context first. Open Mark's live field guide link alongside the slides, since the interactive version lands the layer idea faster.

If they're going to build with Dave's template, make sure they're in a fresh folder for it rather than mixing it into their AIOS workspace. Two different jobs, two different folders.

---

*Table 03, Development. Speakers: Dave Ebbelaar, Joris, Mark Kashef. Packs from Dave and Mark.*
*From Liam Ottley's AI Makeover, youtube.com/@LiamOttley*
