#!/usr/bin/env python3
"""集めた試合データを、相手国ごとの1枚のHTMLにまとめる。

collect.py が書き出したCSVを読んで、選手ごとに積み上げた成績を出す。
出力は単体のHTMLファイルで、通信が切れていても開ける。現地で使うことを
想定しているので、外部のCSSやJavaScriptは読み込まない。

    python3 build_report.py
    open ~/野球/U23ワールドカップ2026/06_レポート/対戦相手.html
"""

from __future__ import annotations

import csv
import html as html_mod
import json
import math
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

DATA_ROOT = Path.home() / "野球" / "U23ワールドカップ2026" / "05_収集データ"
OUT_PATH = Path.home() / "野球" / "U23ワールドカップ2026" / "06_レポート" / "対戦相手.html"

# 相手国ごとに、どの大会のどのチーム名を見るか。
# 先に書いたものほど新しく、直近の世代に近い。
OPPONENTS = [
    ("キューバ", "Cuba", "B", [("u23-americas-2025", "Cuba"), ("u23-wc-2022", "Cuba")]),
    ("韓国", "Korea", "B", [("asian-championship-2025", "Korea"),
                            ("u23-wc-2024", "South Korea")]),
    ("ベネズエラ", "Venezuela", "B", [("u23-wc-2024", "Venezuela"),
                                      ("u23-wc-2022", "Venezuela")]),
    ("イギリス", "Great Britain", "B", [("u23-euro-2025", "Great Britain"),
                                        ("u23-wc-2024", "Great Britain")]),
    ("南アフリカ", "South Africa", "B", [("u23-wc-2024", "South Africa"),
                                         ("u23-wc-2022", "South Africa")]),
    ("チャイニーズタイペイ", "Chinese Taipei", "A",
     [("asian-championship-2025", "Chinese Taipei"),
      ("u23-wc-2024", "Chinese Taipei")]),
    ("プエルトリコ", "Puerto Rico", "A", [("u23-americas-2025", "Puerto Rico"),
                                          ("u23-wc-2024", "Puerto Rico")]),
    ("パナマ", "Panama", "A", [("u23-americas-2025", "Panama")]),
    ("オーストラリア", "Australia", "A", [("u23-wc-2024", "Australia"),
                                          ("u23-wc-2022", "Australia")]),
    ("ニカラグア", "Nicaragua", "A", [("u23-wc-2024", "Nicaragua")]),
    ("チェコ", "Czechia", "A", [("u23-euro-2025", "Czechia")]),
]

EVENT_LABEL = {
    "u23-americas-2025": "北中米カリブ予選 2025",
    "u23-euro-2025": "U-23欧州選手権 2025",
    "asian-championship-2025": "アジア選手権 2025",
    "u23-wc-2024": "U-23W杯 2024",
    "u23-wc-2022": "U-23W杯 2022",
}


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def number(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def name_of(row: dict) -> str:
    last = (row.get("lastname") or "").strip()
    first = (row.get("firstname") or "").strip()
    return f"{last}, {first}".strip(", ")


def fixed(numerator: float, denominator: float, digits: int) -> str:
    """割り算を小数 digits 桁で四捨五入した文字列にする。

    f"{x:.3f}" は2進数でちょうど半分になる値（5/16 = .3125 など）を偶数の側に丸めるので、
    .312 と .313 が混ざる。Decimal で四捨五入（ROUND_HALF_UP）にそろえる。
    """
    value = Decimal(str(numerator)) / Decimal(str(denominator))
    return format(value.quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP), f".{digits}f")


def rate(numerator: float, denominator: float, digits: int = 3) -> str:
    if not denominator:
        return "-"
    return fixed(numerator, denominator, digits).lstrip("0") or "0"


# hittype の意味。narrative と突き合わせて確かめた
HIT_TYPE = {"1": "ゴロ", "2": "ライナー", "3": "フライ", "4": "ポップ"}

FAIR_DEGREES = 45   # hitpull がこの角度を超える打球はファウル域
PULL_DEGREES = 8    # 中堅から左右この角度までは「センター」


def batted_kind(row: dict) -> str | None:
    """打球の種類。打球でない行は None。

    hittype が入っていても、距離と角度がどちらも0の行は打球ではない。
    暴投・盗塁・送球エラーなどの行に hittype が残っていることがある。
    """
    kind = HIT_TYPE.get(str(row.get("hittype") or ""))
    if not kind:
        return None
    if number(row.get("hitdistance")) == 0 and number(row.get("hitpull")) == 0:
        return None
    return kind


def bat_side(row: dict) -> str:
    """打者が実際に立った打席（"L" か "R"）。分からなければ空。

    collect.py が plays.csv に書いた batter_bats と pitcher_throws を見る。
    両打ち（S）は、相手投手の投げ手の逆の打席に立ったと見なす。
    """
    bats = str(row.get("batter_bats") or "").strip().upper()
    if bats in ("L", "R"):
        return bats
    throws = str(row.get("pitcher_throws") or "").strip().upper()
    if bats == "S" and throws in ("L", "R"):
        return "R" if throws == "L" else "L"
    return ""


def direction(angle: float, side: str) -> str:
    """打球方向を 引っ張り・センター・流し に分ける。左打ちは右方向が引っ張り。"""
    if not side:
        return ""
    toward_pull = angle if side == "L" else -angle
    if toward_pull > PULL_DEGREES:
        return "引っ張り"
    if toward_pull < -PULL_DEGREES:
        return "流し"
    return "センター"


def batted_balls(plays: list[dict], team: str) -> dict[str, dict]:
    """打者ごとの打球の内訳と方向。

    hitpull は打球方向の角度で、0が中堅、負が左方向、正が右方向。
    hitdistance は記録用の距離（単位の見立ては SPRAY_NOTE）。
    図と方向の割合には、フェアの範囲（±45°）で距離が0より大きい打球だけを使う。
    """
    out: dict[str, dict] = {}
    for row in plays:
        if row.get("batting_team") != team:
            continue
        kind = batted_kind(row)
        if not kind:
            continue
        entry = out.setdefault(str(row.get("batterid")), {
            "ゴロ": 0, "ライナー": 0, "フライ": 0, "ポップ": 0, "点": [],
            "引っ張り": 0, "センター": 0, "流し": 0,
        })
        entry[kind] += 1
        angle = number(row.get("hitpull"))
        distance = number(row.get("hitdistance"))
        if distance <= 0 or abs(angle) > FAIR_DEGREES:
            continue
        entry["点"].append((angle, distance, kind))
        way = direction(angle, bat_side(row))
        if way:
            entry[way] += 1
    return out


BAT_FIELDS = (("打席", "pa"), ("打数", "ab"), ("安打", "h"),
              ("二塁打", "double"), ("三塁打", "triple"), ("本塁打", "hr"),
              ("打点", "rbi"), ("四球", "bb"), ("死球", "hbp"), ("三振", "so"),
              ("見逃三振", "kl"), ("盗塁", "sb"), ("盗塁死", "cs"),
              ("犠打", "sh"), ("犠飛", "sf"), ("ゴロ", "ground"), ("フライ", "fly"))


def add_batting_rates(entry: dict) -> None:
    """打率・出塁率・長打率・三振率。出塁率の分母は 打数＋四球＋死球＋犠飛。"""
    hits = entry["安打"]
    at_bats = entry["打数"]
    singles = hits - entry["二塁打"] - entry["三塁打"] - entry["本塁打"]
    bases = singles + 2 * entry["二塁打"] + 3 * entry["三塁打"] + 4 * entry["本塁打"]
    on_base = hits + entry["四球"] + entry["死球"]
    chances = at_bats + entry["四球"] + entry["死球"] + entry["犠飛"]
    entry["打率"] = rate(hits, at_bats)
    entry["出塁率"] = rate(on_base, chances)
    entry["長打率"] = rate(bases, at_bats)
    entry["三振率"] = rate(entry["三振"], entry["打席"], 3)


def add_batted_rates(entry: dict, hit: dict) -> None:
    """打球の内訳と方向の割合。左右が分からない打球は方向の分母に入れない。"""
    in_play = sum(hit.get(kind, 0) for kind in HIT_TYPE.values())
    entry["打球"] = in_play
    entry["ゴロ率"] = rate(hit.get("ゴロ", 0), in_play, 2)
    entry["フライ率"] = rate(hit.get("フライ", 0) + hit.get("ポップ", 0), in_play, 2)
    known = sum(hit.get(way, 0) for way in ("引っ張り", "センター", "流し"))
    entry["引っ張り率"] = rate(hit.get("引っ張り", 0), known, 2)
    entry["流し率"] = rate(hit.get("流し", 0), known, 2)
    entry["_points"] = hit.get("点", [])


def row_order(row: dict) -> tuple:
    """行の新しさ（日付 → 試合ID）。同じ選手の綴りが大会の途中で変わったとき、新しい方を選ぶ。"""
    return (str(row.get("date") or ""), int(number(row.get("gameid"))))


def newer_name(entry: dict, row: dict) -> None:
    """entry の名前を、より新しい試合の行の綴りにする（"VAZQUE RIZO" → "VAZQUEZ RIZO" など）。"""
    order = row_order(row)
    if "_name_at" not in entry or order >= entry["_name_at"]:
        entry["名前"] = name_of(row) or entry.get("名前", "")
        entry["_name_at"] = order


def collect_batters(rows: list[dict], team: str,
                    balls: dict[str, dict] | None = None) -> list[dict]:
    """打者を選手ごとに積み上げる。名前は一番新しい試合の綴り。"""
    balls = balls or {}
    agg: dict[str, dict] = {}
    for row in rows:
        if row.get("team") != team:
            continue
        key = row.get("playerid") or name_of(row)
        entry = agg.setdefault(key, {
            "名前": name_of(row), "試合": 0,
            **{label: 0 for label, _ in BAT_FIELDS}, "守備": set(),
        })
        newer_name(entry, row)
        entry["試合"] += 1
        for label, field in BAT_FIELDS:
            entry[label] += int(number(row.get(field)))
        if row.get("pos"):
            entry["守備"].add(row["pos"].strip())
        entry["_id"] = str(row.get("playerid"))

    out = []
    for entry in agg.values():
        entry["守備"] = "/".join(sorted(entry["守備"]))
        add_batting_rates(entry)
        add_batted_rates(entry, balls.get(entry.get("_id", ""), {}))
        out.append(entry)
    out.sort(key=lambda e: (-e["打席"], e["名前"]))
    return out


def outs_of(value) -> int:
    """投球回の表記（"6.2"）をアウトの数（20）に直す。小数点の後ろはアウト数。"""
    whole, _, part = str(value or "0").strip().partition(".")
    try:
        return int(whole or 0) * 3 + int((part or "0")[0])
    except ValueError:
        return 0


def innings_text(outs: int) -> str:
    """アウトの数を野球の表記に戻す（28アウト → "9.1"）。"""
    return f"{outs // 3}.{outs % 3}"


PIT_FIELDS = (("被安打", "pitch_h"), ("失点", "pitch_r"), ("自責点", "pitch_er"),
              ("四球", "pitch_bb"), ("死球", "pitch_hbp"), ("三振", "pitch_so"),
              ("被本塁打", "pitch_hr"), ("球数", "pitch_pitches"),
              ("ストライク", "pitch_strikes"), ("打者", "pitch_bf"),
              ("ゴロ", "pitch_ground"), ("フライ", "pitch_fly"), ("暴投", "pitch_wp"))


def add_pitching_rates(entry: dict) -> None:
    """投球回は野球の表記（9回1/3 → "9.1"）。率の計算には実数（_ip）を使う。"""
    innings = entry["_outs"] / 3
    entry["投球回"] = innings_text(entry["_outs"])
    outs = entry["_outs"]  # 9イニングあたり = 数 × 27 ÷ アウト数
    entry["防御率"] = fixed(entry["自責点"] * 27, outs, 2) if outs else "-"
    entry["奪三振率"] = fixed(entry["三振"] * 27, outs, 1) if outs else "-"
    entry["与四球率"] = fixed(entry["四球"] * 27, outs, 1) if outs else "-"
    entry["ストライク率"] = rate(entry["ストライク"], entry["球数"], 2)
    entry["ゴロ率"] = rate(entry["ゴロ"], entry["ゴロ"] + entry["フライ"], 2)
    entry["_ip"] = innings


def collect_pitchers(rows: list[dict], team: str) -> list[dict]:
    """投手を選手ごとに積み上げる。投球回は登板ごとにアウト数へ直して足す。名前は一番新しい試合の綴り。"""
    agg: dict[str, dict] = {}
    for row in rows:
        if row.get("team") != team:
            continue
        key = row.get("playerid") or name_of(row)
        entry = agg.setdefault(key, {
            "名前": name_of(row), "登板": 0, "先発": 0, "投球回": "0.0",
            **{label: 0 for label, _ in PIT_FIELDS}, "_outs": 0,
        })
        newer_name(entry, row)
        entry["登板"] += 1
        entry["_id"] = str(row.get("playerid"))
        entry["先発"] += int(number(row.get("pitch_gs")))
        entry["_outs"] += outs_of(row.get("pitch_ip"))
        for label, field in PIT_FIELDS:
            entry[label] += int(number(row.get(field)))

    out = []
    for entry in agg.values():
        add_pitching_rates(entry)
        out.append(entry)
    out.sort(key=lambda e: (-e["_ip"], e["名前"]))
    return out


def team_tendency(batters: list[dict], plays: list[dict], team: str) -> dict:
    """チームの色。世代が変わっても残りやすいところを見る。"""
    plate = sum(b["打席"] for b in batters)
    steal = sum(b["盗塁"] for b in batters)
    caught = sum(b["盗塁死"] for b in batters)
    bunt = sum(b["犠打"] for b in batters)
    walks = sum(b["四球"] for b in batters)
    strikeouts = sum(b["三振"] for b in batters)
    kinds = {"ゴロ": 0, "ライナー": 0, "フライ": 0, "ポップ": 0}
    for row in plays:
        if row.get("batting_team") != team:
            continue
        kind = batted_kind(row)
        if kind:
            kinds[kind] += 1
    in_play = sum(kinds.values())  # 打球のデータがなければ率は "-"（".00" にしない）
    return {
        "打席": plate,
        "犠打": bunt,
        "盗塁": f"{steal}/{steal + caught}",
        "四球率": rate(walks, plate, 3),
        "三振率": rate(strikeouts, plate, 3),
        "ゴロ率": rate(kinds["ゴロ"], in_play, 2),
        "フライ率": rate(kinds["フライ"] + kinds["ポップ"], in_play, 2),
    }


# 打球図。縮尺は全図で同じにする（距離1あたり SPRAY_SCALE px）
SPRAY_SCALE = 0.75
SPRAY_EDGE = 320          # 扇形の外周。記録の最大（本塁打の310前後）が入る
SPRAY_INFIELD = 120       # 内野の土の目安
SPRAY_GUIDES = (100, 200, 300)
SPRAY_HOME = (200, 250)
# hitdistance の単位の見立て（2026-10-16、5大会6675球で確認）。
# 柵越えの本塁打が234〜314（82本中37本がちょうど310で、310が入力の上限と見られる）、
# 内野ゴロが94〜113、外野フライが226に集まる（上位4つの値で打球の45%）。メートルではありえず、
# フィートとしても柵や外野手の位置が2割ほど近すぎるので、記録アプリの図の上の距離と見る。
# 単位はどこにも書かれておらず確かめていないので、ページの文も見立てとして書く
SPRAY_NOTE = ("点線は距離100・200・300。距離はWBSCの記録アプリの値で、単位は確かめられていません。"
              "本塁打がおよそ260〜310に集まるので、実際のフィートより2割ほど短く出ているようです。"
              "打球の半分近くが同じいくつかの値（94・113・179・226など）に集まっていて、"
              "処理した野手の定位置の距離で記録されているとみられます。ファウル域と距離0以下の"
              "打球は描いていません。")

# 種類ごとのクラス・形・既定の色。色はサイト側のCSSでクラスごとに上書きできる。
# 既定の色は単体レポート（暗い背景）用。フライとポップは同じ色で、形だけ変える
SPRAY_MARK = {
    "ゴロ": ("spray-ground", "circle", "#3987e5"),
    "ライナー": ("spray-liner", "triangle", "#d95926"),
    "フライ": ("spray-fly", "square", "#199e70"),
    "ポップ": ("spray-pop", "diamond", "#199e70"),
}
COLOR = {kind: color for kind, (_, _, color) in SPRAY_MARK.items()}
SPRAY_FIELD = "#262b27"


def spray_xy(angle: float, distance: float) -> tuple[float, float]:
    """角度（0が中堅、負が左）と距離を、図の上の座標に直す。"""
    radians = math.radians(angle)
    length = min(distance, SPRAY_EDGE) * SPRAY_SCALE
    home_x, home_y = SPRAY_HOME
    return home_x + length * math.sin(radians), home_y - length * math.cos(radians)


def spray_arc(distance: float, closed: bool) -> str:
    """本塁から distance の位置に、ファウルラインからファウルラインまでの弧を引く。"""
    left = spray_xy(-FAIR_DEGREES, distance)
    right = spray_xy(FAIR_DEGREES, distance)
    radius = distance * SPRAY_SCALE
    arc = (f"M{left[0]:.1f} {left[1]:.1f} "
           f"A{radius:.1f} {radius:.1f} 0 0 1 {right[0]:.1f} {right[1]:.1f}")
    if not closed:
        return arc
    home_x, home_y = SPRAY_HOME
    return f"M{home_x} {home_y} L{arc[1:]} Z"


def spray_shape(kind: str, x: float, y: float, inner: str = "") -> str:
    """打球1つの印。ゴロ●・ライナー▲・フライ■・ポップ◆。"""
    css, shape, color = SPRAY_MARK[kind]
    common = (f'class="spray-dot {css}" fill="{color}" stroke="{SPRAY_FIELD}" '
              'stroke-width="1.2"')
    if shape == "circle":
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" {common}>{inner}</circle>'
    if shape == "square":
        return (f'<rect x="{x - 4.5:.1f}" y="{y - 4.5:.1f}" width="9" height="9" '
                f'{common}>{inner}</rect>')
    corners = {
        "triangle": ((0, -6.5), (-6, 4.5), (6, 4.5)),
        "diamond": ((0, -6.5), (6, 0), (0, 6.5), (-6, 0)),
    }[shape]
    points = " ".join(f"{x + dx:.1f},{y + dy:.1f}" for dx, dy in corners)
    return f'<polygon points="{points}" {common}>{inner}</polygon>'


def spray_field() -> str:
    """扇形の地面、ファウルライン、距離の目安線とその数字。"""
    parts = [
        f'<path class="spray-field" d="{spray_arc(SPRAY_EDGE, True)}" '
        f'fill="{SPRAY_FIELD}" stroke="#3d4a40"/>',
        f'<path class="spray-infield" d="{spray_arc(SPRAY_INFIELD, True)}" '
        'fill="#332c24" stroke="#4a3f33"/>',
    ]
    for distance in SPRAY_GUIDES:
        x, y = spray_xy(FAIR_DEGREES, distance)
        parts.append(
            f'<path class="spray-guide" d="{spray_arc(distance, False)}" fill="none" '
            'stroke="#7d8b80" stroke-dasharray="4 4" stroke-width="1"/>'
            f'<text class="spray-label" x="{x + 5:.1f}" y="{y + 4:.1f}" '
            f'fill="#9aa3b2" font-size="11">{distance}</text>'
        )
    home_x, home_y = SPRAY_HOME
    for side in (-FAIR_DEGREES, FAIR_DEGREES):
        x, y = spray_xy(side, SPRAY_EDGE)
        parts.append(f'<line class="spray-line" x1="{home_x}" y1="{home_y}" '
                     f'x2="{x:.1f}" y2="{y:.1f}" stroke="#8a968c" stroke-width="1.2"/>')
    return "".join(parts)


def spray_legend(points: list[tuple], total: int) -> str:
    """凡例（形と色）と、図に描いた打球の数。"""
    chips = []
    for kind in SPRAY_MARK:
        count = sum(1 for _, _, k in points if k == kind)
        chips.append(
            f'<span class="chip"><svg class="spray-key" width="14" height="14" '
            f'viewBox="-7 -7 14 14" aria-hidden="true">{spray_shape(kind, 0, 0)}</svg>'
            f'<b>{kind}</b>{count}</span>'
        )
    chips.append(f'<span class="chip"><b>図の打球</b>{len(points)}/{total}</span>')
    return f'<div class="chips">{"".join(chips)}</div>'


def spray_chart(batters: list[dict]) -> str:
    """打球方向の角度と距離から、落下点を扇形に置く。

    縮尺は全図で同じ。フェアの範囲（±45°）の外と距離0以下の打球は描かない
    （batted_balls の段階で _points から外している）。
    """
    points = [p for b in batters for p in b.get("_points", [])]
    if not points:
        return '<p class="empty">打球の記録がありません。</p>'
    total = sum(b.get("打球", 0) for b in batters) or len(points)
    dots = "".join(
        spray_shape(kind, *spray_xy(angle, distance),
                    inner=f"<title>{kind} {distance:.0f}</title>")
        for angle, distance, kind in points
    )
    _, home_y = SPRAY_HOME
    return f"""<div class="spray">
<svg class="spray-svg" viewBox="0 0 400 {home_y + 8}" width="100%" style="max-width:440px"
     role="img" aria-label="打球の落下点の図（{len(points)}球）">
{spray_field()}
{dots}
</svg>
{spray_legend(points, total)}
<p class="spray-note">{html_mod.escape(SPRAY_NOTE)}</p>
</div>"""


def table(rows: list[dict], columns: list[str]) -> str:
    if not rows:
        return '<p class="empty">データがありません。</p>'
    head = "".join(f"<th>{html_mod.escape(c)}</th>" for c in columns)
    body = []
    for row in rows:
        cells = "".join(
            f"<td>{html_mod.escape(str(row.get(c, '')))}</td>" for c in columns
        )
        body.append(f"<tr>{cells}</tr>")
    return (
        f'<table><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table>'
    )


BAT_COLUMNS = ["名前", "守備", "試合", "打席", "打数", "安打", "打率", "出塁率",
               "長打率", "二塁打", "三塁打", "本塁打", "打点", "四球", "三振",
               "三振率", "盗塁", "盗塁死", "犠打", "犠飛", "打球", "ゴロ率", "フライ率",
               "引っ張り率", "流し率"]
PIT_COLUMNS = ["名前", "登板", "先発", "投球回", "防御率", "被安打", "自責点",
               "三振", "奪三振率", "四球", "与四球率", "被本塁打", "球数",
               "ストライク率", "ゴロ率", "暴投"]


def build() -> str:
    data: dict[str, dict[str, list[dict]]] = {}
    for event in EVENT_LABEL:
        data[event] = {
            "batting": read_csv(DATA_ROOT / event / "batting.csv"),
            "pitching": read_csv(DATA_ROOT / event / "pitching.csv"),
            "plays": read_csv(DATA_ROOT / event / "plays.csv"),
        }

    sections = []
    nav = []
    for label, team, group, sources in OPPONENTS:
        anchor = team.replace(" ", "-").lower()
        nav.append(
            f'<button class="tab" data-target="{anchor}">{html_mod.escape(label)}'
            f'<span class="grp">{group}</span></button>'
        )
        blocks = []
        for event, team_name in sources:
            balls = batted_balls(data[event]["plays"], team_name)
            batters = collect_batters(data[event]["batting"], team_name, balls)
            pitchers = collect_pitchers(data[event]["pitching"], team_name)
            if not batters and not pitchers:
                continue
            tendency = team_tendency(batters, data[event]["plays"], team_name)
            spray = spray_chart(batters)
            chips = "".join(
                f'<span class="chip"><b>{html_mod.escape(k)}</b>'
                f'{html_mod.escape(str(v))}</span>'
                for k, v in tendency.items()
            )
            blocks.append(f"""
<section class="event">
  <h3>{html_mod.escape(EVENT_LABEL[event])}</h3>
  <div class="chips">{chips}</div>
  <h4>打球の散らばり</h4>{spray}
  <h4>打者</h4>{table(batters, BAT_COLUMNS)}
  <h4>投手</h4>{table(pitchers, PIT_COLUMNS)}
</section>""")
        if not blocks:
            blocks.append('<p class="empty">この相手のデータはまだありません。</p>')
        sections.append(
            f'<div class="panel" id="{anchor}"><h2>{html_mod.escape(label)}'
            f'<small>グループ{group}・{html_mod.escape(team)}</small></h2>'
            f'{"".join(blocks)}</div>'
        )

    return TEMPLATE.replace("{{NAV}}", "".join(nav)).replace(
        "{{PANELS}}", "".join(sections)
    )


TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>U-23W杯 対戦相手データ</title>
<style>
:root{--bg:#0f1115;--card:#171a21;--line:#272c36;--text:#e8eaed;--dim:#9aa3b2;
      --accent:#4da3ff;--warm:#ffb454}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
     font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;
     font-size:14px;line-height:1.6}
header{padding:20px 24px 12px;border-bottom:1px solid var(--line)}
h1{margin:0;font-size:19px}
.sub{color:var(--dim);font-size:12px;margin-top:4px}
nav{display:flex;flex-wrap:wrap;gap:6px;padding:12px 24px;
    border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}
.tab{background:var(--card);color:var(--text);border:1px solid var(--line);
     border-radius:999px;padding:6px 13px;font-size:13px;cursor:pointer}
.tab:hover{border-color:var(--accent)}
.tab.on{background:var(--accent);color:#08121f;border-color:var(--accent);font-weight:700}
.grp{margin-left:6px;font-size:10px;opacity:.65}
main{padding:20px 24px 60px}
.panel{display:none}
.panel.on{display:block}
h2{font-size:22px;margin:0 0 4px}
h2 small{display:block;font-size:12px;color:var(--dim);font-weight:400;margin-top:2px}
.event{margin-top:26px;background:var(--card);border:1px solid var(--line);
       border-radius:10px;padding:16px}
h3{margin:0 0 10px;font-size:15px;color:var(--warm)}
h4{margin:18px 0 6px;font-size:13px;color:var(--dim)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:6px}
.chip{background:#1e232c;border:1px solid var(--line);border-radius:6px;
      padding:3px 9px;font-size:12px}
.chip b{color:var(--dim);font-weight:500;margin-right:6px}
.empty{color:var(--dim);font-size:13px}
.spray{margin:8px 0 4px}
.spray-key{vertical-align:-2px;margin-right:5px}
.spray-note{color:var(--dim);font-size:11px;margin:2px 0 0}
table{width:100%;border-collapse:collapse;font-size:12px;
      font-variant-numeric:tabular-nums;display:block;overflow-x:auto}
th,td{padding:5px 8px;border-bottom:1px solid var(--line);
      text-align:right;white-space:nowrap}
th{color:var(--dim);font-weight:500;cursor:pointer;position:sticky;top:0;
   background:var(--card)}
th:hover{color:var(--accent)}
td:first-child,th:first-child{text-align:left;position:sticky;left:0;
   background:var(--card)}
tbody tr:hover td{background:#1d222b}
</style>
</head>
<body>
<header>
  <h1>U-23W杯 対戦相手データ</h1>
  <div class="sub">WBSCの大会サイトから集めた記録。見出しを押すと並べ替わります。</div>
</header>
<nav>{{NAV}}</nav>
<main>{{PANELS}}</main>
<script>
const tabs=[...document.querySelectorAll('.tab')];
const panels=[...document.querySelectorAll('.panel')];
function show(id){
  tabs.forEach(t=>t.classList.toggle('on',t.dataset.target===id));
  panels.forEach(p=>p.classList.toggle('on',p.id===id));
  try{localStorage.setItem('u23tab',id)}catch(e){}
}
tabs.forEach(t=>t.addEventListener('click',()=>show(t.dataset.target)));
let start=null;
try{start=localStorage.getItem('u23tab')}catch(e){}
show(panels.some(p=>p.id===start)?start:panels[0].id);

document.querySelectorAll('table').forEach(tb=>{
  tb.querySelectorAll('th').forEach((th,i)=>{
    let asc=false;
    th.addEventListener('click',()=>{
      asc=!asc;
      const body=tb.tBodies[0];
      const rows=[...body.rows];
      rows.sort((a,b)=>{
        const x=a.cells[i].textContent.trim(), y=b.cells[i].textContent.trim();
        const nx=parseFloat(x), ny=parseFloat(y);
        const both=!isNaN(nx)&&!isNaN(ny);
        if(both) return asc?nx-ny:ny-nx;
        return asc?x.localeCompare(y):y.localeCompare(x);
      });
      rows.forEach(r=>body.appendChild(r));
    });
  });
});
</script>
</body>
</html>
"""


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(build(), encoding="utf-8")
    size = OUT_PATH.stat().st_size / 1024
    print(f"{OUT_PATH} ({size:.0f} KB)")


if __name__ == "__main__":
    main()
