# New capability

> Connect a tool that Composio doesn't cover. The substance lives in the **new-capability skill** (`.claude/skills/new-capability/`), which also fires on its own whenever you ask to connect, integrate or add a service.

**Search Composio first.** It reaches around a thousand tools and takes one click, so it's almost always the right answer:

```
composio search "<what you want to do>"
```

Only come here for what's genuinely left: a niche or regional platform, a client's internal API, a bespoke booking or billing system, a private endpoint.

Run the new-capability skill now against whatever tool was named: research its real API documentation, scope what's actually needed, build the integration, put the key in `.env`, and finish with a live test against their real account. Never report it working on something that wasn't exercised.
