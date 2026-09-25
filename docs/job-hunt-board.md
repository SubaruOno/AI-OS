# 就活リーダーボード

> 就活の締切と選考状況を集めて、企業が「今どれだけ動くべきか」の順に並ぶアプリ。
> コードは [apps/job-hunt-board](../apps/job-hunt-board/README.md)、元データは
> `private/job-hunt/` に置いたままにしている。

## 何ができるか

締切マスターの Markdown、締め切りナビの追加候補、Gmail のメールを合わせて、
企業ごとに次の3つを出す。

1. 選考段階（応募前 / 応募・ES / 適性検査 / 面接 / 最終・内定）
2. 次に来る締切までの日数
3. その2つから出したスコア

スコアが高い企業ほどリーダーボードの上に来る。締切が近いと加点され、選考が
進んでいると加点される。見送りや不合格は0点になる。

## 構成

| 層 | ファイル | 役割 |
|---|---|---|
| 取り込み | `parse.py` | 締切マスターと締め切りナビの Markdown を解析する |
| 取り込み | `sync_gmail.py` | Composio 経由で Gmail を読む（読み取り専用） |
| 判定 | `stages.py` | 段階の推定、ノイズ除去、スコア計算 |
| 統合 | `build_feed.py` | `data/feed.json` を書き出す |
| 収集 | `collect_mypages.py` | Chromeから各社マイページのURLとログインIDを集める |
| 表示 | `server.py` | ブラウザ用の画面と `/api/feed` を出す |
| 表示 | `mobile/` | iOSアプリ（Expo / React Native） |

## 元データの持ち方

Markdown は人が読む正本として残し、アプリ用のデータは `data/` に生成する。
`data/` と `private/job-hunt/board-state.json` は Git に載せない。企業名と選考状況が
入るため、`private/` と同じ扱いにしている。

## メールの接続

Composio に繋がっているのは `subaru.ono1@gmail.com` だけ。企業からの選考メールは
`subaru.ono15@gmail.com` に届いているので、そこはまだ自動で拾えていない。大学と
部活の連絡が Outlook にあるのと同じで、繋がっていないアカウントは検索しても空に
なるだけで、メールが無いことにはならない。

ono15 を足すときは、そのアカウントでログインした状態で `composio link gmail` を
実行し、`sync_gmail.py --account` にそのアカウントを渡す。

## 決めたこと

- 段階の推定は決定的なキーワード一致だけで行う。根拠が無い企業は「応募前」のままにする
- 広告かどうかは差出人だけで判定する。件名で判定すると企業のメールまで落ちる
- `axol.jp` などは企業ATSの直送なのでノイズにしない（住友商事が該当する）
- 元データの Markdown には書き込まない

## マイページとログインID

企業ごとのマイページURLとログインIDは Chrome の履歴と「保存したログイン情報」から集める。
パスワードは読まないし、保存もしない。`Login Data` のうち `username_value` 列だけを見る。

対象にしているATSは axol、i-webs、i-web.jpn.com、snar、saiyo、NRI、eARTH、ソニー、
三菱UFJ銀行、三井住友銀行、talent-p。ここに無いドメインは拾わない。

会社をまたいで同じログインIDが出たときは、その企業専用の値があればそちらを選ぶ。
シンプレクスや双日のIDがGmailアドレスになるのは、多くの企業でメールアドレスを
IDにしているため。

集めた結果は `private/job-hunt/mypages.json` に置く。手で足したいものは
`private/job-hunt/mypages-manual.json` に書けば、再収集しても残る。ログインIDを
含むので、アプリ同梱の `mobile/assets/mypages.json` もGitには載せない。

## 確かめ方

```sh
python3 -m unittest discover -s apps/job-hunt-board/tests
sh apps/job-hunt-board/refresh.sh
python3 apps/job-hunt-board/server.py
```

## 現状

- 締切 59件、企業 39件を取り込んでいる（2026-09-25 時点）
- 解析・統合・Web画面は動く
- iOSアプリはビルドとインストールまで確認済み。起動時の画面確認は下の事情で未完
  （シミュレータの別プロジェクト開発サーバーとポートが衝突した）
