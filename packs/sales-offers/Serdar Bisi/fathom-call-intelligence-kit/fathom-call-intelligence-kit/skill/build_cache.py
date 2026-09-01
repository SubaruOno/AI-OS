#!/usr/bin/env python3
"""
Build/update a local cache of all Fathom meetings.
Paginates through every meeting and saves to meetings_cache.json.
Run periodically to pick up new meetings.

For Solo/impromptu meetings (no calendar invitees), automatically fetches
transcripts to extract real speaker names.

Usage:
  python3 build_cache.py          # Full rebuild
  python3 build_cache.py update   # Only fetch meetings newer than last cached
"""
import json, urllib.request, time, sys, os

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(SKILL_DIR, "meetings_cache.json")
CONFIG_FILE = os.path.join(SKILL_DIR, "config.json")
KEY_FILE = os.path.expanduser("~/.config/fathom/api-key.txt")
BASE = "https://api.fathom.ai/external/v1"


def load_config():
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        return cfg["owner_email"], cfg["owner_name"]
    except (FileNotFoundError, KeyError):
        sys.exit(
            'Missing or incomplete config.json next to this script.\n'
            'Create it with:\n'
            '  {"owner_email": "you@yourcompany.com", "owner_name": "YourFirstName"}\n'
            'owner_email = the email your Fathom account records calls with.\n'
            'owner_name  = your first name as it appears in call transcripts.'
        )


def load_api_key():
    try:
        return open(KEY_FILE).read().strip()
    except FileNotFoundError:
        sys.exit(f"Fathom API key not found at {KEY_FILE}. See the setup guide.")


OWNER_EMAIL, OWNER_NAME = load_config()
API_KEY = load_api_key()


def api_get(path):
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, headers={"X-Api-Key": API_KEY})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def extract_speakers_from_transcript(rec_id):
    """Fetch transcript and extract real speaker names for Solo meetings."""
    try:
        data = api_get(f"/recordings/{rec_id}/transcript")
        entries = data.get("transcript", [])
        speakers = {}
        for entry in entries:
            speaker = entry.get("speaker", {})
            name = speaker.get("display_name", "")
            email = speaker.get("matched_calendar_invitee_email", "")
            if name and OWNER_NAME.lower() not in name.lower():
                speakers[name] = email or speakers.get(name, "")
        return speakers
    except Exception as e:
        if "429" in str(e):
            print(f"    Rate limited fetching transcript for {rec_id}, waiting 62s...", file=sys.stderr)
            time.sleep(62)
            return extract_speakers_from_transcript(rec_id)  # retry once
        print(f"    Failed to get transcript for {rec_id}: {str(e)[:60]}", file=sys.stderr)
        return {}


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {"meetings": [], "last_updated": None}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    cache = load_cache()

    params = ""
    if mode == "update" and cache.get("last_updated"):
        params = f"created_after={cache['last_updated']}"
        print(f"Update mode: fetching meetings after {cache['last_updated']}", file=sys.stderr)
        existing_ids = {m["recording_id"] for m in cache["meetings"]}
    else:
        print("Full rebuild mode", file=sys.stderr)
        cache["meetings"] = []
        existing_ids = set()

    cursor = None
    page = 0
    new_meetings = []

    while True:
        page += 1
        query = params
        if cursor:
            query += f"{'&' if query else ''}cursor={cursor}"

        try:
            data = api_get(f"/meetings?{query}" if query else "/meetings")
        except Exception as e:
            if "429" in str(e):
                print(f"  Rate limited on page {page}, waiting 62s...", file=sys.stderr)
                time.sleep(62)
                continue
            raise

        items = data.get("items", [])
        if not items:
            break

        for m in items:
            rec_id = m.get("recording_id")
            if rec_id in existing_ids:
                continue

            invitees = m.get("calendar_invitees", [])
            parts = []
            for inv in invitees:
                email = inv.get("email", "")
                if email == OWNER_EMAIL:
                    continue
                name = inv.get("display_name") or email.split("@")[0]
                domain = email.split("@")[1] if "@" in email else ""
                parts.append({"name": name, "email": email, "domain": domain})

            new_meetings.append({
                "recording_id": rec_id,
                "title": m.get("title", ""),
                "date": m.get("created_at", "")[:10],
                "created_at": m.get("created_at", ""),
                "url": m.get("url", ""),
                "share_url": m.get("share_url", ""),
                "participants": parts,
                "participant_names": ", ".join([p["name"] for p in parts]) if parts else "",
                "participant_emails": ", ".join([p["email"] for p in parts]) if parts else "",
            })

        print(f"  Page {page}: {len(items)} meetings (range: {items[-1].get('created_at','')[:10]} to {items[0].get('created_at','')[:10]})", file=sys.stderr)

        cursor = data.get("next_cursor")
        if not cursor:
            break
        time.sleep(1.2)

    # Enrich Solo meetings with real speaker names from transcripts
    solo_meetings = [m for m in new_meetings if not m.get("participant_names", "").strip()]
    if solo_meetings:
        print(f"\nEnriching {len(solo_meetings)} Solo meetings with transcript speakers...", file=sys.stderr)
        enriched = 0
        for i, m in enumerate(solo_meetings):
            speakers = extract_speakers_from_transcript(m["recording_id"])
            if speakers:
                names = sorted(speakers.keys())
                emails = [speakers[n] for n in names]
                m["participant_names"] = ", ".join(names)
                m["participant_emails"] = ", ".join(e for e in emails if e)
                m["participants"] = [
                    {"name": n, "email": speakers[n], "domain": speakers[n].split("@")[1] if "@" in speakers[n] else ""}
                    for n in names
                ]
                enriched += 1
                print(f"  + {m['date']} | {m['title'][:40]} -> {', '.join(names)}", file=sys.stderr)
            else:
                print(f"  - {m['date']} | {m['title'][:40]} -> truly solo", file=sys.stderr)
            time.sleep(1.1)  # pace requests
        print(f"  Enriched {enriched}/{len(solo_meetings)} Solo meetings", file=sys.stderr)

    # Merge new meetings into cache
    cache["meetings"] = new_meetings + cache["meetings"]
    # Sort by date descending
    cache["meetings"].sort(key=lambda x: x["created_at"], reverse=True)
    # Update timestamp
    if cache["meetings"]:
        cache["last_updated"] = cache["meetings"][0]["created_at"]
    cache["total"] = len(cache["meetings"])

    save_cache(cache)
    print(f"\nDone! {len(new_meetings)} new meetings added. Total: {len(cache['meetings'])} meetings cached.", file=sys.stderr)
    print(f"Cache saved to: {CACHE_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()
