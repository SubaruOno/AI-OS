# Log

> End-of-work workflow. Complete the record, keep context honest, and save or
> back up the workspace. Claude Code also exposes this as `/log`.

## 1. Ledger completeness

Rows should already have been written as work happened. Check the current
session's completed files, decisions, builds, research, and shipments against
`ledger/<seat>.md`. Append only what is missing:

`- YYYY-MM-DD HH:MM · <seat> · <area>/<type> · <one-line summary>`

Types: `build`, `decision`, `ship`, `research`, `note`. A conversation that
produced no decision or artifact needs no row.

## 2. Context and constitution drift

If work changed strategy, an offer, a team, a tool, or another durable fact,
identify the exact stale statement and ask before updating it. Move private
material out of shared context when approved.

If the workspace gained a capability, folder, or standing rule, update
`CLAUDE.md`, copy the identical content to `AGENTS.md`, and verify the files are
byte-for-byte equal. If a skill changed, run:

```text
python scripts/sync_harness_skills.py
python scripts/sync_harness_skills.py --check
```

Use `python3` on macOS if needed.

## 3. Save and back up

First confirm that the current folder is the intended workspace repository.
Never stage or commit a parent, neighboring, or unrelated repository. Then run:

```text
git add -A
git commit -m "<type>: <plain one-line summary>"
git pull --rebase --autostash
git push
```

- If another seat pushed first, pull and retry up to three times.
- If a real conflict appears, explain both versions and wait for approval of a
  merged result.
- Without a remote, commit locally and explain that the work is saved on this
  computer but not backed up off the machine.
- If offline, commit locally and leave the push for the next log.

## Report

In the person's language, report the rows added, context updates, and save or
backup status in one short block.
