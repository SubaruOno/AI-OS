---
name: outlier-report-creator
description: >-
  Scans YouTube channels you're tracking for outlier videos (ones way above that
  channel's own normal view count) and suggests video ideas based on what's
  actually working right now. Use when the user says: "scan my competitors",
  "run the outlier report", "check what's trending", "find outlier videos",
  "what should I make next", or "add a channel to track".
disable-model-invocation: false
argument-hint: "[--add <channel-url-or-handle>] or leave blank to scan"
---

# Outlier Report Creator

Finds videos that are massively out-performing a channel's own normal numbers, across every channel you're tracking, then turns that into concrete video ideas for your own channel.

This skill does two very different things, on purpose:
1. A small Python script does the mechanical part — hitting the YouTube API, computing view-count outliers, writing a plain data report. No creativity, no opinions.
2. **You (Claude) do the creative part** — reading that raw data next to what you know about the user's business, and suggesting what they should actually make. Don't skip this step. A report full of tables with no suggestions at the end is an incomplete run of this skill.

## First-time setup (only if not already done)

Check for these two things before running anything. Walk the user through whichever is missing — don't assume, don't skip.

### 1. YouTube Data API key

Check for a `.env` file in the project root with `YOUTUBE_API_KEY` set. If missing:

> "This tool needs a free YouTube API key to read channel data. Here's how to get one (takes about 2 minutes):
> 1. Go to https://console.cloud.google.com/
> 2. Create a new project (top left, name it anything — e.g. 'youtube-tools')
> 3. In the search bar, search for **'YouTube Data API v3'** and click **Enable**
> 4. Go to **APIs & Services → Credentials → Create Credentials → API Key**
> 5. Copy the key it gives you and paste it here"

Once they give you the key, create/append to a `.env` file in the project root:
```
YOUTUBE_API_KEY=their_key_here
```

The free tier gives 10,000 quota units/day — enough to scan roughly 90-95 channels a day, far more than most people need.

### 2. Business context (this is what makes the suggestions good)

Check for `business-context.md` in the project root. If it doesn't exist, this is a brand-new setup — have a short conversation, don't just fire off a form. Ask, one at a time if needed:
- "What's your channel/business about, in a sentence or two?"
- "Who's your audience — who are you actually making videos for?"
- "What's your angle — what do you do differently from everyone else covering similar ground?"

Save their answers to `business-context.md` in the project root, plain prose is fine, e.g.:

```markdown
# Business Context

**What I make videos about:** ...
**My audience:** ...
**My angle / what makes me different:** ...
```

You'll re-read this file every time you generate suggestions later. If it already exists, skip this step silently — don't re-ask unless the user wants to update it.

### 3. Python dependency

Check `python3 -c "import yaml"` works. If not, run `pip3 install pyyaml`.

## Adding channels to track

If the user gives you a channel URL or @handle (via `--add` or just in conversation), or this is a fresh setup with no channels yet, resolve and add it:

```bash
cd .claude/skills/outlier-report-creator
python3 outlier_scanner.py --add "<url-or-handle>"
```

Ask which channels they want to track if none are configured yet — at least 3-5 gives the outlier detection something meaningful to compare against. These should be channels in their own niche/competitive space, not random channels.

## Running a scan

```bash
cd .claude/skills/outlier-report-creator
python3 outlier_scanner.py
```

This writes `output/outlier-report-{date}.md` — a plain data report: a ranked table of outlier videos (view multiplier vs. that channel's own median), and a "Trending Across Channels" section for phrases repeating across 2+ tracked channels.

## After the scan: generate suggestions (do not skip this)

1. Read the generated report.
2. Read `business-context.md`.
3. Write a new section at the top of your response (and append it to the report file) called **"Video Ideas For You"** — 3-5 concrete, specific video ideas, each one:
   - Grounded in a real outlier from the report (name which one, and why it's relevant)
   - Adapted through the lens of `business-context.md` — their actual angle, not a generic swap
   - Phrased as an actual title they could film, not a topic area

This is the payoff of the whole tool. Someone running this should walk away with things to film, not just a table of numbers.

## Notes

- If the API returns a quota-exceeded error, tell the user their free daily quota (10,000 units) is used up and to try again tomorrow, or scan fewer channels at once. Don't attempt any scraping workaround.
- Never fabricate view counts or channel data — if the API call for a channel fails, skip it and say so, don't guess.

---

## Embedded script — write this to `outlier_scanner.py` in this skill's folder if it doesn't already exist

```python
#!/usr/bin/env python3
"""YouTube Outlier Report Creator — scans tracked channels for outlier videos.

Usage:
    python3 outlier_scanner.py --add <handle-or-url>   # Add a channel to track
    python3 outlier_scanner.py                          # Scan all tracked channels
"""

import argparse
import json
import os
import re
import statistics
import sys
import urllib.request
import urllib.parse
from collections import defaultdict
from datetime import datetime, timedelta

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "competitors.yaml")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")

MODERATE_THRESHOLD = 2.0
STRONG_THRESHOLD = 5.0
VIRAL_THRESHOLD = 10.0
RECENCY_DAYS = 60
MAX_VIDEOS_PER_CHANNEL = 20

LEVEL_EMOJI = {"viral": "🔴", "strong": "🟠", "moderate": "🟡"}

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "to", "of", "in", "on", "for", "with",
    "at", "by", "from", "this", "that", "these", "those", "is", "are", "was",
    "were", "be", "been", "being", "i", "you", "your", "my", "we", "our", "it",
    "its", "how", "what", "why", "when", "where", "which", "who", "do", "does",
    "did", "get", "got", "can", "will", "would", "should", "just", "not", "no",
    "so", "if", "as", "up", "out", "new", "use", "using", "video", "full", "vs",
    "into", "about", "than", "you're", "im", "i'm",
}


def _load_env():
    """Load .env from the project root (walking up) into os.environ."""
    project_root = SCRIPT_DIR
    for _ in range(5):
        env_path = os.path.join(project_root, ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
            return
        project_root = os.path.dirname(project_root)


_load_env()
API_KEY = os.environ.get("YOUTUBE_API_KEY", "")


def _api_get(url, params):
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{url}?{query}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def resolve_channel_id(handle_or_url):
    """Resolve a channel handle or URL into a channel ID + display name."""
    handle = handle_or_url.strip()
    match = re.search(r"@([\w.-]+)", handle)
    if match:
        handle = "@" + match.group(1)
    elif not handle.startswith("@"):
        handle = "@" + handle

    try:
        data = _api_get("https://www.googleapis.com/youtube/v3/channels", {
            "part": "snippet",
            "forHandle": handle,
            "key": API_KEY,
        })
        items = data.get("items", [])
        if items:
            return items[0]["id"], items[0]["snippet"]["title"]
    except Exception as e:
        print(f"    Error resolving {handle}: {e}")
    return None, None


def fetch_recent_videos(channel_id, max_results=MAX_VIDEOS_PER_CHANNEL):
    """Fetch the most recent videos from a channel with view counts."""
    try:
        search_data = _api_get("https://www.googleapis.com/youtube/v3/search", {
            "part": "snippet",
            "channelId": channel_id,
            "order": "date",
            "maxResults": max_results,
            "type": "video",
            "key": API_KEY,
        })
    except Exception as e:
        print(f"    Error fetching videos: {e}")
        return []

    video_ids = [item["id"]["videoId"] for item in search_data.get("items", [])
                 if item["id"].get("videoId")]
    if not video_ids:
        return []

    try:
        stats_data = _api_get("https://www.googleapis.com/youtube/v3/videos", {
            "part": "statistics,snippet",
            "id": ",".join(video_ids),
            "key": API_KEY,
        })
    except Exception as e:
        print(f"    Error fetching video stats: {e}")
        return []

    videos = []
    for item in stats_data.get("items", []):
        videos.append({
            "video_id": item["id"],
            "title": item["snippet"]["title"],
            "published_at": item["snippet"]["publishedAt"],
            "views": int(item["statistics"].get("viewCount", 0)),
            "url": f"https://www.youtube.com/watch?v={item['id']}",
        })
    return videos


def detect_outliers(videos):
    """Flag videos that significantly out-perform the channel's own median."""
    if not videos:
        return [], 0
    median = statistics.median(v["views"] for v in videos)
    if median == 0:
        return [], 0

    outliers = []
    for video in videos:
        multiplier = video["views"] / median
        if multiplier >= MODERATE_THRESHOLD:
            level = ("viral" if multiplier >= VIRAL_THRESHOLD
                     else "strong" if multiplier >= STRONG_THRESHOLD
                     else "moderate")
            outliers.append({**video, "multiplier": round(multiplier, 1), "level": level})

    outliers.sort(key=lambda x: x["multiplier"], reverse=True)
    return outliers, int(median)


def _title_phrases(title):
    """Extract significant unigrams + bigrams from a title, stopwords removed."""
    words = re.findall(r"[a-z0-9']+", title.lower())
    words = [w for w in words if w not in STOPWORDS and len(w) > 2]
    phrases = set(words)
    for i in range(len(words) - 1):
        phrases.add(f"{words[i]} {words[i + 1]}")
    return phrases


def detect_trending_topics(all_outliers):
    """Group outliers by phrases recurring across 2+ different channels.

    No pre-defined topic list — works for any niche, since the phrases come
    directly from whatever titles are actually in the data.
    """
    phrase_groups = defaultdict(list)
    for outlier in all_outliers:
        for phrase in _title_phrases(outlier["title"]):
            phrase_groups[phrase].append(outlier)

    results = []
    seen_video_sets = []
    for phrase, outliers in phrase_groups.items():
        channels = set(o["channel_name"] for o in outliers)
        if len(channels) < 2:
            continue
        video_ids = frozenset(o["video_id"] for o in outliers)
        if video_ids in seen_video_sets:
            continue
        seen_video_sets.append(video_ids)
        results.append({
            "topic": phrase,
            "outliers": sorted(outliers, key=lambda x: x["views"], reverse=True),
            "total_views": sum(o["views"] for o in outliers),
            "channel_count": len(channels),
            "channels": sorted(channels),
        })

    results.sort(key=lambda x: x["total_views"], reverse=True)
    return results[:8]


def generate_report(scan_results, trending_topics, scan_date):
    all_outliers = []
    for r in scan_results:
        for o in r["outliers"]:
            o["channel_name"] = r["channel_name"]
            all_outliers.append(o)

    cutoff = (datetime.strptime(scan_date, "%Y-%m-%d") - timedelta(days=RECENCY_DAYS)).date()

    def is_recent(o):
        try:
            d = datetime.strptime(o["published_at"][:10], "%Y-%m-%d").date()
            return d >= cutoff
        except (ValueError, TypeError):
            return False

    recent = [o for o in all_outliers if is_recent(o)]
    evergreen = [o for o in all_outliers if not is_recent(o)]
    viral_count = sum(1 for o in all_outliers if o["level"] == "viral")
    strong_count = sum(1 for o in all_outliers if o["level"] == "strong")

    lines = [
        f"# Outlier Report — {scan_date}",
        "",
        f"**{len(scan_results)} channels** scanned | "
        f"**{len(all_outliers)} outliers** ({viral_count} viral, {strong_count} strong) | "
        f"**{len(recent)} recent** (last {RECENCY_DAYS} days)",
        "",
    ]

    def table(outliers):
        rows = [
            "| Signal | Title | Views | Channel | Date |",
            "|--------|-------|------:|---------|------|",
        ]
        for o in outliers:
            emoji = LEVEL_EMOJI[o["level"]]
            pub = o["published_at"][:10]
            rows.append(
                f"| {emoji} {o['multiplier']}x | [{o['title']}]({o['url']}) | "
                f"{o['views']:,} | {o['channel_name']} | {pub} |"
            )
        return "\n".join(rows)

    if recent:
        lines += [
            "---", "",
            f"## Top Outliers — Last {RECENCY_DAYS} Days", "",
            table(sorted(recent, key=lambda x: x["multiplier"], reverse=True)[:20]), "",
        ]

    if trending_topics:
        lines += [
            "---", "",
            "## Trending Across Channels", "",
            "*Recurring phrases showing up in outlier titles across 2+ tracked channels.*", "",
        ]
        for i, topic in enumerate(trending_topics, 1):
            channels_str = ", ".join(topic["channels"][:4])
            lines += [
                f"### {i}. \"{topic['topic']}\" — {topic['total_views']:,} views ({channels_str})",
                "",
                table(topic["outliers"][:5]),
                "",
            ]

    if evergreen:
        lines += [
            "---", "",
            f"## Evergreen Outliers (older than {RECENCY_DAYS} days)", "",
            table(sorted(evergreen, key=lambda x: x["multiplier"], reverse=True)[:15]), "",
        ]

    return "\n".join(lines)


def load_channels():
    if not os.path.exists(CONFIG_PATH):
        return []
    with open(CONFIG_PATH) as f:
        data = yaml.safe_load(f) or {}
    return data.get("channels", [])


def save_channels(channels):
    with open(CONFIG_PATH, "w") as f:
        yaml.safe_dump({"channels": channels}, f, sort_keys=False)


def main():
    parser = argparse.ArgumentParser(description="YouTube Outlier Report Creator")
    parser.add_argument("--add", help="Add a channel by handle or URL")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: YOUTUBE_API_KEY not found. Add it to a .env file in this project's root.")
        sys.exit(1)

    if args.add:
        channel_id, name = resolve_channel_id(args.add)
        if not channel_id:
            print(f"Could not resolve channel: {args.add}")
            sys.exit(1)
        channels = load_channels()
        if any(c["channel_id"] == channel_id for c in channels):
            print(f"{name} is already tracked.")
            return
        channels.append({"name": name, "channel_id": channel_id})
        save_channels(channels)
        print(f"Added: {name} ({channel_id})")
        return

    channels = load_channels()
    if not channels:
        print("No channels configured yet. Run with --add <handle-or-url> to add one.")
        sys.exit(1)

    scan_date = datetime.now().strftime("%Y-%m-%d")
    scan_results = []
    all_outliers_flat = []

    print(f"Scanning {len(channels)} channel(s)...")
    for i, ch in enumerate(channels, 1):
        print(f"[{i}/{len(channels)}] {ch['name']}...", end=" ")
        videos = fetch_recent_videos(ch["channel_id"])
        outliers, median = detect_outliers(videos)
        print(f"median={median:,}, {len(outliers)} outlier(s)")
        for o in outliers:
            o["channel_name"] = ch["name"]
        scan_results.append({"channel_name": ch["name"], "outliers": outliers})
        all_outliers_flat.extend(outliers)

    trending = detect_trending_topics(all_outliers_flat)
    report = generate_report(scan_results, trending, scan_date)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(OUTPUT_DIR, f"outlier-report-{scan_date}.md")
    with open(report_path, "w") as f:
        f.write(report)

    print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    main()
```
