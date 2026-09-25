#!/bin/sh
# データを取り直して、アプリ同梱用の feed.json まで更新する。
# 使い方: sh apps/job-hunt-board/refresh.sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR/../.."
echo "1/4 メールから就活シグナルを取り込む"
python3 apps/job-hunt-board/sync_gmail.py --days 45 --limit 60
echo "2/4 締切マスターとメールを1つにまとめる"
python3 apps/job-hunt-board/build_feed.py
echo "3/4 各社マイページとIDを集める"
python3 apps/job-hunt-board/collect_mypages.py
echo "4/4 アプリに同梱するデータを更新する"
cp apps/job-hunt-board/data/feed.json apps/job-hunt-board/mobile/assets/feed.json
cp private/job-hunt/mypages.json apps/job-hunt-board/data/mypages.json
cp private/job-hunt/mypages.json apps/job-hunt-board/mobile/assets/mypages.json
echo "完了"
