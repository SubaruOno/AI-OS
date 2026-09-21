#!/usr/bin/env python3
"""WBSCの大会サイトから試合データをまとめて取る。

WBSCの大会サイト（wbsc.org と各大陸連盟）は Inertia.js で作られていて、
HTMLの <div data-page="..."> に描画用のJSONがそのまま埋まっている。
画面を解析せずに、このJSONを取り出して保存する。

使い方:
    python3 collect.py --list                     登録済みの大会を表示
    python3 collect.py --event u23-americas-2025  1大会を取る
    python3 collect.py --all                      登録済みを全部取る

出力先は既定で ~/野球/U23ワールドカップ2026/05_収集データ/<大会キー>/。
    games.json        日程と結果の一覧
    raw/<試合ID>.json 試合ごとの生データ
    batting.csv       打者成績（1行＝1試合1選手）
    pitching.csv      投手成績
    plays.csv         打席ごとの記録
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
SLEEP_SECONDS = 1.0
OUT_ROOT = Path.home() / "野球" / "U23ワールドカップ2026" / "05_収集データ"

# 大会キー: (ドメイン, 大会スラッグ, 説明)
EVENTS = {
    "u23-wc-2026": (
        "www.wbsc.org",
        "2026-vi-wbsc-u-23-baseball-world-cup",
        "本大会。11/6〜15 ニカラグア",
    ),
    "u23-wc-2024": (
        "www.wbsc.org",
        "2024-v-u-23-baseball-world-cup",
        "前回大会。中国・紹興。チームの傾向を見る用",
    ),
    "u23-wc-2022": (
        "www.wbsc.org",
        "2022-iv-u-23-baseball-world-cup",
        "2022年大会。台湾。キューバの前回出場",
    ),
    "u23-americas-2025": (
        "www.wbscamericas.org",
        "2025-v-panamericano-sub-23-centro-y-norte-america-"
        "i-u-23-pan-american-central-and-north-america",
        "北中米カリブ予選。キューバ・パナマ・プエルトリコが出場権を獲得",
    ),
    "u23-euro-2025": (
        "www.wbsceurope.org",
        "u23eurobaseball25",
        "U-23欧州選手権。イギリスが優勝、チェコが準優勝で出場権を獲得",
    ),
    "asian-championship-2025": (
        "www.wbscasia.org",
        "2025-asian-baseball-championship",
        "第31回BFAアジア選手権。台北と韓国",
    ),
}


def fetch_page_props(url: str, attempts: int = 4) -> dict:
    """Inertiaの data-page に入っているJSONを取り出す。

    1試合1MB前後あり、回線しだいで読み込みが途中で切れる。
    間隔を空けて数回やり直す。
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = response.read().decode("utf-8", "ignore")
            break
        except (TimeoutError, OSError) as error:
            if attempt == attempts:
                raise
            print(f"    やり直し {attempt}/{attempts - 1}（{error}）")
            time.sleep(3 * attempt)
    marker = 'data-page="'
    start = body.index(marker) + len(marker)
    end = body.index('"', start)
    return json.loads(html.unescape(body[start:end]))["props"]


def event_url(domain: str, slug: str, tail: str = "") -> str:
    return f"https://{domain}/en/events/{slug}/{tail}"


def fetch_games(domain: str, slug: str) -> list[dict]:
    props = fetch_page_props(event_url(domain, slug, "schedule-and-results"))
    return props.get("games", [])


def fetch_game(domain: str, slug: str, game_id: int) -> dict:
    url = event_url(domain, slug, f"schedule-and-results/box-score/{game_id}")
    return fetch_page_props(url)["viewData"]["original"]


def iter_plays(game: dict):
    """打席の記録を、回の表裏の順に並べて返す。"""
    plays = (game.get("gamePlays") or {}).get("all") or {}
    for inning in sorted(plays, key=lambda x: int(x)):
        block = plays[inning] or {}
        for half in ("top", "bottom"):
            for play in block.get(half) or []:
                yield inning, half, play


def iter_box(game: dict):
    """boxScore からチームごとの選手行を返す。

    打順の1〜9が打者、spot が "90" の枠が投手。boxScore 直下の
    "totals" と "pitchers" は集計と勝敗投手の情報なので飛ばす。
    """
    box = game.get("boxScore") or {}
    for team_id, block in box.items():
        if team_id in ("totals", "pitchers") or not isinstance(block, dict):
            continue
        for spot, rows in block.items():
            for row in rows or []:
                yield team_id, spot, row


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        print(f"  {path.name}: 0行のため書き出しません")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {path.name}: {len(rows)}行")


def collect(key: str, out_root: Path) -> None:
    domain, slug, note = EVENTS[key]
    out_dir = out_root / key
    (out_dir / "raw").mkdir(parents=True, exist_ok=True)
    print(f"\n{key} — {note}")

    games = fetch_games(domain, slug)
    (out_dir / "games.json").write_text(
        json.dumps(games, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  試合 {len(games)}件")

    batting: list[dict] = []
    pitching: list[dict] = []
    plays: list[dict] = []

    for index, summary in enumerate(games, 1):
        game_id = summary.get("id")
        if not game_id:
            continue
        cached = out_dir / "raw" / f"{game_id}.json"
        if cached.exists():
            game = json.loads(cached.read_text(encoding="utf-8"))
        else:
            try:
                game = fetch_game(domain, slug, game_id)
            except urllib.error.HTTPError as error:
                print(f"  [{index}/{len(games)}] {game_id} 取得できず（{error.code}）")
                continue
            cached.write_text(
                json.dumps(game, ensure_ascii=False), encoding="utf-8"
            )
            time.sleep(SLEEP_SECONDS)

        info = game.get("gameData") or {}
        context = {
            "event": key,
            "gameid": game_id,
            "date": info.get("gamedate") or summary.get("gamedate"),
            "away": info.get("awaylabel"),
            "home": info.get("homelabel"),
        }

        for team_id, spot, row in iter_box(game):
            entry = {**context, "teamid": team_id, "spot": spot, **row}
            if str(spot) == "90" or row.get("pitch_appear"):
                pitching.append(entry)
            else:
                batting.append(entry)
        for inning, half, play in iter_plays(game):
            plays.append({**context, "inning": inning, "half": half, **play})

        print(f"  [{index}/{len(games)}] {context['away']} @ {context['home']}")

    write_csv(out_dir / "batting.csv", batting)
    write_csv(out_dir / "pitching.csv", pitching)
    write_csv(out_dir / "plays.csv", plays)
    print(f"  出力先 {out_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", action="append", help="大会キー")
    parser.add_argument("--all", action="store_true", help="登録済みを全部取る")
    parser.add_argument("--list", action="store_true", help="大会の一覧を表示")
    parser.add_argument("--out", type=Path, default=OUT_ROOT, help="出力先")
    args = parser.parse_args()

    if args.list:
        for key, (domain, slug, note) in EVENTS.items():
            print(f"{key:26} {note}\n{'':26} https://{domain}/en/events/{slug}/")
        return 0

    keys = list(EVENTS) if args.all else (args.event or [])
    if not keys:
        parser.print_help()
        return 1

    for key in keys:
        if key not in EVENTS:
            print(f"知らない大会キーです: {key}", file=sys.stderr)
            return 1
        collect(key, args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
