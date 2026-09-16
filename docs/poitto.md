# Poitto(紙くず投げゲーム)

丸めた紙くずを転がし、紙飛行機に変形させて、部屋の中を飛んでごみ箱に入れる iPhone ゲーム。
コードは `~/Projects/Poitto`、ブランチは `realitykit-spike`。

## 構成

- **PoittoRK** が本体。RealityKit + SwiftUI、120Hz の固定ステップで手動計算(物理エンジンは使わない)。iOS 26 以降。
- **Poitto** は旧 SpriteKit 版。出荷しない(バンドルID は `com.subaruono.PoittoLegacy` に退避)。
- ステージの座標・家具・風・動く障害物は [CourseDefinition.swift](file:///Users/subaruono/Projects/Poitto/PoittoRK/CourseDefinition.swift) と `HouseStages.swift` に集約。判定(`SpikeWorld`)と描画(`SpikeScenery`)は同じ定義から作る。
- 家具の3Dモデルは Poly Haven の CC0 素材。`ArtSource/polyhaven/` に元データ、`build_usdz.sh` で USDZ に変換して `PoittoRK/Models/` に置く。
- エフェクトは `SpikeEffects.swift`(紙の軌跡、着地の煙、リングのきらめき、クリアの紙吹雪)。

## ステージ

子ども部屋(扇風機の風でベッドへ) → 階段(梁の下をくぐって横風で降りる) → 1階の廊下(掃除機をよけて横風で台へ)。旧5面は `-legacy-stages` で遊べる。

## 確かめ方

- `xcodebuild test -project Poitto.xcodeproj -scheme PoittoRK -destination "id=<シミュレータのUDID>" -only-testing:PoittoRKTests`
- `HouseClearabilityTests` が、各ステージにクリアできる操作があることと、後のステージほど難しいことを確かめる。数字は機械の総当たりの成功率で、人の難しさとは別物。
- 画面は `-screen title|stages|play|result-clear`、`-stage N`、`-unlocked N`、`-overview`、`-debug-hitboxes`、`-debug-hud` で直接確認できる。

## 配布

- App Store Connect: 「Poitto! 紙くずフライト」(Apple ID 6812626509、バンドルID `com.subaruono.Poitto`)。ホーム画面の表示名は Poitto。
- 2026-09-16 に TestFlight の内部テストへ 1.0(1) を配布。すばるの実機で動作確認済み。
- API キーは `~/.appstoreconnect/private_keys/`。ビルドは Release アーカイブ → `xcodebuild -exportArchive` → `xcrun altool --upload-app`。
- App Store 提出用の説明文・スクリーンショット・プライバシーポリシーは未作成。

## 経緯

[家ステージの開発記録](../outputs/poitto/2026-09-16-house-dev-loop.md)、[ステージ企画](../outputs/poitto/2026-09-16-house-stage-ideas.md)、[Phase 3 の引き継ぎ](../outputs/handoffs/2026-09-15-poitto-phase3-done.md)。
