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

## 現状(2026-09-24 19:38)

- 「ゲームとして拡張したい、アイテム過多でやることがない」という課題に着手。原因は「入り口が太い・出口が細い・目標がない」の3点。ブランチ `base/town-growth`。
- **まちの事業**([src/town/projects.ts](https://github.com/SubaruOno/walk-town/blob/base/town-growth/src/town/projects.ts)、[app/projects.tsx](https://github.com/SubaruOno/walk-town/blob/base/town-growth/app/projects.tsx))を追加。住人が**タグ指定**で小物をまとめて要求し、まちに置いていない予備を出すと完成する。まちポイントが増え、しきい値(0/1/5/10/15/21)で**まちレベル**が「はじまりの村→小さな村→にぎわう村→湖の町→大きな町→湖の都」と上がる。レベルで新しい事業が解放。事業は複数同時に出て、どれを先に建てるか・おてつだいに回すかの選択がある。入口は**まち画面のLvチップ**または図鑑の「まちの事業」行。
- **合成**([src/town/craft.ts](https://github.com/SubaruOno/walk-town/blob/base/town-growth/src/town/craft.ts))を追加。図鑑で、同じ小物の予備3つを次のレア度1つにまとめる(未所持が出やすい)。事業ほど大きくない、手元で完結する出口。
- 検証: ①`scripts/check.sh`(型・lint・小物ID)通過。②[sim_projects.py](https://github.com/SubaruOno/walk-town/blob/base/town-growth/scripts/sim_projects.py) が**詰み**(Lv1の事業が2点なのにLv2のしきい値が3点で先へ進めない)を検出し、しきい値を修正。修正後はカジュアル(2包み/日)でLv6まで約22日、アクティブ(3包み/日)で約15日。③[sim_craft.py](https://github.com/SubaruOno/walk-town/blob/base/town-growth/scripts/sim_craft.py) で合成は30日で5〜10回、余りは40〜80個。**主な出口は事業(全事業で計51個消費)で、合成は補助**と確認。④iOSシミュレーターで起動し、事業の建設→Lv.2へ上昇→Lv2事業の解放→材料不足の無効表示、合成でベンチ4→1こ・図鑑2/18→3/18 を実機確認。
- **落ちる不具合を1件修正**。小物を選んだまま「きょうのおてつだい」で同じ小物を住人に渡すと、在庫から消えた小物を配置できてしまい、在庫を指さない配置(孤児)ができて次回の読み込みでクラッシュしていた(`Cannot read property 'itemId' of undefined`)。`savePlacement` が在庫の存在を確認するようにし、起動時に孤児配置を削除するようにした(`src/db/index.ts`)。選択中の小物が消えたら選択を解除し、`useTown` も孤児を無視する。この不具合は「おてつだい」(ui/daily-help)の時点で起き得たもので、事業・合成で削除経路が増えて目立った。
- **ホームと図鑑の画面を整理**([app/(tabs)/index.tsx](../../Projects/walk-town/app/(tabs)/index.tsx)、[app/(tabs)/collection.tsx](../../Projects/walk-town/app/(tabs)/collection.tsx))。散歩、おてつだい、手紙を常時表示する代わりに、画面下の「今日のこと」から開く形にまとめ、閉じた状態では島を広く見せる。歩数非対応の説明も短い表示にし、詳細はパネル内へ移した。Lvチップをホームのヘッダーに戻し、まちの事業を直接開ける。図鑑は「持っている小物」と「まだ出会っていない小物」に分け、未発見品の大きな灰色シルエットを小さな「？」に置き換えた。
- 確認: `./scripts/check.sh` 通過。iPhone 17 Pro Max / iOS 26.4 シミュレーターでホーム、「今日のこと」パネル、図鑑、日誌、設定、まちの事業を開いて表示を確認。合成や建設の操作は今回のセーブデータ上で未実施。Web確認はExpo SQLiteのWeb用WASMが見つからず起動できなかったため、iOSシミュレーターを使った。
- 未了: `ui/daily-help` の main 取り込み、`art/plateless-trial` の取り込み、ウィジェットの実機確認、事業でどれを先に作るかの選択が弱い点。

## 以前の現状(2026-09-24 18:55)

- 小物の使い道が「置く」しかなく、置いても11個の決まった隣接レシピ以外は何も起きないため、余った小物がトレイに溜まる一方だった。そこに出口と目標を足した。ブランチ `ui/daily-help`(2コミット、GitHubへpush済み)。
- **きょうのおてつだい**([src/town/help.ts](https://github.com/SubaruOno/walk-town/blob/ui/daily-help/src/town/help.ts))を追加。引っ越し済みの住人が毎日2件、名指しで小物を1つ頼む。**まちに置いていない予備をわたす**と在庫から消え、なかよし度が増える。1件目は必ず「いま渡せるもの」、2件目は散歩が要ることもあるので、その日のうちに1件は達成できる。置いた小物は渡せないので「飾るか、あげるか」が初めての選択になる。
- **なかよし度**を追加。rarity に応じて1/2/4点。しきい値は0/6/18/36/60の5段階で「はじめまして→ともだち→なかよし→だいすき→かぞくみたい」。ランクが上がるとお礼の包み1つと日誌の記録。街の画面のカードに現在のランクと次のランクまでの残り点が出る。
- 小物に**タグ**を追加(`wood` / `green` / `water` / `light` / `rest` / `food` / `play` / `show` / `town`)。これからの場所・レシピ・おねがいは id ではなくタグで書けるので、小物を1つ足せばタグ経由で自動的に候補に入る。今回のおてつだいの文面も、この形で足していく前提。
- `./scripts/check.sh`(型・lint・小物ID)は通過。小物IDの検査が `src/town/help.ts` も見るようにした。**シミュレーターでの画面確認は未了**(開発サーバーにバンドルを読ませられず起動画面で止まった。コード側の問題ではない見込み)。実機かビルドで見てから main への取り込みを判断する。
- `art/plateless-trial` の見た目の確認、ウィジェットの実機確認(Step 5)、App Store審査の提出は引き続き未着手。

## 以前の現状(2026-09-18 15:13)

- ブランチ `art/plateless-trial` は main より61コミット進み、**GitHubへpush済み**(2026-09-18)。main への取り込みは、すばるが実機で見た目を確かめてから。
- 9/17のTestFlightフィードバック3件のうち2件を直してコミット。最後の包みで同じ意味のボタンが2つ出る件は、表示名と動きの判定を `listUnopenedGifts()` にそろえて解決。ドラッグ中のマス目は、置き待ちと同じ光り方を出し、置き先のひし形を運んでいる小物(zIndex 2000)より上の2500へ。型・lint・小物IDの検査は通過。シミュレーター(iPhone 17 Pro Max)で確認済み: 最後の包みの画面はボタンが「まちに飾りにいく」1つだけになり、小物14個の密な街でもマス目は小物の半透明越しにはっきり読める。ドラッグも移動が成立しクラッシュなし。
- ホーム画面ウィジェット(Small・Medium)とダイナミックアイランドを実装し、シミュレーターで確認済み。仕組みと残作業は[ウィジェットの計画](../plans/2026-09-15-walk-town-widget-dynamic-island.md)。App Groups の Apple Developer 登録だけすばる待ちで、実機と EAS ビルドに必要。
- 残りの1件「トレイから直接ドラッグで置く」も実装し、シミュレーターで確認済み。タップして選ぶ従来のやり方も残している。詰まった点が3つ: 横スクロールのトレイに指を取られる(縦方向を先に確保して解決)、開始時に`setSelectedId`を呼ぶとトレイが切り替わってジェスチャーを持つビュー自体が消える(呼ばない形に変更)、`townLayout`に`'worklet'`を付けると巻き上げが効かず未定義になる(JSスレッドで計算する形に変更)。
- まとめ開封で同じ小物が2つ出る件は、抽選式を写して20万回回した結果**確率どおりで不具合ではない**と結論し、直さないことにした。根拠は[記録](../outputs/walk-town/2026-09-18-duplicate-draws.md)。
- 開発ビルド(Debug)を `npx expo run:ios` で作り直した。9/16 15:12の古い方はexpo-notifications追加前でネイティブ部品が足りず起動しなかった。

## 以前の現状(2026-09-16 22:00)

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
