#!/usr/bin/env python3
"""PreToolUse hook: block irreversible Bash commands before they run.

Plain pushes to main stay allowed because the Stop hook auto-commits and pushes.
"""

from __future__ import annotations

import json
import re
import sys

RULES = [
    (r"\bgit\s+push\b[^;&|]*(\s--force(-with-lease)?\b|\s-[a-zA-Z]*f\b|\s\+\S)",
     "force push は履歴を上書きするため禁止です。"),
    (r"\bgit\s+reset\b[^;&|]*--hard\b", "git reset --hard は未 commit の変更を消すため禁止です。"),
    (r"\bgit\s+clean\b[^;&|]*\s-[a-zA-Z]*f", "git clean -f は未追跡ファイルを消すため禁止です。"),
    (r"\bgit\s+checkout\s+(--\s+)?\.(\s|$)", "git checkout . は変更をまとめて破棄するため禁止です。"),
    (r"\bgit\s+restore\b[^;&|]*\s\.(\s|$)", "git restore . は変更をまとめて破棄するため禁止です。"),
    (r"\bgit\s+branch\b[^;&|]*\s-D\b", "git branch -D は未マージのブランチを消すため禁止です。"),
]

RM_RF = re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*|-r\s+-f|-f\s+-r)\s+([^;&|]+)")
DANGEROUS_TARGET = re.compile(r"^(/|~/?|\$HOME/?|\.|\./|\*|\.git/?|.*/\.git/?|/Users/[^/]+/?|/Users/[^/]+/AI-OS/?)$")


def check(command: str) -> str | None:
    for pattern, reason in RULES:
        if re.search(pattern, command):
            return reason
    for match in RM_RF.finditer(command):
        for target in match.group(2).split():
            if DANGEROUS_TARGET.match(target.strip("'\"")):
                return f"rm -rf {target} は取り返しがつかないため禁止です。"
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    reason = check(payload.get("tool_input", {}).get("command", ""))
    if reason:
        print(f"{reason} 必要ならすばるさん本人がターミナルで実行してください。", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
