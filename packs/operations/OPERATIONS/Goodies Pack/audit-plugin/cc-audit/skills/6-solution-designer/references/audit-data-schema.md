# Audit Data Schema — Solution Architect Reference

> Canonical schema: `apg-audit-plugin/references/audit-data-schema.md`
> This file defines what Agent 6 (Designer) reads and writes. For full field definitions, see the canonical schema.
>
> **Schema v3.0.0** — fields now nested in domains. Use `domain.field` paths when reading or writing (e.g. `architecture.requirements_spec`, `opportunities.proposed_changes[]`). v2 flat files are still supported via the backward-compat flattener in `audit_reader.py`.

## Fields the Solution Architect Reads (v3 domain paths)

| Field (v3 path) | Source | Used by |
|-------|--------|---------|
| `opportunities.proposed_changes[]` | Researcher EI/RI | RE (decomposition) |
| `opportunities.proposed_changes[].implementation` | Researcher BR | RE (scope estimation) |
| `opportunities.proposed_changes[].value` | Researcher BR | RE (priority weighting, all value dimensions) |
| `opportunities.proposed_changes[].proposed_tools[]` | Researcher EI/RI | RE (integration specs) |
| `opportunities.proposed_changes[].depends_on` | Researcher TB | RE (dependency mapping) |
| `opportunities.proposed_changes[].phase` | Researcher TB | RE (phase-aware requirements) |
| `opportunities.proposed_changes[].modal_content` | Researcher BR | RE (user story derivation) |
| `opportunities.proposed_changes[].affected_step_ids` | Researcher EI | RE (screen inventory, data model) |
| `opportunities.proposed_changes[].research` | Researcher RI | RE (integration specs, API details, pricing) |
| `opportunities.proposed_changes[].research.tools_researched[].hidden_costs[]` | Researcher RI | BC (net saving calculation) |
| `opportunities.proposed_changes[].research.tools_researched[].total_cost_with_hidden_aud` | Researcher RI | BC (true cost comparison) |
| `opportunities.proposed_changes[].research.tools_researched[].pricing_source_type` | Researcher RI | BC (pricing confidence) |
| `opportunities.proposed_changes[].research.tools_researched[].requires_paid_plan` | Researcher RI | RE (realistic costing) |
| `opportunities.proposed_changes[].research.tools_researched[].realistic_tier` | Researcher RI | RE (tier assessment) |
| `opportunities.proposed_changes[].research.tools_researched[].realistic_annual_cost_aud` | Researcher RI | RE (cost comparison) |
| `opportunities.proposed_changes[].research.tools_researched[].free_plan_limitations[]` | Researcher RI | RE (limitation analysis) |
| `opportunities.proposed_changes[].research.tools_researched[].setup_cost_aud` | Researcher RI | RE (implementation costing) |
| `opportunities.proposed_changes[].research.tools_researched[].data_silo_risk` | Researcher RI | RE (integration assessment) |
| `opportunities.proposed_changes[].linked_pain_point_ids` | Researcher EI | VA (trace chain), BC (scene extraction) |
| `opportunities.proposed_changes[].linked_optimisation_ids` | Researcher EI | VA (trace chain) |
| `opportunities.proposed_changes[].plugin_candidate` | Researcher RI | BC (candidate filter) |
| `strategy.strategic_approaches` | Researcher SA | RE (cost comparison, data silos) |
| `strategy.transformation_blueprint` | Researcher TB | RE (phase structure reference) |
| `opportunities.risk_register[]` | Researcher RI/BR | RE (risk-aware requirements), VA (coverage matrix) |
| `extraction.business_metrics[]` | Extractor SU + RI | RE (KPI-linked requirements), BP (demo data) |
| `extraction.tools[]` | Extractor SU | RE (existing tool stack), BA (integration architecture) |
| `extraction.staff_roster[]` | Extractor SU | RE (user role identification), BP (prototype data) |
| `findings.waste_items[]` | Extractor SU | BP (prototype data) |
| `extraction.processes[].steps[]` | Extractor SU | RE (step context for requirements) |
| `findings.pain_points[]` | Extractor SU | VA (coverage matrix), BC (verbatim quote + Fathom link) |
| `findings.optimisations[]` | Extractor SU | VA (optimisation coverage) |
| `extraction.sessions[]` | Extractor SU | BC (resolve session to fathom_url) |
| `findings.change_readiness` | Extractor | RE (adoption requirements) |
| `architecture.requirements_spec` | Architect RE | BA (architecture source), BP (prototype source) |
| `architecture.architecture_doc` | Architect BA | VA (verification), BP (prototype generation) |
| `architecture.architecture_verification` | Architect VA | BP (prototype brief) |

## Fields the Solution Architect Writes (v3 domain paths)

- `architecture.requirements_spec` -- written by RE
- `architecture.architecture_doc` -- written by BA
- `architecture.architecture_verification` -- written by VA
- `architecture.cowork_demos[]` -- written by BC
- `architect_metadata` (root-level) -- written by all capabilities

See the canonical schema for full sub-object shapes.
