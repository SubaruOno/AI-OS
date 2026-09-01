---
name: build-technical-specs
description: Generate technical_spec per proposed_change (and therefore per plugin skill) — swim-lane data, implementation phases, integration points with API doc links, and acceptance criteria. Uses sub-agents for parallel processing.
menu-code: TS
---

# Build Technical Specs (TS)

> **Idempotent.** First run generates specs for all rated changes. Re-runs only target changes missing `technical_spec` or with `technical_spec.status == "needs_review"`.
>
> **Sub-agent architecture.** Each proposed_change is specced by an independent sub-agent with its own context window, dispatched in parallel batches of 3. Sub-agents use WebSearch to find real API documentation URLs.
>
> **Plugin-aware.** Every `plugin_bundles[].skills[]` entry maps to exactly one `proposed_change` via `change_id`. Generating a `technical_spec` for that change is therefore the spec for that plugin skill. Stage 1 reports coverage grouped by plugin; Stage 4 asserts every bundled skill has a corresponding spec.

## Purpose

For each rated proposed_change (has `implementation` and `value`), generate a structured `technical_spec` that powers the Technical Appendix on the client portal. The spec breaks down HOW the solution would be built: which tools connect to what, what data flows between them, concrete implementation steps, phased delivery, and integration points with real documentation links.

Because every skill inside a plugin bundle is backed by exactly one proposed_change, this also guarantees every skill in every plugin gets its own spec — addressable in the Technical Appendix grouped under its parent plugin.

This is the bridge between the client-facing modal content (plain English) and what a developer or PM would need to actually build it.

---

## Stage 1: Pre-flight

1. Check audit data is loaded. Verify for v4 clients by checking `clients/{client_slug}/03-audit/data/audit-manifest.json`. If present (v4), read domain files directly:
   - Read `clients/{client_slug}/03-audit/data/meta.json`
   - Read `clients/{client_slug}/03-audit/data/extraction.json`
   - Read `clients/{client_slug}/03-audit/data/opportunities.json`

   If `audit-manifest.json` does not exist, fall back to v3/v2: load the full `audit-data.json`.

2. Scan changes for TS eligibility:
   ```
   TECHNICAL SPEC STATUS — {company_name}
   Total proposed changes: {n}
     has implementation + value:  {n}  — eligible for TS
     missing implementation:      {n}  — SKIP (run BR first)
     already has technical_spec:  {n}  — skip unless force re-run

   Eligible and not yet specced: {n}
   ```

3. Plugin-skill coverage report. For every `plugin_bundles[]` entry, list its skills and whether the linked change has a spec:
   ```
   PLUGIN-SKILL COVERAGE
     PLG-001 {plugin_title} ({n} skills)
       SK-001 -> CH-XXX  [SPEC OK | MISSING]
       ...
     PLG-002 {plugin_title} ({n} skills)
       ...

   Unbundled changes (no plugin_bundle):
     CH-XXX (solution_type={type})  [SPEC OK | MISSING]
   ```
   Flag any `plugin_bundles[].skills[]` entry whose `change_id` does not exist in `proposed_changes[]` as a hard error and stop.

4. Select scope:
   ```
   Scope options:
     A) All un-specced eligible changes — {n} changes
     B) Specific change by ID
     C) Re-spec specific ID (update existing technical_spec)
     D) All eligible changes (full refresh)
     E) All bundled skills only (skip unbundled changes)
   ```
   Wait for user selection.

---

## Stage 2: Build Technical Specs via Sub-Agents

### 2a. Load shared context (once)

Assemble a `ts_context` JSON object:

```json
{
  "company_name": "{from meta.json}",
  "industry_tag": "{from meta.json}",
  "tools": ["{full tools[] array from extraction.json}"],
  "staff_roster": ["{full staff_roster[] array, if present}"]
}
```

### 2b. Load reference files (once)

Read these files once and hold their content as strings:
- `apg-pm-plugin/references/cowork-plugin-architecture.md` (Cowork plugin structure and MCP patterns)
- `apg-pm-plugin/references/mcp-architecture.md` (MCP connector patterns and data flow)

### 2c. Load sub-agent schema (once)

Read `sub-agent-tech-spec.md` from this skill directory.

### 2d. Build per-change context packets

For each in-scope change, build a `ts_packet` JSON object:

```json
{
  "change": {
    "change_id": "CH-003",
    "title": "...",
    "change_type": "automate",
    "proposed_solution": "...",
    "proposed_tools": ["Twilio", "Google Sheets"],
    "affected_step_ids": ["OPS-012"],
    "stage": "operations",
    "solution_type": "cowork_plugin",
    "research": {
      "tools_researched": [
        {
          "name": "Twilio",
          "api_available": true,
          "pricing_monthly_aud": 50,
          "api_notes": "REST API, SMS and voice"
        }
      ],
      "plugin_assessment": {
        "tool_connections": ["Google Sheets", "Twilio"],
        "data_layer": "sheets",
        "complexity_tier": "simple"
      }
    },
    "implementation": {
      "weeks_label": "1-2 weeks",
      "dev_hours": 24,
      "pm_hours": 4
    },
    "modal_content": {
      "how_it_works": "...",
      "what_we_will_build": "..."
    }
  },
  "affected_steps": [
    {
      "step_id": "OPS-012",
      "title": "...",
      "owner": "...",
      "tool_used": "..."
    }
  ]
}
```

**Filtering rules:**
- `research`: include only `tools_researched[]` and `plugin_assessment` (not `industry_landscape`, `gaps[]`, etc.)
- `affected_steps`: filter by `affected_step_ids`; include `step_id`, `title`, `owner`, `tool_used`
- Keep packet under 8KB

### 2e. Dispatch sub-agents in batches

Group eligible changes into batches of 3. For each batch, dispatch all sub-agents simultaneously in a single message:

```
Agent({
  description: "TS spec — {change_id} {title} — {client_slug}",
  model: "sonnet",
  prompt: [
    "[full content of sub-agent-tech-spec.md]",
    "",
    "## Shared Company Context",
    "[ts_context as JSON]",
    "",
    "## Cowork Plugin Architecture Reference",
    "[cowork-plugin-architecture.md content]",
    "",
    "## MCP Architecture Reference",
    "[mcp-architecture.md content]",
    "",
    "## This Proposed Change",
    "[ts_packet as JSON]"
  ].join("\n")
})
```

**Wait for all sub-agents in the batch before dispatching the next.**

Print progress after each batch:
```
  BATCH {n}/{total_batches} COMPLETE
    {change_id}: {n} steps, {n} phases, {n} integration points, {n} acceptance criteria
    ...
```

---

## Stage 3: Merge Results

Maintain a `corrections_log[]` array across all sub-agents (used for the Stage 4 report).

For each completed sub-agent:

1. Parse the returned JSON.

2. Merge `technical_spec` into the corresponding proposed_change:
   ```
   proposed_changes[change_index].technical_spec = {returned technical_spec}
   ```

3. If `parent_corrections` is present and non-empty, process each correction:

   **Allowed field path whitelist** (reject anything not in this list):
   - `implementation.primary_tool`
   - `implementation.approach`
   - `implementation.risks_summary`
   - `implementation.weeks_rationale`
   - `research.plugin_assessment.tool_connections[N].connection_type`
   - `research.plugin_assessment.tool_connections[N].authentication`
   - `research.plugin_assessment.tool_connections[N].notes`
   - `research.plugin_assessment.complexity_notes`
   - `research.feasibility_notes`
   - `modal_content.headline`
   - `modal_content.the_problem`
   - `modal_content.the_solution`
   - `modal_content.the_value`
   - `modal_content.what_we_build`
   - `modal_content.risks_and_notes`

   For each correction `{ field_path, original_value, corrected_value, reason }`:

   a. **Validate path.** If `field_path` is not in the whitelist, append to corrections_log with status `REJECTED — not in whitelist` and skip.

   b. **Resolve path.** Traverse the proposed_change object using dot-notation. For `[N]` segments (e.g., `tool_connections[0]`), parse the integer index and access that array element. If the path does not resolve (missing key or index out of bounds), append with status `SKIPPED — path not found` and skip.

   c. **Idempotency check.** Compare the current value at the resolved path to both `original_value` and `corrected_value`:
      - If current value == `corrected_value` (exact match): append with status `SKIPPED — already corrected` and skip.
      - If current value does not match `original_value` (exact match for short values under 30 chars; substring match for longer values): append with status `SKIPPED — field modified since TS research (current: {current truncated to 60 chars})` and skip.

   d. **Apply.** Set the value at the resolved path to `corrected_value`. Append to corrections_log with status `APPLIED` and record `{ change_id, field_path, before: original_value, after: corrected_value, reason }`.

4. Mark sub-agent failures explicitly:
   ```
   proposed_changes[change_index].technical_spec = { "status": "failed", "error": "..." }
   ```

---

## Stage 4: Save and Report

1. Write the updated `opportunities.json` back to `clients/{client_slug}/03-audit/data/opportunities.json`
2. If v4, update `audit-manifest.json` with `domains.opportunities.updated_at = now()`
3. Print summary:

```
TECHNICAL SPECS COMPLETE — {company_name}
  Generated: {n} technical_specs
  Skipped:   {n} (already had spec)
  Failed:    {n}

Average: {n} steps, {n} integration points per change

Next step: run generate.py --output client-website to render the Technical Appendix.
```

4. Plugin-skill coverage assertion. After write, re-scan `plugin_bundles[]` and confirm every `skills[].change_id` resolves to a proposed_change with a non-failed `technical_spec`. Print:

```
PLUGIN-SKILL COVERAGE — POST-RUN
  PLG-001 {plugin_title}: {n}/{n} skills specced
  PLG-002 {plugin_title}: {n}/{n} skills specced
  ...

  Unbundled changes specced: {n}/{n}

  Status: ALL BUNDLED SKILLS COVERED   (or)   GAPS — see below:
    PLG-XXX SK-YYY -> CH-ZZZ: {missing | failed reason}
```

If any bundled skill is missing or failed, the run is incomplete — surface it loudly and recommend re-running TS scope C on the affected change_ids.

4. If `corrections_log[]` contains any APPLIED entries, print:

```
PARENT FIELD CORRECTIONS — {company_name}
TS sub-agents identified and corrected {n} field(s) that contradicted their research findings.

| Change | Field | Before | After | Reason |
|--------|-------|--------|-------|--------|
{one row per APPLIED entry — truncate Before/After to 60 chars with "..."}
```

5. If `corrections_log[]` contains any SKIPPED or REJECTED entries, print:

```
CORRECTIONS SKIPPED / REJECTED:
{one line per entry: "  {change_id} | {field_path} | {status}"}
```

If `corrections_log[]` is empty, print nothing about corrections.

---

## CRM Task Update

After completing TS, update the CRM task best-effort:
- Task title: "Build Technical Specs (TS)"
- Status: "Done"
- Comment: "Generated technical_spec for {n} proposed changes. {n} integration points with API docs. {n} swim-lane diagrams."
