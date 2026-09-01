---
name: save-memory
description: Save current session progress to sidecar memory
menu-code: SM
---

# Save Memory

Immediately persist the current session context to memory.

## Process

1. **Read current index.md** — Load `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-feedback-reviewer-sidecar/index.md`

2. **Update with current session:**
   - Active client and which round was just ingested or applied
   - Items pending approval or application for each client
   - Any unresolved items that need follow-up
   - Next steps to continue

3. **Write updated index.md** — Replace content with condensed, current version

4. **Checkpoint other files if needed:**
   - `patterns.md` — Add any new cross-client patterns observed this session
   - `chronology.md` — Add session summary if a round was ingested or applied

## Output

Confirm save with brief summary: "Memory saved. {brief-summary-of-what-was-updated}"
