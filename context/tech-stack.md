# Tech stack

> Filled during install, 2026-09-01. 個人ワークスペースなので「ビジネスツール」ではなく、すばるが実際に使っている道具の一覧。

## Platforms

| Platform | 用途 | 連携状況 |
|---|---|---|
| Google Drive | 大阪ガス・RAUD・ゼミの資料、就活書類 | 接続済み |
| Google Calendar | 授業・野球活動・就活イベントのスケジュール | 接続済み |
| Gmail | 就活の連絡・締切管理、企業マイページの確認 | 未接続(claude.aiでは使用歴あり、Step5で接続予定) |
| Notion | ES下書きの保管 | 未接続 |
| Claude.ai (別アカウント) | これまでの会話・メモリー、`context/import/`に取り込み済み | — |
| ChatGPT (別アカウント) | 会話984件(2023年4月〜2026年8月)のフルエクスポート、`context/import/chatgpt-export/`に取り込み済み | — |

## 分析・開発でよく使う道具

Python、R(lme4、lavaan)、JavaScript/React Native/Expo/Supabase、Excel(openpyxl)、PDFレポート生成(ReportLab/WeasyPrint)。野球データはBlast Motion・Trackman・Rapsodoの計測データに加え、大阪ガスチームのスコアリングプラットフォームNEXT BASE「BASS」を管理者として扱う。

## Integration queue

1. Gmail(就活管理に直結するので優先度高)

SHIGABASEのGitHub連携は接続済み(`SubaruOno/ShigabaseiOS`、private)。詳細は
[docs/shigabase.md](../docs/shigabase.md)を参照。

新アプリ「てくてくまち」のコードは `~/Projects/walk-town`(GitHub: `SubaruOno/walk-town`、private)。詳細は
[docs/walk-town.md](../docs/walk-town.md)を参照。
