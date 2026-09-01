#!/usr/bin/env python3
"""Set one .env value through a hidden local prompt, without exposing it in chat."""

from __future__ import annotations

import argparse
import getpass
import os
import re
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


def encode_value(value: str) -> str:
    if "\n" in value or "\r" in value:
        raise ValueError("A secret must be one line.")
    if not value:
        raise ValueError("No value entered.")
    if re.search(r"\s|#|['\"]", value):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def update_env_text(text: str, key: str, value: str) -> str:
    encoded = encode_value(value)
    lines = text.splitlines()
    output: list[str] = []
    replaced = False
    pattern = re.compile(rf"^{re.escape(key)}=")
    for line in lines:
        if pattern.match(line):
            if not replaced:
                output.append(f"{key}={encoded}")
                replaced = True
            continue
        output.append(line)
    if not replaced:
        if output and output[-1] != "":
            output.append("")
        output.append(f"{key}={encoded}")
    return "\n".join(output) + "\n"


def write_private(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        if os.name != "nt":
            os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("key", help="environment variable name, for example FIRECRAWL_API_KEY")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=ROOT / ".env",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()

    if not KEY_PATTERN.fullmatch(args.key):
        parser.error("key must use uppercase letters, numbers, and underscores")

    env_path = args.env_file.resolve()
    if env_path.exists():
        original = env_path.read_text(encoding="utf-8")
    else:
        example = ROOT / ".env.example"
        original = example.read_text(encoding="utf-8") if example.exists() else ""

    try:
        value = getpass.getpass(f"Enter {args.key} (input hidden): ")
        updated = update_env_text(original, args.key, value)
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled. Nothing was saved.")
        return 1
    except ValueError as error:
        print(f"Not saved: {error}")
        return 1

    write_private(env_path, updated)
    print(f"Saved {args.key} to {env_path.name}. The value was not displayed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
