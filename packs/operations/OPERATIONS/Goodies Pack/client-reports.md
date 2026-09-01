# Client Reports

> A branded monthly report for every client: data pulled from your tools on the 1st, written up factually, rendered as a PDF that looks like your company made it.
>
> From the Operations Table at Operator Day. Built by Emil (@emilsystems, Omnifusion AI).

---

## What You End Up With

We send every client of our agency a monthly performance report. The data collection runs on a schedule, Claude writes the narrative from the numbers, and the PDF carries our design. Clients read it, forward it to their team, and stay. Retention is downstream of visibility.

This file builds you the same machine, shaped around YOUR service:

- **Collectors** that pull last month's data from wherever it lives: spreadsheets, Stripe, your CRM, your project tool, your time tracker, or numbers you type in
- **A report engine** (Python, runs locally) that turns pulled data into per-client numbers with month-over-month deltas
- **Your design, rendered to PDF.** A brand interview turns your logo, colors, and fonts into the stylesheet. Nothing of ours appears in the output.
- **A narrative layer**: Claude writes the executive summary, highlights, observations, and recommendations from the data. Factual, short, zero filler.
- **A monthly rhythm**: a cron job pulls the data on the 1st. You type `/client-reports`, skim the PDFs, and send them.
- **A skill file** that teaches Claude Code the engine, so "add a client", "restyle the cover", and "rerun June for Acme" stay one-sentence requests in every future session.

This is not a template you fill in. Claude interviews you first, then builds the engine around your actual clients and the numbers that prove YOUR work happened. A bookkeeping firm reports filings completed and hours saved. An ads agency reports spend, leads, and cost per lead. An automation studio reports workflows shipped and executions ran. A coaching business reports sessions delivered and attendance. Same machinery, your metrics.

Everything runs on your machine. Client data stays on it. Plan for 60 to 90 minutes end to end, with your first real report open on your screen when you finish.

---

## What Running It Feels Like

- **1st of the month, 9:00:** the data is already pulled (cron ran at 6:07). You type `/client-reports`. A PDF per client lands in `client-reports/reports/`.
- **9:10:** you skim each one the way the client will, then send it with a two-line email.
- **Adding client number seven:** "add Riverside Dental, their numbers live in this sheet." A config entry, not a new build.
- **Some month the numbers dip:** the report says so, plainly, next to what was done about it. Clients trust reports that survive bad months.

---

## Install

1. Save this file into your Claude Code workspace folder.
   - For a slash command: save it as `.claude/commands/client-reports.md`, then type `/client-reports`.
   - Or keep it anywhere in the workspace and tell Claude: "Read client-reports.md and build my client reporting engine."
   - New to Claude Code? A workspace is just a folder you open Claude Code in. Make a folder for your business, put this file in it, open a terminal there, and run `claude`.
2. Answer the questions. Claude builds the rest.

Requirements: Claude Code installed, Python 3.9+. Mac and Linux work out of the box. On Windows, the PDF library needs WSL; Claude sets that up with you first.

If you also picked up `operations-hub` from the Operations Table, the two connect: the hub's database becomes one more data source, and the numbers you log there flow into client reports without re-entry.

---

## Common Questions

**Do I need to be technical?** No. You answer questions about your clients and where the data lives; Claude writes every line of code.

**What does it cost to run?** Nothing beyond your Claude Code subscription on the default path. The optional always-on server version (reports generate with zero touch) costs about $6/month for the server plus LLM usage per report, typically well under a dollar per client.

**Where does client data live?** In files on your machine, under `client-reports/data/`. Nothing is uploaded anywhere. The folder is excluded from git.

**My data lives in a tool you have not heard of.** If it has a CSV export or an API, Claude wires a collector for it during setup. Worst case, a spreadsheet you keep updated becomes the source, and that still beats sending no report.

**Part of what I deliver has no numbers.** Fine. Deliverables, milestones, and context go in through a short monthly note, and the narrative sections carry them. Numbers make the report stronger; they are not an entry requirement.

**Can it email clients automatically?** It renders automatically; sending stays yours. You should see what a client sees before they do. Auto-delivery is a named later milestone, not a launch feature.

**What if a data pull fails on the 1st?** Each client is isolated. One broken source produces one flagged client and a log line, never a silently wrong report.

---

## How We Think About This

Six rules from sending these reports ourselves. They shape everything Claude builds below.

1. **Reports are retention.** Clients cancel what they cannot see working. A monthly report is the cheapest churn insurance a service business can buy.
2. **Facts, not adjectives.** The report states what happened. It never grades ("underperformed", "impressive") and never invents. A number that was not pulled stays missing and says so.
3. **The client's month, not your template.** Metrics are defined per client. Two clients of the same company can get structurally different reports because they buy different outcomes.
4. **Your brand, not ours.** Design lives in config as tokens; the layout skeleton is fixed and proven. You get our machinery wearing your identity.
5. **Pull on cadence, narrate once.** Data collection is automated and dumb. Narrative is written once a month by Claude and reviewed by you. Automation where it is safe, judgment where it matters.
6. **One engine, many clients.** Adding a client is a config entry. If adding a client ever requires new code, that code becomes a collector every future client can use.

---

# Instructions

**Claude: everything from here down is for you.** You are building the operator's client reporting engine. Work interactively: present, ask, wait. Never run all stages in one shot.

## Variables

focus: $ARGUMENTS (optional. A starting emphasis, e.g. "start with just my two biggest clients" or "my data is all in Google Sheets". Leave empty for the full interview.)

---

## Stage 0: CONTEXT (no gate)

Before asking anything:

1. Read whatever workspace context exists (skip silently if missing): `CLAUDE.md`, any `context/` files, any obvious business docs in the workspace root.
2. **If `client-reports/` already exists in this workspace:** this is an operating visit, not a rebuild. Read `client-reports/SKILL.md` and do what is asked: run the month, add a client, restyle, rewire a source, fix a pull. The stages below are for the first build only.
3. **If `operations-hub/` exists:** read its `SKILL.md` too. Reuse its client roster and metric names instead of re-asking, and offer the hub database as a data source in Stage 1.
4. **Never ask a question the context already answers.**

---

## Stage 1: INTERVIEW - Service, Clients, Numbers

Small batches, 2 to 4 questions per message. Push gently for real client names and real numbers; this becomes their config.

**Batch A - the service** (skip anything Stage 0 answered):
- What do you do for clients, in one sentence each if you have multiple offers?
- What does a client currently hear from you in a normal month, and what do they ask about?

**Batch B - the roster:**
- Which clients should get reports? Start with 1 to 3 pilots; the rest are a config entry later.
- For each pilot: name, what they pay for, and anything about the relationship worth knowing (new, at risk, expanding).

**Batch C - the numbers that prove the work** (per pilot client):
- Which 3 to 6 numbers prove your work happened this month? Offer examples across business types so they recognize theirs: hours saved, executions ran, deliverables shipped, tickets resolved, response time, leads generated, cost per lead, calls booked, sessions delivered, attendance rate, revenue collected, filings completed, posts published, rankings moved.
- For each number: is more better or less better? Any target?
- Does the work move through stages worth showing as a funnel (lead to booked, ticket to resolved, order to delivered)? Optional. Most services need metrics plus breakdowns, not a funnel; only include one where stage-to-stage drop-off is genuinely the story.
- Anything unnumbered the client must see each month (milestones, deliverables, context)? That flows in through a monthly note.

**Batch D - where the data lives** (per number):
- Which tool holds it? Menu of common answers: a Google Sheet or CSV export, Stripe, a CRM (GoHighLevel, HubSpot, Pipedrive), a project or time tool (ClickUp, Asana, Toggl), a support desk, a calendar, a chat platform export, the Operations Hub database, or "my head" (then it is typed in monthly through the note, which is a valid source).
- For API sources: confirm they can get a key or export. Collect nothing yet; note what Stage 4 will need.

---

## Stage 2: BRAND - The Design Interview

The report must look like THEIR company made it.

1. Ask for: company name as it should appear, a logo file if they have one (copy it to `client-reports/theme/`), brand colors as hex codes (or "pull them from my website or logo", then propose a palette and confirm), font preference (a named font they use, or default to a clean system stack), and the footer line (e.g. "Prepared by Northwind Automation").
2. Map their answers to the design tokens in the Report Design Spec below. Propose the full token set including a cover gradient built from their darkest brand color. Show the mapping, not just the hex codes: "cover gradient ends in your navy, metric numbers in your text color, deltas in green/red".
3. Compile the blueprint: pilot clients with their metrics and sources, plus the brand tokens.

**STOP. Present the blueprint. The operator corrects it before you build. Their metric names win every argument.**

---

## Stage 3: BUILD - Engine and Design Proof

Build the approved blueprint following the Build Spec below. Order:

1. Check Python (`python3 --version`); help install if missing. Folder skeleton, venv, `requirements.txt`, gitignore entries (`client-reports/data/`, `client-reports/reports/`, `client-reports/.venv/`, `client-reports/.env`).
2. Verify the PDF library actually renders before building anything on top: `python -c "import weasyprint"` and fix installs now (this is the one dependency with system libraries; see Build Spec).
3. Write `config.json` from the interview, `theme/base.css` from the Report Design Spec with THEIR tokens, and `engine/report.py` per the Build Spec.
4. Render the **design proof**: a sample report using clearly fictional data (client name "Sample Client", a visible "SAMPLE DATA" line in the cover meta). Open it for the operator.

**STOP. Iterate on the design proof until the operator says it looks like theirs. Cheap now, expensive after a client has seen a report.**

---

## Stage 4: WIRE - Real Data

1. Write one collector per source from Batch D, following the collector contract in the Build Spec. Creds go in `client-reports/.env`, never in config or code.
2. Test-pull the last full calendar month for each pilot client. Show the pulled numbers in chat as a plain table next to what the operator expects from the source of truth.

**STOP. The operator confirms the numbers match reality. A wrong number in a client report costs trust; catch it here.**

---

## Stage 5: FIRST REPORT

1. Aggregate the confirmed pull into `report-data.json` (deltas will appear from month two).
2. Ask for the monthly note if Batch C surfaced unnumbered deliverables ("anything the client must see for last month?").
3. Write `narrative.json` following the Narrative Rules in the Build Spec.
4. Render the real PDF and open it.

**STOP. Review together. Fix wording, ordering, and anything that reads wrong. This PDF is the standard every future month is measured against.**

---

## Stage 6: WRAP - Automation and the Skill File

1. Write `client-reports/SKILL.md`: what the engine is, the config schema, the collector contract, the engine commands, how to add a client, how to run a month, the Narrative Rules, and a dated "quirks and verified behaviors" list (empty to start). Future sessions read this before touching anything.
2. Register in the workspace `CLAUDE.md` (create if missing): a short Client Reports section with the monthly flow and a pointer to the skill file.
3. Install the pull cron (see Build Spec): on the 1st, data collection runs without Claude. Show the installed line and when it fires next.
4. Name the optional Level 2 (the always-on server version in the Build Spec appendix) and ask if they want it now or later. Later is a fine answer; the default rhythm already works.

---

## Stage 7: PROVE IT - Verify, Then Hand Over the Loop

1. Run the verification checklist (bottom of Build Spec). Fix failures before showing off.
2. Do one full live round trip: pick a pilot client, run the entire month end to end (`pull`, `aggregate`, narrative, `render`), and open the result.
3. Hand over the rhythm:
   - **1st of the month:** cron has pulled. Type `/client-reports`. Skim each PDF, then send it yourself.
   - **Any change:** say it. "Add a client", "swap the accent color", "Acme also wants ad spend in there", "rerun June for Riverside".
   - **When a pull flags a failure:** paste the log line to Claude; the collector gets fixed and the month rerun.
4. Name the next milestones in payoff order: more clients onto the engine, the Level 2 server version, auto-delivery by email once they trust the output.

---

## Report Design Spec

The design half of this kit. The skeleton is fixed and proven; every visual decision is a token. Restraint is the brand: one accent color, no emoji, no decoration that does not inform. The report should read like an instrument, not a landing page.

**Page structure, in order:**

1. **Cover** (full-bleed gradient): logo if present, company name small and letter-spaced, report title, client name in the accent color, month + "SAMPLE DATA" only on proofs.
2. **Executive Summary**: 3 to 5 sentences in a bordered block, then the metric card grid (value, label, delta chip vs last month, optional sublabel).
3. **Funnel** (only if configured): waterfall table, one row per stage with a bar, indented "stopped after X" rows between stages in the drop color.
4. **Breakdowns** (optional, from collectors): small tables, label / count / percent.
5. **Highlights** (green-edged cards) and **Observations** (primary-edged cards).
6. **Recommendations**: a short bullet list. Omit the section rather than pad it.
7. **Footer** on every page via CSS: footer text centered, page number right.

**Design tokens** (all live in `config.json` under `agency.brand`; the CSS below carries `__TOKEN__` placeholders the engine substitutes at render time):

| Token | Meaning | Neutral default |
|---|---|---|
| `__PRIMARY__` | headings, section rules, table headers | `#1e3a5f` |
| `__ACCENT__` | client name on cover, emphasis | `#3b82f6` |
| `__COVER_G1__` `__COVER_G2__` `__COVER_G3__` | cover gradient stops, dark to brand | `#0b1220` `#12203a` `#1e3a5f` |
| `__COVER_TEXT__` / `__COVER_MUTED__` | cover text | `#ffffff` / `#94a3b8` |
| `__TEXT__` / `__MUTED__` | body / secondary text | `#1e293b` / `#64748b` |
| `__CARD_BG__` / `__BORDER__` | card fill / borders | `#f8fafc` / `#e2e8f0` |
| `__GOOD__` / `__BAD__` | positive / negative deltas and drops | `#059669` / `#dc2626` |
| `__BAR_MAIN__` / `__BAR_DROP__` | funnel bars | `#3b82f6` / `#fca5a5` |
| `__FONT_STACK__` | the report font | system sans stack |
| `__FOOTER_TEXT__` | page footer | operator's footer line |

**`theme/base.css`** (copy exactly; brand values never get written into this file, only into config):

```css
/* Client Reports - base stylesheet (WeasyPrint). All double-underscore placeholders
   are substituted from config.json brand values at render time. */

@page {
    size: A4;
    margin: 2cm 2.5cm;
    @bottom-center { content: "__FOOTER_TEXT__"; font-size: 8pt; color: __MUTED__; }
    @bottom-right { content: counter(page); font-size: 8pt; color: __MUTED__; }
}
@page :first { margin: 0; @bottom-center { content: none; } @bottom-right { content: none; } }
@page cover { margin: 0; @bottom-center { content: none; } @bottom-right { content: none; } }

body { font-family: __FONT_STACK__; font-size: 10.5pt; line-height: 1.6; color: __TEXT__; }

/* Cover */
.cover-page {
    page: cover; display: flex; flex-direction: column; justify-content: center; align-items: center;
    width: 210mm; height: 297mm; padding: 4cm; box-sizing: border-box; text-align: center;
    background: linear-gradient(160deg, __COVER_G1__ 0%, __COVER_G2__ 40%, __COVER_G3__ 100%);
    color: __COVER_TEXT__;
}
.cover-logo { max-height: 22mm; max-width: 70mm; margin-bottom: 1.5cm; }
.cover-brand { font-size: 10pt; font-weight: 600; letter-spacing: 4px; text-transform: uppercase;
    color: __COVER_MUTED__; margin-bottom: 2cm; }
.cover-title { font-size: 28pt; font-weight: 800; margin: 0 0 0.5cm 0; line-height: 1.2; color: __COVER_TEXT__; }
.cover-client { font-size: 18pt; font-weight: 400; color: __ACCENT__; margin-bottom: 2cm; }
.cover-meta { display: flex; gap: 2cm; font-size: 10pt; color: __COVER_MUTED__; }

.page-break { page-break-before: always; }

/* Headings */
h2 { font-size: 16pt; font-weight: 700; color: __PRIMARY__; margin: 0 0 4px 0;
    padding-bottom: 6px; border-bottom: 2px solid __PRIMARY__; }
h3 { font-size: 12pt; font-weight: 700; color: __TEXT__; margin: 18px 0 6px 0; }
.section-subtitle { font-size: 9.5pt; color: __MUTED__; margin: 0 0 16px 0; }

/* Executive summary */
.summary-text { background: __CARD_BG__; border-left: 3px solid __PRIMARY__; border-radius: 0 6px 6px 0;
    padding: 14px 18px; margin: 16px 0; font-size: 10.5pt; line-height: 1.7; color: __TEXT__; }

/* Metric cards */
.metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 16px 0 20px 0; }
.metric-card { background: __CARD_BG__; border: 1px solid __BORDER__; border-radius: 8px;
    padding: 14px 18px; text-align: center; break-inside: avoid; }
.metric-card .label { font-size: 8.5pt; color: __MUTED__; text-transform: uppercase;
    letter-spacing: 0.5px; margin: 0; }
.metric-card .value { font-size: 20pt; font-weight: 800; color: __TEXT__; margin: 4px 0 0 0; }
.metric-card .sublabel { font-size: 8.5pt; color: __MUTED__; margin: 2px 0 0 0; }
.delta { display: inline-block; font-size: 8pt; font-weight: 700; padding: 1px 8px;
    border-radius: 10px; margin-top: 4px; background: __CARD_BG__; }
.delta-good { color: __GOOD__; border: 1px solid __GOOD__; }
.delta-bad { color: __BAD__; border: 1px solid __BAD__; }
.delta-flat { color: __MUTED__; border: 1px solid __BORDER__; }

/* Funnel waterfall */
table.funnel-table { width: 100%; border-collapse: collapse; font-size: 10pt; margin-top: 12px; }
table.funnel-table th { text-align: left; padding: 8px 4px; border-bottom: 2px solid __TEXT__;
    color: __TEXT__; font-weight: 700; }
table.funnel-table th.num { text-align: right; }
table.funnel-table td { padding: 6px 4px; border-bottom: 1px solid __BORDER__; }
tr.f-row { break-inside: avoid; }
td.f-stage { font-weight: 600; }
td.f-num { text-align: right; font-weight: 700; }
td.f-stopped-label { color: __MUTED__; font-size: 9pt; padding-left: 20px; }
td.f-stopped-num { text-align: right; color: __BAD__; font-size: 9pt; }
td.f-bar-cell { padding: 4px 16px; width: 40%; }
.bar { height: 14px; border-radius: 3px; min-width: 2px; }
.bar-main { background: __BAR_MAIN__; }
.bar-drop { background: __BAR_DROP__; }

/* Breakdown tables */
table.breakdown { width: 100%; border-collapse: collapse; margin: 12px 0 20px 0; font-size: 9.5pt; }
table.breakdown th { background: __PRIMARY__; color: __COVER_TEXT__; font-weight: 600;
    text-align: left; padding: 8px 12px; }
table.breakdown th.num { text-align: right; }
table.breakdown th:first-child { border-radius: 4px 0 0 0; }
table.breakdown th:last-child { border-radius: 0 4px 0 0; }
table.breakdown td { padding: 7px 12px; border-bottom: 1px solid __BORDER__; }
table.breakdown td.num { text-align: right; font-weight: 700; }
table.breakdown tr:nth-child(even) td { background: __CARD_BG__; }

/* Highlight / observation cards */
.card { border: 1px solid __BORDER__; border-left: 4px solid __PRIMARY__; border-radius: 0 8px 8px 0;
    padding: 12px 16px; margin: 10px 0; background: white; break-inside: avoid; }
.card-good { border-left-color: __GOOD__; }
.card p { font-size: 9.5pt; color: __TEXT__; margin: 0; line-height: 1.6; }

/* Recommendations */
ul.recs { font-size: 10pt; line-height: 1.8; color: __TEXT__; padding-left: 20px; }
ul.recs li { margin-bottom: 6px; }
```

If the operator wants structural changes beyond tokens later, add `theme/custom.css` (appended after base at render time) instead of editing base.

---

## Build Spec

The concrete machinery. Deviate only where the operator's tools force it.

**Layout**

```
client-reports/
├── requirements.txt        # weasyprint>=61
├── .env                    # source credentials, gitignored, chmod 600
├── config.json             # agency + brand + clients (the single config)
├── SKILL.md                # written in Stage 6
├── engine/report.py        # the CLI below
├── collectors/<source>.py  # one per data source, shared by all clients
├── theme/                  # base.css, optional custom.css, logo file
├── data/<client>/<YYYY-MM>/    # pulls + report-data.json + narrative.json, gitignored
├── reports/<client>/           # <client>-<YYYY-MM>.pdf (+ .html for debugging), gitignored
└── deploy/                 # only if Level 2 is chosen: systemd unit + timer
```

**WeasyPrint install** (the one dependency with system libraries): `pip install weasyprint` inside the venv. If import fails: Mac `brew install pango libffi`, Debian/Ubuntu `apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev`, Windows: use WSL. Verify with an actual import before Stage 3 continues.

**config.json** (shape, with example values):

```json
{
  "agency": {
    "name": "Northwind Automation",
    "footer_text": "Prepared by Northwind Automation",
    "brand": {
      "primary": "#1e3a5f", "accent": "#3b82f6",
      "cover_gradient": ["#0b1220", "#12203a", "#1e3a5f"],
      "cover_text": "#ffffff", "cover_muted": "#94a3b8",
      "text": "#1e293b", "muted": "#64748b",
      "card_bg": "#f8fafc", "border": "#e2e8f0",
      "good": "#059669", "bad": "#dc2626",
      "bar_main": "#3b82f6", "bar_drop": "#fca5a5",
      "font_stack": "-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
      "logo_path": "theme/logo.png"
    }
  },
  "clients": [
    {
      "slug": "riverside-dental",
      "display_name": "Riverside Dental",
      "report_title": "Monthly Performance Report",
      "service_summary": "Automated patient recall and review collection",
      "metrics": [
        {"id": "recalls_sent", "label": "Recalls Sent", "format": "number", "goal": "up"},
        {"id": "appointments_booked", "label": "Appointments Booked", "format": "number", "goal": "up"},
        {"id": "hours_saved", "label": "Staff Hours Saved", "format": "number", "goal": "up",
         "sublabel": "vs manual recall calls"},
        {"id": "reviews_collected", "label": "New Reviews", "format": "number", "goal": "up"}
      ],
      "funnel": null,
      "sources": [
        {"id": "sheet", "collector": "google_sheets", "options": {"csv_url": "...", "date_column": "date"}},
        {"id": "note", "collector": "manual_note", "options": {}}
      ],
      "narrative_notes": "Practice manager reads this; keep language non-technical."
    }
  ]
}
```

`format` is one of `number`, `currency`, `percent`, `text`. `goal` is `up`, `down`, or `none` (controls delta chip color). A `funnel`, when used: `{"title": "...", "stages": [{"id": "leads_in", "label": "New Leads"}, ...]}` with counts supplied by collectors under matching ids.

**Collector contract.** One file per source type in `collectors/`, shared across clients:

```python
def collect(options: dict, start: str, end: str) -> dict:
    """start/end: ISO dates, end exclusive (one calendar month). Read-only against the source."""
    return {
        "metrics": {"hours_saved": 41.5},          # values for metric ids this source owns
        "funnel_counts": {"leads_in": 210},        # optional, funnel stage ids
        "breakdowns": [{"title": "Executions by workflow",
                        "rows": [{"label": "Invoice chaser", "count": 320}]}],  # optional
        "records": [],                             # raw rows for the narrative, cap 2000
        "meta": {"currency": "eur"}                # optional
    }
```

Rules: credentials only from `.env`; every collector runs standalone (`python collectors/x.py --test` prints last month's result); a failure raises instead of returning zeros, and the engine isolates it per client. The `manual_note` collector just reads `data/<client>/<YYYY-MM>/note.md` (the operator's monthly note) into `records`. Common starters Claude writes on request: `google_sheets` (published CSV url or local file, month-filtered on a date column, sum/count/avg per metric), `stripe` (charges in window via API), a CRM collector for whatever they use, `operations_hub` (reads the hub's SQLite `metrics` table).

**Engine CLI** (`engine/report.py`, stdlib + weasyprint only):

```
python engine/report.py pull      <slug>|--all [--month YYYY-MM]   # run collectors, write data/<client>/<month>/<source>.json
python engine/report.py aggregate <slug>|--all [--month YYYY-MM]   # merge -> report-data.json (values, deltas, funnel, breakdowns)
python engine/report.py render    <slug>|--all [--month YYYY-MM]   # + narrative.json if present -> reports/<client>/<client>-<month>.pdf
python engine/report.py monthly   [--headless]                     # the cron entry: pull + aggregate for all (no LLM)
python engine/report.py status                                     # client x month: pulled / aggregated / narrative / pdf
```

- `--month` defaults to the previous calendar month; the window is [1st, 1st of next), UTC.
- `aggregate` resolves each metric id across the client's sources in order (first hit wins), computes deltas against the previous month's `report-data.json` when it exists, and lists unresolved metric ids in the output and on stderr. Unresolved stays null; the renderer skips the card. Never fill a default.
- `render` substitutes brand tokens into `base.css` (plus `custom.css` if present), builds the HTML sections in the Design Spec order, escapes all dynamic text, and writes the PDF with `base_url` set to the kit folder so the logo path resolves. Renders fine with no `narrative.json` (data sections only); prints a note when narrative is missing.
- `monthly` loops all clients with per-client isolation: one failure logs and flags, the rest proceed. Exit code 1 if anything failed.

**narrative.json** (written by Claude each month, never by the engine):

```json
{
  "executive_summary": "3-5 sentences.",
  "highlights": ["2-4 wins, each tied to a number."],
  "observations": ["2-4 neutral, factual observations."],
  "recommendations": ["0-4 short suggestions tied to the data."]
}
```

**Narrative Rules** (also the prompt for Level 2; put them in SKILL.md verbatim):
- Every number mentioned must exist in `report-data.json` or the pulled records. Never invent, extrapolate, or annualize.
- Factual register. Describe what happened, not what should have happened. No grades, no hype adjectives, no em dashes.
- Write for the client's reader (from `narrative_notes`), not for the operator.
- The executive summary answers in 20 seconds: what happened, the one number that matters most, what changed vs last month.
- A bad month is stated plainly next to what was done about it. Omit `recommendations` rather than pad them.

**The monthly pull cron** (Stage 6, default path; runs without Claude):

```
7 6 1 * *  cd /FULL/PATH/TO/client-reports && .venv/bin/python engine/report.py monthly >> data/cron.log 2>&1
```

Install via `crontab -e` on Mac or Linux. Mac note: if the workspace lives in Desktop, Documents, or Downloads, macOS privacy controls can block cron; grant `cron` Full Disk Access in System Settings or keep the workspace outside those folders.

**Level 2 (optional): the always-on server version.** Reports generate with zero touch on a $6/month DigitalOcean droplet; the operator only skims and sends.

1. Create the droplet (Basic, 1GB, Ubuntu 24.04 LTS). `apt update && apt install -y python3-venv libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev`.
2. Copy the folder up: `rsync -a --exclude .venv --exclude data --exclude reports client-reports/ root@<ip>:/opt/client-reports/`, then rebuild the venv there and copy `.env` separately (`scp`, then `chmod 600`).
3. Install Node and the Claude CLI for the narrative step: `apt install -y nodejs npm && npm install -g @anthropic-ai/claude-code`. Auth either with an Anthropic API key in `/etc/client-reports.env` (metered, simplest) or with `claude setup-token` and `CLAUDE_CODE_OAUTH_TOKEN` (billed to the subscription).
4. `monthly --headless` extends the monthly run per client: build a narrative prompt (the Narrative Rules + `report-data.json` + capped record samples + the monthly note), pipe it to `claude -p --output-format text` via stdin, parse the JSON object from the reply, retry once on invalid JSON, then render. If narrative still fails, render without it and flag; a data-only report beats no report.
5. systemd timer, not cron: a oneshot `client-reports.service` running `engine/report.py monthly --headless` with `EnvironmentFile=/etc/client-reports.env`, and `client-reports.timer` with `OnCalendar=*-*-01 06:07:00` and `Persistent=true`. `systemctl enable --now client-reports.timer`.
6. Getting PDFs back: `scp` them down, or rclone `reports/` to a Drive folder the operator already looks at. Sending remains human.
7. Costs, honestly: $6/month droplet plus LLM usage per report (typically well under a dollar per client per month at normal record volumes). Test with `systemctl start client-reports.service` and read `journalctl -u client-reports`.

**Verification checklist (Stage 7 gate)**
- [ ] `python -c "import weasyprint"` passes inside the venv
- [ ] Design proof PDF rendered and approved, cover marked SAMPLE DATA
- [ ] Real pull for the last full month matched the operator's source-of-truth spot check
- [ ] `report-data.json` lists zero unresolved metrics for pilot clients (or the operator accepted the gaps)
- [ ] First real PDF reviewed and approved by the operator
- [ ] `monthly` runs clean end to end; `status` shows the month complete
- [ ] Cron installed; next fire date shown to the operator
- [ ] `SKILL.md` written; `CLAUDE.md` registers the engine; `data/`, `reports/`, `.env`, `.venv` gitignored

---

## Critical Rules

- **Interactive.** Present, ask, wait at every STOP. Never run Stage 1 through 7 autonomously.
- **Small batches.** 2 to 4 questions per message.
- **Their metrics, their words.** Metric ids, labels, and section wording come from the interview. If they say "workflows shipped", no report says "deliverables".
- **Facts only in reports.** The Narrative Rules are not style advice; they are the product. A report that grades or invents gets the operator fired by their client.
- **Empty stays empty.** An unresolved metric renders as absent and is flagged to the operator, never defaulted, never estimated.
- **The operator sends, never the system.** Nothing in this kit emails a client. Rendering is automated; sending is a human decision every month.
- **Collectors are read-only.** They pull with the narrowest credentials that work (restricted or read-only API keys where offered) and never write to the source.
- **Brand lives in config.** `base.css` keeps its `__TOKEN__` placeholders forever; if a brand value appears hardcoded in CSS, that is a bug.
- **Sample data is labeled.** The design proof says SAMPLE DATA on the cover. Fictional numbers never appear in a real client's report.
- **One engine, many clients.** Adding a client touches `config.json` and maybe `.env`. New code means a new collector, written once, reusable by every client.
- **Documentation is part of done.** Without `SKILL.md` and the `CLAUDE.md` entry, the next session is blind and the build is not finished.

---

*Client Reports kit v1.0, July 2026, from the Operations Table at Operator Day. Structure by Emil (@emilsystems, Omnifusion AI). Send the report every month; it is the cheapest retention system you will ever run.*
