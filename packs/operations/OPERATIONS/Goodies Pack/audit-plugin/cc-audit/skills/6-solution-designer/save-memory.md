---
name: save-memory
description: Save current session progress to sidecar memory
menu-code: SM
---

# Save Memory

Immediately persist the current session context to memory.

## Process

1. **Read current index.md** — Load `${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-solution-architect-sidecar/index.md`

2. **Update with current session:**
   - Active engagements and their current status (packages built, requirements extracted)
   - Client slug being worked on and what was packaged this session
   - Pricing patterns worth remembering across clients (tier mapping decisions, margin adjustments)
   - Next steps to continue

3. **Write updated index.md** — Replace content with condensed, current version

4. **Checkpoint other files if needed:**
   - `patterns.md` — Add new packaging patterns: platform clustering strategies, tier mapping decisions, common package structures by industry
   - `chronology.md` — Add session summary if requirements were extracted or architecture built

## Output

Confirm save with brief summary: "Memory saved. {brief-summary-of-what-was-updated}"
