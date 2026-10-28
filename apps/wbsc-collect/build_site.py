#!/usr/bin/env python3
"""U-23W杯のスタッフ共有サイトを組み立てる。

collect.py が集めたデータと、手で整えた今大会の情報（07_出場選手情報/サイト用）から、
トップ・日程と結果・相手国・日本代表・大会方式・選手のページを静的なHTMLとして
書き出す。サイトは「リンクを知っている人だけが開ける」形で、推測できない長い
フォルダ名（合言葉）の下にすべてのページを置く。入口のURLを開いても白紙しか出ない。
検索エンジンには載せない。

    python3 build_site.py                    # 既定の dist に書き出す
    python3 build_site.py --out DIR          # 書き出し先を変える（update_site.sh は dist.new）
    python3 build_site.py --data-root DIR    # 収集データの場所を変える（試し用のダミーなど）
    python3 build_site.py --new-token        # 合言葉を作り直す（リンクが漏れたとき）

手で整えたデータのうち、次の3つはあれば使い、なくても動く。
    サイト用/同一人物.csv   team,keep_playerid,merge_playerid,evidence
                            merge_playerid の選手を keep_playerid と同じ人として1つの選手ページに
                            まとめる（名前と生年で作る鍵 site_logic.person_key より優先）
    サイト用/名簿_読み.csv  team,roster_name,reading,club_ja,note
                            相手国ページの今大会の名簿と注目選手に、読み（カタカナ）と所属の日本語名を添える
    サイト用/背番号.csv     team,roster_name,number,source,checked,note
                            相手国ページの今大会の名簿に背番号を出す（source は「日本遠征の名簿」など、
                            どの名簿の番号か。表の上の注記に出す）

合言葉はリポジトリに入らない private/u23-site-token に保存する。
URL はフォルダ形式（team/cuba/ → team/cuba/index.html）。Cloudflare Pages は .html を
拡張子なしへ308で転送するので、その往復をなくすため。
ページには作った時刻を入れない。時刻と版は status.js にまとめ（site_offline.py）、
中身の変わったページだけが上がるようにする。
画面の動き（並べ替え・次の日本戦・今日の試合・投手と野手の切り替えなど）は site.js にまとめる。
別の部品（どれも読めなければ、その部分だけ今の形で書き出す）:
    site_theme.py   見た目（CSS の文字列）
    site_clips.py   選手ページの映像のカット集（奪三振集・被安打集など）
    site_japan.py   日本代表のページ（japan/・japan/pitching/・japan/p/<背番号>/）
    site_video.py   台湾の日本遠征の打席ごとの映像（team/chinese-taipei/v/<背番号>/ と media/）
URL に ?now=2026-11-08T12:00:00-06:00 を付けると「今」を差し替えて試せる。
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import html
import json
import os
import re
import secrets
import shutil
import string
import subprocess
import sys
import time
import unicodedata
import urllib.parse
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import build_report as br
import collect
import site_logic as sl
import site_offline as so

try:  # 映像のカット集（別の部品）。なければ選手ページに出さないだけ
    import site_clips
except Exception as _error:
    print(f"注意: site_clips.py が読めないので、カット集は出しません（{_error}）", file=sys.stderr)
    site_clips = None
try:  # 台湾の日本遠征の映像ページ（別の部品）。なければ映像を出さないだけ
    import site_video
except Exception as _error:
    print(f"注意: site_video.py が読めないので、映像ページは出しません（{_error}）", file=sys.stderr)
    site_video = None
try:  # 日本代表のページ（別の部品）。なければ今の japan_page を使う
    import site_japan
except Exception as _error:
    print(f"注意: site_japan.py が読めないので、今の日本代表ページを使います（{_error}）", file=sys.stderr)
    site_japan = None

ROOT = Path.home() / "野球" / "U23ワールドカップ2026"
OUT = ROOT / "07_サイト" / "dist"
INFO = ROOT / "07_出場選手情報"
SITE_INFO = INFO / "サイト用"
REPO = Path(__file__).resolve().parents[2]
TOKEN_FILE = REPO / "private" / "u23-site-token"

CURRENT = "u23-wc-2026"
EVENT_LABEL = {CURRENT: "U-23W杯 2026（本大会）", **br.EVENT_LABEL}
WBSC_DOMAIN, WBSC_SLUG, _ = collect.EVENTS[CURRENT]

# 相手国。WBSCの英語表記 → (日本語名, 組, 見る大会)
OPP = {team: (label, group, sources) for label, team, group, sources in br.OPPONENTS}
JA = {team: label for label, team, _, _ in br.OPPONENTS}
JA.update({"Japan": "日本", "South Korea": "韓国", "China": "中国", "Colombia": "コロンビア",
           "Netherlands": "オランダ", "Mexico": "メキシコ", "Germany": "ドイツ"})

# 公式日程（01_大会情報/WBSC公式日程_2026.png）の GROUP A・B の欄の順。
# 試合前の順位表はこの順に並ぶ
GROUPS = {
    "Australia": "A", "Czechia": "A", "Nicaragua": "A", "Panama": "A",
    "Puerto Rico": "A", "Chinese Taipei": "A",
    "Cuba": "B", "Great Britain": "B", "Japan": "B", "Korea": "B",
    "South Africa": "B", "Venezuela": "B",
}
# 今大会_発表名簿.csv の team 列の略号
TEAM_CODE = {"Cuba": "CUB", "Korea": "KOR", "Venezuela": "VEN", "Great Britain": "GBR",
             "South Africa": "RSA", "Chinese Taipei": "TPE", "Puerto Rico": "PUR",
             "Panama": "PAN", "Australia": "AUS", "Nicaragua": "NCA", "Czechia": "CZE"}
CODE_TEAM = {code: team for team, code in TEAM_CODE.items()}
# まだ決まっていない対戦相手の表記（日程の TBD など）
PLACEHOLDER = {"", "TBD", "TBA"}
TOWN = {"Managua": "マナグア", "Masaya": "マサヤ", "León": "レオン", "Leon": "レオン"}
# gametypelabel に含まれる語 → 札の文字とクラス
ROUND_TAG = (("Opening Round", "1次R", "op"), ("Super Round", "SR", "sup"),
             ("Placement Round", "順位決定", "pl"), ("Bronze", "3位決定", "md"),
             ("Final", "決勝", "md"))
POS_JA = {"P": "投手", "C": "捕手", "IF": "内野手", "OF": "外野手", "UTL": "ユーティリティ"}
POS_ORDER = ("投手", "捕手", "内野手", "外野手")
HAND = {"R": "右", "L": "左", "S": "両"}

# 2026年大会の出場資格。2003年1月1日以降の生まれ
ELIGIBLE_FROM = 2003
# この文字数までの名前は縮めない
SHORT_ENOUGH = 14
BAT = ["名前"] + br.BAT_COLUMNS[1:]
PIT = ["名前"] + br.PIT_COLUMNS[1:]
# 並べ替えの1回目を低い順にする列（投手の成績で、少ないほどよいもの）
PIT_LOW = {"防御率", "与四球率", "被安打", "失点", "自責点", "四球", "被本塁打", "暴投"}
TEXT_COLUMNS = {"名前", "守備", "選手", "所属", "役割"}

NAV = (("japan", "japan/", "日本"), ("teams", "teams/", "相手国"),
       ("schedule", "schedule/", "日程"), ("format", "format/", "大会方式"))
# 最初に開いたときに端末へ先に保存するページ（相手国11ページはこのあとに足す）
CORE = ("", "schedule/", "teams/", "japan/", "japan/pitching/", "format/")

# 公式日程のスーパーラウンドと順位決定ラウンド。(現地の日付, ((先攻, 後攻), ...))。
# 同じ順位どうしの先攻・後攻は大会前の技術会議のコイントスで決まる（公式日程の注記）
SECOND_ROUND = (
    ("2026-11-12", (("A6", "B6"), ("A3", "B3"), ("A5", "B5"),
                    ("A4", "B4"), ("A1", "B1"), ("A2", "B2"))),
    ("2026-11-13", (("A6", "B4"), ("B6", "A5"), ("B5", "A4"),
                    ("A2", "B1"), ("B3", "A1"), ("A3", "B2"))),
    ("2026-11-14", (("A5", "B4"), ("B6", "A4"), ("A6", "B5"),
                    ("B2", "A1"), ("B3", "A2"), ("A3", "B1"))),
)
OFFICIAL_JAPAN = "https://www.japan-baseball.jp/jp/news/press/20261006_1.html"
WBSC_RULES = ("https://static.wbsc.org/uploads/federations/0/cms/documents/"
              "d3d36a7c-4a8a-1cca-adc1-d4edff1efc30.pdf")
FOOTER = "WBSCの大会サイトの記録と公表された情報から作成・関係者限り。リンクを外に回さないでください。"
# 大会方式のページの文。公式日程（01_大会情報/WBSC公式日程_2026.png）とその注記から
FORMAT_FLOW = (
    '<ol class="flow">'
    "<li>12チームが6チームずつ2組に分かれ、1次ラウンドを総当たりで戦います"
    "（日本時間 11/7〜11・現地 11/6〜10、各チーム5試合）。</li>"
    "<li>各組の上位3チームがスーパーラウンド、下位3チームが順位決定ラウンドに進みます"
    "（現地 11/12〜14、各チーム3試合）。相手はもう一方の組の3チームです。</li>"
    "<li>現地 11/11 は予備日です。</li>"
    "<li>現地 11/15 に3位決定戦（スーパーラウンド3位 対 4位）と決勝（1位 対 2位）。"
    "会場はどちらも Nacional Soberania（マナグア）です。時刻は公式日程では未定。</li></ol>"
)
FORMAT_CARRY = (
    "<p>スーパーラウンドでは、1次ラウンドで進出3チーム同士が戦った2試合の結果を持ち越し、"
    "スーパーラウンドの3試合と合わせた5試合で順位を決めます。決勝と3位決定戦に進むのは、"
    "この順位の上位4チームです。どの試合が持ち越しになるかは、1次ラウンドが終わるまで"
    "決まりません。順位決定ラウンドも同じやり方です（WBSCの公式日程の注記）。</p>"
)
WEEK = "月火水木金土日"
# ページに出さない作業用のファイル名と、代わりに出す言い方（public() で使う）
FILE_REF = re.compile(r"（([^（）\s]+\.(?:csv|json))）")
FILE_LABEL = {"名簿照合.csv": "名簿の「過去の記録」欄"}
# 「（10月15日確認）」のように、注記の中に確認日が書いてあるか
CHECKED_IN_TEXT = re.compile(r"\d+月\d+日確認")
# build_site.py が書き出したフォルダの目印。--out はこれがあるフォルダだけを作り直す
MARK = ".u23-site"
# 外部リンクにしてよいURLの形（http か https で、空白や制御文字を含まない）
WEB_URL = re.compile(r"https?://[^\x00-\x20\x7f]+", re.IGNORECASE)
# リンクにしなかったURL（同じ注意を何度も出さないため）
SKIPPED_URLS: set[str] = set()


# ---------------------------------------------------------------- 小さな道具


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""))


def public(text) -> str:
    """相手国.json の文を、ページに出す形にする（エスケープ込み）。

    手元の作業用のファイル名（「（名簿照合.csv）」など）は読む人に分からないので、
    ページの上の言い方に置き換えるか、外す。
    """
    def swap(match) -> str:
        label = FILE_LABEL.get(match.group(1))
        return f"（{label}）" if label else ""
    return esc(FILE_REF.sub(swap, str(text if text is not None else "")))


def name_key(text) -> str:
    """名前の照合用。大文字小文字・アクセント・空白の違いを無視する（ハングルもそろう）。"""
    decomposed = unicodedata.normalize("NFKD", str(text or ""))
    plain = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(plain.casefold().split())


def team_code(value) -> str:
    """「KOR」「Korea」「韓国」のどれでも、今大会_発表名簿.csv の略号にする。分からなければ空。"""
    text = str(value or "").strip()
    if text.upper() in CODE_TEAM:
        return text.upper()
    if text in TEAM_CODE:
        return TEAM_CODE[text]
    named = {label: team for team, label in JA.items()}
    return TEAM_CODE.get(named.get(text, ""), "")


def undecided(team) -> bool:
    """日程でまだ決まっていない相手（TBD など）か。"""
    return str(team or "").strip().upper() in PLACEHOLDER


def team_name(team) -> str:
    """国名の日本語。まだ決まっていない相手は「未定」。"""
    return "未定" if undecided(team) else ja(team)


def slug(team: str) -> str:
    return team.replace(" ", "-").lower()


def ja(team) -> str:
    return JA.get(team, team or "")


def md(moment) -> str:
    """日付を「11/7(土)」にする。"""
    return f"{moment.month}/{moment.day}({WEEK[moment.weekday()]})"


def iso_md(text, year: bool = False) -> str:
    """'2026-10-15' を '10/15'（year=True なら '2024/9/12'）にする。読めなければそのまま。"""
    try:
        day = datetime.strptime(str(text or "")[:10], "%Y-%m-%d")
    except ValueError:
        return esc(text or "-")
    return f"{day.year}/{day.month}/{day.day}" if year else f"{day.month}/{day.day}"


def iso_day(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%d")


def web_url(url) -> str:
    """外部リンクにしてよいURL（http・https）ならそのまま、ほかは空文字を返す。

    javascript: や data: のURL、相対パスや作業用のファイル名をリンクにしないため。
    はじいたURLは、組み立てのときに1回だけ「注意:」と出す。
    """
    text = str(url if url is not None else "").strip()
    if WEB_URL.fullmatch(text):
        return text
    if text and text not in SKIPPED_URLS:
        SKIPPED_URLS.add(text)
        print(f"注意: http・https ではないURLはリンクにしません: {text[:80]!r}", file=sys.stderr)
    return ""


def ext(url, text) -> str:
    """外部へのリンク。参照元（合言葉入りのURL）は送らない。http・https でなければ何も出さない。"""
    href = web_url(url)
    if not href:
        return ""
    return (f'<a class="ext" href="{esc(href)}" target="_blank" rel="noreferrer noopener">'
            f"{esc(text)}</a>")


def sources(text, label: str = "出典") -> str:
    """「URL | URL」の形の出典を、外部リンクに並べる。http・https でないものは飛ばす。"""
    urls = [u for u in (web_url(x) for x in str(text or "").split("|")) if u]
    if len(urls) <= 1:
        return ext(urls[0], label) if urls else ""
    return "・".join(ext(u, f"{label}{i}") for i, u in enumerate(urls, 1))


def short_name(full: str) -> str:
    """「REMON TEJEDA, Yeison」を「REMON TEJEDA, Y.」に縮める（名を頭文字に）。

    「KIM, Jongun」のように短い名前は縮めない。韓国の選手などは頭文字にすると
    同じ表に同じ表記が並んでしまうため。
    """
    last, sep, first = str(full or "").partition(", ")
    if not sep or not first.strip() or len(full) <= SHORT_ENOUGH:
        return full
    return f"{last}, " + "".join(word[0] + "." for word in first.split())


def mark_html(mark) -> str:
    css = {"○": "w", "●": "l", "△": "t"}.get(mark or "")
    return f'<span class="mk {css}">{mark}</span>' if css else ""


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def load_token(renew: bool) -> str:
    if TOKEN_FILE.exists() and not renew:
        return TOKEN_FILE.read_text().strip()
    alphabet = string.ascii_lowercase + string.digits
    token = "".join(secrets.choice(alphabet) for _ in range(24))
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(token + "\n")
    return token


def player_info(row: dict) -> dict:
    """batting.csv の player 列に入っている辞書から、生年や投打を取る。"""
    try:
        info = ast.literal_eval(row.get("player") or "{}")
    except (ValueError, SyntaxError):
        info = {}
    return info if isinstance(info, dict) else {}


def birth_year(info: dict):
    dob = str(info.get("dob") or "")[:4]
    return int(dob) if dob.isdigit() else None


def eligible(year) -> bool:
    """今大会に出られるか。生年が分からない選手は出られるものとして扱う。"""
    return year is None or year >= ELIGIBLE_FROM


# ---------------------------------------------------------------- 読み込みと集計


def load() -> dict:
    """収集データと、手で整えた今大会の情報を読む。"""
    events = {
        event: {kind: br.read_csv(br.DATA_ROOT / event / f"{kind}.csv")
                for kind in ("batting", "pitching", "plays")}
        for event in EVENT_LABEL
    }
    games = read_json(br.DATA_ROOT / CURRENT / "games.json", [])
    if not isinstance(games, list) or not games:
        raise SystemExit(f"{br.DATA_ROOT / CURRENT / 'games.json'} が読めないか、試合が0件です。"
                         "空の日程を書き出さないよう止めました。取り込みを確かめてください。")
    games.sort(key=lambda g: (str(g.get("start") or ""), int(br.number(g.get("gamenumber")))))
    # 今大会の成績は、終わった試合の分だけを数える。collect.py は試合中の試合の行も CSV に
    # 書くので、そのままだと途中の成績が合計や登板記録に混ざり、表の列（終了試合だけ）と合わない
    finished = {str(g.get("id")) for g in games if sl.is_final(g)}
    events[CURRENT] = {kind: [r for r in rows if str(r.get("gameid")) in finished]
                       for kind, rows in events[CURRENT].items()}
    opponents = read_json(SITE_INFO / "相手国.json", {})
    return {
        "events": events, "games": games, "info": player_infos(events),
        "opp": opponents.get("teams") or {}, "checked": opponents.get("checked") or "",
        "roster": br.read_csv(INFO / "今大会_発表名簿.csv"),
        "match": br.read_csv(SITE_INFO / "名簿照合.csv"),
        "japan": br.read_csv(SITE_INFO / "日本代表_公式発表.csv"),
        "same": br.read_csv(SITE_INFO / "同一人物.csv"),
        "reading": readings(br.read_csv(SITE_INFO / "名簿_読み.csv")),
        "numbers": numbers(br.read_csv(SITE_INFO / "背番号.csv")),
        "outs": sl.load_outs(br.DATA_ROOT / CURRENT / "raw"),
        "tables": {}, "people": {}, "pid_key": {},
    }


def readings(rows: list[dict]) -> dict[tuple[str, str], dict]:
    """名簿_読み.csv を {(略号, 名前の照合用の形): 行} にする。ファイルがなければ空。"""
    out: dict[tuple[str, str], dict] = {}
    for row in rows:
        code, name = team_code(row.get("team")), name_key(row.get("roster_name"))
        if code and name and ((row.get("reading") or "").strip() or (row.get("club_ja") or "").strip()):
            out.setdefault((code, name), row)
    return out


def reading_of(d: dict, code: str, name) -> dict:
    return d["reading"].get((code, name_key(name))) or {}


def numbers(rows: list[dict]) -> dict[tuple[str, str], dict]:
    """背番号.csv を {(略号, 名前の照合用の形): 行} にする。番号が空の行は使わない。ファイルがなければ空。"""
    out: dict[tuple[str, str], dict] = {}
    for row in rows:
        code, name = team_code(row.get("team")), name_key(row.get("roster_name"))
        if code and name and (row.get("number") or "").strip():
            out.setdefault((code, name), row)
    return out


def number_hint(found: list[dict], total: int) -> str:
    """名簿の表の上に出す、背番号がどの名簿の番号かの1文。"""
    if not found:
        return ""
    source = (found[0].get("source") or "").strip() or "手元の名簿"
    checked = (found[0].get("checked") or "").strip()
    day = f"（{iso_md(checked)}確認）" if checked else ""
    blank = "載っていない選手は空欄です。" if len(found) < total else ""
    return f"背番号は{esc(source)}の番号です{day}。大会の登録で変わることがあります。{blank}"


def player_infos(events: dict) -> dict[str, dict]:
    """生年・投打を選手IDごとに、どの大会の行からでも拾う。"""
    info: dict[str, dict] = {}
    for rows in events.values():
        for row in rows["batting"] + rows["pitching"]:
            pid = str(row.get("playerid"))
            if not info.get(pid):
                info[pid] = player_info(row)
    return info


def team_sources():
    """(サイトのチーム名, [(大会, その大会でのチーム名)...])。今大会を先に、新しい大会ほど先。"""
    for _, team, _, srcs in br.OPPONENTS:
        yield team, [(CURRENT, team)] + list(srcs)
    yield "Japan", [(CURRENT, "Japan")]


def analyze(d: dict) -> None:
    """大会ごとの打者・投手の表を作り、大会をまたいで同じ選手をまとめる。"""
    for team, srcs in team_sources():
        for event, name in srcs:
            add_event(d, team, event, name)
    merge_people(d)
    # 選手ページを作る人: 年齢で今大会に出られる選手と、今大会の記録がある選手（記録の生年が
    # 食い違っていても、出場したのなら相手国ページのメンバー側に載せるため）
    d["paged"] = {key for key, person in d["people"].items() if eligible(person["year"])
                  or any(event == CURRENT for _, event, _ in person["blocks"])}
    link_roster(d)
    d["starters"] = starters(d["events"][CURRENT]["pitching"])
    pitching = d["events"][CURRENT]["pitching"]
    d["logs"] = {team: sl.pitcher_log(pitching, d["games"], team)
                 for team in list(OPP) + ["Japan"]}


def add_event(d: dict, team: str, event: str, name: str) -> None:
    rows = d["events"][event]
    balls = br.batted_balls(rows["plays"], name)
    batters = br.collect_batters(rows["batting"], name, balls)
    pitchers = br.collect_pitchers(rows["pitching"], name)
    if not batters and not pitchers:
        return
    for kind, group in (("bat", batters), ("pit", pitchers)):
        for entry in group:
            remember(d, entry, team)["blocks"].append((kind, event, entry))
    tendency = br.team_tendency(batters, rows["plays"], name)
    d["tables"].setdefault(team, []).append((event, batters, pitchers, tendency))


def remember(d: dict, entry: dict, team: str) -> dict:
    """選手の行に、人の鍵（site_logic.person_key）と生年を付け、人ごとの記録を返す。"""
    pid = str(entry.get("_id") or "")
    year = birth_year(d["info"].get(pid, {}))
    key = sl.person_key(entry["名前"], year, team)
    entry.update(_key=key, _year=year, _elig=eligible(year))
    d["pid_key"][pid] = key
    person = d["people"].setdefault(key, {"name": entry["名前"], "team": team, "year": year,
                                          "pid": pid, "pids": set(), "blocks": []})
    person["pids"].add(pid)
    return person


def merge_people(d: dict) -> None:
    """同一人物.csv の組を1人にまとめる。名前と生年で作る鍵（person_key）より優先する。

    綴りや生年の登録が大会ごとに違って、鍵では1人にまとまらなかった選手のため。
    ファイルがなければ何もしない。見つからない選手や国が合わない行は、注意を出して飛ばす。
    """
    order = {team: {event: i for i, (event, _) in enumerate(srcs)} for team, srcs in team_sources()}
    for row in d["same"]:
        keep_pid = str(row.get("keep_playerid") or "").strip()
        drop_pid = str(row.get("merge_playerid") or "").strip()
        keep_key, drop_key = d["pid_key"].get(keep_pid), d["pid_key"].get(drop_pid)
        if not keep_key or not drop_key:
            missing = keep_pid if not keep_key else drop_pid
            print(f"注意: 同一人物.csv の playerid {missing} が記録にないので、この行は飛ばします"
                  f"（{keep_pid} ← {drop_pid}）", file=sys.stderr)
            continue
        if keep_key == drop_key:
            continue
        keep, drop = d["people"][keep_key], d["people"][drop_key]
        code = team_code(row.get("team"))
        if keep["team"] != drop["team"] or (code and code != TEAM_CODE.get(keep["team"], code)):
            print(f"注意: 同一人物.csv の {keep_pid} と {drop_pid} は国が合わないので、まとめません",
                  file=sys.stderr)
            continue
        absorb(d, keep_key, drop_key, order.get(keep["team"], {}))


def absorb(d: dict, keep_key: str, drop_key: str, order: dict[str, int]) -> None:
    """drop_key の人の記録を keep_key の人に移し、drop_key を消す。"""
    keep, drop = d["people"][keep_key], d["people"].pop(drop_key)
    keep["pids"] |= drop["pids"]
    keep["year"] = keep["year"] if keep["year"] is not None else drop["year"]
    keep["blocks"] = sorted(keep["blocks"] + drop["blocks"],  # 新しい大会が先、同じ大会は打撃→投球
                            key=lambda b: (order.get(b[1], 99), b[0] != "bat"))
    for _, _, entry in keep["blocks"]:
        entry["_key"] = keep_key
        if entry.get("_year") is None and keep["year"] is not None:
            entry.update(_year=keep["year"], _elig=eligible(keep["year"]))
    for pid, key in d["pid_key"].items():
        if key == drop_key:
            d["pid_key"][pid] = keep_key
    newest = keep["blocks"][0][2]  # 名前は一番新しい大会の綴り
    keep["name"] = newest["名前"]
    if d["info"].get(str(newest.get("_id"))):
        keep["pid"] = str(newest.get("_id"))


def link_roster(d: dict) -> None:
    """名簿照合.csv で、今大会の名簿の選手と過去の記録の人を結ぶ。"""
    status = {(r.get("team"), r.get("name")): r.get("status") or "" for r in d["roster"]}
    d["roster_of"], d["match_by_name"] = {}, {}
    for row in d["match"]:
        place = (row.get("team"), row.get("roster_name"))
        key = d["pid_key"].get(str(row.get("playerid") or ""))
        if not key:
            continue
        d["match_by_name"].setdefault(place, key)
        d["roster_of"][key] = (row.get("roster_name"), status.get(place, ""))
    d["rostered"] = set(d["roster_of"])


def starters(rows: list[dict]) -> dict:
    """{(試合ID, チーム): 先発投手の名前}。"""
    out = {}
    for row in rows:
        if int(br.number(row.get("pitch_gs"))):
            out[(str(row.get("gameid")), row.get("team"))] = br.name_of(row)
    return out


def team_games(d: dict, team: str) -> list[dict]:
    return [g for g in d["games"] if team in (g.get("homelabel"), g.get("awaylabel"))]


def opponent(game: dict, team: str) -> str:
    return game.get("awaylabel") if game.get("homelabel") == team else game.get("homelabel")


def has_current(d: dict, team: str) -> bool:
    return any(event == CURRENT for event, *_ in d["tables"].get(team, []))


# ---------------------------------------------------------------- 試合の行


def box_url(game_id) -> str:
    game = urllib.parse.quote(str(game_id), safe="")
    return collect.event_url(WBSC_DOMAIN, WBSC_SLUG, f"schedule-and-results/box-score/{game}")


def venue(game: dict) -> str:
    """「Roberto Clemente・マサヤ」のように球場と町。"""
    stadium = str(game.get("stadium") or "").replace("Estadio ", "")
    place = str(game.get("location") or "")
    return "・".join(x for x in (stadium, TOWN.get(place, place)) if x)


def tag(game: dict) -> str:
    label = str(game.get("gametypelabel") or "")
    for word, text, css in ROUND_TAG:
        if word in label:
            return f'<span class="tag {css}">{text}</span>'
    return f'<span class="tag">{esc(label)}</span>' if label else ""


def team_link(team, root: str) -> str:
    """国名。日本は日本代表へ、相手国は相手国ページへ。仮の表記（A1など）はリンクにしない。"""
    if team == "Japan":
        return f'<a href="{root}japan/">日本</a>'
    if team in OPP:
        return f'<a href="{root}team/{slug(team)}/">{esc(ja(team))}</a>'
    return esc(team_name(team))


def when_cell(game: dict, mode: str = "full") -> str:
    """日本時間を太字で先に、現地時刻を小さく添える。mode は full・time・time_local。"""
    jst, local = sl.jst_dt(game), sl.local_dt(game)
    if mode == "full":
        main, sub = f"{md(jst)} {jst:%H:%M}", f"{md(local)} {local:%H:%M}"
    elif mode == "time_local":
        main, sub = f"{jst:%H:%M}", f"{local.month}/{local.day} {local:%H:%M}"
    else:
        main, sub = f"{jst:%H:%M}", f"{local:%H:%M}"
    return f'<td class="t"><b>{main}</b><small>現地 {sub}</small></td>'


def matchup(game: dict, root: str, view, strong=None) -> str:
    """対戦とスコア。view のチームがいればその側から（○ 日本 5-3 イギリス）。

    view がなければ先攻 - 後攻の順に書く（見出しが「先攻 - 後攻」の表）。strong のチーム
    （日本）は、並びを変えずに太字と○●で目立たせる。
    """
    state = sl.game_state(game)
    seen = sl.japan_view(game, view) if view else None
    if seen:
        text = (f'{mark_html(seen["mark"])}<b>{esc(ja(view))}</b> '
                f'<span class="sc">{seen["score"] or "vs"}</span> '
                f'{team_link(seen["opponent"], root)}')
    elif undecided(game.get("awaylabel")) and undecided(game.get("homelabel")):
        text = '<span class="tbd">未定</span>'  # 「TBD vs TBD」と出さない
    else:
        middle = sl.score_text(game) if state in ("final", "live", "unknown") else "vs"
        mine = sl.japan_view(game, strong) if strong else None

        def side(team) -> str:
            link = team_link(team, root)
            if mine and team == strong:
                return f'{mark_html(mine["mark"])}<b>{link}</b>'
            return link
        text = (f'{side(game.get("awaylabel"))} <span class="sc">{middle}</span> '
                f'{side(game.get("homelabel"))}')
    return text + state_label(game, state)


def state_label(game: dict, state: str) -> str:
    innings = int(br.number(game.get("innings")))
    if state == "final" and innings and innings != 7:
        return f' <span class="inn">{innings}回</span>'
    if state == "live":
        return ' <span class="live">試合中</span>'
    if state == "other":
        return f' <span class="live">{esc(game.get("gamestatustext") or "中止・延期など")}</span>'
    if state == "unknown":  # 知らない状態の文字は「試合中」と決めつけず、そのまま見せる
        text = esc(str(game.get("gamestatustext")).strip())
        return f' <span class="st" title="{text}">状態: {text}</span>'
    return ""


def game_links(game: dict) -> str:
    parts = [ext(box_url(game["id"]), "速報・ボックス")] if game.get("id") else []
    if game.get("gamevideo"):
        parts.append(ext(game["gamevideo"], "映像"))
    return " ".join(parts)


def starter_text(game: dict, team: str, table: dict) -> str:
    mine = table.get((str(game.get("id")), team))
    theirs = table.get((str(game.get("id")), opponent(game, team)))
    if not mine and not theirs:
        return ""
    return f"先発 {short_name(mine or '?')}（相手 {short_name(theirs or '?')}）"


def game_row(game: dict, root: str, view=None, mode: str = "full",
             table: dict | None = None, today: bool = False) -> str:
    """試合1行。日本戦は日本の側から、view を渡せばそのチームの側から書く。"""
    japan = "Japan" in (game.get("homelabel"), game.get("awaylabel"))
    # 日本戦は、相手国のページでも日本から見た形で書く（○●はいつも日本の勝ち負け）
    side = "Japan" if japan else view
    seen = sl.japan_view(game, side) if side else None
    sub = [esc(venue(game))]
    if seen:  # 「日本は後攻」は途中で割らない
        sub.append(f'<span class="nw">{esc(ja(side))}は{seen["batting"]}</span>')
    if seen and table is not None and seen["state"] == "final":
        sub.append(esc(starter_text(game, side, table)))
    attrs = ' class="jp"' if japan else ""
    if today:
        attrs += f' data-day="{sl.local_day(game)}" hidden'
    return (f"<tr{attrs}>{when_cell(game, mode)}<td class=\"m\">{tag(game)}"
            f"{matchup(game, root, side if view else None, side)}"
            f"<small>{'・'.join(x for x in sub if x)}</small>"
            f'<small class="lk">{game_links(game)}</small></td></tr>')


def games_table(games: list[dict], root: str, view=None, mode: str = "full",
                table: dict | None = None, today: bool = False) -> str:
    rows = [game_row(g, root, view, mode, table, today) for g in games if sl.local_dt(g)]
    if not rows:
        return '<p class="empty">試合がありません。</p>'
    title = "先攻 - 後攻" if not view else "試合"
    return (f'<div class="gwrap"><table class="games"><thead><tr><th>日本時間</th>'
            f'<th>{title}</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


# ---------------------------------------------------------------- 成績の表


def th(column: str, kind: str = "") -> str:
    """並べ替えできる見出し。1回目の向きを data-dir に持たせる。"""
    low = column in TEXT_COLUMNS or (kind == "pit" and column in PIT_LOW)
    return f'<th scope="col" data-dir="{"asc" if low else "desc"}">{esc(column)}</th>'


def name_cell(d: dict, row: dict, root: str, marks: bool) -> str:
    """名前（名は頭文字）。出られる選手と、今大会の名簿と照合できた選手に印を付ける。"""
    full, key = row["名前"], row.get("_key")
    name = esc(short_name(full))
    if key in d["paged"]:
        name = f'<a href="{root}p/{key}/" title="{esc(full)}">{name}</a>'
    badge = ""
    if marks and row.get("_year") is None:
        badge += '<span class="b-el" title="生年が分からない">?</span>'
    elif marks and row.get("_elig"):
        badge += '<span class="b-el" title="2003年以降の生まれ（今大会に出られる）">○</span>'
    if marks and key in d["rostered"]:
        badge += '<span class="b-ro">名簿</span>'
    return f'<td class="nm" data-sort="{esc(full)}">{name}{badge}</td>'


def stat_cell(row: dict, column: str) -> str:
    if column == "守備":  # 「LF/LF/RF」のような重なりをまとめる
        value = "/".join(dict.fromkeys(x for x in str(row.get(column, "")).split("/") if x))
        return f"<td>{esc(value)}</td>"
    if column == "投球回":
        return f'<td data-sort="{row.get("_outs", 0)}">{esc(row.get(column, ""))}</td>'
    return f"<td>{esc(row.get(column, ''))}</td>"


def stats_table(d: dict, rows: list[dict], columns: list[str], root: str, kind: str,
                tid: str, marks: bool = True) -> str:
    """選手の成績表。名前の列と見出しの行を固定し、見出しを押すと並べ替わる。"""
    if not rows:
        return '<p class="empty">データがありません。</p>'
    head = "".join(th(c, kind) for c in columns)
    body = []
    for row in rows:
        plate = row.get("打席") if kind == "bat" else row.get("打者")
        classes = [c for c, on in (("old", not row.get("_elig", True)),
                                   ("few", int(plate or 0) < 10)) if on]
        cls = f' class="{" ".join(classes)}"' if classes else ""
        cells = name_cell(d, row, root, marks) + "".join(stat_cell(row, c) for c in columns[1:])
        body.append(f'<tr data-elig="{int(bool(row.get("_elig", True)))}"{cls}>{cells}</tr>')
    tall = " tall" if len(rows) > 12 else ""
    return (f'<div class="scroll{tall}"><table class="sort" id="{tid}"><thead><tr>{head}</tr>'
            f'</thead><tbody>{"".join(body)}</tbody></table></div>'
            '<p class="none" hidden>条件に合う選手はいません。</p>')


FILTERS = (
    '<div class="filters" role="group" aria-label="表の絞り込み">'
    '<label><input type="checkbox" id="f-elig" checked>今大会に出られる選手だけ</label>'
    '<label><input type="checkbox" id="f-pa">10打席以上だけ（投手は打者10人以上）</label></div>'
    '<p class="note">○＝2003年以降の生まれで今大会に出られる選手。名簿＝今大会の発表名簿と'
    '照合できた選手。見出しを押すと並べ替わります（もう一度押すと逆向き）。</p>'
)


def app_cell(app: dict | None) -> str:
    if not app:
        return '<td class="app" data-sort="-1"></td>'
    role = "先発" if app["gs"] else "救援"
    rest = "" if app["rest"] is None else f'<small>中{app["rest"]}日</small>'
    return (f'<td class="app" data-sort="{app["pitches"]}"><b>{role}</b> {app["ip"]}回<br>'
            f'{app["pitches"]}球{rest}</td>')


def log_name(d: dict, pitcher: dict, root: str) -> str:
    key = d["pid_key"].get(str(pitcher.get("_id")))
    name = esc(short_name(pitcher["name"]))
    if key in d["paged"]:
        name = f'<a href="{root}p/{key}/" title="{esc(pitcher["name"])}">{name}</a>'
    return f'<td class="nm" data-sort="{esc(pitcher["name"])}">{name}</td>'


def log_table(d: dict, team: str, root: str) -> str:
    """投手の登板記録（site_logic.pitcher_log）。列は今大会の各試合。"""
    log = d["logs"].get(team) or []
    if not log:
        return '<p class="empty">まだ登板の記録がありません。</p>'
    # スマホでは右が隠れるので、最終登板・今日なら・計球数を名前のすぐ後ろに置き、
    # 試合の列は新しい順（直近の登板が左）に並べる
    games = [g for g in team_games(d, team) if sl.is_final(g)][::-1]
    head = (th("選手") + '<th data-dir="desc">最終登板</th><th data-dir="desc">今日なら</th>'
            + th("計球数") + "".join(
                f'<th data-dir="desc">現地{iso_md(sl.local_day(g))}<br>'
                f"<small>{esc(ja(opponent(g, team)))}</small></th>" for g in games)
            + th("投球回") + th("先発"))
    body = []
    for pitcher in log:
        apps = {a["gameid"]: a for a in pitcher["apps"]}
        last = pitcher["last_date"]
        body.append(
            f'<tr>{log_name(d, pitcher, root)}'
            f'<td data-sort="{esc(last.replace("-", ""))}">{iso_md(last)}</td>'
            f'<td data-last="{esc(last)}">-</td><td>{pitcher["total_pitches"]}</td>'
            + "".join(app_cell(apps.get(str(g.get("id")))) for g in games)
            + f'<td data-sort="{sl.ip_to_outs(pitcher["ip_total"])}">{pitcher["ip_total"]}</td>'
            f'<td>{pitcher["gs_count"]}</td></tr>')
    return ('<p class="note">日付は現地。「今日なら」は今日（現地）投げるとしたら中何日か。'
            '試合の列は新しい順。U-23W杯には球数制限がありません'
            '（WBSC Official Rules 2025-2026 A1.8.4）。</p>'
            f'<div class="scroll"><table class="sort log"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


# ---------------------------------------------------------------- 順位表


def stand_table(rows: list[dict], title: str, root: str, second: bool = False) -> str:
    """順位表。スマホで国名の横に見えるよう、勝・敗・勝率を国名のすぐ後ろに置く。"""
    ties = any(r["t"] for r in rows)
    cols = (["順位・国", "勝", "敗"] + (["分"] if ties else []) + ["勝率", "差", "試合"]
            + (["持ち越し", "組"] if second else []) + ["得点", "失点"])
    body = []
    for r in rows:
        note = f'<small>{esc(r["note"])}</small>' if r.get("note") else ""
        rank = r["rank"] if r["rank"] is not None else "-"
        cells = ([f'<span class="rk">{rank}</span>{team_link(r["team"], root)}{note}', r["w"], r["l"]]
                 + ([r["t"]] if ties else []) + [r["pct"], r["gb"], r["g"]]
                 + ([r.get("carry", ""), r.get("group", "")] if second else [])
                 + [r["rs"], r["ra"]])
        cls = ' class="jp"' if r["team"] == "Japan" else ""
        body.append(f"<tr{cls}>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    head = "".join(f"<th>{c}</th>" for c in cols)
    return (f'<div class="card st"><h3>{title}</h3><div class="scroll"><table class="stand fix1">'
            f'<thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div></div>')


def standings_block(d: dict, root: str) -> str:
    """順位表。グループB（日本の組）を先に。スーパーラウンドが始まったらその表を上に。"""
    first = sl.standings(d["games"], GROUPS, outs=d["outs"])
    second = sl.second_round(d["games"], GROUPS, outs=d["outs"])
    played = any(sl.is_final(g) and "Super Round" in str(g.get("gametypelabel"))
                 for g in d["games"])
    parts = []
    if second["super"] and (second["ready"] or played):
        parts.append('<div class="two">'
                     + stand_table(second["super"], "スーパーラウンド（持ち越し込み）", root, True)
                     + stand_table(second["placement"], "順位決定ラウンド（持ち越し込み）",
                                   root, True) + "</div>")
    parts.append('<div class="two">'
                 + stand_table(first.get("B", []), "グループB（日本の組）", root)
                 + stand_table(first.get("A", []), "グループA", root) + "</div>")
    started = any(r["rank"] is not None for rows in first.values() for r in rows)
    note = ("試合前なので順位は「-」で、並びは組み合わせ表の順です。" if not started else
            "差はゲーム差です。")
    parts.append(f'<p class="note">{note}同率の並べ方は WBSC のW杯共通の規程（2024年版）で'
                 "計算しています。2026年大会の要項とは照らし合わせていないので、同率のときは WBSC の"
                 '公式の順位も確かめてください。持ち越しの決まりは<a href="'
                 f'{root}format/">大会方式</a>に。</p>')
    return "".join(parts)


# ---------------------------------------------------------------- ページの枠


def header(root: str, current: str) -> str:
    here = ' aria-current="page"'
    links = "".join(f'<a href="{root}{href}"{here if key == current else ""}>{label}</a>'
                    for key, href, label in NAV)
    top = here if current == "top" else ""
    return (f'<header><a class="brand" href="{root or "./"}"{top}>U-23W杯 2026</a>'
            f'<nav aria-label="サイト内">{links}</nav></header>')


def page(title: str, body: str, url: str, current: str, main_class: str = "") -> str:
    """1ページ分のHTML。url はサイトの根元からの相対（"" や "team/cuba/"）。"""
    root = "../" * url.count("/")
    full = "U-23W杯 2026" if not url else f"{title}｜U-23W杯 2026"
    cls = f' class="{main_class}"' if main_class else ""
    return (
        '<!doctype html>\n<html lang="ja"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<meta name="robots" content="noindex,nofollow">\n'
        '<meta name="referrer" content="no-referrer">\n'
        f"<title>{esc(full)}</title>\n<style>{CSS}</style>\n{so.head_tags(root)}\n"
        f'</head><body>\n{header(root, current)}\n<div id="band"></div>\n'
        f"<main{cls}>\n{body}\n</main>\n<footer>{FOOTER}</footer>\n"
        f'<script src="{root}site.js?v={JS_VERSION}" defer></script>\n'
        f"{so.body_end(root)}\n</body></html>\n"
    )


def section(anchor: str, title: str, body: str) -> str:
    return f'<section id="{anchor}"><h2>{title}</h2>{body}</section>'


# ---------------------------------------------------------------- 相手国ページ


def manager_text(manager) -> str:
    if not manager or not manager.get("name"):
        return "未確認"
    checked = f'・{iso_md(manager["checked"])}確認' if manager.get("checked") else ""
    note = f'<small class="mn">{public(manager["note"])}</small>' if manager.get("note") else ""
    return (f'{esc(manager["name"])}{sources(manager.get("source"))}<small>{checked}</small>'
            f"{note}")


def staff_text(staff) -> str:
    if not staff:
        return ""
    roles: dict[str, list[str]] = {}
    for person in staff:
        roles.setdefault(person.get("role") or "", []).append(esc(person.get("name")))
    names = "、".join(f'{esc(role)} {"・".join(people)}' for role, people in roles.items())
    return names + sources(staff[0].get("source"))


def facts_block(info: dict) -> str:
    rank = info.get("ranking") or {}
    rank_text = (f'{esc(rank["rank"])}位<small>（{iso_md(rank.get("as_of"))}時点）</small>'
                 + sources(rank.get("source")) if rank.get("rank") else "未確認")
    route = (esc(info["route"]) + sources(info.get("route_source"))
             if info.get("route") else "未確認")
    rows = (("監督", manager_text(info.get("manager"))), ("首脳陣", staff_text(info.get("staff"))),
            ("世界ランク", rank_text), ("出場経路", route),
            ("直近の成績", esc(" / ".join(info.get("recent") or [])) or "未確認"))
    return ('<dl class="facts">' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows if v)
            + "</dl>")


def notes_block(info: dict) -> str:
    notes = info.get("notes") or []
    if not notes:
        return ""
    return '<ul class="notes">' + "".join(f"<li>{public(n)}</li>" for n in notes) + "</ul>"


def roster_record(d: dict, code: str, name: str, root: str) -> str:
    key = d["match_by_name"].get((code, name))
    if key in d["paged"]:
        return f'<a href="{root}p/{key}/">あり</a>'
    return "あり" if key else ""


def roster_table(d: dict, code: str, rows: list[dict], main: str, root: str) -> str:
    """名簿の表。所属や過去の記録が1人も埋まっていなければ、その列は出さない。"""
    order = {p: i for i, p in enumerate(("P", "C", "IF", "OF"))}
    numbered = {id(r): d["numbers"].get((code, name_key(r.get("name")))) for r in rows}
    # 守備ごとに背番号順（番号のない選手はその守備の最後）。試合中に番号から探せるように
    rows = sorted(rows, key=lambda r: (order.get(r.get("position"), 9),
                                       int(br.number(numbered[id(r)]["number"])) if numbered[id(r)]
                                       else 999))
    shown = [n for n in numbered.values() if n]
    yomi = {id(r): reading_of(d, code, r.get("name")) for r in rows}
    clubs = any((r.get("club") or "").strip() or (yomi[id(r)].get("club_ja") or "").strip()
                for r in rows)
    records = any(roster_record(d, code, r.get("name"), root) for r in rows)
    body = []
    for r in rows:
        status = r.get("status") or ""
        badge = "" if status == main else f' <span class="badge alt">{esc(status.split("・")[0])}</span>'
        name = esc(r.get("name"))
        key = d["match_by_name"].get((code, r.get("name")))
        if key in d["paged"]:  # 名前からも選手ページへ（「あり」だけでは押す所が小さい）
            name = f'<a href="{root}p/{key}/">{name}</a>'
        extra = yomi[id(r)]
        reading = (extra.get("reading") or "").strip()
        if reading:
            name += f'<small class="yomi">{esc(reading)}</small>'
        if shown:  # 番号のない選手も空の枠を置き、名前の頭をそろえる。読みは名前の下にそろえる
            name = (f'<span class="no">{esc((numbered[id(r)] or {}).get("number", "").strip())}</span>'
                    f'<span class="nmw">{name}</span>')
        body.append(f'<tr><td>{esc(POS_JA.get(r.get("position"), "-"))}</td>'
                    f'<td class="nm">{name}{badge}</td>'
                    + (club_cell(r.get("club"), extra.get("club_ja")) if clubs else "")
                    + (f'<td class="rec">{roster_record(d, code, r.get("name"), root)}</td>'
                       if records else "")
                    + "</tr>")
    head = ("<th>守備</th><th>氏名</th>" + ("<th>発表時の所属</th>" if clubs else "")
            + ("<th>過去の記録</th>" if records else ""))
    hint = ("読みは目安です。" if any((yomi[id(r)].get("reading") or "").strip() for r in rows)
            else "") + number_hint(shown, len(rows))
    hint = f'<p class="note">{hint}</p>' if hint else ""
    return (f'{hint}<div class="scroll"><table class="plain roster"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def club_cell(club, club_ja) -> str:
    """所属。日本語名があればそれを出し、元の表記は title に残す。"""
    club, club_ja = (club or "").strip(), (club_ja or "").strip()
    if club_ja:
        title = f' title="{esc(club)}"' if club and club != club_ja else ""
        return f'<td class="cl"{title}>{esc(club_ja)}</td>'
    return f'<td class="cl">{esc(club)}</td>'


def roster_block(d: dict, team: str, info: dict, root: str) -> str:
    """今大会の名簿（今大会_発表名簿.csv）。状態・発表日・出典・確認日を添える。"""
    meta = info.get("roster") or {}
    code = TEAM_CODE.get(team, "")
    rows = [r for r in d["roster"] if r.get("team") == code]
    note = f'<p class="note">{public(meta["note"])}</p>' if meta.get("note") else ""
    if not rows:
        found = sources(meta.get("source"), "調べた先")
        # 注記に確認日が書いてあれば、それと食い違う日付は並べない
        checked = meta.get("checked") or d["checked"]
        day = "" if CHECKED_IN_TEXT.search(meta.get("note") or "") else f"{iso_md(checked)}確認"
        tail = f'<p class="note">{found}{"・" if found and day else ""}{day}</p>'
        return f'<p class="warn">今大会の名簿は未確認。下は過去大会の記録。</p>{note}{tail}'
    main = Counter(r.get("status") or "" for r in rows).most_common(1)[0][0]
    first = next(r for r in rows if (r.get("status") or "") == main)
    label = meta.get("label") or main.split("・")[0]
    # 発表日は相手国.json を先に見る。名簿の CSV の published には記事の日付が入っていることがある
    # （韓国は9/3発表を9/7の記事で確かめた）
    published = meta.get("published") or first.get("published")
    head = (f'<p><span class="badge">{esc(label)}</span> {len(rows)}人・'
            f'発表 {iso_md(published)}・{sources(meta.get("source") or first.get("source"))}・'
            f'{iso_md(first.get("checked"))}確認</p><p class="note">状態: {esc(main)}</p>')
    # 名簿の CSV の notes 列は作業のメモなので出さない。見せる文は相手国.json の roster.note だけ
    return head + note + roster_table(d, code, rows, main, root)


def left_team(d: dict, code: str, name) -> bool:
    """名簿の status に離脱の報道があるか（注目選手の札に使う）。"""
    return any(r.get("team") == code and r.get("name") == name and "離脱" in (r.get("status") or "")
               for r in d["roster"])


def notable_card(d: dict, item: dict, root: str, code: str = "") -> str:
    key = d["pid_key"].get(str(item.get("playerid") or ""))
    reading = (reading_of(d, code, item.get("name")).get("reading") or "").strip()
    yomi = f'<small class="yomi">{esc(reading)}</small>' if reading else ""
    record = f'<a href="{root}p/{key}/">WBSCの記録</a>' if key in d["paged"] else ""
    sub = "・".join(x for x in (POS_JA.get(item.get("pos"), item.get("pos") or ""),
                                item.get("club") or "") if x)
    japan = ('<span class="badge npb jpl">日本の球団</span>' if item.get("japan_league") else "")
    if left_team(d, code, item.get("name")):
        japan += '<span class="badge warn jpl">離脱報道</span>'
    facts = "".join(f"<li>{public(f)}</li>" for f in item.get("facts") or [])
    links = " ".join(x for x in (record, sources(item.get("source"))) if x)
    return (f'<div class="card nb"><h3>{esc(item.get("name"))}{yomi}<small>{esc(sub)}</small>{japan}</h3>'
            f'<ul>{facts}</ul><p class="note">{links}</p></div>')


def notable_block(d: dict, info: dict, root: str, code: str = "") -> str:
    items = info.get("notable") or []
    if not items:
        return '<p class="empty">載せる材料がまだありません。</p>'
    read = any(reading_of(d, code, item.get("name")).get("reading") for item in items)
    return ('<p class="note">事実と公開データだけを載せています。'
            + ("名前の横の読みは目安です。" if read else "") + "</p>"
            + "".join(notable_card(d, item, root, code) for item in items))


def vs_japan_block(info: dict) -> str:
    rows = info.get("vs_japan") or []
    lead = '<p class="note">今とは別の世代どうしの結果です。スコアは日本が先。</p>'
    if not rows:
        return lead + ('<p class="empty">集めた大会（U-23W杯 2022・2024、アジア選手権 2025、アジア競技大会 2026）'
                       "では対戦していません。</p>")
    # 結果は2列目に置き、スマホの最初の画面に入れる。注意書きは表の中で細く折り返すと
    # 読めないので、※印を付けて表の下に出す（同じ文は同じ印）
    marks: dict[str, int] = {}
    body = []
    for r in rows:
        star = ""
        if r.get("note"):
            n = marks.setdefault(r["note"], len(marks) + 1)
            star = f'<sup class="fn">※{n}</sup>'
        body.append(f'<tr><td>{esc(r.get("event"))}</td>'
                    f'<td>{mark_html(r.get("result"))}{esc(r.get("japan_score"))}{star}</td>'
                    f'<td>{iso_md(r.get("local_date"), True)}</td><td>{esc(r.get("round"))}</td></tr>')
    notes = "".join(f'<p class="note">※{n} {public(text)}</p>' for text, n in marks.items())
    return (lead + '<div class="scroll"><table class="plain"><thead><tr><th>大会</th>'
            '<th>日本から見た結果</th><th>日付（現地）</th><th>ラウンド</th></tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>{notes}')


def current_tables(d: dict, team: str, root: str, marks: bool = True) -> str:
    """今大会の打者・投手の表と打球図、投手の登板記録。"""
    _, batters, pitchers, _ = next(t for t in d["tables"][team] if t[0] == CURRENT)
    tid = f"{slug(team)}-now"
    return (f"<h3>投手の登板記録</h3>{log_table(d, team, root)}"
            + (FILTERS if marks else "")
            + f'<h3>打者<span class="tc" data-t="b-{tid}"></span></h3>'
            + stats_table(d, batters, BAT, root, "bat", f"b-{tid}", marks)
            + f'<h3>投手<span class="tc" data-t="p-{tid}"></span></h3>'
            + stats_table(d, pitchers, PIT, root, "pit", f"p-{tid}", marks)
            + f"<h3>打球の散らばり（全打者）</h3>{br.spray_chart(batters)}")


def current_block(d: dict, team: str, root: str) -> str:
    games = games_table(team_games(d, team), root, view=team, table=d["starters"])
    if not has_current(d, team):
        return (f"<h3>試合</h3>{games}<p class=\"note\">大会が始まると、ここに今大会の打者・"
                "投手の成績と投手の登板記録が入ります。</p>")
    return f"<h3>試合</h3>{games}" + current_tables(d, team, root)


def trend_block(d: dict, team: str) -> str:
    rows = d["tables"].get(team, [])
    if not rows:
        return '<p class="empty">データがありません。</p>'
    cols = list(rows[0][3])
    head = "<th>大会</th>" + "".join(f"<th>{esc(c)}</th>" for c in cols)
    body = "".join(f'<tr><td class="ev">{esc(EVENT_LABEL[event])}</td>'
                   + "".join(f"<td>{esc(tendency.get(c, ''))}</td>" for c in cols) + "</tr>"
                   for event, _, _, tendency in rows)
    return (f'<div class="scroll"><table class="fix1"><thead><tr>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div><p class=\"note\">盗塁は 成功/企図。率はチーム全体の"
            "打席・打球に対する割合。大会ごとに顔ぶれが違う点に気をつけてください。</p>")


def event_details(d: dict, event: str, batters: list, pitchers: list, root: str,
                  opened: bool, tid: str) -> str:
    return (f'<details{" open" if opened else ""}><summary>{esc(EVENT_LABEL[event])}'
            f"<small>打者{len(batters)}・投手{len(pitchers)}</small></summary>"
            f'<h4>打者<span class="tc" data-t="b-{tid}"></span></h4>'
            + stats_table(d, batters, BAT, root, "bat", f"b-{tid}")
            + f'<h4>投手<span class="tc" data-t="p-{tid}"></span></h4>'
            + stats_table(d, pitchers, PIT, root, "pit", f"p-{tid}")
            + f"<h4>打球の散らばり（全打者）</h4>{br.spray_chart(batters)}</details>")


def past_block(d: dict, team: str, root: str, with_filters: bool) -> str:
    past = [t for t in d["tables"].get(team, []) if t[0] != CURRENT]
    if not past:
        return '<p class="empty">この相手の過去の記録はまだありません。</p>'
    parts = [FILTERS] if with_filters else []
    for i, (event, batters, pitchers, _) in enumerate(past):
        parts.append(event_details(d, event, batters, pitchers, root, i == 0,
                                   f"{slug(team)}-{i}"))
    return "".join(parts)


def japan_game(d: dict, team: str):
    """この国と日本の試合（日程の最初の1試合）。なければ None。"""
    for game in team_games(d, team):
        if "Japan" in (game.get("homelabel"), game.get("awaylabel")) and sl.local_dt(game):
            return game
    return None


def when_html(game) -> str:
    """日本時間を太字で先に、現地を小さく。"""
    jst, local = sl.jst_dt(game), sl.local_dt(game)
    return f'<b>{md(jst)} {jst:%H:%M}</b> <small>現地 {md(local)} {local:%H:%M}</small>'


def page_head(crumbs: list[str], title: str, meta: str = "") -> str:
    """ページの見出し。crumbs は HTML（リンクか文字）の並び。"""
    return (f'<div class="page-head"><p class="crumbs">{" / ".join(crumbs)}</p><h1>{title}</h1>'
            + (f'<p class="meta">{meta}</p>' if meta else "") + "</div>")


def kv(label: str, value) -> str:
    return f'<span class="kv"><i>{esc(label)}</i><em>{esc(value if value not in (None, "") else "-")}</em></span>'


def badges(items) -> str:
    """[(種類, 文字)] を小さな札に。"""
    inner = "".join(f'<span class="badge {css}">{esc(text)}</span>' for css, text in items if text)
    return f'<span class="badges">{inner}</span>' if inner else ""


def newest_block(person: dict, kind: str):
    """その人の一番新しい大会の (大会, 行)。打撃か投球か。なければ (None, None)。"""
    for k, event, line in person["blocks"]:
        if k == kind:
            return event, line
    return None, None


def short_event(event) -> str:
    return EVENT_LABEL.get(event, str(event)).replace("（本大会）", "")


def japan_league_keys(d: dict, info: dict) -> set:
    """注目選手のうち、日本の球団にいる選手の鍵と、名前の照合用の形（記録のない名簿の選手のため）。"""
    items = [item for item in info.get("notable") or [] if item.get("japan_league")]
    keys = {d["pid_key"].get(str(item.get("playerid") or "")) for item in items} - {None}
    return keys | {("name", name_key(item.get("name"))) for item in items if item.get("name")}


def in_japan_league(npb: set, key, row: dict | None) -> bool:
    """選手の鍵か、名簿の名前が、日本の球団にいる注目選手のものか。"""
    return key in npb or bool(row and ("name", name_key(row.get("name"))) in npb)


def card_kind(d: dict, key: str, position=None) -> str:
    """カードに出す数字の種類（投手 pit・打者 bat）。

    名簿の守備があればそれで決める。なければ記録から: 投球か打撃の片方だけならそれ、両方あれば
    WBSCの登録の守備（捕手・内野手・外野手なら打者）、それも分からなければ投手。
    """
    if position:
        return "pit" if position == "P" else "bat"
    person = d["people"][key]
    kinds = {blk[0] for blk in person["blocks"]}
    if len(kinds) == 1:
        return next(iter(kinds))
    registered = d["info"].get(person["pid"], {}).get("position") or ""
    return "bat" if registered in ("C", "IF", "OF") else "pit"


def card_sub(hand, pos: str, club: str) -> str:
    """カードの上の行の小さな文字（投打・守備・所属）。長い所属名は省く。"""
    return "・".join(x for x in (hand, pos, club if len(club) <= SHORT_ENOUGH else "") if x)


def person_card(d: dict, key: str, kind: str, root: str, code: str, npb: set,
                roster_row: dict | None = None) -> str:
    """記録のある選手のカード。選手ページへのリンク。

    数字2つの下に、どの大会の数字かを小さく書く。札は「離脱報道」「日本の球団」だけ。
    """
    person = d["people"][key]
    row = roster_row or {}
    event, line = newest_block(person, kind)
    if line is None:  # 名簿では投手でも、記録は打撃だけ（またはその逆）
        kind = "bat" if kind == "pit" else "pit"
        event, line = newest_block(person, kind)
    meta = d["info"].get(person["pid"], {})
    hand = HAND.get(meta.get("throws") if kind == "pit" else meta.get("bats"))
    pos = POS_JA.get(row.get("position") or meta.get("position"), "")
    extra = reading_of(d, code, row.get("name") or person["name"])
    club = (extra.get("club_ja") or "").strip() or (row.get("club") or "").strip()
    sub = card_sub(f"{hand}{'投' if kind == 'pit' else '打'}" if hand else "", pos, club)
    reading = (extra.get("reading") or "").strip()
    yomi = f'<small class="yomi">{esc(reading)}</small>' if reading else ""
    pairs = ("防御率", "奪三振率") if kind == "pit" else ("打率", "出塁率")
    stats = "".join(kv(k, (line or {}).get(k)) for k in pairs)
    # 狭いカードで「の記 / 録」と切れないよう、折り返すなら「の記録」の前で
    source = (f'<small class="ev">{esc(short_event(event))} <span class="nw">の記録</span></small>'
              if event else "")
    out = "離脱" in (row.get("status") or "")
    marks = [("warn", "離脱報道" if out else ""),
             ("npb", "日本の球団" if in_japan_league(npb, key, roster_row) else "")]
    native = row.get("name") if row.get("name") and code in ("KOR", "TPE") else ""
    name = native or person["name"]
    title = f' title="{esc(person["name"])}"' if native else ""
    return (f'<a class="pcard{" out" if out else ""}" href="{root}p/{key}/"><b class="nm"{title}>'
            f'{esc(name)}</b>{yomi}<small class="sub">{esc(sub)}</small>{stats}{source}'
            f"{badges(marks)}</a>")


def roster_only_card(d: dict, row: dict, code: str, warn: bool = False,
                     npb: set | None = None) -> str:
    """名簿にいるが、記録（選手ページ）のない選手のカード。リンクにしない。

    warn は、名簿の選手と結んだ記録の生年が年齢超過で、選手ページを作っていないとき。
    npb は japan_league_keys の戻り値（日本の球団にいる注目選手と名前で照らす）。
    """
    extra = reading_of(d, code, row.get("name"))
    club = (extra.get("club_ja") or "").strip() or (row.get("club") or "").strip()
    sub = card_sub("", POS_JA.get(row.get("position"), ""), club)
    reading = (extra.get("reading") or "").strip()
    yomi = f'<small class="yomi">{esc(reading)}</small>' if reading else ""
    out = "離脱" in (row.get("status") or "")
    marks = [("warn", "離脱報道" if out else ""),
             ("npb", "日本の球団" if in_japan_league(npb or set(), None, row) else ""),
             ("warn", "記録の生年が年齢超過" if warn else "")]
    norec = "" if warn else '<small class="ev">国際大会の記録なし</small>'
    return (f'<div class="pcard{" out" if out else ""}"><b class="nm">{esc(row.get("name"))}</b>{yomi}'
            f'<small class="sub">{esc(sub)}</small>{norec}{badges(marks)}</div>')


def volume(person: dict, kind: str) -> float:
    _, line = newest_block(person, kind)
    if not line:
        return 0.0
    return br.number(line.get("投球回" if kind == "pit" else "打席"))


def roster_heading(info: dict, rows: list[dict]) -> tuple[str, str, bool]:
    """名簿のまとまりの見出し（HTML）・その下の小さな文・最終（または代表）発表か。

    相手国.json の roster.label に「候補」が入っていれば候補（最終の24人は未発表）、
    ほか（最終メンバー発表・代表発表・連盟サイトの名簿）は今大会のメンバー。
    """
    meta = info.get("roster") or {}
    main = Counter(r.get("status") or "" for r in rows).most_common(1)[0][0]
    label = meta.get("label") or main.split("・")[0]
    final = "候補" not in label
    # 発表日は相手国.json を先に見る（roster_block と同じ。CSV には記事の日付が入っていることがある）
    published = meta.get("published") or next(
        (r.get("published") for r in rows if (r.get("status") or "") == main and r.get("published")), "")
    title = "今大会のメンバー" if final else "今大会の候補<small>最終の24人は未発表</small>"
    count = f"{len(rows)}人" + (f"・{iso_md(published)}発表" if published else "")
    return title, count, final


def group_html(title: str, note: str, cards: list[str]) -> str:
    """見出し・小さな説明・カードの並びを1つのまとまりに。"""
    grid = (f'<div class="pgrid">{"".join(cards)}</div>' if cards
            else '<p class="empty">該当する選手はいません。</p>')
    return (f'<div class="pgroup"><h3>{title}</h3>'
            + (f'<p class="note">{note}</p>' if note else "") + f"{grid}</div>")


def player_grid(d: dict, team: str, info: dict, root: str) -> str:
    """選手カードの並び。札ではなく見出しでまとまりに分け、投手・野手で切り替える。

    名簿があるチーム: 「今大会のメンバー」（または「今大会の候補」）に名簿の選手全員と、
    今大会の記録がある選手（名簿と名前を結べなくても）。離脱の報道がある選手はまとまりの最後。
    名簿にいない過去の大会の選手は、節の下の閉じた欄にまとめる。
    名簿がないチーム: 「今大会に出場した選手」（大会が始まってから）と「名簿は未発表です」
    （過去の大会に出ていて、年齢では出られる選手）。
    名簿に守備位置が1人も書かれていない（投手がいない）チームは、切り替えずに1つの並びにする。
    """
    code = TEAM_CODE.get(team, "")
    npb = japan_league_keys(d, info)
    order = {event: i for t, srcs in team_sources() if t == team
             for i, (event, _) in enumerate(srcs)}
    rows = [r for r in d["roster"] if r.get("team") == code]
    split = not rows or any(r.get("position") == "P" for r in rows)
    sides = ("p", "b") if split else ("a",)

    def side_of(kind: str) -> str:
        return ("p" if kind == "pit" else "b") if split else "a"

    def played_now(person: dict) -> bool:
        return any(event == CURRENT for _, event, _ in person["blocks"])

    # 並びの順（小さいほど先）: 0 今大会の記録がある選手（多く出た順）→ 1 名簿の選手で過去の記録あり
    # （名簿の順）→ 2 名簿の選手で記録なし → 3 離脱の報道がある選手。閉じた欄と目安の選手は新しい大会・
    # 多く出た順
    top = {s: [] for s in sides}      # 名簿のまとまり（名簿がなければ今大会に出場した選手）
    hint = {s: [] for s in sides}     # 名簿がないチームの目安の選手
    extra = {"p": [], "b": []}        # 閉じた欄（名簿にいない過去の大会の選手）。中は投手・野手に分ける
    used = set()
    # 守備の発表がある国で、守備が空の選手はユーティリティとして野手の側に置く（チェコの名簿の UTL）
    has_pos = any(r.get("position") for r in rows)
    for i, row in enumerate(rows):
        if has_pos and not row.get("position"):
            row = dict(row, position="UTL")
        key = d["match_by_name"].get((code, row.get("name")))
        gone = "離脱" in (row.get("status") or "")
        if key in d["paged"] and key not in used:
            used.add(key)
            person = d["people"][key]
            kind = card_kind(d, key, row.get("position"))
            rank = (3, i, 0) if gone else (0, -volume(person, kind), i) if played_now(person) else (1, i, 0)
            top[side_of(kind)].append((rank, person_card(d, key, kind, root, code, npb, row)))
        else:
            kind = "pit" if row.get("position") == "P" else "bat"
            top[side_of(kind)].append(((3 if gone else 2, i, 0), roster_only_card(
                d, row, code, warn=bool(key) and key not in d["paged"], npb=npb)))
    for k, person in d["people"].items():
        if person["team"] != team or k not in d["paged"] or k in used:
            continue
        kind = card_kind(d, k)
        event, _ = newest_block(person, kind)
        card = person_card(d, k, kind, root, code, npb)
        if played_now(person):
            top[side_of(kind)].append(((0, -volume(person, kind), 0), card))
        else:
            rank = (order.get(event, 99), -volume(person, kind), 0)
            (extra["p" if kind == "pit" else "b"] if rows else hint[side_of(kind)]).append((rank, card))

    def ordered(items: list) -> list[str]:
        return [html_ for _, html_ in sorted(items, key=lambda x: x[0])]

    if not any(top.values()) and not any(hint.values()) and not any(extra.values()):
        return '<p class="empty">名簿も過去の記録もまだありません。</p>'
    title, count, final = roster_heading(info, rows) if rows else ("", "", True)
    first = ""  # 下にまだ別のまとまりがあるときだけ「先に並べています」と書く
    if rows and (extra["p"] or extra["b"]):
        first = f'{"今大会のメンバー" if final else "今大会の候補"}を先に並べています。'
    elif not rows and any(top.values()):
        first = "今大会に出場した選手を先に並べています。"
    lead = (f'<p class="note">{first}数字は国際大会（WBSC）の記録で、どの大会の数字かはカードに'
            "書いています。</p>")
    panels, counts = {}, {}
    for s in sides:
        if rows:
            groups = [group_html(title, count, ordered(top[s]))]
        else:
            groups = [group_html("今大会に出場した選手", "", ordered(top[s]))] if top[s] else []
            groups.append(group_html(
                "名簿は未発表です", "過去の大会に出ていて、年齢では今大会に出られる選手です。"
                "候補の目安としてご覧ください。", ordered(hint[s])))
        panels[s] = "".join(groups)
        counts[s] = len(top[s]) + len(hint[s])
    if split:
        tabs = "".join(
            f'<button type="button" role="tab" aria-selected="{"true" if s == "p" else "false"}" '
            f'data-seg="{s}">{label} <span class="cnt">{counts[s]}</span></button>'
            for s, label in (("p", "投手"), ("b", "野手")))
        body = (f'<div class="seg" role="tablist" aria-label="投手と野手">{tabs}</div>'
                + "".join(f'<div class="seg-panel" role="tabpanel" data-seg="{s}"'
                          f'{"" if s == "p" else " hidden"}>{panels[s]}</div>' for s in sides))
    else:
        body = f'<p class="note nopos">守備位置の発表はありません。</p>{panels["a"]}'
    return lead + body + others_block(extra, final, ordered)


def others_block(extra: dict, final: bool, ordered) -> str:
    """名簿にいないが、過去の大会に出ていて年齢では出られる選手の、閉じた欄。いなければ空。"""
    total = len(extra["p"]) + len(extra["b"])
    if not total:
        return ""
    where = "今回のメンバー" if final else "今の候補名簿"
    parts = [f"<h4>{label}</h4>" + f'<div class="pgrid">{"".join(ordered(extra[s]))}</div>'
             for s, label in (("p", "投手"), ("b", "野手")) if extra[s]]
    # 見出しと（人数…）は1つの span に入れ、狭い画面でも文として折り返す
    return (f'<details class="others"><summary><span>今回の名簿にいない選手<small>（{total}人・過去の大会の'
            f"記録・参考）</small></span></summary><p class=\"note\">過去の大会に出ていて年齢では出られますが、"
            f"{where}には入っていません。</p>{''.join(parts)}</details>")


def team_tiles(d: dict, team: str, info: dict) -> str:
    rank = (info.get("ranking") or {}).get("rank")
    manager = (info.get("manager") or {}).get("name")
    meta = info.get("roster") or {}
    code = TEAM_CODE.get(team, "")
    count = len([r for r in d["roster"] if r.get("team") == code])
    roster = (f'<b>{count}人</b><small>{esc(meta.get("label") or "発表名簿")}</small>' if count
              else "<b>未確認</b><small>今大会の名簿</small>")
    route = esc(info.get("route") or "未確認")
    return ('<div class="tiles">'
            f'<div class="tile"><i>世界ランク</i><b>{esc(str(rank) + "位") if rank else "未確認"}</b></div>'
            f'<div class="tile"><i>今大会の名簿</i>{roster}</div>'
            f'<div class="tile"><i>監督</i><small>{esc(manager or "未確認")}</small></div></div>'
            f'<p class="note">出場経路：{route}</p>')


def team_page(d: dict, label: str, team: str, group: str) -> str:
    root = "../../"
    info = d["opp"].get(team) or {}
    game = japan_game(d, team)
    meta = f"グループ{group}・{esc(team)}" + (f"・日本戦 {when_html(game)}" if game else "")
    details = ("<details class=\"more\"><summary><b>詳しい表と資料</b>"
               "<small>名簿の表・監督と出典・大会ごとの傾向・過去の大会の表</small></summary>"
               + section("facts", "基本情報と出典", facts_block(info))
               + section("roster", "今大会の名簿", roster_block(d, team, info, root))
               + section("trend", "大会ごとの傾向", trend_block(d, team))
               + section("past", "過去の大会", past_block(d, team, root, not has_current(d, team)))
               + "</details>")
    body = "".join([
        page_head([f'<a href="{root}teams/">相手国</a>', esc(label)], esc(label), meta),
        team_tiles(d, team, info), notes_block(info),
        section("players", "選手", player_grid(d, team, info, root)),
        video_section(team, root),
        section("notable", "注目選手", notable_block(d, info, root, TEAM_CODE.get(team, ""))),
        section("vsjapan", "日本との対戦<small>参考値</small>", vs_japan_block(info)),
        section("now", "今大会の試合", current_block(d, team, root)),
        details,
    ])
    return page(label, body, f"team/{slug(team)}/", "teams", "fe")


def video_section(team: str, root: str) -> str:
    """台湾の相手国ページだけに、日本遠征の映像の入口（site_video.py）。失敗しても止めない。"""
    if site_video is None or team != "Chinese Taipei":
        return ""
    try:
        return site_video.team_section(root)
    except Exception as error:
        print(f"注意: 映像の入口を作れませんでした（{error!r}）", file=sys.stderr)
        return ""


# ---------------------------------------------------------------- 選手ページ


def tiles_html(pairs, note: str = "") -> str:
    """数字のタイル。pairs は (見出し, 値)。note は最初のタイルの下に添える小さな文。"""
    return ('<div class="tiles">' + "".join(
        f'<div class="tile"><i>{esc(k)}</i><b>{esc(v)}</b>'
        + (f"<small>{esc(note)}</small>" if note and i == 0 else "") + "</div>"
        for i, (k, v) in enumerate(pairs)) + "</div>")


def player_block(kind: str, event: str, line: dict) -> str:
    """大会ごとの成績を、大きな数字のカードで。"""
    title = esc(EVENT_LABEL[event])
    if kind == "bat":
        pairs = (("打率", line["打率"]), ("出塁率", line["出塁率"]), ("長打率", line["長打率"]),
                 ("三振率", line["三振率"]), ("盗塁", line["盗塁"]))
        sub = (f'{line["試合"]}試合・{line["打席"]}打席・{line["打数"]}打数{line["安打"]}安打・'
               f'本塁打{line["本塁打"]}・打点{line["打点"]}・四球{line["四球"]}・三振{line["三振"]}・'
               f'盗塁死{line["盗塁死"]}・守備 {line["守備"] or "-"}')
        extra = f"<h3>打球</h3>{br.spray_chart([line])}"
        return (f'<section class="card"><h2>{title}<small>打撃</small></h2>{tiles_html(pairs)}'
                f'<p class="sub">{esc(sub)}</p>{extra}</section>')
    pairs = (("防御率", line["防御率"]), ("投球回", line["投球回"]), ("奪三振率", line["奪三振率"]),
             ("与四球率", line["与四球率"]), ("球数", line["球数"]))
    sub = (f'{line["登板"]}登板（先発{line["先発"]}）・被安打{line["被安打"]}・三振{line["三振"]}・'
           f'四球{line["四球"]}・自責点{line["自責点"]}・被本塁打{line["被本塁打"]}')
    return (f'<section class="card"><h2>{title}<small>投球</small></h2>{tiles_html(pairs)}'
            f'<p class="sub">{esc(sub)}</p></section>')


def player_apps(d: dict, person: dict) -> str:
    """今大会の登板（投手の登板記録から、この選手の分）。"""
    log = [p for p in d["logs"].get(person["team"]) or [] if str(p["_id"]) in person["pids"]]
    if not log:
        return ""
    items = "".join(
        f'<li>{iso_md(a["date"])} vs {esc(ja(a["opponent"]))}　{"先発" if a["gs"] else "救援"} '
        f'{a["ip"]}回 {a["pitches"]}球'
        + ("（初登板）" if a["rest"] is None else f'（中{a["rest"]}日）') + "</li>"
        for a in log[0]["apps"])
    return (f'<section class="card"><h2>今大会の登板<small>日付は現地</small></h2>'
            f'<ul class="apps">{items}</ul></section>')


def player_head_tiles(person: dict) -> str:
    """一番新しい大会の数字（打撃か投球の、新しい方）。"""
    if not person["blocks"]:
        return ""
    kind, event, line = person["blocks"][0]
    if kind == "bat":
        pairs = (("打率", line["打率"]), ("出塁率", line["出塁率"]), ("長打率", line["長打率"]),
                 ("打席", line["打席"]))
    else:
        pairs = (("防御率", line["防御率"]), ("投球回", line["投球回"]), ("奪三振率", line["奪三振率"]),
                 ("与四球率", line["与四球率"]))
    return tiles_html(pairs, f"{short_event(event)}")


def player_clips(person: dict) -> str:
    """映像のカット集（site_clips.py）。部品が読めない・記録がないときは出さない。"""
    if site_clips is None:
        return ""
    parts = []
    for kind, event, line in person["blocks"]:
        pid = str(line.get("_id") or "")
        if not pid or event == CURRENT and not d_has_plays(event):
            continue
        try:
            clips = (site_clips.pitcher_clips(event, pid) if kind == "pit"
                     else site_clips.batter_clips(event, pid))
            if not clips or not any(clips.values()):
                continue
            html_ = site_clips.clips_html(clips)
        except Exception as error:  # 部品の失敗でページを止めない
            print(f"注意: カット集を作れませんでした（{event} {pid}: {error}）", file=sys.stderr)
            continue
        label = "投球" if kind == "pit" else "打撃"
        parts.append(f'<h3>{esc(EVENT_LABEL.get(event, event))}<small>{label}</small></h3>{html_}')
    if not parts:
        return ""
    return section("clips", "映像のカット集<small>試合の映像へのリンク</small>",
                   '<p class="note">場面は WBSC の1球ごとの記録から拾っています。映像のリンクは'
                   "試合ごとなので、回とカウントを目安に探してください。</p>" + "".join(parts))


def d_has_plays(event: str) -> bool:
    return (br.DATA_ROOT / event / "plays.csv").is_file()


def player_notes(d: dict, key: str, team: str) -> str:
    """相手国.json の注目選手に入っていれば、その事実と出典。"""
    for item in (d["opp"].get(team) or {}).get("notable") or []:
        if d["pid_key"].get(str(item.get("playerid") or "")) != key:
            continue
        facts = "".join(f"<li>{public(f)}</li>" for f in item.get("facts") or [])
        if not facts:
            return ""
        japan = "<small>日本の球団</small>" if item.get("japan_league") else ""
        return section("notable", f"注目選手のメモ{japan}",
                       f'<ul>{facts}</ul><p class="note">{sources(item.get("source"))}</p>')
    return ""


def player_page(d: dict, key: str, person: dict) -> str:
    team, root = person["team"], "../../"
    meta = d["info"].get(person["pid"], {})
    code = TEAM_CODE.get(team, "")
    if team == "Japan":
        crumbs = [f'<a href="{root}japan/">日本代表</a>', esc(person["name"])]
    else:
        crumbs = [f'<a href="{root}teams/">相手国</a>',
                  f'<a href="{root}team/{slug(team)}/">{esc(ja(team))}</a>', esc(person["name"])]
    roster_name = (d["roster_of"].get(key) or ("", ""))[0]
    reading = (reading_of(d, code, roster_name or person["name"]).get("reading") or "").strip()
    title = esc(person["name"]) + (f'<small class="yomi">{esc(reading)}</small>' if reading else "")
    pos = meta.get("position") or "?"
    facts = [f"登録守備 {POS_JA.get(pos, pos)}",
             f'{HAND.get(meta.get("throws"), "?")}投{HAND.get(meta.get("bats"), "?")}打']
    if team != "Japan":
        facts.append(f'{person["year"]}年生まれ' if person["year"] else "生年不明")
    if key in d["roster_of"]:
        name, status = d["roster_of"][key]
        facts.append(f'今大会の名簿 {status.split("・")[0] or "あり"}（{name}）')
    elif team != "Japan":
        facts.append("今大会の名簿では未確認")
    blocks = "".join(player_block(kind, event, line) for kind, event, line in person["blocks"])
    body = (page_head(crumbs, title, esc("・".join(facts)))
            + player_head_tiles(person) + player_notes(d, key, team) + player_apps(d, person)
            + player_clips(person)
            + section("seasons", "大会ごとの成績", blocks))
    return page(person["name"], body, f"p/{key}/", "japan" if team == "Japan" else "teams")


# ---------------------------------------------------------------- 日本代表


def hands_text(players: list[dict]) -> str:
    pitchers = [r for r in players if r.get("position") == "投手"]
    fielders = [r for r in players if r.get("position") != "投手"]
    throws = Counter(r.get("throws") for r in pitchers)
    bats = Counter(r.get("bats") for r in fielders)
    return (f'<p>投手 {len(pitchers)}人（右投げ {throws["右"]}・左投げ {throws["左"]}）、'
            f'野手 {len(fielders)}人（右打ち {bats["右"]}・左打ち {bats["左"]}・両打ち {bats["両"]}）</p>')


# 日本代表の表の列幅。背番号順の表と守備別の4つの表で列がそろうよう、幅を決めておく（最後の所属は残り）
JAPAN_COLS = '<colgroup><col class="c-nm"><col class="c-pos"><col class="c-hand"><col class="c-age">' \
             '<col class="c-size"><col></colgroup>'


def japan_table(rows: list[dict], tid: str) -> str:
    """日本代表の選手の表。公式発表の項目だけ。12人を超える表は見出し行を固定する。"""
    head = "".join(th(c) for c in ("選手", "守備", "投打", "年齢", "身長・体重", "所属"))
    body = "".join(
        f'<tr><td class="nm" data-sort="{int(br.number(r.get("number"))):03d}">'
        f'<span class="no">{esc(r.get("number"))}</span>{esc(r.get("name"))}</td>'
        f'<td>{esc(r.get("position"))}</td><td>{esc(r.get("throws"))}投{esc(r.get("bats"))}打</td>'
        f'<td>{esc(r.get("age"))}</td><td>{esc(r.get("height_cm"))}cm・{esc(r.get("weight_kg"))}kg</td>'
        f'<td class="cl">{esc(r.get("club"))}</td></tr>' for r in rows)
    tall = " tall" if len(rows) > 12 else ""
    return (f'<div class="scroll{tall}"><table class="sort jpt" id="{tid}">{JAPAN_COLS}'
            f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>")


def japan_players(players: list[dict]) -> str:
    by_number = sorted(players, key=lambda r: int(br.number(r.get("number"))))
    by_pos = "".join(
        f"<h3>{pos}<small>{len(rows)}人</small></h3>{japan_table(rows, f'jp-{i}')}"
        for i, pos in enumerate(POS_ORDER)
        for rows in [[r for r in by_number if r.get("position") == pos]] if rows)
    return (hands_text(players)
            + '<div class="seg" role="group" aria-label="並び">'
            '<button type="button" data-show="jp-num" aria-pressed="true">背番号順</button>'
            '<button type="button" data-show="jp-pos" aria-pressed="false">守備別</button></div>'
            f'<div id="jp-num">{japan_table(by_number, "jp-all")}</div>'
            f'<div id="jp-pos" hidden>{by_pos}</div>')


def japan_staff(staff: list[dict]) -> str:
    body = "".join(f'<tr><td>{esc(r.get("role"))}</td><td>{esc(r.get("number"))}</td>'
                   f'<td>{esc(r.get("name"))}</td><td class="cl">{esc(r.get("club"))}</td></tr>'
                   for r in staff)
    return ('<div class="scroll"><table class="plain"><thead><tr><th>役割</th><th>背番号</th>'
            f"<th>氏名</th><th>所属</th></tr></thead><tbody>{body}</tbody></table></div>")


def japan_page(d: dict) -> str:
    root = "../"
    players = [r for r in d["japan"] if r.get("role") == "選手"]
    staff = [r for r in d["japan"] if r.get("role") and r.get("role") != "選手"]
    if has_current(d, "Japan"):
        now = current_tables(d, "Japan", root, marks=False)
    else:
        now = '<p class="note">大会が始まると、ここに日本の打者・投手の成績と投手の登板記録が入ります。</p>'
    roster = (japan_players(players) if players else
              '<p class="empty">日本代表_公式発表.csv が見つかりません。</p>')
    body = "".join([
        page_head(['<a href="../">トップ</a>', "日本代表"], "日本代表",
                  f"グループB・選手{len(players)}人と首脳陣{len(staff)}人"),
        f'<p class="note">{ext(OFFICIAL_JAPAN, "侍ジャパン公式の発表（2026年10月6日）")}にある'
        "項目だけを載せています。年齢は発表時の値です。</p>",
        "<h2>日本戦の日程と結果</h2>"
        + games_table(team_games(d, "Japan"), root, view="Japan", table=d["starters"]),
        f"<h2>選手<small>{len(players)}人</small></h2>{roster}",
        f"<h2>首脳陣</h2>{japan_staff(staff)}",
        f"<h2>今大会の成績</h2>{now}",
    ])
    return page("日本代表", body, "japan/", "japan")


# ---------------------------------------------------------------- 大会方式


def rank_cell(rank: int, day_pairs) -> str:
    me = f"B{rank}"
    for away, home in day_pairs:
        if me in (away, home):
            other = home if away == me else away
            same = other[1:] == me[1:]
            side = "コイントス" if same else ("先攻" if away == me else "後攻")
            return f"<td>A組{other[1:]}位<small>{side}</small></td>"
    return "<td>-</td>"


def rank_table() -> str:
    """日本（B組）の1次ラウンドの順位ごとの、第2ラウンドの相手。公式日程から。"""
    head = "<th>日本の順位</th>" + "".join(
        f"<th>現地 {md(iso_day(day))}</th>" for day, _ in SECOND_ROUND)
    body = "".join(
        f'<tr><td>B組{rank}位<small>{"SR" if rank <= 3 else "順位決定"}'
        "</small></td>" + "".join(rank_cell(rank, pairs) for _, pairs in SECOND_ROUND) + "</tr>"
        for rank in range(1, 7))
    return (f'<div class="scroll"><table class="plain rk fix1"><thead><tr>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def venue_rows(d: dict) -> str:
    places: dict[str, list] = {}
    for game in d["games"]:
        places.setdefault(venue(game), [])
        if "Japan" in (game.get("homelabel"), game.get("awaylabel")) and sl.jst_dt(game):
            places[venue(game)].append(md(sl.jst_dt(game)))
    return "".join(
        f'<tr><td>{esc(name)}</td><td>{f"{len(days)}試合" if days else "なし"}'
        + (f'<small>{esc("・".join(days))}（日本時間）</small>' if days else "") + "</td></tr>"
        for name, days in places.items() if name)


def japan_venue_text(d: dict) -> str:
    count = Counter(TOWN.get(str(g.get("location")), g.get("location"))
                    for g in team_games(d, "Japan") if "Opening" in str(g.get("gametypelabel")))
    return "・".join(f"{town} {n}試合" for town, n in count.most_common())


def format_rules() -> str:
    """規定。大会要項で確かめていないものは「未確認」とだけ書く。"""
    unknown = ("イニング数", "延長のタイブレーク", "コールドゲーム", "同率の順位の決め方")
    return ("<ul>"
            f"<li>球数制限：U-23W杯にはありません（"
            f"{ext(WBSC_RULES, 'WBSC Official Rules of Baseball 2025-2026')} A1.8.4）。</li>"
            + "".join(f"<li>{name}：未確認（大会要項で確認中）</li>" for name in unknown)
            + "<li>同じ順位どうしの対戦（例：A組1位 対 B組1位）の先攻・後攻：大会前の技術会議の"
            "コイントスで決まります（公式日程の注記）。</li></ul>")


def format_page(d: dict) -> str:
    body = "".join([
        page_head(['<a href="../">トップ</a>', "大会方式"], "大会方式",
                  "U-23W杯 2026（ニカラグア、現地 11/6〜15）"),
        f"<h2>流れ</h2>{FORMAT_FLOW}",
        f"<h2>持ち越し</h2>{FORMAT_CARRY}",
        "<h2>日本の順位ごとの相手<small>公式日程から</small></h2>" + rank_table()
        + '<p class="note">SR＝スーパーラウンド。「コイントス」は同じ順位どうしの対戦で、先攻・後攻は'
          "大会前の技術会議のコイントスで決まります。時刻と球場は公式日程では未定。1次ラウンドと同じ"
          "時間帯（現地10時半〜19時半）なら、日本時間では翌日になります。</p>",
        "<h2>球場</h2>"
        '<div class="scroll"><table class="plain"><thead><tr><th>球場・町</th><th>日本の1次ラウンド</th>'
        f"</tr></thead><tbody>{venue_rows(d)}</tbody></table></div>"
        f'<p class="note">日本の1次ラウンドは {esc(japan_venue_text(d))}。</p>',
        f"<h2>規定</h2>{format_rules()}",
        "<h2>直前合宿</h2><p>10/31〜11/2、NTT東日本グラウンドほか（千葉県船橋市）。</p>",
        "<h2>時差</h2><p>日本時間は現地の15時間後です（ニカラグアは夏時間がありません）。"
        "現地 18:30 の試合は、日本時間では翌日 09:30 です。</p>",
    ])
    return page("大会方式", body, "format/", "format")


# ---------------------------------------------------------------- 日程・相手国一覧


def schedule_page(d: dict) -> str:
    """日本の日付でまとめた日程。見出しは「11/7(土)　現地 11/6(金)」。"""
    root = "../"
    days: dict[str, list] = {}
    for game in d["games"]:
        if sl.jst_dt(game):
            days.setdefault(sl.jst_dt(game).date().isoformat(), []).append(game)
    jump = "".join(f'<a href="#d{day}">{md(iso_day(day))}</a>' for day in days)
    parts = [page_head(['<a href="../">トップ</a>', "日程と結果"], "日程と結果",
                       "日付は日本時間でまとめています。日本時間は現地の15時間後。"),
             f'<nav class="days" aria-label="日付">{jump}</nav>']
    for day, games in days.items():
        locals_ = sorted({sl.local_day(g) for g in games})
        mode = "time" if len(locals_) == 1 else "time_local"
        parts.append(
            f'<h2 class="day" id="d{day}" data-local="{" ".join(locals_)}">{md(iso_day(day))}'
            f'<small>現地 {"・".join(md(iso_day(x)) for x in locals_)}</small></h2>'
            + games_table(games, root, mode=mode))
    if not any("Opening" not in str(g.get("gametypelabel")) for g in d["games"]):
        parts.append('<p class="note">スーパーラウンドと順位決定ラウンド（現地 11/12〜14）、'
                     "3位決定戦と決勝（現地 11/15）の組み合わせは1次ラウンドの結果で決まり、"
                     "決まりしだい載ります。現地 11/11 は予備日です。"
                     f'<a href="{root}format/">大会方式</a></p>')
    return page("日程と結果", "".join(parts), "schedule/", "schedule")


def team_card(d: dict, team: str, root: str, game=None, note: str = "") -> str:
    """相手国の大きなカード。国名・日本戦の日時・世界ランク・監督・名簿の状態。"""
    info = d["opp"].get(team) or {}
    rank = (info.get("ranking") or {}).get("rank")
    manager = (info.get("manager") or {}).get("name")
    code = TEAM_CODE.get(team, "")
    count = len([r for r in d["roster"] if r.get("team") == code])
    label = (info.get("roster") or {}).get("label") or "発表名簿"
    status = (("roster", f"名簿 {label} {count}人") if count else ("warn", "名簿は未確認"))
    if game:
        jst, local = sl.jst_dt(game), sl.local_dt(game)
        sub = (f"<b>日本戦 {md(jst)} {jst:%H:%M}</b> "
               f"<small>現地 {md(local)} {local:%H:%M}</small>")
    else:
        sub = esc(note or f"グループ{GROUPS.get(team, '')}")
    return (f'<a class="pcard team" href="{root}team/{slug(team)}/">'
            f'<span class="num">{esc(code)}</span><b class="nm">{esc(ja(team))}</b>'
            f'<span class="sub">{sub}</span><small class="sub">監督 {esc(manager or "未確認")}</small>'
            f'{kv("世界ランク", f"{rank}位" if rank else "未確認")}'
            f"{badges([status])}</a>")


def teams_grid(d: dict, root: str) -> str:
    """グループB（日本の組）は対戦順に日付つき、続いてスーパーラウンド以降の相手、グループA。"""
    b, later, seen = [], [], set()
    rounds = set()
    for game in team_games(d, "Japan"):
        team = opponent(game, "Japan")
        if team not in OPP or not sl.jst_dt(game):
            continue
        if "Opening" in str(game.get("gametypelabel")):
            if GROUPS.get(team) == "B" and team not in seen:
                seen.add(team)
                b.append(team_card(d, team, root, game))
        elif GROUPS.get(team) != "B" and team not in seen:
            seen.add(team)
            later.append(team_card(d, team, root, game))
            rounds.add("順位決定ラウンド" if "Placement" in str(game.get("gametypelabel"))
                       else "スーパーラウンド")
    b += [team_card(d, t, root) for t, g in GROUPS.items() if g == "B" and t in OPP and t not in seen]
    a = [team_card(d, t, root) for t, g in GROUPS.items() if g == "A" and t in OPP and t not in seen]
    title = "・".join(sorted(rounds, reverse=True)) or "スーパーラウンド"
    second = (f'<h2>{title}の日本の相手</h2><div class="pgrid">{"".join(later)}</div>'
              if later else "")
    return (f'<h2>グループB<small>日本の組・対戦順</small></h2><div class="pgrid">{"".join(b)}</div>'
            f'{second}<h2>グループA<small>スーパーラウンド以降で当たる組</small></h2>'
            f'<div class="pgrid">{"".join(a)}</div>')


def teams_page(d: dict) -> str:
    body = (page_head(['<a href="../">トップ</a>', "相手国"], "相手国",
                      f"{len(OPP)}チーム・今大会の名簿・注目選手・過去の大会の記録")
            + teams_grid(d, "../"))
    return page("相手国", body, "teams/", "teams")


# ---------------------------------------------------------------- トップ


def hero_item(game: dict) -> dict:
    """次の日本戦のカードに入れる中身。開いたときに site.js が選び直す。"""
    seen = sl.japan_view(game)
    local, jst = sl.local_dt(game), sl.jst_dt(game)
    rival = seen["opponent"]
    return {
        "t": local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "opp": team_name(rival), "href": f"team/{slug(rival)}/" if rival in OPP else "schedule/",
        "jst": f"{md(jst)} {jst:%H:%M}", "local": f"{md(local)} {local:%H:%M}",
        "venue": f'{venue(game)}・日本は{seen["batting"]}', "done": seen["state"] == "final",
    }


def round_of(game: dict, *words: str) -> bool:
    return any(w in str(game.get("gametypelabel")) for w in words)


def after_text(d: dict, japan: list[dict]) -> str:
    """日程に残っている日本戦がないときの文。大会の段階で言い方を変える。"""
    games = d["games"]
    done = "日本の試合はすべて終わりました。"
    medal_jp = [g for g in japan if round_of(g, "Final", "Bronze")]
    medal = [g for g in games if round_of(g, "Final", "Bronze")]
    # 中止のまま日程に残った試合も「もう動かない」側に数える（sl.is_settled）
    if (medal_jp or medal) and all(sl.is_settled(g) for g in (medal_jp or medal)):
        return done  # 日本の入ったメダル戦、またはメダル戦そのものが終わった（もう試合はない）
    opening = [g for g in games if round_of(g, "Opening")]
    second_jp = [g for g in japan if round_of(g, "Super", "Placement")]
    if not opening or not all(sl.is_settled(g) for g in opening) or not second_jp:
        return ("次の日本戦は、組み合わせが決まりしだい載ります（スーパーラウンドと順位決定ラウンドの"
                "相手は1次ラウンドの結果で決まります）。")
    if any(round_of(g, "Placement") for g in second_jp):
        return done  # 順位決定ラウンドの後に日本の試合はない
    super_round = [g for g in games if round_of(g, "Super")]
    if super_round and all(sl.is_settled(g) for g in super_round):
        rows = sl.second_round(games, GROUPS, outs=d["outs"])["super"]
        rank = next((r["rank"] for r in rows if r["team"] == "Japan"), None)
        named = [t for g in medal for t in (g.get("awaylabel"), g.get("homelabel")) if t in JA]
        decided = medal and len(named) == 2 * len(medal) and "Japan" not in named
        if (rank is not None and rank > 4) or decided:
            return done  # スーパーラウンド5・6位か、メダル戦の顔ぶれが決まって日本がいない
    return "3位決定戦と決勝の組み合わせは、スーパーラウンドの結果で決まりしだい載ります。"


def hero_block(d: dict, japan: list[dict]) -> str:
    items = [hero_item(g) for g in japan if sl.local_dt(g)]
    ahead = [i for i in items if not i["done"]]
    after = (f'<p class="card" id="next-none"{"" if not ahead else " hidden"}>'
             f"{esc(after_text(d, japan))}</p>")
    if not ahead:
        return after
    g = ahead[0]
    data = so.script_json(items)  # 相手の名前などに </script> や <!-- が入っても中身の終わりがずれない
    return (f'<a class="hero" id="next-jp" href="{esc(g["href"])}" data-start="{esc(g["t"])}"><small>次の日本戦'
            f'<b class="when" id="next-when"></b></small><b class="opp">日本 vs {esc(g["opp"])}</b>'
            f'<span><b class="jst big">{esc(g["jst"])}</b>（日本時間）・'
            f'<span class="local">現地 {esc(g["local"])}</span></span>'
            f'<span class="venue">{esc(g["venue"])}</span></a>{after}'
            f'<script type="application/json" id="jp-games">{data}</script>')


def previous_block(japan: list[dict]) -> str:
    done = [g for g in japan if sl.is_final(g)]
    if not done:
        return ""
    game = done[-1]
    seen = sl.japan_view(game)
    return (f'<p class="prev">前の試合：{mark_html(seen["mark"])}日本 {seen["score"]} '
            f'{team_link(seen["opponent"], "")}<small>{md(sl.jst_dt(game))}（日本時間）・'
            f'日本は{seen["batting"]}</small></p>')


def today_block(d: dict) -> str:
    return ('<section id="today"><h2>今日の試合 <small id="today-day"></small></h2>'
            '<p class="empty" id="today-msg" hidden></p>'
            + games_table(d["games"], "", today=True)
            + '<noscript><p class="note">今日の試合を出すには JavaScript が要ります。'
              '<a href="schedule/">日程</a>を見てください。</p></noscript></section>')


def save_block(count: int, size_mb: float) -> str:
    # 件数と結果はボタンの下の行（save-status）に出す。ボタンの幅は変わらない（site_offline.py）
    return ('<h2>電波が弱い所で使うには</h2><div class="card">'
            '<button type="button" id="save-all" class="save">全ページを端末に保存</button>'
            '<p class="save-st" id="save-status" aria-live="polite"></p>'
            f'<p class="note">ホテルのWi-Fiなど電波のよい所で押すと、全{count}件（約{size_mb:.1f}MB）を'
            "端末に保存し、電波がなくても開けるようになります。iPhone は Safari で開き、共有ボタンから"
            "「ホーム画面に追加」してください。LINEなどアプリの中で開くと、保存が効かないことが"
            "あります。Safariで開いてください。</p></div>")


def wbsc_links() -> str:
    links = (("", "大会ページ"), ("schedule-and-results", "日程と結果"), ("teams", "出場チーム"))
    return ('<h2>WBSCの公式ページ</h2><p class="links">'
            + "".join(ext(collect.event_url(WBSC_DOMAIN, WBSC_SLUG, tail), text)
                      for tail, text in links) + "</p>")


def next_japan_game(japan: list[dict]):
    """書き出した時点で、まだ終わっていない最初の日本戦。"""
    return next((g for g in japan if sl.local_dt(g) and not sl.is_settled(g)), None)


def doors_block(d: dict, japan: list[dict]) -> str:
    games = [g for g in japan if sl.is_final(g)]
    marks = Counter((sl.japan_view(g) or {}).get("mark") for g in games)
    tie = f'{marks["△"]}分' if marks["△"] else ""
    record = f'{len(games)}試合 {marks["○"]}勝{marks["●"]}敗{tie}' if games else "大会前"
    nxt = next_japan_game(japan)
    rival = opponent(nxt, "Japan") if nxt else None
    if rival in OPP:
        jst = sl.jst_dt(nxt)
        opp_text = f"次の相手 {ja(rival)}（{md(jst)} {jst:%H:%M}）"
    else:
        opp_text = "名簿・注目選手・過去の大会の記録"
    return ('<nav class="doors" aria-label="入口">'
            '<a class="door jp" href="japan/"><span class="door-k">自チーム</span><b>日本代表</b>'
            f"<small>{esc(record)}・成績・登板表・計測データ</small></a>"
            '<a class="door opp" href="teams/"><span class="door-k">相手国</span>'
            f"<b>{len(OPP)}チーム</b><small>{esc(opp_text)}</small></a></nav>")


def next_opponent_block(d: dict, japan: list[dict]) -> str:
    """次の日本戦の相手。国ページへの大きなリンクと、注目選手を3人まで。"""
    nxt = next_japan_game(japan)
    rival = opponent(nxt, "Japan") if nxt else None
    if rival not in OPP:
        return ""
    info = d["opp"].get(rival) or {}
    code = TEAM_CODE.get(rival, "")
    cards = []
    for item in (info.get("notable") or [])[:3]:
        key = d["pid_key"].get(str(item.get("playerid") or ""))
        reading = (reading_of(d, code, item.get("name")).get("reading") or "").strip()
        yomi = f'<small class="yomi">{esc(reading)}</small>' if reading else ""
        sub = "・".join(x for x in (POS_JA.get(item.get("pos"), item.get("pos") or ""),
                                    item.get("club") or "") if x)
        fact = public((item.get("facts") or [""])[0])
        # 札は相手国ページの選手カードと同じ決まり（「名簿」などの札は出さない）
        marks = badges([("warn", "離脱報道" if left_team(d, code, item.get("name")) else ""),
                        ("npb", "日本の球団" if item.get("japan_league") else "")])
        inner = (f'<b class="nm">{esc(item.get("name"))}</b>{yomi}<small class="sub">{esc(sub)}</small>'
                 + (f'<small class="sub">{fact}</small>' if fact else "") + marks)
        href = f"p/{key}/" if key in d["paged"] else f"team/{slug(rival)}/#notable"
        cards.append(f'<a class="pcard" href="{href}">{inner}</a>')
    grid = f'<div class="pgrid">{"".join(cards)}</div>' if cards else ""
    return ('<section id="next-opp"><h2>次の相手</h2>'
            + team_card(d, rival, "", nxt)
            + (f"<h3>注目選手</h3>{grid}" if grid else "")
            + f'<p><a class="go" href="team/{slug(rival)}/">{esc(ja(rival))}の選手・過去の対戦・資料を見る →</a></p>'
            + "</section>")


def index_page(d: dict, count: int, size_mb: float) -> str:
    japan = team_games(d, "Japan")
    body = "".join([
        '<h1 class="sr">U-23W杯 2026 スタッフ共有</h1>',
        hero_block(d, japan), previous_block(japan), doors_block(d, japan),
        next_opponent_block(d, japan), today_block(d),
        '<section id="standings" class="small"><h2>順位表</h2>' + standings_block(d, "")
        + '<p><a class="card go" href="schedule/">日程と結果をすべて見る →</a></p>'
          '<p><a class="card go" href="format/">大会方式：スーパーラウンドと持ち越し、日本の順位ごとの相手 →</a></p>'
          "</section>",
        save_block(count, size_mb), wbsc_links(),
    ])
    return page("U-23W杯 2026", body, "", "top")


# ---------------------------------------------------------------- 組み立てと書き出し


def build() -> tuple[dict[str, str], list[dict]]:
    """全ページを作る。戻り値は ({URL: HTML}, games.json の一覧)。"""
    d = load()
    analyze(d)
    pages: dict[str, str] = {"": "", "schedule/": schedule_page(d), "teams/": teams_page(d),
                             "format/": format_page(d)}
    japan = japan_pages(d)
    pages.update(japan)
    if len(japan) > 1:  # site_japan.py が日本の選手ページ（japan/p/）を作ったので、p/ の日本の選手は作らない
        d["paged"] = {k for k in d["paged"] if d["people"][k]["team"] != "Japan"}
    for label, team, group, _ in br.OPPONENTS:
        pages[f"team/{slug(team)}/"] = team_page(d, label, team, group)
    for key in sorted(d["paged"]):
        pages[f"p/{key}/"] = player_page(d, key, d["people"][key])
    pages.update(video_pages())
    size = sum(len(p.encode("utf-8")) for p in pages.values()) / 1024 / 1024
    pages[""] = index_page(d, len(pages) + 1, size + 0.05)
    return pages, d["games"]


def video_pages() -> dict[str, str]:
    """台湾の選手ごとの映像ページ（site_video.py）。読めない・失敗したときは出さない。"""
    if site_video is None:
        return {}
    try:
        return site_video.pages(page)
    except Exception as error:
        print(f"注意: 映像ページを作れませんでした（{error!r}）", file=sys.stderr)
        return {}


def place_media(site: Path) -> None:
    """動画とサムネイルを書き出し先に置く。ハードリンクにして、作り直しのたびの複製とゴミ箱を増やさない。"""
    if site_video is None:
        return
    try:
        files = site_video.media()
    except Exception as error:
        print(f"注意: 映像のファイルの一覧を作れませんでした（{error!r}）", file=sys.stderr)
        return
    for src, rel in files:
        target = site / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(src, target)
        except OSError:  # 別のディスクなどでリンクできなければ複写
            shutil.copy2(src, target)


def japan_pages(d: dict) -> dict[str, str]:
    """日本代表のページ。site_japan.py があればそれを、読めない・失敗したときは今の japan_page。"""
    if site_japan is not None:
        try:
            made = site_japan.build_japan(d, page)
            if isinstance(made, dict) and isinstance(made.get("japan/"), str) and all(
                    isinstance(u, str) and u.startswith("japan/") and u.endswith("/")
                    and isinstance(h, str) for u, h in made.items()):
                return made
            print("注意: site_japan.build_japan の戻り値の形が違うので、今の日本代表ページを使います",
                  file=sys.stderr)
        except Exception as error:
            print(f"注意: site_japan.build_japan が失敗したので、今の日本代表ページを使います（{error!r}）",
                  file=sys.stderr)
    return {"japan/": japan_page(d)}


def version_of(pages: dict[str, str]) -> str:
    """版。ページと site.js の中身から作るので、中身が同じなら版も変わらない。"""
    digest = hashlib.sha1(SITE_JS.encode("utf-8"))
    for url in sorted(pages):
        digest.update(url.encode("utf-8") + b"\0" + pages[url].encode("utf-8"))
    return digest.hexdigest()[:10]


def old_output(out: Path) -> bool:
    """目印を付ける前の版の build_site.py が書いたフォルダか。中身の形で確かめる。

    根元に index.html・404.html・robots.txt・_headers と、合言葉（英数字24文字）のフォルダ
    1つだけがあり、その中に pages.json と sw.js がある。
    """
    items = [p for p in out.iterdir() if p.name != ".DS_Store"]
    folders = [p for p in items if p.is_dir()]
    files = {p.name for p in items if p.is_file()}
    return (files == {"index.html", "404.html", "robots.txt", "_headers"} and len(folders) == 1
            and len(folders[0].name) == 24 and folders[0].name.isalnum()
            and (folders[0] / "pages.json").is_file() and (folders[0] / "sw.js").is_file())


def check_out(out: Path) -> None:
    """消して作り直してよい書き出し先か確かめる。

    通すのは、空のフォルダ（またはまだない）、目印（MARK）のあるフォルダ、目印を付ける前の
    このツールの出力と同じ形のフォルダだけ。robots.txt があるだけでは通さない
    （Web アプリの public/ にもふつうにある）。
    """
    forbidden = {Path.home().resolve(), REPO, ROOT.resolve(), Path(out.anchor)}
    if out in forbidden:
        raise SystemExit(f"{out} には書き出せません。サイト用のフォルダを指定してください。")
    if not out.exists():
        return
    if not out.is_dir():
        raise SystemExit(f"{out} はフォルダではないので書き出せません。")
    if not any(out.iterdir()) or (out / MARK).is_file() or old_output(out):
        return
    raise SystemExit(f"{out} は build_site.py の出力に見えないので消しません。"
                     "空のフォルダか、新しい名前を指定してください。")


def discard(path: Path) -> None:
    """古い出力をゴミ箱に送る（元に戻せない消し方はしない）。"""
    if Path("/usr/bin/trash").exists():
        subprocess.run(["/usr/bin/trash", str(path)], check=True)
        return
    trash = Path.home() / ".Trash"
    trash.mkdir(exist_ok=True)
    shutil.move(str(path), str(trash / f"{path.name}-{time.strftime('%Y%m%d%H%M%S')}"))


def write_site(out: Path, token: str, pages: dict[str, str], games: list[dict]) -> None:
    """--out のフォルダだけを作り直し、合言葉のフォルダの下にページを書く。"""
    check_out(out)
    if out.exists() and any(out.iterdir()):
        discard(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / MARK).write_text("")
    site = out / token
    for url, content in pages.items():
        target = site / url / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    (site / "site.js").write_text(SITE_JS, encoding="utf-8")
    place_media(site)
    version = version_of(pages)
    core = [u for u in pages if u in CORE or u.startswith("team/")] + ["site.js"]
    so.write_assets(site, core, list(pages) + ["site.js"], version,
                    so.status_from_games(games, version))
    (out / "index.html").write_text(BLANK)
    (out / "404.html").write_text(BLANK)
    (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    # _headers に合言葉は書かない（site_offline.headers_rules は /*/sw.js の形で当てる）
    (out / "_headers").write_text(
        "/*\n  X-Robots-Tag: noindex, nofollow\n  Referrer-Policy: no-referrer\n"
        + so.headers_rules())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=OUT, help="書き出し先（中身は作り直す）")
    parser.add_argument("--data-root", type=Path, help="収集データの場所（既定は 05_収集データ）")
    parser.add_argument("--new-token", action="store_true", help="合言葉を作り直す")
    args = parser.parse_args()
    if args.data_root:
        br.DATA_ROOT = args.data_root.expanduser().resolve()
    token = load_token(args.new_token)
    pages, games = build()
    out = args.out.expanduser().resolve()
    write_site(out, token, pages, games)
    size = sum(p.stat().st_size for p in out.rglob("*") if p.is_file()) / 1024 / 1024
    print(f"{len(pages)}ページ・{size:.1f}MB → {out}")
    print(f"入口: /{token}/")


# ---------------------------------------------------------------- 書き出す中身

BLANK = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="robots" content="noindex,nofollow"><title></title></head><body></body></html>
"""

# 色は site_offline.THEME（--bg）と合わせる。打球図の色は build_report.spray_chart のクラスに当てる
CSS = """
:root{--bg:#0f1115;--card:#171a21;--line:#272c36;--text:#e8eaed;--dim:#9aa3b2;--accent:#4da3ff;--btn:#1f6fd1;
--warm:#ffb454;--jp:#2a1d22;--win:#4cc38a;--lose:#ff6b6b;--chip:#1e232c;--red:#d0103a;
--sp-field:#262b27;--sp-edge:#3d4a40;--sp-infield:#332c24;--sp-inedge:#4a3f33;--sp-guide:#7d8b80;
--sp-label:#9aa3b2;--sp-line:#8a968c;--sp-ground:#3987e5;--sp-liner:#d95926;--sp-fly:#199e70}
@media (prefers-color-scheme: light){:root{--bg:#f6f7f9;--card:#fff;--line:#e2e5ea;--text:#1b1f27;
--dim:#5f6878;--accent:#0b64c8;--btn:#0b64c8;--warm:#9a4f00;--jp:#fdecef;--win:#1d7f53;--lose:#c8102e;--chip:#f0f2f5;
--sp-field:#e3e9df;--sp-edge:#c3cdbf;--sp-infield:#ece1cf;--sp-inedge:#d3c3a8;--sp-guide:#8b978e;
--sp-label:#5f6878;--sp-line:#7a877d;--sp-ground:#2a78d6;--sp-liner:#c4501f;--sp-fly:#12805a}}
*{box-sizing:border-box}
[hidden]{display:none!important}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font-size:15px;line-height:1.6;
font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",sans-serif}
a{color:var(--accent);text-decoration:none}
header{display:flex;align-items:center;padding:0 6px 0 14px;border-bottom:1px solid var(--line);
position:sticky;top:0;z-index:5;background:var(--bg)}
.brand{display:inline-flex;align-items:center;min-height:44px;margin-right:auto;padding-right:6px;
color:var(--text);font-weight:700;font-size:15px;white-space:nowrap}
header nav{display:flex}
header nav a{display:inline-flex;align-items:center;justify-content:center;min-width:44px;min-height:44px;
padding:3px 8px 0;font-size:14px;
color:var(--text);white-space:nowrap;border-bottom:3px solid transparent}
header nav a[aria-current]{font-weight:700;border-bottom-color:var(--red)}
main{max-width:1100px;margin:0 auto;padding:6px 16px 48px}
h1{font-size:22px;line-height:1.35;margin:12px 0 8px}
h1 small{display:block;margin-top:2px;font-size:13px;color:var(--dim);font-weight:400}
h2{font-size:17px;margin:28px 0 8px;color:var(--warm);scroll-margin-top:56px}
h2 small,h3 small{margin-left:.5em;font-size:13px;color:var(--dim);font-weight:400}
h3{font-size:15px;margin:16px 0 6px}
h4{font-size:13px;margin:14px 0 6px;color:var(--dim)}
section{scroll-margin-top:56px}
p{margin:6px 0}
.note,.empty,.none{color:var(--dim);font-size:13px}
.crumb{margin:4px 0 0;font-size:14px}
.crumb a{display:inline-flex;align-items:center;min-height:44px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-top:10px}
.card>h2:first-child{margin-top:4px}
.warn{color:var(--warm);font-weight:700}
.ext{margin-left:6px;font-size:13px}
.ext::after{content:"↗";font-size:.8em;margin-left:1px}
.badge{display:inline-block;padding:0 7px;border-radius:4px;background:var(--chip);border:1px solid var(--line);
font-size:12px;font-weight:600}
.badge.alt{border-color:var(--lose);color:var(--lose)}
.badge.jpl{margin-left:8px;border-color:var(--warm);color:var(--warm);font-weight:500}
table{width:100%;border-collapse:separate;border-spacing:0;font-size:13px;font-variant-numeric:tabular-nums}
th,td{padding:6px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap;vertical-align:top}
tbody tr:last-child td{border-bottom:0}
th{color:var(--dim);font-weight:500;background:var(--card)}
.gwrap{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
table.games th,table.games td{text-align:left}
table.games td.t{width:1%}
table.games td.t b{font-size:14px}
table.games td.m{white-space:normal}
table.games td.m a{white-space:nowrap}
table.games small{display:block;color:var(--dim);font-size:12px}
table.games .lk .ext{display:inline-block;margin:-8px 14px -8px 0;padding:10px 0}
a.ext{padding-top:9px;padding-bottom:9px}
table.games td.m a,table.stand td a,table.roster td a{padding:9px 0}
table.roster td.rec a{display:inline-block;margin:-9px -12px;padding:9px 12px}
.sc{display:inline-block;min-width:2.4em;text-align:center;font-weight:700}
.tag{display:inline-block;margin-right:6px;padding:0 6px;border:1px solid var(--line);border-radius:4px;
font-size:11px;color:var(--dim);vertical-align:1px;white-space:nowrap}
.tag.sup,.tag.md{border-color:var(--warm);color:var(--warm)}
.fn{margin-left:2px;font-size:10px;color:var(--dim)}
.mk{margin-right:4px;font-weight:700}.mk.w{color:var(--win)}.mk.l{color:var(--lose)}
.live{margin-left:4px;padding:1px 6px;border-radius:4px;background:var(--red);color:#fff;font-size:11px;font-weight:700;
white-space:nowrap}
.inn{margin-left:4px;color:var(--dim);font-size:12px}
.st{display:inline-block;max-width:100%;margin-left:4px;padding:0 6px;border:1px solid var(--line);border-radius:4px;
color:var(--dim);font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;vertical-align:middle}
.nw{white-space:nowrap}
tr.jp td{background:var(--jp)}
.scroll{overflow:auto;-webkit-overflow-scrolling:touch;background:var(--card);border:1px solid var(--line);border-radius:10px}
.scroll.tall{max-height:75vh}
table.sort thead th,table.stand thead th{position:sticky;top:0;z-index:2}
table.sort th{cursor:pointer;-webkit-user-select:none;user-select:none}
table.sort th[aria-sort=ascending]::after{content:"▲";margin-left:2px;font-size:9px}
table.sort th[aria-sort=descending]::after{content:"▼";margin-left:2px;font-size:9px}
table.sort th:first-child,table.sort td:first-child,table.fix1 th:first-child,table.fix1 td:first-child{
position:sticky;left:0;z-index:1;background:var(--card);text-align:left;box-shadow:1px 0 0 var(--line)}
table.sort thead th:first-child,table.fix1 thead th:first-child{z-index:3}
td.nm{white-space:normal;min-width:7.5em;max-width:10em;line-height:1.35}
@media (min-width:768px){td.nm{min-width:160px;max-width:200px}}
.yomi{display:block;margin-top:1px;color:var(--dim);font-size:11.5px;font-weight:400;line-height:1.3}
h3 .yomi{display:inline;margin-left:.5em;font-size:13px}
.nmw{display:inline-block;max-width:calc(100% - 2.2em);vertical-align:top}
.tbd{color:var(--dim)}
td.cl,td.ev{white-space:normal;min-width:7em}
table.jpt{table-layout:fixed;min-width:47.5em}
table.jpt th,table.jpt td{text-align:left}
table.jpt td.nm,table.jpt td.cl{white-space:nowrap;max-width:none}
table.jpt td.cl{overflow:hidden;text-overflow:ellipsis}
.c-nm{width:9.6em}.c-pos{width:4.6em}.c-hand{width:5.4em}.c-age{width:4em}.c-size{width:8.8em}
td.app{text-align:left;line-height:1.35}
td.app small{display:block;color:var(--dim);font-size:11px}
table.log th small{color:var(--dim);font-size:11px}
tr.old td{color:var(--dim)}
main.fe tr[data-elig="0"],main.fp tr.few{display:none}
.b-el{margin-left:3px;color:var(--win);font-size:11px}
.b-ro{display:inline-block;margin-left:4px;padding:0 4px;border:1px solid var(--accent);border-radius:4px;
color:var(--accent);font-size:10.5px;line-height:1.4}
.tc{margin-left:4px;font-weight:400}
.filters{display:flex;flex-wrap:wrap;gap:0 18px;margin-top:6px}
.filters label{display:inline-flex;align-items:center;gap:8px;min-height:44px;cursor:pointer}
.filters input{width:20px;height:20px;margin:0}
table.plain th,table.plain td{text-align:left}
table.plain td small,table.rk td small{display:block;color:var(--dim);font-size:12px;white-space:normal}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px;margin-top:10px}
.two .card{margin-top:0}
.st h3{margin:0 0 6px;color:var(--warm)}
.st .scroll{border:0;border-radius:0}
table.stand th,table.stand td{padding:6px 7px}
table.stand td:first-child{min-width:9.6em}
.rk{display:inline-block;min-width:1.5em;color:var(--dim);font-weight:600}
table.fix1 tr.jp td:first-child{background:var(--jp)}
table.stand td small{display:block;max-width:12em;color:var(--dim);font-size:11px;white-space:normal}
table.stand tr.jp td{font-weight:700}
.hero{display:flex;flex-direction:column;gap:2px;margin-top:10px;padding:14px 16px;background:var(--card);
border:1px solid var(--line);border-left:5px solid var(--red);border-radius:10px;color:var(--text)}
.hero small{color:var(--dim);font-size:13px}
.hero .when{margin-left:8px;color:var(--warm);font-size:15px}
.hero.on .when{padding:0 6px;border-radius:4px;background:var(--red);color:#fff}
.hero .opp{font-size:22px}
.hero span{color:var(--dim);font-size:13px}
.hero .jst{color:var(--text);font-size:16px}
.prev{margin:10px 0 0;font-size:15px}
.prev small{margin-left:8px;color:var(--dim);font-size:12px}
.tgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px}
.tcard{display:flex;flex-direction:column;justify-content:center;min-height:60px;padding:8px 12px;
background:var(--card);border:1px solid var(--line);border-radius:8px;color:var(--text)}
.tcard span{font-weight:600;font-size:14.5px;white-space:nowrap}
.tcard small{color:var(--dim);font-size:12px;white-space:nowrap;line-height:1.4}
.go{display:flex;align-items:center;min-height:52px;margin-top:24px;color:var(--text);font-weight:600}
.save{width:15em;max-width:100%;min-height:44px;padding:0 12px;border:1px solid var(--btn);border-radius:8px;
background:var(--btn);color:#fff;font:inherit;font-weight:600;cursor:pointer;white-space:nowrap;
overflow:hidden;text-overflow:ellipsis}
.save:disabled{opacity:.6}
.save-st{min-height:1.5em;margin:4px 0 2px;color:var(--dim);font-size:12.5px}
.links .ext{display:inline-flex;align-items:center;min-height:44px;margin:0 18px 0 0;font-size:15px}
.facts{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;margin:8px 0}
.facts dt{padding-top:1px;color:var(--dim);font-size:13px;white-space:nowrap}
.facts dd{margin:0}
.facts small{color:var(--dim);font-size:12px}
.facts small.mn{display:block;line-height:1.45}
ul.notes{margin:8px 0;padding-left:1.2em;color:var(--dim);font-size:13px}
.toc{display:flex;gap:6px;overflow-x:auto;margin:10px -16px 0;padding:4px 16px;background:var(--bg)}
.toc a{flex:none;display:inline-flex;align-items:center;min-height:44px;padding:0 12px;
border:1px solid var(--line);border-radius:999px;font-size:13px;color:var(--text)}
@media (min-width:700px) and (min-height:600px){.toc{position:sticky;top:45px;z-index:4;border-bottom:1px solid var(--line)}
section{scroll-margin-top:110px}}
@media (max-height:599px){.scroll.tall{max-height:none}}
details{margin-top:10px;padding:0 14px;background:var(--card);border:1px solid var(--line);border-radius:10px}
details[open]{padding-bottom:12px}
summary{display:flex;align-items:center;gap:8px;min-height:48px;cursor:pointer;font-weight:700;
color:var(--warm);list-style:none}
summary::-webkit-details-marker{display:none}
summary::before{content:"▶";font-size:10px;color:var(--dim)}
details[open] summary::before{content:"▼"}
summary small{color:var(--dim);font-size:12px;font-weight:400}
.nb h3{margin:0 0 4px}
.nb ul{margin:4px 0;padding-left:1.2em}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}
.chip{padding:2px 9px;border:1px solid var(--line);border-radius:6px;background:var(--chip);font-size:13px}
.chip b{margin-right:6px;color:var(--dim);font-weight:500}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:8px;margin:8px 0}
.tile{padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bg)}
.tile b{display:block;font-size:24px;line-height:1.25;font-variant-numeric:tabular-nums}
.tile span{color:var(--dim);font-size:12px}
.sub{color:var(--dim);font-size:13px}
ul.apps{margin:4px 0;padding-left:1.2em}
.spray{margin:6px 0}
.spray-key{margin-right:5px;vertical-align:-2px}
.spray-note{margin:2px 0 0;color:var(--dim);font-size:12px}
.spray-field{fill:var(--sp-field);stroke:var(--sp-edge)}
.spray-infield{fill:var(--sp-infield);stroke:var(--sp-inedge)}
.spray-guide{stroke:var(--sp-guide)}
.spray-label{fill:var(--sp-label)}
.spray-line{stroke:var(--sp-line)}
.spray-dot{stroke:var(--sp-field)}
.spray-ground{fill:var(--sp-ground)}
.spray-liner{fill:var(--sp-liner)}
.spray-fly,.spray-pop{fill:var(--sp-fly)}
.seg{display:inline-flex;margin:6px 0;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{min-height:44px;padding:0 16px;border:0;background:var(--card);color:var(--text);font:inherit;cursor:pointer}
.seg button[aria-pressed=true]{background:var(--btn);color:#fff;font-weight:600}
.no{display:inline-block;min-width:2em;color:var(--dim)}
ol.flow{padding-left:1.4em}
h2.day{color:var(--text);font-size:16px}
h2.day small{margin-left:.8em}
.today{display:inline-block;margin-left:8px;padding:0 8px;border-radius:4px;background:var(--red);
color:#fff;font-size:12px;vertical-align:2px}
.days{display:flex;flex-wrap:wrap;gap:6px}
.days a{display:inline-flex;align-items:center;min-height:44px;padding:0 10px;border:1px solid var(--line);
border-radius:8px;font-size:13px;color:var(--text)}
footer{padding:20px 16px 32px;color:var(--dim);font-size:12px;text-align:center}
@media (max-width:600px){
table{font-size:13.5px}
.note,.empty,.none,.spray-note,ul.notes,.facts dt,.tile span,.sub,table.games small,
table.plain td small,table.rk td small,.hero small,.hero span{font-size:12px}
h1{font-size:20px}
}
@media (max-width:380px){header{padding-left:10px}.brand{font-size:14px}header nav a{padding:3px 6px 0;font-size:13.5px}}
"""

SITE_JS = r"""// U-23W杯 共有サイトの画面の動き。build_site.py が書き出す（手で直さない）。
// 並べ替え・絞り込み・次の日本戦・今日の試合・今日の見出しへの移動・登板間隔・日本代表の並び。
// URL に ?now=2026-11-08T12:00:00-06:00 を付けると「今」を差し替えて試せる。
(function () {
  var H = 3600000;
  var FIXED = (function () {  // ?now= で差し替えた「今」。なければ null
    var m = /[?&]now=([^&#]+)/.exec(location.search);
    var t = m ? Date.parse(decodeURIComponent(m[1])) : NaN;
    return isNaN(t) ? null : t;
  })();
  var NOW = FIXED === null ? Date.now() : FIXED;
  function dayAt(t, hours) { return new Date(t + hours * H).toISOString().slice(0, 10); }
  var LOCAL = dayAt(NOW, -6);  // ニカラグアは UTC-6（今日の試合と登板間隔は現地の日付で数える）
  var WEEK = "日月火水木金土";
  function md(iso) {
    var d = new Date(iso + "T00:00:00Z");
    return (d.getUTCMonth() + 1) + "/" + d.getUTCDate() + "(" + WEEK[d.getUTCDay()] + ")";
  }
  function gap(a, b) { return Math.round((Date.parse(b) - Date.parse(a)) / (24 * H)); }
  function $(id) { return document.getElementById(id); }
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  function all(sel) { return document.querySelectorAll(sel); }

  // ---- 並べ替え。1回目の向きは見出しの data-dir（成績は高い順、防御率などは低い順、名前は昇順）
  function key(td) {
    if (!td) return { s: "" };
    var s = td.getAttribute("data-sort");
    if (s === null) s = td.textContent.replace(/\s+/g, " ").trim();
    var n = parseFloat(s);
    return isNaN(n) || !/^[-+]?[\d.]/.test(s) ? { s: s } : { n: n };
  }
  function compare(a, b, dir) {
    var x = a.n !== undefined, y = b.n !== undefined;
    if (x && y) return dir * (a.n - b.n);
    if (x !== y) return x ? -1 : 1;  // 数のある行を先に。「-」や空は最後
    var e = !a.s || a.s === "-", f = !b.s || b.s === "-";
    if (e !== f) return e ? 1 : -1;
    return dir * a.s.localeCompare(b.s, "ja");
  }
  function sortable(table) {
    var heads = table.tHead ? table.tHead.rows[0].cells : [];
    each(heads, function (th, i) {
      th.tabIndex = 0;
      function go() {
        var was = th.getAttribute("aria-sort");
        var asc = was ? was === "descending" : th.getAttribute("data-dir") === "asc";
        each(heads, function (o) { o.removeAttribute("aria-sort"); });
        th.setAttribute("aria-sort", asc ? "ascending" : "descending");
        var body = table.tBodies[0];
        var rows = Array.prototype.map.call(body.rows, function (r, j) {
          return { r: r, k: key(r.cells[i]), j: j };
        });
        rows.sort(function (a, b) { return compare(a.k, b.k, asc ? 1 : -1) || a.j - b.j; });
        rows.forEach(function (o) { body.appendChild(o.r); });
      }
      th.addEventListener("click", go);
      th.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); }
      });
    });
  }
  each(all("table.sort"), sortable);

  // ---- 絞り込み（今大会に出られる選手だけ・10打席以上だけ）。隠すのは CSS のクラスで行う
  var main = document.querySelector("main"), fe = $("f-elig"), fp = $("f-pa");
  function filt() {
    if (fe) main.classList.toggle("fe", fe.checked);
    if (fp) main.classList.toggle("fp", fp.checked);
    var onE = main.classList.contains("fe"), onP = main.classList.contains("fp");
    each(all("table.sort"), function (table) {
      var shown = 0, total = 0;
      each(table.tBodies[0].rows, function (tr) {
        if (!tr.hasAttribute("data-elig")) return;
        total++;
        var hide = (onE && tr.getAttribute("data-elig") === "0") || (onP && tr.classList.contains("few"));
        if (!hide) shown++;
      });
      if (!total) return;
      var none = table.parentNode.nextElementSibling;
      if (none && none.classList.contains("none")) none.hidden = shown > 0;
      var count = document.querySelector('.tc[data-t="' + table.id + '"]');
      if (count) count.textContent = "（" + shown + "/" + total + "人）";
    });
  }
  if (fe || fp) {
    [fe, fp].forEach(function (b) { if (b) b.addEventListener("change", filt); });
    filt();
  }

  // ---- 次の日本戦。開いた時刻で「あと4時間」「あと2日5時間」「試合中」「終了」を出し分ける。
  // 「今日／明日」は日本と現地で日付がずれる（現地の朝は日本の夜）ので使わず、残り時間で出す。
  // 日時そのものは、すぐ下に日本時間と現地の両方が出ている
  function left(ms) {
    var m = Math.max(1, Math.ceil(ms / 60000));
    var d = Math.floor(m / 1440), h = Math.floor((m % 1440) / 60), mm = m % 60;
    if (d >= 3) return "あと" + d + "日";
    if (d >= 1) return "あと" + d + "日" + (h ? h + "時間" : "");
    if (h >= 1) return "あと" + h + "時間" + (mm ? mm + "分" : "");
    return "あと" + mm + "分";
  }
  var hero = $("next-jp"), list = $("jp-games");
  function heroAt(now) {
    var games = JSON.parse(list.textContent).filter(function (g) { return !g.done; });
    var pick = null;
    for (var i = 0; i < games.length && !pick; i++) {
      if (now < Date.parse(games[i].t) + 4 * H) pick = games[i];
    }
    var g = pick || games[games.length - 1], t = Date.parse(g.t), when;
    if (!pick) when = "終了（結果は次の更新で入ります）";
    else if (now >= t) when = "試合中";
    else when = left(t - now);
    hero.href = g.href;
    hero.setAttribute("data-start", g.t);
    hero.querySelector(".opp").textContent = "日本 vs " + g.opp;
    hero.querySelector(".jst").textContent = g.jst;
    hero.querySelector(".local").textContent = "現地 " + g.local;
    hero.querySelector(".venue").textContent = g.venue;
    $("next-when").textContent = when;
    hero.classList.toggle("on", when === "試合中");
  }
  if (hero && list) {
    heroAt(NOW);
    if (FIXED === null) setInterval(function () { heroAt(Date.now()); }, 60000);  // 開いたままでも進める
  }

  // ---- 今日の試合（現地の日付で選ぶ）
  var today = $("today");
  if (today) {
    var hit = 0, next = "";
    each(today.querySelectorAll("tr[data-day]"), function (tr) {
      var d = tr.getAttribute("data-day");
      if (d === LOCAL) { tr.hidden = false; hit++; }
      else if (d > LOCAL && (!next || d < next)) next = d;
    });
    $("today-day").textContent = "現地 " + md(LOCAL);
    if (!hit) {
      var wrap = today.querySelector(".gwrap"), msg = $("today-msg");
      if (wrap) wrap.hidden = true;
      msg.hidden = false;
      msg.textContent = "この日の試合はありません。" + (next ? "次の試合は 現地 " + md(next) + " からです。" : "");
    }
  }

  // ---- 日程: 今日（現地）の見出しに印を付け、そこまで送る
  each(all("h2.day"), function (h) {
    if ((" " + h.getAttribute("data-local") + " ").indexOf(" " + LOCAL + " ") < 0) return;
    var b = document.createElement("span");
    b.className = "today";
    b.textContent = "今日（現地）";
    h.appendChild(b);
    if (!location.hash) h.scrollIntoView();
  });

  // ---- 投手の登板記録: 今日（現地）投げるとしたら中何日か
  each(all("[data-last]"), function (td) {
    var last = td.getAttribute("data-last");
    if (!last) return;
    var n = gap(last, LOCAL) - 1;
    td.textContent = n < -1 ? "-" : n === -1 ? "今日登板" : "中" + n + "日";
    td.setAttribute("data-sort", n < -1 ? "" : String(n));
  });

  // ---- 切り替え（投手・野手など）。role=tab の aria-selected と、同じ data-seg のパネルの hidden。
  // URL の #p / #b（ボタンの data-seg）で開く方を覚える
  each(all(".seg[role=tablist]"), function (seg) {
    var tabs = seg.querySelectorAll("[role=tab][data-seg]"), keys = {};
    if (!tabs.length) return;
    each(tabs, function (t) { keys[t.getAttribute("data-seg")] = true; });
    var panels = [];
    each(seg.parentNode.querySelectorAll(".seg-panel[data-seg]"), function (p) {
      if (keys[p.getAttribute("data-seg")]) panels.push(p);
    });
    function show(key, remember) {
      if (!keys[key]) return;
      each(tabs, function (t) {
        t.setAttribute("aria-selected", t.getAttribute("data-seg") === key ? "true" : "false");
      });
      each(panels, function (p) { p.hidden = p.getAttribute("data-seg") !== key; });
      if (remember && history.replaceState) {
        try { history.replaceState(null, "", location.pathname + location.search + "#" + key); } catch (e) {}
      }
    }
    each(tabs, function (t) {
      t.addEventListener("click", function () { show(t.getAttribute("data-seg"), true); });
    });
    var h = location.hash.slice(1);
    if (h) show(decodeURIComponent(h), false);
  });

  // ---- 日本代表: 背番号順と守備別の切り替え（data-show のボタンだけ）
  each(all(".seg button[data-show]"), function (b) {
    b.addEventListener("click", function () {
      each(b.parentNode.querySelectorAll("button[data-show]"), function (o) {
        var on = o === b, target = $(o.getAttribute("data-show"));
        o.setAttribute("aria-pressed", on ? "true" : "false");
        if (target) target.hidden = !on;
      });
    });
  });
})();
"""
JS_VERSION = hashlib.sha1(SITE_JS.encode("utf-8")).hexdigest()[:8]

# 見た目は site_theme.py（CSS の文字列）に任せる。読めなければ上の CSS のまま
try:
    from site_theme import CSS as _THEME_CSS
    if isinstance(_THEME_CSS, str) and _THEME_CSS.strip():
        CSS = _THEME_CSS
except Exception as error:  # 部品が壊れていてもサイトは今の見た目で書き出す
    print(f"注意: site_theme.py が読めないので、今の見た目で書き出します（{error}）", file=sys.stderr)


if __name__ == "__main__":
    main()
