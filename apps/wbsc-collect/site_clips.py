#!/usr/bin/env python3
"""選手ごとの「カット集」（奪三振集・被安打集・被凡打集・牽制集、打者の安打集・凡打集・三振集）。

collect.py が書いた plays.csv（1球ごとの記録）から、打席の終わりの行（pa が 1 の行）と
牽制の行を拾い、選手ページに並べる一覧にする。映像は試合ごとのリンク（games.json の
gamevideo）しかないので、各行には「その試合の映像」へのリンクと、場面（回・カウント）を出す。

    import site_clips as sc
    clips = sc.pitcher_clips("u23-americas-2025", "637041")
    html = sc.clips_html(clips)

plays.csv について確かめたこと:
- result 列はどの大会も空。打席の結果は pa=1 の行の旗（h・double・strikeout・kl・groundout・
  flyout・sac・sf・gdp）と narrative の守備記号（"grounds out 6-3"、"F8"、"L6"、"FF3"）で読む。
- balls・strikes・outs はその球を投げる前の値（"Ball 1." の行が balls=0）。
  なので結果の行の balls-strikes が「結果の球の前のカウント」になる。
- 牽制は "Pickoff Attempt at 1st"（投手の牽制）、"Failed Pickoff Attempt"（2022年の書き方）、
  牽制アウトは "out at 1st PO13" の形（PO の次の数字 1 が投手）。"Catcher Pickoff Attempt" は
  捕手の送球なので投手の牽制集には入れない。

plays.csv がない大会（大会前の u23-wc-2026 など）は空の一覧を返す。例外は出さない。
"""

from __future__ import annotations

import html as html_mod
import json
import re
from pathlib import Path

import build_report as br

CURRENT = "u23-wc-2026"
PITCHER_KEYS = ("奪三振", "被安打", "被凡打", "牽制")
BATTER_KEYS = ("安打", "凡打", "三振")
LIMIT = 30   # 1つの項目に並べる行の上限（新しい順）。件数は全件を出す

POS = {"1": "投", "2": "捕", "3": "一", "4": "二", "5": "三", "6": "遊",
       "7": "左", "8": "中", "9": "右"}
BASE = {"1st": "一塁", "2nd": "二塁", "3rd": "三塁", "home": "本塁"}

# 国名の日本語（build_site.JA と同じ考え。build_site を読み込むと循環するのでここで持つ）
TEAM_JA = {team: label for label, team, _, _ in br.OPPONENTS}
TEAM_JA.update({
    "Japan": "日本", "South Korea": "韓国", "Korea": "韓国", "China": "中国",
    "Colombia": "コロンビア", "Netherlands": "オランダ", "Mexico": "メキシコ",
    "Germany": "ドイツ", "Aruba": "アルバ", "Austria": "オーストリア",
    "Bahamas": "バハマ", "Costa Rica": "コスタリカ", "France": "フランス",
    "Guatemala": "グアテマラ", "Honduras": "ホンジュラス", "Hong Kong, China": "香港",
    "Israel": "イスラエル", "Italy": "イタリア", "Pakistan": "パキスタン",
    "Palestine": "パレスチナ", "Philippines": "フィリピン",
    "United States Virgin Islands": "米領バージン諸島", "USA": "アメリカ",
    "United States": "アメリカ", "Czech Republic": "チェコ", "Dominican Republic": "ドミニカ共和国",
    "Spain": "スペイン", "Brazil": "ブラジル", "Canada": "カナダ",
})

# 打球の方向（narrative の "to left field" など）→ 安打の頭に付ける字
HIT_PLACE = (
    ("down left field line", "左翼線"), ("down lf line", "左翼線"),
    ("down right field line", "右翼線"), ("down rf line", "右翼線"),
    ("left center", "左中間"), ("right center", "右中間"),
    ("left field", "左"), ("center field", "中"), ("right field", "右"),
    ("up the middle", "中"), ("through the left side", "左"),
    ("through the right side", "右"),
    ("third base", "三"), ("shortstop", "遊"), ("second base", "二"),
    ("first base", "一"), ("pitcher", "投"), ("home plate", "捕"), ("catcher", "捕"),
)
OUTFIELD = {"左", "中", "右", "左中間", "右中間", "左翼線", "右翼線"}
FLY_PLACE = (("left center", "左中"), ("right center", "右中"), ("left field", "左"),
             ("center field", "中"), ("right field", "右"))

_cache: dict[tuple[str, str], dict] = {}


# ---------------------------------------------------------------- 読み込み


def _num(value) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _team_ja(team: str) -> str:
    return TEAM_JA.get(team, team or "")


def _event_label(event: str) -> str:
    if event == CURRENT:
        return "U-23W杯 2026"
    return br.EVENT_LABEL.get(event, event)


def _names(rows: list[dict]) -> dict[str, str]:
    """playerid → "SARDUY Dario" の形の名前（batting.csv・pitching.csv から）。"""
    names: dict[str, str] = {}
    for row in rows:
        pid = str(row.get("playerid") or "").strip()
        last = (row.get("lastname") or "").strip()
        first = (row.get("firstname") or "").strip()
        if pid and (last or first):
            names[pid] = f"{last} {first}".strip()
    return names


def _videos(path: Path) -> dict[str, str]:
    try:
        games = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if isinstance(games, dict):
        games = games.get("games") or list(games.values())
    videos = {}
    for game in games if isinstance(games, list) else []:
        if not isinstance(game, dict):
            continue
        link = str(game.get("gamevideo") or "").strip()
        if link.startswith(("http://", "https://")):
            videos[str(game.get("id"))] = link
    return videos


def _load(event: str) -> dict:
    """大会ごとに、打席の終わりの行と牽制の行を1度だけ作ってためる。"""
    root = Path(br.DATA_ROOT)
    key = (str(root), event)
    if key in _cache:
        return _cache[key]
    data = {"pa": [], "pickoff": []}
    try:
        plays = br.read_csv(root / event / "plays.csv")
        pitching = br.read_csv(root / event / "pitching.csv")
        names = _names(br.read_csv(root / event / "batting.csv"))
        names.update(_names(pitching))
        videos = _videos(root / event / "games.json")
        fixed = _box_pitchers(plays, pitching)
        for index, row in enumerate(plays):
            if index in fixed:
                row = dict(row, pitcherid=fixed[index])
            if _num(row.get("pa")) == 1:
                item = _pa_item(row, event, names, videos, index)
                if item:
                    data["pa"].append(item)
            pick = _pickoff(row.get("narrative") or "")
            if pick:
                item = _base_item(row, event, names, videos, index)
                item["kind"] = "牽制"
                item["result"] = pick
                data["pickoff"].append(item)
    except Exception:  # noqa: BLE001  データが崩れていてもサイトは作る（その大会のカット集は空）
        data = {"pa": [], "pickoff": []}
    _cache[key] = data
    return data


def _box_pitchers(plays: list[dict], pitching: list[dict]) -> dict[int, str]:
    """打席ごとの投手を、公式の投手成績（登板順 sub と対戦打者数 pitch_bf）で付け直す。

    plays.csv の pitcherid は、継投を数打者遅れて記録していることがある（北中米予選2025で
    投手成績と三振数が合わない投手がいた）。試合の表・裏ごとに、打席の終わりの行の数と
    守る側の投手の対戦打者数の合計が一致するときだけ、登板順に打者数ずつ割り当てる。
    打席の途中の行（牽制など）は、その打席を終えた投手に合わせる。
    戻り値は plays の行番号 → 付け直した pitcherid（変えない行は入れない）。
    """
    box: dict[tuple[str, str], list[dict]] = {}
    for row in pitching:
        box.setdefault((str(row.get("gameid")), row.get("team") or ""), []).append(row)
    halves: dict[tuple[str, str], list[int]] = {}
    for index, row in enumerate(plays):
        halves.setdefault((str(row.get("gameid")), str(row.get("half") or "").lower()), []).append(index)
    fixed: dict[int, str] = {}
    for (gameid, half), indexes in halves.items():
        if not indexes:
            continue
        first = plays[indexes[0]]
        fielding = first.get("home_team") if half.startswith("t") else first.get("away_team")
        pitchers = sorted(box.get((gameid, fielding or ""), []), key=lambda r: _num(r.get("sub")))
        ends = [i for i in indexes if _num(plays[i].get("pa")) == 1]
        order = [str(r.get("playerid")) for r in pitchers for _ in range(_num(r.get("pitch_bf")))]
        if not ends or len(order) != len(ends):
            continue
        by_end = dict(zip(ends, order))
        current = None
        for i in reversed(indexes):   # 後ろから見て、途中の行に次の打席の投手を付ける
            if i in by_end:
                current = by_end[i]
            if current and current != str(plays[i].get("pitcherid") or "").strip():
                fixed[i] = current
    return fixed


def _base_item(row: dict, event: str, names: dict, videos: dict, index: int) -> dict:
    batting = row.get("batting_team") or ""
    away, home = row.get("away_team") or "", row.get("home_team") or ""
    fielding = home if batting == away else away
    half = str(row.get("half") or "").lower()
    inning = _num(row.get("inning"))
    gameid = str(row.get("gameid") or "")
    batter_id = str(row.get("batterid") or "").strip()
    pitcher_id = str(row.get("pitcherid") or "").strip()
    return {
        "date": str(row.get("date") or "")[:10],
        "gameid": gameid,
        "event": event,
        "event_label": _event_label(event),
        "batting_team": batting,
        "fielding_team": fielding,
        "inning": f"{inning}回{'表' if half.startswith('t') else '裏'}" if inning else "",
        "count": f"{_num(row.get('balls'))}-{_num(row.get('strikes'))}",
        "outs": _num(row.get("outs")),
        "batter_id": batter_id,
        "pitcher_id": pitcher_id,
        "batter": names.get(batter_id) or _narrative_name(row.get("narrative") or ""),
        "pitcher": names.get(pitcher_id, ""),
        "video": videos.get(gameid, ""),
        "utc": str(row.get("utctimestamp") or ""),
        "order": index,
    }


def _narrative_name(text: str) -> str:
    match = re.match(r"(.+?)\s+(singles|doubles|triples|homers|grounds|flies|lines|pops|strikes|"
                     r"walks|reaches|out on|hits into|Hit By)", text)
    return match.group(1).strip() if match else ""


# ---------------------------------------------------------------- 打席の結果を読む


def _place(text: str, table=HIT_PLACE) -> str:
    low = text.lower()
    for word, label in table:
        if word in low:
            return label
    return ""


def _after_verb(text: str, verbs: str) -> str:
    """narrative の動詞から次の文までの部分（"Jr." のような名前の点で切らないため）。"""
    match = re.search(r"\b(?:" + verbs + r")\b(.*?)(?:\.\s|\.$|$)", text)
    return match.group(0) if match else text.split(". ")[0]


def _hit_text(row: dict, text: str) -> str:
    first = _after_verb(text, "singles|doubles|triples|homers")
    place = _place(first)
    if _num(row.get("homerun")):
        kind = "本塁打"
    elif _num(row.get("triple")):
        kind = "三塁打"
    elif _num(row.get("double")):
        kind = "二塁打"
    else:
        if place in ("左", "中", "右"):
            return f"{place}前安打"
        if place in OUTFIELD:
            return f"{place}安打"
        if place == "捕":
            return "捕前安打"
        if place:
            return f"{place}内野安打"
        return "安打"
    return f"{place}{kind}" if place else kind


def _strikeout_text(row: dict, text: str) -> str:
    low = text.lower()
    if "reaches on" in low and "strikeout" in low:
        if "wild pitch" in low:
            return "振り逃げ（暴投）"
        if "passed ball" in low:
            return "振り逃げ（捕逸）"
        return "振り逃げ"
    return "見逃し三振" if _num(row.get("kl")) else "空振り三振"


def _out_text(row: dict, text: str) -> tuple[str, bool]:
    """凡打の日本語と、犠打・犠飛か。凡打でなければ ("", False)。"""
    low = text.lower()
    first = _after_verb(text, "flies|lines|pops|grounds|out on")
    dp = "併殺" if ("double play" in low or _num(row.get("gdp"))) else ""
    if "triple play" in low:
        dp = "三重殺"
    # 犠飛
    if _num(row.get("sf")) or "sacrifice fly" in low:
        match = re.search(r"\bSF\s?(\d)", text)
        pos = POS.get(match.group(1), "") if match else _place(first, FLY_PLACE)
        return f"{pos}犠飛", True
    # 犠打（バント）
    if _num(row.get("sac")) or "sacrifice hit" in low:
        match = re.search(r"sacrifice hit\s+(\d)", text)
        pos = POS.get(match.group(1), "") if match else ""
        if "fielders choice" in low:
            return f"{pos}犠打（野選）", True
        return f"{pos}犠打", True
    # 併殺打
    match = re.search(r"\bGDP\s+(\d)", text)
    if "hits into a double play" in low or match:
        pos = POS.get(match.group(1), "") if match else ""
        return f"{pos}ゴロ併殺打", False
    # ゴロ
    if _num(row.get("groundout")) or "grounds out" in low:
        match = re.search(r"grounds out\.?\s*(?:Bunt\s*)?(\d)", text)
        pos = POS.get(match.group(1), "") if match else ""
        bunt = "（バント）" if "bunt" in low else ""
        return f"{pos}ゴロ{bunt}{'・' + dp if dp else ''}", False
    # フライ・ライナー・ファウルフライ
    if _num(row.get("flyout")) or re.search(r"\b(flies|lines|pops) out", low):
        match = re.search(r"\b(FF|F|P|L)\s?(\d)\b", text)
        if match:
            pos = POS.get(match.group(2), "")
            kind = {"FF": "邪飛", "F": "飛", "P": "飛", "L": "直"}[match.group(1)]
        else:
            pos = _place(first, FLY_PLACE)
            kind = "邪飛" if "foul" in first.lower() else ("直" if "lines" in low else "飛")
        return f"{pos}{kind}{'・' + dp if dp else ''}", False
    # 野手選択で走者がアウト（打者は一塁に残るが、打球でアウトが1つ取れている）
    if "fielders choice" in low and " out at " in low:
        match = re.search(r"out at \w+\s+(\d)", text)
        pos = POS.get(match.group(1), "") if match else ""
        return f"{pos}ゴロ（走者アウト）" if pos else "野選（走者アウト）", False
    return "", False


def _pa_item(row: dict, event: str, names: dict, videos: dict, index: int) -> dict | None:
    text = re.sub(r"<br>.*", "", row.get("narrative") or "")
    item = _base_item(row, event, names, videos, index)
    item["sac"] = False
    if _num(row.get("strikeout")):
        item["kind"] = "三振"
        item["result"] = _strikeout_text(row, text)
    elif _num(row.get("h")):
        item["kind"] = "安打"
        item["result"] = _hit_text(row, text)
    else:
        result, sac = _out_text(row, text)
        if not result:
            return None   # 四死球・失策出塁・打撃妨害などはどの集にも入れない
        item["kind"] = "凡打"
        item["result"] = result
        item["sac"] = sac
    if not item["result"]:
        item["result"] = _short(text)
    return item


def _pickoff(text: str) -> str:
    """牽制の行なら日本語の短い説明、そうでなければ ""。捕手の牽制は入れない。"""
    match = re.search(r"out at (1st|2nd|3rd)\s+PO1\d", text)
    if match:
        return f"{BASE[match.group(1)]}で牽制アウト（{_runner(text, match.group(1))}）"
    match = re.search(r"picked off, out at (1st|2nd|3rd)\s+CS\s+1", text)
    if match:
        return f"牽制から{BASE[match.group(1)]}でアウト（{_runner(text, match.group(1))}）"
    if text.startswith("Catcher"):
        return ""
    match = re.match(r"(Failed )?Pickoff Attempt(?: at (1st|2nd|3rd))?", text)
    if match:
        return f"{BASE[match.group(2)]}へ牽制" if match.group(2) else "牽制"
    return ""


def _runner(text: str, base: str) -> str:
    """牽制アウトになった走者の名前（narrative から）。"""
    match = re.search(r"([A-ZÁÉÍÓÚÑÜ][^.]*?)\s+(?:picked off, )?out at " + base, text)
    if not match:
        return "走者"
    name = re.sub(r"^.*?(Pickoff Attempt at (?:1st|2nd|3rd)|batting)\s*", "", match.group(1))
    name = re.sub(r"^With .*? batting\s+", "", name).strip()
    return name or "走者"


def _short(text: str, size: int = 40) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= size else text[: size - 1] + "…"


# ---------------------------------------------------------------- 公開する関数


def _ids(value) -> set[str]:
    if isinstance(value, (list, tuple, set, frozenset)):
        return {str(v).strip() for v in value if str(v).strip()}
    return {str(value or "").strip()} - {""}


def _public(item: dict, side: str) -> dict:
    """呼び出し側に渡す形。side が "pitcher" なら相手は打撃側の国。"""
    opponent = item["batting_team"] if side == "pitcher" else item["fielding_team"]
    return {
        "date": item["date"], "gameid": item["gameid"], "event": item["event"],
        "event_label": item["event_label"], "opponent": _team_ja(opponent),
        "inning": item["inning"], "count": item["count"], "outs": item["outs"],
        "result": item["result"], "sac": item.get("sac", False),
        "batter": item["batter"], "pitcher": item["pitcher"],
        "video": item["video"], "utc": item["utc"], "order": item["order"],
    }


def _newest_first(rows: list[dict]) -> list[dict]:
    # 日付（現地）を先に見る。utc は同じ日の中の順番に使う（ダミーの日程では年がずれるため）
    return sorted(rows, key=lambda r: (r["date"], r["utc"], r["order"]), reverse=True)


def pitcher_clips(event: str, pitcher_id) -> dict[str, list[dict]]:
    """投手のカット集。鍵は "奪三振" "被安打" "被凡打" "牽制"（この順）。各一覧は新しい順。"""
    out: dict[str, list[dict]] = {key: [] for key in PITCHER_KEYS}
    ids = _ids(pitcher_id)
    if not ids:
        return out
    data = _load(event)
    kind_key = {"三振": "奪三振", "安打": "被安打", "凡打": "被凡打"}
    for item in data["pa"]:
        if item["pitcher_id"] in ids:
            out[kind_key[item["kind"]]].append(_public(item, "pitcher"))
    for item in data["pickoff"]:
        if item["pitcher_id"] in ids:
            out["牽制"].append(_public(item, "pitcher"))
    return {key: _newest_first(rows) for key, rows in out.items()}


def batter_clips(event: str, batter_id) -> dict[str, list[dict]]:
    """打者のカット集。鍵は "安打" "凡打" "三振"（この順）。各一覧は新しい順。"""
    out: dict[str, list[dict]] = {key: [] for key in BATTER_KEYS}
    ids = _ids(batter_id)
    if not ids:
        return out
    for item in _load(event)["pa"]:
        if item["batter_id"] in ids:
            out[item["kind"]].append(_public(item, "batter"))
    return {key: _newest_first(rows) for key, rows in out.items()}


def merge_clips(*parts: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """複数の大会のカット集を1つにまとめる（鍵の順は最初に来たもの、中身は新しい順）。"""
    merged: dict[str, list[dict]] = {}
    for part in parts:
        for key, rows in (part or {}).items():
            merged.setdefault(key, []).extend(rows)
    return {key: _newest_first(rows) for key, rows in merged.items()}


def _date_text(date: str) -> str:
    match = re.match(r"(\d{4})-(\d{2})-(\d{2})", date or "")
    if not match:
        return date or ""
    return f"{match.group(1)}/{int(match.group(2))}/{int(match.group(3))}"


def _row_html(row: dict, key: str) -> str:
    esc = html_mod.escape
    opponent = f" vs {row['opponent']}" if row.get("opponent") else ""
    when = f"{_date_text(row['date'])} {row['event_label']}{opponent} {row['inning']}".strip()
    # 投手の集なら相手は打者、打者の集なら相手は投手
    person = row["pitcher"] if key in BATTER_KEYS else row["batter"]
    who = f"（{person}）" if person else ""
    if key == "牽制":
        what = f"{row['count']}・{row['outs']}死で{row['result']}"
    else:
        what = f"{row['count']} から{row['result']}{who}"
    play = ""
    if row.get("video"):
        play = (f'<a class="play" href="{esc(row["video"], quote=True)}" target="_blank" '
                f'rel="noreferrer">▶ 試合の映像</a>')
    return (f'<li><span class="when">{esc(when)}</span>'
            f'<span class="what">{esc(what)}</span>{play}</li>')


def clips_html(clips: dict[str, list[dict]]) -> str:
    """カット集のHTML。最初の、記録のある項目だけを開いておく。件数0の項目は「記録なし」。"""
    parts = []
    opened = False
    for key, rows in (clips or {}).items():
        rows = rows or []
        is_open = bool(rows) and not opened
        opened = opened or is_open
        head = (f'<summary><b>{html_mod.escape(key)}集</b>'
                f'<span class="cnt">{len(rows)}</span></summary>')
        if rows:
            body = "".join(_row_html(row, key) for row in rows[:LIMIT])
            note = ""
            if len(rows) > LIMIT:
                note = f'<p class="empty">新しい順に{LIMIT}件を表示しています（全{len(rows)}件）。</p>'
            inner = f'<ol class="clip-list">{body}</ol>{note}'
        else:
            inner = '<p class="empty">記録なし</p>'
        parts.append(f'<details class="clip"{" open" if is_open else ""}>{head}{inner}</details>')
    return f'<div class="clips">{"".join(parts)}</div>'
