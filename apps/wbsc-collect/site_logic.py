#!/usr/bin/env python3
"""共有サイトで使う計算だけの部品。画面は持たない。

試合の状態と時刻、順位表（WBSCの同率の決め方つき）、スーパーラウンドと
順位決定ラウンドの持ち越し、日本から見た試合結果、投手の登板記録、
大会をまたいで同じ選手をまとめる鍵を作る。build_site.py から使う。

    python3 site_logic.py --selftest   # 2022年・2024年の公式順位と照らし合わせる

同率の決め方は WBSC Baseball World Cups Tournament Regulations（2024年6月14日改訂）
の C11 による。12チームの大会方式と持ち越しは同じ資料の「12-Team Format」。
https://static.wbsc.org/uploads/federations/0/cms/documents/84c93467-7438-c6b9-5a72-6d2419e95abf.pdf
2026年大会の要項そのものとは照らし合わせていない。
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
import time
import unicodedata
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
from itertools import combinations
from pathlib import Path

import build_report as br

# ニカラグアは UTC-6 で夏時間がない。日本時間は現地の15時間後
LOCAL_TZ = timezone(timedelta(hours=-6))
JST = timezone(timedelta(hours=9))

# U-23W杯は7イニング制。5回以降に10点差がつけばコールド（WBSC Official Rules 2025-2026 A1.4.1.2）
# https://static.wbsc.org/uploads/federations/0/cms/documents/d3d36a7c-4a8a-1cca-adc1-d4edff1efc30.pdf
REGULATION_INNINGS = 7
RUN_DIFFERENCE = 10
RUN_DIFFERENCE_FROM = 5

# 試合が始まらない・止まっているときの gamestatustext に含まれそうな語（推測）
OTHER_WORDS = ("PPD", "POSTP", "SUSP", "CANC", "DELAY", "RAIN")
# そのうち、もう行われない（中止）と読む語。CANCELLED・CANCELED も含む（推測）
CANCEL_WORDS = ("CANC",)
# 試合中と読む gamestatustext の形（推測）。「T3」「B5」「Top 3rd」「Bot 5」「M3」「End 7」のように表裏と回。
# これに当たらない知らない文字は「試合中」と決めつけず、game_state で "unknown" にする
LIVE_TEXT = re.compile(r"(T|B|M|E|TOP|BOT|BOTTOM|MID|MIDDLE|END)[\s.]*\d{1,2}(ST|ND|RD|TH)?")

# 大会によって表記が違う国名をそろえる
TEAM_ALIAS = {
    "south korea": "korea",
    "korea republic": "korea",
    "republic of korea": "korea",
    "czech republic": "czechia",
    "united states": "usa",
}


# ---------------------------------------------------------------- 試合の状態と時刻


def is_final(game: dict) -> bool:
    """終わった試合か。コールドなどで "F/7" のように回数が付く値も終了と見なす。"""
    return str(game.get("gamestatustext") or "").strip().upper().startswith("F")


def is_cancelled(game: dict) -> bool:
    """中止になった試合か。延期（PPD）や中断（SUSP）は、あとで行われるので含めない。"""
    text = str(game.get("gamestatustext") or "").strip().upper()
    return not is_final(game) and any(word in text for word in CANCEL_WORDS)


def is_settled(game: dict) -> bool:
    """もう結果の動かない試合か（終了か中止）。ラウンドが終わったかを見るときに使う。"""
    return is_final(game) or is_cancelled(game)


def game_state(game: dict) -> str:
    """"pre"（試合前）・"live"（試合中）・"final"（終了）・"other"（中止や中断）・
    "unknown"（知らない状態の文字）を返す。

    試合中や中断のときの値は手元のデータに例がないので推測で分けている。
    gamestatus は試合前が0、終了が2か3だった。試合中と読むのは、状態の文字が LIVE_TEXT の形
    （「T3」など）のときと、文字が空で gamestatus が1のときだけ。ほかの文字は "unknown" にして、
    画面には「状態: <文字>」と出す（大会初日に実際の値を見て、LIVE_TEXT などを足す）。
    """
    if is_final(game):
        return "final"
    text = str(game.get("gamestatustext") or "").strip().upper()
    status = int(br.number(game.get("gamestatus")))
    if any(word in text for word in OTHER_WORDS):
        return "other"
    if LIVE_TEXT.fullmatch(text) or (status == 1 and not text):
        return "live"
    if text:
        return "unknown"
    return "pre" if status == 0 else "other"


def parse_utc(text) -> datetime | None:
    """utc 列の時刻を、タイムゾーンつきで読む。時差のない値や読めない値は None。

    Python 3.9 の fromisoformat は末尾の "Z" を読めないので、"+00:00" に直してから読む。
    """
    value = str(text or "").strip()
    if value[-1:] in ("Z", "z"):
        value = value[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return None
    return moment if moment.tzinfo else None


def local_dt(game: dict) -> datetime | None:
    """現地の開始時刻（ニカラグア時間 UTC-6 のタイムゾーンつき）。

    games.json の utc 列は "2026-11-06T10:30:00-06:00" のように現地の時差つきで入っている。
    "Z" や "+00:00" など別の時差で来ても、現地の時刻に直してから返す（日付がずれないように）。
    ない場合は start 列をニカラグア時間（UTC-6）と見なす。
    比べるときは datetime.now(JST) のようにタイムゾーンつき同士で比べること。
    """
    moment = parse_utc(game.get("utc"))
    if moment:
        return moment.astimezone(LOCAL_TZ)
    try:
        moment = datetime.strptime(str(game.get("start") or ""), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None
    return moment.replace(tzinfo=LOCAL_TZ)


def jst_dt(game: dict) -> datetime | None:
    """日本時間の開始時刻（タイムゾーンつき）。ニカラグアなら現地の15時間後。"""
    moment = local_dt(game)
    return moment.astimezone(JST) if moment else None


def local_day(game: dict) -> str:
    """現地の日付（YYYY-MM-DD）。開始時刻が読めなければ空文字。"""
    moment = local_dt(game)
    return moment.date().isoformat() if moment else ""


# ---------------------------------------------------------------- 投球回とイニング


def ip_to_outs(value) -> int:
    """投球回の表記（"6.1" は6回1/3）をアウト数に直す。"""
    text = str(value if value is not None else "").strip()
    whole, _, frac = text.partition(".")
    try:
        return int(whole or 0) * 3 + int(frac[:1] or 0)
    except ValueError:
        return 0


def outs_to_ip(outs: int) -> str:
    """アウト数を投球回の表記に戻す（19 → "6.1"）。"""
    return f"{outs // 3}.{outs % 3}"


def load_outs(raw_dir) -> dict[str, tuple[int, int]]:
    """raw の各試合から、両チームが攻撃したアウト数を正確に取る。

    戻り値は {試合ID: (先攻の攻撃アウト数, 後攻の攻撃アウト数)}。
    boxScore の totals にある守備側の投球回が、そのまま相手の攻撃イニングになる。
    standings() と second_round() の outs に渡すと、サヨナラの回の端数が正確になる。
    """
    out: dict[str, tuple[int, int]] = {}
    for path in sorted(Path(raw_dir).glob("*.json")):
        try:
            game = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        info = game.get("gameData") or {}
        totals = (game.get("boxScore") or {}).get("totals") or {}
        home, away = str(info.get("homeid")), str(info.get("awayid"))
        if not is_final(info) or home not in totals or away not in totals:
            continue
        away_bat = ip_to_outs(totals[home].get("pitch_ip"))
        home_bat = ip_to_outs(totals[away].get("pitch_ip"))
        if away_bat and home_bat:
            out[str(info.get("id") or path.stem)] = (away_bat, home_bat)
    return out


def runs(game: dict) -> tuple[int, int]:
    """(先攻の得点, 後攻の得点)。空の値は0として数える（点数の表示には known_runs を使う）。"""
    return int(br.number(game.get("awayruns"))), int(br.number(game.get("homeruns")))


def known_runs(game: dict) -> tuple[int, int] | None:
    """(先攻の得点, 後攻の得点)。どちらかがまだ入っていない（None・空文字・数でない）なら None。

    試合中に点数が届く前の値を「0-0」と見せないためのもの。記録された0はそのまま0。
    """
    out = []
    for key in ("awayruns", "homeruns"):
        value = game.get(key)
        try:
            out.append(int(float(str(value).strip())))
        except (TypeError, ValueError, OverflowError):
            return None
    return out[0], out[1]


def score_text(game: dict, home_first: bool = False) -> str:
    """点数の表示。先攻-後攻の順（home_first なら後攻-先攻）。点数がそろっていなければ "-"。"""
    known = known_runs(game)
    if not known:
        return "-"
    away, home = known
    return f"{home}-{away}" if home_first else f"{away}-{home}"


def batting_outs(game: dict, outs: dict | None = None) -> tuple[int, int, bool]:
    """(先攻の攻撃アウト数, 後攻の攻撃アウト数, 確かか) を返す。

    games.json の回ごとの得点（runshome1..）と innings から読む。
    - 先攻の勝ち: 後攻も最終回の裏を最後まで攻撃している。7回まで行ったか、
      10点差のコールド（U-23は5回以降10点差。WBSC Official Rules 2025-2026 A1.4.1.2）なら確か。
    - 後攻がリードして最終回の裏を始めなかった（7回裏・9回裏をしない、表の終わりで
      10点差がついた）: 後攻の攻撃は1回少ない。7回まで行ったか、10点差なら確か。
    - 引き分け: サヨナラでは終わらないので、後攻も最終回の裏を最後まで攻撃したと見なす。
      回の途中で打ち切られた試合はずれるので、確かではない。
    - サヨナラ（裏の途中で10点差に届いた場合も含む）: 裏の途中で終わるが、そこまでの
      アウト数は games.json に入っていない（outs 欄は終了後いつも0）。1アウトで終わったと見なす。
      過去5大会の raw では、サヨナラで終わった裏のアウト数は0・1・2がほぼ同じ数（19試合で
      6・7・6）なので、外れても1アウト以内に収まるこの置き方にしている。これ以上は直せない。
    - 点差が足りないのに7回より前に終わった試合（雨など）も確かでない。
    確かでない試合は、raw から load_outs() で取った値を outs に渡せば正確になる。
    終わった試合の raw は collect.py が残すので、ふつうは近似を使わない。raw がないのは、
    ボックススコアのないまま終了になった試合や、collect.py を --skip-missing で流したとき。
    確かな試合は raw より回ごとの得点を信じる（2022年 Mexico@Australia は raw の投球回の
    合計が8回1/3で、8回で終わった試合としてありえない値だった）。
    """
    innings = int(br.number(game.get("innings")))
    away, home = runs(game)
    last = int(br.number(game.get(f"runshome{innings}")))
    full = 3 * innings
    late = innings >= REGULATION_INNINGS
    called = innings >= RUN_DIFFERENCE_FROM and abs(home - away) >= RUN_DIFFERENCE
    if home < away:
        guess, sure = (full, full), late or called
    elif home > away and home - last > away and last == 0:
        guess, sure = (full, full - 3), late or called
    elif home == away:
        guess, sure = (full, full), False
    else:
        guess, sure = (full, full - 2), False
    exact = (outs or {}).get(str(game.get("id")))
    if sure or not exact or max(exact) > full:
        return guess[0], guess[1], sure
    return exact[0], exact[1], True


# ---------------------------------------------------------------- 順位表


def _label_match(game: dict, label: str) -> bool:
    return label in str(game.get("gametypelabel") or "")


def _tally(games: list[dict], teams: list[str], outs: dict | None) -> dict[str, dict]:
    """チームごとに試合数・勝敗・得失点・攻撃と守備のアウト数を数える。"""
    # est は、攻撃と守備のアウト数を推定で数えた試合の数（batting_outs が確かでない試合）
    table = {t: {"g": 0, "w": 0, "l": 0, "t": 0, "rs": 0, "ra": 0, "ob": 0, "of": 0, "est": 0}
             for t in teams}
    for game in games:
        home, away = game.get("homelabel"), game.get("awaylabel")
        if home not in table or away not in table or not known_runs(game):
            continue  # 点数が入っていない試合は、0-0の引き分けと数えない
        away_runs, home_runs = runs(game)
        away_outs, home_outs, sure = batting_outs(game, outs)
        for team, mine, theirs, bat, field in (
            (away, away_runs, home_runs, away_outs, home_outs),
            (home, home_runs, away_runs, home_outs, away_outs),
        ):
            row = table[team]
            row["g"] += 1
            row["w" if mine > theirs else "l" if mine < theirs else "t"] += 1
            row["rs"] += mine
            row["ra"] += theirs
            row["ob"] += bat
            row["of"] += field
            row["est"] += not sure
    return table


def _pct(row: dict) -> Fraction | None:
    """勝率。引き分けは分母に入れない（WBSCの規程に定めがないので、日本と同じ扱い）。"""
    decided = row["w"] + row["l"]
    return Fraction(row["w"], decided) if decided else None


def _tqb(row: dict) -> Fraction | None:
    """TQB = 得点 ÷ 攻撃イニング − 失点 ÷ 守備イニング。イニングはアウト数 ÷ 3。"""
    if not row["ob"] or not row["of"]:
        return None
    return Fraction(3 * row["rs"], row["ob"]) - Fraction(3 * row["ra"], row["of"])


def _bands(teams: list[str], key) -> list[list[str]]:
    """key の値が大きい順に並べ、同じ値どうしを1つの組にまとめる。"""
    ordered = sorted(teams, key=key, reverse=True)
    bands: list[list[str]] = []
    for team in ordered:
        if bands and key(bands[-1][0]) == key(team):
            bands[-1].append(team)
        else:
            bands.append([team])
    return bands


def _break_tie(members: list[str], games: list[dict], outs: dict | None,
               notes: dict[str, str], cancelled: frozenset = frozenset()) -> list[list[str]]:
    """勝率が並んだチームを、WBSCの C11 の順に並べる。分けきれない組はまとめて返す。

    1. 当該チーム同士の勝敗（2チームなら直接対決）。3チーム以上で一部だけ分かれたら、
       残った組でもう一度 1 からやり直す（規程の例 Scenario 3 と同じ扱い）。
    2. 当該チーム同士の試合での TQB。3チーム以上はこれで全員を上から並べる。
    3. ER-TQB と打率は games.json から出せないので計算しない。そこまで並んだら同率のまま。
    当該チーム同士の対戦が残っているうち（大会の途中）は決めず、同率のままにする。
    cancelled は中止になった組（frozenset の集まり）。もう行われないので「残っている」とは
    見なさず、行われた試合だけで比べる（規程に定めがないので、この扱いは推測）。
    """
    if len(members) < 2:
        return [members]
    between = [g for g in games
               if g.get("homelabel") in members and g.get("awaylabel") in members]
    played = {frozenset((g["homelabel"], g["awaylabel"])) for g in between}
    if any(frozenset(pair) not in played and frozenset(pair) not in cancelled
           for pair in combinations(members, 2)):
        for team in members:
            notes[team] = "同率（当該チームの対戦が残っている）"
        return [members]
    if not between:
        for team in members:
            notes[team] = "同率（当該チーム同士の試合は中止）"
        return [members]
    table = _tally(between, members, outs)
    bands = _bands(members, lambda t: _pct(table[t]) or Fraction(0))
    if len(bands) > 1:
        return _split_by_record(members, bands, table, games, outs, notes, cancelled)
    return _split_by_tqb(members, table, notes)


def _split_by_record(members, bands, table, games, outs, notes,
                     cancelled=frozenset()) -> list[list[str]]:
    tiers: list[list[str]] = []
    for band in bands:
        for team in band:
            row = table[team]
            if len(members) == 2:
                notes[team] = "直接対決で勝ち" if row["w"] > row["l"] else "直接対決で負け"
            else:
                notes[team] = f"同率{len(members)}チームの当該対戦 {row['w']}勝{row['l']}敗"
        tiers.extend(_break_tie(band, games, outs, notes, cancelled) if len(band) > 1 else [band])
    return tiers


def _split_by_tqb(members, table, notes) -> list[list[str]]:
    tqb = {t: _tqb(table[t]) for t in members}
    tiers = _bands(members, lambda t: tqb[t] if tqb[t] is not None else Fraction(-999))
    guessed = any(table[t]["est"] for t in members)
    for tier in tiers:
        for team in tier:
            value = tqb[team]
            shown = f"{float(value):+.4f}" if value is not None else "-"
            remarks = (["TQBも同じ。ER-TQB以降は未計算"] if len(tier) > 1 else []) \
                + (["イニングの一部は推定"] if guessed else [])
            extra = f"（{'。'.join(remarks)}）" if remarks else ""
            notes[team] = f"同率{len(members)}チーム・当該TQB {shown}{extra}"
    return tiers


def _fmt_pct(value: Fraction | None) -> str:
    if value is None:
        return "-"
    return f"{float(value):.3f}".lstrip("0") if value < 1 else "1.000"


def _rows(teams: list[str], games: list[dict], outs: dict | None,
          cancelled: frozenset = frozenset()) -> list[dict]:
    """1つの表（組）の順位を決めて、行の一覧にする。試合のないチームは順位なしで最後。

    games は終わった試合だけ。cancelled は中止になった組（_cancelled_pairs）。
    """
    table = _tally(games, teams, outs)
    played = [t for t in teams if table[t]["g"]]
    notes: dict[str, str] = {}
    tiers: list[list[str]] = []
    for band in _bands(played, lambda t: _pct(table[t]) if _pct(table[t]) is not None
                       else Fraction(1, 2)):
        for tier in _break_tie(band, games, outs, notes, cancelled):
            # 同率のまま残った組は、首位とのゲーム差が小さい順に見せる
            tiers.append(sorted(tier, key=lambda t: table[t]["l"] - table[t]["w"]))
    out: list[dict] = []
    for tier in tiers:
        rank = len(out) + 1
        out.extend(_row(t, rank, table, notes) for t in tier)
    out.extend(_row(t, None, table, notes) for t in teams if not table[t]["g"])
    _fill_gb(out, table)
    return out


def _row(team: str, rank: int | None, table: dict, notes: dict) -> dict:
    row = table[team]
    tqb = _tqb(row)
    return {
        "team": team, "rank": rank, "g": row["g"], "w": row["w"], "l": row["l"],
        "t": row["t"], "pct": _fmt_pct(_pct(row)), "gb": "-",
        "rs": row["rs"], "ra": row["ra"],
        "tqb": round(float(tqb), 4) if tqb is not None else None,
        "note": notes.get(team, ""),
    }


def _fill_gb(out: list[dict], table: dict) -> None:
    """ゲーム差 =（首位との勝ち数の差 + 負け数の差）÷ 2。首位と同じなら "-"。"""
    if not out or out[0]["rank"] is None:
        return
    top = table[out[0]["team"]]
    for row in out:
        if row["rank"] is None:
            continue
        mine = table[row["team"]]
        behind = ((top["w"] - mine["w"]) + (mine["l"] - top["l"])) / 2
        row["gb"] = f"{behind:.1f}" if behind > 0 else "-"


def _cancelled_pairs(games: list[dict], label: str) -> frozenset:
    """label のラウンドで中止になった試合の組（{frozenset((先攻, 後攻)), ...}）。"""
    return frozenset(frozenset((g.get("homelabel"), g.get("awaylabel"))) for g in games
                     if is_cancelled(g) and _label_match(g, label))


def standings(games: list[dict], groups: dict[str, str],
              round_label: str = "Opening Round",
              outs: dict | None = None) -> dict[str, list[dict]]:
    """組ごとの順位表。{"A": [行...], "B": [行...]} を返す。

    groups は {チーム名（WBSCの英語表記）: "A" | "B"}。この順が試合前の並び順になる。
    数えるのは終了した round_label の試合のうち、同じ組どうしの試合だけ。
    行: team, rank（試合がなければ None）, g, w, l, t, pct, gb, rs, ra, tqb, note。
    tqb はその組の全試合での値。同率を分けた理由は note に書く（当該チームでの TQB など）。
    outs は load_outs() の戻り値。省くとサヨナラの回の端数が近似になる。
    """
    counted = [g for g in games
               if is_final(g) and _label_match(g, round_label)
               and g.get("homelabel") in groups and g.get("awaylabel") in groups
               and groups[g["homelabel"]] == groups[g["awaylabel"]]]
    cancelled = _cancelled_pairs(games, round_label)
    out: dict[str, list[dict]] = {}
    for group in sorted(set(groups.values())):
        teams = [t for t in groups if groups[t] == group]
        mine = [g for g in counted if groups[g["homelabel"]] == group]
        out[group] = _rows(teams, mine, outs, cancelled)
    return out


# ---------------------------------------------------------------- 第2ラウンド


def _scheduled(games: list[dict], label: str, groups: dict) -> list[str]:
    """日程に載った第2ラウンドの試合から、出るチームを拾う（仮の名前は除く）。"""
    teams: list[str] = []
    for game in games:
        if not _label_match(game, label):
            continue
        for team in (game.get("awaylabel"), game.get("homelabel")):
            if team in groups and team not in teams:
                teams.append(team)
    return teams


def _split_first_round(first: dict[str, list[dict]]) -> tuple[list, list, bool]:
    """各組の上位3と下位3に分ける。3位と4位が同率のままなら、分かれていない扱い。"""
    top: list[str] = []
    bottom: list[str] = []
    clear = True
    for rows in first.values():
        if len(rows) < 6 or any(r["rank"] is None for r in rows):
            return [], [], False
        clear = clear and rows[2]["rank"] != rows[3]["rank"]
        top += [r["team"] for r in rows[:3]]
        bottom += [r["team"] for r in rows[3:]]
    return top, bottom, clear


def _second_table(teams: list[str], games: list[dict], label: str,
                  groups: dict, outs: dict | None) -> list[dict]:
    """当該チーム同士の1次ラウンドの結果を持ち越し、第2ラウンドの試合を足して並べる。"""
    members = set(teams)
    carried = [g for g in games
               if is_final(g) and _label_match(g, "Opening Round")
               and g.get("homelabel") in members and g.get("awaylabel") in members]
    added = [g for g in games
             if is_final(g) and _label_match(g, label)
             and g.get("homelabel") in members and g.get("awaylabel") in members]
    cancelled = _cancelled_pairs(games, "Opening Round") | _cancelled_pairs(games, label)
    rows = _rows(teams, carried + added, outs, cancelled)
    carry = _tally(carried, teams, outs)
    for row in rows:
        mine = carry[row["team"]]
        row["group"] = groups.get(row["team"], "")
        row["carry"] = f"{mine['w']}-{mine['l']}" + (f"-{mine['t']}" if mine["t"] else "")
    return rows


def second_round(games: list[dict], groups: dict[str, str],
                 outs: dict | None = None) -> dict:
    """スーパーラウンドと順位決定ラウンドの順位（持ち越し込み）。

    戻り値は {"ready": bool, "super": [行...], "placement": [行...]}。
    1次ラウンドの各組の上位3チームがスーパーラウンド、下位3チームが順位決定ラウンド。
    1次ラウンドで当該チーム同士が戦った2試合を持ち越す（12-Team Format の規程）。
    1次ラウンドが終わったあと、日程に第2ラウンドの組み合わせが実名で載っていれば、
    そちらの顔ぶれを正とする（3位と4位が同率のまま計算で分けられない場合もこれで決まる）。
    ready は顔ぶれが決まったかどうか。1次ラウンドの途中は False で、
    「今の順位のまま終わったら」の暫定の表を返す（全チームが1試合以上してから）。
    中止（CANC など）のまま日程に残った試合は、もう行われないので「終わった」側に数える。
    行は standings() と同じ形に、group（1次ラウンドの組）と carry（持ち越しの勝敗）を足したもの。
    """
    first = standings(games, groups, "Opening Round", outs)
    top, bottom, clear = _split_first_round(first)
    opening = [g for g in games if _label_match(g, "Opening Round")
               and g.get("homelabel") in groups and g.get("awaylabel") in groups]
    done = bool(opening) and all(is_settled(g) for g in opening)
    ready = done and clear
    super_sched = _scheduled(games, "Super Round", groups)
    place_sched = _scheduled(games, "Placement Round", groups)
    if done and len(super_sched) == 6 and len(place_sched) == 6:
        top, bottom, ready = _keep_order(top, super_sched), _keep_order(bottom, place_sched), True
    if not top:
        return {"ready": False, "super": [], "placement": []}
    return {
        "ready": ready,
        "super": _second_table(top, games, "Super Round", groups, outs),
        "placement": _second_table(bottom, games, "Placement Round", groups, outs),
    }


def _keep_order(computed: list[str], scheduled: list[str]) -> list[str]:
    """日程の顔ぶれを、計算した順位の順に並べる（計算と違うチームは後ろに足す）。"""
    return [t for t in computed if t in scheduled] + [t for t in scheduled if t not in computed]


# ---------------------------------------------------------------- 日本から見た試合


def japan_view(game: dict, japan: str = "Japan") -> dict | None:
    """日本の試合を日本の側から見た形にする。日本の試合でなければ None。

    先攻はビジター（away）、後攻はホーム（home）。
    mark は終了した試合だけ（○勝ち・●負け・△引き分け）。score は日本の得点が先。
    試合中と、状態の文字が知らないもの（unknown）は score にその時点の得点を入れ、mark は空にする。
    点数がまだ両方そろっていない（None や空文字）ときは score を "-" にし、mark は付けない。
    """
    home, away = game.get("homelabel"), game.get("awaylabel")
    if japan not in (home, away):
        return None
    is_home = home == japan
    state = game_state(game)
    known = known_runs(game)
    mark, score = "", ""
    if state in ("final", "live", "unknown"):
        score = score_text(game, home_first=is_home)
    if state == "final" and known:
        away_runs, home_runs = known
        mine, theirs = (home_runs, away_runs) if is_home else (away_runs, home_runs)
        mark = "○" if mine > theirs else "●" if mine < theirs else "△"
    return {
        "opponent": away if is_home else home,
        "batting": "後攻" if is_home else "先攻",
        "mark": mark,
        "score": score,
        "state": state,
    }


# ---------------------------------------------------------------- 投手の登板記録


def _name(row: dict) -> str:
    last = (row.get("lastname") or "").strip()
    first = (row.get("firstname") or "").strip()
    return f"{last}, {first}".strip(", ")


def _as_date(value) -> date:
    """today に渡された値を日付にする。省略時は現地（UTC-6）の今日。"""
    if value is None:
        return datetime.now(LOCAL_TZ).date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _appearance(row: dict, game: dict | None, team: str) -> dict:
    """pitching.csv の1行を、1回の登板の記録にする。日付は games.json の start から。"""
    if game:
        day = local_day(game)
        home, away = game.get("homelabel"), game.get("awaylabel")
        moment = local_dt(game)
    else:
        day = (row.get("date") or "")[:10]
        home, away = row.get("home_team"), row.get("away_team")
        moment = None
    return {
        "date": day,
        "gameid": str(row.get("gameid") or ""),
        "opponent": away if home == team else home,
        "gs": bool(int(br.number(row.get("pitch_gs")))),
        "ip": outs_to_ip(ip_to_outs(row.get("pitch_ip"))),
        "pitches": int(br.number(row.get("pitch_pitches"))),
        "_sort": (day, moment.isoformat() if moment else ""),
    }


def _rest(earlier: str, later: str) -> int | None:
    """中何日か（前の登板の翌日から次の登板の前日までの日数）。"""
    if not earlier or not later:
        return None
    return (date.fromisoformat(later) - date.fromisoformat(earlier)).days - 1


def pitcher_log(pitching_rows: list[dict], games: list[dict], team: str,
                today=None) -> list[dict]:
    """team の投手ごとの登板記録。最近投げた投手が先。

    投手ごと: name, _id, apps, last_date, rest_days, total_pitches, gs_count, ip_total。
    apps の1件: date, gameid, opponent, gs, ip（"6.1"）, pitches, rest（前の登板から中何日。
    初登板は None）。日付は gameid から games.json の start（現地の日付）を引く。
    rest_days は today に投げるとしたら中何日か。today 以降に投げていれば None。
    today は date・datetime・"YYYY-MM-DD" のどれでもよく、省くと現地の今日。
    """
    by_id = {str(g.get("id")): g for g in games}
    pitchers: dict[str, dict] = {}
    seen: set[tuple[str, str]] = set()
    for row in pitching_rows:
        if row.get("team") != team:
            continue
        pid = str(row.get("playerid") or "") or _name(row)
        gid = str(row.get("gameid") or "")
        if (pid, gid) in seen:
            continue
        seen.add((pid, gid))
        entry = pitchers.setdefault(pid, {"name": _name(row), "_id": pid, "apps": []})
        app = _appearance(row, by_id.get(gid), team)
        # 綴りが大会の途中で変わった選手は、一番新しい登板の綴りにする
        order = (app["_sort"], int(br.number(gid)))
        if order >= entry.get("_name_at", order):
            entry["name"] = _name(row) or entry["name"]
            entry["_name_at"] = order
        entry["apps"].append(app)
    day = _as_date(today)
    out = [_summarize(entry, day) for entry in pitchers.values()]
    out.sort(key=lambda e: (e["last_date"], e["total_pitches"]), reverse=True)
    return out


def _summarize(entry: dict, today: date) -> dict:
    entry = {k: v for k, v in entry.items() if k != "_name_at"}
    apps = sorted(entry["apps"], key=lambda a: a["_sort"])
    previous = ""
    for app in apps:
        app["rest"] = _rest(previous, app["date"]) if previous else None
        previous = app["date"] or previous
        app.pop("_sort")
    last = max((a["date"] for a in apps if a["date"]), default="")
    rest_days = None
    if last and date.fromisoformat(last) < today:
        rest_days = (today - date.fromisoformat(last)).days - 1
    outs = sum(ip_to_outs(a["ip"]) for a in apps)
    return {
        **entry, "apps": apps, "last_date": last, "rest_days": rest_days,
        "total_pitches": sum(a["pitches"] for a in apps),
        "gs_count": sum(1 for a in apps if a["gs"]),
        "ip_total": outs_to_ip(outs),
    }


# ---------------------------------------------------------------- 大会をまたぐ選手の鍵


def _plain(text: str) -> list[str]:
    """アクセントと大文字小文字と記号を落とし、単語に分ける。"""
    decomposed = unicodedata.normalize("NFKD", str(text or ""))
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    cleaned = "".join(c if c.isalnum() else " " for c in stripped.casefold())
    return cleaned.split()


def _person_basis(name: str, birth_year, team: str) -> str:
    words = " ".join(sorted(_plain(name)))
    year = str(birth_year).strip()[:4] if birth_year not in (None, "") else ""
    team_key = " ".join(_plain(team))
    team_key = TEAM_ALIAS.get(team_key, team_key)
    return f"{words}|{year if year.isdigit() else '?'}|{team_key}"


def person_key(name: str, birth_year, team: str) -> str:
    """大会ごとに違う playerid を、1人にまとめる鍵（英数字12文字）。

    名前は大文字小文字・アクセント・記号・余分な空白をならし、単語の順に並べ直す
    （姓と名の順が入れ替わっても同じになる）。それに生年と国を合わせて作る。
    生年が分からなければ「?」として扱う。同じ国に同姓同名・同じ年生まれの別人がいると
    1人にまとまってしまうので、まとめた結果は国ごとに目で確かめること。
    """
    basis = _person_basis(name, birth_year, team)
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------- 照合（--selftest）


class Check:
    """合った・合わなかったを数えながら表示する。"""

    def __init__(self) -> None:
        self.ok = 0
        self.ng: list[str] = []

    def __call__(self, passed: bool, text: str) -> None:
        print(f"  {'OK' if passed else 'NG'}  {text}")
        if passed:
            self.ok += 1
        else:
            self.ng.append(text)


def _event(key: str) -> tuple[list[dict], Path]:
    folder = br.DATA_ROOT / key
    return json.loads((folder / "games.json").read_text(encoding="utf-8")), folder


def _teams_info(games: list[dict]) -> dict[str, dict]:
    """games.json に入っている各チームの公式の成績欄（groupstandings など）。"""
    info: dict[str, dict] = {}
    for game in games:
        for side in ("home_team", "away_team"):
            block = game.get(side) or {}
            if block.get("teamlabel"):
                info[block["teamlabel"]] = block
    return info


def _groups(games: list[dict]) -> dict[str, str]:
    groups: dict[str, str] = {}
    for game in games:
        if not _label_match(game, "Opening Round"):
            continue
        for side in ("home_team", "away_team"):
            block = game.get(side) or {}
            groups.setdefault(block.get("teamlabel"), str(block.get("grouplabel"))[-1])
    return groups


def _official_round2(teams: list[str], info: dict, games: list[dict]) -> dict[str, int]:
    """第2ラウンドの公式順位。

    round2standingsadmin が入っていればそれを使う。2024年のスーパーラウンドは0なので、
    round2standings（同率は同じ数字）で並べ、同率はメダル戦のホーム（C10.2 で上位が
    ホーム）→ 最終順位の順で分ける。
    """
    admin = {t: int(info[t].get("round2standingsadmin") or 0) for t in teams}
    if all(admin.values()) and len(set(admin.values())) == len(teams):
        return admin
    medal_home = {g.get("homelabel") for g in games
                  if not any(_label_match(g, x) for x in
                             ("Opening Round", "Super Round", "Placement Round"))}
    ordered = sorted(teams, key=lambda t: (int(info[t].get("round2standings") or 99),
                                           t not in medal_home,
                                           int(info[t].get("finalstandings") or 99)))
    return {t: i for i, t in enumerate(ordered, 1)}


def _check_outs(games: list[dict], outs: dict, check: Check, key: str) -> None:
    """games.json だけで読んだイニングと raw の投球回の合計を比べる。"""
    approx = mismatch = odd = 0
    for game in games:
        exact = outs.get(str(game.get("id")))
        if not is_final(game) or not exact:
            continue
        away, home, sure = batting_outs(game)
        where = f"{game['awaylabel']} {game['awayruns']}-{game['homeruns']} {game['homelabel']}" \
                f"（{game['innings']}回）"
        if not sure:
            approx += 1
            print(f"      近似 {where} 推定 {outs_to_ip(away)}/{outs_to_ip(home)}回・"
                  f"raw {outs_to_ip(exact[0])}/{outs_to_ip(exact[1])}回")
        elif (away, home) != exact:
            impossible = max(exact) > 3 * int(game["innings"])
            odd += impossible
            mismatch += not impossible
            print(f"      {'raw がありえない値' if impossible else '不一致'} {where} "
                  f"回ごとの得点から {outs_to_ip(away)}/{outs_to_ip(home)}回・"
                  f"raw {outs_to_ip(exact[0])}/{outs_to_ip(exact[1])}回")
    check(mismatch == 0, f"{key} イニングの読み取り: 確かと判断した試合は raw と一致"
                         f"（確かでない {approx}試合、raw がありえない値 {odd}試合）")


def _compare(rows: list[dict], official: dict[str, int], label: str, check: Check) -> None:
    for row in rows:
        want = official.get(row["team"])
        record = f"{row['w']}勝{row['l']}敗" + (f"{row['t']}分" if row["t"] else "")
        extra = f" 持ち越し{row['carry']}" if "carry" in row else ""
        note = f"　{row['note']}" if row["note"] else ""
        check(row["rank"] == want,
              f"{label} {row['rank']}位 {row['team']}（公式{want}位）{record}{extra}{note}")


def _selftest_event(key: str, check: Check) -> None:
    games, folder = _event(key)
    info, groups = _teams_info(games), _groups(games)
    outs = load_outs(folder / "raw")
    print(f"\n== {key}（試合 {len(games)}件、raw のイニング {len(outs)}試合分）")
    _check_outs(games, outs, check, key)
    for use, title in ((outs, "raw のアウト数で端数も正確に"), (None, "games.json だけで近似")):
        print(f"  -- 1次ラウンド：{title}")
        for group, rows in standings(games, groups, outs=use).items():
            official = {t: int(info[t]["groupstandingsadmin"]) for t in groups
                        if groups[t] == group}
            _compare(rows, official, f"{key} 1次R 組{group}", check)
    second = second_round(games, groups, outs)
    check(second["ready"], f"{key} 第2ラウンドの顔ぶれが決まっている（ready）")
    for part, label in (("super", "スーパーR"), ("placement", "順位決定R")):
        print(f"  -- {label}：持ち越し込み")
        teams = [r["team"] for r in second[part]]
        _compare(second[part], _official_round2(teams, info, games), f"{key} {label}", check)


def _selftest_netherlands(check: Check) -> None:
    """2024年B組のオランダとチャイニーズタイペイ（どちらも2勝3敗）。"""
    games, folder = _event("u23-wc-2024")
    groups, outs = _groups(games), load_outs(folder / "raw")
    print("\n== 2024年 オランダとチャイニーズタイペイ")
    duel = [g for g in games if {g["homelabel"], g["awaylabel"]}
            == {"Netherlands", "Chinese Taipei"}]
    for game in duel:
        print(f"      直接対決 {game['gametypelabel']}: {game['awaylabel']} {game['awayruns']}"
              f" - {game['homeruns']} {game['homelabel']}")
    rank = {r["team"]: r for r in standings(games, groups, outs=outs)["B"]}
    check(rank["Netherlands"]["rank"] == 4 and rank["Chinese Taipei"]["rank"] == 5,
          "1次R B組 オランダ4位・チャイニーズタイペイ5位（2勝3敗で並び、直接対決でオランダ）")
    place = {r["team"]: r for r in second_round(games, groups, outs)["placement"]}
    check(place["Netherlands"]["rank"] == 1 and place["Chinese Taipei"]["rank"] == 2,
          "順位決定R オランダ1位（大会7位）・チャイニーズタイペイ2位（大会8位）")


def _selftest_times_and_japan(check: Check) -> None:
    games, _ = _event("u23-wc-2026")
    print("\n== 2026年 時刻と日本戦")
    first = min(games, key=lambda g: g["start"])
    local, jst = local_dt(first), jst_dt(first)
    check(local.strftime("%m/%d %H:%M") == "11/06 10:30"
          and jst.strftime("%m/%d %H:%M") == "11/07 01:30",
          f"開幕戦 現地 {local:%m/%d %H:%M} → 日本 {jst:%m/%d %H:%M}（+15時間）")
    want = {"2026-11-06": ("Great Britain", "後攻"), "2026-11-07": ("Korea", "後攻"),
            "2026-11-08": ("Cuba", "先攻"), "2026-11-09": ("South Africa", "先攻"),
            "2026-11-10": ("Venezuela", "後攻")}
    for game in sorted(games, key=lambda g: g["start"]):
        view = japan_view(game)
        if view:
            day = local_day(game)
            check(want.get(day) == (view["opponent"], view["batting"]),
                  f"現地 {day} {view['opponent']} {view['batting']}（状態 {view['state']}）")
    _selftest_japan_results(check)


def _selftest_japan_results(check: Check) -> None:
    games, _ = _event("u23-wc-2024")
    for game in sorted(games, key=lambda g: g["start"]):
        view = japan_view(game)
        if view:
            away, home = runs(game)
            print(f"      2024 {local_day(game)} {view['mark']} {view['score']} "
                  f"{view['opponent']}（{view['batting']}）  元: {game['awaylabel']} {away}"
                  f" - {home} {game['homelabel']}")
    final = next(g for g in games if g["gametypelabel"] == "World Championship Final")
    view = japan_view(final)
    check(view["mark"] == "○" and view["score"] == "5-0" and view["batting"] == "先攻",
          "2024決勝（日本5-0プエルトリコ、日本が先攻）→ ○ 5-0 先攻")


def _fake(gid: str, away: str, away_runs: int, home: str, home_runs: int) -> dict:
    """照合用の7回の試合。後攻が勝った試合は7回裏をしなかった形にする。"""
    return {"id": gid, "gametypelabel": "Opening Round", "gamestatustext": "F",
            "awaylabel": away, "awayruns": away_runs, "homelabel": home,
            "homeruns": home_runs, "innings": 7, "runshome7": 0}


def _selftest_rules(check: Check) -> None:
    """規程 C11 の例（Scenario 2・3）と同じ形の同率を作って並べる。"""
    print("\n== 同率の決め方（WBSC規程 C11 の例）")
    # Scenario 2: A・B・C が1勝1敗で回り合う。B-A は A のサヨナラで6回1/3
    games = [{**_fake("s1", "B", 4, "A", 5), "runshome7": 1},
             _fake("s2", "C", 2, "A", 0), _fake("s3", "B", 6, "C", 2)]
    rows = standings(games, {"A": "X", "B": "X", "C": "X"}, outs={"s1": (18, 19)})["X"]
    order = [(r["team"], r["rank"]) for r in rows]
    print("      " + " / ".join(f"{r['rank']}位 {r['team']} {r['note']}" for r in rows))
    check(order == [("B", 1), ("A", 2), ("C", 3)],
          "Scenario 2: 当該対戦が1勝1敗ずつなら TQB で B・A・C（規程の答えと同じ）")
    # Scenario 3: C・D・E が2勝2敗で並び、当該対戦は C 2-0、E 1-1、D 0-2
    games = [_fake("t1", "D", 3, "C", 4), _fake("t2", "E", 5, "C", 8),
             _fake("t3", "D", 3, "E", 7), _fake("t4", "C", 1, "X", 2),
             _fake("t5", "C", 1, "Y", 2), _fake("t6", "X", 1, "E", 2),
             _fake("t7", "E", 1, "Y", 2), _fake("t8", "X", 1, "D", 2),
             _fake("t9", "Y", 1, "D", 2), _fake("t10", "X", 1, "Y", 2)]
    groups = {t: "X" for t in ("C", "D", "E", "X", "Y")}
    rows = standings(games, groups)["X"]
    print("      " + " / ".join(f"{r['rank']}位 {r['team']} {r['w']}-{r['l']}" for r in rows))
    check([r["team"] for r in rows[1:4]] == ["C", "E", "D"],
          "Scenario 3: 3チームが2勝2敗でも、当該対戦の勝敗で C・E・D（TQB は使わない）")


def _selftest_cancel(check: Check) -> None:
    """1次ラウンドの試合が中止（CANC）のまま日程に残ったとき。"""
    print("\n== 中止の試合が日程に残ったとき")
    games, folder = _event("u23-wc-2024")
    groups, outs = _groups(games), load_outs(folder / "raw")
    target = next(g for g in games if g["gametypelabel"] == "Opening Round")
    cancel = {"gamestatus": 4, "gamestatustext": "CANC", "awayruns": None, "homeruns": None}
    changed = [dict(g, **cancel) if g is target else g for g in games]
    check(second_round(changed, groups, outs)["ready"],
          f"{target['awaylabel']} @ {target['homelabel']} が中止でも、第2ラウンドの顔ぶれが決まる")
    opening = [g for g in changed if g["gametypelabel"] == "Opening Round"]
    check(second_round(opening, groups, outs)["ready"],
          "第2ラウンドの組み合わせが日程に載る前でも、計算で顔ぶれが決まる")
    check(not second_round([{**g, **cancel, "gamestatustext": "PPD"} if g is target else g
                            for g in games], groups, outs)["ready"],
          "延期（PPD）はあとで行われるので、まだ決まらない")
    tied = [_fake("1", "A", 5, "C", 1), _fake("2", "E", 5, "A", 1),
            _fake("3", "B", 5, "C", 1), _fake("4", "E", 5, "B", 1),
            {**_fake("5", "A", 0, "B", 0), **cancel}]
    rows = {r["team"]: r for r in standings(tied, {t: "X" for t in "ABCE"})["X"]}
    check(rows["A"]["rank"] == rows["B"]["rank"] == 2
          and rows["A"]["note"] == "同率（当該チーム同士の試合は中止）",
          f"同率の2チームの直接対決が中止: 同率のまま「{rows['A']['note']}」")


def _selftest_states(check: Check) -> None:
    print("\n== 試合の状態と引き分け")
    cases = [({"gamestatus": 0, "gamestatustext": ""}, "pre"),
             ({"gamestatus": 2, "gamestatustext": "F/7"}, "final"),
             ({"gamestatus": 3, "gamestatustext": "F"}, "final"),
             ({"gamestatus": 1, "gamestatustext": "T3"}, "live"),
             ({"gamestatus": 1, "gamestatustext": "Bot 5th"}, "live"),
             ({"gamestatus": 1, "gamestatustext": ""}, "live"),
             ({"gamestatus": 0, "gamestatustext": "PPD"}, "other"),
             ({"gamestatus": 0, "gamestatustext": "CANC"}, "other"),
             ({"gamestatus": 0, "gamestatustext": "Warm-up"}, "unknown"),
             ({"gamestatus": 1, "gamestatustext": "Protest"}, "unknown")]
    for game, want in cases:
        check(game_state(game) == want, f"{game} → {game_state(game)}")
    tie = {"id": 1, "gametypelabel": "Opening Round", "gamestatustext": "F/7",
           "homelabel": "Japan", "awaylabel": "Cuba", "homeruns": 3, "awayruns": 3,
           "innings": 7, "runshome7": 0}
    rows = {r["team"]: r for r in standings([tie], {"Japan": "B", "Cuba": "B"})["B"]}
    japan = rows["Japan"]
    check(japan["t"] == 1 and japan["l"] == 0 and japan["g"] == 1 and japan["pct"] == "-",
          f"F/7 の引き分け: 日本 {japan['w']}勝{japan['l']}敗{japan['t']}分（敗に数えない）")
    check(japan_view(tie)["mark"] == "△", f"引き分けの印 {japan_view(tie)['mark']}")
    check(batting_outs(tie)[:2] == (21, 21),
          "raw のない引き分けは、後攻も7回の裏を最後まで攻撃したと数える（21/21アウト）")
    pair = [{**_fake("t", "B", 3, "A", 3), "runshome7": 1},
            _fake("1", "A", 5, "C", 1), _fake("2", "E", 5, "A", 1),
            _fake("3", "B", 5, "C", 1), _fake("4", "E", 5, "B", 1)]
    rows = {r["team"]: r for r in standings(pair, {t: "X" for t in "ABCE"})["X"]}
    check(rows["A"]["rank"] == rows["B"]["rank"] and "推定" in rows["A"]["note"],
          f"並んだ2チームの当該対戦が raw のない引き分けなら、同率のまま注記に推定と出す"
          f"（{rows['A']['note']}）")
    empty = standings([], {"Cuba": "B", "Japan": "B"})["B"]
    check([r["team"] for r in empty] == ["Cuba", "Japan"] and empty[0]["rank"] is None,
          "試合前は順位なし・組み合わせ表の順（Cuba, Japan）")
    live = {"homelabel": "Japan", "awaylabel": "Cuba", "gamestatus": 1, "gamestatustext": "T3"}
    views = [japan_view({**live, "awayruns": a, "homeruns": h})["score"]
             for a, h in ((None, None), ("", ""), (None, 2), (0, 0), (1, 0))]
    check(views == ["-", "-", "-", "0-0", "0-1"],
          f"試合中で点数が届く前は「-」、記録された0は「0-0」（{' / '.join(views)}）")
    unknown = {**tie, "id": 2, "homeruns": None, "awayruns": None}
    rows = {r["team"]: r for r in standings([unknown], {"Japan": "B", "Cuba": "B"})["B"]}
    check(rows["Japan"]["g"] == 0 and japan_view(unknown)["mark"] == "",
          "終了でも点数のない試合は、0-0の引き分けと数えない（印も付けない）")
    days = {utc: local_day({"utc": utc}) for utc in
            ("2026-11-07T05:30:00+00:00", "2026-11-07T05:30:00Z", "2026-11-06T23:30:00-06:00")}
    check(set(days.values()) == {"2026-11-06"},
          "utc が Z・+00:00・-06:00 のどれでも現地の日付は 11/6（" + " / ".join(days.values()) + "）")


def _read_rows_settled(path: Path, games: list[dict], tries: int = 6) -> list[dict]:
    """pitching.csv を読む。取り直しの途中で読めない・途中までなら、数秒待って読み直す。"""
    ids = {str(g.get("id")) for g in games}
    for attempt in range(1, tries + 1):
        size = path.stat().st_size if path.exists() else -1
        try:
            rows = br.read_csv(path)
        except (OSError, UnicodeDecodeError, ValueError):
            rows = []
        settled = path.exists() and path.stat().st_size == size
        if rows and settled and None not in rows[-1].values() \
                and all(r.get("gameid") in ids for r in rows):
            return rows
        print(f"      pitching.csv が読めない・途中のため待って読み直し {attempt}/{tries}")
        time.sleep(3)
    return rows


def _selftest_pitchers(check: Check) -> None:
    games, folder = _event("u23-wc-2024")
    rows = _read_rows_settled(folder / "pitching.csv", games)
    print(f"\n== 2024年 プエルトリコの登板記録（pitching.csv {len(rows)}行、"
          f"date 列が空の行 {sum(1 for r in rows if not r.get('date'))}）")
    log = pitcher_log(rows, games, "Puerto Rico", today="2024-09-15")
    for pitcher in log[:4] + log[-2:]:
        rest = "当日登板済み" if pitcher["rest_days"] is None else f"中{pitcher['rest_days']}日"
        print(f"      {pitcher['name']}  最終 {pitcher['last_date']}  9/15に投げるなら {rest}"
              f"  計{pitcher['total_pitches']}球 先発{pitcher['gs_count']} {pitcher['ip_total']}回")
        for app in pitcher["apps"]:
            rest = "初登板" if app["rest"] is None else f"中{app['rest']}日"
            print(f"         {app['date']} vs {app['opponent']:<14} {'先発' if app['gs'] else '救援'}"
                  f" {app['ip']:>4}回 {app['pitches']:>3}球 {rest}")
    apps = [a for p in log for a in p["apps"]]
    by_id = {str(g["id"]): local_day(g) for g in games}
    check(bool(log) and all(a["date"] == by_id.get(a["gameid"]) for a in apps),
          f"{len(log)}人・{len(apps)}登板。日付はすべて games.json の start と一致")
    check(all(a["date"] and a["ip"] and a["opponent"] for a in apps)
          and sum(1 for a in apps if a["gs"]) == len({a["gameid"] for a in apps}),
          "全登板に日付・投球回・相手があり、先発は1試合に1人")


def _people(keys: list[str]) -> list[dict]:
    """batting.csv と pitching.csv から、選手ごとの名前・生年・国・大会を集める。"""
    seen: dict[tuple[str, str], dict] = {}
    for key in keys:
        for name in ("batting.csv", "pitching.csv"):
            for row in br.read_csv(br.DATA_ROOT / key / name):
                try:
                    info = ast.literal_eval(row.get("player") or "{}")
                except (ValueError, SyntaxError):
                    info = {}
                year = str((info or {}).get("dob") or "")[:4]
                seen.setdefault((key, str(row.get("playerid"))), {
                    "event": key, "id": str(row.get("playerid")), "name": _name(row),
                    "year": year, "team": row.get("team") or ""})
    return list(seen.values())


def _selftest_people(check: Check) -> None:
    print("\n== 大会をまたいだ選手の鍵")
    events = ["u23-wc-2022", "u23-wc-2024", "u23-americas-2025", "u23-euro-2025",
              "asian-championship-2025"]
    people = _people(events)
    keyed: dict[str, list[dict]] = {}
    for person in people:
        keyed.setdefault(person_key(person["name"], person["year"], person["team"]),
                         []).append(person)
    luis = [p for p in people if p["id"] in ("461801", "617447")]
    keys = {person_key(p["name"], p["year"], p["team"]) for p in luis}
    for person in luis:
        print(f"      {person['id']} {person['event']} {person['name']} {person['year']}"
              f" {person['team']} → {person_key(person['name'], person['year'], person['team'])}")
    check(len(luis) == 2 and len(keys) == 1, "HERNANDEZ ESTEVEZ, Luis Enrique の2つのIDが同じ鍵")
    check(person_key("Hernández  Estévez, LUIS enrique", 2002, "Puerto Rico") in keys,
          "大文字小文字・アクセント・余分な空白が違っても同じ鍵")
    check(person_key("KIM, Minsu", 2003, "South Korea") == person_key("KIM, Minsu", 2003, "Korea"),
          "South Korea と Korea は同じ国として扱う")
    merged = [v for v in keyed.values() if len({p["id"] for p in v}) > 1]
    same_event = [v for v in keyed.values()
                  if len({p["event"] for p in v}) < len({p["id"] for p in v})]
    print(f"      playerid {len(people)}件 → {len(keyed)}人（複数IDをまとめた人 {len(merged)}人）")
    for group in same_event:
        print("      同じ大会で同じ鍵: " + ", ".join(f"{p['id']} {p['name']}" for p in group))
    check(not same_event, "同じ大会の中で2つのIDが1つの鍵にまとまる例がない（別人の取り違えなし）")


def selftest() -> int:
    check = Check()
    for key in ("u23-wc-2022", "u23-wc-2024"):
        _selftest_event(key, check)
    _selftest_netherlands(check)
    _selftest_rules(check)
    _selftest_cancel(check)
    _selftest_times_and_japan(check)
    _selftest_states(check)
    _selftest_pitchers(check)
    _selftest_people(check)
    print(f"\n合った {check.ok}件 / 合わなかった {len(check.ng)}件")
    for text in check.ng:
        print(f"  NG {text}")
    return 1 if check.ng else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="過去大会の公式順位と照合する")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
