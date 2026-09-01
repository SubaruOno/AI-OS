---
name: youtube-analytics-reviewer
description: >-
  Analyzes a YouTube Studio analytics CSV export and generates a plain, honest
  diagnostic report — what's working, what's not, and concrete next actions.
  Use when the user says: "review my analytics", "analyze this CSV", "how's my
  channel doing", "diagnose my channel", or drops a YouTube Studio CSV export.
disable-model-invocation: false
argument-hint: "[path to CSV export]"
---

# YouTube Analytics Reviewer

Turns a YouTube Studio CSV export into a plain-language diagnostic report: what's working, what's not, and what to do next. No API key, no setup — just a CSV.

## First-time flow: getting the CSV

If the user hasn't already given you a CSV (as a path, or by asking you to review their analytics with nothing in hand yet), don't just explain and wait — make it as close to zero-effort as possible:

1. **Check for one first.** Look for any `.csv` file already sitting in the project root. If you find exactly one, just use it — don't make the user repeat themselves. If you find more than one, ask which one (or default to the most recently modified).
2. **Explain how to export it**, concretely:
   > "Go to **YouTube Studio → Analytics → Advanced Mode**, pick the date range you want, click the download icon (top right), and export as CSV."
3. **Tell them exactly where to put it** — the literal folder, not "drop it in here":
   > "Once it downloads, drag it into this folder: `<absolute path to the project root>`"
4. **Open that folder for them right now**, so they're not hunting for it in Finder — run:
   ```bash
   open "<absolute path to the project root>"
   ```
   Then say something like: "I've opened the folder in Finder — just drag the CSV in whenever it's ready, then let me know."
5. **When they say it's there, actually check** — re-scan the project root for a `.csv` file before proceeding. If you still don't see one, say so plainly ("I don't see a CSV in that folder yet — what's the exact filename?") rather than guessing or stalling silently.

Any of the standard YouTube Studio CSV exports work (Content tab, Overview tab, or Reach tab) — the parser below handles the column naming differences across them.

## Running the review

1. Write `parse_analytics.py` (below) to this skill's folder if it doesn't already exist.
2. Run it against the CSV:
   ```bash
   python3 .claude/skills/youtube-analytics-reviewer/parse_analytics.py "<path-to-csv>" --output json
   ```
3. Read the JSON output — it gives you per-video data, channel averages, trends (first-half vs. second-half of the date range), and pre-identified top/bottom performers.
4. Write the actual report yourself, in your own words, following the structure below. Don't just dump the JSON back at the user.

## Report structure

Use this shape, filled in from the real parsed data — never invent a number that isn't in the JSON output:

```markdown
# YouTube Analytics Review — {channel name if known, else "Your Channel"}

**Review Date:** {today}
**Data Range:** {start} to {end}
**Videos Analyzed:** {count}

---

## Channel Health Snapshot

| Metric | Current Avg | Trend | Reference Point | Status |
|--------|------------|-------|------------------|--------|
| Impressions/video | {value} | {↑↓→} | — | {🟢🟡🔴} |
| CTR | {value}% | {↑↓→} | 4%+ is generally healthy | {🟢🟡🔴} |
| AVD (avg view duration) | {value} | {↑↓→} | 40%+ of video length is generally healthy | {🟢🟡🔴} |
| Views/video | {value} | {↑↓→} | — | {🟢🟡🔴} |
| Subs gained/video | {value} | {↑↓→} | — | {🟢🟡🔴} |
| Watch time (hrs)/video | {value} | {↑↓→} | — | {🟢🟡🔴} |

**Overall trajectory:** {one honest line — accelerating / plateauing / declining, and why}

---

## What's Working

### Top Performers
{list the top_performers from the JSON, with the specific reason each one scored high}

### Winning Patterns
{2-3 honest observations about what these videos have in common — topic, format, length, whatever the data actually shows}

---

## What's NOT Working

### Underperformers
{list the underperformers from the JSON, with the specific bottleneck — low impressions = packaging/discovery problem, low CTR = title/thumbnail problem, low AVD = content/pacing problem}

### Failure Patterns
{1-2 honest observations about what these have in common}

---

## Trend Analysis

- **Views trend:** {up/down/flat} — {why, from the trends data}
- **CTR trend:** {up/down/flat} — {why}
- **AVD trend:** {up/down/flat} — {why}
- **Publishing cadence:** {videos_per_week} videos/week over {period_days} days

---

## Top Recommendations

Ranked by expected impact on growth.

### 1. {Highest-impact recommendation}
- **Why:** {evidence from the data}
- **Next step:** {specific, doable action}

### 2. {Second recommendation}
- **Why:** {evidence}
- **Next step:** {specific action}

### 3. {Third recommendation}
- **Why:** {evidence}
- **Next step:** {specific action}
```

## Tone rules

- **Be honest, not harsh, not a cheerleader.** If a video flopped, say so and explain the specific bottleneck (impressions vs. CTR vs. AVD) — don't soften it into vague encouragement.
- **Every recommendation must be traceable to a specific number in the data.** No generic YouTube advice that isn't grounded in what this channel's own CSV actually shows.
- **Reference points, not verdicts.** The CTR/AVD numbers in the snapshot table are general reference points, not a mandatory bar — a channel with real history to compare against (weeks/months of consistent uploads) will get more accurate trend reads than one with only a handful of videos.

---

## Embedded script — write this to `parse_analytics.py` in this skill's folder if it doesn't already exist

```python
#!/usr/bin/env python3
"""
YouTube Analytics CSV Parser
Parses YouTube Studio CSV exports and outputs structured analysis data.

Usage:
    python3 parse_analytics.py <csv_file_path> [--output json|summary]

Supports standard YouTube Studio export formats:
- Content tab CSV (video-level metrics)
- Overview tab CSV (channel-level metrics)
- Reach tab CSV (impressions, CTR)

Handles varying column names across YouTube Studio export versions.
"""

import csv
import json
import sys
from datetime import datetime
from pathlib import Path


COLUMN_ALIASES = {
    "title": ["video title", "title", "content"],
    "publish_date": ["video publish time", "publish date", "published", "date"],
    "views": ["views", "video views"],
    "impressions": ["impressions", "impressions (thumbnail)"],
    "ctr": [
        "impressions click-through rate (%)",
        "click-through rate (%)",
        "ctr",
        "ctr (%)",
    ],
    "avd": ["average view duration", "avg. view duration", "avd"],
    "avg_percent_viewed": [
        "average percentage viewed (%)",
        "avg. percentage viewed (%)",
        "average % viewed",
    ],
    "watch_hours": ["watch time (hours)", "watch time hours", "watch time"],
    "subscribers": ["subscribers", "subscribers gained", "subs gained", "subscriber change"],
    "likes": ["likes", "like count"],
    "comments": ["comments", "comment count"],
    "shares": ["shares", "share count"],
    "revenue": ["estimated revenue (usd)", "revenue", "estimated revenue"],
}


def normalize_header(header):
    return header.strip().lower()


def map_columns(headers):
    mapping = {}
    normalized = [normalize_header(h) for h in headers]
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[field] = normalized.index(alias)
                break
    return mapping


def parse_duration(duration_str):
    if not duration_str or duration_str.strip() == "":
        return 0.0
    duration_str = duration_str.strip()
    try:
        return float(duration_str)
    except ValueError:
        pass
    parts = duration_str.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return 0.0
    except (ValueError, IndexError):
        return 0.0


def format_duration(seconds):
    if seconds <= 0:
        return "0:00"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def parse_percentage(value):
    if not value or value.strip() == "":
        return 0.0
    cleaned = value.strip().replace("%", "").replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_number(value):
    if not value or value.strip() == "":
        return 0.0
    cleaned = value.strip().replace(",", "").replace("$", "")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_date(date_str):
    if not date_str or date_str.strip() == "":
        return None
    date_str = date_str.strip()
    formats = [
        "%b %d, %Y",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%b %d, %Y %I:%M:%S %p",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def parse_csv(file_path):
    path = Path(file_path)
    if not path.exists():
        return {"error": f"File not found: {file_path}"}

    videos = []
    raw_headers = []
    col_map = {}

    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            with open(path, "r", encoding=encoding) as f:
                reader = csv.reader(f)
                raw_headers = next(reader)

                attempts = 0
                while attempts < 5 and not any(
                    normalize_header(h) in ["video title", "title", "content", "views"]
                    for h in raw_headers
                ):
                    raw_headers = next(reader)
                    attempts += 1

                col_map = map_columns(raw_headers)
                if not col_map:
                    continue

                for row in reader:
                    if not row or all(cell.strip() == "" for cell in row):
                        continue
                    video = {}
                    for field, idx in col_map.items():
                        if idx < len(row):
                            raw_value = row[idx]
                            if field == "title":
                                video[field] = raw_value.strip()
                            elif field == "publish_date":
                                parsed = parse_date(raw_value)
                                video[field] = parsed.isoformat() if parsed else raw_value.strip()
                                video["publish_date_obj"] = parsed
                            elif field in ("ctr", "avg_percent_viewed"):
                                video[field] = parse_percentage(raw_value)
                            elif field == "avd":
                                seconds = parse_duration(raw_value)
                                video["avd_seconds"] = seconds
                                video["avd_formatted"] = format_duration(seconds)
                            else:
                                video[field] = parse_number(raw_value)
                    if video.get("title"):
                        videos.append(video)
                break
        except (UnicodeDecodeError, StopIteration):
            continue

    if not videos:
        return {"error": "Could not parse CSV. No video data found.", "headers_found": raw_headers}

    for v in videos:
        v.pop("publish_date_obj", None)

    averages = calculate_averages(videos)
    trends = calculate_trends(videos)
    top_performers = identify_performers(videos, averages, top=True)
    underperformers = identify_performers(videos, averages, top=False)

    return {
        "video_count": len(videos),
        "date_range": get_date_range(videos),
        "columns_found": list(col_map.keys()),
        "averages": averages,
        "trends": trends,
        "top_performers": top_performers,
        "underperformers": underperformers,
        "videos": videos,
    }


def calculate_averages(videos):
    metrics = ["views", "impressions", "ctr", "avd_seconds", "watch_hours", "subscribers", "likes", "comments"]
    averages = {}
    for metric in metrics:
        values = [v.get(metric, 0) for v in videos if v.get(metric, 0) > 0]
        if values:
            averages[metric] = {
                "mean": round(sum(values) / len(values), 2),
                "median": round(sorted(values)[len(values) // 2], 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "count": len(values),
            }
    if "avd_seconds" in averages:
        averages["avd_formatted"] = format_duration(averages["avd_seconds"]["mean"])
    return averages


def calculate_trends(videos):
    dated_videos = []
    for v in videos:
        d = parse_date(v.get("publish_date", ""))
        if d:
            dated_videos.append({**v, "_date": d})

    if not dated_videos:
        return {"error": "No valid dates found for trend analysis"}

    dated_videos.sort(key=lambda x: x["_date"])
    midpoint = len(dated_videos) // 2
    first_half = dated_videos[:midpoint] if midpoint > 0 else dated_videos
    second_half = dated_videos[midpoint:] if midpoint > 0 else []

    if not second_half:
        return {"note": "Not enough data points for trend analysis"}

    trends = {}
    for metric in ["views", "impressions", "ctr", "avd_seconds"]:
        first_avg = sum(v.get(metric, 0) for v in first_half) / len(first_half) if first_half else 0
        second_avg = sum(v.get(metric, 0) for v in second_half) / len(second_half) if second_half else 0
        change_pct = round(((second_avg - first_avg) / first_avg) * 100, 1) if first_avg > 0 else 0
        direction = "up" if change_pct > 5 else "down" if change_pct < -5 else "flat"
        trends[metric] = {
            "first_half_avg": round(first_avg, 2),
            "second_half_avg": round(second_avg, 2),
            "change_percent": change_pct,
            "direction": direction,
        }

    if len(dated_videos) >= 2:
        date_range_days = (dated_videos[-1]["_date"] - dated_videos[0]["_date"]).days
        weeks = max(date_range_days / 7, 1)
        trends["cadence"] = {
            "total_videos": len(dated_videos),
            "period_days": date_range_days,
            "videos_per_week": round(len(dated_videos) / weeks, 1),
        }

    return trends


def identify_performers(videos, averages, top=True, limit=5):
    scored = []
    for v in videos:
        score = 0
        reasons = []
        for metric in ["views", "impressions", "ctr"]:
            if metric in averages and v.get(metric, 0) > 0:
                avg = averages[metric]["mean"]
                actual = v[metric]
                deviation = ((actual - avg) / avg) * 100 if avg > 0 else 0
                if top and deviation > 20:
                    score += deviation
                    reasons.append(f"{metric}: {actual:.0f} ({deviation:+.0f}% vs avg)")
                elif not top and deviation < -20:
                    score += abs(deviation)
                    reasons.append(f"{metric}: {actual:.0f} ({deviation:+.0f}% vs avg)")
        if score > 0:
            scored.append({
                "title": v.get("title", "Unknown"),
                "score": round(score, 1),
                "reasons": reasons,
                "metrics": {
                    k: v.get(k) for k in ["views", "impressions", "ctr", "avd_formatted", "subscribers"]
                    if v.get(k) is not None
                },
            })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


def get_date_range(videos):
    dates = []
    for v in videos:
        d = parse_date(v.get("publish_date", ""))
        if d:
            dates.append(d)
    if not dates:
        return {"start": "unknown", "end": "unknown"}
    dates.sort()
    return {
        "start": dates[0].strftime("%Y-%m-%d"),
        "end": dates[-1].strftime("%Y-%m-%d"),
        "days": (dates[-1] - dates[0]).days,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 parse_analytics.py <csv_file_path> [--output json|summary]")
        sys.exit(1)

    file_path = sys.argv[1]
    output_mode = "json"
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_mode = sys.argv[idx + 1]

    result = parse_csv(file_path)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        if "headers_found" in result:
            print(f"Headers found: {result['headers_found']}", file=sys.stderr)
        sys.exit(1)

    if output_mode == "summary":
        print(f"Videos analyzed: {result['video_count']}")
        print(f"Date range: {result['date_range']['start']} to {result['date_range']['end']}")
        print(f"Columns found: {', '.join(result['columns_found'])}")
    else:
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
```
