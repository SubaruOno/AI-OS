---
name: deploy
description: Put the app on the internet, or ship a new version of one already there. Use when someone wants their app live, wants to share a link, or wants their latest changes on the live site.
---

# Deploy

Get it **live**: reachable on the internet, by someone who is not them, on a machine that is not theirs.

That is a binary. Running on their laptop is not live.

## 1. Clear the checks

Work [PREFLIGHT.md](PREFLIGHT.md) before running a single deploy command.

A finding gets fixed and the whole list runs again from the top. A check that reports a leak is reporting something true, so the fix is the app.

**Done when:** `./scripts/preflight.sh` exits clean, on a run where nothing was skipped.

## 2. Pick where it goes

Read the level in `.stack-level`.

- **Levels 1 and 2**: the whole app goes to Vercel. `docs/deploy/vercel.md`.
- **Level 3**: the backend goes to Railway first, then the website to Vercel with the backend's address, then back to Railway to point it at the website. `docs/deploy/railway-fastapi.md`, then `docs/deploy/vercel.md`.

Level 3 takes two passes because each piece needs the other's address. Say that up front so it does not look like something went wrong.

**Done when:** the level is stated and the matching deploy page has been read.

## 3. Set the settings before the first build

Every name in `.env.example` needs a value in the hosting provider. A setting added after a build is not in that build.

Type the values in. On Vercel, skip the Supabase marketplace integration: it adds a dozen settings nobody asked for, including a key that ignores row security, and the safety checks read your files rather than Vercel's dashboard.

Then read the list back and count it. Level 1 has exactly four names. Level 2 has exactly two.

**Done when:** the provider's list of settings matches `.env.example` exactly, name for name.

## 4. Ship it

Run the deploy command from the matching page.

**Done when:** the build log ends green and the live address loads the app's first screen.

## 5. Do the job on the internet

Have them do the app's main job once, at the live address, in their own browser. Then check the record landed in the Supabase table editor.

This catches settings that are right locally and wrong in production, which a successful build does not.

**Done when:** they confirm they completed the job at the live address, and the record is visible in Supabase.

## 6. Look at the advisor

Supabase dashboard, then Advisors, then Security Advisor. Confirm no errors.

It runs Supabase's own review and catches a few things the scripts do not.

**Done when:** the advisor shows no errors, or each one has been fixed with a migration.

## 7. Write it down

Put the live address and today's date in `project/BRIEF.md` under "Live at". Mark the deployed slices as `live` in `project/SLICES.md`. Append the hosting choices to `project/DECISIONS.md`.

Then tell them the one thing they need to know: what it costs per month, and what happens when they stop paying. `docs/deploy/costs.md` has the numbers.

## Shipping an update

Steps 1, 4, and 5. The settings are already there.

Never let a failing check through on the grounds that it worked last time. The check runs against what is about to ship.
