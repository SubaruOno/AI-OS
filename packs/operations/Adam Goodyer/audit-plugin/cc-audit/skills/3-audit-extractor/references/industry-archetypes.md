# Industry Process Archetypes

Archetypes define the structural shape of a complete business process — which stages must be present.
Used only for binary structural checks: does this stage exist? Not for field values or thresholds.

---

## ARCHETYPE: SME Services (default fallback)

Required stages:
1. Lead/Inquiry Acquisition — how new work enters the business
2. Quoting or Proposal — how the scope and price is determined
3. Booking/Acceptance — how work is confirmed and scheduled
4. Service Delivery/Fulfilment — how the work is executed
5. Invoicing and Payment — how the business gets paid
6. Completion/Closeout — how the job is formally closed

Optional but common stages:
- Lead qualification (before quoting)
- Subcontractor management (if subcontractors used)
- Defects/warranty (if applicable)
- Re-engagement/upsell (retention)

---

## ARCHETYPE: Construction

Required stages:
1. Lead/Tender Acquisition
2. Estimating and Quoting
3. Contract Execution
4. Site Setup and Mobilisation
5. Construction/Works Execution
6. Progress Claims and Payment
7. Practical Completion
8. Defects Liability

Optional: Variation management, Subcontractor management, Safety management

---

## ARCHETYPE: NDIS / Support Work

Required stages:
1. Participant Intake and Plan Review
2. Rostering and Matching
3. Shift Delivery and Documentation
4. NDIS Claims Submission
5. Payment and Reconciliation

Optional: Incident management, Complaint handling, Plan review scheduling

---

## ARCHETYPE: Home Services / Field Service

Required stages:
1. Job Booking
2. Technician Dispatch and Scheduling
3. Job Execution (on-site)
4. Invoice Generation
5. Payment Collection

Optional: Parts/materials management, Follow-up and review, Re-booking

---

## ARCHETYPE: Real Estate / Property Management

Required stages:
1. Property Listing Management
2. Tenant/Buyer Inquiry Handling
3. Lease/Contract Processing
4. Maintenance and Repair Management
5. Rental Collection and Reconciliation
6. Inspection and Renewal Management

Optional: Trust accounting, Compliance reporting

---

## How to Use

1. Load meta.json to get industry_tag
2. Select the closest archetype (exact match, or SME Services as fallback)
3. For each required stage: check if extraction.json has at least one process/step covering this stage
4. Binary result: PRESENT or MISSING
5. MISSING required stages → add to follow_up_questions[] with priority HIGH
6. MISSING optional stages → add with priority MEDIUM (note as "commonly present in this industry")
