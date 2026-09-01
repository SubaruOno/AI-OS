---
name: save-memory
description: Save current session progress to sidecar memory
menu-code: SM
---

# Save Memory

Immediately persist the current session context to memory.

## Process

1. **Read current index.md** — Load `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-process-analyst-sidecar/index.md`

2. **Update with current session:**
   - Active engagements and their current status (changes researched, gaps remaining, value calculated)
   - Client slug being worked on and what was analyzed this session
   - Research findings worth remembering across clients (tool recommendations, integration patterns)
   - Next steps to continue

3. **Write updated index.md** — Replace content with condensed, current version

4. **Checkpoint other files if needed:**
   - `patterns.md` — Add new research patterns: tool recommendations by industry, integration paths that worked, value estimation benchmarks discovered this session
   - `chronology.md` — Add session summary if research was conducted or estimates were materially updated

## Output

Confirm save with brief summary: "Memory saved. {brief-summary-of-what-was-updated}"
