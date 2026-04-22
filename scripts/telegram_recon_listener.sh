#!/bin/bash
# Polls Telegram for Recon commands and emits one stdout line per match.
# Only messages from TELEGRAM_CHAT_ID are considered.
# Matches (case-insensitive): "recon backtesting", "recon live",
# "/recon_backtesting", "/recon_live".

set -u
cd "$(dirname "$0")/.."
set -a
# shellcheck disable=SC1091
source .env
set +a

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
  echo "ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing in .env" >&2
  exit 1
fi

offset_file="/tmp/tv_recon_offset_${TELEGRAM_CHAT_ID}.txt"

# Prime offset to skip historical messages on first run.
if [ ! -f "$offset_file" ]; then
  latest=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates" \
    | python3 -c "import json,sys
try:
    d=json.load(sys.stdin); r=d.get('result',[])
    print(r[-1]['update_id'] if r else 0)
except Exception:
    print(0)")
  echo "$((latest + 1))" > "$offset_file"
fi

echo "[listener] ready · chat_id=${TELEGRAM_CHAT_ID} · offset=$(cat "$offset_file")" >&2

while true; do
  offset=$(cat "$offset_file")
  resp=$(curl -s --max-time 35 \
    "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates?offset=${offset}&timeout=30" \
    2>/dev/null || true)

  # Write events to stdout, next-offset to $offset_file via python.
  printf '%s' "$resp" | TARGET_CHAT="$TELEGRAM_CHAT_ID" OFFSET_FILE="$offset_file" \
    python3 "$(dirname "$0")/telegram_recon_parse.py"

  sleep 1
done
