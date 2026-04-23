---
name: Auto-skip setups with massive contradicting delta
description: During Recon Live/Backtesting, if a CHoCH prints with delta contradicting the implied trade direction AND |delta| ≥ 2K, skip immediately — do NOT pause the Monitor for a full analysis.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
If a Recon tick surfaces a CHoCH where `delta_contradicting_choch` warning is present AND `|delta_value| ≥ 2000`, skip the setup immediately without stopping the Monitor or writing full analysis. Emit a one-line "skip: massive contra-delta" and keep iterating.

**Why:** on 2026-04-22 a replay tick at 09:42 showed CHoCH bull@26820.25 δ-6.165K (LONG with -6.165K = massive contradicting). I stopped the Monitor to do full setup validation. During the ~20 seconds of analysis, the Monitor backlog piled up past a CLEAN Setup 1 at 10:00 (CHoCH bull@26836 δ+2.993K aligned, LTF +1.10σ within borderline). The clean setup's entry window escaped to +1.65σ before I saw it. The contradicting-delta setup I was analyzing would have been Grade B at best with degraded Kelly — not worth sacrificing a Grade A/B cleaner one.

**How to apply:**
- When bar_read.py summary shows `warn=[...delta_contradicting_choch...]` and `|delta_value| ≥ 2000`, respond with a single short line "skip: massive contra-delta" and move on.
- The full stop-and-analyze path is reserved for setups with aligned or neutral delta (i.e., where the delta is quality-confirming or at worst neutral).
- Threshold is 2K based on strategy doc's "|delta| ≥ 2K = massive institutional conviction" language. Below 2K contradictions still degrade grade but are not auto-skips — they get normal analysis with grade cap applied.
- This is my operational heuristic to protect attention budget; the underlying strategy rule (contradicting delta degrades grade) is unchanged.
