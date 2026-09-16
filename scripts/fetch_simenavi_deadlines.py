#!/usr/bin/env python3
"""Fetch and normalize public 2028-graduate deadlines from simenavi.com."""

from __future__ import annotations

import argparse
import csv
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.simenavi.com/shukatsu/deadlines/2028"
DEADLINE_RE = re.compile(
    r"(?:あと\S+\s+)?(?P<kind>.+?)\s+（(?P<audience>[^）]+)）\s+"
    r"申込期限\s+(?P<deadline>\d{4}-\d{2}-\d{2})\s+(?P<detail>.+)"
)


def fetch_page(page: int) -> list[dict[str, str]]:
    response = requests.get(
        BASE_URL,
        params={"page": page},
        headers={"User-Agent": "Mozilla/5.0 (compatible; personal deadline organizer)"},
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    rows: list[dict[str, str]] = []
    for anchor in soup.select('a[href^="/companies/"]'):
        text = " ".join(anchor.stripped_strings)
        if "申込期限" not in text:
            continue
        match = DEADLINE_RE.fullmatch(text)
        if not match:
            continue
        rows.append(
            {
                "date": match.group("deadline"),
                "kind": match.group("kind"),
                "audience": match.group("audience"),
                "company_and_program": match.group("detail"),
                "url": urljoin(BASE_URL, anchor["href"]),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=int, default=44)
    parser.add_argument("--from-date", default=date.today().isoformat())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with ThreadPoolExecutor(max_workers=8) as executor:
        pages = executor.map(fetch_page, range(1, args.pages + 1))

    unique: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for rows in pages:
        for row in rows:
            if row["date"] < args.from_date:
                continue
            key = (row["date"], row["kind"], row["audience"], row["company_and_program"])
            unique[key] = row

    normalized = sorted(
        unique.values(),
        key=lambda row: (row["date"], row["company_and_program"], row["kind"]),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["date", "kind", "audience", "company_and_program", "url"],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(normalized)
    print(f"saved {len(normalized)} unique deadlines to {args.output}")


if __name__ == "__main__":
    main()
