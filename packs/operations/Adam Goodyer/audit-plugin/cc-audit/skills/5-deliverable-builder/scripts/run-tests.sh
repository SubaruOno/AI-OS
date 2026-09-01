#!/bin/bash
# Run all tests for bmad-apg-agent-generator scripts

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PASS=0
FAIL=0

echo "Running bmad-apg-agent-generator script tests..."
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

run_test "generate tests" "$SCRIPT_DIR/tests/test_generate.py"
run_test "handoff layout tests" "$SCRIPT_DIR/tests/test_handoff_layout.py"

echo ""
echo "================================================"
echo "Results: $PASS passed, $FAIL failed"
if [ $FAIL -gt 0 ]; then
    exit 1
fi
exit 0
