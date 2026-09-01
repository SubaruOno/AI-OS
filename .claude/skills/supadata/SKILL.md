---
name: supadata
description: >
  Fetch video transcripts and transcriptions from external URLs — YouTube transcripts, TikTok transcripts,
  Instagram, X, Facebook. Pull a transcript, get a transcription, extract captions from any video URL.
  Also: YouTube search (find videos, keyword research, competitor discovery), web scraping (scrape a page
  to markdown, crawl a website), social media metadata (views, likes, engagement stats), channel and
  playlist data. For transcripts already in the database, use data-query instead.
---

# Supadata API

Content extraction API for YouTube, social media, and web pages. 21 endpoints, credit-based pricing.

## Setup

```python
from scripts.utils.supadata import SupadataClient
client = SupadataClient()  # reads SUPADATA_API_KEY from .env
```

## Method Reference

| Method                                                                    | Description                                        | Credits                       |
| ------------------------------------------------------------------------- | -------------------------------------------------- | ----------------------------- |
| `transcript(url, text=False, lang=None, mode=None)`                       | Universal transcript (YT, TikTok, IG, X, FB)       | 1 (native), 2/min (generated) |
| `transcript_text(url, lang=None)`                                         | Convenience: plain text string or None             | 1                             |
| `transcript_status(job_id)`                                               | Poll async transcript job (>20 min videos)         | 0                             |
| `youtube_transcript_translate(url_or_id, target_lang)`                    | Translate YT transcript                            | 30/min                        |
| `youtube_transcript_batch(video_ids=, playlist_id=, channel_id=)`         | Batch transcripts (paid)                           | 1 + 1/video                   |
| `youtube_video(url_or_id)`                                                | Single video metadata                              | 1                             |
| `youtube_video_batch(video_ids=, playlist_id=, channel_id=)`              | Batch video metadata (paid)                        | 1 + 1/video                   |
| `youtube_batch_status(job_id)`                                            | Poll batch job                                     | 0                             |
| `youtube_channel(id_or_handle)`                                           | Channel metadata (subs, videos, views)             | 1                             |
| `youtube_channel_videos(id_or_handle, limit=, type=)`                     | List video IDs from channel                        | 1                             |
| `youtube_playlist(id_or_url)`                                             | Playlist metadata                                  | 1                             |
| `youtube_playlist_videos(id_or_url, limit=)`                              | List video IDs from playlist                       | 1                             |
| `youtube_search(query, upload_date=, type=, duration=, sort_by=, limit=)` | Search YouTube                                     | 1/page (~20 results)          |
| `metadata(url)`                                                           | Social media post metadata (YT, TikTok, IG, X, FB) | 1                             |
| `extract(url, prompt=, schema=)`                                          | AI structured data extraction from video           | FREE (beta)                   |
| `extract_status(job_id)`                                                  | Poll extraction job                                | 0                             |
| `web_scrape(url, no_links=False, lang=None)`                              | Scrape webpage to clean Markdown                   | 1                             |
| `web_map(url)`                                                            | Discover all URLs linked from a page               | 1                             |
| `web_crawl(url, limit=)`                                                  | Async full-site crawl (paid)                       | 1 + 1/page                    |
| `web_crawl_status(job_id, skip=)`                                         | Poll crawl job                                     | 0                             |
| `me()`                                                                    | Account info (plan, credits)                       | 1                             |

## Common Patterns

### Get a transcript as plain text

```python
text = client.transcript_text("https://youtube.com/watch?v=VIDEO_ID")
```

### Search YouTube

```python
results = client.youtube_search("AI agency", upload_date="month", sort_by="views", duration="long")
for r in results["results"]:
    print(f"{r['title']} — {r['viewCount']} views")
```

### Scrape a webpage to markdown

```python
page = client.web_scrape("https://example.com")
print(page["content"])  # clean markdown
```

## Credits & Pricing

Current plan credits visible via `client.me()`. Credits don't roll over. 1 credit = most single operations.

## Async Jobs

Videos >20 min and batch/crawl operations return `{"jobId": "..."}`. Poll with the corresponding `_status()` method until `status == "completed"`.

> **Full endpoint documentation:** `references/endpoints.md`

---

## Maintenance

> **Self-improvement rule:** If you used this skill and discovered something not documented here — a gotcha, API quirk, new pattern, or better approach — add it below before finishing your task. Keep entries concise (one line each). If this section grows beyond 10 items, refactor learnings into the main body above.

### Known Gotchas

(none yet)
