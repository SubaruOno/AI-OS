# {Friendly Name}

**What this automation does:** {One plain sentence describing the outcome, e.g. "Chases unpaid invoices by email so you don't have to."}

**Why this one:** {Only when the constraint-finding step ran: one plain sentence tying the automation to the breaking point it relieves, e.g. "If customers grew tenfold, invoicing is what would break first; this takes its biggest chore off your plate." Delete this line otherwise.}

**Where it lives:** {One plain sentence. E.g. "A Claude routine: an assistant that runs on a schedule and follows the steps below." or "An n8n workflow: a workflow tool that reacts the moment something happens."}

## When it runs

{Plain words, including the owner's timezone. E.g. "Every weekday morning around 9:00, Rome time." or "It checks for new form entries once an hour." or "Only when you press the button."}

## The apps it connects

- **{App 1}**: {one line on its role, e.g. "where the invoices live"}
- **{App 2}**: {one line on its role}
- **{App 3}**: {one line on its role}

## Step by step

1. {Plain-language step}
2. {Plain-language step}
3. {Plain-language step}
4. {Plain-language step}

```
{Simple ASCII flow diagram: boxes and arrows, one box per step or grouped step.
Keep it narrow. Example shape:

[When it starts]
       |
       v
+-----------------+
| First thing it  |
| does            |
+-----------------+
       |
       v
+-----------------+     nothing found
| Next thing      |------> done for today
+-----------------+
       |
       v
[Final result]
}
```

## When something goes wrong

- **{Situation, e.g. "An invoice has no email address"}:** {agreed behavior in plain words, e.g. "it gets sent to you to handle by hand"}
- **{Situation}:** {agreed behavior}
- **{Situation}:** {agreed behavior}

## How you'll know it's working

{Plain words. E.g. "You get a short Slack message each time it runs, listing what it did." or "You only hear from it when something goes wrong."}

## What we still need from you

- {Access or connection needed, one bullet per named app, e.g. "Connect Gmail at claude.ai/customize/connectors (takes a minute, the builder can walk you through it)"}
- {Any decision parked during the conversation, phrased as a question}

---

## Notes for the builder

*This section is technical. It's for the person or AI who will build the automation. Keep only the block below that matches the chosen home; delete the other.*

{ROUTINE PATH: keep this block when the plan targets a Claude routine}

**Target:** Claude routine (scheduled cloud agent). Create with the `/schedule` flow in Claude Code; manage or delete at https://claude.ai/code/routines. The routine runs in the cloud with no access to the owner's machine, local files, or local logins.

**Schedule:** {owner's local time and timezone, e.g. "weekdays 09:00 Europe/Rome"}. Convert to a UTC cron expression at creation time. Minimum interval is 1 hour. {If run-on-demand: "No schedule; the owner runs it on demand from claude.ai/code/routines."}

**Connections needed:** {one line per app, e.g. "Gmail, Slack, Google Drive"}. Verify each is connected at claude.ai/settings/connectors before creating the routine; the owner connects missing ones at claude.ai/customize/connectors. {Flag any app with no obvious connection and suggest how the routine might reach it instead, e.g. via its API.}

**To confirm at creation time:** environment; git repository ({"any default repo works, the routine doesn't need project files" or name the repo whose files it needs}); model (default claude-sonnet-5).

**Draft instructions for the routine** (self-contained; the cloud assistant starts with zero context; adjust as needed):

```
{Write the full instruction text here. Include:
- what the routine is and what outcome it is responsible for
- the steps, in order, from the "Step by step" section
- the agreed what-if behaviors from "When something goes wrong"
- exactly where and how to report each run, from "How you'll know it's working"
- what NOT to do (e.g. never email anyone other than the listed recipients)}
```

**Plan date:** {date}

**Change log:**

- {date}: first version of this plan.

{N8N PATH: keep this block when the plan targets n8n}

**Target:** n8n workflow. Reason for escalating past a Claude routine: {instant event reaction / sub-hourly schedule / high volume}.

**Trigger:** {n8n trigger type, e.g. "Schedule Trigger, weekdays 09:00 owner's local timezone" or "Webhook / app-specific trigger node on {event}"}

**Apps and candidate nodes:**

| App | Candidate n8n node | Ready-made connector |
|---|---|---|
| {App 1} | {node name from search_nodes} | {yes/no} |
| {App 2} | {node name} | {yes/no} |
| {App 3} | {node name} | {yes/no} |

**Matching templates:** {template name and ID from search_templates, or "None found."}

**Feasibility:** {"Checked with n8n-MCP on {date}." or "Not checked: n8n-MCP was not connected. Setup: https://github.com/czlonkowski/n8n-mcp"}

**Plan date:** {date}

**Change log:**

- {date}: first version of this plan.
