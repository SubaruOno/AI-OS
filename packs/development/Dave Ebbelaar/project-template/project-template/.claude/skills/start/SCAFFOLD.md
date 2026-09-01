# Building the starter

For levels 1 to 3, after the brief is written. Level 0 goes to `/make-skill` instead.

## Check the machine first

Read the machine from `project/PROFILE.md`. On Windows, confirm they are in Git Bash before running anything, and read `docs/your-computer.md`.

A project folder inside Dropbox, OneDrive, iCloud Drive, or Google Drive syncs every one of the thousands of files that a package install creates. Move it somewhere plain first: `~/dev/<name>` on Mac, `C:\dev\<name>` on Windows.

## Start the Supabase project first

Creating a Supabase project takes about two minutes. Start it before anything else and generate the app while it provisions, so nobody watches a spinner.

Tell them, in these words:

> Open supabase.com/dashboard and create a new project. Pick a region near you. Save the database password somewhere safe, it is shown once. Then come back and tell me when it's ready. I'll build the app while it starts up.

While they do that, keep going.

## Follow the recipe exactly

Read the recipe for their level and follow it as written:

- Level 1: `docs/recipes/l1.md`
- Level 2: `docs/recipes/l2.md`
- Level 3: `docs/recipes/l3.md`

Levels 1 and 2 also need `docs/recipes/_shared-nextjs.md`. All three need `docs/recipes/_dependency-policy.md`.

The recipes are tested. Follow the order they give, particularly the order of the dependency steps: the cooldown policy goes into place before the first package is added, and a package added before it has to be redone.

## What the recipes name no versions

Add packages by bare name. The policy resolves each one to the newest version that is at least seven days old and pins it exactly.

This is deliberate. A version written into a doc is stale within the week, and a stale pin plus the cooldown is a hard install failure. `docs/recipes/_dependency-policy.md` explains the mechanism.

## Ask before installing

The permission rules stop you installing anything without a click. When you ask, say three things: the package name, the version the policy resolved, and one sentence on what it does.

## Then lock the database down

Every level starts with `supabase/migrations/0000_lockdown.sql` from `docs/security/migrations.md`, pushed before any table exists. It closes the automatic web access that Supabase opens by default.

Tables come afterwards, through `/add-data`.

## Write the settings files

`.env.example` is committed and holds names with obviously fake placeholders. Write it yourself.

`.env.local` holds real values and is closed to you. Show them exactly what to paste, and where each value comes from in the Supabase dashboard:

> Create a file called `.env.local` in this folder and paste this in, replacing the two values from Supabase (Project Settings, then API Keys):
>
> ```
> NEXT_PUBLIC_SUPABASE_URL=
> NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
> ```

## Run it

```bash
pnpm install --frozen-lockfile
pnpm dev
```

Then give them the address and wait. Do not report success from the fact that the command started.

**Done when:** they say they can see the first screen in their own browser.

## Then check it

```bash
pnpm lint
pnpm typecheck
pnpm build
```

At level 1 the shape of `check-secrets.sh` is strictest: an empty allowlist, so any `NEXT_PUBLIC_` name at all is a finding.

## What to say at the end

Show them the folder they now have and name three things in it:

- `project/` is what this app is. Plain text, theirs to read and edit.
- `app/` (or `backend/` and `frontend/`) is the software.
- `./scripts/preflight.sh` is the safety check that runs before anything goes live.

Then ask what the first slice should be.
