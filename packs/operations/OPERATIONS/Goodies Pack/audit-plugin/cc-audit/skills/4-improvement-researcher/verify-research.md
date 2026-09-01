---
name: verify-research
description: Comprehensive multi-agent audit of all research output. Four parallel sub-agents (Technical, Sales, Compliance, Text Quality) plus a deterministic rendered-deliverable lint each produce structured findings that are triaged, resolved, and applied to the audit domain files and deliverables.
menu-code: VR
---

# Verify Research (VR)

> **Orchestration capability.** Runs a comprehensive quality audit across all analyst output before client presentation. Three independent sub-agents run in parallel, each with their own review lens. The parent consolidates findings, resolves them, and applies corrections.

## Purpose

By the time VR runs, the analyst pipeline has generated proposed changes, tool research, strategic approaches, value calculations, modal content, and cost estimates. This is the highest-stakes output: it drives the client portal, presentation, and conversion decision. A single research pass inherits whatever blind spots the model had. VR fixes this with **three independent sub-agents**:

1. **Technical Research Review** -- Are all claims evidence-backed? Are tool recommendations current? Are integration assumptions feasible? Are pricing figures accurate?
2. **Sales Effectiveness Review** -- Does this read like a high-ticket consultancy deliverable? Is the value proposition clear? Are we selling the outcome, not the tool?
3. **Data Compliance Review** -- Do the numbers add up? Are we contradicting ourselves anywhere? Do extraction data, opportunities, strategies, and modal content all tell the same story?
4. **Text Quality Review** -- Does all client-facing text pass the APG brand voice standard? No em dashes, no forbidden words, no AI-sounding language, no parallel structure.

**When to run:** After [BR] Build & Rate (ideally the last step before generating deliverables). Can also re-run after any SA/BR corrections.

---

## Stage 1: Pre-flight

### 1a. Load all data

Check for `clients/{client_slug}/03-audit/data/audit-manifest.json`. If present (v4), read domain files directly:
- Read `clients/{client_slug}/03-audit/data/meta.json`
- Read `clients/{client_slug}/03-audit/data/extraction.json`
- Read `clients/{client_slug}/03-audit/data/findings.json`
- Read `clients/{client_slug}/03-audit/data/opportunities.json`
- Read `clients/{client_slug}/03-audit/data/strategy.json`
- Do NOT read `architecture.json`

If `audit-manifest.json` does not exist, fall back to v3/v2 behavior: load the full `audit-data.json` file.

Load from the domain files (or `audit-data.json` for v2 fallback):
- `proposed_changes[]` -- all changes with research, implementation, value, modal_content
- `strategic_approaches` -- service tier recommendation, roadmap
- `processes[]`, `pain_points[]`, `optimisations[]`, `waste_items[]` -- extraction data
- `roi_items[]` -- value calculations
- `tools[]` -- current tool inventory
- `blended_hourly_rate_aud` -- client hourly rate
- `contact` -- company context
- `business_metrics[]` -- KPIs

Also load: `${CLAUDE_PLUGIN_ROOT}/context/pricing/apg-pricing.md` for APG rate validation.

Also load: `${CLAUDE_PLUGIN_ROOT}/context/brand/brand-voice.md` — specifically the "Master Forbidden Words List", "Forbidden Phrases" table, and "Structural Anti-Patterns" sections. This is injected into the text quality sub-agent.

### 1b. Quick health check

```
VR PRE-FLIGHT -- {company_name}

DATA INVENTORY
  Proposed changes:     {n} ({n} with research, {n} with value, {n} with modal)
  Strategic approaches: {present|absent}
  Pain points:          {n}
  Waste items:          {n}
  Optimisations:        {n}
  Processes:            {n} across {stages covered}

MISSING PREREQUISITES
  {List any critical gaps, e.g., "0 proposed_changes have modal_content" -> run BR first}
```

If critical gaps exist, warn and suggest running the missing capability first. Proceed if data is substantially complete.

---

## Stage 2: Dispatch Three Review Lenses

### 2a. Prepare audit data payload

Build a pruned payload from the loaded audit data for the sub-agents. Include:
- `proposed_changes[]` (full, with research, implementation, value, modal_content)
- `strategic_approaches` (full)
- `processes[]` (full)
- `pain_points[]` (full)
- `optimisations[]` (full)
- `waste_items[]` (full)
- `roi_items[]` (full)
- `tools[]` (full)
- `blended_hourly_rate_aud`
- `contact`
- `business_metrics[]`
- `staff_roster[]`

Exclude (saves context space):
- `ingestion_manifest` (tracking only)
- `crm` (IDs only)
- `follow_up_questions[]` (already answered)

Include a trimmed version of `sessions[]` — the compliance sub-agent needs it to verify meeting_references:
- Include per session: `session_number`, `date`, `fathom_url`, `fathom_meeting_id`, `stages_covered`
- Exclude: `key_findings`, `questions_raised`, `transcript_file` (large fields not needed for reference verification)

### 2b. Load sub-agent schemas (once)

Read all four schema files from this skill directory:
- `sub-agent-verify-technical.md`
- `sub-agent-verify-sales.md`
- `sub-agent-verify-compliance.md`
- `sub-agent-verify-text-quality.md`

### 2c. Dispatch all four lenses simultaneously

Send all four Agent() calls in a single message so they run in parallel:

```
Agent({
  description: "VR technical lens -- {client_slug}",
  model: "sonnet",
  prompt: [
    "[full content of sub-agent-verify-technical.md]",
    "",
    "## APG Pricing Reference",
    "[apg-pricing.md content]",
    "",
    "## Full Audit Data",
    "[pruned audit data as JSON]"
  ].join("\n")
})

Agent({
  description: "VR sales lens -- {client_slug}",
  model: "sonnet",
  prompt: [
    "[full content of sub-agent-verify-sales.md]",
    "",
    "## Full Audit Data",
    "[pruned audit data as JSON]"
  ].join("\n")
})

Agent({
  description: "VR compliance lens -- {client_slug}",
  model: "sonnet",
  prompt: [
    "[full content of sub-agent-verify-compliance.md]",
    "",
    "## Full Audit Data",
    "[pruned audit data as JSON]"
  ].join("\n")
})

Agent({
  description: "VR text quality lens -- {client_slug}",
  model: "sonnet",
  prompt: [
    "[full content of sub-agent-verify-text-quality.md]",
    "",
    "## Brand Voice Reference",
    "[content of brand-voice.md — Master Forbidden Words List, Forbidden Phrases table, and Structural Anti-Patterns sections]",
    "",
    "## Full Audit Data",
    "[pruned audit data as JSON]"
  ].join("\n")
})
```

Wait for all four to complete.

### 2d. Collect results

For each sub-agent result:
1. Parse the returned JSON
2. If unparseable or `parse_error` is not null: log the failure, record the lens as failed, continue
3. Extract the `findings[]` array

Print per-lens summary as each completes:
```
  TECHNICAL:     {n} findings ({n} HIGH, {n} MEDIUM, {n} LOW)
  SALES:         {n} findings ({n} HIGH, {n} MEDIUM, {n} LOW)
  COMPLIANCE:    {n} findings ({n} HIGH, {n} MEDIUM, {n} LOW)
  TEXT QUALITY:  {n} findings ({n} MEDIUM, {n} LOW)
```

If a lens failed, note it:
```
  !! {lens} lens sub-agent failed -- re-run VR to retry
```

---

## Stage 2.5: Rendered Deliverable Lint (deterministic)

The four review lenses only ever see the JSON data payload. Many client-visible defects are introduced by the **deliverable builder** when it renders that data into HTML (separators, escaping, templating) and never exist in the data at all — so the lenses are structurally blind to them. This stage closes that gap with a deterministic regex scan of the actual rendered deliverables. It is mechanical, not LLM-based, so it is cheap and reliable. Run it every VR pass.

### 2.5a. Locate deliverables

Scan every `.html` file in `clients/{client_slug}/03-audit/deliverables/` (top level — the numbered and non-numbered variants: `blueprint.html`, `5-blueprint.html`, `client-website.html`, `1-client-website.html`, `findings.html`, etc.). If the folder doesn't exist yet (deliverables not generated), skip this stage and note it.

### 2.5b. Defect patterns

For each file, flag:

| Pattern | Regex | Why it's a defect | Severity |
|---|---|---|---|
| Double-escaped entity | `&amp;(mdash|ndash|nbsp|rsquo|lsquo|ldquo|rdquo|hellip|amp|quot|#\d+);` | Renders as visible literal text (e.g. on-screen `&mdash;`). Always wrong. | HIGH |
| Dash entity in a JS string assigned via `.textContent`/`.innerText` | entity inside a quoted JS string that is later set as text content | Renders literally because textContent does not decode entities | HIGH |
| Raw em/en dash in visible text | `—` or `–` between word characters in a text node | Off brand voice (no em dashes in APG output) | MEDIUM |
| Stray entity in a visible-text position where a real character was intended | `&mdash;`/`&ndash;`/`&hellip;` in element text | Usually fine via innerHTML, but flag clusters for review | LOW |

Note: a `&mdash;` inside element `innerHTML` (static HTML body) renders correctly as `—` and is only a MEDIUM brand-voice issue, not a parsing error. The HIGH cases are the double-escape and the textContent-string cases, which produce visible garbage.

A ready-made scan (run via Bash, adjust the path):

```python
import re, glob, os
DELIV = "clients/{client_slug}/03-audit/deliverables"
DOUBLE = re.compile(r'&amp;(?:mdash|ndash|nbsp|rsquo|lsquo|ldquo|rdquo|hellip|amp|quot|#\d+);')
DASH   = re.compile(r'—|–|&mdash;|&ndash;|&#8212;|&#8211;')   # em/en dashes in any form
findings = []
for f in sorted(glob.glob(os.path.join(DELIV, "**/*.html"), recursive=True)):
    if "/materials/" in f:        # skip client-supplied source material, not APG copy
        continue
    t = open(f, encoding="utf-8").read()
    for m in re.finditer(DOUBLE, t):                       # HIGH: guaranteed visible garbage
        s = max(0, m.start()-40)
        findings.append(("HIGH", "double_escaped_entity", os.path.basename(f), t[s:m.end()+20].replace("\n"," ")))
    n_dash = len(DASH.findall(t))                          # MEDIUM: APG policy is zero em/en dashes
    if n_dash:
        findings.append(("MEDIUM", "em_dash_in_deliverable", os.path.basename(f), f"{n_dash} em/en dash(es) — APG uses none"))
for sev, cat, fn, ctx in findings:
    print(sev, cat, fn, "::", ctx)
print(f"\n{len(findings)} render finding(s)")
```

Replacement guidance for `em_dash_in_deliverable`: em dash → comma in prose, colon for a title/label apposition (e.g. `Layer 3: AI`), and hyphen for numeric ranges (`1-2 weeks`). Never re-encode to `&mdash;`.

### 2.5c. Emit findings

Convert each hit into a finding and merge it into the consolidated list in Stage 3 with `review_type: "deliverable_lint"`:

```json
{
  "finding_id": "DL-001",
  "review_type": "deliverable_lint",
  "severity": "HIGH",
  "category": "html_render_defect",
  "file": "5-blueprint.html",
  "evidence": "the matched text with surrounding context",
  "occurrences": 11,
  "description": "Double-escaped entity &amp;mdash; renders as literal text in the Effort stat",
  "recommendation": "Decode and apply style rule, then fix the builder template so regeneration does not reintroduce it"
}
```

### 2.5d. Resolve render defects

For each defect:
1. **Fix the artifact** — correct the rendered HTML directly so the deliverable in front of the client is right now.
2. **Fix the root cause** — a render defect is almost always a builder-template bug in `5-deliverable-builder/scripts/generate.py`. Find the template line producing it (e.g. an entity used as a separator *inside* an `escape()`/`html.escape()` call) and fix it there too, otherwise the next `[GB]`/`[GW]` regeneration reintroduces the defect. If the builder fix is out of scope for this run, record it as a DEFERRED item naming the exact file and line.
3. **Decode, don't re-encode** — replace an entity with the real character, then apply the relevant brand-voice rule (e.g. decode `&mdash;` → `—` → remove the em dash entirely). Never "fix" a double-escape by collapsing `&amp;mdash;` to `&mdash;`; that just downgrades the bug.

Track resolved render defects under `text_quality.render_defects_fixed` in the verification metadata (Stage 4b).

---

## Stage 3: Triage & Resolution

### 3a. Consolidate findings

Merge all findings from the three lenses into a single list, sorted by severity (HIGH -> MEDIUM -> LOW).

```
FINDINGS SUMMARY -- {company_name}

  CRITICAL (must fix before presentation):
    {n} HIGH findings across {n} changes

  IMPORTANT (should fix):
    {n} MEDIUM findings

  MINOR (nice to fix):
    {n} LOW findings

  BY REVIEW TYPE:
    Technical:  {n} findings ({n} HIGH)
    Sales:      {n} findings ({n} HIGH)
    Compliance: {n} findings ({n} HIGH)
```

### 3b. New finding category resolutions

The following categories are generated by the updated sub-agents. Apply the default resolution when triaging:

| Category | Severity | Default resolution |
|---|---|---|
| GAP_NOT_ACKNOWLEDGED | MEDIUM | Update `research.feasibility_notes` to reference the gap |
| NEW_GAP_DISCOVERED | MEDIUM | Flag for re-run of EI when gap is resolved; annotate change with note |
| RESEARCH_ON_BLOCKED | HIGH | Add comprehensive gap documentation to `research.feasibility_notes` |
| UNADDRESSED_CONTROL_GAP | HIGH | EI must be re-run to add a change for this control gap OR document explicitly why it is excluded |
| MECHANISM_MISMATCH | HIGH | Update `proposed_solution` to correctly describe the automation target |
| INTEGRATION_PAIR_MISMATCH | HIGH | Update `research.integration_pair` to match `proposed_tools[]` |
| ALREADY_AUTOMATED | MEDIUM | Verify with client; if confirmed automated, remove change or repurpose |
| VOLUME_IGNORED | HIGH | Recalculate using volume-adjusted formula |
| MODAL_VOLUME_MISMATCH | HIGH | Rewrite modal content with correct volume-adjusted figures |
| LOW_CONFIDENCE_VOLUME | MEDIUM | Add caveat to modal content and plugin card |
| html_entity | MEDIUM (HIGH if double-escaped) | Decode the entity to its real character in the data field, then apply the brand-voice rule (Check #1/#5 of text-quality lens) |
| html_render_defect | HIGH | Fix the rendered artifact AND the builder template in `5-deliverable-builder/scripts/generate.py` (Stage 2.5d). Decode, never re-encode |

### 3c. Resolution

For each finding, starting with HIGH severity:

1. **If `requires_web_research: true`:** Run targeted WebSearch to verify/correct the claim
2. **If formula error:** Recalculate and show the corrected value
3. **If contradiction:** Determine which source is authoritative (extraction data > analyst assumptions) and correct the other
4. **If generic language:** Rewrite using client-specific data from extraction
5. **If sales issue:** Reframe using the high-ticket best practice principles
6. **If text quality issue (TQ findings):** Apply the `recommendation` text directly to the field specified in `finding.field`. For `proposed_changes[]` fields, look up the change by `finding.change_id` and patch the exact nested path (e.g., `modal_content.the_solution`). For strategic approaches fields, patch the nested path in `strategic_approaches`.
7. **If `category: "empty_source_evidence"`:** Reconstruct `source_evidence[]` for the affected change. Walk `linked_pain_point_ids` and `linked_waste_item_ids`: for each, pull `(source_quote, speaker, source_session, source_timestamp_seconds)` from `pain_points[]` / `waste_items[]`, then resolve `fathom_url = sessions[source_session].fathom_url + "?t=" + source_timestamp_seconds`. De-dupe by `(source_session, source_timestamp_seconds)`, keep ≤8 entries. If zero citations are available after reconstruction, downgrade change `confidence` to LOW and add a note to `proposed_solution`.
8. **If `category: "broken_source_ref"`:** Remove the invalid entry from `source_evidence[]`. If the array becomes empty, treat as `empty_source_evidence` and reconstruct.
9. **If `category: "modal_stat_untraced"`:** Add a note in the finding log. Flag the change for BR re-run if the untraced figure is central to the value proposition. Do not delete the number — the VR run cannot confirm whether the number is right or wrong; only that it cannot be traced to a data field.
10. **If `category: "meeting_ref_invalid"`:** Remove the invalid meeting_reference entry. If the change has valid `source_evidence[]` entries, rebuild meeting_references from those.

Record resolution:

```json
{
  "finding_id": "TR-001",
  "resolution": "corrected | verified_accurate | rewritten | deferred | not_actionable",
  "action_taken": "What was changed",
  "old_value": "Previous text or number",
  "new_value": "Corrected text or number"
}
```

### 3d. Deferred items

Some findings may require re-running earlier capabilities. Flag these clearly:

```
DEFERRED -- requires re-run:
  * TR-012: CH-016 pricing is 18 months stale -> re-run [RI] on CH-016
  * SR-003: CH-004 modal content needs complete rewrite -> re-run [BR] on CH-004
```

---

## Stage 4: Apply Corrections

### 4a. Update audit data

Apply all resolved findings:

1. **Pricing corrections** -> update `tools_researched[].annual_cost_aud`, recalculate totals
2. **Value corrections** -> update `proposed_changes[].value`, recalculate `roi_items[]`
3. **Formula fixes** -> update `formula_summary` and recalculate derived fields
4. **Modal rewrites** -> update `proposed_changes[].modal_content` sections
5. **Cross-reference fixes** -> add missing `meeting_references`, fix orphan pain points
6. **Contradiction fixes** -> correct the non-authoritative source

### 4b. Add verification metadata

Add to `strategic_approaches`:

```json
{
  "verification": {
    "verified_at": "{ISO datetime}",
    "verification_run_count": 1,
    "scope": "full",
    "review_types": ["technical", "sales", "compliance", "text_quality"],
    "lenses_successful": ["technical", "sales", "compliance", "text_quality"],
    "lenses_failed": [],
    "results": {
      "technical": {
        "findings_total": 0,
        "findings_high": 0,
        "findings_resolved": 0,
        "findings_deferred": 0,
        "pricing_corrections": 0,
        "formula_corrections": 0
      },
      "sales": {
        "findings_total": 0,
        "findings_high": 0,
        "findings_resolved": 0,
        "modal_rewrites": 0
      },
      "compliance": {
        "findings_total": 0,
        "findings_high": 0,
        "contradictions_found": 0,
        "contradictions_resolved": 0,
        "value_mismatches_fixed": 0,
        "source_evidence_gaps": 0,
        "source_evidence_reconstructed": 0,
        "modal_stat_untraced": 0,
        "meeting_ref_invalid": 0
      },
      "text_quality": {
        "findings_total": 0,
        "findings_medium": 0,
        "findings_low": 0,
        "findings_resolved": 0,
        "em_dashes_fixed": 0,
        "forbidden_words_fixed": 0,
        "formal_phrasing_fixed": 0,
        "parallel_structure_fixed": 0,
        "html_entities_fixed": 0,
        "render_defects_fixed": 0
      }
    },
    "overall_confidence": "HIGH | MEDIUM | LOW"
  }
}
```

### 4c. Update analyst metadata

```json
{
  "analyst_metadata": {
    "last_vr_run": "{ISO datetime}",
    "total_vr_runs": 1,
    "last_vr_scope": "full",
    "last_vr_confidence": "HIGH"
  }
}
```

---

## Stage 5: Display Summary

```
VERIFICATION COMPLETE -- {company_name}
Run #{verification_run_count} -- {datetime}

Sub-agents: 3 dispatched, {n} successful, {n} failed

--- TECHNICAL RESEARCH ---
  Findings:           {n} ({n} HIGH, {n} MEDIUM, {n} LOW)
  Pricing corrections: {n}
  Formula corrections: {n}
  Resolved:           {n}  |  Deferred: {n}

--- SALES EFFECTIVENESS ---
  Findings:           {n} ({n} HIGH, {n} MEDIUM, {n} LOW)
  Modal rewrites:     {n}
  Resolved:           {n}  |  Deferred: {n}

--- DATA COMPLIANCE ---
  Findings:           {n} ({n} HIGH, {n} MEDIUM, {n} LOW)
  Contradictions:     {n} found, {n} resolved
  Value mismatches:   {n} fixed
  Source evidence gaps: {n} changes with empty source_evidence[] ({n} reconstructed)
  Modal stat untraced:  {n} untraced statistical claims in modal content
  Meeting ref invalid:  {n} invalid session references
  Resolved:           {n}  |  Deferred: {n}

--- TEXT QUALITY ---
  Findings:           {n} ({n} HIGH, {n} MEDIUM, {n} LOW)
  Em dashes fixed:    {n}
  HTML entities fixed: {n}
  Forbidden words:    {n}
  Formal phrasing:    {n}
  Parallel structure: {n}
  Resolved:           {n}  |  Deferred: {n}

--- RENDERED DELIVERABLE LINT ---
  Files scanned:      {n}
  Render defects:     {n} ({n} HIGH double-escape, {n} MEDIUM)
  Artifacts fixed:    {n}  |  Builder fixes: {n}  |  Deferred: {n}

--- CORRECTIONS APPLIED ---
  {List each correction with finding_id, what changed, old -> new}

--- DEFERRED ITEMS ---
  {List items requiring capability re-runs}

Overall confidence: {HIGH if 0 HIGH findings remain | MEDIUM if 1-3 HIGH remain | LOW if >3 HIGH remain}

Recommendation:
  {If HIGH -> Ready for deliverable generation.}
  {If MEDIUM -> Review deferred items. Consider targeted re-runs before generating.}
  {If LOW -> Significant issues remain. Re-run [RI] on flagged changes, then [VR] again.}
```

---

## Stage 6: Save

1. Write the full updated `opportunities` dict to `clients/{client_slug}/03-audit/data/opportunities.json` (includes all corrected `proposed_changes[]`, `roi_items[]`, and `risk_register[]`). Write the full updated `strategy` dict to `clients/{client_slug}/03-audit/data/strategy.json` (includes `strategic_approaches.verification` metadata). For v2 fallback: write to top-level keys in `audit-data.json` as before.
2. Update `clients/{client_slug}/03-audit/data/audit-manifest.json`: set `domains.opportunities.updated_at` and `domains.strategy.updated_at` and the root `updated_at` to the current ISO datetime. Skip for v2 fallback.
3. Save session progress to memory via [SM]
4. Confirm save with summary

---

## Re-run Behaviour

On subsequent runs (`verification_run_count > 1`):
- Increment `verification_run_count`
- Focus on previously deferred items and any changes modified since last VR run
- Compare new findings against previous run to track improvement
- Track whether repeated findings indicate a systemic issue
- If a lens failed on the previous run, re-dispatch it

---

## CRM Task Update

After completion, update the VR task in CRM:
1. Load `crm.project_id` from `meta.json` (v4) or `audit-data.json` (v2/v3). If null, skip.
2. `list_tasks(project_id)` -> find "Verify Research (VR)"
3. `update_task_status(task_id, status: "Done")`
4. `create_task_comment(task_id, content)` with:
   `"VR complete. {n} findings across 4 review lenses (technical/sales/compliance/text-quality) + deliverable lint ({n} render defects fixed). {n} resolved, {n} deferred. Confidence: {level}."`
5. Mark next task "In Progress" (typically Solution Designer [RE] or Generator deliverables)
