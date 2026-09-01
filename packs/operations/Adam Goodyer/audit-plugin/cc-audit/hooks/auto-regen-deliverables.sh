#!/bin/bash
# Auto-regenerate existing HTML deliverables when audit data is updated.
# Only regenerates files that already exist in the client's deliverables/ folder.
# Called by the audit plugin's PostToolUse hook after an audit-data write.
#
# Resolves all generator/validator scripts relative to the plugin root (derived
# from this script's own location), so it is CWD-independent and portable.

AUDIT_FILE="$1"
if [ -z "$AUDIT_FILE" ]; then
  exit 0
fi

PLUGIN_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Extract client dir from the audit-data path.
# New structure: {client}/03-audit/data/<file>  -> client is 3 levels up
# Old structure: {client}/audit/<file>          -> client is 2 levels up
AUDIT_PARENT=$(basename "$(dirname "$AUDIT_FILE")")
if [[ "$AUDIT_PARENT" == "data" ]]; then
  CLIENT_DIR=$(dirname "$(dirname "$(dirname "$AUDIT_FILE")")")
else
  CLIENT_DIR=$(dirname "$(dirname "$AUDIT_FILE")")
fi
CLIENT_SLUG=$(basename "$CLIENT_DIR")

# Deliverables are at 03-audit/deliverables/ (fallback: deliverables/)
if [ -d "$CLIENT_DIR/03-audit/deliverables" ]; then
  DELIVERABLES_DIR="$CLIENT_DIR/03-audit/deliverables"
else
  DELIVERABLES_DIR="$CLIENT_DIR/deliverables"
fi

GENERATE_PY="$PLUGIN_ROOT/skills/5-deliverable-builder/scripts/generate.py"

if [ ! -d "$DELIVERABLES_DIR" ]; then
  exit 0  # No deliverables folder yet, nothing to regenerate
fi
if [ ! -f "$GENERATE_PY" ]; then
  echo "Warning: generate.py not found at $GENERATE_PY"
  exit 1
fi

# Pre-flight: BPMN structural check (non-blocking, prints warnings only)
LINTER_DIR="$PLUGIN_ROOT/skills/3-audit-extractor/scripts"
LINTER="$LINTER_DIR/validate_bpmn_json.py"
EXTRACTION_FILE=""
if [ -f "$CLIENT_DIR/03-audit/data/extraction.json" ]; then
  EXTRACTION_FILE="$CLIENT_DIR/03-audit/data/extraction.json"
elif [ -f "$CLIENT_DIR/audit/audit-data.json" ]; then
  EXTRACTION_FILE="$CLIENT_DIR/audit/audit-data.json"
fi
if [ -n "$EXTRACTION_FILE" ] && [ -f "$LINTER" ]; then
  LINT_OUT=$(python3 "$LINTER" --extraction-json "$EXTRACTION_FILE" --partial-ok 2>/dev/null)
  LINT_STATUS=$(echo "$LINT_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null)
  if [ "$LINT_STATUS" = "fail" ]; then
    echo "BPMN structural warnings for $CLIENT_SLUG (regen continues):"
    echo "$LINT_OUT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for f in d.get('findings',[]):
    if f['severity'] in ('high','medium'):
        print(f'  [{f[\"severity\"].upper()}] {f[\"process\"]}: {f[\"message\"]}')
" 2>/dev/null
  fi
fi

# Semantic quality check (non-blocking advisory)
SEMANTIC_VALIDATOR="$LINTER_DIR/validate_extraction_quality.py"
if [ -n "$EXTRACTION_FILE" ] && [ -f "$SEMANTIC_VALIDATOR" ]; then
  SEMANTIC_OUT=$(python3 "$SEMANTIC_VALIDATOR" --extraction-json "$EXTRACTION_FILE" --partial-ok 2>/dev/null)
  SEMANTIC_STATUS=$(echo "$SEMANTIC_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null)
  if [ "$SEMANTIC_STATUS" = "warning" ] || [ "$SEMANTIC_STATUS" = "advisory" ]; then
    echo "Semantic quality findings for $CLIENT_SLUG (regen continues):"
    echo "$SEMANTIC_OUT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for f in d.get('findings',[]):
    if f['severity'] in ('warning','advisory'):
        print(f'  [{f[\"severity\"].upper()}] {f[\"stage\"]}: {f[\"message\"][:120]}')
" 2>/dev/null
  fi
fi

REGENERATED=0
regen_if_exists() {
  local file="$1"
  local output_type="$2"
  if [ -f "$DELIVERABLES_DIR/$file" ]; then
    python3 "$GENERATE_PY" --client-slug "$CLIENT_SLUG" --output "$output_type" 2>/dev/null
    if [ $? -eq 0 ]; then
      REGENERATED=$((REGENERATED + 1))
    fi
  fi
}

# Numbered filename convention (new clients)
regen_if_exists "2-process-map.html" "process-map"
regen_if_exists "3-findings.html" "findings"
regen_if_exists "4-waste.html" "waste"
regen_if_exists "5-blueprint.html" "blueprint"
regen_if_exists "1-client-website.html" "client-website"
# Legacy filenames (existing clients — unnumbered)
if [ -f "$DELIVERABLES_DIR/process-map.html" ] || [ -d "$DELIVERABLES_DIR/processes" ]; then
  python3 "$GENERATE_PY" --client-slug "$CLIENT_SLUG" --output "process-map" 2>/dev/null \
    && REGENERATED=$((REGENERATED + 1))
fi
regen_if_exists "findings.html" "findings"
regen_if_exists "waste.html" "waste"
regen_if_exists "blueprint.html" "blueprint"
regen_if_exists "client-website.html" "client-website"

if [ $REGENERATED -gt 0 ]; then
  echo "Auto-regenerated $REGENERATED deliverable(s) for $CLIENT_SLUG"
fi
