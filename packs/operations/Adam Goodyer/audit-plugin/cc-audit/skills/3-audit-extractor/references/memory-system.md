# Memory System for APG Analyst ⚡

**Memory location:** `${CLAUDE_PLUGIN_ROOT}/_memory/{skillName}-sidecar/`

## Core Principle

Tokens are expensive. Only remember what matters. Condense everything to its essence.

## File Structure

### `index.md` — Primary Source

**Load on activation.** Contains:
- Active audit engagements and their status (sessions completed / audit data state / outstanding follow-up questions / next session date)
- Configuration (completeness checklist variant)
- Last session summary

**Update:** Immediately when a session is analyzed or audit data is materially updated.

### `access-boundaries.md` — Access Control (Required)

**Load on activation before any file operations.** Contains read/write/deny zones.

**Critical:** Before any file operation, verify the path is within allowed boundaries. If uncertain, ask.

### `patterns.md` — Learned Patterns

**Load when needed.** Contains:
- Industry-specific pain point patterns (NDIS, home services, construction)
- Common tool stacks and integration gaps per industry
- Follow-up questions that reliably surface deep waste data
- Contradiction patterns and how they were resolved

**Format:** Append-only. Prune outdated entries when file grows large.

### `chronology.md` — Timeline

**Load when needed.** Contains:
- Session summaries (date, client, session number, what was extracted, gaps remaining)
- Audit completion events

**Format:** Append-only. Keep last 20 sessions; archive older ones.

## Memory Persistence Strategy

### Write-Through (Immediate)

Persist immediately when:
1. A session transcript is fully analyzed and audit data updated
2. Contradictions detected and logged
3. Completeness checklist updated with new gaps/coverage
4. User explicitly saves (`[SM]`)

### Checkpoint (Periodic)

Update `patterns.md` after:
- A new industry pattern is recognized
- A contradiction reveals a new class of operational gap
- A follow-up question produces unusually rich data

### Save Triggers

**After these events, always update memory:**
- Session analysis complete and audit data saved
- audit data reviewed and confirmed by consultant
- Audit completed (all sessions done, audit data finalized)

## Write Discipline

Before writing to memory, ask:

1. **Is this worth remembering?** — Will it improve the next audit session or the next client? If no, skip.
2. **Minimum tokens?** — Condense to the essential fact. No narrative, no fluff.
3. **Which file?**
   - `index.md` → active engagements, session counts, open follow-up questions, current audit data status
   - `patterns.md` → industry patterns, tool stacks, effective follow-up questions
   - `chronology.md` → session summaries, audit completion events

## Memory Maintenance

Every 10 sessions or when files exceed ~100 lines:
1. **Condense index.md** — Archive completed engagements to chronology
2. **Prune patterns.md** — Remove patterns superseded by better ones
3. **Archive chronology.md** — Keep only last 20 sessions in active file
