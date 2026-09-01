# Feedback Log Schema

Version: 1.0.0

## Format

Append-only JSONL (one JSON object per line) at `{plugin-root}/data/feedback-log.jsonl`.

## Record Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | `FB-{plugin}-{capability}-{YYYYMMDD}-{NNN}` |
| `ts` | string | yes | ISO 8601 timestamp |
| `plugin` | string | yes | Plugin name: `audit`, `sales`, `project-management` |
| `skill` | string | yes | Skill folder name, e.g. `5-deliverable-builder` |
| `capability` | string | yes | Menu code, e.g. `GS`, `DR`, `EK` |
| `prompt_hash` | string | yes | First 6 hex chars of SHA-256 of the capability .md file |
| `output_type` | string | yes | What was produced, e.g. `solutions-overview.html`, `follow-up email`, `proposal PDF` |
| `had_adjustment` | boolean | yes | Whether the user requested a correction |
| `adjustment_description` | string | only if adjusted | One sentence: what was wrong and what changed |
| `root_cause` | string | only if adjusted | One of the constrained values below |
| `reviewer` | string | yes | Name of the team member who reviewed |

## Root Cause Values

| Value | When to use |
|---|---|
| `overconfidence` | Model asserted something too strongly or invented numbers |
| `missing_context` | Output was wrong because relevant context was not provided or loaded |
| `bad_instruction` | The capability prompt led the model in the wrong direction |
| `formatting` | Structure, layout, or formatting was wrong (content was fine) |
| `hallucination` | Model fabricated facts, quotes, or data that don't exist |
| `scope_creep` | Output included things outside the requested scope |
| `other` | None of the above, or user skipped the question |

## Example Records

```json
{"id":"FB-audit-GS-20260518-001","ts":"2026-05-18T03:42:00Z","plugin":"audit","skill":"5-deliverable-builder","capability":"GS","prompt_hash":"a3f2b1","output_type":"solutions-overview.html","had_adjustment":true,"adjustment_description":"ROI figures inflated, corrected hours_per_week for W-003","root_cause":"overconfidence","reviewer":"Jordan"}
{"id":"FB-sales-DR-20260518-002","ts":"2026-05-18T04:10:00Z","plugin":"sales","skill":"1-sales","capability":"DR","prompt_hash":"7c1e44","output_type":"follow-up email draft","had_adjustment":false,"reviewer":"Adam"}
```

## Storage Locations

| Plugin | Path |
|---|---|
| audit | `apg-audit-plugin/data/feedback-log.jsonl` |
| sales | `apg-sales-plugin/data/feedback-log.jsonl` |
| project-management | `apg-pm-plugin/data/feedback-log.jsonl` |

## Drive Sync

Feedback logs are stored locally in the plugin data directories listed above. Because the clients directory is the Google Drive for Desktop mirrored folder, files in the Drive path auto-sync to the cloud without any manual push step.
