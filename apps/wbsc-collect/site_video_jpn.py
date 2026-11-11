#!/usr/bin/env python3
"""共有サイトの映像ページ（日本代表の今大会の打席ごとの動画）。build_site.py と site_japan.py から呼ぶ。

gt_clips.py web JPN が作った動画と一覧（11_日本代表_大会映像/web/<背番号>/index.json）を読み、選手ごとのページを作る。
データはリポジトリの外にある。

    pages(page_fn)        {URL: HTML}。japan/v/<背番号>/ を、動画のある選手に1つずつ
    player_url(number)    その選手の映像ページの URL（根元から）。なければ空
    count(number)         その選手の動画の打席数
    section_html(root)    日本代表のページに入れる節（選手と打席数のリンク）。動画がなければ空
    media()               サイトに置くファイル [(元のパス, サイトの根元からのパス)]

動画の再生と絞り込みは site_video.py の部品を使う。新しい試合を上に並べる（試合のあとに見返すため）。
"""

from __future__ import annotations

import json
from pathlib import Path

from site_video import SCRIPT, STYLE, esc

DATA = Path.home() / "野球" / "U23ワールドカップ2026" / "11_日本代表_大会映像" / "web"
MEDIA = "media/jpn/"
HALF = {"top": "表", "bot": "裏"}
EXTRA_STYLE = "<style>.vjpn .vclip video{aspect-ratio:960/588}.vnote{margin:6px 0 0;color:var(--dim);font-size:12px}</style>"

_cache: dict = {}


def data() -> dict[str, dict]:
    """背番号 → その選手の一覧。動画のある選手だけ。"""
    if "d" not in _cache:
        out = {}
        for path in sorted(DATA.glob("*/index.json")) if DATA.is_dir() else []:
            item = json.loads(path.read_text(encoding="utf-8"))
            if item.get("at_bats"):
                item["folder"] = path.parent
                out[item["num"]] = item
        _cache["d"] = out
    return _cache["d"]


def player_url(number: str) -> str:
    return f"japan/v/{number}/" if str(number) in data() else ""


def count(number: str) -> int:
    person = data().get(str(number))
    return len(person["at_bats"]) if person else 0


def unit(person: dict) -> str:
    return "打者" if person["role"] == "投手" else "打席"


def side_word(person: dict, side: str) -> str:
    who = "打者" if person["role"] == "投手" else "投手"
    return {"L": f"左{who}", "R": f"右{who}"}.get(side, "")


def chips(item: dict) -> str:
    if len(item["chips"]) < 2:
        return ""
    out = "".join(f'<button type="button" data-t="{c["t"]:.1f}">{c["k"]}球目<small>{esc(c["label"])}</small></button>'
                  for c in item["chips"])
    return f'<div class="vchips">{out}</div>'


def card(item: dict, person: dict, root: str) -> str:
    base = f'{root}{MEDIA}{person["num"]}/'
    res = item["res"] or item["chips"][-1]["label"] or "結果の記録なし"
    side = side_word(person, item["side"])
    vs = f'vs {esc(item["other"])}' + (f"（{side}）" if side else "")
    gap = f'（最初の{item["missing"]}球は映像なし）' if item["missing"] else ""
    note = f'<p class="vnote">{esc(item["note"])}</p>' if item["note"] else ""
    return (f'<article class="vclip" data-kind="{item["side"].lower()} {item["kind"]}">'
            f'<h3>{item["inning"]}回{HALF[item["half"]]}　{esc(res)}</h3>'
            f'<p class="vmeta">{vs}　{item["n"]}球{gap}・{item["secs"]}秒</p>'
            f'<video controls playsinline preload="none" poster="{esc(base + item["jpg"])}" src="{esc(base + item["file"])}"></video>'
            f"{chips(item)}{note}</article>")


def player_page(person: dict, page_fn) -> str:
    number = person["num"]
    url = f"japan/v/{number}/"
    root = "../" * url.count("/")
    items = person["at_bats"]
    games = sorted({i["mmdd"] for i in items}, reverse=True)
    crumbs = (f'<a href="{root}japan/">日本代表</a> / <a href="{root}japan/p/{number}/">背番号{esc(number)}</a> / 映像')
    head = (f'<div class="page-head"><p class="crumbs">{crumbs}</p><h1><span class="num">{esc(number)}</span> {esc(person["name"])}</h1>'
            f'<p class="meta">{esc(person["role"])}・今大会 {len(games)}試合 {len(items)}{unit(person)}</p></div>')
    notes = ['<p class="note">打席ごとの動画です。押すと再生します（電波が要ります。動画は端末に保存されません）。'
             "下のボタンで、その球の少し前から再生します。</p>"]
    for label, n in person.get("no_video", {}).items():
        if "韓国" in label:
            notes.append(f'<p class="note">{esc(label)}は4回裏2死より前の映像がなく、{n}{unit(person)}ぶんは動画がありません。</p>')
    who = "打者" if person["role"] == "投手" else "投手"
    filters = (("all", "すべて"), ("l", f"対左{who}"), ("r", f"対右{who}"), ("hit", "安打"), ("out", "凡打"), ("k", "三振・四死球"))
    fil = '<div class="vfil" role="group" aria-label="絞り込み">' + "".join(
        f'<button type="button" data-f="{k}" aria-pressed="{"true" if k == "all" else "false"}">{label}</button>'
        for k, label in filters) + "</div>"
    blocks = []
    for mmdd in games:
        mine = [i for i in items if i["mmdd"] == mmdd]
        blocks.append(f'<h2 class="vgame">{esc(mine[0]["date"])} {esc(mine[0]["rival"])}<small>　{len(mine)}{unit(person)}</small></h2>'
                      f'<div class="vlist">{"".join(card(i, person, root) for i in mine)}</div>')
    body = f'<div class="vjpn">{head}{"".join(notes)}{fil}{STYLE}{EXTRA_STYLE}{"".join(blocks)}{SCRIPT}</div>'
    return page_fn(f'{person["name"]}の映像', body, url, "japan", "fe")


def pages(page_fn) -> dict[str, str]:
    return {f"japan/v/{num}/": player_page(person, page_fn) for num, person in data().items()}


def section_html(root: str) -> str:
    """日本代表のページの節。投手と打者に分けたカード。"""
    people = sorted(data().values(), key=lambda p: int(p["num"]))
    if not people:
        return ""

    def cards(role: str) -> str:
        out = "".join(f'<a class="pcard" href="{root}japan/v/{p["num"]}/"><span class="num">{esc(p["num"])}</span>'
                      f'<b class="nm">{esc(p["name"])}</b><small class="sub">{len(p["at_bats"])}{unit(p)}</small></a>'
                      for p in people if p["role"] == role)
        return f'<div class="pgrid">{out}</div>'

    return (f'<h3 class="vgame">投手</h3>{cards("投手")}<h3 class="vgame">打者</h3>{cards("打者")}')


def media() -> list[tuple[Path, str]]:
    """サイトに置く動画とサムネイル。[(元のパス, 根元からのパス)]"""
    out = []
    for num, person in data().items():
        for item in person["at_bats"]:
            for key in ("file", "jpg"):
                out.append((person["folder"] / item[key], f"{MEDIA}{num}/{item[key]}"))
    return out
