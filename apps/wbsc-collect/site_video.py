#!/usr/bin/env python3
"""共有サイトの映像ページ（台湾の日本遠征の打席ごとの動画）。build_site.py から呼ぶ。

video_clips.py が作った打席の一覧（各試合の 打席.csv、なければ 打席_自動.csv）と、
書き出した動画（clips/<試合>/index.json）を読み、台湾の選手ごとのページを作る。
データは ~/野球/U23ワールドカップ2026/08_映像切り抜き/ にある（リポジトリの外）。

    pages(page_fn)        {URL: HTML}。team/chinese-taipei/v/<背番号>/ を、打席のある最終の24人に1つずつ
    team_section(root)    台湾の相手国ページに入れる節（選手と打席数のリンク）。映像がなければ空
    media()               サイトに置くファイル [(元のパス, サイトの根元からのパス)]
    player_link(name)     その選手の映像ページの URL（根元から）。なければ空

動画は Service Worker に保存させない（site_offline.py の sw.js が .mp4 を素通しにする）。
見出しは、行の headline（BASSと突き合わせたもの・確認用の画面で直したもの）があればそれ、
なければ実況の結果の言葉から仮に作り、ページに「仮」と出す。
"""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path

DATA = Path.home() / "野球" / "U23ワールドカップ2026" / "08_映像切り抜き"
TEAM_URL = "team/chinese-taipei/"
MEDIA = "media/tpe/"
POS = {"P": "投手", "C": "捕手", "IF": "内野手", "OF": "外野手"}

# 実況の結果の言葉 → 仮の見出しと、絞り込みの区分（hit 安打・out 凡打・k 三振と四死球・etc その他）
RESULT_WORDS = (
    (("ホームラン",), "本塁打", "hit"), (("3ベース", "スリーベース"), "三塁打", "hit"),
    (("2ベース", "ツーベース"), "二塁打", "hit"), (("ヒット", "安打"), "安打", "hit"),
    (("三振", "3振", "振り逃げ"), "三振", "k"), (("フォアボール", "四球"), "四球", "k"),
    (("デッドボール", "死球"), "死球", "k"), (("ダブルプレ", "ゲッツー", "併殺"), "併殺", "out"),
    (("犠牲フライ",), "犠飛", "out"), (("バント", "犠打"), "バント", "out"),
    (("エラー", "失策"), "失策", "etc"), (("フォースアウト",), "封殺", "out"),
    (("ゴロ", "ゴール"), "ゴロ", "out"), (("ライナー",), "ライナー", "out"), (("フライ",), "フライ", "out"),
)
KIND_OF = {label: kind for _, label, kind in RESULT_WORDS}
FILTERS = (("all", "全打席"), ("hit", "安打"), ("out", "凡打"), ("k", "三振・四死球"))


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


# ---------------------------------------------------------------- 読み込み


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load() -> dict | None:
    """試合・選手・打席・動画をまとめる。データがなければ None。"""
    games_file = DATA / "試合.json"
    if not games_file.is_file() or not (DATA / "選手.csv").is_file():
        return None
    games = json.loads(games_file.read_text(encoding="utf-8"))["games"]
    people = {p["name"]: p for p in _read_csv(DATA / "選手.csv")}
    clips: dict[str, list[dict]] = {}  # 選手の名前 → 打席（試合順）
    roles: dict[str, set] = {}
    for game in games:
        rows = []
        for name in ("打席.csv", "打席_自動.csv"):
            if (DATA / game["id"] / name).is_file():
                rows = _read_csv(DATA / game["id"] / name)
                break
        index_file = DATA / "clips" / game["id"] / "index.json"
        made = json.loads(index_file.read_text(encoding="utf-8")) if index_file.is_file() else {}
        for row in rows:
            got = made.get(str(row["no"]))
            if not got:
                continue
            tw_bat = row["bat_team"] == "台湾"
            who = row["batter"] if tw_bat else row["pitcher"]
            if who not in people or people[who].get("final24") != "1" or not people[who].get("number"):
                continue
            clips.setdefault(who, []).append({"game": game, "row": row, "clip": got, "batting": tw_bat})
            roles.setdefault(who, set()).add("bat" if tw_bat else "pit")
    if not clips:
        return None
    return {"games": games, "people": people, "clips": clips, "roles": roles}


_cache: dict = {}


def data() -> dict | None:
    if "d" not in _cache:
        _cache["d"] = load()
    return _cache["d"]


# ---------------------------------------------------------------- 見出し


def headline(row: dict) -> tuple[str, str, bool]:
    """(見出し, 区分, 仮か)。行に headline があればそれを使う。"""
    if (row.get("headline") or "").strip():
        text = row["headline"].strip()
        kind = next((KIND_OF[w] for w in KIND_OF if w in text), "etc")
        return text, kind, False
    words = row.get("results") or ""
    for keys, label, kind in RESULT_WORDS:
        if any(k in words for k in keys):
            return label, kind, True
    return "結果は確認中", "etc", True


def chips(row: dict, start: float) -> str:
    out = []
    for i, item in enumerate([p for p in (row.get("pitches") or "").split(";") if "|" in p], 1):
        t, label = item.split("|", 1)
        try:
            at = max(0.0, float(t) - start - 4)
        except ValueError:
            continue
        out.append(f'<button type="button" data-t="{at:.1f}">{i}球目<small>{esc(label)}</small></button>')
    return f'<div class="vchips">{"".join(out)}</div>' if out else ""


def md(date: str) -> str:
    _, m, d = date.split("-")
    return f"{int(m)}/{int(d)}"


# ---------------------------------------------------------------- ページ


def player_link(name: str) -> str:
    d = data()
    if not d or name not in d["clips"]:
        return ""
    return f"{TEAM_URL}v/{d['people'][name]['number']}/"


def card(item: dict, root: str) -> str:
    game, row, clip = item["game"], item["row"], item["clip"]
    text, kind, tentative = headline(row)
    half = "表" if row["half"] == "表" else "裏"
    if item["batting"]:
        vs = f'vs {esc(row["pitcher"] or "投手不明")}'
    else:
        vs = f'vs {esc(row["batter"] or "打者不明")}（{esc(row["order"])}番）'
    start = float(row["start"])
    secs = float(row["end"]) - start
    # 球数は、仮のうちは出さない（実況の1球ごとの言葉を拾えた数なので少なめになる）
    count = "" if tentative else f'{esc(row.get("n_pitch") or "0")}球・'
    mark = '<span class="vtent">仮</span>' if tentative else ""
    src = f"{root}{MEDIA}{game['id']}/{clip['file']}"
    poster = f"{root}{MEDIA}{game['id']}/{clip['jpg']}"
    return (f'<article class="vclip" data-kind="{kind}">'
            f'<h3>{esc(row["inning"])}回{half}　{esc(text)}{mark}</h3>'
            f'<p class="vmeta">{esc(md(game["date"]))} {esc(game["short"])}戦　{vs}　{count}{secs:.0f}秒</p>'
            f'<video controls playsinline preload="none" poster="{esc(poster)}" src="{esc(src)}"></video>'
            f'{chips(row, start)}</article>')


STYLE = """<style>
.vlist{display:grid;grid-template-columns:minmax(0,1fr);gap:12px;margin:10px 0}
@media (min-width:900px){.vlist{grid-template-columns:repeat(2,minmax(0,1fr))}}
.vclip{min-width:0;padding:10px 10px 8px;background:var(--card);border:1px solid var(--line);border-radius:12px}
.vclip h3{margin:0;font-size:16px;line-height:1.4}
.vmeta{margin:2px 0 6px;color:var(--dim);font-size:12px}
.vclip video{display:block;width:100%;aspect-ratio:16/9;background:#000;border-radius:8px}
.vchips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.vchips button{min-height:44px;padding:4px 9px;border:1px solid var(--line);border-radius:8px;background:var(--chip);
color:var(--text);font:inherit;font-size:12px;line-height:1.3;cursor:pointer}
.vchips small{display:block;color:var(--dim);font-size:11px}
.vtent{display:inline-block;margin-left:6px;padding:0 6px;border-radius:6px;background:var(--t-amber-bg);
color:var(--t-amber);font-size:11px;font-weight:700;vertical-align:2px}
.vgame{margin:18px 0 4px;font-size:15px}
.vfil{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}
.vfil button{min-height:44px;padding:0 14px;border:1px solid var(--line);border-radius:22px;background:var(--card);
color:var(--text);font:inherit;font-size:14px;cursor:pointer}
.vfil button[aria-pressed=true]{background:var(--ink);color:var(--ink-t);font-weight:700}
</style>"""

SCRIPT = """<script>
(function () {
  var main = document.currentScript.parentNode;
  main.querySelectorAll(".vclip").forEach(function (a) {
    var v = a.querySelector("video");
    a.querySelectorAll(".vchips button").forEach(function (b) {
      b.addEventListener("click", function () {
        var t = +b.getAttribute("data-t");
        var go = function () { v.currentTime = t; v.play(); };
        if (v.readyState >= 1) go(); else { v.preload = "metadata"; v.addEventListener("loadedmetadata", go, { once: true }); v.load(); }
      });
    });
    v.addEventListener("play", function () {  // 1本だけ鳴らす
      main.querySelectorAll("video").forEach(function (o) { if (o !== v && !o.paused) o.pause(); });
    });
  });
  var buttons = main.querySelectorAll(".vfil button");
  buttons.forEach(function (b) {
    b.addEventListener("click", function () {
      var k = b.getAttribute("data-f");
      buttons.forEach(function (o) { o.setAttribute("aria-pressed", o === b ? "true" : "false"); });
      main.querySelectorAll(".vclip").forEach(function (a) {
        a.hidden = k !== "all" && a.getAttribute("data-kind") !== k;
      });
      main.querySelectorAll(".vgame").forEach(function (h) {
        var n = h.nextElementSibling, any = false;
        n.querySelectorAll(".vclip").forEach(function (a) { if (!a.hidden) any = true; });
        h.hidden = n.hidden = !any;
      });
    });
  });
})();
</script>"""


def player_page(name: str, page_fn) -> str:
    d = data()
    person = d["people"][name]
    url = player_link(name)
    root = "../" * url.count("/")
    items = d["clips"][name]
    tentative = any(headline(i["row"])[2] for i in items)
    pos = POS.get(person.get("position"), "")
    hand = person.get("throws_bats") or ""
    hand_text = f"{hand[0]}投{hand[1]}打" if len(hand) == 2 else ""
    sub = "・".join(x for x in (f"背番号{person['number']}", pos, hand_text) if x)
    crumbs = (f'<a href="{root}teams/">相手国</a> / <a href="{root}{TEAM_URL}">チャイニーズタイペイ</a> / 映像')
    reading = f'<small class="yomi"> {esc(person.get("reading"))}</small>' if person.get("reading") else ""
    head = (f'<div class="page-head"><p class="crumbs">{crumbs}</p><h1>{esc(name)}{reading}</h1>'
            f'<p class="meta">{esc(sub)}　日本遠征（10/16〜21）の{len(items)}打席</p></div>')
    notes = ['<p class="note">打席ごとの動画です。押すと再生します（電波が要ります。動画は端末に保存されません）。'
             '下のボタンで、その球の少し前から再生します。</p>']
    if tentative:
        notes.append('<p class="note"><span class="vtent">仮</span> の見出しと1球ごとのボタンの言葉は、実況から自動で付けたものです。'
                     '聞き違いがあります。BASSの記録が入ったら正確なものに差し替えます。</p>')
    if any(i["game"].get("low_camera") and not i["batting"] for i in items):
        notes.append('<p class="note">西部ガス戦はバックネット裏の低い位置から撮っていて、投手が審判に隠れます。</p>')
    fil = '<div class="vfil" role="group" aria-label="結果で絞る">' + "".join(
        f'<button type="button" data-f="{k}" aria-pressed="{"true" if k == "all" else "false"}">{label}</button>'
        for k, label in FILTERS) + "</div>"
    blocks = []
    for game in d["games"]:
        mine = [i for i in items if i["game"]["id"] == game["id"]]
        if not mine:
            continue
        side = "先攻" if game["taiwan"] == "top" else "後攻"
        blocks.append(f'<h2 class="vgame">{esc(md(game["date"]))} {esc(game["opponent"])}戦'
                      f'<small>　{esc(game.get("score", ""))}・台湾は{side}</small></h2>'
                      f'<div class="vlist">{"".join(card(i, root) for i in mine)}</div>')
    body = head + "".join(notes) + fil + STYLE + "".join(blocks) + SCRIPT
    return page_fn(f"{name}の映像", body, url, "teams", "fe")


def pages(page_fn) -> dict[str, str]:
    d = data()
    if not d:
        return {}
    return {player_link(name): player_page(name, page_fn) for name in d["clips"]}


def team_section(root: str) -> str:
    """台湾の相手国ページの節。投手と野手に分けたカード。"""
    d = data()
    if not d:
        return ""

    def cards(kind: str) -> str:
        names = [n for n in d["clips"] if (kind == "pit") == (d["people"][n]["position"] == "P")]
        names.sort(key=lambda n: int(d["people"][n]["number"]))
        out = []
        for n in names:
            count = sum(1 for i in d["clips"][n] if i["batting"] == (kind == "bat"))
            text = f"{count}打者と対戦" if kind == "pit" else f"{count}打席"
            out.append(f'<a class="pcard" href="{root}{player_link(n)}"><span class="num">{esc(d["people"][n]["number"])}</span>'
                       f'<b class="nm">{esc(n)}</b><small class="sub">{text}</small></a>')
        return f'<div class="pgrid">{"".join(out)}</div>'

    total = sum(len(v) for v in d["clips"].values())
    lead = (f'<p class="note">10/16〜21の日本遠征5試合（社会人チームとの練習試合）を、打席ごとの動画にしました（{total}本）。'
            "選手を押すと、その選手の打席（投手は投げた打席）が並びます。</p>")
    return (f'<section id="video"><h2>日本遠征の打席の映像</h2>{lead}'
            f'<h3 class="vgame">投手</h3>{cards("pit")}<h3 class="vgame">野手</h3>{cards("bat")}</section>')


def media() -> list[tuple[Path, str]]:
    """サイトに置く動画とサムネイル。[(元のパス, 根元からのパス)]"""
    d = data()
    if not d:
        return []
    out, seen = [], set()
    for items in d["clips"].values():
        for i in items:
            gid = i["game"]["id"]
            for key in ("file", "jpg"):
                name = i["clip"][key]
                if (gid, name) in seen:
                    continue
                seen.add((gid, name))
                out.append((DATA / "clips" / gid / name, f"{MEDIA}{gid}/{name}"))
    return out
