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

## 現状(2026-09-16 7:35)

- 夜間の開発で遊びの仕組みを足し([夜間開発レポート](../outputs/walk-town/2026-09-16-overnight-report.md))、朝は見た目・手触り・配置と結果のつながりを35の仮説で改善した([朝の仮説検証ログ](../outputs/walk-town/2026-09-16-morning-hypotheses.md))。
- 住人5人、紙袋、包み、対岸の村、アイコンの絵は Codex CLI の画像生成で作った(`~/Projects/tekuteku-art`)。
- 仕組みの一覧、テスト用リンクは、リポジトリの `docs/CONTRACT.md` が正本。TestFlightの手順は `docs/TESTFLIGHT.md`。変更前に `scripts/check.sh` を通す。
- iPhone実機はExpo Go(`exp://192.168.11.35:8081`、Macと同じWi-Fi)で接続確認済み。
- 未確認: 実機での効果音・触覚・ピンチ・ドラッグ・歩数計、長時間動かしたときの重さ、LINEへの絵はがき送信。
- App Store提出素材はリポジトリの `store/` にある(アイコン、6.9インチのスクショ5枚、`store.config.json` の説明文、プライバシーポリシー)。手順は `store/README.md`。
- 2026-09-15: 起動画面フリーズを修正したビルドがTestFlightで正常に動作(すばるの実機で確認)。App Store Connectのアプリ・説明文・スクショ・プライバシーURLは登録済み。
- 未着手: 台なしの小物の絵、プライバシー情報の「公開」、外部テスト(友だち配布)、審査提出。
- シミュレーターの専用パネルは、Xcodeが選択されていないため使えない(`sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` が必要)。
