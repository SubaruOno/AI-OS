"""
Supadata API client for the Morningside workspace.

Centralizes all Supadata API calls. Import this instead of writing raw HTTP requests.
Full service reference: reference/services/supadata.md

Usage:
    from utils.supadata import SupadataClient

    client = SupadataClient()  # reads SUPADATA_API_KEY from .env
    transcript = client.transcript("https://youtube.com/watch?v=VIDEO_ID", text=True)
    metadata = client.metadata("https://youtube.com/watch?v=VIDEO_ID")
    page = client.web_scrape("https://example.com")
"""

import requests
from utils.config import get_env

BASE_URL = "https://api.supadata.ai/v1"


class SupadataClient:
    """Thin wrapper around the Supadata REST API (21 endpoints)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or get_env("SUPADATA_API_KEY")
        if not self.api_key:
            raise ValueError("SUPADATA_API_KEY not set in .env")
        self._headers = {"x-api-key": self.api_key}

    def _get(self, path: str, params: dict | None = None, timeout: int = 30) -> dict:
        resp = requests.get(f"{BASE_URL}{path}", params=params, headers=self._headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json_body: dict | None = None, timeout: int = 30) -> dict:
        resp = requests.post(f"{BASE_URL}{path}", json=json_body, headers=self._headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    # --- Transcripts ---

    def transcript(
        self,
        url: str,
        *,
        lang: str | None = None,
        text: bool = False,
        chunk_size: int | None = None,
        mode: str | None = None,
    ) -> dict:
        """GET /v1/transcript — Universal transcript extraction.

        Works with YouTube, TikTok, Instagram, X, Facebook, and file URLs.
        Returns dict with 'content' (string if text=True, list of segments otherwise),
        'lang', and 'availableLangs'. May return {'jobId': '...'} for videos >20 min.
        """
        params = {"url": url}
        if lang:
            params["lang"] = lang
        if text:
            params["text"] = "true"
        if chunk_size:
            params["chunkSize"] = chunk_size
        if mode:
            params["mode"] = mode
        return self._get("/transcript", params)

    def transcript_text(self, url: str, *, lang: str | None = None) -> str | None:
        """Convenience: get transcript as plain text string, or None if unavailable.

        This is the most common usage pattern in the workspace.
        """
        try:
            data = self.transcript(url, text=True, lang=lang)
            content = data.get("content", "")
            if isinstance(content, str) and content.strip():
                return content.strip()
            if isinstance(content, list) and content:
                return " ".join(item.get("text", "") for item in content).strip()
        except requests.HTTPError:
            pass
        return None

    def transcript_status(self, job_id: str) -> dict:
        """GET /v1/transcript/{jobId} — Poll async transcript job."""
        return self._get(f"/transcript/{job_id}")

    def youtube_transcript_translate(
        self,
        url_or_id: str,
        target_lang: str,
        *,
        text: bool = False,
    ) -> dict:
        """GET /v1/youtube/transcript/translate — Translate YouTube transcript.

        Credits: 30 per minute of video. Slow (20+ seconds).
        """
        params = {"lang": target_lang}
        if url_or_id.startswith("http"):
            params["url"] = url_or_id
        else:
            params["videoId"] = url_or_id
        if text:
            params["text"] = "true"
        return self._get("/youtube/transcript/translate", params, timeout=120)

    def youtube_transcript_batch(
        self,
        *,
        video_ids: list[str] | None = None,
        playlist_id: str | None = None,
        channel_id: str | None = None,
        limit: int | None = None,
        lang: str | None = None,
        text: bool = False,
    ) -> dict:
        """POST /v1/youtube/transcript/batch — Batch transcript extraction (paid plans).

        Pass exactly one of video_ids, playlist_id, or channel_id.
        Returns {'jobId': '...'} — poll with youtube_batch_status().
        Credits: 1 + 1 per video.
        """
        body = {}
        if video_ids:
            body["videoIds"] = video_ids
        if playlist_id:
            body["playlistId"] = playlist_id
        if channel_id:
            body["channelId"] = channel_id
        if limit:
            body["limit"] = limit
        if lang:
            body["lang"] = lang
        if text:
            body["text"] = True
        return self._post("/youtube/transcript/batch", body)

    # --- YouTube Metadata ---

    def youtube_video(self, url_or_id: str) -> dict:
        """GET /v1/youtube/video — YouTube video metadata. Credits: 1."""
        return self._get("/youtube/video", {"id": url_or_id})

    def youtube_video_batch(
        self,
        *,
        video_ids: list[str] | None = None,
        playlist_id: str | None = None,
        channel_id: str | None = None,
        limit: int | None = None,
    ) -> dict:
        """POST /v1/youtube/video/batch — Batch video metadata (paid plans).

        Returns {'jobId': '...'} — poll with youtube_batch_status().
        Credits: 1 + 1 per video.
        """
        body = {}
        if video_ids:
            body["videoIds"] = video_ids
        if playlist_id:
            body["playlistId"] = playlist_id
        if channel_id:
            body["channelId"] = channel_id
        if limit:
            body["limit"] = limit
        return self._post("/youtube/video/batch", body)

    def youtube_batch_status(self, job_id: str) -> dict:
        """GET /v1/youtube/batch/{jobId} — Poll batch transcript or video job."""
        return self._get(f"/youtube/batch/{job_id}")

    def youtube_channel(self, id_or_handle: str) -> dict:
        """GET /v1/youtube/channel — Channel metadata. Credits: 1."""
        return self._get("/youtube/channel", {"id": id_or_handle})

    def youtube_channel_videos(
        self, id_or_handle: str, *, limit: int | None = None, type: str | None = None
    ) -> dict:
        """GET /v1/youtube/channel/videos — List video IDs from a channel.

        type: 'all', 'video', 'short', 'live'. Credits: 1.
        """
        params = {"id": id_or_handle}
        if limit:
            params["limit"] = limit
        if type:
            params["type"] = type
        return self._get("/youtube/channel/videos", params)

    def youtube_playlist(self, id_or_url: str) -> dict:
        """GET /v1/youtube/playlist — Playlist metadata. Credits: 1."""
        return self._get("/youtube/playlist", {"id": id_or_url})

    def youtube_playlist_videos(self, id_or_url: str, *, limit: int | None = None) -> dict:
        """GET /v1/youtube/playlist/videos — List video IDs from a playlist. Credits: 1."""
        params = {"id": id_or_url}
        if limit:
            params["limit"] = limit
        return self._get("/youtube/playlist/videos", params)

    def youtube_search(
        self,
        query: str,
        *,
        upload_date: str | None = None,
        type: str | None = None,
        duration: str | None = None,
        sort_by: str | None = None,
        limit: int | None = None,
    ) -> dict:
        """GET /v1/youtube/search — Search YouTube programmatically.

        upload_date: 'all', 'hour', 'today', 'week', 'month', 'year'
        type: 'all', 'video', 'channel', 'playlist', 'movie'
        duration: 'all', 'short' (<4m), 'medium' (4-20m), 'long' (>20m)
        sort_by: 'relevance', 'rating', 'date', 'views'
        Credits: 1 per page (~20 results).
        """
        params = {"query": query}
        if upload_date:
            params["uploadDate"] = upload_date
        if type:
            params["type"] = type
        if duration:
            params["duration"] = duration
        if sort_by:
            params["sortBy"] = sort_by
        if limit:
            params["limit"] = limit
        return self._get("/youtube/search", params, timeout=60)

    # --- Social Media ---

    def metadata(self, url: str) -> dict:
        """GET /v1/metadata — Social media post metadata.

        Works with YouTube, TikTok, Instagram, Twitter/X, Facebook.
        Returns platform, type, title, description, author, stats, media, tags.
        Credits: 1.
        """
        return self._get("/metadata", {"url": url})

    # --- Structured Extraction ---

    def extract(self, url: str, *, prompt: str | None = None, schema: dict | None = None) -> dict:
        """POST /v1/extract — AI-powered structured data extraction from video.

        Pass prompt, schema, or both. Returns {'jobId': '...'} — poll with extract_status().
        Credits: FREE during beta.
        """
        body = {"url": url}
        if prompt:
            body["prompt"] = prompt
        if schema:
            body["schema"] = schema
        return self._post("/extract", body)

    def extract_status(self, job_id: str) -> dict:
        """GET /v1/extract/{jobId} — Poll structured extraction job."""
        return self._get(f"/extract/{job_id}")

    # --- Web ---

    def web_scrape(self, url: str, *, no_links: bool = False, lang: str | None = None) -> dict:
        """GET /v1/web/scrape — Scrape webpage to clean Markdown.

        Returns url, content (markdown), name, description, ogUrl, countCharacters, urls.
        Credits: 1.
        """
        params = {"url": url}
        if no_links:
            params["noLinks"] = "true"
        if lang:
            params["lang"] = lang
        return self._get("/web/scrape", params, timeout=60)

    def web_map(self, url: str) -> dict:
        """GET /v1/web/map — Discover all URLs linked from a page.

        Returns {'urls': [...]}.  Credits: 1.
        """
        return self._get("/web/map", {"url": url})

    def web_crawl(self, url: str, *, limit: int | None = None) -> dict:
        """POST /v1/web/crawl — Async full-site crawl (paid plans).

        Returns {'jobId': '...'} — poll with web_crawl_status().
        Credits: 1 + 1 per page crawled.
        """
        body = {"url": url}
        if limit:
            body["limit"] = limit
        return self._post("/web/crawl", body)

    def web_crawl_status(self, job_id: str, *, skip: int | None = None) -> dict:
        """GET /v1/web/crawl/{jobId} — Poll crawl job status."""
        params = {}
        if skip:
            params["skip"] = skip
        return self._get(f"/web/crawl/{job_id}", params or None)

    # --- Account ---

    def me(self) -> dict:
        """GET /v1/me — Account info (plan, credits used/max). Credits: 1."""
        return self._get("/me")
