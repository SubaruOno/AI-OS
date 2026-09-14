# Plan: 散歩のおみやげで小さな街を作るiOSアプリ MVP

**Created:** 2026-09-15
**Status:** Draft
**Request:** 散歩するとおみやげ(小物)が届き、自分の小さな街に飾って眺めるiOSアプリの検証版を計画する
**Purpose:** 「散歩→包みを開ける→飾る→眺める」の一周が、友人5〜8人に2週間自発的に使われるほど楽しいかを、最小の開発量で確かめる

---

## Overview

### What This Plan Accomplishes

仮称「さんぽタウン」の検証版(MVP)を、React Native/Expoで作ってTestFlightで友人に配るところまでを計画する。サーバーは使わず、小物12種・飾る場所1つに絞る。2週間の観察結果で、本格開発に進むか、やめるか、方向を変えるかを判断する。

### Why This Matters

すばるは「面白くてUIのいいアプリ」を作りたい。稼ぐことは二の次。3DSのすれちがいMii広場のピース集めから始まり、Codexのセカンドオピニオンを受けて「集め方より、集めたものを飾って眺める楽しさが本体」という方向に落ち着いた。好きなアプリのYoiLog(飲んだ缶が棚に並ぶ)とも同じ型になる。SHIGABASE複数チーム版([調査メモ](../outputs/2026-09-14-shigabase-multi-team-research.md))とは別の、個人向けで営業のいらないプロジェクトとして並行できる。

---

## Current State

### Relevant Existing Structure

- [SHIGABASE](../docs/shigabase.md): Expo SDK 54 / React Native 0.81.5 / React 19 / expo-router / EAS Build。App Store公開の経験と、Apple Developerアカウント・EASの運用がすでにある。
- SHIGABASEのコードは `~/Projects/TerakoyaAI/ShigabaseiOS` にあり、AI-OSの外で管理している。新アプリも同じくAI-OSの外に置く。
- SHIGABASEでは `react-native-reanimated` / `worklets` のバージョン不整合がiOS 26でクラッシュを起こした。新アプリでも同じ部品を使うので、最初からExpo推奨のバージョンに揃える。
- [context/tech-stack.md](../context/tech-stack.md): 使っている技術と連携の一覧。

### Gaps or Problems Being Addressed

- アイデアは固まったが、画面、データの形、やること・やらないことが文書になっていない。
- Claude・Codex・ChatGPTで分担するため、全員が同じ前提を読める約束事が必要。
- 小物の絵のタッチを統一する方法が決まっていない。

---

## Integration Type

**Classification:** N/A(AI-OSの外に置く独立したアプリ。AI-OS側には計画書とドキュメントだけを置く)
**Reasoning:** アプリのコードは大きくなり、独自のGitHubリポジトリとEASの設定を持つ。SHIGABASEと同じ運用に揃える。
**Location:** コードは `~/Projects/walk-town/`(GitHub: `SubaruOno/walk-town`、private)。AI-OS側は `plans/` と `docs/walk-town.md`。
**Auto-discovery:** なし

---

## Proposed Changes

### Summary of Changes

- 新しいExpoアプリのリポジトリを作る
- 端末内だけで完結するデータの仕組み(小物カタログ、持ち物、配置)を作る
- 4画面を作る: 街、包みを開ける、図鑑、設定
- 歩数(Core Motion)で包みが届く仕組みを作る
- 小物12種のイラストをタッチを揃えて用意する
- 端末内の利用記録と、テスト後の聞き取りで評価する
- TestFlightで友人5〜8人に配る
- AI-OS側にドキュメントを置き、索引に登録する

### New Files to Create

| File Path | Purpose |
|-----------|---------|
| `~/Projects/walk-town/`(リポジトリ一式) | Expoアプリ本体 |
| `~/Projects/walk-town/docs/CONTRACT.md` | Claude・Codex・ChatGPTが共有する約束事(データの型、画面の役割、部品の受け渡し、ブランチ運用) |
| `~/Projects/walk-town/docs/ART_GUIDE.md` | 小物イラストのタッチ、サイズ、生成プロンプトの型 |
| `~/Projects/walk-town/src/data/catalog.ts` | 小物12種の定義 |
| `~/Projects/walk-town/src/db/` | SQLiteの初期化と読み書き |
| `~/Projects/walk-town/app/(tabs)/index.tsx` | 街の画面 |
| `~/Projects/walk-town/app/open.tsx` | 包みを開ける画面 |
| `~/Projects/walk-town/app/(tabs)/collection.tsx` | 図鑑の画面 |
| `~/Projects/walk-town/app/(tabs)/settings.tsx` | 設定と利用記録の書き出し |
| `docs/walk-town.md`(AI-OS) | AI-OSから見たアプリの構成メモ |
| `outputs/walk-town/2026-10-mvp-test-results.md`(AI-OS、テスト後) | 2週間テストの結果と判断 |

### Files to Modify

| File Path | Changes |
|-----------|---------|
| `docs/_index.md` | `docs/walk-town.md` を追加 |
| `context/tech-stack.md` | 新しいリポジトリを追記 |
| `ledger/subaru.md` | 各ステップ完了時に1行 |

### Files to Delete (if any)

なし

---

## Design Decisions

### Key Decisions Made

1. **サーバーを使わない**: 小物・持ち物・配置はすべて端末内のSQLite(`expo-sqlite`)に保存する。2週間の検証にネットは不要で、費用も個人情報の管理責任も発生しない。
2. **位置情報とHealthKitは使わない**: 歩数は `expo-sensors` の `Pedometer`(iOSのCore Motion)で取る。位置の許可がいらず、審査とプライバシーの懸念を避けられる。Codexの「位置情報の保護に比べて見返りが小さい」という指摘を採用。
3. **包みの届き方**: 前回開いた時から2,000歩ごとに1包み、1日最大3包み。歩数が取れない場合に備え、1日1包みの「きょうのおみやげ」も配る。空振りの日をなくすため。
4. **破片ではなく完成品を配る**: 包みを開けると、喫茶店、木、ベンチなどがそのまま手に入り、すぐ飾れる。Codexの「破片では愛着が湧かない」という指摘を採用。
5. **飾る場所は1つ、6×6マスの斜め見下ろし(アイソメトリック)**: 手のひらサイズのジオラマとして眺める。ピクミン ブルームの「地図の上」と差をつける。
6. **小物は12種、3段階のレア度**: ふつう8、すこし珍しい3、珍しい1。図鑑が埋まる楽しさを残しつつ、絵を作る量を抑える。
7. **React Native/Expoで作る**: SHIGABASEで慣れていて、検証の速さを優先する。Expo SDKとreanimatedのバージョンはExpo推奨に揃える。SwiftUIへの移行は本格開発に進むときに再検討。
8. **分担**: Claudeが土台(データ、保存、画面遷移、歩数)と約束事を作る。Codexが演出と操作(包みを開けるアニメーション、ドラッグで置く、触覚フィードバック)を作り込む。ChatGPTが小物の絵を作る。すばるが見た目と触り心地を最終判断する。
9. **ブランチ運用**: `main` は動く状態だけ。Claudeは `base/*`、Codexは `ui/*` ブランチで作業し、`CONTRACT.md` の型を変えるときは必ずClaude側で先に更新する。
10. **任天堂の名前や見た目に寄せない**: 「すれちがい」「Mii」「ピース」などの言葉と、どうぶつの森の画風は使わない。

### Alternatives Considered

- **Bluetoothのすれ違い通信**: iOSのバックグラウンド制限で不安定、利用者が集まるまで何も起きない、出会い系と誤解されやすい。見送り。
- **足跡すれ違い(位置情報を粗くして非同期で拾う)**: 粗くしても行動パターンから個人が特定される危険が残る。見送り。
- **初めて行った駅・市区町村でのボーナス**: 通学路が決まっている学生はすぐ尽き、位置の許可も必要。本格開発で再検討。
- **SwiftUIで作る**: 動きや触り心地には有利だが、学習コストが検証を遅らせる。後回し。
- **Supabaseで保存**: 機種変更の引き継ぎには必要だが、MVPでは不要。

### Open Questions (if any)

1. **アプリ名**: 仮称「さんぽタウン」。本決めは絵のタッチが決まってからでよい。
2. **街の世界観**: 和風の商店街、海辺の町、野球場のある街など。Step 2の前にすばるが決める。
3. **絵の作り方の最終手段**: ChatGPTでタッチが揃わなければ、自分で描く、または外注するかを決める。
4. **テストに誘う友人**: 5〜8人。iPhoneを持っていて、2週間使ってくれる人。

---

## Step-by-Step Tasks

### Step 1: 世界観を決める

**Actions:**

- すばるが街のテーマを1つ選ぶ(Open Question 2)。
- 小物12種の名前とレア度を決める。例(海辺の町なら): 灯台、ベンチ、ヤシの木、かき氷屋、郵便ポスト、自転車、街灯、花壇、パラソル、ボート、喫茶店、観覧車。
- `ART_GUIDE.md` の下書き用に、好きな雰囲気の参考画像を2〜3枚集める。

**Files affected:**

- `~/Projects/walk-town/docs/ART_GUIDE.md`(Step 3で作成)

---

### Step 2: 絵のタッチを決める

**Actions:**

- ChatGPTの画像生成で、1つの小物(例: ベンチ)を斜め見下ろし・透明背景・512×512pxで何パターンか作る。
- すばるが1枚を選び、それを「基準画像」にする。
- 基準画像と同じタッチで、残り11種を作る。揃わないものは作り直す。
- 生成に使ったプロンプトの型を `ART_GUIDE.md` に記録する。追加の小物も同じ型で作れるようにする。

**Files affected:**

- `~/Projects/walk-town/assets/items/*.png`
- `~/Projects/walk-town/docs/ART_GUIDE.md`

---

### Step 3: リポジトリと約束事を作る(Claude)

**Actions:**

- `~/Projects/walk-town` に `npx create-expo-app` でexpo-router構成のアプリを作る。Expo SDKはSHIGABASEと同じ54系に揃える。
- `npx expo install expo-sqlite expo-sensors expo-haptics react-native-reanimated react-native-gesture-handler` で、Expo推奨のバージョンを入れる。
- GitHubに `SubaruOno/walk-town`(private)を作り、pushする。
- `docs/CONTRACT.md` を書く。中身:
  - データの型(下記)
  - 画面ごとの役割と、画面間で受け渡す値
  - Codexが作る部品の名前と、受け取る値(例: `<GiftOpenAnimation item={Item} onDone={() => void} />`、`<TownGrid placements={Placement[]} onMove={(id, x, y) => void} />`)
  - ブランチ運用(Design Decision 9)
- データの型:
  - `Item`: `id`, `name`, `rarity`(`common` / `uncommon` / `rare`), `image`, `footprint`(占めるマス数、MVPは全て1×1)
  - `InventoryEntry`: `id`, `itemId`, `receivedAt`, `note`(思い出の一言、任意)
  - `Placement`: `inventoryId`, `x`(0〜5), `y`(0〜5)
  - `Gift`: `id`, `source`(`steps` / `daily`), `createdAt`, `openedAt`, `itemId`

**Files affected:**

- `~/Projects/walk-town/` 一式
- `~/Projects/walk-town/docs/CONTRACT.md`

---

### Step 4: 保存の仕組みと小物カタログを作る(Claude)

**Actions:**

- `src/data/catalog.ts` に12種を定義する。
- `src/db/` にSQLiteの初期化を作る。テーブルは `inventory`、`placements`、`gifts`、`events`(利用記録)、`meta`(最後に数えた歩数、最後にきょうのおみやげを配った日)。
- 抽選: ふつう70%、すこし珍しい25%、珍しい5%。持っていない小物が出やすいように、未所持に重みをつける。
- 読み書き関数を作る: `listInventory`, `savePlacement`, `createGift`, `openGift`, `logEvent`。

**Files affected:**

- `~/Projects/walk-town/src/data/catalog.ts`
- `~/Projects/walk-town/src/db/*.ts`

---

### Step 5: 歩数で包みが届く仕組みを作る(Claude)

**Actions:**

- アプリを開いたとき、`Pedometer.getStepCountAsync(前回確認時刻, 現在)` で歩数を取る。
- 2,000歩ごとに `gifts` を作る。その日すでに3包みあれば作らない。
- その日に一度も「きょうのおみやげ」を配っていなければ1包み作る。
- 歩数の許可が拒否された場合は、きょうのおみやげだけで動くようにする。
- 通知はMVPでは入れない。「言われなくても開くか」を観察するため。

**Files affected:**

- `~/Projects/walk-town/src/gifts/checkSteps.ts`
- `~/Projects/walk-town/app/_layout.tsx`

---

### Step 6: 4画面の骨組みを作る(Claude)

**Actions:**

- 街: 6×6マスに、配置済みの小物を表示する。未開封の包みがあれば「包みが届いています」を出す。仮の四角い表示でよい。
- 包みを開ける: 包みをタップすると小物が出る。仮の表示でよい。思い出の一言を入力できる(任意)。
- 図鑑: 12種を並べ、未入手はシルエットにする。
- 設定: 利用記録を文字として書き出してコピーできるボタン、データの初期化(確認つき)。
- 各操作で `logEvent` を呼ぶ: `app_open`, `gift_opened`, `item_placed`, `item_moved`, `collection_viewed`, `screenshot_taken`(iOSのスクショ検知で取れる範囲)。
- ここまでを `main` にまとめ、Codexに渡せる状態にする。

**Files affected:**

- `~/Projects/walk-town/app/**`

---

### Step 7: 演出と操作を作り込む(Codex)

**Actions:**

- `CONTRACT.md` を読み、`ui/gift-open` と `ui/town-grid` のブランチで作業してもらう。
- 包みを開ける: 揺れる→リボンがほどける→小物が跳ねて出る。レア度で演出を変える。開いた瞬間に触覚フィードバック。
- 街: 長押しで持ち上げ、ドラッグで置き、マスに吸い付く。置いたときに小さく弾む。
- 街全体をピンチで少し拡大・縮小できる。
- Codexへの指示文はClaudeが書く。データの型や保存処理は変えないこと、変えたいときは提案に留めることを明記する。

**Files affected:**

- `~/Projects/walk-town/src/components/GiftOpenAnimation.tsx`
- `~/Projects/walk-town/src/components/TownGrid.tsx`

---

### Step 8: 実機で触って直す(すばる + Claude)

**Actions:**

- Codexのブランチを `main` にまとめ、実機(iOS 26)で動かす。
- すばるが3日間自分で使い、触り心地と見た目の直したい点を挙げる。
- 直す。見た目の直しはCodex、動作の不具合はClaudeが担当する。
- iOS 26で起動直後に固まらないか、reanimatedの不整合がないかを必ず確認する。

**Files affected:**

- `~/Projects/walk-town/**`

---

### Step 9: TestFlightで友人に配る

**Actions:**

- EASでiOS用に作り、TestFlightに上げる。bundle idは `com.subaruono.walktown`(仮)。
- 友人5〜8人を招待する。渡す説明は「散歩するとおみやげが届く。好きに飾ってね」の一言だけにし、使い方を細かく教えない。
- テスト期間中に催促しない。

**Files affected:**

- `~/Projects/walk-town/eas.json`
- `~/Projects/walk-town/app.json`

---

### Step 10: 2週間後に結果をまとめて判断する

**Actions:**

- 各友人に設定画面から利用記録を書き出して送ってもらう。
- 5分の聞き取りをする: 何が楽しかったか、開かなくなった日はいつでなぜか、人に見せたか、お金を払うとしたら何に払うか。
- 結果を `outputs/walk-town/2026-10-mvp-test-results.md` にまとめ、Success Criteriaで判断する。
- 判断は3択: 本格開発に進む / 方向を変えて再検証 / やめる。

**Files affected:**

- `outputs/walk-town/2026-10-mvp-test-results.md`(AI-OS)

---

### Step 11: AI-OS側のドキュメントを整える

**Actions:**

- `docs/walk-town.md` にリポジトリの場所、技術構成、分担、現状を書く(`docs/shigabase.md` と同じ形)。
- `docs/_index.md` に追加する。
- `context/tech-stack.md` に新しいリポジトリを追記する。
- `ledger/subaru.md` に記録する。

**Files affected:**

- `docs/walk-town.md`
- `docs/_index.md`
- `context/tech-stack.md`
- `ledger/subaru.md`

---

## Connections & Dependencies

### Files That Reference This Area

- [docs/shigabase.md](../docs/shigabase.md): 同じ技術構成とEASの運用を参考にする。
- [context/tech-stack.md](../context/tech-stack.md): リポジトリ追加時に更新する。

### Updates Needed for Consistency

- `docs/_index.md` に新しいドキュメントを登録する。
- アプリがAI-OSの外にあることを `docs/walk-town.md` に明記する。

### Impact on Existing Workflows

- SHIGABASEには触らない。Expo SDKとreanimatedのバージョン問題の知見だけを流用する。
- SHIGABASE複数チーム版の需要調査(チームへのヒアリング)とは並行できる。こちらは営業が不要。

---

## Validation Checklist

- [ ] 実機で、歩数に応じて包みが届く(2,000歩ごと、1日最大3つ)
- [ ] 歩数の許可を拒否しても、きょうのおみやげが1日1つ届く
- [ ] 包みを開けた小物が図鑑に反映される
- [ ] 小物を街に置き、アプリを完全に終了して再起動しても配置が残る
- [ ] 機内モードで全機能が動く(サーバーを使っていない確認)
- [ ] 位置情報・HealthKitの許可を一度も求めない
- [ ] iOS 26の実機で、起動直後に固まらない
- [ ] 利用記録を書き出せる
- [ ] TestFlightで友人の端末にインストールできる

---

## Success Criteria

2週間テストの判断基準:

1. 友人の半数以上が、2週間のうち7日以上アプリを開いている(催促なし)
2. 友人の半数以上が、一度置いた小物を自分で並べ替えている(`item_moved` が記録されている)
3. 少なくとも2人が、言われなくても街のスクショを誰かに見せた、または見せたいと言った

3つとも満たせば本格開発に進む。1つ以下なら、やめるか方向を変える。

---

## Notes

- 本格開発に進んだら検討すること: 友人とのQR交換(サーバーなしで可能)、iCloudでの引き継ぎ、飾る場所の追加、季節限定の小物、初めて行った場所のボーナス、SwiftUIへの移行、アプリ名とアイコン。
- 検討の経緯: すれちがいMii広場のスマホ版から、Codexのセカンドオピニオンで「散歩のおみやげで小さな街を作る」に方向転換した(2026-09-15)。
- 近い既存アプリ: ピクミン ブルーム(歩く+集める)、ねこあつめ(眺める)、ポケ森(短時間で飾る)。差別化は「手のひらサイズのジオラマを作って飾る」こと。
