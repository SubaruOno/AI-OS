---
name: substack
description: >
  Substack search and content extraction. Two-layer: Firecrawl discovers posts via Google,
  Substack undocumented API extracts full article content and metadata.
  Search Substack, find newsletters, read Substack articles, newsletter research,
  Substack publications, thought leadership, newsletter content, expert analysis.
  No API key needed. Zero auth.
  For YouTube/TikTok/Instagram, use Supadata. For web articles, use Firecrawl.
  For X/Twitter, use x-search. For Reddit, use reddit.
---

# Substack Search & Content Extraction

Two-layer architecture: Firecrawl discovers Substack posts via Google search, Substack's undocumented API extracts full article content with metadata. Zero auth required.

## Setup

```python
import importlib.util, os
spec = importlib.util.spec_from_file_location("substack_client",
    os.path.join(os.path.dirname(os.path.abspath(".")), "scripts/substack/client.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
client = mod.SubstackClient()
```

Or validate:
```bash
python scripts/substack/test_client.py all
```

**No env vars needed.** Uses Firecrawl (already configured) for search, Substack's public endpoints for content.

## Method Reference

| Method | What | Layer |
|--------|------|-------|
| `search(query, limit)` | Find Substack posts on a topic via Google | Firecrawl |
| `list_posts(publication, limit, sort)` | List posts from a known publication | Substack API |
| `get_post(publication, slug, as_text)` | Get full post content + metadata | Substack API |
| `discover_publications(query, limit)` | Find publications writing about a topic | Firecrawl |
| `research(query, max_posts, search_limit)` | Full pipeline: search → discover → extract | Both |

## Full Research Pipeline

```python
result = client.research(
    "AI product management specs",
    max_posts=5,       # how many posts to extract in full
    search_limit=10,   # how many search results to consider
)

print(f"Found {result['search_results_count']} results")
print(f"Extracted {result['extracted_count']} full posts")

for p in result["extracted_posts"]:
    print(f"\n[{p['publication']}] {p['title']}")
    print(f"  {p['wordcount']} words, {p['reactions']}")
    print(f"  {p['body'][:300]}...")
```

### Response Shape

```python
{
    "query": "AI product management specs",
    "search_results_count": 10,
    "search_results": [
        {"title": "...", "url": "...", "publication": "addyo", "slug": "how-to-write-specs"}
    ],
    "extracted_count": 5,
    "extracted_posts": [
        {
            "title": "How to write a good spec for AI agents",
            "slug": "how-to-write-specs",
            "date": "2026-02-14T...",
            "body": "full plain text content...",
            "body_length": 43683,
            "wordcount": 7093,
            "reactions": {"❤": 245},
            "comment_count": 18,
            "publication": "addyo",
            "url": "https://addyo.substack.com/p/how-to-write-specs",
        }
    ]
}
```

## Individual Methods

### Search for Posts

```python
# Find Substack posts on any topic
results = client.search("AI coding agents", limit=10)
for r in results:
    print(f"[{r['publication']}] {r['title']}")
    print(f"  {r['url']}")
```

### Discover Publications

```python
# Find which Substack authors write about a topic
pubs = client.discover_publications("artificial intelligence", limit=10)
for p in pubs:
    print(f"{p['publication']} — {p['url']}")
```

### Browse a Publication

```python
# List recent posts from a known publication
posts = client.list_posts("oneusefulthing", limit=10, sort="new")
for p in posts:
    hearts = p.get("reactions", {}).get("❤", 0)
    print(f"[{hearts} ❤] {p['title']} ({p['wordcount']} words)")

# Also works with sort="top"
top_posts = client.list_posts("pragmaticengineer", limit=5, sort="top")
```

### Read Full Post

```python
# Get full article content as plain text
post = client.get_post("oneusefulthing", "the-shape-of-the-thing")
print(post["title"])
print(post["body"])       # clean plain text (HTML stripped)
print(post["wordcount"])
print(post["reactions"])

# Get raw HTML instead
post_html = client.get_post("oneusefulthing", "the-shape-of-the-thing", as_text=False)
print(post_html["body"])  # raw HTML
```

## Known Publications (AI/Tech)

| Publication | Subdomain | Known For |
|------------|-----------|-----------|
| One Useful Thing | `oneusefulthing` | Ethan Mollick, AI strategy and research |
| Pragmatic Engineer | `pragmaticengineer` | Gergely Orosz, software engineering |
| Lenny's Newsletter | `lennysnewsletter` | Product management |
| Stratechery | `stratechery` | Ben Thompson, tech strategy |
| The Gradient | `thegradient` | AI/ML research |
| AI Supremacy | `aisupremacy` | AI industry analysis |

## Rate Limits

| Layer | Limit |
|-------|-------|
| Firecrawl search | Per Firecrawl plan credits |
| Substack API | ~10-20 req/min before 429 |
| Client delay | 2s between Substack API calls |
| Typical research() call | 1 Firecrawl + 3-5 API calls, ~15 seconds |

The client handles rate limiting automatically. On 429, waits 10 seconds and retries.

## Paywalled Content

Free posts return full HTML body. Paywalled (subscriber-only) posts return truncated content. The `audience` field tells you: `"everyone"` = free, `"only_paid"` = paywalled.

---

## Maintenance

> **Self-improvement rule:** If you used this skill and discovered something not documented here, a gotcha, API quirk, new pattern, or better approach, add it below before finishing your task.

### Known Gotchas

1. Substack's publication search endpoint (`/api/v1/publication/search`) returns empty results as of March 2026. Use Firecrawl `site:substack.com` search instead.
2. The archive endpoint (`/api/v1/archive`) returns a JSON array, not an object. Some publications return multiple JSON objects (streaming response), which can cause parse errors with naive JSON parsing.
3. Publications with custom domains (e.g., `platformer.news` instead of `platformer.substack.com`) need the custom domain in the API URL. The client tries subdomain first, then falls back to custom domain patterns.
4. `body_html` is null in archive list responses. You must call `/api/v1/posts/{slug}` to get full content.
5. Reactions are returned as `{"❤": N}` (heart emoji key, not a count field). Parse with `post.get("reactions", {}).get("❤", 0)`.
6. Sitemaps (`/sitemap.xml`) no longer auto-generate for new Substack publications. Don't rely on them for discovery.
7. RSS feeds at `{pub}.substack.com/feed` only contain the last 10-50 posts and may not include full content.

### Improvement Backlog

- Add cookie-based auth for reading paywalled content from subscribed publications
- Add Substack Notes search when/if an endpoint surfaces
- Consider caching publication metadata to avoid repeated profile lookups
