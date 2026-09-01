"""
X/Twitter Search Client — Two-layer architecture for X content discovery and data enrichment.

Layer 1: Grok x_search (xAI Responses API) — semantic search, synthesized insights, citations
Layer 2: X API v2 — raw tweet data, engagement metrics, user profiles

Usage:
    from scripts.x_search.client import XSearchClient

    client = XSearchClient()

    # Discovery: semantic search via Grok
    result = client.search("AI automation agencies", days_back=7)

    # Data: raw tweet lookup with engagement metrics
    tweets = client.lookup_tweets(["1234567890", "0987654321"])

    # Data: search with raw results
    tweets = client.search_recent("AI agency", max_results=20)

    # Data: user profiles
    users = client.lookup_users(usernames=["elonmusk", "AnthropicAI"])
"""

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load .env — walk up from this file until we find it
def _find_and_load_env():
    current = Path(__file__).resolve().parent
    for _ in range(5):
        candidate = current / ".env"
        if candidate.exists():
            load_dotenv(candidate)
            return
        current = current.parent

_find_and_load_env()


class XSearchClient:
    """Two-layer X/Twitter search: Grok discovery + X API v2 data."""

    def __init__(self):
        self.xai_key = os.getenv("XAI_API_KEY")
        self.x_bearer = os.getenv("X_BEARER_TOKEN")

        if not self.xai_key:
            raise ValueError("XAI_API_KEY not set in .env")

        self.xai_base = "https://api.x.ai/v1"
        self.x_api_base = "https://api.x.com/2"

    # ─── Layer 1: Grok x_search (Discovery) ───────────────────────

    def search(
        self,
        query: str,
        days_back: int | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        allowed_handles: list[str] | None = None,
        excluded_handles: list[str] | None = None,
        enable_images: bool = False,
        enable_video: bool = False,
        model: str = "grok-4",
    ) -> dict:
        """
        Semantic search via Grok x_search. Returns synthesized answer + citations.

        Args:
            query: Natural language search query
            days_back: Shortcut — search last N days (overrides from_date)
            from_date: ISO8601 date string (YYYY-MM-DD)
            to_date: ISO8601 date string (YYYY-MM-DD)
            allowed_handles: Only search these accounts (max 10)
            excluded_handles: Exclude these accounts (max 10)
            enable_images: Analyze images in posts
            enable_video: Analyze videos in posts
            model: Grok model to use

        Returns:
            dict with keys: answer, citations, model, usage
        """
        x_search_config = {}

        # Date handling
        if days_back:
            from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
        if from_date:
            x_search_config["from_date"] = from_date
        if to_date:
            x_search_config["to_date"] = to_date

        # Handle filters
        if allowed_handles:
            x_search_config["allowed_x_handles"] = allowed_handles[:10]
        if excluded_handles:
            x_search_config["excluded_x_handles"] = excluded_handles[:10]

        # Media understanding
        if enable_images:
            x_search_config["enable_image_understanding"] = True
        if enable_video:
            x_search_config["enable_video_understanding"] = True

        # Build tool config — only include non-empty fields
        tool = {"type": "x_search"}
        if x_search_config:
            tool.update(x_search_config)

        payload = {
            "model": model,
            "input": [{"role": "user", "content": query}],
            "tools": [tool],
        }

        resp = requests.post(
            f"{self.xai_base}/responses",
            headers={
                "Authorization": f"Bearer {self.xai_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=90,
        )
        resp.raise_for_status()
        data = resp.json()

        # Extract text from Responses API output format
        answer = ""
        for item in data.get("output", []):
            if item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("type") == "output_text":
                        answer += c.get("text", "")

        return {
            "answer": answer,
            "citations": self._extract_citations_from_text(answer),
            "model": data.get("model", model),
            "usage": data.get("usage", {}),
        }

    def _extract_citations_from_text(self, text: str) -> list[str]:
        """Extract X post URLs from Grok's response text."""
        urls = re.findall(r'https?://(?:x\.com|twitter\.com)/\S+', text)
        # Clean trailing punctuation
        urls = [u.rstrip(".,;)\"'") for u in urls]
        return list(set(urls))

    # ─── Layer 2: X API v2 (Data Enrichment) ──────────────────────

    def _x_api_get(self, path: str, params: dict | None = None) -> dict:
        """Make authenticated GET request to X API v2."""
        if not self.x_bearer:
            raise ValueError(
                "X_BEARER_TOKEN not set in .env. "
                "Get one at https://developer.x.com/en/portal/projects-and-apps"
            )
        resp = requests.get(
            f"{self.x_api_base}{path}",
            headers={"Authorization": f"Bearer {self.x_bearer}"},
            params=params or {},
            timeout=30,
        )
        if resp.status_code == 429:
            reset = resp.headers.get("x-rate-limit-reset", "unknown")
            raise RuntimeError(
                f"X API rate limited. Resets at Unix timestamp {reset}. "
                f"Remaining: {resp.headers.get('x-rate-limit-remaining', '0')}"
            )
        resp.raise_for_status()
        return resp.json()

    def lookup_tweets(
        self,
        tweet_ids: list[str],
        include_metrics: bool = True,
        include_author: bool = True,
    ) -> list[dict]:
        """
        Look up tweets by ID with engagement metrics.

        Args:
            tweet_ids: List of tweet ID strings (max 100 per call)
            include_metrics: Include like_count, retweet_count, etc.
            include_author: Expand author user data

        Returns:
            List of tweet dicts with engagement data
        """
        if not tweet_ids:
            return []

        params = {"ids": ",".join(tweet_ids[:100])}

        tweet_fields = ["created_at", "text", "author_id", "conversation_id", "lang"]
        if include_metrics:
            tweet_fields.append("public_metrics")

        params["tweet.fields"] = ",".join(tweet_fields)

        expansions = []
        if include_author:
            expansions.append("author_id")
            params["user.fields"] = "username,name,verified,public_metrics,profile_image_url"

        if expansions:
            params["expansions"] = ",".join(expansions)

        data = self._x_api_get("/tweets", params)

        tweets = data.get("data", [])

        # Merge author data into tweets if expanded
        if include_author and "includes" in data:
            users_map = {u["id"]: u for u in data["includes"].get("users", [])}
            for tweet in tweets:
                author_id = tweet.get("author_id")
                if author_id and author_id in users_map:
                    tweet["author"] = users_map[author_id]

        return tweets

    def search_recent(
        self,
        query: str,
        max_results: int = 10,
        sort_order: str = "relevancy",
        start_time: str | None = None,
        end_time: str | None = None,
        next_token: str | None = None,
    ) -> dict:
        """
        Search recent tweets via X API v2 with raw engagement data.

        Args:
            query: Search query with operators (max 512 chars on pay-per-use)
            max_results: 10-100 per request
            sort_order: 'recency' or 'relevancy'
            start_time: ISO8601 (e.g. '2026-03-14T00:00:00Z')
            end_time: ISO8601
            next_token: Pagination token from previous response

        Returns:
            dict with keys: tweets (list), meta (pagination info)
        """
        params = {
            "query": query[:512],
            "max_results": min(max_results, 100),
            "sort_order": sort_order,
            "tweet.fields": "created_at,text,author_id,public_metrics,conversation_id,lang",
            "expansions": "author_id",
            "user.fields": "username,name,verified,public_metrics",
        }
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if next_token:
            params["next_token"] = next_token

        data = self._x_api_get("/tweets/search/recent", params)

        tweets = data.get("data", [])

        # Merge author data
        if "includes" in data:
            users_map = {u["id"]: u for u in data["includes"].get("users", [])}
            for tweet in tweets:
                author_id = tweet.get("author_id")
                if author_id and author_id in users_map:
                    tweet["author"] = users_map[author_id]

        return {
            "tweets": tweets,
            "meta": data.get("meta", {}),
        }

    def lookup_users(
        self,
        usernames: list[str] | None = None,
        user_ids: list[str] | None = None,
    ) -> list[dict]:
        """
        Look up X user profiles with follower counts.

        Args:
            usernames: List of usernames (without @, max 100)
            user_ids: List of user ID strings (max 100)

        Returns:
            List of user dicts with public_metrics
        """
        params = {
            "user.fields": "created_at,description,public_metrics,verified,verified_type,profile_image_url,url,location",
        }

        if usernames:
            params["usernames"] = ",".join(usernames[:100])
            path = "/users/by"
        elif user_ids:
            params["ids"] = ",".join(user_ids[:100])
            path = "/users"
        else:
            return []

        data = self._x_api_get(path, params)
        return data.get("data", [])

    # ─── Combined Workflows ───────────────────────────────────────

    def discover_and_enrich(
        self,
        query: str,
        days_back: int = 7,
        max_enrich: int = 10,
        **search_kwargs,
    ) -> dict:
        """
        Full pipeline: Grok discovers relevant posts, X API enriches with engagement data.

        Args:
            query: Research query
            days_back: How far back to search
            max_enrich: Max tweets to enrich via X API (saves credits)
            **search_kwargs: Additional args passed to search()

        Returns:
            dict with: answer (Grok synthesis), citations (URLs), enriched_tweets (with metrics)
        """
        # Step 1: Grok discovers
        discovery = self.search(query, days_back=days_back, **search_kwargs)

        # Step 2: Extract tweet IDs from citation URLs
        tweet_ids = self._extract_tweet_ids(discovery["citations"])

        # Step 3: Enrich with X API (if bearer token available)
        enriched = []
        if tweet_ids and self.x_bearer:
            enriched = self.lookup_tweets(tweet_ids[:max_enrich])

        return {
            "answer": discovery["answer"],
            "citations": discovery["citations"],
            "enriched_tweets": enriched,
            "usage": discovery["usage"],
        }

    def _extract_tweet_ids(self, urls: list[str]) -> list[str]:
        """Extract tweet IDs from X/Twitter URLs."""
        ids = []
        for url in urls:
            match = re.search(r'/status/(\d+)', url)
            if match:
                ids.append(match.group(1))
        return list(set(ids))
