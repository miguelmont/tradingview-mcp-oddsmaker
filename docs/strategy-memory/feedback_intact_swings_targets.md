---
name: Targets must be INTACT swings, confluence with Time Cycles boxes / LuxAlgo sessions / PDH-PDL
description: T1/T2/T3 must be structural swing highs (LONG) or lows (SHORT) that have NOT been liquidated by past price action. Prefer levels that coincide with Time Cycles 10/30/90-min box highs/lows, LuxAlgo session highs/lows, PDH/PDL/PWH/PWL, etc. Adequate spacing between targets — no bunching.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
When selecting T1/T2/T3 for a Setup fire:

1. **Intact swings only.** A past BB bearish CHoCH circle is only a valid LONG target if price has NOT exceeded it since it printed (i.e., the high hasn't been "liquidated"). Same logic mirrored for SHORT targets (past bullish CHoCH circles not broken below).
2. **Confluence strongly preferred.** Pick levels that align with multiple structural sources: Time Cycles box high/low (10/30/90 min), LuxAlgo Session High/Low markers, PDH/PDL/PWH/PWL, BB past CHoCH. Confluence > single source.
3. **Adequate spacing.** T1→T2→T3 must be meaningfully separated. Don't put T1 at 26,832.5 and T2 at 26,838 — that's 5.5 pts, noise, redundant. Each step should be a new structural regime.
4. **No forced T3.** If no good higher structural target exists, reduce to T1/T2 or set T3 at a real confluence (even if far).

**Why:** on 2026-04-22 during replay of 2026-04-21 I fired S2 LONG with T1=26,832.5 and T2=26,838 stacked 5.5 pts apart — redundant, not how a real trader would set targets. User corrected with their own chart adjustment showing T2/T3 spread across intact bearish CHoCH circles that coincide with box/session highs.

**How to apply:**
- Before calling fire_setup.sh, enumerate structural lines above (LONG) or below (SHORT) entry.
- Cross-reference each with Time Cycles boxes (`tv data boxes --filter Cycles`) — prefer levels that match box extremes.
- Cross-reference with Sessions labels (`tv data labels --filter Sessions`) — prefer levels near recent session highs/lows.
- Skip levels known to be "liquidated" (exceeded by subsequent price action since they printed). When in doubt, read OHLCV from CHoCH-print bar onward and check max(high) against the circle price.
- Ensure T1→T2 and T2→T3 gaps are ≥20 pts on NQ/MNQ 1m, ideally more.
