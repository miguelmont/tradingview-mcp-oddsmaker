---
name: On setup candidate, kill ticks immediately — replay must stop advancing
description: When bar_read.py summary shows a 🎯 SETUP_CANDIDATE tag, instantly run `pkill -f recon_tick.sh` before any analysis. TaskStop alone has delay; pkill is authoritative.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
The moment the Monitor summary line contains a `🎯` setup candidate tag (e.g. `🎯S2_REVERSAL_PRO LONG entry=... rr_t1=... δ✓`), the very first action MUST be `pkill -f recon_tick.sh`. This hard-kills the bash loop so the replay stops advancing through bars while I analyze.

**Why:** user noted on 2026-04-22 that when I called TaskStop on the Monitor, the replay kept pressing "next bar" in the backlog. Between TaskStop and the tick actually dying, ~15 bars advanced and the entry window escaped. TaskStop is advisory-async; pkill is immediate.

Second rule: **analysis of an emitted candidate must finish in <1 min**. The candidate tag already contains entry/sl/rr_t1/delta_alignment. If all those are good, fire. Deep narrative of the checklist is a post-trade writeup, not a pre-trade gate.

**How to apply:**
1. See `🎯` tag in bar summary.
2. FIRST tool call in the response: Bash `pkill -f recon_tick.sh` (not TaskStop).
3. SECOND tool call: `python3 scripts/bar_read.py` to pull the full JSON (one shot).
4. THIRD tool call: `bash scripts/fire_setup.sh --dry-run ...` — pass the values from the candidate + the structural targets.
5. User confirms or overrides. Remove `--dry-run` to fire.
6. Total time under 60 seconds.

This replaces the slow "stop, narrate full checklist in Spanish, then act" flow.
