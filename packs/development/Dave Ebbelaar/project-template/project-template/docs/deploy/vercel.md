# Putting a website on the internet

Vercel hosts the Next.js app at levels 1 and 2, and the React website at level 3.

At level 3, deploy the backend first with [`railway-fastapi.md`](railway-fastapi.md). This page needs its address.

## Before anything

```bash
./scripts/preflight.sh
```

It has to pass. It checks that nothing secret reaches the browser and that the database is locked down. Findings get fixed, not skipped.

## Connect

```bash
pnpm dlx vercel@latest login
pnpm dlx vercel@latest link
```

This creates a `.vercel` folder, already ignored by git.

At level 3, run these from inside `frontend/`, and set **Root Directory** to `frontend` in the project settings on Vercel.

## Settings

Type the values in. Do not install the Supabase integration from the Vercel marketplace.

That integration injects a dozen settings nobody asked for, including `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, and `POSTGRES_PASSWORD`. At level 2 that quietly puts a key that ignores row security into a project whose entire security model is that no such key exists. `scripts/check-secrets.sh` reads your files, not Vercel's dashboard, so it cannot see what the integration added.

There are one to four values, depending on the level.

**Level 1**, four settings, none public:

```bash
for v in SUPABASE_URL SUPABASE_SECRET_KEY APP_PASSWORD APP_SESSION_SECRET; do
  pnpm dlx vercel@latest env add "$v" production
  pnpm dlx vercel@latest env add "$v" preview
done
```

Generate the last two with `openssl rand -hex 32`.

**Level 2**, two settings, both public:

```bash
for v in NEXT_PUBLIC_SUPABASE_URL NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY; do
  pnpm dlx vercel@latest env add "$v" production
  pnpm dlx vercel@latest env add "$v" preview
done
```

**Level 3**, one setting, the Railway address with no trailing slash:

```bash
pnpm dlx vercel@latest env add VITE_API_BASE_URL production
```

Then read the list back and count it:

```bash
pnpm dlx vercel@latest env ls
```

Level 1 has exactly four names. Level 2 has two. Level 3 has one. Anything else arrived by accident and should go.

Values come from Supabase, under Connect or Project Settings then API Keys.

## Level 3 also needs a rewrite rule

`frontend/vercel.json`:

```json
{
  "rewrites": [{ "source": "/((?!assets/).*)", "destination": "/index.html" }]
}
```

Without it, every page except the first returns "not found" when someone refreshes or opens a link directly. The website handles its own navigation, so the server hands every address to `index.html`.

## Deploy

```bash
pnpm dlx vercel@latest deploy --prod
```

Vercel works out the framework on its own, reads `packageManager` from `package.json`, and installs with the lockfile.

At level 3, go back to Railway afterwards and set `ALLOWED_ORIGIN` to this new Vercel address. Until then, the site loads and every request it makes is refused.

## Then do the job

Open the live address and do the app's main job once, on the internet rather than on localhost. Then check the record landed in the Supabase table editor.

## Level 3: changing a setting means rebuilding

Vite writes `VITE_*` values into the built files. They are baked in at build time rather than read at run time, so changing one needs a new deploy rather than a restart.

```bash
pnpm dlx vercel@latest env rm VITE_API_BASE_URL production
pnpm dlx vercel@latest env add VITE_API_BASE_URL production
pnpm dlx vercel@latest deploy --prod
```

It is also why no key belongs in a `VITE_` name.

## The free plan cannot lock your site

Vercel's free plan protects preview links only. It cannot put a login wall in front of a live address.

This is why level 1 ships its own password screen. Removing `proxy.ts` turns an internal tool into a public website.

The free plan is also for non-commercial personal use, so a tool that runs part of a business belongs on a paid plan. On a paid plan, turn on Deployment Protection, then Vercel Authentication, then All Deployments, and delete the level 1 password screen. Check the current terms at [vercel.com/pricing](https://vercel.com/pricing).

## When it fails

**A release-age error from pnpm.** `package.json` and the lockfile disagree. Run `pnpm install` locally, commit the lockfile, push again. Turning off `minimumReleaseAgeStrict` to make it pass switches the seven-day protection off for every package, which is a bigger decision than the one being made.

**A missing setting.** The error names it. Add it and redeploy; settings added after a build are not in that build.

**Works locally, not live.** Almost always a setting that exists in `.env.local` and not in Vercel. Compare `vercel env ls` against `.env.example`.

**Blocked by CORS at level 3.** `ALLOWED_ORIGIN` on Railway does not match this exact address. Fix it there, not here. Preview deployments get a new address per commit and will fail CORS, which is correct.

## Afterwards

Open the Supabase dashboard, then Advisors, then Security Advisor. Confirm no errors.

Record the live address and the date in `project/BRIEF.md` under "Live at".
