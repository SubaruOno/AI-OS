# Cowork Demo Patterns — Solution Architect Reference

Reference for the `BC` (Build Cowork Demo) capability. Covers candidate scoring, scene extraction, prompt construction, fabrication rules, and output file formats.

---

## Candidate Selection

### Source

Candidates come from **plugin cards** in `strategic_approaches.service_tier_recommendation.{low_ticket|mid_ticket|high_ticket}.plugin_cards[]`.

Collect all cards across all tiers into a flat list. Each card represents a bundled plugin (one or more changes) that the Improvement Researcher has already validated as a coherent deliverable.

Do NOT score from `proposed_changes[]` directly — those are the raw building blocks; the plugin cards are the packaged, client-facing offers.

### Filter criteria (applied before scoring)

Exclude cards where `tools_connected[]` contains only custom-build, SaaS-replacement, or non-Cowork tools (e.g. custom software, Salesforce, NetSuite). These belong on the RE/BA/BP track.

Include cards where at least one of:
1. `tools_connected[]` contains a native MCP (`Google Sheets`, `Google Calendar`, `Gmail`, `Google Drive`, `HubSpot`, `Notion`, `Slack`) — **primary signal**
2. `mcp_wrapper_needed == false` — pure native chain
3. `mcp_wrapper_tools[]` contains only Twilio (fabrication-safe for SMS demos)

### Scoring formula

```
score(plugin_card) =
  PRIMARY (demo-ease):
    + 3 if len(tools_connected) == 1                   # single tool — simplest live demo
    + 2 if len(tools_connected) == 2                   # two tools — clean chain
    + 1 if len(tools_connected) == 3                   # three tools — marginal
    + 0 if len(tools_connected) > 3                    # complexity red flag

  PRIMARY (client clarity):
    + 3 if any source_quotes[] has a pain_point_id whose full pain_point record has
          confidence == "HIGH" AND source_timestamp_seconds IS NOT NULL
    + 2 if HIGH confidence but no timestamp
    + 1 if MEDIUM confidence
    + 0 if no source_quotes or all LOW

  SECONDARY (viability):
    + 1 if mcp_wrapper_needed == false (pure native — can demo without fabrication)
    + 1 if sequential_bundle == true (clear Input → Process → Output narrative)
    + 1 if simplification_metric text contains concrete before/after numbers
      (signal: "hours", "minutes", "/day", "/week", numbers like "3–5 hrs")
    + 1 if output_summary describes a single, visually clear artefact
      (e.g. "roster in Google Sheets", "SMS to each staff member", "payroll exception report")

  ROI (tiebreaker only):
    + normalized(annual_saving_aud / 100000) capped at 1
```

**Goal:** The top candidate should be the plugin the client will recognise immediately and that Claude can demonstrate in under 2 minutes. The ideal demo has self-contained input data, produces a single crisp output, and references a verbatim quote the client said.

---

## Scene Extraction

> **BC now uses a two-layer approach.** Stage 2.5 (Deep Transcript Read) runs first and produces a `scene_bundle` from the raw Fathom transcripts. The `scene_bundle` is the **primary** source for prompt content. The audit-data fields below are the **fallback** when the bundle has gaps. See `references/transcript-deep-read.md` for the full deep-read procedure and scene_bundle schema.

Build a scene bundle from `audit-data.json` and `selected_plugin`. Goal: the client recognises themselves in the scenario.

### Primary source — scene_bundle (from transcript deep-read)

| scene_bundle field | Use in prompt |
|---|---|
| `client_vocabulary[]` | All sections — use their exact terms throughout; never substitute generic equivalents |
| `actual_workflow_steps[]` | Section 1 (role framing) — current-state prose in their order |
| `observed_artefact_structure.columns[]` | Section 3 (task) and Section 4 (output format) — CSV/xlsx columns must mirror their actual sheet |
| `observed_artefact_structure.notes_content_patterns[]` | Notes column content spec — what types of content go in notes (medication, pickup, behaviour, etc.) |
| `concrete_examples[]` | Section 2 — character list (real participant/staff names + constraints) and "Today's situation" paragraph |
| `business_rules_demonstrated[]` | Section 2 — business rules block; use as demonstrated, not as summarised |
| `verbatim_quotes[0]` | demo-brief.md talk track Opening — prefer over `source_quotes[0].quote` if richer |

### Fallback source — audit-data fields (use when scene_bundle has gaps)

| Source field | Use in prompt |
|---|---|
| `company_name` (audit-data root) | Role framing: "You are acting as {name}'s operations assistant" |
| `selected_plugin.source_quotes[best].quote` | Verbatim anchor if scene_bundle verbatim_quotes is empty |
| `selected_plugin.source_quotes[best].pain_point_id` → `pain_points[].source_timestamp_seconds` + `sessions[].fathom_url` | Fathom deep-link: `{fathom_url}?t={seconds}` |
| `staff_roster[]` (up to 8, pick roles relevant to `selected_plugin.what_it_does`) | Character list supplement if concrete_examples is sparse |
| `selected_plugin.change_ids[]` → `proposed_changes[].affected_step_ids` → `processes[].steps[]` | Workflow detail fallback |
| `selected_plugin.simplification_metric` | Before/after numbers: "Currently 3–5 hrs/day → under 30 min" |
| `selected_plugin.tools_connected[]` (the tools being replaced/used) | Tool names in role framing |
| `selected_plugin.annual_saving_aud` + `time_saved_weekly_hrs` | ROI numbers for brief |
| `company_info.industry`, `company_info.location` | Realism (addresses, suburb names, etc.) |

### Character list rules

- Use **real staff names** from `staff_roster[]` — max 8 people in the demo scenario.
- If fewer than 3 staff in roster, fabricate plausible names in the same role categories. This is explicitly permitted (`feedback_demo_data_fabrication_ok.md`). Use common Australian names; avoid obviously fictional ones.
- Include actual job titles/roles from the roster in the prompt character list.
- Real locations (suburb, city) from `company_info` or `processes[]` steps wherever available.

---

## Demo Prompt Structure

The demo prompt (written as body of `SKILL.md` and duplicated to `demo-prompt.md`) must follow this structure:

### Section 1 — Role framing
```
You are Claude acting as {company}'s {function} assistant.

{Company} currently {1–2 sentence description of current-state workflow — use real tools, real volumes, real pain}.
```

### Section 2 — Scene data (inline)
```
Here is the context for today's demo:

**Staff on roster:**
- {Name}, {Role} — availability: {realistic availability}
- ...

**Today's situation:**
{2–4 sentences describing the concrete scenario — real locations, real volumes. Make it specific enough that the client says "that's us."}
```

### Section 3 — Task
```
**Your task:**
{Step-by-step instructions. Each step = one discrete output. Use numbered list.}

1. Build a {table/roster/list} with columns: {exact columns}
2. For each {person/record}, generate {output format — e.g., "an SMS message of ≤160 characters starting with their first name"}
3. {Additional step if needed}
4. At the end, print a summary: {exact format for the summary line}
```

### Section 4 — Output format
```
**Output format:**
- {Roster/table}: Markdown table
- {SMS block}: Numbered list, one per {person/record}
- {Email digest}: Standard email format (Subject: / Body:)

For any send/dispatch action (SMS, email), print a confirmation line:
> [Auto] {Action type} sent to {recipient} ✓
```

### Section 4b — Visual Demo Artifact

> This section is assembled by the BC skill at Stage 3.7 using `references/cowork-demo-html-template.md`. It instructs the demo-time model to write a self-contained HTML artifact as the visual climax of the demo. The text output (markdown table + `[Auto]` lines) runs first; the HTML lands last.

The Section 4b instruction block to embed verbatim in the prompt is defined in `cowork-demo-html-template.md` (see "Section 4b — Instruction Block"). Summary of what it tells the demo-time model:

1. Using the run sheet and SMS messages already generated above, produce a complete `live-demo.html`.
2. Fill `{{PLACEHOLDER}}` values with the scenario data computed in the current run.
3. Write the file to `clients/{client_slug}/cowork-demo/live-demo.html`.
4. Print: `Visual demo written → clients/{client_slug}/cowork-demo/live-demo.html`
5. Emit the same HTML in a single fenced ` ```html ` block (best-effort inline render for Cowork/Desktop).

**Fragment mapping** (which fragments to assemble into Section 4b):

| `observed_artefact_structure` shape | Fragments |
|---|---|
| `{columns: [...], per_person_output: "sms"}` | page-shell + roster-grid + sms-card + metric-bar |
| `{columns: [...]}` no per-person output | page-shell + table-view + metric-bar |
| `{type: "calendar"}` or scheduling-only | page-shell + roster-grid + metric-bar |
| `{type: "report"}` or aggregated | page-shell + table-view + metric-bar |
| Single-output action | page-shell + table-view + metric-bar |

The assembled HTML (full page-shell CSS + JS + selected body fragments) is embedded directly into the prompt so the demo-time model has the complete shell to fill in — no external reference lookup required at run time.

### Section 5 — Acceptance checks (internal — do not show to client)
> These are Adam's sanity checks, not shown in the Claude session:
> - [ ] Output contains real staff names from the roster
> - [ ] SMS messages are ≤160 chars
> - [ ] Totals/counts match the scenario numbers
> - [ ] `[Auto]` lines appear for any Twilio/send action (fabrication line)

---

## Fabrication Rules

1. **Fabrication is permitted and preferred** for intermediate steps that would require live API credentials on the call. Source: `feedback_demo_data_fabrication_ok.md`.
2. **For Twilio / SMS send actions:** never attempt a live API call. Instead, output a formatted fabrication line per recipient:
   ```
   [Auto] SMS sent to Jordan Lee (+61 412 345 678) ✓
   ```
3. **For Google Sheets writes:** if the Sheets MCP is wired up, Claude can write live — this is the ideal demo. If not wired, have Claude print the formatted table first, then a fabrication line:
   ```
   [Auto] Roster updated in "Brightside Services — Scheduling" Google Sheet ✓
   ```
4. **One disclaimer per demo session:** At the conclusion of the demo, Claude prints one line: "Note: send actions are simulated for this demo — live deployment connects to your real accounts." This is the only mention. Do not flag fabrication mid-demo.
5. **Real data fragments beat invented ones.** If the audit-data has real names, use them. Only invent what's genuinely missing (e.g. specific shift times — fabricate realistic ones based on the industry).

---

## Talk Track Template (for `demo-brief.md`)

```
OPENING (read aloud verbatim or adapt):
"{Name}, you mentioned during our session that '[VERBATIM QUOTE]'. What I want to show you
is exactly how that problem gets solved — right here, right now."

[Run the demo — paste demo-prompt.md into Claude or invoke the SKILL.md skill]

AFTER OUTPUT:
"What you just saw took [TIME]. Previously that was taking [BEFORE TIME]. 
That's [SAVING] back every [day/week] — and that's one workflow."

CLOSE:
"This isn't a mockup. That output is real — the only difference between this and a live
system is the send action connects to your actual [SMS/email/sheets] account."
```

---

## Claude Desktop Skill Frontmatter Schema

A Claude Desktop-compatible skill file is a markdown document with YAML frontmatter:

```markdown
---
name: {company-slug}-scheduling-demo     # kebab-case, unique per Desktop install
description: Live demo of {company}'s {pain-point-title} — automated via Claude Cowork
---

{capability instructions body}
```

Rules:
- `name` must be unique on the Claude Desktop instance. Prefix with client slug to avoid collisions.
- `description` is shown in the skill picker — make it recognisable for the prospect call context.
- No `version` required (Claude Desktop skills don't use it).
- Body begins immediately after the closing `---`. No heading required.

---

## Cowork MCP Catalog

**Native MCPs — available without wrapper, preferred for live demos:**

| MCP | Capability | Demo notes |
|---|---|---|
| Google Sheets | Read/write/create sheets, formulas | Best demo MCP — client recognises the tool |
| Google Calendar | CRUD events, availability, find times | Strong for scheduling + booking demos |
| Gmail | Read/send/search/draft, threads | Good for follow-up + notification demos |
| Google Drive | List/read/upload | Supporting role (document access) |
| HubSpot | Contacts, deals, pipeline | Sales-process demos |
| Notion | Pages, databases, search | Knowledge-base / SOP demos |
| Slack | Messages, channels, search | Internal comms demos |

**Wrapper-required — use fabrication escape hatch:**

| Tool | Use case | Fabrication line |
|---|---|---|
| Twilio | SMS send | `[Auto] SMS sent to {name} ✓` |
| Xero | Invoice / payment triggers | `[Auto] Invoice #X created in Xero ✓` |
| Trello | Card creation | `[Auto] Card created in Trello: {title} ✓` |
| Meta Ads | Campaign actions | `[Auto] Campaign updated in Meta Ads Manager ✓` |

---

## Output File Map

```
clients/{slug}/cowork-demo/
├── SKILL.md           # Claude Desktop drag-and-drop skill
│                      # Frontmatter: name, description
│                      # Body: role framing + scene + task + output spec (Sections 1–4b)
├── demo-prompt.md     # Paste-into-chat version (identical body, no frontmatter)
├── live-demo.html     # Self-contained visual artifact (generated at demo run time)
│                      # Written by the demo-time model via Write tool
│                      # APG brand styling, vanilla HTML/CSS/JS, no build step
│                      # Contains: run sheet roster grid + SMS preview cards + metric bar
│                      # Open with: open clients/{slug}/cowork-demo/live-demo.html
└── demo-brief.md      # Adam's pre-call cheat sheet
                       # Contents:
                       #   ## Demo: {title}
                       #   **Pain point:** {description}
                       #   **Quote:** "{verbatim}" — {speaker}, session {n}
                       #   **Fathom:** {fathom_url}?t={seconds} (→ {MM:SS})
                       #   **Before:** {time_cost per occurrence × frequency}
                       #   **After:** estimated {saving}
                       #   **Annual value:** ${roi_item.annual_value_aud}/yr
                       #   ---
                       #   ## Talk Track
                       #   {Opening / After output / Close from template above}
                       #   ---
                       #   ## How to Run
                       #   Option A — Claude Desktop: Drag SKILL.md into ~/Library/...
                       #   Option B — Paste: Copy demo-prompt.md into a Cowork chat
                       #   Option C — Visual: open live-demo.html in Chrome during the call
```

Re-run / multi-scenario naming: if a second scenario is added alongside, files are:
`SKILL-{plugin_slug}.md`, `demo-prompt-{plugin_slug}.md`, `demo-brief-{plugin_slug}.md`

`plugin_slug` = kebab-case of `selected_plugin.title` (e.g. "Scheduling & Staff SMS" → `scheduling-staff-sms`)
