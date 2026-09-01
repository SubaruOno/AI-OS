---
name: save-memory
description: Save current session progress to memory
menu-code: SM
---

# Save Memory

Immediately persist the current session context to memory.

## Process

**Sidecar location:** `${CLAUDE_PLUGIN_ROOT}/_memory/{skillName}-sidecar/`

### Step 1 — Update per-client detail file

1. **Load current client file** — Read `{sidecar}/clients/{client_slug}.md` (create if missing using the template below)
2. **Update all sections** with current session data:
   - Status / Audit status + session count
   - Ingestion State — meetings extracted/total, materials extracted/skipped/pending, last SU run date + what ran
   - Extraction Stats — pain points, waste items, optimisations, decision nodes, tools, open FQs (HIGH/MEDIUM/LOW)
   - Business metrics (blended rate, staff count, key figures)
   - Key People, Key Constraints, Key Pain, Stages, Contradictions
   - Last Activity — date + brief description of what changed this session
   - CRM — confirm `crm.project_id` and `crm.contact_id` are noted
3. **Write updated `clients/{client_slug}.md`**

### Step 2 — Update cross-client index

1. **Load `{sidecar}/index.md`**
2. **Update the row for `{client_slug}`** in the client table with current: status, sessions count, pain points, waste/yr, last activity date
3. **Update the "Last Session" section** with today's date, client, and one-line summary
4. **Write updated `index.md`**

### Step 3 — Checkpoint shared files if needed

- **`patterns.md`** — Add new industry patterns, effective follow-up question types, or tool stack observations from this session
- **`chronology.md`** — Add a chronology entry: `{date} | {client_slug} | {brief: what was extracted/run}`

---

## Per-Client File Template

Use this when creating a new `clients/{client_slug}.md`:

```markdown
# {client_slug} — Process Mapper Detail

## Status
- **Audit status:** {audit_status}
- **Sessions:** {N} ({description of sources})

## Ingestion State
- Meetings: {N}/{total} extracted
- Materials: {N}/{total} extracted, {N} skipped, {N} pending
- Last SU run: {date} — {brief description}
- Manifest: `clients/{client_slug}/03-audit/data/ingestion-manifest.json`

## Extraction Stats
- **Pain points:** {N} | **Waste items:** {N} (${annual}/yr) | **Optimisations:** {N} | **Decision nodes:** {N} | **Tools:** {N}
- **Open follow-up questions:** {N} (HIGH: {N}, MEDIUM: {N}, LOW: {N})
- **Blended rate:** ${rate}/hr ({confidence} confidence — {reason})
- **Staff roster:** {N} entries ({description})
- **Business metrics:** {key figures}

## Key People
- {Name} ({Role}), ...

## Key Constraints
{N} ({brief list})

## Contradictions
{N} ({brief description or "none"})

## Key Pain
- {top pain points}

## Stages
{stage_id} ({step count}), ...

## Last Activity
{date} — {description of what was done}

## CRM
- Check audit-data.json for `crm.project_id`, `crm.contact_id`
```

---

## Output

Confirm save with brief summary: "Memory saved. Updated `clients/{client_slug}.md` and `index.md`. {brief-summary-of-what-changed}"
