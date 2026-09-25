# 就活リーダーボード

就活の締切と選考状況を1か所に集める道具。iOSアプリと、その中身を作るPythonが入っている。

企業は「今どれだけ動くべきか」で並ぶ。締切が近いほど、選考が進んでいるほど上に来る。
順位は急かすためのものではなく、今日どこに時間を使うかを決めるためのもの。

## 何でできているか

| ファイル | 役割 |
|---|---|
| `parse.py` | `private/job-hunt/` の Markdown を読んで締切の一覧にする |
| `sync_gmail.py` | Composio 経由で Gmail を読み、就活に関係するメールだけ残す（読み取り専用） |
| `stages.py` | 件名やメモから選考段階（応募前／応募・ES／適性検査／面接／最終・内定）を推定する |
| `build_feed.py` | 上の3つを1つの `data/feed.json` にまとめる |
| `collect_mypages.py` | Chromeの履歴と保存ログイン情報から各社マイページのURLとログインIDを集める |
| `server.py` | ローカルで画面を開くための小さなWebサーバー |
| `mobile/` | iOSアプリ（Expo / React Native） |

元データの Markdown には書き込まない。書き込むのは `private/job-hunt/board-state.json`
（対応済みの記録）と `data/` の中だけ。

## 動かす

```sh
# データを取り直してアプリ同梱分まで更新する
sh apps/job-hunt-board/refresh.sh

# ブラウザで見る
python3 apps/job-hunt-board/server.py
```

iOSアプリは `apps/job-hunt-board/mobile` で `npx expo run:ios`。
サーバーが動いていればアプリはそこから最新を読み、動いていなければ同梱の
`assets/feed.json` を使う。

## メールの接続について

いま Composio に繋がっているのは `subaru.ono1@gmail.com` だけ。届くのはナビサイトの
案内が中心で、企業からの本物の選考メールは `subaru.ono15@gmail.com` 側にある。
ono15 を足すには、そのアカウントでログインした状態で `composio link gmail` を実行する。
足すまでの間も、締切マスターの Markdown から作る部分は全部動く。

## メールの判定

`sync_gmail.py` は差出人だけで広告を弾く。ナビサイトのドメインと運営事務局の名前が
入っていれば捨てる。件名では判定しない。件名には「就活」「面接」のような普通の語が
入るので、そこを見ると企業のメールまで落ちてしまう。

`axol.jp` のような企業ATSのドメインは残す。住友商事の連絡がここから来る。

## マイページとログインID

`collect_mypages.py` は Chrome の閲覧履歴と「保存したログイン情報」から、各社の
マイページURLとログインIDを集めて `private/job-hunt/mypages.json` に書く。
パスワードは読まない。`Login Data` の `username_value` 列だけを見る。

- 会社名とURLは履歴のタイトルから作る。正式名が分かっているものは `OFFICIAL_NAMES` で上書きする
- ログインIDは保存ログイン情報から、その企業のログインURLに近い値を優先して選ぶ
- 会社をまたいで同じ値が出ているときは、専用の値がある方を優先する（取り違え対策）
- 手で直したいときは `private/job-hunt/mypages-manual.json` に書く。再収集しても残る

アプリでは「マイページ」タブに出る。行をタップするとマイページが開き、IDをタップすると
共有シートでコピーできる。`mypages.json` はログインIDを含むのでGitに載せない。
