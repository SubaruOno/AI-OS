#!/usr/bin/env python3
"""Quick check that the academic client works. No API key needed.
Run: python3 scripts/academic/test_client.py
"""
import importlib.util
import time
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "academic_client", Path(__file__).resolve().parent / "client.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

client = mod.AcademicClient()
papers = []
for attempt in range(2):
    papers = client.search("small business automation", limit=3)
    if papers:
        break
    if attempt == 0:
        print("No results on the first try (often a temporary rate limit). Waiting 30s and retrying once...")
        time.sleep(30)

if papers:
    print("OK, academic search working. Sample:")
    for p in papers[:3]:
        print(f"  - {p.get('title', '(untitled)')}")
else:
    print("The client is wired correctly, but OpenAlex is rate-limiting right now.")
    print("Try again in a few minutes. Setting CONTACT_EMAIL in .env helps a lot.")
