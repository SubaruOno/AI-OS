# Keys and settings

Supabase gives you several keys. They look alike and do very different things. This page says which one belongs where.

## The rule

Two settings names are allowed to start with `NEXT_PUBLIC_` or `VITE_`:

```
NEXT_PUBLIC_SUPABASE_URL          VITE_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY   VITE_SUPABASE_PUBLISHABLE_KEY
```

That prefix means "print this on the front page of the app for the whole internet to read." Those two are designed to be read by strangers. Everything else keeps a plain name and is read on the server.

`scripts/check-secrets.sh` enforces exactly this list. It is an allowlist, so a new name with that prefix fails the check by default rather than by someone noticing.

## The keys

| Key | Looks like | What it can do | Where it belongs |
| --- | --- | --- | --- |
| Publishable | `sb_publishable_…` | Reads and writes only what your row security rules allow | Level 2 only, browser and server |
| Secret | `sb_secret_…` | Reads, changes, and deletes everything, ignoring every rule you wrote | Level 1 server only. Level 2 only with a written reason |
| Access token | `sbp_…` | Controls your whole Supabase account, every project | Your terminal only |
| Database password | inside `DATABASE_URL` | Full control of the database | Level 3 backend only |

The secret key ignores row security. That is its entire purpose: it exists so your server can do work on behalf of people who are not signed in. It is also why a copy of it in the wrong file is the single worst mistake available in this repository.

## Per level

### Level 0

No keys. There is no database and no website.

### Level 1

The browser never talks to Supabase at all. Your server does, using the secret key, and sends finished screens to the browser.

```
SUPABASE_URL
SUPABASE_SECRET_KEY
APP_PASSWORD
APP_SESSION_SECRET
```

Four names, none public. `scripts/check-secrets.sh` runs level 1 with an empty allowlist, so any `NEXT_PUBLIC_` name at all is a finding.

The secret key is read in exactly one file, `lib/supabase/admin.ts`, whose first line is `import "server-only"`. That line makes the build fail if a browser component ever imports it. It is a guardrail, not a comment.

### Level 2

The browser holds the publishable key and talks to Supabase directly. Row security is what keeps one person out of another person's records, which is why level 2's migrations are the strictest in this repository.

```
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
```

Two names, both public. That is the whole file.

The secret key belongs in a level 2 project only when a specific job needs it, such as inviting a user by email. When that happens, put it in `lib/supabase/admin.ts` with `import "server-only"`, and write one paragraph in `project/DECISIONS.md` saying which job needs it. When no such file exists, `SUPABASE_SECRET_KEY` should not exist in `.env.local` or in Vercel either.

### Level 3

The browser holds no Supabase key of any kind. Its only setting is the address of your own backend:

```
VITE_API_BASE_URL
```

The backend reaches the database directly with `DATABASE_URL`. Turn the Data API off in the Supabase dashboard (Settings, then Data API) so the automatic web endpoints stop answering entirely, regardless of keys. That is the strongest guardrail Supabase offers and it costs nothing.

When level 3 uses Supabase sign-in, the browser also gets `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY`, uses them for sign-in only, and sends the resulting token to your backend. Sign-in runs on a different endpoint from the Data API, so it keeps working with the Data API switched off.

## Where values live

`.env.example` is committed and holds names with obviously fake placeholders. `.env.local` holds the real values and is never committed.

Your access token (`sbp_…`) belongs in your terminal, not in a project file:

```bash
export SUPABASE_ACCESS_TOKEN=sbp_your_token_here
export SUPABASE_PROJECT_REF=your_project_ref
```

Put those two lines in `~/.zshrc` so they survive a restart.

## When a key gets out

Rotate it. A key that has been in a public place is spent, and no amount of deleting the file gets it back.

1. Supabase dashboard, then Project Settings, then API Keys.
2. Revoke the exposed key and create a new one.
3. Update `.env.local` and your hosting provider.
4. Redeploy.

Do this even when you are fairly sure nobody saw it. Rotating takes two minutes.
