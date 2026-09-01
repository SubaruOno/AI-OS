# 02 -- audit_reader.py v4 Extensions

> Specification for new functions added to `audit_reader.py` to support v4 multi-file layout.
> Existing v2/v3 functions remain unchanged. New functions extend the module.

## Overview

`audit_reader.py` becomes the universal adapter for all audit data access. It auto-detects v2 (flat single file), v3 (nested single file), and v4 (manifest + domain files) formats. All callers get the same flat dict interface regardless of the underlying storage format.

## New Functions

### detect_version(slug_or_path)

```python
def detect_version(slug_or_path: str) -> str:
    """
    Detect the schema version for a client's audit data.

    Args:
        slug_or_path: Either a client slug (e.g., 'brightside-services') or
                      a path to audit-data.json or audit directory.

    Returns:
        '4' if audit-manifest.json exists in the audit directory
        '3' if audit-data.json exists and _schema_version starts with '3'
        '2' if audit-data.json exists with any other version
        'none' if no audit data found

    Resolution order:
        1. If slug_or_path looks like a path (contains / or .json), resolve the audit dir from it
        2. Otherwise treat as slug: audit_dir = clients/{slug}/audit/
        3. Check for audit-manifest.json (v4)
        4. Fall back to audit-data.json version check (v3/v2)
    """
```

### resolve_audit_dir(slug_or_path)

```python
def resolve_audit_dir(slug_or_path: str) -> Path:
    """
    Resolve a client slug or file path to the audit directory path.

    Args:
        slug_or_path: Client slug ('brightside-services'), path to audit-data.json,
                      or path to audit directory.

    Returns:
        Path to the audit directory (e.g., clients/brightside-services/audit/)

    The resolution uses the repo root as the base. Repo root is determined
    by walking up from __file__ until finding the 'clients' directory.
    """
```

### load_domain(slug, domain)

```python
def load_domain(slug: str, domain: str) -> dict:
    """
    Load a single domain file for a v4 client.

    Args:
        slug: Client slug
        domain: Domain name ('meta', 'extraction', 'findings',
                'opportunities', 'strategy', 'architecture')

    Returns:
        The domain dict (e.g., for 'meta': {"client_slug": "...", ...})

    Raises:
        FileNotFoundError: if domain file doesn't exist
        ValueError: if client is not on v4 (no manifest)
    """
```

### save_domain(slug, domain, data)

```python
def save_domain(slug: str, domain: str, data: dict) -> None:
    """
    Write a domain file and update the manifest.

    This is the ONLY write path for v4 audit data. Agents and scripts must
    never write domain files directly; always use this function.

    Args:
        slug: Client slug
        domain: Domain name
        data: The full domain dict to write (not a partial update;
              caller must load-merge-save)

    Steps:
        1. Write clients/{slug}/audit/{domain}.json (pretty-printed, trailing newline)
        2. Compute SHA-256 of the written bytes
        3. Load audit-manifest.json
        4. Update domains.{domain}.checksum and .updated_at
        5. Update root updated_at
        6. If domain == 'meta': copy audit_status and company_name to manifest root
        7. Write audit-manifest.json

    Raises:
        FileNotFoundError: if manifest doesn't exist (client not on v4)
    """
```

### load_all(slug)

```python
def load_all(slug: str) -> dict:
    """
    Reassemble a full flat dict from all v4 domain files.

    Loads all 6 domain files, merges them into a single dict using
    the same flatten() logic as v3, and returns the flat dict.

    Also includes root-level keys: _schema_version (set to "4.0.0"),
    analyst_metadata, architect_metadata (from manifest or defaults).

    For non-v4 clients, falls back to the existing load path:
    - v3: loads audit-data.json and flattens
    - v2: loads audit-data.json as-is

    Args:
        slug: Client slug

    Returns:
        Flat dict compatible with all existing consumers (generate.py, etc.)
    """
```

## Updated Existing Functions

### load_sections(path_or_slug, sections) -- updated signature

```python
def load_sections(path_or_slug, sections: list) -> dict:
    """
    Load specific domain groups. Updated to support v4.

    If path_or_slug is a slug and the client is on v4:
        - Loads only the requested domain files
        - Merges and flattens to a flat dict

    If path_or_slug is a file path (v2/v3):
        - Existing behavior: loads the single file and filters

    Always includes meta domain regardless of sections specified.
    """
```

### load_profile(path_or_slug, profile) -- updated signature

```python
def load_profile(path_or_slug, profile: str) -> dict:
    """
    Load a predefined read profile. Updated to support v4.

    Delegates to load_sections() internally, which now handles v4.
    """
```

## Implementation Notes

### Repo Root Resolution

All functions need to find `clients/{slug}/audit/`. The repo root is resolved from the script's own location:

```python
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # audit_reader.py -> scripts/ -> apg-audit-plugin/ -> repo root
```

This is anchored to `__file__`, not cwd, so it works regardless of where the script is invoked from.

### Manifest Load/Save Helpers

```python
def _load_manifest(slug: str) -> dict:
    """Load audit-manifest.json for a client. Raises FileNotFoundError if not v4."""
    manifest_path = _REPO_ROOT / f"clients/{slug}/audit/audit-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No v4 manifest for client '{slug}' at {manifest_path}")
    return json.loads(manifest_path.read_text())

def _save_manifest(slug: str, manifest: dict) -> None:
    """Write audit-manifest.json."""
    manifest_path = _REPO_ROOT / f"clients/{slug}/audit/audit-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
```

### Checksum Computation

```python
import hashlib

def _compute_checksum(content: bytes) -> str:
    """SHA-256 hex digest of file content."""
    return hashlib.sha256(content).hexdigest()
```

### Backward-Compatible load_all()

```python
def load_all(slug: str) -> dict:
    version = detect_version(slug)
    audit_dir = resolve_audit_dir(slug)

    if version == '4':
        merged = {}
        for domain in DOMAIN_ORDER:
            domain_path = audit_dir / f"{domain}.json"
            if domain_path.exists():
                domain_data = json.loads(domain_path.read_text())
                merged.update(domain_data)
        merged["_schema_version"] = "4.0.0"
        # Load analyst/architect metadata from manifest extras if present
        manifest = _load_manifest(slug)
        for key in ("analyst_metadata", "architect_metadata"):
            if key in manifest:
                merged[key] = manifest[key]
        return merged

    # v3 or v2: use existing path
    single_file = audit_dir / "audit-data.json"
    data = json.loads(single_file.read_text())
    if is_v3(data):
        return flatten(data)
    return data
```

## CLI Extensions

```bash
# Detect version for a client
python3 audit_reader.py --detect-version brightside-services

# Load a single domain
python3 audit_reader.py --slug brightside-services --domain meta

# Load a profile for a v4 client
python3 audit_reader.py --slug brightside-services --profile waste

# Load all (reassembled flat dict)
python3 audit_reader.py --slug brightside-services --all
```

## Test Plan

### Test 1: Version Detection
```python
# Before migration: v3 client
assert detect_version('brightside-services') == '3'

# After migration: v4 client
assert detect_version('brightside-services') == '4'

# v2 client
assert detect_version('brightside-services') == '2'
```

### Test 2: Roundtrip
```python
# Load v3, flatten, split into domain dicts, reassemble via load_all, compare
from audit_reader import flatten, load_all
import json
from pathlib import Path

v3_data = json.loads(Path('clients/brightside-services/audit/audit-data.json').read_text())
v3_flat = flatten(v3_data)

# After migration to v4:
v4_flat = load_all('brightside-services')

# Compare all keys (excluding _section_index which is v3-only)
for key in v3_flat:
    if key == '_section_index':
        continue
    assert key in v4_flat, f"Missing key: {key}"
    assert v4_flat[key] == v3_flat[key], f"Mismatch on key: {key}"
```

### Test 3: save_domain Updates Manifest
```python
meta = load_domain('brightside-services', 'meta')
meta['sessions_completed'] = 99  # test mutation
save_domain('brightside-services', 'meta', meta)

manifest = _load_manifest('brightside-services')
assert manifest['domains']['meta']['checksum'] != ''
assert manifest['domains']['meta']['updated_at'] != ''
```
