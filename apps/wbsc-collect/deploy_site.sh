#!/bin/sh
# U-23スタッフ共有サイトを Cloudflare Pages に上げる。build_site.py の後に動かす。
# ふだんは update_site.sh から呼ばれる。プロジェクト名はリポジトリに入らない private/u23-site-project にある。
#
#   sh deploy_site.sh             # 今の dist を上げる
#   sh deploy_site.sh <フォルダ>   # 指定したフォルダを上げる
DIR="${1:-$HOME/野球/U23ワールドカップ2026/07_サイト/dist}"
if [ ! -d "$DIR" ]; then
  echo "公開するフォルダがありません: $DIR" >&2
  exit 1
fi
DIR=$(cd "$DIR" && pwd)  # 下で場所を移るので、先に絶対パスにしておく
cd "$(dirname "$0")/../.." || exit 1
if [ ! -f private/u23-site-project ]; then
  echo "private/u23-site-project がありません。プロジェクト名をそこに書いてください。" >&2
  exit 1
fi
wrangler pages deploy "$DIR" \
  --project-name "$(cat private/u23-site-project)" --branch main --commit-dirty=true
