---
name: Setup 3 (Reversal contra-HTF) disabled for now
description: Do not detect or fire S3_REVERSAL_CONTRA. Only S1_CONTINUATION and S2_REVERSAL_PRO are active. S3 may be re-enabled later after collecting more data.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
User directive on 2026-04-22: exclude Setup 3 (contra-HTF reversal) from all detection, scanning, and firing. The low-edge nature of contra-HTF trades combined with early backtest evidence (multiple S3 LONG setups stopping out in bearish momentum) makes the cost-benefit unclear at this sample size.

**Active setups**: S1_CONTINUATION, S2_REVERSAL_PRO only.

**S3 test in replay 2026-01-05 run 2**: S3 LONG fired twice against BEARISH HTF momentum (entries 25,566.5 and 25,562, both Grade B), both stopped out within minutes for -$160 combined while price continued bearish. The structural signal (bullish CHoCH + LTF bearish-overext in bearish HTF) correctly activated S3 CONTRA per strategy, but direction bet against clear momentum produced losers.

**How to apply:**
- In `evaluate_setup_candidate`, the S3 branch is commented out.
- If a pattern structurally matches S3 (LTF overext same-dir as HTF + CHoCH contra-HTF), emit nothing (not even ⚠).
- Re-enable only after collecting explicit user directive AND n≥30 S2 trades to establish baseline edge.
