"""日本代表（自チーム）のページを作る。

build_site.py から build_japan(d, page) で呼ぶ。戻り値は {URL: ページのHTML全体}。

    japan/              自チームの入口（次の日本戦・選手カード・入口のタイル・日程・成績）
    japan/pitching/     投手の登板表（球数・投球回・中何日）
    japan/p/<背番号>/   選手1人のページ

WBSCの記録の日本の選手とは、team が Japan の行の uniform（背番号）で結び付ける
（記録の名前はローマ字なので、公式発表の漢字の名前とは突き合わせられない）。
載せるのは侍ジャパン公式の発表にある項目だけ。生年月日と出身校は載せない。
build_site を import すると循環するので、必要な小さな道具はここに書く。
"""

from __future__ import annotations

import html
import urllib.parse
from datetime import date, timedelta, timezone

import build_report as br
import collect
import site_logic as sl

CURRENT = "u23-wc-2026"
JAPAN = "Japan"
WBSC_DOMAIN, WBSC_SLUG, _ = collect.EVENTS[CURRENT]
OFFICIAL_JAPAN = "https://www.japan-baseball.jp/jp/news/press/20261006_1.html"
JA = {team: label for label, team, _, _ in br.OPPONENTS}
WEEK = "月火水木金土日"
TOWN = {"Managua": "マナグア", "Masaya": "マサヤ", "León": "レオン", "Leon": "レオン"}
ROUND_TAG = (("Opening Round", "1次R", "op"), ("Super Round", "SR", "sup"),
             ("Placement Round", "順位決定", "pl"), ("Bronze", "3位決定", "md"),
             ("Final", "決勝", "md"))
POS_ORDER = ("投手", "捕手", "内野手", "外野手")
PLACEHOLDER = {"", "TBD", "TBA"}
GAME_HOURS = 4  # 次の日本戦の帯で、始まってから何時間は「次の試合」として出し続けるか
LOCK_TEXT = "準備中です。トラックマン・ラプソード・BLASTの数字を、パスワードで保護して載せます。"
NO_LIMIT = ("U-23W杯には球数制限がありません（WBSC Official Rules 2025-2026 A1.8.4）。"
            "起用の判断の材料として使ってください。")


# ---------------------------------------------------------------- 小さな道具


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""))


def ext(url, text) -> str:
    """外部へのリンク。http・https のURLだけ。参照元は送らない。"""
    href = str(url or "").strip()
    if not href.lower().startswith(("https://", "http://")) or any(c in href for c in " \"'<>"):
        return ""
    return (f'<a class="ext" href="{esc(href)}" target="_blank" rel="noreferrer noopener">'
            f"{esc(text)}</a>")


def md(moment) -> str:
    return f"{moment.month}/{moment.day}({WEEK[moment.weekday()]})"


def iso_md(text) -> str:
    """'2026-11-07' を '11/7(土)' にする。読めなければ '-'。"""
    try:
        return md(date.fromisoformat(str(text)[:10]))
    except (ValueError, AttributeError):
        return "-"


def number_key(value) -> str:
    """背番号をそろえる（"07" と "7" を同じにする）。数字でなければそのまま。"""
    text = str(value if value is not None else "").strip()
    if text.endswith(".0"):
        text = text[:-2]
    return str(int(text)) if text.isdigit() else text


def team_name(team) -> str:
    if team == JAPAN:
        return "日本"
    if str(team or "").strip().upper() in PLACEHOLDER:
        return "未定"
    return JA.get(team, team or "")


def team_link(team, root: str) -> str:
    if team in JA:
        return f'<a href="{root}team/{team.replace(" ", "-").lower()}/">{esc(JA[team])}</a>'
    return esc(team_name(team))


def venue(game: dict) -> str:
    stadium = str(game.get("stadium") or "").replace("Estadio ", "")
    place = str(game.get("location") or "")
    return "・".join(x for x in (stadium, TOWN.get(place, place)) if x)


def tag(game: dict) -> str:
    label = str(game.get("gametypelabel") or "")
    for word, text, css in ROUND_TAG:
        if word in label:
            return f'<span class="tag {css}">{text}</span>'
    return f'<span class="tag">{esc(label)}</span>' if label else ""


def mark_html(mark) -> str:
    css = {"○": "w", "●": "l", "△": "t"}.get(mark or "")
    return f'<span class="mk {css}">{mark}</span>' if css else ""


def box_url(game_id) -> str:
    game = urllib.parse.quote(str(game_id), safe="")
    return collect.event_url(WBSC_DOMAIN, WBSC_SLUG, f"schedule-and-results/box-score/{game}")


def when_parts(game: dict) -> tuple[str, str]:
    """（日本時間の「11/7(土) 08:00」, 現地の「11/6(金) 17:00」）。"""
    jst, local = sl.jst_dt(game), sl.local_dt(game)
    return f"{md(jst)} {jst:%H:%M}", f"{md(local)} {local:%H:%M}"


def lock(title: str = "計測データ") -> str:
    return f'<div class="lock"><b>{esc(title)}</b><p>{LOCK_TEXT}</p></div>'


def head(crumbs: list[tuple[str, str]], title: str, meta: str) -> str:
    """page-head。crumbs は [(href, 文字)]。href が空なら今いるページ。"""
    parts = [f'<a href="{esc(h)}">{esc(t)}</a>' if h else esc(t) for h, t in crumbs]
    return (f'<div class="page-head"><p class="crumbs">{" / ".join(parts)}</p>'
            f"<h1>{title}</h1><p class=\"meta\">{meta}</p></div>")


def section(anchor: str, title: str, body: str) -> str:
    return f'<section id="{anchor}"><h2>{title}</h2>{body}</section>'


def table(columns: list[str], rows: list[list[str]], cls: str = "plain") -> str:
    """セルの中身はエスケープ済みの文字列で渡す。"""
    head_row = "".join(f'<th scope="col">{esc(c)}</th>' for c in columns)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return (f'<div class="scroll"><table class="{cls}"><thead><tr>{head_row}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


# ---------------------------------------------------------------- データの整理


def japan_games(d: dict) -> list[dict]:
    return [g for g in d.get("games") or []
            if JAPAN in (g.get("homelabel"), g.get("awaylabel")) and sl.local_dt(g)]


def rows_of(d: dict, kind: str) -> list[dict]:
    current = (d.get("events") or {}).get(CURRENT) or {}
    return [r for r in current.get(kind) or [] if r.get("team") == JAPAN]


def roster(d: dict) -> tuple[list[dict], list[dict]]:
    rows = d.get("japan") or []
    players = [r for r in rows if r.get("role") == "選手"]
    players.sort(key=lambda r: int(br.number(r.get("number"))))
    staff = [r for r in rows if r.get("role") and r.get("role") != "選手"]
    return players, staff


class Record:
    """今大会の日本の記録を、背番号で引けるようにまとめたもの。"""

    def __init__(self, d: dict):
        self.bat_rows = rows_of(d, "batting")
        self.pit_rows = rows_of(d, "pitching")
        self.pid_number: dict[str, str] = {}
        for row in self.bat_rows + self.pit_rows:
            self.pid_number[str(row.get("playerid"))] = number_key(row.get("uniform"))
        self.bat = {self.pid_number.get(e["_id"], ""): e
                    for e in br.collect_batters(self.bat_rows, JAPAN)}
        self.pit = {self.pid_number.get(e["_id"], ""): e
                    for e in br.collect_pitchers(self.pit_rows, JAPAN)}
        self.started = bool(self.bat_rows or self.pit_rows)

    def pid_of(self, number: str) -> str:
        return next((pid for pid, n in self.pid_number.items() if n == number), "")

    def games_of(self, kind: str, number: str) -> list[dict]:
        rows = self.bat_rows if kind == "batting" else self.pit_rows
        return [r for r in rows if number_key(r.get("uniform")) == number]


def roster_names(d: dict) -> dict[str, str]:
    players, _ = roster(d)
    return {number_key(r.get("number")): str(r.get("name") or "") for r in players}


def starters(d: dict, names: dict[str, str]) -> dict[tuple[str, str], str]:
    """{(試合ID, チーム): 先発の名前}。日本の投手は公式発表の名前にする。"""
    current = (d.get("events") or {}).get(CURRENT) or {}
    out = {}
    for row in current.get("pitching") or []:
        if int(br.number(row.get("pitch_gs"))):
            name = br.name_of(row)
            if row.get("team") == JAPAN:
                name = names.get(number_key(row.get("uniform"))) or name
            out[(str(row.get("gameid")), row.get("team"))] = name
    return out


# ---------------------------------------------------------------- 日本戦の日程


def state_label(game: dict, state: str) -> str:
    innings = int(br.number(game.get("innings")))
    if state == "final" and innings and innings != 7:
        return f' <span class="inn">{innings}回</span>'
    if state == "live":
        return ' <span class="live">試合中</span>'
    if state == "other":
        return f' <span class="live">{esc(game.get("gamestatustext") or "中止・延期など")}</span>'
    if state == "unknown":
        text = esc(str(game.get("gamestatustext") or "").strip())
        return f' <span class="st" title="{text}">状態: {text}</span>'
    return ""


def game_row(game: dict, root: str, table_of_starters: dict) -> str:
    seen = sl.japan_view(game) or {}
    state = seen.get("state") or sl.game_state(game)
    jst, local = when_parts(game)
    score = seen.get("score") or "vs"
    text = (f'{mark_html(seen.get("mark"))}<b>日本</b> <span class="sc">{esc(score)}</span> '
            f'{team_link(seen.get("opponent"), root)}{state_label(game, state)}')
    sub = [esc(venue(game)), f'<span class="nw">日本は{esc(seen.get("batting", ""))}</span>']
    if state == "final":
        gid = str(game.get("id"))
        mine = table_of_starters.get((gid, JAPAN))
        theirs = table_of_starters.get((gid, seen.get("opponent")))
        if mine or theirs:
            sub.append(esc(f"先発 {mine or '?'}（相手 {theirs or '?'}）"))
    links = [ext(box_url(game["id"]), "速報・ボックス")] if game.get("id") else []
    if game.get("gamevideo"):
        links.append(ext(game["gamevideo"], "試合の映像"))
    return (f'<tr class="jp"><td class="t"><b>{jst}</b><small>現地 {local}</small></td>'
            f'<td class="m">{tag(game)}{text}<small>{"・".join(x for x in sub if x)}</small>'
            f'<small class="lk">{" ".join(x for x in links if x)}</small></td></tr>')


def games_table(d: dict, root: str, table_of_starters: dict) -> str:
    rows = [game_row(g, root, table_of_starters) for g in japan_games(d)]
    if not rows:
        return '<p class="empty">日本戦の日程がまだありません。</p>'
    return ('<div class="gwrap"><table class="games"><thead><tr><th>日本時間</th><th>試合</th>'
            f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def win_loss(d: dict) -> tuple[int, int, int]:
    marks = [(sl.japan_view(g) or {}).get("mark") for g in japan_games(d)]
    return marks.count("○"), marks.count("●"), marks.count("△")


# ---------------------------------------------------------------- 次の日本戦の帯


def next_block(d: dict, root: str) -> str:
    """終わっていない日本戦を順に並べ、開いたときのJSで「今の次」を選ぶ（JSなしは最初の1つ）。"""
    ahead = [g for g in japan_games(d) if not sl.is_settled(g)]
    items = []
    for i, game in enumerate(ahead):
        seen = sl.japan_view(game) or {}
        rival = seen.get("opponent")
        jst, local = when_parts(game)
        start = sl.local_dt(game).astimezone(timezone.utc)
        until = (start + timedelta(hours=GAME_HOURS)).strftime("%Y-%m-%dT%H:%M:%SZ")
        href = f'{root}team/{rival.replace(" ", "-").lower()}/' if rival in JA else f"{root}schedule/"
        live = ' <span class="live">試合中</span>' if seen.get("state") == "live" else ""
        items.append(
            f'<a class="hero jp-next" href="{esc(href)}" data-until="{until}"{" hidden" if i else ""}>'
            f'<small>次の日本戦 {tag(game)}{live}</small>'
            f'<b class="big">日本 vs {esc(team_name(rival))}</b>'
            f'<small><b>{jst}</b> 日本時間・現地 {local}</small>'
            f'<small>{esc(venue(game))}・日本は{esc(seen.get("batting", ""))}</small></a>')
    finals = [g for g in d.get("games") or [] if "Final" in str(g.get("gametypelabel"))]
    if finals and all(sl.is_settled(g) for g in finals):
        after = "大会のすべての試合が終わりました。"
    else:
        after = ("次の日本戦は、日程に載りしだいここに出ます（スーパーラウンドと順位決定ラウンドの"
                 "相手は1次ラウンドの結果で決まります）。")
    none = f'<p class="empty" id="jp-next-none"{" hidden" if items else ""}>{after}</p>'
    script = ("<script>(function(){var q=new URLSearchParams(location.search).get('now');"
              "var n=q?Date.parse(q):Date.now();if(isNaN(n))n=Date.now();"
              "var a=document.querySelectorAll('.jp-next'),s=null;"
              "a.forEach(function(e){if(!s&&Date.parse(e.getAttribute('data-until'))>n)s=e;});"
              "a.forEach(function(e){e.hidden=e!==s;});"
              "var z=document.getElementById('jp-next-none');if(z)z.hidden=!!s;})();</script>")
    return "".join(items) + none + (script if items else "")


# ---------------------------------------------------------------- 選手カード


def hand_text(row: dict) -> str:
    return f'{row.get("throws") or "?"}投{row.get("bats") or "?"}打'


def kv(label: str, value) -> str:
    return f'<span class="kv"><i>{esc(label)}</i><em>{esc(value)}</em></span>'


def card_numbers(row: dict, rec: Record) -> str:
    if not rec.started:
        return ""
    number = number_key(row.get("number"))
    if row.get("position") == "投手":
        entry = rec.pit.get(number)
        if not entry:
            return kv("登板", "なし")
        return kv("防御率", entry["防御率"]) + kv("投球回", entry["投球回"])
    entry = rec.bat.get(number)
    if not entry or not entry["打席"]:
        return kv("出場", "なし")
    return kv("打率", entry["打率"]) + kv("打点", entry["打点"])


def player_card(row: dict, rec: Record, href: str) -> str:
    number = number_key(row.get("number"))
    sub = "・".join(x for x in (hand_text(row), row.get("position"), row.get("club")) if x)
    return (f'<a class="pcard" href="{esc(href)}"><span class="num">{esc(number)}</span>'
            f'<b class="nm">{esc(row.get("name"))}</b><small class="sub">{esc(sub)}</small>'
            f"{card_numbers(row, rec)}</a>")


def player_cards(players: list[dict], rec: Record) -> str:
    pitchers = [r for r in players if r.get("position") == "投手"]
    fielders = [r for r in players if r.get("position") != "投手"]

    def grid(rows: list[dict]) -> str:
        cards = "".join(player_card(r, rec, f'p/{number_key(r.get("number"))}/') for r in rows)
        return f'<div class="pgrid">{cards}</div>'

    by_pos = "".join(
        f"<h3>{pos}<small>{len(rows)}人</small></h3>{grid(rows)}"
        for pos in POS_ORDER[1:]
        for rows in [[r for r in fielders if r.get("position") == pos]] if rows)
    others = [r for r in fielders if r.get("position") not in POS_ORDER]
    if others:
        by_pos += f"<h3>その他<small>{len(others)}人</small></h3>{grid(others)}"
    return ('<div class="seg" role="tablist" aria-label="選手の区分">'
            f'<button type="button" role="tab" aria-selected="true" data-seg="p">投手 '
            f'<span class="cnt">{len(pitchers)}</span></button>'
            f'<button type="button" role="tab" aria-selected="false" data-seg="b">野手 '
            f'<span class="cnt">{len(fielders)}</span></button></div>'
            f'<div class="seg-panel" data-seg="p">{grid(pitchers)}</div>'
            f'<div class="seg-panel" data-seg="b" hidden>{by_pos}</div>')


def staff_cards(staff: list[dict]) -> str:
    if not staff:
        return '<p class="empty">首脳陣の情報がありません。</p>'
    cards = "".join(
        f'<div class="pcard"><span class="num">{esc(r.get("number"))}</span>'
        f'<b class="nm">{esc(r.get("name"))}</b>'
        f'<small class="sub">{esc("・".join(x for x in (r.get("role"), r.get("club")) if x))}</small></div>'
        for r in staff)
    return f'<div class="pgrid">{cards}</div>'


# ---------------------------------------------------------------- 今大会の成績の表


def name_link(names: dict[str, str], number: str, fallback: str, prefix: str) -> str:
    name = names.get(number)
    if name:
        return f'<span class="no">{esc(number)}</span><a href="{prefix}p/{esc(number)}/">{esc(name)}</a>'
    return f'<span class="no">{esc(number)}</span>{esc(fallback)}'


def stats_block(rec: Record, names: dict[str, str]) -> str:
    if not rec.started:
        return '<p class="empty">大会が始まると、試合ごとに日本の打者・投手の成績が自動で入ります。</p>'
    bat_cols = ["選手", "試合", "打席", "打数", "安打", "打率", "出塁率", "本塁打", "打点",
                "四球", "三振", "盗塁"]
    bats = sorted(((n, e) for n, e in rec.bat.items() if e["打席"]),
                  key=lambda x: (-x[1]["打席"], int(br.number(x[0]))))
    bat_rows = [[name_link(names, n, e["名前"], "")]
                + [esc(e[c]) for c in bat_cols[1:]] for n, e in bats]
    pit_cols = ["選手", "登板", "先発", "投球回", "防御率", "被安打", "自責点", "三振", "四球",
                "球数"]
    pits = sorted(rec.pit.items(), key=lambda x: (-x[1]["_outs"], int(br.number(x[0]))))
    pit_rows = [[name_link(names, n, e["名前"], "")]
                + [esc(e[c]) for c in pit_cols[1:]] for n, e in pits]
    return ("<h3>打者</h3>" + (table(bat_cols, bat_rows) if bat_rows else
                               '<p class="empty">まだ打席の記録がありません。</p>')
            + "<h3>投手</h3>" + (table(pit_cols, pit_rows) if pit_rows else
                                 '<p class="empty">まだ登板の記録がありません。</p>')
            + '<p class="note">終わった試合の分だけを数えています。</p>')


# ---------------------------------------------------------------- japan/


def japan_page(d: dict, page, rec: Record) -> str:
    root = "../"
    players, staff = roster(d)
    names = roster_names(d)
    pitchers = sum(1 for r in players if r.get("position") == "投手")
    finished = [g for g in japan_games(d) if sl.is_final(g)]
    w, l, t = win_loss(d)
    record_text = f"{w}勝{l}敗" + (f"{t}分" if t else "") if finished else "大会前"
    tiles = (
        # 入口の3枚は横幅いっぱいに並べる（.tiles の既定は小さな数字のタイル向けの幅）
        '<div class="tiles" style="grid-template-columns:repeat(auto-fit,minmax(100px,1fr))">'
        f'<a class="tile" href="pitching/"><i>投手の登板表</i><b>{pitchers}人</b>'
        "<small>試合ごとの球数・投球回と中何日</small></a>"
        f'<a class="tile" href="#stats"><i>今大会の成績</i><b>{record_text}</b>'
        f"<small>{len(finished)}試合・打者と投手の表へ</small></a>"
        '<a class="tile" href="#measure"><i>計測データ</i><b>準備中</b>'
        "<small>パスワードで保護して載せる予定</small></a></div>")
    meta = (f"グループB・選手{len(players)}人と首脳陣{len(staff)}人・"
            f'{ext(OFFICIAL_JAPAN, "侍ジャパン公式の発表（2026年10月6日）")}の項目だけを載せています。'
            "年齢は発表時の値です。")
    roster_html = (player_cards(players, rec) if players else
                   '<p class="empty">日本代表_公式発表.csv が見つかりません。</p>')
    body = "".join([
        head([(root, "トップ"), ("", "自チーム")], "日本代表", meta),
        next_block(d, root),
        section("players", f"選手<small>{len(players)}人</small>", roster_html),
        tiles,
        section("staff", "首脳陣", staff_cards(staff)),
        section("games", "日本戦の日程と結果", games_table(d, root, starters(d, names))),
        section("stats", "今大会の成績", stats_block(rec, names)),
        section("measure", "計測データ", lock()),
    ])
    return page("日本代表", body, "japan/", "japan")


# ---------------------------------------------------------------- japan/pitching/


BOARD_SCRIPT = """<script>(function(){
var q=new URLSearchParams(location.search).get('now');
var n=q?Date.parse(q):Date.now();if(isNaN(n))n=Date.now();
var today=new Date(n-6*3600e3).toISOString().slice(0,10);
var t0=Date.parse(today+'T00:00:00Z');
document.querySelectorAll('table.board').forEach(function(t){
 t.querySelectorAll('[data-day]').forEach(function(c){
  c.classList.toggle('today',c.getAttribute('data-day')===today);});
 t.querySelectorAll('td[data-lastday]').forEach(function(c){
  var last=c.getAttribute('data-lastday');if(!last)return;
  var diff=Math.round((t0-Date.parse(last+'T00:00:00Z'))/864e5);
  c.classList.remove('rest0','rest1','ok');
  if(diff<0){c.textContent='-';return;}
  if(diff===0){c.textContent='今日登板';c.classList.add('rest0');return;}
  c.textContent='中'+(diff-1)+'日';
  c.classList.add(diff===1?'rest0':diff===2?'rest1':'ok');});
 var w=t.closest('.scroll');if(w&&t.tBodies[0]&&t.tBodies[0].rows.length)w.scrollLeft=w.scrollWidth;});
var s=document.getElementById('board-today');if(s)s.textContent=today.slice(5).replace('-','/');
})();</script>"""


def board_head(games: list[dict]) -> str:
    cells = []
    for game in games:
        jst = sl.jst_dt(game)
        local = sl.local_dt(game)
        seen = sl.japan_view(game) or {}
        cells.append(
            f'<th scope="col" data-day="{sl.local_day(game)}"><b>{md(jst)}</b><br>'
            f"<small>現地{local.month}/{local.day}</small><br>"
            f'<small>{esc(team_name(seen.get("opponent")))}</small></th>')
    return ('<th scope="col" class="nm">投手</th>' + "".join(cells)
            + '<th scope="col">最終登板<br><small>現地</small></th>'
              '<th scope="col">今日なら</th><th scope="col">計球数</th>')


def board_cell(app: dict | None, day: str) -> str:
    if not app:
        return f'<td data-day="{day}"></td>'
    cls = "app gs" if app["gs"] else "app"
    role = "先発" if app["gs"] else "救援"
    return (f'<td class="{cls}" data-day="{day}" title="{role}"><b>{app["pitches"]}球</b>'
            f'<small>{esc(app["ip"])}回</small></td>')


def pitching_page(d: dict, page, rec: Record) -> str:
    root = "../../"
    games = japan_games(d)
    names = roster_names(d)
    players, _ = roster(d)
    log = sl.pitcher_log(rows_of(d, "pitching"), d.get("games") or [], JAPAN)
    meta = ("日本の投手が、試合ごとに何球・何回投げたか。中何日は現地の日付で数えます。" + NO_LIMIT)
    crumbs = [(root, "トップ"), ("../", "日本代表"), ("", "投手の登板表")]
    if not log:
        sample = ('<p class="note">表の見本（列の見出しだけ）。行は投手、列は日本の試合です。</p>'
                  f'<div class="scroll"><table class="board">'
                  f"<thead><tr>{board_head(games)}</tr></thead><tbody></tbody></table></div>")
        body = (head(crumbs, "投手の登板表", meta)
                + '<p class="empty">大会が始まると、試合ごとに自動で埋まります。</p>' + sample
                + BOARD_SCRIPT)
        return page("投手の登板表", body, "japan/pitching/", "japan")
    rows = []
    shown = set()
    entries = []
    for pitcher in log:
        number = rec.pid_number.get(str(pitcher.get("_id")), "")
        shown.add(number)
        entries.append((number, pitcher))
    entries.sort(key=lambda x: (int(br.number(x[0])) if x[0].isdigit() else 999, x[1]["name"]))
    for number, pitcher in entries:
        apps = {a["gameid"]: a for a in pitcher["apps"]}
        name = names.get(number)
        label = (f'<a href="../p/{esc(number)}/">{esc(name)}</a>' if name
                 else esc(pitcher["name"]))
        last = pitcher["last_date"]
        rows.append(
            f'<tr><td class="nm"><span class="no">{esc(number)}</span>{label}</td>'
            + "".join(board_cell(apps.get(str(g.get("id"))), sl.local_day(g)) for g in games)
            + f"<td>{iso_md(last)}</td><td data-lastday=\"{esc(last)}\">-</td>"
              f'<td><b>{pitcher["total_pitches"]}球</b><br><small>{len(pitcher["apps"])}登板・'
              f'{esc(pitcher["ip_total"])}回</small></td></tr>')
    for row in players:  # まだ投げていない投手も並べる（起用の判断の材料）
        number = number_key(row.get("number"))
        if row.get("position") != "投手" or number in shown:
            continue
        rows.append(
            f'<tr><td class="nm"><span class="no">{esc(number)}</span>'
            f'<a href="../p/{esc(number)}/">{esc(row.get("name"))}</a></td>'
            + "".join(f'<td data-day="{sl.local_day(g)}"></td>' for g in games)
            + "<td>-</td><td>未登板</td><td>0</td></tr>")
    legend = ('<p class="note">セルは球数と投球回。先発は濃い色、救援は薄い色のセルです。'
              '「今日なら」は今日（現地 <b id="board-today">-</b>）投げるとしたら中何日か。'
              "試合の列は日本時間の日付が上、現地の日付が下です。</p>")
    body = (head(crumbs, "投手の登板表", meta) + legend
            + f'<div class="scroll"><table class="board"><thead><tr>{board_head(games)}</tr></thead>'
              f'<tbody>{"".join(rows)}</tbody></table></div>' + BOARD_SCRIPT)
    return page("投手の登板表", body, "japan/pitching/", "japan")


# ---------------------------------------------------------------- japan/p/<背番号>/


def game_label(game: dict | None, row: dict) -> tuple[str, str]:
    """（日付のセル, 相手のセル）。日本時間を先に、現地を小さく。"""
    if game and sl.local_dt(game):
        jst, local = when_parts(game)
        seen = sl.japan_view(game) or {}
        mark = mark_html(seen.get("mark"))
        score = esc(seen.get("score") or "")
        return (f"<b>{jst.split(' ')[0]}</b><small>現地 {local.split(' ')[0]}</small>",
                f"{mark}{esc(team_name(seen.get('opponent')))} <small>{score}</small>")
    other = row.get("away_team") if row.get("home_team") == JAPAN else row.get("home_team")
    return iso_md(row.get("date")), esc(team_name(other))


def tiles(items: list[tuple[str, str, str]]) -> str:
    return '<div class="tiles">' + "".join(
        f"<div class=\"tile\"><i>{esc(a)}</i><b>{esc(b)}</b><small>{esc(c)}</small></div>"
        for a, b, c in items) + "</div>"


def pitcher_part(d: dict, rec: Record, number: str, by_id: dict) -> str:
    entry = rec.pit.get(number)
    if not entry:
        return ""
    head_tiles = tiles([
        ("登板", f'{entry["登板"]}', f'先発 {entry["先発"]}'),
        ("投球回", entry["投球回"], f'球数 {entry["球数"]}'),
        ("防御率", entry["防御率"], f'自責点 {entry["自責点"]}'),
        ("三振", f'{entry["三振"]}', f'奪三振率 {entry["奪三振率"]}'),
        ("四球", f'{entry["四球"]}', f'与四球率 {entry["与四球率"]}'),
        ("被安打", f'{entry["被安打"]}', f'被本塁打 {entry["被本塁打"]}'),
    ])
    rows = []
    for row in sorted(rec.games_of("pitching", number),
                      key=lambda r: (str(r.get("date") or ""), int(br.number(r.get("gameid"))))):
        day, rival = game_label(by_id.get(str(row.get("gameid"))), row)
        role = "先発" if int(br.number(row.get("pitch_gs"))) else "救援"
        rows.append([day, rival, role, esc(sl.outs_to_ip(sl.ip_to_outs(row.get("pitch_ip")))),
                     *(esc(int(br.number(row.get(k)))) for k in (
                         "pitch_pitches", "pitch_h", "pitch_r", "pitch_er", "pitch_so",
                         "pitch_bb"))])
    cols = ["日付", "相手", "役割", "投球回", "球数", "被安打", "失点", "自責点", "三振", "四球"]
    return ("<h3>投手として</h3>" + head_tiles + "<h3>試合ごと（投手）</h3>" + table(cols, rows))


def batter_part(d: dict, rec: Record, number: str, by_id: dict) -> str:
    entry = rec.bat.get(number)
    if not entry or not entry["打席"]:
        return ""
    head_tiles = tiles([
        ("試合", f'{entry["試合"]}', f'打席 {entry["打席"]}'),
        ("打率", entry["打率"], f'{entry["安打"]}安打・{entry["打数"]}打数'),
        ("出塁率", entry["出塁率"], f'四球 {entry["四球"]}・死球 {entry["死球"]}'),
        ("長打率", entry["長打率"], f'本塁打 {entry["本塁打"]}'),
        ("打点", f'{entry["打点"]}', f'盗塁 {entry["盗塁"]}'),
        ("三振", f'{entry["三振"]}', f'三振率 {entry["三振率"]}'),
    ])
    rows = []
    for row in sorted(rec.games_of("batting", number),
                      key=lambda r: (str(r.get("date") or ""), int(br.number(r.get("gameid"))))):
        if not int(br.number(row.get("pa"))):
            continue
        day, rival = game_label(by_id.get(str(row.get("gameid"))), row)
        rows.append([day, rival, esc(row.get("pos") or ""),
                     *(esc(int(br.number(row.get(k)))) for k in (
                         "pa", "ab", "h", "hr", "rbi", "bb", "so", "sb"))])
    cols = ["日付", "相手", "守備", "打席", "打数", "安打", "本塁打", "打点", "四球", "三振", "盗塁"]
    return ("<h3>打者として</h3>" + head_tiles + "<h3>試合ごと（打者）</h3>" + table(cols, rows))


def clips_part(rec: Record, number: str, pitcher: bool) -> str:
    """今大会の映像のカット集（site_clips があり、記録があるときだけ）。"""
    pid = rec.pid_of(number)
    if not pid:
        return ""
    try:
        import site_clips
        clips = (site_clips.pitcher_clips(CURRENT, pid) if pitcher
                 else site_clips.batter_clips(CURRENT, pid))
        if not any(clips.values()):
            return ""
        return section("clips", "今大会のカット集", site_clips.clips_html(clips))
    except Exception:  # カット集が作れなくても、選手のページは出す
        return ""


def player_page(d: dict, page, rec: Record, row: dict) -> str:
    root = "../../../"
    number = number_key(row.get("number"))
    by_id = {str(g.get("id")): g for g in d.get("games") or []}
    size = ""
    if row.get("height_cm") or row.get("weight_kg"):
        size = f'{row.get("height_cm") or "?"}cm {row.get("weight_kg") or "?"}kg'
    meta = "・".join(esc(x) for x in (
        row.get("position"), hand_text(row), f'{row.get("age")}歳（発表時）' if row.get("age") else "",
        size, row.get("club")) if x)
    title = f'<span class="num">{esc(number)}</span> {esc(row.get("name"))}'
    crumbs = [(root, "トップ"), ("../../", "日本代表"), ("", f"背番号{number}")]
    pitcher = row.get("position") == "投手"
    parts = ([pitcher_part(d, rec, number, by_id), batter_part(d, rec, number, by_id)] if pitcher
             else [batter_part(d, rec, number, by_id), pitcher_part(d, rec, number, by_id)])
    now = "".join(p for p in parts if p)
    if not now:
        now = ('<p class="empty">大会が始まると、試合ごとに自動で入ります。</p>' if not rec.started
               else '<p class="empty">今大会はまだ出場の記録がありません。</p>')
    link = ('<p class="note"><a href="../../pitching/">投手の登板表へ</a></p>' if pitcher else "")
    body = (head(crumbs, title, meta)
            + section("now", "今大会の成績", now + link)
            + clips_part(rec, number, pitcher)
            + section("measure", "計測データ", lock()))
    return page(str(row.get("name") or f"背番号{number}"), body, f"japan/p/{number}/", "japan")


# ---------------------------------------------------------------- 入口


def build_japan(d: dict, page) -> dict[str, str]:
    """日本代表のページを {URL: HTML} で返す。"""
    rec = Record(d)
    out = {"japan/": japan_page(d, page, rec), "japan/pitching/": pitching_page(d, page, rec)}
    players, _ = roster(d)
    for row in players:
        number = number_key(row.get("number"))
        if not number:
            continue
        out[f"japan/p/{number}/"] = player_page(d, page, rec, row)
    return out
