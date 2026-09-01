# 07 — Migration Runbook

> Step-by-step execution guide, ordered by session.
> Update `WIKI.md` checklist after completing each step.
> Each session is designed to be independent — read WIKI.md first to pick up where the last session left off.

## Before Starting Any Session

1. Read `WIKI.md` — check the checklist to see what's done and what's next
2. Open the reference file for the current step
3. Work through the step, verify against the verification instructions
4. Update the WIKI.md checklist: change `[ ] pending` to `[x] done` or `[!] blocked: <reason>`

---

## Session 1: Build the wiki folder

**Status in WIKI.md after completion:** Step 1a done

**Steps:**
1. Create `apg-audit-plugin/references/schema-v3/` directory
2. Create all 7 files: WIKI.md, 01-07 reference files
3. Update WIKI.md step 1a to `[x] done`

**Verification:** All 7 files exist at `apg-audit-plugin/references/schema-v3/`

---

## Session 2: Build tooling

**Reference files:** `02-audit-reader.md`

**Scripts to create:**
- `apg-audit-plugin/scripts/audit_reader.py`
- `apg-audit-plugin/scripts/migrate_audit_data.py`

### audit_reader.py

Follow the spec in `02-audit-reader.md` exactly. Key requirements:
- `load_sections(path, sections)` returns flat dict
- `load_profile(path, profile_name)` returns flat dict using PROFILES dict
- `flatten(nested)` converts v3 to v2 flat
- `nest(flat)` converts v2 flat to v3 nested
- CLI: `python3 audit_reader.py <path> --profile <name>` outputs JSON to stdout
- Handles both v2 and v3 input for all functions

### migrate_audit_data.py

```python
#!/usr/bin/env python3
"""
migrate_audit_data.py — Migrate an audit-data.json file from v2 flat to v3 nested structure.

Usage:
  python3 migrate_audit_data.py --client-slug <slug> [--dry-run]

Allowed client slugs: brightside-services, riverside-dental
All other clients are NOT migrated (they stay on v2 indefinitely).

Options:
  --client-slug SLUG   Client slug to migrate (required)
  --dry-run            Show what would change without writing

Exit codes:
  0 — success
  1 — error (file not found, client not in allowed list, invalid JSON)
"""
```

The script must:
1. Enforce an allowlist: only `brightside-services` and `riverside-dental` can be migrated
2. Bail with an error message if any other slug is provided
3. Load the existing audit-data.json
4. If already v3 (starts with "3"), print "Already on v3" and exit 0
5. Call `nest(data)` from audit_reader.py
6. In `--dry-run` mode: print a summary of which keys move to which domain, do NOT write
7. In normal mode: write the v3 file to the same path (overwriting the v2 file)
8. Create a backup at `clients/{slug}/audit/audit-data-v2-backup.json` before overwriting

### Roundtrip Test (run after building both scripts)

```bash
cd /path/to/APG-AI-Operating-System

# Step 1: Save checksums of current deliverables
for f in clients/brightside-services/deliverables/*.html; do md5 "$f"; done > /tmp/pre-migration.txt
cat /tmp/pre-migration.txt

# Step 2: Run roundtrip test
python3 apg-audit-plugin/scripts/audit_reader.py \
  clients/brightside-services/audit/audit-data.json --version
# Expected: 2.0.0

# Step 3: Run dry-run migration to see what would change
python3 apg-audit-plugin/scripts/migrate_audit_data.py \
  --client-slug brightside-services --dry-run
# Expected: summary of key moves, no file written

# Step 4: Programmatic roundtrip test (from 02-audit-reader.md Test 1)
python3 -c "
import json
from pathlib import Path
import sys
sys.path.insert(0, 'apg-audit-plugin/scripts')
from audit_reader import nest, flatten

original = json.loads(Path('clients/brightside-services/audit/audit-data.json').read_text())
nested = nest(original)
roundtripped = flatten(nested)

missing = [k for k in original if k not in roundtripped and k not in ('_schema_version',)]
mismatched = [k for k in original if k in roundtripped and roundtripped[k] != original[k]]

if missing: print('MISSING KEYS:', missing)
if mismatched: print('MISMATCHED KEYS:', mismatched)
if not missing and not mismatched: print('Roundtrip test PASSED')
"
```

**Expected:** `Roundtrip test PASSED`

**Update WIKI.md:** Steps 2a, 2b, 2c

---

## Session 3: Integrate generate.py and validate_audit_data.py

**Reference files:** `03-generate-py-integration.md`, `04-validation-integration.md`

### Step 3a: Update generate.py

1. Open `apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py`
2. Navigate to line 237
3. Replace `load_audit_data` function (lines 237-243) with the "After" code from `03-generate-py-integration.md`
4. Save the file

### Step 3b: Update validate_audit_data.py

1. Open `apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py`
2. Navigate to line 24
3. Replace `load_audit_data` function (lines 24-34) with the "After" code from `04-validation-integration.md`
4. Save the file

### Step 3c: Regression test (v2 file, both scripts)

**Generate test — JLR is still v2 at this point:**
```bash
# Save current checksums
for f in clients/brightside-services/deliverables/*.html; do md5 "$f"; done > /tmp/step3-before.txt

# Run generation
python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py \
  --client-slug brightside-services --output all

# Compare checksums
for f in clients/brightside-services/deliverables/*.html; do md5 "$f"; done > /tmp/step3-after.txt
diff /tmp/step3-before.txt /tmp/step3-after.txt
```
Expected: no diff

**Validation test:**
```bash
python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py \
  --file clients/brightside-services/audit/audit-data.json
```
Expected: same exit code as before (0 or 1 depending on pre-existing issues)

**Update WIKI.md:** Steps 3a, 3b, 3c

---

## Session 4: Migrate brightside-services to v3

**Prerequisites:** Sessions 1-3 complete (check WIKI.md)

### Step 4a: Run migration

```bash
# Backup is created automatically by migrate_audit_data.py
python3 apg-audit-plugin/scripts/migrate_audit_data.py --client-slug brightside-services
```

Expected output:
- `Backup saved to clients/brightside-services/audit/audit-data-v2-backup.json`
- `Migration complete. brightside-services is now on v3.`

Verify the backup exists:
```bash
ls -la clients/brightside-services/audit/
# Should see audit-data.json and audit-data-v2-backup.json
```

Verify v3 schema:
```bash
python3 apg-audit-plugin/scripts/audit_reader.py \
  clients/brightside-services/audit/audit-data.json --version
# Expected: 3.0.0
```

### Step 4b: Verify generate.py on v3 data

```bash
# Save current checksums (from v2 deliverables)
for f in clients/brightside-services/deliverables/*.html; do md5 "$f"; done > /tmp/step4-v2-html.txt

# Regenerate from v3 data
python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py \
  --client-slug brightside-services --output all

# Compare
for f in clients/brightside-services/deliverables/*.html; do md5 "$f"; done > /tmp/step4-v3-html.txt
diff /tmp/step4-v2-html.txt /tmp/step4-v3-html.txt
```
Expected: no diff

### Step 4c: Verify validation on v3 data

```bash
python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py \
  --file clients/brightside-services/audit/audit-data.json
```
Expected: same exit code as before migration

### Step 4d: Verify selective loading

```bash
python3 apg-audit-plugin/scripts/audit_reader.py \
  clients/brightside-services/audit/audit-data.json --profile waste > /tmp/waste-profile.json

python3 -c "
import json
data = json.load(open('/tmp/waste-profile.json'))
print('Has waste_items:', 'waste_items' in data)
print('Has blended_rate:', 'blended_hourly_rate_aud' in data)
print('Has proposed_changes:', 'proposed_changes' in data)
# Expected: True, True, False
"
```

**Update WIKI.md:** Steps 4a, 4b, 4c

---

## Session 5: Migrate riverside-dental to v3

**Prerequisites:** Session 4 complete and verified

Same steps as Session 4, with `--client-slug riverside-dental`:

```bash
python3 apg-audit-plugin/scripts/migrate_audit_data.py --client-slug riverside-dental

python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py \
  --client-slug riverside-dental --output all

python3 apg-audit-plugin/skills/3-audit-extractor/scripts/validate_audit_data.py \
  --file clients/riverside-dental/audit/audit-data.json
```

**Update WIKI.md:** Steps 5a, 5b

---

## Session 6: Update agent prompts

**Reference file:** `05-agent-prompt-updates.md`

Read `05-agent-prompt-updates.md` in full before making any changes. The changes are editorial — they add selective loading instructions and correct write paths for v3 files.

Work through each capability file in order:
1. Agent 3: sync-and-update.md, audit-check.md, generate-questions.md, merge-extraction.md, process-review.md, waste-review.md, findings-review.md, ingest-materials.md, resolve-questions.md
2. Agent 4: extract-improvements.md, research-improvements.md, build-strategic-approaches.md, build-and-rate.md, verify-research.md
3. Agent 6: extract-requirements.md, build-architecture.md, verify-architecture.md, build-prototype.md, build-cowork-demo.md

For each file:
1. Open it
2. Find the audit data loading instruction (grep for "audit-data" or "Load")
3. Apply the changes described in `05-agent-prompt-updates.md`
4. Find the write-back instruction
5. Apply the v3 write path changes

**Update WIKI.md:** Steps 6a, 6b, 6c

---

## Session 7: Update schema documentation

**Steps:**
1. Copy content of `06-schema-reference.md` into `apg-audit-plugin/references/audit-data-schema.md` (replacing the existing v2 content, or adding a v3 section)
2. Update the per-agent thin pointer files at each `skills/{N}-{name}/references/audit-data-schema.md` to reference v3 domain paths
3. Run `/refresh-plugin-wiki apg-audit-plugin` to regenerate the plugin CLAUDE.md

**Update WIKI.md:** Steps 7a, 7b — mark migration COMPLETE

---

## Rollback

If anything breaks after migrating a client:

```bash
# Restore v2 file from backup
cp clients/{slug}/audit/audit-data-v2-backup.json clients/{slug}/audit/audit-data.json

# Verify
python3 apg-audit-plugin/scripts/audit_reader.py \
  clients/{slug}/audit/audit-data.json --version
# Expected: 2.0.0

# Regenerate deliverables
python3 apg-audit-plugin/skills/5-deliverable-builder/scripts/generate.py \
  --client-slug {slug} --output all
```

The backup is preserved at `clients/{slug}/audit/audit-data-v2-backup.json` indefinitely.

---

## New Client Onboarding (After Migration Complete)

New clients created after the migration is complete should start on v3 directly. When Agent 3's SU capability creates a fresh audit-data.json:

1. Copy the template from `references/schema-v3/06-schema-reference.md`
2. Populate `meta` with client details
3. Leave `extraction`, `findings`, `opportunities`, `strategy`, `architecture` as empty objects with their structure
4. Set `_schema_version` to "3.0.0"
5. Update `_section_index` after the first write (line ranges will be approximate until the file has real content)
