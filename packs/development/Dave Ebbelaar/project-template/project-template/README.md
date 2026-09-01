# Project template

Build working software for your business with an AI assistant doing the typing. You do not need to know how to code.

## Start here

1. Install [Claude Code](https://claude.com/claude-code) or [Codex](https://developers.openai.com/codex).
2. Clone this repository and open it:

```bash
git clone https://github.com/daveebbelaar/project-template.git my-app && cd my-app
```

3. Start your assistant in that folder and tell it what you want:

```
I want something that tells me which invoices are overdue so I stop chasing them by hand.
```

It asks questions, one at a time, and writes down your answers.

## The four levels

After the interview it recommends a level. You can override the recommendation, and it records that you did.

| Level | What you get | Runs where | Costs |
| --- | --- | --- | --- |
| **0** | A written recipe your assistant follows. No website. | Your own machine | Nothing |
| **1** | One website behind one shared password. Everyone sees the same thing. | The internet | Free to try, then monthly |
| **2** | One website where everyone signs in and sees only their own records. | The internet | Free to try, then monthly |
| **3** | A website plus a separate engine for reading documents, running on a schedule, or handling big files. | The internet | Free to try, then monthly |

Your assistant looks up the current prices before you commit.

Level 0 is a real answer. A lot of what people call an app is a job they do by hand every week, and a recipe handles it for nothing.

Levels 1 and 2 are the same website. When you outgrow level 1, say so and it renovates in place.

## What to say

There are no commands to memorise.

| Say something like | What happens |
| --- | --- |
| "I want to build something that…" | It interviews you and sets up your project |
| "I want it to also show me…" | It builds one working piece, end to end |
| "I need to keep track of…" | It adds that to your database |
| "What does this file do?" or "I'm lost" | It gives you a plain-English tour |
| "Put this on the internet" | It runs the safety checks, then deploys |
| "Other people need their own logins" | It upgrades level 1 to level 2 |

## Your project's memory

Everything you decide is written into `project/` as plain text:

- `PROFILE.md` — you and your business
- `BRIEF.md` — what this app is for
- `SLICES.md` — what is built, what is next
- `DECISIONS.md` — every choice you made and why

## Staying safe

Your data lives in [Supabase](https://supabase.com). The dangerous mistake is letting the wrong person read the wrong records, so a script checks for it.

`./scripts/preflight.sh` runs every check and blocks the deploy until they pass. Your assistant runs it for you.

## What you need

- A [Supabase](https://supabase.com) account
- A [Vercel](https://vercel.com) account, for levels 1 to 3
- A [Railway](https://railway.com) account, for level 3
- [Node.js 22 or newer](https://nodejs.org)

Level 0 needs none of these.

On Windows, run everything in Git Bash rather than PowerShell, and set `git config --global core.symlinks true` before cloning. [docs/your-computer.md](docs/your-computer.md) covers the Mac and Windows differences that bite.

## Licence

MIT. See [LICENSE](LICENSE).
