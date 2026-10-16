#!/bin/sh
# U-23スタッフ共有サイトを1コマンドで更新する。途中で失敗したら、そこで止まる。
#   取り込み（collect.py）→ 組み立て（build_site.py --out dist.new）→ 検査 →
#   dist を dist.prev に、dist.new を dist に入れ替え → 公開（deploy_site.sh）→ グループに貼る1行を表示
#
#   sh update_site.sh              全部流す
#   sh update_site.sh --no-deploy  入れ替えまでで止め、公開しない
#   sh update_site.sh --rollback   1つ前の版（dist.prev）と入れ替えて上げ直す。もう一度で元に戻る
#   sh update_site.sh --force      日程の試合数・ページ数・終了試合数が減っても止めない（意図して減らしたとき）。
#                                  終わった試合のボックススコアが404などで取れなくても、成績を入れずに進む
#
# 試すときだけ、次の環境変数で中身を差し替えられる。
#   U23_SITE_DIR  dist を置くフォルダ（既定 ~/野球/U23ワールドカップ2026/07_サイト）
#   U23_COLLECT   取り込みのコマンド（既定 python3 collect.py --event u23-wc-2026）
#   U23_BUILD     組み立てのコマンド。後ろに --out <フォルダ> が付く（既定 python3 build_site.py）
#   U23_DEPLOY    公開のコマンド。後ろに <フォルダ> が付く（既定 sh deploy_site.sh）
# zsh で流しても $COLLECT などを語に分けるよう sh のふるまいにする。emulate は set -e を戻すので先に置く
if [ -n "${ZSH_VERSION:-}" ]; then emulate sh; fi
set -e
cd "$(dirname "$0")"

SITE_DIR="${U23_SITE_DIR:-$HOME/野球/U23ワールドカップ2026/07_サイト}"
DIST="$SITE_DIR/dist"
NEW="$SITE_DIR/dist.new"
PREV="$SITE_DIR/dist.prev"
SWAP="$SITE_DIR/dist.swap"
COLLECT="${U23_COLLECT:-python3 collect.py --event u23-wc-2026}"
BUILD="${U23_BUILD:-python3 build_site.py}"
DEPLOY="${U23_DEPLOY:-sh deploy_site.sh}"

PUBLISH=1
ROLLBACK=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --no-deploy) PUBLISH=0 ;;
    --rollback) ROLLBACK=1 ;;
    --force) FORCE=1 ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "知らない指定です: $arg（--no-deploy / --rollback / --force）" >&2; exit 2 ;;
  esac
done

# --force のときは、取り込みでも日程の試合が減ったのと、終わった試合が取れないのを通す（既定の取り込みのときだけ）
if [ "$FORCE" = 1 ] && [ -z "${U23_COLLECT:-}" ]; then COLLECT="$COLLECT --allow-fewer --skip-missing"; fi

STEP="準備"
SWAPPED=0  # 入れ替え・戻すの進み具合。1 = dist を脇へ動かした、2 = 新しい dist を置き終えた

folders() {  # いま実際にあるフォルダを並べる（止まったときの案内用）
  found=""
  for name in dist dist.prev dist.new dist.swap; do
    if [ -d "$SITE_DIR/$name" ]; then found="$found $name"; fi
  done
  echo "いまあるフォルダ:${found:- なし}（場所 $SITE_DIR）" >&2
}

undo_swap() {  # 入れ替えの途中で止まったら、脇へ動かした前の版を dist に戻す
  if [ "$SWAPPED" = 1 ] && [ ! -d "$DIST" ] && [ -d "$PREV" ]; then
    if mv "$PREV" "$DIST"; then
      echo "新しい版を dist に置けなかったので、前の版を dist に戻しました。手元の dist と公開中のサイトは前のままです。組み立てた版は dist.new に残っています。" >&2
    else
      echo "dist がない状態です。前の版は dist.prev、組み立てた版は dist.new にあります。どちらかの名前を dist に変えてください。" >&2
    fi
  elif [ "$SWAPPED" = 2 ]; then
    echo "手元の dist は新しい版に入れ替わっています。公開はまだです。上げるときは: sh deploy_site.sh" >&2
  elif [ -d "$DIST" ]; then
    echo "手元の dist はそのままです（公開中のサイトも変わっていません）。組み立てた版は dist.new に残っています。" >&2
  else
    echo "dist がありません。下のフォルダの中身を確かめてください。" >&2
  fi
  folders
}

undo_rollback() {  # 戻すの途中で止まったら、元の dist に戻す
  if [ "$SWAPPED" = 1 ] && [ ! -d "$DIST" ] && [ -d "$SWAP" ]; then
    if mv "$SWAP" "$DIST"; then
      echo "1つ前の版を dist に置けなかったので、元の版を dist に戻しました。何も変わっていません。" >&2
    else
      echo "dist がない状態です。元の版は dist.swap、1つ前の版は dist.prev にあります。どちらかの名前を dist に変えてください。" >&2
    fi
  elif [ "$SWAPPED" = 2 ] && [ -d "$SWAP" ] && [ ! -d "$PREV" ]; then
    echo "dist は1つ前の版に戻っています。元の版は dist.prev ではなく dist.swap に残っています。公開はまだです。" >&2
  elif [ -d "$DIST" ]; then
    echo "手元の dist はそのままです（公開中のサイトも変わっていません）。" >&2
  else
    echo "dist がありません。下のフォルダの中身を確かめてください。" >&2
  fi
  folders
}

finish() {
  code=$?
  trap - EXIT INT TERM HUP
  [ "$code" -eq 0 ] && return 0
  echo "" >&2
  echo "止まりました（${STEP}の段）。" >&2
  case "$STEP" in
    検査) echo "公開中のサイトと手元の dist はそのままです。組み立てた版は dist.new に残っています。" >&2 ;;
    入れ替え) undo_swap ;;
    戻す) undo_rollback ;;
    公開) echo "手元の dist は入れ替わっていますが、公開中のサイトはまだ前のままです。電波のある所で sh deploy_site.sh を流し直してください。" >&2 ;;
    *) echo "公開中のサイトと手元の dist はそのままです。" >&2 ;;
  esac
  return "$code"
}
# 途中で失敗したとき（set -e）も、Ctrl-C などで止めたときも、finish を通ってから終わる
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

discard() {  # 消すときはゴミ箱へ（rm は使わない）
  [ -e "$1" ] || return 0
  if [ -x /usr/bin/trash ]; then
    /usr/bin/trash "$1"
  else
    mv "$1" "$HOME/.Trash/$(basename "$1")-$(date +%Y%m%d%H%M%S)"
  fi
}

look() {  # dist の pages.json と status.js を読む。count は「ページ数 終了試合数 全試合数 合言葉のフォルダ」、line は貼る1行
  python3 - "$1" "$2" <<'PY'
import json, sys
from datetime import datetime, timedelta
from pathlib import Path

dist, what = Path(sys.argv[1]), sys.argv[2]
found = [p.parent for p in dist.glob("*/pages.json") if (p.parent / "status.js").exists()]
if len(found) != 1:
    print("- - - -" if what == "count" else "")
    sys.exit(0)
site = found[0]
text = (site / "status.js").read_text(encoding="utf-8")
status = json.loads(text[text.index("{"):text.rindex("}") + 1])
if what == "count":
    pages = json.loads((site / "pages.json").read_text(encoding="utf-8"))
    print(len(pages), status.get("finals", 0), status.get("games", 0), site.name)
    sys.exit(0)
jst = datetime.strptime(status["updated"], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=9)
last = status.get("last_final")
if not last:
    tail = "試合結果はまだありません。"
else:
    day = f'現地{int(last["date"][5:7])}/{int(last["date"][8:10])}'
    if last["day_finals"] >= last["day_games"]:
        tail = f'{day}の{last["day_games"]}試合の結果まで入っています。'
    else:
        tail = f'{day}は{last["day_games"]}試合中{last["day_finals"]}試合の結果まで入っています。'
print(f"U-23サイトを更新しました（日本時間 {jst.month}/{jst.day} {jst:%H:%M}）。{tail}")
PY
}

publish() {
  if [ "$PUBLISH" = 1 ]; then
    STEP="公開"
    started=$(date +%s)
    $DEPLOY "$DIST"
    echo "公開: $(( $(date +%s) - started ))秒"
  else
    echo "公開はしていません（--no-deploy）。上げるときは: sh deploy_site.sh"
  fi
}

# ---------------------------------------------------------------- 1つ前の版に戻す

if [ "$ROLLBACK" = 1 ]; then
  STEP="戻す"
  if [ ! -d "$PREV" ]; then
    echo "dist.prev がないので戻せません。" >&2
    exit 1
  fi
  discard "$SWAP"
  if [ -d "$DIST" ]; then mv "$DIST" "$SWAP"; SWAPPED=1; fi
  mv "$PREV" "$DIST"
  SWAPPED=2
  if [ -d "$SWAP" ]; then mv "$SWAP" "$PREV"; fi
  SWAPPED=3
  echo "1つ前の版に戻しました（もう一度 --rollback を付けると元に戻ります）。"
  echo "戻した版: $(look "$DIST" line)"
  publish
  exit 0
fi

# ---------------------------------------------------------------- 取り込み → 組み立て

STEP="取り込み"
t0=$(date +%s)
$COLLECT

STEP="組み立て"
t1=$(date +%s)
discard "$NEW"
$BUILD --out "$NEW"
t2=$(date +%s)

# ---------------------------------------------------------------- 検査

STEP="検査"
read -r NEW_PAGES NEW_FINALS NEW_GAMES NEW_SITE <<EOF
$(look "$NEW" count)
EOF
if [ -z "$NEW_PAGES" ] || [ "$NEW_PAGES" = "-" ]; then
  echo "dist.new に pages.json と status.js がそろっていません（合言葉のフォルダが1つでない可能性もあります）。" >&2
  exit 1
fi
if [ "$NEW_GAMES" -eq 0 ]; then
  echo "日程の試合が0件です。空の日程を公開しないよう止めました。取り込みを確かめてください。" >&2
  exit 1
fi
if ! grep -q "日本戦" "$NEW/$NEW_SITE/index.html"; then
  echo "トップに「日本戦」がありません。組み立てに失敗している可能性があります。" >&2
  exit 1
fi
read -r OLD_PAGES OLD_FINALS OLD_GAMES OLD_SITE <<EOF
$(look "$DIST" count)
EOF
if [ -z "$OLD_PAGES" ] || [ "$OLD_PAGES" = "-" ]; then
  echo "今の dist に pages.json がないので、前回との数の比べは飛ばします。"
  OLD_PAGES=0
  OLD_FINALS=0
elif [ "$FORCE" = 0 ]; then
  if [ "$NEW_GAMES" -lt "$OLD_GAMES" ]; then
    echo "日程の試合数が減りました（${OLD_GAMES} → ${NEW_GAMES}）。取り込みを確かめてください。意図したものなら --force を付けて流し直してください。" >&2
    exit 1
  fi
  if [ "$NEW_PAGES" -lt "$OLD_PAGES" ]; then
    echo "ページ数が減りました（${OLD_PAGES} → ${NEW_PAGES}）。意図したものなら --force を付けて流し直してください。" >&2
    exit 1
  fi
  if [ "$NEW_FINALS" -lt "$OLD_FINALS" ]; then
    echo "終わった試合の数が減りました（${OLD_FINALS} → ${NEW_FINALS}）。取り込みを確かめてください。" >&2
    exit 1
  fi
fi
echo "検査OK: ページ ${NEW_PAGES}（前回 ${OLD_PAGES}）・試合 ${NEW_GAMES}・終了試合 ${NEW_FINALS}（新しく $((NEW_FINALS - OLD_FINALS))）"

# ---------------------------------------------------------------- 入れ替え → 公開

STEP="入れ替え"
if [ -d "$DIST" ]; then
  discard "$PREV"
  mv "$DIST" "$PREV"
  SWAPPED=1
fi
mv "$NEW" "$DIST"
SWAPPED=2
echo "取り込み $((t1 - t0))秒・組み立て $((t2 - t1))秒"
publish

echo ""
if [ "$PUBLISH" = 1 ]; then
  echo "グループに貼る1行:"
else
  echo "公開したら、グループに次の1行を貼ってください:"
fi
look "$DIST" line
