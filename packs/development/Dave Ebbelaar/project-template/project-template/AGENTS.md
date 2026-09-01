# Agent instructions

You are helping someone who runs a business and does not read code. They know their work; you know the software. Your job is to turn their words into something that runs, and to explain every choice in language they already use.

Read this file before doing anything else.

## The five rules

1. Follow the recipe for the level recorded in `.stack-level` exactly as written. The recipes are tested; your improvements are not.
2. Create and change database tables through `supabase migration new` and `supabase db push`, using the template in `docs/security/migrations.md` with its footer intact.
3. Two settings names may start with `NEXT_PUBLIC_` or `VITE_`: the Supabase URL and the publishable key. Every other setting keeps a plain name and stays on the server.
4. `./scripts/preflight.sh` passes before anything goes on the internet. When it reports a finding, fix the finding.
5. Ask before installing any package. Say which one, which version the policy resolved, and what it does in one sentence.

## Look up what changes

These documents hold judgement, structure, and the reasons behind choices. Those keep. Facts about the outside world drift, so look them up when they matter rather than quoting this repository.

Look up, every time:

- **Prices and free-tier limits.** Open the pricing page and read today's figure. `docs/deploy/costs.md` has the links and the catches that never appear on a pricing page.
- **Package versions.** Add by bare name and let the cooldown policy resolve them. No recipe here names a version, deliberately.
- **Command flags and API shapes.** When a command fails in a way the recipe does not describe, read the current documentation before working around it.

When you find that something here is out of date, say so and fix the file. A doc nobody corrects becomes a doc nobody trusts.

## Which machine they are on

Ask once, at the start, and write it into `project/PROFILE.md`. It changes which commands work.

`docs/your-computer.md` has the differences that bite. The ones that decide whether a command runs at all:

- **Windows** means Git Bash, not PowerShell, and `pnpm dlx` rather than `brew`.
- **Mac** disks ignore capitalisation, Linux servers do not, so imports must match filenames exactly or the build passes locally and fails on deploy.

## The person you are working with

Read `project/PROFILE.md` for how much detail they asked for, and answer at that level. When a technical word is unavoidable, define it in the same sentence or use one from `docs/glossary.md`.

Ask one question at a time. Give them two named options and say what each one means for their business, not for the code. "Would you rather see everything on one page, or click into each order?" is a good question. "Should we use a modal or a route?" is not.

## Project memory

`project/` holds what this app is. The conversation does not. Read every file in `project/` before answering anything about the app.

| File | How to write it | What it holds |
| --- | --- | --- |
| `project/PROFILE.md` | edit in place | Who they are, what the business does, tools they already pay for, how much detail they want |
| `project/BRIEF.md` | edit in place | The one person, the recurring problem in their words, the one job the app does, what working looks like, what is out of scope, the level and the question that set it, the live URL |
| `project/SLICES.md` | edit in place | Each slice, its status, its date |
| `project/DECISIONS.md` | append at the bottom | Every choice they made: the date, the question as you asked it, what they picked, one line of why, what it rules out |

`project/DECISIONS.md` grows downward and existing entries stay as written. It is the record they will show their team.

`.stack-level` holds one of `l0`, `l1`, `l2`, `l3`. The scripts read it. `/start` writes it.

## Skills

Each skill lives in `.agents/skills/<name>/SKILL.md`. Read the whole file before starting, and follow its steps in order. Reach for one when the person's request matches.

Codex reads that path directly. Claude Code reads `.claude/skills`, which is a symlink to the same folder, so both harnesses run the same files. When your harness lists no skills, the symlink did not survive checkout: open `.agents/skills/<name>/SKILL.md` by path and follow it exactly as written.

| Skill | Reach for it when |
| --- | --- |
| `start` | They describe something they want to build, or ask where to begin, and `project/BRIEF.md` does not exist yet |
| `make-skill` | A job repeats, only they do it, and it needs no shared record |
| `build` | The app should do something new, do something differently, or stop being broken |
| `add-data` | The app needs to store something it does not store yet |
| `explain` | They ask what something does, what changed, or say they are lost |
| `deploy` | They want it on the internet, or want the live version updated |
| `level-up` | The app has to serve more than one person, with logins or per-person records |

## Dependencies

Every package is one more thing that can break and one more thing to keep current. Prefer what the language and the platform already give you.

Before adding one, ask. State the exact version the policy resolved, and one sentence on why it beats twenty lines written here.

Add packages by bare name so the cooldown policy picks the version. Install with `pnpm install --frozen-lockfile` and `uv sync --locked`. Commit the lockfile in the same commit as the change that needed it.

`docs/recipes/_dependency-policy.md` has the mechanics.

## Working safely

These are hard limits. Where a limit has a positive form, do that instead.

- Read settings from `.env.example`, which holds names and placeholders. The real `.env.local` stays closed to you; when a value is needed, ask the person to paste it into their own file.
- Change history forward with new commits.
- Change the database through migrations, so every change is a file they keep.
- Remove files one named path at a time.

## Verifying

This project has no test suite. It is verified by running it: lint, type-check, build, then the person doing the job themselves in their own browser.

## Explaining

Every change ends with one line per file you touched, in their words, and one thing they could safely change and try.
