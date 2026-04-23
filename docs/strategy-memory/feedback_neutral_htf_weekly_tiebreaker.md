---
name: NEUTRAL HTF — Weekly VWAP tiebreaker, Grade C setups only
description: When HTF bias is NEUTRAL (2-2 split), don't abstain. Use Weekly VWAP direction as the permitted trade direction. All setups in NEUTRAL are capped Grade C (0.10% equity or skip).
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
When HTF voting yields **NEUTRAL** (2-2 tie, typically Weekly/Monthly bullish vs CHoCH/Delta bearish or vice versa):

- Do NOT skip all setups.
- Use the **Weekly VWAP direction** as tiebreaker: `price > weekly` ⟹ only LONGs allowed; `price < weekly` ⟹ only SHORTs allowed.
- Every setup taken in NEUTRAL is **Grade C** (low-probability, cap 0.10% equity or skip per user discretion).
- Setups against the Weekly direction in NEUTRAL are skipped completely.
- All other structural rules (S1/S2/S3 checklists, sweep-in-band for S1, etc.) still apply.

**Why:** user clarified on 2026-04-22 that on Day 2 (2026-01-05) the HTF was Weekly+1, Monthly+1, CHoCH-1, Delta-1 = 2-2 NEUTRAL. The weekly was bullish so only LONG setups at Grade C should have been considered. My original code returned no candidates for NEUTRAL HTF, and a separate cache bug made me read HTF as BEARISH 0-4 causing wrong-direction SHORTs.

**How to apply (code):**
- In `evaluate_setup_candidate`, when `htf.bias == "NEUTRAL"`, derive `weekly_dir` from votes (bullish if weekly vote +1, bearish if -1, else skip).
- Allow candidates only if `trade_direction` matches `weekly_dir`.
- Force grade to **C** (override any A/A+/B caps).
- Default position size: **0.10%** equity for Grade C (or skip).
