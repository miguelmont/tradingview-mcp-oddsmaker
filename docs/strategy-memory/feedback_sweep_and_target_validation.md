---
name: Strict sweep + intact-target validation before fire
description: Before firing S1 Continuation I MUST verify (a) a real liquidity sweep occurred (price broke a prior swing high/low or TBL box edge and reversed) and (b) the T1/T2/T3 targets are INTACT liquidity pools (not previously touched). CHoCH alone is not a sweep. Session highs that were already tagged today are NOT valid targets.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
User directive 2026-04-23, after I fired an invalid S1 LONG at 27019.25 (MNQ 2026-04-23 live):
> "No hubo un sweep en liquidity y el T1. O sea, no es T1. O sea, tenemos reglas de dónde colocar T1. Definitivamente, eso no es un sweep high ni absolutamente nada valido para T1."

**Rule A — Real sweep required for S1:**
A Setup 1 Continuation is only valid if, **before the CHoCH formed**, a specific vela swept a concrete liquidity level:
- Prior swing high (for SHORT setup) or swing low (for LONG setup), visible on chart — typically a prior BB CHoCH circle, a prior visible pivot, or a local extreme over recent bars.
- OR a TBL box high/low (Time Cycles 10/30/90min box or Sessions [LuxAlgo] Tokyo/London/NY session extremes) that was INTACT going into the sweep.

The sweep must be a **piercing then rejection**: price's high/low goes **beyond** the level, then the bar closes back inside. A CHoCH forming in the middle of a range where no prior level was pierced is **NOT a sweep** — it is a continuation breakout at best, and not valid S1.

**Practical check before firing S1:**
1. Identify the CHoCH circle price.
2. Point to the specific prior swing/TBL level that the last ~5 bars **pierced**.
3. If no such pierced level exists within the last ~10 bars, **do not fire**.

**Rule B — Intact targets only:**
T1, T2, T3 must each be an **intact** liquidity pool — never touched today (for intraday levels) / never touched since its formation (for swing levels). A level that was swept earlier in the same session (e.g., Tokyo High 27,062.50 touched at 07:56 local on 2026-04-23) is **dead liquidity** and not a valid target.

**Practical check before firing:**
- For each candidate T: has the current session's price already traded at or through this level?
- If yes → that level is no longer a magnet. Skip it.
- Find the next INTACT level beyond (prior day's untouched high/low, next up-unswept prior swing, further confluence).
- If no intact level gives RR ≥ 1 from entry → **do not fire**.

**Application to the invalid fire on 2026-04-23:**
- CHoCH bull @26,985 circle was a small LTF range low, not a structural sweep level.
- No documented sweep of a prior swing or TBL box edge before the CHoCH.
- T1 chosen was Tokyo High 27,062.50, which had been swept at 07:56 local (price reached 27,082). Dead liquidity.
- Correct action: skip the setup entirely.
