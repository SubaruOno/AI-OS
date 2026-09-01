# Prime

> Start-of-session workflow. Catch up safely, load the right context, and report
> where things stand. Claude Code also exposes this as `/prime`.

## Phase 1: Catch up

1. Read `.seat` if it exists (`person: <name>`). Without it, use the owner named
   in the active constitution (`CLAUDE.md` in Claude Code, `AGENTS.md` in Codex).

2. If Git and a remote are configured, run:

   ```text
   git pull --rebase --autostash
   ```

   If a conflict appears, read both versions, explain the difference in the
   person's language, propose a merged version, and wait for approval. Do not
   show raw conflict markers.

3. Classify uncommitted paths with the cross-platform helper:

   ```text
   python scripts/workspace_status.py --json
   ```

   Use `python3` if that is the available command on macOS.

   - `stale` means untouched for more than one hour. It may belong to a closed
     session. Read the changes, add missing rows to the current seat's ledger,
     save them, and mention the recovery in one line.
   - `recent` may belong to another open session. Leave it completely alone and
     report only the count.
   - `unknown` includes deletions or paths without a usable timestamp. Treat it
     as recent and leave it alone unless the person confirms it is abandoned.

   If Git is not configured, skip this phase quietly.

## Phase 2: Load the workspace

Read, in order:

1. The active constitution. Confirm `CLAUDE.md` and `AGENTS.md` still match.
2. `reference/writing-style.md`.
3. Every Markdown file directly in `context/`, plus files under
   `context/businesses/` and `context/roles/` when present. Never bulk-read
   `context/import/`.
4. `docs/_index.md`. Use it as a routing table and open an individual document
   only when the current task matches its condition.
5. For a teammate seat, use `context/shared-manifest.md` plus
   `team/<seat>.md` instead of loading owner-only context.
6. The last 14 days of rows across all files in `ledger/`, interleaved by date.

If source material in `context/import/` appears too private for a shared folder,
say so in one line and offer to move it.

## Phase 3: Report

Use the person's language. Keep the report short:

1. the person or business in one line;
2. the two or three most recent work threads;
3. unfinished work, stale context, or backup issues needing attention;
4. “Ready.” or 「準備できました。」

Then begin the requested work.
