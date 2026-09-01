# Fathom Call Intelligence: Complete Build Kit

> **How to install:** Open Claude Code, drop this folder in (or point Claude at it), and say:
> **"Read README.md in this folder and set it up for me step by step."**
> Claude handles everything: copying files, saving your API key, building your call database, and testing it with you. Setup takes about 5 minutes.

## Why This Exists

You record every call with Fathom. And then nobody ever watches them again.

Buried in those recordings: every objection a prospect raised, every commitment you made, every price discussion, every "let me think about it" that never got followed up. That is some of the most valuable data in your business, and right now it is unsearchable.

This kit gives Claude perfect memory of every call you have ever recorded. After setup, you just ask in plain English:

- "What objections came up in my sales calls this month?"
- "I have a call with Jamie tomorrow. Brief me on everything we have discussed."
- "What did I commit to in my last 5 calls?"
- "Pull the exact quote where the client approved the budget."
- "When did we decide to change the offer? Who suggested it?"

Claude finds the right call in a fraction of a second, pulls the transcript, and answers with exact quotes and timestamps.

## What You're Building

```
  You: "What did Jamie say about pricing last week?"
                      |
                      v
   +---------------------------------------+
   |  Claude Code (fathom-meetings skill)  |
   +---------------------------------------+
        |                        |
        v                        v
  +-------------+        +----------------+
  | Local cache |        |  Fathom API    |
  | (instant    |        |  (transcripts, |
  |  search of  |        |   summaries,   |
  |  ALL calls) |        |   new calls)   |
  +-------------+        +----------------+
```

**Capabilities:**
- Instant search across your entire call history by person, company, email, or title (~0.03 seconds, no internet needed)
- Full transcript retrieval with speaker names and timestamps
- AI summaries and action items for any call
- Impromptu/ad-hoc calls automatically labeled with the real people on them (not "Solo")
- Public share links for any recording
- Optional: a Call Intelligence agent that does cross-call analysis, such as meeting prep briefings, commitment tracking, and objection pattern detection

**Tech stack:** Python 3 standard library only. Zero packages to install. One API key. No servers, no databases, no monthly cost beyond your existing Fathom plan.

## Prerequisites

1. **Claude Code** installed and working
2. **A Fathom account with API access.** API access is included on Fathom's paid plans.
   - **New to Fathom?** Sign up here: **https://get.fathom.ai/workless**
   - **Already using Fathom?** Do not use the signup link. If you are on the free plan, upgrade to a paid plan from inside your Fathom account settings.
3. **Python 3** (already installed on every Mac and most Linux systems; on Windows, use WSL or install from python.org)

That's it.

## What's in This Kit

| File | What it does |
|------|-------------|
| `skill/SKILL.md` | The skill instructions Claude reads: API reference, search strategy, output formats |
| `skill/search_cache.py` | Instant name/company search over your local call database |
| `skill/build_cache.py` | Builds and updates the local call database from the Fathom API |
| `skill/fetch_meetings.py` | Date-range listings with summaries, fetched in parallel |
| `skill/enrich_cache.py` | One-time pass that labels impromptu "Solo" calls with the real speakers |
| `agents/call-intelligence.md` | Optional agent for cross-call analysis (meeting prep, objection patterns) |

## Step-by-Step Setup

**For Claude:** You are installing this for the user. Run the steps below in order. Ask the questions exactly where indicated, verify each step before moving on, and never display the API key back to the user or put it in a shell command with curl.

### Step 0: Confirm Fathom access

Ask the user: **"Do you already use Fathom to record your calls?"**
- **No, not yet**: give them the signup link from Prerequisites (https://get.fathom.ai/workless) and pause setup until their account exists and they have recorded calls to search.
- **Yes**: do NOT share the signup link. Confirm they are on a paid plan with API access; if not, direct them to upgrade from inside their Fathom account settings.

### Step 1: Copy the skill into place

Create `~/.claude/skills/fathom-meetings/` and copy everything from this kit's `skill/` folder into it.

**Verify:** `ls ~/.claude/skills/fathom-meetings/` shows SKILL.md and the four .py scripts.

### Step 2: Get and store the Fathom API key

Ask the user to:
1. Log in at fathom.video
2. Open **Settings** and find the **API** section (on paid plans; if they cannot find it, their plan may not include API access, see Prerequisites)
3. Generate an API key and paste it into the chat

Then save it:
```bash
mkdir -p ~/.config/fathom
# Write the key the user pasted into this file (use a file-writing tool, not echo, to avoid shell escaping issues)
chmod 600 ~/.config/fathom/api-key.txt
```

**Verify:** the file exists and is non-empty. Do not print its contents.

### Step 3: Ask the user two questions and write config.json

Ask:
1. **"What email address is your Fathom account under?"** (this filters them out of participant lists, so calls show the OTHER people)
2. **"What first name shows up for you in call transcripts?"** (usually just their first name)

Write the answers to `~/.claude/skills/fathom-meetings/config.json`:
```json
{
  "owner_email": "their@email.com",
  "owner_name": "TheirFirstName"
}
```

**Verify:** `python3 -c "import json; print(json.load(open('config.json')))"` from the skill folder prints both values.

### Step 4: Test the API connection

Run one small API call:
```bash
python3 -c "
import urllib.request, json, os
key = open(os.path.expanduser('~/.config/fathom/api-key.txt')).read().strip()
req = urllib.request.Request('https://api.fathom.ai/external/v1/meetings')
req.add_header('X-Api-Key', key)
data = json.loads(urllib.request.urlopen(req).read())
print(f\"Connected. Found {len(data.get('items', []))} recent meetings.\")
"
```

**Verify:** it prints "Connected." If it errors with 401, the key was pasted wrong; redo Step 2.

### Step 5: Build the call database

```bash
python3 ~/.claude/skills/fathom-meetings/build_cache.py
```

Tell the user: for a typical library this takes a few minutes. If they have hundreds of impromptu calls, the speaker-labeling pass can take longer (it fetches one transcript per unlabeled call, paced to respect Fathom's rate limit). It is safe to let it run in the background; you can start using the skill for named calls right away and run `enrich_cache.py` later for old impromptu calls.

**Verify:** the script ends with "Total: N meetings cached."

### Step 6: Test it for real

Ask the user for the name of someone they had a call with recently, then run:
```bash
python3 ~/.claude/skills/fathom-meetings/search_cache.py <that name>
```

Then answer a real question from the results, for example "summarize my last call with them" by pulling that recording's summary. Show the user the answer in the standard table format from SKILL.md.

### Step 7 (Optional but recommended): Install the Call Intelligence agent

This is the power feature for sales teams. Ask the user: **"Want the Call Intelligence agent too? It adds meeting prep briefings, commitment tracking across calls, and objection pattern detection."**

If yes:
1. Copy `agents/call-intelligence.md` to `~/.claude/agents/call-intelligence.md`
2. Interview the user to fill in the two template sections in that file:
   - **Team Roster**: "Who are the 5 to 10 people you talk to most on calls? For each: name, role, email if you know it." Fill the table.
   - **Product Context**: "What do you sell? Offers and price points." Fill the bullets.
3. Delete the two SETUP comment blocks once filled.

**Verify:** ask the user to try "Brief me for my next call with [person from their roster]."

### Done. Suggested first prompts for the user:

- "Show me my calls from last week"
- "What were the action items from my last call with [person]?"
- "What has [person] said about [topic] across our calls?"

## How It Works (Architecture)

**Cache-first design.** The Fathom API caps listings at 10 meetings per page, so searching hundreds of calls live would take minutes. Instead, `build_cache.py` walks the whole library once and saves a compact index (title, date, participants, IDs) to `meetings_cache.json`. Searches then run locally in milliseconds. Transcripts and summaries are fetched live, per recording, only when actually needed.

**The "Solo" problem.** Ad-hoc Zoom/Meet calls have no calendar invitees, so the API cannot tell you who was on them. The scripts solve this by pulling each such call's transcript and extracting the speaker display names, then storing those as the participants. Your impromptu calls become just as searchable as scheduled ones.

**Why urllib and not curl.** Fathom API keys can contain characters that break shell quoting. Passing the key through a shell command with curl corrupts it or leaks it into shell history. Every script reads the key from a file and sends it via Python's urllib, which has no escaping issues.

**Rate limiting.** Fathom allows 60 requests/minute for standard calls, but only 30/minute for "heavy" calls (transcripts and summaries), and can throttle harder during peak platform load. The scripts pace themselves (batching, delays, automatic retry on 429 responses that honors Fathom's Retry-After header), so even a full rebuild of a large library completes without errors.

**Share links.** Every recording has two URLs. The `url` field requires being logged in to your Fathom account. The `share_url` field is publicly viewable. The skill always hands out `share_url`, so links you paste to clients or teammates actually work.

## Customization Guide

- **Your identity**: `config.json` (`owner_email`, `owner_name`) controls who gets filtered out of participant lists. If your transcripts show a nickname, use that as `owner_name`.
- **Cache freshness**: `build_cache.py update` only fetches meetings newer than the last run, so it takes seconds. Run it whenever recent calls are missing. If you want it fully automatic, ask Claude to schedule it daily.
- **Summary length**: `fetch_meetings.py` truncates summaries to 80 characters for table display. Change the `80` in `extract_short_summary` if you want longer previews.
- **Agent personality**: `call-intelligence.md` is yours to edit. Add your sales methodology, your qualification framework, or your follow-up rules to the agent's instructions.

## Extending It

Once this is running, natural next steps (just ask Claude to build them):

- **Weekly objection report**: a scheduled job that scans the week's sales calls and summarizes recurring objections every Friday
- **Post-call follow-up drafts**: "Draft a follow-up email for today's call with [person]" using the transcript's action items
- **Testimonial mining**: search client calls for moments where customers describe results in their own words
- **CRM notes sync**: push call summaries into your CRM after each call

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `401` error on API calls | API key is wrong or expired. Regenerate in Fathom Settings and re-save the key file. |
| `429` error | Rate limit hit. The scripts auto-wait and retry; if calling the API manually, wait for the Retry-After header value (or 60 seconds). |
| No API section in Fathom Settings | Your plan does not include API access. Upgrade to a paid plan from inside your Fathom account settings. |
| A recent call is not found | Cache is stale. Run `build_cache.py update`. |
| Calls show as "Solo" | Run `enrich_cache.py` once to backfill speaker names for old impromptu calls. |
| Key works in Python but curl fails | Expected. The key breaks shell escaping. Never use curl; the scripts handle this. |
| `python3: command not found` (Windows) | Use WSL, or install Python 3 from python.org and ensure it is on PATH. |
| Summaries come back empty from `/meetings` | Known API quirk. Fetch `GET /recordings/{id}/summary` directly instead (the scripts already do this). |
| Search finds nothing for a person you definitely met | They may appear under a different display name. Try their company domain (e.g. `acme`) or partial name. |
| `/recordings/{id}` returns 404 | That endpoint does not exist. Use `/meetings` for listing and `/recordings/{id}/transcript` or `/summary` for details. |
