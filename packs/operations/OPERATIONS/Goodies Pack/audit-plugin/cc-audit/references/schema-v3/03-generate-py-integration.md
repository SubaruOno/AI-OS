# 03 — generate.py Integration

> Exact code change to make `generate.py` handle v3 nested format.
> File: `apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py`
> Target: lines 237-243 (`load_audit_data` function)

## The Integration Point

`generate.py` has a single data entry point at line 237. Everything downstream (19,000+ lines of `.get()` calls on the `ssad` dict) works against a flat dict. By flattening v3 data at this single point, zero other changes are needed.

## Before (current, lines 237-243)

```python
def load_audit_data(client_slug: str) -> dict:
    path = Path(f"clients/{client_slug}/audit/audit-data.json")
    if not path.exists():
        print(f"Error: audit data not found at {path}", file=sys.stderr)
        sys.exit(2)
    with open(path) as f:
        return json.load(f)
```

## After (replacement)

```python
def load_audit_data(client_slug: str) -> dict:
    path = Path(f"clients/{client_slug}/audit/audit-data.json")
    if not path.exists():
        print(f"Error: audit data not found at {path}", file=sys.stderr)
        sys.exit(2)
    with open(path) as f:
        raw = json.load(f)
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

## Why This Works

- All 19K lines of `.get()` calls downstream access keys like `ssad.get("pain_points", [])`. After flattening, those keys exist at the top level exactly as before.
- `_schema_version`, `_section_index`, `analyst_metadata`, `architect_metadata` are root-level in v3 and are explicitly preserved.
- For v2 flat files, the function returns `raw` unchanged — backward compatible.
- Detection uses both `version.startswith("3")` and `"meta" in raw` as a belt-and-suspenders check (handles any version string inconsistencies during migration).

## How to Make This Change

1. Open `apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py`
2. Navigate to line 237 (`def load_audit_data`)
3. Replace lines 237-243 with the "After" code above
4. The function now runs to line ~250 (13 lines instead of 7)
5. No other changes needed in generate.py

## Verification

After making the change:

### Test 1: v2 file still works (run before migrating any client)
```bash
cd /path/to/APG-AI-Operating-System
python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py \
  --client-slug brightside-services --output all --no-deploy
```
Expected: All deliverables regenerate. No errors. HTML output identical to pre-change.

To compare output, generate before the change and save checksums:
```bash
# Before change:
for f in clients/brightside-services/deliverables/*.html; do md5 "$f"; done > /tmp/before.txt

# Make the change, then:
python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py \
  --client-slug brightside-services --output all --no-deploy
for f in clients/brightside-services/deliverables/*.html; do md5 "$f"; done > /tmp/after.txt

diff /tmp/before.txt /tmp/after.txt
# Expected: no diff
```

### Test 2: v3 file works (run after migrating JLR to v3)
Same command as Test 1. Expected: identical HTML output from v3 data.

### Test 3: Mixed environment (one v2, one v3 client)
```bash
# Generate for a v2 client (e.g. brightside-services) after JLR is migrated to v3
python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py \
  --client-slug brightside-services --output all --no-deploy
```
Expected: No errors. v2 path (the `return raw` branch) is taken.
