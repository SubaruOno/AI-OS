# Poitto RealityKit — Phase 3 完了・Phase 4 着手前のハンドオフ

## この作業について

`~/Projects/Poitto` の `realitykit-spike` ブランチで、RealityKit 製の紙屑投げゲーム「Poitto」を開発中。
旧 SceneKit 版を RealityKit で全面書き直したスパイク版。

## 完了済み

### Phase 0
- DOF（被写界深度）クラッシュを無効化で対処（`customPostProcessing` を make クロージャ外に出しても再現するため保留）
- 入力録音・再生（`-replay` フラグ）
- 着地判定の下からの吸着バグ修正
- 紙飛行機を 1.5 倍デフォルトに決定

### Phase 1
- フラットコース（8m × 120m、z=−80 にゴールアーチ）
- CLEAR / MISS / RETRY の基本フロー

### Phase 2
- ハウスコース（机 → 棚 → ゴミ箱）
- リング 3 本（z=−17, −35, −42）
- 棚・家具・室内壁の MISS 判定

### Phase 3（今セッションで完了）
- `GameRoot`：タイトル → プレイ → タイトルの画面遷移
- `TitleScreen`：「POITTO」「紙屑、飛ばそ。」「TAP TO START」
- `ResultScreen`：CLEAR / MISS 演出、RETRY / TITLE ボタン
- `TutorialHints`：初回クリアまで操作説明表示
- `Haptics`：transform / landing / ring / binDrop / cleared / fell
- `Sounds`：効果音 + ロールループ / BGM
- リング進捗ピップ（画面上部 ○○○）

### 衝突判定の改善（今セッション）
- 室内床 MISS 閾値：y < −8.5 → y < −7.75（視覚的な床面に合わせた）
- 机の胴体判定を追加（横からの突き抜け防止）
- 棚側面 MISS 閾値：y < −1.8 → y < −1.6
- 家具ヒットボックスを半径 0.25m 拡張
- ゴミ箱 CLEAR を「真上から入ったときだけ」に修正（`prevY >= −4.5` チェック）

### 修正したバグ
- **isActive 固定バグ**：RealityView の make クロージャが struct を値キャプチャするため `self.isActive` が常に `false`。`SpikeWorld.isActive` を持たせ `update:` クロージャで同期することで解決。

## 現在進行中

特になし。Phase 3 + 衝突改善が完了し、次のフェーズを検討中の状態。

## 未着手

### Phase 4：ビジュアル磨き
- **テクスチャ改善**：AI 生成テクスチャ（木目・紙素材・壁材など）を PBR マテリアルに適用
  - DALL-E / Midjourney でテクスチャ画像を生成 → `TextureResource` で読み込み
  - 現状のジオメトリはそのままで素材だけ差し替え
- **3D モデル差し替え（オプション）**：Meshy.ai などで机・棚・ゴミ箱を生成 → USDZ 変換 → `Entity.load(named:)`
- **DOF 再挑戦**：`customPostProcessing` を make クロージャ外で設定する試み（保留中）
- **照明調整**：`addSun()` の方向・強度、fill ライトのバランス

## 決定事項

- kinematic（手動、物理なし）で 120Hz 固定ステップ維持
- ハウスコースがメイン（`-flat-course` フラグでフラットコースに切り替え）
- `-small-dart` で元サイズ、デフォルト 1.5 倍
- `-close-cam` で 4m カメラ（デフォルト 6m）
- DOF はクラッシュ問題が解決するまで無効のまま

## 次にやること（優先順）

1. **テクスチャ生成から試す**
   - DALL-E で木目テクスチャ（棚・机脚）、コンクリート壁、布・カーペット床などを生成
   - `SpikeScenery.swift` の `lit()` / `graphPaper()` を差し替え
   - 実機でビルド・確認

2. **気に入ったら 3D モデル差し替えへ進む**
   - Meshy.ai でゴミ箱・棚などを生成、USDZ に変換
   - `SpikeScenery.build()` で `root.addChild(try! Entity.load(named: "bin"))` のように差し替え

3. **DOF 問題の調査**（時間があれば）

## ブロッカー・注意事項

- リング座標が `SpikeWorld.houseRings` と `SpikeScenery.build()` の 2 箇所に書かれている（現在は同期済み）。変更するときは必ず両方更新。
- デバイス UDID：`4C762B64-A232-548E-905C-662C5515D33E`
- ビルドコマンド：
  ```bash
  cd ~/Projects/Poitto
  xcodebuild build -project Poitto.xcodeproj -scheme PoittoRK \
    -destination 'id=00008150-00162108013A401C' \
    -derivedDataPath build/DDdev -allowProvisioningUpdates
  xcrun devicectl device install app \
    --device 4C762B64-A232-548E-905C-662C5515D33E \
    build/DDdev/Build/Products/Debug-iphoneos/PoittoRK.app
  xcrun devicectl device process launch \
    --device 4C762B64-A232-548E-905C-662C5515D33E \
    --terminate-existing com.subaruono.PoittoRK
  ```
- `xcodegen generate` は新 `.swift` ファイルを追加したときだけ必要（既存ファイルの編集は不要）

## 関連ファイル

| ファイル | 役割 |
|---|---|
| `~/Projects/Poitto/PoittoRK/SpikeWorld.swift` | シミュレーション・当たり判定・入力処理 |
| `~/Projects/Poitto/PoittoRK/SpikeScenery.swift` | シーン構築・ジオメトリ・マテリアル |
| `~/Projects/Poitto/PoittoRK/SpikeView.swift` | SwiftUI レイヤー・GameRoot 連携 |
| `~/Projects/Poitto/PoittoRK/GameRoot.swift` | タイトル ↔ プレイの画面遷移 |
| `~/Projects/Poitto/PoittoRK/TitleScreen.swift` | タイトル画面 |
| `~/Projects/Poitto/PoittoRK/ResultScreen.swift` | CLEAR / MISS 画面 |
| `~/Projects/Poitto/PoittoRK/TutorialHints.swift` | チュートリアルヒント |
| `~/Projects/Poitto/PoittoRK/Haptics.swift` | ハプティクス |
| `~/Projects/Poitto/PoittoRK/Sounds.swift` | 効果音・BGM |
| `~/Projects/Poitto/PoittoRK/SpikeScenery.swift` | シーン（ここでテクスチャ差し替え） |
