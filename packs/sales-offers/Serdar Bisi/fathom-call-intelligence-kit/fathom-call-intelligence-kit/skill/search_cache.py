#!/usr/bin/env python3
"""
Search the local meetings cache instantly (no API calls).

Usage:
  python3 search_cache.py <search_term> [search_term2] ...

Examples:
  python3 search_cache.py armstrong          # Find all meetings with "armstrong"
  python3 search_cache.py vincent vinnie     # Find meetings matching either term

Searches across: title, participant names, participant emails, domains.
"""
import json, sys, os

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meetings_cache.json")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 search_cache.py <search_term> [term2] ...", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(CACHE_FILE):
        print("No cache found. Run build_cache.py first to build your meetings cache.", file=sys.stderr)
        sys.exit(1)

    terms = [t.lower() for t in sys.argv[1:]]

    with open(CACHE_FILE) as f:
        cache = json.load(f)

    matches = []
    for m in cache["meetings"]:
        searchable = " ".join([
            m.get("title", ""),
            m.get("participant_names", ""),
            m.get("participant_emails", ""),
        ]).lower()

        if any(term in searchable for term in terms):
            matches.append(m)

    print(json.dumps(matches, indent=2))
    print(f"\n{len(matches)} matches found for: {', '.join(terms)}", file=sys.stderr)

if __name__ == "__main__":
    main()
