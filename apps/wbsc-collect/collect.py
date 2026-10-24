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
    - 終わった試合を、WBSCが 404 や 5xx（やり直したあと）で返した（--skip-missing で通す）
試合中の試合が取れなかったときは、注意を出して次へ進む（その試合の途中の成績は入らない）。
CSV の行が0件になったときは、前回の CSV をゴミ箱へ送る（古い成績が残って読まれないように）。

登録名簿（Teams & Rosters）は試合とは別に取る。
    python3 collect.py --event u23-wc-2026 --rosters
Teams & Rosters の各チームのページは Inertia ではなく普通のHTMLなので、表を読む。
    rosters.csv       登録された選手（playerid・背番号・ローマ字の名前・守備・投打・生年）
    coaches.csv       首脳陣（背番号・名前・役職）
playerid は、同じ大会のボックススコアの playerid と同じ。WBSCが名簿をまだ出していない
（「Team rosters are not available yet」）ときは何も書かずに終わる。名簿が出ているチームが
前回の rosters.csv より減ったときは、何も書かずに止まる（--allow-fewer で通す）。
"""

from __future__ import annotations

import argparse
import csv
import html
import http.client
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
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


def fetch_html(url: str, attempts: int = 4) -> str:
    """ページのHTMLを取る。

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
    return body


def fetch_page_props(url: str, attempts: int = 4) -> dict:
    """Inertiaの data-page に入っているJSONを取り出す。"""
    body = fetch_html(url, attempts)
    marker = 'data-page="'
    start = body.index(marker) + len(marker)
    end = body.index('"', start)
    return json.loads(html.unescape(body[start:end]))["props"]


def http_reason(code: int) -> str:
    """HTTPの状態番号を、止めたときの説明にする。"""
    if code >= 500:
        return "WBSC側の不調。間隔を空けて4回試しました"
    if code == 404:
        return "WBSCにその試合のページがない"
    return "WBSCに断られた"


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


def parse_utc(text) -> datetime | None:
    """utc 列の時刻をタイムゾーンつきで読む。時差がない・読めないときは None。

    "-06:00" のほかに "Z" や "+00:00" で来ても同じ時刻として読む
    （Python 3.9 の fromisoformat は末尾の "Z" を読めないので "+00:00" に直す）。
    site_logic.parse_utc と同じ決まり。
    """
    value = str(text or "").strip()
    if value[-1:] in ("Z", "z"):
        value = value[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return None
    return moment if moment.tzinfo else None


def not_started(summary: dict, now: datetime | None = None) -> bool:
    """日程の上でまだ始まっていない試合か。

    状態が空で、開始時刻（utc。時差つき）が今より後なら、取りに行っても
    中身は空。開始時刻を過ぎても状態が変わらない試合（遅れ・中断）は取りに行く。
    now は試し用（タイムゾーンつき）。省くと今。
    """
    if str(summary.get("gamestatustext") or "").strip():
        return False
    if str(summary.get("gamestatus") or "0") != "0":
        return False
    start = parse_utc(summary.get("utc"))
    if start is None:
        return False
    return start > (now or datetime.now(timezone.utc))


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


def discard(path: Path) -> None:
    """ファイルをゴミ箱へ送る（元に戻せない消し方はしない）。"""
    if Path("/usr/bin/trash").exists():
        subprocess.run(["/usr/bin/trash", str(path)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return
    trash = Path.home() / ".Trash"
    trash.mkdir(exist_ok=True)
    shutil.move(str(path), str(trash / f"{path.name}-{time.strftime('%Y%m%d%H%M%S')}"))


def write_csv(path: Path, rows: list[dict]) -> None:
    """CSV を書く。0行なら、前回の CSV をゴミ箱へ送る（古い成績を残さない）。"""
    if not rows:
        if not path.exists():
            print(f"  {path.name}: 0行のため書き出しません")
            return
        try:
            discard(path)
        except (OSError, subprocess.CalledProcessError) as error:
            raise Refused(f"{path.name} が0行になりましたが、前回の {path.name} をゴミ箱へ"
                          f"送れませんでした（{error}）。古い成績が残るので止めました。") from error
        print(f"  {path.name}: 0行のため、前回の {path.name} をゴミ箱へ送りました")
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


def collect(key: str, out_root: Path, allow_fewer: bool = False,
            skip_missing: bool = False) -> None:
    """1大会を取り込む。止めるときは何も書かずに Refused を投げる。

    skip_missing は、WBSCが終わった試合を 404 や 5xx で返したときに止めず、その試合の
    成績を入れないまま書き出す（ボックススコアがないと分かっているときだけ使う）。
    """
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
    missing: list[str] = []
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
                # 終わった試合を飛ばすと、日程では「終了」なのに成績の行がない組ができる
                if is_final(summary) and not skip_missing:
                    raise Refused(f"終わった試合 {game_id} を、WBSCが {error.code} で返したため"
                                  f"取れませんでした（{http_reason(error.code)}）。前回の取り込み結果は"
                                  "そのままです。しばらくしてもう一度流してください。ボックススコアが"
                                  "ないまま進めるなら --skip-missing を付けてください"
                                  "（その試合の成績は入りません）。") from error
                if is_final(summary):
                    missing.append(str(game_id))
                    print(f"  [{index}/{len(games)}] {game_id} 取得できず（{error.code}）。"
                          "--skip-missing なので、終わった試合の成績を入れずに進みます")
                else:
                    print(f"  [{index}/{len(games)}] {game_id} 取得できず（{error.code}）。"
                          "試合中の試合なので飛ばします")
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
    if missing:
        print(f"  注意: 終わった {len(missing)}試合（{', '.join(missing)}）は成績が入っていません。"
              "次に流したときに取り直します")
    # 0行の CSV を先に片付ける。ゴミ箱へ送れずに止まったときは、まだ何も書いていない
    outputs = (("batting.csv", batting), ("pitching.csv", pitching), ("plays.csv", plays))
    for name, rows in sorted(outputs, key=lambda item: bool(item[1])):
        write_csv(out_dir / name, rows)
    # games.json は最後に書く。途中で止まっても、前回の games.json と CSV の組が残る
    (out_dir / "games.json").write_text(
        json.dumps(games, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  games.json: {len(games)}件")
    print(f"  出力先 {out_dir}")


# ---------------------------------------------------------------- 登録名簿（Teams & Rosters）

JST = timezone(timedelta(hours=9))
# 一覧の1行: <tr onClick="...teams/40774'"><td><p><img src=".../flags/ioc/AUS.svg"> Australia</p>
TEAM_ROW = re.compile(r"/teams/(\d+)'\"\s*>\s*<td[^>]*>\s*<p>\s*<img[^>]*?/ioc/([A-Za-z]+)\.svg[^>]*>"
                      r"\s*([^<]*?)\s*</p>", re.S)


def strip_tags(text: str) -> str:
    """HTMLの断片から文字だけを取り出し、空白をならす。"""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text)).split())


def team_list(page: str) -> list[dict]:
    """Teams & Rosters の一覧から、チームID・略号（国旗の IOC コード）・英語のチーム名を出す。

    一覧は名簿が出る前から並んでいる。同じチームが2度出たら最初の1つだけ残す。
    """
    teams, seen = [], set()
    for team_id, ioc, name in TEAM_ROW.findall(page):
        if team_id not in seen:
            seen.add(team_id)
            teams.append({"teamid": team_id, "ioc": ioc.upper(), "team": strip_tags(name)})
    return teams


def html_tables(page: str) -> list[tuple[list[str], list[list[str]]]]:
    """ページの表ごとに、(見出しの列, 行ごとのセルのHTML) を返す。"""
    out = []
    for table in re.findall(r"<table.*?</table>", page, re.S):
        heads = [strip_tags(h) for h in re.findall(r"<th[^>]*>(.*?)</th>", table, re.S)]
        body = table.split("</thead>", 1)[-1]
        rows = [re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
                for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", body, re.S)]
        out.append((heads, [cells for cells in rows if cells]))
    return out


def pick(cells: list[str], col: dict, name: str, text: bool = True) -> str:
    """見出しの名前で列を選ぶ。text が偽ならタグを残したまま返す。"""
    i = col.get(name)
    if i is None or i >= len(cells):
        return ""
    return strip_tags(cells[i]) if text else cells[i]


def split_name(cell: str) -> tuple[str, str]:
    """「<strong>CHEN</strong> Chiu-Teng」を（姓, 名）にする。太字の部分が姓。"""
    strong = re.search(r"<strong>(.*?)</strong>", cell, re.S)
    if not strong:
        return strip_tags(cell), ""
    return strip_tags(strong.group(1)), strip_tags(cell[strong.end():])


def parse_roster(page: str) -> dict | None:
    """チームのページから登録名簿を読む。名簿がまだ出ていなければ None。

    選手の表は見出しが「# / Player / POS / B/T / YOB」、首脳陣の表は「# / Name / POS」。
    列は見出しの名前で探す（並びが変わっても読めるように）。B/T は「打/投」の順。
    """
    players, coaches = [], []
    for heads, rows in html_tables(page):
        col = {head.upper(): i for i, head in enumerate(heads)}
        if "PLAYER" in col:
            for cells in rows:
                cell = pick(cells, col, "PLAYER", text=False)
                link = re.search(r"/players/(\d+)", cell)
                last, first = split_name(cell)
                hands = (pick(cells, col, "B/T").upper().split("/") + ["", ""])[:2]
                players.append({
                    "playerid": link.group(1) if link else "",
                    "uniform": pick(cells, col, "#"),
                    "lastname": last,
                    "firstname": first,
                    "position": pick(cells, col, "POS").upper(),
                    "bats": hands[0].strip(),
                    "throws": hands[1].strip(),
                    "yob": pick(cells, col, "YOB"),
                })
        elif "NAME" in col:
            for cells in rows:
                last, first = split_name(pick(cells, col, "NAME", text=False))
                coaches.append({"uniform": pick(cells, col, "#"), "lastname": last,
                                "firstname": first, "role": pick(cells, col, "POS")})
    if not players:
        return None
    return {"players": players, "coaches": coaches}


def fetch_rosters(key: str) -> tuple[list[dict], list[dict], list[dict]]:
    """1大会の全チームの登録名簿を取る。(チームの一覧, 選手の行, 首脳陣の行)。

    チームの一覧の各行には players（読めた選手の人数。名簿がなければ0）が付く。
    """
    domain, slug, _ = EVENTS[key]
    teams = team_list(fetch_html(event_url(domain, slug, "teams")))
    fetched = datetime.now(JST).strftime("%Y-%m-%d %H:%M")
    players: list[dict] = []
    coaches: list[dict] = []
    for team in teams:
        time.sleep(SLEEP_SECONDS)
        roster = parse_roster(fetch_html(event_url(domain, slug, f"teams/{team['teamid']}")))
        team["players"] = len(roster["players"]) if roster else 0
        if not roster:
            continue
        base = {"event": key, "teamid": team["teamid"], "team": team["team"], "ioc": team["ioc"]}
        players += [{**base, **row, "fetched": fetched} for row in roster["players"]]
        coaches += [{**base, **row, "fetched": fetched} for row in roster["coaches"]]
    return teams, players, coaches


def roster_teams(path: Path) -> set[str]:
    """前回の rosters.csv に名簿があったチームの略号。なければ空。"""
    if not path.exists():
        return set()
    with path.open(encoding="utf-8-sig") as handle:
        return {row.get("ioc") or "" for row in csv.DictReader(handle)} - {""}


def collect_rosters(key: str, out_root: Path, allow_fewer: bool = False) -> None:
    """1大会の登録名簿を rosters.csv と coaches.csv に書く。止めるときは何も書かずに Refused。"""
    note = EVENTS[key][2]
    out_dir = out_root / key
    print(f"\n{key} の登録名簿 — {note}")
    try:
        teams, players, coaches = fetch_rosters(key)
    except (OSError, http.client.HTTPException) as error:
        raise Refused(f"登録名簿のページを読み込めませんでした（{error}）。"
                      "前回の rosters.csv はそのままです。") from error
    if not teams:
        raise Refused("Teams & Rosters にチームが1つもありませんでした。WBSCのページの形が"
                      "変わった可能性があります。前回の rosters.csv はそのままです。")
    for team in teams:
        count = f"{team['players']}人" if team["players"] else "名簿なし"
        print(f"  {team['ioc']} {team['team']}: {count}")
    if not players:
        print("  登録名簿はまだ出ていません（WBSCの表示は「Team rosters are not available yet」）。"
              "何も書きません")
        return
    lost = roster_teams(out_dir / "rosters.csv") - {row["ioc"] for row in players}
    if lost and not allow_fewer:
        raise Refused(f"前回は名簿があったチーム（{', '.join(sorted(lost))}）の名簿が読めませんでした。"
                      "前回の rosters.csv はそのままです。意図したものなら --allow-fewer を付けてください。")
    unlinked = [row for row in players if not row["playerid"]]
    if unlinked:
        names = ", ".join(f"{row['ioc']} {row['lastname']} {row['firstname']}" for row in unlinked)
        print(f"  注意: 選手ページへのリンクがなく playerid が空の選手がいます（{names}）")
    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(out_dir / "rosters.csv", players)
    if coaches:
        write_csv(out_dir / "coaches.csv", coaches)
    print(f"  出力先 {out_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", action="append", help="大会キー")
    parser.add_argument("--all", action="store_true", help="登録済みを全部取る")
    parser.add_argument("--list", action="store_true", help="大会の一覧を表示")
    parser.add_argument("--out", type=Path, default=OUT_ROOT, help="出力先")
    parser.add_argument("--allow-fewer", action="store_true",
                        help="日程の試合が前回より減っても書き出す（意図して減ったとき）")
    parser.add_argument("--skip-missing", action="store_true",
                        help="終わった試合が404や5xxで取れなくても、その試合の成績を入れずに書き出す")
    parser.add_argument("--rosters", action="store_true",
                        help="試合ではなく登録名簿（Teams & Rosters）を rosters.csv と coaches.csv に取る")
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
            if args.rosters:
                collect_rosters(key, args.out, args.allow_fewer)
            else:
                collect(key, args.out, args.allow_fewer, args.skip_missing)
        except Refused as error:
            print(f"  止めました: {error}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
