# Handoff

> Package the state of a long thread and provide a clean restart. Claude Code
> also exposes this as `/handoff`.

1. Run the log workflow first so the handoff starts from a clean save.
2. Write `outputs/handoffs/YYYY-MM-DD-<topic>.md` with:
   - what the work is and why it matters;
   - what is done, in progress, and not started;
   - decisions already made;
   - exact next actions in order;
   - blockers, test results, and gotchas.
3. Give the person this message in their language:

   > Open a new session, prime this workspace, read
   > `outputs/handoffs/<file>`, and continue from “what to do next.”

The new session uses the same instruction in Claude Code or Codex.
