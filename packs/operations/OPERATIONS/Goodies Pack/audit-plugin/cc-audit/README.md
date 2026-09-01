# The Audit Plugin (`cc-audit`)

The exact Claude Code plugin APG Software and Bosar Agency use to deliver client AI audits — packaged as a standalone, installable plugin. Shared free at Workless 2026 (Montenegro, 30 July).

It runs the full audit pipeline end to end: you drop meeting transcripts and documents into a client folder, and the plugin extracts every process and pain point with source quotes, researches automation opportunities with effort and ROI estimates, and assembles the client‑ready deliverable — process maps, findings, waste analysis, an AI blueprint, and a clickable prototype.

This README is the single place to understand **how the plugin works, how to run it, and how to modify it.** For the deep internal reference (schemas, conventions, gotchas), see [`CLAUDE.md`](CLAUDE.md).

---

## Table of contents

1. [How it works — the pipeline at a glance](#how-it-works--the-pipeline-at-a-glance)
2. [The five agents](#the-five-agents)
3. [Requirements](#requirements)
4. [Install](#install)
5. [Configure](#configure)
6. [The client folder — where your inputs go](#the-client-folder--where-your-inputs-go)
7. [Running an audit](#running-an-audit)
8. [Commands reference](#commands-reference)
9. [Data model — the source of truth](#data-model--the-source-of-truth)
10. [What gets produced (deliverables)](#what-gets-produced-deliverables)
11. [How to modify or extend the plugin](#how-to-modify-or-extend-the-plugin)
12. [Repository layout](#repository-layout)
13. [Standalone vs. internal (CRM) mode](#standalone-vs-internal-crm-mode)
14. [First run — audit your own business](#first-run--audit-your-own-business)
15. [Credits](#credits)

---

## How it works — the pipeline at a glance

An audit is a **sequence of five agents**, run one after another. Each agent reads the data the previous one wrote, enriches it, and hands off to the next. Nothing runs in parallel at the top level — you (or Bo) run each agent after each client session, in order.

```
 Transcripts + documents  ─►  the pipeline  ─►  client-ready deliverables

 ┌─────────────────────────────────────────────────────────────────────┐
 │  3  Process Mapper      Extract every process, pain point, waste item │
 │      (audit-extractor)  from transcripts — each cited to a quote      │
 │            │                                                          │
 │            ▼                                                          │
 │  4  Process Analyst     Research automation opportunities, estimate   │
 │      (improvement-      effort + ROI, build the 3-tier strategy       │
 │       researcher)                                                     │
 │            │                                                          │
 │            ▼                                                          │
 │  5  Generator           Render HTML deliverables from the data:       │
 │      (deliverable-      process map, findings, waste, blueprint,      │
 │       builder)          client website                                │
 │            │                                                          │
 │            ▼                                                          │
 │  6  Solution Architect  Requirements spec, architecture doc, and a    │
 │      (solution-         clickable prototype for the conversion call   │
 │       designer)                                                       │
 │            │                                                          │
 │            ▼                                                          │
 │  7  Feedback Reviewer   Human QA — ingest a review video or typed     │
 │      (feedback-         notes, map each correction to a data field,   │
 │       reviewer)         apply it with a permanent audit trail         │
 └─────────────────────────────────────────────────────────────────────┘
```

> **Why the numbers start at 3.** In the full Bosar/APG consulting workflow, stages 1–2 are the sales system (a separate plugin). This plugin is the **delivery engine** — stages 3–7, from the first discovery session through to the prototype presented at conversion. The numbering is kept so it lines up with that workflow.

Each agent is a Claude Code **skill** (in `skills/`) with a matching **subagent** definition (in `agents/`). Inside each agent are numbered **capabilities** — discrete steps you can run individually, or chain via a pipeline command. The Process Mapper's whole extraction chain, for example, runs in one trigger with `/audit:run-pipeline`.

---

## The five agents

Each agent owns a stage of the pipeline and writes only its own slice of the audit data. Capability codes (e.g. `SU`, `EI`) are the individual steps inside an agent; the full list lives in [`CLAUDE.md`](CLAUDE.md).

### 3 — Process Mapper (`3-audit-extractor`)
Extracts structured process data from meeting transcripts using a "subject‑following" methodology: every step, tool, pain point, and waste item is captured, **cited to a verbatim quote**, and confidence‑scored. Also generates follow‑up questions for gaps in the map.
Key steps: **SU** sync/ingest new transcripts · **IM** deep‑extract documents · **PR** process‑map QA (BPMN validation) · **FR** findings QA · **WR** waste QA · **RX** run the whole chain in one trigger.

### 4 — Process Analyst (`4-improvement-researcher`)
Turns the map into a plan. Synthesises proposed changes from the pain points and waste, researches the right tool for each with real pricing, estimates implementation effort in weeks, and calculates annual value with transparent ROI formulas. Builds a holistic three‑tier strategic approach and the transformation blueprint.
Key steps: **EI** extract improvements · **RI** research each change · **SA** build strategic approaches · **BO** build outlook/blueprint phases · **BR** estimate weeks + value · **VR** technical/sales/compliance verification.

### 5 — Generator (`5-deliverable-builder`)
Renders the client‑facing HTML deliverables **from the data** — it never writes HTML by hand. A single Python script (`generate.py`) produces every page, so if a deliverable looks wrong you fix the script, not a prompt. Runs progressively: you can generate a process map after session 1, before any solution data exists.
Produces: process map · findings · waste analysis · AI blueprint (scroll journey) · client website (progressive unlock) · handover zip.

### 6 — Solution Architect (`6-solution-designer`)
After the client sees the priority matrix, this agent produces the implementation‑ready artifacts: a requirements spec, an architecture document (user journeys, page structure, data models, access policies), and a **clickable Next.js prototype** using Untitled UI components. Has two tracks — a full custom‑build spec, or a lighter "Cowork demo" for the single easiest pain point.
Key steps: **RE** extract requirements · **BA** build architecture · **VA** verify coverage · **BP** build prototype · **BC** build Cowork demo.

### 7 — Feedback Reviewer (`7-feedback-reviewer`)
The human QA layer. Ingests a Loom (or local) review video or typed corrections, transcribes it, maps each piece of feedback to a **specific audit‑data field**, and shows you an approval table before changing anything. Applies approved corrections with cascading financial recalculations and a permanent, per‑round audit trail. Over time it surfaces recurring corrections to improve future audits.
Key steps: **IF** ingest feedback · **AF** apply feedback (with recalculation) · **RH** review history · **LP** learn patterns.

---

## Requirements

- **Claude Code** (desktop, CLI, or IDE) with plugin support.
- **Python 3.12+** — the generation, validation, and migration scripts run via the Bash tool.
- **Node.js** — only if you build the interactive BPMN drill‑downs or the Next.js prototype (Agent 5/6).
- **`ffmpeg`** and **`yt-dlp`** — only for Agent 7 if you ingest review videos (frame extraction + Loom download).
- A folder where client folders live (a local path or a Google Drive for Desktop mount both work).

The base extraction → analysis → deliverable flow needs only Claude Code + Python.

---

## Install

Install it like any Claude Code plugin, then run the setup skill.

1. Unzip / clone the plugin into your Claude Code plugins location, or point Claude Code at the folder.
2. In Claude Code, run:

   ```
   /audit:0-setup
   ```

   The setup wizard checks your Python dependencies, asks where your client folders should live, and writes that path into `config.yaml`.

Or paste this into Claude Code to be walked through it:

```
Read this plugin's CLAUDE.md and config.yaml. Then:
1. Ask me for my name and where my client folders should live, and update config.yaml.
2. Walk me through the files in context/ (pricing, brand voice, pipeline) — they are
   templates I need to fill in with my own business details.
3. Show me how to run my first audit with /audit:run-pipeline on a test client folder.
```

---

## Configure

Two things to set up before live client work:

**1. `config.yaml`** (machine‑specific — do not commit personal paths):

```yaml
user_name: "Your Name"            # personalises agent communication
communication_language: English

paths:
  clients_dir: "~/clients"        # absolute path where client folders live
  client_paths: {}                # optional per-client overrides (auto-populated)
```

Run `/audit:0-setup` to set `clients_dir` interactively.

**2. `context/` — replace the templates with your own business details.** These are the numbers and voice the agents use when writing client‑facing content:

| File | What to put there |
|------|-------------------|
| `context/pricing/apg-pricing.md`, `apg-service-tiers.md`, `apg-custom-build.md` | Your pricing and ROI formulas |
| `context/brand/brand-voice.md` | Your brand voice for client‑facing copy |
| `context/pipeline/apg-pipeline.md` | Your pipeline sequence and data contracts |

Ship these as your own before the plugin quotes prices or writes in your voice.

---

## The client folder — where your inputs go

Everything for one client lives in a folder under `clients_dir`. You feed the pipeline by **placing files in `01-materials/`**; the agents read from there.

```
{clients_dir}/{client-slug}/
├── 00-admin/
├── 01-materials/                 # ← YOUR INPUTS
│   ├── meetings/{YYYY-MM-DD}-{title-slug}/transcript.txt   (+ optional metadata.json)
│   ├── emails/{YYYY-MM-DD}-{subject-slug}/email.html       (+ metadata.json)
│   └── documents/                # PDFs, exports, screenshots
└── 03-audit/                     # ← THE PLUGIN'S OUTPUTS
    ├── data/                     # canonical audit data (see Data model)
    ├── deliverables/*.html       # generated client-facing pages
    └── reviews/RR-{NNN}/         # review-round source (Agent 7)
```

`clients/clients.json` is the master registry mapping each client slug to its email, portal URL, and (optionally) CRM IDs.

---

## Running an audit

Run the agents **in order**, after each client session. The typical flow:

1. **Set up once:** `/audit:0-setup`
2. **After each interview**, drop the transcript into `01-materials/meetings/…` and run the extraction pipeline:

   ```
   /audit:run-pipeline {client-slug}
   ```

   This runs the whole Process Mapper chain in one trigger — sync → ingest → process review → findings review → waste review. It's autonomous by default; add `--gate` to review each step, or flags like `--only FR,WR` / `--skip IM` / `--from PR` to target parts of it.
3. **Check where you are** at any time:

   ```
   /audit:status {client-slug}
   /audit:check-completeness {client-slug}
   ```
4. **When all sessions are done**, mark the audit `process_map_complete` (see [Data model](#data-model--the-source-of-truth)). That unlocks:
   - **Agent 4** — invoke the `4-improvement-researcher` skill to research opportunities and build the strategy.
   - **Agent 5** — invoke `5-deliverable-builder` (or it regenerates automatically, see hooks) to produce the deliverables.
   - **Agent 6** — invoke `6-solution-designer` to build the architecture and prototype for the conversion call.
5. **After an internal or client review**, invoke `7-feedback-reviewer`, hand it the review video or notes, approve the mapped corrections, and it updates the data with a full audit trail.
6. **To hand off**, package an offline bundle:

   ```
   /audit:handover {client-slug}
   ```

Agents 4–7 are invoked by activating their skill (e.g. "run the improvement researcher on brightside‑services"); Agents 3 has the shortcut commands above.

---

## Commands reference

| Command | Does |
|---------|------|
| `/audit:0-setup` | Verify prerequisites and configure `clients_dir` (run first) |
| `/audit:run-pipeline {slug}` | Run the full Process Mapper extraction chain in one trigger |
| `/audit:sync-transcripts {slug}` | Pull/ingest the latest transcripts and extract into the audit data |
| `/audit:status {slug}` | Show what's done and what's next for a client |
| `/audit:check-completeness {slug}` | Run a completeness + contradiction check on the audit data |
| `/audit:handover {slug}` | Build a zippable offline client bundle (portal + PDF + source JSON) |

Agents 4, 5, 6, and 7 are run by invoking their skill by name rather than a slash command.

---

## Data model — the source of truth

The canonical data for an audit lives in `clients/{slug}/03-audit/data/`. **HTML deliverables are derived outputs — never edit them directly.** Fix the data (or the generator script) and regenerate.

The current schema (**v4**) splits audit data into **per‑domain files**, each owned by one agent, with a manifest as the index:

```
03-audit/data/
├── audit-manifest.json    # index: version, checksums, timestamps, audit_status
├── meta.json              # client info, rates, audit_status        (Agent 3)
├── extraction.json        # processes, tools, sessions, roster       (Agent 3)
├── findings.json          # pain points, waste, questions            (Agent 3)
├── opportunities.json     # proposed changes, ROI, risks             (Agent 4)
├── strategy.json          # strategic approaches, blueprint          (Agent 4)
├── architecture.json      # requirements, architecture, prototype    (Agent 6)
└── reviews.json           # review rounds + corrections              (Agent 7)
```

Two things drive the whole system:

- **`audit_status` is the state machine.** `in_progress` means sessions are ongoing (the Generator can produce process map / findings / waste / website). Set it to `process_map_complete` when all sessions are done — this unlocks the Analyst chain and the blueprint. The Analyst refuses to run until it's set.
- **Data is append‑only by design.** Agents enrich their own domain file and never delete what another agent wrote. This is what lets the pipeline run incrementally, session by session.

The reader (`scripts/audit_reader.py`) transparently handles v2, v3, and v4 data, so every script sees the same flat dict regardless of a client's schema version. Full field‑level definitions are in `references/audit-data-schema.md`; the v4 migration notes are in `references/schema-v4/WIKI.md`.

---

## What gets produced (deliverables)

All output lands in `clients/{slug}/03-audit/deliverables/` as **self‑contained HTML**, produced by `skills/5-deliverable-builder/scripts/generate.py`:

- **Process map** — a BPMN‑style view of how the client works today.
- **Findings** — pain points with their source quotes.
- **Waste analysis** — quantified waste with the math shown.
- **AI blueprint** — a scroll‑journey narrative of the transformation and its phases.
- **Client website** — a progressive‑unlock portal tying it all together.
- **Prototype** — a clickable Next.js app (Agent 6).
- **Handover zip** — an offline bundle of the portal + a comprehensive PDF + the source audit JSON (`/audit:handover`).

An **auto‑regen hook** (`hooks/hooks.json` → `hooks/auto-regen-deliverables.sh`) re‑runs `generate.py` whenever `audit-manifest.json` is written, so deliverables stay in sync with the data.

---

## How to modify or extend the plugin

Start with [`CLAUDE.md`](CLAUDE.md) — it's the internal wiki with every convention, gotcha, and "where to look for X" table. The essentials:

- **To change what an agent extracts or how it reasons** → edit that agent's capability files in `skills/{n}-{agent}/*.md`. Each `.md` is one capability (e.g. `research-improvements.md`). The `SKILL.md` is the menu/entry point.
- **To change a deliverable's look or content** → edit `skills/5-deliverable-builder/scripts/generate.py`, **not** the agent prompt. The script owns all HTML.
- **To change the data shape** → update `references/audit-data-schema.md` and `scripts/audit_reader.py`. Read `references/schema-v4/WIKI.md` first before any schema work.
- **To add a new field to a proposed change's value** → the value dimensions (`time_saving`, `productivity_enhancement`, `risk_reduction`, `customer_experience`, `scalability`) all feed `combined_annual_value_aud`. All are optional.
- **Sub‑agent context‑packet convention** — the Extractor and Researcher dispatch sub‑agents with **filtered context packets capped at ~10 KB**, never a raw domain file. This keeps sub‑agent context constant regardless of audit size. Any new agent that dispatches sub‑agents must follow this pattern (see the "Sub‑agent context packet convention" section in `CLAUDE.md`).
- **Write ownership is strict** — one domain file per agent. Don't have Agent 4 write to Agent 3's `extraction.json` (one documented exception aside). This is what keeps the append‑only model safe.
- **Skills and agents are paired** — a new pipeline stage means a new `skills/{n}-name/SKILL.md` (with `name` + `description` frontmatter) and a matching `agents/{n}-name.md`. Missing frontmatter means the skill won't register.

---

## Repository layout

```
cc-audit/
├── .claude-plugin/plugin.json    # plugin manifest (name, version, agents, commands, skills)
├── CLAUDE.md                     # internal wiki — the deep reference
├── config.yaml                   # your machine config (paths, name)
├── agents/                       # subagent definitions (3–7)
├── skills/                       # the step-by-step capabilities each agent runs
│   ├── 0-setup/                  # install + environment verification
│   ├── 3-audit-extractor/
│   ├── 4-improvement-researcher/
│   ├── 5-deliverable-builder/    # includes generate.py + BPMN rendering
│   ├── 6-solution-designer/
│   ├── 7-feedback-reviewer/
│   └── shared/                   # shared resources (e.g. email voice)
├── commands/                     # slash commands
├── context/                      # TEMPLATES: pricing, brand voice, pipeline — replace with your own
├── references/                   # data schemas + migration wikis (v3, v4)
├── scripts/                      # plugin-level Python (audit_reader, migrations, loom/frames)
├── templates/                    # client-folder + close-page HTML templates
├── hooks/                        # auto-regen hook
└── assets/                       # logos
```

---

## Standalone vs. internal (CRM) mode

This distribution is **standalone**: transcripts, emails, and documents are placed directly into each client's `01-materials/` folder, and all CRM steps are skipped automatically. You don't need any external service to run a full audit.

Internally, Bosar/APG wire the same plugin to a CRM (Supabase via an HTTP MCP) to pull transcripts and track tasks automatically. That integration is optional and not required here — `CLAUDE.md` describes it for completeness, but with no CRM configured the pipeline runs entirely on local folders (a missing `crm.project_id` silently skips every CRM step by design).

---

## First run — audit your own business

The fastest way to learn the tool: run an audit on yourself. Record two or three interviews with your team about how work actually happens, drop the transcripts into a client folder under `01-materials/meetings/`, and run `/audit:run-pipeline`. You'll see the whole chain produce a real process map and findings.

## The playbook around it

The plugin is the delivery engine. The full playbook — the funnel, the sales system, the audit SOP, and weekly calls where we run real audits — lives inside [AI First Academy](https://aif.academy).

Built by [APG Software](https://apgsoftware.com) and [Bosar Agency](https://bosar.agency).
