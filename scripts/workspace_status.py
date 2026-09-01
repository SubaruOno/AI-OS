#!/usr/bin/env python3
"""Classify uncommitted Git paths by age on Windows and macOS."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Optional


def git_root(start: Path) -> Optional[Path]:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        text=True,
        capture_output=True,
        check=False,
    )
    return Path(result.stdout.strip()) if result.returncode == 0 else None


def changed_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    fields = result.stdout.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(fields):
        field = fields[index]
        if not field:
            index += 1
            continue
        status = field[:2].decode("ascii", errors="replace")
        path = field[3:].decode("utf-8", errors="surrogateescape")
        paths.append(path)
        if "R" in status or "C" in status:
            index += 1
        index += 1
    return paths


def classify(root: Path, paths: list[str], threshold_minutes: float) -> dict[str, list[str]]:
    cutoff = time.time() - threshold_minutes * 60
    groups: dict[str, list[str]] = {"recent": [], "stale": [], "unknown": []}
    for name in paths:
        path = root / name
        try:
            modified = path.stat().st_mtime
        except OSError:
            groups["unknown"].append(name)
            continue
        groups["stale" if modified < cutoff else "recent"].append(name)
    return groups


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold-minutes", type=float, default=60)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    root = git_root(args.root.resolve())
    if root is None:
        data = {"git": False, "recent": [], "stale": [], "unknown": []}
    else:
        data = {"git": True, **classify(root, changed_paths(root), args.threshold_minutes)}

    if args.as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif not data["git"]:
        print("Git is not set up in this folder yet.")
    elif not any(data[name] for name in ("recent", "stale", "unknown")):
        print("No uncommitted paths.")
    else:
        for group in ("stale", "recent", "unknown"):
            for name in data[group]:
                print(f"{group}\t{name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
