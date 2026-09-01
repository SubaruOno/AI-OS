---
name: research-tool-stack
description: TR capability — Research the client's existing tool stack for API availability and MCP server existence. Enriches tools[] in extraction.json with integration_openness, api_available, mcp_available, and related fields. Run after process_map_complete, before EI.
---

# TR — Research Tool Stack

## Role

You are running the Tool Research step for the APG Process Analyst. Your job is to dispatch lightweight sub-agents to check each of the client's existing tools for:

1. Public API availability (can we programmatically read/write their data?)
2. MCP server existence (can Claude connect to this tool natively?)

Results are written back to `extraction.json` so the downstream RI step can find tools with real API coverage when scanning for untapped integration potential.

**Write domain:** `extraction.json` (`tools[]` field only). Update `audit-manifest.json` timestamps after each batch checkpoint.

---

## Stage 1: Pre-flight

Load `clients/{client_slug}/03-audit/data/extraction.json`. Read the `tools[]` array.

Display a status table:

```
TOOL RESEARCH PRE-FLIGHT — {company_name}
─────────────────────────────────────────
Total tools in stack:     {n}
Already researched:       {m}   (integration_openness is set)
Awaiting research:        {k}   (integration_openness is null or "unknown")
```

If all tools are already researched (`integration_openness` set on all), display the summary from Stage 5 and stop. Ask if the user wants to re-research any tools.

Load `clients/{client_slug}/03-audit/data/meta.json` to get `company_name` and `industry_tag` for the company context packet.

---

## Stage 2: Filter and Batch

**Filter out non-software tools.** Any tool where the name clearly describes a manual process (e.g., "Paper forms", "Whiteboard", "Manual spreadsheet", "Phone calls") should be auto-classified without dispatching a sub-agent:

```json
{
  "api_available": false,
  "api_docs_url": null,
  "mcp_available": false,
  "mcp_url": null,
  "integration_openness": "closed",
  "integration_notes": "Not a software tool.",
  "confidence": "HIGH"
}
```

**Build batches of 5** from the remaining unresearched tools.

---

## Stage 3: Build Shared Context

Build a compact company context packet (keep under 500 tokens):

```json
{
  "company_name": "{company_name}",
  "industry_tag": "{industry_tag}",
  "total_tools": {n}
}
```

Load the sub-agent prompt from:
`apg-audit-plugin/skills/4-improvement-researcher/sub-agent-tool-research.md`

---

## Stage 4: Dispatch Sub-Agents

For each batch of tools, construct the sub-agent prompt by substituting `{company_context}` and `{tool_batch}` into the sub-agent template.

Dispatch batches in parallel (up to 3 at once) using the `Agent()` tool:

```
Agent(
  description="Tool integration research — {company_name} batch {n}",
  prompt=<filled sub-agent prompt>
)
```

After each batch completes:

1. Parse the returned JSON array
2. For each result, find the matching tool in `tools[]` by `tool_name` (case-insensitive match)
3. Merge the new fields into the tool object:
   - `api_available`
   - `api_docs_url`
   - `mcp_available`
   - `mcp_url`
   - `integration_openness`
   - `integration_notes`
   - `confidence` (update if sub-agent result has higher confidence)
4. Write the updated `extraction.json` back to disk
5. Update `audit-manifest.json`: set `domains.extraction.updated_at` and root `updated_at` to the current ISO timestamp

Checkpoint save after each batch so partial progress is preserved.

---

## Stage 5: Summary

After all batches complete, print a final summary:

```
TOOL RESEARCH COMPLETE — {company_name}
─────────────────────────────────────────
Total tools researched:   {total}

  Open  (API + MCP):   {open_count}   ████...
  Partial (API only):  {partial_count} ████...
  Closed (no API):     {closed_count}  ████...
  Unknown:             {unknown_count}
  Skipped (non-SW):    {skipped_count}

Tools with MCP:   {mcp_count}
─────────────────────────────────────────
Next step: Run [EI] to extract improvements.
The api_available data is now available for RI to find untapped integration potential.
```

List any tools marked `confidence: LOW` as a review note.

---

## CRM Task Update

If `meta.json` has a `crm.project_id`, update the CRM task named "Tool Research" or "TR" to "Done" via `apg-crm` MCP. If no such task exists, skip silently.
