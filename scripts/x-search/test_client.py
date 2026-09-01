"""
Validation tests for X Search Client — runs all 5 tests sequentially.

Usage:
    python scripts/x-search/test_client.py           # run all tests
    python scripts/x-search/test_client.py grok       # test Grok x_search only
    python scripts/x-search/test_client.py xapi       # test X API v2 only
    python scripts/x-search/test_client.py combined   # test combined workflow only
"""

import sys
import os
import importlib.util

# Load client directly from path (hyphen in dir name prevents normal import)
_client_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "client.py")
_spec = importlib.util.spec_from_file_location("x_search_client", _client_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
XSearchClient = _module.XSearchClient


def test_1_grok_search():
    """Test 1: Grok x_search — semantic search with x_search tool."""
    print("\n" + "=" * 60)
    print("TEST 1: Grok x_search (semantic search)")
    print("=" * 60)

    client = XSearchClient()
    result = client.search(
        "What are people saying about AI automation agencies?",
        days_back=7,
    )

    assert result["answer"], "No answer returned from Grok"
    assert len(result["answer"]) > 50, f"Answer too short ({len(result['answer'])} chars)"

    print(f"  Answer length: {len(result['answer'])} chars")
    print(f"  Citations found: {len(result['citations'])}")
    for url in result["citations"][:5]:
        print(f"    {url}")
    print(f"  Model: {result['model']}")
    print(f"  Tokens used: {result['usage']}")
    print("  PASS")
    return result


def test_2_grok_filtered():
    """Test 2: Grok x_search — filtered by handles and date."""
    print("\n" + "=" * 60)
    print("TEST 2: Grok x_search (filtered search)")
    print("=" * 60)

    client = XSearchClient()
    result = client.search(
        "Latest thoughts on AI and the future",
        days_back=30,
        allowed_handles=["elonmusk", "AnthropicAI"],
    )

    assert result["answer"], "No answer returned"
    print(f"  Answer length: {len(result['answer'])} chars")
    print(f"  Citations: {len(result['citations'])}")
    print(f"  First 200 chars: {result['answer'][:200]}...")
    print("  PASS")
    return result


def test_3_xapi_search_recent():
    """Test 3: X API v2 — recent search with engagement metrics."""
    print("\n" + "=" * 60)
    print("TEST 3: X API v2 (search recent tweets)")
    print("=" * 60)

    client = XSearchClient()
    if not client.x_bearer:
        print("  SKIP — X_BEARER_TOKEN not set in .env")
        return None

    result = client.search_recent(
        "AI automation -is:retweet lang:en",
        max_results=10,
        sort_order="relevancy",
    )

    tweets = result["tweets"]
    assert len(tweets) > 0, "No tweets returned"

    print(f"  Tweets returned: {len(tweets)}")
    for t in tweets[:3]:
        metrics = t.get("public_metrics", {})
        author = t.get("author", {})
        print(f"  [{metrics.get('like_count', 0)} likes, {metrics.get('retweet_count', 0)} RTs] "
              f"@{author.get('username', '?')}: {t['text'][:80]}...")

    print(f"  Pagination: {result['meta']}")
    print("  PASS")
    return result


def test_4_xapi_user_lookup():
    """Test 4: X API v2 — user profile lookup with follower counts."""
    print("\n" + "=" * 60)
    print("TEST 4: X API v2 (user lookup)")
    print("=" * 60)

    client = XSearchClient()
    if not client.x_bearer:
        print("  SKIP — X_BEARER_TOKEN not set in .env")
        return None

    users = client.lookup_users(usernames=["AnthropicAI", "OpenAI"])

    assert len(users) > 0, "No users returned"

    for u in users:
        metrics = u.get("public_metrics", {})
        print(f"  @{u['username']} — {metrics.get('followers_count', 0):,} followers, "
              f"{metrics.get('tweet_count', 0):,} tweets, verified: {u.get('verified', False)}")

    print("  PASS")
    return users


def test_5_combined_workflow():
    """Test 5: Full discover-and-enrich pipeline."""
    print("\n" + "=" * 60)
    print("TEST 5: Combined workflow (Grok discover → X API enrich)")
    print("=" * 60)

    client = XSearchClient()
    result = client.discover_and_enrich(
        "Most discussed AI tools and frameworks this week",
        days_back=7,
        max_enrich=5,
    )

    assert result["answer"], "No Grok answer"
    print(f"  Grok answer: {len(result['answer'])} chars")
    print(f"  Citations found: {len(result['citations'])}")
    print(f"  Tweet IDs extracted: {len(client._extract_tweet_ids(result['citations']))}")
    print(f"  Enriched tweets: {len(result['enriched_tweets'])}")

    for t in result["enriched_tweets"][:3]:
        metrics = t.get("public_metrics", {})
        author = t.get("author", {})
        print(f"    [{metrics.get('like_count', 0)} likes] "
              f"@{author.get('username', '?')}: {t['text'][:80]}...")

    if not result["enriched_tweets"] and not client.x_bearer:
        print("  (No enrichment — X_BEARER_TOKEN not set, Grok layer worked fine)")

    print("  PASS")
    return result


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    print("X Search Client — Validation Tests")
    print(f"Mode: {mode}")

    passed = 0
    skipped = 0
    failed = 0

    tests = {
        "grok": [test_1_grok_search, test_2_grok_filtered],
        "xapi": [test_3_xapi_search_recent, test_4_xapi_user_lookup],
        "combined": [test_5_combined_workflow],
    }

    if mode == "all":
        run_tests = tests["grok"] + tests["xapi"] + tests["combined"]
    elif mode in tests:
        run_tests = tests[mode]
    else:
        print(f"Unknown mode: {mode}. Use: all, grok, xapi, combined")
        sys.exit(1)

    for test_fn in run_tests:
        try:
            result = test_fn()
            if result is None:
                skipped += 1
            else:
                passed += 1
        except Exception as e:
            failed += 1
            print(f"  FAIL — {type(e).__name__}: {e}")

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {skipped} skipped, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
