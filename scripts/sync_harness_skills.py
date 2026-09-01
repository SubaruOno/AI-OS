#!/usr/bin/env python3
"""Keep Claude and Codex project skills identical without writing outside the kit."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / ".claude" / "skills"
TARGET = ROOT / ".agents" / "skills"
IGNORED_NAMES = {".DS_Store", "__pycache__"}


def included(path: Path) -> bool:
    return not any(part in IGNORED_NAMES for part in path.parts) and path.suffix != ".pyc"


def manifest(folder: Path) -> dict[str, str]:
    """Return stable content hashes for all ordinary files below a folder."""
    if not folder.is_dir():
        return {}
    result: dict[str, str] = {}
    for path in sorted(folder.rglob("*")):
        relative = path.relative_to(folder)
        if not included(relative) or not path.is_file():
            continue
        result[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def differences(source: dict[str, str], target: dict[str, str]) -> list[str]:
    messages: list[str] = []
    for name in sorted(source.keys() - target.keys()):
        messages.append(f"missing from .agents/skills: {name}")
    for name in sorted(target.keys() - source.keys()):
        messages.append(f"extra in .agents/skills: {name}")
    for name in sorted(source.keys() & target.keys()):
        if source[name] != target[name]:
            messages.append(f"different content: {name}")
    return messages


def sync() -> None:
    if not SOURCE.is_dir():
        raise RuntimeError(f"Source skill folder not found: {SOURCE}")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="skills-sync-", dir=TARGET.parent) as temp_name:
        staged = Path(temp_name) / "skills"
        shutil.copytree(
            SOURCE,
            staged,
            symlinks=False,
            ignore=shutil.ignore_patterns(".DS_Store", "__pycache__", "*.pyc"),
        )
        if TARGET.exists():
            shutil.rmtree(TARGET)
        staged.replace(TARGET)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift without changing files",
    )
    args = parser.parse_args()

    before = differences(manifest(SOURCE), manifest(TARGET))
    if args.check:
        if before:
            print("Claude and Codex skills are out of sync:")
            for item in before:
                print(f"- {item}")
            return 1
        print(f"OK: {len(manifest(SOURCE))} skill files match across both harnesses.")
        return 0

    sync()
    after = differences(manifest(SOURCE), manifest(TARGET))
    if after:
        print("Skill sync failed verification:", file=sys.stderr)
        for item in after:
            print(f"- {item}", file=sys.stderr)
        return 1

    print(f"Synced {len(manifest(SOURCE))} files into .agents/skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
