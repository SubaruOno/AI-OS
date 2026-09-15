#!/usr/bin/env python3
"""PostToolUse hook: flag unnatural Japanese phrasing right after a Markdown/text write.

Rules live in ng-rules.json next to this file. Exit 2 sends the findings back to the
assistant so it rewrites the sentence; nothing is blocked.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKIP_PARTS = {"packs", ".agents", "skills", "ledger", "node_modules", ".git"}
MAX_FINDINGS = 15


def prose_lines(text: str):
    in_code = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            yield number, re.sub(r"`[^`]*`", "", line)


def lint(path: Path) -> list[str]:
    rules = json.loads((HERE / "ng-rules.json").read_text(encoding="utf-8"))["rules"]
    job_hunt = "job-hunt" in path.parts
    findings = []
    for number, line in prose_lines(path.read_text(encoding="utf-8")):
        if not re.search(r"[ぁ-んァ-ン一-龥]", line):
            continue
        for rule in rules:
            if rule.get("scope") == "job-hunt" and not job_hunt:
                continue
            match = re.search(rule["pattern"], line)
            if match:
                findings.append(f"L{number} 「{match.group(0)}」: {rule['reason']} → {rule['hint']}")
    return findings


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    file_path = payload.get("tool_input", {}).get("file_path", "")
    path = Path(file_path)
    if path.suffix not in {".md", ".txt"} or SKIP_PARTS & set(path.parts) or not path.is_file():
        return 0
    findings = lint(path)
    if not findings:
        return 0
    shown = findings[:MAX_FINDINGS]
    more = f"\n…ほか {len(findings) - MAX_FINDINGS} 件" if len(findings) > MAX_FINDINGS else ""
    print(
        f"ja-lint: {path.name} に不自然になりやすい表現があります。検出語だけ差し替えず、文ごと書き直してください。"
        " 固有名詞や引用で意図的なものはそのままで構いません。\n" + "\n".join(shown) + more,
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
