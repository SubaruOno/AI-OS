# Document

> Write or update documentation for something built in this workspace and file it so future sessions can find it. Usually runs after implement.

## Variables

target: $ARGUMENTS (a name like "booking-system" or "stripe", a doc path like `docs/system-booking.md`, or `archive <name>` to retire one)

---

## Instructions

### Step 1: Work out the mode

1. Starts with `archive ` or `retire ` → **archive mode**. Find the doc's row in `docs/_index.md`, take the path from it, and target that file.
2. A file path that exists in `docs/` → **update mode**.
3. A name → search `docs/_index.md` for a matching row. Found means **update mode** on that file, not found means **create mode**.

Say which mode you're in and which file you're targeting before doing anything.

### Step 2: Research it properly

Don't write from memory.

1. **Read the actual thing.** For something built here, that's the files under `apps/` or `scripts/` that make it work. For a connected tool, that's how it's wired: which skill or capability calls it, what's in `.env`, and what it touches.
2. **Check what's changed:** `git log --oneline --since="30 days ago" -- <paths>`.
3. **Update mode:** read the existing doc first and work out what's stale, what's missing, what's new.

Verify every file path, command and setting against what's actually there. A doc that lies is worse than no doc.

### Step 3: Write it

Skip this in archive mode.

Target **60 to 120 lines**. Long enough to be useful, short enough that someone reads it.

**Update mode:** keep the existing structure, change only what actually changed, and leave the rest alone. Dates and history come from `git log`, never a hand-maintained table inside the doc.

**Create mode:** use the template below.

```markdown
# <Name>

> One sentence on what this is and who it's for.

## What it does
Two or three sentences in plain English. What problem it solves and for whom.

## How it works
The shape of it. What calls what, what it reads, what it writes.
Name real files and real paths.

## Setup
What has to exist for it to run: keys, accounts, anything installed.
Where each of those lives.

## Using it
The normal path, and the two or three things people actually ask for.

## When it breaks
The failure modes you've actually hit, and what fixed each one.
Add to this every time something goes wrong. It's the most valuable
section in the file and the one people skip.
```

### Step 4: File it

- **Create mode:** add a row to the right section of `docs/_index.md` (Systems / Integrations / Apps / Reference). Three columns: **when you'd want this doc**, the backticked path, and a dense one-line summary. Write the condition as the situation someone would be in, not as a topic, because that's what makes routing work.
- **Update mode:** leave the row alone unless the doc's scope genuinely moved. Then refresh its summary.
- **Archive mode:** delete its row from `_index.md` (the index lists live things only), then `git mv` the doc into `docs/archive/`. Never delete it outright.

### Step 5: Say what you did

One short block: mode, file, and whether the index changed. Then stop.

---

## Why this exists

As the workspace grows, so does the documentation. The index lets prime load a routing table instead of every document.

The other half is that it stays true. Docs get updated by the same command that builds things, so they don't drift into a pile nobody trusts.

---

## Finish with log (automatic)

Run the log workflow as the final step.
