---
name: Recon Backtesting — manual step, not background Monitor loop
description: Backtesting must advance one bar at a time via manual `bash scripts/recon_tick.sh` calls in my own tool runs. NO persistent Monitor that auto-steps and has to be stopped.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
In Recon Backtesting, **I step manually, one tick at a time**, via my own Bash tool calls. Do NOT start a persistent Monitor that loops with `sleep 1` in the background.

**Why:** on 2026-04-22 the auto-Monitor caused a backlog of "next bar" presses that advanced the replay past setup windows while I was analyzing. User corrected: "debes hacerlo presionando tu manualmente next bar cada segundo, no debes dejarlo correr por si solo y detenerlo" — must press manually each second, not let it run alone and stop it.

**How to apply:**
- To advance: run `bash scripts/recon_tick.sh` — this is step + read + summary in ONE shell call.
- Run it in a small batch (e.g. 5-10 iterations via `for i in $(seq 1 10); do bash scripts/recon_tick.sh; done`) if the user wants multi-bar coverage per turn. Scan the batch output for `🎯` candidate tags.
- When a `🎯` candidate appears, simply stop calling `recon_tick.sh`. No kill needed — replay stays frozen at that bar.
- Analyze JSON → fire_setup.sh dry-run → fire. Then user decides to resume.
- Recon LIVE may still use a Monitor because bars arrive on wallclock (60s); backtesting shouldn't.
