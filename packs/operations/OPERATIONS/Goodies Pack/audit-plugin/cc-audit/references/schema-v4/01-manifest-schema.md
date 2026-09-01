# 01 -- Manifest Schema

> Full specification for `audit-manifest.json`, the index file that replaces `_section_index`.
> This is the source of truth for the manifest format. Create new manifests from this template.

## Purpose

The manifest serves three roles:
1. **Version detection:** presence of `audit-manifest.json` signals v4 layout
2. **Domain index:** maps domain names to files, write owners, and timestamps
3. **Integrity:** SHA-256 checksums verify domain file consistency

## Template

```json
{
  "_schema_version": "4.0.0",
  "client_slug": "",
  "company_name": "",
  "audit_status": "in_progress",
  "updated_at": "2026-01-01T00:00:00Z",
  "domains": {
    "meta": {
      "file": "meta.json",
      "written_by": "extractor",
      "updated_at": "2026-01-01T00:00:00Z",
      "checksum": ""
    },
    "extraction": {
      "file": "extraction.json",
      "written_by": "extractor",
      "updated_at": "2026-01-01T00:00:00Z",
      "checksum": ""
    },
    "findings": {
      "file": "findings.json",
      "written_by": "extractor",
      "updated_at": "2026-01-01T00:00:00Z",
      "checksum": ""
    },
    "opportunities": {
      "file": "opportunities.json",
      "written_by": "researcher",
      "updated_at": "2026-01-01T00:00:00Z",
      "checksum": ""
    },
    "strategy": {
      "file": "strategy.json",
      "written_by": "researcher",
      "updated_at": "2026-01-01T00:00:00Z",
      "checksum": ""
    },
    "architecture": {
      "file": "architecture.json",
      "written_by": "designer",
      "updated_at": "2026-01-01T00:00:00Z",
      "checksum": ""
    },
    "reviews": {
      "file": "reviews.json",
      "written_by": "reviewer",
      "updated_at": "2026-01-01T00:00:00Z",
      "checksum": ""
    }
  }
}
```

## Field Definitions

### Root Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `_schema_version` | string | yes | Always `"4.0.0"` |
| `client_slug` | string | yes | Kebab-case client identifier, matches `clients.json` key |
| `company_name` | string | yes | Duplicated from `meta.json` for quick access without loading meta |
| `audit_status` | enum | yes | `"in_progress"` or `"process_map_complete"`. Duplicated from `meta.json` for pipeline gating without loading meta |
| `updated_at` | ISO 8601 | yes | Timestamp of the most recent domain write. Updated by `save_domain()` |
| `domains` | object | yes | Map of domain name to domain descriptor |

### Domain Descriptor Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | string | yes | Filename of the domain file (always `{domain}.json`) |
| `written_by` | enum | yes | `"extractor"`, `"researcher"`, or `"designer"` |
| `updated_at` | ISO 8601 | yes | Timestamp of the last write to this specific domain file |
| `checksum` | string | yes | SHA-256 hex digest of the domain file content. Empty string before first write |

## Update Rules

### When `save_domain(slug, domain, data)` is called:

1. Write `clients/{slug}/audit/{domain}.json` with `json.dumps(data, indent=2, ensure_ascii=False)` + trailing newline
2. Compute SHA-256 of the written bytes
3. Load `audit-manifest.json`
4. Update `domains.{domain}.checksum` with the new hash
5. Update `domains.{domain}.updated_at` with current ISO timestamp
6. Update root `updated_at` with the same timestamp
7. If domain is `meta`:
   - Copy `data["audit_status"]` into manifest root `audit_status`
   - Copy `data["company_name"]` into manifest root `company_name`
8. Write `audit-manifest.json`

### When creating a new client (v4 from scratch):

1. Create `audit-manifest.json` from the template above
2. Populate `client_slug`, `company_name` from client intake
3. Set `audit_status` to `"in_progress"`
4. Create all 6 domain files with empty structures (see domain file templates below)
5. Compute checksums for each domain file
6. Set all `updated_at` timestamps to creation time

## Domain File Templates (New Client Bootstrap)

### meta.json
```json
{
  "client_slug": "",
  "company_name": "",
  "industry_tag": "",
  "audit_start_date": "",
  "audit_status": "in_progress",
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
  "blended_rate_confidence": "LOW",
  "blended_rate_source": ""
}
```

### extraction.json
```json
{
  "processes": [],
  "decision_nodes": [],
  "tools": [],
  "staff_roster": [],
  "business_metrics": {},
  "business_stages_covered": [],
  "sessions": [],
  "extracted_materials": [],
  "client_context": {}
}
```

### findings.json
```json
{
  "pain_points": [],
  "pain_points_summary": {},
  "optimisations": [],
  "waste_items": [],
  "contradictions": [],
  "follow_up_questions": [],
  "follow_up_summary": "",
  "completeness_checklist": {},
  "change_readiness": {},
  "objections": [],
  "positive_signals": [],
  "data_gaps": []
}
```

### opportunities.json
```json
{
  "proposed_changes": [],
  "roi_items": [],
  "risk_register": []
}
```

### strategy.json
```json
{
  "strategic_approaches": {},
  "transformation_blueprint": {}
}
```

### architecture.json
```json
{
  "requirements_spec": {},
  "architecture_doc": {},
  "architecture_verification": {},
  "cowork_demos": [],
  "branding": {}
}
```

### reviews.json
```json
{
  "review_rounds": [],
  "meta_learning": {
    "patterns": [],
    "last_pattern_analysis": null
  }
}
```

## Integrity Verification

To verify manifest consistency (used by `validate_audit_data.py`):

```python
import hashlib, json
from pathlib import Path

def verify_manifest(audit_dir: Path) -> list[str]:
    manifest = json.loads((audit_dir / "audit-manifest.json").read_text())
    errors = []
    for domain, desc in manifest["domains"].items():
        domain_file = audit_dir / desc["file"]
        if not domain_file.exists():
            errors.append(f"Missing domain file: {desc['file']}")
            continue
        content = domain_file.read_bytes()
        actual_hash = hashlib.sha256(content).hexdigest()
        if desc["checksum"] and actual_hash != desc["checksum"]:
            errors.append(f"{domain}: checksum mismatch (expected {desc['checksum'][:12]}..., got {actual_hash[:12]}...)")
    return errors
```

Checksum mismatches are warnings, not hard errors. They indicate the manifest was not updated after a domain file write (e.g., crash during save). The reader should proceed with the domain file content as-is.
