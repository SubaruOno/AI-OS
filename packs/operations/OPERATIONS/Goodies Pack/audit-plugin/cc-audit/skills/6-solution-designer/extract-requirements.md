---
name: extract-requirements
description: Decompose proposed changes into internal requirements specifications — user stories, acceptance criteria, screen inventory, data model, user roles, and integration specs.
menu-code: RE
---

# Extract Requirements (RE)

> **Idempotent.** First run creates requirements from scratch. Re-runs update based on proposed change updates.

> **INTERNAL DOCUMENTATION ONLY.** Requirements specifications are never shown to clients. They are for the dev team and project management.

## Purpose

For each proposed change (grouped by transformation blueprint phase), decompose into functional requirements with user stories, acceptance criteria, screen inventory, data model, user roles, and integration specs. Write the `requirements_spec` top-level object to audit-data.json.

---

## Stage 1: Pre-flight

1. Load audit data:
   - Check for `clients/{slug}/03-audit/data/audit-manifest.json`. If present (v4): read domain files directly:
     - `clients/{slug}/03-audit/data/meta.json`
     - `clients/{slug}/03-audit/data/extraction.json` (for staff_roster, processes.steps)
     - `clients/{slug}/03-audit/data/findings.json` (for change_readiness)
     - `clients/{slug}/03-audit/data/opportunities.json`
     - `clients/{slug}/03-audit/data/strategy.json`
     - Skip `architecture.json` (RE creates it fresh)
   - For v3 files (no manifest, `_schema_version` starts with "3"): load `meta`, `extraction`, `findings`, `opportunities`, and `strategy` domains from `audit-data.json`.
   - For v2 files: load the full `audit-data.json`.
   Verify `proposed_changes[]` has `implementation` and `value` populated.

2. Scan for readiness:
   ```
   REQUIREMENTS STATUS — {company_name}
   Proposed changes: {n} total ({n} with implementation + value)
   Transformation blueprint: {present|absent} ({n} phases)
   Existing requirements_spec: {present|absent}
   ```

3. If `proposed_changes[]` lack implementation or value, warn and suggest running Improvement Researcher [BR] first.

4. Select scope:
   ```
   Select scope for requirements extraction:
     A) All changes — {n} changes across {n} phases
     B) Specific phase (e.g., Phase 1: Quick Wins)
     C) Specific change by ID (e.g., CH-001)
     D) All changes in sequence
   ```

---

## Stage 2: Functional Requirements Decomposition

For each selected change within the chosen packages, decompose into functional requirements.

### 2a. Extract user stories

From the change's `modal_content`, `proposed_solution`, and `affected_step_ids`, derive user stories:

```
As a {role}, I want to {action} so that {outcome}.
```

- Role comes from the step owner or `staff_roster[]` match
- Action comes from the proposed solution
- Outcome comes from the value calculation (time saved or productivity gained)

Each change should produce 1-3 user stories depending on complexity.

### 2b. Write acceptance criteria

For each user story, write testable acceptance criteria:

```
Given {precondition}
When {action}
Then {expected result}
```

Draw from:
- Current step descriptions (what must change)
- Proposed tools (what integrations must work)
- Value assumptions (what must be true for the value calculation to hold)

### 2c. Populate requirements array

```json
{
  "requirement_id": "REQ-001",
  "change_id": "CH-001",
  "derived_from_change_ids": ["CH-001"],
  "package_id": "PKG-001",
  "title": "Automated lead follow-up sequence",
  "user_stories": [
    {
      "story_id": "US-001",
      "role": "Sales Manager",
      "action": "have new leads automatically entered into a nurture sequence",
      "outcome": "I don't spend 3.5 hrs/wk manually sending follow-up emails",
      "acceptance_criteria": [
        {
          "given": "a new lead is created in HubSpot",
          "when": "the lead matches the target segment criteria",
          "then": "the lead is automatically enrolled in the appropriate nurture sequence within 5 minutes"
        }
      ]
    }
  ],
  "priority": "must-have",
  "complexity": "medium",
  "notes": ""
}
```

**Source trail (mandatory):** Every requirement carries `derived_from_change_ids[]` — the proposed_change(s) it implements. Single-change requirements set both `change_id` and `derived_from_change_ids: ["CH-XXX"]` for backward compatibility. Shared requirements (e.g. one dashboard serving CH-002 and CH-004) set `change_id` to the primary and list all sources in `derived_from_change_ids[]`. This is the link that lets the prototype and the comprehensive-report PDF trace any feature back through CH → PP/W → meeting transcript.

---

## Stage 3: Identify User Roles

Build the user roles inventory from two sources:

### 3a. From staff_roster

Extract roles from `staff_roster[]` that appear as step owners in affected processes:
```json
{
  "role_id": "ROLE-001",
  "name": "Sales Manager",
  "source": "staff_roster",
  "staff_members": ["Riley"],
  "affected_packages": ["PKG-001"],
  "permission_level": "admin",
  "notes": "Primary user of HubSpot CRM"
}
```

### 3b. From end-user types

Identify external user types from process context (e.g., clients, leads, suppliers):
```json
{
  "role_id": "ROLE-005",
  "name": "Client",
  "source": "end_user",
  "staff_members": [],
  "affected_packages": ["PKG-001", "PKG-002"],
  "permission_level": "external",
  "notes": "Receives automated communications and self-service portal access"
}
```

---

## Stage 4: Build Screen Inventory

For each requirement that involves a user interface, identify the screens needed.

### 4a. Identify screen types

- **Configuration screens** — setup and settings for automations
- **Dashboard screens** — monitoring and reporting views
- **Input screens** — forms, data entry points
- **Notification screens** — alerts, email templates, SMS templates
- **Integration screens** — connection setup, mapping configuration

### 4b. Populate screen inventory

```json
{
  "screen_id": "SCR-001",
  "name": "Lead Nurture Sequence Configuration",
  "type": "configuration",
  "package_id": "PKG-001",
  "requirement_ids": ["REQ-001"],
  "platform": "HubSpot",
  "description": "Configure nurture sequence triggers, email templates, and timing rules",
  "user_roles": ["ROLE-001"],
  "is_custom_build": false,
  "notes": "Native HubSpot sequences UI — no custom build needed"
}
```

Mark `is_custom_build: true` for screens that need custom development vs. native platform UI.

---

## Stage 5: Build Data Model

Identify the key data entities from the requirements and their relationships.

### 5a. Extract entities

From user stories and acceptance criteria, identify data entities:
```json
{
  "entity_id": "ENT-001",
  "name": "Lead",
  "source_system": "HubSpot",
  "key_fields": ["name", "email", "company", "segment", "source", "created_date"],
  "relationships": [
    { "target_entity": "ENT-002", "type": "has_many", "description": "Lead has many Activities" }
  ],
  "package_ids": ["PKG-001"],
  "notes": "Existing HubSpot contact object — may need custom properties added"
}
```

### 5b. Map data flows

For each integration point, document the data flow:
```json
{
  "flow_id": "FLOW-001",
  "name": "New Lead to Nurture Sequence",
  "source_entity": "ENT-001",
  "source_system": "HubSpot",
  "destination_system": "HubSpot Sequences",
  "trigger": "Lead created with segment = target",
  "fields_mapped": ["name", "email", "segment"],
  "frequency": "real-time",
  "package_id": "PKG-001"
}
```

---

## Stage 6: Map Integration Requirements

From `proposed_tools[]` on each change and `research.tools_researched[]`, document integration specs.

### 6a. Extract integrations

```json
{
  "integration_id": "INT-001",
  "name": "HubSpot to Xero Sync",
  "source_system": "HubSpot",
  "target_system": "Xero",
  "integration_method": "API",
  "middleware": "Make.com",
  "package_id": "PKG-001",
  "api_details": {
    "source_api": "HubSpot CRM API v3",
    "target_api": "Xero Accounting API 2.0",
    "auth_method": "OAuth 2.0",
    "rate_limits": "100 requests/10 seconds (HubSpot), 60/minute (Xero)"
  },
  "data_entities": ["ENT-001", "ENT-003"],
  "requirements": ["REQ-001", "REQ-004"],
  "risks": ["API rate limits may require batching for bulk operations"],
  "notes": "Research confirmed API endpoints exist for all required operations"
}
```

### 6b. Cross-reference with research

Pull from `research.tools_researched[]` on each proposed change:
- API documentation links
- Known limitations
- Pricing implications (e.g., API access requires higher plan tier)
- Authentication requirements

---

## Stage 7: Write Requirements Spec to Audit Data

Write the `requirements_spec` to the audit data:
- v4: load `clients/{slug}/03-audit/data/architecture.json`, merge `requirements_spec` into the existing dict, write the full dict back to `clients/{slug}/03-audit/data/architecture.json`, then update `audit-manifest.json`: set `domains.architecture.updated_at` and root `updated_at`.
- v3: write into `architecture.requirements_spec` in `audit-data.json`
- v2: write to top-level `requirements_spec` in `audit-data.json`

```json
{
  "requirements_spec": {
    "generated_at": "2026-03-29T14:30:00Z",
    "scope": "all_packages",
    "package_ids_included": ["PKG-001", "PKG-002", "PKG-003"],
    "requirements": [
      {
        "requirement_id": "REQ-001",
        "change_id": "CH-001",
        "derived_from_change_ids": ["CH-001"],
        "package_id": "PKG-001",
        "title": "Automated lead follow-up sequence",
        "user_stories": [...],
        "priority": "must-have",
        "complexity": "medium",
        "notes": ""
      }
    ],
    "user_roles": [
      {
        "role_id": "ROLE-001",
        "name": "Sales Manager",
        "source": "staff_roster",
        "staff_members": ["Riley"],
        "affected_packages": ["PKG-001"],
        "permission_level": "admin",
        "notes": ""
      }
    ],
    "screen_inventory": [
      {
        "screen_id": "SCR-001",
        "name": "Lead Nurture Sequence Configuration",
        "type": "configuration",
        "package_id": "PKG-001",
        "requirement_ids": ["REQ-001"],
        "platform": "HubSpot",
        "description": "...",
        "user_roles": ["ROLE-001"],
        "is_custom_build": false,
        "notes": ""
      }
    ],
    "data_model": {
      "entities": [
        {
          "entity_id": "ENT-001",
          "name": "Lead",
          "source_system": "HubSpot",
          "key_fields": [...],
          "relationships": [...],
          "package_ids": ["PKG-001"],
          "notes": ""
        }
      ],
      "data_flows": [
        {
          "flow_id": "FLOW-001",
          "name": "New Lead to Nurture Sequence",
          "source_entity": "ENT-001",
          "source_system": "HubSpot",
          "destination_system": "HubSpot Sequences",
          "trigger": "...",
          "fields_mapped": [...],
          "frequency": "real-time",
          "package_id": "PKG-001"
        }
      ]
    },
    "integrations": [
      {
        "integration_id": "INT-001",
        "name": "HubSpot to Xero Sync",
        "source_system": "HubSpot",
        "target_system": "Xero",
        "integration_method": "API",
        "middleware": "Make.com",
        "package_id": "PKG-001",
        "api_details": {...},
        "data_entities": ["ENT-001", "ENT-003"],
        "requirements": ["REQ-001", "REQ-004"],
        "risks": [...],
        "notes": ""
      }
    ],
    "summary": {
      "total_requirements": 12,
      "total_user_stories": 28,
      "total_user_roles": 5,
      "total_screens": 8,
      "custom_build_screens": 2,
      "total_entities": 6,
      "total_integrations": 4,
      "total_data_flows": 7
    }
  }
}
```

---

## Stage 8: Display Summary

```
REQUIREMENTS EXTRACTED — {company_name} (INTERNAL — NOT FOR CLIENT)

| Package              | Requirements | User Stories | Screens | Integrations |
|----------------------|-------------|-------------|---------|--------------|
| PKG-001 HubSpot...  | 4           | 10          | 3       | 2            |
| PKG-002 ShiftCare...| 3           | 7           | 2       | 1            |
| PKG-003 AI Workflow..| 5          | 11          | 3       | 1            |

User Roles: {n} identified ({n} staff, {n} end-user types)
Data Model: {n} entities, {n} data flows
Custom Build Screens: {n} of {n} total (rest use native platform UI)

Requirement priorities:
  must-have:  {n}
  should-have: {n}
  nice-to-have: {n}

Next step: Use requirements for prototyping and sprint planning.
```

---

## Stage 9: Save

1. Write `requirements_spec` to audit data (see Stage 7 for path — v4/v3/v2 rules apply)
2. Update `architect_metadata`:
   ```json
   {
     "architect_metadata": {
       "last_re_run": "ISO timestamp",
       "total_re_runs": 1,
       "requirements_extracted": 12,
       "packages_covered": ["PKG-001", "PKG-002", "PKG-003"]
     }
   }
   ```
3. Confirm save
