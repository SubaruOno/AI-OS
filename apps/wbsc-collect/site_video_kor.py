#!/usr/bin/env python3
"""共有サイトの映像ページ（韓国の投手のKBO1軍の打席ごとの動画）。build_site.py から呼ぶ。

kbo_pitcher_reel.py web が作った動画と一覧（投手別映像/web/<投手>/index.json）を読み、投手ごとのページを作る。
データは ~/野球/U23ワールドカップ2026/04_対戦国/韓国/投手別映像/ にある（リポジトリの外）。

    pages(page_fn)        {URL: HTML}。team/korea/v/<投手>/ を、動画のある投手に1つずつ
                          全打席の欄は新しい順に RECENT_LIMIT 打席まで
    team_section(root)    韓国の相手国ページに入れる節（投手のリンク）。映像がなければ空
    media()               サイトに置くファイル [(元のパス, サイトの根元からのパス)]

ページは「左右別まとめ・奪三振集・全打席」を切り替えて見る。動画の再生と絞り込みは site_video.py の部品を使う。
何球目かは読み違いが出るので出さない。1球ごとのボタンには、中継の表示から読めた球速と球種だけを書く。
"""

from __future__ import annotations

import json
from pathlib import Path

from site_video import SCRIPT, STYLE, esc

DATA = Path.home() / "野球" / "U23ワールドカップ2026" / "04_対戦国" / "韓国" / "投手別映像" / "web"
TEAM_URL = "team/korea/"
MEDIA = "media/kor/"
HAND = {"우": "右打", "좌": "左打", "양": "両打"}
KIND = {"安打": "hit", "凡打": "out", "三振": "k", "四死球": "k"}
# 全打席の欄に載せる打席の数（新しい順）。원종혁の84打席などは多すぎるので絞る（11/3 すばるの判断）
RECENT_LIMIT = 30
FILTERS = (("all", "すべて"), ("l", "対左"), ("r", "対右"), ("hit", "安打"), ("out", "凡打"), ("k", "三振・四死球"))
TABS = ("sides", "k", "all")

EXTRA_STYLE = """<style>
.vkor .vclip video{aspect-ratio:960/588}
.vtabs{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0 4px}
.vtabs button{flex:1 1 auto;min-height:44px;padding:0 12px;border:1px solid var(--line);border-radius:10px;background:var(--card);
color:var(--text);font:inherit;font-size:14px;font-weight:600;cursor:pointer}
.vtabs button[aria-selected=true]{background:var(--ink);color:var(--ink-t);font-weight:700}
.vchips b{font-weight:600}
</style>"""

TAB_SCRIPT = """<script>
(function () {
  var main = document.currentScript.parentNode;
  var tabs = main.querySelectorAll(".vtabs button");
  var panels = main.querySelectorAll("[data-tab]");
  var show = function (name) {
    tabs.forEach(function (b) { b.setAttribute("aria-selected", b.getAttribute("data-open") === name ? "true" : "false"); });
    panels.forEach(function (p) {
      var on = p.getAttribute("data-tab") === name;
      p.hidden = !on;
      if (on) {  // サムネイルは開いた欄の分だけ読む（電波の弱い所で全打席分を読まない）
        p.querySelectorAll("video[data-poster]").forEach(function (v) {
          v.poster = v.getAttribute("data-poster");
          v.removeAttribute("data-poster");
        });
      } else {
        p.querySelectorAll("video").forEach(function (v) { if (!v.paused) v.pause(); });
      }
    });
  };
  tabs.forEach(function (b) {
    b.addEventListener("click", function () { show(b.getAttribute("data-open")); });
  });
  show(tabs[0].getAttribute("data-open"));
})();
</script>"""


# ---------------------------------------------------------------- 読み込み


def load() -> list[dict]:
    """投手ごとの一覧を、対戦した打者の多い順に返す。データがなければ空。"""
    out = []
    if DATA.is_dir():
        for path in sorted(DATA.glob("*/index.json")):
            item = json.loads(path.read_text(encoding="utf-8"))
            item["folder"] = path.parent
            out.append(item)
    return sorted(out, key=lambda p: -len(p["at_bats"]))


_cache: dict = {}


def data() -> list[dict]:
    if "d" not in _cache:
        _cache["d"] = load()
    return _cache["d"]


# ---------------------------------------------------------------- ページ


def page_url(person: dict) -> str:
    return f"{TEAM_URL}v/{person['slug']}/"


def md(date: str) -> str:
    return f"{int(date[:2])}/{int(date[3:])}"


def video_tag(src: str, poster: str) -> str:
    return f'<video controls playsinline preload="none" data-poster="{esc(poster)}" src="{esc(src)}"></video>'


def scene_chips(item: dict) -> str:
    """場面ごとのボタン。押すと、その場面の頭から流す。読めた球速と球種だけを書く。"""
    out = []
    for scene in item["scenes"]:
        head = f'{esc(scene["kmh"])}km/h' if scene["kmh"] else "球速なし"
        out.append(f'<button type="button" data-t="{scene["t"]:.1f}"><b>{head}</b><small>{esc(scene["kind"]) or "&nbsp;"}</small></button>')
    return f'<div class="vchips">{"".join(out)}</div>' if len(out) > 1 else ""


def at_bat_card(item: dict, root: str, base: str) -> str:
    side = "r" if item["hand"] == "우" else "l"
    kind = KIND.get(item["class"], "out")
    result = esc(item["result"]) or "結果なし"
    return (f'<article class="vclip" data-kind="{side} {kind}">'
            f'<h3>{esc(item["inning"])}　{result}</h3>'
            f'<p class="vmeta">{md(item["date"])} {esc(item["opp"])}戦　vs {esc(item["batter"])}（{HAND.get(item["hand"], "")}）　{item["pitches"]}球</p>'
            f'{video_tag(root + base + item["file"], root + base + item["jpg"])}{scene_chips(item)}</article>')


def strikeout_card(item: dict, root: str, base: str) -> str:
    extra = "　".join(x for x in (f'{item["k_kmh"]}km/h' if item["k_kmh"] else "", item["k_kind"]) if x)
    return (f'<article class="vclip"><h3>{esc(item["k_word"])}</h3>'
            f'<p class="vmeta">{md(item["date"])} {esc(item["opp"])}戦 {esc(item["inning"])}　vs {esc(item["batter"])}（{HAND.get(item["hand"], "")}）'
            f'{"　" + esc(extra) if extra else ""}</p>'
            f'{video_tag(root + base + item["k_file"], root + base + item["k_jpg"])}</article>')


def recent(person: dict) -> list[dict]:
    """全打席の欄に載せる打席。一覧は新しい試合から並んでいる。"""
    return person["at_bats"][:RECENT_LIMIT]


def grid(title: str, cards: list[str]) -> str:
    return f'<h2 class="vgame">{esc(title)}</h2><div class="vlist">{"".join(cards)}</div>' if cards else ""


def player_page(person: dict, page_fn) -> str:
    url = page_url(person)
    root = "../" * url.count("/")
    base = f'{MEDIA}{person["slug"]}/'
    items = person["at_bats"]
    by_key = {(i["game"], i["no"]): i for i in items}
    style = f'・{person["style"]}' if person.get("style") else ""
    sub = f'{person["club"]}・{person["throw"]}投げ{style}　2026年KBO1軍 {person["games"]}試合 {len(items)}打者'
    crumbs = f'<a href="{root}teams/">相手国</a> / <a href="{root}{TEAM_URL}">韓国</a> / 映像'
    head = (f'<div class="page-head"><p class="crumbs">{crumbs}</p><h1>{esc(person["player"])}<small class="yomi"> {esc(person["kana"])}</small></h1>'
            f'<p class="meta">{esc(sub)}</p></div>')
    notes = ('<p class="note">KBOの中継から投球の場面だけを抜いた動画です。押すと再生します（電波が要ります。動画は端末に保存されません）。'
             '音はありません。カウントと累計球数は中継の画面を見てください。</p>'
             '<p class="note">下のボタンで、その球の少し前から再生します。球速と球種は中継の表示を読んだもので、球種は中継によって出ません。'
             '球速の出なかった場面には、投球の映っていないものが少し混ざります。</p>')

    sides = ""
    for name, key in (("対 左打者", "left"), ("対 右打者", "right")):
        chosen = [by_key[tuple(k)] for k in person["sides"][key]]
        sides += grid(f"{name}（{len(chosen)}打席）", [at_bat_card(i, root, base) for i in chosen])
    strikeouts = [i for i in items if "k_file" in i]
    kay = ""
    for name, test in (("対 左打者", lambda i: i["hand"] != "우"), ("対 右打者", lambda i: i["hand"] == "우")):
        mine = [i for i in strikeouts if test(i)]
        kay += grid(f"{name}（{len(mine)}個）", [strikeout_card(i, root, base) for i in mine])
    fil = '<div class="vfil" role="group" aria-label="絞り込み">' + "".join(
        f'<button type="button" data-f="{k}" aria-pressed="{"true" if k == "all" else "false"}">{label}</button>'
        for k, label in FILTERS) + "</div>"
    games = ""
    shown = recent(person)
    for game in dict.fromkeys(i["game"] for i in shown):
        mine = [i for i in shown if i["game"] == game]
        games += grid(f'{md(mine[0]["date"])} {mine[0]["opp"]}戦', [at_bat_card(i, root, base) for i in mine])

    many = len(shown) < len(items)
    labels = {"sides": "左右別まとめ", "k": f"奪三振集（{len(strikeouts)}）",
              "all": f"最近の{len(shown)}打席" if many else f"全打席（{len(items)}）"}
    tabs = '<div class="vtabs" role="tablist">' + "".join(
        f'<button type="button" role="tab" data-open="{k}" aria-selected="false">{labels[k]}</button>' for k in TABS) + "</div>"
    lead = f'<p class="note">{len(items)}打席のうち、新しい{len(shown)}打席です。</p>' if many else ""
    panels = (f'<section data-tab="sides" hidden>{sides}</section><section data-tab="k" hidden>{kay}</section>'
              f'<section data-tab="all" data-vscope hidden>{lead}{fil}{games}</section>')
    body = (f'<div class="vkor">{head}{notes}{STYLE}{EXTRA_STYLE}{tabs}{panels}{TAB_SCRIPT}{SCRIPT}</div>')
    return page_fn(f'{person["player"]}の映像', body, url, "teams", "fe")


def pages(page_fn) -> dict[str, str]:
    return {page_url(p): player_page(p, page_fn) for p in data()}


def team_section(root: str) -> str:
    """韓国の相手国ページの節。動画のある投手のカード。"""
    people = data()
    if not people:
        return ""
    cards = "".join(
        f'<a class="pcard" href="{root}{page_url(p)}"><b class="nm">{esc(p["player"])}</b>'
        f'<small class="sub">{esc(p["kana"])}・{len(p["at_bats"])}打者</small></a>' for p in people)
    lead = ('<p class="note">今季KBOの1軍で投げた投手の、投球の場面だけを抜いた動画です。投手を押すと、'
            '左右別まとめ・奪三振集・全打席を切り替えて見られます。1軍で投げていない投手の映像はありません。</p>')
    return f'<section id="video"><h2>KBOの投球の映像</h2>{lead}<div class="pgrid">{cards}</div></section>'


def media() -> list[tuple[Path, str]]:
    """サイトに置く動画とサムネイル。[(元のパス, 根元からのパス)]"""
    out = []
    for person in data():
        chosen = {tuple(k) for side in person["sides"].values() for k in side}
        shown = {(i["game"], i["no"]) for i in recent(person)}
        for item in person["at_bats"]:
            keys = ["k_file", "k_jpg"] if "k_file" in item else []
            if (item["game"], item["no"]) in chosen | shown:
                keys += ["file", "jpg"]
            for key in keys:
                out.append((person["folder"] / item[key], f'{MEDIA}{person["slug"]}/{item[key]}'))
    return out
