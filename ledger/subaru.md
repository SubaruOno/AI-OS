# すばる — 作業記録

- 2026-09-01 17:29 · すばる · setup/note · AI OSインストール開始、個人モードを選択、既存ワークスペースなし
- 2026-09-01 17:29 · すばる · setup/decision · Step 1完了、名前を確認
- 2026-09-01 17:51 · すばる · setup/build · Step 2完了。Claudeエクスポート(会話225件・メモリー)とGoogle Drive/Calendarを読み込み、context/you.md・context/people.md・context/tech-stack.md を作成。個人モード(business系ファイル削除、team/data/ディレクトリ削除)。CLAUDE.md/AGENTS.mdをスタンプ済み
- 2026-09-01 18:05 · すばる · setup/build · フォルダ構成を整理。~/AI-OS/ai-os-kit → ~/ai-os-kit に移動し、インストール用の配布ガイド(README・PDF2種・.url)を削除。distribution/skill syncチェックは移動後も正常
- 2026-09-01 18:15 · すばる · setup/build · Slack(terakoyaai.slack.com)を確認し、テラコヤ.AIの実働メンバー(Paul, Shun, Rick, Philippe, Teiichirou)をcontext/people.mdに追記
- 2026-09-01 18:40 · すばる · setup/decision · gitリポジトリのルートがホームディレクトリ全体になっていた問題を修正。空リポジトリを`~/.git.stray-empty-backup`に退避し、`~/AI-OS`単体で再初期化・初回コミット(1305ファイル)。GitHubにprivateリポジトリ`SubaruOno/AI-OS`を作成しremote追加まで完了(push自体はクラシファイアにブロックされ本人が手動実行)
- 2026-09-01 18:55 · すばる · research/note · `~/Projects/TerakoyaAI/ShigabaseiOS`を調査し、構成・技術スタック・既知の課題(バージョン不一致、iOS 26クラッシュ対応中)をdocs/shigabase.mdに記録。GitHub連携は接続済みと確認しcontext/tech-stack.mdを更新
- 2026-09-03 · すばる · research/build · ChatGPTのフルデータエクスポート(会話984件、2023年4月〜2026年8月)を`context/import/chatgpt-export/`に取り込み、25並列エージェントで全件digest化(`conversations_digest.md`)。新たに判明した事実(DSコミュニティ推進会/Worcreaでの活動、テラコヤ.AI Business Development Team所属・虎ノ門オフィス、統計検定3級・漢検準2級、NEXT BASE「BASS」のデータ管理者役、オーケストラでの指揮)をcontext/you.md・people.md・tech-stack.mdに反映
- 2026-09-13 · すばる · setup/build · セッション終了時のログ漏れを防ぐため`.claude/settings.json`に`Stop`フックを追加。未コミットの変更がある間は完了扱いにさせず、ログワークフロー(ledger確認→commit→push)を強制実行させる仕組み。CLAUDE.md/AGENTS.mdの「The rhythm」節にも反映

- 2026-09-13 15:09 · すばる · job-hunt/research · Gmail・締め切りナビ・カレンダーの初期確認を実施。本人用の[進捗記録](../private/job-hunt/2026-09-13/status.md)に確認済み締切と残作業を保存。全件確認は継続中
- 2026-09-13 · すばる · job-hunt/build · Codex(Astraモデル)の就活タスクが利用上限で中断しても引き継げるよう、[handoffドキュメント](../outputs/handoffs/2026-09-13-job-hunt-schedule-check.md)を作成。優先対応(KDDIアンケート等)と次のアクションを明記
- 2026-09-13 15:20 · すばる · job-hunt/note · 上限前の[最新引き継ぎ](../outputs/handoffs/2026-09-13-job-hunt-codex-latest.md)を作成。メール検索15ページ・締切一覧の閲覧範囲、本人回答、未確認事項と再開順を本人用ファイルに保存
- 2026-09-13 15:28 · subaru · job-hunt/research · 利用枠を確認して再開。重要企業4社のメール本文から締切・検査流用・応募完了条件を確認し、[非公開作業記録](../private/job-hunt/2026-09-13/status.md)に保存。

- 2026-09-13 15:35 · subaru · job-hunt/note · 本人指示で調査停止。公式学年暦の確認と通常授業10件の当日分削除・検証を[最新引き継ぎ](../outputs/handoffs/2026-09-13-job-hunt-codex-latest.md)に反映。
- 2026-09-13 15:46 · すばる · job-hunt/build · Claudeで再開。Gmail/カレンダーMCPに接続し、受付完了メールの横断検索で今日締切5社が未提出の可能性が高いと判明(Speeeは本選考エントリー済み確定)。本文確認済みの締切・予定26件をGoogleカレンダーに登録し、色分けで確認済み/要確認を区別。提出自体は本人指示で保留
- 2026-09-13 16:20 · すばる · job-hunt/ship · 本日の4タスクを完了。①Gmail全件スイープ(ATS直送201スレッド)で新規締切8件を発見し[記録](../private/job-hunt/2026-09-13/gmail-sweep.md)。②締め切りナビ975件をcurlで取得し[原票をTSV保存](../private/job-hunt/2026-09-13/simenavi-raw-2028.tsv)、関係企業133件を突合してメール未着のKDDI DS・AI等を発見。③[締切マスター](../private/job-hunt/2026-09-13/master-deadlines.md)を作成し本人と相談、EYはStrategy一本に決定。④夏休みの授業16件を削除し締切42件に3日前・前日通知を設定
- 2026-09-13 · すばる · job-hunt/decision · 今夜23:59締切はKDDIアンケート・ダイフク・大和総研の3件に絞ると決定。EY SCは併願不可のためStrategy Consultant(10/26)一本。今日以降の応募判断は後日
- 2026-09-14 15:39 · すばる · job-hunt/decision · KDDI技術系IS事後アンケートは提出済みと本人確認。9/14のPwC公認会計士キャリアチャレンジ オンラインイベントは不参加に決定。[締切マスター](../private/job-hunt/2026-09-13/master-deadlines.md)に反映
- 2026-09-14 15:44 · すばる · job-hunt/decision · 9/13締切のダイフク3days/2daysと大和総研ITソリューション1Day二次は未提出と本人確認。[締切マスター](../private/job-hunt/2026-09-13/master-deadlines.md)に反映
- 2026-09-14 18:39 · すばる · shigabase/research · SHIGABASEを複数チーム向けの新アプリとして出す案を検討。競合調査と需要検証の計画を[調査メモ](../outputs/2026-09-14-shigabase-multi-team-research.md)に保存

- 2026-09-15 00:26 · subaru · codex/research · 定期実行「毎朝の就活・情報管理チェック」の消費原因を実行履歴から確認。広範囲の画面操作と連携不可日の再実行が要因。設定変更なし。
- 2026-09-15 01:47 · すばる · walk-town/decision · 新アプリ案を「散歩のおみやげで小さな街を作る」に決定(Codexの意見で、すれ違い通信から方向転換)。MVP計画書を[plans/2026-09-15-walk-town-app-mvp.md](../plans/2026-09-15-walk-town-app-mvp.md)に作成
- 2026-09-15 01:51 · すばる · walk-town/research · Codexと世界観・仕掛け・名前・小物12種のアイデア出し。[記録](../outputs/walk-town/2026-09-15-ideation-with-codex.md)。テスター5〜8人は確保済み
- 2026-09-15 01:56 · すばる · walk-town/decision · 世界観「湖畔のよりみち」、仮称「てくてくまち」に決定。計画書を更新し、絵のタッチ決め用の[プロンプト](../outputs/walk-town/2026-09-15-art-prompt-bench.md)を作成
- 2026-09-15 02:04 · すばる · walk-town/decision · 小物の絵は粘土ミニチュア風・草の台付きに決定。残り12枚分の[生成プロンプト](../outputs/walk-town/2026-09-15-art-prompt-bench.md)を作成
- 2026-09-15 02:42 · すばる · walk-town/build · ChatGPTで生成した小物14枚の背景(描き込まれた市松模様)を除去し、~/Projects/tekuteku-art/processed に透過PNGで保存。6×6の街の見本画像を作成
- 2026-09-15 02:54 · すばる · walk-town/build · てくてくまちの土台を~/Projects/walk-townに作成(端末内DB、歩数とデイリーの包み、6×6の街、図鑑、設定、絵はがき)。iOS 26シミュレーターで起動確認。[ドキュメント](../docs/walk-town.md)
- 2026-09-15 03:16 · すばる · walk-town/ship · GitHub CLIを導入し、privateリポジトリSubaruOno/walk-townを作成してpush
- 2026-09-15 03:51 · すばる · walk-town/build · Codexに開封演出・長押しドラッグ・ピンチズームを実装させ、シミュレーターで動作確認してmainに取り込み。デモ動画を~/Projects/tekuteku-art/demo-step7.mp4に保存
- 2026-09-15 04:49 · すばる · walk-town/build · 夜間開発ループ: 住人の手紙(10通)とお礼、初回5包み、時間帯で変わる湖の景色と夜の明かり、手紙で4×4→8×8に広がる土地を実装。各機能をCodexレビュー→修正→シミュレーター撮影で確認しmainへ
- 2026-09-15 05:25 · すばる · walk-town/build · 夜間ループ続き: 住人がお気に入りの場所を使う、散歩便は珍しい物寄り、絵はがき共有、手紙のスタンプ、抽選の救済、散歩前に持ち帰る物を選ぶ、7種類の場所の発見、画面の余白調整。Codexのゲームデザイン評価を反映
- 2026-09-15 05:50 · すばる · walk-town/build · 夜間ループ完了分: 持ち帰りの選択、7種類の場所、住人の後日談と日誌、天気、初回案内、テスト前の歩数処理の修正。Codex再評価で主要3課題が改善判定。[夜間開発レポート](../outputs/walk-town/2026-09-16-overnight-report.md)
- 2026-09-15 05:53 · すばる · walk-town/build · 場所ごとの飾り(電飾、波紋、花びら、旗、ホタル、落ち葉)を追加。後日談の進みで増える
- 2026-09-15 05:58 · すばる · walk-town/build · Codexの実機配布前レビューで出た2件を修正(歩数の保存を1回の書き込みにまとめる、非表示中はアニメーション停止)
- 2026-09-15 06:12 · すばる · walk-town/build · Codex CLIの画像生成で住人5人と紙袋の絵を作成し、仮の人形・手紙の差出人アイコン・紙袋に組み込み。iPhone実機(Expo Go)で接続確認
- 2026-09-15 07:32 · すばる · walk-town/build · 朝の仮説検証ループ: 35仮説を試し、砂浜・絵の対岸・全画面の景色・包みとアイコンの絵・丸い書体・効果音・住人タップ・季節・場所ヒント(金色のマス)などを取り込み。[朝の仮説検証ログ](../outputs/walk-town/2026-09-16-morning-hypotheses.md)
- 2026-09-15 07:41 · すばる · walk-town/build · 朝の仮説検証ループ終盤: 開けたらそのまま置ける、開封時の場所ヒント、トレイの金色の点、場所ができた瞬間の住人のお礼、知らせの重なり修正。計38仮説
- 2026-09-15 10:18 · すばる · walk-town/ship · App Store提出の準備: Codex画像生成でアイコンと宣伝画像の背景5枚、実画面をはめ込んだスクショ5枚(6.9インチ)、説明文・キーワード・年齢区分・審査メモ(store.config.json)、プライバシーポリシーとサポートページ
- 2026-09-15 10:35 · すばる · walk-town/ship · App Store準備: Apple DeveloperにバンドルID com.subaruono.tekutekumachi を登録、プライバシーポリシーとサポートをNotionで公開しURLを設定、審査用連絡先はGit外の.env.storeに保存
