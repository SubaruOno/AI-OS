# 引き継ぎ: Poitto RealityKit 技術検証（Phase 0）

2026-09-15 15:50 時点。Claude Code から Warp へ引き継ぎ。

## これは何か、なぜ大事か

すばるの iOS ゲーム試作 Poitto（紙屑が転がり、紙飛行機に変形して滑空する）を、SceneKit から **RealityKit で全面的に書き直す**計画の最初の検証。書き直す前に「RealityKit で旧版の手触りと見た目が作れるか」を小さく確かめている。ここで詰まる技術があれば、書き直しの方針自体を見直す。

- リポジトリ: `~/Projects/Poitto`（GitHub: SubaruOno/Poitto, 非公開）
- 作業ブランチ: `realitykit-spike`（検証コードは `PoittoRK/`, テストは `PoittoRKTests/`）
- 旧版: `main` と `scenekit-final` タグ（`Poitto/` ターゲット）
- 書き直し仕様書: [rewrite-spec-realitykit.md](../../../Projects/Poitto/docs/rewrite-spec-realitykit.md)
- 検証ログ（仮説→実装→結果→考察、全9ラウンド）: [2026-09-15-realitykit-spike.md](../poitto/2026-09-15-realitykit-spike.md)

## 決まっていること

- 書き直しは **RealityKit（Swift）**。Codex（GPT-6/Astra）は Unity を推したが、すばるが Swift 継続を選んだ
- **対応 OS は iOS 26 以上**（ぼかしの後処理 `PostProcessEffect` が iOS 26 から）
- 旧版のアイデアと手触りの目標は引き継ぐが、コードは移植しない
- 滑空は物理任せにせず手動で動かす。計算は RealityKit から切り離した純粋な関数にしてテストする
- 画像アセットは追加しない（手続き生成）
- 検証コードは使い捨て。書き直し本体の設計ではない

## 状態

### 終わっている
- シーン（方眼紙の机、棚、ゴミ箱、部屋、窓、光の筋、ホコリのパーティクル）
- 自動操縦ループ: 転がる→ヒットストップ→変形→滑空→棚に着地→再ジャンプ→ゴミ箱
- 手動操作: ドラッグ旋回、上フリックでジャンプ、滑空中の縦ドラッグでピッチ
- FOV パンチと速度での FOV 拡大
- `Flight`（純粋な計算）と Swift Testing 9本: **全合格**
- シミュレーターで 41〜60fps、シーン生成 115ms
- 光の筋は「部屋を暗めにしてから光を足す」で日差しらしくなった
- 実機（ちぴぃ = iPhone 17 Pro Max, iOS 26.7）への署名ビルドとインストール

### 途中（ここで止まっている）
- **アプリが実機で起動直後に落ちる。** クラッシュ位置はシミュレーターと同じ:
  `SpikeView.body` の RealityView make クロージャ → `content.renderingEffects.customPostProcessing = .effect(TiltShiftEffect())` → `ARView.renderCallbacks.setter` で SIGTRAP
- 実機ではぼかしがデフォルトでオン（`SpikeOptions` がシミュレーターのときだけ切る）

### 手を付けていない
- 実機での影の確認（シミュレーターでは影がまったく描かれなかった）
- 実機での 60fps 計測
- ぼかしの見た目の確認
- 滑空中の紙飛行機が小さい問題（カメラ距離はすばるの判断待ち）
- Phase 1（平坦コースで遊べる縦スライス）

## 次にやること（順番どおり）

1. **`-no-dof` で実機起動して、落ちないことを確認する。** 影と fps を先に見る
   ```bash
   cd ~/Projects/Poitto && git checkout realitykit-spike
   xcrun devicectl device process launch --device 4C762B64-A232-548E-905C-662C5515D33E --terminate-existing com.subaruono.PoittoRK -no-dof
   ```
   すばるに画面を見てもらい、スクショをもらう（`dof off`、紙屑の影、窓格子の影、fps）
2. **ぼかしのクラッシュを直す。** 試す順:
   - `customPostProcessing` を make クロージャで代入せず、`update` クロージャや `.task` など後のタイミングで設定する
   - `renderingEffects` を一度ローカル変数にコピーして変更し、まとめて代入する
   - `TiltShiftEffect` の `nonisolated(unsafe) var pipeline` を外し、`prepare` で作ったものを保持する別の形にする（Sendable 要件で落ちていないか）
   - Apple の `PostProcessEffect` サンプルと突き合わせる（SDK の swiftinterface は `RealityFoundation` の 14483 行付近）
3. 直ったら実機でぼかしの見た目と fps を確認し、[検証ログ](../poitto/2026-09-15-realitykit-spike.md) にラウンド10以降として追記する
4. 結果をすばるに報告し、Phase 1 に進むか判断してもらう

## ビルドと実行

```bash
cd ~/Projects/Poitto
xcodegen generate
# シミュレーター
xcodebuild build -project Poitto.xcodeproj -scheme PoittoRK -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -derivedDataPath build/DD
xcodebuild test  -project Poitto.xcodeproj -scheme PoittoRK -destination 'platform=iOS Simulator,name=iPhone 17 Pro' -derivedDataPath build/DD
# 実機（ちぴぃ）
xcodebuild build -project Poitto.xcodeproj -scheme PoittoRK -destination 'id=00008150-00162108013A401C' -derivedDataPath build/DDdev -allowProvisioningUpdates
xcrun devicectl device install app --device 4C762B64-A232-548E-905C-662C5515D33E build/DDdev/Build/Products/Debug-iphoneos/PoittoRK.app
xcrun devicectl device process launch --device 4C762B64-A232-548E-905C-662C5515D33E --terminate-existing com.subaruono.PoittoRK
# 実機のクラッシュログ
xcrun devicectl device info files --device 4C762B64-A232-548E-905C-662C5515D33E --domain-type systemCrashLogs | grep PoittoRK
```

起動引数: `-no-dof`（ぼかしなし）, `-no-shafts`（光の筋なし）, `-close-cam`（カメラ 6m→4m）, `-shadow-test`（影確認用の赤い板）, `-lattice-visible`（窓格子を見せる）

## 注意点

- **Metal コンパイラ未インストール**。シェーダーは `TiltShiftEffect.swift` 内の文字列を実行時にコンパイルしている。`.metal` ファイルを足すとビルドが落ちる
- 実機の destination は devicectl の ID（`4C76…`）ではなく xcodebuild の ID（`00008150-00162108013A401C`）
- Xcode のサインインが切れると署名で落ちる。すばるに Xcode → Settings → Apple Accounts で入り直してもらう（パスワードは本人が入力）
- シミュレーター画面を撮るときは旧版 Poitto が前面に残っていないか注意（一度、旧版を撮っていた）
- 実機の画面は Mac から直接撮れない。すばるにスクショをもらう
- 旧版 Poitto の `Poitto` スキームとテスト（105本）は `main` のまま触っていない
