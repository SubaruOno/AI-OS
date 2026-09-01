"""
Podcast Search & Transcript Client — discovery + quality filtering + extraction.

Two-layer architecture:
  Layer 1 (Discovery): Firecrawl Google search + Supadata YouTube search
  Layer 2 (Extraction): Supadata transcript_text() for YouTube episodes

Usage:
    from scripts.podcast_search.client import PodcastSearchClient

    client = PodcastSearchClient()

    # Search for podcast episodes on a topic
    episodes = client.search("autonomous AI coding agents", limit=10)

    # Search YouTube specifically for podcast interviews
    episodes = client.youtube_search("AI coding agents", limit=10)

    # Get transcript from a YouTube episode
    transcript = client.get_transcript("https://youtube.com/watch?v=VIDEO_ID")

    # Full pipeline: discover → rank by quality → extract transcripts
    result = client.research("AI coding agents", max_transcripts=3)
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


def _find_and_load_env():
    current = Path(__file__).resolve().parent
    for _ in range(5):
        candidate = current / ".env"
        if candidate.exists():
            load_dotenv(candidate)
            return
        current = current.parent

_find_and_load_env()

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
_ROOT_DIR = _SCRIPTS_DIR.parent


def _get_supadata():
    """Load SupadataClient with correct import path."""
    sys.path.insert(0, str(_SCRIPTS_DIR))
    from utils.supadata import SupadataClient
    return SupadataClient()


# ─── Quality Scoring ─────────────────────────────────────────

def _score_episode(episode: dict) -> float:
    """
    Score a podcast episode 0-100 for research quality.

    Signals:
    - View count (YouTube): Higher views = more reach, likely higher quality guest
    - Duration: 20-120 min is the sweet spot for interviews (too short = clip, too long = rambling)
    - Source authority: Known podcast networks score higher
    - Freshness: Recent episodes score higher for fast-moving topics
    """
    score = 50.0  # baseline

    # View count signal (YouTube)
    views = episode.get("views", 0)
    if isinstance(views, str):
        views = int(views) if views.isdigit() else 0
    if views > 1_000_000:
        score += 25
    elif views > 500_000:
        score += 20
    elif views > 100_000:
        score += 15
    elif views > 50_000:
        score += 10
    elif views > 10_000:
        score += 5
    elif views > 0:
        score += 2

    # Duration sweet spot (20-120 min = interview territory)
    duration_min = episode.get("duration_min", 0)
    if 20 <= duration_min <= 120:
        score += 10
    elif 10 <= duration_min < 20:
        score += 3
    elif duration_min > 120:
        score += 5  # still good, just long

    # Source type bonus
    source = episode.get("source", "")
    if source == "youtube":
        score += 5  # transcript extractable
    elif source == "apple_podcasts":
        score += 3

    # Channel/show authority (known high-quality sources)
    title_lower = (episode.get("title", "") + " " + episode.get("show", "") + " " + episode.get("channel", "")).lower()
    authority_signals = [
        "lex fridman", "dwarkesh", "y combinator", "a16z", "no priors",
        "all-in", "acquired", "starter story", "my first million",
        "lenny", "pragmatic engineer", "software engineering daily",
        "changelog", "syntax", "shop talk", "js party", "real python",
        "talk python", "corecursive", "scale", "gradient dissent",
        "practical ai", "machine learning street talk", "replit",
        "hormozi", "huberman", "tim ferriss", "joe rogan",
    ]
    for signal in authority_signals:
        if signal in title_lower:
            score += 10
            break

    # Penalize noise
    noise_signals = ["shorts", "tiktok", "#shorts", "60 seconds", "in 1 minute", "clip"]
    for noise in noise_signals:
        if noise in title_lower:
            score -= 20
            break

    return min(max(score, 0), 100)


# ─── Client ──────────────────────────────────────────────────

class PodcastSearchClient:
    """Podcast episode discovery + quality ranking + transcript extraction."""

    def __init__(self):
        self._supadata = None

    @property
    def supadata(self):
        if self._supadata is None:
            self._supadata = _get_supadata()
        return self._supadata

    # ─── Discovery Layer 1: Firecrawl Google Search ───────────

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search Google for podcast episodes on a topic via Firecrawl.
        Finds episodes across Apple Podcasts, Spotify, YouTube, and podcast sites.

        Returns ranked list of episodes with quality scores.
        """
        try:
            result = subprocess.run(
                ["firecrawl", "search", f"{query} podcast episode interview", "--limit", str(limit), "--json"],
                capture_output=True, text=True, timeout=60,
                cwd=str(_ROOT_DIR),
            )
            if result.returncode != 0:
                return []

            data = json.loads(result.stdout)
            items = []
            if isinstance(data, dict):
                web = data.get("data", {}).get("web", data.get("results", []))
                if isinstance(web, list):
                    items = web
            elif isinstance(data, list):
                items = data

            episodes = []
            for item in items[:limit]:
                url = item.get("url", item.get("metadata", {}).get("sourceURL", ""))
                title = item.get("title", item.get("metadata", {}).get("title", ""))
                desc = item.get("description", item.get("metadata", {}).get("description", ""))

                # Classify source
                source = "web"
                if "youtube.com" in url or "youtu.be" in url:
                    source = "youtube"
                elif "podcasts.apple.com" in url:
                    source = "apple_podcasts"
                elif "spotify.com" in url:
                    source = "spotify"
                elif "podcast" in url.lower():
                    source = "podcast_site"

                # Extract YouTube video ID if applicable
                yt_id = ""
                if source == "youtube":
                    match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
                    if match:
                        yt_id = match.group(1)

                ep = {
                    "title": title,
                    "url": url,
                    "description": desc[:300] if desc else "",
                    "source": source,
                    "youtube_id": yt_id,
                    "show": "",
                    "channel": "",
                    "views": 0,
                    "duration_min": 0,
                }
                ep["quality_score"] = _score_episode(ep)
                episodes.append(ep)

            episodes.sort(key=lambda x: x["quality_score"], reverse=True)
            return episodes

        except Exception as e:
            print(f"Firecrawl search failed: {e}")
            return []

    # ─── Discovery Layer 2: YouTube via Supadata ─────────────

    def youtube_search(
        self,
        query: str,
        limit: int = 10,
        upload_date: str = "year",
        duration: str = "long",
    ) -> list[dict]:
        """
        Search YouTube for podcast interviews on a topic.

        Args:
            query: Topic to search
            limit: Max results
            upload_date: hour, today, week, month, year
            duration: short (<4min), medium (4-20min), long (>20min)

        Returns ranked list with quality scores, view counts, and YouTube IDs.
        """
        try:
            results = self.supadata.youtube_search(
                f"{query} podcast interview",
                upload_date=upload_date,
                sort_by="views",
                duration=duration,
                limit=limit,
            )
            items = results.get("results", []) if isinstance(results, dict) else []

            episodes = []
            for item in items:
                vid_id = item.get("id", item.get("videoId", ""))
                channel = item.get("channelTitle", "")
                if isinstance(channel, dict):
                    channel = channel.get("name", "")

                views = item.get("viewCount", item.get("views", 0))
                if isinstance(views, str):
                    views = int(views) if views.isdigit() else 0

                # Parse duration
                duration_val = item.get("duration", "")
                duration_min = 0
                if isinstance(duration_val, str) and ":" in duration_val:
                    parts = duration_val.split(":")
                    if len(parts) == 3:
                        duration_min = int(parts[0]) * 60 + int(parts[1])
                    elif len(parts) == 2:
                        duration_min = int(parts[0])
                elif isinstance(duration_val, (int, float)):
                    duration_min = int(duration_val / 60) if duration_val > 1000 else int(duration_val)

                ep = {
                    "title": item.get("title", ""),
                    "url": f"https://youtube.com/watch?v={vid_id}",
                    "youtube_id": vid_id,
                    "channel": channel,
                    "views": views,
                    "duration_min": duration_min,
                    "published": item.get("publishedAt", item.get("published", "")),
                    "source": "youtube",
                    "show": channel,
                    "description": item.get("description", "")[:300],
                }
                ep["quality_score"] = _score_episode(ep)
                episodes.append(ep)

            episodes.sort(key=lambda x: x["quality_score"], reverse=True)
            return episodes

        except Exception as e:
            print(f"YouTube search failed: {e}")
            return []

    # ─── Transcript Extraction ───────────────────────────────

    def get_transcript(self, url: str) -> str | None:
        """
        Get transcript from a YouTube video URL via Supadata.
        Returns plain text transcript or None.
        """
        try:
            text = self.supadata.transcript_text(url)
            return text
        except Exception as e:
            print(f"Transcript extraction failed for {url}: {e}")
            return None

    # ─── Combined Research Pipeline ──────────────────────────

    def research(
        self,
        query: str,
        max_transcripts: int = 3,
        search_limit: int = 10,
        youtube_limit: int = 10,
        min_quality_score: float = 55,
        upload_date: str = "year",
    ) -> dict:
        """
        Full pipeline: discover episodes → rank by quality → extract transcripts.

        1. Firecrawl finds episodes across all platforms
        2. YouTube search finds high-view podcast interviews
        3. Merge + deduplicate + rank by quality score
        4. Extract transcripts from top YouTube results

        Args:
            query: Research topic
            max_transcripts: How many transcripts to pull (each ~1 Supadata credit)
            search_limit: Firecrawl search results
            youtube_limit: YouTube search results
            min_quality_score: Minimum score to consider for transcripts
            upload_date: YouTube recency filter

        Returns dict with all discovered episodes + extracted transcripts.
        """
        # Step 1: Dual discovery
        firecrawl_results = self.search(query, limit=search_limit)
        youtube_results = self.youtube_search(query, limit=youtube_limit, upload_date=upload_date)

        # Step 2: Merge and deduplicate
        all_episodes = []
        seen_ids = set()
        seen_urls = set()

        for ep in youtube_results + firecrawl_results:
            yt_id = ep.get("youtube_id", "")
            url = ep.get("url", "")

            if yt_id and yt_id in seen_ids:
                continue
            if url and url in seen_urls:
                continue

            if yt_id:
                seen_ids.add(yt_id)
            if url:
                seen_urls.add(url)

            all_episodes.append(ep)

        # Step 3: Sort by quality score
        all_episodes.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

        # Step 4: Extract transcripts from top YouTube episodes
        transcripts_extracted = 0
        for ep in all_episodes:
            if transcripts_extracted >= max_transcripts:
                break
            if ep.get("quality_score", 0) < min_quality_score:
                break
            if ep.get("source") != "youtube" or not ep.get("youtube_id"):
                continue

            transcript = self.get_transcript(ep["url"])
            if transcript:
                ep["transcript"] = transcript
                ep["transcript_length"] = len(transcript)
                transcripts_extracted += 1

        return {
            "query": query,
            "total_discovered": len(all_episodes),
            "transcripts_extracted": transcripts_extracted,
            "episodes": all_episodes,
        }
