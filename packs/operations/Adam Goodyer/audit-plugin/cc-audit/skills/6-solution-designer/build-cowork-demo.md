---
name: build-cowork-demo
description: Generate a live Cowork demo package for the client's easiest-to-demonstrate, most-expressed pain point. Outputs a Claude Desktop-compatible SKILL.md, a paste-into-chat prompt, and Adam's talk track cheat sheet.
menu-code: BC
---

# BC — Build Cowork Demo

> **Idempotent.** First run creates a hero demo package from scratch. Re-runs offer to rebuild with a new candidate, add a second scenario alongside, or cancel.

## Purpose

Take the client's audit data and produce a ready-to-run live Cowork demo — the kind Adam can load on a call and run in under 2 minutes. The demo picks the pain point the client expressed most clearly and that is the simplest to automate via Claude Cowork, then generates:

1. **`SKILL.md`** — drag into Claude Desktop's skills folder; invoke on the call
2. **`demo-prompt.md`** — paste into a fresh Cowork chat (no import needed)
3. **`demo-brief.md`** — Adam's pre-call cheat sheet: verbatim quote, Fathom link, before/after numbers, 3-sentence talk track

The demo prompt inlines all scene data (real staff names, real volumes, real current-state workflow) so the client recognises themselves in the scenario. Claude generates any intermediate artifacts (rosters, SMS strings, email drafts) live in the session.

**This is the Cowork-track parallel to BP.** RE/BA/BP build the custom-platform prototype; BC builds the live Cowork demo. They serve different conversations — BC is for "let me show you what this looks like right now" on a sales or post-audit call.

---

## Pre-flight

Load all three reference files before proceeding:
- `{project-root}/apg-audit-plugin/skills/6-solution-designer/references/cowork-demo-patterns.md` — scoring formula, scene extraction rules, prompt structure template (Sections 1–4b), fabrication rules, output file map
- `{project-root}/apg-audit-plugin/skills/6-solution-designer/references/transcript-deep-read.md` — transcript lookup pattern, window sizing, scene_bundle schema, extraction prompt block
- `{project-root}/apg-audit-plugin/skills/6-solution-designer/references/cowork-demo-html-template.md` — APG HTML shell, component fragments (roster-grid, sms-card, table-view, metric-bar), fragment-selection logic, Section 4b instruction block

Load audit data:
- Check for `clients/{slug}/03-audit/data/audit-manifest.json`. If present (v4): read domain files directly:
  - `clients/{slug}/03-audit/data/meta.json`
  - `clients/{slug}/03-audit/data/extraction.json`
  - `clients/{slug}/03-audit/data/findings.json`
  - `clients/{slug}/03-audit/data/opportunities.json`
  - `clients/{slug}/03-audit/data/strategy.json`
  - Do NOT load `architecture.json`
- For v3 files (no manifest, `_schema_version` starts with "3"): load `meta`, `extraction`, `findings`, `opportunities`, and `strategy` domains from `audit-data.json`.
- For v2 files: load the full `audit-data.json`.

Check readiness:

1. `strategic_approaches.service_tier_recommendation` exists (in `strategy.strategic_approaches.service_tier_recommendation` for v3/v4, or top-level `strategic_approaches.service_tier_recommendation` for v2) and has at least one tier (`low_ticket`, `mid_ticket`, `high_ticket`) with `plugin_cards[]` populated. If not → stop: "No plugin cards found in strategic approaches. Run Analyst [SA] first."
2. Collect all plugin cards across all tiers into a flat list. If zero → stop: "No plugin cards found."
3. Check `clients/{client_slug}/cowork-demo/` — does it already exist?
   - **First run:** proceed to Stage 1.
   - **Re-run (folder exists):** present options:
     ```
     Cowork demo already generated for {company_name}.
     Existing: {list SKILL.md / demo-prompt.md / demo-brief.md and their plugin titles}

     A) Full rebuild — re-score all candidates, pick new hero, overwrite all files
     B) Add another scenario — pick next-best candidate, emit as SKILL-{plugin_id}.md etc. alongside
     C) Cancel

     Select A, B, or C:
     ```
     Wait for response. If C → stop.

---

## Stage 1 — Candidate Scoring

Apply the scoring formula from `cowork-demo-patterns.md`.

Collect all plugin cards from `strategic_approaches.service_tier_recommendation.{low_ticket|mid_ticket|high_ticket}.plugin_cards[]`. Score each card using the plugin-card scoring formula in the patterns reference.

Build a ranked table of the top 5 candidates:

```
COWORK DEMO CANDIDATES — {company_name}

#  Plugin          Title                             Score  Tools                    Top Quote
──────────────────────────────────────────────────────────────────────────────────────────────────
1  {title}         {title}                           {n}    {tools_connected list}   "{source_quotes[0].quote snippet}"
2  ...

Recommended: #{n} — {one-line reason: e.g. "native MCPs, clearest quote, self-contained input"}
```

Show this table. Confirm: "Select a number (1–5) to package, or press Enter to accept the recommendation:"

Wait for response. Use the selected plugin card for all subsequent stages. Store it as `selected_plugin`.

---

## Stage 2 — Scene Extraction

Build the scene bundle from `audit-data.json` and `selected_plugin`. Follow the extraction table in `cowork-demo-patterns.md`.

> **Note:** Steps 2.1 and 2.2 below run first to establish the Fathom anchor and ROI numbers. Then Stage 2.5 (Deep Transcript Read) runs before steps 2.3–2.6, so that the scene bundle produced in 2.5 is available to inform character list, current-state prose, and output type decisions.

1. **Resolve the Fathom deep-link:**
   - Use `selected_plugin.source_quotes[]` — pick the quote with the strongest/most-concrete expression of the pain.
   - From `source_quotes[best].pain_point_id` → look up the full pain point in `pain_points[]`.
   - `pain_point.source_session` → `sessions[session_number]` → `sessions[].fathom_url`
   - Construct: `{fathom_url}?t={source_timestamp_seconds}`
   - Convert seconds to MM:SS for display (e.g. 2648s → 44:08)
   - Store: `fathom_link`, `verbatim_quote` (from `source_quotes[best].quote`), `speaker` (from `source_quotes[best].speaker`)

2. **Resolve before/after numbers:**
   - Use `selected_plugin.simplification_metric` as the primary before/after narrative.
   - Use `selected_plugin.time_saved_weekly_hrs` and `selected_plugin.annual_saving_aud` for the numbers table.
   - "After" estimate: typically 1 voice brief or a single paste — flag as estimated.

---

## Stage 2.5 — Deep Transcript Read

> Run this after steps 2.1–2.2 and before steps 2.3–2.6. The `scene_bundle` it produces supersedes audit-data.json as the primary source for steps 2.3–2.6 and Stage 3 prompt writing.

Follow the full procedure in `references/transcript-deep-read.md`. Summary:

1. **Collect anchors** — walk `selected_plugin.source_quotes[]` → `pain_points[]` → `meeting_references[]`, plus `change_ids[]` → `proposed_changes[]` → `linked_pain_point_ids[]` + `affected_step_ids[]`, plus relevant `tools[].meeting_references[]`. Deduplicate on `(meeting_id, timestamp_seconds)`.

2. **Resolve transcript paths** — scan `clients/{client_slug}/01-materials/meetings/*/metadata.json`; match where `metadata.fathom_url` ends with the anchor's `meeting_id` (see gotcha in reference file — do NOT use `recording_id`). Build a `meeting_id → transcript.txt` map.

3. **Compute windows** — for each anchor: `[ts - 90s, ts + 300s]`. Merge overlapping windows within the same transcript. Cap total at ~6000 tokens; drop lowest-confidence singletons if exceeded.

4. **Read transcript slices** — use the `Read` tool (or `Grep` to find line offsets first) to pull each window. Inline the raw `[MM:SS] Speaker: text` lines into context.

5. **Extract scene_bundle** — perform a structured extraction pass per the schema in `references/transcript-deep-read.md`:
   - `client_vocabulary[]` — exact terms they use
   - `actual_workflow_steps[]` — their process in their order
   - `observed_artefact_structure{}` — columns, sections, notes patterns, layout
   - `concrete_examples[]` — real names, venues, times, constraints
   - `business_rules_demonstrated[]` — rules as shown, not just stated
   - `verbatim_quotes[]` — best 3–6 lines with timestamps
   - `gaps_and_unknowns[]` — what wasn't clear (prevents fabricating details)

Hold `scene_bundle` in memory — it is the primary input to steps 2.3–2.6 and all of Stage 3.

---

## Stage 2.6 — Client Research (optional, disabled by default)

*Skip on first run. Enable manually when deeper vocabulary or visual context is needed.*

If enabled: `WebFetch` the client's `company_website` (from audit-data root) to cross-check service names, branded terminology, and real locations. Add any new terms to `scene_bundle.client_vocabulary` and any confirmed venues to `scene_bundle.concrete_examples` before proceeding.

---

3. **Build character list** (now informed by scene_bundle):
   - Primary: `scene_bundle.concrete_examples[]` where `type == "participant"` or `type == "staff"` — real names Jordan mentioned in the transcript, with their constraints.
   - Secondary: `staff_roster[]` for any additional roles not captured in the bundle.
   - Fabricate only what is genuinely missing — use `scene_bundle.gaps_and_unknowns[]` to know where fabrication is needed vs where the transcript had real data.
   - Format: `Name, Role` pairs; include any constraint noted in `concrete_examples` as a parenthetical.

4. **Build current-state workflow prose** (now from scene_bundle):
   - Use `scene_bundle.actual_workflow_steps[]` as the primary source — write in their order, using their language.
   - Use `scene_bundle.client_vocabulary[]` to ensure their exact terms appear (e.g., "run sheet" not "schedule", "cafe program" not "day program").
   - Cross-check against `selected_plugin.tools_consolidated` for completeness. If the transcript steps contradict the plugin card summary, prefer the transcript.
   - This becomes the "currently" paragraph in the role framing.

5. **Identify the output type(s):**
   - Primary: `scene_bundle.observed_artefact_structure{}` — if they showed or described a specific format (columns, layout), mirror it exactly in Section 3 output spec and the CSV/xlsx column definition.
   - Secondary: `selected_plugin.output_summary` as a fallback.
   - The output format in the prompt must reflect the artefact structure they actually use, not a generic schema.

6. **Check for wrapper-required MCPs:**
   - Use `selected_plugin.mcp_wrapper_tools[]` — these are already flagged. They get the `[Auto] ... ✓` fabrication line in the output spec.

---

## Stage 3 — Write the Demo Prompt

Use the prompt structure template from `cowork-demo-patterns.md` (Section 1–5).

Populate each section primarily from `scene_bundle` (Stage 2.5). Where the bundle has gaps, fall back to the audit-data fields listed in `cowork-demo-patterns.md`.

**Section 1 — Role framing:**
- `{company_name}`, `{function}` (derived from affected process stage)
- Current-state prose: use `scene_bundle.actual_workflow_steps[]` in sequence, using `scene_bundle.client_vocabulary[]` terms throughout. Write as 2–3 sentences in their voice.

**Section 2 — Scene data:**
- Character list: from `scene_bundle.concrete_examples[]` (real names + constraints) + any gaps filled from `staff_roster[]` or fabrication
- Business rules block: from `scene_bundle.business_rules_demonstrated[]` — these are the rules as they explained or showed them, not the tidy summary versions
- "Today's situation" paragraph: `scene_bundle.concrete_examples[]` (real venues, real volumes, real constraints), 2–4 sentences. Written so the client says "that's us."

**Section 3 — Task:**
- Output column definitions: use `scene_bundle.observed_artefact_structure.columns[]` and `notes_content_patterns[]` — the CSV/xlsx columns must mirror their actual sheet, not a generic schema
- Step sequence: infer from `scene_bundle.actual_workflow_steps[]` — what they do first, second, third
- Each step produces one discrete output

**Section 4 — Output format:**
- CSV column spec: `scene_bundle.observed_artefact_structure.columns[]` (with a Notes column that matches their `notes_content_patterns[]`)
- xlsx: invoke `xlsx` skill with filename `{client-short}-{context}.xlsx`
- Fabrication lines: `[Auto] ... ✓` for any `mcp_wrapper_tools[]`

**Section 5 — Acceptance checks:** Internal checklist (do not expose to client in the skill file). Checks should reference scene_bundle fields: e.g., "verbatim quote in Opening matches `scene_bundle.verbatim_quotes[0]`", "CSV Notes column includes: {scene_bundle.observed_artefact_structure.notes_content_patterns}".

The talk track **Opening** in `demo-brief.md` should use `scene_bundle.verbatim_quotes[0].quote` if it is richer or more specific than `selected_plugin.source_quotes[0].quote`. Include the `timestamp_mmss` for the Fathom link.

**Section 4b — Assemble Visual HTML Shell:**

1. Consult the fragment selection table in `cowork-demo-html-template.md` — pick fragments based on `scene_bundle.observed_artefact_structure`.
2. Assemble the HTML by concatenating: page-shell opening → selected body fragment(s) → metric-bar → page-shell closing.
3. Pre-fill static placeholders you know from the scene_bundle:
   - `{{RUN_TITLE}}` → `{company_name} — {selected_plugin.title}`
   - `{{DEMO_DATE}}` → the scenario date
   - `{{STAFF_COUNT}}` → integer staff count from `scene_bundle.concrete_examples[]`
   - `{{BEFORE_TIME}}`, `{{BEFORE_LABEL}}` → from `selected_plugin.simplification_metric`
   - Leave data placeholders (`{{STAFF_COLUMNS}}`, `{{TIME_ROWS}}`, `{{SMS_CARDS}}`, `{{TABLE_ROWS}}`, `{{PARTICIPANT_COUNT}}`, `{{SMS_COUNT}}`, etc.) as literal `{{PLACEHOLDER}}` text — the demo-time model fills these from the run it generates.
4. Wrap the assembled HTML with the Section 4b instruction block from `cowork-demo-html-template.md` ("Section 4b — Instruction Block"). This tells the demo-time model to fill the placeholders and write `live-demo.html`.
5. Append the complete Section 4b (instruction block + HTML shell) to the prompt body after Section 4.

This full prompt body (Sections 1–4b, including the HTML shell) is the same content used in both `SKILL.md` and `demo-prompt.md`. Write it once; it copies across.

---

## Stage 4 — Write the Three Output Files

Create `clients/{client_slug}/cowork-demo/` if it doesn't exist.

### `SKILL.md`

```markdown
---
name: {client_slug}-{plugin_slug}-demo
description: Live demo of {selected_plugin.title} for {company_name} — automated via Claude Cowork
---

{full prompt body from Stage 3 — Sections 1–4b only, not Section 5}
```

`plugin_slug` = kebab-case of `selected_plugin.title` (e.g. "Scheduling & Staff SMS" → `scheduling-staff-sms`).

### `demo-prompt.md`

```markdown
# {company_name} — {selected_plugin.title} Demo

{full prompt body from Stage 3 — Sections 1–4b only, no frontmatter, no acceptance checks}
```

### `demo-brief.md`

```markdown
# Demo Brief: {selected_plugin.title}
**Client:** {company_name}
**Plugin:** {selected_plugin.title} (covers {selected_plugin.change_ids joined})
**Generated:** {ISO date}

---

## Pain Point

**{pain_point.pain_point_id}:** {pain_point.description}

> "{verbatim_quote}"
> — {speaker}

**Fathom:** {fathom_link} (→ {MM:SS})

---

## Before / After

| | Before | After |
|---|---|---|
| Time | {before_time} | ~{after_time_estimate} |
| Annual saving | — | ${roi_annual_value}/yr |
| Tools | {current_tool_names} | Claude Cowork + {target_tools} |

---

## Talk Track

**Opening (read aloud):**
"{company_first_name_or_company}, you mentioned that ['{verbatim_quote}']. What I want to show you is exactly how that gets solved — right here, right now."

**[Run the demo — paste demo-prompt.md into Claude or invoke the skill]**

**After the output:**
"That took about 30 seconds. Previously that was {before_time}. That's {saving} back every {period} — and that's just one workflow."

**Close:**
"This isn't a mockup. That's a real output. The only difference between this and a live system is the send action would connect to your actual {tool} account."

---

## How to Run

**Option A — Claude Desktop (recommended for calls):**
1. Drag `SKILL.md` into `~/Library/Application Support/Claude/skills/`
2. Open a new Claude Desktop / Cowork chat
3. The skill is now available — type its name or trigger it from the skills menu
4. Claude will run the full demo from the scene data already embedded in the skill

**Option B — Paste (no import needed):**
1. Open `demo-prompt.md`
2. Copy the full contents
3. Paste into a fresh Claude / Cowork chat
4. Claude runs identically to Option A

---

## Acceptance Checks (run these before the call)

- [ ] Real staff names from audit data appear in the output
- [ ] Before/after numbers match the audit ROI items
- [ ] `[Auto] ... ✓` lines appear for any Twilio/send actions
- [ ] Verbatim quote in the Opening matches `{pain_point.pain_point_id}`
- [ ] Fathom link resolves to the correct moment ({MM:SS})
```

---

## Stage 5 — Write Audit-Data

Update the audit data with the new cowork demo record:
- v4: load `clients/{client_slug}/03-audit/data/architecture.json`, append to `cowork_demos[]` (create array if absent), write the full dict back to `clients/{client_slug}/03-audit/data/architecture.json`, then update `audit-manifest.json`: set `domains.architecture.updated_at` and root `updated_at`.
- v3: write into `architecture.cowork_demos[]` in `audit-data.json` (create array if absent)
- v2: write to top-level `cowork_demos[]` in `audit-data.json`

1. Append to `cowork_demos[]`:
```json
{
  "plugin_title": "{selected_plugin.title}",
  "plugin_slug": "{plugin_slug}",
  "change_ids": ["{selected_plugin.change_ids}"],
  "pain_point_id": "{pain_point_id used for Fathom link}",
  "fathom_link": "{fathom_link}",
  "output_files": [
    "clients/{client_slug}/cowork-demo/SKILL.md",
    "clients/{client_slug}/cowork-demo/demo-prompt.md",
    "clients/{client_slug}/cowork-demo/demo-brief.md",
    "clients/{client_slug}/cowork-demo/live-demo.html"
  ],
  "mcp_dependencies": ["{selected_plugin.tools_connected}"],
  "fabrication_flags": ["{selected_plugin.mcp_wrapper_tools}"],
  "scene_bundle": {
    "client_vocabulary": [],
    "actual_workflow_steps": [],
    "observed_artefact_structure": {},
    "concrete_examples": [],
    "business_rules_demonstrated": [],
    "verbatim_quotes": [],
    "gaps_and_unknowns": []
  },
  "scene_bundle_generated_at": "{ISO timestamp}",
  "generated_at": "{ISO timestamp}"
}
```

2. Update `architect_metadata`:
```json
{
  "last_bc_run": "{ISO timestamp}",
  "total_bc_runs": {increment},
  "bc_demos_generated": {count of cowork_demos[]}
}
```

---

## Stage 6 — CRM Task Update

Best-effort — never block.

1. Load `crm.project_id` from audit-data.json. If null → skip silently.
2. Find task titled "Build Cowork Demo (BC)" in `list_tasks(project_id)`.
3. `update_task_status(task_id, "Done")`
4. `create_task_comment(task_id, "Cowork demo generated for plugin: {selected_plugin.title} (covers {change_ids joined}). Pain point: {pain_point_id}. Files: cowork-demo/SKILL.md, demo-prompt.md, demo-brief.md.")`
5. Update `crm.last_synced` in audit-data.json.

---

## Stage 7 — Summary

Print to terminal:

```
COWORK DEMO GENERATED — {company_name}
────────────────────────────────────────────────────────────
Plugin:      {selected_plugin.title} (covers {change_ids joined})
Pain point:  {pain_point_id} — "{verbatim_quote}"
Fathom:      {fathom_link} (→ {MM:SS})
Before/after: {before_time} → ~{after_time} per {period}

Output files:
  clients/{client_slug}/cowork-demo/SKILL.md
  clients/{client_slug}/cowork-demo/demo-prompt.md
  clients/{client_slug}/cowork-demo/demo-brief.md
  clients/{client_slug}/cowork-demo/live-demo.html  (written at demo run time)

Run modes:
  A — Drag SKILL.md into Claude Desktop skills folder, then invoke on the call
  B — Copy demo-prompt.md and paste into any Claude / Cowork chat
  C — Open live-demo.html in Chrome for the visual artifact (written during the demo run)

Note: live-demo.html is not written by BC — it is written by the demo-time model when the
prompt runs. After running the demo once, open the file with:
  open clients/{client_slug}/cowork-demo/live-demo.html

To add another scenario: re-run BC and select option B (Add alongside).
```
