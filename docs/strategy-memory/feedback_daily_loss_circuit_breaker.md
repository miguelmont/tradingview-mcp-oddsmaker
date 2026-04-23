---
name: Daily loss / consecutive-SL circuit breaker
description: After 3 consecutive stop-outs in a single trading day, STOP firing any new setups for the rest of that session. Even structurally clean 🎯 candidates are skipped. Resume normal sizing next day.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
Rule: if a single trading day registers **3 consecutive SL hits**, circuit-breaker activates and no additional setups are fired for that day (session close at 15:30 CT). Any remaining 🎯 emissions are logged-only (tagged "circuit_breaker_active"), no fire_setup.sh.

**Why:** on 2026-01-05 during Day 2 backtest, the playbook printed 4 S1/S2 SHORT setups in sequence (10:26, 10:43, 13:38, 13:58 NY). All 4 stopped out quickly in a chop range, cumulative -$1,093 vs $50,626 opening equity (2.2% DD). Fourth entry (size-reduced) still lost. The strategy was clearly not in its edge regime for that market structure. Continuing to fire identical setups after repeated failures is gambling, not systematic trading.

**Rationale:** consecutive SL hits on the same underlying structure type (e.g., repeated S2 SHORTs rejected off same level) indicate the market isn't in the setup's expected regime. The correct response is to stop and re-evaluate next session, not to chase with reduced size.

**How to apply:**
- Track consecutive-SL counter per day in trade log.
- After the 3rd consecutive SL on a given date, all new 🎯 emissions for that day get logged as "CIRCUIT_BREAKER_SKIP" without fire.
- Counter resets at next session open (08:30 CT next trading day).
- Can override manually if user explicitly requests "--override-circuit-breaker" — but default is strict.
