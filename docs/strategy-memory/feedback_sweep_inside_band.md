---
name: Sweep-inside-band rule applies ONLY to Setup 1 (NY Continuation)
description: The requirement that sweep occur with LTF |SD|≤1.0 applies ONLY to Setup 1. Setups 2 and 3 (NY Reversal / Reversal) by definition activate on LTF overext, so sweep outside band is expected and required.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
**Scope** — the rule differs by setup:

- **Setup 1 (NY Continuation)**: sweep MUST occur with LTF |SD|≤1.0. If sweep bar was already overextended, the setup is invalid. No "slightly overext" inference at the sweep. Borderline tolerance (|SD|≤~1.2) applies ONLY at entry confirmation.
- **Setup 2 (NY Reversal / Reversal pro-HTF)**: sweep IS the overextended flush. `sweep_out_of_band` is EXPECTED, not a blocker. Premise: LTF overext opposite HTF + flush further out + reversal CHoCH in HTF direction → reversion toward mean.
- **Setup 3 (Reversal contra-HTF)**: similar to Setup 2 but contra-HTF; also premises on overextension. `sweep_out_of_band` expected.

**Why:** user rejected my correct-on-paper skip at 09:44 NY (CHoCH bull@26,726.25, δ+7.345K massive aligned, sweepσ -2.296 out of band, HTF BULL, LTF -1.17σ near-band at CHoCH bar, deeper at the flush). That was textbook Setup 2: HTF bullish + LTF overext bearish (opposite) + deep flush (sweep_out) + bullish CHoCH in HTF direction. Mean-reversion reversal. I skipped it mechanically because I applied the Setup-1 rule universally. The strategy's Setup 2 requires `LTF |SDs| > 1.0 IN OPPOSITE DIRECTION to HTF` and `TBL sweep in the same direction as the overextension` — which is exactly what makes `sweep_out_of_band` correct for S2.

**How to apply:**
- When bar_read.py emits `sweep_out_of_band`, FIRST ask: is this a Setup 2/3 context (LTF |SD|>1 + CHoCH in appropriate direction)? If yes, the warning is informative but NOT a blocker.
- Only for Setup 1 evaluation is `sweep_out_of_band` a hard skip.
- Mental decision tree:
  1. CHoCH direction + HTF direction + LTF band state → which setup is the candidate?
  2. Setup 1 → sweep MUST be in-band, else skip.
  3. Setup 2 → sweep_out_of_band is EXPECTED; proceed to other checks (delta, RR, NY).
  4. Setup 3 → same as S2 regarding overext.
