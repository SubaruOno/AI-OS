#!/usr/bin/env python3
"""
Fast Fathom meeting fetcher with parallel API calls.
Usage: python3 fetch_meetings.py [created_after] [created_before]
  Dates in ISO format: 2026-01-26T00:00:00Z
  If omitted, fetches the 10 most recent meetings.
"""
import json, sys, os, time, urllib.request, urllib.error, concurrent.futures

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
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
            '  {"owner_email": "you@yourcompany.com", "owner_name": "YourFirstName"}'
        )


def load_api_key():
    try:
        return open(KEY_FILE).read().strip()
    except FileNotFoundError:
        sys.exit(f"Fathom API key not found at {KEY_FILE}. See the setup guide.")


OWNER_EMAIL, OWNER_NAME = load_config()
API_KEY = load_api_key()


def api_get(path, _retries=2):
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, headers={"X-Api-Key": API_KEY})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        # Heavy endpoints can throttle hard under platform load; honor Fathom's Retry-After
        if e.code == 429 and _retries > 0:
            wait = int(e.headers.get("Retry-After") or 60)
            time.sleep(wait + 1)
            return api_get(path, _retries - 1)
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def extract_short_summary(summary_data):
    md = summary_data.get("summary", {}).get("markdown_formatted", "")
    if not md:
        return ""
    for line in md.split("\n"):
        cleaned = line.strip().lstrip("#").strip().lstrip("-").strip().lstrip("[").strip()
        if cleaned and len(cleaned) > 20:
            if "](http" in cleaned:
                cleaned = cleaned.split("](")[0].rstrip("[")
            cleaned = cleaned.strip("*").strip()
            if len(cleaned) > 80:
                cleaned = cleaned[:77] + "..."
            return cleaned
    return ""


def extract_speakers_from_transcript(transcript_data):
    """Extract unique speaker names from transcript data (most reliable source)."""
    entries = transcript_data.get("transcript", [])
    speakers = set()
    for entry in entries:
        name = entry.get("speaker", {}).get("display_name", "")
        if name:
            speakers.add(name)
    # Remove the owner's name variants so lists show the OTHER people on the call
    to_remove = set()
    for s in speakers:
        if OWNER_NAME.lower() in s.lower():
            to_remove.add(s)
    speakers -= to_remove
    return sorted(speakers)


def main():
    # Build query params
    params = "include_summary=true"
    if len(sys.argv) > 1:
        params += f"&created_after={sys.argv[1]}"
    if len(sys.argv) > 2:
        params += f"&created_before={sys.argv[2]}"

    # Step 1: List meetings
    data = api_get(f"/meetings?{params}")
    if "error" in data:
        print(f"Error listing meetings: {data['error']}", file=sys.stderr)
        sys.exit(1)

    items = data.get("items", [])
    if not items:
        print("No meetings found for this date range.")
        sys.exit(0)

    rec_ids = [m.get("recording_id") for m in items]

    # Identify which meetings need transcript-based speaker extraction
    # (meetings with no external calendar invitees = "Solo" meetings)
    solo_rec_ids = []
    for m in items:
        invitees = m.get("calendar_invitees", [])
        has_external = any(inv.get("email", "") != OWNER_EMAIL for inv in invitees)
        if not has_external:
            solo_rec_ids.append(m.get("recording_id"))

    # Step 2: Fetch ALL summaries + transcripts for Solo meetings in parallel
    summaries = {}
    transcripts = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        # Submit all summary requests
        summary_futures = {
            executor.submit(api_get, f"/recordings/{rid}/summary"): ("summary", rid)
            for rid in rec_ids
        }
        # Submit transcript requests only for Solo meetings
        transcript_futures = {
            executor.submit(api_get, f"/recordings/{rid}/transcript"): ("transcript", rid)
            for rid in solo_rec_ids
        }

        all_futures = {**summary_futures, **transcript_futures}
        for future in concurrent.futures.as_completed(all_futures):
            ftype, rid = all_futures[future]
            if ftype == "summary":
                summaries[rid] = future.result()
            else:
                transcripts[rid] = future.result()

    # Step 3: Build output
    results = []
    for i, m in enumerate(items):
        rec_id = m.get("recording_id")
        title = m.get("title", "N/A")
        date = m.get("created_at", "")[:10]

        # Get participants from calendar invitees (excluding owner)
        invitees = m.get("calendar_invitees", [])
        parts = []
        for inv in invitees:
            email = inv.get("email", "")
            if email == OWNER_EMAIL:
                continue
            name = inv.get("display_name") or email.split("@")[0]
            parts.append(name)

        # If no external participants, get real speakers from transcript
        if not parts and rec_id in transcripts:
            parts = extract_speakers_from_transcript(transcripts[rec_id])

        part_str = ", ".join(parts) if parts else "Solo"

        # Get short summary
        summary_data = summaries.get(rec_id, {})
        short_summary = extract_short_summary(summary_data)
        if not short_summary:
            short_summary = "No summary available"

        results.append({
            "num": i + 1,
            "date": date,
            "title": title,
            "participants": part_str,
            "summary": short_summary,
            "recording_id": rec_id,
            "share_url": m.get("share_url", "")
        })

    # Print as JSON for easy parsing by Claude
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
