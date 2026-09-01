---
name: build-architecture
description: Build the custom platform alternative to compare against the SaaS strategic approaches — user journeys, page structure, data models, access policies, integration specs.
menu-code: BA
---

# Build Architecture (BA)

> **Idempotent.** First run creates architecture from scratch. Re-runs review and update existing architecture after requirement changes.

## Purpose

Build the custom platform alternative to compare against the SaaS strategic approaches. Transforms the `requirements_spec` into a complete architecture document that defines user journeys, page structure, data models, access policies, and integration architecture for the APG Unified Platform. This is INTERNAL documentation — the source of truth for prototype generation. Never shown to clients directly.

---

## Pre-flight

1. Load audit data:
   - Check for `clients/{slug}/03-audit/data/audit-manifest.json`. If present (v4): read domain files directly:
     - `clients/{slug}/03-audit/data/meta.json`
     - `clients/{slug}/03-audit/data/extraction.json`
     - `clients/{slug}/03-audit/data/opportunities.json`
     - `clients/{slug}/03-audit/data/architecture.json`
     - Do NOT load `findings.json` or `strategy.json`
   - For v3 files (no manifest, `_schema_version` starts with "3"): load `meta`, `extraction`, `opportunities`, and `architecture` domains from `audit-data.json`.
   - For v2 files: load the full `audit-data.json`.

   Check `requirements_spec` exists (`architecture.requirements_spec` in v3/v4, top-level in v2).
   - If missing: warn and suggest running [RE] first.

2. Show readiness summary:
   ```
   ARCHITECTURE BUILD — {company_name}
   Requirements: {n} requirements across {n} packages
   User roles: {n} roles identified
   Screens: {n} screens in inventory
   Entities: {n} data entities
   Integrations: {n} integrations

   Existing architecture_doc: {present|absent}
   ```

3. If `architecture_doc` already exists, ask:
   ```
   Existing architecture found.
   Options:
     A) Full rebuild — regenerate from current requirements
     B) Update existing — adjust based on requirement changes
     C) Cancel
   ```

---

## Stage 0: Module Inventory

The Solution Designer always architects the APG Unified Platform — the custom build alternative that clients compare against the SaaS strategic approaches. There is no strategy selection step.

### 0a. Load custom build data

From each `proposed_changes[].research.custom_build_option`, collect:
- Module mappings (which platform modules handle each change)
- Scope levels and week estimates
- Change IDs for traceability

### 0b. Build module inventory

1. Group `custom_build_option` data by module
2. Map each module to the APG platform template using `references/apg-custom-build.md` Module Mapping Guide:
   - `configure_existing` — module exists in template, needs config
   - `medium_customisation` — module exists, needs additional views/logic
   - `custom_build` — new module needed, uses platform patterns
   - `heavy_custom` — significant new functionality

Build the module inventory:
```json
{
  "modules": [
    {
      "module_name": "CRM Module",
      "scope_level": "configure_existing",
      "change_ids": ["CH-001", "CH-002"],
      "template_modules": ["CRM Core (Leads + Contacts)"],
      "weeks_estimate": 1.0
    }
  ]
}
```

This module inventory drives all subsequent stages.

---

## Stage 1: User Journeys

For each user role in `requirements_spec.user_roles[]`, map their key workflows through the system.

### 1a. Identify journeys per role

**Derivation algorithm:**
1. For each role, collect all `requirement_ids` from `requirements_spec.requirements[]` where `user_stories[].role` matches this role
2. For each requirement, collect `affected_step_ids` (from the parent `proposed_change`)
3. Cross-reference `affected_step_ids` with `processes[].steps[]` to get the actual process steps — who does what, with what data, in what order
4. Group steps by process (e.g., Acquisition, Onboarding, Fulfilment, Retention, Payroll & Invoicing)
5. Each process-role combination = one journey candidate
6. Map each step to the module that handles it (from the module inventory matched via `change_id`)

### 1b. Map journey steps

For each journey, define the sequence of screens visited, actions taken, data seen, and data entered:

```json
{
  "role": "operations_manager",
  "journey_name": "Daily scheduling workflow",
  "module": "Scheduling Engine",
  "change_ids": ["CH-006", "CH-007", "CH-008"],
  "steps": [
    {
      "screen": "SCR-SCHED-001",
      "action": "View weekly roster",
      "data_shown": ["staff_availability", "participant_appointments", "shift_gaps"],
      "data_input": [],
      "next": "SCR-SCHED-002"
    },
    {
      "screen": "SCR-SCHED-002",
      "action": "Assign shift to available worker",
      "data_shown": ["worker_profile", "qualifications", "distance"],
      "data_input": ["worker_id", "shift_time", "participant_id"],
      "next": "SCR-SCHED-003"
    },
    {
      "screen": "SCR-SCHED-003",
      "action": "Confirm and send notification",
      "data_shown": ["assignment_summary", "notification_preview"],
      "data_input": [],
      "integration": "Twilio SMS",
      "next": "SCR-SCHED-001"
    }
  ]
}
```

### 1c. Validate coverage

- Every screen in `screen_inventory[]` must appear in at least one journey. Flag orphan screens.
- Every requirement must be represented by at least one journey step. Flag unrepresented requirements.

---

## Stage 2: Page Structure

Build the sitemap and navigation tree from `requirements_spec.screen_inventory[]`, grouped by module.

### 2a. Define pages

For each screen in `screen_inventory[]`, create a page definition. Group screens by module (from Stage 0c module inventory, matching via `change_ids`).

**Component inference rules** — derive `components[]` from the screen description and type:

| Screen pattern | Components |
|---|---|
| "list", "view all", "browse" | `Table`, `Input` (search), `Pagination`, `Badge` (status tags) |
| "create", "new", "add" | `Input`, `Select`, `Textarea`, `Button`, `FileUpload` (if documents) |
| "dashboard", "overview" | metric cards, `Charts` (recharts), quick-action `Button`s |
| "detail", "profile", "view" | page header, `Tabs`, activity timeline, `Badge`, `Avatar` |
| "settings", "configuration" | `Toggle`, `Input`, `Select`, `Radio`, form sections |
| "kanban", "pipeline" | card layout, `Badge`, `Dropdown` (actions) |
| "calendar", "schedule", "roster" | `DatePicker`, grid layout, `Avatar`, `Tooltip` |
| "notifications", "alerts" | list layout, `Badge`, `Toggle` (preferences) |

```json
{
  "screen_id": "SCR-CRM-001",
  "name": "Lead Pipeline",
  "route": "/crm/leads",
  "parent": "/crm",
  "module": "CRM Module",
  "roles": ["admin", "operations_manager"],
  "components": ["Table", "Input", "Pagination", "Badge", "Dropdown", "Button"]
}
```

- Derive `route` from the module and screen name (kebab-case, logical hierarchy: `/{module}/{screen}`)
- Set `parent` for nested pages (e.g., `/crm/leads/:id` is child of `/crm/leads`)
- List `roles` from `screen_inventory[].user_roles[]`
- Add `module` from module inventory grouping

### 2b. Build navigation

Create the navigation structure grouped by module:

```json
{
  "section": "CRM",
  "module": "CRM Module",
  "items": [
    {"label": "Leads", "route": "/crm/leads", "icon": "Users01", "roles": ["admin", "operations_manager"]},
    {"label": "Contacts", "route": "/crm/contacts", "icon": "BookOpen01", "roles": ["admin", "operations_manager", "coordinator"]}
  ]
}
```

- Each module = one navigation section
- Assign icon names using Untitled UI icon naming convention (PascalCase with number suffix, e.g., `Home01`, `Users01`, `Calendar01`)
- **>>> MCP CALL:** For each nav item, call `search_icons("{keyword}")` to find the best matching icon. Example: `search_icons("calendar")` → `Calendar01`, `search_icons("users")` → `Users01`, `search_icons("invoice")` → `Receipt`
- Set role visibility from page roles

### 2c. Standard pages

Every prototype gets these standard pages regardless of modules:
- **Dashboard** (`/dashboard`) — overview metrics, recent activity, quick actions
- **Settings** (`/settings`) — user profile, notification preferences
- **Not Found** (`/404`) — error page

---

## Stage 3: Data Models

Expand `requirements_spec.data_model` into full entity definitions.

### 3a. Define entities

For each entity in `data_model.entities[]`, expand with complete field definitions:

```json
{
  "entity": "Participant",
  "table_name": "participants",
  "module": "CRM Module",
  "fields": [
    {"name": "id", "type": "uuid", "primary": true},
    {"name": "first_name", "type": "string", "required": true},
    {"name": "last_name", "type": "string", "required": true},
    {"name": "email", "type": "string", "unique": true},
    {"name": "phone", "type": "string"},
    {"name": "ndis_number", "type": "string", "unique": true},
    {"name": "funding_level", "type": "decimal", "required": true},
    {"name": "status", "type": "enum", "values": ["active", "inactive", "pending"], "default": "pending"},
    {"name": "assigned_coordinator_id", "type": "uuid", "foreign_key": "staff.id"},
    {"name": "created_at", "type": "timestamp", "required": true, "default": "now()"},
    {"name": "updated_at", "type": "timestamp", "required": true, "default": "now()"}
  ],
  "relationships": [
    {"to": "Staff", "type": "many-to-one", "foreign_key": "assigned_coordinator_id", "label": "coordinator"},
    {"to": "Shift", "type": "one-to-many", "foreign_key": "participant_id"},
    {"to": "CaseNote", "type": "one-to-many", "foreign_key": "participant_id"},
    {"to": "Invoice", "type": "one-to-many", "foreign_key": "participant_id"}
  ]
}
```

**Field derivation sources:**
- Entity `key_fields[]` from requirements → expand into full field definitions
- `data_flows[].fields_mapped[]` → additional fields needed for integrations
- Process step descriptions → domain-specific fields (e.g., NDIS number, funding level)
- Standard fields all entities get: `id`, `created_at`, `updated_at`, `created_by`

### 3b. Validate relationships

- Every foreign key must reference a valid entity
- Every relationship must be bidirectional (if Participant has-many Shifts, Shift belongs-to Participant)
- Flag any orphan entities with no relationships

---

## Stage 4: Access Policies

Build the RBAC matrix from `requirements_spec.user_roles[]` and the data models.

### 4a. Derive permission matrix

**Algorithm:**

1. Start with `requirements_spec.user_roles[].permission_level`:

| Permission Level | Default Read | Default Write | Default Delete | Scope |
|---|---|---|---|---|
| `admin` | all records | all records | all records | global |
| `standard` | all records | own records | none | team-scoped |
| `read-only` | all records | none | none | global read |
| `external` | own record only | own record only | none | self-only |

2. Override defaults using process step ownership — cross-reference `processes[].steps[].owner` with roles:
   - If a role owns a step that creates/modifies an entity → grant write on that entity
   - If a role owns a step that reads an entity → confirm read access

3. Generate the matrix:

```json
{
  "role": "support_worker",
  "permission_level": "standard",
  "entity_policies": [
    {
      "entity": "Participant",
      "read": "assigned_only",
      "write": "case_notes_only",
      "delete": false,
      "scope_field": "assigned_worker_id"
    },
    {
      "entity": "Shift",
      "read": "own_only",
      "write": "clock_in_out",
      "delete": false,
      "scope_field": "worker_id"
    }
  ]
}
```

### 4b. Generate Supabase RLS policies

For each role-entity policy, translate to Row Level Security:

```json
{
  "role": "support_worker",
  "entity": "Participant",
  "rls_policy": "auth.uid() IN (SELECT worker_id FROM assignments WHERE participant_id = participants.id AND status = 'active')",
  "policy_name": "support_workers_see_assigned_participants"
}
```

Rules:
- `global` scope → no RLS restriction (admin roles)
- `own_only` scope → `auth.uid() = {scope_field}`
- `assigned_only` scope → `auth.uid() IN (SELECT ... FROM junction_table)`
- `team-scoped` → `auth.uid() IN (SELECT id FROM staff WHERE team_id = {entity}.team_id)`

### 4c. Screen-level access

Derive which screens each role can navigate to:

```json
{
  "role": "support_worker",
  "accessible_screens": ["SCR-DASH-001", "SCR-SCHED-002", "SCR-CASE-001", "SCR-TIME-001"],
  "hidden_screens": ["SCR-CRM-001", "SCR-FIN-001", "SCR-ADMIN-001"]
}
```

Source: `page_structure.pages[].roles[]` — if role not in page roles, screen is hidden.

### 4d. Validate completeness

- Every role must have policies for every entity
- External roles should have minimal permissions
- Admin roles should have full access
- Every screen must be accessible by at least one role

---

## Stage 5: Integration Architecture

Define API contracts and data sync patterns.

### 5a. Extract integration points

**Source:** `proposed_changes[].research.custom_build_option` integration needs + `requirements_spec` data flows

Each integration point already contains:
- `tool_a`, `tool_b` — the two systems
- `integration_type` — native, api, manual, apps_script, zapier, webhook
- `notes` — description

### 5b. Expand with API details

For each integration, enrich using `proposed_changes[].research.tools_researched[]`:
- Find the tool in `tools_researched[]` and extract: `api_available`, `api_notes`, `docs_url`
- Determine data direction from the process step `data_flow`:
  - If data originates in tool_a and is consumed by tool_b → `outbound`
  - If data flows both ways → `bidirectional`
  - If tool_a reads from tool_b → `inbound`

```json
{
  "integration_id": "INT-001",
  "name": "Xero Accounting Sync",
  "source": "APG Platform",
  "target": "Xero",
  "type": "REST API",
  "direction": "bidirectional",
  "auth_method": "OAuth2",
  "endpoints": [
    {"method": "POST", "path": "/api.xro/2.0/Invoices", "purpose": "Create invoice in Xero"},
    {"method": "GET", "path": "/api.xro/2.0/Contacts", "purpose": "Sync contacts from Xero"}
  ],
  "trigger": "Invoice created in platform",
  "sync_frequency": "real-time (webhook) + daily reconciliation",
  "entities_synced": ["Invoice", "Contact", "Payment"],
  "field_mappings": [
    {"platform_field": "participant.name", "external_field": "Contact.Name"},
    {"platform_field": "invoice.total", "external_field": "Invoice.Total"}
  ],
  "error_handling": "Queue failed syncs, retry 3x with exponential backoff, alert admin on persistent failure"
}
```

### 5c. Platform implementation specs

For each integration, define the Supabase implementation:

```json
{
  "implementation": {
    "type": "edge_function",
    "function_name": "sync-xero-invoice",
    "trigger": "database webhook on invoices.insert",
    "cron": "0 2 * * * (daily reconciliation at 2am)",
    "secrets": ["XERO_CLIENT_ID", "XERO_CLIENT_SECRET"],
    "estimated_complexity": "medium"
  }
}
```

Types:
- `edge_function` — Supabase Edge Function (Deno) for API calls
- `webhook` — Platform exposes an endpoint for external system to push data
- `cron` — Scheduled sync via pg_cron or Edge Function scheduler
- `realtime` — Supabase Realtime subscription triggers sync

---

## Stage 5b: Tech Stack Specification

Generate the APG Unified Platform tech stack specification:

```json
{
  "tech_stack": {
    "framework": "Next.js 15 (App Router)",
    "language": "TypeScript 5.3+",
    "ui_library": "Untitled UI (200+ components)",
    "css": "Tailwind CSS 4",
    "state": "Zustand + React Query",
    "api": "tRPC + Supabase auto-generated REST",
    "database": "PostgreSQL 15 via Supabase",
    "auth": "Supabase Auth (email/password, magic links, 2FA)",
    "storage": "Supabase Storage (S3-compatible)",
    "realtime": "Supabase Realtime (WebSocket)",
    "hosting": "Vercel (edge) + Supabase (Sydney region)",
    "external_apis": [],
    "template_modules": [],
    "custom_modules": []
  }
}
```

Populate `external_apis` from integration architecture (Stage 5).
Populate `template_modules` and `custom_modules` from module inventory (Stage 0b).

---

## Stage 6: Write Architecture to Audit Data

Write the `architecture_doc` to the audit data:
- v4: load `clients/{slug}/03-audit/data/architecture.json`, merge `architecture_doc` into the existing dict, write the full dict back to `clients/{slug}/03-audit/data/architecture.json`, then update `audit-manifest.json`: set `domains.architecture.updated_at` and root `updated_at`.
- v3: write into `architecture.architecture_doc` in `audit-data.json`
- v2: write to top-level `architecture_doc` in `audit-data.json`

```json
{
  "architecture_doc": {
    "generated_at": "ISO timestamp",
    "strategy": "apg-unified-platform",
    "module_inventory": [],
    "user_journeys": [
      {
        "role": "operations_manager",
        "journey_name": "Daily scheduling workflow",
        "module": "Scheduling Engine",
        "change_ids": ["CH-006", "CH-007"],
        "steps": [
          {
            "screen": "SCR-SCHED-001",
            "action": "View weekly roster",
            "data_shown": ["staff_availability", "participant_appointments"],
            "data_input": [],
            "next": "SCR-SCHED-002"
          }
        ]
      }
    ],
    "page_structure": {
      "pages": [
        {
          "screen_id": "SCR-CRM-001",
          "name": "Lead Pipeline",
          "route": "/crm/leads",
          "parent": "/crm",
          "module": "CRM Module",
          "roles": ["admin", "operations_manager"],
          "components": ["Table", "Input", "Pagination", "Badge", "Dropdown", "Button"]
        }
      ],
      "navigation": [
        {
          "section": "CRM",
          "module": "CRM Module",
          "items": [
            {"label": "Leads", "route": "/crm/leads", "icon": "Users01", "roles": ["admin", "operations_manager"]}
          ]
        }
      ]
    },
    "data_models": [
      {
        "entity": "Participant",
        "table_name": "participants",
        "module": "CRM Module",
        "fields": [],
        "relationships": []
      }
    ],
    "access_policies": [
      {
        "role": "support_worker",
        "permission_level": "standard",
        "entity_policies": [
          {"entity": "Participant", "read": "assigned_only", "write": "case_notes_only", "delete": false, "scope_field": "assigned_worker_id"}
        ],
        "rls_policies": [
          {"entity": "Participant", "policy_name": "workers_see_assigned", "rls_policy": "auth.uid() IN (...)"}
        ],
        "screen_access": {
          "accessible": ["SCR-DASH-001", "SCR-SCHED-002"],
          "hidden": ["SCR-CRM-001", "SCR-FIN-001"]
        }
      }
    ],
    "integration_architecture": [
      {
        "integration_id": "INT-001",
        "name": "Xero Accounting Sync",
        "source": "APG Platform",
        "target": "Xero",
        "type": "REST API",
        "direction": "bidirectional",
        "endpoints": [],
        "trigger": "Invoice created",
        "implementation": {"type": "edge_function", "function_name": "sync-xero-invoice"}
      }
    ],
    "tech_stack": {}
  }
}
```

Update `architect_metadata`:
```json
{
  "last_ba_run": "ISO timestamp",
  "total_ba_runs": 1
}
```

---

## Display Summary

```
ARCHITECTURE BUILT — {company_name}
Strategy:         APG Unified Platform (custom build alternative)
Modules:          {n} modules ({n} template, {n} custom)

User Journeys:    {n} journeys across {n} roles
Pages:            {n} pages ({n} top-level, {n} nested)
Data Models:      {n} entities, {n} relationships, {n} fields total
Access Policies:  {n} role policies, {n} RLS rules
Integrations:     {n} integration specs ({n} edge functions, {n} webhooks, {n} cron jobs)
Tech Stack:       {framework} + {database} + {n} external APIs

This is INTERNAL documentation only — never shown to clients.
Next step: Run [BP] to generate clickable prototype from this architecture.
```
