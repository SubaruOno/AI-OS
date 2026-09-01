# CRM Integration Reference

Shared reference for all APG skills that interact with the APG CRM via MCP tools (`mcp__claude_ai_APG_CRM__*`).

---

## Entity Model

Each client maps to three CRM entities:

| Entity | Created by | Updated by | Purpose |
|--------|-----------|------------|---------|
| **Contact** | NC (new client) | Skills 1-2 | The person or company |
| **Lead** | NC (new client) | Skills 1-2 | Sales pipeline (pre-discovery through won/lost) |
| **Project** | First SU run | Skills 3-6 | Audit engagement (extraction through delivery) |

---

## CRM Block in Data Files

Both `prospect-profile.json` (sales) and `audit-data.json` (audit) store CRM IDs:

```json
{
  "crm": {
    "contact_id": "uuid | null",
    "lead_id": "uuid | null",
    "project_id": "uuid | null",
    "task_list_ids": {
      "extraction": "uuid | null",
      "analysis": "uuid | null",
      "deliverables": "uuid | null",
      "solution_design": "uuid | null"
    },
    "last_synced": "ISO 8601 | null"
  }
}
```

---

## Lookup-First Pattern (Critical)

**Contacts, leads, and projects almost always already exist in the CRM.** Every CRM integration point MUST search first and only create as a last-resort fallback.

### Contact Lookup

```
1. search_contacts(query: "{company_name}") → match by name
2. If no match: search_contacts(query: "{domain}") → match by website/email domain
3. If still no match: create_contact(name, email_address, website, is_customer: true)
4. Store contact_id in crm block
```

### Lead Lookup

```
1. search_leads(query: "{company_name}") → match by title containing company name
2. If multiple matches: prefer the one linked to the matched contact_id
3. If no match: ASK the user before creating — "No existing lead found for {company_name}. Create new lead?" Only call create_lead(title: "{company_name} - Operational Audit", contact_id, value: 3000, stage: "New") after explicit user approval.
4. Store lead_id in crm block
```

### Project Lookup

```
1. list_projects() → filter by contact_id matching crm.contact_id
2. If multiple matches: prefer project with "Audit" in name, or most recent
3. If no match: create_project(name: "{company_name} Audit", contact_id, status: "active", budget: 3000)
4. Store project_id in crm block
```

---

## Lead Stage Mapping

Skills only advance stages forward. Never override manual stages.

| Pipeline Phase | Lead Stage | Trigger Skill |
|---------------|------------|---------------|
| NC created | New | 1-call-prep / new-client |
| Research done | Contacted | 1-call-prep / research-client |
| Discovery page built | Discovery Call - Scheduled | 2-sales-closer / generate-discovery-page |
| Close page built | Discovery Call - Completed | 2-sales-closer / generate-close-page |
| Follow-up sent | Negotiation | 2-sales-closer / generate-followup-email |
| Client pays / first SU | Won | 3-audit-extractor / sync-and-update |

### Stage Update Rule

Before updating a lead stage:
1. `get_lead(lead_id)` → read current stage
2. Only update if current stage is in the expected "previous" set for that transition
3. If the lead is in a manual stage (e.g. "Need Re-Activation", "Not Showing up to Discovery Call"), do NOT override — add a `create_lead_comment` instead noting what happened

**Safe previous stages per transition:**
- → Contacted: from "New"
- → Discovery Call - Scheduled: from "New", "Contacted", "Initial Follow-Up Phone Call"
- → Discovery Call - Completed: from "Discovery Call - Scheduled", "Contacted"
- → Negotiation: from "Discovery Call - Completed"
- → Won: from "Negotiation", "Proposal", "Discovery Call - Completed"

---

## Audit Project Task Board

Each audit project has 4 task lists with grouped tasks. Created on first SU run.

### List 1: Extraction
| Task | Priority |
|------|----------|
| Session Extraction — Complete all sessions | 3 (high) |
| Process Map Complete — All stages covered | 2 (medium) |

### List 2: Analysis
| Task | Priority |
|------|----------|
| Extract Improvements (EI) | 2 |
| Research Improvements (RI) | 1 |
| Build Strategic Approaches (SA) | 1 |
| Build & Rate (BR) | 1 |
| Verify Research (VR) | 1 |
| Build Transformation Blueprint (TB) | 1 |

### List 3: Deliverables
| Task | Priority |
|------|----------|
| Generate Deliverables | 1 |

### List 4: Solution Design
| Task | Priority |
|------|----------|
| Extract Requirements (RE) | 1 |
| Build Architecture (BA) | 1 |
| Build Prototype (BP) | 1 |

### Task Update Pattern

Skills update tasks after completing their work:

```
1. list_tasks(project_id: crm.project_id) → find task by title match
2. update_task_status(task_id, status: "Done")
3. create_task_comment(task_id, content: "{summary of what was done}")
```

### Idempotency

SU runs repeatedly. Before creating tasks:
1. `list_tasks(project_id)` → check if tasks already exist (match by title)
2. Only create tasks that don't already exist
3. Add comments to existing tasks (comments are append-only, safe to repeat)

---

## Best-Effort Rule

CRM calls are **best-effort**. If any CRM MCP call fails:
1. Log a warning: `CRM SYNC WARNING: {operation} failed — {error}. Will retry on next run.`
2. Continue the pipeline — never block extraction, analysis, or delivery
3. The next run retries naturally because lookups are idempotent

---

## Data Flow Direction

**One-way: local files → CRM.** The audit-data.json / prospect-profile.json remain the source of truth. CRM is a downstream visibility mirror. The only data flowing back from CRM is entity IDs (contact_id, lead_id, project_id, task_list_ids).
