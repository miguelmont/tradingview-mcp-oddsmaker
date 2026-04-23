---
name: Trade exits model as limit orders on targets
description: Each target (T1/T2/T3) is a simulated limit order that fills the instant price touches it. Partial exits on multi-target trades. After T1, runner SL moves to BE.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
User directive 2026-04-22: "cerraste muy tarde el trade, hazlo con limit orders simuladas en los targets".

**Execution model (going forward, all backtest trades):**

1. **Targets are limit orders.** When intrabar high (long) / low (short) touches T1/T2/T3, that portion of the position fills **at the target price exactly**, on that bar. No lag, no wait-for-close.

2. **Partial exits by target count:**
   - T1 only (single-target mode) → 100% exit at T1.
   - T1 + T2 (two structural targets) → 50% at T1, 50% at T2.
   - T1 + T2 + T3 → 1/3 at each.

3. **Breakeven (BE) trail after T1.** The instant T1 fills, the SL on the remaining runner moves to entry price (BE). If price pulls back and touches BE after T1, runner exits at $0 P&L. No re-risk of the realized T1 gain.

4. **SL hit before any T.** All contracts exit at SL price. Full loss = risk_pts × $2 × contracts.

**Why:** Previous model reported "closed at SL" long after T1 was touched, which conflated monitor-naive SL events with the actual limit-order mechanics of a real trader. This is not realistic and understates edge.

**How to apply:**
- Per-trade P&L in backtest = sum of (fill_price - entry) × $2 × contracts per leg.
- `recon_batch.sh` monitor is informational only; authoritative P&L comes from this model.
- When writing to SQLite `trades` table: `t1_reached`, `t2_reached`, `t3_reached` booleans based on intrabar high/low touching; `pnl_final` reflects partial fills + BE-runner modeling.
- Trade 1 (2026-01-02 08:46 S1 LONG, 2 contracts, T1+T2 mode): T1 hit → 1 contract @ +$191; runner BE → 0; total **+$191**.
