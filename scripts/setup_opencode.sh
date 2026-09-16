#!/bin/bash
# opencode Go を Codex から使えるようにする。キーは画面に表示されない。
set -u
ENV_FILE="$HOME/AI-OS/.env"
printf "opencode の API キーを貼り付けて Enter（画面には出ません）: "
stty -echo; read -r KEY; stty echo; echo

if [ -z "$KEY" ]; then echo "キーが空でした。もう一度実行してください。"; exit 1; fi

touch "$ENV_FILE"; chmod 600 "$ENV_FILE"
grep -v '^OPENCODE_API_KEY=' "$ENV_FILE" > "$ENV_FILE.tmp" 2>/dev/null || true
mv "$ENV_FILE.tmp" "$ENV_FILE"
printf 'OPENCODE_API_KEY=%s\n' "$KEY" >> "$ENV_FILE"
echo "1/3 キーを保存しました: ~/AI-OS/.env"

LINE='export OPENCODE_API_KEY=$(grep -m1 "^OPENCODE_API_KEY=" ~/AI-OS/.env | cut -d= -f2-)'
grep -qF "$LINE" "$HOME/.zshrc" 2>/dev/null || echo "$LINE" >> "$HOME/.zshrc"
echo "2/3 ターミナルでキーを読み込む設定を追加しました"

CODE=$(curl -s -m 30 -o /dev/null -w '%{http_code}' https://opencode.ai/zen/go/v1/responses \
  -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -d '{"model":"kimi-k2.7-code","input":"hi","max_output_tokens":16}')
case "$CODE" in
  200) echo "3/3 接続できました。新しいターミナルを開いて  codex --profile oc  で使えます。" ;;
  401|403) echo "3/3 キーが受け付けられませんでした（$CODE）。キーをもう一度確認してください。" ;;
  *) echo "3/3 応答コード $CODE。Claude に伝えてください。" ;;
esac
