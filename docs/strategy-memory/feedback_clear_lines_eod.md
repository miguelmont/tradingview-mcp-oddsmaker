---
name: Clear all drawn lines at end of each session
description: At [SESSION CLOSE] of every trading day, wipe all Entry/SL/T1/T2/T3 horizontal lines from the chart with draw_clear. Don't leave lines accumulating across days.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
User directive 2026-04-22: "cuando termine el dia limpia todas las lineas trazadas".

**How to apply:**
- At the end of each session (after 15:30 CT bar prints and session-close summary is sent to Telegram), call `mcp__tradingview__draw_clear` to remove every Entry / SL / T1 / T2 / T3 horizontal line drawn by `fire_setup.sh` that day.
- Do NOT leave lines from prior trades overlapping the next session's chart — they clutter analysis and can be mistaken for active levels.
- If there is an open trade carrying over (should be rare per limit-order exit model, but possible), keep that trade's lines and clear the rest only.
