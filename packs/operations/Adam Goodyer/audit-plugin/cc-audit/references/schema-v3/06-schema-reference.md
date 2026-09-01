# 06 — v3 Schema Reference

> This is the canonical v3 schema template.
> New clients must start from this template (not the v2 schema in `references/audit-data-schema.md`).
> When Session 7 is complete, this content replaces `references/audit-data-schema.md`.

Schema version: **3.0.0**

---

## Top-Level Structure

```json
{
  "_schema_version": "3.0.0",
  "_section_index": {
    "meta":          { "key_count": 13, "line_start": 3,     "line_end": 55,    "written_by": "extractor" },
    "extraction":    { "key_count": 9,  "line_start": 56,    "line_end": 0,     "written_by": "extractor" },
    "findings":      { "key_count": 12, "line_start": 0,     "line_end": 0,     "written_by": "extractor" },
    "opportunities": { "key_count": 3,  "line_start": 0,     "line_end": 0,     "written_by": "researcher" },
    "strategy":      { "key_count": 2,  "line_start": 0,     "line_end": 0,     "written_by": "researcher" },
    "architecture":  { "key_count": 5,  "line_start": 0,     "line_end": 0,     "written_by": "designer" }
  },
  "meta": { ... },
  "extraction": { ... },
  "findings": { ... },
  "opportunities": { ... },
  "strategy": { ... },
  "architecture": { ... },
  "analyst_metadata": {},
  "architect_metadata": {}
}
```

Note: `line_start` and `line_end` in `_section_index` should be updated after every write to reflect actual line positions. Set to 0 when unknown.

---

## meta domain

Written by: Extractor (SU)
Read by: All agents, always

```json
"meta": {
  "_schema_version": "3.0.0",
  "client_slug": "",
  "company_name": "",
  "industry_tag": "home-services|ndis|construction|real-estate|cleaning|trades|professional-services|other",
  "audit_start_date": "YYYY-MM-DD",
  "audit_status": "in_progress|process_map_complete",
  "sessions_completed": 0,
  "google_drive_folder_url": "",
  "crm": {
    "contact_id": null,
    "lead_id": null,
    "project_id": null,
    "task_list_ids": {
      "extraction": null,
      "analysis": null,
      "deliverables": null,
      "solution_design": null
    },
    "last_synced": null
  },
  "contact": {
    "name": "",
    "role": "",
    "company_size": "",
    "revenue_range": "",
    "domain": "",
    "emails": []
  },
  "blended_hourly_rate_aud": null,
  "blended_rate_confidence": "HIGH|MEDIUM|LOW",
  "blended_rate_source": ""
}
```

- `audit_status`: state machine gate. `"in_progress"` during extraction sessions. Set to `"process_map_complete"` when all sessions are done — this unlocks the Researcher EI capability.
- `blended_hourly_rate_aud`: extracted from salary/pay rate data in transcripts. Used for all waste calculations. Fallback: 50 with confidence LOW.
- `crm.project_id`: if null, all CRM updates are skipped silently.

---

## extraction domain

Written by: Extractor (SU, merge-extraction, process-review)
Read by: Extractor, Researcher, Designer, Builder (process map, solutions overview)

```json
"extraction": {
  "processes": [
    {
      "stage": "scheduling",
      "label": "Scheduling & Dispatch",
      "owner": "Jordan",
      "steps": [
        {
          "step_id": "SCH-001",
          "type": "step|decision|pain|optimisation|automation|parallel_group",
          "label": "",
          "description": "",
          "tool_ids": [],
          "owner": "",
          "time_estimate_hours_per_week": null,
          "data_flow": "",
          "meeting_references": [{"session_id": "", "timestamp_seconds": null}],
          "branch_only": false,
          "parallel_group": null
        }
      ],
      "flows": [
        {"from": "step_id", "to": "step_id", "label": "", "condition": ""}
      ],
      "plugin_scope": {}
    }
  ],
  "decision_nodes": [
    {
      "node_id": "DN-001",
      "label": "",
      "step_id": "",
      "yes_label": "Yes",
      "no_label": "No",
      "yes_next": "step_id",
      "no_next": "step_id"
    }
  ],
  "tools": [
    {
      "tool_id": "T-001",
      "tool_name": "",
      "category": "",
      "monthly_cost_aud": null,
      "maturity_level": "core|supplementary|underutilised|workaround",
      "utilization_pct": null,
      "meeting_references": [],
      "workarounds": []
    }
  ],
  "staff_roster": [
    {
      "name": "",
      "role": "",
      "employment_type": "employee|contractor|owner",
      "hourly_rate_aud": null,
      "hours_per_week": null,
      "primary_processes": []
    }
  ],
  "business_metrics": [
    {
      "metric_id": "BM-001",
      "name": "",
      "current_value": null,
      "unit": "",
      "industry_benchmark": null,
      "top_quartile": null,
      "benchmark_source": "",
      "delta_narrative": ""
    }
  ],
  "business_stages_covered": [],
  "sessions": [
    {
      "session_id": "S1",
      "fathom_meeting_id": "",
      "fathom_url": "",
      "date": "YYYY-MM-DD",
      "analyzed": false,
      "stages_covered": []
    }
  ],
  "extracted_materials": [],
  "client_context": {
    "business_overview": "",
    "revenue_streams": [],
    "constraints": [],
    "strategic_notes": []
  }
}
```

---

## findings domain

Written by: Extractor (SU, merge-extraction, findings-review, waste-review, audit-check, generate-questions)
Read by: Extractor, Researcher, Builder (findings, waste, blueprint, process map heatmap)

```json
"findings": {
  "pain_points": [
    {
      "id": "PP-001",
      "title": "",
      "description": "",
      "source_quote": "",
      "speaker": "",
      "stage": "",
      "source_session": "S1",
      "source_timestamp_seconds": null,
      "priority": "HIGH|MEDIUM|LOW",
      "meeting_references": []
    }
  ],
  "pain_points_summary": {
    "top_themes": [],
    "highest_priority_count": 0
  },
  "optimisations": [
    {
      "id": "OPT-001",
      "description": "",
      "source_quote": "",
      "speaker": "",
      "stage": "",
      "opportunity_type": "automation|ai|integration|process|tool",
      "source_session": "S1",
      "meeting_references": []
    }
  ],
  "waste_items": [
    {
      "waste_id": "W-001",
      "title": "",
      "description": "",
      "waste_type": "manual-data-entry|duplicate-work|context-switching|communication-overhead|error-rework|waiting|manual-reporting|undocumented-process",
      "hours_per_week": null,
      "headcount_affected": null,
      "hourly_rate_aud": null,
      "rate_is_estimated": true,
      "annual_waste_aud": null,
      "confidence": "HIGH|MEDIUM|LOW",
      "stage": "",
      "source_quote": "",
      "speaker": "",
      "meeting_references": [],
      "linked_pain_point_ids": [],
      "linked_step_id": ""
    }
  ],
  "contradictions": [
    {
      "id": "CON-001",
      "description": "",
      "session_a": "",
      "session_b": "",
      "resolution_status": "unresolved|resolved",
      "resolution_note": ""
    }
  ],
  "follow_up_questions": [
    {
      "id": "FQ-001",
      "question": "",
      "priority": "HIGH|MEDIUM|LOW",
      "stage": "",
      "source_session": "",
      "status": "open|answered"
    }
  ],
  "follow_up_summary": "",
  "completeness_checklist": {
    "stage_name": {
      "status": "complete|partial|not_started",
      "gaps": []
    }
  },
  "change_readiness": {
    "score": "HIGH|MEDIUM|LOW",
    "evidence": [],
    "blockers": []
  },
  "objections": [],
  "positive_signals": [],
  "data_gaps": []
}
```

---

## opportunities domain

Written by: Researcher (EI creates, RI/SA/BR/VR enrich)
Read by: Researcher, Builder (solutions, blueprint), Designer

```json
"opportunities": {
  "proposed_changes": [
    {
      "change_id": "CHG-001",
      "title": "",
      "change_type": "automation|integration|ai|process|tool-replacement|custom-build",
      "source": "client|analyst",
      "solution_type": "plugin|saas|custom-build|process",
      "stage": "",
      "confidence": "HIGH|MEDIUM|LOW",
      "value_type": "time-saving|risk-reduction|revenue|compliance|customer-experience",
      "affected_step_ids": [],
      "linked_roi_item_id": "",
      "linked_pain_point_ids": [],
      "linked_optimisation_ids": [],
      "proposed_solution": "",
      "proposed_tools": [],
      "time_saving_minutes_per_occurrence": null,
      "frequency": "",
      "phase": 1,
      "phase_label": "",
      "sequence_order": 1,
      "depends_on": [],

      "research": {
        "tools_researched": [
          {
            "tool_name": "",
            "url": "",
            "pricing_aud": "",
            "api_available": null,
            "integrations": [],
            "verdict": "recommended|viable|not-suitable",
            "notes": ""
          }
        ],
        "custom_build_option": {
          "modules": [],
          "estimated_weeks": null,
          "tech_stack": []
        },
        "plugin_assessment": {
          "is_plugin_candidate": false,
          "plugin_title": "",
          "plugin_rationale": "",
          "plugin_scope": "",
          "target_user": ""
        },
        "status": "pending|complete"
      },

      "implementation": {
        "weeks_estimate": null,
        "effort_breakdown": {},
        "phase_placement": ""
      },

      "value": {
        "time_saving": {
          "hours_per_week": null,
          "hourly_rate_aud": null,
          "annual_saving_aud": null,
          "formula_summary": ""
        },
        "productivity_enhancement": {},
        "risk_reduction": {},
        "customer_experience": {},
        "scalability": {},
        "combined_annual_value_aud": null
      },

      "modal_content": {
        "problem_statement": "",
        "current_state": "",
        "proposed_solution": "",
        "value_delivered": "",
        "implementation_path": ""
      },

      "build_cost_range_aud": "",
      "payback_months": null,
      "risk_label": "LOW|MEDIUM|HIGH",
      "plugin_candidate": false,

      "future_step_label": "",
      "future_step_description": "",
      "future_step_tool_ids": [],
      "future_step_owner": "",
      "future_step_time_estimate_hours_per_week": null
    }
  ],
  "roi_items": [
    {
      "roi_id": "ROI-001",
      "linked_change_id": "",
      "description": "",
      "annual_saving_aud": null,
      "one_time_cost_aud": null,
      "payback_months": null
    }
  ],
  "risk_register": [
    {
      "risk_id": "RSK-001",
      "title": "",
      "description": "",
      "likelihood": "HIGH|MEDIUM|LOW",
      "impact": "HIGH|MEDIUM|LOW",
      "mitigation": "",
      "linked_change_ids": []
    }
  ]
}
```

---

## strategy domain

Written by: Researcher (SA capability)
Read by: Researcher, Builder (blueprint, strategic approaches), Designer

```json
"strategy": {
  "strategic_approaches": {
    "recommended_tier": "low_ticket|mid_ticket|high_ticket",
    "recommended_tier_rationale": "",
    "approach_rationale": {
      "evidence_items": [],
      "summary": ""
    },
    "service_tier_recommendation": {
      "low_ticket": {
        "label": "AI OS Setup",
        "price_range_aud": "$5,000 – $8,000",
        "description": "",
        "inclusions": []
      },
      "mid_ticket": {
        "label": "Plugin Suite",
        "price_range_aud": "$10,000 – $25,000",
        "description": "",
        "plugin_cards": [
          {
            "plugin_title": "",
            "plugin_scope": "",
            "target_user": "",
            "process": "",
            "pain_point_ids": [],
            "estimated_weeks": null,
            "price_range_aud": ""
          }
        ]
      },
      "high_ticket": {
        "label": "Custom Build",
        "price_range_aud": "$60,000+",
        "description": "",
        "modules": []
      }
    },
    "implementation_roadmap": {
      "foundation_layer": "",
      "starting_point": "",
      "stages": [],
      "end_state": ""
    },
    "verification": {}
  },
  "transformation_blueprint": {}
}
```

---

## architecture domain

Written by: Designer (RE, BA, VA, BP, BC capabilities)
Read by: Designer, Builder (comprehensive report only)

```json
"architecture": {
  "requirements_spec": {
    "requirements": [],
    "user_roles": [],
    "screen_inventory": [],
    "data_model": {
      "entities": [],
      "data_flows": []
    },
    "integrations": [],
    "summary": ""
  },
  "architecture_doc": {
    "module_inventory": [],
    "user_journeys": [],
    "page_structure": {
      "pages": [],
      "navigation": []
    },
    "data_models": [],
    "access_policies": [],
    "integration_architecture": [],
    "tech_stack": {}
  },
  "architecture_verification": {
    "coverage_matrix": [],
    "prototype_brief": [],
    "summary": ""
  },
  "cowork_demos": [],
  "branding": {
    "primary_color": "",
    "secondary_color": "",
    "logo_url": "",
    "font": ""
  }
}
```

---

## Root-Level Fields

```json
"analyst_metadata": {
  "last_run": "ISO-8601",
  "capabilities_run": [],
  "notes": ""
},
"architect_metadata": {
  "last_run": "ISO-8601",
  "capabilities_run": [],
  "notes": ""
}
```
