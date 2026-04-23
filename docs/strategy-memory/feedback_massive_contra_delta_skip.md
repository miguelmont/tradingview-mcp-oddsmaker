---
name: Massive contra-delta degrades grade to B max — NOT auto-skip
description: When a CHoCH prints with |delta|≥2K contradicting the intended trade direction, the setup is NOT invalidated. If every other structural condition is aligned (HTF bias, sweep real, LTF band, intact targets), the setup is still valid but grade is capped at B maximum.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
User directive 2026-04-23 (corrects earlier memo): "un delta masivo en contra si todo lo demas esta alineado no invalida el setup solo degrada su calidad pero sigue siendo B maximo".

**Rule:**
- If |delta_value| ≥ 2000 **contradicting** the trade direction:
  - **Do NOT skip**. Evaluate the full setup.
  - Cap grade at **Grade B maximum** regardless of other quality factors.
- If |delta_value| < 2000 contradicting → normal grade-degrade (A+ → A, A → B, B → C) per strategy spec.
- If delta is aligned → grade may be boosted (|δ|≥2K aligned = institutional conviction).

**Interaction with grade cap:**
- A clean Setup 2 pro-HTF with perfect checklist BUT contra-δ massive → would be A+ → capped at **B** (0.25% equity)
- A Setup 1 aligned with contra-δ massive → would be A → capped at **B**
- A NEUTRAL-HTF setup (already C per tiebreaker) + contra-δ massive → stays C (can't go below C)

**Supersedes** the prior rule that auto-skipped massive contra-delta setups. That earlier rule was too aggressive. Reason for original rule: attention budget during Recon Live Opus mode. With Haiku speed-up that constraint is gone.

**How to apply:**
- Detector emits setup with grade field. If massive contra-δ applies, grade assignment logic: `grade = min(otherwise_grade, "B")`.
- Fire pipeline sizing uses grade as usual → B cap 0.25%.
- Do NOT short-circuit analysis. Run full sweep + target validation regardless of delta.

**Retroactive impact on existing REQs:**
- `DET-04` changes from "|δ|≥2K contradicting → skip" to "|δ|≥2K contradicting → grade capped at B, setup still evaluated".
