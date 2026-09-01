#!/usr/bin/env python3
"""
Enrich Solo/impromptu meetings in the cache with real speaker names from transcripts.

For meetings that have no calendar invitees (marked as "Solo"), this script:
1. Fetches the transcript for each meeting
2. Extracts unique speaker names (excluding you, the owner)
3. Updates participant_names and participant_emails in the cache

Usage:
  python3 enrich_cache.py          # Enrich all Solo meetings
  python3 enrich_cache.py --dry    # Show how many need enrichment without fetching

Safe to interrupt: progress is saved after every batch.
Only needs to run once. build_cache.py enriches new meetings going forward.
"""
import json, urllib.request, time, sys, os

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE = os.path.join(SKILL_DIR, "meetings_cache.json")
CONFIG_FILE = os.path.join(SKILL_DIR, "config.json")
KEY_FILE = os.path.expanduser("~/.config/fathom/api-key.txt")
BASE = "https://api.fathom.ai/external/v1"

# Max concurrent requests to stay safely under 60/min rate limit
BATCH_SIZE = 10
BATCH_DELAY = 12  # seconds between batches (10 req per 12s = 50/min, safe margin)


def load_config():
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        return cfg["owner_name"]
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


OWNER_NAME = load_config()
API_KEY = load_api_key()


def api_get(path):
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, headers={"X-Api-Key": API_KEY})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def extract_speakers(transcript_data):
    """Extract unique speaker names from transcript, excluding the owner."""
    entries = transcript_data.get("transcript", [])
    speakers = {}
    for entry in entries:
        speaker = entry.get("speaker", {})
        name = speaker.get("display_name", "")
        email = speaker.get("matched_calendar_invitee_email", "")
        if name and OWNER_NAME.lower() not in name.lower():
            speakers[name] = email or speakers.get(name, "")
    return speakers


def apply_speakers(cache, idx, speakers):
    """Write extracted speakers into the cache entry at idx."""
    names = sorted(speakers.keys())
    emails = [speakers[n] for n in names]
    cache["meetings"][idx]["participant_names"] = ", ".join(names)
    cache["meetings"][idx]["participant_emails"] = ", ".join(e for e in emails if e)
    parts = []
    for name in names:
        email = speakers[name]
        domain = email.split("@")[1] if "@" in email else ""
        parts.append({"name": name, "email": email, "domain": domain})
    cache["meetings"][idx]["participants"] = parts
    return names


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def main():
    dry_run = "--dry" in sys.argv

    if not os.path.exists(CACHE_FILE):
        sys.exit("No cache found. Run build_cache.py first.")

    with open(CACHE_FILE) as f:
        cache = json.load(f)

    # Find meetings that need enrichment (no participant names)
    to_enrich = []
    for i, m in enumerate(cache["meetings"]):
        if not m.get("participant_names", "").strip():
            to_enrich.append((i, m))

    print(f"Total meetings: {len(cache['meetings'])}", file=sys.stderr)
    print(f"Need enrichment: {len(to_enrich)}", file=sys.stderr)

    if dry_run:
        print("Dry run, no API calls made.", file=sys.stderr)
        return

    enriched = 0
    failed = 0
    still_solo = 0

    for batch_start in range(0, len(to_enrich), BATCH_SIZE):
        batch = to_enrich[batch_start:batch_start + BATCH_SIZE]
        batch_num = batch_start // BATCH_SIZE + 1
        total_batches = (len(to_enrich) + BATCH_SIZE - 1) // BATCH_SIZE

        print(f"\nBatch {batch_num}/{total_batches} ({batch_start + 1}-{batch_start + len(batch)} of {len(to_enrich)})", file=sys.stderr)

        for idx, meeting in batch:
            rec_id = meeting["recording_id"]
            try:
                transcript = api_get(f"/recordings/{rec_id}/transcript")
                speakers = extract_speakers(transcript)

                if speakers:
                    names = apply_speakers(cache, idx, speakers)
                    enriched += 1
                    print(f"  + {meeting['date']} | {meeting['title'][:40]} -> {', '.join(names)}", file=sys.stderr)
                else:
                    still_solo += 1
                    print(f"  - {meeting['date']} | {meeting['title'][:40]} -> truly solo (no other speakers)", file=sys.stderr)

            except Exception as e:
                failed += 1
                err = str(e)
                if "429" in err:
                    print(f"  ! Rate limited. Saving progress and waiting 65s...", file=sys.stderr)
                    save_cache(cache)
                    time.sleep(65)
                    # Retry this one
                    try:
                        transcript = api_get(f"/recordings/{rec_id}/transcript")
                        speakers = extract_speakers(transcript)
                        if speakers:
                            names = apply_speakers(cache, idx, speakers)
                            enriched += 1
                            failed -= 1
                            print(f"  + (retry) {meeting['date']} | {meeting['title'][:40]} -> {', '.join(names)}", file=sys.stderr)
                    except Exception as e2:
                        print(f"  ! Failed retry: {meeting['date']} | {rec_id}: {e2}", file=sys.stderr)
                else:
                    print(f"  ! Error: {meeting['date']} | {rec_id}: {err[:80]}", file=sys.stderr)

            time.sleep(1.1)  # ~1 req/s within batch

        # Save progress after each batch
        save_cache(cache)
        print(f"  Saved. Progress: {enriched} enriched, {still_solo} truly solo, {failed} failed", file=sys.stderr)

        # Wait between batches to stay under rate limit
        if batch_start + BATCH_SIZE < len(to_enrich):
            remaining = len(to_enrich) - batch_start - len(batch)
            est_minutes = remaining / BATCH_SIZE * BATCH_DELAY / 60
            print(f"  Waiting {BATCH_DELAY}s... (~{est_minutes:.0f} min remaining)", file=sys.stderr)
            time.sleep(BATCH_DELAY)

    print(f"\nDone! Enriched: {enriched}, Truly solo: {still_solo}, Failed: {failed}", file=sys.stderr)
    print(f"Cache saved to: {CACHE_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()
