# Plan: てくてくまち ウィジェット & ダイナミックアイランド

**Created:** 2026-09-15
**Status:** 進行中(2026-09-18 に Step 2・3 の Small ウィジェットを実装。Step 1 はすばる待ち、Step 4 以降は未着手)
**Request:** てくてくまちにホーム画面ウィジェットとダイナミックアイランドを追加する
**Purpose:** アプリを開かなくても「歩いている途中」に存在感を出す。包みが届く瞬間にロック画面やダイナミックアイランドで報せることで、開きたくなる理由を増やす

---

## 進捗メモ(2026-09-18)

Small ウィジェット(「つぎの包みまであと○歩」)まで実装した。Step 3 で「自前の Config Plugin より先に使えるパッケージを調べる」としていた件は、`@bacons/apple-targets` v5 が Expo 54 で使えたのでそちらを採用。Xcode ターゲットの作成と App Groups の権限付与をやってくれる。

作ったもの:

- `targets/widget/expo-target.config.js` — ウィジェットのターゲット定義。**ターゲット名は英字にすること。** 日本語にすると CocoaPods が `Unicode Normalization not appropriate for ASCII-8BIT` で落ちる。画面に出る名前は Swift 側の `configurationDisplayName`。
- `targets/widget/index.swift` — WidgetKit の Provider と Small のビュー。共有 UserDefaults から `stepsToNext` と `giftsWaiting` を読むだけで、データベースには触らない。包みが待っているときは歩数ではなく包みの数を出す。歩数はアプリを開いたときしか動かないので「○時点」を添えた(計画の「決まっていないこと」への答え)。
- `modules/app-group/` — アプリ側から共有 UserDefaults へ書くだけのローカル Expo モジュール。
- `app.json` — App Groups の権限と `@bacons/apple-targets` プラグイン。
- `app/(tabs)/index.tsx` — 歩数か包みの数が変わったら書き込む。

残っていること:

- **すばる:** Apple Developer での App Groups 登録(Step 1)と、`app.json` への `ios.appleTeamId` の追記。実機と EAS ビルドの署名にこの2つが要る。シミュレーターでの確認は登録前でもできる。
- Medium サイズ、ダイナミックアイランド(Step 4)、実機確認(Step 5)、TestFlight(Step 6)。

### もとの引き継ぎメモ(2026-09-17 時点)

### いまの状態

- TestFlight のビルド4(2026-09-16 23:17 完了)に、朝のおしらせ通知まで入っている。ブランチ `art/plateless-trial`、main には未取り込み。昨夜の変更は[夜の開発レポート](../outputs/walk-town/2026-09-16-evening-report.md)。
- `expo-notifications` を入れたとき、プッシュ通知の権限がプロファイルになくてEASビルドが失敗した。App Groups も同じ種類の「権限(entitlement)」なので、**Apple Developer で登録してから**ビルドしないと同じ失敗になる。直し方はアプリの `docs/TESTFLIGHT.md` の「プッシュ通知の権限でビルドが止まるとき」。
- 権限を足し引きする Config Plugin の置き場所はすでにある(`plugins/withoutPushEntitlement.js`)。`app.json` のプラグインは後に書いたものから適用される。
- ネイティブの確認は、Expo Go ではなく Release 構成のシミュレータービルドで先に行う(`docs/TESTFLIGHT.md` の手順)。EAS の無料枠を節約できる。

### 最初にやる順番(範囲を小さくする)

1. **すばる:** Apple Developer で App ID `com.subaruono.tekutekumachi` に App Groups を追加し、Group `group.com.subaruono.tekutekumachi` を作る。ウィジェット用の App ID `com.subaruono.tekutekumachi.widget` も同じ Group に入れる。ログインは本人。
2. **Claude:** ウィジェットは Small だけ、表示は「次の包みまであと何歩」だけで作る。ダイナミックアイランド(Step 4)と Medium は後回し。
3. **Claude:** 自前の Config Plugin を書く前に、Expo SDK 54 で動くウィジェット用パッケージ(例: `@bacons/apple-targets`)が使えるか調べる。使えればそちらを使う。
4. **Claude:** Release のシミュレータービルドでウィジェットが出ることを確かめてから、EAS でビルドする。

### 決まっていないこと

- TestFlight の反応を見てから着手するか、先に作るか(2026-09-17 時点で保留)。
- 歩数はアプリを開いたときにしか更新されない。ウィジェットの数字が古くなるのを許すか(「○時点」と表示する案)。

---

## Overview

### What This Plan Accomplishes

2つの機能を追加する。

1. **ホーム画面ウィジェット(WidgetKit)**: 次の包みまであと何歩かをホーム画面に常時表示する。サイズ別に小・中の2種。
2. **ダイナミックアイランド / Live Activities(ActivityKit)**: 散歩中に「あと○歩で包みが届く」をダイナミックアイランドとロック画面下部に表示し、届いた瞬間にアニメーションで知らせる。

### Why This Matters

MVPの観察で「通知なしに自分から開くか」を確かめた。本格開発では逆の仮説——ホーム画面やダイナミックアイランドで歩数の進捗が見えると、散歩への動機になるか——を検証する。

---

## Current State

### Relevant Existing Structure

- 技術スタック: [docs/walk-town.md](../docs/walk-town.md) — Expo SDK 54 / React Native 0.81.5 / expo-router。EAS Buildを使用済み。
- データ: `expo-sqlite`(端末内のみ)、`meta` テーブルに最終確認歩数・日付を保存。
- 歩数: `expo-sensors` の Pedometer(Core Motion)。
- App Groups と Swift拡張はMVPでは未使用。

### Gaps or Problems Being Addressed

- WidgetKit と ActivityKit は Swift/SwiftUI の拡張 Target として書く必要があり、React Native から直接操作できない。
- アプリ本体と Widget Extension の間でデータを共有するには **App Groups**(`UserDefaults(suiteName:)` または ファイル共有コンテナ)が必要。
- Expo の Managed Workflow は WidgetKit / ActivityKit を標準でサポートしていない。カスタム Config Plugin を書くか、サードパーティパッケージを使う。

---

## Design Decisions

### Key Decisions

1. **Expo Config Plugin で Swift 拡張を注入する**: EAS Build の `prebuild` フェーズで `ios/` フォルダに Swift コードと Xcode Target を自動追加する。アプリ本体は Expo Managed Workflow のままで、ウィジェットだけネイティブを足す形にする。
2. **データ共有は App Groups の UserDefaults**: アプリ本体が SQLite から読んで App Groups の共有 UserDefaults に書き込む。Widget/Live Activity は共有 UserDefaults だけを読む。SQLite には触らない。
3. **書き込むデータは最小限**: `stepsToNextGift: Int`、`giftsAvailable: Int`、`lastUpdated: Date`。街の画像はウィジェットには入れない(MVPは探索段階)。
4. **ダイナミックアイランドは Live Activities で実装**: `ActivityKit` を使い、散歩を始めたとき(アプリを開いたとき)に Activity を開始する。歩数の更新は `Pedometer` のバックグラウンド計測と組み合わせる。
5. **サイズ**: ウィジェットは Small(次の包みまでの歩数 + アイコン)と Medium(歩数バー + 今日届いた包み数)の2種。Large は後回し。
6. **通知許可は不要**: Live Activities はユーザーが許可しなくても起動できる(iOS 16.2+)。Push での更新は入れない。アプリがフォアグラウンドのときだけ更新する。

---

## Proposed Changes

### New Files to Create (アプリリポジトリ側)

| ファイル | 役割 |
|---|---|
| `plugins/withWidgetExtension.js` | Expo Config Plugin: Widget Extension Target を Xcode プロジェクトに追加する |
| `widget/TekutekuWidget.swift` | WidgetKit の Entry / View / Timeline Provider |
| `widget/TekutekuLiveActivity.swift` | ActivityKit の Attributes と ContentState の定義 |
| `widget/TekutekuLiveActivityView.swift` | ダイナミックアイランド・ロック画面のUI |
| `src/native/AppGroupBridge.ts` | React Native → App Groups へ書き込む薄いラッパー(expo-modules-core) |
| `src/gifts/syncAppGroup.ts` | 歩数と包み情報を AppGroupBridge 経由で共有 UserDefaults に書き込む関数 |
| `src/gifts/liveActivity.ts` | Live Activity の開始・更新・終了を呼び出す React Native 側のラッパー |

### Files to Modify (アプリリポジトリ側)

| ファイル | 変更内容 |
|---|---|
| `app.json` | App Groups entitlement、Widget Extension のバンドル ID を追加 |
| `app.config.js` | `withWidgetExtension` プラグインを読み込む |
| `src/gifts/checkSteps.ts` | 歩数確認後に `syncAppGroup` を呼ぶ1行を追加 |
| `app/_layout.tsx` | アプリ起動時・フォアグラウンド復帰時に Live Activity を開始/更新する |

### Files to Modify (AI-OS側)

| ファイル | 変更内容 |
|---|---|
| `docs/walk-town.md` | ウィジェット・ダイナミックアイランドの仕組みと現状を追記 |
| `ledger/subaru.md` | 各ステップ完了時に1行 |

---

## Step-by-Step Tasks

### Step 1: App Groups を有効にする

**前提:** MVPが検証済みで、本格開発を進める判断をした後。

**Actions:**

- Apple Developer ポータルで App ID `com.subaruono.tekutekumachi` に App Groups capability を追加する。Group ID は `group.com.subaruono.tekutekumachi` にする。
- Widget Extension 用の App ID `com.subaruono.tekutekumachi.widget` を作る。同じ Group に入れる。
- `app.json` の `entitlements` に App Groups を追加する。
- EAS Build で再ビルドし、実機で App Groups が動くことを確認する。

**確認:** アプリから `UserDefaults(suiteName: "group.com.subaruono.tekutekumachi")` に書いた値が読めること。

---

### Step 2: AppGroupBridge を作る(Claude)

**Actions:**

- `expo-modules-core` を使い、`AppGroupBridge` というネイティブモジュールを作る。
- Swift 側: `write(stepsToNext: Int, giftsAvailable: Int)` → App Groups UserDefaults に保存。
- TypeScript 側: 同名の関数をエクスポートする薄いラッパー。
- `src/gifts/syncAppGroup.ts` から呼ぶ。

**確認:** iOS シミュレーターで `write` を呼んだあと、Swift のテストコードで読み出せること。

---

### Step 3: WidgetKit Extension を作る(Claude + ChatGPT)

**Actions:**

- `plugins/withWidgetExtension.js` を書く。EAS `prebuild` で `ios/TekutekuWidget/` に Swift ファイルを追加し、Xcode プロジェクトに Target を登録する。
- `widget/TekutekuWidget.swift` を書く:
  - `TimelineEntry`: `stepsToNext: Int`、`giftsAvailable: Int`。
  - `TimelineProvider`: App Groups UserDefaults から読み込む。`refreshInterval` は15分。
  - Small View: 包みのアイコン + 「あと ○ 歩」。
  - Medium View: 歩数バー(0〜2,000) + 今日の包み数。
- `app.config.js` にプラグインを追加する。

**確認:** シミュレーターのウィジェットギャラリーに「てくてくまち」が表示され、歩数が反映されること。

---

### Step 4: Live Activities / ダイナミックアイランドを作る(Claude + ChatGPT)

**Actions:**

- `widget/TekutekuLiveActivity.swift` を書く:
  - `Attributes`: アクティビティ1回分の固定情報(今日の目標歩数2,000)。
  - `ContentState`: 更新される情報(`stepsToNext: Int`、`giftsAvailable: Int`、`arrived: Bool`)。
- `widget/TekutekuLiveActivityView.swift` を書く:
  - ダイナミックアイランド(コンパクト表示): 包みアイコン + 「あと ○」。
  - ダイナミックアイランド(展開表示): 歩数バー。
  - ロック画面: 歩数バー + 包み数。
  - `arrived == true` のとき: 揺れるアニメーション + 「包みが届きました」。
- `src/gifts/liveActivity.ts`:
  - `startLiveActivity()`: アクティビティを開始する。
  - `updateLiveActivity(stepsToNext, giftsAvailable, arrived)`: 状態を更新する。
  - `endLiveActivity()`: 終了する(アプリがバックグラウンドに入ったら、または今日の上限に達したら)。
- `app/_layout.tsx` でアプリ起動時に `startLiveActivity` を呼ぶ。
- `src/gifts/checkSteps.ts` で歩数確認後に `updateLiveActivity` を呼ぶ。

**確認:** 実機(iPhone 14 以降、ダイナミックアイランドあり)でアプリを開きながら歩くと、ダイナミックアイランドに歩数が出ること。

---

### Step 5: すばるが実機で触って直す

**Actions:**

- 2〜3日自分で使い、以下を確認する:
  - ウィジェットの更新頻度が15分で十分か(見た目の鮮度感)。
  - ダイナミックアイランドが散歩中に自然に見えるか(邪魔でないか)。
  - 包みが届いた瞬間の演出が気持ちいいか。
- 直したい点をまとめてClaudeに渡す。

---

### Step 6: TestFlight で確認して AppStore 審査へ

**Actions:**

- EAS Build で新しいビルドを作り、TestFlight に上げる。
- App Store Connect で Widget Extension の審査情報を確認する(プライバシー情報に App Groups を追加)。
- 既存の審査提出プロセス(`store/README.md`)に沿って進める。

---

## Connections & Dependencies

### 依存関係

- **MVP完了・検証済みが前提**: Step 1〜10(MVPの計画書)がすべて終わり、本格開発に進む判断をした後に着手する。
- `docs/walk-town.md` に現状が反映されていること。

### Impact on Existing Workflows

- `checkSteps.ts` に `syncAppGroup` の呼び出しを1行足すだけ。既存ロジックへの影響は最小限。
- Widget Extension は別 Target なので、既存コードが壊れるリスクは低い。
- EAS Build のビルド時間が少し伸びる(Swift のコンパイルが増えるため)。

---

## Validation Checklist

- [ ] ホーム画面に Small ウィジェットを追加し、歩数が15分以内に更新される
- [ ] Medium ウィジェットで今日届いた包みの数が正しく出る
- [ ] ダイナミックアイランドにアプリを開いたあと「あと ○ 歩」が出る
- [ ] 2,000歩を超えたとき、ダイナミックアイランドが「届いた」演出に切り替わる
- [ ] アプリをバックグラウンドに移したあと Live Activity が終了する
- [ ] ダイナミックアイランドのないiPhone(iPhone SE など)でもクラッシュしない(ロック画面のみ表示)
- [ ] 機内モードで全機能が動く
- [ ] EAS Build が通り、TestFlight に上がる

---

## Open Questions

1. **バックグラウンド歩数更新**: アプリを閉じている間にダイナミックアイランドを更新するには Push to Start / Push Update が必要。MVPでは「アプリを開いている間だけ更新」に絞る。サーバーを持たない設計を壊さないための判断。
2. **ウィジェットに街の絵を出すか**: 絵を Widget に載せるには Image をシリアライズして App Groups コンテナに保存する必要がある。コストが高いためフェーズ2に回す。
3. **watchOS**: Apple Watch の Complication は、ダイナミックアイランドが一段落してから検討する。

---

## Notes

- このプランは MVP([MVP計画書](2026-09-15-walk-town-app-mvp.md))の成功判断後に着手するバックログ。
- WidgetKit / ActivityKit は SwiftUI で書く。このプランが終わったら、アプリ本体も SwiftUI への移行を再検討するタイミングになる。
- Config Plugin の書き方は Expo の公式ドキュメント「Creating Expo Modules」と「Config Plugins」が基本資料。
