---
name: bpmn-examples
description: Gold-standard BPMN process extraction examples for the sub-agent. Shows the expected quality bar for labels, descriptions, element types, lane assignment, and sequence flow wiring.
---

# BPMN Process Extraction — Gold Standard Examples

## How to use these examples

Read these before emitting your `new_steps[]` and `new_sequence_flows[]`. They show the quality bar you must meet:

- **Labels** — short action verbs that pass the "Now I ___" test. Not "Quote Management" — "Build itemised quote in Simpro."
- **Descriptions** — 1–2 sentences explaining WHAT happens and WHERE. Include tool context and what triggers the next step.
- **Element types** — use the full vocabulary. Most steps are `task`, but use `exclusive_gateway`, `parallel_gateway`, `intermediate_catch_event`, `send_task`, `receive_task`, `service_task`, `manual_task`, `business_rule_task` where the pattern matches.
- **Annotations** — `["pain"]` on steps a person is doing but that are clearly broken or wasteful. `["automation"]` on steps the system executes without human action.
- **Lanes** — data-location-based (`system`, `external`, `offline`). Never named for a person or role.
- **Flows** — every step wired. Gateways have 2+ outgoing flows. Start and end events explicit. Default flow on exclusive gateways set correctly.

---

## Example 1: Sales Quoting Process

**Domain:** Trade/construction — lead enquiry through to job scheduled or quote declined.

**Elements demonstrated:**

| Element | Used for |
|---|---|
| `start_event` | Process entry point |
| `receive_task` | Inbound client enquiry email |
| `user_task` + `["pain"]` | Manual rate lookup in disconnected spreadsheet |
| `user_task` | Quote preparation and review |
| `exclusive_gateway` + `default_flow_id` | High-value quote threshold check |
| `parallel_gateway` (fork + join) | Simultaneous quote email + CRM log |
| `send_task` + `["automation"]` | System-generated quote email |
| `service_task` + `["automation"]` | Automated CRM status update |
| `intermediate_catch_event` + `timer` | 3-day response wait |
| `exclusive_gateway` | Client decision outcome |
| `end_event` (x2) | Job won / Quote declined |
| **4 lanes** | External (Client), Gmail, Excel/Local Files, Simpro |

```json
{
  "stage": "quoting",
  "label": "Sales Quoting",
  "owner": "",
  "process_id": "QUOT-sales-quoting",
  "parallel_tracks": null,
  "called_from": [],
  "calls": [],
  "lanes": [
    { "id": "external_client", "name": "External (Client)", "type": "external", "order": 1 },
    { "id": "Gmail",           "name": "Gmail",             "type": "system",   "order": 2 },
    { "id": "local_files",     "name": "Excel / Local Files","type": "offline",  "order": 3 },
    { "id": "Simpro",          "name": "Simpro",            "type": "system",   "order": 4 }
  ],
  "steps": [
    {
      "step_id": "QUO-S01",
      "bpmn_id": "Start_quoting",
      "element_type": "start_event",
      "annotations": [],
      "label": "Quote request arrives",
      "description": "A prospective client submits a job enquiry, triggering the quoting workflow.",
      "owner": "",
      "lane_id": "external_client",
      "confidence": "HIGH",
      "sources": [
        {
          "kind": "fathom",
          "quote": "Usually it comes in via email, sometimes they call first but we always get them to send through the scope so we've got it in writing",
          "speaker": "Sam Carter",
          "confidence": "HIGH",
          "session_id": 1,
          "timestamp_seconds": 312
        }
      ]
    },
    {
      "step_id": "QUO-001",
      "bpmn_id": "Task_QUO_001",
      "element_type": "task",
      "task_type": "receive_task",
      "annotations": [],
      "label": "Receive client job enquiry",
      "display_label": "Receive client job enquiry",
      "description": "Reads the inbound email, confirms the scope of works, and creates a new job record in Simpro. Attaches any drawings or site notes the client provided.",
      "owner": "Sam Carter",
      "lane_id": "Gmail",
      "tool_ids": ["Gmail", "Simpro"],
      "duration_per_instance_minutes": 10,
      "confidence": "HIGH",
      "iato": {
        "input": "Client email with job scope and any attached drawings",
        "action": "Reads email, confirms scope of works, and creates job record in Simpro",
        "actor": "Sam Carter (Estimator)",
        "output": "New job record in Simpro with attached scope documents"
      },
      "_gaps": null,
      "handoff": null,
      "sources": [
        { "kind": "fathom", "quote": "I read the email, create the job in Simpro straight away so it's not floating in my inbox", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 340 }
      ]
    },
    {
      "step_id": "QUO-002",
      "bpmn_id": "Task_QUO_002",
      "element_type": "task",
      "task_type": "user_task",
      "annotations": ["pain"],
      "label": "Look up applicable labour rate in rate spreadsheet",
      "display_label": "Look up applicable labour rate in rate spreadsheet",
      "description": "Opens a locally-saved Excel file to find the correct labour rate for the job type and region. The spreadsheet is not linked to Simpro and is updated manually whenever award rates change — the wrong rate has been used on quotes twice this year.",
      "owner": "Sam Carter",
      "lane_id": "local_files",
      "tool_ids": [],
      "time_estimate_hours_per_week": 2.0,
      "confidence": "HIGH",
      "iato": {
        "input": "Job type and region from the Simpro job record",
        "action": "Opens locally-saved Excel rate spreadsheet and looks up the correct labour rate for the job type and region",
        "actor": "Sam Carter (Estimator)",
        "output": "Labour rate figure used to populate Simpro quote line items"
      },
      "_gaps": null,
      "handoff": {
        "source_tool": "Simpro",
        "mechanism": "manual_export_import",
        "destination_tool": "Excel / Local Files",
        "data_transferred": "Job type and region used to look up rate — no automated link between systems"
      },
      "sources": [
        { "kind": "fathom", "quote": "We've got a spreadsheet with all the rates, it's not connected to anything, I just have to open it and check — it's annoying because if someone updates it I might not know", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 410 }
      ]
    },
    {
      "step_id": "QUO-003",
      "bpmn_id": "Task_QUO_003",
      "element_type": "task",
      "task_type": "user_task",
      "annotations": [],
      "label": "Build itemised quote in Simpro",
      "display_label": "Build itemised quote in Simpro",
      "description": "Creates line items for labour, materials, and subcontractor costs in the Simpro quoting module. Applies margin, adds standard terms, and generates a formatted PDF quote document.",
      "owner": "Sam Carter",
      "lane_id": "Simpro",
      "tool_ids": ["Simpro"],
      "duration_per_instance_minutes": 45,
      "confidence": "HIGH",
      "iato": {
        "input": null,
        "action": "Contact preferred supplier to request current materials pricing",
        "actor": "Sam Carter (Estimator)",
        "output": "Supplier pricing received by email"
      },
      "_gaps": {
        "missing_input": true,
        "missing_output": false,
        "missing_actor": false,
        "missing_action": false,
        "gap_type": null,
        "gap_note": "Trigger for contacting supplier not described — unclear what prompts this vs using standard rate schedule"
      },
      "handoff": {
        "source_tool": "Excel / Local Files",
        "mechanism": "copy_paste",
        "destination_tool": "Simpro",
        "data_transferred": "Labour rate figures copied from spreadsheet into Simpro quote line items"
      },
      "sources": [
        { "kind": "fathom", "quote": "So I do all the line items in Simpro, labour first then materials, it spits out a PDF at the end which is what goes to the client", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 480 }
      ]
    },
    {
      "step_id": "QUO-D01",
      "bpmn_id": "Gateway_QUO_D01",
      "element_type": "exclusive_gateway",
      "annotations": [],
      "label": "Quote value over $50K?",
      "description": "Quotes exceeding $50,000 require director sign-off before being sent to the client. Below that threshold, Sam can approve and send directly.",
      "owner": "Sam Carter",
      "lane_id": "Simpro",
      "default_flow_id": "SF-006",
      "confidence": "HIGH",
      "sources": [
        { "kind": "fathom", "quote": "Anything over fifty thousand I have to get James to look at it before it goes out, that's just policy", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 541 }
      ]
    },
    {
      "step_id": "QUO-004",
      "bpmn_id": "Task_QUO_004",
      "element_type": "task",
      "task_type": "user_task",
      "annotations": [],
      "label": "Email quote to director for sign-off",
      "display_label": "Email quote to director for sign-off",
      "description": "Emails the Simpro quote PDF to James (director) with a brief margin summary. James reviews scope, pricing, and risk exposure then replies with approval or change requests.",
      "owner": "Sam Carter",
      "lane_id": "Gmail",
      "tool_ids": ["Gmail"],
      "confidence": "MEDIUM",
      "iato": {
        "input": "Formatted PDF quote exported from Simpro",
        "action": "Emails PDF quote to director with a brief margin summary note",
        "actor": "Sam Carter (Estimator)",
        "output": "Quote PDF and margin summary in director's Gmail inbox awaiting approval"
      },
      "_gaps": null,
      "handoff": {
        "source_tool": "Simpro",
        "mechanism": "email_forward",
        "destination_tool": "Gmail",
        "data_transferred": "Quote PDF exported from Simpro and sent via Gmail to director"
      },
      "sources": [
        { "kind": "fathom", "quote": "I'll just fire it off to James with a note on the margin, he usually gets back to me same day", "speaker": "Sam Carter", "confidence": "MEDIUM", "session_id": 1, "timestamp_seconds": 572 }
      ]
    },
    {
      "step_id": "QUO-005",
      "bpmn_id": "Task_QUO_005",
      "element_type": "task",
      "task_type": "user_task",
      "annotations": [],
      "label": "Final check and lock quote document",
      "display_label": "Final check and lock quote document",
      "description": "Reviews the quote PDF one last time — line items, totals, payment terms, and contact details. Both the under-$50K path and the director-approved path converge here before the quote is dispatched.",
      "owner": "Sam Carter",
      "lane_id": "Simpro",
      "tool_ids": ["Simpro"],
      "duration_per_instance_minutes": 10,
      "confidence": "HIGH",
      "iato": {
        "input": "Draft quote PDF in Simpro (either under $50K or director-approved)",
        "action": "Reviews line items, totals, payment terms, and contact details — locks and finalises quote document",
        "actor": "Sam Carter (Estimator)",
        "output": "Locked, ready-to-dispatch quote PDF in Simpro"
      },
      "_gaps": null,
      "handoff": null,
      "sources": [
        { "kind": "fathom", "quote": "Before it goes out I just do a quick sanity check, make sure the totals add up and the client name is right", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 618 }
      ]
    },
    {
      "step_id": "QUO-PF01",
      "bpmn_id": "Gateway_QUO_PF01",
      "element_type": "parallel_gateway",
      "annotations": [],
      "label": "Dispatch quote and log activity",
      "description": "Triggers two simultaneous actions: emailing the quote to the client and updating the CRM pipeline status.",
      "owner": "",
      "lane_id": "Simpro",
      "confidence": "HIGH",
      "sources": [
        { "kind": "fathom", "quote": "When I hit send in Simpro it fires off the email and updates the status at the same time", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 650 }
      ]
    },
    {
      "step_id": "QUO-006",
      "bpmn_id": "Task_QUO_006",
      "element_type": "task",
      "task_type": "send_task",
      "annotations": ["automation"],
      "label": "Email quote PDF to client",
      "display_label": "Email quote PDF to client",
      "description": "Simpro sends the formatted quote PDF to the client's email address using the standard quote template. A copy lands in the Gmail sent folder automatically.",
      "owner": "",
      "lane_id": "Gmail",
      "tool_ids": ["Simpro", "Gmail"],
      "confidence": "HIGH",
      "iato": {
        "input": "Locked quote PDF in Simpro",
        "action": "Sends formatted quote PDF to client's email address using standard quote template",
        "actor": "Simpro (automated)",
        "output": "Quote PDF delivered to client's inbox; copy logged in Gmail sent folder"
      },
      "_gaps": null,
      "handoff": null,
      "sources": [
        { "kind": "fathom", "quote": "Simpro sends it out directly, I don't have to copy anything into Gmail, it all goes from there", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 661 }
      ]
    },
    {
      "step_id": "QUO-007",
      "bpmn_id": "Task_QUO_007",
      "element_type": "task",
      "task_type": "service_task",
      "annotations": ["automation"],
      "label": "Update quote status to Sent in CRM",
      "display_label": "Update quote status to Sent in CRM",
      "description": "Simpro automatically sets the quote record status to 'Sent' and logs the timestamp. This keeps the pipeline view current without any manual entry.",
      "owner": "",
      "lane_id": "Simpro",
      "tool_ids": ["Simpro"],
      "confidence": "HIGH",
      "iato": {
        "input": "Quote dispatch event from Simpro send action",
        "action": "Sets quote record status to 'Sent' and logs timestamp automatically",
        "actor": "Simpro (automated)",
        "output": "Quote record with status 'Sent' and dispatch timestamp in Simpro pipeline view"
      },
      "_gaps": null,
      "handoff": null,
      "sources": [
        { "kind": "fathom", "quote": "The status updates on its own when it goes out, so the pipeline is always accurate", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 671 }
      ]
    },
    {
      "step_id": "QUO-PJ01",
      "bpmn_id": "Gateway_QUO_PJ01",
      "element_type": "parallel_gateway",
      "annotations": [],
      "label": "Quote sent and CRM updated",
      "description": "Both parallel tasks complete before the process proceeds to await the client's response.",
      "owner": "",
      "lane_id": "Simpro",
      "confidence": "HIGH",
      "sources": [
        { "kind": "fathom", "quote": "Once it's sent and logged we're just waiting on the client", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 685 }
      ]
    },
    {
      "step_id": "QUO-008",
      "bpmn_id": "Event_QUO_008",
      "element_type": "intermediate_catch_event",
      "event_definition": "timer",
      "annotations": [],
      "label": "Await client response (3 business days)",
      "description": "Process pauses for up to 3 business days waiting for the client to respond. No automated follow-up or reminder exists at this point — Sam manually checks her inbox.",
      "owner": "",
      "lane_id": "Gmail",
      "confidence": "HIGH",
      "sources": [
        { "kind": "fathom", "quote": "We give them three days, after that I'll reach out if I haven't heard", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 720 }
      ]
    },
    {
      "step_id": "QUO-009",
      "bpmn_id": "Task_QUO_009",
      "element_type": "task",
      "task_type": "receive_task",
      "annotations": [],
      "label": "Receive client acceptance or rejection",
      "display_label": "Receive client acceptance or rejection",
      "description": "Client replies by email (or calls to confirm) with their decision. Sam reads the response and determines the next step.",
      "owner": "Sam Carter",
      "lane_id": "external_client",
      "tool_ids": ["Gmail"],
      "confidence": "HIGH",
      "iato": {
        "input": "Client reply email (or phone confirmation) with acceptance or rejection decision",
        "action": "Reads client response and determines whether to proceed with job creation or close as lost",
        "actor": "Sam Carter (Estimator)",
        "output": "Decision to proceed to job creation or mark as lost in Simpro"
      },
      "_gaps": null,
      "handoff": null,
      "sources": [
        { "kind": "fathom", "quote": "Usually they just reply to the email, occasionally they'll call but I always ask them to confirm in writing as well", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 755 }
      ]
    },
    {
      "step_id": "QUO-D02",
      "bpmn_id": "Gateway_QUO_D02",
      "element_type": "exclusive_gateway",
      "annotations": [],
      "label": "Quote accepted?",
      "description": "Client's reply determines whether to proceed to job creation or close the opportunity as lost.",
      "owner": "Sam Carter",
      "lane_id": "Simpro",
      "default_flow_id": "SF-017",
      "confidence": "HIGH",
      "sources": [
        { "kind": "fathom", "quote": "If they say yes, great, I create the job. If not I just mark it as lost in Simpro and that's that", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 790 }
      ]
    },
    {
      "step_id": "QUO-010",
      "bpmn_id": "Task_QUO_010",
      "element_type": "task",
      "task_type": "user_task",
      "annotations": [],
      "label": "Convert quote to job and schedule site visit",
      "display_label": "Convert quote to job and schedule site visit",
      "description": "Marks the quote as Won in Simpro, which automatically creates the job record. Sets an initial site visit date and assigns a field supervisor.",
      "owner": "Sam Carter",
      "lane_id": "Simpro",
      "tool_ids": ["Simpro"],
      "duration_per_instance_minutes": 10,
      "confidence": "HIGH",
      "iato": {
        "input": "Accepted quote record in Simpro and client confirmation",
        "action": "Converts quote to job using Simpro convert function, sets site visit date, and assigns field supervisor",
        "actor": "Sam Carter (Estimator)",
        "output": "Active job record in Simpro with site visit date and supervisor assigned"
      },
      "_gaps": null,
      "handoff": null,
      "sources": [
        { "kind": "fathom", "quote": "There's a convert button in Simpro, I hit that and it becomes a job, then I put in the site visit date and assign someone to it", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 820 }
      ]
    },
    {
      "step_id": "QUO-E01",
      "bpmn_id": "End_quoting_won",
      "element_type": "end_event",
      "annotations": [],
      "label": "Job scheduled — quote won",
      "description": "",
      "owner": "",
      "lane_id": "Simpro",
      "confidence": "HIGH",
      "sources": [
        { "kind": "fathom", "quote": "Once the job's in the system the scheduling team takes over from there", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 840 }
      ]
    },
    {
      "step_id": "QUO-E02",
      "bpmn_id": "End_quoting_declined",
      "element_type": "end_event",
      "annotations": [],
      "label": "Quote declined — opportunity closed",
      "description": "",
      "owner": "",
      "lane_id": "external_client",
      "confidence": "HIGH",
      "sources": [
        { "kind": "fathom", "quote": "I just mark it as lost, sometimes they come back later so I never delete them", "speaker": "Sam Carter", "confidence": "HIGH", "session_id": 1, "timestamp_seconds": 798 }
      ]
    }
  ],
  "sequence_flows": [
    { "id": "SF-001", "from": "QUO-S01",  "to": "QUO-001" },
    { "id": "SF-002", "from": "QUO-001",  "to": "QUO-002" },
    { "id": "SF-003", "from": "QUO-002",  "to": "QUO-003" },
    { "id": "SF-004", "from": "QUO-003",  "to": "QUO-D01" },
    { "id": "SF-005", "from": "QUO-D01",  "to": "QUO-004", "condition": "Yes — approval required" },
    { "id": "SF-006", "from": "QUO-D01",  "to": "QUO-005" },
    { "id": "SF-007", "from": "QUO-004",  "to": "QUO-005" },
    { "id": "SF-008", "from": "QUO-005",  "to": "QUO-PF01" },
    { "id": "SF-009", "from": "QUO-PF01", "to": "QUO-006" },
    { "id": "SF-010", "from": "QUO-PF01", "to": "QUO-007" },
    { "id": "SF-011", "from": "QUO-006",  "to": "QUO-PJ01" },
    { "id": "SF-012", "from": "QUO-007",  "to": "QUO-PJ01" },
    { "id": "SF-013", "from": "QUO-PJ01", "to": "QUO-008" },
    { "id": "SF-014", "from": "QUO-008",  "to": "QUO-009" },
    { "id": "SF-015", "from": "QUO-009",  "to": "QUO-D02" },
    { "id": "SF-016", "from": "QUO-D02",  "to": "QUO-010", "condition": "Accepted" },
    { "id": "SF-017", "from": "QUO-D02",  "to": "QUO-E02" },
    { "id": "SF-018", "from": "QUO-010",  "to": "QUO-E01" }
  ]
}
```

### Key decisions in this example

- **`QUO-002` is `["pain"]`** — it is a real action (opening a spreadsheet and reading it) that is genuinely broken. It passes the Action Test. The pain is modeled on the step, not as a separate pain_point.
- **`QUO-D01` has `default_flow_id: "SF-006"`** — the default path skips director approval (most quotes are under $50K). The "Yes" branch has an explicit `condition` label. The default branch has no condition label.
- **Parallel gateway pair (QUO-PF01 / QUO-PJ01)** — both outgoing flows from the fork merge at the join before the timer event. BJ10 balance: 1 fork, 1 join — balanced.
- **`QUO-008` is `intermediate_catch_event` with `event_definition: "timer"`** — process genuinely pauses here. Not a task, not a gateway.
- **Lanes are data-location-based** — "External (Client)" is where the client initiates and responds. "Gmail" is where email traffic lives. "Excel / Local Files" is where the disconnected spreadsheet lives (offline). "Simpro" is the operating system for all internal work.
- **Two end events** — one for each terminal outcome. Both have distinct `bpmn_id` values.

---

## Example 2: Construction Payroll Process

**Domain:** Construction — weekly timesheet submission through to bank transfer and payslip delivery.

**Elements demonstrated:**

| Element | Used for |
|---|---|
| `start_event` | Weekly pay period close trigger |
| `manual_task` + `["pain"]` | Paper timesheet completion (physical, no screen) |
| `user_task` + `["pain"]` | Manual re-entry of paper timesheets into system |
| `business_rule_task` + `["automation"]` | Automated project code validation |
| `exclusive_gateway` + `default_flow_id` | Validation error routing |
| `intermediate_catch_event` + `timer` | Payroll cutoff deadline hold |
| `parallel_gateway` (fork + join) | Concurrent base pay + allowances calculation |
| `service_task` + `["automation"]` (x3) | Automated pay calculations and bank transfer |
| `send_task` + `["automation"]` | Automated payslip emails |
| `business_rule_task` | Authorisation step |
| `end_event` (x2) | Payroll complete / Pay run rejected |
| **4 lanes** | Paper/Manual (offline), TimeTarget (system), Xero Payroll (system), ANZ Bank (external) |

```json
{
  "stage": "payroll_processing",
  "label": "Weekly Payroll Processing",
  "owner": "",
  "process_id": "PAY-weekly-payroll",
  "parallel_tracks": null,
  "called_from": [],
  "calls": [],
  "lanes": [
    { "id": "paper_manual",  "name": "Paper / Manual", "type": "offline",  "order": 1 },
    { "id": "TimeTarget",    "name": "TimeTarget",      "type": "system",   "order": 2 },
    { "id": "Xero_Payroll",  "name": "Xero Payroll",   "type": "system",   "order": 3 },
    { "id": "ANZ_Bank",      "name": "ANZ Bank",        "type": "external", "order": 4 }
  ],
  "steps": [
    {
      "step_id": "PAY-S01",
      "bpmn_id": "Start_payroll",
      "element_type": "start_event",
      "annotations": [],
      "label": "Pay period ends (Sunday midnight)",
      "description": "The weekly pay period closes automatically at midnight Sunday, triggering the timesheet collection and payroll processing cycle.",
      "owner": "",
      "lane_id": "paper_manual",
      "confidence": "HIGH",
      "sources": [
        {
          "kind": "fathom",
          "quote": "Pay week runs Monday to Sunday, so Sunday night is the cutoff and then we process on Monday and Tuesday",
          "speaker": "Karen Tran",
          "confidence": "HIGH",
          "session_id": 2,
          "timestamp_seconds": 188
        }
      ]
    },
    {
      "step_id": "PAY-001",
      "bpmn_id": "Task_PAY_001",
      "element_type": "task",
      "task_type": "manual_task",
      "annotations": ["pain"],
      "label": "Fill in paper timesheet for the week",
      "display_label": "Fill in paper timesheet for the week",
      "description": "Field worker records daily start time, finish time, break duration, and project code for each day on a pre-printed paper timesheet. Completed forms are dropped in the site office collection tray by Monday morning.",
      "owner": "Field Worker",
      "lane_id": "paper_manual",
      "tool_ids": [],
      "time_estimate_hours_per_week": 1.5,
      "confidence": "HIGH",
      "iato": {
        "input": "Completed work week — daily hours, breaks, and project codes from memory or site notes",
        "action": "Records daily start time, finish time, break duration, and project code on pre-printed paper timesheet for each day of the week",
        "actor": "Field Worker",
        "output": "Completed paper timesheet dropped in site office collection tray by Monday morning"
      },
      "_gaps": null,
      "handoff": null,
      "sources": [
        { "kind": "fathom", "quote": "The guys fill in the paper forms on site, they drop them in the box in the site office, that's been the process for years", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 220 }
      ]
    },
    {
      "step_id": "PAY-002",
      "bpmn_id": "Task_PAY_002",
      "element_type": "task",
      "task_type": "user_task",
      "annotations": ["pain"],
      "label": "Re-enter timesheet data into TimeTarget",
      "display_label": "Re-enter timesheet data into TimeTarget",
      "description": "Payroll officer manually keys each worker's hours and project codes from the paper timesheet into TimeTarget. No OCR or photo import exists. With 35 field staff, this takes approximately 4 hours each Monday.",
      "owner": "Karen Tran",
      "lane_id": "TimeTarget",
      "tool_ids": ["TimeTarget"],
      "time_estimate_hours_per_week": 4.0,
      "confidence": "HIGH",
      "iato": {
        "input": "Completed paper timesheets collected from site office tray",
        "action": "Manually keys each worker's daily hours and project codes from paper timesheet into TimeTarget — one person at a time for all 35 field staff",
        "actor": "Karen Tran (Payroll Officer)",
        "output": "All 35 field staff timesheet entries loaded into TimeTarget ready for validation"
      },
      "_gaps": null,
      "handoff": {
        "source_tool": "Paper / Manual",
        "mechanism": "paper",
        "destination_tool": "TimeTarget",
        "data_transferred": "Daily hours, break durations, and project codes for each of 35 field workers"
      },
      "sources": [
        { "kind": "fathom", "quote": "I sit there and type it all in, every single person, takes me most of Monday morning — it's the thing I'd most like to get rid of", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 265 }
      ]
    },
    {
      "step_id": "PAY-003",
      "bpmn_id": "Task_PAY_003",
      "element_type": "task",
      "task_type": "business_rule_task",
      "annotations": ["automation"],
      "label": "Validate hours against approved project codes",
      "display_label": "Validate hours against approved project codes",
      "description": "TimeTarget automatically checks each submitted entry against open project budgets and approved cost codes. Flags entries where the project code is closed, over budget, or does not match a known cost centre.",
      "owner": "",
      "lane_id": "TimeTarget",
      "tool_ids": ["TimeTarget"],
      "confidence": "HIGH",
      "iato": {
        "input": "All 35 field staff timesheet entries loaded into TimeTarget",
        "action": "Checks each entry against open project budgets and approved cost codes — flags closed codes, over-budget entries, and unknown cost centres",
        "actor": "TimeTarget (automated)",
        "output": "Validation error report listing any entries that failed code or budget checks"
      },
      "_gaps": null,
      "handoff": null,
      "sources": [
        { "kind": "fathom", "quote": "TimeTarget has validation built in, it tells me if a code doesn't exist or if the budget's blown, I get a report of the errors", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 310 }
      ]
    },
    {
      "step_id": "PAY-D01",
      "bpmn_id": "Gateway_PAY_D01",
      "element_type": "exclusive_gateway",
      "annotations": [],
      "label": "Validation errors found?",
      "description": "Determines whether any timesheet entries failed the project code or budget validation check.",
      "owner": "Karen Tran",
      "lane_id": "TimeTarget",
      "default_flow_id": "SF-006",
      "confidence": "HIGH",
      "sources": [
        { "kind": "fathom", "quote": "If there are errors I have to chase them down before I can move on, otherwise I go straight to processing", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 345 }
      ]
    },
    {
      "step_id": "PAY-004",
      "bpmn_id": "Task_PAY_004",
      "element_type": "task",
      "task_type": "user_task",
      "annotations": [],
      "label": "Contact worker and correct timesheet entries",
      "display_label": "Contact worker and correct timesheet entries",
      "description": "Karen phones the field worker or their site supervisor to confirm the correct project code, then updates the entry in TimeTarget. Repeat errors from the same worker are flagged to the site manager.",
      "owner": "Karen Tran",
      "lane_id": "TimeTarget",
      "tool_ids": ["TimeTarget"],
      "confidence": "HIGH",
      "iato": {
        "input": "TimeTarget validation error report with flagged entries",
        "action": "Phones field worker or their site supervisor to confirm correct project code, then updates the entry in TimeTarget",
        "actor": "Karen Tran (Payroll Officer)",
        "output": "Corrected timesheet entries in TimeTarget; repeat offenders flagged to site manager"
      },
      "_gaps": null,
      "handoff": null,
      "sources": [
        { "kind": "fathom", "quote": "I'll ring them or their supervisor, get the right code, fix it in TimeTarget — usually takes maybe 20 minutes if it's just one or two errors", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 380 }
      ]
    },
    {
      "step_id": "PAY-005",
      "bpmn_id": "Event_PAY_005",
      "element_type": "intermediate_catch_event",
      "event_definition": "timer",
      "annotations": [],
      "label": "Hold until Thursday 5pm payroll cutoff",
      "description": "All validated timesheets are held in a 'ready' state in TimeTarget until 5pm Thursday — the mandatory cutoff for the weekly pay run. Entries submitted after this point roll to the following week's run.",
      "owner": "",
      "lane_id": "TimeTarget",
      "confidence": "HIGH",
      "sources": [
        { "kind": "fathom", "quote": "We run payroll on Thursday afternoon, the cutoff is five o'clock, anything after that misses the run", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 420 }
      ]
    },
    {
      "step_id": "PAY-PF01",
      "bpmn_id": "Gateway_PAY_PF01",
      "element_type": "parallel_gateway",
      "annotations": [],
      "label": "Calculate pay components",
      "description": "Xero Payroll runs base pay and allowances/deductions calculations simultaneously as independent processes within the same pay run.",
      "owner": "",
      "lane_id": "Xero_Payroll",
      "confidence": "HIGH",
      "sources": [
        { "kind": "fathom", "quote": "Xero does the base pay and the allowances at the same time, it's all part of the one pay run", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 455 }
      ]
    },
    {
      "step_id": "PAY-006",
      "bpmn_id": "Task_PAY_006",
      "element_type": "task",
      "task_type": "service_task",
      "annotations": ["automation"],
      "label": "Calculate base pay and overtime",
      "display_label": "Calculate base pay and overtime",
      "description": "Xero Payroll applies the base hourly rate and overtime multiplier (1.5x after 38 hours ordinary time) for each employee based on hours imported from TimeTarget. Public holiday loadings are applied automatically.",
      "owner": "",
      "lane_id": "Xero_Payroll",
      "tool_ids": ["Xero Payroll", "TimeTarget"],
      "confidence": "HIGH",
      "iato": {
        "input": "Validated timesheet hours imported from TimeTarget into Xero Payroll",
        "action": "Applies base hourly rate and 1.5x overtime multiplier for hours over 38 — includes public holiday loadings",
        "actor": "Xero Payroll (automated)",
        "output": "Gross base pay and overtime totals per employee calculated in Xero Payroll"
      },
      "_gaps": null,
      "handoff": {
        "source_tool": "TimeTarget",
        "mechanism": "api_sync",
        "destination_tool": "Xero Payroll",
        "data_transferred": "Validated hours and project codes for all 35 employees"
      },
      "sources": [
        { "kind": "fathom", "quote": "It pulls the hours from TimeTarget, applies the rate, calculates overtime automatically — that bit I don't have to touch", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 468 }
      ]
    },
    {
      "step_id": "PAY-007",
      "bpmn_id": "Task_PAY_007",
      "element_type": "task",
      "task_type": "service_task",
      "annotations": ["automation"],
      "label": "Calculate allowances and deductions",
      "display_label": "Calculate allowances and deductions",
      "description": "Calculates site allowances, vehicle allowances, and voluntary deductions (salary sacrifice, union fees) for each employee based on their stored payroll configuration in Xero.",
      "owner": "",
      "lane_id": "Xero_Payroll",
      "tool_ids": ["Xero Payroll"],
      "confidence": "HIGH",
      "iato": {
        "input": "Employee payroll configuration records in Xero (allowance types, deduction elections per person)",
        "action": "Applies site allowances, vehicle allowances, and voluntary deductions per employee based on stored configuration",
        "actor": "Xero Payroll (automated)",
        "output": "Allowance and deduction totals per employee added to pay run in Xero Payroll"
      },
      "_gaps": null,
      "handoff": null,
      "sources": [
        { "kind": "fathom", "quote": "The allowances are set up per person in Xero, it applies them automatically each week, same with the deductions", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 480 }
      ]
    },
    {
      "step_id": "PAY-PJ01",
      "bpmn_id": "Gateway_PAY_PJ01",
      "element_type": "parallel_gateway",
      "annotations": [],
      "label": "Pay components calculated",
      "description": "Both parallel calculation tracks complete before the pay run moves to authorisation.",
      "owner": "",
      "lane_id": "Xero_Payroll",
      "confidence": "HIGH",
      "sources": [
        { "kind": "fathom", "quote": "Once both are done Xero has the full gross and net for each person ready to review", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 494 }
      ]
    },
    {
      "step_id": "PAY-008",
      "bpmn_id": "Task_PAY_008",
      "element_type": "task",
      "task_type": "business_rule_task",
      "annotations": [],
      "label": "Review and submit pay run for director authorisation",
      "display_label": "Review and submit pay run for director authorisation",
      "description": "Karen reviews the payroll summary — total gross, net, and PAYG tax — then submits the pay run in Xero for director authorisation. Director receives an email notification and approves directly in Xero.",
      "owner": "Karen Tran",
      "lane_id": "Xero_Payroll",
      "tool_ids": ["Xero Payroll"],
      "duration_per_instance_minutes": 20,
      "confidence": "HIGH",
      "iato": {
        "input": "Completed pay run in Xero with all base pay, overtime, allowances, and deductions calculated",
        "action": "Reviews payroll summary totals (gross, net, PAYG tax) for reasonableness, then submits pay run for director authorisation",
        "actor": "Karen Tran (Payroll Officer)",
        "output": "Pay run submitted in Xero with approval request notification sent to director"
      },
      "_gaps": null,
      "handoff": null,
      "sources": [
        { "kind": "fathom", "quote": "I check the totals make sense, submit it in Xero, and that sends an approval request to David — he clicks approve in Xero", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 528 }
      ]
    },
    {
      "step_id": "PAY-D02",
      "bpmn_id": "Gateway_PAY_D02",
      "element_type": "exclusive_gateway",
      "annotations": [],
      "label": "Pay run approved by director?",
      "description": "Director's decision determines whether to proceed with the bank transfer or hold the run for investigation.",
      "owner": "David Chen",
      "lane_id": "Xero_Payroll",
      "default_flow_id": "SF-016",
      "confidence": "HIGH",
      "sources": [
        { "kind": "fathom", "quote": "He either approves it and it processes, or he flags it and we stop — that's only happened twice, usually it just goes through", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 560 }
      ]
    },
    {
      "step_id": "PAY-009",
      "bpmn_id": "Task_PAY_009",
      "element_type": "task",
      "task_type": "user_task",
      "annotations": [],
      "label": "Raise payroll discrepancy report and hold run",
      "display_label": "Raise payroll discrepancy report and hold run",
      "description": "Documents the issue, notifies the director of the root cause, and holds the pay run in Xero until resolved. Affected workers are contacted directly to explain the delay.",
      "owner": "Karen Tran",
      "lane_id": "Xero_Payroll",
      "tool_ids": ["Xero Payroll"],
      "confidence": "MEDIUM",
      "iato": {
        "input": "Pay run rejected by director with unspecified discrepancy",
        "action": "Documents the discrepancy root cause in a written report, holds the pay run in Xero, and contacts affected workers to explain the delay",
        "actor": "Karen Tran (Payroll Officer)",
        "output": "Written discrepancy report; pay run held in Xero pending resolution"
      },
      "_gaps": null,
      "handoff": null,
      "sources": [
        { "kind": "fathom", "quote": "The two times it's happened I've written up what the problem was, put it in a report, and we've held the run until David and I worked it out", "speaker": "Karen Tran", "confidence": "MEDIUM", "session_id": 2, "timestamp_seconds": 590 }
      ]
    },
    {
      "step_id": "PAY-010",
      "bpmn_id": "Task_PAY_010",
      "element_type": "task",
      "task_type": "service_task",
      "annotations": ["automation"],
      "label": "Initiate ABA bank transfer to employee accounts",
      "display_label": "Initiate ABA bank transfer to employee accounts",
      "description": "Xero Payroll generates an ABA file and submits it electronically to ANZ Business Banking for batch payment processing. Funds clear in employee accounts by 9am Friday.",
      "owner": "",
      "lane_id": "ANZ_Bank",
      "tool_ids": ["Xero Payroll"],
      "confidence": "HIGH",
      "iato": {
        "input": "Director-approved pay run in Xero with final net pay figures per employee",
        "action": "Generates ABA file and submits it electronically to ANZ Business Banking for batch payment processing",
        "actor": "Xero Payroll (automated)",
        "output": "ABA batch payment file submitted to ANZ; funds clear in employee accounts by 9am Friday"
      },
      "_gaps": null,
      "handoff": {
        "source_tool": "Xero Payroll",
        "mechanism": "api_sync",
        "destination_tool": "ANZ Bank",
        "data_transferred": "ABA file with net pay amounts and employee bank account details for batch processing"
      },
      "sources": [
        { "kind": "fathom", "quote": "Xero sends the ABA file straight to ANZ, we don't have to log into the bank separately anymore, it just processes overnight", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 615 }
      ]
    },
    {
      "step_id": "PAY-011",
      "bpmn_id": "Task_PAY_011",
      "element_type": "task",
      "task_type": "send_task",
      "annotations": ["automation"],
      "label": "Email payslip to each employee",
      "display_label": "Email payslip to each employee",
      "description": "Xero automatically emails a PDF payslip to each employee's registered email address once the bank transfer is initiated. The payslip details gross pay, deductions, net pay, and year-to-date figures.",
      "owner": "",
      "lane_id": "Xero_Payroll",
      "tool_ids": ["Xero Payroll"],
      "confidence": "HIGH",
      "iato": {
        "input": "Completed pay run with bank transfer confirmed",
        "action": "Emails PDF payslip to each employee's registered email address automatically",
        "actor": "Xero Payroll (automated)",
        "output": "PDF payslip delivered to each of 35 employees' inboxes showing gross pay, deductions, net pay, and YTD figures"
      },
      "_gaps": null,
      "handoff": null,
      "sources": [
        { "kind": "fathom", "quote": "The payslips go out automatically from Xero, the guys get them on their phones, I don't have to do anything for that", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 640 }
      ]
    },
    {
      "step_id": "PAY-E01",
      "bpmn_id": "End_payroll_complete",
      "element_type": "end_event",
      "annotations": [],
      "label": "Payroll complete — funds transferred",
      "description": "",
      "owner": "",
      "lane_id": "ANZ_Bank",
      "confidence": "HIGH",
      "sources": [
        { "kind": "fathom", "quote": "That's it, done for the week — the guys get their money Friday morning", "speaker": "Karen Tran", "confidence": "HIGH", "session_id": 2, "timestamp_seconds": 658 }
      ]
    },
    {
      "step_id": "PAY-E02",
      "bpmn_id": "End_payroll_rejected",
      "element_type": "end_event",
      "annotations": [],
      "label": "Pay run rejected — investigation required",
      "description": "",
      "owner": "",
      "lane_id": "Xero_Payroll",
      "confidence": "MEDIUM",
      "sources": [
        { "kind": "fathom", "quote": "We hold everything until we know what the problem is, you can't run a partial payroll", "speaker": "Karen Tran", "confidence": "MEDIUM", "session_id": 2, "timestamp_seconds": 598 }
      ]
    }
  ],
  "sequence_flows": [
    { "id": "SF-001", "from": "PAY-S01",  "to": "PAY-001" },
    { "id": "SF-002", "from": "PAY-001",  "to": "PAY-002" },
    { "id": "SF-003", "from": "PAY-002",  "to": "PAY-003" },
    { "id": "SF-004", "from": "PAY-003",  "to": "PAY-D01" },
    { "id": "SF-005", "from": "PAY-D01",  "to": "PAY-004", "condition": "Yes — errors found" },
    { "id": "SF-006", "from": "PAY-D01",  "to": "PAY-005" },
    { "id": "SF-007", "from": "PAY-004",  "to": "PAY-005" },
    { "id": "SF-008", "from": "PAY-005",  "to": "PAY-PF01" },
    { "id": "SF-009", "from": "PAY-PF01", "to": "PAY-006" },
    { "id": "SF-010", "from": "PAY-PF01", "to": "PAY-007" },
    { "id": "SF-011", "from": "PAY-006",  "to": "PAY-PJ01" },
    { "id": "SF-012", "from": "PAY-007",  "to": "PAY-PJ01" },
    { "id": "SF-013", "from": "PAY-PJ01", "to": "PAY-008" },
    { "id": "SF-014", "from": "PAY-008",  "to": "PAY-D02" },
    { "id": "SF-015", "from": "PAY-D02",  "to": "PAY-009", "condition": "Rejected" },
    { "id": "SF-016", "from": "PAY-D02",  "to": "PAY-010" },
    { "id": "SF-017", "from": "PAY-009",  "to": "PAY-E02" },
    { "id": "SF-018", "from": "PAY-010",  "to": "PAY-011" },
    { "id": "SF-019", "from": "PAY-011",  "to": "PAY-E01" }
  ]
}
```

### Key decisions in this example

- **`PAY-001` is `manual_task`** — paper timesheet is a physical action, not on a screen. `manual_task` is the right type, not `user_task`.
- **`PAY-002` carries `["pain"]`** even though it is a `user_task` — re-entry of paper data into a system is a real discrete action AND it is genuinely painful/wasteful. Both the annotation and a corresponding `pain_points[]` entry are appropriate here.
- **`PAY-003` is `business_rule_task` + `["automation"]`** — the system applies defined rules (project code validation) automatically. The `business_rule_task` type signals policy-based logic; `["automation"]` signals no human action required.
- **`PAY-005` is `intermediate_catch_event` + `timer`** — the process genuinely waits for a specific time condition before proceeding. This is not a task; no human action happens here.
- **Parallel gateway pair (PAY-PF01 / PAY-PJ01)** — BJ10 balance: 1 fork, 1 join — balanced. Both outgoing flows from the fork (PAY-006, PAY-007) converge at the join (PAY-PJ01) before authorisation.
- **`PAY-D02` has `default_flow_id: "SF-016"`** — the approved/normal path is the default (no condition). The "Rejected" branch has an explicit condition label.
- **Lanes are data-location-based** — "Paper / Manual" is where data originates (offline). "TimeTarget" is the timesheet SaaS system. "Xero Payroll" is the payroll SaaS system. "ANZ Bank" is an external party the data flows to.
- **`time_estimate_hours_per_week`** on PAY-001 and PAY-002 is what feeds the waste calculator. Always capture this on painful, repetitive steps.
