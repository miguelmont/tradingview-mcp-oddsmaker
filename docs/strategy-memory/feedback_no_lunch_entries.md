---
name: No entries 11:00–13:00 NY (lunch hour chop filter)
description: Even structurally valid setups must be skipped if the CHoCH/entry bar falls within 11:00–13:00 NY time. Institutional volume thins, chop dominates, sweep fakeouts are common.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
Block all setup entries when the entry bar's NY time is between **11:00 and 13:00** (inclusive of 11:00, inclusive of 13:00). Implement as a hard filter in `evaluate_setup_candidate` — emits `⚠` with `SKIP[lunch_hour_11_13_NY]` reason so the user still sees the would-be candidate but no fire.

**Why:** user directive on 2026-04-22 after observing 2 S2 LONG setups fail (structurally clean, stopped out) on 2026-01-02 at 11:11 NY and 11:15 NY. Both got chopped in the 11:00-14:00 NY midday range. Institutional flow thins between US cash lunch (noon ET) and afternoon resume. Liquidity sweeps are more likely to be false pick-offs rather than reversal triggers in this window.

**How to apply:**
- Convert the bar timestamp to NY time and check hour ∈ [11, 13]. If yes, add `lunch_hour_11_13_NY` to rejected_reasons.
- Filter applies to ALL setup types (S1, S2, S3).
- Even if all other structural checks pass and RR≥1, the lunch filter is terminal (⚠, not 🎯).
