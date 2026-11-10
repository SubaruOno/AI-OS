#!/usr/bin/env python3
"""BASS（U-23 の入力画面）からダウンロードした全試合の JSON から、試合ごとの書き出しを作る。

    python3 -I bass_json.py list <BASSのJSON>                         # 入っている試合の一覧（試合番号・日付・対戦・球数）
    python3 -I bass_json.py export <BASSのJSON> <試合番号> <出力の頭>   # <出力の頭>.bass.txt / .bass_xy.txt / .bass_pa.csv を書く

<出力の頭> は 収録/<月日>_<相手>戦 のように、gt_clips.py が読む場所と名前にする。作るものは、それまでページの JS で
少しずつ読み出していたものと同じ形。
- .bass.txt     1球を「回・表裏（t/b）・投げる前のボール・ストライク・球種の記号・打席（1左2右）・9分割のコース」の7文字にして空白でつないだもの
                 （gt_clips.py types が読む）。球種もけん制先もない行は記号 -
- .bass_xy.txt  同じ7文字のあとに、コースの横・縦・球速を36進2桁ずつ足した13文字（gt_clips.py xy が読む）
- .bass_pa.csv  打席の最後の球の、打席の結果と打球（位置・角度・性質）。打線の一枚の打球の図に使う

JSON の作り方（2026-11-10）：Chrome でログイン済みの入力画面を開き、ページの JS で、チーム名が「_u23_26」で終わるチームの試合と、
その1球の記録（gamedata）、チーム、選手、球種の表を1つのオブジェクトにして Blob でダウンロードする。置き場は
~/野球/U23ワールドカップ2026/05_収集データ/u23-wc-2026/bass/（選手のデータなのでリポジトリには入れない）。
ダウンロードしたファイルを読むので、ほかの台本を読み込まず（標準の部品だけ）、python3 -I で流す。
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

# 球種の名前 → 記号（gt_clips.BASS_KIND の記号）。表にない名前は X（その他）
KIND = {"Fastball": "F", "Slider": "S", "Curveball": "C", "ChangeUp": "H", "Cutter": "T", "Sinker": "K", "Two Seam": "W", "TwoSeam": "W",
        "Splitter": "P", "Forkball": "P", "Sweeper": "X", "Other": "X",
        "ストレート": "F", "スライダー": "S", "カーブ": "C", "チェンジアップ": "H", "カットボール": "T", "シンカー": "K", "ツーシーム": "W",
        "スプリット": "P", "フォーク": "P"}


def b36(v) -> str:
    """0〜1295 の整数を36進2桁にする（JS の Math.round と同じく .5 は切り上げ）"""
    n = max(0, min(1295, math.floor((v or 0) + 0.5)))
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    return digits[n // 36] + digits[n % 36]


def r1(v) -> str:
    """小数1桁に丸めて、JS と同じ書き方にする（194.9、247、0）"""
    x = math.floor((v or 0) * 10 + 0.5) / 10
    return str(int(x)) if x == int(x) else str(x)


def load(path: str) -> dict:
    return json.load(open(path, encoding="utf-8"))


def rows_of(d: dict, game_num: str) -> tuple[dict, list[dict]]:
    game = next((g for g in d["games"] if str(g["game_num"]) == str(game_num) or g["_id"] == game_num), None)
    if game is None:
        sys.exit(f"試合番号 {game_num} が JSON にありません。list で確かめてください。")
    rows = sorted((r for r in d["gamedata"] if r["game_id"] == game["_id"] and r.get("page", 0) > 0), key=lambda r: r["page"])
    return game, rows


def cmd_list(path: str) -> None:
    d = load(path)
    tn = {t["_id"]: t["name"].replace("_u23_26", "") for t in d["teams"]}
    n = Counter(r["game_id"] for r in d["gamedata"])
    print("書き出した時刻", d["meta"]["exported_at"])
    for g in d["games"]:
        rows = [r for r in d["gamedata"] if r["game_id"] == g["_id"]]
        last = max((f"{r['inning']}{'表' if r.get('top_bottom') else '裏'}" for r in rows), default="")
        xy = sum(1 for r in rows if (r.get("course_x") or 0) > 0 or (r.get("course_y") or 0) > 0)
        print(g["game_num"], str(g["date"])[:10], f"{tn.get(g['first_team_id'], '?')}（先攻）対 {tn.get(g['second_team_id'], '?')}",
              f"{n[g['_id']]}行", f"座標あり{xy}", f"最後は{last}", "" if g.get("ended") else "（試合終了の印なし）")


def cmd_export(path: str, game_num: str, stem: str) -> None:
    d = load(path)
    names = {b["_id"]: b.get("name", "") for b in d["balltypes"]}
    game, rows = rows_of(d, game_num)
    unknown = Counter()
    toks7, toks13 = [], []
    for x in rows:
        pt = str(x.get("pitch_type") or "")
        if pt.endswith("000000000000000") or (x.get("pickoff_throw_to") or 0) > 0:
            a = "-"
        else:
            a = KIND.get(names.get(pt, ""))
            if a is None:
                unknown[names.get(pt, pt)] += 1
                a = "X"
        t = (f"{x['inning']}{'t' if x.get('top_bottom') else 'b'}{x.get('pre_ball_count', 0)}{x.get('pre_strike_count', 0)}{a}"
             f"{(x.get('batter') or {}).get('box_id') or '0'}{x.get('course_number_9') or 0}")
        toks7.append(t)
        toks13.append(t + b36(x.get("course_x")) + b36(x.get("course_y")) + b36(x.get("ball_speed")))
    pa = ["page,inning,half,pre_ball,pre_strike,end_result_id,bb_result,x,y,angle,dir5,feature,rank"]
    for x in rows:
        if not x.get("last_ball_flag"):
            continue
        b = x.get("batted_ball") or {}
        e = x.get("end_result_id")
        pa.append(",".join(str(v) for v in (x["page"], x["inning"], "t" if x.get("top_bottom") else "b", x.get("pre_ball_count", 0), x.get("pre_strike_count", 0),
                                              "" if e is None else e, b.get("result") or 0, r1(b.get("x")), r1(b.get("y")),
                                              math.floor((b.get("angle") or 0) + 0.5), b.get("direction_5_division") or 0, b.get("feature") or 0, b.get("rank") or 0)))
    out = Path(stem)
    out.parent.mkdir(parents=True, exist_ok=True)
    Path(str(out) + ".bass.txt").write_text(" ".join(toks7) + "\n", encoding="utf-8")
    Path(str(out) + ".bass_xy.txt").write_text(" ".join(toks13) + "\n", encoding="utf-8")
    Path(str(out) + ".bass_pa.csv").write_text("\n".join(pa) + "\n", encoding="utf-8")
    half = Counter(f"{x['inning']}{'t' if x.get('top_bottom') else 'b'}" for x in rows)
    print(f"{game['game_num']} {len(rows)}行、打席 {len(pa) - 1}、回ごとの行数 {dict(half)}")
    if unknown:
        print("  記号の表にない球種（その他にした）:", dict(unknown))
    print("→", str(out) + ".bass.txt / .bass_xy.txt / .bass_pa.csv")


def main() -> None:
    a = sys.argv[1:]
    if len(a) == 2 and a[0] == "list":
        cmd_list(a[1])
    elif len(a) == 4 and a[0] == "export":
        cmd_export(a[1], a[2], a[3])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
