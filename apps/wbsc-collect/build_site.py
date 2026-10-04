#!/usr/bin/env python3
"""U-23W杯のスタッフ共有サイトを組み立てる。

collect.py が集めたデータから、日程と結果・順位表・相手国ページ・選手ページを
静的なHTMLとして書き出す。サイトは「リンクを知っている人だけが開ける」形で、
推測できない長いフォルダ名（合言葉）の下にすべてのページを置く。入口のURLを
開いても白紙しか出ない。検索エンジンには載せない。

    python3 build_site.py              # 書き出す
    python3 build_site.py --new-token  # 合言葉を作り直す（リンクが漏れたとき）

合言葉はリポジトリに入らない private/u23-site-token に保存する。
出力先は ~/野球/U23ワールドカップ2026/07_サイト/dist で、この中身をそのまま
Cloudflare Pages に上げる。
"""

from __future__ import annotations

import argparse
import ast
import html
import json
import secrets
import shutil
import string
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import build_report as br

ROOT = Path.home() / "野球" / "U23ワールドカップ2026"
OUT = ROOT / "07_サイト" / "dist"
TOKEN_FILE = Path(__file__).resolve().parents[2] / "private" / "u23-site-token"

CURRENT = "u23-wc-2026"
EVENT_LABEL = {CURRENT: "U-23W杯 2026（本大会）", **br.EVENT_LABEL}

# 日本語の国名。WBSCの表記からひく
JA = {team: label for label, team, _, _ in br.OPPONENTS}
JA.update({"Japan": "日本", "South Korea": "韓国", "Korea": "韓国"})
GROUP = {team: group for _, team, group, _ in br.OPPONENTS}
GROUP["Japan"] = "B"

# 2026年大会の出場資格。2003年1月1日以降の生まれ
ELIGIBLE_FROM = 2003


def esc(value) -> str:
    return html.escape(str(value))


def slug(team: str) -> str:
    return team.replace(" ", "-").lower()


def ja(team: str) -> str:
    return JA.get(team, team)


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


def birth_year(info: dict) -> int | None:
    dob = str(info.get("dob") or "")[:4]
    return int(dob) if dob.isdigit() else None


def local_time(game: dict) -> datetime | None:
    try:
        return datetime.strptime(game["start"], "%Y-%m-%d %H:%M:%S")
    except (KeyError, TypeError, ValueError):
        return None


WEEK = "月火水木金土日"


def fmt(moment: datetime) -> str:
    return f"{moment.month}/{moment.day}({WEEK[moment.weekday()]}) {moment:%H:%M}"


def finished(game: dict) -> bool:
    return game.get("gamestatustext") == "F"


# ---------------------------------------------------------------- 部品


def page(title: str, body: str, depth: int, token: str) -> str:
    up = "../" * depth
    return TEMPLATE.format(
        title=esc(title), body=body, home=f"{up}index.html",
        sched=f"{up}schedule.html", teams=f"{up}teams.html",
        sw=f"{up}sw.js", built=datetime.now().strftime("%m/%d %H:%M"),
    )


def score(game: dict) -> str:
    if finished(game):
        return f'{game.get("awayruns", "")} - {game.get("homeruns", "")}'
    return "-"


def game_rows(games: list[dict], up: str) -> str:
    rows = []
    for game in games:
        moment = local_time(game)
        if not moment:
            continue
        away, home = game.get("awaylabel", ""), game.get("homelabel", "")
        japan = "Japan" in (away, home)
        def side(team: str) -> str:
            if team in GROUP and team != "Japan":
                return f'<a href="{up}team/{slug(team)}.html">{esc(ja(team))}</a>'
            return esc(ja(team))

        stadium = (game.get("stadium") or "").replace("Estadio ", "")
        jst = moment + timedelta(hours=15)
        rows.append(
            f'<tr class="{"jp" if japan else ""}">'
            f'<td><b>{fmt(jst)}</b><small>現地 {fmt(moment)}</small></td>'
            f'<td>{side(away)} <span class="sc">{score(game)}</span> {side(home)}'
            f'<small>{esc(stadium)}</small></td></tr>'
        )
    if not rows:
        return '<p class="empty">試合がありません。</p>'
    return (
        '<table class="games"><thead><tr><th>日本時間</th><th>ビジター - ホーム</th>'
        f'</tr></thead><tbody>{"".join(rows)}</tbody></table>'
    )


def standings(games: list[dict]) -> str:
    table: dict[str, dict] = {
        team: {"勝": 0, "敗": 0, "得点": 0, "失点": 0} for team in GROUP
    }
    for game in games:
        if not finished(game) or game.get("gametypelabel") != "Opening Round":
            continue
        home, away = game.get("homelabel"), game.get("awaylabel")
        hr, ar = int(br.number(game.get("homeruns"))), int(br.number(game.get("awayruns")))
        for team, mine, theirs in ((home, hr, ar), (away, ar, hr)):
            if team not in table:
                continue
            table[team]["得点"] += mine
            table[team]["失点"] += theirs
            table[team]["勝" if mine > theirs else "敗"] += 1
    out = []
    for group in ("A", "B"):
        teams = sorted(
            (t for t in table if GROUP[t] == group),
            key=lambda t: (-table[t]["勝"], table[t]["敗"],
                           table[t]["失点"] - table[t]["得点"]),
        )
        rows = "".join(
            f'<tr class="{"jp" if t == "Japan" else ""}"><td>{i}</td><td>'
            + (esc(ja(t)) if t == "Japan"
               else f'<a href="team/{slug(t)}.html">{esc(ja(t))}</a>')
            + f'</td><td>{table[t]["勝"]}</td><td>{table[t]["敗"]}</td>'
            f'<td>{table[t]["得点"]}</td><td>{table[t]["失点"]}</td></tr>'
            for i, t in enumerate(teams, 1)
        )
        out.append(
            f'<div class="card"><h3>グループ{group}</h3><table class="stand"><thead><tr>'
            '<th>#</th><th>国</th><th>勝</th><th>敗</th><th>得点</th><th>失点</th>'
            f'</tr></thead><tbody>{rows}</tbody></table></div>'
        )
    return '<div class="two">' + "".join(out) + "</div>"


def linked_table(rows: list[dict], columns: list[str], up: str) -> str:
    if not rows:
        return '<p class="empty">データがありません。</p>'
    head = "".join(f"<th>{esc(c)}</th>" for c in columns)
    body = []
    for row in rows:
        cells = []
        for c in columns:
            value = row.get(c, "")
            if c == "名前" and row.get("_id"):
                value = f'<a href="{up}p/{row["_id"]}.html">{esc(value)}</a>'
            else:
                value = esc(value)
            cells.append(f"<td>{value}</td>")
        body.append(f'<tr>{"".join(cells)}</tr>')
    return (
        f'<div class="scroll"><table class="sort"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


# ---------------------------------------------------------------- 組み立て


def build(token: str) -> dict[str, str]:
    data = {
        event: {
            "batting": br.read_csv(br.DATA_ROOT / event / "batting.csv"),
            "pitching": br.read_csv(br.DATA_ROOT / event / "pitching.csv"),
            "plays": br.read_csv(br.DATA_ROOT / event / "plays.csv"),
        }
        for event in EVENT_LABEL
    }
    games_path = br.DATA_ROOT / CURRENT / "games.json"
    games = json.loads(games_path.read_text()) if games_path.exists() else []
    games.sort(key=lambda g: g.get("start") or "")

    # 生年・投打は選手IDごとに、どの大会の行からでも拾う
    info: dict[str, dict] = {}
    for event in EVENT_LABEL:
        for row in data[event]["batting"] + data[event]["pitching"]:
            pid = str(row.get("playerid"))
            if pid not in info:
                info[pid] = player_info(row)

    pages: dict[str, str] = {}
    players: dict[str, dict] = defaultdict(lambda: {"blocks": []})

    # 相手国ページ
    team_cards = []
    for label, team, group, sources in br.OPPONENTS:
        sources = [(CURRENT, team)] + list(sources)
        blocks = []
        for event, name in sources:
            balls = br.batted_balls(data[event]["plays"], name)
            batters = br.collect_batters(data[event]["batting"], name, balls)
            pitchers = br.collect_pitchers(data[event]["pitching"], name)
            if not batters and not pitchers:
                continue
            for entry in batters + pitchers:
                year = birth_year(info.get(entry.get("_id"), {}))
                entry["生年"] = year or "?"
                entry["2026"] = "○" if year and year >= ELIGIBLE_FROM else ""
            tendency = br.team_tendency(batters, data[event]["plays"], name)
            chips = "".join(
                f'<span class="chip"><b>{esc(k)}</b>{esc(v)}</span>'
                for k, v in tendency.items()
            )
            blocks.append(f"""
<section class="card">
  <h3>{esc(EVENT_LABEL[event])}</h3>
  <div class="chips">{chips}</div>
  <h4>打球の散らばり</h4>{br.spray_chart(batters)}
  <h4>打者</h4>{linked_table(batters, ["名前", "生年", "2026"] + br.BAT_COLUMNS[1:], "../")}
  <h4>投手</h4>{linked_table(pitchers, ["名前", "生年", "2026"] + br.PIT_COLUMNS[1:], "../")}
</section>""")
            for entry in batters:
                players[entry["_id"]]["blocks"].append(("bat", event, team, entry))
            for entry in pitchers:
                players[entry["_id"]]["blocks"].append(("pit", event, team, entry))
        mine = [g for g in games if team in (g.get("homelabel"), g.get("awaylabel"))]
        body = (
            f'<h2>{esc(label)}<small>グループ{group}・{esc(team)}</small></h2>'
            '<p class="note">「2026」の○は、生年から見て今大会も出場できる選手'
            f'（{ELIGIBLE_FROM}年以降生まれ）。見出しを押すと並べ替わります。</p>'
            f'<h3 class="sec">今大会の日程</h3>{game_rows(mine, "../")}'
            + ("".join(blocks) or '<p class="empty">この相手のデータはまだありません。</p>')
        )
        pages[f"team/{slug(team)}.html"] = page(label, body, 1, token)
        team_cards.append(
            f'<a class="tcard" href="team/{slug(team)}.html"><span>{esc(label)}</span>'
            f'<small>グループ{group}</small></a>'
        )

    # 選手ページ
    for pid, entry in players.items():
        meta = info.get(pid, {})
        first = entry["blocks"][0][3]
        team = entry["blocks"][0][2]
        year = birth_year(meta)
        chips = "".join(
            f'<span class="chip"><b>{k}</b>{esc(v)}</span>'
            for k, v in (("国", ja(team)), ("位置", meta.get("position", "?")),
                         ("投打", f'{meta.get("throws", "?")}投{meta.get("bats", "?")}打'),
                         ("生年", year or "?"),
                         ("今大会", "出場可" if year and year >= ELIGIBLE_FROM
                          else "年齢超過" if year else "?"))
        )
        sections = []
        for kind, event, _, line in entry["blocks"]:
            if kind == "bat":
                sections.append(
                    f'<section class="card"><h3>{esc(EVENT_LABEL[event])} 打撃</h3>'
                    + linked_table([line], br.BAT_COLUMNS[1:], "../")
                    + f'<h4>打球</h4>{br.spray_chart([line])}</section>'
                )
            else:
                sections.append(
                    f'<section class="card"><h3>{esc(EVENT_LABEL[event])} 投球</h3>'
                    + linked_table([line], br.PIT_COLUMNS[1:], "../") + "</section>"
                )
        body = (
            f'<p class="crumb"><a href="../team/{slug(team)}.html">← {esc(ja(team))}</a></p>'
            f'<h2>{esc(first["名前"])}</h2><div class="chips">{chips}</div>'
            + "".join(sections)
        )
        pages[f"p/{pid}.html"] = page(first["名前"], body, 1, token)

    # トップ
    now = datetime.utcnow() - timedelta(hours=6)  # マナグアは UTC-6
    japan = [g for g in games if "Japan" in (g.get("homelabel"), g.get("awaylabel"))]
    upcoming = [g for g in japan if not finished(g)]
    next_card = ""
    if upcoming:
        game = upcoming[0]
        moment = local_time(game)
        rival = game["awaylabel"] if game["homelabel"] == "Japan" else game["homelabel"]
        days = (moment.date() - now.date()).days if moment else None
        next_card = (
            f'<a class="hero" href="team/{slug(rival)}.html"><small>次の日本戦'
            + (f"（あと{days}日）" if days and days > 0 else "")
            + f'</small><b>日本 vs {esc(ja(rival))}</b><span>現地 {fmt(moment)}'
            f'　日本時間 {fmt(moment + timedelta(hours=15))}</span>'
            f'<span>{esc(game.get("stadium", ""))}</span></a>'
        )
    body = (
        f"{next_card}<h3 class='sec'>日本戦</h3>{game_rows(japan, '')}"
        f"<h3 class='sec'>順位（1次ラウンド）</h3>{standings(games)}"
        f"<h3 class='sec'>相手国</h3><div class='tgrid'>{''.join(team_cards)}</div>"
    )
    pages["index.html"] = page("U-23W杯 2026", body, 0, token)

    # 日程
    by_day: dict[str, list[dict]] = defaultdict(list)
    for game in games:
        moment = local_time(game)
        if moment:
            by_day[fmt(moment).split(" ")[0]].append(game)
    body = "<h2>日程と結果<small>日本時間は現地 +15時間</small></h2>" + "".join(
        f"<h3 class='sec'>{esc(day)}</h3>{game_rows(day_games, '')}"
        for day, day_games in by_day.items()
    ) + ('<p class="note">スーパーラウンド以降（11/12〜15）の組み合わせは'
         '1次ラウンドの結果で決まり、決まりしだい載ります。</p>')
    pages["schedule.html"] = page("日程と結果", body, 0, token)
    pages["teams.html"] = page(
        "相手国", f"<h2>相手国</h2><div class='tgrid'>{''.join(team_cards)}</div>", 0, token
    )
    return pages


SW = """const C='u23-v1';
self.addEventListener('install',e=>self.skipWaiting());
self.addEventListener('activate',e=>self.clients.claim());
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  e.respondWith(fetch(e.request).then(r=>{
    const copy=r.clone();caches.open(C).then(c=>c.put(e.request,copy));return r;
  }).catch(()=>caches.match(e.request)));
});
"""

BLANK = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="robots" content="noindex,nofollow"><title></title></head><body></body></html>
"""

TEMPLATE = """<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta name="referrer" content="no-referrer">
<title>{title}</title>
<style>
:root{{--bg:#0f1115;--card:#171a21;--line:#272c36;--text:#e8eaed;--dim:#9aa3b2;
  --accent:#4da3ff;--warm:#ffb454;--jp:#2a1d22}}
@media (prefers-color-scheme: light){{:root{{--bg:#f6f7f9;--card:#fff;--line:#e2e5ea;
  --text:#1b1f27;--dim:#5f6878;--accent:#0b64c8;--warm:#b45d00;--jp:#fdecef}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);
  font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;font-size:14px;line-height:1.6}}
a{{color:var(--accent);text-decoration:none}}
header{{display:flex;gap:16px;align-items:center;padding:12px 16px;border-bottom:1px solid var(--line);
  position:sticky;top:0;background:var(--bg);z-index:5;flex-wrap:wrap}}
header b{{font-size:15px;margin-right:auto}}
header a{{font-size:13px}}
main{{max-width:1100px;margin:0 auto;padding:16px 16px 60px}}
h2{{font-size:21px;margin:8px 0 6px}}
h2 small{{display:block;font-size:12px;color:var(--dim);font-weight:400}}
h3{{font-size:15px;margin:0 0 8px;color:var(--warm)}}
h3.sec{{margin:26px 0 8px}}
h4{{margin:16px 0 6px;font-size:13px;color:var(--dim)}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin-top:18px}}
.two{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}}
.two .card{{margin-top:0}}
.hero{{display:flex;flex-direction:column;gap:2px;background:var(--card);border:1px solid var(--line);
  border-left:4px solid #d0103a;border-radius:10px;padding:14px 16px;color:var(--text)}}
.hero b{{font-size:20px}} .hero small,.hero span{{color:var(--dim);font-size:13px}}
.tgrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}}
.tcard{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px 12px;
  display:flex;justify-content:space-between;align-items:center;color:var(--text)}}
.tcard small{{color:var(--dim)}}
.chips{{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}}
.chip{{background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:3px 9px;font-size:12px}}
.chip b{{color:var(--dim);font-weight:500;margin-right:6px}}
.note,.empty,.crumb{{color:var(--dim);font-size:12px}}
.scroll{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:12px;font-variant-numeric:tabular-nums}}
th,td{{padding:5px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap}}
th{{color:var(--dim);font-weight:500}}
table.sort th{{cursor:pointer}}
td:first-child,th:first-child{{text-align:left}}
table.games td{{text-align:left;white-space:normal;vertical-align:top}}
table.games small{{display:block;color:var(--dim);font-size:11px;font-weight:400}}
.sc{{color:var(--dim);margin:0 6px}}
table.stand td:nth-child(2),table.stand th:nth-child(2){{text-align:left}}
tr.jp td{{background:var(--jp);font-weight:600}}
footer{{color:var(--dim);font-size:11px;text-align:center;padding:20px}}
</style></head><body>
<header><b>U-23W杯 2026</b><a href="{home}">トップ</a><a href="{sched}">日程と結果</a>
<a href="{teams}">相手国</a></header>
<main>{body}</main>
<footer>WBSCの大会サイトの記録から作成・{built}更新・関係者限り。リンクを外に回さないでください。</footer>
<script>
if('serviceWorker' in navigator)navigator.serviceWorker.register('{sw}').catch(()=>{{}});
document.querySelectorAll('table.sort').forEach(tb=>{{
  tb.querySelectorAll('th').forEach((th,i)=>{{let asc=false;th.addEventListener('click',()=>{{
    asc=!asc;const b=tb.tBodies[0];[...b.rows].sort((x,y)=>{{
      const p=x.cells[i].textContent.trim(),q=y.cells[i].textContent.trim();
      const a=parseFloat(p),c=parseFloat(q);
      if(!isNaN(a)&&!isNaN(c))return asc?a-c:c-a;return asc?p.localeCompare(q):q.localeCompare(p);
    }}).forEach(r=>b.appendChild(r));}});}});
}});
</script></body></html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--new-token", action="store_true", help="合言葉を作り直す")
    args = parser.parse_args()
    token = load_token(args.new_token)

    if OUT.exists():
        shutil.rmtree(OUT)
    site = OUT / token
    pages = build(token)
    for path, content in pages.items():
        target = site / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    (site / "sw.js").write_text(SW)
    (OUT / "index.html").write_text(BLANK)
    (OUT / "404.html").write_text(BLANK)
    (OUT / "robots.txt").write_text("User-agent: *\nDisallow: /\n")
    (OUT / "_headers").write_text(
        "/*\n  X-Robots-Tag: noindex, nofollow\n  Referrer-Policy: no-referrer\n"
    )
    size = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file()) / 1024 / 1024
    print(f"{len(pages)}ページ・{size:.1f}MB → {OUT}")
    print(f"入口: /{token}/index.html")


if __name__ == "__main__":
    main()
