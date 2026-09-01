# Key Intelligence Question Library

KIQs define what must be known about a client's business BEFORE extraction begins.
Every unresolved KIQ after full ingestion is a confirmed Type A gap.

Format: KIQ-[STAGE]-[NNN]

---

## Universal KITs (apply to all clients)

### KIT-ACQ: Customer Acquisition

KIQ-ACQ-001: How does a new customer inquiry first reach the business?
  Expected fields: entry_step_id, channel (phone/email/web/walk-in/referral), step actor

KIQ-ACQ-002: What qualifies a lead as worth pursuing? Is there a formal qualification step?
  Expected fields: decision gateway after initial contact, condition criteria

KIQ-ACQ-003: Who handles initial customer contact and through what system?
  Expected fields: actor on first steps, tool_ids on those steps

KIQ-ACQ-004: What data is captured about the prospect and where is it stored?
  Expected fields: tool_ids for CRM/records, iato.output on capture step

KIQ-ACQ-005: What is the typical time from first inquiry to first meeting or quote?
  Expected fields: time_estimate on interim steps, or business_metrics entry

KIQ-ACQ-006: What percentage of inquiries convert to a quote/proposal?
  Expected fields: volume_split on qualification gateway, or business_metrics entry

### KIT-QUO: Quoting and Estimation

KIQ-QUO-001: What triggers a quote or proposal?
  Expected fields: start_event or intermediate_catch_event for quoting process

KIQ-QUO-002: What information is needed before a quote can be prepared?
  Expected fields: iato.input on first estimation step

KIQ-QUO-003: Who is responsible for preparing the quote and what tools do they use?
  Expected fields: actor and tool_ids on estimation steps

KIQ-QUO-004: Does a quote require approval before it goes to the client? Under what conditions?
  Expected fields: exclusive_gateway with gateway_anatomy.condition (threshold, job type, etc.)

KIQ-QUO-005: How long does quote preparation typically take?
  Expected fields: time_estimate_hours_per_week on quoting steps

KIQ-QUO-006: How is the quote delivered to the client and in what format?
  Expected fields: send_task or iato.output on final quoting step

KIQ-QUO-007: What is the typical win rate on quotes and how are losses tracked?
  Expected fields: gateway_anatomy on acceptance/rejection gateway, volume_split

### KIT-DEL: Service Delivery / Fulfilment

KIQ-DEL-001: What triggers the start of delivery or fulfilment once a job is won?
  Expected fields: intermediate_catch_event or start_event for delivery process

KIQ-DEL-002: How are jobs scheduled and resources allocated?
  Expected fields: scheduling steps with tool_ids and actor

KIQ-DEL-003: Is there a quality check or sign-off before the deliverable reaches the client?
  Expected fields: gateway or intermediate event for quality/approval

KIQ-DEL-004: How are exceptions or problems during delivery handled?
  Expected fields: error event or exception gateway in delivery process

KIQ-DEL-005: How does the client confirm completion or provide sign-off?
  Expected fields: receive_task or end event triggered by client confirmation

KIQ-DEL-006: How long does a typical job take from start to completion?
  Expected fields: time_estimate at process level or business_metrics

### KIT-INV: Invoicing and Payment

KIQ-INV-001: What triggers invoice generation — job completion, milestone, time period?
  Expected fields: intermediate_catch_event or start_event for invoicing process

KIQ-INV-002: Who generates invoices and in what system?
  Expected fields: actor and tool_ids on invoice generation step

KIQ-INV-003: What is the typical payment terms and collection process?
  Expected fields: time_estimate on payment wait, follow-up steps

KIQ-INV-004: How is a payment received and reconciled against the invoice?
  Expected fields: reconciliation steps, tool_ids (accounting system)

KIQ-INV-005: What happens when a client doesn't pay on time?
  Expected fields: gateway or exception path for late payment

### KIT-OPS: Operations and Workforce Management

KIQ-OPS-001: How are staff/subcontractors scheduled and notified of jobs?
  Expected fields: scheduling steps, notification tool

KIQ-OPS-002: How is time tracked and how does it flow into payroll?
  Expected fields: timesheet steps, payroll steps, handoff between them

KIQ-OPS-003: How are subcontractor invoices managed and approved?
  Expected fields: approval steps for subcontractor invoices

---

## Industry-Specific KITs

### Industry: Construction (use when industry_tag = "construction" or "trade")

KIQ-CON-001: How are variations to the original scope documented and approved?
  Expected fields: variation gateway, approval steps, documentation tool

KIQ-CON-002: How are progress claims structured and when are they submitted?
  Expected fields: milestone events, claim generation steps

KIQ-CON-003: How are subcontractor invoices reviewed against progress?
  Expected fields: review steps, approval gateway

KIQ-CON-004: Is there a formal practical completion or defects liability process?
  Expected fields: completion gateway, defects steps

KIQ-CON-005: How is site safety documentation managed (SWMS, inductions)?
  Expected fields: safety steps, tool for safety records

### Industry: NDIS / Support Work (use when industry_tag = "ndis" or "disability_services")

KIQ-NDIS-001: How are NDIS plans and funding reviewed before services begin?
  Expected fields: plan review steps, portal tool

KIQ-NDIS-002: How are support worker shifts matched to participant needs?
  Expected fields: matching/rostering steps, rostering tool

KIQ-NDIS-003: How is service delivery documented for NDIS compliance?
  Expected fields: shift note steps, documentation tool

KIQ-NDIS-004: How are NDIS claims submitted and how often?
  Expected fields: claims steps, portal tool, frequency

KIQ-NDIS-005: How are incidents or complaints managed and documented?
  Expected fields: incident steps, reporting gateway

### Industry: Home Services (use when industry_tag = "home_services" or "field_service")

KIQ-HOME-001: How are jobs booked — phone, app, website? Is there a booking system?
  Expected fields: booking step, tool, channel

KIQ-HOME-002: How are technicians dispatched to jobs?
  Expected fields: dispatch steps, dispatch tool or method

KIQ-HOME-003: Is there a follow-up process after job completion?
  Expected fields: follow-up steps, review request, rebooking

KIQ-HOME-004: How are parts/materials managed — stock, ordering, reimbursement?
  Expected fields: parts steps, inventory tool

### Industry: Real Estate (use when industry_tag = "real_estate" or "property_management")

KIQ-RE-001: How are new property listings processed end to end?
  Expected fields: listing steps, portal tool

KIQ-RE-002: How are maintenance requests from tenants managed?
  Expected fields: maintenance request steps, trade coordination

KIQ-RE-003: How is rental income collected and reconciled?
  Expected fields: collection steps, trust accounting tool

KIQ-RE-004: How are lease renewals and inspections scheduled?
  Expected fields: renewal steps, inspection steps

---

## How to Use This Library

1. Before starting extraction, identify `industry_tag` from meta.json or client context
2. Load Universal KITs (always applicable) + the matching Industry KIT
3. For each KIQ, check if the expected fields already exist in extraction.json
4. Pass the list of UNRESOLVED KIQs to sub-agents in their context packet
5. Sub-agents output `kiq_evidence[]` — which KIQs they found evidence for
6. After all sub-agents complete: any KIQ with no evidence = confirmed Type A gap
