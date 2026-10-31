#!/usr/bin/env python3
"""韓国U-23代表のうち、KBOの1軍に出た選手の打席だけを、SOOPの見逃しから打席ごとの動画にする道具。

試合の一覧・打席の並び・途中のファイル・動画は ~/野球/U23ワールドカップ2026/04_対戦国/韓国/KBO映像/ に置く
（選手の映像なのでリポジトリに入れない）。計画は plans/2026-10-31-u23-korea-kbo-clips.md。

    python3 kbo_clips.py games                 # KBO公式の日別の記録 → 選手.csv・試合.json（出た試合）
    python3 kbo_clips.py soop                  # SOOPの見逃しを試合に結びつける（ビジター・ホームと試合番号も決まる）
    python3 kbo_clips.py relay [--game ID]     # KBO公式の文字中継 → <試合>/打席_KBO.csv（全打席の並び、対象に印）
    python3 kbo_clips.py locate [--game ID]    # 540pの静止画の帯の投手名・打者名で、対象の打席の場面を探す → 打席_映像.csv
    python3 kbo_clips.py cut [--game ID]       # 720pで対象の打席だけ取り、clips/<選手>/ に打席ごとの動画を書く
    python3 kbo_clips.py check [--game ID]     # 動画の頭と終わりの静止画で、打者・投手が合うか確かめる
    python3 kbo_clips.py index                 # BASSに入れる順の 一覧.csv・一覧.html
    python3 kbo_clips.py run [--player 名前]   # relay→locate→cut→check を試合ごとに続けて流す（できた試合は飛ばす）

打席の正解はKBO公式の文字中継で、映像からは「その打席が何秒から何秒か」だけを取る。
場面は、静止画を丸ごと文字認識にかけ、その試合に出た選手の名前（投手と打者の組み）で決める。
放送局ごとの画面の作りは覚えさせていない。作業中に動画は再生しない（静止画は ffmpeg の -an で作る）。
"""

from __future__ import annotations

import argparse
import csv
import html
import http.cookiejar
import json
import re
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path.home() / "野球" / "U23ワールドカップ2026"
DATA = ROOT / "04_対戦国" / "韓国" / "KBO映像"
CLIPS = DATA / "clips"
REPO = Path(__file__).resolve().parents[2]
BASS_LIST = REPO / "private" / "u23-bass" / "BASS登録一覧_20261026.csv"
OCR_SRC = Path(__file__).resolve().parent / "ocr_frames.swift"
OCR_BIN = Path.home() / ".cache" / "kbo_clips" / "ocr_frames"
YEAR = "2026"

KBO = "https://www.koreabaseball.com"
SOOP_LIST = "https://chapi.sooplive.co.kr/api/{ch}/vods/review?keyword=&orderby=reg_date&perPage=20&field=title,contents,user_nick,user_id&page={page}&start_date=&end_date="
SOOP_VIEW = "https://api.m.sooplive.co.kr/station/video/a/view"
SOOP_CHANNELS = ["kboglobal1", "kboglobal2", "kboglobal3", "kboglobal4", "kboglobal5"]

# 球団：KBOの記号、韓国語（KBO公式）、日本語（BASS登録一覧）、英語（SOOPの題名）
TEAMS = [
    ("LG", "LG", "LG", "LG"), ("OB", "두산", "斗山", "DOOSAN"), ("SK", "SSG", "SSG", "SSG"),
    ("HT", "KIA", "KIA", "KIA"), ("SS", "삼성", "サムスン", "SAMSUNG"), ("LT", "롯데", "ロッテ", "LOTTE"),
    ("NC", "NC", "NC", "NC"), ("HH", "한화", "ハンファ", "HANWHA"), ("KT", "KT", "KT", "KT"),
    ("WO", "키움", "キウム", "KIWOOM"),
]
BY_KO = {ko: code for code, ko, ja, en in TEAMS}
BY_JA = {ja: code for code, ko, ja, en in TEAMS}
BY_EN = {en: code for code, ko, ja, en in TEAMS}
KO_OF = {code: ko for code, ko, ja, en in TEAMS}

# 1球の結果（文字中継の言葉 → 一覧の記号）
PITCH_MARK = {"볼": "B", "스트라이크": "S", "헛스윙": "W", "파울": "F", "타격": "X",
              "번트파울": "F", "번트헛스윙": "W", "몸에 맞는 볼": "H", "자동 고의4구": "I", "고의4구": "I"}

BEFORE = 5.0   # 打席の始まりの前に足す秒
AFTER = 3.0    # 次の打者に替わったあとに足す秒
COARSE = 15    # 見取り図で何小片おきに調べるか（6秒×15＝約90秒）
HEAD_BYTES = 80_000  # 静止画1枚のために取る小片の頭の大きさ（540pの小片は約0.75MB）

PA_FIELDS = ["no", "inning", "half", "bat_team", "order", "batter", "pit_team", "pitcher", "pitchers",
             "n_pitch", "pitches", "result", "complete", "pit_before", "pit_after", "targets"]
LOC_FIELDS = ["no", "inning", "half", "batter", "pitcher", "n_pitch", "targets", "start", "end",
              "seg_first", "seg_last", "status", "check", "files"]


# ---------------------------------------------------------------- 通信


_jar = http.cookiejar.CookieJar()
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_jar))


def fetch(url: str, data: dict | bytes | None = None, tries: int = 3, headers: dict | None = None) -> bytes:
    body = urllib.parse.urlencode(data).encode() if isinstance(data, dict) else data
    for i in range(tries):
        try:
            with _opener.open(urllib.request.Request(url, data=body, headers=headers or {}), timeout=60) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))
    raise RuntimeError(url)


def clean(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


# ---------------------------------------------------------------- 置き場


def game_dir(gid: str) -> Path:
    d = DATA / gid
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_games() -> list[dict]:
    p = DATA / "試合.json"
    return json.loads(p.read_text(encoding="utf-8"))["games"] if p.exists() else []


def save_games(games: list[dict], note: str | None = None) -> None:
    p = DATA / "試合.json"
    old = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    out = {"_note": note or old.get("_note", ""), "games": games}
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


def load_players() -> list[dict]:
    with open(DATA / "選手.csv", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def pick(games: list[dict], gid: str | None, player: str | None = None) -> list[dict]:
    out = [g for g in games if (not gid or g["id"] == gid or g.get("kbo_id") == gid)]
    if player:
        out = [g for g in out if player in g["targets"]]
    return out


# ---------------------------------------------------------------- games：出た試合


def daily_rows(kind: str, pid: str) -> tuple[list[str], list[list[str]]]:
    """KBO公式の日別の記録（レギュラーシーズン）。開くとポストシーズンが選ばれているので送り直す。"""
    url = f"{KBO}/Record/Player/{kind}Detail/Daily.aspx?playerId={pid}"
    t = fetch(url).decode("utf-8", "replace")
    hidden = dict(re.findall(r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"', t))
    hidden = {k: html.unescape(v) for k, v in hidden.items()}
    sel = dict((n.split("$")[-1], n) for n in re.findall(r'<select name="([^"]+)"', t))
    hidden[sel["ddlYear"]] = YEAR
    hidden[sel["ddlSeries"]] = "0"
    hidden["__EVENTTARGET"] = sel["ddlSeries"]
    hidden["__EVENTARGUMENT"] = ""
    t2 = fetch(url, hidden).decode("utf-8", "replace")
    head: list[str] = []
    rows: list[list[str]] = []
    for tb in re.findall(r"<table.*?</table>", t2, re.S):
        if not head:
            head = [clean(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", tb, re.S)]
        for tr in re.findall(r"<tbody>.*?</tbody>", tb, re.S):
            for row in re.findall(r"<tr[^>]*>(.*?)</tr>", tr, re.S):
                cells = [clean(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
                if len(cells) > 3:
                    rows.append(cells)
    return head, rows


def cmd_games(_args) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    with open(BASS_LIST, encoding="utf-8-sig") as f:
        roster = [r for r in csv.DictReader(f) if r["チーム"] == "KOR"]
    players = []
    games: dict[tuple, dict] = {}
    for r in roster:
        m = re.search(r"koreabaseball\.com/.*?(Pitcher|Hitter)Detail.*?playerId=(\d+)", r["投打の出典"])
        if not m or r["所属"] not in BY_JA:
            continue  # 大学・尚武（KBO1軍の記録がない）
        kind, pid = m.group(1), m.group(2)
        team = BY_JA[r["所属"]]
        head, rows = daily_rows(kind, pid)
        col = head.index("TBF" if kind == "Pitcher" else "PA") if head else -1
        played = [c for c in rows if col >= 0 and (int(c[col]) if c[col].isdigit() else 0) > 0]
        players.append({"name": r["発表の表記"], "bass": r["名前（登録）"], "team": team, "team_ko": KO_OF[team],
                        "kind": "投手" if kind == "Pitcher" else "打者", "kbo_id": pid,
                        "games": len(rows), "with_pa": len(played),
                        "pa": sum(int(c[col]) for c in played), "target": "1" if played else ""})
        for c in played:
            mm, dd = c[0].split(".")
            opp = BY_KO.get(c[1])
            if not opp:
                print(f"  ! {r['発表の表記']} {c[0]} 相手が読めない: {c[1]}")
                continue
            key = (f"{YEAR}{mm}{dd}", tuple(sorted([team, opp])))
            g = games.setdefault(key, {"date": key[0], "teams": list(key[1]), "targets": {}, "n": 0})
            g["targets"][r["発表の表記"]] = {"kind": players[-1]["kind"], "team": team, "pa": int(c[col])}
            g["n"] += 1
        print(f"  {r['発表の表記']}（{r['所属']}・{players[-1]['kind']}）: 1軍 {len(rows)}試合、打席/対戦打者のある試合 {len(played)}")
    write_csv(DATA / "選手.csv", ["name", "bass", "team", "team_ko", "kind", "kbo_id", "games", "with_pa", "pa", "target"], players)
    old = {g["id"]: g for g in load_games()}
    out = []
    for (date, teams), g in sorted(games.items()):
        gid = f"{date}_{'-'.join(teams)}"
        prev = old.get(gid, {})
        out.append({**prev, "id": gid, "date": date, "teams": list(teams), "targets": g["targets"]})
    save_games(out, "KBO公式の日別の記録（2026年レギュラーシーズン）で、対象の選手が打席に立つか打者と対戦した試合。"
                    "away・home・kbo_id・soop は soop で付く。")
    tg = [p for p in players if p["target"]]
    print(f"対象 {len(tg)}人、試合 {len(out)}（{DATA / '試合.json'}）")


# ---------------------------------------------------------------- soop：見逃しを結びつける


def soop_list(refresh: bool = False) -> list[dict]:
    cache = DATA / "soop一覧.json"
    if cache.exists() and not refresh and time.time() - cache.stat().st_mtime < 12 * 3600:
        return json.loads(cache.read_text(encoding="utf-8"))
    vods = []
    for ch in SOOP_CHANNELS:
        page = 1
        while True:
            d = json.loads(fetch(SOOP_LIST.format(ch=ch, page=page)))
            for x in d.get("data", []):
                vods.append({"ch": ch, "title_no": x["title_no"], "title": x["title_name"], "reg_date": x["reg_date"],
                             "sec": round(x["ucc"]["total_file_duration"] / 1000)})
            meta = d.get("meta") or {}
            if not d.get("data") or page >= int(meta.get("last_page") or 1):
                break
            page += 1
            time.sleep(0.3)
    cache.write_text(json.dumps(vods, ensure_ascii=False, indent=0), encoding="utf-8")
    return vods


def parse_title(t: str):
    m = re.search(r"([A-Z]+)\s+vs\s+([A-Z]+)\s+Live[_ ]*(\d{8})", t)
    if not m or m.group(1) not in BY_EN or m.group(2) not in BY_EN:
        return None
    return BY_EN[m.group(1)], BY_EN[m.group(2)], m.group(3)


def cmd_soop(args) -> None:
    vods = soop_list(args.refresh)
    by_key: dict[tuple, list[dict]] = {}
    for v in vods:
        p = parse_title(v["title"])
        if p:
            away, home, date = p
            by_key.setdefault((date, tuple(sorted([away, home]))), []).append({**v, "away": away, "home": home})
    games = load_games()
    miss = []
    for g in games:
        cand = sorted(by_key.get((g["date"], tuple(g["teams"])), []), key=lambda v: v["sec"], reverse=True)
        if not cand:
            miss.append(g["id"])
            continue
        v = cand[0]
        if len(cand) > 1:
            g["soop_others"] = [c["title_no"] for c in cand[1:]]
        g["away"], g["home"] = v["away"], v["home"]
        g["kbo_id"] = f"{g['date']}{v['away']}{v['home']}0"
        g["soop"] = {"title_no": v["title_no"], "title": v["title"], "sec": v["sec"], "ch": v["ch"]}
    save_games(games)
    print(f"見逃し {len(vods)}本を読み、{len(games) - len(miss)}/{len(games)}試合に結びつけた")
    for gid in miss:
        print(f"  ! 見つからない: {gid}")
    for g in games:
        if g.get("soop_others"):
            print(f"  ! 同じ日・同じ対戦が複数（ダブルヘッダーか撮り直し）: {g['id']} → 長いものを使用 {g['soop']['title_no']}")


# ---------------------------------------------------------------- relay：打席の並び


def relay_raw(kbo_id: str) -> str:
    """文字中継の全イニングと出場選手表（LiveText.aspx が中で呼んでいるもの）。1回の問い合わせで1試合分が来る。"""
    return fetch(f"{KBO}/Game/LiveTextView2.aspx",
                 {"leagueId": "1", "seriesId": "0", "gameId": kbo_id, "gyear": YEAR}).decode("utf-8", "replace")


def relay_lines(raw: str) -> list[tuple[str, str]]:
    """（種類, 文）の古い順の並び。ページの中では回ごとに新しい順に並んでいる。"""
    lines = []
    for n in range(1, 11):
        m = re.search(r'id="numCont%d".*?(?=id="numCont%d")' % (n, n + 1), raw, re.S)
        if not m:
            continue
        spans = re.findall(r'spanLiveText_\d+" class="([^"]*)">(.*?)</span>', m.group(0), re.S)
        lines += [(c, clean(x)) for c, x in spans][::-1]
    return lines


def pitcher_box(raw: str) -> dict[str, list[tuple[str, int]]]:
    """文字中継のHTMLにある出場選手表から、チームごとの投手（登板順、投球数）。lineup1 がビジター、lineup2 がホーム。"""
    out = {}
    for side, lid in (("away", "lineup1"), ("home", "lineup2")):
        i = raw.find(f'id="{lid}"')
        seg = raw[i:raw.find("btnClose", i)] if i >= 0 else ""
        for tb in re.findall(r"<table.*?</table>", seg, re.S):
            head = [clean(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", tb, re.S)]
            if not head or head[0] != "투수":
                continue
            col = head.index("투구") if "투구" in head else -1
            rows = [[clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
                    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", tb, re.S)]
            out[side] = [(r[0], int(r[col]) if col >= 0 and r[col].isdigit() else -1) for r in rows if r]
    return out


def parse_relay(lines: list[tuple[str, str]], away: str, home: str, box: dict) -> list[dict]:
    pas: list[dict] = []
    # 守っているチームごとの今の投手。出だしは出場選手表の先頭（先発）
    pitcher = {away: (box.get("away") or [("?", 0)])[0][0], home: (box.get("home") or [("?", 0)])[0][0]}
    count = {}                           # 投手ごとの累計の球数
    cur = None
    half = inning = bat = pit = None
    for cls, s in lines:
        m = re.match(r"(\d+)회([초말]) (.+) 공격", s)
        if m:
            inning, half = int(m.group(1)), m.group(2)
            bat = away if half == "초" else home
            pit = home if bat == away else away
            cur = None
            continue
        # 投手交代。「투수 A : 투수 B」のほか、「우익수 A : 투수 B」（野手の枠からの交代）でも来る
        m = re.match(r"\S+ \S+ : 투수 (\S+) \(으\)로 교체", s)
        if m and pit:
            pitcher[pit] = m.group(1)
            continue
        # 代打。打者の見出し（N번타자 A）のあとに来るので、今の打席の打者を差し替える
        m = re.match(r"(\d)번타자 (\S+) : 대타 (\S+) \(으\)로 교체", s)
        if m:
            if cur is not None and cur["batter"] == m.group(2) and not cur["result"]:
                cur["pinch_for"] = cur["batter"]
                cur["batter"] = m.group(3)
            continue
        m = re.match(r"(\d)번타자 (\S+)$", s)
        if m and bat:
            cur = {"no": len(pas) + 1, "inning": inning, "half": half, "bat_team": bat, "order": int(m.group(1)),
                   "batter": m.group(2), "pit_team": pit, "pitchers": [], "marks": [], "result": ""}
            pas.append(cur)
            continue
        m = re.match(r"- (\d+)구 (.+)$", s)
        if m and cur is not None:
            cur["marks"].append(PITCH_MARK.get(m.group(2).strip(), m.group(2).strip()))
            cur["pitchers"].append(pitcher[pit])
            continue
        if cur is not None and not cur["result"]:
            m = re.match(r"(\S+) : (.+)$", s)
            if m and m.group(1) == cur["batter"]:
                cur["result"] = m.group(2)
                cur["at_end"] = pitcher[pit]
    for p in pas:
        pit_list = p["pitchers"]
        # 1球もない打席（申告敬遠など）は、結果の時点の投手
        p["pitcher"] = pit_list[-1] if pit_list else p.get("at_end") or pitcher.get(p["pit_team"], "?")
        p["n_pitch"] = len(p["marks"])
        p["pitches"] = " ".join(p["marks"])
        key = (p["pit_team"], p["pitcher"])
        p["pit_before"] = count.get(key, 0)   # 帯に出る投球数と照らすため、この打席の前後の累計を持つ
        for x in pit_list:
            count[(p["pit_team"], x)] = count.get((p["pit_team"], x), 0) + 1
        p["pit_after"] = count.get(key, 0)
        p["pitchers"] = "/".join(dict.fromkeys(pit_list or [p["pitcher"]]))
        # 結果の行がない打席は、走者アウトなどで回が終わり、打席が成立しなかったもの（次の回に持ち越し）
        p["complete"] = "1" if p["result"] else ""
        if not p["result"]:
            p["result"] = "（打席不成立：回の終わり）"
        if p.get("pinch_for"):
            p["result"] = f"{p['result']}（{p['pinch_for']}の代打）"
    return pas, count


def pitch_check(count: dict, box: dict, away: str, home: str) -> list[str]:
    """文字中継で数えた投手ごとの球数を、出場選手表の投球数と比べる。合わない投手を返す。"""
    bad = []
    for side, team in (("away", away), ("home", home)):
        for name, n in box.get(side, []):
            if n >= 0 and count.get((team, name), 0) != n:
                bad.append(f"{name} 表{n}・中継{count.get((team, name), 0)}")
    return bad


def mark_targets(pas: list[dict], g: dict) -> None:
    """対象の選手が打者か投手の打席に印を付ける。投手は、打席の途中で替わった場合も両方に付ける。"""
    for p in pas:
        tg = []
        for name, t in g["targets"].items():
            if t["kind"] == "打者" and p["batter"] == name and p["bat_team"] == t["team"]:
                tg.append(name)
            if t["kind"] == "投手" and p["pit_team"] == t["team"] and name in p["pitchers"].split("/"):
                tg.append(name)
        p["targets"] = "/".join(tg)


def cmd_relay(args) -> None:
    games = load_games()
    bad = 0
    for g in pick(games, args.game, args.player):
        if not g.get("kbo_id"):
            print(f"  ! {g['id']}: 試合番号がない（先に soop）")
            continue
        gd = game_dir(g["id"])
        cache = gd / "文字中継.html"
        if args.force or not cache.exists():
            cache.write_text(relay_raw(g["kbo_id"]), encoding="utf-8")
            time.sleep(0.5)
        raw = cache.read_text(encoding="utf-8")
        box = pitcher_box(raw)
        pas, count = parse_relay(relay_lines(raw), g["away"], g["home"], box)
        mark_targets(pas, g)
        write_csv(gd / "打席_KBO.csv", PA_FIELDS, pas)
        note = []
        for name, t in g["targets"].items():
            # 公式の記録と比べるのは、成立した打席（投手はその打席の最後の投手）だけ
            n = sum(1 for p in pas if p["complete"] and name in p["targets"].split("/")
                    and (t["kind"] == "打者" or p["pitcher"] == name))
            if n != t["pa"]:
                note.append(f"{name} 記録{t['pa']}・中継{n}")
        pitch_bad = pitch_check(count, box, g["away"], g["home"])
        g["relay_pa"] = len(pas)
        g["relay_ok"] = not note
        g["relay_pitch_diff"] = pitch_bad
        if not pas:
            note.append("文字中継が空")
        if note:
            bad += 1
            print(f"  ! {g['id']}: 打席数が合わない（{'、'.join(note)}）")
        else:
            print(f"  {g['id']}: 全{len(pas)}打席、対象 {sum(1 for p in pas if p['targets'])}打席"
                  + (f"、球数の合わない投手 {'、'.join(pitch_bad)}" if pitch_bad else ""))
    save_games(games)
    if bad:
        print(f"打席数の合わない試合 {bad}")


# ---------------------------------------------------------------- 映像（SOOP）


def manifest(title_no: int | str, label: str) -> tuple[str, list[float], list[str], str]:
    """動画の目次。返すのは（initのURL、小片の始まりの秒、小片のURL、目次のURL）。目次のURLは期限つきなので保存しない。"""
    info = json.loads(fetch(SOOP_VIEW, {"nTitleNo": str(title_no), "nApiLevel": "11", "nPlaylistIdx": "0"}))
    files = info["data"]["files"]
    q = next(q for q in files[0]["quality_info"] if q.get("label") == label)
    murl = q["file"]
    text = fetch(murl).decode()
    init, starts, segs, t, dur = "", [], [], 0.0, 0.0
    for line in (x.strip() for x in text.splitlines()):
        if line.startswith("#EXT-X-MAP:"):
            init = urllib.parse.urljoin(murl, line.split('URI="', 1)[1].split('"', 1)[0])
        elif line.startswith("#EXTINF:"):
            dur = float(line[8:].split(",")[0])
        elif line and not line.startswith("#"):
            starts.append(t)
            segs.append(urllib.parse.urljoin(murl, line))
            t += dur
    starts.append(t)  # 終わり
    if len(files) > 1:
        print(f"  ! 見逃しが{len(files)}つに分かれている。最初の1つだけ使う")
    return init, starts, segs, murl


class Video:
    """1本の見逃しの小片を、必要な分だけ取って静止画にする。小片は一時フォルダに置き、静止画にしたら消す。"""

    def __init__(self, title_no, label: str, tmp: Path):
        self.init_url, self.starts, self.segs, _ = manifest(title_no, label)
        self.tmp = tmp
        self.init = tmp / f"init_{label}.mp4"
        self.init.write_bytes(fetch(self.init_url))
        self.got = 0
        self._lock = threading.Lock()

    def n(self) -> int:
        return len(self.segs)

    def seg_file(self, i: int) -> Path:
        p = self.tmp / f"seg_{i:05d}.m4s"
        if not p.exists():
            data = fetch(self.segs[i])
            p.write_bytes(data)
            with self._lock:
                self.got += len(data)
        return p

    def frame(self, i: int) -> Path:
        """小片 i の最初の1コマ（キーフレーム）の静止画。小片の頭の HEAD_BYTES だけ取れば足りる
        （10/31に確認：60KBで1コマ目が出る）。音は扱わない（-an）。"""
        png = self.tmp / f"f_{i:05d}.png"
        if png.exists():
            return png
        data = fetch(self.segs[i], headers={"Range": f"bytes=0-{HEAD_BYTES - 1}"})
        with self._lock:
            self.got += len(data)
        mp4 = self.tmp / f"one_{i:05d}.mp4"
        mp4.write_bytes(self.init.read_bytes() + data)
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", str(mp4), "-an", "-frames:v", "1", str(png)], check=False)
        mp4.unlink(missing_ok=True)
        return png

    def frames(self, idx: list[int]) -> dict[int, Path]:
        with ThreadPoolExecutor(max_workers=6) as ex:
            return dict(zip(idx, ex.map(self.frame, idx)))


# ---------------------------------------------------------------- 文字認識


def ocr_bin() -> Path:
    if not OCR_BIN.exists() or OCR_BIN.stat().st_mtime < OCR_SRC.stat().st_mtime:
        OCR_BIN.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["swiftc", "-O", "-o", str(OCR_BIN), str(OCR_SRC)], check=True)
    return OCR_BIN


def ocr(files: list[Path]) -> dict[str, list[dict]]:
    files = [f for f in files if f.exists()]
    if not files:
        return {}
    out = subprocess.run([str(ocr_bin()), *map(str, files)], capture_output=True, text=True, check=False).stdout
    res = {}
    for line in out.splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        res[d["file"]] = d["lines"]
    return res


HANGUL = re.compile(r"[가-힣]{2,6}")


def names_in(lines: list[dict], names: set[str]) -> dict[str, float]:
    """読めた文字から、その試合の選手の名前を探す。名前→確からしさ（完全一致1、1文字違い0.5）。
    540pでは「어준서」が「이준서」と読まれるような1文字の読み違いがあるので、3文字以上の名前は1文字違いまで拾う。"""
    text = " ".join(l["text"] for l in lines)
    found = {n: 1.0 for n in names if n in text}
    # ほかの選手の名前そのものの文字は除く（投手「김서현」を打者「김재현」の読み違いと取らないため）
    toks = {t for t in HANGUL.findall(text) if t not in names}
    for n in names:
        if n in found or len(n) < 3:
            continue
        if any(len(t) == len(n) and sum(x != y for x, y in zip(t, n)) == 1 for t in toks):
            found[n] = 0.5
    return found


def numbers_in(lines: list[dict]) -> set[int]:
    return {int(x) for l in lines for x in re.findall(r"(?<![\d.])(\d{1,3})(?![\d.])", l["text"])}


# ---------------------------------------------------------------- locate：打席の場面を探す


def candidates(pas: list[dict], found: dict[str, float], nums: set[int]) -> dict[int, float]:
    """静止画に写っている名前から、どの打席の場面か（打席の番号→点数）。打者が写っていることが前提で、
    投手も写っていれば足し、帯の投球数がその打席の投手の累計の範囲に入っていればさらに足す。"""
    out = {}
    for i, p in enumerate(pas):
        b = found.get(p["batter"], 0.0)
        if not b:
            continue
        pitchers = [x for x in p["pitchers"].split("/") if x] or [p["pitcher"]]
        pt = max(found.get(x, 0.0) for x in pitchers)
        s = b + pt
        if pt and any(int(p["pit_before"]) <= n <= int(p["pit_after"]) for n in nums):
            s += 0.5
        out[i] = s
    return out


def assign(probes: list[dict]) -> None:
    """時刻順の静止画に打席の番号を割り当てる。時刻が進むほど番号も進む（同じか増える）並びのうち、点数の合計が
    最大のもの。打席は100前後、静止画は数百なので、「最後に選んだ番号ごとの最良」を持つ動的計画で足りる。"""
    for p in probes:
        p["pa"] = None
    pts = sorted((p for p in probes if p["cands"]), key=lambda r: r["seg"])
    table: dict[int, tuple[float, list[tuple[int, int]]]] = {}
    for j, p in enumerate(pts):
        new = dict(table)
        for k, s in p["cands"].items():
            prev = max((v for kk, v in table.items() if kk <= k), default=(0.0, []), key=lambda v: v[0])
            cand = (prev[0] + s, prev[1] + [(j, k)])
            if k not in new or cand[0] > new[k][0]:
                new[k] = cand
        table = new
    if table:
        for j, k in max(table.values(), key=lambda v: v[0])[1]:
            pts[j]["pa"] = k


def look(v: Video, idx: list[int], pas: list[dict], names: set[str], log: dict[int, dict]) -> None:
    """小片 idx の静止画をまとめて読み、log（小片→結果）に足す。読んだ小片は飛ばす。"""
    idx = sorted({i for i in idx if 0 <= i < v.n() and i not in log})
    for c in range(0, len(idx), 60):
        chunk = idx[c:c + 60]
        pngs = v.frames(chunk)
        res = ocr(list(pngs.values()))
        for i, png in pngs.items():
            lines = res.get(str(png), [])
            found = names_in(lines, names)
            log[i] = {"seg": i, "sec": round(v.starts[i] + 3, 1),
                      "names": "/".join(f"{n}{'' if s == 1 else '?'}" for n, s in sorted(found.items())),
                      "cands": candidates(pas, found, numbers_in(lines)), "pa": None}
            png.unlink(missing_ok=True)


def bracket(log: dict[int, dict], k: int, n: int) -> tuple[int, int]:
    """打席 k の場面がありうる小片の範囲：k より前の打席と分かっている最後の小片から、k より後の最初の小片まで。"""
    known = sorted((i, r["pa"]) for i, r in log.items() if r["pa"] is not None)
    lo = max((i for i, a in known if a < k), default=0)
    hi = min((i for i, a in known if a > k and i > lo), default=n - 1)
    return lo, hi


def locate_game(g: dict, force: bool = False) -> list[dict] | None:
    gd = game_dir(g["id"])
    out = gd / "打席_映像.csv"
    if out.exists() and not force:
        print(f"  {g['id']}: 打席_映像.csv あり（飛ばす。やり直すなら --force）")
        return None
    pas = read_csv(gd / "打席_KBO.csv")
    if not pas:
        print(f"  ! {g['id']}: 打席_KBO.csv がない（先に relay）")
        return None
    names = {p["batter"] for p in pas} | {x for p in pas for x in p["pitchers"].split("/") if x and x != "?"}
    targets = [k for k, p in enumerate(pas) if p["targets"]]
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix="kbo_") as td:
        v = Video(g["soop"]["title_no"], "540p", Path(td))
        log: dict[int, dict] = {}
        # 1. 見取り図：COARSE 小片おき
        look(v, list(range(1, v.n(), COARSE)), pas, names, log)
        assign(list(log.values()))
        # 2. 対象の打席がありうる範囲を、2小片（12秒）おきに読む
        for step in (2, 1):
            want = []
            for k in targets:
                lo, hi = bracket(log, k, v.n())
                want += list(range(lo + 1, hi, step))
            look(v, want, pas, names, log)
            assign(list(log.values()))
        # 3. 始まりと終わりの手前の小片も読み、境目を6秒単位にする
        edge = []
        for k in targets:
            segs = sorted(i for i, r in log.items() if r["pa"] == k)
            if segs:
                edge += [segs[0] - 1, segs[0] - 2, segs[-1] + 1, segs[-1] + 2]
        look(v, edge, pas, names, log)
        assign(list(log.values()))
        rows = [place(k, pas, log, v) for k in targets]
        write_csv(out, LOC_FIELDS, rows)
        write_csv(gd / "探索.csv", ["seg", "sec", "names", "pa", "batter", "cands"],
                  [{**r, "batter": pas[r["pa"]]["batter"] if r["pa"] is not None else "",
                    "cands": json.dumps(r["cands"])} for _, r in sorted(log.items())])
        g["locate"] = {"probes": len(log), "mb": round(v.got / 1e6, 1), "sec": round(time.time() - t0)}
    ok = sum(1 for r in rows if r["status"] == "ok")
    print(f"  {g['id']}: 対象 {len(rows)}打席、打者名で場面を確かめた {ok}、静止画 {len(log)}枚、"
          f"通信 {g['locate']['mb']}MB、{g['locate']['sec']}秒")
    return rows


def place(k: int, pas: list[dict], log: dict[int, dict], v: Video) -> dict:
    """打席 k の始まりと終わりの秒を決める。"""
    p = pas[k]
    row = {**{f: p[f] for f in ("no", "inning", "half", "batter", "pitcher", "n_pitch", "targets")},
           "status": "", "check": "", "files": ""}
    segs = sorted(i for i, r in log.items() if r["pa"] == k)
    lo, hi = bracket(log, k, v.n())
    if segs:
        first, last = segs[0], segs[-1]
        # 直前の小片が「帯なし」なら、打者の登場がそこまでさかのぼるかもしれないので1つ足す
        if first - 1 > lo and not log.get(first - 1, {}).get("cands"):
            first -= 1
        after = min((i for i, r in log.items() if r["pa"] is not None and r["pa"] > k and i > last), default=v.n())
        if after - last > 10:  # 次の打者まで1分以上空く（回の終わりの広告など）：最後に見えてから30秒まで
            end = v.starts[last] + 6 + 30
        else:
            end = v.starts[min(after, v.n())] + AFTER
        start = v.starts[first] - BEFORE
        row["status"] = "ok"
    else:
        # 打者名が一度も読めなかった（短い打席で、帯がリプレーや広告で隠れていた）：前の打席が最後に見えた所から、
        # 「30秒＋1球25秒」か次の打席が見えた所の早いほうまでを切る
        start = v.starts[min(lo + 1, v.n() - 1)] - BEFORE
        end = min(v.starts[min(hi, v.n())] + AFTER, start + 30 + 25 * max(1, int(p["n_pitch"] or 1)))
        first, last = lo + 1, hi
        row["status"] = "打者名が読めず、前の打席の直後から切り出した"
    row.update({"start": round(max(0.0, start), 1), "end": round(min(v.starts[-1], end), 1),
                "seg_first": first, "seg_last": last})
    return row


def cmd_locate(args) -> None:
    games = load_games()
    for g in pick(games, args.game, args.player):
        if g.get("soop"):
            locate_game(g, args.force)
    save_games(games)


# ---------------------------------------------------------------- cut：打席ごとの動画


def clip_name(g: dict, row: dict, who: str, pas_by_no: dict) -> str:
    p = pas_by_no[row["no"]]
    t = g["targets"][who]
    opp_team = KO_OF[p["pit_team"]] if t["kind"] == "打者" else KO_OF[p["bat_team"]]
    other = row["pitcher"] if t["kind"] == "打者" else row["batter"]
    return f"{g['date'][4:]}_{opp_team}_{row['inning']}회{row['half']}_{other}_{int(row['no']):03d}.mp4"


def cmd_cut(args) -> None:
    games = load_games()
    for g in pick(games, args.game, args.player):
        gd = game_dir(g["id"])
        rows = read_csv(gd / "打席_映像.csv")
        if not rows:
            continue
        pas_by_no = {p["no"]: p for p in read_csv(gd / "打席_KBO.csv")}
        todo = []
        for r in rows:
            files = [CLIPS / who / clip_name(g, r, who, pas_by_no) for who in r["targets"].split("/") if who]
            r["files"] = "|".join(str(f.relative_to(DATA)) for f in files)
            if args.force or not all(f.exists() for f in files):
                todo.append((r, files))
        if not todo:
            print(f"  {g['id']}: 動画はそろっている")
            write_csv(gd / "打席_映像.csv", LOC_FIELDS, rows)
            continue
        with tempfile.TemporaryDirectory(prefix="kbo_cut_") as td:
            v = Video(g["soop"]["title_no"], "720p", Path(td))
            for r, files in todo:
                start, end = float(r["start"]), float(r["end"])
                s0 = max(0, next(i for i in range(len(v.starts) - 1) if v.starts[i + 1] > start))
                s1 = min(v.n() - 1, max(i for i in range(v.n()) if v.starts[i] < end))
                with ThreadPoolExecutor(max_workers=6) as ex:  # 小片を並行して取る
                    list(ex.map(v.seg_file, range(s0, s1 + 1)))
                joined = Path(td) / "joined.mp4"
                with open(joined, "wb") as f:
                    f.write(v.init.read_bytes())
                    for i in range(s0, s1 + 1):
                        f.write(v.seg_file(i).read_bytes())
                files[0].parent.mkdir(parents=True, exist_ok=True)
                off = start - v.starts[s0]
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{off:.2f}", "-i", str(joined),
                                "-t", f"{end - start:.2f}", "-c", "copy", "-movflags", "+faststart", str(files[0])],
                               check=True)
                for f in files[1:]:
                    f.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(files[0], f)
                joined.unlink(missing_ok=True)  # 小片は、続く打席と重なることがあるので試合の終わりまで残す
            g["cut_mb"] = round(v.got / 1e6, 1)
        write_csv(gd / "打席_映像.csv", LOC_FIELDS, rows)
        print(f"  {g['id']}: 動画 {len(todo)}本（通信 {g['cut_mb']}MB）")
    save_games(games)


# ---------------------------------------------------------------- check：動画を確かめる


def stills(mp4: Path, at: list[float], tmp: Path) -> list[Path]:
    out = []
    for j, t in enumerate(at):
        png = tmp / f"{mp4.stem}_{j}.png"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0, t):.2f}", "-i", str(mp4), "-an",
                        "-frames:v", "1", str(png)], check=False)
        out.append(png)
    return out


def duration(mp4: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp4)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def cmd_check(args) -> None:
    games = load_games()
    total = flagged = 0
    for g in pick(games, args.game, args.player):
        gd = game_dir(g["id"])
        rows = read_csv(gd / "打席_映像.csv")
        if not rows:
            continue
        pas = read_csv(gd / "打席_KBO.csv")
        by_no = {p["no"]: i for i, p in enumerate(pas)}
        with tempfile.TemporaryDirectory(prefix="kbo_chk_") as td:
            for r in rows:
                files = [DATA / f for f in r["files"].split("|") if f]
                if not files or not files[0].exists():
                    r["check"] = "動画がない"
                    continue
                total += 1
                mp4 = files[0]
                dur = duration(mp4)
                # 頭から終わりまで6枚。帯はリプレーや紹介の画面で隠れるので、どれか1枚に見えればよい
                shots = stills(mp4, [dur * j / 6 for j in range(1, 7)][:-1] + [dur - 1], Path(td))
                res = ocr(shots)
                p = pas[by_no[r["no"]]]
                names = {x["batter"] for x in pas} | {y for x in pas for y in x["pitchers"].split("/") if y}
                seen: dict[str, float] = {}
                for s in shots:
                    for n, sc in names_in(res.get(str(s), []), names).items():
                        seen[n] = max(seen.get(n, 0), sc)
                notes = []
                if p["batter"] not in seen:
                    notes.append("打者名が見えない")
                if not any(x in seen for x in p["pitchers"].split("/") if x):
                    notes.append("投手名が見えない")
                n = int(p["n_pitch"] or 0)
                if n and dur < 8 * n + BEFORE:
                    notes.append(f"短い（{dur:.0f}秒・{n}球）")
                r["check"] = "ok" if not notes else "／".join(notes)
                flagged += bool(notes)
                for s in shots:
                    s.unlink(missing_ok=True)
        write_csv(gd / "打席_映像.csv", LOC_FIELDS, rows)
        bad = [r for r in rows if r["check"] != "ok"]
        print(f"  {g['id']}: {len(rows)}本、印 {len(bad)}" + "".join(f"\n    - {r['no']} {r['batter']} vs {r['pitcher']}: {r['check']}" for r in bad))
    print(f"確かめた動画 {total}本、印の付いたもの {flagged}")


# ---------------------------------------------------------------- index：BASSに入れる順の一覧


def cmd_index(_args) -> None:
    games = load_games()
    players = {p["name"]: p for p in load_players() if p["target"]}
    rows = []
    for g in games:
        gd = DATA / g["id"]
        locs = {r["no"]: r for r in read_csv(gd / "打席_映像.csv")}
        for p in read_csv(gd / "打席_KBO.csv"):
            for who in [x for x in (p["targets"] or "").split("/") if x]:
                loc = locs.get(p["no"], {})
                f = next((x for x in (loc.get("files") or "").split("|") if f"clips/{who}/" in x), "")
                t = g["targets"][who]
                opp = p["pit_team"] if t["kind"] == "打者" else p["bat_team"]
                rows.append({"選手": who, "区分": t["kind"], "日付": f"{g['date'][4:6]}/{g['date'][6:]}",
                             "相手": KO_OF[opp], "ホーム": KO_OF.get(g.get("home", ""), ""),
                             "回": f"{p['inning']}회{p['half']}", "打順": p["order"], "打者": p["batter"],
                             "投手": p["pitchers"].replace("/", "→"), "球数": p["n_pitch"], "1球の並び": p["pitches"],
                             "結果": p["result"], "動画": f, "確かめ": loc.get("check") or loc.get("status") or "未",
                             "試合": g["id"], "打席番号": p["no"]})
    order = sorted(players, key=lambda n: -int(players[n]["pa"]))
    rows.sort(key=lambda r: (order.index(r["選手"]) if r["選手"] in order else 99, r["日付"], int(r["打席番号"])))
    fields = ["選手", "区分", "日付", "相手", "ホーム", "回", "打順", "打者", "投手", "球数", "1球の並び", "結果", "動画", "確かめ", "試合", "打席番号"]
    write_csv(DATA / "一覧.csv", fields, rows)
    # 手元用の確認ページ（自動では再生しない）
    esc = html.escape
    body = []
    for who in order:
        rs = [r for r in rows if r["選手"] == who]
        if not rs:
            continue
        body.append(f"<h2>{esc(who)}（{esc(players[who]['bass'])}・{esc(players[who]['kind'])}） {len(rs)}打席</h2><table>")
        body.append("<tr><th>日付</th><th>相手</th><th>回</th><th>打者</th><th>投手</th><th>球数</th><th>1球の並び</th><th>結果</th><th>確かめ</th><th>動画</th></tr>")
        for r in rs:
            vid = (f'<video src="{esc(urllib.parse.quote(r["動画"]))}" controls preload="none" width="320"></video>'
                   if r["動画"] else "なし")
            cls = "" if r["確かめ"] == "ok" else ' class="flag"'
            body.append(f"<tr{cls}><td>{esc(r['日付'])}</td><td>{esc(r['相手'])}</td><td>{esc(r['回'])}</td><td>{esc(r['打者'])}</td>"
                        f"<td>{esc(r['投手'])}</td><td>{esc(r['球数'])}</td><td class=seq>{esc(r['1球の並び'])}</td><td>{esc(r['結果'])}</td>"
                        f"<td>{esc(r['確かめ'])}</td><td>{vid}</td></tr>")
        body.append("</table>")
    page = ("<!doctype html><meta charset=utf-8><title>韓国 KBO打席一覧</title>"
            "<style>body{font-family:-apple-system,sans-serif;margin:16px}table{border-collapse:collapse;margin-bottom:32px}"
            "td,th{border:1px solid #ccc;padding:4px 6px;font-size:13px;vertical-align:top}.seq{font-family:monospace}"
            ".flag{background:#fff3cd}</style>"
            "<p>B=ボール S=見逃し W=空振り F=ファウル X=打った H=死球。黄色の行は確かめで印が付いたもの。動画は押したときだけ再生する。</p>"
            + "".join(body))
    (DATA / "一覧.html").write_text(page, encoding="utf-8")
    print(f"一覧 {len(rows)}打席（動画あり {sum(1 for r in rows if r['動画'])}）→ {DATA / '一覧.csv'}・一覧.html")


# ---------------------------------------------------------------- run：続けて流す


MIN_FREE_GB = 15  # Macの空きがこれを切ったら止める


def cmd_run(args) -> None:
    """打席の多い選手から、各選手の新しい試合の順に流す（韓国戦までに終わらなくても、主な選手から使えるように）。"""
    games = load_games()
    rank = {p["name"]: -int(p["pa"]) for p in load_players() if p["target"]}
    targets = sorted(pick(games, args.game, args.player),
                     key=lambda g: (min(rank.get(n, 0) for n in g["targets"]), -int(g["date"])))
    for g in targets:
        free = shutil.disk_usage(DATA).free / 1e9
        if free < MIN_FREE_GB:
            print(f"  ! Macの空きが {free:.0f}GB になったので止める（{MIN_FREE_GB}GB未満）")
            break
        a = argparse.Namespace(game=g["id"], player=None, force=False)
        try:
            cmd_relay(a)
            cmd_locate(a)
            cmd_cut(a)
            cmd_check(a)
        except Exception as e:  # 1試合の失敗で全体を止めない
            print(f"  ! {g['id']}: 止まった（{type(e).__name__}: {e}）。次の試合へ")
    cmd_index(args)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("games")
    s = sub.add_parser("soop")
    s.add_argument("--refresh", action="store_true")
    for name in ("relay", "locate", "cut", "check", "run"):
        s = sub.add_parser(name)
        s.add_argument("--game")
        s.add_argument("--player")
        s.add_argument("--force", action="store_true")
    sub.add_parser("index")
    args = ap.parse_args()
    {"games": cmd_games, "soop": cmd_soop, "relay": cmd_relay, "locate": cmd_locate, "cut": cmd_cut,
     "check": cmd_check, "index": cmd_index, "run": cmd_run}[args.cmd](args)


if __name__ == "__main__":
    main()
