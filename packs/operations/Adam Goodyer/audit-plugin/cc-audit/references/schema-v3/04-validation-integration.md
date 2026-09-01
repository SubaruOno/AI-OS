# 04 — validate_audit_data.py Integration

> Exact code change to make the validation script handle v3 nested format.
> File: `apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py`
> Target: `load_audit_data()` function at line 24

## Before (current, lines 24-34)

```python
def load_audit_data(file_path: str) -> dict:
    path = Path(file_path)
    if not path.exists():
        print(json.dumps({"status": "error", "message": f"File not found: {file_path}"}))
        sys.exit(2)
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(2)
```

## After (replacement)

```python
def load_audit_data(file_path: str) -> dict:
    path = Path(file_path)
    if not path.exists():
        print(json.dumps({"status": "error", "message": f"File not found: {file_path}"}))
        sys.exit(2)
    try:
        with open(path) as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"Invalid JSON: {e}"}))
        sys.exit(2)
    # v3 detection: flatten nested domains back to flat dict before validation
    version = raw.get("_schema_version", "2.0.0")
    if version.startswith("3") or "meta" in raw:
        ssad = {}
        for domain in ("meta", "extraction", "findings", "opportunities", "strategy", "architecture"):
            ssad.update(raw.get(domain, {}))
        ssad["_schema_version"] = version
        ssad["_section_index"] = raw.get("_section_index", {})
        ssad["analyst_metadata"] = raw.get("analyst_metadata", {})
        ssad["architect_metadata"] = raw.get("architect_metadata", {})
        return ssad
    return raw
```

## Why This Is Identical to generate.py

The same flattening logic is used in both places. This is intentional: both scripts need a flat dict to operate against. The logic is simple enough that duplication is preferable to importing from a shared module (which would add a dependency on audit_reader.py being on the path).

If you want to avoid duplication, you can import flatten from audit_reader.py:
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))
from audit_reader import flatten
# Then replace the flattening block with: return flatten(raw)
```
But this creates a cross-skill dependency. The inline approach is safer.

## Verification

### Test 1: v2 file passes validation unchanged
```bash
python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py \
  --file clients/brightside-services/audit/audit-data.json --verbose
```
Expected: Same output as before the change. Exit code 0.

### Test 2: v3 file passes validation
Run after migrating JLR to v3:
```bash
python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py \
  --file clients/brightside-services/audit/audit-data.json --verbose
```
Expected: Exit code 0 (or 1 if there are pre-existing HIGH severity issues, same as before).

### Test 3: v2 client still validates
```bash
python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py \
  --file clients/brightside-services/audit/audit-data.json
```
Expected: Same exit code as before the change.
