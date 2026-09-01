# Operations Hub

> Your whole operation visible in one dashboard, and changeable in one conversation.
>
> From the Operations Table at Operator Day. Built by Emil (@emilsystems, Omnifusion AI).

---

## What You End Up With

We run our agency this way: every client, configuration, and metric lives in one database behind one API. A dashboard sits on top so we can see everything at a glance. Claude Code is wrapped around the same API, so changing a client's setup is a sentence ("switch Acme to the new package and pause follow-ups"), not twenty minutes of clicking through tools.

This file gets you the same structure, shaped around YOUR business:

- **One database** as the single source of truth for your operations
- **A small API** over that database (this is what makes everything else possible)
- **A dashboard** (clean HTML/CSS, runs locally) that shows your clients, numbers, and pipelines in one screen
- **A skill file** that teaches Claude Code your API, so Claude becomes the operator: you ask for changes in plain language, Claude makes them, the dashboard shows them

The dashboard is the glass. Claude is the hands.

This is not a template you fill in. Claude interviews you about your business first, then designs and builds the hub around your actual clients, your actual numbers, and the words you actually use. A coaching business gets students and show-up rates. An agency gets clients and retainers. An ecom brand gets SKUs and fulfilment. Same structure, your nouns.

Everything runs on your machine. Your client data never leaves it, and it costs nothing to run. The server and dashboard ship as tested code at the bottom of this file, so Claude adapts working parts instead of writing everything from scratch.

Plan for about an hour end to end. You talk for the first 15 minutes, Claude builds the rest.

---

## What Running It Feels Like

- **Morning:** open the dashboard, ask Claude "what needs attention today?"
- **Any change:** say it. "Move Jake to stage 2 and bump his package to premium." Done, and logged.
- **Numbers time:** "log this week's revenue at 12,400 and calls at 23."
- **Friday:** "anything stale?" and "back up the hub."

---

## Install

1. Save this file into your Claude Code workspace folder.
   - For a slash command: save it as `.claude/commands/operations-hub.md`, then type `/operations-hub`.
   - Or keep it anywhere in the workspace and tell Claude: "Read operations-hub.md and build my Operations Hub."
   - New to Claude Code? A workspace is just a folder you open Claude Code in. Make a folder for your business, put this file in it, open a terminal there, and run `claude`.
2. Answer the questions. Claude does the rest.

Requirements: Claude Code installed, Python 3.9+ on your machine. Mac, Linux, or Windows. Nothing else.

If you also picked up `explore-operations` from the Operations Table, the two pair well: that one finds the bottleneck worth systemizing next, this one gives you the control panel where your operation lives.

---

## Common Questions

**Do I need to be technical?** No. You answer questions about your business; Claude writes every line of code. If you can describe your operation, you can build this.

**What does it cost to run?** Nothing beyond your Claude Code subscription. The database and server are free, open tools running on your own machine.

**I already run things in Notion / a CRM / spreadsheets.** Keep them. The hub starts as the one place you LOOK instead of six. Later, small collector scripts pull from those tools automatically. It replaces a tool only once it has earned that.

**Where does my data live?** In one file on your machine (`operations-hub/data/hub.db`). No cloud, no accounts, and the dashboard is only reachable from your own computer.

**Does it need to run all the time?** No. Start it when you sit down to work ("start my hub" is enough, Claude handles it). Your data sits safely in the file either way.

**Can my team use it?** Version one is yours. When the team needs access, the same code moves to a small $6/month server. The structure is ready for that; the move is a later conversation.

---

## How We Think About This

Five rules we learned running an agency on this structure. They shape everything Claude builds below.

1. **One source of truth.** The database holds reality. The dashboard, reports, and documents are projections of it. When something is wrong on the dashboard, you fix the data, never the HTML.
2. **See in the dashboard, change through Claude.** The dashboard stays read-only. Every change goes through Claude and the API, which means every change is logged, validated in one place, and one sentence away.
3. **Start manual, automate what you actually check.** Version one takes numbers typed in through Claude. Only after you've lived with the hub do you wire up collectors that pull from Stripe, your CRM, or your calendar, and only for the numbers you really look at.
4. **The hub grows by pull, not by push.** Add a module when a real pain asks for it, not because the menu has empty slots. Two modules used daily beat six that look impressive.
5. **The skill file is the product.** The dashboard is nice. The thing that compounds is Claude knowing your API: every future session can read your operation, change it, and build on it. Documentation is not an afterthought here, it is the interface.

---

# Instructions

**Claude: everything from here down is for you.** You are building the operator's Operations Hub. Work interactively: present, ask, wait. Never run all stages in one shot.

## Variables

focus: $ARGUMENTS (optional. A starting emphasis, e.g. "start with just KPIs for my ecom store" or "client registry first". Leave empty for the full interview.)

---

## Stage 0: CONTEXT (no gate)

Before asking anything:

1. Read whatever workspace context exists (skip silently if missing): `CLAUDE.md`, any `context/` files, any obvious business docs in the workspace root.
2. Note what the business does, the offer, the team, current priorities.
3. **Never ask a question the context already answers.** Use what you learn to make every question specific ("your retainer clients", not "your customers, if any").
4. **If `operations-hub/` already exists in this workspace:** this is a change visit, not a rebuild. Read `operations-hub/SKILL.md`, ask what they want (a new module, new fields, new records, a fix), and follow its change protocol. The stages below are for the first build only.

---

## Stage 1: INTERVIEW - Map the Operation

Ask in small batches, 2 to 4 questions per message. Push gently for real names and real numbers. This conversation produces the seed data, so specifics matter.

**Batch A - the business** (skip anything Stage 0 answered):
- What do you sell, and who buys it?
- Who is on the team, and what do they own?

**Batch B - the unit of your operation:**
- What is the unit your operation revolves around? Clients, students, projects, orders, locations, properties. Whatever you manage a roster of.
- List your current ones with their status. A pasted spreadsheet or rough list is perfect. Up to 20 or so; this becomes the real data in your hub, so the first thing you see is your business, not placeholder rows.
- What do you look up or change about them repeatedly? Package, price, posting schedule, assigned team member, cadence, stage. These become the fields and the per-record config.

**Batch C - the numbers:**
- Which 5 to 7 numbers tell you the business is healthy? Mix leading (calls booked, conversations started) and lagging (revenue, churn).
- What do you check every morning, and how many places do you have to look to see it today?
- Do any of these numbers have targets?

**Batch D - flows and sources:**
- Which recurring processes move through stages? Onboarding, delivery, hiring, content production.
- Where does operational data live today? Stripe, spreadsheets, CRM, calendar, Notion, your head.
- Which of it are you fine typing in through me for now, and which would you eventually want pulled automatically? (Note the answer. Nothing external gets wired at launch; this list becomes the collectors roadmap in Stage 5.)

If `focus` was provided, narrow the interview to it, but always cover Batch B and C at minimum. Registry plus KPIs is the core almost every business lands on.

---

## Stage 2: BLUEPRINT - Design the Hub

Compile the interview into a build proposal and present it:

1. **Entities and fields.** Their primary table in their words (`clients`, `students`, `orders`), the fields from Batch B, and which repeated-change items go into the per-record `config` JSON. If two units compete to be primary (clients and projects, say), the roster they manage week to week wins; the other becomes a linked module table.
2. **Modules.** Pick from the Module Menu below based on what they actually said. Registry + KPI tiles almost always; at most ONE more at launch. Say why each made the cut and what you left out.
3. **The KPI row.** The 5 to 7 tiles, each with source (manual for now), and target if they gave one.
4. **Dashboard sketch.** A compact ASCII layout, for example:

```
┌──────────────────────────────────────────────────┐
│  ACME OPS HUB                    updated 07:12   │
├──────────┬──────────┬──────────┬─────────────────┤
│ MRR      │ Active   │ Calls    │ Churn risk      │
│ $42,300  │ 11       │ 23/wk    │ 2 flagged       │
├──────────┴──────────┴──────────┴─────────────────┤
│ CLIENTS                                          │
│ name       status    package    last touch  ...  │
├──────────────────────────────────────────────────┤
│ ONBOARDING PIPELINE                              │
│ stage: kickoff(2) → build(1) → live(8)           │
└──────────────────────────────────────────────────┘
```

5. **What stays manual vs. pulled later.** From Batch D.

**STOP. The operator corrects the blueprint before you build. Their nouns win every argument.**

---

## Stage 3: BUILD - Database, API, Dashboard

Build exactly the approved blueprint following the Build Spec below. The server, dashboard, and run script ship as tested code in the Appendix: copy them verbatim, adapt only the marked zones. Order:

1. Check Python first (`python3 --version`, or `py -V` on Windows); help install it if missing. Then the folder skeleton with the Appendix files copied in verbatim (`run.sh`, `requirements.txt`, `server/main.py`, all three `static/` files), plus `.gitignore` entries (if the workspace is a git repo, ignore `operations-hub/data/` and `operations-hub/.venv/`).
2. `db/schema.sql` from the Appendix template, renamed to their nouns and fields. The server auto-creates `data/hub.db` from it on first start; then **seed it with the real records and numbers from the interview.**
3. Adapt the three marked zones in `server/main.py`: `BUSINESS` + `ENTITIES`, the `KPIS` list, and the sections inside `summary()`. The dashboard files stay untouched: they render whatever `/api/summary` sends, so their nouns flow through data.
4. Start it with `run.sh` (first run creates the venv itself) and confirm `/api/health` answers before moving on.

Do not present half-built work. Come back when the dashboard renders their real data.

---

## Stage 4: WRAP - Make Claude the Operator

This stage is why the hub beats a spreadsheet. Two files:

1. **`operations-hub/SKILL.md`** - the API wrapper skill. Required sections:
   - What the hub is and how to start it (`bash operations-hub/run.sh`, dashboard at `http://localhost:8300`)
   - Endpoint table: method, path, body, returns, one example call each (curl or Python)
   - Field reference per entity, including every `config` key and what it means
   - Rules: writes go through the API, archive instead of delete, missing data stays empty (never invent a value)
   - Maintenance: back up = copy `data/hub.db` to `data/backups/hub-YYYY-MM-DD.db`; restore = copy back and restart
   - **Quirks and verified behaviors**: an empty dated list to start. Any surprising API behavior discovered later gets documented here with a date. The reference carries API truth; sessions come and go.
   - Change protocol: a schema change means migration + endpoint + dashboard + this file, in the same task
2. **Register in the workspace `CLAUDE.md`** (create it if missing): a short Operations Hub section saying what it is, that the DB is the source of truth, how to start it, and that `operations-hub/SKILL.md` is the API reference every session should read before touching the hub.

---

## Stage 5: PROVE IT - Verify, Then Teach the Loop

1. Run the verification checklist (bottom of Build Spec). Fix anything that fails before showing off.
2. **Do one live round trip with the operator.** Have them open `http://localhost:8300`, then ask you for a real change in their own words ("pause Sarah", "log this week's revenue at 12,400"). Make the change through the API, have them refresh, point at the result and at the activity log entry it wrote.
3. Hand over the loop:
   - **Morning:** open the dashboard (ask Claude to start the hub if it is not running), then "what needs attention today?"
   - **Any change:** say it to Claude. Status updates, config changes, new records, this week's numbers.
   - **Weekly:** ask for anything stale (records untouched in 14 days, KPIs missing entries), then "back up the hub" (a dated copy of `data/hub.db` into `data/backups/`).
4. Name the next milestones, from their Batch D answers, in order of payoff:
   - **Collectors:** a small script per source (Stripe, calendar, CRM export) that writes into `metrics` on a schedule. Start with the one source they check most often.
   - **Next module:** whatever pain showed up in the interview but did not make the launch cut.
   - **Later, when the team needs access:** move the hub to a small VPS. Same code, different machine. Not today.

---

## Module Menu

Examples, not defaults. Nothing is included until the interview asks for it. Rename everything into the operator's vocabulary.

| Module | What the dashboard shows | What Claude changes there | Usually for |
|--------|--------------------------|---------------------------|-------------|
| **Account registry** | Every client/student/order with status, key fields, last touch | Status, package, config, notes, new records | Everyone. This is the spine. |
| **KPI tiles** | The 5-7 health numbers with targets and trend | Logs new values, corrects entries | Everyone |
| **Pipelines & tasks** | Stage counts and per-record position (onboarding, delivery, hiring) | Moves records between stages, adds tasks, marks done | Service businesses, agencies |
| **Health flags** | Records that broke their own baseline (no touch in X days, metric dropped) | Acknowledges flags, records check-ins | Retainer businesses |
| **Content calendar** | What ships when, per channel | Schedules, reorders, marks published | Creators, brands |
| **Cash view** | Invoices out, overdue, upcoming renewals | Marks paid, flags overdue | Anyone invoicing manually |
| **Support queue** | Open questions by age | Assigns, resolves, escalates | Products, communities |

Three sketches of the same structure wearing different businesses:

- **Agency:** `clients` (status, retainer, niche, config: posting cadence + assigned setter), KPIs: MRR, active clients, calls booked/wk, churn risk. Pipeline: onboarding stages.
- **Coaching / info:** `students` (cohort, program, config: check-in day + coach), KPIs: enrollments, show-up rate, completion %, renewals. Pipeline: enrollment to graduation.
- **Ecom:** `skus` (stock, supplier, config: reorder point + margin), KPIs: daily revenue, orders, refund rate, ad ROAS. Pipeline: sourcing to live listing.

---

## Dashboard Design System

The design section of this kit. Follow it exactly; restraint is the brand. `static/styles.css` in the Appendix implements this system: extend that file, never rewrite it.

**Canvas and color**
- Dark canvas by default: background `#0f1117`, surfaces `#161a22`, borders `1px solid #232837`.
- Text: `#e8eaf0` primary, `#8b93a7` secondary. Keep contrast at 4.5:1 or better.
- ONE accent color, chosen to fit their brand (ask, or pick a restrained blue `#4c8dff`). Accent is for emphasis only: active states, deltas, links. Never for decoration.
- Status pills: green `#2ecc71`, amber `#f5a623`, red `#e5484d`, each as text on a 15% opacity tint of itself. No other colors in the UI.

**Type and numbers**
- System font stack (`-apple-system, 'Segoe UI', Roboto, sans-serif`). Two weights maximum per view (400, 600).
- Scale: 12px labels (uppercase, letter-spaced, secondary color), 14px body, 16px section titles, 32-40px KPI numbers.
- All metrics use `font-variant-numeric: tabular-nums` so columns of numbers align.

**Layout**
- 8px spacing grid. Page padding 24px. Card padding 16-20px.
- Cards: surface color, 12px radius, 1px border. No shadows, no gradients, no glassmorphism.
- KPI row: CSS grid `repeat(auto-fit, minmax(220px, 1fr))`. Tables below, full width.
- Each KPI tile: label on top, big number, small delta or target line under it. Nothing else.
- Tables: text left-aligned, numbers right-aligned, 13-14px, row borders only (no zebra), generous row height (44px).

**Behavior and tone**
- A "last updated" stamp in the header. Auto-refresh every 60 seconds.
- Empty states tell the truth: "No entries yet. Add one through Claude." Never fake data.
- No emoji in the UI, no icons unless they carry meaning, no animation beyond a subtle hover on rows.
- The test: it should look like an instrument, not a landing page. If an element exists to impress rather than inform, delete it.

---

## Build Spec

The concrete stack. Deviate only if the operator's machine forces it. The commands below assume Mac or Linux; on Windows, mirror them (`run.ps1` instead of `run.sh`, `py -m venv`) rather than asking the operator to change their machine.

**Layout**

```
operations-hub/
├── run.sh              # venv activate + uvicorn on :8300
├── requirements.txt    # fastapi, uvicorn
├── SKILL.md            # written in Stage 4
├── db/schema.sql       # the only place schema lives
├── data/               # hub.db (SQLite) + backups/, gitignored
├── server/main.py      # FastAPI: API + serves static/
└── static/             # index.html, styles.css, app.js
```

**Database (SQLite, stdlib `sqlite3`)**
- Primary entity table in their noun. Standard columns: `id INTEGER PRIMARY KEY`, `name TEXT`, `status TEXT`, their 3-6 interview fields, `config TEXT` (JSON string for the repeated-change settings), `notes TEXT`, `created_at`, `updated_at`.
- `metrics`: `id, metric TEXT, date TEXT, value REAL, source TEXT DEFAULT 'manual'`. Long format, one row per metric per date.
- `activity_log`: `id, ts, actor, action, detail`. The server writes a row on EVERY mutation. This is the audit trail that makes "Claude changes things" trustworthy.
- The server sets `created_at`/`updated_at` on every write; callers never send timestamps.
- Module tables only for modules in the approved blueprint. Five tables maximum at launch.

**API (FastAPI, port 8300)**
- `GET /api/health` → `{"ok": true}`
- `GET /api/summary` → everything the dashboard needs in ONE call: KPI values with latest date AND the prior value (so tiles can show a delta), entity rows, module data, last-updated timestamp.
- Per entity: `GET /api/{entity}`, `GET /api/{entity}/{id}`, `POST /api/{entity}`, `PATCH /api/{entity}/{id}`.
- `POST /api/metrics` for logging values: `{"metric": "...", "date": "YYYY-MM-DD", "value": 123}`.
- No DELETE. Archiving is `PATCH status: "archived"`. You will thank yourself.
- Errors as `{"error": "plain sentence"}` with a proper status code.
- If 8300 is taken on their machine, pick a nearby free port and use it consistently everywhere (`run.sh`, SKILL.md, CLAUDE.md).
- Register API routes BEFORE mounting `StaticFiles(directory="static", html=True)` at `/`, or the static mount swallows `/api/*`.

**Dashboard**
- Vanilla HTML/CSS/JS. No frameworks, no build step, no CDN dependencies. `app.js` fetches `/api/summary` and renders; `setInterval` refresh at 60s.
- All three files ship in the Appendix and are business-agnostic: nouns, KPI labels, and sections arrive through the `/api/summary` payload. Extend them for a new section type; never restyle from scratch.
- Read-only. No forms, no edit buttons. Changes come through Claude. (One exception allowed if the operator insists on a quick-action; keep it to one.)

**Verification checklist (Stage 5 gate)**
- [ ] `bash run.sh` starts clean; `/api/health` returns 200
- [ ] `/api/summary` carries the operator's real seeded records and numbers
- [ ] Dashboard renders them: KPI row, registry table, chosen module
- [ ] One PATCH round trip shown live: change → refresh → visible, and `activity_log` has the row
- [ ] Restart `run.sh`; the data is still there (persistence proven, not an in-memory accident)
- [ ] `SKILL.md` exists with every endpoint documented; `CLAUDE.md` registers the hub
- [ ] `data/` and `.venv/` gitignored (if a git repo)

---

## Critical Rules

- **Interactive.** Present, ask, wait at every STOP. Never run Stage 1 through 5 autonomously.
- **Small batches.** 2 to 4 questions per message. This is a conversation, not a form.
- **Their nouns everywhere.** Schema, API paths, UI labels, SKILL.md. If they say "members", the table is `members`.
- **Real data from minute one.** Seed the interview's actual records and numbers. A hub showing placeholder rows dies the same week.
- **Empty stays empty.** Never invent a value, a default, or a plausible-looking number. Missing is honest; fabricated is poison in a source of truth.
- **Writes through the API.** You (Claude) also follow this rule. The server validates and logs in one place; do not sneak writes into the DB file directly.
- **Build only the blueprint.** Modules they did not pick do not exist, no matter how nice the menu looks.
- **Appendix code is the baseline.** Copy it verbatim, adapt only the marked zones. Rewriting working code spends the operator's hour on bugs the kit already solved.
- **Nothing external at launch.** No OAuth, no API keys, no Stripe wiring today. Collectors are the named next milestone, not a launch feature.
- **Local only.** Bind to localhost. Deployment is a later conversation.
- **Documentation is part of done.** A hub without SKILL.md and the CLAUDE.md entry is not finished, because the next session would be blind.

---

## Appendix: Drop-In Code (tested)

Verified working end to end on 2026-07-28 against Python 3.9 (the stated floor): health check, summary payload, PATCH round trip with JSON config, metric upsert on repeat dates, archive filtering with `?all=1` override, both 404 error shapes, restart persistence, and static serving. Copy each file verbatim to the path shown. Per business, only two files change: `db/schema.sql` (their nouns and fields) and the three ADAPT zones in `server/main.py`. The dashboard files never change.

The `/api/summary` contract the dashboard renders:

```json
{
  "business": "Acme Coaching",
  "updated": "2026-07-28T07:12:00",
  "kpis": [
    {"label": "MRR", "format": "money", "value": 42300, "prev": 41100, "target": 50000}
  ],
  "sections": [
    {"type": "table", "title": "Clients", "columns": ["name", "status", "stage"],
     "rows": [{"id": 1, "name": "Sarah", "status": "active", "stage": "live"}]},
    {"type": "pipeline", "title": "Onboarding",
     "stages": [{"name": "kickoff", "count": 2}, {"name": "build", "count": 1}]}
  ]
}
```

`format` is `money`, `number`, or `percent`. `prev` and `target` are optional; the tile shows a delta and a target line when they are present. Table cells in a `status` or `stage` column render as colored pills automatically.

### `run.sh` (first run creates the venv itself)

```bash
#!/usr/bin/env bash
# Start the Operations Hub. First run also creates the environment.
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  ./.venv/bin/pip install --quiet -r requirements.txt
fi
./.venv/bin/uvicorn server.main:app --port 8300 --reload
```

### `requirements.txt`

```
fastapi
uvicorn
```

### `db/schema.sql` (template: rename to their nouns)

```sql
-- Rename 'clients' and its business fields to YOUR nouns (mirror the change in ENTITIES in server/main.py).
-- id/status/config/notes/timestamps are the standard columns every hub keeps.
CREATE TABLE IF NOT EXISTS clients (
  id          INTEGER PRIMARY KEY,
  name        TEXT NOT NULL,
  status      TEXT DEFAULT 'active',
  stage       TEXT,
  package     TEXT,
  assigned_to TEXT,
  config      TEXT DEFAULT '{}',
  notes       TEXT DEFAULT '',
  created_at  TEXT,
  updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS metrics (
  id     INTEGER PRIMARY KEY,
  metric TEXT NOT NULL,
  date   TEXT NOT NULL,
  value  REAL NOT NULL,
  source TEXT DEFAULT 'manual',
  UNIQUE (metric, date)
);

CREATE TABLE IF NOT EXISTS activity_log (
  id     INTEGER PRIMARY KEY,
  ts     TEXT NOT NULL,
  actor  TEXT DEFAULT 'claude',
  action TEXT NOT NULL,
  detail TEXT DEFAULT ''
);
```

### `server/main.py`

```python
"""Operations Hub server.

Generic on purpose: CRUD, logging, and serving never change per business.
The three ADAPT zones are the only places to edit:
  ADAPT 1 - business name + entity tables
  ADAPT 2 - KPI definitions
  ADAPT 3 - dashboard sections
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent.parent
DB_PATH = BASE / "data" / "hub.db"

# ── ADAPT 1: your business name and entity tables ────────────────────────────
# Key = table name (becomes the API path: /api/clients). Values = writable columns.
# Rename to YOUR nouns here and in db/schema.sql; paths and UI follow automatically.
BUSINESS = "Acme Coaching"
ENTITIES = {
    "clients": ["name", "status", "stage", "package", "assigned_to", "config", "notes"],
}

# ── ADAPT 2: KPI tiles (metric = rows in the metrics table) ──────────────────
# format: "money" | "number" | "percent". target is optional.
KPIS = [
    {"label": "MRR", "metric": "mrr", "format": "money", "target": 50000},
    {"label": "Active clients", "metric": "active_clients", "format": "number"},
    {"label": "Calls booked / wk", "metric": "calls_booked", "format": "number", "target": 30},
    {"label": "Show-up rate", "metric": "showup_rate", "format": "percent", "target": 80},
]

app = FastAPI(title="Operations Hub")


def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    fresh = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if fresh:
        schema = BASE / "db" / "schema.sql"
        if schema.exists():
            conn.executescript(schema.read_text())
            conn.commit()
    return conn


def now():
    return datetime.now().isoformat(timespec="seconds")


def err(status, message):
    return JSONResponse({"error": message}, status_code=status)


def log(conn, action, detail=""):
    conn.execute(
        "INSERT INTO activity_log (ts, actor, action, detail) VALUES (?, 'claude', ?, ?)",
        (now(), action, detail),
    )


def row_out(row):
    d = dict(row)
    if isinstance(d.get("config"), str):
        try:
            d["config"] = json.loads(d["config"])
        except (json.JSONDecodeError, TypeError):
            pass
    return d


# Fixed routes MUST be registered before the /api/{entity} routes below.
@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/summary")
def summary():
    conn = db()
    try:
        kpis = []
        for k in KPIS:
            rows = conn.execute(
                "SELECT value FROM metrics WHERE metric = ? ORDER BY date DESC LIMIT 2",
                (k["metric"],),
            ).fetchall()
            kpis.append({
                "label": k["label"],
                "format": k["format"],
                "target": k.get("target"),
                "value": rows[0]["value"] if rows else None,
                "prev": rows[1]["value"] if len(rows) > 1 else None,
            })

        # ── ADAPT 3: the dashboard sections, top to bottom ────────────────────
        sections = [
            table_section(conn, "Clients", "clients",
                          ["name", "status", "stage", "package", "assigned_to"]),
            pipeline_section(conn, "Onboarding pipeline", "clients", "stage",
                             order=["kickoff", "build", "live"]),
        ]

        last = conn.execute("SELECT ts FROM activity_log ORDER BY id DESC LIMIT 1").fetchone()
        return {
            "business": BUSINESS,
            "updated": last["ts"] if last else now(),
            "kpis": kpis,
            "sections": sections,
        }
    finally:
        conn.close()


def table_section(conn, title, table, columns):
    rows = conn.execute(
        f"SELECT id, {', '.join(columns)} FROM {table} "
        "WHERE status IS NULL OR status != 'archived' ORDER BY updated_at DESC"
    ).fetchall()
    return {"type": "table", "title": title, "columns": columns,
            "rows": [dict(r) for r in rows]}


def pipeline_section(conn, title, table, stage_col, order=None):
    counts = {r[stage_col]: r["n"] for r in conn.execute(
        f"SELECT {stage_col}, COUNT(*) AS n FROM {table} "
        f"WHERE {stage_col} IS NOT NULL AND (status IS NULL OR status != 'archived') "
        f"GROUP BY {stage_col}"
    ).fetchall()}
    stages = order or sorted(counts)
    return {"type": "pipeline", "title": title,
            "stages": [{"name": s, "count": counts.get(s, 0)} for s in stages]}


@app.post("/api/metrics")
async def log_metric(request: Request):
    body = await request.json()
    if not all(f in body for f in ("metric", "date", "value")):
        return err(400, "metric, date, and value are required")
    conn = db()
    try:
        conn.execute(
            "INSERT INTO metrics (metric, date, value, source) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(metric, date) DO UPDATE SET value = excluded.value, source = excluded.source",
            (body["metric"], body["date"], body["value"], body.get("source", "manual")),
        )
        log(conn, f"metric {body['metric']}", f"{body['date']} = {body['value']}")
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


@app.get("/api/{entity}")
def list_rows(entity: str, all: int = 0):
    if entity not in ENTITIES:
        return err(404, f"unknown entity '{entity}'")
    conn = db()
    try:
        q = f"SELECT * FROM {entity}"
        if not all:
            q += " WHERE status IS NULL OR status != 'archived'"
        rows = conn.execute(q + " ORDER BY updated_at DESC").fetchall()
        return {entity: [row_out(r) for r in rows], "total": len(rows)}
    finally:
        conn.close()


@app.get("/api/{entity}/{row_id}")
def get_row(entity: str, row_id: int):
    if entity not in ENTITIES:
        return err(404, f"unknown entity '{entity}'")
    conn = db()
    try:
        row = conn.execute(f"SELECT * FROM {entity} WHERE id = ?", (row_id,)).fetchone()
        return row_out(row) if row else err(404, f"{entity} {row_id} not found")
    finally:
        conn.close()


@app.post("/api/{entity}")
async def create_row(entity: str, request: Request):
    if entity not in ENTITIES:
        return err(404, f"unknown entity '{entity}'")
    body = await request.json()
    fields = {k: v for k, v in body.items() if k in ENTITIES[entity]}
    if not fields:
        return err(400, "no writable fields in body")
    if isinstance(fields.get("config"), dict):
        fields["config"] = json.dumps(fields["config"])
    fields["created_at"] = fields["updated_at"] = now()
    conn = db()
    try:
        cols = ", ".join(fields)
        marks = ", ".join("?" for _ in fields)
        cur = conn.execute(f"INSERT INTO {entity} ({cols}) VALUES ({marks})",
                           tuple(fields.values()))
        log(conn, f"create {entity}/{cur.lastrowid}", json.dumps(body))
        conn.commit()
        return {"ok": True, "id": cur.lastrowid}
    finally:
        conn.close()


@app.patch("/api/{entity}/{row_id}")
async def update_row(entity: str, row_id: int, request: Request):
    if entity not in ENTITIES:
        return err(404, f"unknown entity '{entity}'")
    body = await request.json()
    fields = {k: v for k, v in body.items() if k in ENTITIES[entity]}
    if not fields:
        return err(400, "no writable fields in body")
    if isinstance(fields.get("config"), dict):
        fields["config"] = json.dumps(fields["config"])
    fields["updated_at"] = now()
    conn = db()
    try:
        sets = ", ".join(f"{k} = ?" for k in fields)
        cur = conn.execute(f"UPDATE {entity} SET {sets} WHERE id = ?",
                           (*fields.values(), row_id))
        if cur.rowcount == 0:
            return err(404, f"{entity} {row_id} not found")
        log(conn, f"update {entity}/{row_id}", json.dumps(body))
        conn.commit()
        return {"ok": True}
    finally:
        conn.close()


# Static mount stays LAST or it swallows /api/*.
app.mount("/", StaticFiles(directory=str(BASE / "static"), html=True), name="static")
```

### `static/index.html`

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Operations Hub</title>
  <link rel="stylesheet" href="/styles.css">
</head>
<body>
  <header>
    <h1 id="biz">Operations Hub</h1>
    <div id="updated" class="muted"></div>
  </header>
  <main id="app">
    <div class="card empty">Loading</div>
  </main>
  <script src="/app.js"></script>
</body>
</html>
```

### `static/styles.css`

```css
/* Operations Hub design system. Extend it; do not restyle it. */
:root {
  --bg: #0f1117;
  --surface: #161a22;
  --surface-hover: #1a1f2a;
  --border: #232837;
  --text: #e8eaf0;
  --muted: #8b93a7;
  --accent: #4c8dff;   /* the ONE accent - swap for the brand color */
  --ok: #2ecc71;
  --warn: #f5a623;
  --bad: #e5484d;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 24px;
}

h1 { font-size: 16px; font-weight: 600; letter-spacing: 0.02em; }
.muted { color: var(--muted); font-size: 12px; }

/* KPI row */
.kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 20px;
}

.kpi .label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  margin-bottom: 8px;
}

.kpi .value {
  font-size: 36px;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
}

.kpi .sub {
  font-size: 12px;
  color: var(--muted);
  margin-top: 6px;
  font-variant-numeric: tabular-nums;
}

.delta-pos { color: var(--ok); }
.delta-neg { color: var(--bad); }

/* Sections */
section.card { margin-bottom: 16px; padding: 0; overflow: hidden; }

section .section-title {
  font-size: 16px;
  font-weight: 600;
  padding: 16px 20px 0;
}

/* Tables */
table { width: 100%; border-collapse: collapse; margin-top: 8px; }

th {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  font-weight: 400;
  text-align: left;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border);
}

td {
  padding: 0 20px;
  height: 44px;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
}

tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--surface-hover); }
th.num, td.num { text-align: right; font-variant-numeric: tabular-nums; }

/* Status pills */
.pill {
  display: inline-block;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 999px;
  text-transform: capitalize;
}
.pill-ok      { color: var(--ok);   background: color-mix(in srgb, var(--ok) 15%, transparent); }
.pill-warn    { color: var(--warn); background: color-mix(in srgb, var(--warn) 15%, transparent); }
.pill-bad     { color: var(--bad);  background: color-mix(in srgb, var(--bad) 15%, transparent); }
.pill-neutral { color: var(--muted); background: color-mix(in srgb, var(--muted) 15%, transparent); }

/* Pipeline */
.pipeline {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 16px 20px 20px;
}

.stage {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
}

.stage b {
  font-weight: 600;
  color: var(--accent);
  margin-left: 8px;
  font-variant-numeric: tabular-nums;
}

.arrow { color: var(--muted); }

.empty { color: var(--muted); padding: 20px; }

@media (max-width: 600px) {
  body { padding: 12px; }
  .kpi .value { font-size: 28px; }
}
```

### `static/app.js`

```javascript
// Operations Hub dashboard. Renders whatever /api/summary sends; no per-business edits needed here.
const FMT = {
  money:   v => '$' + Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 }),
  number:  v => Number(v).toLocaleString(),
  percent: v => Number(v).toLocaleString(undefined, { maximumFractionDigits: 1 }) + '%',
};

const PILL = {
  active: 'ok', live: 'ok', paid: 'ok', done: 'ok', won: 'ok',
  paused: 'warn', pending: 'warn', 'at risk': 'warn', trial: 'warn',
  overdue: 'bad', churned: 'bad', lost: 'bad', blocked: 'bad',
};

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function fmtVal(v, format) {
  if (v === null || v === undefined) return '<span class="muted">no data</span>';
  const f = FMT[format];
  return esc(f ? f(v) : String(v));
}

function kpiTile(k) {
  let sub = '';
  if (k.value != null && k.prev != null) {
    const d = k.value - k.prev;
    const cls = d > 0 ? 'delta-pos' : d < 0 ? 'delta-neg' : '';
    const txt = (d >= 0 ? '+' : '-') + (FMT[k.format] || String)(Math.abs(d));
    sub += `<span class="${cls}">${esc(txt)}</span> vs prev`;
  }
  if (k.target != null) {
    sub += (sub ? ' &middot; ' : '') + 'target ' + fmtVal(k.target, k.format);
  }
  return `<div class="card kpi">
    <div class="label">${esc(k.label)}</div>
    <div class="value">${fmtVal(k.value, k.format)}</div>
    ${sub ? `<div class="sub">${sub}</div>` : ''}
  </div>`;
}

function cell(col, v) {
  if (v === null || v === undefined || v === '') return '<td class="muted">-</td>';
  if (col === 'status' || col === 'stage') {
    const cls = PILL[String(v).toLowerCase()] || 'neutral';
    return `<td><span class="pill pill-${cls}">${esc(v)}</span></td>`;
  }
  if (typeof v === 'number') return `<td class="num">${esc(v.toLocaleString())}</td>`;
  return `<td>${esc(v)}</td>`;
}

function tableSection(s) {
  if (!s.rows.length) {
    return `<section class="card"><div class="section-title">${esc(s.title)}</div>
      <div class="empty">No entries yet. Add one through Claude.</div></section>`;
  }
  const head = s.columns.map(c => `<th>${esc(c.replace(/_/g, ' '))}</th>`).join('');
  const body = s.rows.map(r =>
    `<tr>${s.columns.map(c => cell(c, r[c])).join('')}</tr>`).join('');
  return `<section class="card"><div class="section-title">${esc(s.title)}</div>
    <table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></section>`;
}

function pipelineSection(s) {
  const stages = s.stages.map(st =>
    `<span class="stage">${esc(st.name)}<b>${st.count}</b></span>`
  ).join('<span class="arrow">&rarr;</span>');
  return `<section class="card"><div class="section-title">${esc(s.title)}</div>
    <div class="pipeline">${stages || '<span class="empty">Nothing in flight.</span>'}</div></section>`;
}

async function render() {
  try {
    const data = await (await fetch('/api/summary')).json();
    document.getElementById('biz').textContent = data.business + ' - Operations Hub';
    document.title = data.business + ' - Operations Hub';
    document.getElementById('updated').textContent =
      'updated ' + String(data.updated).replace('T', ' ');
    const parts = [`<div class="kpis">${data.kpis.map(kpiTile).join('')}</div>`];
    for (const s of data.sections) {
      if (s.type === 'table') parts.push(tableSection(s));
      if (s.type === 'pipeline') parts.push(pipelineSection(s));
    }
    document.getElementById('app').innerHTML = parts.join('');
  } catch (e) {
    document.getElementById('app').innerHTML =
      '<div class="card empty">Hub API not reachable. Is the server running?</div>';
  }
}

render();
setInterval(render, 60000);
```

---

*Operations Hub kit v1.1, July 2026, from the Operations Table at Operator Day. Structure by Emil (@emilsystems, Omnifusion AI). Build it once, then run your business from one screen and one conversation.*
