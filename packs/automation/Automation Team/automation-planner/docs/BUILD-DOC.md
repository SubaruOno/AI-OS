# automation-planner: how it works

This document describes the skill as built: the session flow, the files, and the reasoning behind the main design decisions.

## What the skill does

automation-planner turns a business owner's "I keep doing this by hand" into a saved, buildable automation plan through a short guided conversation. The owner never sees a technical term. The output is a one-page markdown plan in plain language, ending with a "Notes for the builder" section that carries the technical detail for whoever builds it.

Every plan targets one of two homes. The default is a **Claude routine**: a scheduled cloud agent created with Claude Code's built-in `/schedule` flow and managed at claude.ai/code/routines. The escalation is an **n8n workflow**, recommended only when the automation must react within minutes of an event, run more often than hourly, or push high volume through identical steps.

The skill designs and stops there. It never creates routines, validates workflows, writes workflow JSON, or deploys anything.

## Session flow

Ten steps, each a single question or read-back, in fixed order, preceded by an optional discovery step:

0. Finding what to automate, run only when the owner arrives without a specific task. One opening question ("if you suddenly had ten times the customers tomorrow, what would break first?"), up to 3 breaking points collected, the owner picks the most painful one, names the repetitive by-hand work inside it, and chooses the chore to automate first. The chosen breaking point becomes the plan's "Why this one" line. Capped at six questions; skipped entirely when the owner already knows their chore.
1. The chore: what task to take off the owner's plate.
2. The apps involved.
3. When it should happen: schedule, event, or button, as a multiple choice. Event-driven answers get a speed follow-up (right away vs a regular check), which feeds the routing.
4. The steps, told as if done by hand.
5. Mirror-back of the steps as a numbered list, looped until confirmed.
6. Where it should live: the routing step. The skill recommends a routine by default, or n8n when a complexity signal is present, in one plain sentence each, and the owner confirms or switches. Feasibility checks for the chosen home run behind the scenes here.
7. What could go wrong: 2-3 multiple-choice questions picked from a four-recipe library (missing info, duplicates, app unreachable, nothing to do), tailored to the named apps and steps.
8. How the owner wants to hear from it: per-run message, errors only, or summary.
9. The name: 2-3 friendly suggestions, silently converted to kebab-case.
10. Full read-back and an explicit "Shall I save this plan?" before any file is written.

The plan lands at `automations/spec/{automation-name}/automation-plan.md`, relative to the current working directory.

## The routing rule

Claude routine unless at least one n8n signal is present: reaction within minutes of an event, a schedule tighter than hourly, or high volume (roughly hundreds of items a day) through identical steps. Routines run on a cron schedule with a 1-hour minimum interval, so event-driven cases where an hourly or daily check is fast enough stay routines that look for new items each run. "Press a button" stays a routine too: routines can be run on demand. When in doubt, the routine wins; it is simpler to set up and easier to change. The owner's choice always overrides the recommendation.

## Requirements the plan must capture

Always: the steps in the owner's words, the apps and their roles, the schedule in the owner's local time plus timezone, the agreed what-if behaviors, the reporting channel, anything the owner still owes, and, when the constraint-finding step ran, the breaking point this automation relieves.

Routine path, in the builder notes: a self-contained draft of the routine's instructions (the cloud agent starts with zero context, so the draft folds in the steps, the what-if behaviors, and the reporting instructions), the schedule with a UTC-conversion note and the 1-hour minimum, the needed claude.ai connections with verification links, the items confirmed at creation time (environment, git repository, model, default claude-sonnet-5), a no-local-access reminder, and the management link.

n8n path, in the builder notes: trigger type, candidate node per app, connector availability, matching template or "none found", and feasibility status.

## Files

- `SKILL.md`: entry point. Session flow, routing rule, hard interaction rules, jargon-translation table, requirements checklist, per-home feasibility checks and degradation rule, output path, save gate.
- `prompts/questions.md`: the exact wording of every question, the multiple-choice options, the routing scripts for both recommendation directions, mirror-back patterns, the what-if recipe library, and the read-back script.
- `templates/automation-plan.md`: the output template with placeholders, plain-language sections first, then two builder-notes blocks (routine and n8n); the builder keeps only the block for the chosen home.
- `templates/example-plan.md`: one fully worked routine-path example (invoice chasing with Google Sheets, Gmail, Slack) that anchors output quality, including a complete draft of the routine's instructions.
- `README.md`: install and usage for the public repo, including the optional n8n-MCP setup for n8n-path plans.
- `docs/BUILD-DOC.md`: this document.

## Design decisions

**Constraint-finding before chore-designing, but only on demand.** Owners who ask "what should I automate?" don't need a planning session, they need a selection method. The 10x-customers question surfaces the business's real constraints in the owner's own words, and anchoring the chosen chore to the most painful breaking point means the first automation built is the highest-leverage one, not just the most recently annoying one. The step is capped at six questions, never runs when a chore was already named, and never name-drops constraint theory: the owner experiences it as a few quick questions, not a framework.

**Routine-first, n8n on signal.** Most small-business automations are "check something on a schedule and act": squarely what a routine does with zero infrastructure. Making the routine the default removes the n8n installation and hosting hurdle from the common case entirely. n8n stays in the picture for the cases a scheduled agent genuinely cannot serve, and the routing rule names those cases precisely so the recommendation is mechanical, not a vibe.

**Routing happens after the steps are mirrored back, not earlier.** The recommendation depends on trigger speed, frequency, and volume, and those only become reliable once the owner has walked through the task. Placing the choice at step 6 means it is made once, with full information, and feasibility checks run only for the home actually chosen.

**One question at a time.** The target user abandons forms and walls of questions. A single question per message keeps the exchange conversational, keeps answers short and honest, and lets each answer shape the next question. Multiple choice is offered wherever possible because picking A, B, or C is easier than composing an answer.

**Plain language everywhere the owner looks.** Terms like trigger, webhook, cron, and idempotency each have a fixed plain-language substitute in SKILL.md. The concepts still get covered; only the vocabulary changes. "Claude routine" and "n8n" are the two deliberate exceptions, named once in step 6 with a one-sentence explanation each, because the owner is choosing between them.

**A small what-if library instead of a failure analysis.** A full failure-mode review is the right tool for an engineer and the wrong tool for a 15-minute owner conversation. Four recipes cover the failure classes that matter in practice, and the skill asks only the 2-3 that fit the case, each as an A/B/C choice about business behavior, not mechanisms.

**The routine plan ships a draft of the routine's instructions.** A routine is only as good as its prompt, and the cloud agent starts with zero context. Writing the self-contained instruction draft at planning time, while the steps, edge behaviors, and reporting channel are fresh and owner-approved, is the routine-path equivalent of the old "candidate nodes and templates" table: it turns the plan from a description into something the builder can nearly paste into `/schedule`.

**The plan carries a builder section.** A plan only the owner can read is not buildable; a spec only a builder can read never gets approved. Ordering the document plain-language-first and technical-last serves both readers with one file.

**n8n-MCP is quiet, optional, and only consulted on the n8n path.** Feasibility checks surface as one friendly sentence, because raw tool output would break the plain-language contract. When the server is not connected, the session runs to completion anyway and the plan's feasibility line says "not checked" with a setup link. Routine-path plans never touch it.

**ASCII flow diagram, after the step list.** The numbered list is the source of truth; the diagram is a visual echo. ASCII keeps the plan a single portable markdown file with no rendering dependencies.

**One worked example in the repo.** `templates/example-plan.md` fixes the tone, length, and level of detail of the output, now including what a good routine instruction draft looks like. Template placeholders alone drift toward either too terse or too technical.

**Fully self-contained.** No file in the skill references anything outside the skill folder. Clone the repo into `~/.claude/skills/` on any machine and it works identically.
