#!/usr/bin/env python3
"""Unified Google OAuth setup for all workspace Google services.

Replaces per-service setup scripts (setup_calendar_oauth.py, etc.).
Authorizes all Google scopes at once: Calendar, Gmail, and future services.

Prerequisites:
1. Enable APIs in Google Cloud Console:
   - Google Calendar API: https://console.cloud.google.com/apis/library/calendar-json.googleapis.com
   - Gmail API: https://console.cloud.google.com/apis/library/gmail.googleapis.com
2. OAuth client at credentials/google-client.json

Usage:
    python scripts/setup_google_oauth.py

On macOS, use python3 if python is not available.
"""

import json
import sys
from pathlib import Path

# Import shared config
sys.path.insert(0, str(Path(__file__).resolve().parent))
from google_auth import SCOPES, TOKEN_FILE, CLIENT_SECRET


def main():
    if not CLIENT_SECRET.exists():
        print(f"ERROR: OAuth client secret not found at {CLIENT_SECRET}")
        print("This script reuses the YouTube OAuth client credentials from Google Cloud Console.")
        sys.exit(1)

    from google_auth_oauthlib.flow import InstalledAppFlow

    print("=" * 60)
    print("Google OAuth Setup (Unified)")
    print("=" * 60)
    print()
    print("This will authorize the workspace for ALL Google services:")
    print(f"  Scopes: {len(SCOPES)}")
    for s in SCOPES:
        name = s.split("/auth/")[-1] if "/auth/" in s else s
        print(f"    - {name}")
    print()
    print("Sign in with your Google account and grant all requested access.")
    print("A browser window will open now...")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    credentials = flow.run_local_server(port=0, prompt="consent")

    # Save unified token
    token_data = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes) if credentials.scopes else SCOPES,
    }

    TOKEN_FILE.write_text(json.dumps(token_data, indent=2))
    print(f"Token saved to {TOKEN_FILE}")
    print()

    # Verification tests
    from googleapiclient.discovery import build

    print("-" * 40)
    print("Verification")
    print("-" * 40)

    errors = []

    # Test Calendar
    try:
        cal = build("calendar", "v3", credentials=credentials)
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        events = cal.events().list(
            calendarId="primary", timeMin=now, maxResults=3,
            singleEvents=True, orderBy="startTime"
        ).execute()
        items = events.get("items", [])
        print(f"\nCalendar: OK ({len(items)} upcoming events)")
        for ev in items[:3]:
            start = ev["start"].get("dateTime", ev["start"].get("date"))
            print(f"  {start[:16]}  {ev.get('summary', '(no title)')}")
    except Exception as e:
        errors.append(f"Calendar: {e}")
        print(f"\nCalendar: FAILED - {e}")

    # Test Gmail
    try:
        gmail = build("gmail", "v1", credentials=credentials)
        profile = gmail.users().getProfile(userId="me").execute()
        email = profile.get("emailAddress", "unknown")
        total = profile.get("messagesTotal", 0)
        threads = profile.get("threadsTotal", 0)
        print(f"\nGmail: OK")
        print(f"  Account: {email}")
        print(f"  Messages: {total:,}  Threads: {threads:,}")
    except Exception as e:
        errors.append(f"Gmail: {e}")
        print(f"\nGmail: FAILED - {e}")

    print()
    if errors:
        print("WARNINGS:")
        for err in errors:
            print(f"  - {err}")
        print()
        print("Some services failed. Check that the APIs are enabled in Google Cloud Console.")
    else:
        print("All services verified. Google OAuth is ready.")

    print()
    print("CLI tools:")
    print("  python scripts/calendar_tool.py today")
    print("  python scripts/gmail_tool.py inbox")
    print("  python scripts/gmail_tool.py profile")


if __name__ == "__main__":
    main()
