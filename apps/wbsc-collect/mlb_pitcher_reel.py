#!/usr/bin/env python3
"""MLBの1球映像（Baseball Savant）から、投手の左右別まとめを1本作る道具。

kbo_pitcher_reel.py の左右別まとめと同じ形にする（対左・対右を5打席ずつ、1打席を通しで、新しい試合から、章つき、音なし）。
1球の並びと結果はMLB公式のデータなので、韓国の映像のように画面を読んで場面を探す必要はない。
1球映像は投球の約3.3秒前から始まるので、投げた後の字幕は決まった秒から出す。
元の映像と一覧は video_get.py と video_manifest.py（~/野球/U23ワールドカップ2026/10_情報収集/_MLB集計/）で作る。

    python3 mlb_pitcher_reel.py list    # 全打席の結果の字幕と、選ばれる打席を出す（動画は作らない）
    python3 mlb_pitcher_reel.py render  # 動画にする
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw

from kbo_clips import ROOT
from kbo_pitcher_reel import AT_BATS_PER_SIDE, RESULT_MIX, STRIP, VH, VW, card, draw_text, encode_flags, render_card, text_width

PLAYER = "Andry Lara"
PLAYER_ID = 691251
KANA = "アンドリー・ララ"
WHO = "ベネズエラ代表・右投げ　2025年のMLB（ナショナルズ）"
OUT = ROOT / "04_対戦国" / "ベネズエラ" / "MLB映像" / PLAYER
CLIPS = OUT / "MLB2025_Savant"
MANIFEST = ROOT / "10_情報収集" / "_MLB集計" / "manifest.json"
GAMES = ROOT / "10_情報収集" / "_MLB集計" / "Lara_試合.json"
API = "https://statsapi.mlb.com/api/v1"

# 1球の切り方（秒）。投球は映像の約3.3秒後で、中継の球速の表示はその1秒ほど後に出る
REVEAL = 4.0
LONGEST_PITCH = 9.0
LONGEST_IN_PLAY = 16.0

KINDS = {"Four-Seam Fastball": "直球", "Sinker": "シンカー", "Slider": "スライダー", "Splitter": "スプリット",
         "Changeup": "チェンジアップ", "Cutter": "カット", "Curveball": "カーブ"}
TEAMS = {"Athletics": "アスレチックス", "Milwaukee Brewers": "ブルワーズ", "Houston Astros": "アストロズ", "Cincinnati Reds": "レッズ",
         "San Diego Padres": "パドレス", "Detroit Tigers": "タイガース"}
PLACES = {"left center": "左中間", "right center": "右中間", "left": "レフト", "center": "センター", "right": "ライト",
          "shortstop": "ショート", "second": "セカンド", "third": "サード", "first": "ファースト", "pitcher": "ピッチャー", "catcher": "キャッチャー"}
FIELDER = re.compile(r"\b(left center|right center|left|center|right) field(?:er)?\b|\b(first|second|third) baseman\b|\b(shortstop|pitcher|catcher)\b")
INFIELD = {"ショート", "セカンド", "サード", "ファースト", "ピッチャー", "キャッチャー"}


def result_ja(desc: str) -> str:
    """MLBの結果の文を、野球の言い方の日本語にする。読めない形は空にする（間違った字幕を出さない）。"""
    if "strikes out swinging" in desc:
        return "空振り三振"
    if "called out on strikes" in desc:
        return "見逃し三振"
    if "strikes out" in desc:
        return "三振"
    if " walks" in desc:
        return "四球"
    if "hit by pitch" in desc:
        return "死球"
    if "sacrifice bunt" in desc or "sac bunts" in desc:
        return "送りバント"
    first = desc.split(". ")[0]
    found = FIELDER.search(first)
    where = PLACES[next(g for g in found.groups() if g)] if found else ""
    if not where:
        return ""
    if " homers" in first:
        return f"{where}へのホームラン"
    if " triples" in first:
        return f"{where}へのスリーベース"
    if " doubles" in first or "ground-rule double" in first:
        return f"{where}へのツーベース"
    if " singles" in first:
        return f"{where}への内野安打" if where in INFIELD else f"{where}前ヒット"
    if "sacrifice fly" in first or "sac fly" in first:
        return f"{where}犠牲フライ"
    if "double play" in first:
        return f"{where}ゴロ併殺"
    if "grounds" in first or "force out" in first:
        return f"{where}ゴロ"
    if "flies out" in first or "pops out" in first:
        return f"{where}フライ"
    if "lines out" in first:
        return f"{where}ライナー"
    return ""


def result_class(event: str) -> str:
    if event == "Strikeout":
        return "三振"
    if event in ("Walk", "Intent Walk", "Hit By Pitch"):
        return "四死球"
    if event in ("Single", "Double", "Triple", "Home Run"):
        return "安打"
    return "凡打"


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
        return json.load(r)


def load_games(pks: list[int]) -> dict:
    """相手のチーム、表裏、打席の結果の文をMLB公式から取って控える。"""
    if GAMES.exists():
        return json.loads(GAMES.read_text(encoding="utf-8"))
    games = {}
    for pk in pks:
        game = fetch_json(f"{API}/schedule?gamePk={pk}")["dates"][0]["games"][0]
        plays = {}
        for p in fetch_json(f"{API}/game/{pk}/playByPlay")["allPlays"]:
            if p["matchup"]["pitcher"]["id"] == PLAYER_ID:
                plays[str(p["atBatIndex"])] = {"half": p["about"]["halfInning"], "desc": p["result"].get("description") or "",
                                               "pitches": sum(1 for e in p["playEvents"] if e.get("isPitch"))}
        games[str(pk)] = {"home": game["teams"]["home"]["team"]["name"], "away": game["teams"]["away"]["team"]["name"], "plays": plays}
    GAMES.write_text(json.dumps(games, ensure_ascii=False, indent=1), encoding="utf-8")
    return games


def load_pitches() -> list[dict]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pitches = next(m for m in manifest if m["name"] == PLAYER)["savant"]
    games = load_games(sorted({x["gamePk"] for x in pitches}))
    for x in pitches:
        game = games[str(x["gamePk"])]
        play = game["plays"][str(x["ab"])]
        rival = game["away"] if game["home"] == "Washington Nationals" else game["home"]
        month, day = int(x["date"][5:7]), int(x["date"][8:])
        x["試合"] = f"{x['date'][:4]}/{month}/{day} {TEAMS[rival]}戦 {x['inning']}回{'表' if play['half'] == 'top' else '裏'}"
        x["左右"] = {"L": "左打者", "R": "右打者"}[x["side"]]
        x["結果"] = result_ja(play["desc"])
        x["文"] = play["desc"]
        x["打席の球数"] = play["pitches"]
        x["最後"] = x["n"] == max(y["n"] for y in pitches if y["gamePk"] == x["gamePk"] and y["ab"] == x["ab"])
        found = list(CLIPS.glob(f"{x['date']}_{x['inning']}回_{x['ab']:03d}-{x['n']}_*.mp4"))
        assert len(found) == 1, (x["date"], x["ab"], x["n"], found)
        x["動画"] = found[0]
    return pitches


def at_bat_groups(pitches: list[dict]) -> list[list[dict]]:
    """球を打席ごとにまとめ、新しい試合から並べる。"""
    groups = defaultdict(list)
    for x in sorted(pitches, key=lambda x: (x["date"], -x["ab"], -x["n"]), reverse=True):
        groups[(x["date"], x["ab"])].append(x)
    return list(groups.values())


def choose_at_bats(pitches: list[dict], count: int) -> list[list[dict]]:
    """全球そろった3球以上の打席から、新しい順に、結果の内訳の目安どおりに選ぶ。1試合からは2打席まで（kbo_pitcher_reel.py と同じ決まり）。"""
    groups = [g for g in at_bat_groups(pitches) if len(g) == g[0]["打席の球数"] and g[0]["結果"]]
    long_ones = [g for g in groups if len(g) >= 3]
    chosen: list[list[dict]] = []
    room = dict(RESULT_MIX)
    games: Counter = Counter()
    for g in long_ones:
        kind = result_class(g[0]["event"])
        if room.get(kind, 0) > 0 and games[g[0]["date"]] < 2:
            chosen.append(g)
            room[kind] -= 1
            games[g[0]["date"]] += 1
    for g in long_ones + groups:  # 内訳が埋まらないときは、新しい打席で足す
        if len(chosen) >= count:
            break
        if g not in chosen:
            chosen.append(g)
    order = at_bat_groups(pitches)
    return sorted(chosen[:count], key=order.index)


def caption(x: dict, path: Path, after_pitch: bool) -> None:
    """字幕の帯。after_pitch のときだけ、投げた後に分かること（球速・球種・打席の結果）も書く。"""
    img = Image.new("RGB", (VW, STRIP), "#111418")
    draw = ImageDraw.Draw(img)
    end = draw_text(draw, (20, 16), f"{x['左右']}　{x['試合']}　", 26, "#FFFFFF")
    end = draw_text(draw, (end, 19), x["batter"], 22, "#AEB6C2")
    if after_pitch:
        pieces = [f"{round(x['mph'] * 1.60934)}km/h", KINDS.get(x["type"], x["type"] or "")]
        if x["最後"] and x["結果"]:
            pieces.append(f"→ {x['結果']}")
        right = "　".join(p for p in pieces if p)
        size = 26
        while size > 16 and end + 24 + text_width(right, size) > VW - 20:  # 左の字幕とぶつかるときは小さくする
            size -= 2
        draw_text(draw, (VW - 20 - text_width(right, size), 16 + (26 - size) // 2), right, size, "#FFD76A")
    img.save(path)


def seconds_of(path: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True).stdout.strip() or 0)


def render_pitch(x: dict, before: Path, after: Path, out: Path) -> None:
    """放送の画面の上に字幕の帯を足す。投げた後の字幕は決まった秒から重ねる。打球の球は行方まで長めに残す。"""
    longest = LONGEST_IN_PLAY if x["call"].startswith("In play") else LONGEST_PITCH
    graph = (f"[0:v]fps=60000/1001,scale={VW}:{VH},setsar=1,pad={VW}:{VH + STRIP}:0:{STRIP}:black[b];"
             "[b][1:v]overlay=0:0:shortest=1[c];"
             f"[c][2:v]overlay=0:0:shortest=1:enable='gte(t,{REVEAL:.2f})'[v]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-t", f"{min(seconds_of(x['動画']), longest):.2f}", "-i", str(x["動画"]),
                    "-loop", "1", "-i", str(before), "-loop", "1", "-i", str(after),
                    "-filter_complex", graph, "-map", "[v]", *encode_flags(), "-f", "mpegts", str(out)], check=True)


def chosen_sections(pitches: list[dict]) -> list[tuple[str, list[list[dict]]]]:
    return [(name, choose_at_bats([x for x in pitches if x["side"] == side], AT_BATS_PER_SIDE))
            for name, side in (("対 左打者", "L"), ("対 右打者", "R"))]


def cmd_list() -> None:
    pitches = load_pitches()
    for g in at_bat_groups(pitches):
        print(g[0]["date"], g[0]["side"], result_class(g[0]["event"]), repr(g[0]["結果"]), "|", g[0]["文"][:90])
    for name, groups in chosen_sections(pitches):
        print(name, Counter(KINDS.get(x["type"], x["type"]) for g in groups for x in g))
        for g in groups:
            print(" ", g[0]["試合"], g[0]["batter"], f"{len(g)}球", g[0]["結果"], [KINDS.get(x["type"], x["type"]) for x in g])


def cmd_render() -> None:
    pitches = load_pitches()
    sections = chosen_sections(pitches)
    with tempfile.TemporaryDirectory(prefix="mlbreel") as folder:
        work = Path(folder)
        card([(f"{PLAYER}　{KANA}", 64, "#FFFFFF"), (WHO, 34, "#AEB6C2"),
              (f"左打者・右打者 各{AT_BATS_PER_SIDE}打席", 34, "#FFD76A"),
              ("新しい試合から順に並べています。球速と球種はMLB公式のデータです", 26, "#AEB6C2"),
              ("中継の画面の球種の表示とは違うことがあります", 26, "#AEB6C2")], work / "title.png")
        render_card(work / "title.png", 3.0, work / "title.ts")
        order = [work / "title.ts"]
        starts = {work / "title.ts": "はじめに"}
        jobs = []
        for i, (name, groups) in enumerate(sections):
            title = f"{name}（{len(groups)}打席）"
            card([(f"{PLAYER}　{title}", 56, "#FFD76A")], work / f"section{i}.png")
            render_card(work / f"section{i}.png", 2.0, work / f"section{i}.ts")
            order.append(work / f"section{i}.ts")
            starts[work / f"section{i}.ts"] = title
            for k, g in enumerate(groups):
                card([(f"{g[0]['左右']}　{g[0]['batter']}", 46, "#FFFFFF"), (f"{g[0]['試合']}　{len(g)}球", 30, "#AEB6C2")], work / f"{i}_{k}.png")
                render_card(work / f"{i}_{k}.png", 1.5, work / f"{i}_{k}.ts")
                order.append(work / f"{i}_{k}.ts")
                for x in sorted(g, key=lambda x: x["n"]):
                    stem = f"{i}_{k}_{x['n']:02d}"
                    caption(x, work / f"{stem}_a.png", False)
                    caption(x, work / f"{stem}_b.png", True)
                    jobs.append((x, work / f"{stem}_a.png", work / f"{stem}_b.png", work / f"{stem}.ts"))
                    order.append(work / f"{stem}.ts")
        with ThreadPoolExecutor(4) as ex:
            list(ex.map(lambda j: render_pitch(*j), jobs))

        meta = [";FFMETADATA1"]
        position = 0.0
        marks = []
        for ts in order:
            if ts in starts:
                marks.append((position, starts[ts]))
            position += seconds_of(ts)
        for k, (begin, name) in enumerate(marks):
            finish = marks[k + 1][0] if k + 1 < len(marks) else position
            meta += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(begin * 1000)}", f"END={int(finish * 1000)}", f"title={name}"]
        (work / "meta.txt").write_text("\n".join(meta) + "\n", encoding="utf-8")
        (work / "list.txt").write_text("".join(f"file '{ts}'\n" for ts in order), encoding="utf-8")
        final = OUT / f"{PLAYER}_{KANA.replace('・', '')}_左右別まとめ.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "list.txt"),
                        "-i", str(work / "meta.txt"), "-map", "0:v", "-map_metadata", "1", "-c", "copy",
                        "-movflags", "+faststart", str(final)], check=True)
    print(f"{final.name} {position / 60:.1f}分 {final.stat().st_size / 1e6:.0f}MB {len(jobs)}球")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("list", "render"))
    {"list": cmd_list, "render": cmd_render}[parser.parse_args().command]()


if __name__ == "__main__":
    main()
