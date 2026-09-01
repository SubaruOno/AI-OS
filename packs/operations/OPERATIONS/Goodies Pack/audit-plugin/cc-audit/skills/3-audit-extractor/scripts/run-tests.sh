#!/bin/bash
# Run all tests for bmad-apg-agent-analyst scripts

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS=0
FAIL=0

echo "Running bmad-apg-agent-analyst script tests..."
echo "================================================"

run_test() {
    local name="$1"
    local file="$2"
    echo ""
    echo ">>> $name"
    if python3 "$file"; then
        PASS=$((PASS + 1))
    else
        FAIL=$((FAIL + 1))
    fi
}

run_test "validate_audit_data tests" "$SCRIPT_DIR/tests/test_validate_audit_data.py"

echo ""
echo "================================================"
echo "Results: $PASS passed, $FAIL failed"
if [ $FAIL -gt 0 ]; then
    exit 1
fi
exit 0
