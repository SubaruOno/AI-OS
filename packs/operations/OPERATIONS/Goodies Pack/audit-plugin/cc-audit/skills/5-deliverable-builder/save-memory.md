---
name: save-memory
description: Save current session progress to memory
menu-code: SM
---

# Save Memory

Immediately persist the current session context to memory.

## Process

1. **Read current index.md** — Load `${CLAUDE_PLUGIN_ROOT}/_memory/apg-generator-sidecar/index.md`

2. **Update with current session:**
   - Which client and which outputs were generated this session
   - File paths of generated deliverables
   - Any audit data gaps that caused incomplete sections

3. **Write updated index.md**

## Output

Confirm save with brief summary: "Memory saved. {brief-summary}"
