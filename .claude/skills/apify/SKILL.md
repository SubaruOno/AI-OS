---
name: apify
description: >
  Scrape places other tools cannot reach, including Instagram, TikTok, LinkedIn,
  Facebook, Google Maps, marketplaces, and review sites. Use when the user asks
  to scrape social comments, profiles, listings, reviews, marketplace data,
  competitor followers, or social engagement and Firecrawl or Supadata do not
  cover the source.
---

# Apify

The scraping service for everything the rest of the stack can't reach. Firecrawl covers websites; Supadata covers video transcripts; Apify covers the walled gardens: Instagram, TikTok, LinkedIn, Facebook, Google Maps, Amazon, review platforms and more, via a marketplace of thousands of pre-built scrapers called **actors**.

## First use: self-setup

If `APIFY_API_TOKEN` is missing from `.env`, walk the setup right then (this skill is designed to install itself on first need):

1. Explain the why in one line: "Apify runs pre-built scrapers for the platforms nothing else can reach, pay-as-you-go, free credits to start."
2. Sign up: https://console.apify.com (free plan includes monthly credits).
3. Get the token: Console → Settings → Integrations → Personal API token.
4. Run `python scripts/set_secret.py APIFY_API_TOKEN`; enter the value only in the hidden local prompt.
5. Run `python scripts/check_api_key.py apify`, then a tiny relevant actor run.

The shell snippets below use POSIX syntax. On Windows, translate them to
PowerShell or use Python. Never send a Windows user a Bash continuation command.

## How to use it

1. **Find the right actor** for the job. Search the store:
```bash
curl -s "https://api.apify.com/v2/store?search=<platform keywords>&limit=5" | head -c 2000
```
Prefer actors with high user counts and recent updates. The workhorses: `apify/instagram-scraper`, `clockworks/tiktok-scraper`, `apify/google-maps-scraper`, `apify/website-content-crawler`.

2. **Run it synchronously and get the data** (fine for small-to-medium jobs):
```bash
curl -s -X POST \
  "https://api.apify.com/v2/acts/<actor~name>/run-sync-get-dataset-items?token=$APIFY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '<actor input JSON>'
```
Each actor documents its input on its store page (`https://apify.com/<actor>`); fetch the page if unsure of the input shape.

3. **For big jobs**, start an async run (`/runs?token=...`), poll `/v2/actor-runs/<id>`, then pull `/v2/datasets/<datasetId>/items`.

4. **Land the data** somewhere useful: `data/` as CSV/JSON, or summarised straight into the analysis the user asked for.

## Rules

- Mind the credits: estimate result counts before big runs and say what a run will roughly cost in credits.
- Scrape respectfully and legally: public data, reasonable volumes, no login-walled personal data.
- If an actor fails, read its README on the store page before retrying blindly; input shape is the usual culprit.
