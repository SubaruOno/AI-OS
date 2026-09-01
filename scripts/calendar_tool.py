#!/usr/bin/env python3
"""Google Calendar CLI tool for workspace-wide calendar access.

Claude Code or Codex can call this cross-platform Python CLI.
Supports reading events, creating events, updating events, and deleting events.

Usage:
    python scripts/calendar_tool.py today                          # Today's events
    python scripts/calendar_tool.py upcoming [--days 7]            # Next N days
    python scripts/calendar_tool.py search "meeting with nick"     # Search events
    python scripts/calendar_tool.py create "Team standup" \
        --start "2026-03-16T09:00:00" --end "2026-03-16T09:30:00" \
        --description "Weekly sync" --location "Zoom"
    python scripts/calendar_tool.py create "Content day" \
        --date "2026-03-17" --all-day                              # All-day event
    python scripts/calendar_tool.py block "Deep work" \
        --start "2026-03-16T14:00:00" --hours 3                   # Time block
    python scripts/calendar_tool.py update EVENT_ID \
        --summary "New title" --start "2026-03-16T10:00:00"
    python scripts/calendar_tool.py delete EVENT_ID
    python scripts/calendar_tool.py free --date "2026-03-16"       # Free/busy windows
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from google_auth import get_google_service

import os

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def _get_timezone() -> str:
    """Read timezone from TIMEZONE environment variable, defaulting to UTC."""
    timezone_str = os.getenv('TIMEZONE', 'UTC')
    try:
        ZoneInfo(timezone_str)  # Validate
        return timezone_str
    except Exception:
        return 'UTC'


def _get_service():
    """Build an authenticated Calendar API service via shared Google auth."""
    return get_google_service("calendar", "v3")


def _format_event(event: dict, tz_name: str) -> str:
    """Format a single event for terminal display."""
    summary = event.get("summary", "(no title)")
    start_raw = event["start"].get("dateTime", event["start"].get("date"))
    end_raw = event["end"].get("dateTime", event["end"].get("date"))
    is_all_day = "date" in event["start"]
    event_id = event["id"]

    if is_all_day:
        time_str = f"{start_raw} (all day)"
    else:
        try:
            start_dt = datetime.fromisoformat(start_raw)
            end_dt = datetime.fromisoformat(end_raw)
            start_local = start_dt.astimezone(ZoneInfo(tz_name))
            end_local = end_dt.astimezone(ZoneInfo(tz_name))
            time_str = f"{start_local.strftime('%H:%M')}–{end_local.strftime('%H:%M')}"
        except Exception:
            time_str = start_raw

    location = event.get("location", "")
    loc_str = f" | {location}" if location else ""
    hangout = event.get("hangoutLink", "")
    link_str = f" | {hangout}" if hangout else ""

    return f"  {time_str}  {summary}{loc_str}{link_str}  [id: {event_id[:12]}]"


def _get_events(service, time_min: str, time_max: str, calendar_id: str = "primary",
                query: str = None, max_results: int = 50) -> list:
    """Fetch events from a calendar within a time range."""
    kwargs = {
        "calendarId": calendar_id,
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": True,
        "orderBy": "startTime",
        "maxResults": max_results,
    }
    if query:
        kwargs["q"] = query

    result = service.events().list(**kwargs).execute()
    return result.get("items", [])


def cmd_today(args):
    """Show today's events."""
    service = _get_service()
    tz_name = _get_timezone()
    tz = ZoneInfo(tz_name)

    now = datetime.now(tz)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)

    events = _get_events(
        service,
        start_of_day.isoformat(),
        end_of_day.isoformat(),
    )

    print(f"📅 {now.strftime('%A, %B %d %Y')} ({tz_name})")
    print(f"   {len(events)} events\n")

    if not events:
        print("  No events today.")
        return

    for ev in events:
        print(_format_event(ev, tz_name))


def cmd_tomorrow(args):
    """Show tomorrow's events."""
    service = _get_service()
    tz_name = _get_timezone()
    tz = ZoneInfo(tz_name)

    now = datetime.now(tz)
    tomorrow_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow_end = tomorrow_start + timedelta(days=1)

    events = _get_events(
        service,
        tomorrow_start.isoformat(),
        tomorrow_end.isoformat(),
    )

    print(f"📅 {tomorrow_start.strftime('%A, %B %d %Y')} ({tz_name})")
    print(f"   {len(events)} events\n")

    if not events:
        print("  No events tomorrow.")
        return

    for ev in events:
        print(_format_event(ev, tz_name))


def cmd_upcoming(args):
    """Show events for next N days or N hours."""
    service = _get_service()
    tz_name = _get_timezone()
    tz = ZoneInfo(tz_name)

    now = datetime.now(tz)

    # Hours mode: surface events in the next N hours from now
    if hasattr(args, "hours") and args.hours:
        start = now
        end = now + timedelta(hours=args.hours)
        events = _get_events(service, start.isoformat(), end.isoformat(), max_results=20)
        print(f"📅 Next {args.hours} hours ({now.strftime('%H:%M')} → {end.strftime('%H:%M')}) | {tz_name}")
        print(f"   {len(events)} events\n")
        for ev in events:
            print(_format_event(ev, tz_name))
        return

    days = args.days
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=days)

    events = _get_events(service, start.isoformat(), end.isoformat(), max_results=100)

    print(f"📅 Next {days} days ({now.strftime('%b %d')} – {(now + timedelta(days=days-1)).strftime('%b %d')}) | {tz_name}")
    print(f"   {len(events)} events\n")

    # Group by date
    current_date = None
    for ev in events:
        start_raw = ev["start"].get("dateTime", ev["start"].get("date"))
        try:
            if "T" in start_raw:
                ev_date = datetime.fromisoformat(start_raw).astimezone(tz).strftime("%A, %b %d")
            else:
                ev_date = datetime.strptime(start_raw, "%Y-%m-%d").strftime("%A, %b %d")
        except Exception:
            ev_date = start_raw[:10]

        if ev_date != current_date:
            current_date = ev_date
            print(f"\n  {current_date}")
            print(f"  {'─' * 40}")

        print(_format_event(ev, tz_name))


def cmd_search(args):
    """Search events by query string."""
    service = _get_service()
    tz_name = _get_timezone()
    tz = ZoneInfo(tz_name)

    now = datetime.now(tz)
    # Search past 30 days + next 30 days
    start = (now - timedelta(days=30)).isoformat()
    end = (now + timedelta(days=30)).isoformat()

    events = _get_events(service, start, end, query=args.query, max_results=20)

    print(f"🔍 Search: \"{args.query}\" ({len(events)} results)\n")
    for ev in events:
        start_raw = ev["start"].get("dateTime", ev["start"].get("date"))
        date_str = start_raw[:10]
        print(f"  {date_str} {_format_event(ev, tz_name).strip()}")


def cmd_create(args):
    """Create a new calendar event."""
    service = _get_service()
    tz_name = _get_timezone()

    body = {"summary": args.summary}

    if args.description:
        body["description"] = args.description
    if args.location:
        body["location"] = args.location

    if args.all_day:
        date = args.date or datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d")
        body["start"] = {"date": date}
        end_date = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        body["end"] = {"date": args.end_date or end_date}
    else:
        if not args.start:
            print("ERROR: --start is required for timed events", file=sys.stderr)
            sys.exit(1)
        body["start"] = {"dateTime": args.start, "timeZone": tz_name}
        if args.end:
            body["end"] = {"dateTime": args.end, "timeZone": tz_name}
        else:
            # Default 1 hour
            start_dt = datetime.fromisoformat(args.start)
            end_dt = start_dt + timedelta(hours=1)
            body["end"] = {"dateTime": end_dt.isoformat(), "timeZone": tz_name}

    if args.attendees:
        body["attendees"] = [{"email": e.strip()} for e in args.attendees.split(",")]

    if args.color:
        body["colorId"] = args.color

    event = service.events().insert(calendarId="primary", body=body).execute()
    print(f"Created: {event.get('summary')}")
    print(f"  ID: {event['id']}")
    print(f"  Link: {event.get('htmlLink')}")


def cmd_block(args):
    """Create a time block (event with no attendees, colored differently)."""
    service = _get_service()
    tz_name = _get_timezone()

    if not args.start:
        print("ERROR: --start is required", file=sys.stderr)
        sys.exit(1)

    start_dt = datetime.fromisoformat(args.start)
    end_dt = start_dt + timedelta(hours=args.hours)

    body = {
        "summary": args.summary,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": tz_name},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": tz_name},
        "colorId": args.color or "7",  # 7 = peacock/teal, good for focus blocks
        "transparency": "opaque",
    }

    if args.description:
        body["description"] = args.description

    event = service.events().insert(calendarId="primary", body=body).execute()
    print(f"Time block created: {event.get('summary')}")
    print(f"  {start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')} ({args.hours}h)")
    print(f"  ID: {event['id']}")


def cmd_update(args):
    """Update an existing calendar event."""
    service = _get_service()
    tz_name = _get_timezone()

    # Get existing event first
    event = service.events().get(calendarId="primary", eventId=args.event_id).execute()

    if args.summary:
        event["summary"] = args.summary
    if args.description:
        event["description"] = args.description
    if args.location:
        event["location"] = args.location
    if args.start:
        event["start"] = {"dateTime": args.start, "timeZone": tz_name}
    if args.end:
        event["end"] = {"dateTime": args.end, "timeZone": tz_name}
    if args.color:
        event["colorId"] = args.color

    updated = service.events().update(
        calendarId="primary", eventId=args.event_id, body=event
    ).execute()
    print(f"Updated: {updated.get('summary')}")
    print(f"  Link: {updated.get('htmlLink')}")


def cmd_delete(args):
    """Delete a calendar event."""
    service = _get_service()
    service.events().delete(calendarId="primary", eventId=args.event_id).execute()
    print(f"Deleted event: {args.event_id}")


def cmd_free(args):
    """Show free/busy windows for a given date."""
    service = _get_service()
    tz_name = _get_timezone()
    tz = ZoneInfo(tz_name)

    date_str = args.date or datetime.now(tz).strftime("%Y-%m-%d")
    day_start = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz)
    day_end = day_start + timedelta(days=1)

    # Get all events for the day
    events = _get_events(service, day_start.isoformat(), day_end.isoformat())

    # Build busy blocks
    busy = []
    for ev in events:
        if "date" in ev["start"]:  # Skip all-day events for free/busy
            continue
        try:
            s = datetime.fromisoformat(ev["start"]["dateTime"]).astimezone(tz)
            e = datetime.fromisoformat(ev["end"]["dateTime"]).astimezone(tz)
            busy.append((s, e, ev.get("summary", "")))
        except Exception:
            continue

    busy.sort(key=lambda x: x[0])

    # Working hours: 7 AM - 9 PM
    work_start = day_start.replace(hour=7)
    work_end = day_start.replace(hour=21)

    print(f"📊 Free/busy: {day_start.strftime('%A, %b %d')} ({tz_name})")
    print(f"   Working hours: 7:00–21:00\n")

    if not busy:
        print(f"  ✅ Entirely free (7:00–21:00) — 14 hours available")
        return

    # Calculate free windows
    free_windows = []
    cursor = work_start
    for start, end, title in busy:
        if start > cursor:
            gap = start - cursor
            if gap.total_seconds() >= 900:  # 15min minimum
                free_windows.append((cursor, start, gap))
        cursor = max(cursor, end)

    if cursor < work_end:
        gap = work_end - cursor
        if gap.total_seconds() >= 900:
            free_windows.append((cursor, work_end, gap))

    print("  Busy:")
    for s, e, title in busy:
        print(f"    {s.strftime('%H:%M')}–{e.strftime('%H:%M')}  {title}")

    total_free = sum(w[2].total_seconds() for w in free_windows) / 3600
    print(f"\n  Free ({total_free:.1f}h available):")
    for s, e, gap in free_windows:
        hours = gap.total_seconds() / 3600
        print(f"    {s.strftime('%H:%M')}–{e.strftime('%H:%M')}  ({hours:.1f}h)")


def main():
    parser = argparse.ArgumentParser(description="Google Calendar CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # today
    sub.add_parser("today", help="Today's events")

    # tomorrow
    sub.add_parser("tomorrow", help="Tomorrow's events")

    # upcoming
    p = sub.add_parser("upcoming", help="Next N days (--days) or next N hours (--hours)")
    p.add_argument("--days", type=int, default=7, help="Days ahead (default 7)")
    p.add_argument("--hours", type=int, default=0, help="Hours ahead (overrides --days if set)")

    # search
    p = sub.add_parser("search", help="Search events")
    p.add_argument("query")

    # create
    p = sub.add_parser("create", help="Create event")
    p.add_argument("summary")
    p.add_argument("--start", help="Start datetime (ISO format)")
    p.add_argument("--end", help="End datetime (ISO format)")
    p.add_argument("--date", help="Date for all-day events (YYYY-MM-DD)")
    p.add_argument("--end-date", help="End date for multi-day events")
    p.add_argument("--all-day", action="store_true")
    p.add_argument("--description")
    p.add_argument("--location")
    p.add_argument("--attendees", help="Comma-separated emails")
    p.add_argument("--color", help="Color ID (1-11)")

    # block
    p = sub.add_parser("block", help="Create time block")
    p.add_argument("summary")
    p.add_argument("--start", required=True, help="Start datetime (ISO format)")
    p.add_argument("--hours", type=float, default=2, help="Duration in hours")
    p.add_argument("--description")
    p.add_argument("--color", help="Color ID (1-11, default 7=teal)")

    # update
    p = sub.add_parser("update", help="Update event")
    p.add_argument("event_id")
    p.add_argument("--summary")
    p.add_argument("--description")
    p.add_argument("--location")
    p.add_argument("--start")
    p.add_argument("--end")
    p.add_argument("--color")

    # delete
    p = sub.add_parser("delete", help="Delete event")
    p.add_argument("event_id")

    # free
    p = sub.add_parser("free", help="Free/busy windows")
    p.add_argument("--date", help="Date (YYYY-MM-DD, default today)")

    args = parser.parse_args()
    cmd_map = {
        "today": cmd_today,
        "tomorrow": cmd_tomorrow,
        "upcoming": cmd_upcoming,
        "search": cmd_search,
        "create": cmd_create,
        "block": cmd_block,
        "update": cmd_update,
        "delete": cmd_delete,
        "free": cmd_free,
    }
    cmd_map[args.command](args)


if __name__ == "__main__":
    main()
