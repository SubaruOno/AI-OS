# automation-planner

A Claude Code skill that helps a business owner design an automation by conversation. No technical knowledge needed: Claude asks one simple question at a time, in plain language, for about 10-15 minutes. At the end you get a one-page automation plan you can actually read, with a short technical section at the bottom for whoever builds it, a person or an AI.

Not sure what to automate? The skill starts with one question: **"If you suddenly had ten times the customers tomorrow, what would break first?"** It walks you from those breaking points to the repetitive chore behind the most painful one, so the first automation you build is the one your business actually needs. If you already know your chore, it skips straight to designing.

By default the plan targets a **Claude routine**: a scheduled cloud assistant, created with Claude Code's built-in `/schedule` flow and managed at [claude.ai/code/routines](https://claude.ai/code/routines). Nothing to install, nothing to host. When the automation needs more than a routine can give (reacting the instant an event fires, running more often than hourly, or pushing high volume through identical steps), the skill recommends **n8n** instead and plans for that.

If you're a consultant, install this for your clients and let them draft their own automation ideas; the plans land in a folder ready for you to build from.

## Install

Clone it straight into your Claude Code skills folder:

```bash
git clone https://github.com/riccardovandra/automation-planner ~/.claude/skills/automation-planner
```

Or copy the folder there by hand. That's it.

## Optional: connect n8n-MCP (n8n-path plans only)

Claude-routine plans need no extra setup. For plans that escalate to n8n, the free [n8n-MCP](https://github.com/czlonkowski/n8n-mcp) server lets the skill quietly check whether each app has a ready-made n8n connector and whether an existing workflow template is close to what you want. One command:

```bash
claude mcp add n8n-mcp -e MCP_MODE=stdio -e LOG_LEVEL=error -e DISABLE_CONSOLE_OUTPUT=true -- npx n8n-mcp
```

A fuller variant with `N8N_API_URL` and `N8N_API_KEY` exists for people who also build and deploy from Claude. You don't need it for planning.

Without n8n-MCP everything still works; n8n-path plans just mark the connector checks as "not checked" so your builder knows to verify them.

## How to use

In Claude Code, type:

```
/automation-planner
```

Or just say what's on your mind: "I want to automate chasing unpaid invoices." Claude takes it from there, one question at a time.

## What you get

A markdown file at `automations/spec/{automation-name}/automation-plan.md` in your current project folder. It covers:

- what the automation does, why it was picked (when the what-would-break-first step ran), when it runs, and where it lives (Claude routine or n8n)
- the apps involved and the steps, in plain words, with a simple flow diagram
- what should happen when something goes wrong
- how you'll know it's working
- what's still needed from you (connections, decisions)
- Notes for the builder: for routine plans, the schedule, needed connections, and a ready-to-use draft of the routine's instructions; for n8n plans, trigger, candidate nodes, and matching templates

Hand that file to whoever builds your automations and they have everything they need to start. Routine plans get built with `/schedule` in Claude Code; the live routine shows up at [claude.ai/code/routines](https://claude.ai/code/routines).

## Credit

n8n connector and template checks are powered by [n8n-MCP](https://github.com/czlonkowski/n8n-mcp) by Romuald Czlonkowski.

## License

MIT. See [LICENSE](LICENSE).
