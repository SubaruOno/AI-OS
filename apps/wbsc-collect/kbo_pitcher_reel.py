#!/usr/bin/env python3
"""韓国U-23代表の投手と打者の対策映像を、kbo_clips.py で切った打席の動画から作る道具。

打席の動画（約30秒に1球）から投球の場面だけを抜き、選手ごとに動画にする：
投手は全球（全部の場面）、左右別まとめ（対左・対右の数打席を通しで）、奪三振集（三振の決め球）。
打者は左右別まとめ（対左投手・対右投手の数打席を通しで）、三振集、安打集。
字幕に出すのは、打者の左右・試合・打者名と、投げた後に読めた球速と球種、打席の最後の球の結果。
何球目かは読み違いが出るので字幕にしない（カウントと累計球数は中継の画面に映っている）。
動画は ~/野球/U23ワールドカップ2026/04_対戦国/韓国/ の 投手別映像/ と 打者別映像/ に書く（選手の映像なのでリポジトリに入れない）。

    python3 kbo_pitcher_reel.py hands                 # 対戦した打者と投手の左右をKBO公式から取る → 打者の左右.json・投手の左右.json
    python3 kbo_pitcher_reel.py scan --player 최우석    # 打席の動画を読む（球速と球種の表示、センター映像の区間）
    python3 kbo_pitcher_reel.py pick --player 최우석    # 1球ずつの場面を決める → <投手>_1球.csv
    python3 kbo_pitcher_reel.py render --player 최우석  # 3種類の動画にする（--kind all / sides / k で1種類だけ）
    python3 kbo_pitcher_reel.py web --player 최우석     # 共有サイト用の打席ごとの動画（投手別映像/web/）。site_video_kor.py が読む
    python3 kbo_pitcher_reel.py share                 # 選手共有用の1本と、YouTubeの説明欄に貼るタイムスタンプ（選手共有用/）。render のあとに流す

1球の並びの正解はKBO公式の文字中継（kbo_clips.py の 打席_KBO.csv）で、映像からは場面だけを取る。
球速の表示が出た時刻を第一の目印にし、球速が読めた場面を手本にしてセンターカメラの映像を見分け、
球速が出なかった球（ファウルの直後にカメラが替わるなど）はその区間で補う。作業中に動画は再生しない。
"""

from __future__ import annotations

import argparse
import csv
import difflib
import html
import json
import re
import subprocess
import tempfile
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from kbo_clips import BASS_LIST, DATA, KBO, ROOT, TEAMS, fetch, ocr_bin

OUT = ROOT / "04_対戦国" / "韓国" / "投手別映像"
READINGS = ROOT / "07_出場選手情報" / "サイト用" / "名簿_読み.csv"
CACHE = Path.home() / ".cache" / "kbo_clips" / "reel"
HANDS = OUT / "打者の左右.json"
BAT_OUT = ROOT / "04_対戦国" / "韓国" / "打者別映像"
SHARE_OUT = ROOT / "04_対戦国" / "韓国" / "選手共有用"
# 選手共有用の1本の順番。投手は起用の見込みの順、打者は打席の多い順
SHARE_ORDER = (("최우석", ("左右別まとめ", "奪三振集")), ("원종혁", ("左右別まとめ", "奪三振集")),
               ("신상연", ("左右別まとめ", "奪三振集")), ("서준오", ("左右別まとめ", "奪三振集")),
               ("어준서", ("左右別まとめ", "安打集", "三振集")), ("유민", ("左右別まとめ", "安打集", "三振集")),
               ("양현종", ("左右別まとめ", "安打集", "三振集")), ("김건", ("三振集",)))
PITCHER_HANDS = BAT_OUT / "投手の左右.json"

# 映像を読むときの大きさ（10コマ/秒の小さな白黒）
FPS = 10
GW, GH = 160, 90
# センター映像の見分けに使う範囲（マウンドと芝。帯と球速の枠は入らない）
REGION = (slice(int(GH * 0.45), int(GH * 0.88)), slice(int(GW * 0.05), int(GW * 0.65)))

# 1球の切り方（秒）。球速の表示は放送局によって投球の0〜3秒後に出る
BEFORE_MARK = 8.0
AFTER_MARK = 2.5
AFTER_HIT = 6.0
LONGEST_NO_MARK = 10.0

# 映像の形：放送の画面（720p）の上に字幕の帯を足す
VW, VH, STRIP = 1280, 720, 64
BITRATE = "4500k"
# 共有サイト用の形（字幕の帯まで含めて縮める）
WEB_W, WEB_H, WEB_CRF = 960, 588, 28

SPEED = re.compile(r"(1[0-6]\d)\s*[kK]")
SPEED_UNIT = re.compile(r"[kKc][mM]|/h")
KINDS = {
    "패스트볼": "速球", "직구": "速球", "포심": "速球", "슬라이더": "スライダー", "커브": "カーブ",
    "체인지업": "チェンジアップ", "포크": "フォーク", "스플리터": "スプリット", "투심": "ツーシーム",
    "싱커": "シンカー", "커터": "カット",
}
FIELDERS = {
    "1루수": "ファースト", "2루수": "セカンド", "3루수": "サード", "유격수": "ショート", "좌익수": "レフト",
    "중견수": "センター", "우익수": "ライト", "투수": "ピッチャー", "포수": "キャッチャー", "좌중간": "左中間", "우중간": "右中間",
}
# 左右別まとめに入れる打席の数と、結果の内訳の目安
AT_BATS_PER_SIDE = 5
RESULT_MIX = {"三振": 2, "安打": 1, "四死球": 1, "凡打": 1}


# ---------------------------------------------------------------- 打席の並び


def is_batter(player: str) -> bool:
    return any(r["name"] == player and r["kind"] == "打者" for r in csv.DictReader(open(DATA / "選手.csv", encoding="utf-8-sig")))


def out_dir(player: str) -> Path:
    return BAT_OUT if is_batter(player) else OUT


def at_bats(player: str) -> list[dict]:
    """一覧.csv のこの選手の打席に、文字中継の打席（両チーム・結果）を足す。"""
    rows = [r for r in csv.DictReader(open(DATA / "一覧.csv", encoding="utf-8-sig")) if r["選手"] == player and r["動画"]]
    relay: dict[str, dict] = {}
    for game in {r["試合"] for r in rows}:
        relay[game] = {x["no"]: x for x in csv.DictReader(open(DATA / game / "打席_KBO.csv", encoding="utf-8-sig"))}
    for r in rows:
        kbo = relay[r["試合"]][r["打席番号"]]
        r["bat_team"] = kbo["bat_team"]
        r["pit_team"] = kbo["pit_team"]
        r["last_pitcher"] = r["投手"].split("→")[-1]  # 打席の途中で替わったら、最後の投手の左右で分ける
        r["seq"] = r["1球の並び"].split()
        r["game_batters"] = sorted({x["batter"] for x in relay[r["試合"]].values()})
        r["stem"] = Path(r["動画"]).stem
    return rows


def team_ja(code: str) -> str:
    return next(t[2] for t in TEAMS if t[0] == code)


def team_ko(code: str) -> str:
    return next(t[1] for t in TEAMS if t[0] == code)


# ---------------------------------------------------------------- 打者の左右


def form_value(page: str, name: str) -> str:
    m = re.search(rf'name="{re.escape(name)}"[^>]*value="([^"]*)"', page)
    return html.unescape(m.group(1)) if m else ""


def player_hand(name: str, team: str, pitcher: bool = False) -> str:
    """KBO公式の選手検索で、同じ名前の選手の打席（우・좌・양）か投げる手（우・좌）を取る。

    そのチームにいなければ（移籍など）、同じ名前が1人だけのときに限ってその人とする。
    「우언우타」のように下手投げは 언 と書かれる。
    """
    ui = "ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$"
    url = f"{KBO}/Player/Search.aspx"
    page = fetch(url).decode("utf-8", "replace")
    form = {k: form_value(page, k) for k in ("__VIEWSTATE", "__EVENTVALIDATION", "__VIEWSTATEGENERATOR")}
    form[ui + "txtSearchPlayerName"] = name
    form[ui + "btnSearch"] = "검색"
    res = fetch(url, form).decode("utf-8", "replace")
    same, here = [], []
    for row in re.findall(r"<tr>(.*?)</tr>", res, re.S):
        link = re.search(r"""href=['"]([^'"]*Detail[^'"]*playerId=\d+)['"][^>]*>([^<]+)<""", row)
        if link and link.group(2).strip() == name:
            same.append(link.group(1))
            if team_ko(team) in row:
                here.append(link.group(1))
    found = set()
    for link in here or (same if len(same) == 1 else []):
        detail = fetch(f"{KBO}{link}").decode("utf-8", "replace")
        m = re.search(r"([우좌])[투언]([우좌양])타", detail)
        found.add((m.group(1) if pitcher else m.group(2)) if m else "")
    # 同じチームに同じ名前が2人いて左右が違うとき（サムスンの이승현）は、どちらか分からないので空にする
    return found.pop() if len(found) == 1 else ""


def fill_hands(path: Path, wanted: set, pitcher: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    done = json.loads(path.read_text()) if path.exists() else {}
    for name, team in sorted(wanted):
        if not done.get(f"{name}|{team}"):
            done[f"{name}|{team}"] = player_hand(name, team, pitcher)
            path.write_text(json.dumps(done, ensure_ascii=False, indent=0))
            time.sleep(0.5)
    blank = [k for k, v in done.items() if not v]
    print(f"{path.name}: {len(done)}人、取れなかった {len(blank)}人 {blank}")


def cmd_hands() -> None:
    rows = list(csv.DictReader(open(DATA / "一覧.csv", encoding="utf-8-sig")))
    pitchers = {r["選手"] for r in rows if r["区分"] == "投手"}
    batters = {r["選手"] for r in rows if r["区分"] == "打者"}
    fill_hands(HANDS, {(r["打者"], r["bat_team"]) for p in pitchers for r in at_bats(p)}, False)
    fill_hands(PITCHER_HANDS, {(r["last_pitcher"], r["pit_team"]) for p in batters for r in at_bats(p)}, True)


# ---------------------------------------------------------------- 読む（scan）


def ocr(paths: list[str]) -> list[list[dict]]:
    res = subprocess.run([str(ocr_bin()), *paths], capture_output=True, text=True).stdout
    return [json.loads(line)["lines"] for line in res.splitlines()]


def pitch_kind(lines: list[dict]) -> str:
    """球速と同じ行の文字から球種を拾う。1文字の読み違いは許す。ほかの行は広告（포크밸리 など）を拾うので見ない。"""
    for item in lines:
        if not SPEED_UNIT.search(item["text"]):
            continue
        for word in re.findall(r"[가-힣]{2,}", item["text"]):
            hit = difflib.get_close_matches(word, KINDS, n=1, cutoff=0.6)
            if hit:
                return KINDS[hit[0]]
    return ""


def read_marks(clip: Path) -> list[list]:
    """0.5秒おきに右下を読み、球速が出た時刻を [秒, 球速, 球種] で返す。表示は1秒ほどで消えるので1秒おきでは見落とす。"""
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["ffmpeg", "-v", "error", "-an", "-i", str(clip), "-vf",
                        "fps=2,crop=iw*0.4:ih*0.5:iw*0.6:ih*0.5", "-q:v", "3", f"{tmp}/%05d.jpg"], check=True)
        frames = sorted(str(p) for p in Path(tmp).glob("*.jpg"))
        pages = ocr(frames)
    groups: list[dict] = []
    for index, lines in enumerate(pages):
        sec = index / 2
        kmh = next((int(m.group(1)) for x in lines for m in [SPEED.search(x["text"])] if m), 0)
        if not kmh:
            continue
        if groups and sec - groups[-1]["last"] <= 4:
            groups[-1]["last"] = sec
        else:
            groups.append({"first": sec, "last": sec, "kmh": [], "kind": []})
        groups[-1]["kmh"].append(kmh)
        groups[-1]["kind"].append(pitch_kind(lines))
    marks = []
    for g in groups:
        kinds = [k for k in g["kind"] if k]
        marks.append([g["first"], Counter(g["kmh"]).most_common(1)[0][0], Counter(kinds).most_common(1)[0][0] if kinds else ""])
    return marks


def read_gray(clip: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-an", "-i", str(clip), "-vf", f"fps={FPS},scale={GW}:{GH}",
                          "-pix_fmt", "gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, GH, GW)


def scan_one(row: dict, folder: Path) -> None:
    clip = DATA / row["動画"]
    marks_file = folder / f"{row['stem']}.json"
    gray_file = folder / f"{row['stem']}.npy"
    if not marks_file.exists():
        marks_file.write_text(json.dumps(read_marks(clip), ensure_ascii=False))
    if not gray_file.exists():
        np.save(gray_file, read_gray(clip))


def cmd_scan(player: str) -> None:
    folder = CACHE / player
    folder.mkdir(parents=True, exist_ok=True)
    rows = at_bats(player)
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda r: scan_one(r, folder), rows))
    print(f"{player}: {len(rows)}打席を読んだ")


# ---------------------------------------------------------------- 場面を決める（pick）


def center_runs(dist: np.ndarray, thr: float) -> list[tuple[float, float]]:
    """手本との差が小さいコマの続きを、センター映像の区間（秒）にする。1秒未満は捨て、0.5秒以内の切れ目はつなぐ。"""
    runs: list[list[int]] = []
    start = None
    for i, ok in enumerate(dist < thr):
        if ok and start is None:
            start = i
        if not ok and start is not None:
            runs.append([start, i])
            start = None
    if start is not None:
        runs.append([start, len(dist)])
    joined: list[list[int]] = []
    for r in runs:
        if joined and r[0] - joined[-1][1] <= FPS // 2:
            joined[-1][1] = r[1]
        else:
            joined.append(r)
    return [(a / FPS, b / FPS) for a, b in joined if b - a >= FPS]


def game_runs(rows: list[dict], folder: Path) -> dict[str, list[tuple[float, float]]]:
    """試合ごとに、球速が読めた場面の中央値を手本にして、打席ごとのセンター映像の区間を返す。"""
    out: dict[str, list[tuple[float, float]]] = {}
    games = defaultdict(list)
    for r in rows:
        games[r["試合"]].append(r)
    for rs in games.values():
        grays = {r["stem"]: np.load(folder / f"{r['stem']}.npy") for r in rs}
        refs = []
        for r in rs:
            gray = grays[r["stem"]]
            for sec, _, _ in json.loads((folder / f"{r['stem']}.json").read_text()):
                if sec >= 3 and int(sec * FPS) < len(gray):
                    refs.append(gray[int(sec * FPS)][REGION].astype(np.int16))
        if not refs:
            for r in rs:
                out[r["stem"]] = []
            continue
        model = np.median(np.stack(refs), axis=0)
        gaps = [float(np.abs(x - model).mean()) for x in refs]
        thr = max(14.0, float(np.percentile(gaps, 90)) * 1.3)
        for r in rs:
            region = grays[r["stem"]][(slice(None),) + REGION].astype(np.int16)
            out[r["stem"]] = center_runs(np.abs(region - model).mean(axis=(1, 2)), thr)
    return out


def near_name(name: str, text: str) -> bool:
    """文字認識の行に名前が入っているか。3文字以上の名前は1文字違いまで許す（kbo_clips.py と同じ考え方）。"""
    if name in text:
        return True
    if len(name) < 3:
        return False
    for word in re.findall(r"[가-힣]{%d}" % len(name), text):
        if sum(a != b for a, b in zip(word, name)) <= 1:
            return True
    return False


def read_screens(clip: Path, times: list[float]) -> list[str]:
    """その時刻の画面全体を読み、文字をつないで返す。"""
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for i, t in enumerate(times):
            p = f"{tmp}/{i:04d}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-an", "-ss", f"{t:.2f}", "-i", str(clip),
                            "-frames:v", "1", "-q:v", "2", p], check=True)
            paths.append(p)
        pages = ocr(paths) if paths else []
    return [" ".join(x["text"] for x in lines) for lines in pages]


def pick_clip(row: dict, runs: list[tuple[float, float]], folder: Path, hands: dict) -> list[dict]:
    clip = DATA / row["動画"]
    seq = row["seq"]
    duration = len(np.load(folder / f"{row['stem']}.npy", mmap_mode="r")) / FPS
    marks = [m for m in json.loads((folder / f"{row['stem']}.json").read_text()) if m[0] > 2]

    # 候補：球速が読めた場面と、球速の出なかったセンター映像の区間
    events = []
    used_runs = set()
    for sec, kmh, kind in marks:
        run = next((r for r in runs if r[0] - 1 <= sec <= r[1] + 1), None)
        if run:
            used_runs.add(run)
        floor = run[0] if run else max(0.0, sec - 6)
        events.append({"mark": sec, "kmh": kmh, "kind": kind, "start": max(floor, sec - BEFORE_MARK), "end": sec + AFTER_MARK})
    for run in runs:
        if run not in used_runs and run[0] > 2:
            events.append({"mark": None, "kmh": 0, "kind": "", "start": max(run[0], run[1] - LONGEST_NO_MARK), "end": run[1] + 1.0})
    events.sort(key=lambda e: e["start"])

    # 帯の打者名を読み、前後の打者の場面を見分ける
    screens = read_screens(clip, [min(e["start"] + 0.3, duration - 0.1) for e in events])
    others = [b for b in row["game_batters"] if b != row["打者"]]
    for e, text in zip(events, screens):
        e["target"] = near_name(row["打者"], text)
        e["other"] = any(o in text for o in others) and not e["target"]

    # 球数に合わせる：球速の読めた場面を先に、足りない分を球速のない区間から補う。
    # 別の打者の名前が見えても、引退試合の字幕などもあるので、球数より多いときだけ落とす
    marked = [e for e in events if e["mark"] is not None]
    blanks = [e for e in events if e["mark"] is None and not e["other"]]
    if len(marked) > len(seq):
        marked = sorted(marked, key=lambda e: (e["other"], not e["target"]))[:len(seq)]
    room = max(len(seq) - len(marked), 0)
    blanks = sorted(blanks, key=lambda e: (not e["target"], e["start"]))[:room]
    chosen = sorted(marked + blanks, key=lambda e: e["start"])
    # 打って終わった打席のほかは、最後に球速が読めた場面のあとに投球はない
    if seq and seq[-1] != "X" and marked:
        finish = max(e["start"] for e in marked)
        chosen = [e for e in chosen if e["start"] <= finish]
    # 中継に球速が1回も出ず、場面の取れなかった打席は、目で決めた秒を 手直し.json から使う（[始まり, 終わり, 字幕を出す秒]）
    manual = out_dir(row["選手"]) / "手直し.json"
    if not chosen and manual.exists():
        for start, end, reveal in json.loads(manual.read_text(encoding="utf-8")).get(row["stem"], []):
            chosen.append({"mark": reveal, "kmh": 0, "kind": "", "start": start, "end": end})

    batting = row["区分"] == "打者"
    hand = hands.get(f"{row['last_pitcher']}|{row['pit_team']}" if batting else f"{row['打者']}|{row['bat_team']}", "")
    out = []
    for k, e in enumerate(chosen):
        # 打って終わった打席は、最後の場面だけ打球の行方まで残す
        end = e["end"] + (AFTER_HIT - AFTER_MARK if k == len(chosen) - 1 and seq[-1] == "X" else 0)
        out.append({
            "選手": row["選手"], "立場": row["区分"], "相手の選手": row["投手"] if batting else row["打者"],
            "試合": row["試合"], "打席番号": row["打席番号"], "日付": row["日付"], "相手": row["pit_team"] if batting else row["bat_team"],
            "回": row["回"], "打者": row["打者"], "左右": hand, "打席結果": row["結果"], "球速": e["kmh"] or "", "球種": e["kind"],
            "目印": "球速" if e["mark"] is not None else "区間", "動画": row["動画"],
            "始まり": round(e["start"], 1), "終わり": round(min(end, duration), 1), "打席の球数": len(seq),
            "目印の秒": e["mark"] if e["mark"] is not None else "", "打席の最後": int(k == len(chosen) - 1), "最後の球": seq[-1],
        })
    return out


def cmd_pick(player: str) -> None:
    folder = CACHE / player
    rows = at_bats(player)
    hand_file = PITCHER_HANDS if is_batter(player) else HANDS
    hands = json.loads(hand_file.read_text()) if hand_file.exists() else {}
    runs = game_runs(rows, folder)
    with ThreadPoolExecutor(4) as ex:
        parts = list(ex.map(lambda r: pick_clip(r, runs[r["stem"]], folder, hands), rows))
    picks = [p for part in parts for p in part]
    path = out_dir(player) / f"{player}_1球.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(picks[0]))
        w.writeheader()
        w.writerows(picks)
    total = sum(len(r["seq"]) for r in rows)
    even = sum(1 for r, part in zip(rows, parts) if len(part) == len(r["seq"]))
    kinds = Counter(p["球種"] for p in picks if p["球種"])
    seconds = sum(p["終わり"] - p["始まり"] for p in picks)
    print(f"{player}: 球数 {total}、場面 {len(picks)}（球速あり {sum(p['目印'] == '球速' for p in picks)}）、"
          f"球数がそろった打席 {even}/{len(rows)}、球種 {dict(kinds)}、約{seconds / 60:.0f}分")


# ---------------------------------------------------------------- 動画にする（render）


FONT_JA = next(Path("/System/Library/Fonts").glob("*W6.ttc"))
FONT_KO = Path("/System/Library/Fonts/AppleSDGothicNeo.ttc")


def draw_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int, fill: str) -> int:
    """日本語とハングルでフォントを替えながら書き、書き終わりのxを返す。"""
    ja, ko = ImageFont.truetype(str(FONT_JA), size), ImageFont.truetype(str(FONT_KO), size)
    x, y = xy
    for part in re.findall(r"[가-힣]+|[^가-힣]+", text):
        font = ko if re.match(r"[가-힣]", part) else ja
        draw.text((x, y), part, font=font, fill=fill)
        x += int(draw.textlength(part, font=font))
    return x


def text_width(text: str, size: int) -> int:
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    ja, ko = ImageFont.truetype(str(FONT_JA), size), ImageFont.truetype(str(FONT_KO), size)
    return sum(int(probe.textlength(p, font=ko if re.match(r"[가-힣]", p) else ja)) for p in re.findall(r"[가-힣]+|[^가-힣]+", text))


def result_ja(text: str) -> str:
    """文字中継の結果を、野球の言い方の日本語にする。読めない形は空にする（間違った字幕を出さない）。"""
    text = re.sub(r"[(（].*?[)）]", "", text).strip()
    if "삼진" in text or "낫 아웃" in text:
        return "三振"
    if "볼넷" in text:
        return "四球"
    if "몸에 맞는" in text:
        return "死球"
    text = text.replace("투수 맞고 ", "")  # 投手に当たって内野手が捕った打球は、捕った内野手のゴロ
    where = next((ja for ko, ja in FIELDERS.items() if text.startswith(ko)), "")
    if not where:
        return ""
    if "홈런" in text:
        return f"{where}へのホームラン"
    if "3루타" in text:
        return f"{where}へのスリーベース"
    if "2루타" in text:
        return f"{where}へのツーベース"
    if "내야안타" in text:
        return f"{where}への内野安打"
    if "1루타" in text:
        return f"{where}前ヒット" if "앞" in text and where not in ("左中間", "右中間") else f"{where}へのヒット"
    if "희생번트" in text:
        return "送りバント"
    if "병살타" in text:
        return f"{where}ゴロ併殺"
    if "실책으로 출루" in text:
        return f"{where}フライのエラーで出塁" if "플라이" in text else f"{where}のエラーで出塁"
    for ko, ja in (("땅볼", "ゴロ"), ("플라이", "フライ"), ("라인드라이브", "ライナー")):
        if ko in text:
            return f"{where}{ja}"
    return ""


def result_class(text: str) -> str:
    word = result_ja(text)
    if word == "三振":
        return "三振"
    if word in ("四球", "死球"):
        return "四死球"
    if any(w in word for w in ("ヒット", "ツーベース", "スリーベース", "ホームラン", "内野安打")):
        return "安打"
    return "凡打"


def inning_ja(text: str) -> str:
    return text.replace("회초", "回表").replace("회말", "回裏")


def batting_view(p: dict) -> bool:
    return p.get("立場") == "打者"


def rival(p: dict) -> str:
    return p.get("相手の選手") or p["打者"]


def hand_ja(p: dict) -> str:
    if batting_view(p):
        return {"우": "右投手", "좌": "左投手"}.get(p["左右"], "左右不明")
    return {"우": "右打者", "좌": "左打者", "양": "左打者（両打ち）"}.get(p["左右"], "左右不明")


def is_left(p: dict) -> bool:
    """対左の章に入れるか。4人の投手はみな右投手なので、両打ちの打者は左打者に入れる。"""
    return p["左右"] == "좌" if batting_view(p) else p["左右"] != "우"


def is_right(p: dict) -> bool:
    return p["左右"] == "우"


def caption(p: dict, path: Path, after_pitch: bool, strikeout: bool = False) -> None:
    """字幕の帯。after_pitch のときだけ、投げた後に分かること（球速・球種・打席の結果）も書く。"""
    img = Image.new("RGB", (VW, STRIP), "#111418")
    draw = ImageDraw.Draw(img)
    head = f"{hand_ja(p)}　{int(p['日付'][:2])}/{int(p['日付'][3:])} {team_ja(p['相手'])}戦 {inning_ja(p['回'])}　"
    x = draw_text(draw, (20, 16), head, 26, "#FFFFFF")
    x = draw_text(draw, (x, 19), rival(p), 22, "#AEB6C2")
    if after_pitch:
        pieces = []
        if p["球速"] != "":
            pieces.append(f"{p['球速']}km/h")
        if p["球種"]:
            pieces.append(p["球種"])
        if p["打席の最後"] == "1":
            word = {"W": "空振り三振", "S": "見逃し三振"}.get(p["最後の球"], "三振") if strikeout else result_ja(p["打席結果"])
            if word:
                pieces.append(f"→ {word}")
        right = "　".join(pieces)
        size = 26
        while size > 16 and x + 24 + text_width(right, size) > VW - 20:  # 左の字幕とぶつかるときは小さくする
            size -= 2
        draw_text(draw, (VW - 20 - text_width(right, size), 16 + (26 - size) // 2), right, size, "#FFD76A")
    img.save(path)


def card(lines: list[tuple[str, int, str]], path: Path) -> None:
    img = Image.new("RGB", (VW, VH + STRIP), "#111418")
    draw = ImageDraw.Draw(img)
    y = (VH + STRIP - sum(size + 26 for _, size, _ in lines)) // 2
    for text, size, color in lines:
        draw_text(draw, ((VW - text_width(text, size)) // 2, y), text, size, color)
        y += size + 26
    img.save(path)


def web_flags() -> list[str]:
    """共有サイト用。電波の弱い所で見るので軽くする（台湾の映像ページと同じ libx264 の veryfast）。"""
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(WEB_CRF), "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-r", "30000/1001", "-g", "60", "-threads", "2", "-an"]


def encode_flags() -> list[str]:
    return ["-c:v", "h264_videotoolbox", "-b:v", BITRATE, "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-r", "60000/1001", "-video_track_timescale", "90000", "-an"]


def render_card(image: Path, seconds: float, out: Path) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(image), "-t", str(seconds),
                    *encode_flags(), "-f", "mpegts", str(out)], check=True)


def render_pitch(p: dict, before: Path, after: Path, out: Path, web: bool = False) -> None:
    """放送の画面の上に字幕の帯を足す。投げた後の字幕は、球速の表示が出た秒から重ねる。web は共有サイト用の軽い版。"""
    length = p["終わり"] - p["始まり"]
    reveal = float(p["目印の秒"]) - p["始まり"] if p["目印の秒"] != "" else max(length - 2.0, 0.0)
    rate = "30000/1001" if web else "60000/1001"
    finish = f",scale={WEB_W}:{WEB_H}" if web else ""
    graph = (f"[0:v]fps={rate},scale={VW}:{VH},setsar=1,pad={VW}:{VH + STRIP}:0:{STRIP}:black[b];"
             "[b][1:v]overlay=0:0:shortest=1[c];"
             f"[c][2:v]overlay=0:0:shortest=1:enable='gte(t,{reveal:.2f})'{finish}[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(p["始まり"]), "-t", f"{length:.2f}",
                    "-i", str(DATA / p["動画"]), "-loop", "1", "-i", str(before), "-loop", "1", "-i", str(after),
                    "-filter_complex", graph, "-map", "[v]", *(web_flags() if web else encode_flags()), "-f", "mpegts", str(out)], check=True)


def player_info(player: str) -> dict:
    kana = next(r["reading"] for r in csv.DictReader(open(READINGS, encoding="utf-8-sig")) if r["roster_name"] == player)
    row = next(r for r in csv.reader(open(BASS_LIST, encoding="utf-8-sig")) if player in r)
    return {"kana": kana, "throw": row[5], "bat": row[6], "style": row[7], "team": row[8]}


def newest(p: dict) -> tuple:
    return (-int(p["日付"].replace("/", "")), int(p["打席番号"]), p["始まり"])


def at_bat_groups(scenes: list[dict]) -> list[list[dict]]:
    """場面を打席ごとにまとめ、新しい試合から並べる。"""
    groups = defaultdict(list)
    for p in sorted(scenes, key=newest):
        groups[(p["試合"], p["打席番号"])].append(p)
    return list(groups.values())


def choose_at_bats(scenes: list[dict], count: int) -> list[list[dict]]:
    """全球そろった3球以上の打席から、新しい順に、結果の内訳の目安どおりに選ぶ。1試合からは2打席まで。"""
    groups = [g for g in at_bat_groups(scenes) if len(g) == int(g[0]["打席の球数"]) and result_ja(g[0]["打席結果"])]
    long_ones = [g for g in groups if len(g) >= 3]
    chosen: list[list[dict]] = []
    room = dict(RESULT_MIX)
    games: Counter = Counter()
    for g in long_ones:
        kind = result_class(g[0]["打席結果"])
        if room.get(kind, 0) > 0 and games[g[0]["試合"]] < 2:
            chosen.append(g)
            room[kind] -= 1
            games[g[0]["試合"]] += 1
    for g in long_ones + groups:  # 内訳が埋まらないときは、新しい打席で足す
        if len(chosen) >= count:
            break
        if g not in chosen:
            chosen.append(g)
    return sorted(chosen[:count], key=lambda g: newest(g[0]))


def at_bat_card(g: list[dict]) -> list[tuple[str, int, str]]:
    p = g[0]
    return [(f"{hand_ja(p)}　{rival(p)}", 46, "#FFFFFF"),
            (f"{int(p['日付'][:2])}/{int(p['日付'][3:])} {team_ja(p['相手'])}戦 {inning_ja(p['回'])}　{len(g)}球", 30, "#AEB6C2")]


def build_reel(player: str, kind_name: str, subtitle: str, sections: list[tuple[str, list]], strikeout: bool = False) -> None:
    """sections は [(章の名前, [場面 または 打席の札の行, ...])]。題の画面と章の札を足して1本につなぐ。中身がなければ作らない。"""
    if not any(items for _, items in sections):
        print(f"{player}の{kind_name}: 場面がないので作りません")
        return
    info = player_info(player)
    style = f"・{info['style']}" if info["style"] else ""
    who = f"{info['team']}・{info['bat']}打ち" if is_batter(player) else f"{info['team']}・{info['throw']}投げ{style}"
    work = Path(tempfile.mkdtemp(prefix="reel", dir=CACHE / player))
    title = work / "title.png"
    card([(f"{player}　{info['kana']}", 64, "#FFFFFF"),
          (who, 34, "#AEB6C2"),
          (subtitle, 34, "#FFD76A"),
          ("新しい試合から順に並べています。球速と球種は中継の表示を読んだものです", 26, "#AEB6C2")], title)
    render_card(title, 3.0, work / "title.ts")
    chapters = [("はじめに", work / "title.ts")]
    order = [work / "title.ts"]
    jobs = []
    for i, (name, items) in enumerate(sections):
        if not items:
            continue
        image = work / f"section{i}.png"
        card([(f"{player}　{name}", 56, "#FFD76A")], image)
        ts = work / f"section{i}.ts"
        render_card(image, 2.0, ts)
        chapters.append((name, ts))
        order.append(ts)
        for k, item in enumerate(items):
            out = work / f"{i}_{k:04d}.ts"
            if isinstance(item, list):
                image = work / f"{i}_{k:04d}.png"
                card(item, image)
                render_card(image, 1.5, out)
            else:
                before, after = work / f"{i}_{k:04d}_a.png", work / f"{i}_{k:04d}_b.png"
                caption(item, before, False)
                caption(item, after, True, strikeout)
                jobs.append((item, before, after, out))
            order.append(out)
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(lambda j: render_pitch(*j), jobs))

    meta = [";FFMETADATA1"]
    position = 0.0
    starts = {ts: name for name, ts in chapters}
    marks = []
    for ts in order:
        if ts in starts:
            marks.append((position, starts[ts]))
        position += float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ts)],
                                         capture_output=True, text=True).stdout.strip() or 0)
    for k, (begin, name) in enumerate(marks):
        finish = marks[k + 1][0] if k + 1 < len(marks) else position
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(begin * 1000)}", f"END={int(finish * 1000)}", f"title={name}"]
    (work / "meta.txt").write_text("\n".join(meta) + "\n", encoding="utf-8")
    (work / "list.txt").write_text("".join(f"file '{ts}'\n" for ts in order), encoding="utf-8")
    final = out_dir(player) / f"{player}_{info['kana'].replace('・', '')}_{kind_name}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "list.txt"),
                    "-i", str(work / "meta.txt"), "-map", "0:v", "-map_metadata", "1", "-c", "copy",
                    "-movflags", "+faststart", str(final)], check=True)
    for ts in work.iterdir():
        ts.unlink()
    work.rmdir()
    print(f"{final.name} {position / 60:.1f}分 {final.stat().st_size / 1e6:.0f}MB {[(n, sum(not isinstance(x, list) for x in i)) for n, i in sections]}")


def by_side(scenes: list[dict], names: tuple) -> list[tuple[str, list[dict]]]:
    return [(names[0], sorted((p for p in scenes if is_left(p)), key=newest)),
            (names[1], sorted((p for p in scenes if is_right(p)), key=newest))]


def cmd_render(player: str, kind: str) -> None:
    picks = list(csv.DictReader(open(out_dir(player) / f"{player}_1球.csv", encoding="utf-8-sig")))
    for p in picks:
        p["始まり"], p["終わり"] = float(p["始まり"]), float(p["終わり"])
    batter = is_batter(player)
    names = ("対 左投手", "対 右投手") if batter else ("対 左打者", "対 右打者")
    if kind == "every" or (kind == "all" and not batter):
        sections = [(f"{n}（{len(i)}場面）", i) for n, i in by_side(picks, names)]
        build_reel(player, "全球", f"全球 {len(picks)}場面（{len({(p['試合'], p['打席番号']) for p in picks})}打席）", sections)
    if kind in ("all", "sides"):
        sections = []
        for name, side in by_side(picks, names):
            groups = choose_at_bats(side, AT_BATS_PER_SIDE)
            items: list = []
            for g in groups:
                items.append(at_bat_card(g))
                items.extend(g)
            sections.append((f"{name}（{len(groups)}打席）", items))
            print(name, [(g[0]["日付"], rival(g[0]), len(g), result_ja(g[0]["打席結果"])) for g in groups])
        build_reel(player, "左右別まとめ", f"{names[0][2:]}・{names[1][2:]} 各{AT_BATS_PER_SIDE}打席", sections)
    lasts = [p for p in picks if p["打席の最後"] == "1"]
    if kind in ("all", "k"):
        strikeouts = [p for p in lasts if result_ja(p["打席結果"]) == "三振"]
        title = "三振集" if batter else "奪三振集"
        sections = [(f"{n}（{len(i)}個）", i) for n, i in by_side(strikeouts, names)]
        build_reel(player, title, f"{title} {len(strikeouts)}個（決め球）", sections, strikeout=True)
    if batter and kind in ("all", "hits"):
        hits = [p for p in lasts if result_class(p["打席結果"]) == "安打"]
        sections = [(f"{n}（{len(i)}本）", i) for n, i in by_side(hits, names)]
        build_reel(player, "安打集", f"安打集 {len(hits)}本", sections)


def clock(sec: float) -> str:
    """YouTubeのタイムスタンプの形（0:00、12:34、1:02:03）。"""
    whole = int(sec)
    hours, rest = divmod(whole, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"


def file_chapters(path: Path) -> list[tuple[float, str]]:
    res = subprocess.run(["ffprobe", "-v", "error", "-show_chapters", "-of", "json", str(path)], capture_output=True, text=True).stdout
    return [(float(c["start_time"]), c["tags"]["title"]) for c in json.loads(res)["chapters"]]


def cmd_share() -> None:
    """render で作った動画を1本につなぎ、YouTubeの説明欄に貼るタイムスタンプを書く。

    YouTubeのチャプターは 0:00 から始まり、1つ10秒以上が決まり。題の画面は最初の選手のチャプターに含め、10秒未満は前につなぐ。
    左右別まとめは対左と対右に分け、三振集と安打集は1つにする。
    """
    SHARE_OUT.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="share", dir=CACHE))
    names = [player_info(p)["kana"] for p, _ in SHARE_ORDER]
    pitchers = "・".join(n for (p, _), n in zip(SHARE_ORDER, names) if not is_batter(p))
    batters = "・".join(n for (p, _), n in zip(SHARE_ORDER, names) if is_batter(p))
    title = work / "title.png"
    card([("韓国代表 KBO1軍の映像", 60, "#FFFFFF"), ("U-23W杯 2026", 34, "#AEB6C2"),
          (f"投手　{pitchers}", 26, "#FFD76A"), (f"打者　{batters}", 26, "#FFD76A"),
          ("チャプターから選手へ飛べます。音はありません", 26, "#AEB6C2")], title)
    opening = work / "title.ts"
    render_card(title, 4.0, opening)
    head = work / "title.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(opening), "-c", "copy", "-movflags", "+faststart", str(head)], check=True)
    order = [head]
    at = seconds_of(head)
    stamps: list[tuple[float, str]] = []
    for player, kinds in SHARE_ORDER:
        info = player_info(player)
        role = "打者" if is_batter(player) else "投手"
        for kind in kinds:
            path = out_dir(player) / f"{player}_{info['kana'].replace('・', '')}_{kind}.mp4"
            parts = [c for c in file_chapters(path) if c[1] != "はじめに"]
            if kind == "左右別まとめ":
                for k, (start, name) in enumerate(parts):
                    side = name.split("（")[0].replace(" ", "")
                    stamps.append((at if k == 0 else at + start, f"{info['kana']}（{role}）{side}"))
            else:
                count = sum(int(n) for _, name in parts for n in re.findall(r"（(\d+)[個本]）", name))
                unit = "本" if kind == "安打集" else "個"
                stamps.append((at, f"{info['kana']}（{role}）{kind} {count}{unit}"))
            order.append(path)
            at += seconds_of(path)
    stamps[0] = (0.0, stamps[0][1])
    kept: list[tuple[float, str]] = []
    for k, (start, name) in enumerate(stamps):
        finish = stamps[k + 1][0] if k + 1 < len(stamps) else at
        if finish - start < 10 and kept:
            print(f"10秒未満なのでチャプターにしません: {name}")
            continue
        kept.append((start, name))
    final = SHARE_OUT / "韓国代表KBO映像まとめ.mp4"
    meta = [";FFMETADATA1"]
    for k, (start, name) in enumerate(kept):
        finish = kept[k + 1][0] if k + 1 < len(kept) else at
        meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(start * 1000)}", f"END={int(finish * 1000)}", f"title={name}"]
    (work / "meta.txt").write_text("\n".join(meta) + "\n", encoding="utf-8")
    (work / "list.txt").write_text("".join(f"file '{x}'\n" for x in order), encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "list.txt"), "-i", str(work / "meta.txt"),
                    "-map", "0:v", "-map_metadata", "1", "-map_chapters", "1", "-c", "copy", "-movflags", "+faststart", str(final)], check=True)
    lines = [f"{clock(start)} {name}" for start, name in kept]
    (SHARE_OUT / "タイムスタンプ.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for item in work.iterdir():
        item.unlink()
    work.rmdir()
    print(f"{final.name} {seconds_of(final) / 60:.1f}分（足し算 {at / 60:.1f}分） {final.stat().st_size / 1e9:.2f}GB チャプター{len(kept)}")
    print("\n".join(lines))


def seconds_of(path: Path) -> float:
    res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(res or 0)


def join_clip(parts: list[Path], out: Path, work: Path) -> None:
    listing = work / f"{out.stem}.txt"
    listing.write_text("".join(f"file '{x}'\n" for x in parts), encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(listing), "-map", "0:v",
                    "-c", "copy", "-movflags", "+faststart", str(out)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-an", "-ss", "0.5", "-i", str(out), "-frames:v", "1",
                    "-vf", "scale=480:-2", "-q:v", "5", str(out.with_suffix(".jpg"))], check=True)


def web_scene(p: dict, stem: str, work: Path, strikeout: bool = False) -> Path:
    before, after, ts = work / f"{stem}_a.png", work / f"{stem}_b.png", work / f"{stem}.ts"
    caption(p, before, False)
    caption(p, after, True, strikeout)
    render_pitch(p, before, after, ts, web=True)
    return ts


def web_at_bat(group: list[dict], folder: Path, work: Path) -> dict:
    """1打席を1つの動画にする。奪三振の打席は、決め球だけの動画も作る。"""
    first = group[0]
    stem = f"{first['試合']}_{int(first['打席番号']):03d}"
    parts = [web_scene(p, f"{stem}_{i}", work) for i, p in enumerate(group)]
    join_clip(parts, folder / f"{stem}.mp4", work)
    scenes, at = [], 0.0
    for p, part in zip(group, parts):
        scenes.append({"t": round(at, 1), "kmh": p["球速"], "kind": p["球種"]})
        at += seconds_of(part)
    item = {
        "game": first["試合"], "no": int(first["打席番号"]), "date": first["日付"], "opp": team_ja(first["相手"]),
        "inning": inning_ja(first["回"]), "batter": first["打者"], "rival": rival(first), "hand": first["左右"], "result": result_ja(first["打席結果"]),
        "class": result_class(first["打席結果"]), "pitches": int(first["打席の球数"]), "complete": len(group) == int(first["打席の球数"]),
        "file": f"{stem}.mp4", "jpg": f"{stem}.jpg", "seconds": round(at, 1), "scenes": scenes,
    }
    last = next((p for p in group if p["打席の最後"] == "1"), None)
    if last and item["result"] == "三振":
        join_clip([web_scene(last, f"{stem}_k", work, strikeout=True)], folder / f"{stem}_k.mp4", work)
        item.update({"k_file": f"{stem}_k.mp4", "k_jpg": f"{stem}_k.jpg", "k_kmh": last["球速"], "k_kind": last["球種"],
                     "k_word": {"W": "空振り三振", "S": "見逃し三振"}.get(last["最後の球"], "三振")})
    if last and batting_view(last) and item["class"] == "安打":  # 打者の安打集。打った球だけの動画
        join_clip([web_scene(last, f"{stem}_h", work)], folder / f"{stem}_h.mp4", work)
        item.update({"h_file": f"{stem}_h.mp4", "h_jpg": f"{stem}_h.jpg", "h_kmh": last["球速"], "h_kind": last["球種"]})
    for name in work.glob(f"{stem}*"):
        name.unlink()
    return item


def cmd_web(player: str) -> None:
    picks = list(csv.DictReader(open(out_dir(player) / f"{player}_1球.csv", encoding="utf-8-sig")))
    for p in picks:
        p["始まり"], p["終わり"] = float(p["始まり"]), float(p["終わり"])
    info = player_info(player)
    latin = next(r["bass"] for r in csv.DictReader(open(DATA / "選手.csv", encoding="utf-8-sig")) if r["name"] == player)
    slug = re.sub(r"[^a-z]+", "-", latin.lower()).strip("-")
    folder = out_dir(player) / "web" / slug
    folder.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="web", dir=CACHE / player))
    groups = at_bat_groups(picks)
    with ThreadPoolExecutor(4) as ex:
        items = list(ex.map(lambda g: web_at_bat(g, folder, work), groups))
    work.rmdir()
    index = {"player": player, "view": "打者" if is_batter(player) else "投手", "kana": info["kana"], "club": info["team"],
             "throw": info["throw"], "bat": info["bat"], "style": info["style"], "slug": slug,
             "games": len({i["game"] for i in items}), "sides": {},  "at_bats": items}
    for name, side in (("left", [g for g in groups if is_left(g[0])]), ("right", [g for g in groups if is_right(g[0])])):
        index["sides"][name] = [[g[0]["試合"], int(g[0]["打席番号"])] for g in choose_at_bats([p for g in side for p in g], AT_BATS_PER_SIDE)]
    (folder / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    size = sum(f.stat().st_size for f in folder.glob("*.mp4")) / 1e6
    biggest = max(f.stat().st_size for f in folder.glob("*.mp4")) / 1024 / 1024
    print(f"{player}: {len(items)}打席 {sum('k_file' in i for i in items)}三振 動画{size:.0f}MB 最大{biggest:.1f}MiB")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["hands", "scan", "pick", "render", "web", "share"])
    parser.add_argument("--player")
    parser.add_argument("--kind", choices=["all", "every", "sides", "k", "hits"], default="all")
    args = parser.parse_args()
    if args.command == "hands":
        cmd_hands()
    elif args.command == "scan":
        cmd_scan(args.player)
    elif args.command == "pick":
        cmd_pick(args.player)
    elif args.command == "web":
        cmd_web(args.player)
    elif args.command == "share":
        cmd_share()
    else:
        cmd_render(args.player, args.kind)


if __name__ == "__main__":
    main()
