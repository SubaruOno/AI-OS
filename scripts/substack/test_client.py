#!/usr/bin/env python3
"""Quick check that the substack client works. No API key needed
(this test uses the direct publication API; topic search also needs Firecrawl).
Run: python3 scripts/substack/test_client.py
"""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "substack_client", Path(__file__).resolve().parent / "client.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

client = mod.SubstackClient()
posts = client.list_posts("www.lennysnewsletter.com", limit=2)
assert posts, "no posts returned"
print("OK, substack client working. Sample:")
for p in posts[:2]:
    print(f"  - {p.get('title', '(untitled)')}")
