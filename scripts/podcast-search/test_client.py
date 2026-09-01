#!/usr/bin/env python3
"""Quick check that podcast search works. Needs SUPADATA_API_KEY in .env.
Run: python3 scripts/podcast-search/test_client.py
"""
import importlib.util
import os
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "podcast_client", Path(__file__).resolve().parent / "client.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

if not os.environ.get("SUPADATA_API_KEY"):
    print("SUPADATA_API_KEY not set in .env yet. Add it (see .env.example), then re-run.")
    sys.exit(1)

client = mod.PodcastSearchClient()
episodes = client.search("founder productivity", limit=3)
assert episodes, "no episodes returned"
print("OK, podcast search working. Sample:")
for e in episodes[:3]:
    print(f"  - {e.get('title', '(untitled)')}")
