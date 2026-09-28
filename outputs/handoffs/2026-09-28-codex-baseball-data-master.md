# Codexへの引き継ぎ：試合入力のデータ格納・設定・マスタ登録

2026-09-28 夜、Claude Codeからの引き継ぎ。入力画面の動き（1球ごとの入力、走者、交代、訂正）は試作でほぼ固まった。次は「データをどう保存するか」「アプリの中の設定」「マスタ登録（チーム・選手・球場など）」の仕様を決める段階で、ここからCodexに頼む。

これまでの流れは[計画と前半の引き継ぎ](2026-09-28-baseball-platform-plan.md)、全体計画は[野球記録・分析プラットフォーム計画](../../plans/2026-09-28-baseball-scoring-analysis-platform.md)にある。

## 1. 決まっていること（変えない）

- **組み込み先はSHIGABASE**（Expo + Supabase、リポジトリは `~/Projects/TerakoyaAI/ShigabaseiOS`）。iPad＝試合中の入力、iPhone＝確認、Mac・Windows＝Web版。
- **保存するデータの形は旧VBAの191列のまま**。並びは、試合終了時に `End_Form2` が並べ替えたあとの順（保存済みの `試合記録（…）.xlsx` と同じ）。分析マクロ、デバックチェッカー、滋賀大の対策資料ツールがこの順で読むため。
- 使っていない列（○番タイプ、投手背番号、打者タイプ、勝利チーム、得点チーム、タイムの種類など）は入力欄を作らず、空（`0`）のまま残す。
- 入力画面は **BASS（NEXT BASE）を再現してから改善する**。すばるの一番の困りごとは「訂正のしにくさ」。
- 試作の考え方は **「1ページ＝1プレイ。入力だけを保存し、状況（カウント・走者・得点・打順）は毎回最初から計算し直す」**。途中を直すと、その先が全部つじつまの合う状態になる。BASSはここができていない（直したあと1ページずつ確定し直す必要がある）。

## 2. 読むべき資料

| 資料 | 中身 |
|---|---|
| [旧Excelの調査](../../private/baseball-platform/01-vba-input-survey.md) | 191列の形、列の並びが2種類あること、実データの問題（選手名の表記ゆれなど）、VBAの入力の流れ |
| `private/baseball-platform/vba/input/`, `vba/analysis/` | 旧VBAのコード（入力ブック・分析ブック）。`DataInput` と `次のプレイの事前情報入力` が1行の書き方と次の状況の計算 |
| `private/baseball-platform/column-values.txt` | 2025秋リーグ10試合分、各列にどんな値が入っているかの集計 |
| `private/baseball-platform/input-original-copy.xlsm` | 入力ブックのコピー（マクロは実行しない） |
| [BASSの調査](../../private/baseball-platform/02-bass-survey.md) | BASSの画面、座標の仕様、実際に入力して分かった動き（交代・走塁・妨害・訂正・延長・試合編集まで） |
| [試作](../../apps/scoring-prototype/index.html) | 1ファイルのHTML。ブラウザで開けば動く。Dキーで今のページの記録（JSON）が出る |

`private/` はGitに入っていないが、同じMacのこのフォルダーにある。中身（実際の選手名・試合データ）を外部サービスや公開の場所に書き写さないこと。

## 3. 試作が今持っているデータ

1ページ（1プレイ）で保存しているのは「入力だけ」。`blank()` の形：

```text
subs        選手交代 [{t:0先攻/1後攻, slot:0-8 または 'P', no:背番号, bats:右/左/両, pos:2-10(10=DH), throws}]
tb          タイブレーク {bi:打者の打順, r:[1塁,2塁,3塁の打順 or null], b, s, o}
pitch_type  球種（FB, SL, …）
course      コース [x, y]（200×250、捕手目線）
catcher_mitt_position  構え 1内角 2外角 3高め 4真ん中 5内角高 6外角高
ball_speed  球速
res         結果 {label, kind}  kind: S(ストライク) B(ボール) FO(ファウル) IBB BK 1-4(安打) out sac sf e fc io hbp
flags       逆球・ワンバウンド・クイック・WP・PB
plan        作戦 {バント:…, 盗塁:…, エンドラン:…}
batted_ball 打球 {x, y, angle, direction_3_division, direction_5_division}（280×280、ホーム(46,238)）
feature     打球の質 1ゴロ 2フライ 3ライナー
rank        強さ A1 B2 C3 X0
catch_fielder 捕球順 [守備位置 or {pos, err:[エラーの種類]}]
ra          手で入れた走者の動き {0:打者,1-3:走者: {to, out, steal, stealTo, homeOut, scored, rbi, back}}
pickoff_throw_to 牽制先の塁
skip        打席スキップ
memo, time, handP, handB
```

状況は `stateAt(i)` で最初のページから計算する（`applyPre` で交代・タイブレーク → `applyPage` で1プレイ分）。試合の設定（両チームの名前・スタメン・左右）は、今はファイル先頭の `TEAMS` に直書きのダミー。**ここを本物のマスタと試合作成につなぐのが今回の仕事の中心**。

## 4. BASSのデータの形（参考）

BASSは試合（game）とページ（gamedata）を分けて持つ。

- **試合**：`no`（試合ID 9桁・重複不可）、`date`、`time`、`stadium`、`weather`、`method`（ライブ／動画）、`firstTeam`・`secondTeam`、`firstTeamPlayers`・`secondTeamPlayers`（スタメン10人）、`firstTeamChanges`・`secondTeamChanges`（交代のたびに「回・表裏・ページ」とその時点の10人の打順・守備を丸ごと保存）、`tags`、`holds`、`drawGame`、`pitcherData`（投手ごとの球種別の数）。
- **チーム**：`name`、`name_s`（略称）、`name_e`・`name_es`（英語）、`category_id`、`stadium_id`、`mark`、`show_index`。
- **選手**：`name`、`name_s`、`name_e`・`name_es`、`team_id`、`uniform_no`、`position_id`、`t_lr`・`b_lr`（投・打の左右）、`retired`、`affiliation`、`career`（所属と期間・背番号の履歴）、`show_index`。
- **球場**：`name`、`name_s`、英語名、`size`、`left_length`・`right_length`・`center_length`、`home_team_id`。
- **ページ**：1球ごとに約90項目。前の状況（`pre_*_count`）、投手・捕手・打者・走者それぞれの状態、打球、フラグ（`intentional_ball_flag`、`balk`、`tie_brake` など）、集計用の値（`total_pitches`、`innings_pitched`、`earned_runs` など）。詳しくはBASS調査の「座標と記録の仕様」。
- **試合の作成画面**：日付・時刻・試合ID・球場・天気・入力方法・両チーム（後攻が左）・打順（「ラストオーダー」でそのチームの前の試合の打順を呼び出す。なければ「ない」と出る）・タグ。

## 5. 今回お願いしたいこと

**まず仕様書を作り、すばると決めてから実装する。** いきなりコードを書かない。

1. **データ格納の仕様**
   - Supabaseにどう保存するか。試作と同じく「入力（ページ）」を正本として持ち、191列は計算して作るのか、191列の行そのものを持つのか。訂正のしやすさを最優先に、それぞれの利点・欠点を並べて推薦を1つ出す。
   - 191列の各列が、試作のどの入力・どの計算から作れるかの対応表。作れない列、試作に入力が足りない列を洗い出す（旧VBAの `DataInput` と `次のプレイの事前情報入力` を読むこと）。
   - 191列（並べ替え後の順）のExcel／CSVとして書き出せること。旧ファイルとの突き合わせ方法。
   - 試合中に通信が切れたときの扱い（iPadでの入力が止まらないこと）。
2. **中の設定**
   - 球種の並び・球速の範囲、結果ボタン、作戦メニューの中身、エラーの種類など、試作で直書きしているものの中で、チームごとに変えたいものの洗い出し。
3. **マスタ登録**
   - チーム、選手（背番号・左右・守備・在籍期間、表記ゆれを起こさない仕組み）、球場、大会・リーグ（旧Excelの「リーグ戦／練習試合／紅白戦／神宮」、季節・週・日・第何試合）、タグ。
   - 試合の作成（BASSの作成画面＋旧VBA `UserForm1` の項目）と、ラストオーダー。
   - 旧Excelの過去試合を取り込むときに、名前の表記ゆれ（例：髙山／高山）をどう寄せるか。
4. **SHIGABASEの今のSupabaseの表を読んで**、既存の選手・チームの表と重ねられるか確認する。

成果物は `plans/` に仕様書を1つ（Markdown、日本語）。表記は [writing-style](../../reference/writing-style.md) に従う。

## 6. 守ること

- 返事は日本語の です・ます調。すばるは技術者ではない前提で、専門用語は言い換える。
- 実データ（選手名・成績）は `private/` から外に出さない。Gitに入るファイルには書かない。
- `~/Petacot` やTursoには触らない。
- 作業が一区切りしたら [ledger](../../ledger/subaru.md) に1行足す（形式は [AGENTS.md](../../AGENTS.md) の「Working with the ledger」）。
- 大阪ガス硬式野球部の作業をしたら、`private/osakagas-worklog.md` に実際の開始・終了時刻（`date` の値）を書く。

## 7. 未解決・注意

- 二塁打・三塁打のときにBASSが走者を自動で進めるかは未確認。試作では動かしていない。
- 代打は、BASSでは記録上の「代打の印」が付かなかった（代走は付く）。191列で代打をどう表すかは旧VBAで確認が必要。
- BASSのテスト試合（ID 999999901・999999902、タグ「テスト（Claude）」）はBASSに残っている。すばるが後で削除する。
