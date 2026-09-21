# wbsc-collect — WBSCの試合データをまとめて取る

U-23W杯の対戦相手分析のために、WBSCの大会サイトから試合データを落とす道具です。
何のために集めているかは [スカウティング準備](../private/u23-scouting-prep.md) にあります。

場所は [apps/wbsc-collect/collect.py](../apps/wbsc-collect/collect.py)。
Python 3 の標準ライブラリだけで動き、追加のインストールは要りません。

## 仕組み

WBSCの大会サイト（`wbsc.org` と各大陸連盟の `wbscamericas.org`、`wbscasia.org`、
`wbsceurope.org`）は Inertia.js で作られていて、**HTMLの `<div data-page="...">` に
描画用のJSONがそのまま入っています。** 画面を読み取るのではなく、このJSONを取り出します。
そのため画面の見た目が変わっても壊れにくく、画面に出ていない項目まで取れます。

大会ごとに違うのはドメインとスラッグだけなので、スクリプト上部の `EVENTS` に1行足せば
新しい大会を追加できます。

## 使い方

```bash
python3 apps/wbsc-collect/collect.py --list
python3 apps/wbsc-collect/collect.py --event u23-americas-2025
python3 apps/wbsc-collect/collect.py --all
```

一度落とした試合は `raw/` に残り、次回は再取得しません。途中で止まっても続きから走ります。
1試合あたり1MB前後あるので、読み込みが切れたときは間隔を空けて4回までやり直します。

出力先は `~/野球/U23ワールドカップ2026/05_収集データ/<大会キー>/`。
**選手データなのでこのリポジトリには入れません。**

| ファイル | 中身 |
|---|---|
| `games.json` | 日程と結果の一覧 |
| `raw/<試合ID>.json` | 試合ごとの生データ |
| `batting.csv` | 打者成績。1行が1試合1選手 |
| `pitching.csv` | 投手成績。`spot` が90の枠 |
| `plays.csv` | 打席ごとの記録 |

## 取れるもの

`plays.csv` には画面に出ていない項目が入っています。

- **`pitchheight` / `pitchoutside`** … その打席を決めた1球の到達位置の座標。
  ストライクゾーン上にプロットできます
- `pitch_pitches` / `pitch_balls` / `pitch_strikes` … 打席ごとの投球数
- `balls` / `strikes` / `outs` と各塁の走者、進塁と刺殺
- `result` 系と `hittype` … 打球の種類と処理した野手

`pitching.csv` は投球回・被安打・自責点に加えて、`pitch_pitches`（総球数）、
`pitch_strikes`、`pitch_ground` と `pitch_fly`（ゴロとフライの数）まで入ります。

**そして打席ごとに `utctimestamp` が入っています。** `gameData.gamevideo` に
GameTimeの試合映像のURLが入るので、**この2つを突き合わせれば、打席の頭出しリストを
自動で作れます。** 映像URLの有無は大会によって違います（2024年W杯は50試合すべて、
欧州選手権は20試合すべて、北中米カリブ予選は24試合中12試合、アジア選手権は0件）。

打球には `hitdistance`（飛距離）、`hitpull`（引っ張りか流しか）、`hitlaunch`（打球角度）が
入ります。全打席ではなく、記録された打球のみです（2024年W杯で970件）。
`exitvelo` の枠はありますが値は空でした。

**入っていないもの**は `speed`（球速。全部ゼロ）、`pitchtype`（球種。-1で未分類）、
`hitx` / `hity`（ゼロ。ただし落下点は `hitpull` と `hitdistance` の極座標で取れる）。
球速と球種はTrackmanとBLASTの自前計測で埋める前提になります。

## レポートの書き出し

[build_report.py](../apps/wbsc-collect/build_report.py) が、集めたCSVから
相手11カ国分の1枚のHTMLを作ります。

```bash
python3 apps/wbsc-collect/build_report.py
open ~/野球/U23ワールドカップ2026/06_レポート/対戦相手.html
```

**外部のCSSもJavaScriptも読み込まない単体ファイルです。** 通信が切れていても開けるので、
現地でそのまま使えます。国のタブで切り替え、表の見出しを押すと並べ替わります。

中身は相手ごと・大会ごとに、チームの傾向（犠打、盗塁、四球率、三振率、ゴロ率、
フライ率）、打球の散らばり図、打者の表、投手の表。

**打球の散らばり図は `hitpull`（打球方向の角度）と `hitdistance`（飛距離）から
落下点を出しています。** 打球の種類で色を分けています（ゴロ・ライナー・フライ・ポップ）。
`hittype` の 1〜4 が何を指すかは `narrative` と突き合わせて確かめました。

どの相手にどの大会を見せるかは、スクリプト上部の `OPPONENTS` で決めています。

## 登録済みの大会（2026-09-21 時点）

| キー | 大会 | 試合 |
|---|---|---|
| `u23-wc-2026` | 本大会。11/6〜15 ニカラグア | 開幕後に埋まる |
| `u23-americas-2025` | 北中米カリブ予選。キューバ・パナマ・プエルトリコ | 24 |
| `u23-euro-2025` | U-23欧州選手権。イギリス優勝、チェコ2位 | 20 |
| `asian-championship-2025` | 第31回BFAアジア選手権。台北・韓国 | 22 |
| `u23-wc-2024` | 前回大会。中国・紹興 | 50 |
| `u23-wc-2022` | 2022年大会。台湾 | 50 |

オセアニア予選（オーストラリア）だけ、大会ページのURLが見つかっていません。

## 確かめたこと

2026年9月21日に5大会166試合を実際に取得しました。打者3526行、投手1131行、
打席22437行、生データ101MB。北中米カリブ予選の選手名が、9月に発表された
キューバの予備選考45人と一致することを確認しています。
