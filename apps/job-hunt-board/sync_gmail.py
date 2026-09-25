#!/usr/bin/env python3
"""Composio 経由で Gmail を読み、就活に関係するメールだけを data/mail.json に残す。

読み取り専用。メールの既読・ラベル・送信は一切変更しない。
「メールプラグイン」の中身はこのファイル1つで、アプリはこの出力を見るだけ。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stages  # noqa: E402

APP_DIR = Path(__file__).resolve().parent
WORKSPACE = APP_DIR.parents[1]
DATA_DIR = APP_DIR / "data"
MAIL_PATH = DATA_DIR / "mail.json"

DEFAULT_QUERY = (
    "newer_than:{days}d (選考 OR 面接 OR 面談 OR 適性検査 OR SPI OR エントリーシート OR "
    "エントリー OR 応募 OR 締切 OR 内定 OR 説明会 OR インターン OR 会社説明会)"
)


def hdr(message: dict, name: str) -> str:
    for header in message.get("payload", {}).get("headers", []):
        if header.get("name", "").lower() == name:
            return header.get("value", "")
    return ""


def fetch(days: int, limit: int, account: str | None):
    query = DEFAULT_QUERY.format(days=days)
    payload = {"query": query, "max_results": limit, "verbose": False}
    cmd = ["composio", "execute", "GMAIL_FETCH_EMAILS", "-d", json.dumps(payload, ensure_ascii=False)]
    if account:
        cmd += ["--account", account]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"composio の実行に失敗しました: {proc.stderr.strip()[:300]}")
    out = proc.stdout
    match = re.search(r"\{[\s\S]*\}", out)
    if not match:
        raise RuntimeError(f"composio の出力を読めませんでした: {out.strip()[:300]}")
    result = json.loads(match.group(0))
    if not result.get("successful"):
        raise RuntimeError(f"Gmail の取得に失敗しました: {result.get('error')}")
    stored = result.get("outputFilePath")
    if stored:
        return json.loads(Path(stored).read_text(encoding="utf-8"))
    return {"data": result.get("data", {})}


def normalize(blob: dict, known_companies):
    messages = (blob.get("data") or {}).get("messages") or []
    kept, dropped = [], 0
    for message in messages:
        sender = hdr(message, "from")
        subject = hdr(message, "subject")
        if not subject:
            dropped += 1
            continue
        if stages.is_noise(sender, subject):
            dropped += 1
            continue
        rank, label = stages.classify(subject)
        company = stages.company_from_mail(sender, subject)
        matched = next(
            (name for name in known_companies if name and (name in company or name in subject)),
            company,
        )
        kept.append({
            "date": (message.get("messageTimestamp") or "")[:10],
            "sender": re.sub(r"\s*<.*?>\s*$", "", sender or "").strip().strip('"'),
            "subject": subject,
            "company": matched,
            "signal_rank": rank,
            "signal": label,
            "url": message.get("display_url", ""),
        })
    kept.sort(key=lambda m: m["date"], reverse=True)
    return kept, dropped


def main():
    ap = argparse.ArgumentParser(description="Gmail から就活シグナルを取り込む")
    ap.add_argument("--days", type=int, default=45, help="さかのぼる日数")
    ap.add_argument("--limit", type=int, default=60, help="取得する最大件数")
    ap.add_argument("--account", default=None, help="Composio のアカウント別名やID")
    ap.add_argument("--dry-run", action="store_true", help="保存せず件数だけ表示")
    args = ap.parse_args()

    sys.path.insert(0, str(APP_DIR))
    import parse

    companies = sorted({item["firm"] for item in parse.load(WORKSPACE)["items"]})

    try:
        blob = fetch(args.days, args.limit, args.account)
    except Exception as exc:
        print(f"取得できませんでした: {exc}")
        return 1

    kept, dropped = normalize(blob, companies)
    print(f"取得 {len(kept) + dropped}件 → 就活シグナル {len(kept)}件（ノイズ {dropped}件を除外）")
    for message in kept[:15]:
        print(f"  {message['date']} [{message['signal'] or '-'}] {message['company']} | {message['subject'][:52]}")
    if args.dry_run:
        return 0

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MAIL_PATH.write_text(
        json.dumps(
            {"fetched_at": datetime.now().isoformat(timespec="seconds"),
             "query": DEFAULT_QUERY.format(days=args.days),
             "messages": kept},
            ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"保存しました: {MAIL_PATH.relative_to(WORKSPACE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
