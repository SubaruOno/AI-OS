# 02 — audit_reader.py Spec

> Full specification for `apg-audit-plugin/scripts/audit_reader.py`.
> This script is the foundation of the migration. Build it in Session 2.

## Purpose

Provides three capabilities:
1. **Selective loading** — read only the domains an agent needs from audit-data.json
2. **Predefined profiles** — named read sets mapped to deliverables/capabilities
3. **Format conversion** — flatten v3 nested structure to v2 flat dict and back

## Output Location

`apg-audit-plugin/scripts/audit_reader.py`

## Python Version

3.9+. No external dependencies beyond stdlib (`json`, `pathlib`, `sys`, `argparse`).

## Function Signatures

```python
def load_sections(path: str | Path, sections: list[str]) -> dict:
    """
    Load specific domain groups from audit-data.json.
    
    Works with both v2 (flat) and v3 (nested) files.
    Returns a flat dict matching the v2 interface so all existing .get() calls work.
    
    sections: list of domain names, any subset of:
        ['meta', 'extraction', 'findings', 'opportunities', 'strategy', 'architecture']
    
    For v2 files: returns all data regardless of sections (cannot filter flat format)
    For v3 files: loads only specified domains, flattens, and returns

    Always includes _schema_version, _section_index, analyst_metadata, architect_metadata
    regardless of sections specified.
    """


def load_profile(path: str | Path, profile: str) -> dict:
    """
    Load a predefined read profile by name.
    Calls load_sections() internally with the profile's domain list.
    Raises ValueError if profile name not recognized.
    """


def flatten(nested: dict) -> dict:
    """
    Convert v3 nested structure to v2 flat dict.
    
    Merges meta, extraction, findings, opportunities, strategy, architecture
    into a single dict. Preserves root-level keys (_schema_version, _section_index,
    analyst_metadata, architect_metadata).
    
    Safe to call on a v2 flat dict (detects by absence of domain keys, returns as-is).
    """


def nest(flat: dict) -> dict:
    """
    Convert v2 flat structure to v3 nested dict.
    
    Reads 01-domain-mapping.md logic to route each key to its domain.
    Sets _schema_version to "3.0.0".
    Updates _section_index with domain group names (line ranges added after write).
    
    Used by migrate_audit_data.py.
    """


def is_v3(data: dict) -> bool:
    """Return True if data is v3 nested format."""
    version = data.get("_schema_version", "")
    return version.startswith("3") or "meta" in data
```

## Profiles Dictionary

```python
PROFILES = {
    # Always load everything — used by GC (comprehensive report), validation, CRM sync
    "full": ["meta", "extraction", "findings", "opportunities", "strategy", "architecture"],
    
    # Process map: swim lanes, tools, waste heatmap overlay
    # GP capability, Agent 3 process review
    "process_map": ["meta", "extraction", "findings"],
    
    # Findings page: pain points, optimisations, contradictions, session grouping
    # GF capability
    "findings_page": ["meta", "findings", "extraction"],
    
    # Waste page: waste_items breakdown with hourly rate
    # GV capability
    "waste": ["meta", "findings"],
    
    # Solutions overview: proposed_changes.research, process sidebar, pain point quotes
    # GS capability
    "solutions": ["meta", "extraction", "findings", "opportunities"],
    
    # AI Blueprint: waste anchor, proposed_changes with value/cost, pain point quotes, benchmarks
    # GB capability
    "blueprint": ["meta", "findings", "opportunities", "strategy"],
    
    # Strategic approaches (legacy GA / strategic-approaches-landing)
    "strategic": ["meta", "opportunities", "strategy", "architecture"],
    
    # Comprehensive report — needs everything
    "report": ["meta", "extraction", "findings", "opportunities", "strategy", "architecture"],
    
    # Agent 3 (Extractor) — read existing data before merge, never needs analyst/architect output
    "extractor": ["meta", "extraction", "findings"],
    
    # Agent 4 EI capability — synthesise improvements from extraction evidence
    "researcher_ei": ["meta", "extraction", "findings"],
    
    # Agent 4 RI/SA/BR/VR capabilities — need opportunities too
    "researcher_analysis": ["meta", "extraction", "findings", "opportunities"],
    
    # Agent 4 VR capability — verifies everything including strategy
    "researcher_verify": ["meta", "extraction", "findings", "opportunities", "strategy"],
    
    # Agent 6 (Designer) — needs full picture for requirements + architecture
    "designer": ["meta", "extraction", "findings", "opportunities", "strategy", "architecture"],
}
```

## CLI Interface

```
python3 audit_reader.py <path_to_audit_data_json> [options]

Options:
  --profile PROFILE     Load a predefined profile (see PROFILES dict above)
  --sections SEC [SEC]  Load specific domain names (space-separated)
  --list-profiles       Print all available profile names and their domain lists
  --version             Print the schema version of the file

Output: JSON to stdout (pipe to jq or redirect to file)

Examples:
  python3 audit_reader.py clients/brightside-services/audit/audit-data.json --profile waste
  python3 audit_reader.py clients/brightside-services/audit/audit-data.json --sections meta findings
  python3 audit_reader.py clients/brightside-services/audit/audit-data.json --list-profiles
  python3 audit_reader.py clients/brightside-services/audit/audit-data.json --version
```

## Domain Key Routing (for `nest()` function)

The `nest()` function uses this routing dict. Every key not listed defaults to `meta`:

```python
DOMAIN_ROUTING = {
    # extraction domain
    "processes": "extraction",
    "decision_nodes": "extraction",
    "tools": "extraction",
    "staff_roster": "extraction",
    "business_metrics": "extraction",
    "business_metrics_list": "extraction",  # legacy, merge or discard
    "business_stages_covered": "extraction",
    "sessions": "extraction",
    "extracted_materials": "extraction",
    "client_context": "extraction",
    "constraints": "extraction",        # legacy, nested under client_context
    "strategic_notes": "extraction",    # legacy, nested under client_context

    # findings domain
    "pain_points": "findings",
    "pain_points_summary": "findings",
    "optimisations": "findings",
    "waste_items": "findings",
    "contradictions": "findings",
    "follow_up_questions": "findings",
    "follow_up_summary": "findings",
    "completeness_checklist": "findings",
    "change_readiness": "findings",
    "objections": "findings",
    "positive_signals": "findings",
    "data_gaps": "findings",
    "quick_wins": "findings",           # legacy

    # opportunities domain
    "proposed_changes": "opportunities",
    "roi_items": "opportunities",
    "risk_register": "opportunities",

    # strategy domain
    "strategic_approaches": "strategy",
    "transformation_blueprint": "strategy",

    # architecture domain
    "requirements_spec": "architecture",
    "architecture_doc": "architecture",
    "architecture_verification": "architecture",
    "cowork_demos": "architecture",
    "branding": "architecture",
}

# Root-level keys (not nested in any domain)
ROOT_KEYS = {
    "_schema_version", "_section_index",
    "analyst_metadata", "architect_metadata",
}

# Meta domain keys (everything not in the above routing and not a root key)
META_KEYS = {
    "client_slug", "company_name", "industry_tag", "audit_start_date",
    "audit_status", "sessions_completed", "google_drive_folder_url",
    "crm", "contact",
    "blended_hourly_rate_aud", "blended_rate_confidence", "blended_rate_source",
}

# Keys to drop (should not be in audit-data.json at all)
DROP_KEYS = {"ingestion_manifest"}
```

## Legacy Key Handling in `nest()`

When routing `constraints` and `strategic_notes`:
- If `client_context` already exists in flat dict, merge them into `extraction.client_context` as sub-keys
- If `business_metrics_list` exists alongside `business_metrics`, keep `business_metrics` (canonical) and discard `business_metrics_list`

## Test Cases

After writing the script, verify these three cases:

### Test 1: Roundtrip (v2 -> nest -> flatten = original)
```python
import json
from pathlib import Path
from audit_reader import nest, flatten

original = json.loads(Path("clients/brightside-services/audit/audit-data.json").read_text())
nested = nest(original)
roundtripped = flatten(nested)

# Every key in original should exist in roundtripped with the same value
for key, value in original.items():
    if key == "_schema_version":
        continue  # version changes from 2 to 3
    assert key in roundtripped, f"Missing key: {key}"
    assert roundtripped[key] == value, f"Value mismatch for {key}"

print("Roundtrip test PASSED")
```

### Test 2: Selective loading (v3)
```python
from audit_reader import load_profile

# After migrating JLR to v3:
data = load_profile("clients/brightside-services/audit/audit-data.json", "waste")

# Should have waste_items and blended_hourly_rate_aud
assert "waste_items" in data
assert "blended_hourly_rate_aud" in data

# Should NOT have proposed_changes (not in waste profile)
assert "proposed_changes" not in data

print("Selective loading test PASSED")
```

### Test 3: v2 backward compat
```python
from audit_reader import load_profile

# v2 flat file should work with any profile (returns full data)
data = load_profile("clients/brightside-services/audit/audit-data.json", "waste")
# For v2 files, load_profile returns everything (cannot filter flat format)
assert "waste_items" in data
print("v2 backward compat test PASSED")
```
