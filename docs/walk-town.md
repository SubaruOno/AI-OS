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

## 現状(2026-09-16 22:00)

- 見た目の作り直しはブランチ `art/plateless-trial` でほぼ完了。小物は台なしの絵で18種、地面は島1枚の絵、影は足元にアプリ側で描く。main への取り込みは、すばるが実機で見た目を確かめてから。
- 遊びの足し: 新しい小物の手紙3通(物語の手紙は13通、TestFlight利用者の進行がずれないよう末尾に追加)、場所は全11か所、住人のタップのセリフは各6つ、その日最初のタップは場所にちなむ一言。物語の手紙を読み終えたあとは日替わりのお願いが毎日1つ届く。
- つまずき対策: 開けた小物を「これを飾る」ですぐ置ける、歩数を読めないときの理由と設定への導線、手紙に合わせて持ち帰り候補が変わる、上限後も翌日の持ち帰りを予約できる、同じ日に開いた後日談を全部順に見せる、日誌に住人ごとの「続きまであと何日」。
- 朝のおしらせ通知(`src/notifications/`、expo-notifications)。10:30、その日0歩のときだけ住人のひとこと。予約制なので、アプリを開かずに歩いた日にも届くことがある(制約は `docs/CONTRACT.md`)。ネイティブの部品が増えたので、TestFlightには新しいビルドが要る。「テストしてほしいこと」の文案は `docs/TESTFLIGHT.md`。
- `scripts/check.sh` に、手紙や場所で使う小物IDがカタログに実在するかの検査(`scripts/check_item_ids.py`)を追加。
- Codex CLI と並行で開発した。Codex の利用上限は 2026-09-17 01:59 に戻る。

## 以前の現状(2026-09-16 16:25)

- 見た目を作り直している。原因は、小物の絵が「草の台に載った1マス」として描かれ、地面のマスと二重に重なっていたこと。倍率や島の形をいじっても直らず、絵の作り方から変えることにした。計画は[見た目の作り直し](../plans/2026-09-16-walk-town-look-rework.md)、真上から見た地図の案は[別案](../plans/2026-09-16-walk-town-map-view.md)。
- 新しい決まりは `docs/ART_GUIDE.md`(アプリのリポジトリ)にある。小物は台なし・物だけ・影なしで描き、大きさは人の背丈を1.0とするものさしで決める。比率は絵ではなく `tileW` の数値で揃える。
- TestFlightのフィードバック3件と、直すことリストは[記録](../outputs/walk-town/2026-09-16-testflight-feedback.md)。
- ブランチ: `fix/feedback-round1` に触り心地の修正、`art/plateless-trial` に台なしの絵の試作(ポストと時計塔の2種)。

## 以前の現状(2026-09-16 7:35)

- 夜間の開発で遊びの仕組みを足し([夜間開発レポート](../outputs/walk-town/2026-09-16-overnight-report.md))、朝は見た目・手触り・配置と結果のつながりを35の仮説で改善した([朝の仮説検証ログ](../outputs/walk-town/2026-09-16-morning-hypotheses.md))。
- 住人5人、紙袋、包み、対岸の村、アイコンの絵は Codex CLI の画像生成で作った(`~/Projects/tekuteku-art`)。
- 仕組みの一覧、テスト用リンクは、リポジトリの `docs/CONTRACT.md` が正本。TestFlightの手順は `docs/TESTFLIGHT.md`。変更前に `scripts/check.sh` を通す。
- iPhone実機はExpo Go(`exp://192.168.11.35:8081`、Macと同じWi-Fi)で接続確認済み。
- 未確認: 実機での効果音・触覚・ピンチ・ドラッグ・歩数計、長時間動かしたときの重さ、LINEへの絵はがき送信。
- App Store提出素材はリポジトリの `store/` にある(アイコン、6.9インチのスクショ5枚、`store.config.json` の説明文、プライバシーポリシー)。手順は `store/README.md`。
- 2026-09-15: 起動画面フリーズを修正したビルドがTestFlightで正常に動作(すばるの実機で確認)。App Store Connectのアプリ・説明文・スクショ・プライバシーURLは登録済み。
- 未着手: 台なしの小物の絵、プライバシー情報の「公開」、外部テスト(友だち配布)、審査提出。
- シミュレーターの専用パネルは、Xcodeが選択されていないため使えない(`sudo xcode-select -s /Applications/Xcode.app/Contents/Developer` が必要)。
