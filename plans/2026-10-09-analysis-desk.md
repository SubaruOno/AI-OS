# Plan: 分析デスク（対策資料のためのMacアプリ）の最初の版

**Created:** 2026-10-09
**Status:** Implemented（最初の版）
**Request:** 大阪ガスと滋賀大の対策資料づくりを、画面で分析を見て、コメントを書き、資料を書き出すところまで1つのMacアプリで行う。
**Purpose:** スクリプトをコマンドで流し、数字を別のファイルで見ている今の流れを、1つの画面にまとめる。すばるが自分のMacで使い、使いながら直す。

---

## Overview

### What This Plan Accomplishes

`~/Projects/analysis-desk` に、Pythonの分析とHTMLの画面をMacのウィンドウで開くアプリを作る。大阪ガスと滋賀大の対策資料フォルダを開き、野手と投手の分析を画面で見て、コメントを書き、今のスクリプトで資料を書き出せるようにする。探索の結果は [探索メモ](explore-2026-10-09-analysis-desk.md) にある。

### Why This Matters

対策資料は大阪ガスでも滋賀大でも毎回作る。数字を見る、コメントを書く、資料を書き出す、の3つが別々の道具に分かれているため手間がかかり、資料によって数字の定義が食い違うことも起きている。画面の分析を1か所の定義から出すことで、数字のずれにも気づける。

---

## Current State

### Relevant Existing Structure

- 大阪ガスの道具: `~/大阪ガス/分析ツール/`（野手は `run_all.py`、投手は `pitcher_analysis/run_pitcher.py`）。v2のデータスライドは `~/大阪ガス/scripts/create_slide2_a4.py`。作り方は [対策資料づくり](../private/osakagas-taisaku.md) と `~/大阪ガス/CLAUDE.md`
- 滋賀大の道具: `~/野球/対策資料/滋賀大ツール/`（`build_v2.py`、`build_pitcher_shiga.py`、`generate_ippai_matome.py`）。作り方は [滋賀大 対策資料づくり](../docs/shiga-taisaku.md)
- 後輩向けのzip: `~/大阪ガス/野手分析ツール/hitter_scouting/`。判定のルールを `baseball.py`、CSVの読み込みを `io_csv.py` にまとめてある
- チームフォルダ: 大阪ガスは `~/大阪ガス/<チーム>対策資料/`、滋賀大は `~/野球/対策資料/<年と季節>/<大学>対策資料/`
- データの形（2026-10-09に確認）
  - 1球ごとのCSVは大阪ガス30列。滋賀大は同じ30列に「期・打球X・打球Y・試合」を足した34列
  - 打者の左右は「打席」列、投手の左右は「投手利き腕」列に入っている
  - ファイル名がチームごとに揺れる（`全打席結果.csv`、`日本新薬　全打席結果.csv`、`日本生命全打席結果.csv`）。`config.yaml` の `csv_file` に名前がある
  - 投手のデータは `*全投球データ.csv`。大阪ガスでは日本生命にしかない。滋賀大では変換のたびにできる
  - 2025年までの大阪ガスの一部のフォルダ（Honda、TDKなど）には成績CSVしかない
- コメント
  - 滋賀大: `コメント.yaml`（打者名 → 全体・対右・対左・警戒）と `投手コメント.yaml`（投手名 → ページごと）
  - 大阪ガス: 野手はPowerPointに直接書く。投手は `auto_comment.py` の下書きに手を入れる
- このMacの道具: Python 3.9（Xcode付属、pandas・python-pptx・PyYAMLあり）、Node 22、Homebrew、PowerPoint、pdftoppm。uvは入っていない

### Gaps or Problems Being Addressed

- 分析の数字を見る場所、コメントを書く場所、資料を作るコマンドが別々になっている
- ゾーン内スイング率が資料によって違う定義で出ている（大阪ガスのv2データスライドだけ全球で計算）
- どのチームのデータがどこまで揃っているかを、フォルダを開かないと確かめられない

---

## Integration Type

**Classification:** N/A（独立したアプリ）
**Reasoning:** 毎回開いて使う道具なので、ワークスペースのスキルではなく、`~/Projects/` に独立したリポジトリとして置く。
**Location:** `~/Projects/analysis-desk`。使い方は完成後に `docs/analysis-desk.md`
**Auto-discovery:** なし

---

## Proposed Changes

### Summary of Changes

- `~/Projects/analysis-desk` を作り、Git管理する。選手データは入れない
- 判定のルール（ゾーン・スイング・打席の区切り）を `desk/core/baseball.py` に置き、アプリの正本にする。中身はzipの `baseball.py` から始める
- チームフォルダを探して、どのデータが揃っているかを返す
- 1球ごとのCSVを読み、打者別と投手別の集計を、絞り込み（対右・対左、カウント、球種、試合、期）つきで返す
- 画面はReact（Vite）で作り、Pythonの裏側（FastAPI）から数字を受け取る。pywebviewでMacのウィンドウとして開く
- コメントを画面で書き、滋賀大は今のYAMLに、大阪ガスはチームフォルダの `コメント.yaml` に保存する
- 書き出しボタンで今のスクリプトを今のPython（3.9）で呼び、進み具合を画面に出す
- 書き出したPDFをアプリの中で見る。PPTXしかないときはPowerPointでPDFにする
- ダブルクリックで起動できる `分析デスク.app` を作る

### New Files to Create

| File Path | Purpose |
|-----------|---------|
| `~/Projects/analysis-desk/README.md` | 起動の仕方、置き場所、データを入れない決まり |
| `~/Projects/analysis-desk/pyproject.toml` | Pythonの依存（fastapi、uvicorn、pandas、pyyaml、pywebview、python-pptx） |
| `~/Projects/analysis-desk/.gitignore` | CSV・画像・PPTX・PDF・YAMLのデータ、仮想環境、ビルド物を除外 |
| `~/Projects/analysis-desk/desk/core/baseball.py` | 判定のルール。zipの `baseball.py` を元にした正本 |
| `~/Projects/analysis-desk/desk/core/io_csv.py` | 文字コードと見出しの揺れを吸収する読み込み |
| `~/Projects/analysis-desk/desk/core/teams.py` | チームフォルダを探し、揃っているファイルを返す |
| `~/Projects/analysis-desk/desk/core/pitches.py` | 1球ごとのCSVを読み、判定の列（ゾーン内、スイング、打席ID、カウント場面など）を足す |
| `~/Projects/analysis-desk/desk/core/hitter.py` | 打者別の集計 |
| `~/Projects/analysis-desk/desk/core/pitcher.py` | 投手別の集計 |
| `~/Projects/analysis-desk/desk/comments.py` | コメントの読み書き |
| `~/Projects/analysis-desk/desk/export.py` | 書き出しスクリプトの呼び出しとPDF化 |
| `~/Projects/analysis-desk/desk/server.py` | 画面に数字を渡すAPI |
| `~/Projects/analysis-desk/desk/app.py` | サーバーを立ててMacのウィンドウを開く入口 |
| `~/Projects/analysis-desk/web/` | 画面（React＋TypeScript、Vite） |
| `~/Projects/analysis-desk/scripts/make_app.sh` | `分析デスク.app` を作る |
| `~/Projects/analysis-desk/tests/` | 判定と集計の確認 |

### Files to Modify

| File Path | Changes |
|-----------|---------|
| `ledger/subaru.md` | 作業の記録を足す |
| `docs/_index.md` | 完成後に分析デスクの行を足す |
| `context/tech-stack.md` | 完成後に分析デスクの置き場所を足す |

### Files to Delete (if any)

なし。大阪ガスと滋賀大の道具には手を入れない。

---

## Design Decisions

### Key Decisions Made

1. **Python＋HTMLの画面をMacのウィンドウで開く**: 分析も書き出しも今のPythonを活かせる。すばるがStreamlit、SwiftUIと比べて選んだ
2. **画面の分析は新しい共通部分で計算し、書き出しは今のスクリプトを呼ぶ**: 資料はもう完成した形があり、作り直すと崩れるおそれがある。画面だけ1か所の定義から出す
3. **書き出しは今のPython（`/usr/bin/python3`、3.9）で動かす**: 今のスクリプトは3.9とそのライブラリで動いている。アプリ本体の新しいPythonで動かすと、動かなくなる心配が増える
4. **判定のルールはアプリのリポジトリを正本にする**: zipには渡す時点のコピーを入れる。zipの組み立てをこちらにつなぐのは後の作業
5. **ゾーン内SW率と全体SW率を並べて出す**: 大阪ガスのv2データスライドの「Zn内SW」は全球で計算している。どちらの数字も見えるようにし、ラベルで定義を書く
6. **打者の左右はCSVの「打席」列から取る**: `config.yaml` の `left_batters` を手で埋めなくても済む。食い違えば画面に出す
7. **画面のチャートは自前のSVGで描く**: 投球図、9マス、打球方向は資料と同じ座標をそのまま使える。ライブラリの見た目に引っ張られない
8. **選手データはアプリに持たない**: チームフォルダを読みに行くだけ。リポジトリに入れるのはコードだけ
9. **大阪ガスのコメントはチームフォルダの `コメント.yaml` に置く**: 滋賀大と同じ形。資料に入れる工程は、書き出したPPTXのコメント欄に書き込む形で後から足す

### Alternatives Considered

- Streamlit: 早く作れるが、投球図をクリックして絞り込むような操作が作りにくい
- SwiftUI: Macらしいが、分析をSwiftで書き直すか、Pythonを裏で呼ぶ二重構造になる
- 書き出しも共通部分で作り直す: 資料の形が崩れる心配が大きい。最初の版ではやらない
- 画面をビルドなしの素のJavaScriptで書く: 最初は早いが、使いながら直す前提なので、すばるが慣れているReactにした

### Open Questions (if any)

- 大阪ガスのv2データスライドの「Zn内SW」を直すか（アプリとは別の作業）
- 大阪ガスの投手対策の書き出しは、ベースのPPTX（`作戦等_<チーム>.pptx`）を選ぶ必要がある。どこに置くかは使いながら決める
- 球速帯の区切り。社会人（143・137）と大学Ⅱ部で分けるか。最初の版は区切りを出さず、球速の分布で見せる

---

## Step-by-Step Tasks

### Step 1: リポジトリと環境を作る

**Actions:**

- `brew install uv` でuvを入れ、`uv` でPython 3.12の仮想環境を作る
- `~/Projects/analysis-desk` を作って `git init`。`.gitignore` にデータの拡張子（csv、xlsx、pptx、pdf、png、jpg、yaml）、`.venv`、`web/node_modules`、`web/dist` を入れる。設定の雛形のYAMLだけは例外にする
- `pyproject.toml` に依存を書き、`uv sync` で入れる
- `web/` をViteのReact＋TypeScriptで作る

**Files affected:**

- `~/Projects/analysis-desk/pyproject.toml`、`.gitignore`、`README.md`、`web/`

---

### Step 2: 判定のルールと読み込みを移す

**Actions:**

- zipの `baseball.py` と `io_csv.py` を `desk/core/` にコピーし、先頭に出どころと「こちらが正本」と書く
- `pitches.py` に、1球ごとのCSVをDataFrameにして判定の列を足す処理を書く: 球速（数値）、X・Y（数値）、ゾーン内、9マス（打者から見た内外）、スイング、空振り、打席ID、試合ID、打席の中の何球目、カウント場面（初球・打者有利・中間・追い込み）、打席の最終結果、打者の左右、投手の左右
- カウント場面の区切りは滋賀大の `page3.py` に合わせる（初球=0-0、打者有利=ボール先行、中間=0-1と1-1、追い込み=2ストライク）
- 日本新薬と京都外大のCSVで読み込みを確かめる。ゾーン内SW率が、上で確認した数字（全球46.1%、ゾーン内70.4%）と一致することをテストにする

**Files affected:**

- `desk/core/baseball.py`、`io_csv.py`、`pitches.py`、`tests/`

---

### Step 3: チームフォルダを探す

**Actions:**

- `teams.py` で `~/大阪ガス/*対策資料` と `~/野球/対策資料/*/*対策資料` を探す
- 各フォルダについて、1球ごとのCSV（`config.yaml` の `csv_file` を優先し、なければ `*全打席結果.csv`。`_cleaned` などの別版は候補として返す）、投手のCSV（`*全投球データ.csv`）、成績CSV（`*成績_全体.csv`、なければ `*全体.csv`）、切り抜き画像のフォルダ、`output/` の資料、コメントのYAMLを返す
- チームの識別子はフォルダのパスから作る（URLに日本語を入れない）
- 揃っていないデータは「なし」と返し、画面で分かるようにする

**Files affected:**

- `desk/core/teams.py`

---

### Step 4: 打者と投手の集計

**Actions:**

- `hitter.py`: 打者一覧（スタメン順は `config.yaml` の `starters`、残りは打席の多い順）。打者ごとに成績（打席・打数・安打・本塁打・四死球・三振・打率・出塁率・長打率）、選球（全体SW率、ゾーン内SW率、ゾーン外SW率、空振り率、初球SW率）、9マスの打率とスイング率、球種別の結果、カウント場面別、打球性質、投球の点（X・Y・球種・結果）、打球の点（滋賀大は打球X・Y）
- `pitcher.py`: 投手一覧（`config.yaml` の `pitchers` を優先、なければ投球数の多い順）。投手ごとに球種の割合と球速（平均・最速）、対右・対左の成績、カウント場面別の球種、決め球（2ストライクからの球種と結果）、投球の点、ゾーン内率
- 成績CSVがあれば、打者の公式成績はそちらを出す（1球ごとの集計と並べる）
- 絞り込み（対右・対左、カウント場面、球種、試合、期）はどの集計にも同じ形で効くようにする
- 数が少ないもの（打席や球数が10未満）には印をつける

**Files affected:**

- `desk/core/hitter.py`、`desk/core/pitcher.py`、`tests/`

---

### Step 5: APIとウィンドウ

**Actions:**

- `server.py`（FastAPI）に次を作る: チーム一覧、チームの中身、打者一覧と打者の分析、投手一覧と投手の分析、コメントの読み書き、書き出しの開始と進み具合、資料の一覧、画像やPDFの配信（チームフォルダの中のファイルだけ）
- 画面の組み立て済みファイル（`web/dist`）も同じサーバーから配る
- `app.py` で空いているポートにサーバーを立て、pywebviewでウィンドウを開く

**Files affected:**

- `desk/server.py`、`desk/app.py`

---

### Step 6: 画面

**Actions:**

- 左にチーム一覧（大阪ガス・滋賀大に分ける）、チームを開くと「野手」「投手」「資料」のタブ
- 野手: 左に打者一覧、右に成績カード、選球の数字（ゾーン内SW率と全体SW率を並べる）、投球図（ゾーンの枠と点、球種で色分け、結果で形を変える）、9マス（打率とスイング率の切り替え）、球種別の表、カウント場面別の表、打球方向（滋賀大は点で描き、大阪ガスは切り抜き画像）
- 投手: 球種の割合、球速、対右・対左、カウント場面別の配球、決め球、投球図
- 上の段に絞り込み（対右・対左、カウント場面、球種、試合、期）
- 文字の大きさや色は、対策資料の見た目に寄せる。数の少ない値は薄く出す

**Files affected:**

- `web/src/`

---

### Step 7: コメント

**Actions:**

- 打者の画面の横にコメント欄（全体・対右・対左・警戒）、投手の画面にページごとの欄を置く
- 滋賀大は `コメント.yaml` と `投手コメント.yaml` を読み書きする。キーの形と順番を崩さない。保存の前に前の版を `.bak` で残す
- 大阪ガスはチームフォルダの `コメント.yaml` に同じ形で保存する。資料への書き込みは、書き出したPPTXのコメント欄の形を調べてから足す
- 打ちながら自動で保存する（少し待ってから保存）

**Files affected:**

- `desk/comments.py`、`web/src/`

---

### Step 8: 書き出しと資料の確認

**Actions:**

- 「資料」タブに、書き出しボタンと `output/` の資料一覧を置く
- 大阪ガスの野手は `run_all.py` と `generate_ippai_matome.py`、滋賀大の野手は `build_v2.py` と `generate_ippai_matome.py`、滋賀大の投手は `build_pitcher_shiga.py` を `/usr/bin/python3` で呼ぶ。`input()` の確認待ちがあるものは、標準入力に答えを渡すか止まらない引数を使う
- 進み具合（スクリプトの出力）を画面に流す
- PDFはアプリの中でそのまま表示する。PPTXしかないときはPowerPointでPDFにする（`~/Library/Containers/com.microsoft.Powerpoint/Data/` に書き出すと許可画面が出ない）
- 大阪ガスの投手（`run_pitcher.py`）は、ベースのPPTXを選ぶ欄を置く

**Files affected:**

- `desk/export.py`、`web/src/`

---

### Step 9: 起動の仕方

**Actions:**

- `scripts/make_app.sh` で `分析デスク.app` を作る（中身は仮想環境のPythonで `desk.app` を開くだけ）
- `README.md` に起動の仕方、データを入れない決まり、正本の場所を書く

**Files affected:**

- `scripts/make_app.sh`、`README.md`

---

### Step 10: 確かめて記録する

**Actions:**

- 日本新薬（大阪ガス）、日本生命（大阪ガス、投手データあり）、京都外大（滋賀大）の3つで、全部の画面を開いて確かめる
- 画面の数字を、今の資料や分析ページ（滋賀大の `打者分析.json` など）と何人か照らし合わせる
- 画面写真を `~/Pictures/ai/` に置いてすばるに見せる
- `docs/analysis-desk.md` を書き、[文書の索引](../docs/_index.md) と [道具の一覧](../context/tech-stack.md) に足す
- ledgerに記録する

**Files affected:**

- `docs/analysis-desk.md`、`docs/_index.md`、`context/tech-stack.md`、`ledger/subaru.md`

---

## Connections & Dependencies

### Files That Reference This Area

- [対策資料づくり](../private/osakagas-taisaku.md) と [滋賀大 対策資料づくり](../docs/shiga-taisaku.md) に、アプリからも作れることを後で書き足す
- [野手分析パッケージの計画](2026-10-09-osakagas-hitter-package.md): 判定のルールの正本がアプリ側に移ることを書き足す

### Updates Needed for Consistency

- 完成したら `docs/_index.md` と `context/tech-stack.md` に分析デスクを足す

### Impact on Existing Workflows

- 今のスクリプトには手を入れない。コマンドで作る今のやり方はそのまま使える
- 大阪ガスの対策資料の作業時間は、今までどおり [出勤記録](../private/osakagas-worklog.md) に書く

---

## Validation Checklist

- [ ] 日本新薬のゾーン内SW率（チーム全体）が70.4%、全体SW率が46.1%と出る
- [ ] 大阪ガスと滋賀大のチームが一覧に出て、データの揃い具合が分かる
- [ ] 日本新薬・日本生命・京都外大で、野手と投手の画面が開き、絞り込みで数字が変わる
- [ ] 京都外大の打者の数字が、滋賀大の `打者分析.json` と合う（定義が同じもの）
- [ ] コメントを書いて閉じ、開き直すと残っている。滋賀大のYAMLの形が崩れていない
- [ ] 書き出しボタンで今と同じPPTXができ、PDFがアプリの中で見られる
- [ ] `分析デスク.app` のダブルクリックで開く
- [ ] リポジトリに選手データが1つも入っていない（`git ls-files` で確認）

---

## Success Criteria

1. すばるが `分析デスク.app` を開き、大阪ガスと滋賀大のどちらのチームでも、野手と投手の分析を画面で見られる
2. 画面でコメントを書き、資料を書き出し、書き出した資料をアプリの中で確かめられる
3. 画面の数字の定義が1か所（`desk/core/baseball.py`）から出ている

---

## Notes

- すばるは「一回作ってみて、使いながら直したい」。見た目や並びの細部はこの計画で決めきらず、画面を見てもらってから直す
- 後からやること: 滋賀大のExcel変換ボタン、BASSのCSVの取り込みと点検、データ点検の画面、大阪ガスのPPTXへのコメント書き込み、zipの組み立てを正本につなぐ
- 大阪ガスのv2データスライドの「Zn内SW」の定義は、アプリとは別に直すかを決める

---

## Implementation Notes

**Implemented:** 2026-10-09

### Summary

`~/Projects/analysis-desk` に最初の版を作った。`~/Applications/分析デスク.app` で開く。大阪ガス20チームと滋賀大3チームが一覧に出て、
野手・投手・資料の3つのタブが動く。使い方は [分析デスク](../docs/analysis-desk.md)。

### Deviations from Plan

- 打席の区切り方を変えた。最初はCSVの並び順で区切ったが、滋賀大のCSVは並び順が時間順とは限らず、
  結果の行が2回入っていることもあったため、試合・イニング・打者が同じ球をまとめて区切る形にした。
  京都外大の「終わっていない打席」は47から4に減った
- 判定のルールを3点直した（失策出塁・野手選択を打席の終わりに足す、ボークをスイングに数えない、13分割のゾーン）
- 覚えておく内容（前回のチームとタブ）は、ウィンドウの保存場所が閉じるときに消えるため、
  `~/Library/Application Support/analysis-desk/state.json` に置いた
- 画面写真を `~/Pictures/ai/` に保存しようとしたが、この環境に画面収録の権限がなく保存できなかった
- リポジトリは `git init` と `git add` までで、まだコミットしていない。GitHubにも上げていない

### Issues Encountered

- 日本生命の `全投球データ.csv` は、ファイル名の濁点の持ち方（NFD）が違い、最初は見つからなかった。比べる前に揃えるようにした
- 公式成績CSVと照らし合わせると、7チーム中2チームは全員一致、残りは各チーム1人が1打席違う。
  滋賀大の2件は、`convert_shiga.py` が振り逃げを打席に数えていないため
- 滋賀大の投手分析（`分析/投手分析.json`）と比べると、北岡投手の球数・球種の割合・ゾーン率・初球ストライク率・三振数・四死球数は一致した。
  対戦打者数だけ、アプリが221、分析ファイルが215で6違う。分析ファイルは元のExcelから数えていて、理由はまだ突き止めていない
- 大阪ガスの書き出しは、本物のフォルダを上書きするので流していない。滋賀大の3つとPDF化は作業用コピーで確かめた

### Validation Checklist

- [x] 日本新薬のゾーン内SW率（チーム全体）が70.4%、全体SW率が46.1%と出る
- [x] 大阪ガスと滋賀大のチームが一覧に出て、データの揃い具合が分かる
- [x] 日本新薬・日本生命・京都外大で、野手と投手の画面が開き、絞り込みで数字が変わる
- [x] 京都外大の投手の数字が、滋賀大の `投手分析.json` と合う（定義が同じもの。対戦打者数だけ6違う）
- [x] コメントを書いて保存すると、書き換えた欄だけが変わる（作業用コピーとテストで確認）
- [x] 書き出しボタンで今と同じPPTXができ、PDFがアプリの中で見られる（滋賀大、作業用コピー）
- [x] `分析デスク.app` のダブルクリックで開き、閉じて開き直すと前回のチームとタブから始まる
- [x] リポジトリに選手データが1つも入っていない（`git ls-files` で確認）
