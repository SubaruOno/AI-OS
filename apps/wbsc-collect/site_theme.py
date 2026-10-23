"""U-23W杯 共有サイトの見た目（CSS）。build_site.py が from site_theme import CSS で読み、<style> に入れる。

方針: 試合の現場の道具らしい締まった見た目。
- ヘッダーとヒーロー（.hero）は「ナイターの電光掲示板」風の濃紺〜黒の地に白の太い数字。ライトでもダークでも濃い地のまま。
- 差し色は日本代表の赤 #bc002d（地に使う --red。文字に使うときは --red-t）。
- 中身は Notion のデータベースのギャラリーのような、整ったカード（.pcard）と色札（.tag / .badge）。
- 外部の CSS・Web フォント・CDN は使わない。書体はシステムのものだけ。数字は tabular-nums。

色の切り替え: 既定はダーク。prefers-color-scheme: light でライトに替わる。
<html data-theme="light|dark"> を付けると、端末の設定にかかわらずその色にできる（見本の確認用）。
site_offline.THEME（theme-color）はヘッダーの地 --head と同じ色にしてある。
"""

# ライトの色。prefers-color-scheme: light と data-theme="light" の両方で使うので1か所にまとめる
_LIGHT = """color-scheme:light;
--bg:#f3f4f7;--card:#fff;--card2:#f7f8fa;--line:#dde1e8;--line2:#c3c9d4;--text:#11151d;--dim:#566072;
--accent:#0a58b8;--btn:#0a58b8;--warm:#9a4a00;--jp:#fdebef;--win:#17784d;--lose:#c4002c;--chip:#eceef3;
--red-t:#bc002d;--ink:#0b1020;--ink-t:#fff;--hatch:rgba(10,20,40,.045);
--t-gray:#4a5263;--t-gray-bg:#eceef3;--t-blue:#0b4f9c;--t-blue-bg:#e2eefc;--t-green:#11683f;--t-green-bg:#dff3e8;
--t-red:#a1001f;--t-red-bg:#fde6ea;--t-amber:#864700;--t-amber-bg:#fcefd6;--t-violet:#5b2fa8;--t-violet-bg:#efe8fc;
--sp-field:#e3e9df;--sp-edge:#c3cdbf;--sp-infield:#ece1cf;--sp-inedge:#d3c3a8;--sp-guide:#8b978e;
--sp-label:#5f6878;--sp-line:#7a877d;--sp-ground:#2a78d6;--sp-liner:#c4501f;--sp-fly:#12805a"""

_CSS = """
:root{color-scheme:dark;
--bg:#0b0d12;--card:#141821;--card2:#1a1f2a;--line:#262c38;--line2:#3a4252;--text:#eaedf2;--dim:#a0a9b8;
--accent:#6cb0ff;--btn:#1f6fd1;--warm:#ffb454;--jp:#2b1720;--win:#4cc38a;--lose:#ff6b7f;--chip:#1d222d;
--red:#bc002d;--red-t:#ff5c7a;--red-hi:#ff3358;--ink:#eef1f6;--ink-t:#0b0d12;--hatch:rgba(255,255,255,.035);
--head:#0a0f1c;--head-dim:#b9c2d3;--board:#0a0f1e;--board2:#141d38;--board-line:#27324f;--board-dim:#b3bdd1;
--led:#ffc53d;
--t-gray:#c6cdd8;--t-gray-bg:#232833;--t-blue:#a5cdff;--t-blue-bg:#15304f;--t-green:#93e2b7;--t-green-bg:#123626;
--t-red:#ffa1b1;--t-red-bg:#40141f;--t-amber:#ffd08a;--t-amber-bg:#3a2a10;--t-violet:#d2b8ff;--t-violet-bg:#2c2047;
--sp-field:#262b27;--sp-edge:#3d4a40;--sp-infield:#332c24;--sp-inedge:#4a3f33;--sp-guide:#7d8b80;
--sp-label:#9aa3b2;--sp-line:#8a968c;--sp-ground:#3987e5;--sp-liner:#d95926;--sp-fly:#199e70}
@media (prefers-color-scheme: light){:root:not([data-theme=dark]){__LIGHT__}}
:root[data-theme=light]{__LIGHT__}
*{box-sizing:border-box}
[hidden]{display:none!important}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
html{-webkit-text-size-adjust:100%;text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font-size:15px;line-height:1.6;
font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Hiragino Kaku Gothic ProN","Noto Sans JP","Yu Gothic UI",Meiryo,system-ui,sans-serif;
font-variant-numeric:tabular-nums;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
a:focus-visible,button:focus-visible,summary:focus-visible,th:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* ---- ヘッダー（上に固定。電光掲示板と同じ濃い地） */
header{display:flex;align-items:center;min-height:48px;padding:0 4px 0 14px;position:sticky;top:0;z-index:5;
background:var(--head);color:#fff;box-shadow:0 1px 0 var(--board-line)}
.brand{display:inline-flex;align-items:center;gap:8px;min-height:48px;margin-right:auto;padding-right:6px;
color:#fff;font-weight:800;font-size:15px;letter-spacing:.01em;white-space:nowrap}
.brand::before{content:"";flex:none;width:11px;height:11px;border-radius:50%;background:var(--red);box-shadow:0 0 0 2px #fff}
header nav{display:flex;min-width:0;overflow-x:auto;scrollbar-width:none}
header nav::-webkit-scrollbar{display:none}
header nav a{display:inline-flex;align-items:center;justify-content:center;min-width:44px;min-height:48px;
padding:3px 9px 0;font-size:14px;font-weight:600;color:var(--head-dim);white-space:nowrap;border-bottom:3px solid transparent}
header nav a[aria-current]{color:#fff;font-weight:800;border-bottom-color:var(--red-hi)}
@media (hover:hover){header nav a:hover,.brand:hover{color:#fff}}

main{max-width:1120px;margin:0 auto;padding:8px 16px 56px}
h1{font-size:23px;line-height:1.3;font-weight:800;letter-spacing:-.005em;margin:14px 0 8px}
h1 small{display:block;margin-top:2px;font-size:13px;color:var(--dim);font-weight:400;letter-spacing:0}
h2{font-size:17px;line-height:1.35;font-weight:800;margin:30px 0 10px;padding-left:10px;border-left:4px solid var(--red);
color:var(--text);scroll-margin-top:60px}
h2 small,h3 small{margin-left:.5em;font-size:13px;color:var(--dim);font-weight:400}
h3{font-size:15px;font-weight:700;margin:16px 0 6px}
h4{font-size:13px;margin:14px 0 6px;color:var(--dim)}
section{scroll-margin-top:60px}
p{margin:6px 0}
.note,.empty,.none{color:var(--dim);font-size:13px}
.crumb{margin:4px 0 0;font-size:14px}
.crumb a{display:inline-flex;align-items:center;min-height:44px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-top:10px}
.card>h2:first-child{margin-top:4px}
.warn{color:var(--warm);font-weight:700}
.ext{margin-left:6px;font-size:13px}
.ext::after{content:"↗";font-size:.8em;margin-left:1px}

/* ---- 札（Notion の色札） */
.badge{display:inline-block;padding:1px 7px;border-radius:5px;background:var(--t-gray-bg);color:var(--t-gray);
border:1px solid transparent;font-size:11.5px;font-weight:700;line-height:1.5;white-space:nowrap}
.badge.alt,.badge.warn{background:var(--t-red-bg);color:var(--t-red)}
.badge.jpl{margin-left:8px;background:var(--t-amber-bg);color:var(--t-amber);font-weight:600}
.badge.roster{background:var(--t-blue-bg);color:var(--t-blue)}
.badge.npb{background:var(--t-violet-bg);color:var(--t-violet)}
.badge.ok{background:var(--t-green-bg);color:var(--t-green)}
.tag{display:inline-block;margin-right:6px;padding:0 6px;border-radius:4px;background:var(--t-gray-bg);color:var(--t-gray);
font-size:11.5px;font-weight:600;line-height:1.6;vertical-align:1px;white-space:nowrap}
.tag.sup,.tag.md{background:var(--t-amber-bg);color:var(--t-amber)}
.fn{margin-left:2px;font-size:10px;color:var(--dim)}
.mk{margin-right:4px;font-weight:800}.mk.w{color:var(--win)}.mk.l{color:var(--lose)}
.live{margin-left:4px;padding:1px 7px;border-radius:4px;background:var(--red);color:#fff;font-size:11px;font-weight:800;
letter-spacing:.04em;white-space:nowrap}
.inn{margin-left:4px;color:var(--dim);font-size:12px}
span.st{display:inline-block;max-width:100%;margin-left:4px;padding:0 6px;border-radius:4px;background:var(--t-gray-bg);
color:var(--t-gray);font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;vertical-align:middle}
.nw{white-space:nowrap}
.cnt{display:inline-block;min-width:1.7em;padding:0 6px;border-radius:999px;background:var(--chip);color:var(--dim);
font-size:12px;font-weight:700;line-height:1.6;text-align:center;font-variant-numeric:tabular-nums}

/* ---- 表 */
table{width:100%;border-collapse:separate;border-spacing:0;font-size:13.5px;font-variant-numeric:tabular-nums}
th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:right;white-space:nowrap;vertical-align:top}
tbody tr:last-child td{border-bottom:0}
th{color:var(--dim);font-weight:600;font-size:13px;background:var(--card)}
.gwrap{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}
table.games th,table.games td{text-align:left}
table.games td.t{width:1%}
table.games td.t b{font-size:14px}
table.games td.m{white-space:normal}
table.games td.m a{white-space:nowrap}
table.games small{display:block;color:var(--dim);font-size:12px}
table.games .lk .ext{display:inline-block;margin:-8px 14px -8px 0;padding:10px 0}
a.ext{padding-top:9px;padding-bottom:9px}
table.games td.m a,table.stand td a,table.roster td a{padding:9px 0}
table.roster td.rec a{display:inline-block;margin:-9px -12px;padding:9px 12px}
.sc{display:inline-block;min-width:2.4em;text-align:center;font-weight:800}
tr.jp td{background:var(--jp)}
.scroll{overflow:auto;-webkit-overflow-scrolling:touch;background:var(--card);border:1px solid var(--line);border-radius:12px}
.scroll.tall{max-height:75vh}
table.sort thead th,table.stand thead th{position:sticky;top:0;z-index:2}
table.sort th{cursor:pointer;-webkit-user-select:none;user-select:none}
table.sort th[aria-sort]{color:var(--text)}
table.sort th[aria-sort=ascending]::after{content:"▲";margin-left:2px;font-size:9px;color:var(--red-t)}
table.sort th[aria-sort=descending]::after{content:"▼";margin-left:2px;font-size:9px;color:var(--red-t)}
table.sort th:first-child,table.sort td:first-child,table.fix1 th:first-child,table.fix1 td:first-child{
position:sticky;left:0;z-index:1;background:var(--card);text-align:left;box-shadow:1px 0 0 var(--line)}
table.sort thead th:first-child,table.fix1 thead th:first-child{z-index:3}
td.nm{white-space:normal;min-width:7.5em;max-width:10em;line-height:1.35}
@media (min-width:768px){td.nm{min-width:160px;max-width:200px}}
.yomi{display:block;margin-top:1px;color:var(--dim);font-size:11.5px;font-weight:400;line-height:1.3}
h3 .yomi{display:inline;margin-left:.5em;font-size:13px}
.tbd{color:var(--dim)}
td.cl,td.ev{white-space:normal;min-width:7em}
table.jpt{table-layout:fixed;min-width:47.5em}
table.jpt th,table.jpt td{text-align:left}
table.jpt td.nm,table.jpt td.cl{white-space:nowrap;max-width:none}
table.jpt td.cl{overflow:hidden;text-overflow:ellipsis}
.c-nm{width:9.6em}.c-pos{width:4.6em}.c-hand{width:5.4em}.c-age{width:4em}.c-size{width:8.8em}
td.app{text-align:left;line-height:1.35}
td.app small{display:block;color:var(--dim);font-size:11px}
table.log th small{color:var(--dim);font-size:11px}
tr.old td{color:var(--dim)}
main.fe tr[data-elig="0"],main.fp tr.few,main.fe .pcard[data-elig="0"],main.fp .pcard.few{display:none}
.b-el{margin-left:3px;color:var(--win);font-size:11px;font-weight:700}
.b-ro{display:inline-block;margin-left:4px;padding:0 5px;border-radius:4px;background:var(--t-blue-bg);
color:var(--t-blue);font-size:10.5px;font-weight:700;line-height:1.5}
.tc{margin-left:4px;font-weight:400}
.filters{display:flex;flex-wrap:wrap;gap:0 18px;margin-top:6px}
.filters label{display:inline-flex;align-items:center;gap:8px;min-height:44px;cursor:pointer}
.filters input{width:20px;height:20px;margin:0;accent-color:var(--red)}
table.plain th,table.plain td{text-align:left}
table.plain td small,table.rk td small{display:block;color:var(--dim);font-size:12px;white-space:normal}
.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px;margin-top:10px}
.two .card{margin-top:0}
.card.st h3{margin:0 0 6px}
.card.st .scroll{border:0;border-radius:0}
table.stand th,table.stand td{padding:6px 7px}
table.stand td:first-child{min-width:9.6em}
.rk{display:inline-block;min-width:1.5em;color:var(--dim);font-weight:700}
table.fix1 tr.jp td:first-child{background:var(--jp)}
table.stand td small{display:block;max-width:12em;color:var(--dim);font-size:11px;white-space:normal}
table.stand tr.jp td{font-weight:800}

/* ---- ヒーロー（ナイターの電光掲示板。ライトでもダークでも濃い地） */
.hero{position:relative;display:flex;flex-direction:column;gap:4px;margin-top:12px;padding:16px 18px 18px;
background:radial-gradient(circle,rgba(255,255,255,.07) 1px,transparent 1.6px) 0 0/6px 6px,
linear-gradient(180deg,var(--board2),var(--board));
border:1px solid var(--board-line);border-radius:14px;box-shadow:inset 0 3px 0 var(--red);color:#fff;overflow:hidden}
a.hero{color:#fff}
@media (hover:hover){a.hero:hover{border-color:#3d4a73}}
.hero small{color:var(--board-dim);font-size:13px;letter-spacing:.04em}
.hero .when{margin-left:10px;color:var(--led);font-size:15px;font-weight:800;letter-spacing:0}
.hero.on .when{padding:1px 8px;border-radius:5px;background:var(--red);color:#fff}
.hero .opp{font-size:26px;line-height:1.25;font-weight:800;color:#fff}
.hero span{color:var(--board-dim);font-size:13.5px}
.hero .jst{color:#fff;font-size:18px;font-weight:800}
.hero .local{white-space:nowrap}
.hero .big{display:block;font-size:46px;line-height:1.05;font-weight:800;letter-spacing:-.02em;color:#fff;
font-variant-numeric:tabular-nums}
.hero .big em{font-style:normal;color:var(--led)}
.hero .tile{background:rgba(255,255,255,.05);border-color:var(--board-line)}
.hero .tile b{color:#fff}
.hero .tile i,.hero .tile span,.hero .tile small{color:var(--board-dim)}
.prev{margin:10px 0 0;font-size:15px}
.prev small{margin-left:8px;color:var(--dim);font-size:12px}

/* ---- 入口の2枚（自チーム＝赤、相手国＝濃紺〜墨） */
.doors{display:grid;grid-template-columns:1fr;gap:10px;margin:14px 0 6px}
@media (min-width:640px){.doors{grid-template-columns:1fr 1fr;gap:12px}}
.door{position:relative;isolation:isolate;display:flex;flex-direction:column;justify-content:flex-end;gap:2px;
min-height:120px;padding:16px 60px 16px 18px;border:1px solid transparent;border-radius:14px;color:#fff;overflow:hidden}
.door.jp{background:linear-gradient(135deg,#d0063a 0%,#bc002d 45%,#8e0021 100%)}
.door.opp{background:linear-gradient(135deg,#1c2540 0%,#111831 50%,#080c18 100%);border-color:var(--board-line)}
.door.jp::before{content:"";position:absolute;right:-30px;top:50%;width:150px;height:150px;margin-top:-75px;
border-radius:50%;background:rgba(255,255,255,.09);z-index:-1}
.door.opp::before{content:"";position:absolute;top:0;right:0;bottom:0;left:0;z-index:-1;
background:radial-gradient(circle,rgba(255,255,255,.07) 1px,transparent 1.6px) 0 0/6px 6px}
.door::after{content:"→";position:absolute;right:20px;top:50%;transform:translateY(-50%);font-size:24px;font-weight:800}
.door-k{font-size:12px;font-weight:800;letter-spacing:.12em;color:rgba(255,255,255,.88)}
.door b{font-size:26px;line-height:1.2;font-weight:800;letter-spacing:.01em}
.door small{font-size:13.5px;line-height:1.45;color:rgba(255,255,255,.9)}
.door:focus-visible{outline:3px solid var(--accent);outline-offset:3px}
@media (hover:hover){.door:hover{filter:brightness(1.1)}}

/* ---- 見出しの組み（パンくず・h1・補足） */
.page-head{margin:6px 0 10px}
.page-head h1{margin:0 0 4px}
.crumbs{margin:0;color:var(--dim);font-size:13.5px}
.crumbs a{display:inline-flex;align-items:center;min-height:44px}
.meta{margin:0;color:var(--dim);font-size:13.5px}

/* ---- チームのカード（トップの一覧） */
.tgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:8px}
.tcard{display:flex;flex-direction:column;justify-content:center;min-height:60px;padding:8px 12px;
background:var(--card);border:1px solid var(--line);border-radius:10px;color:var(--text)}
@media (hover:hover){.tcard:hover{border-color:var(--line2);background:var(--card2)}}
.tcard span{font-weight:700;font-size:14.5px;white-space:nowrap}
.tcard small{color:var(--dim);font-size:12px;white-space:nowrap;line-height:1.4}
.go{display:flex;align-items:center;min-height:52px;margin-top:24px;color:var(--text);font-weight:700}
@media (hover:hover){.card.go:hover{border-color:var(--line2)}}
.save{width:15em;max-width:100%;min-height:44px;padding:0 12px;border:1px solid var(--btn);border-radius:8px;
background:var(--btn);color:#fff;font:inherit;font-weight:700;cursor:pointer;white-space:nowrap;
overflow:hidden;text-overflow:ellipsis}
.save:disabled{opacity:.6}
.save-st{min-height:1.5em;margin:4px 0 2px;color:var(--dim);font-size:12.5px}
.links .ext{display:inline-flex;align-items:center;min-height:44px;margin:0 18px 0 0;font-size:15px}
.facts{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;margin:8px 0}
.facts dt{padding-top:1px;color:var(--dim);font-size:13px;white-space:nowrap}
.facts dd{margin:0}
.facts small{color:var(--dim);font-size:12px}
.facts small.mn{display:block;line-height:1.45}
ul.notes{margin:8px 0;padding-left:1.2em;color:var(--dim);font-size:13px}
.toc{display:flex;gap:6px;overflow-x:auto;margin:10px -16px 0;padding:4px 16px;background:var(--bg)}
.toc a{flex:none;display:inline-flex;align-items:center;min-height:44px;padding:0 14px;
border:1px solid var(--line);border-radius:999px;background:var(--card);font-size:13px;font-weight:600;color:var(--text)}
@media (min-width:700px) and (min-height:600px){.toc{position:sticky;top:48px;z-index:4;border-bottom:1px solid var(--line)}
section{scroll-margin-top:112px}}
@media (max-height:599px){.scroll.tall{max-height:none}}
details{margin-top:10px;padding:0 14px;background:var(--card);border:1px solid var(--line);border-radius:12px}
details[open]{padding-bottom:12px}
summary{display:flex;align-items:center;gap:8px;min-height:48px;cursor:pointer;font-weight:700;
color:var(--text);list-style:none}
summary::-webkit-details-marker{display:none}
summary::before{content:"▶";font-size:10px;color:var(--dim)}
details[open] summary::before{content:"▼"}
summary small{color:var(--dim);font-size:12px;font-weight:400}
.nb h3{margin:0 0 4px}
.nb ul{margin:4px 0;padding-left:1.2em}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}
.chip{padding:2px 9px;border:1px solid var(--line);border-radius:6px;background:var(--chip);font-size:13px}
.chip b{margin-right:6px;color:var(--dim);font-weight:500}

/* ---- 数字のタイル（<i>見出し</i><b>数字</b><small>補足</small>。古い版の <span> 見出しも同じ見た目） */
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:8px;margin:8px 0}
.tile{min-width:0;padding:9px 11px 10px;border:1px solid var(--line);border-radius:10px;background:var(--card)}
.card .tile{background:var(--bg)}
.tile i,.tile span{display:block;font-style:normal;color:var(--dim);font-size:12px;font-weight:600;line-height:1.4}
.tile b{display:block;font-size:26px;line-height:1.2;font-weight:800;letter-spacing:-.01em;font-variant-numeric:tabular-nums;
overflow-wrap:anywhere}
.tile small{display:block;color:var(--dim);font-size:12px;line-height:1.4}
.sub{color:var(--dim);font-size:13px}
ul.apps{margin:4px 0;padding-left:1.2em}
.spray{margin:6px 0}
.spray-key{margin-right:5px;vertical-align:-2px}
.spray-note{margin:2px 0 0;color:var(--dim);font-size:12px}
.spray-field{fill:var(--sp-field);stroke:var(--sp-edge)}
.spray-infield{fill:var(--sp-infield);stroke:var(--sp-inedge)}
.spray-guide{stroke:var(--sp-guide)}
.spray-label{fill:var(--sp-label)}
.spray-line{stroke:var(--sp-line)}
.spray-dot{stroke:var(--sp-field)}
.spray-ground{fill:var(--sp-ground)}
.spray-liner{fill:var(--sp-liner)}
.spray-fly,.spray-pop{fill:var(--sp-fly)}

/* ---- 切り替え（新しい role=tab の aria-selected と、古い aria-pressed の両方） */
.seg{display:inline-flex;gap:2px;margin:10px 0 6px;padding:3px;border:1px solid var(--line);border-radius:11px;
background:var(--chip)}
.seg button{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:44px;padding:0 18px;
border:0;border-radius:8px;background:transparent;color:var(--text);font:inherit;font-size:15px;font-weight:700;
cursor:pointer;white-space:nowrap}
.seg button[aria-pressed=true],.seg button[aria-selected=true]{background:var(--ink);color:var(--ink-t);
box-shadow:0 1px 2px rgba(0,0,0,.25)}
.seg button[aria-pressed=true] .cnt,.seg button[aria-selected=true] .cnt{background:rgba(127,127,127,.28);color:inherit}
@media (max-width:600px){.seg{display:flex}.seg button{flex:1 1 0;padding:0 10px}}
.seg-panel{margin-top:6px}

/* ---- 選手カード（Notion のギャラリー。375px で2列、PC で4〜5列） */
.pgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:8px 0}
@media (min-width:700px){.pgrid{grid-template-columns:repeat(auto-fill,minmax(196px,1fr));gap:10px}}
.pcard{display:flex;flex-wrap:wrap;align-items:baseline;align-content:flex-start;gap:4px 8px;min-width:0;min-height:44px;
padding:11px 12px 12px;background:var(--card);border:1px solid var(--line);border-radius:12px;color:var(--text)}
a.pcard{color:var(--text)}
@media (hover:hover){a.pcard:hover{border-color:var(--line2);background:var(--card2)}}
a.pcard:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.pcard .num{flex:none;min-width:1.4em;font-size:20px;line-height:1;font-weight:800;color:var(--red-t);
font-variant-numeric:tabular-nums}
.pcard .nm{flex:1 1 0;min-width:0;font-size:15px;line-height:1.3;font-weight:800;overflow-wrap:anywhere}
.pcard .sub{flex:0 0 100%;color:var(--dim);font-size:12px;line-height:1.4}
.pcard .kv{flex:1 1 calc(50% - 4px);display:flex;flex-direction:column;min-width:0;padding:5px 8px 6px;
border-radius:8px;background:var(--chip)}
.pcard .kv i{font-style:normal;color:var(--dim);font-size:11px;font-weight:600;line-height:1.35}
.pcard .kv em{font-style:normal;font-size:17px;line-height:1.25;font-weight:800;font-variant-numeric:tabular-nums}
.pcard .badges{flex:0 0 100%;display:flex;flex-wrap:wrap;gap:4px;margin-top:2px}
.pcard .badge{white-space:normal;max-width:100%}

/* ---- カット集（奪三振集・被安打集など） */
.clips{display:grid;gap:8px;margin-top:10px}
.clips details.clip{margin-top:0}
.clip summary b{font-size:15px;color:var(--text)}
.clip summary .cnt{margin-left:auto}
.clip .empty{margin:0 0 4px}
ol.clip-list{margin:0;padding:0;list-style:none}
.clip-list li{display:grid;grid-template-columns:minmax(0,1fr) auto;column-gap:10px;align-items:center;
padding:9px 0;border-top:1px solid var(--line)}
.clip-list li:first-child{border-top:0}
.clip-list .when{grid-column:1;color:var(--dim);font-size:12px;line-height:1.4}
.clip-list .what{grid-column:1;font-size:14.5px;line-height:1.45}
.clip-list .play{grid-column:2;grid-row:1/span 2;display:inline-flex;align-items:center;min-height:44px;padding:0 12px;
border-radius:8px;background:var(--red);color:#fff;font-size:13px;font-weight:800;white-space:nowrap}
@media (hover:hover){.clip-list .play:hover{filter:brightness(1.12)}}

/* ---- 登板表（行＝投手、列＝日付） */
table.board th,table.board td{min-width:3em;padding:6px;text-align:center;vertical-align:middle;
border-bottom:1px solid var(--line);border-right:1px solid var(--line)}
table.board th:last-child,table.board td:last-child{border-right:0}
table.board thead th{position:sticky;top:0;z-index:2}
table.board th:first-child,table.board td:first-child{position:sticky;left:0;z-index:1;min-width:7.5em;
background:var(--card);text-align:left;white-space:normal;box-shadow:1px 0 0 var(--line)}
table.board thead th:first-child{z-index:3}
table.board caption{position:sticky;left:0;padding:8px 10px 6px;caption-side:top;text-align:left;color:var(--dim);
font-size:12px;font-weight:600}
table.board th b{color:var(--text)}
table.board th small{color:var(--dim);font-size:11px;font-weight:400;line-height:1.3}
table.board th.today b,table.board th.today small{color:#fff}
table.board td.app{background:var(--t-blue-bg);color:var(--t-blue);font-weight:800;text-align:center;line-height:1.3}
table.board td.app small{color:inherit}
table.board td.gs{background:var(--ink);color:var(--ink-t);font-weight:800}
table.board td.rest0{background:var(--t-red-bg);color:var(--t-red);font-weight:800}
table.board td.rest1{background:var(--t-amber-bg);color:var(--t-amber);font-weight:800}
table.board td.ok{background:var(--t-green-bg);color:var(--t-green);font-weight:700}
table.board .today{box-shadow:inset 2px 0 0 var(--red-t),inset -2px 0 0 var(--red-t)}
table.board th.today{background:var(--red);color:#fff;font-weight:800}

/* ---- 鍵つきの枠（準備中の計測データなど） */
.lock{display:grid;grid-template-columns:auto minmax(0,1fr);column-gap:12px;align-items:start;margin-top:10px;
padding:16px;border:1px dashed var(--line2);border-radius:12px;
background:repeating-linear-gradient(135deg,transparent 0 10px,var(--hatch) 10px 20px),var(--card)}
.lock::before{content:"";grid-row:1/span 9;width:22px;height:22px;margin-top:1px;background:var(--dim);
-webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M7 10V7a5 5 0 0 1 10 0v3h1a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-9a1 1 0 0 1 1-1h1zm2 0h6V7a3 3 0 0 0-6 0v3z'/%3E%3C/svg%3E") center/contain no-repeat;
mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M7 10V7a5 5 0 0 1 10 0v3h1a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-9a1 1 0 0 1 1-1h1zm2 0h6V7a3 3 0 0 0-6 0v3z'/%3E%3C/svg%3E") center/contain no-repeat}
.lock>*{grid-column:2}
.lock b{font-size:15px;font-weight:800}
.lock p{margin:2px 0 0;color:var(--dim);font-size:13.5px}

.no{display:inline-block;min-width:2em;color:var(--dim)}
ol.flow{padding-left:1.4em}
h2.day{color:var(--text);font-size:16px}
h2.day small{margin-left:.8em}
span.today{display:inline-block;margin-left:8px;padding:0 8px;border-radius:4px;background:var(--red);
color:#fff;font-size:12px;font-weight:800;vertical-align:2px}
.days{display:flex;flex-wrap:wrap;gap:6px}
.days a{display:inline-flex;align-items:center;min-height:44px;padding:0 12px;border:1px solid var(--line);
border-radius:8px;background:var(--card);font-size:13px;font-weight:600;color:var(--text)}
footer{padding:20px 16px 32px;color:var(--dim);font-size:12px;text-align:center}
@media (max-width:600px){
table{font-size:13.5px}
.note,.empty,.none,.spray-note,ul.notes,.facts dt,.tile span,.tile i,.sub,table.games small,
table.plain td small,table.rk td small,.hero small,.hero span{font-size:12px}
.hero .jst{font-size:17px}
h1{font-size:21px}
}
@media (max-width:600px){table.board th,table.board td{min-width:2.7em;padding:6px 4px}
table.board th:first-child,table.board td:first-child{min-width:8em;padding-left:8px}}
@media (max-width:380px){header{padding-left:10px}.brand{font-size:14px;gap:7px}header nav a{padding:3px 6px 0;font-size:13.5px}
.hero .big{font-size:40px}.door b{font-size:24px}}
"""

CSS = _CSS.replace("__LIGHT__", _LIGHT)
