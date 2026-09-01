# Audit Completeness Checklist

Used by the Analyst agent to track coverage per stage. A stage is `covered: true` only when the consultant confirms it, not when items are inferred.

## Per-Stage Checklist

Apply this checklist to **each stage** discovered in `processes[]`. Stages are dynamic, derived from transcript analysis, not a fixed list. Common examples: Acquisition, Quoting, Onboarding, Fulfilment, Retention, Property Management, Recruitment, etc.

### For every stage:
- [ ] Core process steps described end-to-end (complete workflow, not just highlights)
- [ ] Staff roles involved named (who does what)
- [ ] Tools used in this stage named (software, platforms, manual methods)
- [ ] Time spent per unit of work stated (hours/week, hours/task, hours/client)
- [ ] Volume/frequency stated (per week, per month, per year)
- [ ] Pain points identified (or confirmed none exist)
- [ ] Handoff to/from other stages described (who triggers, how data moves)
- [ ] Exception handling described (what happens when things go wrong)

---

## Industry Variants

### NDIS / Support Work (additional items)

**Compliance & Documentation**
- [ ] NDIS portal usage described (participant plans, claiming)
- [ ] Progress note process described (how, who, tool, frequency)
- [ ] Support worker onboarding described (compliance docs, NDIS worker screening)
- [ ] Participant funding tracking described (how balances are monitored)
- [ ] Incident reporting process described

**Common tools to verify:** Careview, ShiftCare, Xero, NDIS portal, HubSpot, ServiceM8

### Home Services (additional items)

**Field Operations**
- [ ] On-site vs remote quoting process described
- [ ] Job scheduling and dispatch process described (how jobs are assigned)
- [ ] Subcontractor vs employee ratio mentioned
- [ ] Materials/parts ordering process described
- [ ] Job completion sign-off described (photos, client sign, app)
- [ ] Review collection trigger described (Google/Facebook)

**Common tools to verify:** ServiceM8, Tradify, simPRO, Xero, Google My Business

### Construction (additional items)

**Project Management**
- [ ] Project estimation/scope process described
- [ ] Variation management described (how scope changes are handled)
- [ ] Subcontractor management described (scheduling, compliance, invoicing)
- [ ] Progress claim / payment schedule described
- [ ] Site safety documentation described
- [ ] Project handover process described

**Common tools to verify:** BuildXact, Procore, Airtable, Xero, Microsoft Project

### Real Estate (additional items)

**Sales & Property Management**
- [ ] Listing to contract process described
- [ ] Property management onboarding described
- [ ] Routine inspection process described
- [ ] Maintenance request handling described
- [ ] Rental arrears process described

**Common tools to verify:** REX, PropertyMe, Console Cloud, Xero, DocuSign

---

## Coverage Rating Guide

| Rating | Meaning |
|--------|---------|
| **HIGH confidence** | Multiple explicit statements with specifics: times, volumes, names |
| **MEDIUM confidence** | Process described but key data (times, volumes) not stated |
| **LOW confidence** | Stage mentioned but not described, needs follow-up |
| **Not covered** | No mention at all, must be on follow-up agenda |

---

## Opportunity Quantification Checklist

Used by the GQ (Generate Questions) capability to audit opportunity item readiness. An opportunity is "quantified" only when all required fields are populated with real (not estimated) data.

### Per waste_item (time-based, standard model)
- [ ] `hours_per_week` populated (null = hard gap)
- [ ] `headcount_affected` populated (null = gap; 1 acceptable if single person stated)
- [ ] `annual_waste_aud` calculable: hrs/wk × headcount × $50 × 52 (the canonical blended rate)
- [ ] `confidence` is HIGH or MEDIUM (LOW items don't appear on waste.html)

### Per waste_item (revenue leakage, hours_per_week N/A by design)
- [ ] Volume metric stated (occurrences per year, lost leads per month, families affected, etc.)
- [ ] Per-unit value stated (avg plan value, avg customer lifetime value, avg job value, etc.)
- [ ] Miss/loss rate stated (% missed, % churned, % paying cash directly, etc.)
- [ ] `annual_waste_aud` calculated from volume × value × rate

### Blended rate (no longer gated)
- [ ] `blended_hourly_rate_aud` is `50` (the canonical assumed blended team rate). Per-staff pay is out of scope and is never collected.

### Volume multipliers
- [ ] New clients/families per week stated (unlocks per-onboard waste items)
- [ ] New staff/workers onboarded per week stated (unlocks per-onboard waste items)
- [ ] Active client count stated (unlocks revenue leakage calculations)
- [ ] Lead volume per month stated (unlocks conversion/nurture waste items)
