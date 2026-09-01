# Getting your keys

> Every platform this workspace connects to, with the documented route. Claude or Codex walks through these one at a time, so the person never needs to read this cover to cover.
>
> **Routes last documented: 2026-07-28. Verify the current console before use.**

## For the assistant: how to run any block below

**Two stages, always. Never hand over both links at once.**

1. **Send the sign-up link first, on its own.** Then stop and wait for them to say they're signed in. Don't give them the key page yet, don't explain the next step, just wait. The sign-up link is the one that has to be clicked first.
2. **Once they confirm, give the key page.** Most consoles make it obvious from there. The direct link is in each block for anyone who gets lost.
3. **Keep the key out of chat.** Run `python scripts/set_secret.py KEY_NAME` (`python3` on macOS if needed). The person enters it into the hidden local prompt. Never print `.env` or place a secret in a command argument.
4. **Then test it.** Run `python scripts/check_api_key.py PROVIDER` where a provider is supported below, followed by one small real task. Call the step done only after a clean result.

## For the assistant: keep this file true

Console UIs move. Before walking anyone through a block, check the page still matches. If it doesn't:

1. Search for the current route, use it, finish the setup.
2. Update the block with the new path and a fresh `verified` date.
3. Add a line to the Changelog at the bottom.

Never delete a Changelog entry. A `verified` date more than a couple of months old is itself a reason to check first.

Two real examples of why, both found on 2026-07-28: Anthropic renamed its whole console from `console.anthropic.com` to `platform.claude.com`, and this file's own Supadata path was wrong before anyone used it.

---

## Product access

The person needs access to the harness they chose: Claude Code for the Claude
path or Codex for the OpenAI path. Product names, plans, and entitlements can
change. Confirm access in the current app or account page. This does not require
an API key.

---

## One rule that saves you an hour later: sign in with GitHub

You set up a GitHub account early in the install, before any of the sign-ups below. **Wherever a developer tool offers "Continue with GitHub", take it.** Supabase, Apify, Firecrawl and most of the others do.

- One identity instead of eight passwords, so no reset spiral six weeks from now.
- Turn on two-factor once, on GitHub, and it covers everything behind it.
- Your teammates already go through GitHub for repository access, so the pattern carries.

The exception is the model consoles. Anthropic, OpenAI and Gemini want an email or a Google account, and Gemini needs Google specifically. GitHub for developer tools, Google for the model consoles. Two identities, not eight.

---

## Integrations: one account, a thousand tools

### Composio
*Connects your business tools. Gmail, Slack, Notion, HubSpot, Stripe, Sheets and around a thousand more, without building an integration for each one.*

**1. Sign up:** https://composio.dev
Wait until they're in.

**2. Install the CLI and log in:**
```
curl -fsSL https://composio.dev/install | bash
composio login
```
No key to copy. The CLI holds the credentials.

**3. Connect a tool:** `composio link gmail` (swap for whatever they need). One OAuth click each.

**Test:** `composio whoami`, then something real: `composio search "recent emails"` and execute it.

Check the current plan page for limits before describing cost or usage quotas.

**Windows:** check the current Composio installation page for a native Windows route. If only a shell installer is offered, explain that before opening Git Bash. If the command still is not found, park it and use new-capability for the tool that matters most.

**Git itself on Windows:** `winget install --id Git.Git -e --source winget` installs it silently, no dialog. If winget isn't recognised, use https://git-scm.com/download/win and accept every default. Close and reopen PowerShell afterwards or `git` still won't be found.

`verified: 2026-07-28`

---

## Research services

### Firecrawl
*Reads any website properly. JavaScript-heavy pages, bot-protected sites, PDFs, and far cleaner content than basic tools.*

**1. Sign up:** https://firecrawl.link/worklessai
Wait until they're in.

**2. Get the key:** Dashboard → API Keys → create one.

**3. Save it locally.** Run `python scripts/set_secret.py FIRECRAWL_API_KEY`.

**Test:**
`python scripts/check_api_key.py firecrawl`
Returns their remaining credits. Then do a real one: scrape a competitor's pricing page and show them the content.

`verified: 2026-07-28`

### Supadata
*Turns video into text. YouTube, TikTok, Instagram, X. Also searches YouTube, so every video in your market becomes readable.*

**1. Sign up:** https://supadata.ai/?ref=worklessai
Wait until they're in.

**2. Get the key:** Dashboard at https://dash.supadata.ai → API Keys.

**3. Save it locally.** Run `python scripts/set_secret.py SUPADATA_API_KEY`.

**Test:**
`python scripts/check_api_key.py supadata`
Then do a real one: pull the transcript of a video in their niche.

`verified: 2026-07-28`

---

## Model keys: for what you build

Not for the workspace itself. These power the apps, scripts and agents built inside it. Get one the day it's needed.

### Anthropic
*The strong models. Behind anything that has to reason well, and what agents run on.*

**1. Sign up:** https://platform.claude.com
Wait until they're in. (The console used to be `console.anthropic.com`, which now redirects here.)

**2. Get the key:** https://platform.claude.com/settings/keys → Create Key.

**3. Save it locally.** Run `python scripts/set_secret.py ANTHROPIC_API_KEY`. It commonly starts with `sk-ant-`.

**Test:**
`python scripts/check_api_key.py anthropic`

`verified: 2026-07-28`

### OpenAI
*Mainly Whisper, for turning audio into text. Call recordings, voice notes, dictation.*

**1. Sign up:** https://platform.openai.com
Wait until they're in.

**2. Get the key:** https://platform.openai.com/api-keys → Create new secret key.

**3. Save it locally.** Run `python scripts/set_secret.py OPENAI_API_KEY`. It is normally shown once, so save it before closing the provider dialog.

**Test:**
`python scripts/check_api_key.py openai`. A successful authentication does not
prove that the account has usage credit, so follow it with the intended small
API call before declaring the integration ready.

`verified: 2026-07-28`

### Gemini
*Cheap and multimodal. Good for volume, and for reading images, audio and video directly.*

**1. Sign up:** https://aistudio.google.com
Wait until they're in.

**2. Get the key:** https://aistudio.google.com/apikey → Create API key.

**3. Save it locally.** Run `python scripts/set_secret.py GEMINI_API_KEY`.

**Test:**
`python scripts/check_api_key.py gemini`

`verified: 2026-07-28`

---

## Your data

### Supabase
*A real database instead of fifteen spreadsheets. Once the data is here, you can ask it things a spreadsheet can't answer.*

**1. Sign up:** https://supabase.com → Start your project. Sign in with GitHub, set up earlier in the install.

**2. Create an organisation, then a project.** Provisioning takes a couple of minutes.

**Test:** ask it to list the tables. Empty is the right answer on a fresh project, and it proves the connection.

Check the current Supabase plan before describing limits. The assistant builds the tables and moves the data in.

`verified: 2026-07-28`

### GitHub
*Backup, version history, and where teammates connect later.*

**1. Sign up:** https://github.com
**2. The assistant signs in** through GitHub's device flow, using the short browser code.

**Test:** push, then open the repo in a browser. Files there, `private/` absent.

Free plan covers unlimited private repositories and collaborators.

`verified: 2026-07-28`

---

## Talk instead of type

### Glaido
*Voice dictation. Around three times faster than typing, and this workspace is built around talking to it.*

**1. Sign up and install:** https://get.glaido.com/worklessai
**2. Follow the current installer for Windows or macOS.** Approve microphone and accessibility permissions only when the operating system asks and the person understands why.

**Test:** have them dictate their next answer instead of typing it.

`verified: 2026-07-28`

---

## Everything else, when you want it

### Apify
*Scrapes what nothing else reaches. Instagram, TikTok, LinkedIn, Google Maps, marketplaces, review sites.*

**1. Sign up:** https://apify.com?fpr=8txghh&fp_sid=workless
Wait until they're in.

**2. Get the token:** https://console.apify.com/settings/integrations → API tokens.

**3. Save it locally.** Run `python scripts/set_secret.py APIFY_API_TOKEN`.

**Test:**
`python scripts/check_api_key.py apify`

Sets itself up the first time someone asks to scrape one of those platforms.

`verified: 2026-07-28`

### xAI, for searching X
*What's being said in your market on X, right now.*

**1. Sign up:** https://console.x.ai
**2. Get the key:** API Keys. Save it with `python scripts/set_secret.py XAI_API_KEY`, then test with `python scripts/check_api_key.py xai`.

Paid, no free tier. There's an optional `X_BEARER_TOKEN` from `developer.x.com` that adds engagement numbers, but it needs a developer account and an app, so skip it unless likes and impressions are the point.

`verified: 2026-07-28`

### Gmail and Calendar
Through **Composio**, not a Google Cloud project. `composio link gmail` and `composio link googlecalendar`, one OAuth click each.

The old route (a Cloud project, two APIs enabled, a downloaded OAuth JSON, a setup script) still works and the scripts are in `scripts/`. It takes about twenty minutes instead of twenty seconds, so only reach for it if Composio can't cover what's needed.

`verified: 2026-07-28`

---

## Changelog

- **2026-07-28.** File created, every link and test verified live. Two-stage flow added (sign-up link first, wait for confirmation, then the key page). A tested check added to every block. Corrected Supadata's dashboard to `dash.supadata.ai` (was `supadata.ai/dashboard`). Recorded Anthropic's console move to `platform.claude.com`. Routed Gmail and Calendar through Composio instead of Google Cloud.
