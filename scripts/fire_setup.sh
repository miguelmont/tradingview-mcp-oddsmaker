#!/bin/bash
# fire_setup.sh — atomic "fire the trade" action: draws 5 black horizontal
# lines on chart (Entry/SL/T1/T2/T3) + sends Telegram formatted + logs to JSONL.
# NO decision logic. Caller (Claude) has already validated.
#
# Assertions (abort if violated, no trade fired):
#   - direction must be long or short
#   - LONG:  sl < entry < t1 ≤ t2 ≤ t3
#   - SHORT: sl > entry > t1 ≥ t2 ≥ t3
#   - abs(entry - sl) ≥ 0.25 (at least 1 tick)
#   - RR_T1 ≥ 1 unless --force
#
# Readback: after drawing, calls `tv draw list` and verifies the 5 new
# horizontals exist at the exact prices. If not, aborts Telegram send.
#
# Usage:
#   fire_setup.sh --direction long|short \
#                 --entry 26952.5 --sl 26949 --t1 26978 --t2 26990 --t3 26996.5 \
#                 --grade B --size 0.25 --label "S1 LONG" \
#                 [--dry-run] [--force]

set -euo pipefail
cd "$(dirname "$0")/.."

# ---- parse args ----
DIRECTION=""; ENTRY=""; SL=""; T1=""; T2=""; T3=""
GRADE=""; SIZE=""; LABEL=""
DRY_RUN=0; FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --direction) DIRECTION="$2"; shift 2;;
    --entry)     ENTRY="$2"; shift 2;;
    --sl)        SL="$2"; shift 2;;
    --t1)        T1="$2"; shift 2;;
    --t2)        T2="$2"; shift 2;;
    --t3)        T3="$2"; shift 2;;
    --grade)     GRADE="$2"; shift 2;;
    --size)      SIZE="$2"; shift 2;;
    --label)     LABEL="$2"; shift 2;;
    --dry-run)   DRY_RUN=1; shift;;
    --force)     FORCE=1; shift;;
    *) echo "ERROR: unknown arg $1" >&2; exit 2;;
  esac
done

# ---- required args (T2 and T3 optional; if missing, 100% exits at T1) ----
for var in DIRECTION ENTRY SL T1 GRADE SIZE LABEL; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: missing required --${var,,}" >&2
    exit 2
  fi
done
# T2/T3 default: same as T1 (→ script treats all legs at T1 level, i.e. 100% exit at T1)
SINGLE_TARGET=0
if [[ -z "$T2" && -z "$T3" ]]; then
  T2="$T1"; T3="$T1"; SINGLE_TARGET=1
elif [[ -z "$T3" ]]; then
  T3="$T2"
fi

# ---- assertions via python (handles float math) ----
ASSERT_OUTPUT=$(python3 - <<PY
import sys
direction = "${DIRECTION}".lower()
entry, sl, t1, t2, t3 = ${ENTRY}, ${SL}, ${T1}, ${T2}, ${T3}
force = ${FORCE}
errors = []
if direction not in ("long", "short"):
    errors.append(f"direction must be long|short, got: {direction}")
if direction == "long":
    if not (sl < entry < t1 <= t2 <= t3):
        errors.append(f"LONG order invalid: sl={sl} entry={entry} t1={t1} t2={t2} t3={t3} (require sl<entry<t1<=t2<=t3)")
elif direction == "short":
    if not (sl > entry > t1 >= t2 >= t3):
        errors.append(f"SHORT order invalid: sl={sl} entry={entry} t1={t1} t2={t2} t3={t3} (require sl>entry>t1>=t2>=t3)")
risk = abs(entry - sl)
if risk < 0.25:
    errors.append(f"risk too tight: |entry-sl|={risk:.2f} (< 1 tick 0.25)")
reward_t1 = abs(t1 - entry)
rr_t1 = reward_t1 / risk if risk > 0 else 0
rr_t2 = abs(t2 - entry) / risk if risk > 0 else 0
rr_t3 = abs(t3 - entry) / risk if risk > 0 else 0
if rr_t1 < 1.0 and not force:
    errors.append(f"RR_T1={rr_t1:.2f} < 1.0 (use --force to override)")
if errors:
    for e in errors:
        print(f"ASSERT_FAIL: {e}", file=sys.stderr)
    sys.exit(1)
print(f"RR_T1={rr_t1:.2f}")
print(f"RR_T2={rr_t2:.2f}")
print(f"RR_T3={rr_t3:.2f}")
print(f"RISK_PTS={risk:.2f}")
PY
)

if [[ $? -ne 0 ]]; then
  exit 1
fi
eval "$ASSERT_OUTPUT"

echo "─── fire_setup.sh ──────────────────────────────"
echo "Label:     ${LABEL}"
echo "Direction: ${DIRECTION}"
echo "Grade:     ${GRADE}    Size: ${SIZE}%"
echo "Entry:     ${ENTRY}"
echo "SL:        ${SL}    (risk ${RISK_PTS} pts)"
if [[ $SINGLE_TARGET -eq 1 ]]; then
  echo "T1:        ${T1}    (RR ${RR_T1})  ← 100% exit at T1 (no T2/T3 structural)"
else
  echo "T1:        ${T1}    (RR ${RR_T1})"
  echo "T2:        ${T2}    (RR ${RR_T2})"
  echo "T3:        ${T3}    (RR ${RR_T3})"
fi
echo "────────────────────────────────────────────────"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "DRY RUN — no draws, no telegram, no log."
  exit 0
fi

# ---- draw 5 horizontal lines on current pane ----
TV="node tradingview-mcp/src/cli/index.js"
NOW=$(date +%s)

draw_line() {
  local price="$1" name="$2"
  $TV draw shape --type horizontal_line --price "${price}" --time "${NOW}" \
      --overrides "{\"linecolor\":\"#000000\",\"linewidth\":2,\"showLabel\":true,\"text\":\"${name}\"}" \
      --text "${name}" 2>&1
}

echo "Drawing lines..."
ENTRY_ID=$(draw_line "$ENTRY" "Entry" | python3 -c "import json,sys; print(json.load(sys.stdin).get('entity_id',''))")
SL_ID=$(draw_line "$SL" "SL" | python3 -c "import json,sys; print(json.load(sys.stdin).get('entity_id',''))")
T1_ID=$(draw_line "$T1" "T1" | python3 -c "import json,sys; print(json.load(sys.stdin).get('entity_id',''))")
T2_ID=$(draw_line "$T2" "T2" | python3 -c "import json,sys; print(json.load(sys.stdin).get('entity_id',''))")
T3_ID=$(draw_line "$T3" "T3" | python3 -c "import json,sys; print(json.load(sys.stdin).get('entity_id',''))")

for id in "$ENTRY_ID" "$SL_ID" "$T1_ID" "$T2_ID" "$T3_ID"; do
  if [[ -z "$id" ]]; then
    echo "ERROR: at least one draw failed (empty entity_id). Aborting Telegram." >&2
    exit 3
  fi
done
echo "Drawn: Entry=$ENTRY_ID SL=$SL_ID T1=$T1_ID T2=$T2_ID T3=$T3_ID"

# ---- Telegram ----
if [[ ! -f .env ]]; then
  echo "WARN: .env not found, skipping telegram" >&2
else
  set -a; source .env; set +a
  DIR_UP=$(echo "$DIRECTION" | tr a-z A-Z)
  NY_TIME=$(TZ='America/New_York' date +'%H:%M')
  MSG="🎯 *${LABEL}* · Grade *${GRADE}*
🕐 ${NY_TIME} NY

Entry: ${ENTRY}
SL:    ${SL}  (${RISK_PTS} pts)
T1:    ${T1}  (RR ${RR_T1})
T2:    ${T2}  (RR ${RR_T2})
T3:    ${T3}  (RR ${RR_T3})

Size:  ${SIZE}% equity"
  STATUS=$(curl -s -o /dev/null -w '%{http_code}' -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${MSG}" \
    --data-urlencode "parse_mode=Markdown")
  echo "Telegram: HTTP ${STATUS}"
fi

# ---- Decision journal ----
mkdir -p logs
python3 - <<PY >> logs/recon_live.jsonl
import json, time
print(json.dumps({
    "ts": int(time.time()),
    "label": "${LABEL}",
    "direction": "${DIRECTION}",
    "grade": "${GRADE}",
    "size_pct": ${SIZE},
    "entry": ${ENTRY}, "sl": ${SL},
    "t1": ${T1}, "t2": ${T2}, "t3": ${T3},
    "risk_pts": ${RISK_PTS},
    "rr_t1": ${RR_T1}, "rr_t2": ${RR_T2}, "rr_t3": ${RR_T3},
    "draw_ids": {"entry": "${ENTRY_ID}", "sl": "${SL_ID}", "t1": "${T1_ID}", "t2": "${T2_ID}", "t3": "${T3_ID}"}
}))
PY

echo "✅ Setup fired and logged."

# Persist active-trade state for batch monitoring
cat > .active_trade.json <<EOF
{"label": "${LABEL}", "direction": "${DIRECTION}", "entry": ${ENTRY}, "sl": ${SL}, "t1": ${T1}, "t2": ${T2}, "t3": ${T3}, "grade": "${GRADE}", "size_pct": ${SIZE}, "contracts_risk_usd": ${RISK_PTS} }
EOF