# Feedback Schema Reference

> Schema for `clients/{slug}/03-audit/data/reviews.json`. Domain: `reviews`. Written by: `reviewer`.

## Full Template

```json
{
  "review_rounds": [],
  "meta_learning": {
    "patterns": [],
    "last_pattern_analysis": null
  }
}
```

## Review Round Object

```json
{
  "round_id": "RR-001",
  "round_number": 1,
  "reviewer": {
    "name": "string",
    "role": "internal_pm | client | stakeholder",
    "trust_level": "full | advisory"
  },
  "source": {
    "type": "loom_video | local_video | text_input",
    "url": "string or null",
    "transcript_path": "reviews/RR-001/transcript.txt or null",
    "video_path": "reviews/RR-001/video.mp4 or null",
    "frames_dir": "reviews/RR-001/frames/ or null",
    "screen_context_path": "reviews/RR-001/screen-context.json or null",
    "duration_seconds": null,
    "recorded_at": "ISO8601 or null"
  },
  "ingested_at": "ISO8601",
  "status": "pending_approval | partially_applied | applied",
  "feedback_items": [],
  "unresolved_items": [],
  "summary": {
    "total_items": 0,
    "by_type": {
      "correction": 0,
      "removal": 0,
      "addition": 0,
      "clarification": 0,
      "endorsement": 0,
      "priority_change": 0
    },
    "by_severity": {
      "HIGH": 0,
      "MEDIUM": 0,
      "LOW": 0
    },
    "domains_affected": [],
    "items_applied": 0,
    "items_deferred": 0,
    "items_rejected": 0
  }
}
```

## Feedback Item Object

```json
{
  "feedback_id": "FB-001",
  "target_domain": "findings | opportunities | extraction | strategy | architecture",
  "target_path": "waste_items[waste_id=W-003]",
  "target_id": "W-003",
  "target_title": "Manual data entry during onboarding",
  "feedback_type": "correction | removal | addition | clarification | endorsement | priority_change",
  "severity": "HIGH | MEDIUM | LOW",
  "reviewer_statement": "Cleaned-up summary of what the reviewer said",
  "source_quote": "Verbatim words from the transcript",
  "source_timestamp_seconds": 45,
  "screen_context_note": "Reviewer was viewing waste.html, pointing at W-003 row (from frame analysis)",
  "proposed_changes": [
    {
      "field": "hours_per_week",
      "old_value": 10,
      "new_value": 1.5,
      "rationale": "Reviewer correction based on Jordan's confirmation"
    }
  ],
  "resolution": {
    "status": "pending | approved | rejected | deferred",
    "applied_at": null,
    "rejection_reason": null,
    "defer_note": null
  },
  "confidence": "HIGH | MEDIUM | LOW",
  "requires_cascade": false,
  "cascade_note": null
}
```

## Unresolved Item Object

```json
{
  "unresolved_id": "UR-001",
  "source_quote": "Verbatim words from transcript",
  "source_timestamp_seconds": 120,
  "reason_unresolved": "Could not determine which proposed_change the reviewer was referring to",
  "screen_context_note": "Reviewer was viewing solutions-overview.html at this timestamp",
  "manual_mapping": null
}
```

## Meta-Learning Pattern Object

```json
{
  "pattern_id": "ML-001",
  "observed_in_clients": ["client-slug-1", "client-slug-2"],
  "observed_in_rounds": ["RR-001"],
  "pattern_type": "systematic_overcount | systematic_undercount | hallucination | misattribution | missing_context | formatting_drift",
  "description": "Time estimates from staff self-reporting tend to be 2-3x actual when cross-checked by PM",
  "affected_agent": "extractor | researcher | designer",
  "affected_capability": "SU | EI | etc",
  "suggested_action": "Concrete recommendation for the relevant agent prompt",
  "occurrences": 4,
  "status": "observed | recommended | applied"
}
```

## Feedback Types

| Type | When to use |
|---|---|
| `correction` | Factual error: wrong number, wrong owner, wrong date, misattributed quote |
| `removal` | Item should not exist: hallucinated, irrelevant, duplicate |
| `addition` | Missing item the reviewer wants added (must provide content) |
| `clarification` | Item is factually correct but vague, misleading, or poorly worded |
| `endorsement` | Reviewer explicitly confirms an item is accurate (positive signal) |
| `priority_change` | Correct data but wrong severity, tier, or category |

## Trust Levels

| Level | Who | Behavior |
|---|---|---|
| `full` | Internal PM (Adam) | Items can be applied after PM approves in the IF table |
| `advisory` | Client or external stakeholder | Items are saved and presented to PM with a "client_suggested" tag — PM decides whether to apply |

## Severity Guidelines

| Severity | Criteria |
|---|---|
| `HIGH` | Affects financial calculations, invalidates a proposed change, or changes the conclusion |
| `MEDIUM` | Affects accuracy of a specific item without changing overall direction |
| `LOW` | Wording improvement, minor clarification, endorsement |

## Target Domain Mapping

| Reviewer says | Target domain | Example target_path |
|---|---|---|
| "This waste item" | `findings` | `waste_items[waste_id=W-003]` |
| "This pain point" | `findings` | `pain_points[pain_point_id=PP-007]` |
| "This proposed change / automation" | `opportunities` | `proposed_changes[change_id=CH-012]` |
| "This process step" | `extraction` | `processes[stage=onboarding].steps[step_id=S-015]` |
| "This tool" | `extraction` | `tools[tool_id=T-004]` |
| "This strategic approach / tier" | `strategy` | `strategic_approaches.service_tier_recommendation.mid_ticket` |
| "This ROI item" | `opportunities` | `roi_items[roi_item_id=R-003]` |

## Cascading Recalculations

When `findings.waste_items[].hours_per_week` or `headcount_affected` changes:
- Recalculate `annual_waste_aud = hours_per_week * 52 * headcount_affected * hourly_rate_aud`
- Recalculate `monthly_waste_aud = annual_waste_aud / 12`
- Check if the linked `opportunities.roi_items[].annual_saving_aud` references this waste item
- If yes: flag as cascade — ask whether to update the ROI item value too

When a `findings.waste_item` is removed:
- Check `opportunities.proposed_changes[].linked_roi_item_id` for references
- If a proposed change references a deleted waste/ROI item: flag as orphan

When a `findings.pain_point` is removed:
- Check `opportunities.proposed_changes[].linked_pain_point_ids[]` for references
- If a proposed change's only linked pain point was removed: flag as potentially orphaned
