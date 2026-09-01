---
description: Run completeness and contradiction check on a client's audit data
---

Run the process mapper's audit-check on the specified client:

1. Read `clients/{client}/03-audit/data/audit-data.json`
2. Check completeness per stage against the checklist
3. Surface any contradictions between sessions
4. Report gaps, low-confidence items, and recommended follow-up questions

Client: $ARGUMENTS
