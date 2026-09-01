# 03 -- generate.py v4 Integration

> Exact replacement for the `load_audit_data()` function in generate.py.
> This is Session 3 work. Do NOT execute until audit_reader.py v4 extensions are built and tested.

## Current State (v3)

`generate.py` at line 237 has an inline v3 flattener:

```python
def load_audit_data(client_slug):
    audit_path = Path(f"clients/{client_slug}/audit/audit-data.json")
    if not audit_path.exists():
        print(f"Error: audit data not found at {audit_path}", file=sys.stderr)
        sys.exit(2)
    raw = json.loads(audit_path.read_text())
    # v3 detection: flatten nested domains into a single dict
    if raw.get("_schema_version", "").startswith("3") or "meta" in raw:
        ssad = {}
        for domain in ("meta", "extraction", "findings", "opportunities", "strategy", "architecture"):
            if domain in raw and isinstance(raw[domain], dict):
                ssad.update(raw[domain])
        ssad["_schema_version"] = raw.get("_schema_version", "3.0.0")
        return ssad
    return raw
```

## After (v4)

Replace the entire `load_audit_data` function with:

```python
def load_audit_data(client_slug):
    """Load audit data for a client. Supports v2, v3, and v4 formats."""
    import sys as _sys
    _reader_path = str(Path(__file__).resolve().parent.parent.parent.parent / "scripts")
    if _reader_path not in _sys.path:
        _sys.path.insert(0, _reader_path)
    from audit_reader import load_all
    try:
        return load_all(client_slug)
    except FileNotFoundError:
        print(f"Error: audit data not found for client '{client_slug}'", file=sys.stderr)
        sys.exit(2)
```

## Path Resolution

`generate.py` is at:
```
apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py
```

`audit_reader.py` is at:
```
apg-audit-plugin/scripts/audit_reader.py
```

The path resolution:
```
Path(__file__).resolve().parent     = .../skills/5-deliverable-builder/scripts/
                       .parent      = .../skills/5-deliverable-builder/
                       .parent      = .../skills/
                       .parent      = .../apg-audit-plugin/
                       / "scripts"  = .../apg-audit-plugin/scripts/
```

## Why This Works

`load_all(slug)` handles all three versions:
- **v4:** reads domain files, merges, returns flat dict
- **v3:** reads audit-data.json, flattens nested domains, returns flat dict
- **v2:** reads audit-data.json, returns as-is

The 19K lines of generation logic below this function receive the same flat dict they always have. Zero changes needed downstream.

## Same Pattern for extract_report_content.py

`extract_report_content.py` has a similar local load function. Apply the same replacement pattern:

```python
def load_audit_data(client_slug):
    _reader_path = str(Path(__file__).resolve().parent.parent.parent.parent / "scripts")
    if _reader_path not in sys.path:
        sys.path.insert(0, _reader_path)
    from audit_reader import load_all
    return load_all(client_slug)
```

## Verification

After updating generate.py (but before any client migration):

```bash
# Save current checksums
for f in clients/brightside-services/deliverables/*.html; do md5 "$f"; done > /tmp/pre-v4-gen.txt

# Regenerate (still v3 data, but now using audit_reader path)
python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py \
  --client-slug brightside-services --output all

# Compare
for f in clients/brightside-services/deliverables/*.html; do md5 "$f"; done > /tmp/post-v4-gen.txt
diff /tmp/pre-v4-gen.txt /tmp/post-v4-gen.txt
# Expected: no diff
```
