---
name: C-cap increased to 0.20% (from 0.10%)
description: Grade C (NEUTRAL HTF tiebreaker setups + 2-warning setups) now sized 0.20% equity instead of 0.10%. Otherwise NEUTRAL days cannot be sized at typical 50-80pt SL widths.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
User directive 2026-04-23: "aplica a 1 0.20% para setups C y corre recon live".

**Effective cap table:**
| Grade | Cap |
|---|---|
| A+ | 0.75% |
| A | 0.50% |
| B | 0.25% |
| **C** | **0.20%** (was 0.10%) |

**Reason**: backtest at $50k equity + 0.10% × 50,000 = $50 risk budget could not fit even 1 MNQ contract at typical S1/S2 SL widths (50-80pt = $100-160/contract). Result: NEUTRAL HTF days (common) produced 0 fires. Raising to 0.20% yields $100 budget → 1 contract is sizeable at ~50-80pt SL.

**How to apply:**
- When HTF is NEUTRAL 2-2 → Weekly VWAP tiebreaker → cap at Grade C = **0.20%** equity per trade.
- When setup has 2+ warnings → cap at Grade C = 0.20%.
- Still a full skip if risk budget can't fit ≥1 contract even at 0.20%.
- Strategy doc [docs/my-strategy.md](docs/my-strategy.md) grading table should be updated to reflect 0.20%.
