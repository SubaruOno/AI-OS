#!/usr/bin/env python3
"""Test a supported API key from .env without printing the key or response body."""

from __future__ import annotations

import argparse
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Tuple


ROOT = Path(__file__).resolve().parent.parent


def load_env(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def request_for(provider: str, values: Dict[str, str]) -> Tuple[str, urllib.request.Request]:
    settings = {
        "firecrawl": ("FIRECRAWL_API_KEY", "https://api.firecrawl.dev/v2/team/credit-usage", "bearer"),
        "supadata": ("SUPADATA_API_KEY", "https://api.supadata.ai/v1/youtube/video?id=dQw4w9WgXcQ", "x-api-key"),
        "anthropic": ("ANTHROPIC_API_KEY", "https://api.anthropic.com/v1/models", "anthropic"),
        "openai": ("OPENAI_API_KEY", "https://api.openai.com/v1/models", "bearer"),
        "gemini": ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/models", "gemini"),
        "apify": ("APIFY_API_TOKEN", "https://api.apify.com/v2/users/me", "bearer"),
        "xai": ("XAI_API_KEY", "https://api.x.ai/v1/models", "bearer"),
    }
    key_name, url, auth_type = settings[provider]
    secret = values.get(key_name, "")
    if not secret:
        raise ValueError(f"{key_name} is not set in .env")

    headers = {"Accept": "application/json", "User-Agent": "ai-os-kit-key-check/1"}
    if auth_type == "bearer":
        headers["Authorization"] = f"Bearer {secret}"
    elif auth_type == "x-api-key":
        headers["x-api-key"] = secret
    elif auth_type == "anthropic":
        headers["x-api-key"] = secret
        headers["anthropic-version"] = "2023-06-01"
    elif auth_type == "gemini":
        headers["x-goog-api-key"] = secret
    return key_name, urllib.request.Request(url, headers=headers)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "provider",
        choices=("firecrawl", "supadata", "anthropic", "openai", "gemini", "apify", "xai"),
    )
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env", help=argparse.SUPPRESS)
    args = parser.parse_args()

    try:
        key_name, request = request_for(args.provider, load_env(args.env_file))
        with urllib.request.urlopen(request, timeout=20) as response:
            status = response.status
            response.read(1)
    except ValueError as error:
        print(f"Not tested: {error}")
        return 1
    except urllib.error.HTTPError as error:
        print(f"Failed: {args.provider} returned HTTP {error.code}. Check or replace the key.")
        return 1
    except (urllib.error.URLError, TimeoutError) as error:
        reason = error.reason if hasattr(error, "reason") else error
        print(f"Could not reach {args.provider}: {reason}")
        return 1

    if 200 <= status < 300:
        print(f"OK: {key_name} authenticated successfully. The value was not displayed.")
        return 0
    print(f"Failed: {args.provider} returned HTTP {status}.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
