# ケタ感 UIパターン調査

調査日: 2026-10-06。対象は日替わりの数字推定ゲーム（90%信頼区間を定規の上の幅で答える、マスコットあり、iPhone/SwiftUI）。
各パターンは「何をしているか / なぜ効くか / ケタ感での実装案」の順に書いています。出典に具体的な数値がないものは、一般に知られた挙動として書きました（出典欄に「観察」とあるもの）。

## 主な出典

- Wordleの演出と共有: https://dinogame.gg/blog/why-is-wordle-so-popular/ , https://wyzowl.beehiiv.com/p/the-magic-behind-wordle , https://vp0.com/blogs/wordle-clone-swiftui-source-code
- Duolingo: https://blog.duolingo.com/streak-milestone-design-animation , https://blog.duolingo.com/how-duolingo-streak-builds-habit , https://blakecrosley.com/guides/design/duolingo , https://duolingo.deconstructoroffun.com/mechanics/streaks
- 較正ゲーム: https://www.clearerthinking.org/post/2019/10/16/practice-making-accurate-predictions-with-our-new-tool , https://lovkush.substack.com/p/an-anecdotal-critique-of-clearerthinkings , https://forum.effectivealtruism.org/posts/dAcKjgC4fMesXesyf/the-estimation-game-how-well-calibrated-are-your-intuitions , https://www.lesswrong.com/posts/5XBv2onWGRKFtAEMN/link-how-to-calibrate-your-confidence-intervals
- Wikitrivia: https://en.wikipedia.org/wiki/Wikitrivia
- Immaculate Grid: https://en.wikipedia.org/wiki/Immaculate_Grid , https://scienceoflearning.jhu.edu/tof/beyond-perfection-the-allure-of-the-immaculate-grid
- Clues by Sam: https://en.wikipedia.org/wiki/Clues_By_Sam
- Connections共有: https://tech.yahoo.com/general/articles/nyt-connections-hint-answers-today-050032582.html
- Juice: https://rpgplayground.com/research-making-a-juicy-game/ （"Juice it or lose it" Jonasson & Purho の解説）, https://gamedeveloper.com/design/squeezing-more-juice-out-of-your-game-design- , https://gameanalytics.com/?p=3400

---

## (1) 答え合わせの瞬間

| パターン | 何をしているか / なぜ効くか | ケタ感での実装案 |
|---|---|---|
| 1枚ずつめくる遅延リビール（Wordle） | タイルを左から順に裏返し、結果を一度に見せない。数百ミリ秒の「溜め」で期待が膨らむ。出典: dinogame, wyzowl | 正解マーカーを定規の端から自分の区間へ向けてスライドさせ、到着時に色が決まる。`withAnimation(.spring(response:0.5,dampingFraction:0.7).delay(0.3))` |
| 正解時の「勝ちダンス」（Wordle） | 全タイルが順に跳ねる。成功を体で感じさせる。出典: dinogame | 区間内に入ったら区間バーを `scaleEffect` で1.0→1.12→1.0にはね、マスコットがジャンプ。外れたら `offset` で左右に3回揺らす（Wordleの無効語シェイク） |
| ケタ単位の目盛りズーム | 答えが区間の外でも「何ケタずれたか」が見えると納得感が出る。出典: 観察（Estimathon系の比率採点の考え方） | 外れた場合はカメラを引いて、正解と区間の両方が入る倍率まで定規をアニメーションで縮める。「×3 ずれ」「1ケタ下」などの距離ラベルを表示 |
| 触覚と音を結果ごとに変える（juice） | 視覚・触覚・音を重ねると同じ結果でも手応えが増す。出典: rpgplayground, gameanalytics | 命中は `UINotificationFeedbackGenerator().notificationOccurred(.success)`、外れは `.warning`。SwiftUIなら `.sensoryFeedback(.success, trigger:)` |
| 狭くて当たったら特別演出 | 幅が狭いほど価値が高いことを、演出の大きさで伝える。出典: Immaculate Gridのレア度スコアの発想 | 幅スコア上位なら紙吹雪（`Canvas`＋`TimelineView`か、Lottie）。広すぎて当たった時は控えめに「安全運転」と表示 |

## (2) 連続日数・習慣化

| パターン | 何をしているか / なぜ効くか | ケタ感での実装案 |
|---|---|---|
| 炎が燃え上がる連続日数（Duolingo） | 1日の終わりに炎が点火する演出。数字が増える瞬間を儀式にする。出典: duolingo blog, deconstructoroffun | 結果画面の後に専用の1画面を挟み、日数の数字を `contentTransition(.numericText())` で繰り上げる |
| 節目でマスコットが変身（Duolingo） | 7・30・100日などの節目を「パワーアップ」として扱い、キャラ自体が変わる。出典: blog.duolingo.com/streak-milestone-design-animation | 節目の日だけマスコットに帽子などの装備を追加し、以後の画面でもその姿で出す |
| 軽い連続日数（Wordle） | 継続を褒めるが、毎日を強制しない。3分で終わる設計。出典: dinogame | 1日1問を守り、追加問題で引き止めない。「また明日」で閉じられる画面にする |
| 連続記録の保険（Duolingoのストリークフリーズ） | 1日休んでも全部失わない仕組みで、途切れた時の離脱を防ぐ。出典: how-duolingo-streak-builds-habit | 月1回だけ自動で使える「おやすみ札」。消費された日はカレンダーに氷のアイコン |
| 週のカレンダー表示 | 今週の◯×が並ぶと、空いたマスを埋めたくなる。出典: 観察（Duolingo週間表示） | 結果画面上部に月〜日の7つの丸、命中は塗り、外れは輪郭、未プレイは灰色 |

## (3) 結果共有の見た目

| パターン | 何をしているか / なぜ効くか | ケタ感での実装案 |
|---|---|---|
| ネタバレしない絵文字グリッド（Wordle） | 過程は見せるが答えは見せない。貼っても未プレイの人の楽しみを奪わない。出典: dinogame | 定規を文字で描く。例 `ケタ感 #42 ▁▁[■■■]▁▁ 🎯 幅×4` 。正解位置は区間内なら🎯、外なら◀や▶ |
| 色で順序を記録（Connections） | 色の並びが解いた順番を語る。出典: yahoo | 1日の問題数が複数なら、問題ごとに🟩🟨🟥（命中/ギリギリ/外れ）を1行に |
| 画像シェア（Clues by Sam） | テキストに加えてきれいな画像も選べる。出典: wikipedia Clues_By_Sam | `ImageRenderer` で結果カード（定規＋マスコット）をPNGにし、`ShareLink` に渡す |
| 他人との比較値（Immaculate Grid） | 「何%の人より狭い」などが話題の種になる。出典: wikipedia Immaculate_Grid | サーバーで全体分布を集計し「今日の幅は上位18%」を共有文に入れる（バックエンドが要る） |

## (4) 統計画面

| パターン | 何をしているか / なぜ効くか | ケタ感での実装案 |
|---|---|---|
| 4つの大きな数字＋分布棒（Wordle） | プレイ回数・勝率・現在/最大連続と、試行回数の分布。一目で自分がわかる。出典: buttondown.com/nuno (Wordle clone解説) | 上段に「回答数・命中率・連続・最長」。下段に幅の分布を `Swift Charts` の `BarMark`、今日の棒だけ色付け |
| 較正グラフ（Clearer Thinking） | 「90%と言った時に実際何%当たったか」を見せる。このゲームの核心。出典: clearerthinking.org | 目標90%に点線、自分の命中率を太線。直近30問の移動平均を `LineMark` で。「自信過剰」「慎重すぎ」のどちら寄りかを一言で |
| 採点ルールの説明不足への注意 | 点数の仕組みが分かりにくいと不満が出るという体験談。出典: lovkush.substack.com | スコアの内訳（命中ボーナス、幅の対数ペナルティ）を統計画面でタップすると開く形で見せる |

## (5) キャラクターの使い方

| パターン | 何をしているか / なぜ効くか | ケタ感での実装案 |
|---|---|---|
| 正解時の小さな反応（Duolingoのキャラ） | キャラのわずかな動き自体が報酬になる。出典: blog.duolingo.com | 表情を3〜5種類（待機・考え中・喜び・残念・驚き）用意し、状態に応じて切り替え。Rive/Lottieか、SF Symbolsの `symbolEffect(.bounce)` で代用 |
| 入力中に反応するキャラ | 幅を広げると心配顔、狭めると汗をかくなど、操作中から会話になる。出典: 観察（Duolingoのタイピング中の反応） | 区間幅の値をマスコットの表情パラメータに直結。`onChange(of: width)` で段階切り替え |
| モーションの尺を決める | Duolingoは節目のジャンプに480msのスプリング、解放に320msを使う。出典: blakecrosley.com | 短い反応は300ms前後、節目の演出は500ms前後に揃え、アプリ全体の手触りを統一 |
| 叱らない外れ演出 | 失敗を罰すると翌日来なくなる。出典: how-duolingo-streak-builds-habit | 外れたらマスコットが「意外！」と驚き、豆知識を1行添える。外れは学びの瞬間として見せる |

## (6) 入力操作の気持ちよさ

| パターン | 何をしているか / なぜ効くか | ケタ感での実装案 |
|---|---|---|
| 入力時のポップ（Wordle） | 文字を打つたびタイルが一瞬大きくなる。押した感覚が返る。出典: dinogame | 区間の端をつかんだ瞬間にハンドルを1.2倍、離したら戻す |
| 目盛りの吸着＋カチカチ触覚 | 1、2、5、10…の切りの良い値に吸い付き、通過ごとに軽い振動。物理的なダイヤルの感覚。出典: juice解説（gameanalytics, rpgplayground） | `.sensoryFeedback(.selection, trigger: snappedValue)`。対数目盛りなので吸着点は1-2-5系列 |
| 対数定規のピンチ操作 | 2本指で幅、1本指で位置。ケタをまたぐ操作が直感的になる | `MagnifyGesture` と `DragGesture` を `simultaneousGesture` で併用。現在の幅を「約3倍の幅」と言葉でも表示 |
| 送信前の確認を軽く | 長押しやスライドで確定させると、誤送信を防ぎつつ儀式感が出る | 「確定」ボタンを0.4秒長押しでリングが一周して送信 |

## (7) 初回体験

| パターン | 何をしているか / なぜ効くか | ケタ感での実装案 |
|---|---|---|
| 説明より先に1問遊ばせる（Wordle, Wikitrivia） | ルールが数秒で分かる画面構成で、すぐ遊べる。Wikitriviaは置くだけで理解できる。出典: wikipedia Wikitrivia | 初回は誰でも知っている問題（例: 東京タワーの高さ）で、マスコットが指で操作を示す |
| 90%の意味を体験で教える（Estimation Game, LessWrong） | 多くの人は区間が狭すぎて自信過剰になる。最初にそれを体験させると目的が腹落ちする。出典: lesswrong, EA forum | チュートリアルを3問にして、外れたら「人は普通、狭くしすぎます」と伝え、広げて再挑戦させる |
| ライフ制で緊張感（Wikitrivia, Duolingoのハート） | 3回までの失敗枠で、1問ごとの重みが増す。出典: wikipedia Wikitrivia | 練習モードのみハート3つ。外れでハートがひび割れて消える演出（`scale`+`opacity`） |

---

## トップ10（入れる価値が高い順）

| 順位 | パターン | 実装の重さ |
|---|---|---|
| 1 | 正解マーカーの遅延スライドリビール＋命中で区間がはねる／外れで揺れる | 小 |
| 2 | 目盛り吸着＋選択触覚（カチカチ）と、つかんだ時のハンドル拡大 | 小 |
| 3 | 結果別の触覚・音（命中success、外れwarning） | 小 |
| 4 | ネタバレしないテキスト定規の共有文（🎯/◀▶＋幅倍率） | 小 |
| 5 | 較正グラフ（目標90%と自分の命中率、自信過剰/慎重すぎの一言） | 中 |
| 6 | 連続日数の専用画面（数字の繰り上げ＋週の7つの丸） | 中 |
| 7 | マスコットの表情を入力幅と結果に連動（5表情） | 中 |
| 8 | 外れた時に定規を引いて「何ケタずれたか」を見せる | 中 |
| 9 | 初回3問チュートリアル（狭すぎ体験→広げて再挑戦） | 中 |
| 10 | ImageRendererの画像シェア＋全体比の「上位◯%」 | 大（全体比はサーバー集計が必要。画像シェアだけなら中） |

連続日数の保険（おやすみ札）と節目のマスコット変身は、利用者が増えてから足せば十分です。
