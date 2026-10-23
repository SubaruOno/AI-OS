# SHIGABASE

すばるが個人開発している大学野球部向けアプリ。コードはこのワークスペースの外、
`~/Projects/TerakoyaAI/ShigabaseiOS` にある(GitHub: `SubaruOno/ShigabaseiOS`、
privateリポジトリ、originに設定済み)。このドキュメントはAI-OS側で作業する際に
参照する構成メモで、実装そのものはSHIGABASE側のリポジトリで行う。

## 何をするアプリか

大学野球部のチーム運用アプリ。選手・アナリスト・admin・OB(卒業生)のロール制で、
以下をカバーする:

- ブルペン投球の記録(`app/bullpen/`)
- 試合分析・スコア・ラインスコア(`app/game-analysis/`, `app/scores.tsx`)
- 対戦投手のスカウティング(`app/opponent-pitchers/`)
- 選手成績(`app/player-stats/`)、アナリティクス/スカウト画面(`app/analytics/`)
- 体重管理と体重リマインド通知(`app/weight*.tsx`)
- 動画ライブラリ(YouTubeのタイムスタンプ連携)、資料共有、チームメッセージ

[context/you.md](../context/you.md) では「選手コンディション管理アプリ」と紹介しているが、
実際のスコープはそれより広く、投球・打撃データ分析やスカウティングまで含む。

## 技術スタック

Expo SDK 54 / React Native 0.81.5 / React 19、expo-router(file-based routing、
typed routes有効)、TanStack Query、Supabase(Auth + Postgres + Edge Functions)、
react-native-gifted-charts・react-native-svgで投球コース図やスプレーチャートを描画。
配布はEAS Build/Submit(iOS本番プロファイルは`autoIncrement`有効)。

## 主なディレクトリ

- `app/` — 画面(expo-router)
- `components/` — 共通UI。`pitch-location-chart.tsx`・`spray-chart.tsx`・`pitch-type-pie-chart.tsx`など分析系チャートも含む
- `hooks/use-auth.tsx` — Supabase認証とロール取得(`user_roles`テーブル)。ロールは`player` / `analyst` / `admin` / `ob`の4種
- `lib/` — Supabaseクライアント、打撃・分析系の集計ロジック、YouTube連携
- `supabase/functions/` — Edge Functions。`import-game-excel`(試合Excel取込)、`weight-reminder`、`notify-on-insert`、`update-linescore`、`fetch-youtube-timestamps`
- `supabase/migrations/` — スキーマ履歴。体重管理、対戦投手サマリー、通知トリガー、`app_config`など

## 現状(2026-09-01時点で確認)

- バージョン表記が不一致: `app.json`は1.6.0だが`package.json`は1.4.0のまま
- bundle id `com.subaruono.shigabaseios`、EAS project `732321f9-86fe-4f12-bb36-312c6907839e`
- 直近のコミットはiOS 26でのクラッシュ対応が中心。`react-native-reanimated`/`worklets`のバージョン不整合と、`messages.tsx`のフック順序違反によるスプラッシュ画面ハングを修正しているが、最新コミット(`8c28f2d`)がデバッグログ追加なので完全解決の確認はまだ途中と見られる
- GitHubリモートは既に設定済み・private。[context/tech-stack.md](../context/tech-stack.md)のインテグレーションキューにあった「GitHub連携待ち」は解消済み
- (2026-10-23確認)ブラウザ版(`npx expo start --web`)は、起動直後に止まる。`app/_layout.tsx` の `Notifications.useLastNotificationResponse` がWebでは使えないため。画面の確認はiOSシミュレーターで行う

## パスワードの再設定(2026-10-23に作り直し)

それまでのアプリは再設定のメールを送るだけで、届いたあとに新しいパスワードを決める画面がなく、最後まで進めなかった。今は次の流れで動く。

1. ログイン画面の「パスワードをお忘れですか？」でメールアドレスを入れると、6桁のコードがメールで届く
2. `app/reset-password.tsx` の画面でコードと新しいパスワード(8文字以上)を入れる。コードを確かめた時点でログイン状態になり、そのままホームへ進む

- メールにはリンクを入れず、コードだけを載せる。大学のメール(Microsoft 365)のように受信時にリンクを先回りして開くところでは、開かれた時点でコードも使えなくなるため。文面の正本は `supabase/templates/recovery.html` で、手元の練習用Supabaseは `supabase/config.toml` 経由でこれを読む
- 管理画面の一括登録で作ったアカウント(`player[背番号]@shiga-baseball.internal`)は実在しないアドレスなので、メールは届かない。アプリはこの宛先には送らず、管理者に聞くよう案内する
- 判定とエラーの言い方は `lib/password-reset.ts`、テストは `lib/__tests__/password-reset.test.ts`

## パスワードの変更と管理者の再発行(2026-10-23に追加)

メールが届かない一括登録の部員も、パスワードを変えられるようにした。

- メニューの「パスワードを変更する」(`app/change-password.tsx`)。今のパスワードでログインし直して確かめてから、新しいパスワードに変える
- 管理者はロール管理タブの「パスワードを再発行」で、部員のパスワードを仮のものに決め直せる。仮のパスワードは12字(4字ずつ「-」で区切る)で、画面を閉じると二度と表示しない。管理者は自分の行には出ない。処理はEdge Function `admin-reset-password` で、呼んだ人が管理者かをデータベースで確かめる
- 仮のパスワードには印(`user_metadata.must_change_password`)が付く。その人がログインすると、ホームではなく変更の画面が開く。「あとで変える」も選べ、そのあいだはメニューに注意が出る。本人が変えると印が外れる
- 一括登録の初期パスワード(`shiga`＋背番号)でログインしたときも、同じように変更の画面が開く。背番号を知っていれば誰でもログインできてしまうため。初期パスワードかどうかはログインの時に入力された値と比べるだけで、どこにも残さない
- 仮のパスワードを作る処理は `supabase/functions/_shared/temporary-password.ts`、テストは `lib/__tests__/temporary-password.test.ts`

## 本番で使うまでに要る作業

ここまでの変更は SHIGABASE側の `fix/password-reset` ブランチにある(2026-10-23時点で未コミット)。iPhone 17 ProとiPad Pro 13インチのシミュレーターで、手元の練習用Supabaseを相手に一通り確かめた。管理者でない人の再発行が断られることも、仕組みの側で確かめてある。本番の設定は読めておらず、今どうなっているかは確かめていない。

- Authentication → Emails → Templates の Reset Password を、`supabase/templates/recovery.html` と同じ件名・本文にする
- Authentication → Emails → SMTP Settings で、独自のメール送信(Custom SMTP)が有効かを見る。Supabase標準の送信のままだと、組織のメンバー以外のアドレスには届かず、送れる数もごく少ない
- Edge Function `admin-reset-password` を本番に反映する(`supabase functions deploy admin-reset-password --project-ref qmbqywqtkstwswslgnvo`)。反映するまでは、再発行のボタンを押すとエラーになる
- これらを済ませてから、新しいビルドを配る

## 投球コースの座標(試合データ共通)

京滋リーグの全試合Excel(`コースX`・`コースY`)とアプリの `course_x`・`course_y` は同じ座標で、
正本は `components/pitch-location-chart.tsx` の冒頭コメント。

- 264×264、左上が原点、**捕手視点**。0は「記録なし」なので集計から外す
- ストライクゾーンは両軸 53.25〜210.75、3×3の区切りは 105.75 と 158.25
- Xが小さい左側が**右打者の内角・左打者の外角**。打者の左右は `打席左右` 列で取る
- 打球位置(`打球位置X/Y`)は本塁が下、Xが小さい側が左翼の球場図

`~/野球/対策資料/分析コード/` の旧スクリプトはこの判定が逆や左右無視になっていたため、
2026年9月27日に `analyze_hits.py`・`analyze_outs.py`・`gen_shigaken_batter_md.py` を修正した。
修正前のコピーは `~/野球/対策資料/分析コード_修正前バックアップ_20260927/`。
