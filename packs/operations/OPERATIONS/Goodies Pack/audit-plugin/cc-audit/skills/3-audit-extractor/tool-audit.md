---
name: tool-audit
description: Open Playwright in a visible browser. User authenticates into a client's SaaS tool, then Claude crawls it read-only, page by page, and produces a dense markdown audit dropped into 01-materials/documents/ for IM to extract on the next run.
menu-code: TA
---

# Tool Audit

## Purpose

Clients regularly grant Adam read-only access to their internal SaaS tools — Workday, BambooHR, HubSpot, custom CRMs, scheduling systems, internal admin panels. Today the only way that knowledge enters `audit-data.json` is if it's discussed on a call or written into an email. TA captures it directly.

TA opens a visible Playwright browser, waits for the user to authenticate, then crawls the tool page by page — clicking only navigation elements, reading every page, taking a structured snapshot — and produces a single dense markdown document at `clients/{slug}/01-materials/documents/tool-audits/{tool-name}/{date-slug}/documentation.md`.

TA is **capture-only**. It writes that one folder. It does NOT write to `extraction.tools[]`, the audit manifest, or any audit domain file. The existing IM (Ingest Materials) capability picks up the new markdown on its next run and handles extraction.

## Read-Only Contract — Hard Rule

> **This capability is READ-ONLY. You are navigating around a tool the user has granted access to, capturing what is visible. You will never modify, create, delete, or submit anything inside the tool. The user is watching every action live and will interrupt if anything looks wrong. In most engagements the client has only granted view access — but you must behave as if you have full edit access and still refuse to modify anything.**

The contract has three layers, all enforced before the first navigation:

### 1. Always headed — never headless

Before any browser tool is called, verify the Playwright MCP is running headed. Inspect the running config via the MCP's introspection or the project's `apg-audit-plugin/.mcp.json` — if `--headless` appears anywhere in the args list, **abort immediately** with:

```
TA ABORTED — Playwright MCP is configured with --headless.
The user must see every action. Remove --headless from
apg-audit-plugin/.mcp.json args, restart Claude Code, and re-run TA.
```

The user must be able to watch the browser at all times. This is non-negotiable.

### 2. Tool allowlist

**Allowed MCP tools:**

| Tool | Used for |
|---|---|
| `mcp__playwright__browser_navigate` | Visit a URL |
| `mcp__playwright__browser_click` | Click a navigation element (links, menu items, tabs) |
| `mcp__playwright__browser_snapshot` | Capture the ARIA tree of the current page (primary read mechanism) |
| `mcp__playwright__browser_tabs` | Switch tabs or list open tabs |
| `mcp__playwright__browser_evaluate` | Run a read-only JS expression to extract DOM data |
| `mcp__playwright__browser_wait_for` | Wait for an element or network idle |
| `mcp__playwright__browser_console_messages` | Read console logs (context only) |
| `mcp__playwright__browser_network_requests` | Read network log (integration discovery) |
| `mcp__playwright__browser_storage_state` | Read auth state (debugging only) |
| `mcp__playwright__browser_take_screenshot` | OFF by default — only call if user explicitly asks |

**Forbidden tools — never call. Also denied at the harness level in `.claude/settings.json`:**

- `mcp__playwright__browser_type`
- `mcp__playwright__browser_fill_form`
- `mcp__playwright__browser_press_key`
- `mcp__playwright__browser_select_option`
- `mcp__playwright__browser_file_upload`
- `mcp__playwright__browser_handle_dialog`
- `mcp__playwright__browser_drag`

The user does the typing (during login). You never type. If something blocks the crawl that would require typing to bypass, stop the crawl and report — do not try to work around it.

### 3. Click discipline — forbidden targets

Even with `browser_click` allowed, do NOT click any element whose visible text or `aria-label` (case-insensitive) matches this regex:

```
\b(save|submit|delete|send|confirm|apply|update|create|publish|archive|remove|cancel|reject|approve|invite|pay|charge|export|download|share|edit|new|add)\b
```

When in doubt, **skip and log "ambiguous — not clicked"**.

**Allowed click targets:**
- Sidebar / top-nav menu items
- Tab headers
- Pagination links (numbers, "Next", "Previous")
- Breadcrumb links
- `<a href>` anchors that navigate to a same-origin URL not matching the forbidden regex

**Read-only `browser_evaluate` only.** Never run JS that calls `document.execCommand`, `fetch` with non-GET methods, `XMLHttpRequest` writes, or anything that touches `localStorage`/`sessionStorage`/`indexedDB` with set/delete. DOM-read queries only (e.g., `Array.from(document.querySelectorAll('a')).map(a => a.href)`).

**If a click accidentally surfaces a confirm dialog** (e.g. a hover-revealed delete button fires on click): do NOT call `browser_handle_dialog`. Let the dialog block the page. The user dismisses it manually. Log the incident and stop the crawl for review.

**No request replay.** The network log capture is for read traffic context only — never replay POST/PUT/DELETE/PATCH requests, even via `browser_evaluate`.

---

## Inputs Needed From User

Before starting the crawl, gather these via a single batched question:

1. **Client slug** — auto-detected if a session is active; otherwise ask.
2. **Tool name** — kebab-case (e.g., `hubspot`, `timely`, `workday-hr`). Becomes the folder name.
3. **Starting URL** — login page or post-login dashboard. The page that opens when the user clicks "Open the tool" on their bookmark.
4. **Origin allowlist** — defaults to the host of the starting URL. Ask the user to confirm and optionally extend (some tools host on multiple subdomains).
5. **Max pages** — default 50. Cap at 200 for safety.

Print the plan and confirm before opening the browser:

```
TOOL AUDIT — {company_name}
─────────────────────────────────────────────────────
  Tool name:        {tool_name}
  Client slug:      {client_slug}
  Output folder:    clients/{client_slug}/01-materials/documents/tool-audits/{tool_name}/{YYYY-MM-DD}-{tool_name}-audit/
  Starting URL:     {start_url}
  Origin allowlist: {origins}
  Max pages:        {max_pages}
─────────────────────────────────────────────────────
  Hard guarantees:
    • Browser is visible — you watch every action
    • No typing, filling, or destructive clicks
    • Crawl stops at first confirm dialog
─────────────────────────────────────────────────────
Confirm? [Y / corrections]
```

---

## Process

Run all stages autonomously after the initial confirmation. The only mid-run pause is for the user to log in (Stage 2). Headed-mode check must happen in Stage 1 before any browser tool is called.

### Stage 1 — Pre-flight

1. **Verify headed mode.** Read `apg-audit-plugin/.mcp.json` and check the `playwright` server's args. If `--headless` appears anywhere, abort with the message above.
2. **Verify deny rules.** Read `.claude/settings.json` and confirm the seven destructive Playwright tools are in `permissions.deny[]`. If any are missing, warn the user — do not proceed until the user confirms they've added them or explicitly waives the check for this session.
3. **Create the output folder** at `clients/{client_slug}/01-materials/documents/tool-audits/{tool_name}/{YYYY-MM-DD}-{tool_name}-audit/`. Date = today's date (`date '+%Y-%m-%d'`).
4. **Initialise in-memory state:**
   - `visited_urls: Set<string>` — URLs already snapshotted
   - `queue: Array<string>` — BFS frontier
   - `pages_captured: Array<PageRecord>` — one entry per visited page
   - `skipped: Array<{url, reason}>` — anything we chose not to visit
   - `crawl_start_ts: ISO timestamp`

### Stage 2 — User Authentication

Call `browser_navigate(url: starting_url)`. The visible browser opens.

Print to the user:

```
BROWSER OPEN — please authenticate.
─────────────────────────────────────────────────────
  1. Log in to {tool_name} in the browser window.
  2. Navigate to the page you want me to start crawling from
     (usually the post-login dashboard).
  3. Type "ready" below when you're sitting on the starting page.
─────────────────────────────────────────────────────
```

Wait for the user to type "ready" (or any confirmation). Do NOT poll the browser. Do NOT take any snapshots during this phase — the user may be entering credentials.

### Stage 3 — BFS Crawl

When the user confirms ready:

1. Call `browser_snapshot()` — capture the post-login starting page.
2. Read the current URL (from the snapshot or via `browser_evaluate("location.href")`). This is the seed URL. Add to `visited_urls`. Append to `queue`.
3. **Loop** while `queue.length > 0 AND pages_captured.length < max_pages`:
   - Dequeue the next URL.
   - `browser_navigate(url)` — navigate to it.
   - `browser_wait_for(time: 1.5)` — let SPAs settle. If the tool is fast, drop to `0.5`.
   - `browser_snapshot()` — read the ARIA tree.
   - **Forbidden-text check on the page itself**: if the page's main heading or URL clearly matches a destructive action (e.g. `/settings/billing/delete`, `Confirm cancellation`), record it under `skipped` with reason "destructive page" and continue to the next queued URL — don't extract.
   - **Extract a `PageRecord`** (see Stage 4 for the data shape).
   - **Discover links.** Run `browser_evaluate` with a read-only expression like:

     ```js
     Array.from(document.querySelectorAll('a[href], [role="tab"], [role="menuitem"], nav button'))
       .map(el => ({
         href: el.href || null,
         text: (el.innerText || el.getAttribute('aria-label') || '').trim().slice(0, 80),
         role: el.getAttribute('role') || el.tagName.toLowerCase()
       }))
       .filter(x => x.href || x.role === 'tab' || x.role === 'menuitem')
     ```

     For each candidate:
     - If `href` is set: only enqueue if the origin is in the allowlist AND not already in `visited_urls` AND the URL doesn't match the forbidden regex (in path or text).
     - If only `role` is set (tabs/menuitems without href — common in SPAs): record under `pages_captured[].navigation_hints` for documentation but do NOT auto-click in v1 (avoids accidental destructive clicks on non-navigation menuitems).
   - **Network log capture (every page):** call `browser_network_requests()` to capture the integrations the page touches. Filter to: distinct hosts + the first path segment per host (e.g., `api.stripe.com/v1/customers`). Store under `pages_captured[].integrations`. Drop bodies — host + path only.
   - **Checkpoint every 10 pages:** flush `pages_captured` to disk by writing partial `documentation.md` so a crash mid-run is recoverable. Append-only writing is fine.

4. **Stop conditions:**
   - Queue empty
   - `max_pages` reached
   - Any forbidden-tool refusal from the harness
   - A confirm dialog blocks the page
   - User interrupts

### Stage 4 — Per-page extraction

For each visited page, build a `PageRecord` with these fields:

| Field | Source |
|---|---|
| `url` | navigation target |
| `title` | from snapshot or `<title>` |
| `nav_position` | breadcrumb + sidebar selection (where do you click to get here from the dashboard?) |
| `purpose` | one-sentence summary inferred from headings + primary content |
| `headings` | h1/h2/h3 list |
| `data_structures` | tables (list column names only — never row values), lists (item type only), cards (label only) |
| `forms_visible` | form name + field labels only — **never field values** |
| `ctas` | buttons + their visible labels (record even forbidden ones — they're documentation) |
| `links_out` | distinct same-origin link targets |
| `integrations` | filtered network log (host + first path segment) |
| `notes` | anything else worth flagging (e.g., "this page has an export button — read-only export likely safe to ignore") |

**Critical privacy rule for tables and forms:** record SCHEMA (column names, field labels) — never DATA (cell values, field values). A page displaying a list of 200 customers becomes "Table with columns: Name, Email, Subscription Status, Last Activity" — not "Customer #1: Jane Doe, jane@..., Active, 2026-05-10". This protects the client's data from ever being committed to disk.

### Stage 5 — Write outputs

Once the crawl stops, write to `clients/{client_slug}/01-materials/documents/tool-audits/{tool_name}/{YYYY-MM-DD}-{tool_name}-audit/`:

#### `metadata.json`

```json
{
  "tool_name": "{tool_name}",
  "tool_url": "{start_url}",
  "audited_at": "{ISO timestamp}",
  "audited_by": "TA capability — Agent 3 audit-extractor",
  "pages_visited": 42,
  "pages_skipped": [
    { "url": "...", "reason": "forbidden text in link" }
  ],
  "crawl_duration_seconds": 412,
  "origin_allowlist": ["https://app.example.com"],
  "playwright_mcp_version": "@playwright/mcp@latest",
  "client_slug": "{client_slug}"
}
```

#### `documentation.md`

```markdown
# Tool Audit — {tool_name}

**Client:** {company_name} ({client_slug})
**Audited:** {date}
**Tool URL:** {start_url}
**Pages captured:** {n}

## Overview

{2-3 paragraph summary written from synthesising the page records: what is this tool, what does the user appear to use it for, what are the main functional areas (e.g. "Bookings", "Customers", "Reports"), what integrations are visible (e.g. "talks to Stripe and Mailchimp via webhooks"). This section is what an APG analyst reads to ramp on the tool. Make it dense and useful — no fluff.}

## Functional Areas

{One paragraph per main area, derived from sidebar/top-nav structure. Each area lists which pages live underneath it.}

## Integrations Observed

{Bulleted list of distinct external hosts seen in network logs, with first-path-segment context. E.g.:
- api.stripe.com — `/v1/customers`, `/v1/subscriptions`
- hooks.slack.com — webhook delivery
- accounts.google.com — OAuth provider}

## Pages

### {url}
**Title:** {title}
**Navigation:** {nav_position}
**Purpose:** {purpose}

**Headings:** {list}

**Data structures:**
- Table — columns: {columns}
- List — item type: {type}

**Forms visible:** {form name — field labels only}

**CTAs:** {buttons}

**Links out:** {distinct same-origin link targets}

**Integrations on this page:** {hosts}

**Notes:** {notes if any}

---

{repeat per page}
```

### Stage 6 — Summary

Print:

```
TOOL AUDIT COMPLETE — {tool_name}
══════════════════════════════════════════════════════
  Pages visited:        {n}
  Pages skipped:        {n}  ({reasons summary})
  Distinct integrations: {n}
  Crawl duration:       {mm:ss}
  Output:               clients/{client_slug}/01-materials/documents/tool-audits/{tool_name}/{date-slug}/documentation.md
══════════════════════════════════════════════════════

NEXT: Run /audit:3-audit-extractor → IM (Ingest Materials)
      to extract this tool audit into extraction.tools[].
```

### Stage 7 — Close browser

Do NOT explicitly close the browser via an MCP tool — `--user-data-dir` persists state, and leaving the window open lets the user spot-check pages. Just print the summary and stop.

---

## Resumability

If the crawl is interrupted (user closes the browser, hits Ctrl-C, harness times out): the last checkpoint flush in Stage 3 means `documentation.md` exists with whatever pages were captured. Re-running TA for the same tool on the same date will use the same folder (`{YYYY-MM-DD}-{tool_name}-audit/`) — read the existing `metadata.json`, populate `visited_urls` from the page sections in `documentation.md`, and resume the BFS. If the date has rolled over, start a fresh folder.

## CRM Task Update

None. TA is an enrichment capability that doesn't gate any pipeline stage. No CRM mutation.

## Sidecar memory

Save a one-line memory in the active client's sidecar file at `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-process-mapper-sidecar/clients/{client_slug}.md`:

```
{date} — TA captured {tool_name} ({n} pages, {n} integrations) → tool-audits/{tool_name}/{date-slug}/
```

That's it. The memory entry helps SU and IM notice the new material on the next run.
