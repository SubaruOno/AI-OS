#!/usr/bin/env python3
"""U-23W杯の共有サイトを、電波が弱い所でも読めるようにする部品。

build_site.py から呼ぶ。画面は持たず、タグを返すか、ファイルを書き出すだけ。

    head_tags(root)          <head> に足すタグ（ホーム画面用の manifest・アイコン・色、帯の見た目）
    body_end(root)           </body> の直前に足す <script>（Service Worker の登録、帯、全ページ保存）
    write_assets(...)        sw.js・manifest・アイコン・offline/・status.js・pages.json を書く
    headers_rules(token)     Cloudflare Pages の _headers に足す行
    status_from_games(...)   status.js に入れる中身を games.json の一覧から作る

URL はすべてサイトの根元（合言葉のフォルダ）からの相対で、フォルダ形式で書く。
"" がトップ、"team/cuba/" が相手国ページ。root は「そのページから根元への相対パス」で、
トップなら ""、team/cuba/ なら "../../"。

各ページはヘッダーのすぐ下に <div id="band"></div> を置く（なければ script が作る）。
トップには <button id="save-all">全ページを端末に保存</button> を置く。

    python3 site_offline.py --selftest   # 一時フォルダに書き出して中身を確かめる
"""

from __future__ import annotations

import argparse
import html
import json
import struct
import sys
import tempfile
import zlib
from datetime import datetime, timezone
from pathlib import Path

NAME = "U-23W杯 2026"
SHORT = "U-23W杯"
# ページの地の色。build_site.py の TEMPLATE の --bg に合わせる
THEME = {"dark": "#0f1115", "light": "#f6f7f9"}
RED = (200, 16, 46)
WHITE = (255, 255, 255)
ICONS = {"icon-192.png": 192, "icon-512.png": 512, "icon-180.png": 180}
# install のときに core_urls と一緒に先に保存するもの
EXTRA = ["status.js", "pages.json", "manifest.webmanifest",
         "icons/icon-192.png", "icons/icon-180.png"]


# ---------------------------------------------------------------- ページに足すもの


def head_tags(root: str) -> str:
    """<head> に足すタグを返す。root はそのページからサイトの根元への相対パス。"""
    r = html.escape(root)
    return "\n".join([
        f'<link rel="manifest" href="{r}manifest.webmanifest">',
        f'<meta name="theme-color" content="{THEME["dark"]}" media="(prefers-color-scheme: dark)">',
        f'<meta name="theme-color" content="{THEME["light"]}" media="(prefers-color-scheme: light)">',
        f'<link rel="icon" type="image/png" sizes="192x192" href="{r}icons/icon-192.png">',
        f'<link rel="apple-touch-icon" href="{r}icons/icon-180.png">',
        '<meta name="apple-mobile-web-app-capable" content="yes">',
        '<meta name="mobile-web-app-capable" content="yes">',
        f'<meta name="apple-mobile-web-app-title" content="{SHORT}">',
        '<meta name="apple-mobile-web-app-status-bar-style" content="default">',
        f"<style>{BAND_CSS}</style>",
    ])


def body_end(root: str) -> str:
    """</body> の直前に足す <script> を返す。帯・Service Worker・全ページ保存をまとめて受け持つ。"""
    return "<script>" + PAGE_JS.replace("__ROOT__", json.dumps(root)) + "</script>"


# ---------------------------------------------------------------- 書き出すもの


def write_assets(site_dir, core_urls, all_urls, version, status) -> None:
    """sw.js などを site_dir（合言葉のフォルダ）に書く。ページを書き終えてから呼ぶ。

    core_urls は最初に開いたときに先に保存するページ、all_urls は全ページ（pages.json になる）。
    status は status_from_games() の戻り値。version と updated が欠けていれば補う。
    """
    site = Path(site_dir)
    core, every = clean_urls(core_urls), clean_urls(all_urls)
    write(site / "sw.js", sw_js(core, version))
    write(site / "manifest.webmanifest", manifest())
    for name, size in ICONS.items():
        target = site / "icons" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(icon_png(size))
    write(site / "offline" / "index.html", OFFLINE_HTML)
    write(site / "status.js", status_js(status, version))
    write(site / "pages.json", json.dumps(every, ensure_ascii=False) + "\n")
    warn_missing(site, every)


def headers_rules(token: str) -> str:
    """_headers に足す行を返す。sw.js・status.js・pages.json は毎回サーバーに確かめさせる。"""
    lines = []
    for name in ("sw.js", "status.js", "pages.json"):
        lines += [f"/{token}/{name}", "  Cache-Control: no-cache"]
    return "\n".join(lines) + "\n"


def status_from_games(games, version, updated=None) -> dict:
    """games.json の一覧から status.js の中身を作る。updated は UTC の時刻（省略時は今）。

    戻り値: {"version", "updated": "2026-11-09T05:10:00Z", "games": 全試合の数,
             "finals": 終了試合の数,
             "last_final": {"date": 現地の日付, "nth": その日の第1試合から続けて終わっている
             試合の数, "day_finals": その日に終わった数, "day_games": その日の試合数} か None}

    nth は「第1〜第N試合がすべて終わっている最大の N」。同じ時刻に2試合ある日は後の番号の
    試合が先に終わることがあり、一番遅く始まった終了試合の番号を出すと、まだ終わっていない
    試合まで入っているように読めてしまうため。
    """
    finals = [g for g in games if is_final(g)]
    last = None
    if finals:
        end = max(finals, key=order)
        day = str(end.get("start") or "")[:10]
        same = sorted((g for g in games if str(g.get("start") or "")[:10] == day), key=order)
        nth = 0
        for game in same:
            if not is_final(game):
                break
            nth += 1
        last = {
            "date": day,
            "nth": nth,
            "day_finals": sum(1 for g in same if is_final(g)),
            "day_games": len(same),
        }
    return {"version": str(version), "updated": utc_iso(updated), "games": len(games),
            "finals": len(finals), "last_final": last}


# ---------------------------------------------------------------- 下回り


def is_final(game: dict) -> bool:
    """試合が終わっているか。site_logic.is_final と同じ決まり（F/7 なども終了）。"""
    return str(game.get("gamestatustext") or "").strip().upper().startswith("F")


def order(game: dict) -> tuple:
    return (str(game.get("start") or ""), int(game.get("gamenumber") or 0), int(game.get("id") or 0))


def utc_iso(moment: datetime | None) -> str:
    moment = moment or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean_urls(urls) -> list[str]:
    """重なりを除き、根元からの相対であることを確かめる。"""
    out: list[str] = []
    for url in urls:
        url = str(url)
        if url.startswith("/") or "://" in url:
            raise ValueError(f"URL はサイトの根元からの相対で書く: {url}")
        if url not in out:
            out.append(url)
    return out


def warn_missing(site: Path, urls: list[str]) -> None:
    """pages.json に載せたのにファイルがないページを知らせる。"""
    missing = [u for u in urls
               if (u == "" or u.endswith("/")) and not (site / u / "index.html").exists()]
    if missing:
        print(f"注意: pages.json の {len(missing)} ページにファイルがない（例: {missing[0]!r}）",
              file=sys.stderr)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sw_js(core: list[str], version: str) -> str:
    return (SW_JS.replace("__VERSION__", json.dumps(str(version)))
            .replace("__CORE__", json.dumps(core))
            .replace("__EXTRA__", json.dumps(EXTRA)))


def status_js(status: dict | None, version: str) -> str:
    data = dict(status or {})
    data.setdefault("version", str(version))
    data.setdefault("updated", utc_iso(None))
    data.setdefault("games", 0)
    data.setdefault("finals", 0)
    data.setdefault("last_final", None)
    return "window.U23_STATUS = " + json.dumps(data, sort_keys=True) + ";\n"


def manifest() -> str:
    icons = [{"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
             {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
             {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png",
              "purpose": "maskable"}]
    data = {"name": NAME, "short_name": SHORT, "lang": "ja", "start_url": "./", "scope": "./",
            "display": "standalone", "theme_color": THEME["dark"],
            "background_color": THEME["dark"], "icons": icons}
    return json.dumps(data, ensure_ascii=False, indent=1) + "\n"


def icon_png(size: int) -> bytes:
    """赤地に白い球と赤い縫い目のアイコン。球は丸く切り抜かれても欠けない大きさにする。"""
    center, ball = size / 2, size * 0.34
    seam, width = ball * 0.95, max(ball * 0.08, 1.5)
    red = bytes(RED)
    rows = []
    for y in range((size + 1) // 2):  # 上下は同じ形なので、上半分だけ計算して折り返す
        row = bytearray()
        py = y + 0.5 - center
        for x in range(size):
            px = x + 0.5 - center
            far = px * px + py * py
            if far > (ball + 1) ** 2:
                row += red
                continue
            inside = clamp(ball - far ** 0.5 + 0.5)
            line = max(clamp(width / 2 - abs(((px + dx) ** 2 + py * py) ** 0.5 - seam) + 0.5)
                       for dx in (ball * 1.3, -ball * 1.3))
            white = inside * (1 - line)
            row += bytes(round(r * (1 - white) + w * white) for r, w in zip(RED, WHITE))
        rows.append(bytes(row))
    return png(size, rows + rows[: size // 2][::-1])


def clamp(value: float) -> float:
    return 0.0 if value < 0 else 1.0 if value > 1 else value


def png(size: int, rows: list[bytes]) -> bytes:
    """RGB の行の並びから PNG を作る（標準ライブラリだけで書く）。"""
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    raw = b"".join(b"\x00" + row for row in rows)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


# ---------------------------------------------------------------- 書き出す中身

BAND_CSS = (
    "#band{display:flex;flex-wrap:wrap;align-items:center;gap:2px 12px;padding:6px 16px;"
    "font-size:12.5px;line-height:1.5;color:var(--dim,#9aa3b2);"
    "border-bottom:1px solid var(--line,#272c36)}"
    "#band:empty{display:none}"
    "#band.off{background:#3a2a0e;color:#ffd79a}"
    "#band button{font:inherit;min-height:44px;padding:0 14px;border-radius:8px;cursor:pointer;"
    "border:1px solid var(--btn,#1f6fd1);background:var(--btn,#1f6fd1);color:#fff;"
    "font-weight:600}"
    "@media (prefers-color-scheme: light){#band.off{background:#fff1d6;color:#7a4300}}"
)

# ページ側の script。古いiPhoneのSafariでも動くよう var と function で書く
PAGE_JS = r"""
(function () {
  var R = __ROOT__;  // サイトの根元への相対パス
  var sw = "serviceWorker" in navigator ? navigator.serviceWorker : null;
  var band = document.getElementById("band");
  if (!band) {
    band = document.createElement("div");
    band.id = "band";
    var head = document.querySelector("header");
    if (head) head.parentNode.insertBefore(band, head.nextSibling);
    else document.body.insertBefore(band, document.body.firstChild);
  }
  var meta = document.querySelector('meta[name="u23-saved"]');
  var saved = meta ? meta.getAttribute("content") : null;  // 保存版を出しているときだけある
  var startVer = null, fresh = false, reg = null;
  var controlled = !!(sw && sw.controller);

  function keyOf(href) {  // sw.js と同じ決まりで、保存の鍵にする
    var u = new URL(href, location.href), p = u.pathname;
    if (/\/index\.html$/.test(p)) p = p.slice(0, -10);
    return u.origin + p;
  }
  var me = keyOf(location.href);

  function two(n) { return (n < 10 ? "0" : "") + n; }
  function at(iso, hours) {  // UTC の時刻を、日本(+9)や現地(-6)の「11/9 14:10」にする
    var t = Date.parse(iso);
    if (isNaN(t)) return "?";
    var d = new Date(t + hours * 3600000);
    return (d.getUTCMonth() + 1) + "/" + d.getUTCDate() + " " +
      two(d.getUTCHours()) + ":" + two(d.getUTCMinutes());
  }
  function both(iso) { return "日本 " + at(iso, 9) + "／現地 " + at(iso, -6); }
  function result(s) {  // 途中の試合が抜けている日は「6試合中5試合」と数で出す（第N試合までと言えない）
    var f = s.last_final;
    if (!f || !f.date) return "結果反映 まだ試合はありません";
    var p = f.date.split("-"), day = "現地" + Number(p[1]) + "/" + Number(p[2]);
    if (f.nth && f.nth === f.day_finals) return "結果反映 " + day + " 第" + f.nth + "試合まで";
    return "結果反映 " + day + " " + f.day_games + "試合中" + f.day_finals + "試合";
  }
  function add(text) {
    var el = document.createElement("span");
    el.textContent = text;
    band.appendChild(el);
  }
  function render() {
    var s = window.U23_STATUS, off = navigator.onLine === false;
    band.textContent = "";
    band.className = saved !== null || off ? "off" : "";
    if (saved !== null) {  // 狭い画面では2行に分かれる。どちらも1行に収まる長さにする
      add((off ? "電波がないため" : "電波が弱いため") + "保存した内容を表示中");
      if (!isNaN(Date.parse(saved))) add(both(saved) + " 時点");
    } else if (off) {
      add("電波がありません");
    }
    if (s && s.updated && saved === null) {
      add("最終更新 " + both(s.updated));
      add(result(s));
    }
    if (fresh) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = "新しい更新があります（押すと再読み込み）";
      b.onclick = function () { location.reload(); };
      band.appendChild(b);
    }
  }

  function loadStatus() {
    var el = document.createElement("script");
    el.src = R + "status.js";
    el.onload = function () {
      if (window.U23_STATUS) startVer = window.U23_STATUS.version;
      render();
    };
    el.onerror = render;
    document.head.appendChild(el);
  }
  function check() {  // 開いている間に新しい版が出ていないか、status.js の版で確かめる
    if (document.hidden || fresh || startVer === null) return;
    fetch(R + "status.js", { cache: "no-store" }).then(function (r) {
      return r.ok ? r.text() : "";
    }).then(function (t) {
      var m = /"version":\s*"([^"]*)"/.exec(t);
      if (m && m[1] !== startVer) { fresh = true; render(); }
    }).catch(function () {});
  }

  function saveOne(url) {  // sw.js にネットから取って保存させる
    return fetch(url, { headers: { "x-u23-save": "1" }, cache: "no-store" }).then(function (r) {
      return r.blob().then(function () { return r.ok; });
    }, function () { return false; });
  }
  function ready() {  // Service Worker がこのページを受け持つまで待つ（最長5秒）
    if (sw.controller) return Promise.resolve(true);
    return new Promise(function (ok) {
      sw.addEventListener("controllerchange", function () { ok(true); });
      setTimeout(function () { ok(!!sw.controller); }, 5000);
    });
  }
  function setupSave(btn) {
    var label = btn.textContent || "全ページを端末に保存", busy = false;
    if (!sw || !window.caches) {
      btn.disabled = true;
      btn.textContent = "この画面では保存できません（Safariで開いてください）";
      return;
    }
    function list() {
      return fetch(R + "pages.json", { cache: "no-store" }).then(function (r) { return r.json(); });
    }
    function abs(u) { return new URL(R + u, location.href).href; }
    function count() {
      list().then(function (urls) {
        return Promise.all(urls.map(function (u) {
          return caches.match(keyOf(abs(u)), { ignoreVary: true });
        })).then(function (hits) {
          var n = hits.filter(Boolean).length;
          if (!busy) btn.textContent = label + "（保存済み " + n + "/" + urls.length + "）";
        });
      }).catch(function () {});
    }
    function saveAll(urls) {
      var i = 0, good = 0, bad = 0;
      function show() { btn.textContent = "保存中… " + (good + bad) + "/" + urls.length; }
      function next() {
        if (i >= urls.length) return Promise.resolve();
        return saveOne(abs(urls[i++])).then(function (ok) {
          if (ok) good++; else bad++;
          show();
          return next();
        });
      }
      show();
      return Promise.all([next(), next(), next(), next()]).then(function () {
        btn.textContent = bad
          ? "保存できなかったページが " + bad + " 件あります（押すともう一度）"
          : "保存しました（" + good + "/" + urls.length + "）";
      });
    }
    btn.addEventListener("click", function () {
      if (busy) return;
      busy = true;
      btn.disabled = true;
      btn.textContent = "保存の準備中…";
      ready().then(function (ok) {
        if (!ok) throw new Error("not ready");
        return list();
      }).then(saveAll).catch(function () {
        btn.textContent = "保存できませんでした。電波のある所でもう一度押してください";
      }).then(function () { busy = false; btn.disabled = false; });
    });
    count();
  }

  if (sw) {
    sw.addEventListener("message", function (e) {
      var d = e.data || {};
      if (d.t === "fresh" && d.key === me) { fresh = true; render(); }
    });
    sw.addEventListener("controllerchange", function () {
      // 初めて開いたページは Service Worker より先に届くので、受け持ちが決まってから保存する
      if (!controlled) { controlled = true; saveOne(location.href); }
    });
    if (sw.startMessages) sw.startMessages();
    sw.register(R + "sw.js", { scope: R || "./" }).then(function (r) { reg = r; }).catch(function () {});
  }
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) return;
    check();
    if (reg) reg.update().catch(function () {});
  });
  window.addEventListener("online", render);
  window.addEventListener("offline", render);
  setInterval(check, 5 * 60 * 1000);
  var btn = document.getElementById("save-all");
  if (btn) setupSave(btn);
  render();
  loadStatus();
})();
"""

SW_JS = r"""// U-23W杯 共有サイトの Service Worker。site_offline.py が書き出す（手で直さない）。
// 読み込みは「3秒待って応答がなければ保存版を出し、裏で新しい版を取る」。
const VERSION = __VERSION__;
const CACHE = "u23s-" + VERSION;          // 版ごとに名前を変え、古いものは activate で消す
const BASE = self.registration.scope;     // サイトの根元（合言葉のフォルダ）
const CORE = __CORE__;                    // 最初に先に保存するページ
const EXTRA = __EXTRA__;
const WAIT = 3000;    // ネットの応答を待つ時間
const LAST = 12000;   // 保存がないときに、さらにネットを待つ時間
const SAVE = 20000;   // 全ページ保存で1ページを待つ時間

function keyOf(href) {  // 保存の鍵。?以降を外し、…/index.html は …/ にそろえる
  const u = new URL(href);
  let p = u.pathname;
  if (p.endsWith("/index.html")) p = p.slice(0, -10);
  return u.origin + p;
}
function abs(u) { return keyOf(new URL(u, BASE).href); }
const ALWAYS_NET = ["status.js", "pages.json"].map(abs);
const OFFLINE = abs("offline/");

function within(p, ms) {
  return new Promise((ok, ng) => {
    const t = setTimeout(() => ng(new Error("timeout")), ms);
    p.then(v => { clearTimeout(t); ok(v); }, e => { clearTimeout(t); ng(e); });
  });
}
function keep(e, p) {  // 応答を返したあとも、保存が終わるまで止めさせない
  try { e.waitUntil(p.catch(() => {})); } catch (err) {}
}
function put(key, r) {  // 保存した時刻を付け、転送の印を外した複製を保存する
  return r.blob().then(body => {
    const h = new Headers(r.headers);
    h.set("x-u23-saved", new Date().toISOString());
    const copy = new Response(body, { status: r.status, statusText: r.statusText, headers: h });
    return caches.open(CACHE).then(c => c.put(key, copy));
  });
}
function fromNet(req, opts) {  // 5xx は電波がないのと同じに扱い、保存版へ回す
  return fetch(req, opts).then(r => {
    if (r.status >= 500) throw new Error("server " + r.status);
    return r;
  });
}
function tell(key) {
  return self.clients.matchAll({ type: "window", includeUncontrolled: true })
    .then(list => list.forEach(c => c.postMessage({ t: "fresh", key: key })));
}
function offline() {
  return caches.match(OFFLINE, { ignoreVary: true }).then(hit => hit || new Response(
    "<!doctype html><meta charset=utf-8><p>電波がありません。",
    { headers: { "content-type": "text/html; charset=utf-8" } }));
}

function stale(e, net, key, hit, nav) {  // 保存版を出す。HTML には保存した時刻の印を入れる
  const type = hit.headers.get("content-type") || "";
  if (!nav && type.indexOf("text/html") < 0) { keep(e, net); return hit; }
  return hit.text().then(old => {
    keep(e, net.then(r => (r.ok ? r.clone().text() : old)).then(now => {
      if (now !== old) return tell(key);
    }));
    const saved = hit.headers.get("x-u23-saved") || "";
    const body = old.replace("</head>", '<meta name="u23-saved" content="' + saved + '"></head>');
    return new Response(body, { headers: { "content-type": type || "text/html; charset=utf-8" } });
  });
}
function handle(e, key, opts) {
  const nav = e.request.mode === "navigate";
  const net = fromNet(opts ? e.request.url : e.request, opts).then(r => {
    if (r.ok && r.type === "basic") keep(e, put(key, r.clone()));
    return r;
  });
  return within(net, WAIT).catch(() => caches.match(key, { ignoreVary: true }).then(hit => {
    if (hit) return stale(e, net, key, hit, nav);
    return within(net, LAST).catch(() => (nav ? offline() : Response.error()));
  }));
}
function save(e, key) {  // 全ページ保存。保存版は使わず、ネットから取れたものだけ保存する
  return within(fromNet(e.request.url, { cache: "no-cache" }), SAVE).then(r => {
    if (!r.ok) return r;
    return put(key, r.clone()).then(() => r);
  });
}

function precache() {
  const one = (u, must) => fetch(new URL(u, BASE).href, { cache: "no-cache" }).then(r => {
    if (!r.ok) throw new Error(u);
    return put(abs(u), r);
  }).catch(err => { if (must) throw err; });
  return Promise.all([one("offline/", true)].concat(EXTRA.concat(CORE).map(u => one(u, false))));
}
function carry(names) {  // 古い版にだけある保存（全ページ保存など）を移す。今の一覧にないページは捨てる
  return caches.open(CACHE).then(cur => cur.match(abs("pages.json"))
    .then(r => (r ? r.json() : null)).catch(() => null)
    .then(list => {
      const keep = list ? new Set(list.map(abs)) : null;
      return names.reduce((p, n) => p.then(() => caches.open(n).then(o => o.keys().then(reqs =>
        Promise.all(reqs.map(q => {
          if (keep && !keep.has(q.url)) return null;
          return cur.match(q).then(hit => hit || o.match(q).then(r => r && cur.put(q, r)));
        }))))), Promise.resolve());
    }));
}

self.addEventListener("install", e => {
  e.waitUntil(precache().then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(names => {
    const old = names.filter(n => n !== CACHE && n.indexOf("u23") === 0);
    return carry(old.filter(n => n.indexOf("u23s-") === 0))
      .then(() => Promise.all(old.map(n => caches.delete(n))));
  }).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const q = e.request;
  if (q.method !== "GET" || !q.url.startsWith(BASE)) return;
  const key = keyOf(q.url);
  if (key === abs("sw.js")) return;
  if (q.headers.get("x-u23-save")) { e.respondWith(save(e, key)); return; }
  e.respondWith(handle(e, key, ALWAYS_NET.indexOf(key) >= 0 ? { cache: "no-cache" } : null));
});
"""

OFFLINE_HTML = """<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta name="referrer" content="no-referrer">
<title>保存されていない画面</title>
<style>
:root{--bg:#0f1115;--text:#e8eaed;--dim:#9aa3b2;--accent:#4da3ff}
@media (prefers-color-scheme: light){:root{--bg:#f6f7f9;--text:#1b1f27;--dim:#5f6878;--accent:#0b64c8}}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;font-size:16px;line-height:1.7}
main{max-width:560px;margin:0 auto;padding:48px 20px}
h1{font-size:20px;margin:0 0 12px}
p{margin:0 0 20px}
.row{display:flex;flex-wrap:wrap;gap:10px}
a,button{display:inline-flex;align-items:center;min-height:44px;padding:0 18px;border-radius:10px;
  border:1px solid var(--accent);color:var(--accent);background:transparent;font:inherit;text-decoration:none}
small{display:block;margin-top:28px;color:var(--dim);font-size:13px}
</style></head><body><main>
<h1>電波がないため開けません</h1>
<p>この画面は端末に保存されていません。電波のある所で開くか、トップの『全ページを端末に保存』を押してください。</p>
<div class="row"><button type="button" onclick="location.reload()">もう一度読み込む</button>
<a id="top" href="javascript:history.back()">トップへ</a></div>
<small>LINEなどのアプリの中で開くと保存が効きません。Safariで開いて、ホーム画面に追加してください。</small>
</main>
<script>
if (navigator.serviceWorker) navigator.serviceWorker.getRegistration().then(function (r) {
  if (r) document.getElementById("top").href = r.scope;
});
</script></body></html>
"""


# ---------------------------------------------------------------- 試し


def selftest() -> None:
    """一時フォルダに書き出し、読み直して形を確かめる。"""
    games = [
        {"id": 1, "gamenumber": 1, "start": "2026-11-08 10:30:00", "gamestatustext": "F"},
        {"id": 2, "gamenumber": 2, "start": "2026-11-08 12:00:00", "gamestatustext": "F/7"},
        {"id": 3, "gamenumber": 3, "start": "2026-11-08 14:30:00", "gamestatustext": ""},
        {"id": 4, "gamenumber": 4, "start": "2026-11-07 18:30:00", "gamestatustext": "F"},
    ]
    status = status_from_games(games, "t1", datetime(2026, 11, 9, 5, 10, tzinfo=timezone.utc))
    assert status["finals"] == 3, status
    assert status["last_final"] == {"date": "2026-11-08", "nth": 2, "day_finals": 2,
                                    "day_games": 3}, status
    assert status["updated"] == "2026-11-09T05:10:00Z", status
    assert status["games"] == 4, status
    assert status_from_games([], "t0")["last_final"] is None
    # 同じ時刻の2試合のうち、後の番号が先に終わった日。第2試合までしか続けて終わっていない
    gap = [{"id": i, "gamenumber": i, "start": f"2026-11-07 {t}:00",
            "gamestatustext": "F" if i != 3 else "B6"}
           for i, t in ((1, "10:30"), (2, "14:30"), (3, "18:30"), (4, "18:30"))]
    assert status_from_games(gap, "t2")["last_final"] == {
        "date": "2026-11-07", "nth": 2, "day_finals": 3, "day_games": 4}
    gap[0]["gamestatustext"] = "SUSP"  # 第1試合が中断なら、続けて終わった試合は0
    assert status_from_games(gap, "t2")["last_final"]["nth"] == 0
    with tempfile.TemporaryDirectory() as tmp:
        site = Path(tmp)
        for url in ("", "team/cuba/"):
            write(site / url / "index.html", "<html><head></head><body></body></html>")
        write_assets(site, ["", "team/cuba/"], ["", "team/cuba/", ""], "t1", status)
        text = (site / "status.js").read_text()
        assert json.loads(text[text.index("{"):text.rindex("}") + 1]) == status
        assert json.loads((site / "pages.json").read_text()) == ["", "team/cuba/"]
        assert json.loads((site / "manifest.webmanifest").read_text())["start_url"] == "./"
        sw = (site / "sw.js").read_text()
        assert '"t1"' in sw and '["", "team/cuba/"]' in sw and "__" not in sw
        for name, size in ICONS.items():
            data = (site / "icons" / name).read_bytes()
            assert data[:8] == b"\x89PNG\r\n\x1a\n"
            assert struct.unpack(">II", data[16:24]) == (size, size)
        assert "端末に保存されていません" in (site / "offline" / "index.html").read_text()
    assert '"../../"' in body_end("../../") and "__ROOT__" not in body_end("")
    assert 'href="../manifest.webmanifest"' in head_tags("../")
    assert "/tok/status.js\n  Cache-Control: no-cache" in headers_rules("tok")
    try:
        clean_urls(["/team/"])
        raise AssertionError("先頭の / を通してしまった")
    except ValueError:
        pass
    print("selftest: OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--selftest", action="store_true", help="書き出しを試す")
    args = parser.parse_args()
    if args.selftest:
        selftest()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
