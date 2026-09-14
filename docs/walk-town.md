# てくてくまち(walk-town)

散歩するとおみやげの小物が届き、湖畔の6×6マスの街に飾って眺めるiOSアプリ。すばるが個人開発中の検証版(MVP)。計画は[MVP計画書](../plans/2026-09-15-walk-town-app-mvp.md)、アイデアの経緯は[アイデア出しの記録](../outputs/walk-town/2026-09-15-ideation-with-codex.md)。

コードはこのワークスペースの外、`~/Projects/walk-town` にある。GitHub: `SubaruOno/walk-town`(private)。小物の絵の元データと透過処理後の画像は `~/Projects/tekuteku-art`。

## 技術スタック

Expo SDK 54 / React Native 0.81.5 / React 19 / expo-router。保存は `expo-sqlite`(端末内のみ、サーバーなし)。歩数は `expo-sensors` の Pedometer(Core Motion、位置情報とHealthKitは不使用)。ほかに `expo-haptics`、`expo-screen-capture`(スクショ検知)、`expo-clipboard`。bundle id は `com.subaruono.tekutekumachi`。

## 主なファイル

- `docs/CONTRACT.md` — Claude・Codex・ChatGPTの約束事。データの型、画面、Codexが作り込む部品のprops、ブランチ運用
- `docs/ART_GUIDE.md` — 小物の絵の生成プロンプトと取り込み手順
- `src/db/index.ts` — SQLite(inventory, placements, gifts, events, meta)
- `src/gifts/` — 歩数とデイリーの包み、抽選
- `src/components/TownGrid.tsx` — 斜め見下ろしの街の描画、タップ位置の判定、長押しドラッグでの移動、ピンチでの拡大縮小(ドラッグとズームはCodex作)
- `src/components/GiftOpenAnimation.tsx` — 包みを開ける演出(揺れ→リボン→小物が弾んで出る、レア度で光り方が変わる。Codex作)
- `app/` — まち・図鑑・設定のタブと、おみやげ画面

## 現状(2026-09-16 朝)

- 計画書のStep 1〜7が完了し、夜間の開発で遊びの仕組みを大きく足した。何を足したかと、確かめたこと・確かめていないことは[夜間開発レポート](../outputs/walk-town/2026-09-16-overnight-report.md)にまとめた。
- 仕組みの一覧、テスト用リンク、利用記録の種類は、リポジトリの `docs/CONTRACT.md` が正本。
- 未確認: 実機での触覚・ピンチ・ドラッグ・歩数計、絵はがきの共有シート、長時間動かしたときの重さ。
- 未着手: 住人の本物の絵、紙袋の絵、実機での試用(Step 8)、TestFlight配布(Step 9)。
- シミュレーターの専用パネルは、Xcodeが選択されていないため使えない(`sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` が必要)。夜間は `app/debug.tsx` のテスト用リンクと `xcrun simctl` の撮影で確認した。
- デモ動画: `~/Projects/tekuteku-art/demo-overnight.mp4`。
