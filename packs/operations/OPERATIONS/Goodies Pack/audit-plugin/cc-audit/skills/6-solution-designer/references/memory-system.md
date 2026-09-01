# Memory System — APG Solution Architect

## Location

`${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-solution-architect-sidecar/`

## Files

| File | Purpose | Load when |
|------|---------|-----------|
| `index.md` | Active engagements, configuration, last session | Always on activation |
| `access-boundaries.md` | Read/write/deny zones | Always on activation |
| `patterns.md` | Cross-client packaging patterns, tier mapping decisions | When building plans (CP) |
| `chronology.md` | Session timeline | When saving memory (SM) |

## Discipline

- Only remember what matters for the next packaging session
- Condense to essence — no narrative
- Update index.md immediately after packaging session
- Write-through on critical events:
  - New packaging pattern discovered (platform cluster strategy, tier decision)
  - Margin adjustment decision made (why and outcome)
  - Value narrative that resonated with a client
- Prune when files exceed 100 lines
- Keep last 20 chronology entries

## What to Remember

- Which platforms cluster well together per industry (e.g., "NDIS providers: ShiftCare + Xero always form a package")
- Typical package sizes and tier mappings by industry (e.g., "Home services CRM overhaul is always Complex tier")
- Margin patterns (e.g., "Micro tier margin is usually 50%+, Sprint tier margin is tighter at 35-40%")
- Effective value narratives (e.g., "Waste budget framing resonates most when payback is under 3 months")
- Common package structures that recur across clients (e.g., "Sales automation + lead nurturing is a natural Standard-tier package")
- Requirements decomposition shortcuts (e.g., "API integrations via Make.com always need 3 screens: connection, mapping, monitoring")

## What NOT to Remember

- Client-specific data (that lives in the audit data)
- Specific change details (those live on proposed_changes)
- Specific requirements (those live on requirements_spec)
- Anything derivable from the current audit data state
