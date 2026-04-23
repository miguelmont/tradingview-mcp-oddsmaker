---
name: SL floor needed — 0.5pt margin not surviving CHoCH retest
description: Strategy's 2-tick (0.5pt) margin on CHoCH circle is repeatedly wicked out on retest. Valid S1 setups with strict spec compliance still stop out within 1-17 min. Need minimum SL floor.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
Observed across n=12 original backtest + 1 manually-verified valid S1 trade (2026-01-16 12:59 CT re-run):

**Pattern**: CHoCH circle acts as a magnet. Price validates the CHoCH, pulls to entry region, then reliably wicks 1-3pt past the circle before resuming direction. A 0.5pt (2-tick) margin above/below circle does not survive this re-test in any of the 10 tight-stop trades observed.

**Evidence (manual re-run 2026-01-16)**:
- Strict S1 SHORT: HTF BEARISH 1-3 aligned, LTF IN_BAND −0.29σ, CHoCH bear@25941.5, δ −2.965K aligned, sweep in band, post-lunch, all conditions met.
- SL at 25942.0 (circle + 0.5pt). Entry 25932. Risk 10pt.
- **Bar high at 13:04 CT (5 min post-fire): 25943.75** = 2.25pt above SL.
- Price did eventually continue down but only after sweeping the SL.

**Evidence (prior backtest)**:
- 9/9 losing trades hit SL within 1–17 minutes of entry.
- Trade 5 (Day 6): SL hit 2min post fire, price closed +151pt in the trade direction afterward.
- Trade 8 (Day 10): 5.25pt stop wicked out in 1 bar.

**How to apply**:
- Do NOT fire S1 setups where the structural SL (circle + 2 ticks) gives less than ~10-15 pts total risk.
- Proposed rule: **minimum SL distance = max(10pt, 1× ATR(14) on 1m)**.
- If the CHoCH-circle-based SL is too tight, either (a) widen to structural swing high/low BEYOND the circle, or (b) skip the setup.
- This caps Kelly-implied position size at realistic levels and eliminates the "wick-out" failure mode.

**Strategy doc update needed**: [docs/my-strategy.md](docs/my-strategy.md) Setup 1/2 STOP rules should add: "SL distance minimum 10 pts. If circle+2ticks < 10pt, use the next structural swing beyond the circle, OR pass on the setup."
