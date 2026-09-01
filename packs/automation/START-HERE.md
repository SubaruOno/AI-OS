# Start here, Table 04: Automation

> Written 29 July 2026, Operator Day, Porto Montenegro.
>
> This file is addressed to Claude, not to the person who downloaded it. If you're the person: drop this whole folder into the workspace you built this morning, then tell Claude "read Table-04-Automation/START-HERE.md and take me through it."

---

## What this folder is, and what it isn't

The Automation table handed over a shared folder rather than one pack each, so what's in here came from several people and isn't individually labelled. Riccardo Vandra's automation planner is the substantial piece. There's a morning-routine template, a session-handoff skill that came off a Windows machine, and a short list of n8n resources.

None of it is a product. The planner encodes one person's view of how to decide what to automate, which is a strong view and a defensible one, but it's still a view. The morning routine is a template full of placeholders that means nothing until it's filled in with a real person's priorities.

**Treat this folder as a signal bank.** The thinking is the asset. Read it, work out which decision each piece is really making, and then build the version that fits the business you already know.

---

## The rule

**Adapt, don't install.** Three honest outcomes:

1. **Take it as-is.** The planner is genuinely designed to be installed and used directly, so this is real here.
2. **Take the idea, rebuild the piece.** The morning routine is a template by design. It doesn't become anything until you interview them and fill it.
3. **Take nothing, keep the note.** They're not at the stage where automation is the constraint. Say so and write down what's here.

One thing to be firm about: automating a broken process gives you a broken process running faster. If the thing they want to automate shouldn't exist, say that first.

---

## Step 1: load the business first

Read quietly before opening anything:

- `CLAUDE.md`
- `context/business.md`, `context/you.md`, `context/offer.md`
- `context/strategy.md`, `context/numbers.md`, `context/team.md`
- `context/tech-stack.md`

Four things to establish:

- **Where does their week actually go?** From `you.md` and `team.md`. The planner's opening question is about what breaks at ten times the volume, and you'll answer it better than they will if you've read their context properly.
- **What's connected already?** Whatever Composio linked this morning is the realistic surface for any automation today. Something that needs a tool they haven't connected is a plan, not a build.
- **How many people?** A solo operator and a team of six need different answers. Handoff and notification automations only matter once there's someone to hand off to.
- **Is anything already automated?** If they've got Zapier or Make running, that's both a constraint and a head start.

If those files don't exist, ask five short questions and carry on.

---

## Step 2: survey what's actually in here

### `automation-planner/` (Riccardo Vandra)

A skill that designs an automation by conversation. Ten to fifteen minutes, one plain-language question at a time, ending in a one-page plan a person can read with a short technical section at the bottom for whoever builds it.

The best thing in it is the opening move. If they don't know what to automate, it asks: **"If you suddenly had ten times the customers tomorrow, what would break first?"** Then it walks from the breaking points to the repetitive chore behind the most painful one. That reframing is the whole value of the pack, and it's worth using even if you build nothing else from this table.

The routing decision is also good. It targets a scheduled Claude routine by default, since that needs nothing installed and nothing hosted, and only escalates to n8n when the job genuinely needs it: reacting the instant an event fires, running more often than hourly, or pushing high volume through identical steps. Read `docs/BUILD-DOC.md` and `prompts/questions.md` to understand how it decides.

*Assumes:* they'll run it from a Claude Code project folder, and optionally that n8n-MCP is connected for connector checks. Without n8n-MCP everything still works, the n8n-path plans just mark connector checks as unverified.

### `morning-routine-prompt.md`

A template for a scheduled daily brief that pulls from email, chat, project tool and calendar, then produces a short prioritised list. It opens by instructing the assistant to interview the person and fill every placeholder before running anything, which is the right instinct.

It's placeholders all the way down: their name, role, timezone, top outcomes, north-star metrics, the work that always outranks everything else, work that feels urgent but almost never is, non-negotiable blocks, realistic daily capacity, VIP senders, priority channels, noise to ignore. That list is the actual content. Run the interview properly and it becomes something good. Skip the interview and it produces generic mush.

*Assumes:* several connected tools and a scheduled run. Check what's actually linked before promising a full version.

### `session-handoff-SKILL.md` (Nate Herk)

Produces a structured end-of-session summary so you can clear context and start fresh without losing continuity. Written for a future instance of the assistant rather than for a human stakeholder, which is the right audience and an easy thing to get wrong. It has a good rule about not auditing the filesystem: this is synthesis of what happened in the session, not a rediscovery exercise.

*One thing to fix during adaptation:* it hardcodes `C:\Users\Nate\.claude\plans\` and a matching memory path. Those are Nate's own machine. Rewrite them for this person's setup, or the skill will send Claude looking for folders that don't exist. This is a two-minute fix, but it will silently degrade the skill if you miss it.

Also worth noting: the workspace they built this morning already has `/handoff`, which does a similar job. Compare the two rather than stacking both. Take whichever ideas are better and keep one.

### `Important Links.docx`

Four repos: `czlonkowski/n8n-mcp`, `zie619/n8n-workflows`, `czlonkowski/n8n-skills`, and `riccardovandra/automation-planner`. Only relevant if they end up on the n8n path.

---

## Step 3: name the gap out loud

Show them a short ranked view in their own language.

Something like:

> The planner is the piece I'd run first, and I can answer its opening question for you already. From `team.md` and this morning's interview, the thing that breaks at ten times the volume is you personally doing every onboarding call and then typing the notes into three places afterwards.
>
> The morning brief is real for you but not today. It reads from four tools and you've got two connected. We can build a two-tool version now that gets better as you connect more, or park it.
>
> The handoff skill overlaps with the `/handoff` you already have. I'd take one idea from Nate's version, the rule about not re-auditing the filesystem, fold it into yours, and drop the rest.

---

## Step 4: pick one and go deep

Run the planner properly on their single most painful repeated job. One plan, built and working, beats three plans on paper.

If the plan comes back saying "this should be a Claude routine", build the routine today and let them see it fire. If it comes back saying n8n, be honest that it's a longer road and finish the plan so they've got something to hand a builder.

---

## Step 5: adapt and build

- **Fix Nate's hardcoded Windows paths** if you use that skill at all.
- **Do the morning-routine interview properly, or don't ship it.** A template with placeholders left in is worse than nothing because it looks done.
- **Only automate what's connected.** If the plan depends on a tool they haven't linked, either link it now or write the plan and stop honestly.
- **Check the process is worth keeping** before you automate it. Sometimes the right answer is to delete the step.
- **Rewrite trigger phrases** to match how they talk.
- **Start smaller than feels right.** The first automation should be one they can watch run end to end today.
- **Update `CLAUDE.md`** with anything that landed.

---

## Step 6: record what happened

Write a row into `ledger/`: what came from this table, what got built, what got skipped and why.

If the planner produced a plan you didn't build, that plan is an artifact worth keeping. Save it and note where it lives, so a future session can pick it up cold.

---

## If they're doing this at home

Same process. Load the context first. Since nobody's in the room to ask, take the planner's interview slowly and let them think out loud; the quality of the plan is entirely downstream of that conversation.

---

*Table 04, Automation. Speakers: Bo Sar, Riccardo Vandra, Nate Herk, Tyler Germain. The pack came in as one shared folder, so individual attribution is partial.*
*From Liam Ottley's AI Makeover, youtube.com/@LiamOttley*
