"""
Substack Search & Content Client — Two-layer architecture.

Layer 1: Firecrawl (discovery) — search Google for Substack content via site:substack.com
Layer 2: Substack undocumented API (extraction) — pull full post content, archives, metadata

Usage:
    from scripts.substack.client import SubstackClient

    client = SubstackClient()

    # Search for Substack posts on a topic
    results = client.search("AI coding agents")

    # List recent posts from a known publication
    posts = client.list_posts("oneusefulthing", limit=10)

    # Get full post content
    post = client.get_post("oneusefulthing", "the-shape-of-the-thing")

    # Full research pipeline: search → discover publications → extract top posts
    research = client.research("AI product management", max_posts=10)
"""

import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load .env
def _find_and_load_env():
    current = Path(__file__).resolve().parent
    for _ in range(5):
        candidate = current / ".env"
        if candidate.exists():
            load_dotenv(candidate)
            return
        current = current.parent

_find_and_load_env()

# Rate limiter for Substack API
_last_substack_request = 0.0


def _rate_limit(min_delay: float = 2.0):
    """Enforce minimum delay between Substack API requests."""
    global _last_substack_request
    elapsed = time.time() - _last_substack_request
    if elapsed < min_delay:
        time.sleep(min_delay - elapsed)
    _last_substack_request = time.time()


def _strip_html(html: str) -> str:
    """Convert HTML to clean plain text."""
    if not html:
        return ""
    # Remove tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'</p>', '\n\n', text)
    text = re.sub(r'</h[1-6]>', '\n\n', text)
    text = re.sub(r'</li>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class SubstackClient:
    """Two-layer Substack search: Firecrawl discovery + Substack API extraction."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
        })

    # ─── Layer 1: Firecrawl Discovery ─────────────────────────────

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search for Substack posts on a topic via Firecrawl + Google.

        Args:
            query: Search topic
            limit: Max results (default 10)

        Returns:
            List of dicts with: title, url, description, publication, slug
        """
        try:
            result = subprocess.run(
                ["firecrawl", "search", f"{query} site:substack.com", "--limit", str(limit), "--json"],
                capture_output=True, text=True, timeout=60,
                cwd=str(Path(__file__).resolve().parent.parent.parent),
            )

            if result.returncode != 0:
                return []

            data = json.loads(result.stdout)

            # Handle different Firecrawl output formats
            items = []
            if isinstance(data, dict):
                web = data.get("data", {}).get("web", data.get("results", []))
                if isinstance(web, list):
                    items = web
            elif isinstance(data, list):
                items = data

            results = []
            for item in items[:limit]:
                url = item.get("url", item.get("metadata", {}).get("sourceURL", ""))
                title = item.get("title", item.get("metadata", {}).get("title", ""))
                desc = item.get("description", item.get("metadata", {}).get("description", ""))

                # Extract publication name and slug from URL
                pub, slug = self._parse_substack_url(url)

                results.append({
                    "title": title,
                    "url": url,
                    "description": desc,
                    "publication": pub,
                    "slug": slug,
                })

            return results

        except Exception as e:
            print(f"Firecrawl search failed: {e}")
            return []

    def _parse_substack_url(self, url: str) -> tuple[str, str]:
        """Extract publication name and post slug from a Substack URL."""
        pub = ""
        slug = ""

        # Pattern: {pub}.substack.com/p/{slug}
        match = re.search(r'(?:https?://)?([^./]+)\.substack\.com/p/([^/?#]+)', url)
        if match:
            return match.group(1), match.group(2)

        # Pattern: open.substack.com/pub/{pub}/p/{slug}
        match = re.search(r'open\.substack\.com/pub/([^/]+)/p/([^/?#]+)', url)
        if match:
            return match.group(1), match.group(2)

        # Custom domain: try to extract slug from /p/ path
        match = re.search(r'/p/([^/?#]+)', url)
        if match:
            slug = match.group(1)
            # Try to get domain as publication hint
            domain_match = re.search(r'https?://(?:www\.)?([^./]+)', url)
            if domain_match:
                pub = domain_match.group(1)

        return pub, slug

    # ─── Layer 2: Substack API (Extraction) ───────────────────────

    def _api_get(self, base_url: str, path: str, params: dict = None) -> dict | list | None:
        """Make rate-limited GET to Substack's undocumented API."""
        _rate_limit()
        url = f"https://{base_url}/api/v1{path}"
        try:
            resp = self.session.get(url, params=params or {}, timeout=15)
            if resp.status_code == 429:
                time.sleep(10)
                resp = self.session.get(url, params=params or {}, timeout=15)
            if resp.status_code != 200:
                return None
            return resp.json()
        except Exception:
            return None

    def list_posts(
        self,
        publication: str,
        limit: int = 12,
        offset: int = 0,
        sort: str = "new",
    ) -> list[dict]:
        """
        List posts from a Substack publication.

        Args:
            publication: Publication subdomain (e.g., 'oneusefulthing')
            limit: Posts per page (max ~50)
            offset: Pagination offset
            sort: 'new' or 'top'

        Returns:
            List of post dicts with title, slug, date, wordcount, reactions
        """
        # Try subdomain first, then custom domain
        for base in [f"{publication}.substack.com", f"www.{publication}.com", publication]:
            data = self._api_get(base, "/archive", {"sort": sort, "limit": limit, "offset": offset})
            if data and isinstance(data, list):
                return [{
                    "title": p.get("title", ""),
                    "slug": p.get("slug", ""),
                    "date": p.get("post_date", ""),
                    "wordcount": p.get("wordcount", 0),
                    "reactions": p.get("reactions", {}),
                    "subtitle": p.get("subtitle", ""),
                    "audience": p.get("audience", ""),
                    "comment_count": p.get("comment_count", 0),
                    "publication": publication,
                    "url": f"https://{base}/p/{p.get('slug', '')}",
                } for p in data]

        return []

    def get_post(self, publication: str, slug: str, as_text: bool = True) -> dict | None:
        """
        Get full post content from a Substack publication.

        Args:
            publication: Publication subdomain
            slug: Post slug (from URL or list_posts)
            as_text: Convert HTML body to plain text (default True)

        Returns:
            Dict with title, date, body, wordcount, reactions, comments, etc.
        """
        for base in [f"{publication}.substack.com", f"www.{publication}.com", publication]:
            data = self._api_get(base, f"/posts/{slug}")
            if data and isinstance(data, dict) and data.get("title"):
                body_html = data.get("body_html", "") or ""
                body = _strip_html(body_html) if as_text else body_html

                return {
                    "title": data.get("title", ""),
                    "slug": slug,
                    "date": data.get("post_date", ""),
                    "body": body,
                    "body_length": len(body),
                    "wordcount": data.get("wordcount", 0),
                    "reactions": data.get("reactions", {}),
                    "comment_count": data.get("comment_count", 0),
                    "subtitle": data.get("subtitle", ""),
                    "audience": data.get("audience", ""),
                    "publication": publication,
                    "url": f"https://{base}/p/{slug}",
                    "canonical_url": data.get("canonical_url", ""),
                }

        return None

    # ─── Combined Workflows ───────────────────────────────────────

    def research(
        self,
        query: str,
        max_posts: int = 5,
        search_limit: int = 10,
    ) -> dict:
        """
        Full research pipeline: Firecrawl discovers → Substack API extracts content.

        Args:
            query: Research topic
            max_posts: Max posts to extract full content for
            search_limit: How many search results to consider

        Returns:
            dict with: query, search_results, extracted_posts
        """
        # Step 1: Discover via Firecrawl
        search_results = self.search(query, limit=search_limit)

        # Step 2: Extract full content from top results
        extracted = []
        for result in search_results[:max_posts]:
            pub = result.get("publication", "")
            slug = result.get("slug", "")

            if not pub or not slug:
                continue

            post = self.get_post(pub, slug)
            if post and post.get("body"):
                extracted.append(post)

        return {
            "query": query,
            "search_results_count": len(search_results),
            "search_results": search_results,
            "extracted_count": len(extracted),
            "extracted_posts": extracted,
        }

    def discover_publications(self, query: str, limit: int = 10) -> list[dict]:
        """
        Find Substack publications on a topic via Google search.

        Returns unique publications found in search results.
        """
        results = self.search(query, limit=limit)
        pubs = {}
        for r in results:
            pub = r.get("publication", "")
            if pub and pub not in pubs and pub != "open":
                pubs[pub] = {
                    "publication": pub,
                    "url": f"https://{pub}.substack.com",
                    "found_via": r.get("title", ""),
                }
        return list(pubs.values())
