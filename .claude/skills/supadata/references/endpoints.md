# Supadata — Full Endpoint Reference

> Extracted from this file. All 21 endpoints with params and response schemas.

## Authentication

| Item | Value |
|------|-------|
| Env var | `SUPADATA_API_KEY` |
| Header | `x-api-key: <key>` |
| Base URL | `https://api.supadata.ai/v1` |

## 1. Universal Transcript — `GET /v1/transcript`

| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `url` | string | Yes | — | Video URL (YouTube, TikTok, IG, X, FB) or file URL |
| `lang` | string | No | First available | ISO 639-1 language code |
| `text` | boolean | No | `false` | `true` = plain text; `false` = timestamped chunks |
| `chunkSize` | number | No | — | Max chars per chunk (50-10,000) |
| `mode` | string | No | `auto` | `native`, `auto`, or `generate` |

**Response:** `{content, lang, availableLangs}`. When `text=true`, content is a plain string.
**Async:** Videos >20 min return `{jobId}` — poll with `/transcript/{jobId}`.

## 2. Poll Transcript Job — `GET /v1/transcript/{jobId}`

Returns same as `/transcript` plus `status: queued|active|completed|failed`. Credits: 0.

## 3. YouTube Transcript Translation — `GET /v1/youtube/transcript/translate`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `url` or `videoId` | string | One required | YouTube video |
| `lang` | string | Yes | Target language (ISO 639-1) |
| `text` | boolean | No | Plain text vs chunks |

Credits: 30/min of video. Slow (20+ seconds).

## 4. Batch YouTube Transcripts — `POST /v1/youtube/transcript/batch`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `videoIds` | string[] | One of* | Array of video IDs/URLs |
| `playlistId` | string | One of* | Playlist URL or ID |
| `channelId` | string | One of* | Channel URL, handle, or ID |
| `limit` | number | No | Max videos (1-5,000, default 10) |

*Exactly one required. Returns `{jobId}` — poll with `GET /v1/youtube/batch/{jobId}`. Credits: 1 + 1/video.

## 5. Batch YouTube Video Metadata — `POST /v1/youtube/video/batch`

Same params as batch transcripts. Returns `{jobId}`. Credits: 1 + 1/video.

## 6. Poll Batch Job — `GET /v1/youtube/batch/{jobId}`

Response: `{status, results: [{videoId, transcript, video, errorCode}], stats: {total, succeeded, failed}}`. Credits: 0.

## 7. Social Media Metadata — `GET /v1/metadata`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | Post/video URL (YouTube, TikTok, IG, X, FB) |

Response: `{platform, type, id, url, title, description, author: {username, displayName, verified}, stats: {views, likes, comments, shares}, media: {type, duration, thumbnailUrl}, tags, createdAt}`. Credits: 1.

## 8. Structured Data Extraction — `POST /v1/extract`

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | string | Yes | Video URL |
| `prompt` | string | One of* | What to extract |
| `schema` | object | One of* | JSON Schema for output |

Returns `{jobId}` — poll with `GET /v1/extract/{jobId}`. Credits: FREE (beta).

## 9. YouTube Video Metadata — `GET /v1/youtube/video`

`id` param (URL or ID). Returns: `{id, title, description, duration, channel, tags, thumbnail, uploadDate, viewCount, likeCount}`. Credits: 1.

## 10. YouTube Channel Metadata — `GET /v1/youtube/channel`

`id` param (URL, handle, or ID). Returns: `{id, name, description, subscriberCount, videoCount, viewCount, thumbnail, banner}`. Credits: 1.

## 11. YouTube Channel Video IDs — `GET /v1/youtube/channel/videos`

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | — | Channel URL, handle, or ID |
| `limit` | number | 30 | Max IDs (1-5,000) |
| `type` | string | `all` | `all`, `video`, `short`, `live` |

Returns: `{videoIds, shortIds, liveIds}`. Credits: 1.

## 12. YouTube Playlist Metadata — `GET /v1/youtube/playlist`

`id` param. Returns: `{id, title, description, videoCount, viewCount, lastUpdated, channel}`. Credits: 1.

## 13. YouTube Playlist Video IDs — `GET /v1/youtube/playlist/videos`

`id` + optional `limit` (default 100). Returns same as channel/videos. Credits: 1.

## 14. YouTube Search — `GET /v1/youtube/search`

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | — | Search query |
| `uploadDate` | string | `all` | `all`, `hour`, `today`, `week`, `month`, `year` |
| `type` | string | `all` | `all`, `video`, `channel`, `playlist`, `movie` |
| `duration` | string | `all` | `short` (<4m), `medium` (4-20m), `long` (>20m) |
| `sortBy` | string | `relevance` | `relevance`, `rating`, `date`, `views` |
| `limit` | number | ~20 | Auto-paginate (1-5,000) |

Returns: `{query, results: [{type, id, title, description, thumbnail, duration, viewCount, uploadDate, channel}], totalResults, nextPageToken}`. Credits: 1/page.

## 15. Web Scrape — `GET /v1/web/scrape`

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `url` | string | — | Webpage URL |
| `noLinks` | boolean | `false` | Remove markdown links |
| `lang` | string | `en` | Language preference |

Returns: `{url, content (markdown), name, description, ogUrl, countCharacters, urls}`. Credits: 1.

## 16. Web URL Map — `GET /v1/web/map`

`url` param. Returns: `{urls: [...]}`. Credits: 1.

## 17. Web Crawl — `POST /v1/web/crawl`

`url` + optional `limit` (default 100). Returns `{jobId}`. Credits: 1 + 1/page.

## 18. Poll Crawl Job — `GET /v1/web/crawl/{jobId}`

Optional `skip` for pagination. Returns: `{status, pages: [{url, content, name, description}], next}`. Credits: 0.

## 19. Account Info — `GET /v1/me`

Returns: `{organizationId, plan, maxCredits, usedCredits}`. Credits: 1.

## Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `unauthorized` | 401 | Invalid API key |
| `forbidden` | 402 | Payment required |
| `upgrade-required` | 402 | Feature requires paid plan |
| `invalid-request` | 400 | Invalid params |
| `not-found` | 404 | Resource not found |
| `limit-exceeded` | 429 | Rate/credit limit |
| `transcript-unavailable` | 206 | No transcript (still costs 1 credit) |

## Supported URL Formats

- **YouTube:** `youtube.com/watch?v=ID`, `youtu.be/ID`, `youtube.com/shorts/ID`, bare video ID
- **Channels:** `youtube.com/@handle`, `youtube.com/channel/UCID`, bare channel ID
- **Playlists:** `youtube.com/playlist?list=PLID`, bare playlist ID
- **Not supported:** Live streams (in progress), private/unlisted, YouTube Music
