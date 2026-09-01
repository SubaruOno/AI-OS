# Memory System — APG Process Analyst

## Location

`${CLAUDE_PLUGIN_ROOT}/_memory/bmad-apg-process-analyst-sidecar/`

## Files

| File | Purpose | Load when |
|------|---------|-----------|
| `index.md` | Active research engagements, configuration, last session | Always on activation |
| `access-boundaries.md` | Read/write/deny zones | Always on activation |
| `patterns.md` | Cross-client research patterns, tool recommendations by industry | When researching (RI) |
| `chronology.md` | Research session timeline | When saving memory (SM) |

## Discipline

- Only remember what matters for the next research session
- Condense to essence — no narrative
- Update index.md immediately after research session
- Write-through on critical events:
  - New industry pattern discovered (tool recommendation, integration path)
  - Value estimation benchmark established
  - Research strategy that produced strong results
- Prune when files exceed 100 lines
- Keep last 20 chronology entries

## What to Remember

- Which tools work well together per industry (e.g., "NDIS providers: ShiftCare + Xero + Make.com is the standard stack")
- Typical time savings by automation type (e.g., "API roster sync typically saves 4-8 hrs/wk for 30+ staff")
- Effective research queries (e.g., "searching '{tool} API documentation integration' produces better results than '{tool} automation'")
- Value estimation benchmarks (e.g., "AI call analysis typically yields 5-15% conversion improvement")
- Risks that repeat across clients (e.g., "staff resistance to new tools is the #1 implementation risk in home services")

## What NOT to Remember

- Client-specific data (that lives in the audit data)
- Specific research findings (those live on the proposed_change)
- Anything derivable from the current audit data state
