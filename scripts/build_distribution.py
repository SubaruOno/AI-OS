#!/usr/bin/env python3
"""Build and verify a clean, Windows/macOS-compatible AI OS zip."""

from __future__ import annotations

import argparse
import hashlib
import stat
import zipfile
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_ROOT = "ai-os-kit"
EXCLUDED_PARTS = {
    ".git",
    ".env",
    ".install-state",
    ".seat",
    ".DS_Store",
    ".firecrawl",
    ".venv",
    "__pycache__",
    "credentials",
    "node_modules",
    "private",
    "tokens.json",
    "venv",
}


def should_include(relative: Path) -> bool:
    if any(part in EXCLUDED_PARTS or part.endswith("-oauth-token.json") for part in relative.parts):
        return False
    if relative.suffix == ".pyc":
        return False
    if relative.parts[:2] == ("context", "import") and relative.name != ".gitkeep":
        return False
    if relative.parts and relative.parts[0] == "outputs" and relative.suffix == ".zip":
        return False
    return True


def source_files(source: Path) -> Iterable[Path]:
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"Distribution contains a symlink: {path.relative_to(source)}")
        if path.is_file() and should_include(path.relative_to(source)):
            yield path


def build(source: Path, output: Path) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
        allowZip64=True,
    ) as archive:
        for path in source_files(source):
            relative = path.relative_to(source)
            name = (Path(ARCHIVE_ROOT) / relative).as_posix()
            info = zipfile.ZipInfo(name, date_time=(2026, 8, 5, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = path.stat().st_mode
            permissions = 0o755 if mode & stat.S_IXUSR else 0o644
            info.external_attr = (stat.S_IFREG | permissions) << 16
            archive.writestr(info, path.read_bytes(), compresslevel=6)
            count += 1
    return count


def verify(output: Path) -> int:
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
        bad = archive.testzip()
        if bad:
            raise RuntimeError(f"Corrupt archive entry: {bad}")
        if not names or any(not name.startswith(f"{ARCHIVE_ROOT}/") for name in names):
            raise RuntimeError("Archive does not have one ai-os-kit root folder")
        for name in names:
            relative = Path(name).relative_to(ARCHIVE_ROOT)
            if not should_include(relative):
                raise RuntimeError(f"Excluded path entered archive: {relative}")
            if name.endswith(("/.git", "/.env", "/.install-state", "/.seat")):
                raise RuntimeError(f"Private or local path entered archive: {relative}")
        return len(names)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT.parent / "ai-os-kit.zip",
        help="archive path; defaults to the parent of the source folder",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    try:
        output.relative_to(ROOT)
    except ValueError:
        pass
    else:
        parser.error("output must be outside the source folder")
    count = build(ROOT, output)
    verified = verify(output)
    if count != verified:
        raise RuntimeError(f"Archive count mismatch: wrote {count}, verified {verified}")
    print(f"Built {output} with {verified} files.")
    print(f"SHA-256: {sha256(output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
