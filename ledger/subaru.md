# すばる — 作業記録

- 2026-09-01 17:29 · すばる · setup/note · AI OSインストール開始、個人モードを選択、既存ワークスペースなし
- 2026-09-01 17:29 · すばる · setup/decision · Step 1完了、名前を確認
- 2026-09-01 17:51 · すばる · setup/build · Step 2完了。Claudeエクスポート(会話225件・メモリー)とGoogle Drive/Calendarを読み込み、context/you.md・context/people.md・context/tech-stack.md を作成。個人モード(business系ファイル削除、team/data/ディレクトリ削除)。CLAUDE.md/AGENTS.mdをスタンプ済み
- 2026-09-01 18:05 · すばる · setup/build · フォルダ構成を整理。~/AI-OS/ai-os-kit → ~/ai-os-kit に移動し、インストール用の配布ガイド(README・PDF2種・.url)を削除。distribution/skill syncチェックは移動後も正常
- 2026-09-01 18:15 · すばる · setup/build · Slack(terakoyaai.slack.com)を確認し、テラコヤ.AIの実働メンバー(Paul, Shun, Rick, Philippe, Teiichirou)をcontext/people.mdに追記
- 2026-09-01 18:40 · すばる · setup/decision · gitリポジトリのルートがホームディレクトリ全体になっていた問題を修正。空リポジトリを`~/.git.stray-empty-backup`に退避し、`~/AI-OS`単体で再初期化・初回コミット(1305ファイル)。GitHubにprivateリポジトリ`SubaruOno/AI-OS`を作成しremote追加まで完了(push自体はクラシファイアにブロックされ本人が手動実行)
- 2026-09-01 18:55 · すばる · research/note · `~/Projects/TerakoyaAI/ShigabaseiOS`を調査し、構成・技術スタック・既知の課題(バージョン不一致、iOS 26クラッシュ対応中)をdocs/shigabase.mdに記録。GitHub連携は接続済みと確認しcontext/tech-stack.mdを更新
- 2026-09-03 · すばる · research/build · ChatGPTのフルデータエクスポート(会話984件、2023年4月〜2026年8月)を`context/import/chatgpt-export/`に取り込み、25並列エージェントで全件digest化(`conversations_digest.md`)。新たに判明した事実(DSコミュニティ推進会/Worcreaでの活動、テラコヤ.AI Business Development Team所属・虎ノ門オフィス、統計検定3級・漢検準2級、NEXT BASE「BASS」のデータ管理者役、オーケストラでの指揮)をcontext/you.md・people.md・tech-stack.mdに反映
