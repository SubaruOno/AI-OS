# 06 -- Hook and Shell Script Updates

> Before/after diffs for all hook configurations and shell scripts.
> This is Session 6 work. Do NOT execute until agent prompts are updated.

## Design Decision: Manifest-Only Trigger

Auto-regen fires **only** when `audit-manifest.json` is written. This gives a single clean trigger per save cycle instead of firing 3x when the Extractor writes meta + extraction + findings.

`save_domain()` always writes the manifest last, so the trigger fires after all domain files are saved.

---

## 1. .claude/settings.json

**File:** `{PROJECT_ROOT}/.claude/settings.json`

### PostToolUse Write hook

**Before:**
```json
{
  "type": "command",
  "command": "bash scripts/auto-regen-deliverables.sh \"$CLAUDE_FILE_PATH\"",
  "if": "Write(clients/*/audit/audit-data.json)",
  "async": true,
  "statusMessage": "Auto-regenerating deliverables..."
}
```

**After:**
```json
{
  "type": "command",
  "command": "bash scripts/auto-regen-deliverables.sh \"$CLAUDE_FILE_PATH\"",
  "if": "Write(clients/*/audit/audit-manifest.json)",
  "async": true,
  "statusMessage": "Auto-regenerating deliverables..."
}
```

**Why:** Regen fires once when the manifest is updated (commit point), not on every domain file write. The manifest is always the last file written by `save_domain()`.

---

## 2. apg-audit-plugin/hooks/hooks.json

**File:** `apg-audit-plugin/hooks/hooks.json`

### PostToolUse Write|Edit advisory hook

The plugin hook prints a reminder when audit data is modified. Update the detection pattern to match v4 domain files.

**Before (grep pattern in the hook script):**
```
audit-data.json
```

**After:**
```
audit/(audit-manifest|meta|extraction|findings|opportunities|strategy|architecture|audit-data)\.json
```

This matches any audit file write, printing the advisory reminder for all of them.

---

## 3. scripts/auto-regen-deliverables.sh

**File:** `scripts/auto-regen-deliverables.sh`

### Path derivation update

The hook fires with `$CLAUDE_FILE_PATH` set to the manifest path (e.g., `clients/brightside-services/audit/audit-manifest.json`). The existing slug derivation still works because the directory structure is the same:

```
dirname dirname "clients/brightside-services/audit/audit-manifest.json"
= dirname "clients/brightside-services/audit"
= "clients/brightside-services"
```

No change needed to the `CLIENT_DIR` / `CLIENT_SLUG` derivation.

### Script path resolution

The script calls `generate.py`, which now uses `audit_reader.load_all()` internally. No change needed to the generate.py invocation.

### Full updated script (minimal changes):

**Before (line 8-9):**
```bash
# Extract client slug from path: clients/{slug}/audit/audit-data.json
CLIENT_DIR=$(dirname "$(dirname "$AUDIT_FILE")")
```

**After:**
```bash
# Extract client slug from path: clients/{slug}/audit/audit-manifest.json (or audit-data.json for v2/v3)
CLIENT_DIR=$(dirname "$(dirname "$AUDIT_FILE")")
```

Comment-only change. The dirname logic works for both `audit-data.json` and `audit-manifest.json` paths.

---

## 4. scripts/auto-regen-after-python.sh

**File:** `scripts/auto-regen-after-python.sh`

This script parses Python commands for audit-data.json write patterns. Update the grep pattern.

**Before:**
```bash
grep -q "audit-data.json"
```

**After:**
```bash
grep -qE "clients/[^/]+/audit/(meta|extraction|findings|opportunities|strategy|architecture|audit-manifest|audit-data)\.json"
```

**Client slug extraction (if needed):**

**Before:**
```bash
# Extract slug from: clients/{slug}/audit/audit-data.json
```

**After:**
```bash
# Extract slug from: clients/{slug}/audit/{any-audit-file}.json
SLUG=$(echo "$CMD" | grep -oE 'clients/[^/]+/audit/' | head -1 | cut -d'/' -f2)
```

---

## 5. scripts/protect-client-data.sh

**File:** `scripts/protect-client-data.sh`

This script blocks shell redirects (`>`) targeting client audit data.

**Before:**
```bash
# Pattern matching audit-data.json
>\s*clients/.*/audit/audit-data\.json
```

**After:**
```bash
# Pattern matching any audit file
>\s*clients/.*/audit/[^/]*\.json
```

This blocks redirects to any JSON file in the audit directory: domain files, manifest, and the legacy single file.

---

## Verification Checklist

After updating all 5 files:

1. **Manifest write triggers regen:**
   - Write to `clients/brightside-services/audit/audit-manifest.json` using the Write tool
   - Confirm auto-regen fires (check for "Auto-regenerating deliverables..." status message)

2. **Domain file write does NOT trigger regen directly:**
   - Write to `clients/brightside-services/audit/meta.json` using the Write tool
   - Confirm no auto-regen fires (no status message)
   - Note: in practice, `save_domain()` writes both the domain file and the manifest, so regen always fires at the right time

3. **Advisory hook fires on domain writes:**
   - Write to `clients/brightside-services/audit/extraction.json` using the Write tool
   - Confirm the plugin hook prints its advisory reminder

4. **Protect script blocks redirects:**
   - Attempt: `echo '{}' > clients/brightside-services/audit/meta.json` via Bash tool
   - Confirm protect-client-data.sh blocks the redirect

5. **Python script detection:**
   - Run a Python script that touches a domain file path
   - Confirm auto-regen-after-python.sh detects the audit file reference
