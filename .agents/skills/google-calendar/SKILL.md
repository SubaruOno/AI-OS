---
name: google-calendar
description: >
  Google Calendar read/write access via CLI tool. Read today's events, tomorrow's events,
  week view, upcoming events within N hours. Also create, update, delete events and check
  free/busy windows. Reads all calendars accessible to the authorized account.
  Use for calendar, events today, calls or meetings today, tomorrow's calendar,
  free time, block time, add to calendar, create event, or schedule changes.
---

# Google Calendar

CLI tool at `scripts/calendar_tool.py`. Read and write. Auth via shared Google OAuth module (`scripts/google_auth.py`).

**Account:** Your primary calendar account (authorized during Google OAuth setup)

## CLI Reference

```bash
# Today's events
python scripts/calendar_tool.py today

# Tomorrow's events
python scripts/calendar_tool.py tomorrow

# Next 7 days (grouped by date)
python scripts/calendar_tool.py upcoming --days 7

# Upcoming events in the next N hours (default 4) — useful for midday pulse
python scripts/calendar_tool.py upcoming --hours 4

# Search events
python scripts/calendar_tool.py search "team meeting"

# Create a timed event
python scripts/calendar_tool.py create "Team sync" --start "2026-04-01T09:00:00" --end "2026-04-01T09:30:00"

# Create an all-day event
python scripts/calendar_tool.py create "Content day" --date "2026-04-01" --all-day

# Create a time block (focus block, no attendees)
python scripts/calendar_tool.py block "Deep work" --start "2026-04-01T14:00:00" --hours 3

# Update an event
python scripts/calendar_tool.py update EVENT_ID --summary "New title"

# Delete an event
python scripts/calendar_tool.py delete EVENT_ID

# Free/busy windows for a day
python scripts/calendar_tool.py free --date "2026-04-01"
```

## Output Format (reads)

Timed events:
```
HH:MM–HH:MM  Event Title [id: abc123]
             Location (if set)
```

All-day events:
```
2026-04-01 (all day)  Event Title
```

- Times shown in the timezone set in `.env` as TIMEZONE= (default: UTC if not set)
- All calendars accessible to your authorized account appear in read commands

## Notes

- Calendar scopes are in `scripts/google_auth.py` — token already includes them
- If calendar events do not appear, save the OAuth client JSON as
  `credentials/google-client.json`, then run
  `python scripts/setup_google_oauth.py` (`python3` on macOS if needed).
- Time blocks use colorId 7 (teal) by default — good visual distinction from meetings
