#!/bin/sh
# U-23スタッフ共有サイトを Cloudflare Pages に上げる。build_site.py の後に動かす。
# プロジェクト名はリポジトリに入らない private/u23-site-project にある。
cd "$(dirname "$0")/../.." || exit 1
wrangler pages deploy "$HOME/野球/U23ワールドカップ2026/07_サイト/dist" \
  --project-name "$(cat private/u23-site-project)" --branch main --commit-dirty=true
