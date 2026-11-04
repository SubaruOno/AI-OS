#!/usr/bin/env python3
"""共有サイトの「探す」と「使い方」。build_site.py から使う。

    TOPICS            検索に出す固定の行き先（ページと節、言いかえの言葉つき）
    guide_page(page)  使い方とTipsのページ（guide/）
    button(root)      ヘッダーの虫めがね。JavaScript が動かないときは使い方のページへ
    search_box()      トップの検索の入口
    plain(text)       HTML を検索用の文字だけにする
    sentences(text)   本文を文に分ける
    dump(entries)     search.json の中身
    CSS, JS           build_site.py が CSS と site.js の後ろに足す

検索はサーバーも外部のAIも使わない。組み立てのときに search.json（ページに載っている文字だけ）を
作り、端末の中で照らし合わせる。電波がなくても動き、打った言葉が外へ出ることもない。
しくみは JS の頭に書いた。
"""

from __future__ import annotations

import html
import json
import re

GUIDE_URL = "guide/"

# (題, 説明, 行き先, 言いかえ)。行き先はサイトの根元から
TOPICS = (
    ("次の日本戦", "トップ", "", "次 試合 いつ 何時 開始 プレーボール 日本戦 残り時間"),
    ("次の相手", "トップ", "#next-opp", "次の対戦相手 対戦国 注目選手"),
    ("今日の試合", "トップ", "#today", "今日 きょう 本日 現地の今日"),
    ("順位表", "トップ", "#standings", "順位 スタンディング 勝敗 ゲーム差 グループ 組"),
    ("全ページを端末に保存", "トップの下のボタン", "#save", "全ページ保存 保存 オフライン 電波 圏外 ダウンロード"),
    ("WBSCの公式ページ", "トップ", "#wbsc", "公式 大会ページ ボックススコア 速報"),
    ("日程と結果", "全試合", "schedule/", "日程 スケジュール 試合予定 結果 スコア 全試合"),
    ("相手国の一覧", "11チーム", "teams/", "相手国 対戦国 国 チーム グループA グループB"),
    ("日本代表", "選手・首脳陣・成績", "japan/", "日本 ジャパン 侍 自チーム"),
    ("日本の選手", "日本代表", "japan/#players", "選手 24人 名簿 メンバー 背番号"),
    ("日本の首脳陣", "日本代表", "japan/#staff", "監督 コーチ スタッフ"),
    ("日本戦の日程と結果", "日本代表", "japan/#games", "日本戦 試合 結果 先発"),
    ("日本の今大会の成績", "日本代表", "japan/#stats", "成績 打者 投手 打率 防御率"),
    ("日本の投手の登板表", "日本代表", "japan/pitching/", "登板 球数 中何日 連投 休養 投球回 ブルペン 何球"),
    ("大会方式", "流れ・持ち越し・規定", "format/", "方式 ルール レギュレーション"),
    ("大会の流れ", "大会方式", "format/#flow", "1次ラウンド スーパーラウンド 順位決定 決勝 3位決定戦 SR"),
    ("持ち越し", "大会方式", "format/#carry", "持ち越し キャリーオーバー スーパーラウンドの勝敗"),
    ("日本の順位ごとの相手", "大会方式", "format/#rank", "組み合わせ 1位なら 2位なら 3位なら スーパーラウンドの相手"),
    ("球場", "大会方式", "format/#venues", "球場 会場 場所 スタジアム グラウンド マナグア マサヤ レオン"),
    ("7回制", "大会方式の規定", "format/#rule-innings", "規定 イニング 何回まで 回数"),
    ("タイブレーク", "大会方式の規定", "format/#rule-tiebreak", "規定 延長 同点 無死一・二塁 ノーアウト 8回 打順"),
    ("コールドゲーム", "大会方式の規定", "format/#rule-called", "規定 コールド 10点差 点差 打ち切り"),
    ("雨などで止まった試合", "大会方式の規定", "format/#rule-rain", "規定 雨 天候 中断 止まった 再開 正式試合 成立 サスペンデッド"),
    ("球数制限", "大会方式の規定", "format/#rule-pitches", "規定 球数 投球数 何球 制限"),
    ("同率の順位の決め方", "大会方式の規定", "format/#rule-tie", "規定 同率 並んだ TQB ER-TQB コイントス 直接対決"),
    ("中止の試合があるとき", "大会方式の規定", "format/#rule-cancel", "規定 中止 世界ランキング"),
    ("先攻と後攻の決め方", "大会方式の規定", "format/#rule-coin", "規定 先攻 後攻 コイントス 技術会議"),
    ("直前合宿", "大会方式", "format/#camp", "合宿 NTT東日本 船橋 千葉"),
    ("時差", "大会方式", "format/#jet", "時差 15時間 日本時間 現地時間 ニカラグア"),
    ("使い方とTips", "このサイトの使い方", GUIDE_URL, "使い方 ヘルプ ガイド Tips コツ"),
    ("最初の設定", "使い方", GUIDE_URL + "#start", "ホーム画面に追加 アイコン Safari LINE はじめ 設定"),
    ("探し方", "使い方", GUIDE_URL + "#find", "検索 虫めがね 探す"),
    ("画面の見方", "使い方", GUIDE_URL + "#read", "見方 時刻 太字 帯 札 最終更新 結果反映 並べ替え"),
    ("映像の見方", "使い方", GUIDE_URL + "#video", "映像 動画 YouTube GameTime 有料 無料 配信 中継 ライブ"),
    ("困ったとき", "使い方", GUIDE_URL + "#trouble", "更新されない 開けない 電波がありません 保存できない 不具合"),
)

ICON = ('<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" '
        'stroke="currentColor" stroke-width="2.4" stroke-linecap="round">'
        '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 21 21"/></svg>')


def button(root: str) -> str:
    return (f'<a class="find-btn" href="{root}{GUIDE_URL}#find" data-find aria-label="サイト内を探す">'
            f"{ICON}</a>")


def search_box() -> str:
    return (f'<a class="find-box" href="{GUIDE_URL}#find" data-find>{ICON}'
            "<span>選手名・国・知りたいことで探す</span></a>"
            f'<p class="find-help"><a href="{GUIDE_URL}">使い方とTips →</a></p>')


def plain(text) -> str:
    """HTML のタグを外し、文字参照を戻す。"""
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(text or "")))).strip()


def sentences(text) -> list[str]:
    """本文を文に分ける。検索の結果には、言葉の入っている文だけを出す。"""
    return [part.strip() for part in re.split(r"(?<=[。．！？])", plain(text)) if part.strip()]


def dump(entries: list[dict]) -> str:
    return json.dumps(entries, ensure_ascii=False, separators=(",", ":")) + "\n"


def guide_page(page) -> str:
    """使い方とTips。page は build_site.page。"""
    root = "../"
    jump = "".join(f'<a href="#{a}">{t}</a>' for a, t in (
        ("start", "最初の設定"), ("find", "探し方"), ("goto", "よく見るページ"),
        ("read", "画面の見方"), ("video", "映像"), ("trouble", "困ったとき")))
    go = "".join(f'<a href="{root}{u}">{t}</a>' for u, t in (
        ("", "次の日本戦"), ("#next-opp", "次の相手"), ("#today", "今日の試合"), ("#standings", "順位表"),
        ("schedule/", "日程と結果"), ("teams/", "相手国"), ("japan/pitching/", "日本の投手の登板表"),
        ("format/#rank", "日本の順位ごとの相手"), ("format/#rules", "規定")))
    examples = "".join(f"<tr><td><b>{q}</b></td><td>{a}</td></tr>" for q, a in (
        ("韓国 左投手", "韓国の左投手の一覧"),
        ("ゴンサレス", "カタカナでも英字の選手名に当たります"),
        ("延世大", "所属や注目選手のメモの中の言葉でも探せます"),
        ("雨で止まったら", "大会方式の規定の該当の行"),
        ("台湾 映像", "日本遠征の打席の映像"),
        ("11/8", "その日の試合")))
    body = "".join([
        '<div class="page-head"><p class="crumbs"><a href="../">トップ</a> / 使い方</p><h1>使い方とTips</h1></div>',
        f'<nav class="toc" aria-label="このページの中">{jump}</nav>',
        '<section id="start"><h2>最初の設定</h2><ol class="steps">'
        "<li>LINEで届いたリンクは、Safariで開き直します。LINEの中で開くと、保存が効かないことがあります。</li>"
        "<li>共有ボタンから「ホーム画面に追加」を選びます。次からはアイコンで開けます。</li>"
        '<li>ホテルのWi-Fiなど電波のよい所で、<a href="../#save">トップの下の「全ページを端末に保存」</a>を押します。'
        "電波がなくても全ページを開けるようになります。</li></ol></section>",
        '<section id="find"><h2>探し方</h2>'
        "<p>右上の虫めがねを押して、見たいものをそのまま打ちます。選手名・国・知りたいことのどれでも探せて、"
        "押すとその場所に飛びます。</p>"
        '<div class="scroll"><table class="plain"><thead><tr><th>打つ言葉の例</th><th>出るもの</th></tr></thead>'
        f"<tbody>{examples}</tbody></table></div>"
        '<p class="note">検索は端末の中だけで動きます。電波がなくても使え、打った言葉はどこにも送られません。'
        "飛び先のページが端末に保存されていないと、電波のない所では開けません。</p></section>",
        f'<section id="goto"><h2>よく見るページ</h2><nav class="days" aria-label="よく見るページ">{go}</nav></section>',
        '<section id="read"><h2>画面の見方</h2><ul>'
        "<li><b>時刻</b>：太字が日本時間、小さい字が現地です。日本は現地の15時間後です。"
        "「今日の試合」だけは現地の日付で選んでいます。</li>"
        "<li><b>上の帯</b>：「最終更新」はサイトを作り直した時刻、「結果反映」はどの試合の結果まで入っているかです。</li>"
        "<li><b>相手国の選手カード</b>：数字は国際大会（WBSC）の記録で、どの大会の数字かはカードに書いています。"
        "「国際大会の記録なし」は、WBSCの大会の記録が見つからない選手です。国内リーグの成績は入っていません。</li>"
        "<li><b>札</b>：「離脱報道」は外れたと報じられた選手、「日本の球団」は日本の球団に所属する選手です。"
        "日程の「1次R」「SR」は、1次ラウンドとスーパーラウンドです。</li>"
        "<li><b>表</b>：成績の表は、見出しを押すと並べ替えられます。横に長い表は指で横に動かせます。</li>"
        "<li><b>順位表の注記</b>：「当該」は並んだチーム同士の試合、「全試合」はそのラウンドの全試合での数字です。</li>"
        "<li><b>閉じた欄</b>：名簿の表、過去の大会の表、場面の一覧は閉じてあります。押すと開きます。</li>"
        "</ul></section>",
        '<section id="video"><h2>映像</h2><ul>'
        "<li><b>台湾の日本遠征</b>：打席ごとの動画を、このサイトの中で見られます。"
        '<a href="../team/chinese-taipei/#video">台湾のページの「日本遠征の打席の映像」</a>から選手を選びます。</li>'
        "<li><b>韓国のKBO</b>：投球の場面だけを抜いた動画を、このサイトの中で見られます。"
        '<a href="../team/korea/#players">韓国のページの選手一覧</a>で「▶ 映像」の付いた選手を押します。投手は左右別まとめ・奪三振集・最近の打席を、打者は左右別まとめ・安打集・三振集・最近の打席を切り替えられます。</li>'
        "<li><b>北中米カリブ予選2025</b>：YouTubeに試合全体の映像があります。選手ページの「場面の一覧」で、"
        "▶ の付いた場面から飛べます。回とカウントを目安に探してください。</li>"
        "<li><b>そのほかの大会</b>：映像は有料の配信やログインが必要な所にあるので、このサイトからはリンクしていません。"
        "今大会の配信はWBSC公式のGameTime（有料）です。</li>"
        "<li>動画は端末に保存されません。電波のある所で見てください。</li></ul></section>",
        '<section id="trouble"><h2>困ったとき</h2><ul>'
        "<li><b>結果が入っていない</b>：更新は手作業なので、試合が終わってすぐには入らないことがあります。"
        "上の帯の「結果反映」で、どこまで入っているかが分かります。</li>"
        "<li><b>「新しい更新があります」と出た</b>：押すと読み込み直します。</li>"
        "<li><b>「保存した内容を表示中」と出た</b>：電波が弱いときの印で、端末に保存した内容を出しています。"
        "電波が戻れば新しい内容になります。</li>"
        "<li><b>「電波がありません」と出てページが開けない</b>：そのページが端末に保存されていません。"
        "電波のよい所で「全ページを端末に保存」を押してください。</li>"
        "<li><b>保存のボタンが効かない</b>：LINEなどアプリの中で開いているかもしれません。Safariで開き直してください。</li>"
        "<li><b>数字や順位がおかしいと思ったら</b>：WBSCの公式ページと見比べてください。"
        "同率の順位はコイントスで決まる場合もあります。</li></ul></section>",
    ])
    return page("使い方とTips", body, GUIDE_URL, "guide")


CSS = """
/* ---- 探す（虫めがね・入口・全画面の検索） */
.find-btn{flex:none;display:inline-flex;align-items:center;justify-content:center;width:44px;min-height:48px;color:#fff}
.find-box{display:flex;align-items:center;gap:10px;min-height:52px;margin:14px 0 0;padding:0 14px;border:1px solid var(--line2);
border-radius:12px;background:var(--card);color:var(--dim);font-size:15px;font-weight:600}
.find-box svg{flex:none;color:var(--text)}
.find-help{margin:2px 0 0;font-size:13px;text-align:right}
.find-help a{display:inline-flex;align-items:center;min-height:44px;font-weight:600}
#find-panel{position:fixed;top:0;right:0;bottom:0;left:0;z-index:20;display:flex;flex-direction:column;background:var(--bg);box-shadow:0 100vh 0 100vh var(--bg)}
.find-bar{flex:none;display:flex;align-items:center;gap:6px;padding:8px 6px 8px 12px;background:var(--head)}
.find-bar input{flex:1;min-width:0;height:44px;padding:0 12px;border:0;border-radius:10px;background:#fff;color:#11151d;
font-size:16px;font-family:inherit;-webkit-appearance:none;appearance:none}
.find-bar input:focus{outline:2px solid var(--accent);outline-offset:1px}
.find-bar button{flex:none;min-width:44px;min-height:44px;padding:0 8px;border:0;background:none;color:#fff;font:inherit;font-size:14px;font-weight:700}
.find-body{flex:1;min-height:0;overflow-y:auto;-webkit-overflow-scrolling:touch;overscroll-behavior:contain;padding:12px 16px 40px}
.find-body h3{margin:16px 0 6px;font-size:13px;font-weight:700;color:var(--dim)}
.find-body h3:first-child{margin-top:2px}
.find-count{margin:0 0 6px;color:var(--dim);font-size:13px}
ul.find-list{margin:0;padding:0;list-style:none}
ul.find-list li{border-top:1px solid var(--line)}
ul.find-list li:first-child{border-top:0}
.find-hit{display:block;min-height:44px;padding:9px 2px;color:var(--text)}
.find-hit b{font-size:15.5px;font-weight:700}
.find-hit .y{margin-left:.5em;color:var(--dim);font-size:12.5px}
.find-hit small{display:block;color:var(--dim);font-size:12.5px;line-height:1.5}
.find-hit i{display:inline-block;margin-right:7px;padding:0 6px;border-radius:4px;background:var(--chip);color:var(--dim);
font-size:11px;font-style:normal;font-weight:700;vertical-align:1px}
.find-more{margin:10px 0 0;color:var(--dim);font-size:13px}
/* ---- 飛んできた先に色を付ける */
li[id]{scroll-margin-top:60px}
li:target{margin:-2px -6px;padding:2px 6px;border-radius:6px;background:var(--t-amber-bg)}
/* ---- 使い方 */
ol.steps{padding-left:1.4em}
#find table td{white-space:normal}
#find table td:first-child{white-space:nowrap}
.toc{scrollbar-width:none}
.toc::-webkit-scrollbar{display:none}
ol.steps li{margin:6px 0}
#read ul li,#video ul li,#trouble ul li{margin:7px 0}
@media (max-width:430px){.brand-more{display:none}}
"""

# 探すときの決まり。
# 1. 文字をそろえる（全角半角・大文字小文字・カタカナとひらがな・アクセント・区切りの記号）。
# 2. 打った文から「を見たい」「どこ」などの言い回しを落とし、助詞で語に分ける（「韓国の左投手」→ 韓国, 左投手）。
# 3. 題・言いかえ・本文の順に重く点を付ける。語がすべて当たった行を先に、一部だけの行は「近い候補」に回す。
# 4. カタカナの語でふつうに当たる行が1つもなければ、英字の選手名と子音の並びで照らす（ゴンサレス gnsrs ＝ Gonzalez gnsrs）。
# 5. それでもなければ、2文字ずつの重なりで打ち間違いを拾う。
JS = r"""
// ---- 探す。組み立てのときに作った search.json を端末の中で照らし合わせる。外へは何も送らない
(function () {
  var script = document.currentScript;
  if (!script) return;
  var BASE = new URL("./", script.src);
  var box = null, input, body, data = null, waiting = false, pushed = false;
  var QUICK = [["次の日本戦", ""], ["次の相手", "#next-opp"], ["今日の試合", "#today"], ["順位表", "#standings"],
    ["日程と結果", "schedule/"], ["相手国", "teams/"], ["日本の投手の登板表", "japan/pitching/"],
    ["規定", "format/#rules"], ["使い方", "guide/"]];
  var SAMPLES = ["韓国 左投手", "ゴンサレス", "延世大", "雨で止まったら", "台湾 映像", "11/8"];

  function latinOnly(c) { return c.normalize("NFD").charAt(0); }
  function fold(s) {  // 文字をそろえる。区切りの記号は残す
    return String(s || "").normalize("NFKC").toLowerCase()
      .replace(/[À-ɏ]/g, latinOnly)
      .replace(/[ァ-ヶ]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0x60); });
  }
  function norm(s) { return fold(s).replace(/[\s・･\-‐−.,'’`"()\[\]「」、。:;\/]/g, ""); }

  var FILLER = /(を|が|は)?(見たい|みたい|見せて|見る|知りたい|しりたい|教えて|おしえて|調べたい|しらべたい|探したい|探す|さがす|どうなる|どうする|どこ|いつ|ください|について|って何|ってなに|とは|ですか|ますか|のこと|やり方|やりかた|方法|仕方|一覧|情報|詳細|詳しく|全部|すべて)/g;
  function tokens(q) {
    var s = String(q || "").normalize("NFKC").replace(FILLER, " ").replace(/[?!。、,]/g, " ");
    var out = [];
    s.split(/[\sのとでにをはが]+/).forEach(function (w) {
      w = w.replace(/(たら|ると|れば|なら)$/, "");
      var n = norm(w);
      if (n.length > 1 || /[^぀-ゟ]/.test(n) && n) out.push(n);
    });
    return out;
  }

  var ROWS = { k: "かきくけこ", g: "がぎぐげご", s: "さしすせそざずぜぞづ", t: "たちつてと", d: "だでど",
    n: "なにぬねのん", m: "まみむめも", r: "らりるれろ", b: "ばびぶべぼゔ", p: "ぱぴぷぺぽ", f: "ふ" };
  var SOUND = {};
  Object.keys(ROWS).forEach(function (k) { ROWS[k].split("").forEach(function (c) { SOUND[c] = k; }); });
  function squeeze(s) { return s.replace(/(.)\1+/g, "$1"); }
  function kanaBones(w) {  // ひらがなの子音の並び
    return squeeze(w.split("").map(function (c) { return SOUND[c] || ""; }).join(""));
  }
  function latinBones(w) {  // 英字の子音の並び（日本語の読みに寄せる）
    return squeeze(w.replace(/ch/g, "t").replace(/sh/g, "s").replace(/ph/g, "f").replace(/th/g, "t")
      .replace(/qu/g, "k").replace(/gu(?=[ei])/g, "g").replace(/c(?=[ei])/g, "s").replace(/[cq]/g, "k")
      .replace(/[zx]/g, "s").replace(/v/g, "b").replace(/l/g, "r").replace(/ng$/, "n")
      .replace(/[aeiouyhjw]/g, ""));
  }

  function prepare(list) {
    list.forEach(function (e) {
      e._t = norm(e.t + (e.y || ""));
      e._w = norm((e.s || "") + (e.w || ""));
      e._b = (e.b || []).map(norm);
      e._n = e.n ? (fold(e.n).match(/[a-z]+/g) || []).map(latinBones) : [];
    });
    return list;
  }
  function one(e, w, bones) {  // 1語の点と、当たった文。bones が真なら子音の並びでも照らす
    if (!w) return null;
    if (e._t === w) return { p: 100 };
    if (e._t.indexOf(w) === 0) return { p: 70 };
    if (e._t.indexOf(w) >= 0) return { p: 50 };
    if (e._w.indexOf(w) >= 0) return { p: 30 };
    if (bones && e._n.length) {
      var b = kanaBones(w);
      if (b.length >= 3) {
        if (e._n.indexOf(b) >= 0) return { p: 28 };
        if (b.length >= 4 && e._n.some(function (x) { return x.indexOf(b) === 0; })) return { p: 20 };
      }
    }
    for (var i = 0; i < e._b.length; i++) if (e._b[i].indexOf(w) >= 0) return { p: 12, s: e.b[i] };
    return null;
  }
  function grams(s) {
    var out = {};
    for (var i = 0; i < s.length - 1; i++) out[s.substr(i, 2)] = 1;
    return out;
  }
  function close(a, b) {  // 2文字ずつの重なり（0〜1）
    var x = grams(a), y = grams(b), n = 0, p = 0, q = 0, k;
    for (k in x) { p++; if (y[k]) n++; }
    for (k in y) q++;
    return p + q ? 2 * n / (p + q) : 0;
  }
  function needsBones(w) {  // かなだけの語で、ふつうに当たる行が1つもないとき
    return /^[ぁ-ゖー]+$/.test(w) && !data.some(function (e) { return one(e, w); });
  }
  function run(q) {
    var whole = norm(q), words = tokens(q), full = [], part = [];
    var bones = {};
    words.concat(whole).forEach(function (t) { bones[t] = needsBones(t); });
    data.forEach(function (e) {
      var w = one(e, whole, bones[whole]), sum = 0, got = 0, snip = "";
      words.forEach(function (t) {
        var r = one(e, t, bones[t]);
        if (r) { got++; sum += r.p; snip = snip || r.s || ""; }
      });
      var rank = e.r || 0;
      if (w) full.push({ e: e, v: w.p * 1.1 + rank, s: w.s || "" });
      else if (words.length && got === words.length) full.push({ e: e, v: sum + (got > 1 ? 40 : 0) + rank, s: snip });
      else if (got) part.push({ e: e, v: sum + rank, s: snip });
    });
    if (!full.length && !part.length && whole.length >= 3) {
      data.forEach(function (e) {
        var c = Math.max(close(whole, e._t), Math.max.apply(null, (e.t.split(/[\s,]+/).map(function (x) {
          return close(whole, norm(x));
        }))));
        if (c >= 0.55) part.push({ e: e, v: c * 100 + (e.r || 0), s: "" });
      });
    }
    function order(a, b) { return b.v - a.v; }
    return { full: full.sort(order), part: part.sort(order) };
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  }
  function hit(item) {
    var e = item.e, li = el("li"), a = el("a", "find-hit");
    a.href = new URL(e.u || "", BASE).href;
    a.appendChild(el("i", "", e.k));
    a.appendChild(el("b", "", e.t));
    if (e.y) a.appendChild(el("span", "y", e.y));
    var sub = item.s ? (item.s.length > 70 ? item.s.slice(0, 69) + "…" : item.s) : (e.s || "");
    if (sub) a.appendChild(el("small", "", sub));
    li.appendChild(a);
    return li;
  }
  function listOf(items) {
    var ul = el("ul", "find-list");
    items.forEach(function (x) { ul.appendChild(hit(x)); });
    return ul;
  }
  function home() {
    body.textContent = "";
    body.appendChild(el("h3", "", "よく見るページ"));
    var nav = el("nav", "days");
    QUICK.forEach(function (x) {
      var a = el("a", "", x[0]);
      a.href = new URL(x[1], BASE).href;
      nav.appendChild(a);
    });
    body.appendChild(nav);
    body.appendChild(el("h3", "", "こんな言葉で探せます"));
    var chips = el("nav", "days");
    SAMPLES.forEach(function (x) {
      var a = el("a", "", x);
      a.href = "#";
      a.setAttribute("data-q", x);
      chips.appendChild(a);
    });
    body.appendChild(chips);
  }
  var LIMIT = 40;
  function show() {
    var q = input.value;
    if (!norm(q)) { home(); return; }
    body.textContent = "";
    if (!data) {
      body.appendChild(el("p", "find-count", waiting ? "読み込み中です…" :
        "検索のデータを読めませんでした。電波のある所で一度開いてください。"));
      return;
    }
    var r = run(q);
    if (!r.full.length && !r.part.length) {
      body.appendChild(el("p", "find-count", "見つかりませんでした。短い言葉や、国の名前で試してください。"));
      return;
    }
    if (r.full.length) {
      body.appendChild(listOf(r.full.slice(0, LIMIT)));
      if (r.full.length > LIMIT) {
        body.appendChild(el("p", "find-more", "ほかに" + (r.full.length - LIMIT) + "件あります。言葉を足すと絞れます。"));
      }
    }
    if (r.part.length && r.full.length < 5) {
      body.appendChild(el("h3", "", "近い候補"));
      body.appendChild(listOf(r.part.slice(0, 15)));
    }
    body.scrollTop = 0;
  }
  function load() {
    if (data || waiting) return;
    waiting = true;
    fetch(new URL("search.json", BASE).href, { cache: "no-cache" }).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    }).then(function (list) {
      data = prepare(list);
    }).catch(function () {}).then(function () {
      waiting = false;
      if (box && !box.hidden) show();
    });
  }
  function lock(on) { document.documentElement.style.overflow = on ? "hidden" : ""; }
  // iPhone はキーボードが出ると、見えている範囲だけが小さくなり、指で動かすとその範囲がずれる。
  // 検索の画面を見えている範囲に合わせ続けて、結果がキーボードに隠れず、画面ごとずれないようにする
  var view = window.visualViewport;
  function fit() {
    if (!view || !box || box.hidden) return;
    box.style.top = view.offsetTop + "px";
    box.style.bottom = "auto";
    box.style.height = view.height + "px";
  }
  if (view) {
    view.addEventListener("resize", fit);
    view.addEventListener("scroll", fit);
  }
  function hide() {
    if (!box || box.hidden) return;
    box.hidden = true;
    box.style.top = box.style.bottom = box.style.height = "";
    lock(false);
  }
  function make() {
    box = el("div");
    box.id = "find-panel";
    box.hidden = true;
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.setAttribute("aria-label", "サイト内を探す");
    var bar = el("div", "find-bar");
    input = el("input");
    input.type = "search";
    input.placeholder = "選手名・国・知りたいこと";
    input.setAttribute("aria-label", "探す言葉");
    input.setAttribute("enterkeyhint", "search");
    input.setAttribute("autocomplete", "off");
    input.setAttribute("autocapitalize", "off");
    var shut = el("button", "", "閉じる");
    shut.type = "button";
    bar.appendChild(input);
    bar.appendChild(shut);
    body = el("div", "find-body");
    box.appendChild(bar);
    box.appendChild(body);
    document.body.appendChild(box);
    input.addEventListener("input", show);
    input.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { shut.click(); return; }
      if (e.key !== "Enter") return;
      e.preventDefault();
      var first = body.querySelector("a.find-hit");
      if (first) first.click();
      else input.blur();
    });
    shut.addEventListener("click", function () {
      if (pushed) { pushed = false; history.back(); } else hide();
    });
    body.addEventListener("click", function (e) {
      var a = e.target.closest ? e.target.closest("a") : null;
      if (!a) return;
      var q = a.getAttribute("data-q");
      if (q) { e.preventDefault(); input.value = q; show(); return; }
      var to = new URL(a.href);
      if (to.pathname !== location.pathname) return;  // 別のページならそのまま移る
      e.preventDefault();
      hide();
      if (to.hash && to.hash !== location.hash) location.hash = to.hash;
      else if (to.hash) reveal();
      else window.scrollTo(0, 0);
    });
  }
  function open(e) {
    e.preventDefault();
    if (!box) make();
    box.hidden = false;
    lock(true);
    fit();
    if (history.pushState) {
      try { history.pushState({ find: 1 }, ""); pushed = true; } catch (err) {}
    }
    show();
    input.focus();
    input.select();
    load();
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest ? e.target.closest("[data-find]") : null;
    if (a) open(e);
  });
  window.addEventListener("popstate", function () { pushed = false; hide(); });

  // ---- 飛んできた先を見せる。閉じた欄の中なら開き、#p・#b（投手・野手の切り替え）は選手の節へ送る
  function reveal() {
    var h = "";
    try { h = decodeURIComponent(location.hash.slice(1)); } catch (err) { return; }
    if (!h) return;
    var t = document.getElementById(h);
    if (!t && (h === "p" || h === "b")) t = document.getElementById("players");
    if (!t) return;
    for (var n = t; n; n = n.parentElement) if (n.tagName === "DETAILS") n.open = true;
    t.scrollIntoView();
  }
  window.addEventListener("hashchange", reveal);
  reveal();
})();
"""
