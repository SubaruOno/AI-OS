---
name: new-capability
description: >
  Build a custom API integration when Composio doesn't cover the tool. ALWAYS run
  `composio search "requested action"` first: it covers around a thousand platforms
  and takes one OAuth click instead of an afternoon. Use this only for what's left:
  a niche or regional platform, a client's internal API, a bespoke booking or billing
  system, a private endpoint. New capability, add capability, API integration,
  connect service, add integration, build capability, service integration, add API,
  connect API, new integration.
  Runs deep web research on official API docs, interactive scoping, and produces
  a complete Context Skill auto-matched to one of 4 capability forms (Lean Reference, Client Wrapper, SDK Pass-Through, CLI Tool).
  Strictly custom-built from primary API documentation — no third-party skills or marketplace integrations.
---

# New capability: capability factory

Systematically build custom API integration capabilities for this workspace. Take a service name and run a seven-stage interactive workflow: gather intent, research official API docs, scope read/write operations, design the integration, write an exploration doc, generate an implementation plan, and hand off to implement.

The output is a Context Skill whose description makes it load when relevant topics arise. Build it from official API documentation and match it to one of four capability forms based on the API's shape.

**Output chain:** exploration doc → implementation plan → implement handoff

---

## Anti-Marketplace Rule (HARD CONSTRAINT)

Do NOT suggest, recommend, or use:
- Pre-built MCP servers from any marketplace or registry
- Third-party wrapper skills or plugins
- Community-built integrations or "awesome-mcp" lists
- Any pre-packaged solution not built from this workspace's patterns

**Why this rule exists:** Third-party skills are black boxes. You don't know what they actually do, what endpoints they skip, what they'll break when the API changes, or when the maintainer stops updating them. They almost always cover 20% of the API surface and leave you stuck when you need the other 80%. They create invisible dependencies on someone else's maintenance schedule.

The point of new-capability is to build capabilities that are understood, controlled, and fit the workspace architecture.

**Redirect script:** If the user mentions a pre-built integration, acknowledge it exists but redirect: "That covers basic reads but won't handle [specific operations from their intent]. Building custom from the official docs gives you full control and exactly the operations you need. Takes a bit longer upfront but you never hit a wall."

---

## Capability Forms

Every capability fits one of four forms. The form determines the file structure, SKILL.md shape, and implementation approach. **Auto-select the form during Stage 3 (Scope) based on the decision tree below, then read the matching example before Stage 4.**

### Decision Tree

```
1. Does a mature, actively-maintained official Python SDK exist?
   YES → Form 3: SDK Pass-Through
   NO  ↓
2. Is the API simple? (API-key auth, <15 endpoints, mostly reads, stateless)
   YES → Form 1: Lean Reference
   NO  ↓
3. Does the use case need CLI subcommands, safety-first writes, or complex query syntax?
   YES → Form 4: CLI Tool
   NO  ↓
4. Default → Form 2: Client Wrapper
```

### Form 1: Lean Reference

**Best for:** Simple API-key auth, <15 endpoints, read-heavy, stateless calls. No token refresh. Rate limits generous.

**Structure:** SKILL.md contains everything. No separate client module. A copy-paste helper function (5-8 lines) with auth baked in, an endpoint table, 3-5 high-value query recipes, and a lookup table for magic strings (IDs, statuses, field names). Target ~100-150 lines.

**Files:** SKILL.md + reference doc only. No `scripts/` folder.

**Emphasize:** Get-to-working-in-10-seconds. The agent should never need to leave the file for common operations.

**When raw HTTP beats a wrapper:** The API is simple enough that a client class adds dependency without reducing complexity. A 5-line helper function wins.

| Example | Lines | Key Features | Path |
|---------|-------|-------------|------|
| Supadata | ~90 | `SupadataClient()` class, 21-method table, async job polling, credit costs | `.claude/skills/supadata/SKILL.md` |
| Close CRM | ~123 | HTTP Basic helper, endpoint table, pipeline IDs, 4 query recipes | `.claude/skills/<name>/SKILL.md` |

### Form 2: Client Wrapper

**Best for:** OAuth or complex auth, 20+ endpoints, read-write operations, domain-specific data formats, enough quirks that raw HTTP means rediscovering gotchas every session. **This is the default for medium-to-complex APIs.**

**Structure:** SKILL.md (~250-400 lines) is the reference guide. Custom `scripts/{service}/client.py` handles auth, retries, pagination, and convenience methods. Optional helpers for domain-specific formats (rich text builders, nested object constructors, cache layers).

**Files:**
- `.claude/skills/{service}/SKILL.md` — reference guide
- `scripts/{service}/client.py` — main client class
- `scripts/{service}/config.py` (optional) — constants, env var loading
- `scripts/{service}/cache.py` (optional) — for read-heavy APIs with tight rate limits
- Domain helpers as needed (e.g., `tiptap.py` for rich text, report parsers)

**Client class pattern:**
1. HTTP base methods (`_get`, `_post`, `_put`, `_patch`, `_delete`)
2. Auto-retry on 429/5xx with exponential backoff
3. Pagination helpers (`_paginate_all`)
4. Auth management (token caching, refresh)
5. High-level convenience methods (what SKILL.md documents)

**Emphasize:** Convenience methods over raw endpoints. Domain helpers for complex data formats. Accumulated gotchas that prevent re-learning the API's quirks.

| Example | Lines | Key Features | Path |
|---------|-------|-------------|------|
| Circle | ~296 | 80+ endpoints, TipTap rich text builder, cache layer, Playwright fallback, space lookup table, 4 gotchas | `.claude/skills/<name>/SKILL.md` |
| Guesty | ~301 | OAuth token caching (5/day limit), auto-pagination, convenience aggregations (`revenue_for_period`, `occupancy_rate`), 10 gotchas | `blake-os/.claude/skills/guesty/SKILL.md` |

### Form 3: SDK Pass-Through

**Best for:** APIs with a high-quality official Python SDK that covers the endpoints you need. Multi-domain platforms where the SDK handles serialization, streaming, retries, and type hints that would take 50+ lines to replicate manually.

**Structure:** SKILL.md (~200-350 lines) documents what the SDK can do, organized by capability domain. Don't rewrite the SDK's documentation. Instead: configure it, map capabilities, provide workspace-specific context (which models/voices/presets to prefer), and give ready-to-run snippets. Lookup tables for IDs, models, and enum values inline.

**Files:** SKILL.md + reference doc. No custom client (the SDK IS the client). SDK installed via requirements.txt.

**Emphasize:** Domain-organized capability sections, each with a code snippet and a reference table. Workspace-specific defaults ("Use this voice ID for brand content"). Plan limits and pricing.

**When to use SDK vs raw HTTP:** Use the SDK when it exists, is actively maintained, and the API has complex request/response shapes (multipart uploads, streaming, nested objects). Only drop to raw HTTP for endpoints the SDK doesn't cover yet.

| Example | Lines | Key Features | Path |
|---------|-------|-------------|------|
| ElevenLabs | ~340 | 9 domain sections (TTS, STT, voice clone, SFX, etc.), voice ID lookup, model table, plan details, SDK v2.38.0 | `.claude/skills/<name>/SKILL.md` |

### Form 4: CLI Tool

**Best for:** APIs where the primary UX is command-line subcommands, safety-critical writes need explicit confirmation (draft-then-send), or the API has complex query syntax that benefits from documented search operators.

**Structure:** SKILL.md (~200-250 lines) is a CLI reference. Documents subcommands, arguments, flags, query syntax, and compound patterns (chained bash calls). Supporting Python script with argparse/click CLI interface invoked via `python scripts/{service}_tool.py <command>`.

**Files:**
- `.claude/skills/{service}/SKILL.md` — CLI reference
- `scripts/{service}_tool.py` — main CLI script
- Shared auth module if using OAuth (e.g., `scripts/google_auth.py`)

**Emphasize:** Command reference table, query/search syntax documentation (often the most valuable section), safety guarantees (no permanent delete, draft before send), and compound bash patterns.

**When CLI beats a client class:** When the tool has many distinct subcommands with different behaviors, when safety requires explicit user confirmation steps, or when the primary consumer is bash scripts and cron jobs rather than Python imports.

| Example | Lines | Key Features | Path |
|---------|-------|-------------|------|
| Gmail | ~220 | CLI subcommands (inbox, search, read, draft, send, label), Gmail search syntax docs, draft-then-send safety, shared Google OAuth | `.claude/skills/google-gmail/SKILL.md` |

### Quick Reference

| Signal | Form 1: Lean | Form 2: Client Wrapper | Form 3: SDK | Form 4: CLI Tool |
|--------|:---:|:---:|:---:|:---:|
| Endpoints | <15 | 20+ | 30+ (SDK covers) | Many subcommands |
| Auth | API key | OAuth / complex | Any (SDK handles) | OAuth / complex |
| Official SDK? | No / unnecessary | No / poor quality | Yes, mature | No |
| Operations | Mostly read | Full CRUD | Multi-domain | Safety-critical writes |
| Data formats | Simple JSON | Complex + custom | Complex (SDK handles) | Query syntax |
| SKILL.md size | ~100-150 lines | ~250-400 lines | ~200-350 lines | ~200-250 lines |
| Supporting code | None (inline) | `scripts/{service}/` | None (SDK) | CLI script |

**Also read:** this workspace for the master service index, `.env.example` for credential patterns.

---

## Stage 1: INTENT — What Do You Need This For?

**Goal:** Understand business context before burning tokens on research.

Ask these questions:

1. **What service are you connecting?** Confirm the exact product and API. ("Google Calendar" vs. "Google Workspace" vs. "CalDAV" are very different scopes.)
2. **What role does this play in your business?** What problem does connecting it solve? Why now?
3. **What specific use cases?** Concrete examples, not abstract needs. ("Check my calendar before sending daily briefs" vs. "full event CRUD for a scheduling feature" shapes research completely differently.)
4. **Which existing commands/workflows/crons would use this?** Ground it in the workspace.
5. **Do you already have API access set up?** Account, API key, OAuth app, or is that part of the work?
6. **Any constraints?** Read-only, specific plan tier, multiple accounts, rate limit concerns?

**Output:** A clear intent statement that shapes all subsequent research. Save it internally for the exploration doc.

**STOP — wait for user responses before proceeding.**

---

## Stage 2: RESEARCH — Deep API Discovery

**Goal:** Complete understanding of the API surface from official primary sources.

### Research Methodology (follow this checklist in order)

1. **Official API documentation** — Web search for `{service} API documentation`, `{service} REST API reference`, `{service} developer docs`. Find the canonical docs site. Read the getting-started guide and API reference.

2. **Authentication** — What auth model? API key, OAuth2, service account, JWT? What scopes/permissions are needed for the operations identified in Stage 1? Token refresh requirements?

3. **SDK availability** — Is there an official Python SDK? Well-maintained? What version? Does it cover the endpoints you need? Or is raw HTTP the better path? Check PyPI for install instructions.

4. **Endpoint inventory** — Catalog every relevant endpoint group. For each: HTTP method, path, one-line description, required parameters, response shape summary. Group by domain (e.g., Calendar: Events, Calendars, Settings).

5. **Rate limits and quotas** — Hard limits per minute/day/month? Quota differences by plan tier? Burst limits? Retry-After header behavior?

6. **Webhooks/real-time** — Push notifications, websockets, or event subscriptions? Relevant to the user's use cases?

7. **Known limitations** — Search for `{service} API limitations`, `{service} API gotchas`, `{service} API breaking changes`. Check GitHub issues, Stack Overflow, developer forums. Note undocumented behavior.

8. **Existing workspace state** — Read this workspace to check if this service is already partially connected. Check `.claude/skills/` for any existing skill. Check `scripts/` for existing collectors. Check `.env.example` for existing env vars.

### Anti-Marketplace Reminder

If the user mentions a pre-built integration during research, use the redirect script from the Anti-Marketplace Rule section above.

### Present Findings In This Format

- **Auth model summary** — type, scopes needed, token refresh requirements
- **SDK recommendation** — official SDK vs. raw HTTP, with reasoning
- **Endpoint groups by domain** — organized by logical grouping (Events, Members, Settings, etc.)
  - For each group: key endpoints table with method, path, one-line description
- **Rate limits table** — limits, quotas, retry behavior
- **Known gotchas** — numbered list of pain points, undocumented behavior, common mistakes
- **Workspace integration points** — which existing systems would use this capability

**STOP — present findings, wait for user input before proceeding.**

---

## Stage 3: SCOPE — Read/Write Priority Matrix

**Goal:** User picks exactly which operations they need. No more, no less.

### Present a Capability Matrix

For each endpoint group identified in research:

```
### {Domain} (e.g., Events)

#### Read Operations
- [ ] List all → GET /resource
- [ ] Get single → GET /resource/{id}
- [ ] Search/filter → GET /resource?query=...

#### Write Operations
- [ ] Create → POST /resource
- [ ] Update → PUT/PATCH /resource/{id}
- [ ] Delete → DELETE /resource/{id}

#### Subscribe
- [ ] Webhook → POST /webhooks
```

### Scope Discipline

Push back on scope creep: "You mentioned [intent from Stage 1]. Do you actually need [obscure endpoint] for that, or can we skip it?"

### Map to Workspace

For each selected operation, note:
- Which existing commands/skills/crons would call this?
- Does this feed the SQLite warehouse? Which table? (Check this workspace)
- Does this need a cron job? What schedule?
- Interactive during sessions, or fully automated?

### Select Form

Based on the research findings and scoped operations, run the decision tree from the Capability Forms section:

1. **Announce the selected form** and why (e.g., "This is a Form 2: Client Wrapper because Guesty uses OAuth with token refresh, has 30+ endpoints, and needs pagination helpers.")
2. **Name the example skill** you'll read before Stage 4 (e.g., "I'll read Circle's SKILL.md as the reference for this form.")
3. **Note any form-specific file requirements** (e.g., Form 2 needs `scripts/{service}/client.py`, Form 4 needs a CLI script)

**STOP — confirm final scope and form selection before proceeding.**

---

## Stage 4: DESIGN — Integration Architecture

**Goal:** Design the complete capability before writing anything.

**Before designing:** Read the matching form's example skill from the Capability Forms section above. The form was selected during Stage 3 based on the decision tree.

### Design Decisions Checklist

#### 1. File Inventory

Determine which files this capability needs:

| File | When to include |
|------|----------------|
| `.claude/skills/{service}/SKILL.md` | Always. The canonical auto-loading Context Skill. Mirror it with `scripts/sync_harness_skills.py`. |
| `reference/services/{service}.md` | Always. Deep reference doc with full endpoint details. |
| `scripts/{service}/client.py` or `scripts/utils/{service}.py` | When auth needs wrapping, retry logic, or the API has quirks that benefit from a client class. |
| Entry in this workspace | Always. Register in the master index. |
| Entry in `.env.example` | Always. Credential template for API keys/tokens. |

#### 2. Auth Architecture

Design the full auth flow:
- **API key:** Save through `scripts/set_secret.py`, store in `.env`, and load via `os.getenv()`. Never enter it in chat or a command argument.
- **OAuth2:** Needs: token storage location, refresh flow, initial authorization script (`scripts/setup_{service}_oauth.py`), scopes. Spec the complete flow including first-time setup.
- **Service account:** JSON key file, store path in `.env`, load with the service's SDK.

#### 3. SKILL.md Structure

The resulting Context Skill follows this template:

```
---
name: {service}
description: >
  {Service Name} API integration — {what it does}.
  {Natural language keywords for auto-discovery}.
  {Routing note: "For X, use Y instead."}
---

# {Service Name} API

{One-line: what this is, how many endpoints, scope.}

## Setup

{Auth initialization code block — copy-paste ready.}

## Key Endpoints

{Quick-reference tables grouped by domain. Columns: Method | What | Code.}

## Common Patterns

{3-5 copy-paste code blocks for the most frequent workflows.}

## Reference

{Lookup tables: IDs, field names, enum values, status codes.}

## Rate Limits

{Limits, quotas, retry behavior.}

---

## Maintenance

> **Self-improvement rule:** If you used this skill and discovered
> something not documented here — a gotcha, API quirk, new pattern,
> or better approach — add it below before finishing your task.
> Keep entries concise (one line each). If this section grows beyond
> 10 items, refactor learnings into the main body above.

### Known Gotchas

(none yet)

### Improvement Backlog

(none yet)
```

#### 4. Validation Test Matrix

For every scoped read/write operation, define a concrete test:

| # | Operation | Test Description | Expected Result | Self-Heal Strategy |
|---|-----------|-----------------|-----------------|-------------------|
| 1 | List items | Fetch all items from the primary resource | Array of items returned, status 200 | Check auth, check base URL, check required headers |
| 2 | Get single | Fetch one item by ID from test 1 | Item fields match, status 200 | Check ID format, check API version |
| 3 | Create | Create a test item with required fields | Item ID returned, item visible via read | Check required fields, check payload format |
| 4 | Update | Modify a field on the test item | Updated field returned on re-read | Check PUT vs PATCH, check required fields on update |
| 5 | Delete | Delete the test item | 404 on re-read, or 200 with deleted flag | Check soft-delete vs hard-delete behavior |

Tests run sequentially during implementation. If a test fails: read the error, diagnose, fix the code, re-run. Loop until pass. After 3 failed attempts on the same test, surface as a hard blocker to the user (missing permissions, plan limitations, undocumented API behavior).

#### 5. Self-Healing Design

The resulting skill includes two Maintenance subsections:
- **Known Gotchas** — one-liner issues discovered during use. Standard pattern from existing skills.
- **Improvement Backlog** — larger items needing a dedicated session. Track them here rather than losing them.

When gotchas hit 10+ items, refactor the patterns into the main SKILL.md body.

### Present the Full Design

Show the complete architecture: file inventory, auth flow, SKILL.md outline with section headers, validation test matrix, and self-healing plan.

**STOP — confirm design before proceeding.**

---

## Stage 5: EXPLORATION DOC — Write the Handoff Artifact

**Goal:** Compile everything into a single, extensive exploration document.

**File:** `plans/explore-YYYY-MM-DD-{service}-capability.md`

### Required Sections

Use this template for the exploration doc:

```markdown
# Explore: {Service Name} API Capability

**Created:** YYYY-MM-DD
**Status:** Explored
**Origin:** {One-line: what capability is being built and why}

---

## Intent

{Full intent statement from Stage 1: service, business context, use cases, constraints}

## API Research

### Authentication
{Auth model, scopes, token refresh, SDK or raw HTTP recommendation}

### Endpoint Inventory
{Full endpoint tables by domain group — method, path, description, required params}

### Rate Limits
{Limits table, quota notes, retry behavior}

### SDK Analysis
{Official SDK assessment — version, coverage, recommendation}

### Known Gotchas
{Numbered list from web research — limitations, undocumented behavior, common mistakes}

## Scoped Operations

### Read Operations
{Confirmed read operations with workspace mapping}

### Write Operations
{Confirmed write operations with workspace mapping}

### Out of Scope
{Endpoints explicitly excluded with reasoning}

## Architecture Design

### File Inventory
{Complete list of files to create/modify}

### Auth Flow
{Step-by-step auth setup including first-time configuration}

### SKILL.md Structure
{Planned section headers and content summary for each}

### Validation Test Matrix
{Full test table from Stage 4}

## Decisions Log
{All decisions made during interactive stages, alternatives considered}

## Workspace Connections
{Which existing systems use this, data flow, cron integration}
```

**This is the critical artifact.** If it's thin, the plan will be thin. If it's thorough, the plan will produce a working capability on the first `/implement` run. Be exhaustive.

Present the doc path and confirm it's saved.

---

## Stage 6: PLAN — Generate Implementation Plan

**Goal:** Chain directly into plan generation while all context is fresh.

**Prompt the user:** "Exploration doc complete. I have all the context from research and scoping. Want me to write the implementation plan now?"

**If yes:** Generate a phased plan at `plans/YYYY-MM-DD-{service}-capability.md`.

### Plan Format (HARD REQUIREMENT)

**You MUST read `.claude/commands/create-plan.md` and use its exact plan format.** This is not optional. The plan must include every section from the `/create-plan` template:

1. Header: Created, Status (Draft), Request, GTD Project
2. **Overview** — What This Plan Accomplishes + Why This Matters
3. **Current State** — Relevant Existing Structure + Gaps or Problems Being Addressed
4. **Integration Type** — Classification, Reasoning, Location, Auto-discovery
5. **Proposed Changes** — Summary + New Files table + Files to Modify table + Files to Delete table
6. **Design Decisions** — Key Decisions Made + Alternatives Considered + Open Questions
7. **Step-by-Step Tasks** — Each step with detailed Actions, Files affected, and Validation
8. **Connections & Dependencies** — Files That Reference This Area + Updates Needed + Impact on Existing Workflows
9. **Validation Checklist** — Checkbox list of every verification step
10. **Success Criteria** — Numbered measurable criteria
11. **Notes** — Future considerations, related ideas

### Plan Step Structure

The Step-by-Step Tasks section should follow these phases (adapt to the specific capability):

1. **Auth setup and basic connectivity** — prove the API key/OAuth flow works with a single test request
2. **Build client wrapper / CLI tool — read operations** — core read operations, search, fetch
3. **Add write operations** — create, update, delete with payload formatting
4. **Write the Context Skill SKILL.md** — auto-loading capability with all sections from the design
5. **Write the reference doc** — deep documentation at `reference/services/{service}.md`
6. **Register the capability** — add to this workspace and `.env.example`
7. **Validation** — run every test in the matrix sequentially. Self-heal until all pass or hard blocker identified.
8. **Smoke test** — use the capability in a real workflow from the intent statement. Confirm end-to-end.

**Each step includes:**
- Detailed description of what to do
- Specific bullet-pointed actions
- Files affected (with paths)
- Validation criteria (how to know the step is done)

---

## Stage 7: HANDOFF — Guide to Implementation

**Goal:** Set the user up for a clean implementation session.

**Output:**

```
Plan complete at plans/YYYY-MM-DD-{service}-capability.md

To build this capability, start a fresh session:

Prime this workspace, then implement plans/YYYY-MM-DD-{service}-capability.md

The plan includes validation tests for every operation.
Implementation will self-heal until full read/write capability is confirmed.
```

---

## Critical Rules

1. **Interactive** — present findings at every stage, wait for responses. Never complete all stages autonomously. The stop gates between stages are mandatory.
2. **Anti-marketplace** — zero tolerance for third-party skills, MCP servers, or pre-built integrations. This is not a preference, it's a hard constraint.
3. **Workspace-aware** — always ground the design in existing workspace patterns. Read the matching form's example skill before designing. Check this workspace for existing state.
4. **Exhaustive research** — Stage 2 must go deep on the web. Thin research produces thin plans that stall during implementation. Search multiple queries, read multiple doc pages, find the gotchas.
5. **Self-healing** — the test matrix is mandatory. Every scoped operation gets a concrete test with expected result and self-heal strategy. No shipping untested capabilities.
6. **Quality bar** — the resulting Context Skill must match the quality of the matching form's example (Circle for Form 2, ElevenLabs for Form 3, Gmail for Form 4, Supadata for Form 1). If it wouldn't look right next to those skills, it's not done.
7. **Plan format compliance** — Stage 6 plan MUST use the exact create-plan template. Read `.claude/commands/create-plan.md` before writing the plan.
8. **Dual-harness registration** — Write the canonical skill under `.claude/skills/`, run `python scripts/sync_harness_skills.py`, and test `--check` before reporting it available in Codex.

---

## Maintenance

> **Self-improvement rule:** If you used this skill and discovered something not documented here (a gotcha, better research approach, improved stage flow, or pattern worth codifying) add it below before finishing your task. Keep entries concise. If this section grows beyond 10 items, refactor learnings into the main body above.

### Known Gotchas

1. Stage 6 plan MUST use the exact `/create-plan` template format (read `.claude/commands/create-plan.md`). First implementation (Gmail, 2026-03-15) used a loose "phases" structure that was missing Overview, Current State, Integration Type, Design Decisions, Connections & Dependencies, Validation Checklist, and Success Criteria sections. The `/implement` command expects the strict format. Now enforced as Critical Rule #7 and in Stage 6 instructions.

### Improvement Backlog

(none yet)
