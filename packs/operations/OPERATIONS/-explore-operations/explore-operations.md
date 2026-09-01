# Explore Operations

> Find the biggest bottleneck in your operations and shape it into a systemization project - ready to hand to /create-plan.

## Variables

focus: $ARGUMENTS (optional - describe the operational area you want to improve, e.g. "I do client reporting manually for 12 agency clients and want to improve this". Leave empty to start with a task audit that finds your bottleneck for you.)

---

## Instructions

You are running an **interactive operations exploration**. Your job is to find where the user's time actually goes, identify the 1-2 highest-leverage things to systemize, understand exactly how those things work today, and shape them into a clear systemization concept. Do NOT run through all stages autonomously - present findings at each stage, ask questions, and wait for responses before proceeding.

**Two entry paths:**
- **No arguments** → run the full flow starting with the TASK AUDIT (Stage 1). The audit finds the bottleneck.
- **Focus provided** → skip Stages 1-2. Confirm your understanding of the focus area, ask the quick time-reality questions from Stage 2b, then continue from Stage 3. If during the conversation the stated focus turns out to be small (under ~2 hrs/week) while something clearly bigger surfaces, say so and offer the full audit.

**Output:** An operations exploration doc saved to `plans/explore-YYYY-MM-DD-{descriptive-name}.md`

**Downstream:** The doc is written to be handed directly to `/create-plan` for implementation planning.

---

## Stage 0: CONTEXT - Know the Business (no gate)

Before asking anything, quietly gather what's already known:

1. Read whatever workspace context exists (skip silently if a file is missing or empty):
   - `CLAUDE.md`
   - `context/group/overview.md`, `context/group/strategy.md`, `context/group/team.md`
   - `gtd/dashboard.md` and `gtd/areas.md`
2. Note: what the business does, the offer, team size, current priorities.
3. **Never ask a question the context already answers.** Use what you learn to make every later question specific to their business ("your client onboarding" not "a hypothetical process").
4. If no context exists at all, open Stage 1 (or 2b on the focused path) with 2-3 business basics first: what do you sell, who buys it, who's on the team.

---

## Stage 1: TASK AUDIT - Where the Time Goes

**Step 1 - Pull from connected tools (quietly):**

1. Check whether any calendar or task-management tools are connected in this session (MCP tools for Google Calendar, Notion, ClickUp, Asana, Linear, Todoist, or similar).
2. If a calendar is available: pull the last 14 days of events. Bucket them by category, estimate meeting hours per category, and note recurring meetings.
3. If a task manager is available: pull active tasks/projects and note recurring or overdue clusters.
4. If nothing is connected, or a tool errors or needs re-auth: continue seamlessly with questions. Mention it in at most one line. **Never turn the session into an integration setup exercise.**

**Step 2 - Guided audit questions:**

Present anything the tools revealed ("your calendar shows ~6 hrs/week of client calls..."), then run the audit as four passes. Work through them across several messages - 2-4 questions per message, never more - and skip anything the tools or context already answered. Use these categories as the sorting frame - adapt them to the business, add or drop categories as needed:

- **Sales** - calls, DMs, follow-ups, proposals, closing
- **Marketing & Content** - creating, posting, ads, funnels
- **Delivery & Fulfilment** - the actual client/customer work
- **Customer Support & Success** - questions, check-ins, retention
- **Admin & Finance** - invoicing, bookkeeping, scheduling, email
- **Team & Management** - hiring, meetings, reviews, coordination
- **Product & Development** - building or improving what you sell

**Pass 1 - Reconstruct a real week (don't ask for estimates yet).** People misestimate abstract categories but recall concrete days well:

1. Walk me through your last full workday, start to finish - what did you actually do, roughly hour by hour?
2. What do you do every single day no matter what? What recurs weekly (e.g. every Monday)? What recurs monthly?
3. How many hours do you work in a normal week, all in? (Keep this as the control total for Pass 2.)
4. Which apps or tools are open all day? (Tools reveal tasks people forget to mention.)

**Pass 2 - Put numbers on it.** Translate what surfaced into hours per category:

1. Roughly how many hours per week do YOU personally spend in each category? Estimates are fine - push gently for numbers, not "a lot". Convert monthly/quarterly tasks to their weekly equivalent (a 4-hour monthly report = ~1 hr/week).
2. For client/order businesses, do the per-unit math: how much time does ONE client or order take per week, times how many do you have? Hours hide in that multiplication.
3. Communication is its own line: how much time per day in email, Slack/WhatsApp, DMs, and meetings that aren't sales or delivery calls?
4. Cross-check: do the category numbers add up to the control total from Pass 1? If they work 60-hour weeks but categories sum to 35, chase the gap - it's usually firefighting, context switching, and comms, and that gap is often the finding.

**Pass 3 - Drill into the biggest blocks.** For the 2-3 biggest categories:

1. Which specific recurring tasks make up those hours? For each: what exactly is it, how often, how long per run, who does it (you or team), and which tools does it touch?
2. If there's a team: which tasks eat significant TEAM hours? Big leverage often hides there, not in the owner's calendar.
3. How much of the week arrives unplanned - interruptions, urgent requests, firefighting? What kind, and from where?

**Pass 4 - The tells.** These expose what the numbers miss:

1. Which task do you dread or keep procrastinating on?
2. What did you do this week that you also did last week and the week before, near-identically?
3. If you disappeared for two weeks, what would break first?
4. What does your team wait on you for, or constantly ask you about?
5. Is there work you'd never hand off because explaining it feels harder than doing it? (That instinct usually marks a missing SOP, not an undelegable task.)
6. What do you keep NOT getting to because the week gets eaten?

**Step 3 - Build the Time Map:**

Compile everything into a table:

| Task | Category | Hrs/week | Done by | Frequency | Repetitive? | Rule-based? |
|------|----------|----------|---------|-----------|-------------|-------------|

Include lines for communication overhead and unplanned/firefighting time - they're rarely a single "task" but they're real hours. If the table total still falls short of the control total, say so and show the gap.

**STOP - present the Time Map and ask the user to correct anything that looks wrong before you score it.**

---

## Stage 2: LEVERAGE - Find the Bottleneck

**Actions:**

1. Score each recurring task (or cluster of related tasks) on four dimensions:
   - **Time** - hours per week it consumes
   - **Repetition** - is it the same shape every time?
   - **Rules** - could the way it's done be written down? (low judgment = high score)
   - **Owner-lock** - does it need this specific person, or just get done?
2. Rank by expected payoff: hours reclaimed × ease of systemization. High-time but genuinely low-systemizability work (e.g. sales calls only the founder can take) gets flagged honestly as "not the target" - never force it into the list.
3. Present a ranked shortlist (top 3-5) with one line each on WHY it's leverage, and recommend the top 1-2.

**STOP - the user picks the 1-2 leverage points to explore. Everything downstream runs on their picks, not yours.**

### Stage 2b: Quick Time Check (focused path only)

If the user provided a focus and skipped the audit, ask just enough to ground the exploration in numbers: hours per week this takes, who does it, how often it recurs, and what it blocks. Then continue to Stage 3.

---

## Stage 3: PROCESS DEEP-DIVE - How It Works Today

For each chosen leverage point:

1. **Frame it first** (one small batch): what does "solved" look like here - the outcome, not the mechanism? And is anything explicitly out of scope (a step that must stay personal, no new hires, a tool they won't add)?
2. **Ask: do you have an SOP or documented process for this?**
   - **Yes** → ask them to paste it, point to the file, or share the link. Read it fully. Note where reality differs from the doc and where steps are missing.
   - **No** → capture the process through a guided walkthrough. Ask in small batches:
     - What triggers this task? (a date, a client action, a message, an amount of backlog)
     - Walk me through the steps, in order, as you actually do them.
     - What tools/apps do you touch at each step?
     - Where do you make judgment calls, and what's the rule behind each one?
     - What does the finished output look like? Who receives it?
     - What are the exceptions - the cases where the normal process breaks?
     - How long does one full run take?
3. Write up a clean **process map** (trigger → steps → tools → decisions → output → exceptions → time per run) and present it back. This is a byproduct worth keeping: if they had no SOP, this IS their first SOP draft.

**STOP - confirm the process map is accurate before designing anything on top of it.**

---

## Stage 4: RESEARCH - Explore the Landscape

**Actions:**

1. Research what already exists before designing anything new:
   - **Their stack** - which tools from the process map (or elsewhere in the business) can already do more than they're being used for
   - **Their workspace** - existing commands, scripts, or automations that could be extended
   - **What's available** - Claude Code capabilities (commands, skills, scheduled automations), native features of their existing SaaS, off-the-shelf tools
2. Present findings:
   - What already exists that's relevant
   - What options are available (with pros/cons)
   - What constraints or dependencies you've found (access, data, budget, technical comfort)
   - Rough complexity estimate (Small / Medium / Large)

**STOP and wait for input on direction before proceeding.**

---

## Stage 5: SHAPE - Design the Systemized Version

**Actions:**

1. For each step in the process map, classify what should happen to it:
   - **Automate** - AI or scripts can do it (drafting, data pulls, formatting, classification, reporting)
   - **Delegate** - a team member can do it with the SOP
   - **Eliminate/Simplify** - the step exists out of habit, not need
   - **Keep human** - judgment or relationships that genuinely need the owner
2. Present 2-3 design options with tradeoffs (e.g. full automation vs human-in-the-loop vs SOP + delegation). Since the downstream is `/create-plan` and `/implement` in this workspace, be concrete about what Claude Code can build here - but recommend delegation or elimination when that's honestly the better answer.
3. For the recommended option, define:
   - **What it does** - clear description of the future state
   - **How it works** - the new flow, including where the human stays in the loop
   - **What it replaces** - which current steps disappear, with estimated hours reclaimed per week
   - **How it connects** - where it plugs into their existing tools, systems, and team workflow
4. Flag anything risky, uncertain, or dependent on tools/data they don't have yet.

**STOP - wait for confirmation on the direction before scoping.**

---

## Stage 6: SCOPE - Break It Down

**Actions:**

1. Define the **minimum viable version** - the smallest thing that reclaims real hours, buildable first
2. Define the **full vision** - where this goes once the MVP works
3. Break into components - for each, note what it involves, dependencies, and rough effort (Small / Medium / Large). Recommend phasing if the build is large.
4. **Classify the delivery type:** Claude Code command / script / scheduled automation / SOP + delegation / a combination. Suggest a name and where the files or documents will live.
5. If two leverage points were chosen, recommend which to build first and why

**STOP - present the breakdown for review.**

---

## Stage 7: OUTPUT - Write the Exploration Doc

Save to `plans/explore-YYYY-MM-DD-{descriptive-name}.md`. If two leverage points were chosen, write ONE doc covering both, with a clear recommendation on which to plan first.

```markdown
# Operations Exploration: {Leverage Point Name}

**Created:** YYYY-MM-DD
**Status:** Explored
**Origin:** {Task audit | Direct focus: "original input"}

---

## The Business
{2-3 sentences: what it does, team size, stage - from context + answers}

## Time Audit Summary
{The Time Map table + one paragraph on where the hours actually go. Omit this section on the focused path - include the Stage 2b numbers instead.}

## The Bottleneck
{The chosen leverage point(s), with numbers: hrs/week, who does it, why this is the highest-leverage target}

## Vision
{2-3 sentences: what the systemized version makes possible and why it matters for this business}

## Current Process
{The confirmed process map: trigger, steps, tools, judgment calls + rules, output, exceptions, time per run. Note whether an SOP existed or this walkthrough created the first one.}

## Proposed System

### What It Does
### How It Works
{Include the automate / delegate / eliminate / keep-human split per step}
### Human-in-the-Loop Points
### What It Replaces
{Estimated hours reclaimed per week}

## Scope

### Start Here (MVP)
### Full Vision
### Components
### Out of Scope

## Technical Considerations
{Tools, data, and access needed; risks; unknowns}

## Delivery Type
**Classification:** {Claude Code command / script / scheduled automation / SOP + delegation / combination}
**Location:** {Where the files or documents will live}

## Connections
{How this plugs into their existing tools, systems, and team workflow}

## Next Steps
Run `/create-plan` and reference this doc to turn the MVP into an implementation plan.

## Discovery Notes
{Key decisions and corrections made during the exploration}
```

After saving, report the file path, the headline (which bottleneck, how many hours/week it should reclaim), and recommend running `/create-plan` next.

---

## Critical Rules

- **Interactive** - present findings, wait for responses at every STOP. Never complete all stages autonomously.
- **Small question batches** - 2-4 questions per message, maximum. This is a conversation, not a form.
- **Numbers over vibes** - push for hours, frequencies, and durations. Estimates are fine; "a lot" is not.
- **Graceful with tools** - use connected calendar/task tools if present, continue seamlessly if not. Never ask the user to set up an integration mid-session.
- **Context-aware** - never ask what the workspace context already answers.
- **Honest leverage** - if the biggest time sink isn't systemizable, say so and target the best one that is. If the user's stated focus isn't the real bottleneck, tell them.
- **Honest about complexity** - flag hard problems clearly. Never sell a five-integration build as a quick win.
- **Not a plan** - this doc captures where the time goes, how the process works, and what the system should be. Implementation detail belongs in `/create-plan`.
