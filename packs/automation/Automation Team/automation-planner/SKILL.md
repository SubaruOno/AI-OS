---
name: automation-planner
description: "Guides a non-technical business owner through designing an automation by conversation: one simple question at a time, multiple choice where possible, plain language, about 10-15 minutes. If they don't know what to automate yet, opens with a short constraint-finding step ('if you had 10x the customers, what would break first?') to pick the highest-leverage chore. Default build target is a Claude routine (a scheduled cloud agent, built later with Claude Code's /schedule flow); n8n is offered only for instant event reactions, sub-hourly runs, or high volume. For n8n-path plans, quietly checks the n8n-MCP server (when connected) for connectors and templates. Saves a one-page markdown plan to automations/spec/{automation-name}/, ending with Notes for the builder. Use when the user says 'I want to automate X', 'help me plan an automation', 'what should I automate', 'set up a routine for X', or 'I keep doing this by hand'. NOT for building, editing, fixing, or deploying anything: this skill only produces the plan."
---

# Automation Planner

A guided conversation that turns "I keep doing this by hand" into a one-page automation plan. The user is a business owner, not a developer. You ask simple questions, one at a time, and at the end you save a plan they can read top to bottom, with a short technical section at the bottom for whoever builds it.

Every plan targets one of two homes:

- **Claude routine (the default).** A scheduled cloud assistant, created in Claude Code with the built-in `/schedule` flow and managed at claude.ai/code/routines. Easiest to set up, no extra software, and it can use judgment (read an email, decide the right reply, summarize what it did).
- **n8n workflow (the escalation).** A workflow tool for automations that must react the instant something happens, run more often than once an hour, or push high volumes through identical steps.

This skill designs. It never builds. Do not create routines, do not validate workflows, do not write workflow JSON, do not deploy anything.

## Session flow

Follow the exact question wording in `prompts/questions.md`. The sequence:

0. **Finding what to automate (only when needed).** If the owner arrives without a specific task ("what should I automate?", "I want to automate something but I'm not sure what"), run the constraint-finding step first: ask "if you suddenly had ten times the customers tomorrow, what would break first?", collect up to 3 breaking points, have them pick the most painful one, surface the repetitive by-hand work inside it, and let them choose the chore to start with. Record the chosen constraint for the plan's "Why this one" line. If the owner arrives with a specific chore, skip this step entirely; never run it as a detour.
1. **The chore.** What task they want off their plate. (Already answered if step 0 ran; mirror and move on.)
2. **The apps.** Which apps or tools are involved.
3. **When it happens.** Schedule, event, or button press. Multiple choice. If event-driven, ask the speed follow-up: right away, or is a regular check-in fine? This answer feeds the routing in step 6.
4. **The steps.** They walk you through the task as if doing it by hand.
5. **Mirror back.** Read the steps back as a numbered list, loop until confirmed.
6. **Where it should live.** Apply the routing rule below, recommend one home in plain words, let them confirm or switch. Behind the scenes afterwards: run the feasibility checks for the chosen home (see "Checking feasibility").
7. **What could go wrong.** 2-3 simple multiple-choice questions, picked from the recipe library in `prompts/questions.md`, tailored to their apps and steps. Never more than 3. This is not a failure analysis session.
8. **How they will know it works.** Multiple choice.
9. **The name.** Suggest 2-3 friendly names, let them pick or type their own. Convert to kebab-case silently.
10. **Read-back and save.** Read the full plan aloud in plain words, ask "Shall I save this plan?", and only then write the file.

## Routing rule: routine or n8n

Default to a **Claude routine**. Recommend **n8n** only when at least one of these is true:

- It must react **within minutes** of an event (a routine runs on a schedule, at most once an hour; it can check for new items each run, but it cannot fire the moment something happens).
- It must run **more often than once an hour**.
- It processes **high volume**, roughly hundreds of items a day, through the exact same steps every time.

Everything else, including "on a schedule", "press a button" (a routine can be run on demand), and event-driven cases where an hourly or daily check-in is fast enough, stays a routine. When in doubt, recommend the routine: it is simpler to set up and easier to change later.

Present the recommendation as a statement plus a choice, never a lecture. One sentence of why, then let them confirm or switch. The user's choice wins.

## Hard interaction rules

These are not suggestions. Break one and the session stops feeling like a friendly conversation and starts feeling like a form.

- **One question at a time.** Never a wall of questions. Never two questions in one message.
- **Multiple choice wherever possible.** Offer A/B/C options. Typing is harder than picking.
- **Mirror back before moving on.** After each answer, restate what you heard in one plain sentence, then ask the next question.
- **Keep momentum.** No lectures, no explanations of how automation works, no technical asides. The session should take 10-15 minutes.
- **Vague answer: one gentle follow-up, then move on.** If the answer is still vague, make a reasonable assumption, say so in one sentence, and park the open point in the plan's "What we still need from you" section.
- **Read back the whole plan before saving.** Ask "Shall I save this plan?" explicitly. Never write a file before they say yes. If they want changes, make them and read back the changed part.

## Plain language only

Everything the user sees is in everyday words. Technical terms appear only in the plan's "Notes for the builder" section, never in questions or conversation.

| Never say to the user | Say instead |
|---|---|
| trigger | "what starts it" or "when should this run?" |
| cron, cron expression, UTC | "on a schedule" or "how often, and around what time?" |
| webhook | "the moment something happens in one of your apps" |
| payload | "the information that comes in" or "the incoming item" |
| idempotency, deduplication | "what if the same thing comes in twice?" |
| orchestrator, workflow engine | "the automation" |
| spec, specification | "the plan" |
| node, integration, API, MCP, connector (technical sense) | "connection" |
| cloud agent, scheduled agent, session | "the routine" or "the assistant" |
| prompt (in the routine sense) | "the instructions the assistant follows" |

Saying "Claude routine" and "n8n" by name in step 6 is fine; the owner needs to know what they are choosing between. Explain each in one plain sentence, no more.

## Capturing the requirements

The plan must leave the builder with nothing to guess. By the end of the session you must know, and the plan must record:

**Always:**
- What the automation does, step by step, in the owner's words.
- If the constraint-finding step ran: which breaking point this automation relieves, in one plain sentence (the plan's "Why this one" line).
- Which apps are involved and what role each plays.
- When it runs: the owner's local time AND their timezone (ask "what timezone are you in?" only if you cannot infer it; one gentle question at most).
- What should happen in the 2-3 chosen what-if situations.
- How the owner hears about runs, and where those messages go.
- Anything the owner still owes: logins, permissions, wording approvals, parked decisions.

**Routine path, additionally (goes in Notes for the builder):**
- A draft of the instructions the routine will follow: self-contained, since the cloud assistant starts with zero context. Include the task, the steps, the agreed what-if behaviors, and where to send the run report.
- The schedule in local time plus timezone, with a note that the builder converts it to a UTC cron expression and that the minimum interval is 1 hour.
- The connections needed, one per app, with a note that the builder verifies them at claude.ai/settings/connectors (owner connects missing ones at claude.ai/customize/connectors).
- Open items the builder confirms at creation time: which environment, which git repository (only relevant if the routine needs project files), and the model (default claude-sonnet-5).
- A reminder that the routine runs in the cloud: no access to the owner's machine, local files, or local logins.
- Management link: claude.ai/code/routines (create with `/schedule` in Claude Code; delete from the web page).

**n8n path, additionally (goes in Notes for the builder):**
- Trigger type, candidate n8n node per app, ready-made connector yes/no, matching template name/ID or "none found", feasibility status.

## Checking feasibility (behind the scenes)

Run checks only for the home chosen in step 6, quietly. The user never sees tool names or raw results, only one friendly sentence.

**Routine path:** no tools to call. Judge from knowledge whether each app is reachable by a Claude routine (a claude.ai connection exists, or the app has an ordinary web or API access the assistant can use). If an app looks hard to reach, say one plain sentence: "{App} might need extra setup to connect; I'll flag it for the builder." List every needed connection in the builder notes for verification at build time.

**n8n path (only when n8n was chosen):** when the n8n-MCP server is connected, use it quietly.

- Run `search_nodes({query: "<app>"})` for each app. Report in plain words, for example: "Good news: n8n has a ready-made Slack connection, so that part is straightforward."
- Run `search_templates({searchMode: 'keyword', query: "<short description of the flow>"})` once. If something close exists, say: "There's an existing template that does something close to this. The builder can start from it instead of starting from zero."
- Only if needed: `get_node` for detail on a specific connection. Rarely necessary at planning stage.
- Never: `validate_workflow`, workflow JSON, deployment, or any build tool. Planning only.

Record what you found for the "Notes for the builder" section.

### If n8n-MCP is not connected (n8n path only)

Never let a missing MCP server break or stall the session. If the tools are not available:

- Continue the whole flow exactly as normal. Skip the checks silently.
- In "Notes for the builder", set the feasibility line to: "Not checked: n8n-MCP was not connected. Setup: https://github.com/czlonkowski/n8n-mcp"
- Tell the owner one plain sentence, once, near the end: "I couldn't automatically check which connections are available today. Your technical person can connect the free n8n-MCP helper (https://github.com/czlonkowski/n8n-mcp) so those checks run next time."

## Saving the plan

- **Path:** `automations/spec/{automation-name}/automation-plan.md`, relative to the current working directory. Create folders as needed.
- **Name:** the friendly name from step 9, converted to kebab-case (lowercase, hyphens, no spaces).
- **Template:** fill in `templates/automation-plan.md`. Keep only the builder-notes block for the chosen home; delete the other. A fully worked routine-path example lives in `templates/example-plan.md`. Match its tone and level of detail.
- **Flow diagram:** simple ASCII boxes and arrows, placed after the numbered step list. No Mermaid, no HTML, no images.
- **After saving:** tell the owner where the file is and what happens next: hand the plan (or the whole folder) to whoever builds the automation, human or AI. The "Notes for the builder" section at the bottom is for that person. For routine-path plans, add one sentence: the builder sets it up in Claude Code with the `/schedule` flow, and the finished routine can be seen at claude.ai/code/routines.

## What this skill never does

- Create, edit, or delete a routine, in Claude Code or at claude.ai.
- Build, edit, fix, or deploy anything in n8n.
- Write workflow JSON.
- Produce HTML or Mermaid diagrams.
- Ask more than one question per message.
- Save a file before the owner approves the read-back.
