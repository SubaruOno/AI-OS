# Before anything goes live

Every item, in order, before the first deploy command. A failure gets fixed and the whole list runs again.

## Run the script

```bash
./scripts/preflight.sh
```

It does items 1 to 6 below. The rest are yours to check.

## 1. Lockfiles are committed

`pnpm-lock.yaml`, and `backend/uv.lock` at level 3, match what is committed.

An uncommitted lockfile means the server installs something you have not run.

## 2. It installs from the lock

`pnpm install --frozen-lockfile` and `uv sync --locked` both succeed without changing anything.

## 3. It passes its own checks

`pnpm lint`, `pnpm typecheck`, `pnpm build`. At level 3 also `ruff check` and `ruff format --check` in the backend.

## 4. Nothing secret reaches the browser

`./scripts/check-secrets.sh`. It checks six things:

- No settings file is committed to git
- Only allowlisted names carry a browser-visible prefix
- No key or database address is written into the code
- Anything reading the secret key is marked server-only
- No browser component imports a server-only file
- No real secret value appears anywhere in the built output

The last one is the decisive check. It searches the build for the literal values from `.env.local`, so a hit is always real.

## 5. The database is locked down

`./scripts/check-rls.sh`. Needs `SUPABASE_ACCESS_TOKEN` and `SUPABASE_PROJECT_REF` in the terminal.

It checks the live database for tables without row security, rules open to the public, rules that trust data users can edit, views that skip row security, functions that can be hijacked, public file buckets, and leftover permissions.

## 6. The settings match

Every name in `.env.example` has a value in the hosting provider, and the provider has nothing extra.

```bash
pnpm dlx vercel@latest env ls
```

Count them. Level 1 has four. Level 2 has two. Anything else arrived by accident.

## 7. Two accounts, at level 2

The two-account test in `docs/security/rls.md`. Not automated, and the only check that tells you whether row security works.

## 8. They know what it costs

Before the first deploy, look up the current prices and say the monthly figure. `docs/deploy/costs.md` has the links and the catches.

## When something fails

Fix the finding. The scripts report what is true about the app, so changing a script changes what you know rather than what is real.

Then run the whole list again from the top. A fix in one place moves things in another.
