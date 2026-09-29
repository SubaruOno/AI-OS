# SHIGABASE試合記録機能の進捗

**更新日:** 2026-09-29 00:18 JST
**作業先:** `~/Projects/TerakoyaAI/ShigabaseiOS`

## 作ったもの

- `supabase/config.toml` を追加し、既存の `intern-info-deno` とポートが重ならないよう API 55421、DB 55422、Studio 55423 などに設定しました。
- production 型 snapshot からローカル専用 baseline migration を作成しました。players、opponent_teams、games、pitches、profiles、user_roles、app_role、has_role と既存 migration に要る周辺表を含みます。ファイル冒頭に本番へ push しない注意を書きました。
- 既存 migration の初期適用を成立させるため documents を baseline に追加し、投手集計関数の返却列変更をローカル migration 内の `DROP FUNCTION` + `CREATE` に変更しました。
- scoring マスタ、試合、lineup、play、substitution、audit log と RLS を追加しました。試合中の正本は入力イベントです。
- seed に結果39、作戦53、画面表示球種13、牽制詳細19、メモ15、天気18、守備位置16、ダミーチーム2、ダミー選手24と経歴24を追加しました。実名は入れていません。
- `lib/scoring/engine.ts` に prototype の純粋状態計算を移し、`lib/scoring/export191.ts` に保存ファイル順の191列ヘッダーと行出力を追加しました。

## ローカルでの実行

```sh
cd ~/Projects/TerakoyaAI/ShigabaseiOS
supabase start
supabase db reset
npm test
```

ローカル Supabase は 55421/55422/55423 を使います。別プロジェクトの `intern-info-deno` は停止していません。

## 検証

- `supabase db reset`: 成功。baseline、既存 migration、scoring schema、seed が最後まで適用されました。
- SQL counts: results 39、plans 53、ball types 13、pickoff details 19、memos 15、weather 18、positions 16、dummy roster 24。
- `npm test`: 2ファイル14テスト成功。交代と四球、代走、盗塁/牽制アウト、申告敬遠、ボーク、打撃妨害警告、野手選択、単打、本塁打、タイブレーク、3アウト、191列の順と出力を確認しました。
- `npx tsc --noEmit`: 既存の `app/opponent-pitchers/[name].tsx` の型アサーション1件と、既存 Supabase Edge Function の Deno URL import / `Deno` 未定義で失敗します。今回追加した scoring ファイルからの型エラーは表示されませんでした。

## 未完了と判断待ち

- Git の branch 参照・index 更新が OS sandbox で `Operation not permitted` となり、`feature/scoring-local` の作成と小刻み commit ができていません。作業ファイルは現時点で main の未コミット変更です。権限が直ったら feature branch を作って変更を commit してください。push/merge は行っていません。
- BASS球種37件のうち、調査ノートには入力画面の13件と集計項目しか残っておらず、残り24件の正確な名前・属性が未確認です。seed は13件に留めています。元のBASS管理データまたは完全なリストが必要です。
- plan 53件は調査表が全項目を載せていないため、メニュー16件とノート記載の詳細・代表値を組み合わせています。個別の旧Excelラベルや成功/失敗フラグは再照合が要ります。
- `scoring_games` の表示番号と season/kind/week/day/game_number の一意性が同時に必須になっています。大会外の練習試合や番号体系を決める際に、これらの採番方法を確認してください。
- `games` と `pitches` へ scoring から同期する実装は未作成です。設計では正本を scoring 側に置くことが決まっていますが、要件本文の「same-shape write」への変換は次段階です。
- RLS は analyst/admin 書込、認証済み閲覧の初期形です。`scoring_is_team_member` はチーム単位のユーザー所属表が未設計なため、現在 own-team または analyst/admin に閲覧を許しています。誰をチームメンバーとみなすか、人の決定が必要です。
- 191列の出力は基本の状態・スタメン・scoreboard を実装しました。交代後の最新守備履歴、H/R表記、全列の旧語彙変換と守備名表示は未完成です。

## 第2段階（2026-09-29）

### 作ったもの

- `.env.local` を追加し、ExpoからローカルSupabase（API `http://127.0.0.1:55421`）へ接続します。`.gitignore` の `.env*.local` によりGit対象外です。本番の `.env` は読み出していません。
- ローカルseedに次のAuthユーザーと `user_roles` を追加しました。どちらもローカルDBの初期化で作り直されます。
  - analyst: `analyst@example.test` / `shigabase-test-2026`
  - admin: `admin@example.test` / `shigabase-admin-2026`
- トップ画面にanalyst/adminだけが見られる「試合記録」入口を追加しました。アプリ内ルートにも同じrole gateがあります。
- 「試合」「マスタ」タブを追加し、チーム・選手・球場・カテゴリ・球種・結果・作戦・メモの一覧、追加、編集を実装しました。選手は投打・投球フォーム・守備位置、背番号、経歴、旧Excel名の別名欄を持ちます。無効化は選手引退またはマスタ表示フラグの無効化で行います。
- 試合作成は端末内に下書き保存し、日付＋時刻の12桁表示番号、先攻/後攻、Season/Kind/Week/Day/GameNumberの初期値を作ります。テストロスターの先頭9人と投手を暫定スタメンに入れます。同時に進行できるローカル試合は1つです。
- 入力画面は試合状態、打順/投手、スコア、カウント、塁状況と結果選択を表示し、`lib/scoring/engine.ts` で状態を再計算します。プレイはAsyncStorage（iOS/Android）またはlocalStorage（Web）へ保存し、手動の「同期」操作でゲーム・ラインアップ・プレイをローカルSupabaseへupsertします。
- 同期時に既存 `games`/`pitches` も更新します。191列変換を経由しますが、詳細入力UIがない項目は空になります。
- Webで既存Supabaseセッションを復元するときSecureStoreのネイティブAPIが落ちるため、WebだけlocalStorageを使うadapterを追加しました。

### 起動・テスト

```sh
cd ~/Projects/TerakoyaAI/ShigabaseiOS
supabase start
supabase db reset
npx expo start
```

ローカル接続はgitignored `.env.local` が指定します。iPadでは横向き、iPhoneでは縦スクロールで確認してください。Studioは `http://127.0.0.1:55423` です。

### 検証結果

- `supabase db reset`: 成功（ローカルmigrationとseedを再適用）。
- `supabase db lint --local`: 成功、schema errorなし。
- ローカルAuth/API確認: analystユーザーでログイン成功、`scoring_weather`をAPIから取得成功。
- `npm test`: 成功、3ファイル16テスト。
- `npx expo export --platform web`: 成功。出力に `/scoring`、`/scoring/[id]`、`/scoring/master` を含みます。既存notificationsのWeb対応警告と、Expoが最後にforce exitするメッセージは出ますがexportは0終了です。
- `npx tsc --noEmit --pretty false`: 失敗。今回変更した画面・保存層からの型エラーはありません。既存の `app/opponent-pitchers/[name].tsx` の型アサーションと、Supabase Edge Functionを通常tscで検査できないDeno URL import / `Deno` 未定義が残ります。
- `.env.local` は `git check-ignore .env.local` で無視を確認しました。

### 未完了・すばるに確認したいこと

- 試合作成フォームは本仕様どおりではありません。球場・天気・入力方法・タグ・審判・manual display number・ホーム/ビジター選択・9人の選手/守備選択・ラストオーダー・大谷ルール切替はまだ不足し、初期値で下書きを作ります。次段階ではどの項目を最初に必須にするか決めたいです。
- マスタフォームはチーム/選手IDを文字列で直接入力する暫定形です。選手の守備位置は1つだけ、編集時の既存経歴・alias読込と一括置換UIは未完成です。追加で打順候補に選ぶ選手は仮の先頭9人です。
- 球種・結果・作戦・メモは現状「追加」導線がありますが、ID採番/必須属性/内部flagをすべて編集できるフォームではありません。結果や球種の現行seedは削除・上書きせず維持する運用で良いか確認が必要です。
- game/pitches再構築は191列の基本変換までです。入力画面では守備イベント・走者進塁・交代・球種・球速・コース等を十分入力できず、現時点の分析データは完成記録とみなせません。
- 仕様にある「ラストオーダー」の具体的な最新ゲームの選び方（全履歴か同一大会/同じteamか）と、大谷ルールの適用時の打順/投手処理を確認したいです。
- 球種のマスタseedはphase 1記載のとおり表示用13件のみです。BASS完全版37件の正確なリストが必要です。

実装コミット: `06d7eab`（画面・端末保存・手動同期）、`542d095`（ローカルAuthユーザーseed）。seedのcommitは初回にGit index lock作成がOS sandboxで拒否されましたが、再試行で成功しています。ブランチは `feature/scoring-local`、pushしていません。

## 第3段階（2026-09-29）

### 作ったもの

- 入力画面を1512×771基準のReact Nativeレイアウトに置き換え、画面幅に合わせて縮小する枠を追加しました。スコア、B/S/O、投手・打者名、DBの結果・球種・作戦、コース、球速、打球、守備選択、走者入力、交代・タイブレーク用モーダルを配置しました。
- 球種は`scoring_ball_types.display_flag`、結果は`scoring_results.engine_kind`、作戦は表示対象の`show_index`から読込みます。結果名はengine_kindを保持します。
- `teamSetupsFromLineup`を使いラインナップから状態計算を構築しました。背番号がない場合はRosterのshow_indexを使います。投手・打者名はラインナップの選手IDとrosterを照合します。
- 確定ボタンとcheckCommitを接続し、3ストライク時の打席結果不足をブロックするengineテストを追加しました。
- 試合作成モーダルに各チームの打順9人、守備位置、投手、引退選手表示、ラストオーダー、大谷ルールの入力を追加しました。大谷ルールを選ぶと、同一選手の打順行をDHにし、P行にも登録します。

### 検証

- `npm test`: 成功、3ファイル17テスト。3ストライクで進塁/アウト指定がない場合に警告し、アウト指定後は確定可能なことを確認しました。
- `npx expo export --platform web`: 成功、終了コード0。`/scoring`と`/scoring/[id]`を含む37ルートを生成しました。Expoは既存通知Web警告とforce exitメッセージを出しますが、Exported表示後に終了しています。
- `npx tsc --noEmit --pretty false`: 今回のscoring変更由来の型エラーは解消。既存の`app/opponent-pitchers/[name].tsx`およびSupabase Edge FunctionのDeno import/型エラーは残ります。
- BASSプロトタイプの`checkCommit`、`autoMoves`、`commit`、`drawZone`、`drawField`、`runnerClick`の該当箇所を読み、初期動作との比較に使いました。iPadシミュレータでの実操作確認は未実施です。

### 未完了

- 画面はBASSレイアウトの近似骨格です。SVGのフィールド／ゾーン完全描画、投手左右に応じた球種glyph、走者のアウト/盗塁/戻るポップアップと塁タップ、打球位置タップ、捕球・送球順とエラー理由選択、ホームのアウト/得点/打点選択、pickoffモード、タイブレーク各走者・打者・カウント入力、両打ち手選択、イニング終了確認、前ページ修正後の後続ページ再計算と再保存は完全実装されていません。
- 入力中ページは確定までlocalStoreへ永続保存されません。毎確定ページの保存は実装しましたが、画面離脱・クラッシュ時の編集中データ保全がありません。
- ゲーム作成ではラストオーダーの直近ゲーム選定・履歴取得に見直しが必要です。大谷ルールの適用前条件（交代前のみ）と、ゲーム中の交代後に禁止するガードは未実装です。投手＋同一打順選手を重複表示する形のみです。
- 試合作成フォームは球場/天候等の保存候補を一部初期値に固定しており、要件にある全ゲーム属性フォームではありません。
- ブランチ上のcommitは未実施です。Git index書込み制限の結果はこの追記時点では未確認です。push、本番Supabase操作、Metro停止は行っていません。

### すばるの判断が必要な点

- BASSの残り24球種と作戦メニューの全件ラベルは、既存調査ノートに完全情報がなく、現在のseed範囲でよいか別途確認が必要です。
- ラストオーダーは「同一チームの最新試合」を候補にしました。練習/公式戦などの絞込み要件は未確認です。
- 大谷ルールでDHになった選手と投手行を、保存ファイルやlegacy出力でどう表記するかの確認が必要です。
- 2026-09-29 01:15 JST: `git add`/`git commit`を試しましたが、`.git/index.lock`作成がOperation not permittedで拒否されました。4ファイルとこのメモは未commitのままです。強制回避はしていません。

## 第4段階（2026-09-29）

### 作ったもの

- `app/scoring/[id].tsx`を、試作HTMLの1512×771ステージと同じ座標順に置き換えました。画面幅・高さに合わせて均等縮小し、ボタン、入力欄、ラベル、球種、結果、スコアボード、BSO、走者欄をHTMLの位置・寸法で配置しています。
- コース図は投手・打者のシルエット、20px間隔の格子、ストライクゾーン、投球履歴の番号・球速、現在球をSVGで描きました。投手目線の左右反転と投手左右による球種記号の反転を入れています。
- グラウンド図にファウルライン、フェンス、内野、守備位置、打球線、走者トークンと進塁線を描きました。野手タップ、打球位置、牽制先、走者選択、アウト・盗塁・戻る、得点・アウト・打点の入力を接続しました。
- 球速キーの先頭「1」、投球結果・フラグ、4球目の確認、左右の構え、捕手ミットの内外表示、作戦ドロップダウン、打席スキップ確認、エラー種類、交代・タイブレーク、ストップウォッチ、メモ、球種円グラフ、過去ページ移動を実装しました。
- 状態は`stateAt`で過去ページから計算し、ページの編集ごとに端末内localStoreへ保存します。ローカルSupabaseに視覚確認用のテスト試合と打順を作りました。production Supabaseには書き込んでいません。

### 検証

- `npm test`: 成功、3ファイル20テスト。
- `npx expo export --platform web`: 成功、終了コード0。`/scoring/[id]`を含む37ルートを出力しました。既存notificationsのWeb警告とExpoのforce-exit表示はあります。
- `npx tsc --noEmit --pretty false`: 入力画面の型エラーはありません。既存の`app/opponent-pitchers/[name].tsx`、`lib/scoring/engine.ts`の`show_index`型、Supabase Edge FunctionのDeno import/型エラーが残ります。
- 1512×771の画像比較は未完了です。Chrome headlessは終了コード134で停止し、Chrome/Chromiumのheadless撮影でPNGを作れませんでした。既存ブラウザのComputer Useからローカル開発画面へ接続したところ、ブラウザのセキュリティ制御に拒否されました。同じ接続を別経路で試すことは禁止されたため、比較画像は作成していません。`~/Pictures/ai/`に第4段階の画像はありません。

### 残っている差

- 実画面の比較ができていないため、文字幅、フォント差、各要素の重なりなどの視覚差は未確認です。
- 選手交代の画面は簡易入力で、試作の両チームの打順表を一括編集するダイアログと同じ動きではありません。3アウト時の確認表も次打者と得点の表示が中心です。
- 入力終了時の試合編集表は簡易一覧です。表の各打席結果から先頭投球へ戻る操作は未実装です。捕球順は野手タップで追加できますが、入力中の守備選択は確定打球結果があるときに限っています。
- 球種・結果・作戦の見出しとデータはローカルマスタから読みますが、プロトタイプの固定ダミー名称・全メニュー表示との一致は視覚比較で確認できていません。

### Git

- 作業ブランチは`feature/scoring-local`のままです。pushはしていません。画面ファイルのcommitは未実施です。
