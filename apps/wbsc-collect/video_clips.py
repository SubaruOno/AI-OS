#!/usr/bin/env python3
"""台湾U23の日本遠征の映像を、打席ごとに切り抜く道具。

試合の定義（試合.json・選手.csv）と、試合ごとの途中のファイル・動画は
~/野球/U23ワールドカップ2026/08_映像切り抜き/ に置く（選手の映像なのでリポジトリに入れない）。

    python3 video_clips.py prep [--game ID] [--force]   # 実況の文字起こしとカメラの切り替わり
    python3 video_clips.py prep --dtw [--game ID]       # 1球ごとの時刻用の文字起こし（時刻合わせつき、遅い）
    python3 video_clips.py segment [--game ID]          # 打席の区切り → <試合>/打席_自動.csv
    python3 video_clips.py score                        # 西部ガス戦の正解と照らす（決まりを変えたら流す。78打席中77）
    python3 video_clips.py scorebook --game ID          # スコア.csv（印刷のスコアを読み取ったもの）を当てて 打席.csv を書く
    python3 video_clips.py review [--port 8783]         # 確認用の画面（127.0.0.1 だけ）→ <試合>/打席.csv
    python3 video_clips.py export [--game ID]           # 打席ごとの動画とサムネイル → clips/<試合>/
    python3 video_clips.py serve DIR [--port 8783]      # 組み立てたサイトを、動画の部分読み込みに応じて配る

区切りは、実況の言葉（「4番、ファースト、ソン・ボーハン」「147、ボール」「3アウト」「2回の表」）と、
カメラの切り替わり（ffmpeg の scene）から出す。決まりは西部ガス戦で78打席中77を当てたもので（スコアで確かめた正解）、
試合ごとのくせに合わせ込む決まり（回の終わりのまとめで回を付け直す、など）は入れていない。
打席_自動.csv は segment のたびに作り直す。確かめて直したものは 打席.csv で、segment は触らない。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path.home() / "野球" / "U23ワールドカップ2026"
DATA = ROOT / "08_映像切り抜き"
VIDEO_DIR = ROOT / "04_対戦国" / "台湾"
MODEL = Path.home() / ".cache" / "whisper" / "ggml-large-v3-turbo.bin"
TAIWAN = "台湾"
OPP = "相手"

AUTO = "打席_自動.csv"
CHECKED = "打席.csv"
FIELDS = ["no", "inning", "half", "order", "bat_team", "batter", "pit_team", "pitcher",
          "start", "end", "n_pitch", "pitches", "results", "headline", "seq", "result", "note", "ctx", "source"]


# ---------------------------------------------------------------- 試合の定義


def games() -> list[dict]:
    return json.loads((DATA / "試合.json").read_text(encoding="utf-8"))["games"]


def game_of(game_id: str) -> dict:
    for g in games():
        if g["id"] == game_id:
            return g
    raise SystemExit(f"試合.json に {game_id} がありません。")


def pick(game_id: str | None) -> list[dict]:
    return [game_of(game_id)] if game_id else games()


def players() -> list[dict]:
    with (DATA / "選手.csv").open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def video_path(game: dict) -> Path:
    return VIDEO_DIR / game["video"]


def game_dir(game: dict) -> Path:
    path = DATA / game["id"]
    path.mkdir(parents=True, exist_ok=True)
    return path


def side_teams(game: dict) -> tuple[str, str]:
    """（表の攻撃, 裏の攻撃）。台湾が先攻なら（台湾, 相手）。"""
    return (TAIWAN, OPP) if game["taiwan"] == "top" else (OPP, TAIWAN)


def readings_of(game: dict) -> dict[str, dict[str, list[str]]]:
    """チームごとに、名前 → 読みの候補。台湾は 選手.csv、相手は 試合.json。"""
    tw = {}
    for p in players():
        kana = [p["reading"]] + [a for a in (p.get("alt_readings") or "").split("|") if a]
        tw[p["name"]] = [k for k in kana if k]
    return {TAIWAN: tw, OPP: {name: [kana] for name, kana in game.get("readings", {}).items()}}


# ---------------------------------------------------------------- prep


def prompt_of(game: dict) -> str:
    """whisper に渡す言葉の手がかり。打順と名前、よく出る言い回し。"""
    reads = readings_of(game)
    parts = []
    for team in side_teams(game):
        label = "台湾代表" if team == TAIWAN else game["opponent"]
        names = []
        for i, name in enumerate(game["orders"][team], 1):
            kana = (reads[team].get(name) or [""])[0]
            names.append(f"{i}番、{kana or name}")
        parts.append(f"{label}。" + "。".join(names))
    return "。".join(parts) + "。147ストライク、1ボール2ストライク。打って、セカンドゴロ、ワンアウト。空振り三振。"


def prep_dtw(game: dict, force: bool) -> None:
    """1球ごとの時刻用の文字起こし（words_dtw.json）。

    ふつうの文字起こしは、30秒の窓ごとの区切りの時刻が数秒〜10秒ずれることがある（西部ガス戦の3打席目で7秒早い）。
    DTW（音声と言葉の細かい対応づけ）を付けると、実況の球速の言葉が投球の0〜2秒後にそろう。
    DTW は flash attention と一緒に使えないので -nfa を付ける（そのぶん遅い）。打席の区切りは words.json のまま使う。
    """
    out = game_dir(game)
    target = out / "words_dtw.json"
    if target.is_file() and not force:
        return
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "a.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video_path(game)), "-vn", "-af",
                        "highpass=f=150,lowpass=f=4000,dynaudnorm", "-ar", "16000", "-ac", "1", str(wav)],
                       check=True)
        stem = Path(tmp) / "w"
        subprocess.run(["whisper-cli", "-m", str(MODEL), "-l", "ja", "-mc", "0", "-bs", "5", "-nfa",
                        "-dtw", "large.v3.turbo", "-ojf", "-of", str(stem), "--prompt", prompt_of(game), str(wav)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        shutil.move(str(stem) + ".json", target)
    print(f"{game['id']}: 1球ごとの時刻用の文字起こし → {target}")


def prep(game: dict, force: bool) -> None:
    out = game_dir(game)
    words, scenes = out / "words.json", out / "scenes.txt"
    video = video_path(game)
    if not video.is_file():
        raise SystemExit(f"映像がありません: {video}")
    cut = None
    if force or not scenes.is_file():
        tmp_scenes = out / "scenes.txt.part"
        cut = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-hwaccel", "videotoolbox", "-i", str(video), "-vf",
             f"scale=320:-2,select='gt(scene,0.2)',metadata=print:file={tmp_scenes}",
             "-an", "-f", "null", "-"])
    if force or not words.is_file():
        with tempfile.TemporaryDirectory() as tmp:
            wav = Path(tmp) / "a.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-af",
                            "highpass=f=150,lowpass=f=4000,dynaudnorm", "-ar", "16000", "-ac", "1",
                            str(wav)], check=True)
            stem = Path(tmp) / "w"
            subprocess.run(["whisper-cli", "-m", str(MODEL), "-l", "ja", "-mc", "0", "-bs", "5",
                            "-ojf", "-of", str(stem), "--prompt", prompt_of(game), str(wav)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            shutil.move(str(stem) + ".json", words)
        print(f"{game['id']}: 文字起こし → {words}")
    if cut is not None:
        if cut.wait() != 0:
            raise SystemExit(f"{game['id']}: カメラの切り替わりの検出に失敗しました")
        (out / "scenes.txt.part").replace(scenes)
        print(f"{game['id']}: カメラの切り替わり → {scenes}")


# ---------------------------------------------------------------- segment


KANJI = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
Z2H = str.maketrans("０１２３４５６７８９", "0123456789")
HALF = re.compile(r"([0-9０-９一二三四五六七八九十]{1,2})\s*[回階会]\s*目?\s*の?\s*(表|裏|ラース|うら)")
BAT = re.compile(r"(?<![背号0-9\-ー−])(バッター\s*)?([1-9１-９一二三四五六七八九])\s*番(?!号|と|目)")
BAT_NAME = re.compile(r"バッター[、 ]*([ァ-ヴー・]{3,})")
PITCH = re.compile(r"(?:(\d)\s*[-ー−]\s*(\d)|表示(?:なし|出し|無し)|([1-9]\d)\s*(?=ボール|ストライク|ファ|打|空|見))"
                   r"[、。 ]*(ボール|ストライク|スト|ファウル|ファール|ファイル|打って|打つ|空振り|カラブリ|見逃し|"
                   r"バント|デッドボール|変化|まっすぐ)")
RESULT = re.compile(r"((?:1|2|3|ワン|ツー|スリー|スリ)\s*(?:アウト|アート|ナート|ナット|アット)|3振|振り逃げ|三振|"
                    r"ゴロ|ゴール|フライ|ライナー|ヒット|安打|ホームラン|ツーベース|2ベース|スリーベース|3ベース|"
                    r"フォアボール|四球|デッドボール|死球|ダブルプレ|ゲッツー|併殺|エラー|失策|犠打|バント|"
                    r"犠牲フライ|フォースアウト|野選|フィルダース)")
THIRD = re.compile(r"(?:3|スリー|スリ|三)\s*(?:アウト|アート|アーチ|アット|ナート)|チェンジ|チャンジ")
SUB = re.compile(r"(ピッチャー|投手)[^。]{0,25}?(代|変|かわ)わ?り?(まして|ました)[、。 ]*(?:ピッチャー[、 ]*)?"
                 r"([ァ-ヴー・一-龯 A-Za-z]{2,})?")
KATA = re.compile(r"[ァ-ヴー・ 　]+")
POSITIONS = ("キャッチャー", "ファースト", "セカンド", "サード", "ショート", "レフト", "センター", "ライト",
             "指名打者", "ピッチャー")
# 西部ガス戦の正解（崎坂さん経由の印刷のスコアで確かめたもの。9回表は4打席）。決まりを変えたら score で照らす
TRUTH_SEIBU = {
    "表": {1: [1, 2, 3], 2: [4, 5, 6, 7], 3: [8, 9, 1], 4: [2, 3, 4, 5, 6, 7], 5: [8, 9, 1, 2, 3, 4, 5],
          6: [6, 7, 8, 9], 7: [1, 2, 3], 8: [4, 5, 6, 7, 8], 9: [9, 1, 2, 3]},
    "裏": {1: [1, 2, 3], 2: [4, 5, 6, 7], 3: [8, 9, 1], 4: [2, 3, 4, 5, 6, 7], 5: [8, 9, 1, 2, 3, 4, 5, 6],
          6: [7, 8, 9, 1], 7: [2, 3, 4, 5, 6, 7, 8], 8: [9, 1, 2, 3]},
}


def num(s: str):
    s = s.translate(Z2H)
    if s.isdigit():
        return int(s)
    if s == "十":
        return 10
    if len(s) == 2 and s[0] == "十":
        return 10 + KANJI[s[1]]
    return KANJI.get(s)


def load_chars(path: Path) -> tuple[str, list[float]]:
    """全文と、1文字ごとの時刻（秒）。whisper-cli -ojf のトークンの時刻を使う。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    text, times = [], []
    for seg in data["transcription"]:
        for tok in seg.get("tokens", []):
            t = tok.get("text", "")
            if not t or t.startswith("[_"):
                continue
            dtw = tok.get("t_dtw", -1)
            sec = dtw / 100 if dtw is not None and dtw >= 0 else tok["offsets"]["from"] / 1000
            for ch in t:
                text.append(ch)
                times.append(sec)
        text.append("。")
        times.append(seg["offsets"]["to"] / 1000)
    return "".join(text), times


def load_cuts(path: Path) -> list[float]:
    if not path.is_file():
        return []
    return [float(m) for m in re.findall(r"pts_time:([0-9.]+)", path.read_text(encoding="utf-8"))]


def norm_kana(s: str) -> str:
    return re.sub(r"[ー・ 　]", "", s)


def kana_score(said: str, kanas: list[str]) -> float:
    said = norm_kana(said)
    best = 0.0
    for kana in kanas:
        k = norm_kana(kana)
        if said and k:
            best = max(best, SequenceMatcher(None, said, k).ratio(),
                       SequenceMatcher(None, said[:len(k) + 1], k).ratio())
    return best


def match_name(said: str, readings: dict[str, list[str]], threshold: float = 0.6) -> tuple[str, float]:
    """実況の言葉に一番近い名前。漢字がそのまま出ていればそれ。近くなければ空。"""
    for name in readings:
        if name in said:
            return name, 1.0
    if len(norm_kana(said)) < 2:
        return "", 0.0
    best, score = "", 0.0
    for name, kanas in readings.items():
        r = kana_score(said, kanas)
        if r > score:
            best, score = name, r
    return (best, score) if score >= threshold else ("", score)


def events(text: str, times: list[float]) -> list[tuple]:
    ev = []
    for m in HALF.finditer(text):
        n = num(m.group(1))
        if not n or n > 12:
            continue
        side = "表" if m.group(2) == "表" else "裏"
        tail = text[m.end():m.end() + 25]
        end = "得点" in tail.split("攻撃")[-1][:12] or re.match(r"[^。]{0,14}得点", tail)
        ev.append((times[m.start()], "half_end" if end else "half_start", (n, side), m.group(0) + tail[:14]))
    for m in BAT.finditer(text):
        if "背" in text[max(0, m.start() - 3):m.start()]:
            continue
        rest = re.split(r"[。、]", text[m.end():m.end() + 22].lstrip("、。 "))[0]
        ev.append((times[m.start()], "batter", num(m.group(2)), text[m.start():m.end()] + rest))
    for m in BAT_NAME.finditer(text):
        if not re.match(r"[、 ]*[1-9１-９一二三四五六七八九]\s*番", text[m.start() + 4:m.start() + 8]):
            ev.append((times[m.start()], "batter", 0, m.group(0)))
    for m in THIRD.finditer(text):
        ev.append((times[m.start()], "third_out", m.group(0), text[max(0, m.start() - 8):m.end() + 6]))
    spans = []  # 数字つきで拾った1球の実況の、文の中の位置
    for m in PITCH.finditer(text):
        spans.append((m.start(), m.end()))
        word = m.group(0)
        if not re.search(r"ボール|ストライク|スト|ファ|打|空振り|見逃し|バント", word):
            # 「表示なし、変化、ボール」のように、種類が後ろに来る言い方
            more = re.match(r"[、 ]*(ボール|ストライク|ファウル|ファール|打って|空振り|見逃し|バント)", text[m.end():m.end() + 8])
            if more:
                word += more.group(1)
        ev.append((times[m.start()], "pitch", pitch_label(word), text[m.start():m.end() + 10]))
    # 球速の数字がない言い方（「まっすぐ、ボール」「変化、打ってファウル」）。数字つきの実況と文の中で重なる・
    # すぐ続くものは同じ球なので足さない（文字起こしが1つの言葉を離れた時刻に割ることがあるため、時刻では見分けない）
    for m in re.finditer(r"(まっすぐ|真っ直ぐ|ストレート|変化|スライダー|カーブ|フォーク|チェンジアップ)[、 ]*"
                         r"(ボール|ストライク|ファウル|ファール|打って|空振り|見逃し)", text):
        if any(a - 1 <= m.start() <= b + 3 for a, b in spans):
            continue
        if re.search(r"\d[\s、。\-ー−]*$", text[max(0, m.start() - 4):m.start()]):
            continue  # 「3-5、まっすぐ」のように球速が前にある（数字つきの形で拾えなかった言い方）
        ev.append((times[m.start()], "pitch", pitch_label(m.group(0)), text[m.start():m.end() + 10]))
    for m in RESULT.finditer(text):
        ev.append((times[m.start()], "result", m.group(0), text[max(0, m.start() - 6):m.end() + 4]))
    for m in SUB.finditer(text):
        ev.append((times[m.start()], "pitcher_change", m.group(4) or "", text[max(0, m.start() - 15):m.end()]))
    ev.sort(key=lambda e: e[0])
    return ev


def pitch_label(raw: str) -> str:
    """実況の1球の言葉を短くする。「4-7ボール」→「147 ボール」。"""
    raw = re.sub(r"[、。 ]", "", raw)
    m = re.match(r"(\d)[-ー−](\d)(.*)", raw)
    if m:
        return f"1{m.group(1)}{m.group(2)} {m.group(3)}"
    m = re.match(r"([1-9]\d)(.*)", raw)
    if m:
        return f"1{m.group(1)} {m.group(2)}"
    return raw.replace("表示なし", "球速なし ").replace("表示出し", "球速なし ").replace("表示無し", "球速なし ")


def segment(game: dict) -> list[dict]:
    out = game_dir(game)
    text, times = load_chars(out / "words.json")
    cuts = load_cuts(out / "scenes.txt")
    reads = readings_of(game)
    top, bot = side_teams(game)
    team_of = lambda side: top if side == "表" else bot
    defense_of = lambda side: bot if side == "表" else top
    order_now = {team: {str(i): n for i, n in enumerate(names, 1)} for team, names in game["orders"].items()}
    pitch_seq = {team: list(names) for team, names in game.get("pitchers", {}).items()}
    pitcher_now = {team: names[0] for team, names in pitch_seq.items() if names}
    duration = times[-1] + 5 if times else 0

    half = (1, "表")
    pas: list[dict] = []
    cur = None
    expect = {"表": 0, "裏": 0}
    last_third = -99.0

    def close(t_end: float) -> None:
        nonlocal cur
        if cur:
            cur["end"] = t_end
            pas.append(cur)
        cur = None

    def next_half(h):
        return (h[0], "裏") if h[1] == "表" else (h[0] + 1, "表")

    for t, kind, val, ctx in events(text, times):
        if kind == "half_start":
            if val != half:
                close(t - 0.5)
                half = val
        elif kind == "half_end":
            if val == half:
                close(t - 0.5)
                half = next_half(half)
        elif kind == "third_out":
            in_half = sum(1 for p in pas if (p["inning"], p["half"]) == half) + (1 if cur else 0)
            if in_half >= 2 and t - last_third > 20:
                close(t + 4)
                half = next_half(half)
                last_third = t
        elif kind == "pitcher_change":
            # どちらの投手か: 言葉の前にチーム名があればそれ、なければ今の守りの側
            head = ctx[:20]
            team = TAIWAN if re.search(r"台湾|タイペイ|チャイニーズ", head) else (
                OPP if game["short"][:2] in head else defense_of(half[1]))
            name, _ = match_name(val, reads[team])
            seq = pitch_seq.get(team, [])
            if not name and pitcher_now.get(team) in seq:  # 名前が聞き取れなければ、継投の順で次の投手
                i = seq.index(pitcher_now[team])
                name = seq[i + 1] if i + 1 < len(seq) else ""
            if name:
                pitcher_now[team] = name
        elif kind == "batter":
            close(t - 1.0)
            side = half[1]
            team = team_of(side)
            exp = expect[side] % 9 + 1
            said = KATA.findall(ctx[ctx.find("番") + 1:] if "番" in ctx else ctx.replace("バッター", ""))
            said = max(said, key=len) if said else ""
            for pos in POSITIONS:
                said = said.replace(pos, "")
            slot_of = {v: k for k, v in order_now[team].items()}
            by_name, _ = match_name(said, reads[team], threshold=0.75)
            if val == 0:
                val = exp
                notes = ["実況は名前だけ（打順は次の番として扱った）"]
            elif val != exp and by_name and slot_of.get(by_name) == str(exp):
                notes = [f"聞き取りは{val}番だが、名前（{by_name}）で{exp}番とした"]
                val = exp
            else:
                notes = [] if val == exp else [f"打順の飛び（{exp}番のはず）"]
            name, score = match_name(said, reads[team], threshold=0.7)
            listed = order_now[team].get(str(val), "")
            listed_score = kana_score(said, reads[team].get(listed, []))
            if name and name != listed and score - listed_score >= 0.2:
                notes.append(f"実況の名前は{name}（打順表は{listed}）")
                order_now[team][str(val)] = name
            expect[side] = val
            cur = {"inning": half[0], "half": half[1], "order": val, "start": t - 1.0,
                   "bat_team": team, "batter": order_now[team].get(str(val), ""),
                   "pit_team": defense_of(side), "pitcher": pitcher_now.get(defense_of(side), ""),
                   "pitches": [], "results": [], "result_times": [], "notes": notes, "ctx": ctx}
        elif kind == "pitch" and cur:
            cur["pitches"].append((round(t, 1), val))
        elif kind == "result" and cur:
            cur["results"].append(val)
            cur["result_times"].append(t)
    close(duration)

    pas = [p for p in pas if p["end"] - p["start"] >= 3 or p["pitches"]]  # 言い直し（長さなし）を捨てる
    pas = fill_gaps(pas, cuts, order_now, team_of)

    for p in pas:  # 頭をカメラの切り替わりにそろえる
        before = [c for c in cuts if p["start"] - 8 <= c <= p["start"] + 1]
        p["start"] = before[-1] if before else p["start"]
    for a, b in zip(pas, pas[1:]):
        same = (a["inning"], a["half"]) == (b["inning"], b["half"])
        a["end"] = min(a["end"] + 0.5, b["start"]) if same else a["end"] + 0.5
    dtw = out / "words_dtw.json"
    if dtw.is_file():  # 1球ごとの時刻は DTW つきの文字起こしから取り直す（区切りはそのまま）
        d_text, d_times = load_chars(dtw)
        calls = [(t, v) for t, kind, v, _ in events(d_text, d_times) if kind == "pitch"]
        for p in pas:
            p["pitches"] = [(round(t, 1), v) for t, v in calls if p["start"] <= t < p["end"]]
    rows = []
    for i, p in enumerate(pas, 1):
        rows.append({
            "no": i, "inning": p["inning"], "half": p["half"], "order": p["order"],
            "bat_team": p["bat_team"], "batter": p["batter"], "pit_team": p["pit_team"], "pitcher": p["pitcher"],
            "start": f"{p['start']:.1f}", "end": f"{p['end']:.1f}", "n_pitch": len(p["pitches"]),
            "pitches": ";".join(f"{t}|{v}" for t, v in p["pitches"]),
            "results": "/".join(dict.fromkeys(p["results"])), "headline": "",
            "note": " ".join(p["notes"]), "ctx": p["ctx"], "source": "auto"})
    return rows


def fill_gaps(pas: list[dict], cuts: list[float], order_now: dict, team_of) -> list[dict]:
    """打順の飛びを埋める。抜けた打者の分だけ、前の打席を結果の言葉のところで割る。"""

    def split_at_result(p: dict, k: int) -> list[dict]:
        pieces, last = [], p["start"]
        for t in [t for t in p["result_times"] if p["start"] + 5 < t < p["end"] - 5]:
            if len(pieces) == k:
                break
            if t - last < 6:
                continue
            after = [c for c in cuts if t <= c <= t + 12]
            cut = after[0] if after else t + 3
            if cut >= p["end"] - 3:
                break
            pieces.append(cut)
            last = cut
        bounds = [p["start"]] + pieces + [p["end"]]
        out = []
        for j in range(len(bounds) - 1):
            a, b = bounds[j], bounds[j + 1]
            q = dict(p, start=a, end=b,
                     pitches=[x for x in p["pitches"] if a <= x[0] < b],
                     results=[r for r, t in zip(p["results"], p["result_times"]) if a <= t < b],
                     result_times=[t for t in p["result_times"] if a <= t < b])
            if j:
                q["order"] = (p["order"] + j - 1) % 9 + 1
                q["batter"] = order_now[team_of(p["half"])].get(str(q["order"]), "")
                q["notes"] = ["実況に打順なし。区切りは結果の言葉から推定"]
                q["ctx"] = ""
            out.append(q)
        return out

    fixed: list[dict] = []
    last_order = {"表": 0, "裏": 0}
    for idx, p in enumerate(pas):
        side = p["half"]
        exp = last_order[side] % 9 + 1
        miss = (p["order"] - exp) % 9
        nxt = pas[idx + 1] if idx + 1 < len(pas) else None
        if (miss == 1 and nxt and (nxt["inning"], nxt["half"]) == (p["inning"], side)
                and nxt["order"] == p["order"]):
            p["notes"] = [f"打順を{p['order']}番から{exp}番に直した（次の打席と同じ番号だったため）"]
            p["order"] = exp
            p["batter"] = order_now[team_of(side)].get(str(exp), p["batter"])
            miss = 0
        if miss == 8 and fixed and fixed[-1]["half"] == side:  # 同じ打順が2回（言い直し・聞き違い）
            p["notes"] = [f"打順を{p['order']}番から{exp}番に直した（前と同じ番号だったため）"] + p["notes"][1:]
            p["order"] = exp
            miss = 0
        if 1 <= miss <= 3:
            prev_i = next((i for i in range(len(fixed) - 1, -1, -1) if fixed[i]["half"] == side), None)
            if prev_i is not None:
                parts = split_at_result(fixed[prev_i], miss)
                if len(parts) > 1:
                    fixed[prev_i:prev_i + 1] = parts
                    fixed.sort(key=lambda x: x["start"])
                    p["notes"] = [n for n in p["notes"] if not n.startswith("打順の飛び")]
                    if len(parts) - 1 < miss:
                        p["notes"].append(f"打順の飛び（{miss - len(parts) + 1}打席分は割れなかった）")
        last_order[side] = p["order"]
        fixed.append(p)
    return fixed


def write_rows(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rows_of(game: dict) -> tuple[list[dict], str]:
    """確かめた 打席.csv があればそれ、なければ 打席_自動.csv。どちらもなければ空。"""
    out = DATA / game["id"]
    for name in (CHECKED, AUTO):
        if (out / name).is_file():
            return read_rows(out / name), name
    return [], ""


def chain_report(rows: list[dict]) -> str:
    """打順のつながりの点検。表と裏それぞれ、前の打席の次の番でない行を数える。"""
    bad, last = 0, {"表": 0, "裏": 0}
    for r in rows:
        side, order = r["half"], int(r["order"])
        if last[side] and order != last[side] % 9 + 1:
            bad += 1
        last[side] = order
    return f"打順のつながりが切れる所 {bad}"


def score() -> None:
    game = game_of("1020-seibu")
    rows = segment(game)
    truth = {(i, side, o) for side, by in TRUTH_SEIBU.items() for i, l in by.items() for o in l}
    got = [(int(r["inning"]), r["half"], int(r["order"])) for r in rows]
    hit = {g for g in got if g in truth}
    print(f"西部ガス戦: 正解{len(truth)}打席、出た行{len(rows)}、当たり{len(hit)}、"
          f"余計{len([g for g in got if g not in truth])}、取りこぼし{sorted(truth - set(got))}")


# ---------------------------------------------------------------- scorebook

SCORE = "スコア.csv"  # 印刷のスコアを読み取ったもの。inning,half,order,batter,pitcher,seq,result,result_ja
TYPE_JA = {"B": "ボール", "S": "ストライク", "F": "ファウル"}


def call_types(label: str) -> set[str]:
    """実況の1球の言葉から、ありうる球の種類（B・S・F・X=打球・H=死球）。分からなければ全部。"""
    if "デッドボール" in label:
        return {"H"}
    out = set()
    if "ボール" in label:
        out.add("B")
    if any(w in label for w in ("ストライク", "スト", "見逃し", "空振り", "カラブリ")):
        out.add("S")
    if any(w in label for w in ("ファウル", "ファール", "ファイル")):
        out.add("F")
    if any(w in label for w in ("打って", "打つ", "バント")):
        out |= {"X", "F"}
    return out or {"B", "S", "F", "X", "H"}


def final_type(result: str) -> str:
    if result in ("K", "Ks"):
        return "S"
    if result in ("B", "IB"):  # IB（申告敬遠）は最後のボールに当てる。4球目は投げていない
        return "B"
    if result in ("HBP", "HP"):
        return "H"
    return "X"


def align(a: list, b: list, same, gap_a: float = -1.0, gap_b: float = -1.0, miss: float = -3.0):
    """順番を保った対応づけ（ずれを許す）。戻り値は [(i, j)]。i か j が None なら相手なし。"""
    n, m = len(a), len(b)
    score = [[0.0] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        score[i][0], back[i][0] = score[i - 1][0] + gap_a, "a"
    for j in range(1, m + 1):
        score[0][j], back[0][j] = score[0][j - 1] + gap_b, "b"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = same(a[i - 1], b[j - 1])
            options = [(score[i - 1][j - 1] + (s if s is not None else miss), "ab"),
                       (score[i - 1][j] + gap_a, "a"), (score[i][j - 1] + gap_b, "b")]
            score[i][j], back[i][j] = max(options, key=lambda x: x[0])
    out, i, j = [], n, m
    while i or j:
        step = back[i][j]
        if step == "ab":
            out.append((i - 1, j - 1)); i -= 1; j -= 1
        elif step == "a":
            out.append((i - 1, None)); i -= 1
        else:
            out.append((None, j - 1)); j -= 1
    return out[::-1]


def apply_scorebook(game: dict) -> None:
    """スコア.csv の打席を、映像の区切り（打席_自動.csv）に当てて 打席.csv を書く。

    打席の対応は（回・表裏・打順）の並びで取る。映像の区切りがないスコアの打席は前後の区切りの間を当て、
    スコアにない区切りは同じ回の前の打席につなぐ。1球ごとは、実況の言葉（words_dtw.json から取った時刻つき）を
    スコアの1球の並び（B・S・F と最後の結果）に当てはめ、何球目かを決める。言葉のない球は時刻なしで残す。
    """
    out = DATA / game["id"]
    score = read_rows(out / SCORE)
    auto = read_rows(out / AUTO)
    key = lambda r: (int(r["inning"]), r["half"], int(r["order"]))
    # 回・表裏・打順がそろえば強く、打順だけ違う（実況の聞き違い）ときは弱く結ぶ
    same = lambda s, a: 2.0 if key(s) == key(a) else (0.5 if key(s)[:2] == key(a)[:2] else None)
    pairs = align(score, auto, same, gap_a=-1.0, gap_b=-1.0)
    rows, report = [], {"対応": 0, "区切りを当てた": 0, "つないだ": 0, "要確認": []}
    pending = []  # 映像の区切りがまだないスコアの打席
    for si, ai in pairs:
        if si is not None and ai is not None:
            for s in pending:  # 前の区切りの終わりからこの区切りの頭までを当てる
                prev_end = float(rows[-1]["end"]) if rows else 0.0
                start = float(auto[ai]["start"])
                if start - prev_end >= 8:
                    rows.append(scored_row(game, s, {"start": f"{prev_end:.1f}", "end": f"{start:.1f}", "pitches": ""},
                                           "映像の区切りがなかったので、前後の区切りの間を当てた"))
                    report["区切りを当てた"] += 1
                else:  # 間がない: あとで前の打席を、その最後の1球の実況のあとで割る
                    rows.append(dict(scored_row(game, s, {"start": "", "end": ""}, ""), _split=True))
            pending = []
            note = "" if key(score[si]) == key(auto[ai]) else f"映像の区切りは{auto[ai]['order']}番として出ていた（スコアに合わせた）"
            rows.append(scored_row(game, score[si], auto[ai], note))
            report["対応"] += 1
        elif si is not None:
            pending.append(score[si])
        else:  # スコアにない区切り: 同じ回の前の打席につなぐ
            a = auto[ai]
            if rows and (rows[-1]["inning"], rows[-1]["half"]) == (str(a["inning"]), a["half"]):
                rows[-1]["end"] = a["end"]
                rows[-1]["note"] = (rows[-1]["note"] + " 次の区切りをつないだ").strip()
                report["つないだ"] += 1
            else:
                report["要確認"].append(f"{a['inning']}回{a['half']} {a['order']}番の区切り（{a['start']}秒〜）: スコアにない")
    for s in pending:
        rows.append(dict(scored_row(game, s, {"start": "", "end": ""}, ""), _split=True))
    # 1球ごとは、つないだ・当てた後の範囲で、実況の言葉を文字起こし全体から拾い直す
    calls = []
    dtw = out / "words_dtw.json"
    cuts = load_cuts(out / "scenes.txt")
    if dtw.is_file():
        d_text, d_times = load_chars(dtw)
        d_events = events(d_text, d_times)
        calls = [(round(t, 1), v) for t, kind, v, _ in d_events if kind == "pitch"]
        report["頭を合わせ直した"] = refine_starts(rows, d_events, cuts)
    else:
        for a in auto:
            calls += [(float(x.split("|")[0]), x.split("|")[1]) for x in (a.get("pitches") or "").split(";") if "|" in x]
    within = lambda r: [c for c in calls if float(r["start"]) <= c[0] < float(r["end"])]
    for r in rows:
        if not r.get("_split"):
            r["pitches"] = place_pitches(r, within(r))
    for i, r in enumerate(rows):
        if not r.get("_split"):
            continue
        prev = next((rows[j] for j in range(i - 1, -1, -1) if not rows[j].get("_split")), None)
        last = None
        if prev and (prev["inning"], prev["half"]) == (r["inning"], r["half"]):
            last = next((p.split("|")[0] for p in prev["pitches"].split(";")
                         if p.split("|")[2] == str(prev["n_pitch"]) and p.split("|")[0]), None)
        if last and float(prev["end"]) - float(last) > 8:
            t = float(last)
            after = [c for c in cuts if t <= c <= t + 12]
            cut = after[0] if after else t + 4
            r["start"], r["end"] = f"{cut:.1f}", prev["end"]
            prev["end"] = f"{cut:.1f}"
            r["note"] = "映像の区切りがなかったので、前の打席の最後の1球の実況のあとで割った"
            prev["pitches"] = place_pitches(prev, within(prev))
            r["pitches"] = place_pitches(r, within(r))
            r.pop("_split")
            report["区切りを当てた"] += 1
        else:
            report["要確認"].append(f"{r['inning']}回{r['half']} {r['order']}番 {r['batter']}: 映像の区切りがない")
    rows = [r for r in rows if not r.get("_split")]
    if dtw.is_file():  # 回ごとにまとめて当てはめ、境目も置き直す
        moved = 0
        for key_h in dict.fromkeys((r["inning"], r["half"]) for r in rows):
            moved += place_half([r for r in rows if (r["inning"], r["half"]) == key_h], calls, d_events, cuts)
        report["境目を置き直した"] = moved
    for i, r in enumerate(rows, 1):
        r["no"] = i
    write_rows(out / CHECKED, rows)
    print(f"{game['id']}: スコアの打席{len(score)}、映像の区切り{len(auto)} → 対応{report['対応']}・"
          f"区切りを当てた{report['区切りを当てた']}・つないだ{report['つないだ']}・"
          f"頭を合わせ直した{report.get('頭を合わせ直した', 0)}・境目を置き直した{report.get('境目を置き直した', 0)}・"
          f"要確認{len(report['要確認'])} → {CHECKED}")
    for line in report["要確認"]:
        print("  要確認:", line)


def refine_starts(rows: list[dict], d_events: list[tuple], cuts: list[float], window: float = 20.0) -> int:
    """打席の頭を、時刻合わせつきの文字起こしの「N番」の時刻に合わせ直す。同じ回の前の打席の終わりもそろえる。

    古い文字起こしの時刻は数秒〜10秒ずれることがある（日本製鉄九州戦の2回表7番は、頭が6〜8秒早かった）。
    古い頭の前後 window 秒以内に、同じ打順の「N番」が時刻合わせつきの側にあれば、その1秒前（直前8秒以内に
    カメラの切り替わりがあればそこ）を新しい頭にする。見つからない打席はそのまま。
    """
    batters = [(t, v) for t, kind, v, _ in d_events if kind == "batter" and v]
    used, moved = set(), 0
    for i, r in enumerate(rows):
        if r.get("_split") or not r.get("start"):
            continue
        old = float(r["start"])
        near = [(abs(t - old), k, t) for k, (t, v) in enumerate(batters)
                if v == int(r["order"]) and abs(t - old) <= window and k not in used]
        if not near:
            continue
        _, k, t = min(near)
        used.add(k)
        before = [c for c in cuts if t - 8 <= c <= t + 1]
        new = before[-1] if before else t - 1.0
        prev = next((rows[j] for j in range(i - 1, -1, -1) if not rows[j].get("_split") and rows[j].get("end")), None)
        if prev and (prev["inning"], prev["half"]) == (r["inning"], r["half"]) and new <= float(prev["start"]) + 2:
            continue  # 前の打席を食いつぶすような動きはしない
        if abs(new - old) >= 0.5:
            moved += 1
        r["start"] = f"{new:.1f}"
        r["_anchored"] = True  # 実況の「N番」で決めた頭。place_half は動かさず、当てはめもまたがない
        if prev and (prev["inning"], prev["half"]) == (r["inning"], r["half"]):
            prev["end"] = r["start"]
        elif prev and float(prev["end"]) > new:
            prev["end"] = r["start"]
    return moved


def place_half(rows_h: list[dict], calls: list, d_events: list[tuple], cuts: list[float]) -> int:
    """「N番」で頭を決めた打席の前で区切り、かたまりごとに place_chunk を流す。"""
    moved, chunk = 0, []
    for r in rows_h:
        if r.get("_anchored") and chunk:
            moved += place_chunk(chunk, calls, d_events, cuts)
            chunk = []
        chunk.append(r)
    if chunk:
        moved += place_chunk(chunk, calls, d_events, cuts)
    return moved


def place_chunk(rows_h: list[dict], calls: list, d_events: list[tuple], cuts: list[float]) -> int:
    """1回の表（または裏）の打席をまとめて、実況の1球の言葉を当てはめ、打席の境目も置き直す。

    スコアの全打席の1球の並びをつなげ、その回の実況の言葉の並びと一度に対応づける。続く2打席の境目は、
    前の打席で最後に当たった実況と、次の打席で最初に当たった実況のあいだに置く。そのあいだに時刻合わせつきの
    「N番」があればその1秒前、なければカメラの切り替わり（次の打席の最初の実況の5秒前に近いもの）、
    それもなければ前の実況の4秒後。動かした境目の数を返す。
    """
    # かたまりの両端が「N番」で決めた境目なら、そこはまたがない
    lo = float(rows_h[0]["start"]) - (0 if rows_h[0].get("_anchored") else 5)
    hi = float(rows_h[-1]["end"])
    cs = [c for c in calls if lo <= c[0] < hi]
    items = []  # (打席の番号, 何球目, 種類)
    for ri, r in enumerate(rows_h):
        seq = list(r.get("seq") or "") + [final_type(r.get("result") or "")]
        items += [(ri, k, t) for k, t in enumerate(seq, 1)]
    if not cs or not items:
        return 0
    span = max(1.0, hi - lo)

    def fit(item, c):
        if item[2] not in call_types(c[1]):
            return -1.0
        return 2.0 - 0.5 * abs((items.index(item) + 0.5) / len(items) - (c[0] - lo) / span)

    pairs = align(items, cs, fit, gap_a=0.0, gap_b=-0.5, miss=-1.0)
    got = {}  # 打席の番号 → [(何球目, 時刻, 言葉)]
    for i, j in pairs:
        if i is not None and j is not None:
            ri, k, _ = items[i]
            got.setdefault(ri, []).append((k, cs[j][0], cs[j][1]))
    batters = {t: v for t, kind, v, _ in d_events if kind == "batter"}
    moved = 0
    for ri in range(len(rows_h) - 1):
        a, b = rows_h[ri], rows_h[ri + 1]
        if not got.get(ri) or not got.get(ri + 1):
            continue
        ta, tb = max(t for _, t, _ in got[ri]), min(t for _, t, _ in got[ri + 1])
        if tb - ta < 3:
            continue
        ann = [t for t, v in batters.items() if ta < t < tb and v in (0, int(b["order"]))]
        if ann:
            cut = ann[0] - 1.0
        else:
            inside = [c for c in cuts if ta + 2 <= c <= tb - 2]
            cut = min(inside, key=lambda c: abs(c - (tb - 5))) if inside else min(ta + 4, tb - 1)
        if not (float(a["start"]) + 4 <= cut <= float(b["end"]) - 4):
            continue  # 前後の打席が4秒より短くなる置き方はしない（実況の時刻が詰まっている所がある）
        if abs(cut - float(b["start"])) >= 0.5:
            moved += 1
        a["end"] = b["start"] = f"{cut:.1f}"
    for ri, r in enumerate(rows_h):
        lo_r, hi_r = float(r["start"]) - 1, float(r["end"])
        r["pitches"] = pitches_text(r, [h for h in got.get(ri, []) if lo_r <= h[1] < hi_r])  # 範囲の外は時刻なしに
    return moved


def pitches_text(r: dict, hits: list) -> str:
    """「時刻|球速 種類|何球目」を全球ぶん並べる（実況の当たらない球は時刻なし）。"""
    seq = list(r.get("seq") or "") + [final_type(r.get("result") or "")]
    labels = [TYPE_JA.get(t, "") for t in seq[:-1]] + [r.get("headline") or ""]
    at = {k: (t, c) for k, t, c in hits}
    out = []
    for k, label in enumerate(labels, 1):
        if k in at:
            t, c = at[k]
            speed = c.split(" ")[0] if c.split(" ")[0].isdigit() else ""
            out.append(f"{t}|{(speed + ' ' + label).strip()}|{k}")
        else:
            out.append(f"|{label}|{k}")
    return ";".join(out)


def scored_row(game: dict, s: dict, a: dict, note: str) -> dict:
    top, bot = side_teams(game)
    bat, pit = (top, bot) if s["half"] == "表" else (bot, top)
    return {"inning": s["inning"], "half": s["half"], "order": s["order"],
            "bat_team": bat, "batter": s["batter"], "pit_team": pit, "pitcher": s["pitcher"],
            "start": a["start"], "end": a["end"], "n_pitch": len(s["seq"]) + 1, "pitches": a.get("pitches", ""),
            "results": a.get("results", ""), "headline": s["result_ja"], "seq": s["seq"], "result": s["result"],
            "note": note, "ctx": a.get("ctx", ""), "source": "score"}


def place_pitches(r: dict, calls: list) -> str:
    """スコアの1球の並びに実況の言葉を当てはめ、「時刻|球速 種類|何球目」を全球ぶん並べる（時刻なしもある）。"""
    seq = list(r.get("seq") or "") + [final_type(r.get("result") or "")]
    labels = [TYPE_JA.get(t, "") for t in seq[:-1]] + [r.get("headline") or ""]
    start, end = float(r["start"]), float(r["end"])
    span, n = max(1.0, end - start), len(seq)
    items = list(enumerate(seq))

    def fit(item, c):
        i, t = item
        if t not in call_types(c[1]):
            return -1.0
        return 2.0 - 0.5 * abs((i + 0.5) / n - (c[0] - start) / span)  # 同じ種類なら、打席の中の位置が近いほど高い

    pairs = align(items, calls, fit, gap_a=0.0, gap_b=-0.5, miss=-1.0)
    at = {i: calls[j] for i, j in pairs if i is not None and j is not None}
    out = []
    for k, (t, label) in enumerate(zip(seq, labels), 1):
        if k - 1 in at:
            c = at[k - 1]
            speed = c[1].split(" ")[0] if c[1].split(" ")[0].isdigit() else ""
            out.append(f"{c[0]}|{(speed + ' ' + label).strip()}|{k}")
        else:
            out.append(f"|{label}|{k}")
    return ";".join(out)


# ---------------------------------------------------------------- export

LIMIT = 25 * 1024 * 1024  # Cloudflare Pages の1ファイルの上限


def clip_stem(row: dict) -> str:
    """動画の名前。頭と終わりの時刻から作るので、区切りが変わった打席だけ作り直しになる。"""
    return f"{round(float(row['start']) * 10):06d}-{round(float(row['end']) * 10):06d}"


def encode(video: Path, start: float, end: float, mp4: Path, jpg: Path) -> None:
    part = mp4.with_suffix(".part.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.2f}", "-to", f"{end:.2f}", "-i", str(video),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-profile:v", "high",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "64k", "-ac", "1",
                    "-movflags", "+faststart", str(part)], check=True)
    part.replace(mp4)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{min(3.0, (end - start) / 2):.1f}", "-i", str(mp4),
                    "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "5", str(jpg)], check=True)


def to_trash(path: Path) -> None:
    if Path("/usr/bin/trash").exists():
        subprocess.run(["/usr/bin/trash", str(path)], check=True)
    else:
        trash = Path.home() / ".Trash"
        trash.mkdir(exist_ok=True)
        shutil.move(str(path), str(trash / path.name))


def export(game: dict, workers: int = 3) -> None:
    from concurrent.futures import ThreadPoolExecutor

    rows, source = rows_of(game)
    if not rows:
        print(f"{game['id']}: 打席の一覧がまだないので飛ばします（segment を先に）")
        return
    out = DATA / "clips" / game["id"]
    out.mkdir(parents=True, exist_ok=True)
    video = video_path(game)
    index, jobs = {}, []
    for r in rows:
        start, end = float(r["start"]), float(r["end"])
        if end - start < 2:
            continue
        stem = clip_stem(r)
        mp4, jpg = out / f"{stem}.mp4", out / f"{stem}.jpg"
        index[str(r["no"])] = {"file": mp4.name, "jpg": jpg.name, "secs": round(end - start, 1)}
        if not (mp4.is_file() and jpg.is_file()):
            jobs.append((start, end, mp4, jpg))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(lambda j: encode(video, *j), jobs))
    total = 0
    for no, item in list(index.items()):
        size = (out / item["file"]).stat().st_size
        if size > LIMIT:
            print(f"注意: {game['id']} の{no}番の打席は {size / 1e6:.1f}MB で上限を超えるので載せません"
                  "（区切りが長すぎないか確かめてください）", file=sys.stderr)
            del index[no]
            continue
        item["bytes"] = size
        total += size
    keep = {"index.json"} | {i["file"] for i in index.values()} | {i["jpg"] for i in index.values()}
    stale = [p for p in out.iterdir() if p.is_file() and p.name not in keep]
    for p in stale:
        to_trash(p)
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{game['id']}: {len(index)}本（新しく{len(jobs)}本、古いもの{len(stale)}個をゴミ箱へ）、"
          f"合計{total / 1e6:.0f}MB（{source}から）")


# ---------------------------------------------------------------- review / serve


def send_file(handler, path: Path, ctype: str) -> None:
    """ファイルを返す。Range があれば部分だけ返す（iOS の Safari は動画をこれで取りに来る）。"""
    size = path.stat().st_size
    start, end = 0, size - 1
    rng = handler.headers.get("Range")
    m = re.match(r"bytes=(\d*)-(\d*)$", rng or "")
    if m and (m.group(1) or m.group(2)):
        if m.group(1):
            start = int(m.group(1))
            end = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
        else:
            start = max(0, size - int(m.group(2)))
        if start > end:
            handler.send_response(416)
            handler.send_header("Content-Range", f"bytes */{size}")
            handler.end_headers()
            return
        handler.send_response(206)
        handler.send_header("Content-Range", f"bytes {start}-{end}/{size}")
    else:
        handler.send_response(200)
    handler.send_header("Content-Type", ctype)
    handler.send_header("Accept-Ranges", "bytes")
    handler.send_header("Content-Length", str(end - start + 1))
    handler.send_header("Cache-Control", "no-cache")
    handler.end_headers()
    if handler.command == "HEAD":
        return
    with path.open("rb") as f:
        f.seek(start)
        left = end - start + 1
        while left > 0:
            chunk = f.read(min(1 << 20, left))
            if not chunk:
                break
            try:
                handler.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                return
            left -= len(chunk)


def content_type(path: Path) -> str:
    import mimetypes
    special = {".mp4": "video/mp4", ".js": "text/javascript; charset=utf-8", ".webmanifest": "application/manifest+json",
               ".html": "text/html; charset=utf-8", ".json": "application/json; charset=utf-8"}
    return special.get(path.suffix) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"


def names_for(game: dict) -> dict[str, list[str]]:
    out = {}
    for team in (TAIWAN, OPP):
        names = list(game["orders"][team])
        for subs in game.get("subs", {}).get(team, {}).values():
            names += subs
        names += game.get("pitchers", {}).get(team, [])
        if team == TAIWAN:
            names += [p["name"] for p in players()]
        else:
            names += list(game.get("readings", {}))
        out[team] = list(dict.fromkeys(names))
    return out


def run_server(port: int, handler_cls) -> None:
    from http.server import ThreadingHTTPServer
    server = ThreadingHTTPServer(("127.0.0.1", port), handler_cls)
    print(f"http://127.0.0.1:{port}/ で開いています（Ctrl-C で止める）", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


def review(port: int) -> None:
    from http.server import BaseHTTPRequestHandler
    from urllib.parse import parse_qs, urlparse

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, body: bytes, ctype: str, code: int = 200) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def json_reply(self, data, code: int = 200) -> None:
            self.reply(json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", code)

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            url = urlparse(self.path)
            q = parse_qs(url.query)
            if url.path == "/":
                return self.reply(REVIEW_HTML.encode("utf-8"), "text/html; charset=utf-8")
            if url.path == "/api/games":
                out = []
                for g in games():
                    rows, source = rows_of(g)
                    out.append({"id": g["id"], "label": f"{g['date'][5:]} {g['opponent']}", "source": source,
                                "rows": len(rows), "notes": sum(1 for r in rows if r.get("note"))})
                return self.json_reply(out)
            if url.path == "/api/rows":
                g = game_of(q["game"][0])
                rows, source = rows_of(g)
                return self.json_reply({"rows": rows, "source": source, "names": names_for(g),
                                        "top": side_teams(g)[0]})
            if url.path.startswith("/video/"):
                g = game_of(url.path.split("/")[2])
                return send_file(self, video_path(g), "video/mp4")
            self.reply(b"not found", "text/plain", 404)

        def do_POST(self):
            url = urlparse(self.path)
            q = parse_qs(url.query)
            if url.path != "/api/save":
                return self.reply(b"not found", "text/plain", 404)
            g = game_of(q["game"][0])
            rows = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)).decode("utf-8"))
            rows.sort(key=lambda r: float(r["start"]))
            for i, r in enumerate(rows, 1):
                r["no"] = i
            path = DATA / g["id"] / CHECKED
            tmp = path.with_suffix(".tmp")
            write_rows(tmp, rows)
            tmp.replace(path)
            self.json_reply({"saved": len(rows), "file": str(path)})

    run_server(port, Handler)


def serve(folder: Path, port: int) -> None:
    from http.server import BaseHTTPRequestHandler
    from urllib.parse import unquote, urlparse
    base = folder.resolve()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            rel = unquote(urlparse(self.path).path).lstrip("/")
            if not rel or rel.startswith("_/"):
                # 入口と /_/<パス> は合言葉のフォルダへ送る（手元の確かめで、URLに合言葉を打たずに済むように）
                sites = [p for p in base.iterdir() if p.is_dir() and (p / "pages.json").is_file()]
                if len(sites) == 1:
                    self.send_response(302)
                    self.send_header("Location", f"/{sites[0].name}/{rel[2:]}")
                    self.end_headers()
                    return
            path = (base / rel).resolve()
            if base not in path.parents and path != base:
                return self.send_error(404)
            if path.is_dir():
                if not self.path.split("?")[0].endswith("/"):
                    self.send_response(301)
                    self.send_header("Location", self.path.split("?")[0] + "/")
                    self.end_headers()
                    return
                path = path / "index.html"
            if not path.is_file():
                return self.send_error(404)
            send_file(self, path, content_type(path))

    run_server(port, Handler)


REVIEW_HTML = r"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>打席の区切りの確認</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--line:#d9dde3;--text:#1b1f27;--dim:#5f6878;--warn:#fff3d6;--sel:#dcebff;--ok:#e6f6ec}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--card:#171a21;--line:#2b303a;--text:#e8eaed;--dim:#9aa3b2;--warn:#3a2f12;--sel:#18324f;--ok:#15301f}}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 -apple-system,"Hiragino Sans",sans-serif}
.top{position:sticky;top:0;z-index:2;background:var(--bg);padding:8px 12px;border-bottom:1px solid var(--line)}
.bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0}
button,select,input{font:inherit;color:inherit}
button{min-height:34px;padding:0 10px;border:1px solid var(--line);border-radius:6px;background:var(--card);cursor:pointer}
button.main{background:#1f6fd1;color:#fff;border-color:#1f6fd1}
video{width:min(100%,800px);aspect-ratio:16/9;background:#000;display:block}
#t{font-variant-numeric:tabular-nums;min-width:7em}
table{border-collapse:collapse;width:100%;background:var(--card)}
th,td{border-bottom:1px solid var(--line);padding:3px 5px;text-align:left;vertical-align:top;white-space:nowrap}
td.wrap{white-space:normal;min-width:12em;color:var(--dim);font-size:12px}
tr.note td{background:var(--warn)}tr.ok td{background:var(--ok)}tr.sel td{background:var(--sel)!important}
input.n{width:3.5em}input.t{width:5.5em}input.p{width:7em}input.h{width:11em}
#msg{color:var(--dim)}
.help{color:var(--dim);font-size:12px}
</style></head><body>
<div class="top">
<div class="bar"><select id="game"></select>
<label><input type="checkbox" id="onlynote"> 注意つきで未確認の行だけ</label>
<button class="main" id="save">保存（打席.csv）</button><span id="msg"></span></div>
<video id="v" controls preload="metadata"></video>
<div class="bar"><span id="t">0:00.0</span>
<button data-a="head">頭へ</button><button data-a="play">この打席を再生</button>
<button data-a="b5">◀5秒</button><button data-a="b1">◀1秒</button><button data-a="f1">1秒▶</button><button data-a="f5">5秒▶</button>
<button data-a="setS">今の位置を頭に</button><button data-a="setE">今の位置を終わりに</button>
<button data-a="split">今の位置で割る</button><button data-a="merge">次の行とつなぐ</button><button data-a="del">この行を消す</button>
<button data-a="ok">確認した（次へ）</button></div>
<p class="help">行を押すとその打席の頭から。空白キーで再生と停止、←→で1秒、↑↓で前後の行。打者・投手・見出しは打ち直せます（候補が出ます）。保存するまでファイルは変わりません。</p>
</div>
<datalist id="dl-a"></datalist><datalist id="dl-b"></datalist>
<table><thead><tr><th>#</th><th>回</th><th>打順</th><th>打者</th><th>投手</th><th>頭</th><th>終わり</th><th>秒</th><th>球</th><th>見出し</th><th>実況の結果</th><th>注意</th></tr></thead><tbody id="rows"></tbody></table>
<script>
var S = {game: null, rows: [], sel: -1, top: "", dirty: false, stopAt: null};
var v = document.getElementById("v"), tb = document.getElementById("rows");
function fmt(s) { s = +s || 0; var m = Math.floor(s / 60); return m + ":" + (s - m * 60).toFixed(1).padStart(4, "0"); }
function msg(t) { document.getElementById("msg").textContent = t; }
function dirty() { S.dirty = true; msg("保存していない変更があります"); }
function teamOf(r) { return r.half === "表" ? S.top : (S.top === "台湾" ? "相手" : "台湾"); }
function show() {
  var only = document.getElementById("onlynote").checked;
  tb.innerHTML = "";
  S.rows.forEach(function (r, i) {
    if (only && (!r.note || r.source === "checked")) return;
    var tr = document.createElement("tr");
    tr.className = (r.source === "checked" ? "ok" : r.note ? "note" : "") + (i === S.sel ? " sel" : "");
    var bt = teamOf(r) === "台湾" ? "dl-a" : "dl-b", pt = bt === "dl-a" ? "dl-b" : "dl-a";
    tr.innerHTML = "<td>" + (i + 1) + "</td><td>" + r.inning + r.half + "</td>" +
      '<td><input class="n" data-k="order" value="' + r.order + '"></td>' +
      '<td><input class="p" list="' + bt + '" data-k="batter"></td><td><input class="p" list="' + pt + '" data-k="pitcher"></td>' +
      "<td>" + fmt(r.start) + "</td><td>" + fmt(r.end) + "</td><td>" + Math.round(r.end - r.start) + "</td><td>" + (r.n_pitch || 0) + "</td>" +
      '<td><input class="h" data-k="headline" placeholder="例 二ゴロ"></td><td class="wrap"></td><td class="wrap"></td>';
    tr.querySelector('[data-k=batter]').value = r.batter || "";
    tr.querySelector('[data-k=pitcher]').value = r.pitcher || "";
    tr.querySelector('[data-k=headline]').value = r.headline || "";
    tr.children[10].textContent = r.results || "";
    tr.children[11].textContent = (r.note || "") + (r.ctx ? "　「" + r.ctx + "」" : "");
    tr.querySelectorAll("input").forEach(function (inp) {
      inp.addEventListener("change", function () { r[inp.getAttribute("data-k")] = inp.value; dirty(); });
      inp.addEventListener("focus", function () { pick(i, false); });
    });
    tr.addEventListener("click", function (e) { if (e.target.tagName !== "INPUT") pick(i, true); });
    tb.appendChild(tr);
  });
}
function pick(i, seek) {
  if (i < 0 || i >= S.rows.length) return;
  S.sel = i;
  if (seek) { v.currentTime = +S.rows[i].start; }
  each(tb.children, function (tr) { tr.classList.toggle("sel", +tr.children[0].textContent - 1 === i); });
}
function each(l, f) { Array.prototype.forEach.call(l, f); }
function cur() { return S.rows[S.sel]; }
function act(a) {
  var r = cur(), t = Math.round(v.currentTime * 10) / 10;
  if (!r) return;
  if (a === "head") v.currentTime = +r.start;
  if (a === "play") { v.currentTime = +r.start; S.stopAt = +r.end; v.play(); }
  if (a === "b5") v.currentTime -= 5; if (a === "b1") v.currentTime -= 1;
  if (a === "f1") v.currentTime += 1; if (a === "f5") v.currentTime += 5;
  if (a === "setS") { r.start = t; dirty(); show(); }
  if (a === "setE") { r.end = t; dirty(); show(); }
  if (a === "split" && t > +r.start + 2 && t < +r.end - 2) {
    var n = Object.assign({}, r, {start: t, order: (+r.order % 9) + 1, batter: "", pitches: "", n_pitch: 0,
      results: "", headline: "", note: "確認用の画面で割った", ctx: "", source: "checked"});
    n.pitches = (r.pitches || "").split(";").filter(function (p) { return p && +p.split("|")[0] >= t; }).join(";");
    r.pitches = (r.pitches || "").split(";").filter(function (p) { return p && +p.split("|")[0] < t; }).join(";");
    n.n_pitch = n.pitches ? n.pitches.split(";").length : 0; r.n_pitch = r.pitches ? r.pitches.split(";").length : 0;
    r.end = t; S.rows.splice(S.sel + 1, 0, n); dirty(); show();
  }
  if (a === "merge" && S.sel + 1 < S.rows.length) {
    var b = S.rows[S.sel + 1];
    r.end = b.end; r.pitches = [r.pitches, b.pitches].filter(Boolean).join(";");
    r.n_pitch = (+r.n_pitch || 0) + (+b.n_pitch || 0); r.results = [r.results, b.results].filter(Boolean).join("/");
    S.rows.splice(S.sel + 1, 1); dirty(); show();
  }
  if (a === "del" && confirm("この行を消しますか（保存するまでファイルは変わりません）")) { S.rows.splice(S.sel, 1); dirty(); show(); }
  if (a === "ok") { r.source = "checked"; dirty(); show(); pick(S.sel + 1, true); }
}
each(document.querySelectorAll("[data-a]"), function (b) { b.addEventListener("click", function () { act(b.getAttribute("data-a")); }); });
v.addEventListener("timeupdate", function () {
  document.getElementById("t").textContent = fmt(v.currentTime);
  if (S.stopAt !== null && v.currentTime >= S.stopAt) { v.pause(); S.stopAt = null; }
});
document.addEventListener("keydown", function (e) {
  if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
  if (e.key === " ") { e.preventDefault(); v.paused ? v.play() : v.pause(); }
  if (e.key === "ArrowLeft") { e.preventDefault(); v.currentTime -= 1; }
  if (e.key === "ArrowRight") { e.preventDefault(); v.currentTime += 1; }
  if (e.key === "ArrowUp") { e.preventDefault(); pick(S.sel - 1, true); }
  if (e.key === "ArrowDown") { e.preventDefault(); pick(S.sel + 1, true); }
});
document.getElementById("onlynote").addEventListener("change", show);
document.getElementById("save").addEventListener("click", function () {
  fetch("/api/save?game=" + encodeURIComponent(S.game), {method: "POST", body: JSON.stringify(S.rows)})
    .then(function (r) { return r.json(); }).then(function (j) { S.dirty = false; msg(j.saved + "行を保存しました"); load(S.game); });
});
window.addEventListener("beforeunload", function (e) { if (S.dirty) { e.preventDefault(); e.returnValue = ""; } });
function load(id) {
  S.game = id; S.sel = -1;
  fetch("/api/rows?game=" + encodeURIComponent(id)).then(function (r) { return r.json(); }).then(function (j) {
    S.rows = j.rows; S.top = j.top;
    ["dl-a", "dl-b"].forEach(function (d, k) {
      document.getElementById(d).innerHTML = (j.names[k ? "相手" : "台湾"] || []).map(function (n) { return "<option value=\"" + n + "\">"; }).join("");
    });
    if (v.getAttribute("src") !== "/video/" + id) v.src = "/video/" + id;
    msg((j.source || "まだ区切りがありません") + "　" + j.rows.length + "行");
    show();
  });
}
document.getElementById("game").addEventListener("change", function (e) {
  if (S.dirty && !confirm("保存していない変更があります。捨てて切り替えますか")) { e.target.value = S.game; return; }
  S.dirty = false; load(e.target.value);
});
fetch("/api/games").then(function (r) { return r.json(); }).then(function (gs) {
  var sel = document.getElementById("game");
  sel.innerHTML = gs.map(function (g) { return '<option value="' + g.id + '">' + g.label + "（" + g.rows + "行・注意" + g.notes + "）</option>"; }).join("");
  if (gs.length) load(gs[0].id);
});
</script></body></html>
"""


# ---------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep", help="文字起こしとカメラの切り替わり")
    p.add_argument("--game")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dtw", action="store_true", help="1球ごとの時刻用の文字起こし（words_dtw.json）だけ作る")
    p = sub.add_parser("segment", help="打席の区切り")
    p.add_argument("--game")
    sub.add_parser("score", help="西部ガス戦の正解と照らす")
    p = sub.add_parser("scorebook", help="スコア.csv を映像の区切りに当てて 打席.csv を書く")
    p.add_argument("--game", required=True)
    p = sub.add_parser("export", help="打席ごとの動画とサムネイル")
    p.add_argument("--game")
    p.add_argument("--workers", type=int, default=3)
    p = sub.add_parser("review", help="確認用の画面")
    p.add_argument("--port", type=int, default=8783)
    p = sub.add_parser("serve", help="組み立てたサイトを部分読み込みに応じて配る")
    p.add_argument("folder", type=Path)
    p.add_argument("--port", type=int, default=8783)
    args = parser.parse_args()

    if args.cmd == "prep":
        for g in pick(args.game):
            (prep_dtw if args.dtw else prep)(g, args.force)
    elif args.cmd == "segment":
        for g in pick(args.game):
            if not (DATA / g["id"] / "words.json").is_file():
                print(f"{g['id']}: 文字起こしがまだないので飛ばします（prep を先に）")
                continue
            rows = segment(g)
            write_rows(DATA / g["id"] / AUTO, rows)
            notes = sum(1 for r in rows if r["note"])
            print(f"{g['id']}: {len(rows)}打席、注意つき{notes}、{chain_report(rows)} → {AUTO}")
    elif args.cmd == "score":
        score()
    elif args.cmd == "scorebook":
        apply_scorebook(game_of(args.game))
    elif args.cmd == "export":
        for g in pick(args.game):
            export(g, args.workers)
    elif args.cmd == "review":
        review(args.port)
    elif args.cmd == "serve":
        serve(args.folder.expanduser(), args.port)


if __name__ == "__main__":
    main()
