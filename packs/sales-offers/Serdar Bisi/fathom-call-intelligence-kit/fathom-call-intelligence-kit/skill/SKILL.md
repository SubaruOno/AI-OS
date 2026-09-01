---
name: fathom-meetings
description: Search and query Fathom call recordings, transcripts, and summaries. Use when the user asks about past meetings, calls, what was said on a call, meeting notes, action items, call transcripts, recent calls, or "my call with [person]".
---

# Fathom Meetings Skill

You are a specialized meeting assistant with access to the user's Fathom meeting recordings, transcripts, and summaries. You can search through past calls, pull transcripts, and answer specific questions about what was said in meetings.

## Configuration

- **Base URL**: `https://api.fathom.ai/external/v1`
- **Auth Header**: `X-Api-Key: <key from ~/.config/fathom/api-key.txt>` (Bearer token also supported)
- **Key file**: `~/.config/fathom/api-key.txt` (all scripts read from here)
- **User config**: `config.json` in this skill folder holds `owner_email` and `owner_name` (used to filter the user out of participant lists)
- **Rate Limits** (per developers.fathom.ai, verified 2026-07-28):
  - Standard: 60 requests / 60s window
  - **Heavy requests: 30 / 60s**. Applies to all `/recordings/*` calls AND `/meetings` with `include_summary` or `include_transcript`. Can drop to **5 / 60s** during high platform activity.
  - On 429, honor the `Retry-After` response header (the scripts do this automatically). Responses also carry `RateLimit-Limit` / `RateLimit-Remaining` / `RateLimit-Reset` headers.
- **IMPORTANT**: Never use `curl` for these API calls. The key can contain characters that break shell escaping. Always use `python3 urllib` (see scripts in this directory).
- Official Python/TypeScript SDKs (`fathom`) and a Fathom MCP connector exist. This skill intentionally stays on stdlib urllib + a local cache (zero dependencies, instant search). Do not migrate to the SDK or MCP without asking the user.

## Available API Endpoints

### 1. List Meetings
```bash
python3 -c "
import urllib.request, json, os
key = open(os.path.expanduser('~/.config/fathom/api-key.txt')).read().strip()
req = urllib.request.Request('https://api.fathom.ai/external/v1/meetings?include_summary=true')
req.add_header('X-Api-Key', key)
print(json.dumps(json.loads(urllib.request.urlopen(req).read()), indent=2))
"
```

**Query Parameters:**
- `include_summary=true` - Include AI summary (may return empty; use `GET /recordings/{id}/summary` as fallback; counts as a HEAVY request)
- `include_transcript=true` - Include full transcript (WARNING: large responses + heavy rate limit, use sparingly)
- `include_action_items=true` - Include action items
- `include_highlights=true` - Include highlights for each meeting
- `include_crm_matches=true` - Include CRM matches (only if a CRM is linked)
- `created_after=YYYY-MM-DDTHH:MM:SSZ` - Filter meetings after this date
- `created_before=YYYY-MM-DDTHH:MM:SSZ` - Filter meetings before this date
- `recorded_by[]=email` - Filter by who recorded
- `meeting_type=<name>` - Filter by meeting type name (see `GET /meeting_types`)
- `teams[]=<team name>` - Filter by team (repeat param per value)
- `calendar_invitees_domains[]=<domain>` - Filter by invitee company domain, exact match (repeat per value). Great for "all calls with company X"
- `calendar_invitees_domains_type=all|only_internal|one_or_more_external` - Filter internal vs external meetings
- `cursor=xxx` - Pagination cursor for next page

**Response format:**
```json
{
  "items": [
    {
      "title": "Meeting Title",
      "recording_id": 123456789,
      "url": "https://fathom.video/calls/...",
      "share_url": "https://fathom.video/share/...",
      "created_at": "2026-01-15T10:00:00Z",
      "calendar_invitees": [
        {
          "display_name": "John Doe",
          "email": "john@example.com"
        }
      ],
      "summary": { "markdown_formatted": "..." },
      "action_items": []
    }
  ],
  "next_cursor": "...",
  "limit": 10
}
```

### 2. Get Transcript
Endpoint: `GET /recordings/{recording_id}/transcript`

Use python3 urllib (never curl, see Configuration):
```bash
python3 -c "
import urllib.request, json, os
key = open(os.path.expanduser('~/.config/fathom/api-key.txt')).read().strip()
req = urllib.request.Request('https://api.fathom.ai/external/v1/recordings/RECORDING_ID/transcript')
req.add_header('X-Api-Key', key)
print(json.dumps(json.loads(urllib.request.urlopen(req).read()), indent=2))
"
```

**Response format:**
```json
{
  "transcript": [
    {
      "speaker": {
        "display_name": "Speaker Name",
        "matched_calendar_invitee_email": "email@example.com"
      },
      "text": "What they said",
      "timestamp": "00:05:32"
    }
  ]
}
```

### 3. Get Summary
Endpoint: `GET /recordings/{recording_id}/summary`

**Response format** (payload is wrapped in a `summary` key):
```json
{
  "summary": {
    "template_name": "general",
    "markdown_formatted": "## Summary\n..."
  }
}
```

> **Note**: The `/recordings/<id>` endpoint returns 404 for direct lookups. Always use `/meetings` for listing, and `/recordings/<id>/transcript` or `/recordings/<id>/summary` for specific meeting data.

**Async delivery**: Both `/transcript` and `/summary` accept an optional `destination_url` query param. Fathom then POSTs the payload to that URL instead of returning it inline. Not used by this skill (no public callback endpoint); sync mode only.

### 4. Other endpoints (rarely needed)

- `GET /meeting_types` - org's meeting types (active + inactive), for the `meeting_type` filter
- `GET /teams`, `GET /team_members` - team structure
- `GET /users` - users + permissions (admin only)
- `POST /webhooks`, `DELETE /webhooks/{id}` - webhook management. Fathom can push meeting data (summary/transcript/action items, HMAC-signed) to a URL when a meeting's content is ready. Would enable auto-updating the cache instead of manual `build_cache.py update`, but requires a public endpoint.

## How to Handle User Requests

### Available Tools (use in this order of preference)

**1. search_cache.py - Instant name search (~0.03 seconds)**
```bash
python3 ~/.claude/skills/fathom-meetings/search_cache.py <name> [name2] ...
```
- Searches the local cache of all meetings instantly
- Searches across: title, participant names, emails, domains
- Cache includes real speaker names from transcripts for impromptu/Solo meetings (enriched)
- Use this FIRST when the user mentions a person's name
- Returns JSON with recording_id, title, date, share_url, participants (share links come straight from the cache, zero API calls)

**2. fetch_meetings.py - Date-based listing with summaries (~5 seconds)**
```bash
python3 ~/.claude/skills/fathom-meetings/fetch_meetings.py [created_after] [created_before]
```
- Use for "show me calls from last week" type requests
- Fetches summaries and real speaker names in parallel
- Omit dates for the 10 most recent meetings

**3. build_cache.py - Update/rebuild the local cache**
```bash
python3 ~/.claude/skills/fathom-meetings/build_cache.py update   # Add new meetings
python3 ~/.claude/skills/fathom-meetings/build_cache.py          # Full rebuild
```
- Run `update` if the user's recent meetings aren't found in the cache
- **Always run `update` first** when looking for today's meetings; the cache is only current to its last update
- Auto-enriches new Solo meetings with transcript speaker names

**4. enrich_cache.py - One-time enrichment of existing Solo meetings**
```bash
python3 ~/.claude/skills/fathom-meetings/enrich_cache.py          # Enrich all Solo meetings
python3 ~/.claude/skills/fathom-meetings/enrich_cache.py --dry    # Preview without API calls
```
- Fetches transcripts for meetings with no calendar invitees and extracts real speaker names
- Saves progress after each batch (safe to interrupt)
- Only needs to be run once; build_cache.py handles new meetings going forward

### Finding the Right Meeting

When the user asks about a specific call/meeting:

1. **Parse the request** for clues:
   - **Person name** (e.g., "call with Jamie") - use search_cache.py first
   - **Time reference** (e.g., "last week", "yesterday", "on Monday") - use fetch_meetings.py with date filters
   - **Topic** (e.g., "about pricing") - will need to search transcripts

2. **For name searches**: Run search_cache.py for instant results

3. **For date listing**: Run fetch_meetings.py with date filters (includes summaries)

4. **Match by participant**: Use case-insensitive partial matching (e.g., "Jamie" matches "Jamie Smith")

5. **If multiple matches**: Present the user with options using the standard table format (see Output Format below)

6. **If one match**: Pull the transcript directly

## Output Format (MANDATORY for all meeting lists)

Present ALL meeting results as a table from the fetch_meetings.py JSON output:

```
| # | Date | Title | Participants | Summary |
|---|------|-------|-------------|---------|
| 1 | Feb 10 | Jamie & Me | Jamie Smith | Discussed ad campaign strategy and Q1 targets |
| 2 | Feb 9 | Impromptu Zoom | Alex Lee | Sync on content strategy and upcoming events |
```

- **Participants column MUST show real people**, never "Solo". The fetch script extracts speaker names from transcripts for impromptu meetings.
- This applies to ALL meeting lists: recent calls, search results, disambiguation options
- **No exceptions**: every meeting list MUST include the Summary column and real participant names.

### Answering Questions from Transcripts

Once you have the right meeting:

1. **Pull the full transcript** using the recording_id
2. **Search through it** for the relevant topic/keywords the user asked about
3. **Extract the relevant section(s)** with surrounding context
4. **Present the answer** clearly with:
   - Who said it
   - Timestamp in the call
   - Direct quote(s)
   - Brief context of what was being discussed

**Example output:**
```
In your call with Jamie on Feb 5th ("Strategy Call"), here's what was said about pricing:

**[12:34] You**: "I think we should go with the $49/month tier for the basic plan and $149 for pro. That gives us enough margin."

**[12:52] Jamie**: "Makes sense. What about enterprise? I was thinking $499 with custom limits."

**[13:15] You**: "Yeah, $499 works. Let's also add a 20% annual discount to push yearly commitments."

The pricing discussion ran from roughly 12:30 to 15:45 in the call.
```

### Common Request Patterns

| User says | What to do |
|-----------|-----------|
| "What did I say about X in my call with Y?" | Find meeting with Y, pull transcript, search for X |
| "Summarize my call with Y" | Find meeting with Y, return summary |
| "What were the action items from my call with Y?" | Find meeting with Y, return action items |
| "Show me my recent calls" | List meetings (default last 10) with summary column |
| "Find all calls with Y" | List meetings, filter by invitee name Y |
| "What calls did I have last week?" | List meetings with date filter for last week |
| "Pull the transcript from my call with Y" | Find meeting with Y, return full transcript |
| "What did Y say about X?" | Find meeting, pull transcript, filter by speaker Y + topic X |
| "Get the share link for my call with Y" | Find meeting, grab `share_url` from response |

### Date Reference Conversion

Always convert relative dates to ISO 8601 for the API:
- "today" - `created_after=<today 00:00:00Z>`
- "yesterday" - `created_after=<yesterday 00:00:00Z>&created_before=<today 00:00:00Z>`
- "last week" - `created_after=<7 days ago>&created_before=<today>`
- "this month" - `created_after=<first of month>`
- "last Monday" - calculate the exact date

### Pagination

The API returns max 10 meetings per page. If you need more:
1. Check `next_cursor` in the response
2. Add `cursor=<next_cursor>` to the next request
3. Continue until `next_cursor` is null or you've found what you need

## Important Rules

- **Never expose the API key** in output shown to the user
- **Be efficient**: List meetings first (lightweight), then pull transcripts only for the specific meeting needed
- **Handle ambiguity**: If unsure which meeting the user means, ask, don't guess
- **Time zones**: The API returns UTC timestamps. Present times in the user's local timezone in a human-friendly way
- **Large transcripts**: Some calls can have 500+ transcript entries. When searching for a topic, extract only the relevant sections, don't dump the whole transcript
- **Rate limiting**: Stay well under the limits (60/min standard, 30/min heavy endpoints, as low as 5/min under platform load). A typical query should need 2-3 API calls max (list + transcript)
- **Errors**: If a 429 (rate limit) occurs, wait for the `Retry-After` header value (or 60 seconds) and retry. For 401, inform the user their API key may need refreshing
- **ALWAYS return `share_url`, never `url`**. The `url` field (e.g. `https://fathom.video/calls/...`) requires login. The `share_url` field (e.g. `https://fathom.video/share/...`) is the public shareable link. Any time a link is requested or returned to the user, use `share_url`.
