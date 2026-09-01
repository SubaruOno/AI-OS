# 04 -- Migration Runbook

> Step-by-step execution guide, ordered by session.
> Update `WIKI.md` checklist after completing each step.
> Each session is designed to be independent: read WIKI.md first to pick up where the last session left off.

## Before Starting Any Session

1. Read `WIKI.md` in this folder: check the checklist to see what's done and what's next
2. Open the reference file for the current step
3. Work through the step, verify against the verification instructions
4. Update the WIKI.md checklist: change `[ ] pending` to `[x] done` or `[!] blocked: <reason>`

---

## Session 1: Build the wiki folder

**Status in WIKI.md after completion:** Step 1a done

**Steps:**
1. Create `apg-audit-plugin/references/schema-v4/` directory
2. Create all 7 files: WIKI.md, 01-06 reference files
3. Update WIKI.md step 1a to `[x] done`

**Verification:** All 7 files exist at `apg-audit-plugin/references/schema-v4/`

---

## Session 2: Extend audit_reader.py and write migration script

**Reference file:** `02-audit-reader-v4.md`

### Step 2a: Extend audit_reader.py

Add the following functions to the existing `audit_reader.py`:
- `_REPO_ROOT` constant (anchored to `__file__`)
- `resolve_audit_dir(slug_or_path)`
- `detect_version(slug_or_path)`
- `_load_manifest(slug)` / `_save_manifest(slug, manifest)`
- `_compute_checksum(content)`
- `load_domain(slug, domain)`
- `save_domain(slug, domain, data)`
- `load_all(slug)`

Update existing functions:
- `load_sections()`: detect v4, delegate to domain file reads
- `load_profile()`: delegate to updated `load_sections()`

Add CLI extensions:
- `--detect-version <slug>`
- `--slug <slug> --domain <domain>`
- `--slug <slug> --all`

### Step 2b: Write migrate_v3_to_v4.py

```bash
# Location
apg-audit-plugin/scripts/migrate_v3_to_v4.py
```

The script must:
1. Enforce allowlist: only `brightside-services` and `riverside-dental`
2. Load the v3 `audit-data.json`
3. If already v4 (manifest exists), print "Already on v4" and exit 0
4. Create backup at `audit-data-v3-backup.json`
5. Split the nested structure into 6 domain files
6. Create `audit-manifest.json` with checksums
7. If `--keep-v3-file` is passed, keep `audit-data.json` (default: keep)
8. `--dry-run`: print summary of domain sizes without writing

CLI:
```
python3 migrate_v3_to_v4.py --client-slug <slug> [--dry-run] [--keep-v3-file]
```

### Step 2c: Roundtrip test

```bash
# Test version detection (should return '3' since no migration yet)
python3 apg-audit-plugin/scripts/audit_reader.py --detect-version brightside-services
# Expected: 3

# Programmatic roundtrip: flatten v3 -> split to domain dicts -> merge back -> compare
python3 -c "
import json, sys
from pathlib import Path
sys.path.insert(0, 'apg-audit-plugin/scripts')
from audit_reader import flatten, is_v3, DOMAIN_ORDER, DOMAIN_ROUTING, META_KEYS, ROOT_KEYS

# Load and flatten v3
v3_data = json.loads(Path('clients/brightside-services/audit/audit-data.json').read_text())
v3_flat = flatten(v3_data)

# Simulate v4 split: extract each domain from the nested structure
domains = {}
for domain in DOMAIN_ORDER:
    if domain in v3_data and isinstance(v3_data[domain], dict):
        domains[domain] = v3_data[domain]

# Reassemble by merging all domains (simulating load_all)
reassembled = {}
for domain in DOMAIN_ORDER:
    if domain in domains:
        reassembled.update(domains[domain])
reassembled['_schema_version'] = '4.0.0'

# Compare
missing = [k for k in v3_flat if k not in reassembled and k not in ('_schema_version', '_section_index', 'analyst_metadata', 'architect_metadata')]
mismatched = [k for k in v3_flat if k in reassembled and reassembled[k] != v3_flat[k] and k != '_schema_version']

if missing: print('MISSING KEYS:', missing)
if mismatched: print('MISMATCHED KEYS:', mismatched)
if not missing and not mismatched: print('Roundtrip test PASSED')
"
```

**Expected:** `Roundtrip test PASSED`

**Update WIKI.md:** Steps 2a, 2b, 2c

---

## Session 3: Update all Python consumers

**Reference file:** `03-generate-py-v4.md`

### Step 3a: Update generate.py

Replace `load_audit_data()` at line 237 with the audit_reader-based version from `03-generate-py-v4.md`.

### Step 3b: Update validate_audit_data.py

Replace the inline v3 flattener with:
```python
import sys as _sys
_reader_path = str(Path(__file__).resolve().parent.parent.parent.parent / "scripts")
if _reader_path not in _sys.path:
    _sys.path.insert(0, _reader_path)
from audit_reader import load_all, detect_version
```

### Step 3c: Update extract_report_content.py

Same pattern as generate.py. See `03-generate-py-v4.md`.

### Step 3d: Update root scripts

For scripts that only need `meta` domain (contact, emails, drive URL):

**fetch-transcripts.py, fetch-emails.py, fetch-drive-folder.py:**
```python
_reader_path = str(Path(__file__).resolve().parent / "apg-audit-plugin" / "scripts")
if _reader_path not in sys.path:
    sys.path.insert(0, _reader_path)
from audit_reader import load_domain, detect_version, resolve_audit_dir
```

Then replace their local `json.loads(Path(...).read_text())` calls with:
```python
version = detect_version(slug)
if version == '4':
    meta = load_domain(slug, 'meta')
else:
    # existing single-file load
    ...
```

**generate-team-portfolio.py:** Needs meta + extraction. Use `load_all(slug)` or `load_sections(slug, ['meta', 'extraction'])`.

### Step 3e: Update PM plugin scripts

**generate_developer_portal.py, generate_handoff.py, generate_dev_brief.py:**

```python
_reader_path = str(Path(__file__).resolve().parent.parent.parent / "apg-audit-plugin" / "scripts")
if _reader_path not in sys.path:
    sys.path.insert(0, _reader_path)
from audit_reader import load_all
```

Path resolution for PM scripts:
```
Path(__file__).resolve().parent     = .../apg-pm-plugin/scripts/
                       .parent      = .../apg-pm-plugin/
                       .parent      = .../APG-AI-Operating-System/
                       / "apg-audit-plugin" / "scripts" = correct path
```

### Step 3f: Regression test

```bash
# Save current checksums for both v3 clients
for f in clients/brightside-services/deliverables/*.html; do md5 "$f"; done > /tmp/s3-jlr-before.txt
for f in clients/riverside-dental/deliverables/*.html; do md5 "$f"; done > /tmp/s3-omni-before.txt

# Regenerate (still v3 data, now using audit_reader)
python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py --client-slug brightside-services --output all
python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py --client-slug riverside-dental --output all

# Compare
for f in clients/brightside-services/deliverables/*.html; do md5 "$f"; done > /tmp/s3-jlr-after.txt
for f in clients/riverside-dental/deliverables/*.html; do md5 "$f"; done > /tmp/s3-omni-after.txt
diff /tmp/s3-jlr-before.txt /tmp/s3-jlr-after.txt
diff /tmp/s3-omni-before.txt /tmp/s3-omni-after.txt
# Expected: no diff for both

# Validate
python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py --file clients/brightside-services/audit/audit-data.json
python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py --file clients/riverside-dental/audit/audit-data.json
# Expected: same exit codes as before session
```

**Update WIKI.md:** Steps 3a-3f

---

## Session 4: Migrate clients to v4

**Prerequisites:** Sessions 1-3 complete (check WIKI.md)

### Step 4a: Migrate brightside-services

```bash
# Dry run first
python3 apg-audit-plugin/scripts/migrate_v3_to_v4.py --client-slug brightside-services --dry-run

# Migrate (keeps v3 file as backup)
python3 apg-audit-plugin/scripts/migrate_v3_to_v4.py --client-slug brightside-services --keep-v3-file
```

### Step 4b: Verify JLR generate.py

```bash
for f in clients/brightside-services/deliverables/*.html; do md5 "$f"; done > /tmp/s4-jlr-before.txt
python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py --client-slug brightside-services --output all
for f in clients/brightside-services/deliverables/*.html; do md5 "$f"; done > /tmp/s4-jlr-after.txt
diff /tmp/s4-jlr-before.txt /tmp/s4-jlr-after.txt
# Expected: no diff
```

### Step 4c: Verify JLR validation

```bash
python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py --file clients/brightside-services/audit/audit-manifest.json
# Expected: pass (validator updated to accept manifest path)
```

### Step 4d: Verify v4 directory structure

```bash
ls -la clients/brightside-services/audit/
# Expected: audit-manifest.json, meta.json, extraction.json, findings.json,
#           opportunities.json, strategy.json, architecture.json,
#           audit-data.json (backup), audit-data-v3-backup.json, ingestion-manifest.json

python3 apg-audit-plugin/scripts/audit_reader.py --detect-version brightside-services
# Expected: 4
```

### Step 5a-5b: Migrate riverside-dental

Same steps as 4a-4d with `--client-slug riverside-dental`.

**Update WIKI.md:** Steps 4a-4c, 5a-5b

---

## Session 5: Update agent capability prompts

**Reference file:** `05-agent-prompt-updates.md`

Work through each capability file in order. For each file:
1. Find the audit data loading instruction
2. Replace `_section_index` + `Read(path, offset, limit)` with `Read(clients/{slug}/audit/{domain}.json)`
3. Replace write instructions to target individual domain files
4. Remove any references to `_section_index`

Order:
1. Agent 3: sync-and-update.md, generate-questions.md, audit-check.md, merge-extraction.md, process-review.md, waste-review.md, findings-review.md, ingest-materials.md, resolve-questions.md
2. Agent 4: extract-improvements.md, research-improvements.md, build-strategic-approaches.md, build-and-rate.md, verify-research.md
3. Agent 6: extract-requirements.md, build-architecture.md, verify-architecture.md, build-prototype.md, build-cowork-demo.md

**Update WIKI.md:** Steps 6a, 6b, 6c

---

## Session 6: Update hooks, scripts, and documentation

**Reference file:** `06-hook-updates.md`

### Step 7a: Update hooks

Update `.claude/settings.json` and `apg-audit-plugin/hooks/hooks.json` per `06-hook-updates.md`.

### Step 7b: Update shell scripts

Update `auto-regen-deliverables.sh`, `auto-regen-after-python.sh`, `protect-client-data.sh` per `06-hook-updates.md`.

### Step 7c: Update documentation

1. Update `apg-audit-plugin/references/audit-data-schema.md` with v4 section
2. Update `apg-audit-plugin/CLAUDE.md` source of truth and where-to-look table
3. Update root `CLAUDE.md` Client Data Model section

### Step 7d: Refresh plugin wiki

Run `/refresh-plugin-wiki apg-audit-plugin`.

**Update WIKI.md:** Steps 7a-7d. Mark migration COMPLETE.

---

## Rollback

If anything breaks after migrating a client:

```bash
# Remove v4 files
rm clients/{slug}/audit/audit-manifest.json
rm clients/{slug}/audit/meta.json clients/{slug}/audit/extraction.json
rm clients/{slug}/audit/findings.json clients/{slug}/audit/opportunities.json
rm clients/{slug}/audit/strategy.json clients/{slug}/audit/architecture.json

# audit-data.json was kept (--keep-v3-file), so it becomes active again
python3 apg-audit-plugin/scripts/audit_reader.py --detect-version {slug}
# Expected: 3

# Regenerate deliverables
python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py \
  --client-slug {slug} --output all
```

---

## New Client Onboarding (After Migration Complete)

New clients created after the migration should start on v4 directly. When Agent 3 SU creates a fresh audit:

1. Create `clients/{slug}/audit/` directory
2. Create `audit-manifest.json` from template in `01-manifest-schema.md`
3. Create all 6 domain files from templates in `01-manifest-schema.md`
4. Populate `meta.json` with client details
5. Compute checksums for each domain file and update manifest
6. All domain files start with empty structures, populated progressively by agents
