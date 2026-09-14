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
