# てくてくまち(walk-town)

散歩するとおみやげの小物が届き、湖畔の6×6マスの街に飾って眺めるiOSアプリ。すばるが個人開発中の検証版(MVP)。計画は[MVP計画書](../plans/2026-09-15-walk-town-app-mvp.md)、アイデアの経緯は[アイデア出しの記録](../outputs/walk-town/2026-09-15-ideation-with-codex.md)。

コードはこのワークスペースの外、`~/Projects/walk-town` にある。GitHubのリポジトリはまだ作っていない(2026-09-15時点、ローカルのGitのみ)。小物の絵の元データと透過処理後の画像は `~/Projects/tekuteku-art`。

## 技術スタック

Expo SDK 54 / React Native 0.81.5 / React 19 / expo-router。保存は `expo-sqlite`(端末内のみ、サーバーなし)。歩数は `expo-sensors` の Pedometer(Core Motion、位置情報とHealthKitは不使用)。ほかに `expo-haptics`、`expo-screen-capture`(スクショ検知)、`expo-clipboard`。bundle id は `com.subaruono.tekutekumachi`。

## 主なファイル

- `docs/CONTRACT.md` — Claude・Codex・ChatGPTの約束事。データの型、画面、Codexが作り込む部品のprops、ブランチ運用
- `docs/ART_GUIDE.md` — 小物の絵の生成プロンプトと取り込み手順
- `src/db/index.ts` — SQLite(inventory, placements, gifts, events, meta)
- `src/gifts/` — 歩数とデイリーの包み、抽選
- `src/components/TownGrid.tsx` — 斜め見下ろしの街の描画とタップ位置の判定
- `src/components/GiftOpenAnimation.tsx` — 包みを開ける演出(今は仮実装、Codexが作り込む)
- `app/` — まち・図鑑・設定のタブと、おみやげ画面

## 現状(2026-09-15)

- 土台(計画書のStep 3〜6)は完成。型チェックとlintは通過。iOS 26.4シミュレーターで起動し、きょうのおみやげが届いて街に置けるところまで動作した。
- タップ位置の判定と出来事(猫の昼寝)の判定は、コード単体のテストで確認済み。
- 未確認: 実機での歩数の包み、並べ替えの操作全般、絵はがきモード、図鑑、設定画面。
- 未着手: GitHubリポジトリの作成、Codexによる演出とドラッグ操作(Step 7)、紙袋の絵、TestFlight配布。
- シミュレーターの専用パネルは、Xcodeが選択されていないため使えない(`sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` が必要)。
