---
name: composio
description: Reach the business's own tools. Gmail, Slack, Notion, HubSpot, Stripe, Google Sheets, Calendar, Salesforce, Shopify and around a thousand more, through one CLI. Use whenever the user asks to do something in a platform they run their business on. Triggers on - send an email, check my inbox, what's in my calendar, look at my CRM, my deals, my customers, pull from my spreadsheet, post to Slack, add to Notion, my Stripe payments, my bookings, my orders, update that record, message them, schedule it, "can you check my [tool]", "in my [tool]", any named SaaS product. Also the first thing to try before building a custom integration.
---

# Composio

One account, one CLI, around a thousand tools. Instead of building an integration per platform, search for the action, run it, and connect the account the first time it's needed.

## The workflow: search, execute, link

```
composio search "<what the user wants done>"   # find the tool
composio execute <SLUG> -d '<params>'          # run it
composio link <toolkit>                        # only if execute says auth is missing
```

**Bias to action.** Search first, then just try executing. Input validation and auth checks are built in and the errors say what's wrong. Don't ask the user which apps to connect before you've tried, and don't preemptively link things.

**Don't assume it isn't covered.** The catalogue is large and oddly specific. Search before concluding a tool isn't supported.

### The one flow that matters

1. `composio search "create a calendar event"` returns a slug like `GOOGLECALENDAR_CREATE_EVENT`.
2. `composio execute GOOGLECALENDAR_CREATE_EVENT -d '{...}'`.
3. If that comes back with an auth error, run `composio link googlecalendar`, which opens one OAuth screen for the user, then retry step 2.

The auth error is normal on first use of any toolkit. It isn't a failure, it's the prompt to link.

## Other commands worth knowing

| Command | What it does |
|---|---|
| `composio tools list <toolkit>` | Every action available in one toolkit |
| `composio tools info <slug>` | What a specific action takes and returns |
| `composio proxy <url> --toolkit <name>` | Raw API call when no packaged tool fits |
| `composio run '<js>'` | Run a small script with `execute()` injected, for chaining several calls |
| `composio whoami` | Which account is logged in |
| `composio login` / `logout` | Session |

## When to use this vs new-capability

**Try Composio first, every time.** It covers most SaaS a business runs on, and it takes one OAuth click instead of an afternoon.

**Fall back to new-capability** when Composio genuinely does not have it: a niche or regional tool, a client's internal API, a bespoke booking or billing system, or a private endpoint.

Search Composio before reaching for the fallback. Building an integration for something that was already one `composio link` away wastes an hour.

## Setup

Covered in `reference/getting-keys.md`. Short version:

```
curl -fsSL https://composio.dev/install | bash
composio login
```

No API key to store. The CLI holds its own credentials, so nothing goes in `.env`.

Free tier is 20,000 tool calls a month with unlimited connected accounts.

**Windows:** check the current Composio documentation for a native Windows route first. If only the shell installer is offered, explain that before using Git Bash. If `composio` still is not found, say so plainly and use new-capability for the tool that matters most.

## Gotchas

- Auth errors on first use of a toolkit are expected. Link, retry, move on. Don't treat them as broken.
- Toolkit slugs aren't always the obvious name (`googlecalendar`, not `google-calendar`). `composio search` returns the correct one, so use what it gives you rather than guessing.
- Connections are per user account. Each person on the team links their own, which is what you want: nobody is reading anyone else's inbox by accident.
- If a tool's action exists but the shape of the data is wrong, `composio tools info <slug>` shows the exact parameters. Faster than guessing at the payload.

## Keep this skill improving

Found a gotcha, a slug that surprised you, or a better pattern? Add it above before you finish. One line each. Append a dated note to the changelog, and never delete an entry.

### Changelog

- **2026-07-28.** Skill created. Workflow and command reference taken from Composio's own CLI documentation, which is written as agent instructions.
