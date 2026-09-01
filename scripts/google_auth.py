#!/usr/bin/env python3
"""Shared Google OAuth module for all Google API services.

Provides a single auth layer that Calendar, Gmail, and future Google services
import from. One token file, one setup flow, all scopes.

Usage:
    from google_auth import get_google_service
    gmail = get_google_service("gmail", "v1")
    calendar = get_google_service("calendar", "v3")
"""

import json
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = WORKSPACE_ROOT / "credentials" / "google-oauth-token.json"
CLIENT_SECRET = WORKSPACE_ROOT / "credentials" / "google-client.json"

# All Google scopes the workspace needs. Adding a new service = add scope here + re-auth.
SCOPES = [
    # Calendar
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    # Gmail (modify = read + write + send + labels + trash, no permanent delete)
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_credentials() -> Credentials:
    """Load and refresh Google OAuth credentials from the unified token file.

    Returns authenticated Credentials object. Exits with clear error if
    token file doesn't exist (directs user to setup script).
    """
    if not TOKEN_FILE.exists():
        print(
            "ERROR: No Google OAuth token found.\n"
            f"  Expected: {TOKEN_FILE}\n"
            "  Run: python scripts/setup_google_oauth.py (or python3 on macOS)",
            file=sys.stderr,
        )
        sys.exit(1)

    token_data = json.loads(TOKEN_FILE.read_text())
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_data["token"] = creds.token
        TOKEN_FILE.write_text(json.dumps(token_data, indent=2))

    return creds


def get_google_service(api_name: str, api_version: str):
    """Build an authenticated Google API service client.

    Args:
        api_name: API name (e.g. "gmail", "calendar")
        api_version: API version (e.g. "v1", "v3")

    Returns:
        googleapiclient.discovery.Resource service object
    """
    creds = get_credentials()
    return build(api_name, api_version, credentials=creds)
