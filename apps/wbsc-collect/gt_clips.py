#!/usr/bin/env python3
"""GameTime から保存した今大会の試合映像（gametime_dl.py）を、WBSCの1球ごとの記録に合わせて切り、
イギリスの欧州2025（../../野球/.../イギリス/調査メモ/euro_*.py）と同じ形の対策映像にする。

    python3 gt_clips.py ocr <映像.mp4>                         # 右下の得点表示（回・カウント・アウト・球速）を毎秒1回読む → <映像>.bug.json
    python3 gt_clips.py align <試合ID> <映像.mp4>               # 記録の時刻と映像の秒のずれを決める → <映像>.align.json
    python3 gt_clips.py cut <試合ID> <国> <映像.mp4>            # その国の投手と打者を1球ずつに切り、試合ごとのまとめを作る
    python3 gt_clips.py reel <国> <投手> [番号 ...]             # 投手の対策映像（走者あり・対右打者・対左打者・球種別）
    python3 gt_clips.py youtube <国> 投手|野手 [--starter 投手] [--order 投手,投手,...]
                                                               # YouTube（限定公開）に上げる1本と章の説明文
    python3 gt_clips.py phone <まとめ.mp4> ...                  # スマホで見る軽い版と、送れる大きさに分けたもの

<国> は IOC の略号（KOR など）。<投手> は名簿の名前（최우석 など）。
出力は ~/野球/U23ワールドカップ2026/04_対戦国/<国名>/大会2026_映像/。配信の規約上、チームの中だけで使う。

1球の位置は2段で決める。
1. 記録の入力：得点表示のカウントは記録の入力と同時に変わるので、記録の「この球の前のカウント → 後のカウント」に
   変わった瞬間を、その球の入力とみる。まず全球のずれの最頻値で試合全体のずれを決め、球ごとにその前後10秒で探す。
   カウントが変わらない球（2ストライクからのファウル）や、得点表示が消えていた球は、記録の時刻に全体のずれを足して置く。
2. 投げた瞬間：得点表示の下の「@WBSC」は、投げた1〜2秒後に「74 MPH」のような球速に替わる。入力の8秒前までに出た
   球速の表示のうち最後のもの（入力の位置が推定の球は、前の球の入力より後に出た最初のもの）を、その球の目印にする。
   記録の球速は空（0）なので値では合わせず、表示が出た瞬間だけを使う。目印がない球は入力の4秒前を投げた瞬間とする。
   前の球の表示が残っているのを拾わないよう、前の球の目印から4秒以上後の表示に限る。
11/6の韓国対キューバ戦で、投球はカウントが変わる4〜5秒前（打球が前に飛んだ球は約8秒前）だった。
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

from kbo_clips import ocr
from kbo_pitcher_reel import STRIP, VH, VW, draw_text, text_width

ROOT = Path.home() / "野球" / "U23ワールドカップ2026"
DATA = ROOT / "05_収集データ" / "u23-wc-2026"
SITE = ROOT / "07_出場選手情報" / "サイト用"
COUNTRY = {"CUB": "キューバ", "KOR": "韓国", "JPN": "日本", "VEN": "ベネズエラ", "GBR": "イギリス", "RSA": "南アフリカ",
           "NCA": "ニカラグア", "TPE": "台湾", "PAN": "パナマ", "CZE": "チェコ", "PUR": "プエルトリコ", "AUS": "オーストラリア"}

# 得点表示の下の行（「3RD ▲ 0-0 2 OUTS」）と、その下の「@WBSC」（投げた直後は球速）。1280×720 の映像で
BUG_CROP = "290:76:962:606"
BUG_FPS = 1
# 球速の表示は投げてから出るまで約1秒（読むのは毎秒1回なので前後1秒ほどぶれる）。目印がない球は、カウントが変わる4秒前を投げた瞬間とする
TAG_LAG, NO_TAG_LEAD = 1.0, 4.0
# 1球の切り方（秒）。基準は投げた瞬間。前に飛んだ球は打球と走者を見せるため後ろを長く取る
BEFORE, AFTER, AFTER_HIT = 6.5, 6.0, 14.0
FPS = 30
FLAGS = ["-c:v", "h264_videotoolbox", "-b:v", "4500k", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-video_track_timescale", "90000", "-an"]
CARD_SECONDS = 4.0
NOT_PITCH = re.compile(r"(Pitching Change|Defensive (Substitution|Change)|Pinch (Hitter|Runner)|Offensive Substitution)")
IBB = re.compile(r".* is intentionally walked")
POS = {"1": "ピッチャー", "2": "キャッチャー", "3": "ファースト", "4": "セカンド", "5": "サード", "6": "ショート",
       "7": "レフト", "8": "センター", "9": "ライト"}
FIELD = (("left center", "左中間"), ("right center", "右中間"), ("left field", "レフト"), ("center field", "センター"),
         ("right field", "ライト"), ("LF line", "レフト線"), ("right field line", "ライト線"), ("third base", "サード"),
         ("second base", "セカンド"), ("first base", "ファースト"), ("shortstop", "ショート"), ("pitcher", "ピッチャー"),
         ("home plate", "キャッチャー前"), ("up the middle", "センター"), ("through the left side", "レフト"),
         ("through the right side", "ライト"))


# ---------------------------------------------------------------- 記録

def ts(s: str) -> float:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()


def game_info(game: str) -> dict:
    g = next(x for x in json.load(open(DATA / "games.json")) if str(x["id"]) == str(game))
    return g


def team_name(ioc: str) -> str:
    for r in csv.DictReader(open(DATA / "rosters.csv", encoding="utf-8-sig")):
        if r["ioc"] == ioc:
            return r["team"]
    raise SystemExit(f"{ioc} が名簿にない")


def pitches(game: str) -> list[dict]:
    return [r for r in csv.DictReader(open(DATA / "plays.csv", encoding="utf-8-sig"))
            if r["gameid"] == str(game) and r["nopitch"] in ("0", "") and not NOT_PITCH.match(r["narrative"].strip())
            and not IBB.match(r["narrative"].strip())]


def plate_appearances(rows: list[dict]) -> list:
    pas = []
    for r in rows:
        key = (r["inning"], r["half"], r["batterid"])
        if pas and pas[-1][0] == key:
            pas[-1][1].append(r)
        else:
            pas.append((key, [r]))
    return pas


def players() -> dict[str, dict]:
    """選手ID → {name: 表示名, folder: フォルダ名, hangul}。名簿照合.csv と 名簿_読み.csv から。"""
    reading = {(r["team"], r["roster_name"]): r["reading"] for r in csv.DictReader(open(SITE / "名簿_読み.csv", encoding="utf-8-sig"))}
    out = {}
    for r in csv.DictReader(open(SITE / "名簿照合.csv", encoding="utf-8-sig")):
        if not r["playerid"]:
            continue
        rd = reading.get((r["team"], r["roster_name"]), "")
        name = r["roster_name"]
        out[r["playerid"]] = {"name": rd or name, "folder": f"{name}_{rd.replace('・', '')}" if rd else name, "roster": name}
    # 名簿照合にいない選手は WBSC の名前（名の最初の語と姓の最初の語）
    for f in ("batting.csv", "pitching.csv"):
        for r in csv.DictReader(open(DATA / f, encoding="utf-8-sig")):
            if r["playerid"] in out:
                continue
            first = r["firstname"].replace("\\'", "'").split()
            last = r["lastname"].replace("\\'", "'").split()
            nm = " ".join(first[:1] + [last[0].title()] if last else first[:1])
            out[r["playerid"]] = {"name": nm, "folder": nm.replace(" ", ""), "roster": nm}
    return out


def short_name(p: dict) -> str:
    """字幕に出す相手の名前。ラテン文字は「J. Perez」の形に縮める。"""
    n = p["name"]
    if re.search(r"[ァ-ヶ가-힣]", n):
        return n
    parts = n.split()
    return f"{parts[0][0]}. {parts[-1]}" if len(parts) >= 2 else n


def pitch_call(n: str) -> str:
    for en, ja in (("Ball", "ボール"), ("Called Strike", "見逃し"), ("Swinging Strike", "空振り"), ("Foul", "ファウル")):
        if n.startswith(en):
            return ja
    return ""


def result_ja(n: str) -> str:
    """打席の結果を日本語にする。読めない形は空にする（間違った字幕を出さない）。euro_clips.py と同じ。"""
    low = n.lower()
    if "strikeout wild pitch" in low or "strikeout passed ball" in low:
        return "振り逃げ"
    if "strikes out swinging" in low:
        return "空振り三振"
    if "strikes out looking" in low:
        return "見逃し三振"
    if " walks" in low:
        return "四球"
    if "hit by pitch" in low:
        return "死球"
    if "double play" in low:
        return "併殺"
    if "sacrifice hit" in low or "sacrifice bunt" in low:
        return "送りバント"
    if "fielders choice" in low or "fielder's choice" in low:
        return "野選"
    if "error" in low:
        return "エラーで出塁"
    m = re.search(r"grounds out (\d)", n)
    if m:
        return f"{POS[m[1]]}ゴロ"
    if "grounds out 3U" in n:
        return "ファーストゴロ"
    where = next((ja for en, ja in FIELD if en in n), "")
    if "sacrifice fly" in low:
        return f"{where}犠牲フライ" if where else "犠牲フライ"
    for verb, ja in (("singles", "ヒット"), ("doubles", "ツーベース"), ("triples", "スリーベース"), ("homers", "ホームラン")):
        if verb in low:
            if verb == "singles" and "bunt" in low:
                return "バントヒット"
            if verb == "singles":
                if where in ("レフト", "センター", "ライト"):
                    return f"{where}前ヒット"
                if where in ("左中間", "右中間", "レフト線", "ライト線"):
                    return f"{where}へのヒット"
                return f"{where}への内野安打" if where else "ヒット"
            return f"{where}への{ja}" if where else ja
    for verb, ja in (("flies out", "フライ"), ("pops out", "フライ"), ("lines out", "ライナー")):
        if verb in low:
            m = re.search(r"\s[FLP][FP]?(\d)\b", n)
            place = where or (POS.get(m[1], "") if m else "")
            foul = "ファウル" if " foul" in low else ""
            return f"{place}{foul}{ja}" if place else f"{foul}{ja}"
    return ""


# ---------------------------------------------------------------- 得点表示を読む

BUG_INN = re.compile(r"\b(\d{1,2})\s*(ST|ND|RD|TH)\b", re.I)
BUG_CNT = re.compile(r"\b([0-3])\s*[-–—]\s*([0-2])\b")
BUG_OUT = re.compile(r"\b([0-3])\s*OUTS?\b", re.I)
BUG_MPH = re.compile(r"\b(\d{2,3})\s*M\s*P\s*H", re.I)


def cmd_ocr(video: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="gtocr") as tmp:
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={BUG_FPS},crop={BUG_CROP},scale=870:-1",
                        str(Path(tmp) / "%06d.png")], check=True)
        files = sorted(Path(tmp).glob("*.png"))
        chunks = [files[i:i + 300] for i in range(0, len(files), 300)]
        out = []
        with ThreadPoolExecutor(6) as ex:
            for chunk, res in zip(chunks, ex.map(ocr, chunks)):
                for f in chunk:
                    text = " ".join(l["text"] for l in res.get(str(f), []))
                    i, c, o, m = BUG_INN.search(text), BUG_CNT.search(text), BUG_OUT.search(text), BUG_MPH.search(text)
                    out.append([round((int(f.stem) - 1) / BUG_FPS, 2), int(i[1]) if i else None,
                                f"{c[1]}-{c[2]}" if c else None, int(o[1]) if o else None, int(m[1]) if m else None])
    json.dump(out, open(str(video) + ".bug.json", "w"))
    print(len(out), "コマ", sum(1 for o in out if o[2]), "コマでカウントを読めた", sum(1 for o in out if o[4]), "コマで球速を読めた")


def transitions(video: Path) -> list[tuple[float, str, str, int | None]]:
    """カウントが変わった瞬間 [(映像の秒, 前, 後, 回)]。読めない間が3秒を超えたところは使わない。"""
    reads = [r for r in json.load(open(str(video) + ".bug.json")) if r[2]]
    out = []
    for a, b in zip(reads, reads[1:]):
        if a[2] != b[2] and b[0] - a[0] <= 3:
            out.append((b[0], a[2], b[2], b[1] or a[1]))
    return out


def tags(video: Path) -> list[float]:
    """球速の表示が出た瞬間（映像の秒）。読めないコマを1つ挟んで同じ値が続くのは同じ表示とみる。"""
    out, last_t, last_v = [], -99.0, None
    for r in json.load(open(str(video) + ".bug.json")):
        v = r[4] if len(r) > 4 else None
        if v is None:
            if r[2] is not None and r[0] - last_t > 1.5:   # 得点表示は見えていて球速が出ていない
                last_v = None
            continue
        if v != last_v or r[0] - last_t > 4:
            out.append(r[0])
        last_t, last_v = r[0], v
    return out


def expected(game: str) -> list[dict]:
    """各球の「前のカウント → 後のカウント」。打席の最後の球は 0-0 に戻る。"""
    rows = pitches(game)
    out = []
    for _, group in plate_appearances(rows):
        for k, r in enumerate(group):
            nxt = group[k + 1] if k + 1 < len(group) else None
            out.append({"id": r["id"], "utc": ts(r["utctimestamp"]), "inning": int(r["inning"]),
                        "pre": f"{r['balls']}-{r['strikes']}", "post": f"{nxt['balls']}-{nxt['strikes']}" if nxt else "0-0",
                        "final": nxt is None})
    return out


def cmd_align(game: str, video: Path) -> None:
    tr = transitions(video)
    exp = expected(game)
    votes: Counter = Counter()
    for e in exp:
        if e["pre"] == e["post"]:
            continue
        for t, a, b, inn in tr:
            if a == e["pre"] and b == e["post"] and (inn is None or inn == e["inning"] or e["final"]):
                votes[round(t - e["utc"])] += 1
    # 近い秒をまとめて数える（±2秒）
    best = max(votes, key=lambda s: sum(votes[s + d] for d in range(-2, 3)))
    offset = sum(s * votes[s] for s in range(best - 2, best + 3)) / sum(votes[s] for s in range(best - 2, best + 3))
    anchors = {}
    for e in exp:
        if e["pre"] == e["post"]:
            continue
        near = [t for t, a, b, inn in tr if a == e["pre"] and b == e["post"] and abs(t - e["utc"] - offset) <= 10]
        if near:
            anchors[e["id"]] = min(near, key=lambda t: abs(t - e["utc"] - offset))
    diffs = sorted(anchors[i] - e["utc"] for e in exp for i in [e["id"]] if i in anchors)
    shift = diffs[len(diffs) // 2]
    # 投げた瞬間（球速の表示が出た瞬間から TAG_LAG 秒前）
    # 前の球の表示が残っているのを拾わないよう、前の球の目印から4秒以上後の表示だけを見る
    tg = tags(video)
    release, prev_entry, prev_tag = {}, None, -99.0
    for e in exp:
        entry = anchors.get(e["id"], e["utc"] + shift)
        if e["id"] in anchors:
            near = [t for t in tg if entry - 8 <= t <= entry + 0.5 and t > prev_tag + 4]
            pick = near[-1] if near else None
        else:
            lo = max(prev_entry - 1 if prev_entry is not None else entry - 40, prev_tag + 4)
            near = [t for t in tg if lo < t <= entry + 3]
            pick = near[0] if near else None
        if pick is not None:
            release[e["id"]] = pick - TAG_LAG
        prev_tag = pick if pick is not None else entry - 2
        prev_entry = entry
    json.dump({"offset": shift, "anchors": anchors, "release": release}, open(str(video) + ".align.json", "w"))
    start = datetime.fromtimestamp(-shift, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"全{len(exp)}球のうち得点表示で入力の位置が分かった球 {len(anchors)}、球速の表示で投げた瞬間が分かった球 {len(release)}、"
          f"映像の始まり {start} UTC")


def anchor_times(game: str, video: Path) -> dict[str, float]:
    al = json.load(open(str(video) + ".align.json"))
    return {e["id"]: al["anchors"].get(e["id"], e["utc"] + al["offset"]) for e in expected(game)}


def release_times(game: str, video: Path) -> dict[str, float]:
    """投げた瞬間（映像の秒）。球速の目印がない球は、入力の NO_TAG_LEAD 秒前。"""
    al = json.load(open(str(video) + ".align.json"))
    anc = anchor_times(game, video)
    return {i: al.get("release", {}).get(i, t - NO_TAG_LEAD) for i, t in anc.items()}


# ---------------------------------------------------------------- 1球ずつに切る

def out_root(ioc: str) -> Path:
    return ROOT / "04_対戦国" / COUNTRY[ioc] / "大会2026_映像"


def game_label(game: str, ioc: str) -> tuple[str, str, str]:
    """(月日の表示 11/6, フォルダの頭 1106, 相手 キューバ戦)"""
    g = game_info(game)
    d = datetime.strptime(g["start"][:10], "%Y-%m-%d")
    rival = g["awayioc"] if g["homeioc"] == ioc else g["homeioc"]
    return f"{d.month}/{d.day}", d.strftime("%m%d"), f"{COUNTRY.get(rival, rival)}戦"


def caption(head: str, who: str, after: str, path: Path) -> None:
    img = Image.new("RGB", (VW, STRIP), "#111418")
    draw = ImageDraw.Draw(img)
    x = draw_text(draw, (20, 16), head, 26, "#FFFFFF")
    x = draw_text(draw, (x, 19), who, 22, "#AEB6C2")
    if after:
        size = 26
        while size > 16 and x + 24 + text_width(after, size) > VW - 20:
            size -= 2
        draw_text(draw, (VW - 20 - text_width(after, size), 16 + (26 - size) // 2), after, size, "#FFD76A")
    img.save(path)


def render(video: Path, start: float, length: float, reveal: float, before: Path, after: Path, out: Path) -> None:
    graph = (f"[0:v]fps={FPS},scale={VW}:{VH},setsar=1,pad={VW}:{VH + STRIP}:0:{STRIP}:black[b];"
             "[b][1:v]overlay=0:0:shortest=1[c];"
             f"[c][2:v]overlay=0:0:shortest=1:enable='gte(t,{reveal:.2f})'[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(start, 0):.2f}", "-t", f"{length:.2f}", "-i", str(video),
                    "-loop", "1", "-i", str(before), "-loop", "1", "-i", str(after),
                    "-filter_complex", graph, "-map", "[v]", "-t", f"{length:.2f}", *FLAGS, "-f", "mpegts", str(out)], check=True)


def clip_stem(r: dict, k: int, final: bool, res: str, other: str) -> str:
    call = pitch_call(r["narrative"].strip())
    short = other.split()[-1] if other else ""
    stem = f"{r['inning']}回_{short}_{k}球目_{r['balls']}-{r['strikes']}" + (f"_{res}" if final and res else (f"_{call}" if call else ""))
    return re.sub(r'[\\/:*?"<>|]', "", stem)


def team_rows(game: str, ioc: str, role: str) -> list[dict]:
    """role = 投手（その国が守る球）か 打者（その国が攻める球）。"""
    team = team_name(ioc)
    return [r for r in pitches(game) if (r["batting_team"] == team) == (role == "打者")]


def pa_items(game: str, ioc: str, role: str, nm: dict) -> list[dict]:
    """その国の投手（または打者）の打席。1打席ごとに、全球のファイルの置き場所と、場面分けに使う値。"""
    date, mmdd, rival = game_label(game, ioc)
    types = {}
    for f in (out_root(ioc) / "収録").glob(f"{mmdd}_*.mp4.types.json"):
        types.update(json.load(open(f)))
    out = []
    for i, ((inning, half, bid), group) in enumerate(plate_appearances(team_rows(game, ioc, role))):
        r0 = group[0]
        me = r0["pitcherid"] if role == "投手" else bid
        other_id = bid if role == "投手" else r0["pitcherid"]
        res = result_ja(group[-1]["narrative"].strip())
        other = short_name(nm.get(other_id, {"name": ""}))
        folder = out_root(ioc) / role / nm[me]["folder"] / f"{mmdd}_{rival}"
        if role == "打者":
            side = r0["pitcher_throws"]
        else:
            side = r0["batter_bats"] if r0["batter_bats"] != "S" else ("L" if r0["pitcher_throws"] == "R" else "R")
        pitches_ = []
        for k, r in enumerate(group, 1):
            final = k == len(group)
            pitches_.append({"row": r, "k": k, "final": final, "path": folder / (clip_stem(r, k, final, res, other) + ".mp4"),
                             "call": pitch_call(r["narrative"].strip()), "count": (r["balls"], r["strikes"]),
                             "res": res if final else "", "bats": r["batter_bats"], "throws": r["pitcher_throws"],
                             "runners": any(r[f"runner{j}"] not in ("", "0") for j in (1, 2, 3)), "pa": (game, i), "game": game, "date": date,
                             "type": types.get(r["id"], "")})
        out.append({"game": game, "date": date, "rival": rival, "me": me, "inning": int(inning), "half": half,
                    "order": int(r0["playorder"] or 0), "slot": int(r0["lineuporder"] or 9), "side": side, "res": res,
                    "other": other, "folder": folder, "pitches": pitches_, "hand": r0["pitcher_throws"] if role == "投手" else r0["batter_bats"],
                    "complete": all(p["path"].exists() for p in pitches_)})
    return out


def cmd_cut(game: str, ioc: str, video: Path) -> None:
    nm = players()
    anc = anchor_times(game, video)
    rel = release_times(game, video)
    order = [r["id"] for r in pitches(game)]
    prev_of = {rid: rel[order[i - 1]] if i else None for i, rid in enumerate(order)}
    vlen = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                                capture_output=True, text=True, check=True).stdout)
    jobs = []
    for role in ("投手", "打者"):
        for pa in pa_items(game, ioc, role, nm):
            pa["folder"].mkdir(parents=True, exist_ok=True)
            hand = ({"L": "左打者", "R": "右打者", "S": "両打ち"} if role == "投手" else {"L": "左投手", "R": "右投手"}).get(
                pa["pitches"][0]["bats"] if role == "投手" else pa["pitches"][0]["throws"], "")
            head = f"{hand}　{pa['date']} {pa['rival']} {pa['inning']}回{'表' if pa['half'] == 'top' else '裏'}　"
            for p in pa["pitches"]:
                r = p["row"]
                pitch_t = rel[r["id"]]
                in_play = p["final"] and not p["call"] and pa["res"] and "三振" not in pa["res"] and pa["res"] not in ("四球", "死球")
                start = pitch_t - BEFORE
                # 前の球の投げた瞬間の4秒後より前には戻らない（前の球の投球を入れないため）
                prev = prev_of[r["id"]]
                if prev is not None and prev < pitch_t - 1:
                    start = max(start, prev + 4)
                # 投げた後の字幕（判定と打席の結果）は、カウントが変わった瞬間か、投げた2.5秒後の早いほうから
                entry = min(anc[r["id"]], pitch_t + 2.5) if anc[r["id"]] > pitch_t else pitch_t + 2.5
                length = min(pitch_t + (AFTER_HIT if in_play else AFTER), vlen) - start
                count = f"{r['balls']}-{r['strikes']}"
                after = "　".join(x for x in (p["call"], f"→ {pa['res']}" if p["final"] and pa["res"] else "") if x)
                jobs.append((p["path"], head, f"{pa['other']}　{count}", after, start, length, entry - start, pa))
    with tempfile.TemporaryDirectory(prefix="gtcut") as tmp:
        work = Path(tmp)

        def one(i_job):
            i, (path, head, who, after, start, length, reveal, _) = i_job
            a, b = work / f"{i}a.png", work / f"{i}b.png"
            caption(head, who, "", a)
            caption(head, who, after, b)
            tsp = path.with_suffix(".ts")
            render(video, start, length, reveal, a, b, tsp)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(tsp), "-c", "copy", "-movflags", "+faststart", str(path)], check=True)
            return path

        with ThreadPoolExecutor(3) as ex:
            list(ex.map(one, enumerate(jobs)))
        made = defaultdict(list)
        for path, *_, pa in jobs:
            made[pa["folder"]].append(path.with_suffix(".ts"))
        for folder, items in made.items():
            lst = work / "list.txt"
            lst.write_text("".join(f"file '{i}'\n" for i in items), encoding="utf-8")
            joined = folder.parent / f"{folder.name}_まとめ.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                            "-movflags", "+faststart", str(joined)], check=True)
            for i in items:
                i.unlink()
            print(folder.parent.name, joined.name, len(items), "球")


# ---------------------------------------------------------------- 対策映像（投手5本）

def games_of(ioc: str) -> list[str]:
    """その国の試合のうち、映像を切ってあるもの（大会2026_映像/収録/<月日>_*.mp4.align.json がある試合）。"""
    rec = out_root(ioc) / "収録"
    have = {p.name[:4] for p in rec.glob("*.mp4.align.json")}
    out = []
    for g in json.load(open(DATA / "games.json")):
        if ioc in (g["homeioc"], g["awayioc"]) and g["start"][5:7] + g["start"][8:10] in have:
            out.append(str(g["id"]))
    return out


def all_pas(ioc: str, role: str) -> list[dict]:
    nm = players()
    return [pa for g in games_of(ioc) for pa in pa_items(g, ioc, role, nm)]


def rate(part: int, whole: int) -> str:
    return f"{part}/{whole}（{round(100 * part / whole)}%）" if whole else "なし"


def kind(res: str) -> str:
    if "三振" in res:
        return "三振"
    if any(w in res for w in ("ヒット", "安打", "ベース", "ホームラン")):
        return "安打"
    if res in ("四球", "死球"):
        return "四死球"
    return "凡打"


def pa_line(chosen: list[dict]) -> str:
    ends = [p for p in chosen if p["final"]]
    return (f"{len(ends)}打席：安打 {sum(kind(p['res']) == '安打' for p in ends)}・三振 {sum('三振' in p['res'] for p in ends)}"
            f"・四死球 {sum(p['res'] in ('四球', '死球') for p in ends)}")


def sections(ps: list[dict]) -> list:
    """対策映像の場面分け（2026-11-07 にすばるの指示で、初球と2ストライクからの2本を外した）。
    1_走者あり・2_対右打者・3_対左打者・4_球種別。球種別は球種の分かった球があるときだけ（BASSの入力を <収録>.types.json に置く）。
    初球と追い込んでからの数字は、対右・対左の表紙に入れる。"""
    strike = lambda p: p["call"] != "ボール" and p["res"] not in ("四球", "死球")
    runners = [p for p in ps if p["runners"]]
    left = [p for p in ps if p["bats"] == "L" or (p["bats"] == "S" and p["throws"] == "R")]
    right = [p for p in ps if p["bats"] == "R" or (p["bats"] == "S" and p["throws"] == "L")]
    lefty = ps[0]["throws"] == "L"

    def side_lines(chosen: list[dict], note: str) -> list[str]:
        first = [p for p in chosen if p["count"] == ("0", "0")]
        two = [p for p in chosen if p["count"][1] == "2"]
        return [f"{len(chosen)}球{note}",
                f"ストライク {rate(sum(strike(p) for p in chosen), len(chosen))}　初球ストライク {rate(sum(strike(p) for p in first), len(first))}",
                f"2ストライクから {len(two)}球、三振 {sum(p['final'] and '三振' in p['res'] for p in two)}",
                pa_line(chosen)]

    out = [
        ("1_走者あり", "走者がいるとき", [f"{len(runners)}球（全{len(ps)}球のうち）",
                                         f"ストライク {rate(sum(strike(p) for p in runners), len(runners))}",
                                         "セットの間合いとけん制の様子を見る"], runners),
        ("2_対右打者", "右打者への球", side_lines(right, "（両打ちが右打席に入った球を含む）" if lefty else "（両打ちは左打席に入るので含まない）"), right),
        ("3_対左打者", "左打者への球", side_lines(left, "（両打ちは右打席に入るので含まない）" if lefty else "（両打ちが左打席に入った球を含む）"), left),
    ]
    typed = [p for p in ps if p.get("type")]
    if typed:
        kinds = Counter(p["type"] for p in typed)
        order = [k for k, _ in kinds.most_common()]
        chosen = sorted(typed, key=lambda p: order.index(p["type"]))
        out.append(("4_球種別", "球種ごと", [f"{len(typed)}球（全{len(ps)}球のうち球種が分かった球）",
                                             "、".join(f"{k} {v}" for k, v in kinds.most_common())], chosen))
    return out


def card(who: str, hand: str, title: str, lines: list[str], games: str, path: Path) -> None:
    img = Image.new("RGB", (VW, VH + STRIP), "#111418")
    draw = ImageDraw.Draw(img)
    draw_text(draw, (80, 150), f"{who}（{hand}）", 40, "#AEB6C2")
    draw_text(draw, (80, 220), title, 72, "#FFFFFF")
    for i, line in enumerate(lines):
        draw_text(draw, (80, 350 + i * 64), line, 36, "#FFD76A")
    draw_text(draw, (80, VH + STRIP - 90), games, 26, "#AEB6C2")
    img.save(path)


def card_ts(png: Path, out: Path, flags: list[str]) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(png), "-t", str(CARD_SECONDS),
                    *flags, "-f", "mpegts", str(out)], check=True)


def games_line(items: list[dict]) -> str:
    return "、".join(sorted({f"{p['date']} {p['rival']}" for p in items})) + "（U-23ワールドカップ2026）"


def find_player(name: str) -> tuple[str, dict]:
    nm = players()
    for pid, p in nm.items():
        if name in (p["roster"], p["name"], p["folder"]):
            return pid, p
    raise SystemExit(f"{name} が見つからない")


def cmd_reel(ioc: str, name: str, only: list[str]) -> None:
    pid, me = find_player(name)
    pas = [pa for pa in all_pas(ioc, "投手") if pa["me"] == pid]
    ps = [p for pa in pas for p in pa["pitches"] if p["path"].exists()]
    out_dir = out_root(ioc) / "投手" / me["folder"] / "対策"
    out_dir.mkdir(parents=True, exist_ok=True)
    hand = {"L": "左投手", "R": "右投手"}.get(ps[0]["throws"], "")
    with tempfile.TemporaryDirectory(prefix="reel") as tmp:
        work = Path(tmp)
        for fname, title, lines, chosen in sections(ps):
            if only and fname.split("_")[0] not in only:
                continue
            if not chosen:   # 走者を出さなかった、左打者と当たっていない、など
                print(fname, "0球なので作らない")
                continue
            png, head = work / f"{fname}.png", work / f"{fname}.ts"
            card(me["name"], hand, title, lines, games_line(pas), png)
            card_ts(png, head, FLAGS)
            files = [head]
            for i, p in enumerate(chosen):
                if fname.endswith("球種別") and (i == 0 or chosen[i - 1]["type"] != p["type"]):
                    sub = work / f"{fname}_{len(files)}.png"
                    n = sum(q["type"] == p["type"] for q in chosen)
                    card(me["name"], hand, p["type"], [f"{n}球"], games_line(pas), sub)
                    card_ts(sub, sub.with_suffix(".ts"), FLAGS)
                    files.append(sub.with_suffix(".ts"))
                files.append(p["path"])
            lst = work / f"{fname}.txt"
            lst.write_text("".join(f"file '{f}'\n" for f in files), encoding="utf-8")
            reel = out_dir / f"{me['folder']}_{fname}.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                            *FLAGS, "-movflags", "+faststart", str(reel)], check=True)
            print(reel.name, len(chosen), "球", " / ".join(lines))


# ---------------------------------------------------------------- YouTube の1本

YT_FLAGS = ["-c:v", "h264_videotoolbox", "-b:v", "2500k", "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-an", "-movflags", "+faststart"]
PITCHER_PAS, BATTER_PAS_R = 5, 4


def hand_label(code: str, role: str) -> str:
    return "両打ち" if code == "S" else {"L": "左", "R": "右"}.get(code, "") + role


def choose(pas: list[dict], n: int | None) -> list[dict]:
    """全球そろった打席から n 打席。三振・安打・四死球・凡打が混ざるように。n が None なら全部。"""
    full = [p for p in pas if p["complete"]]
    key = lambda p: (p["game"], p["inning"], p["order"])
    if n is None or len(full) <= n:
        return sorted(full, key=key)
    full.sort(key=lambda p: (len(p["pitches"]) < 3, -int(p["game"]), p["inning"], p["order"]))
    want = {"三振": 2, "安打": 1, "四死球": 1, "凡打": 1}
    picked = []
    for p in full:
        if len(picked) < n and want.get(kind(p["res"]), 0) > 0:
            picked.append(p)
            want[kind(p["res"])] -= 1
    for p in full:
        if len(picked) < n and p not in picked:
            picked.append(p)
    return sorted(picked, key=key)


def summary(pas: list[dict]) -> str:
    c = Counter(kind(p["res"]) for p in pas)
    return f"{len(pas)}打席：安打 {c['安打']}・三振 {c['三振']}・四死球 {c['四死球']}"


def duration(path: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True, check=True).stdout)


def cmd_youtube(ioc: str, kind_: str, starter: str | None, first: list[str] | None = None) -> None:
    role = "投手" if kind_ == "投手" else "打者"
    nm = players()
    pas = all_pas(ioc, role)
    out_dir = out_root(ioc) / "YouTube"
    out_dir.mkdir(parents=True, exist_ok=True)
    pieces: list[Path] = []
    chapters: list[tuple[int, str]] = []
    with tempfile.TemporaryDirectory(prefix="yt") as tmp:
        work = Path(tmp)

        def add_card(who, hand, title, lines, games):
            png = work / f"c{len(pieces)}.png"
            card(who, hand, title, lines, games, png)
            card_ts(png, png.with_suffix(".ts"), YT_FLAGS[:-2])
            pieces.append(png.with_suffix(".ts"))

        if role == "投手":
            by = defaultdict(list)
            for pa in pas:
                by[pa["me"]].append(pa)
            order = sorted(by, key=lambda m: -sum(len(pa["pitches"]) for pa in by[m]))
            if starter:
                sid, sp = find_player(starter)
                reels = sorted(p for p in (out_root(ioc) / "投手" / sp["folder"] / "対策").glob("*_[0-9]_*.mp4") if "スマホ用" not in p.name)
                if reels:
                    hand = hand_label(by[sid][0]["hand"], "投手")
                    chapters.append((len(pieces), f"{sp['name']}（{hand}・先発）" + reels[0].stem.rsplit("_", 1)[1]))
                    add_card(sp["name"], hand, "日本戦の先発", ["このあと5つの場面に分けて見せます",
                                                           "初球 → 追い込んでから → 走者あり → 左打者 → 右打者"], games_line(by[sid]))
                    for i, r in enumerate(reels):
                        if i:
                            chapters.append((len(pieces), f"　{sp['name']} {r.stem.rsplit('_', 1)[1]}"))
                        pieces.append(r)
                    order = [m for m in order if m != sid]
            if first:
                # 指定した投手を先に（日本戦で投げそうな順）。残りは球数の多い順
                ids = [find_player(n)[0] for n in first]
                order = [m for m in ids if m in by] + [m for m in order if m not in ids]
            sides = (("R", "対右打者", PITCHER_PAS), ("L", "対左打者", PITCHER_PAS))
        else:
            by = defaultdict(list)
            for pa in pas:
                by[pa["me"]].append(pa)
            last = max(pa["game"] for pa in pas)
            slot = {m: min((pa["slot"], pa["order"]) for pa in v if pa["game"] == last) if any(pa["game"] == last for pa in v)
                    else (10, 0) for m, v in by.items()}
            order = sorted(by, key=lambda m: slot[m])
            sides = (("R", "対右投手", BATTER_PAS_R), ("L", "対左投手", None))

        for m in order:
            mine = by[m]
            who = nm[m]["name"]
            role_hand = hand_label(mine[0]["hand"], "投手" if role == "投手" else "打者")
            chapters.append((len(pieces), f"{who}（{role_hand}）"))
            add_card(who, role_hand, who, [summary([p for p in mine if p["side"] == s]) + f"（{t}）" for s, t, _ in sides],
                     games_line(mine))
            for s, title, n in sides:
                chosen = choose([p for p in mine if p["side"] == s], n)
                if not chosen:
                    continue
                add_card(who, role_hand, f"{title}（{len(chosen)}打席）", [summary(chosen)], games_line(chosen))
                for p in chosen:
                    pieces.extend(q["path"] for q in p["pitches"])
                print(who, title, summary(chosen))

        lst = work / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in pieces), encoding="utf-8")
        video = out_dir / f"{COUNTRY[ioc]}_{kind_}_大会2026.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), *YT_FLAGS, str(video)], check=True)
        starts, t = [], 0.0
        for p in pieces:
            starts.append(t)
            t += CARD_SECONDS if p.suffix == ".ts" else duration(p)
    lines = [f"{int(starts[i] // 3600)}:{int(starts[i] % 3600 // 60):02d}:{int(starts[i] % 60):02d} {name}" if starts[i] >= 3600
             else f"{int(starts[i] // 60)}:{int(starts[i] % 60):02d} {name}" for i, name in chapters]
    text = out_dir / f"{COUNTRY[ioc]}_{kind_}_大会2026_説明文.txt"
    text.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(video.name, f"{duration(video) / 60:.1f}分", f"{video.stat().st_size / 1e6:.0f}MB")
    print(text.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- スマホ用

def cmd_phone(srcs: list[Path]) -> None:
    for src in srcs:
        stem = src.stem.removesuffix("_まとめ")
        if not stem.startswith((src.parent.name, src.parent.parent.name)):
            stem = f"{src.parent.name}_{stem}"
        light = src.with_name(f"{stem}_まとめ_スマホ用.mp4")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
                        "-vf", "scale=960:588,fps=25", "-c:v", "h264_videotoolbox", "-b:v", "450k",
                        "-g", "50", "-an", "-movflags", "+faststart", str(light)], check=True)
        old = list(src.parent.glob(f"{stem}_スマホ用_*.mp4"))
        if old:
            subprocess.run(["/usr/bin/trash", *map(str, old)], check=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(light), "-c", "copy",
                        "-f", "segment", "-segment_time", "360", "-reset_timestamps", "1",
                        "-segment_format_options", "movflags=+faststart", str(src.with_name(f"{stem}_スマホ用_%d.mp4"))], check=True)
        parts = sorted(src.parent.glob(f"{stem}_スマホ用_*.mp4"))
        print(light.name, f"{light.stat().st_size / 1e6:.0f}MB", "→", ", ".join(f"{p.name} {p.stat().st_size / 1e6:.0f}MB" for p in parts))


def main() -> None:
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "ocr":
        cmd_ocr(Path(a[1]))
    elif a[0] == "align":
        cmd_align(a[1], Path(a[2]))
    elif a[0] == "cut":
        cmd_cut(a[1], a[2], Path(a[3]))
    elif a[0] == "reel":
        cmd_reel(a[1], a[2], a[3:])
    elif a[0] == "youtube":
        starter = a[a.index("--starter") + 1] if "--starter" in a else None
        first = a[a.index("--order") + 1].split(",") if "--order" in a else None
        cmd_youtube(a[1], a[2], starter, first)
    elif a[0] == "phone":
        cmd_phone([Path(x) for x in a[1:]])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
