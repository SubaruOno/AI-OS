#!/usr/bin/env python3
"""Verify that the AI OS distribution is portable across both supported harnesses."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "START-HERE.md",
    "INSTALL-GUIDE.md",
    "WHAT-THIS-IS.md",
    "CLAUDE.md",
    "AGENTS.md",
    ".claude/commands/install.md",
    ".claude/skills/install/SKILL.md",
    ".agents/skills/install/SKILL.md",
    "packs/COMPATIBILITY.md",
    "scripts/sync_harness_skills.py",
    "scripts/set_secret.py",
    "scripts/check_api_key.py",
    "scripts/workspace_status.py",
    "scripts/build_distribution.py",
]
CONTROLLED_TEXT = [
    ROOT / "START-HERE.md",
    ROOT / "INSTALL-GUIDE.md",
    ROOT / "WHAT-THIS-IS.md",
    ROOT / "CLAUDE.md",
    ROOT / "AGENTS.md",
    ROOT / "reference" / "getting-keys.md",
    *sorted((ROOT / ".claude" / "commands").glob("*.md")),
]


def local_only(relative: Path) -> bool:
    if not relative.parts:
        return False
    if relative.parts[0] in {".git", ".firecrawl", ".venv", "node_modules", "private", "venv"}:
        return True
    return relative.parts[:2] == ("context", "import")


def file_manifest(folder: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not folder.is_dir():
        return result
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        name = path.relative_to(folder).as_posix()
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def skill_frontmatter_errors(folder: Path) -> list[str]:
    errors: list[str] = []
    allowed = {"name", "description", "license", "allowed-tools", "metadata"}
    for skill_file in sorted(folder.glob("*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8", errors="replace")
        match = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        if not match:
            errors.append(f"invalid skill frontmatter: {skill_file.relative_to(ROOT)}")
            continue
        frontmatter = match.group(1)
        keys = {
            key
            for key in re.findall(r"^([A-Za-z][A-Za-z0-9_-]*):", frontmatter, flags=re.MULTILINE)
        }
        for key in sorted(keys - allowed):
            errors.append(f"unsupported frontmatter field {key}: {skill_file.relative_to(ROOT)}")
        for field in ("name", "description"):
            if not re.search(rf"^{field}:\s*\S", frontmatter, flags=re.MULTILINE):
                errors.append(f"missing {field}: {skill_file.relative_to(ROOT)}")
        name_match = re.search(r"^name:\s*([^\n]+)", frontmatter, flags=re.MULTILINE)
        if name_match and name_match.group(1).strip() != skill_file.parent.name:
            errors.append(f"skill name does not match folder: {skill_file.relative_to(ROOT)}")
    return errors


def main() -> int:
    errors: list[str] = []

    for relative in REQUIRED:
        if not (ROOT / relative).exists():
            errors.append(f"missing required path: {relative}")

    claude_file = ROOT / "CLAUDE.md"
    agents_file = ROOT / "AGENTS.md"
    if claude_file.exists() and agents_file.exists() and claude_file.read_bytes() != agents_file.read_bytes():
        errors.append("CLAUDE.md and AGENTS.md are not byte-for-byte identical")

    claude_skills = file_manifest(ROOT / ".claude" / "skills")
    codex_skills = file_manifest(ROOT / ".agents" / "skills")
    if claude_skills != codex_skills:
        errors.append(".claude/skills and .agents/skills are not identical mirrors")
    errors.extend(skill_frontmatter_errors(ROOT / ".claude" / "skills"))

    for nested_git in ROOT.rglob(".git"):
        relative = nested_git.relative_to(ROOT)
        if nested_git != ROOT / ".git" and not local_only(relative):
            errors.append(f"nested Git metadata: {nested_git.relative_to(ROOT)}")

    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if local_only(relative):
            continue
        if path.is_symlink():
            target = path.readlink()
            if target.is_absolute():
                errors.append(f"absolute symlink: {relative}")
            if not path.exists():
                errors.append(f"broken symlink: {relative}")
        elif path.is_file() and path.stat().st_size > 100 * 1024 * 1024:
            errors.append(f"file exceeds 100 MB: {relative}")

    windows_reserved = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{number}" for number in range(1, 10)),
        *(f"LPT{number}" for number in range(1, 10)),
    }
    casefolded: dict[str, list[str]] = {}
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if local_only(relative):
            continue
        name = relative.as_posix()
        casefolded.setdefault(name.casefold(), []).append(name)
        if len(name) > 200:
            errors.append(f"path is too long for reliable Windows extraction: {name}")
        for part in relative.parts:
            stem = part.split(".", 1)[0].upper()
            if re.search(r'[<>:"|?*]', part) or part.endswith((" ", ".")) or stem in windows_reserved:
                errors.append(f"Windows-incompatible path: {name}")
                break
    for matches in casefolded.values():
        if len(matches) > 1:
            errors.append(f"case-insensitive path collision: {' <> '.join(matches)}")

    obsolete = ("~/.codex/skills", ".codex/skills", "scripts/install_skills.py")
    insecure_secret_phrases = (
        "paste keys straight into the chat",
        "paste the key into the chat",
        "they paste it",
    )
    # Any absolute home path is a trace of a previous user's machine.
    private_markers_re = re.compile(r"/Users/(?!YOUR-NAME)[A-Za-z0-9_.-]+/|C:\\+Users\\+[A-Za-z0-9_.-]+\\+")
    for path in CONTROLLED_TEXT:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in obsolete:
            if marker in text:
                errors.append(f"obsolete Codex path in {path.relative_to(ROOT)}: {marker}")
        for phrase in insecure_secret_phrases:
            if phrase in text.lower():
                errors.append(f"insecure secret instruction in {path.relative_to(ROOT)}")
        if private_markers_re.search(text):
            errors.append(f"private machine path in {path.relative_to(ROOT)}")

    for name in ("START-HERE.md", "INSTALL-GUIDE.md", "WHAT-THIS-IS.md"):
        path = ROOT / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for term in ("Claude", "Codex", "Windows", "macOS"):
            if term not in text:
                errors.append(f"{name} does not mention {term}")
        if not re.search(r"[ぁ-んァ-ン一-龯]", text):
            errors.append(f"{name} has no Japanese instructions")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    if re.search(r"^\*\.zip\s*$", gitignore, flags=re.MULTILINE):
        errors.append(".gitignore excludes every zip, including original pack archives")

    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    for line in env_example.splitlines():
        if re.match(r"^[A-Z][A-Z0-9_]+=.+", line) and line != "TIMEZONE=UTC":
            errors.append(f"non-placeholder value in .env.example: {line.split('=', 1)[0]}")

    install_skill = (ROOT / ".claude" / "skills" / "install" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    for trigger in ("set up", "セットアップ"):
        if trigger not in install_skill:
            errors.append(f"install skill is missing trigger: {trigger}")

    install_playbook = (ROOT / ".claude" / "commands" / "install.md").read_text(
        encoding="utf-8"
    )
    for requirement in ("Windows", "macOS", "scripts/set_secret.py", "language"):
        if requirement not in install_playbook:
            errors.append(f"install playbook is missing requirement: {requirement}")

    if errors:
        print(f"FAILED: {len(errors)} distribution check(s)")
        for error in errors:
            print(f"- {error}")
        return 1

    skill_count = len(list((ROOT / ".claude" / "skills").glob("*/SKILL.md")))
    print("OK: distribution checks passed")
    print(f"- {skill_count} project skills mirrored for Claude and Codex")
    print("- shared constitution, bilingual guides, Git safety, and portability verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
