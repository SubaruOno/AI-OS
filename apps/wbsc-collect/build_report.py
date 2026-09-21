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
from collections import defaultdict
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


def rate(numerator: float, denominator: float, digits: int = 3) -> str:
    if not denominator:
        return "-"
    return f"{numerator / denominator:.{digits}f}".lstrip("0") or "0"


# hittype の意味。narrative と突き合わせて確かめた
HIT_TYPE = {"1": "ゴロ", "2": "ライナー", "3": "フライ", "4": "ポップ"}


def batted_balls(plays: list[dict], team: str) -> dict[str, dict]:
    """打者ごとの打球の内訳と方向。

    hitpull は打球方向の角度で、負が左方向、正が右方向。
    hitdistance は飛距離。この2つで落下点が決まる。
    """
    out: dict[str, dict] = {}
    for row in plays:
        if row.get("batting_team") != team:
            continue
        kind = HIT_TYPE.get(row.get("hittype"))
        if not kind:
            continue
        entry = out.setdefault(str(row.get("batterid")), {
            "ゴロ": 0, "ライナー": 0, "フライ": 0, "ポップ": 0, "点": [],
        })
        entry[kind] += 1
        angle = row.get("hitpull")
        distance = row.get("hitdistance")
        if angle not in ("", None) and distance not in ("", "0", None):
            entry["点"].append((float(angle), float(distance), kind))
    return out


def collect_batters(rows: list[dict], team: str,
                    balls: dict[str, dict] | None = None) -> list[dict]:
    """打者を選手ごとに積み上げる。"""
    balls = balls or {}
    agg: dict[str, dict] = {}
    for row in rows:
        if row.get("team") != team:
            continue
        key = row.get("playerid") or name_of(row)
        entry = agg.setdefault(key, {
            "名前": name_of(row), "試合": 0, "打席": 0, "打数": 0, "安打": 0,
            "二塁打": 0, "三塁打": 0, "本塁打": 0, "打点": 0, "四球": 0,
            "死球": 0, "三振": 0, "見逃三振": 0, "盗塁": 0, "盗塁死": 0,
            "犠打": 0, "ゴロ": 0, "フライ": 0, "守備": set(),
        })
        entry["試合"] += 1
        for label, field in (("打席", "pa"), ("打数", "ab"), ("安打", "h"),
                             ("二塁打", "double"), ("三塁打", "triple"),
                             ("本塁打", "hr"), ("打点", "rbi"), ("四球", "bb"),
                             ("死球", "hbp"), ("三振", "so"), ("見逃三振", "kl"),
                             ("盗塁", "sb"), ("盗塁死", "cs"), ("犠打", "sh"),
                             ("ゴロ", "ground"), ("フライ", "fly")):
            entry[label] += int(number(row.get(field)))
        if row.get("pos"):
            entry["守備"].add(row["pos"].strip())
        entry["_id"] = str(row.get("playerid"))

    out = []
    for entry in agg.values():
        hits = entry["安打"]
        at_bats = entry["打数"]
        singles = hits - entry["二塁打"] - entry["三塁打"] - entry["本塁打"]
        bases = singles + 2 * entry["二塁打"] + 3 * entry["三塁打"] + 4 * entry["本塁打"]
        on_base = hits + entry["四球"] + entry["死球"]
        chances = at_bats + entry["四球"] + entry["死球"] + entry["犠打"]
        balls_in_play = entry["ゴロ"] + entry["フライ"]
        entry["守備"] = "/".join(sorted(entry["守備"]))
        entry["打率"] = rate(hits, at_bats)
        entry["出塁率"] = rate(on_base, chances)
        entry["長打率"] = rate(bases, at_bats)
        entry["三振率"] = rate(entry["三振"], entry["打席"], 3)
        hit = balls.get(entry.pop("_id", ""), {})
        ground = hit.get("ゴロ", 0)
        liner = hit.get("ライナー", 0)
        fly = hit.get("フライ", 0)
        pop = hit.get("ポップ", 0)
        in_play = ground + liner + fly + pop
        entry["打球"] = in_play
        entry["ゴロ率"] = rate(ground, in_play, 2)
        entry["フライ率"] = rate(fly + pop, in_play, 2)
        points = hit.get("点", [])
        pulled = sum(1 for angle, _, _ in points if angle < -8)
        opposite = sum(1 for angle, _, _ in points if angle > 8)
        entry["引っ張り率"] = rate(pulled, len(points), 2)
        entry["流し率"] = rate(opposite, len(points), 2)
        entry["_points"] = points
        out.append(entry)
    out.sort(key=lambda e: (-e["打席"], e["名前"]))
    return out


def collect_pitchers(rows: list[dict], team: str) -> list[dict]:
    agg: dict[str, dict] = {}
    for row in rows:
        if row.get("team") != team:
            continue
        key = row.get("playerid") or name_of(row)
        entry = agg.setdefault(key, {
            "名前": name_of(row), "登板": 0, "先発": 0, "投球回": 0.0,
            "被安打": 0, "失点": 0, "自責点": 0, "四球": 0, "死球": 0,
            "三振": 0, "被本塁打": 0, "球数": 0, "ストライク": 0,
            "打者": 0, "ゴロ": 0, "フライ": 0, "暴投": 0,
        })
        entry["登板"] += 1
        entry["先発"] += int(number(row.get("pitch_gs")))
        entry["投球回"] += number(row.get("pitch_ip"))
        for label, field in (("被安打", "pitch_h"), ("失点", "pitch_r"),
                             ("自責点", "pitch_er"), ("四球", "pitch_bb"),
                             ("死球", "pitch_hbp"), ("三振", "pitch_so"),
                             ("被本塁打", "pitch_hr"), ("球数", "pitch_pitches"),
                             ("ストライク", "pitch_strikes"), ("打者", "pitch_bf"),
                             ("ゴロ", "pitch_ground"), ("フライ", "pitch_fly"),
                             ("暴投", "pitch_wp")):
            entry[label] += int(number(row.get(field)))

    out = []
    for entry in agg.values():
        # 投球回は .1 と .2 が1/3回と2/3回を表すので、実数に直す
        whole = int(entry["投球回"])
        fraction = round((entry["投球回"] - whole) * 10)
        innings = whole + fraction / 3
        entry["投球回"] = f"{innings:.1f}"
        entry["防御率"] = f"{entry['自責点'] * 9 / innings:.2f}" if innings else "-"
        entry["奪三振率"] = f"{entry['三振'] * 9 / innings:.1f}" if innings else "-"
        entry["与四球率"] = f"{entry['四球'] * 9 / innings:.1f}" if innings else "-"
        entry["ストライク率"] = rate(entry["ストライク"], entry["球数"], 2)
        entry["ゴロ率"] = rate(entry["ゴロ"], entry["ゴロ"] + entry["フライ"], 2)
        entry["_ip"] = innings
        out.append(entry)
    out.sort(key=lambda e: (-e["_ip"], e["名前"]))
    for entry in out:
        entry.pop("_ip")
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
        kind = HIT_TYPE.get(row.get("hittype"))
        if kind:
            kinds[kind] += 1
    in_play = sum(kinds.values()) or 1
    return {
        "打席": plate,
        "犠打": bunt,
        "盗塁": f"{steal}/{steal + caught}",
        "四球率": rate(walks, plate, 3),
        "三振率": rate(strikeouts, plate, 3),
        "ゴロ率": rate(kinds["ゴロ"], in_play, 2),
        "フライ率": rate(kinds["フライ"] + kinds["ポップ"], in_play, 2),
    }


COLOR = {"ゴロ": "#4da3ff", "ライナー": "#ffb454", "フライ": "#7ee081",
         "ポップ": "#c792ea"}


def spray_chart(batters: list[dict]) -> str:
    """打球方向の角度と飛距離から、落下点を扇形に置く。"""
    import math

    points = [p for b in batters for p in b.get("_points", [])]
    if not points:
        return '<p class="empty">打球の記録がありません。</p>'
    longest = max(distance for _, distance, _ in points) or 1
    dots = []
    for angle, distance, kind in points:
        # 角度は0が中堅方向。負が左、正が右。
        radians = math.radians(angle * 2)
        length = 190 * (distance / longest)
        x = 200 + length * math.sin(radians)
        y = 250 - length * math.cos(radians)
        dots.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{COLOR[kind]}" '
            f'opacity=".65"><title>{kind} {distance:.0f}</title></circle>'
        )
    legend = " ".join(
        f'<span class="chip"><b style="color:{color}">●</b>{kind}</span>'
        for kind, color in COLOR.items()
    )
    return f"""<div class="spray">
<svg viewBox="0 0 400 270" width="100%" style="max-width:420px">
  <path d="M200 250 L60 110 A198 198 0 0 1 340 110 Z"
        fill="#1b2a20" stroke="#2f4638"/>
  <path d="M200 250 L128 178 A102 102 0 0 1 272 178 Z"
        fill="#2a2018" stroke="#3d3025"/>
  <line x1="200" y1="250" x2="60" y2="110" stroke="#41503f"/>
  <line x1="200" y1="250" x2="340" y2="110" stroke="#41503f"/>
  {''.join(dots)}
</svg>
<div class="chips">{legend}<span class="chip"><b>打球</b>{len(points)}</span>
<span class="chip"><b>最長</b>{longest:.0f}</span></div>
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
               "三振率", "盗塁", "盗塁死", "犠打", "打球", "ゴロ率", "フライ率",
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
