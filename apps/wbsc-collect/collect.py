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
    games.json        日程と結果の一覧（毎回取り直す。CSV を書き終えてから最後に書く）
    raw/<試合ID>.json 試合ごとの生データ（終わった試合だけ残す）
    batting.csv       打者成績（1行＝1試合1選手）
    pitching.csv      投手成績
    plays.csv         1球ごとの記録。batter_bats と pitcher_throws に打者と投手の左右

raw を使い回すのは、終わった試合（gamestatustext が F で始まる）で boxScore が
空でないものだけ。試合前・試合中のものは毎回取り直し、raw には残さない。
日程の上でまだ始まっていない試合は、中身が空なので取りに行かない。

途中で止まったときに games.json と CSV の中身が食い違わないよう、次のときは何も書かずに
終了コード1で止まる（前回の取り込み結果がそのまま残る）。
    - 日程が0件、または前回の games.json より試合が減った（--allow-fewer で通す）
    - 終わった試合の読み込みが、やり直しても通信の失敗で取れなかった
試合中の試合が取れなかったときは、注意を出して次へ進む（その試合の途中の成績は入らない）。
"""

from __future__ import annotations

import argparse
import csv
import html
import http.client
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
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
        except urllib.error.HTTPError as error:
            # 404 など相手が「ない」と答えたものは、やり直しても変わらないのですぐ投げる
            if error.code < 500 or attempt == attempts:
                raise
            print(f"    やり直し {attempt}/{attempts - 1}（{error}）")
            time.sleep(3 * attempt)
        except (TimeoutError, OSError, http.client.HTTPException) as error:
            # 読み込みが途中で切れたとき（IncompleteRead・RemoteDisconnected）は
            # OSError の仲間ではなく HTTPException の仲間なので、ここで一緒に受ける
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


def is_final(info: dict) -> bool:
    """終わった試合か。コールドなどは "F/7" のように後ろに回が付く。"""
    return str(info.get("gamestatustext") or "").startswith("F")


def is_complete(game: dict) -> bool:
    """raw に残してよい試合か。終わっていて、ボックススコアが入っている。"""
    return is_final(game.get("gameData") or {}) and bool(game.get("boxScore"))


def not_started(summary: dict) -> bool:
    """日程の上でまだ始まっていない試合か。

    状態が空で、開始時刻（utc。時差つき）が今より後なら、取りに行っても
    中身は空。開始時刻を過ぎても状態が変わらない試合（遅れ・中断）は取りに行く。
    """
    if str(summary.get("gamestatustext") or "").strip():
        return False
    if str(summary.get("gamestatus") or "0") != "0":
        return False
    try:
        start = datetime.fromisoformat(str(summary.get("utc")))
    except ValueError:
        return False
    if start.tzinfo is None:
        return False
    return start > datetime.now(timezone.utc)


def load_cached(path: Path) -> dict | None:
    """保存済みの raw を、使い回せるときだけ返す。"""
    if not path.exists():
        return None
    try:
        game = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return game if is_complete(game) else None


def game_date(info: dict, summary: dict) -> str:
    """試合の日付。gamedate が空なら、日程の start（現地時刻）の日付で埋める。"""
    date = info.get("gamedate") or summary.get("gamedate")
    if date:
        return str(date)
    start = str(summary.get("start") or info.get("start") or "")
    return start[:10]


def player_hands(game: dict) -> dict:
    """選手IDごとの投打（bats と throws）。boxScore の player 列から引く。"""
    hands = {}
    for _, _, row in iter_box(game):
        player = row.get("player") or {}
        hands[row.get("playerid")] = {
            "bats": player.get("bats") or "",
            "throws": player.get("throws") or "",
        }
    return hands


def iter_plays(game: dict):
    """打席の記録を、回の表裏の順に並べて返す。

    WBSCの生データでは裏のキーが "bot"。念のため "bottom" も受ける。
    """
    plays = (game.get("gamePlays") or {}).get("all") or {}
    for inning in sorted(plays, key=lambda x: int(x)):
        block = plays[inning] or {}
        halves = (("top", block.get("top")),
                  ("bot", block.get("bot") or block.get("bottom")))
        for half, rows in halves:
            for play in rows or []:
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


class Refused(Exception):
    """書き出すと前回の取り込み結果を壊すので、何も書かずに止めるとき。"""


def previous_count(path: Path) -> int | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return len(data) if isinstance(data, list) else None


def collect(key: str, out_root: Path, allow_fewer: bool = False) -> None:
    domain, slug, note = EVENTS[key]
    out_dir = out_root / key
    (out_dir / "raw").mkdir(parents=True, exist_ok=True)
    print(f"\n{key} — {note}")

    games = fetch_games(domain, slug)
    print(f"  試合 {len(games)}件")
    before = previous_count(out_dir / "games.json")
    if not games:
        raise Refused("日程が0件で返ってきました。WBSCのページの形が変わったか、"
                      "読み込みに失敗した可能性があります。前回の取り込み結果はそのままです。")
    if before is not None and len(games) < before and not allow_fewer:
        raise Refused(f"日程の試合が前回より減りました（{before}件 → {len(games)}件）。"
                      "前回の取り込み結果はそのままです。意図したものなら --allow-fewer を付けてください。")

    batting: list[dict] = []
    pitching: list[dict] = []
    plays: list[dict] = []

    skipped = 0
    for index, summary in enumerate(games, 1):
        game_id = summary.get("id")
        if not game_id:
            continue
        cached = out_dir / "raw" / f"{game_id}.json"
        game = load_cached(cached)
        if game is None:
            if not_started(summary):
                skipped += 1
                continue
            try:
                game = fetch_game(domain, slug, game_id)
            except urllib.error.HTTPError as error:
                print(f"  [{index}/{len(games)}] {game_id} 取得できず（{error.code}）")
                continue
            except (urllib.error.URLError, http.client.HTTPException, OSError) as error:
                if is_final(summary):
                    raise Refused(f"終わった試合 {game_id} を、やり直しても読み込めませんでした"
                                  f"（{error}）。前回の取り込み結果はそのままです。"
                                  "電波のよい所でもう一度流してください。") from error
                print(f"  [{index}/{len(games)}] {game_id} 取得できず（{error}）。"
                      "試合中の試合なので飛ばします")
                continue
            if is_complete(game):
                cached.write_text(
                    json.dumps(game, ensure_ascii=False), encoding="utf-8"
                )
            time.sleep(SLEEP_SECONDS)

        info = game.get("gameData") or {}
        hands = player_hands(game)
        # 選手行にも home（0か1か）があるので、試合側は別の名前にする
        context = {
            "event": key,
            "gameid": game_id,
            "date": game_date(info, summary),
            "away_team": info.get("awaylabel"),
            "home_team": info.get("homelabel"),
        }

        for team_id, spot, row in iter_box(game):
            side = "home_team" if str(row.get("home")) == "1" else "away_team"
            entry = {
                **context,
                "team": context[side],
                "teamid": team_id,
                "spot": spot,
                **row,
            }
            if str(spot) == "90" or row.get("pitch_appear"):
                pitching.append(entry)
            else:
                batting.append(entry)
        for inning, half, play in iter_plays(game):
            bat_side = "home_team" if str(play.get("home")) == "1" else "away_team"
            plays.append({
                **context,
                "batting_team": context[bat_side],
                "inning": inning,
                "half": half,
                **play,
                "batter_bats": hands.get(play.get("batterid"), {}).get("bats", ""),
                "pitcher_throws": hands.get(play.get("pitcherid"), {}).get("throws", ""),
            })

        state = ""
        if not is_complete(game):
            state = f"（{info.get('gamestatustext') or '試合前'}。raw には残さない）"
        print(f"  [{index}/{len(games)}] {context['away_team']} @ "
              f"{context['home_team']}{state}")

    if skipped:
        print(f"  まだ始まっていない {skipped}試合は取りに行きませんでした")
    write_csv(out_dir / "batting.csv", batting)
    write_csv(out_dir / "pitching.csv", pitching)
    write_csv(out_dir / "plays.csv", plays)
    # games.json は最後に書く。途中で止まっても、前回の games.json と CSV の組が残る
    (out_dir / "games.json").write_text(
        json.dumps(games, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  games.json: {len(games)}件")
    print(f"  出力先 {out_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", action="append", help="大会キー")
    parser.add_argument("--all", action="store_true", help="登録済みを全部取る")
    parser.add_argument("--list", action="store_true", help="大会の一覧を表示")
    parser.add_argument("--out", type=Path, default=OUT_ROOT, help="出力先")
    parser.add_argument("--allow-fewer", action="store_true",
                        help="日程の試合が前回より減っても書き出す（意図して減ったとき）")
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
        try:
            collect(key, args.out, args.allow_fewer)
        except Refused as error:
            print(f"  止めました: {error}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
