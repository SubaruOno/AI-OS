# Putting the Python backend on the internet

Level 3 only. Railway hosts the backend. Deploy it **before** the website, because the website needs its address.

## Two files first

`backend/.python-version`:

```
3.12
```

Without it Railway picks 3.13, and packages that have not caught up fail to build.

`backend/railway.json`:

```json
{
  "$schema": "https://railway.com/railway.schema.json",
  "build": { "builder": "RAILPACK" },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host :: --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

`--host ::` listens on both IPv6 and IPv4, which is what Railway's router expects. `0.0.0.0` answers Railway's health check and then quietly refuses real traffic.

Railway sees `pyproject.toml`, notices `uv.lock`, and installs with uv automatically.

## Deploy

```bash
brew install railway
railway login
railway init
railway link
```

Then the settings:

```bash
railway variables --set "DATABASE_URL=postgresql+psycopg://postgres.YOUR_REF:YOUR_PASSWORD@aws-0-YOUR_REGION.pooler.supabase.com:5432/postgres"
railway variables --set "ALLOWED_ORIGIN=http://localhost:5173"
```

Start with the localhost origin. You do not have the website's address yet.

```bash
railway up
railway domain
```

`railway domain` prints something like `https://your-service.up.railway.app`. Write it down; the website needs it.

## The database address

Take it from Supabase, under Connect, then **Session pooler**. Port 5432.

Not the transaction pooler on 6543: SQLAlchemy keeps connections open and uses prepared statements, and transaction mode breaks both.

Not the direct `db.<ref>.supabase.co` address: it answers on IPv6 only, Railway sends IPv4, and the error reads like a wrong password.

## Check it

```bash
curl https://your-service.up.railway.app/health
```

Expect `{"status":"ok"}`. If it hangs, read the logs:

```bash
railway logs
```

## Then the website

Deploy the frontend with [`vercel.md`](vercel.md), note its address, and come back to point the backend at it:

```bash
railway variables --set "ALLOWED_ORIGIN=https://your-app.vercel.app"
```

Railway redeploys itself. Until you do this, the website loads and every request it makes is refused by the browser.

## The order, in full

1. Deploy the backend with `ALLOWED_ORIGIN=http://localhost:5173`. Note the Railway address.
2. Set `VITE_API_BASE_URL` on Vercel to that address. Deploy the website. Note the Vercel address.
3. Set `ALLOWED_ORIGIN` on Railway to the Vercel address.
4. Open the site and do the job once.

Each piece needs the other's address, so it takes two passes. There is no way around it.

## When something is refused

The browser console says the request was blocked by CORS.

Check that `ALLOWED_ORIGIN` on Railway is the exact address in your browser's address bar, including `https://` and with no trailing slash.

Widening it to `["*"]` produces a different, harder error: browsers refuse a wildcard origin together with credentials. The fix is the exact address, always.

Preview deployments on Vercel get a new address for every commit, so they fail CORS. That is correct. Verify on the production address.

## Costs

Railway has no ongoing free tier: a trial credit, then services pause. Look up the current price at [railway.com/pricing](https://railway.com/pricing), and note that the paid tier is a floor rather than a cap, so heavy use costs more.

Record the live address and the date in `project/BRIEF.md`.
