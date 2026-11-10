#!/usr/bin/env python3
"""GameTime から保存した今大会の試合映像（gametime_dl.py）を、WBSCの1球ごとの記録に合わせて切り、
イギリスの欧州2025（../../野球/.../イギリス/調査メモ/euro_*.py）と同じ形の対策映像にする。

    python3 gt_clips.py ocr <映像.mp4>                         # 右下の得点表示（回・カウント・アウト・球速）を毎秒1回読む → <映像>.bug.json
    python3 gt_clips.py align <試合ID> <映像.mp4>               # 記録の時刻と映像の秒のずれを決める → <映像>.align.json
    python3 gt_clips.py check <試合ID> <映像.mp4> [top|bot]     # align のあとに、ずれていそうな打席（目印のない球・使っていない球速の表示）を並べる
    python3 gt_clips.py cut <試合ID> <国> <映像.mp4>            # その国の投手と打者を1球ずつに切り、試合ごとのまとめを作る
    python3 gt_clips.py reel <国> <投手> [番号 ...]             # 投手の対策映像（走者あり・対右打者・対左打者・球種別）
    python3 gt_clips.py youtube <国> 投手|野手 [--starter 投手 [--starter-games 試合]] [--order 投手,投手,...]
                                [--pas 右,左] [--scenes 場面,場面] [--bitrate 2000k]   # 短くするとき
                                                               # YouTube（限定公開）に上げる1本と章の説明文
    python3 gt_clips.py types <試合ID> <BASSの書き出し.txt> <映像.mp4>  # BASSの球種を記録の1球に付ける → <映像>.types.json
    python3 gt_clips.py phone <まとめ.mp4> ...                  # スマホで見る軽い版と、送れる大きさに分けたもの
    python3 gt_clips.py player <国>                             # 選手ごとに、試合ごとのまとめを全試合つないだ1本

BASSの書き出しは、U-23の入力画面（Chrome、ログイン済み）で、試合の1球の記録を「回・表裏・投げる前のボールとストライク・球種の記号・
打席（1左2右）・9分割のコース」の7文字（例 1t01C23、けん制などは記号 -）に縮めて空白でつないだもの。作り方は docs/wbsc-collect.md。

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
import os
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


# WBSCの登録と打席が違う打者（映像で確かめたもの）。김건は登録が右打ちだが、11/6 の映像で左打席（KBOの登録も左）
BATS_FIX = {"809943": "L"}


def pitches(game: str) -> list[dict]:
    rows = [r for r in csv.DictReader(open(DATA / "plays.csv", encoding="utf-8-sig"))
            if r["gameid"] == str(game) and r["nopitch"] in ("0", "") and not NOT_PITCH.match(r["narrative"].strip())
            and not IBB.match(r["narrative"].strip())]
    for r in rows:
        r["batter_bats"] = BATS_FIX.get(r["batterid"], r["batter_bats"])
    return rows


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
    """選手ID → {name: 表示名, folder: フォルダ名, roster, num: 背番号}。名簿照合.csv と 名簿_読み.csv、背番号は今大会の登録名簿 rosters.csv から。"""
    reading = {(r["team"], r["roster_name"]): r["reading"] for r in csv.DictReader(open(SITE / "名簿_読み.csv", encoding="utf-8-sig"))}
    roster = list(csv.DictReader(open(DATA / "rosters.csv", encoding="utf-8-sig")))
    nums = {r["playerid"]: r["uniform"] for r in roster if r["uniform"]}
    throws = {r["playerid"]: r["throws"] for r in roster}
    for f in ("batting.csv", "pitching.csv"):
        for r in csv.DictReader(open(DATA / f, encoding="utf-8-sig")):
            if r["uniform"] and r["playerid"] not in nums:
                nums[r["playerid"]] = r["uniform"]
    out = {}
    for r in csv.DictReader(open(SITE / "名簿照合.csv", encoding="utf-8-sig")):
        if not r["playerid"]:
            continue
        rd = reading.get((r["team"], r["roster_name"]), "")
        name = r["roster_name"]
        out[r["playerid"]] = {"name": rd or name, "folder": f"{name}_{rd.replace('・', '')}" if rd else name, "roster": name}
    # 日本の選手は公式発表の漢字の名前（背番号で結ぶ）。フォルダは「16_飯田真渚斗」にして背番号順に並べる
    official = {r["number"]: r["name"] for r in csv.DictReader(open(SITE / "日本代表_公式発表.csv", encoding="utf-8-sig"))
                if r["role"] == "選手"}
    for r in roster:
        if r["ioc"] == "JPN" and r["uniform"] in official:
            name = official[r["uniform"]]
            out[r["playerid"]] = {"name": name, "folder": f"{r['uniform']}_{name.replace(' ', '')}", "roster": name}
    # 名簿照合にいない選手は WBSC の名前（名の最初の語と姓の最初の語）
    for f in ("batting.csv", "pitching.csv"):
        for r in csv.DictReader(open(DATA / f, encoding="utf-8-sig")):
            if r["playerid"] in out:
                continue
            first = r["firstname"].replace("\\'", "'").split()
            last = r["lastname"].replace("\\'", "'").split()
            nm = " ".join(first[:1] + [last[0].title()] if last else first[:1])
            out[r["playerid"]] = {"name": nm, "folder": nm.replace(" ", ""), "roster": nm}
    for pid, v in out.items():
        v["num"] = nums.get(pid, "")
        v["throws"] = throws.get(pid, "")
    return out


def tagged(p: dict, name: str | None = None) -> str:
    """背番号つきの名前（#51 イ・ドウ）。背番号が分からなければ名前だけ。"""
    n = p["name"] if name is None else name
    return f"#{p['num']} {n}" if p.get("num") else n


SURNAME_PREFIX = {"mc", "mac", "van", "von", "de", "da", "del", "della", "di", "du", "la", "le", "der", "den", "st."}


def short_name(p: dict) -> str:
    """字幕に出す相手の名前。ラテン文字は「J. Perez」の形に縮める。"""
    n = p["name"]
    if re.search(r"[ァ-ヶ가-힣一-鿿]", n):
        return n
    parts = n.split()
    if len(parts) < 2:
        return n
    # 姓の前に付く語（Mc Quirk、Van Duivenbooden、De La Cruz）は姓に含める。11/9 に「S. Quirk」と出ていたのを直した
    k = len(parts) - 1
    while k > 1 and parts[k - 1].lower() in SURNAME_PREFIX:
        k -= 1
    return f"{parts[0][0]}. {' '.join(parts[k:])}"


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


def shown_counts(video: Path, tg: list[float]) -> dict[float, tuple[str | None, str | None]]:
    """球速の表示が出た瞬間ごとの (表示が出る直前のカウント, そのあと14秒までに最初に変わったカウント)。"""
    cnt = {round(r[0]): r[2] for r in json.load(open(str(video) + ".bug.json")) if r[2]}
    out = {}
    for t in tg:
        s = round(t)
        pre = next((cnt[k] for k in (s - 1, s - 2, s, s - 3) if k in cnt), None)
        post = next((cnt[k] for k in range(s, s + 15) if k in cnt and cnt[k] != pre), None)
        out[t] = (pre, post)
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
    seen = shown_counts(video, tg)

    def fits(t: float, e: dict) -> bool:
        """球速の表示が出たときの得点表示が、この球のカウント（投げる前 → 後）と合うか。"""
        pre, post = seen[t]
        if pre != e["pre"]:
            return False
        if post == e["post"]:
            return True
        # 打席の最後の球と、2ストライクからのファウルは、表示が変わらないか消えることがある
        return post is None and (e["final"] or e["pre"] == e["post"])

    release, prev_entry, prev_tag, odd = {}, None, -99.0, []
    for e in exp:
        entry = anchors.get(e["id"], e["utc"] + shift)
        if e["id"] in anchors:
            near = [t for t in tg if entry - 8 <= t <= entry + 0.5 and t > prev_tag + 4]
            if not near:
                # 打球になった球は、カウントが戻るまで10秒ほどかかることがある（11/8 南アフリカ対イギリスで5球）。
                # 8秒前までに表示がないときだけ20秒前まで探す。前の球の入力より前には戻らない
                lo = max(entry - 20, prev_tag + 4, prev_entry - 1 if prev_entry is not None else -99.0)
                near = [t for t in tg if lo < t < entry - 8]
            pick = near[-1] if near else None
        else:
            lo = max(prev_entry - 1 if prev_entry is not None else entry - 40, prev_tag + 4)
            near = [t for t in tg if lo < t <= entry + 3]
            pick = near[0] if near else None
            if pick is None or not fits(pick, e):
                # 入力が遅れた球（数球まとめて入力したときなど）は、前の球の入力より前に投げている。
                # 前の球の目印のあとで、得点表示のカウントがこの球と合う表示を探す（11/9 日本対南アフリカで9球）
                # 探すのは、時刻で拾った表示より前だけ。後ろの表示は次の球のもので、得点表示が1球遅れているときに
                # カウントが合ってしまう（11/6 ベネズエラ対南アフリカの1回裏：三塁打の球に、次の打者の初球の表示が付いた）
                same = [t for t in tg if prev_tag + 4 < t <= entry + 3 and fits(t, e) and (pick is None or t < pick)]
                if same:
                    pick = same[0]
                elif pick is not None:
                    odd.append(e["id"])   # 表示のカウントが記録と違う。位置は入力の時刻から決めたまま
        if pick is not None:
            release[e["id"]] = pick - TAG_LAG
        prev_tag = pick if pick is not None else entry - 2
        prev_entry = entry
    # 得点表示が隠れていて目印がない球は、映像を見て決めた投げた瞬間を <映像>.fix.json に書くと使う。
    # {1球のID: 映像の秒}。直前がリプレイのときは {1球のID: {"t": 映像の秒, "before": 投げる何秒前から切るか}}
    fix_f = Path(str(video) + ".fix.json")
    fixed, lead = {}, {}
    for k, v in (json.load(open(fix_f)) if fix_f.exists() else {}).items():
        fixed[k] = float(v["t"] if isinstance(v, dict) else v)
        if isinstance(v, dict) and "before" in v:
            lead[k] = float(v["before"])
    release.update(fixed)
    json.dump({"offset": shift, "anchors": anchors, "release": release, "fixed": sorted(fixed), "before": lead},
              open(str(video) + ".align.json", "w"))
    start = datetime.fromtimestamp(-shift, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    print(f"全{len(exp)}球のうち得点表示で入力の位置が分かった球 {len(anchors)}、球速の表示で投げた瞬間が分かった球 {len(release) - len(fixed)}、"
          f"映像を見て決めた球 {len(fixed)}、映像の始まり {start} UTC")
    # 映像で確かめたい球（目印がなく入力の時刻から置いた球と、表示のカウントが記録と違う球）
    for e in exp:
        if e["id"] not in release:
            t = anchors.get(e["id"], e["utc"] + shift) - NO_TAG_LEAD
            print(f"  目印なし（入力の時刻から {t:.0f} 秒に置いた）: {e['id']} {e['inning']}回 {e['pre']}→{e['post']}")
        elif e["id"] in odd:
            print(f"  表示のカウントが記録と違う（{release[e['id']]:.0f} 秒）: {e['id']} {e['inning']}回 {e['pre']}→{e['post']}")


def cmd_check(game: str, video: Path, half: str | None = None) -> None:
    """align のあとに、ずれていそうな打席を並べる。目印のない球がある打席と、打席の時間の中に使っていない球速の表示がある打席。

    記録の入力が1球ぶん遅れ続けると、表示が1つずつ後ろの球に結ばれ、打席の最後の球が「目印なし」になる
    （11/8 ベネズエラ対韓国の7回表：6球に表示が6つあり、3球目から1つずつ後ろにずれていた）。
    表示の数と球数が同じで、使っていない表示が打席の途中にあるときは、その形を疑う。回の最初の表示は投球練習、
    打席のあとの表示はリプレイのことが多い。映像で確かめてから <映像>.fix.json に書く。
    half に top か bot を渡すと、表か裏だけを出す（その国の投手の球だけ見たいとき）。"""
    exp = expected(game)
    al = json.load(open(str(video) + ".align.json"))
    rel, anc = al["release"], al["anchors"]
    tg = tags(video)
    bug = {round(r[0]): r[4] for r in json.load(open(str(video) + ".bug.json")) if len(r) > 4 and r[4]}
    rows = {r["id"]: r for r in pitches(game)}
    pas: list[list[dict]] = []
    for (_, _, _), group in plate_appearances(list(rows.values())):
        ids = {r["id"] for r in group}
        pas.append([e for e in exp if e["id"] in ids])
    entry = lambda e: anc.get(e["id"], e["utc"] + al["offset"])
    est = lambda e: rel.get(e["id"], entry(e) - NO_TAG_LEAD)
    used = {round(rel[i] + TAG_LAG) for i in rel if i not in al.get("fixed", [])} | {round(rel[i] + TAG_LAG - 0.3) for i in al.get("fixed", [])}
    for n, pa in enumerate(pas):
        r0 = rows[pa[0]["id"]]
        if half and r0["half"] != half:
            continue
        lo = est(pas[n - 1][-1]) + 4 if n else 0
        hi = est(pas[n + 1][0]) - 3 if n + 1 < len(pas) else est(pa[-1]) + 30
        inwin = [t for t in tg if lo < t < hi]
        free = [t for t in inwin if round(t) not in used]
        if all(e["id"] in rel for e in pa) and not free:
            continue
        print(f"{r0['inning']}回{'表' if r0['half'] == 'top' else '裏'} {len(pa)}球 / 打席の時間の中の表示 {len(inwin)}（使っていない {len(free)}）")
        for e in pa:
            t = rel.get(e["id"])
            mark = "映像で決めた" if e["id"] in al.get("fixed", []) else ""
            print(f"   {e['id']} {e['pre']}→{e['post']}{' 終' if e['final'] else ''}  ", f"{t:.0f}秒" if t is not None else f"目印なし（{est(e):.0f}秒に置いた）",
                  f"入力 {entry(e):.0f}秒{'' if e['id'] in anc else '（得点表示と結べず）'}", mark)
        print("   表示:", " ".join(f"{t:.0f}秒({bug.get(round(t)) or bug.get(round(t) + 1)}MPH){'' if round(t) in used else '＊'}" for t in inwin))


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
    # 日本は対戦国ではないので、選手へのフィードバック用に別の置き場にする（11/9）
    if ioc == "JPN":
        return ROOT / "11_日本代表_大会映像"
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
        while size > 14 and x + 24 + text_width(after, size) > VW - 20:   # 相手の名前が長いとき（S. Van Duivenbooden）は14まで下げる
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
    # ファイル名には姓を使う。漢字の名前（日本の選手）は姓が先
    short = (other.split()[0] if re.search(r"[一-鿿]", other) else other.split()[-1]) if other else ""
    stem = f"{r['inning']}回_{short}_{k}球目_{r['balls']}-{r['strikes']}" + (f"_{res}" if final and res else (f"_{call}" if call else ""))
    return re.sub(r'[\\/:*?"<>|]', "", stem)


def team_rows(game: str, ioc: str, role: str) -> list[dict]:
    """role = 投手（その国が守る球）か 打者（その国が攻める球）。"""
    team = team_name(ioc)
    return [r for r in pitches(game) if (r["batting_team"] == team) == (role == "打者")]


def pa_items(game: str, ioc: str, role: str, nm: dict) -> list[dict]:
    """その国の投手（または打者）の打席。1打席ごとに、全球のファイルの置き場所と、場面分けに使う値。"""
    date, mmdd, rival = game_label(game, ioc)
    types, speed = {}, {}
    for f in (out_root(ioc) / "収録").glob(f"{mmdd}_*.mp4.types.json"):
        types.update(json.load(open(f)))
    for v in (out_root(ioc) / "収録").glob(f"{mmdd}_*.mp4"):
        al_f, bug_f = Path(str(v) + ".align.json"), Path(str(v) + ".bug.json")
        if al_f.exists() and bug_f.exists():
            # 中継の「74 MPH」の表示を、1球の投げた瞬間に合わせて拾う（km/h に直す）
            bug = {round(r[0]): r[4] for r in json.load(open(bug_f)) if len(r) > 4 and r[4]}
            for i, t in json.load(open(al_f)).get("release", {}).items():
                mph = next((bug[k] for k in (round(t + TAG_LAG), round(t + TAG_LAG) + 1, round(t + TAG_LAG) - 1) if k in bug), None)
                if mph and 55 <= mph <= 100:
                    speed[i] = round(mph * 1.609)
    out = []
    used: set[Path] = set()
    for i, ((inning, half, bid), group) in enumerate(plate_appearances(team_rows(game, ioc, role))):
        r0 = group[0]
        me = r0["pitcherid"] if role == "投手" else bid
        other_id = bid if role == "投手" else r0["pitcherid"]
        res = result_ja(group[-1]["narrative"].strip())
        other_p = nm.get(other_id, {"name": "", "num": ""})
        other = short_name(other_p)
        folder = out_root(ioc) / role / nm[me]["folder"] / f"{mmdd}_{rival}"
        if role == "打者":
            side = r0["pitcher_throws"]
        else:
            side = r0["batter_bats"] if r0["batter_bats"] != "S" else ("L" if r0["pitcher_throws"] == "R" else "R")
        pitches_ = []
        for k, r in enumerate(group, 1):
            final = k == len(group)
            path = folder / (clip_stem(r, k, final, res, other) + ".mp4")
            # 同じ回に同じ姓の相手が2人いると名前がぶつかる（11/7 キューバの Pérez 2人）。2つ目からは番号を足す
            n = 2
            while path in used:
                path = folder / (clip_stem(r, k, final, res, other) + f"_{n}.mp4")
                n += 1
            used.add(path)
            pitches_.append({"row": r, "k": k, "final": final, "path": path,
                             "call": pitch_call(r["narrative"].strip()), "count": (r["balls"], r["strikes"]),
                             "res": res if final else "", "bats": r["batter_bats"], "throws": r["pitcher_throws"],
                             "runners": any(r[f"runner{j}"] not in ("", "0") for j in (1, 2, 3)), "pa": (game, i), "game": game, "date": date,
                             "type": types.get(r["id"], ""), "speed": speed.get(r["id"])})
        out.append({"game": game, "date": date, "rival": rival, "me": me, "inning": int(inning), "half": half,
                    "order": int(r0["playorder"] or 0), "slot": int(r0["lineuporder"] or 9), "side": side, "res": res,
                    "other": other, "other_tag": tagged(other_p, other), "me_tag": tagged(nm[me]), "folder": folder, "pitches": pitches_, "hand": r0["pitcher_throws"] if role == "投手" else r0["batter_bats"],
                    "complete": all(p["path"].exists() for p in pitches_)})
    return out


def cmd_cut(game: str, ioc: str, video: Path) -> None:
    nm = players()
    anc = anchor_times(game, video)
    rel = release_times(game, video)
    lead = json.load(open(str(video) + ".align.json")).get("before", {})
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
            head = f"{pa['me_tag']}　{hand}　{pa['date']} {pa['rival']} {pa['inning']}回{'表' if pa['half'] == 'top' else '裏'}　"
            for p in pa["pitches"]:
                r = p["row"]
                pitch_t = rel[r["id"]]
                if pitch_t < 1:
                    # 録画が試合の途中から始まっている（11/7 韓国対日本は配信が4回裏2死から）。その前の球は切らない
                    print(f"  録画の始まりより前なので切らない: {p['path'].name}", flush=True)
                    continue
                in_play = p["final"] and not p["call"] and pa["res"] and "三振" not in pa["res"] and pa["res"] not in ("四球", "死球")
                start = pitch_t - lead.get(r["id"], BEFORE)
                # 前の球の投げた瞬間の4秒後より前には戻らない（前の球の投球を入れないため）
                prev = prev_of[r["id"]]
                if prev is not None and prev < pitch_t - 1:
                    start = max(start, prev + 4)
                # 投げた後の字幕（判定と打席の結果）は、カウントが変わった瞬間か、投げた2.5秒後の早いほうから
                entry = min(anc[r["id"]], pitch_t + 2.5) if anc[r["id"]] > pitch_t else pitch_t + 2.5
                length = min(pitch_t + (AFTER_HIT if in_play else AFTER), vlen) - start
                if length < 2:
                    # 録画が試合の終わりより前で切れている（11/6 南アフリカ対ベネズエラの最後の1球）
                    print(f"  録画の外なので切らない: {p['path'].name}", flush=True)
                    continue
                count = f"{r['balls']}-{r['strikes']}"
                after = "　".join(x for x in (p["call"], f"→ {pa['res']}" if p["final"] and pa["res"] else "") if x)
                jobs.append((p["path"], head, f"vs {pa['other_tag']}　{count}", after, start, length, entry - start, pa))
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
    # 1球も切れなかった打席のフォルダ（録画の外の球だけ）は消す。空のフォルダしか消さない
    for role in ("投手", "打者"):
        for d in sorted((out_root(ioc) / role).glob("*/*"), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
        for d in (out_root(ioc) / role).glob("*"):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()


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
    初球と追い込んでからの数字は、対右・対左の表紙に入れる。表紙はデータだけにし、提案や注記は入れない（11/7 すばるの指示）。"""
    strike = lambda p: p["call"] != "ボール" and p["res"] not in ("四球", "死球")
    runners = [p for p in ps if p["runners"]]
    left = [p for p in ps if p["bats"] == "L" or (p["bats"] == "S" and p["throws"] == "R")]
    right = [p for p in ps if p["bats"] == "R" or (p["bats"] == "S" and p["throws"] == "L")]

    def side_lines(chosen: list[dict], note: str) -> list[str]:
        first = [p for p in chosen if p["count"] == ("0", "0")]
        two = [p for p in chosen if p["count"][1] == "2"]
        return [f"{len(chosen)}球{note}",
                f"ストライク {rate(sum(strike(p) for p in chosen), len(chosen))}　初球ストライク {rate(sum(strike(p) for p in first), len(first))}",
                f"2ストライクから {len(two)}球、三振 {sum(p['final'] and '三振' in p['res'] for p in two)}",
                pa_line(chosen)]

    out = [
        ("1_走者あり", "走者がいるとき", [f"{len(runners)}球（全{len(ps)}球のうち）",
                                         f"ストライク {rate(sum(strike(p) for p in runners), len(runners))}"], runners),
        ("2_対右打者", "右打者への球", side_lines(right, ""), right),
        ("3_対左打者", "左打者への球", side_lines(left, ""), left),
    ]
    typed = [p for p in ps if p.get("type")]
    if typed:
        kinds = Counter(p["type"] for p in typed)
        order = [k for k, _ in kinds.most_common()]
        chosen = sorted(typed, key=lambda p: order.index(p["type"]))
        def avg(k):
            sp = [p["speed"] for p in typed if p["type"] == k and p.get("speed")]
            return f"（平均{round(sum(sp) / len(sp))}km）" if sp else ""
        out.append(("4_球種別", "球種ごと", [f"{len(typed)}球"]
                    + [f"{k} {v}球{avg(k)}" for k, v in kinds.most_common()], chosen))
    return out


def card(who: str, hand: str, title: str, lines: list[str], games: str, path: Path) -> None:
    img = Image.new("RGB", (VW, VH + STRIP), "#111418")
    draw = ImageDraw.Draw(img)
    draw_text(draw, (80, 150), f"{who}（{hand}）", 40, "#AEB6C2")
    draw_text(draw, (80, 220), title, 72, "#FFFFFF")
    # 球種が5つあると6行になり、下の試合名に重なっていた（11/9 南アフリカの Tribe・White）。行が多いときは行の間を詰める
    step = min(64, (VH + STRIP - 120 - 350) // max(len(lines), 1))
    for i, line in enumerate(lines):
        draw_text(draw, (80, 350 + i * step), line, 36, "#FFD76A")
    # 4試合ぶん並ぶと右端からはみ出す（11/10 ベネズエラの野手）。収まるまで文字を小さくする
    size = 26
    while size > 16 and 80 + text_width(games, size) > VW - 40:
        size -= 1
    draw_text(draw, (80, VH + STRIP - 90), games, size, "#AEB6C2")
    img.save(path)


def card_ts(png: Path, out: Path, flags: list[str]) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(png), "-t", str(CARD_SECONDS),
                    *flags, "-f", "mpegts", str(out)], check=True)


def games_line(items: list[dict]) -> str:
    return "、".join(sorted({f"{p['date']} {p['rival']}" for p in items})) + "（U-23ワールドカップ2026）"


def find_player(name: str) -> tuple[str, dict]:
    nm = players()
    hits = [(pid, p) for pid, p in nm.items() if name in (p["roster"], p["name"], p["folder"])]
    if not hits:
        raise SystemExit(f"{name} が見つからない")
    # 名簿照合に過去の大会のIDもある選手（キューバの予選組など）は、今大会の背番号があるほう
    return max(hits, key=lambda x: bool(x[1].get("num")))


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
            card(tagged(me), hand, title, lines, games_line(pas), png)
            card_ts(png, head, FLAGS)
            files = [head]
            for i, p in enumerate(chosen):
                if fname.endswith("球種別") and (i == 0 or chosen[i - 1]["type"] != p["type"]):
                    sub = work / f"{fname}_{len(files)}.png"
                    same = [q for q in chosen if q["type"] == p["type"]]
                    sp = [q["speed"] for q in same if q.get("speed")]
                    sub_lines = [f"{len(same)}球"] + ([f"平均 {round(sum(sp) / len(sp))}km　最速 {max(sp)}km（球速が出た{len(sp)}球）"] if sp else [])
                    card(tagged(me), hand, p["type"], sub_lines, games_line(pas), sub)
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


def cmd_youtube(ioc: str, kind_: str, starter: str | None, first: list[str] | None = None, starter_games: str | None = None,
                pas_n: tuple[int | None, int | None] | None = None, scenes: list[str] | None = None) -> None:
    """pas_n は1人あたりの (対右, 対左) の打席数（None は全部）。scenes は先発の対策映像のうち使う場面（例 対右打者,対左打者）。
    2026-11-08 キューバ：2試合分で長くなり、アップロードが試合に間に合わないので、--pas と --scenes で短くした。"""
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
                rdir = out_root(ioc) / "投手" / sp["folder"] / "対策"
                if not rdir.exists():
                    # 今大会に投げていない先発は、別に作った対策映像（<国>/<名前>_映像/対策/。박준성は park_reels.py）
                    rdir = out_root(ioc).parent / f"{sp['roster']}_映像" / "対策"
                reels = sorted(p for p in rdir.glob("*_[0-9]_*.mp4") if "スマホ用" not in p.name)
                if scenes:
                    reels = [r for r in reels if r.stem.rsplit("_", 1)[1] in scenes]
                if reels:
                    hand = hand_label(by[sid][0]["hand"] if sid in by else sp.get("throws", ""), "投手")
                    scenes = [r.stem.rsplit("_", 1)[1] for r in reels]
                    chapters.append((len(pieces), f"{tagged(sp)}（{hand}・先発）" + scenes[0]))
                    add_card(tagged(sp), hand, "日本戦の先発", [f"このあと{len(reels)}つの場面に分けて見せます", " → ".join(scenes)],
                             games_line(by[sid]) if sid in by else (starter_games or ""))
                    for i, r in enumerate(reels):
                        if i:
                            chapters.append((len(pieces), f"　{tagged(sp)} {r.stem.rsplit('_', 1)[1]}"))
                        pieces.append(r)
                    order = [m for m in order if m != sid]
            if first:
                # 指定した投手を先に（日本戦で投げそうな順）。残りは球数の多い順
                ids = [find_player(n)[0] for n in first]
                order = [m for m in ids if m in by] + [m for m in order if m not in ids]
            nR, nL = pas_n or (PITCHER_PAS, PITCHER_PAS)
            sides = (("R", "対右打者", nR), ("L", "対左打者", nL))
        else:
            by = defaultdict(list)
            for pa in pas:
                by[pa["me"]].append(pa)
            last = max(pa["game"] for pa in pas)
            slot = {m: min((pa["slot"], pa["order"]) for pa in v if pa["game"] == last) if any(pa["game"] == last for pa in v)
                    else (10, 0) for m, v in by.items()}
            order = sorted(by, key=lambda m: slot[m])
            nR, nL = pas_n or (BATTER_PAS_R, None)
            sides = (("R", "対右投手", nR), ("L", "対左投手", nL))

        for m in order:
            mine = by[m]
            who = tagged(nm[m])
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


BASS_KIND = {"F": "ストレート", "S": "スライダー", "C": "カーブ", "P": "スプリット", "H": "チェンジアップ", "T": "カット", "W": "ツーシーム", "K": "シンカー"}


def _lcs(a: list, b: list) -> list[tuple[int, int]]:
    """2つの並びの、順番を保った一番長い対応（添字の組）。"""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            dp[i][j] = dp[i + 1][j + 1] + 1 if a[i] == b[j] else max(dp[i + 1][j], dp[i][j + 1])
    out, i, j = [], 0, 0
    while i < n and j < m:
        if a[i] == b[j]:
            out.append((i, j)); i += 1; j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            i += 1
        else:
            j += 1
    return out


def match_types(game: str, bass_txt: Path) -> tuple[dict, list[str]]:
    """BASSの球種を記録の1球に付ける。回・表裏ごとに、まず打席を順番に対応させ、打席の中は「投げる前のカウント」の並びで合わせる。

    11/10 までは回・表裏の全球をひと続きの並びとして difflib で合わせていた。BASS の球数が記録より少ない回では、
    「0-0、0-1、0-2、0-0、0-1」のような同じ並びが別の打席にもあると、いちばん長く一致する所（別の打席）に飛んで付いていた
    （11/8 ベネズエラ対韓国の6回表：記録14・BASS11で、1人目の3球に4人目のスライダー3球が付いた）。
    BASS の打席の切れ目は、カウントが 0-0 に戻るか、ボール・ストライクが減った所。球種が空でコースが入っている球（球種を入れ忘れた投球）は
    並びに残し、球種もコースもない球（けん制）は外す。"""
    B, W = defaultdict(list), defaultdict(list)
    for t in bass_txt.read_text().split():
        if t[4] == "-" and t[6:7] in ("0", ""):
            continue
        pas, cnt = B[(int(t[0]), "top" if t[1] == "t" else "bot")], t[2:4]
        if not pas or cnt == "00" or cnt[0] < pas[-1][-1][0][0] or cnt[1] < pas[-1][-1][0][1]:
            pas.append([])
        pas[-1].append((cnt, t[4]))
    rows = pitches(game)
    for (inning, half, _), group in plate_appearances(rows):
        W[(int(inning), half)].append(group)
    types, miss = {}, []
    for key in sorted(set(B) | set(W)):
        bp, wp = B.get(key, []), W.get(key, [])
        n, m = len(wp), len(bp)
        pair = [[_lcs([f"{r['balls']}{r['strikes']}" for r in wp[i]], [x[0] for x in bp[j]]) for j in range(m)] for i in range(n)]
        # 打席どうしの対応：一致する球の数の合計がいちばん多くなるように、順番を保って結ぶ（同点なら1対1の並びを優先）
        dp = [[0.0] * (m + 1) for _ in range(n + 1)]
        for i in range(n - 1, -1, -1):
            for j in range(m - 1, -1, -1):
                dp[i][j] = max(dp[i + 1][j + 1] + len(pair[i][j]) + 0.01, dp[i + 1][j], dp[i][j + 1])
        i = j = got = 0
        while i < n and j < m:
            if dp[i][j] == dp[i + 1][j + 1] + len(pair[i][j]) + 0.01:
                for a, b in pair[i][j]:
                    if bp[j][b][1] != "-":
                        types[wp[i][a]["id"]] = BASS_KIND.get(bp[j][b][1], "その他")
                        got += 1
                i += 1; j += 1
            elif dp[i][j] == dp[i + 1][j]:
                i += 1
            else:
                j += 1
        nw, nb = sum(len(x) for x in wp), sum(1 for pa in bp for x in pa if x[1] != "-")
        if got != nw or nb != nw:
            miss.append(f"{key[0]}回{'表' if key[1] == 'top' else '裏'} 記録{nw} BASS{nb} 一致{got}")
    return types, miss


def cmd_types(game: str, bass_txt: Path, video: Path) -> None:
    """BASSの球種を記録の1球に付けて <映像>.types.json に書く（合わせ方は match_types）。"""
    types, miss = match_types(game, bass_txt)
    json.dump(types, open(str(video) + ".types.json", "w"), ensure_ascii=False)
    print(f"記録 {len(pitches(game))}球のうち球種が付いた {len(types)}球", *miss, sep="\n  ")


# ---------------------------------------------------------------- 選手ごとの全試合の1本

def cmd_player(ioc: str) -> None:
    """投手と打者の選手フォルダごとに、試合ごとのまとめ（<月日>_<相手>_まとめ.mp4）を日付の順につなぎ、<選手>_全試合.mp4 にする。
    試合が増えたら cut のあとに流し直す。1試合だけの選手は、まとめと同じ中身なのでハードリンクにする。"""
    for role in ("投手", "打者"):
        base = out_root(ioc) / role
        for d in sorted(p for p in base.iterdir() if p.is_dir()) if base.exists() else []:
            parts = sorted(d.glob("[0-9][0-9][0-9][0-9]_*_まとめ.mp4"))
            if not parts:
                continue
            out = d / f"{d.name}_全試合.mp4"
            out.unlink(missing_ok=True)
            if len(parts) == 1:
                os.link(parts[0], out)
            else:
                with tempfile.TemporaryDirectory(prefix="player") as tmp:
                    lst = Path(tmp) / "list.txt"
                    lst.write_text("".join("file '{}'\n".format(str(p).replace("'", "'\\''")) for p in parts), encoding="utf-8")
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                                    "-movflags", "+faststart", str(out)], check=True)
            print(role, d.name, " + ".join(p.name.removesuffix("_まとめ.mp4") for p in parts), f"{duration(out) / 60:.1f}分")


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
    elif a[0] == "check":
        cmd_check(a[1], Path(a[2]), a[3] if len(a) > 3 else None)
    elif a[0] == "cut":
        cmd_cut(a[1], a[2], Path(a[3]))
    elif a[0] == "reel":
        cmd_reel(a[1], a[2], a[3:])
    elif a[0] == "youtube":
        starter = a[a.index("--starter") + 1] if "--starter" in a else None
        first = a[a.index("--order") + 1].split(",") if "--order" in a else None
        sg = a[a.index("--starter-games") + 1] if "--starter-games" in a else None
        pas_n = tuple(None if x == "全部" else int(x) for x in a[a.index("--pas") + 1].split(",")) if "--pas" in a else None
        scenes = a[a.index("--scenes") + 1].split(",") if "--scenes" in a else None
        if "--bitrate" in a:
            YT_FLAGS[YT_FLAGS.index("-b:v") + 1] = a[a.index("--bitrate") + 1]
        cmd_youtube(a[1], a[2], starter, first, sg, pas_n, scenes)
    elif a[0] == "types":
        cmd_types(a[1], Path(a[2]), Path(a[3]))
    elif a[0] == "phone":
        cmd_phone([Path(x) for x in a[1:]])
    elif a[0] == "player":
        cmd_player(a[1])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
