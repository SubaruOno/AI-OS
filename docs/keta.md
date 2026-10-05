# ケタ感（数字を幅で当てる日替わりゲーム）

1日5問、数字を「90%の自信で入る幅」で答えるブラウザゲーム。2026-10-06の深夜に一晩で作った。作った経緯と検証の結果は[開発レポート](../outputs/keta/report.md)にある。

- 遊ぶ：<https://claude.ai/artifact/Rgen6tgcCC6uMrbNLAyTnH>（非公開のページ）
- コード：[index.html](../apps/keta/index.html)、問題は[questions.json](../apps/keta/questions.json)

## 仕組み

- 採点は対数の目盛りでのWinkler区間スコア。点＝100−25×スコア。外れると、はみ出した分の20倍が引かれる。0点を下回ることもある。
- 問題は日本時間の日付から選ぶので、同じ日なら全員が同じ5問になる。練習モードはランダム。
- 自分の的中率はブラウザに保存する。各問題の答えは、ページのデータベースの `answers` に匿名で保存され、「みんなの的中率」として表示される（練習の答えは保存しない）。

## 問題を足すとき

1. [questions.json](../apps/keta/questions.json) に1件足す。出典URLは必ず付ける。
2. `questions.js` を作り直す：`python3 -c "import json;d=json.load(open('apps/keta/questions.json'));open('apps/keta/questions.js','w').write('const QUESTIONS='+json.dumps(d,ensure_ascii=False)+';\n')"`
3. index.html と questions.js を同じURLに公開し直す。

答えが有名な問題（富士山の標高など）は迷う余地がないので入れない。手元で確かめるときは、`.claude/launch.json` の `keta` でサーバーを立てて `preview.html` を開く。

## 未確認のこと

- 人が遊んだときに、本当に自信過剰が出るか（中心の仮説）。
- データベースへの書き込みが実際の画面で動くか。読み取りだけ確認済み。
