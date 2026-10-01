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

## 第5段階（2026-09-29）

### 作ったもの

- `teamSetupsFromLineup`のチーム順を明記し、先攻（teamIds[0]）が1回表の攻撃、後攻（teamIds[1]）が1回表の守備になるエンジンテストを追加しました。投手欄は守備側P枠、打者欄は攻撃側の現在打順スロットから表示します。1回裏では対応が反転します。
- 選手表示を`#背番号 名前`にし、投手・打者欄タップで「ピッチャーを選択」「バッターを選択」を開くようにしました。名簿タブに守備フィルター、検索、引退選手切替、現在出場中の選手の強調表示、選択中選手からの交代確定を追加しました。
- 打者の交代は現在の打順枠、投手の交代は守備側チームのP枠を対象に、通常の`Page.subs`へ記録します。エンジンテストで両方の枠が更新されることを確認します。
- 新規選手フォームに日時入り初期名、背番号、守備、利き腕、打席位置、仮登録を用意しました。仮登録した名簿はチーム単位でlocalStoreへ保存し、再読込で復元します。
- 上部フィールド、塁、捕球順、メモのラベル位置をfieldset風にずらし、日付などの文字に重ならない位置へ調整しました。

### 検証

- `npm test -- --run`: 3ファイル23テスト成功。
- `npx expo export --platform web`: 成功。37ルートを出力しました。既存Expo通知のWeb警告と終了時force-exit表示があります。
- `git diff --check`: 成功。
- `npx tsc --noEmit`: 失敗。既存の opponent-pitchers 型、Supabase Edge FunctionのDeno環境型エラーに加え、元々あったlineup player_snapshotの`show_index`型不足が出たため型定義に追加しました。今回の入力画面由来のエラーは出ていません。
- 要求されたiPad Simulatorスクリーンショット確認はこの作業環境では実施できていません。Web書き出しとテストで確認しました。

### Gitと未完了事項

- branchは`feature/scoring-local`のまま。pushも本番Supabaseへの書き込みもありません。
- `51d1b88 test(scoring): verify top-bottom lineup mapping` と `1592b87 feat(scoring): add roster player selection substitutions` をコミットしました。
- ローカル名簿永続化の`lib/scoring/local-store.ts`は、2件目のコミット時に`.git/index.lock`作成が`Operation not permitted`で拒否されたため、未コミットで残しています。強制操作はしていません。
- 仮登録選手が同期対象になるタイミングと、登録後の選手情報をゲームラインナップへどの粒度で保持するかは未決です。現在は端末内名簿とページ交代イベントに保持し、サーバー送信はしていません。
- 左右の「T」「B」は投・打の利き腕として表示しています。BASS欄の正確な略号の意味はノートで明示されていないため、この解釈にしました。

## 第6段階

- 選手モーダルが空になる原因は、`scoring_roster_players` に存在しない `uniform_no` を含めたSELECTがPostgREST 400となり、初期データ一式のロードを中断していたこと。背番号は `scoring_player_careers` の現行キャリアから取得し、チーム別に結合する `buildRosterPlayers` 関数とユニットテストを追加。守備側P・攻撃側Bのチーム切替は既存の `openPlayer` が正しく `1-state.half` / `state.half` を選んでいた。ラインナップ強調もチームIDを含めて判定するよう修正。
- analyst@example.test でローカル55421へログインし、PostgREST経由で各チームID（`20000000-0000-4000-8000-000000000001/2`）のroster 12件・現行career背番号12件を確認。誤ったroster.uniform_noクエリは400「column ... does not exist」。指定された試合UUID・チームUUID（`...0001/...0002`）は現在のローカルDBに存在せず、実際のseedチームIDは20000000系列。RLSで analyst が阻害されているわけではないことも確認。
- fieldsetラベルの共通表示を白背景・左寄せ・小padding付きでプロトタイプの `.cap` CSS（13px bold、line-height 18px）に合わせ、全対象欄のcaption配置を確認。走者欄はラインナップの選手名を引き、1〜3塁すべて `#背番号 名前` 表示へ変更。
- 検証: `npm test` 4 files / 24 tests passed（roster list builder追加を含む）。`npx expo export --platform web` 成功、37 routesを `dist` へ出力。`git diff --check` clean。TypeScript全体チェックは既存の `app/opponent-pitchers/[name].tsx` の型不一致、Deno Supabase FunctionsのURL import・Deno global型不足で失敗（今回の変更とは無関係）。ブラウザー経由の画面確認はローカルfile URLをブラウザー制御ポリシーがブロックしたため実施できず。試合画面は指定試合がDBにないため実データ表示も確認できず。
- コミット: `dd69e81 fix(scoring): restore player roster selection` は完了。ラベル修正・走者表示修正はコミット操作時の `.git/index.lock` 作成拒否により未コミットで残存（`app/scoring/[id].tsx`）。リモートpushなし。作業ツリーの `supabase/.temp/cli-latest` 自動更新は元の `v2.84.2` に戻した。


## 表示の高速化

- `app/scoring/[id].tsx`でストップウォッチの50ms更新状態を`React.memo`の子コンポーネント内に移し、画面本体がタイマー更新で再描画されないようにしました。コース図のSVG要素配列は投手目線、打者・投手の利き腕、過去投球、現在球に依存する`useMemo`で保持しています。グラウンド図も描画要素を`useMemo`に移し、操作イベントはref経由で最新状態を参照します。開発用`PERF`フラグは`__DEV__ && false`で既定オフです。
- 今回の環境ではiPad SimulatorのCoreSimulatorServiceへ接続できず、フラグを有効にしたタップ計測を実施できませんでした。変更前の実測は約170ms/タップ（SVGを隠すと約125ms）です。変更後の実測値は未取得で、60ms未満の達成を確認していません。画面の数百要素を領域別に`React.memo`境界へ分割する作業も未完了であり、この差分だけでは依頼の性能目標を満たしたとは判断できません。
- 検証: `npm test` は4ファイル24テスト成功。`npx tsc --noEmit`は既存の別画面・Deno関数のエラーに加え、変更中に一時発生したスコアリング画面のエラーを修正し、最終実行では同画面固有のエラーなし。`npx expo export --platform web`は成功し、37ルートを出力しました。終了時にExpoがforce-exitしましたが、出力完了と成功コードを確認しました。iPad Simulator計測と完了確認は未実施です。
- Git commitは`.git/index.lock`作成が`Operation not permitted`で拒否されたため未コミットです。作業ブランチは`feature/scoring-local`で、push・main・本番Supabaseへの操作はありません。

## 入力までの流れ

- トップをBASS風の「試合管理」「新規試合入力／試合入力を再開」「マスター管理」の3択にし、未同期件数を表示します。試合中ゲームがある場合は確認付き「リセット」を出し、プレイを削除せず `suspended` にして保存します。マスターにチームがない、または自チーム・対戦候補に現役選手が9人未満ならガイダンスを表示し、新規作成を無効にします。
- 新規試合画面を追加しました。日付・時刻・表示番号（YYYYMMDDHHmm自動生成と手入力）・球場・BASS資料に記載の天気18種類・ライブ／動画・季節・種別・週・日・試合番号・主審・タグ、両チームの1〜9番・守備位置・選手選択、ラストオーダー、大谷ルールを入力します。必須項目、打順不足、選手重複、守備重複を赤字で示し、ローカルストアへ試合を作成して入力画面へ進みます。マスター読み取りは端末へキャッシュします。
- 試合管理画面にはローカル・サーバーの試合を並べ、番号、日付、チーム、得点欄（保存データにスコアがある場合）、同期状態を表示します。既存の同期処理を共通関数へ移し、管理画面とトップから再利用します。入力画面の「入力終了」は確認後にトップへ戻るようナビゲーションのみ変更しました。
- バリデーションと進行中ゲームを1試合に制限するユニットテストを追加。`npm test` は5ファイル27テスト成功。`npx expo export --platform web` は成功し `dist` を出力しました（Expoが最後に正常終了できずforce-exit表示）。`npx tsc --noEmit` は失敗しますが、エラーは既存の `app/opponent-pitchers/[name].tsx` とDeno用Supabase Edge Functionだけです。`app/scoring`・`lib/scoring`に型エラーはありません。`git diff --check` も成功しました。
- 参照資料の曖昧さ: 天気18項目と季節4・種別5は資料の固定選択肢を採用しました。主審はBASS画面上は欄がない一方今回の要件に列挙されていたので作成画面に設け、必須にはしませんでした（資料にもデータ項目のみとあるため）。記録者欄は追加していません。打順10人分のPは、選択されたチームの投手マスターから自動設定します。
- 手動トレース: (a) 空の端末状態でガイダンス表示・新規入力無効、(b) 有効ゲーム作成・入力画面遷移、(c) 入力終了後に再開表示・未同期数更新、(d) 確認付きリセット後にプレイ保持・保存済み状態、(e) 管理一覧と再開をコード経路・ローカル保存ルールから追跡しましたが、ログイン済み実機でのクリック確認はしていません。よって全項目とも画面実操作は未検証です。特に既存の `app/scoring/[id].tsx` は起動時に結果・球種・チーム等をSupabaseから取得するため、ゲーム作成・保存がオフラインでも、試合入力全体の完全オフライン動作はこの変更では保証できません。得点欄も現状の `LocalGame` に保存スコアがある場合のみ表示し、この入力画面から同期済み表示を手動検証していません。
- `app/scoring/[id].tsx` は「入力終了」の確認後にトップへ移るナビゲーションだけ変更しました。フック追加や入力UIの変更はしていません。Git commitは `.git/index.lock` 作成時の `Operation not permitted` で拒否され、全変更が未コミットです。ブランチは `feature/scoring-local`、pushなし、main・本番Supabaseには触れていません。
- 人が手で確認する項目: ログイン後の初回ガイダンス、9人揃ったチームでの新規作成から入力・終了・再開、プレイを1つ記録した後のリセットとプレイ保持、試合管理の編集／再開とオンライン同期、ネットワークを切った状態で `[id].tsx` が入力に必要なマスターを読み込めるか、実際のスコア表示。同期はローカルSupabase環境を接続した状態だけで確認し、本番には接続しないでください。


## マスター管理の一覧（2026-09-29）

- `/scoring/masters` にチーム・選手・球場・カテゴリ・球種・結果・作戦・メモの8タブ一覧を復元しました。編集と追加から従来フォームへ移動し、保存・無効化後は一覧に戻ります。フォーカス時に再取得し、無効レコードと引退選手は切り替えて表示できます。選手にはチーム絞り込みと名前検索があります。
- `npm test` は27件成功。`npx expo export --platform web` は成功しました。`npx tsc --noEmit` は既存の投球記録型アサーションとEdge FunctionのDeno型エラーで失敗し、今回のscoring画面のエラーはありません。
- 実機/シミュレータでは、8タブの横スクロール、選手のチーム・引退・検索フィルター、編集・追加後の一覧再読込、ヘッダー名を確認してください。

## 同期と既存画面への反映（2026-09-30）

- Part A: `app/scoring/masters.tsx` のチーム一覧はカテゴリ名・本拠地球場名を参照表示し、選手一覧は `scoring_player_careers` の現行背番号を表示します。投打コードは右・左・両、守備位置コードは投・捕・一・二・三・遊・左・中・右・DH、boolean値は○・—へ置き換えました。
- Part B: `lib/scoring/sync-game.ts` に試合・スタメン・プレイの同期、仮登録選手の作成、交代履歴の再構築、分析用 `games` / `pitches` のゲーム単位delete-then-insertを実装しました。プレイは `client_mutation_id` でupsertし、仮選手はローカルで同期用IDを保持して再試行時の重複登録を避けます。同期成功後だけローカルの `synced_at` を更新します。試合管理画面には各試合の日本語エラーを表示します。
- `lib/scoring/to-pitches.ts` はエンジンの `stateAt` / `applyPage` を使う純粋変換です。既存Excel取込と同じ `pitches` の列意味・日本語語彙（表/裏、打席継続/完了、安打・凡打・三振・四球など）を出し、球種は `scoring_ball_types.old_excel_label` を参照します。変換テストはカウント推移、走者ありの安打、三振、四球、回・表裏の切替、交代の6ケースです。
- 新規ローカルmigration `20260930000000_scoring_game_analysis_link.sql` で `games.scoring_game_id` を追加しました。既存migrationは編集していません。
- ローカル Supabase（API 55421 / DB 55422）上でseed analystのIDを使い、同じ `syncScoringGame` 関数を小さな3プレイのゲームに実行しました。API照会結果は `games=1`、`pitches=3`、`scoring_plays=3` です。同期処理内で不足していた `pitches.game_day`列を送らないよう修正後に成功しました。本番Supabaseには接続していません。
- 検証: `npm test` は6ファイル33テスト成功。`npx tsc --noEmit` は既存 `app/opponent-pitchers/[name].tsx` の型エラー1件とSupabase Edge FunctionのDeno型・URL import不足で失敗し、今回の `app/scoring` / `lib/scoring` はエラーなし。`npx expo export --platform web` は `dist` を出力しましたが、Expoが終了待ちのあとforce-exit表示を出しました。`git diff --check` は成功。
- コミット: `e0991ca feat(scoring): 同期データを分析テーブルへ反映`。pushなし。既存の `app/_layout.tsx` 変更とCLIによる `supabase/.temp/cli-latest` 更新は今回のコミットに含めていません。
- すばるの手動確認: iPadでチームのカテゴリ・本拠地、選手の背番号と投打・守備・boolean表記を確認。小さな試合を入力して「試合管理」から同期し、同期済み表示と既存の試合分析・選手成績・相手投手・スカウト画面への反映を確認。ネットワーク切断時に同期エラーが各試合のカード内へ出て、同期済み扱いにならないことも確認してください。

## 2026-09-30 scoring-local mapping fix
- `to-pitches.ts` now maps scoring outcomes to the saved-file vocabulary, maps batted-ball feature/strength, preserves field SVG coordinates, and filters blank pages; sync writes runs and totals from the committed engine state.
- Added coverage for result words, hit fields/coordinates, blank-page exclusion, and line score. `npm test`: 37 passed. `npx tsc --noEmit` still reports existing unrelated errors in `app/opponent-pitchers/[name].tsx` and Deno edge functions; no errors point to changed files.
- No sync was run. Human follow-up: re-sync display game `202609290056` manually. Commit could not be created because writing `.git/index` was denied; changes remain uncommitted.
- Coordinate convention: scoring UI stores absolute field-SVG coordinates (home near x=46,y=238; outward/upward), matching legacy import data and spray-chart rendering.


## 座標を旧Excelに合わせる

- 旧フォームの `course_a.jpg`（351×351px）と `hit_a.png`（353×353px）をアプリの `assets/` に置き、打球図は旧画像の形を背景にしました。画像上の割合を実際のレイアウト寸法から取得し、旧VBAの0.75ポイント/画素で得る旧コントロール寸法（コース263.25pt、打球264.75pt）を掛けて保存します。向き表示を変えてもコースは捕手目線の保存値を保ちます。
- `lib/scoring/coords.ts` に座標定数と変換をまとめました。旧コントロール画像を保持しているページには版マークを付け、旧SVG座標だった未マークページだけを一度変換します。打球図の過去値変換は旧3塁・本塁・1塁の対応による近似です。旧Excel取込値は旧座標としてそのまま読み込みます。
- 自動テスト49件成功。端末画面での実測（iPad各機種、縦横、iPhone）は未実施です。打球図上の守備位置は旧画像のベース形状を元にした初期配置で、各円の実測位置はシミュレーターで確認が必要です。旧VBA画像上のコース5×5グリッド（内側3×3ストライクゾーン）も画面へ反映済みです。シミュレーターで実位置を照合してください。
- `compare-computed.ts` の座標列（43、44、51、52）は各315/315、一致100%です。191列の計算グループ率: state 5308/6300 (84.25%)、lineup 4824/6930 (69.61%)、pitch 4388/4725 (92.87%)、battedBall 1888/1890 (99.89%)、runners 2786/3465 (80.40%)、runningScore 9243/9450 (97.81%)、other 6299/25830 (24.39%)。全セルでは34472/60165 (57.30%)です。比較スクリプトはセル値や実名を表示せず、差分列番号だけを出します。残差の列番号一覧は同スクリプトの `diff-report-computed.md` にあります。
- 191列の残り差は主に空値と0の旧Excel表現、マスタ情報/プレイ状態からまだ再現できない項目です。pitchは95%未達、state/lineup/runners/otherも未達で、個別差の理由調査が必要です。

## 191列の照合（計算のみ）

- 対象315行。比較スクリプトは saved rows との照合計算だけを行い、実行時出力に実名やセル値を含めません。
- 座標（course_x/course_y/hit_x/hit_y、列43・44・51・52）は1260/1260一致（100%）。
- グループ率: state 84.25%、lineup 69.61%、pitch 92.87%、battedBall 99.89%、runners 80.40%、runningScore 97.81%、other 24.39%。100%一致は不要、各グループ95%以上、未達箇所は差分列・行番号だけの理由記録が残作業です。
- 比較スクリプトのグループ定義は領域が重ならない列リストに変更し、打球位置2列を打球率から分けて座標専用100%照合します。

## 圧縮前のメモ（2026-09-30 夕方、Claude）

- ブランチ `feature/scoring-local`（ShigabaseiOS）最新は 6fbedad。テスト51件成功。本番Supabase・mainには触れていない。
- ローカル: Docker → `supabase start`（API 55421 / DB 55422）、Metro 8081（`npx expo start --dev-client`、ログは scratchpad/metro.log）。Dockerが固まったら `pkill -9 -f /Applications/Docker.app` → `open -a Docker` → `supabase start`。
- シミュレーター: iPad Air 11 (M3) 76AE4C88-…（開発用アプリ入り）、iPad mini ED449E14-…（開発用アプリをインストール済み、未ログイン）。開発用アプリの控え: scratchpad/dev-app-backup/SHIGABASE.app。本番用ビルドは `LANG=en_US.UTF-8 npx expo run:ios --configuration Release`。
- テスト用アカウント: analyst@example.test（seed.sql 参照）。
- 座標: 旧Excel準拠（画像ピクセル×0.75ポイント、コース263.25、打球264.75）。全53試合の実データで上限263.35・0.75刻みを確認。シミュレーターでコース中央→(132.1,131.3)、中堅フェンス→(132.4,35.4)で一致。
- 191列（計算のみ、写しなし）: 状態84・打順70・投球93・打球89・走者83・得点98%。測定は private/baseball-platform/export191-check/compare-computed.ts。

### 次にやること
1. 入力画面の見やすさ（すばるの依頼）：打球の図を旧画像と同じ形の線画で描き直し、スペースいっぱいに大きく。守備位置・塁・走者の印も大きく重ならないように。コースは正方形で表示（ゆがみなし）。保存は割合×旧サイズのままなので座標の正しさは変わらない。
2. iPad mini・Air・Pro 13で同じ場所を押して保存値が同じか確認。
3. 191列の残り（各群95%以上か理由の記録）。
4. BASS球種の残り24件と作戦の細区分、本番Supabaseへの展開（要確認）、App Store提出（iPad対応はブランチに入れ済み）。

## 2026-10-01 早朝の状態（Claude更新前の保存）

- ShigabaseiOS `feature/scoring-local` 最新 `1f0f0da`。テスト205件すべて通過。push はしていない。
- 9/30〜10/1にやったこと：
  - 図の配置を大きくし、投球図を線で描き直し、走者を塁より小さい丸に。
  - 走者まわりを実機で一通り確認し、不具合を多数修正。テストは塁8通り×全結果の網羅と、交代・タイブレーク・スキップ・併殺など。
  - 座標の保存値を実機で確認。新しいページに旧Excel座標の印を付け、開き直しでずれる不具合を修正。
  - 交代の規則（出場中・退いた選手は不可、大谷ルールの試合だけ投手を打順に入れられる）。
  - 191列の一致 57%→99.57%。残りの理由は private/baseball-platform/export191-check/remaining-diffs.md。
  - 球種を旧Excelの10種に統一（ボタン・マスタ・保存値）。
  - 試しの試合は端末とローカルDBから削除済み。
- 残り：iPad mini・Pro 13での確認（保留中）、ほかの試合の旧Excelで191列を再測定（ファイル待ち）、本番反映とApp Store提出（要確認）。
- 再開時：Docker が固まっていたら `pkill -9 -f /Applications/Docker.app; open -a Docker` のあと `supabase start`。Metro は 8081。
