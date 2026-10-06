# ケタ感（数字を幅で当てる日替わりゲーム）

1日5問、数字を「90%の自信で入る幅」で答えるiPhoneアプリ。先にブラウザ版で中身を確かめ、同じ夜にiOS版（SwiftUI、iOS 26以降）にした。2026-10-06の深夜に一晩で作った。作った経緯と検証の結果は[開発レポート](../outputs/keta/report.md)にある。

- iOS版のコード：`~/Projects/Keta`（xcodegenの `project.yml` から作る。バンドルID `com.subaruono.Keta`）
- iOS版のテスト：`xcodebuild test -project Keta.xcodeproj -scheme Keta -destination "id=<シミュレータのUDID>"`。数字の読み取り、日替わりの選び方、正直な幅が採点で勝つこと、日付の切り替えを確かめる
- iOS版の画面確認：起動引数 `-screen play|reveal|result`
- ブラウザ版：<https://claude.ai/artifact/Rgen6tgcCC6uMrbNLAyTnH>（非公開のページ）、コード：[index.html](../apps/keta/index.html)、問題は[questions.json](../apps/keta/questions.json)

## 仕組み

- 採点は対数の目盛りでのWinkler区間スコア。点＝100−25×スコア。外れると、はみ出した分の20倍が引かれる。0点を下回ることもある。
- 問題は日本時間の日付から選ぶので、同じ日なら全員が同じ5問になる。練習モードはランダム。
- 自分の的中率はブラウザに保存する。各問題の答えは、ページのデータベースの `answers` に匿名で保存され、「みんなの的中率」として表示される（練習の答えは保存しない）。

## 問題を足すとき

1. [questions.json](../apps/keta/questions.json) に1件足す。出典URLは必ず付ける。
2. `questions.js` を作り直す：`python3 -c "import json;d=json.load(open('apps/keta/questions.json'));open('apps/keta/questions.js','w').write('const QUESTIONS='+json.dumps(d,ensure_ascii=False)+';\n')"`
3. index.html と questions.js を同じURLに公開し直す。

答えが有名な問題（富士山の標高など）は迷う余地がないので入れない。手元で確かめるときは、`.claude/launch.json` の `keta` でサーバーを立てて `preview.html` を開く。

## iOS版の操作と採点（朝の作り込み後）

- 入力は定規の操作：桁を選ぶ（1〜10兆の定規をなぞって離す）→ 幅を決める（帯の移動、両端のつまみ、ピンチ、「狭める・広げる」）。数字での直接入力も残してある。
- 1問の最低点は−200点（`Scoring.floor`）。これより緩くすると正直な幅が得をしなくなる。
- 問題には難しさの段階 `tier`（0〜2）があり、毎日「易2・中2・難1」で出す。同じ日に出すと答えの見当がつく組は `Daily.conflicts` で避ける。
- 単位は「円・人・枚」などの基本単位で持つ。万や億はアプリが表示時に付ける。
- UIテスト `KetaUITests` が初回10問を通しで遊ぶ。画面確認用の起動引数は `-screen play|reveal|reveal-miss|result|share` と `-adjust`、記録を消すのは `-reset`。

- 処方箋は `Calibration.prescription`（10問から）。豆知識は questions.json の `note`。効果音は `Sound.swift` で合成し、ホームでオフにできる。
- 見本の記録で画面を確認するときは、開発版を `-seed` 付きで起動する。

- マスコットは `Penta.swift`（`PentaRig` が形と動き、`PentaView` がSwiftUIに置く部品）。台詞は `PlayView.pentaLine`。考え方のヒントは questions.json の `hint`。表情一覧は `-screen penta` で確認できる。

- ジャンルは questions.json の `genre`（6種類、`Genre.all`）。記録画面は `RecordsView`、確認は `-seed -records`。
- ウィジェットは `KetaWidget` ターゲット。アプリが `Store.publishSummary()` で App Group `group.com.subaruono.Keta` に要約を書き、ウィジェットが読む。表示部分 `WidgetViews.swift` はアプリ側にも入っていて `-screen widget` で確認できる。タップは `keta://play`。
- 初回はチュートリアル（`OnboardingView` と `Tutorial.question`）。確認は `-screen onboarding`。

## iOS版だけの機能

- 数字キーボードの上の「千・万・億」ボタン
- 初回だけ10問にして、1日目から自信の診断を出す
- 的中率の推移グラフ、連続日数、毎朝8時の通知（任意）、共有シート
- 答え合わせのあと0.5秒は「次へ」が効かない（誤タップで正解を見逃さないため）
- 「みんなの的中率」はサーバーがないので未対応

## 配布

- App Store Connect:「ケタ感 - 数字を幅で当てる」（Apple ID 6819563229、SKU keta-2026、バンドルID `com.subaruono.Keta`）。2026-10-06 に作成。アプリの新規作成はAPIでは許されないので、ブラウザで行った。
- 2026-10-06 に 1.0(1) をアップロードし、内部テストグループ「内部テスト」（全ビルドに自動で参加）に配布。テスターはアカウント所有者のみ。
- アップロード手順: Release アーカイブ → `xcodebuild -exportArchive`（method app-store-connect）→ `xcrun altool --upload-app`。APIキーは `~/.appstoreconnect/private_keys/`、発行者IDは AI-OS の `.env` の `ASC_ISSUER_ID`。次のビルドは `CURRENT_PROJECT_VERSION` を上げてから。

## 未確認のこと

- 実機での動作と、TestFlightでの配布。

- 人が遊んだときに、本当に自信過剰が出るか（中心の仮説）。
- データベースへの書き込みが実際の画面で動くか。読み取りだけ確認済み。
