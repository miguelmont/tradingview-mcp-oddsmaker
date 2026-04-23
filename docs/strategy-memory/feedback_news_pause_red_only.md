---
name: News pause — red folder only, not orange
description: Only RED folder (High impact) Forex Factory events require a trading pause window. Orange folder (Medium) events do NOT require pause — continue normal Recon Live monitoring through them.
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
User directive 2026-04-23: "las orange news no requieren pausa".

**Pause policy (final, 2026-04-23):**
- 🔴 **Red folder** (High impact USD news): pause Recon Live from **5 min BEFORE** the release to **5 min AFTER**. No new fires during this window. Manage open trades normally (SL/T1 still trigger).
- 🟠 **Orange folder** (Medium impact): **no pause**. Continue normal monitoring and firing.
- Other currencies' red news (EUR, GBP, JPY, etc.): not explicitly covered — assume same logic applies if asked, but default is focus on USD since NQ is USD-denominated.

**How to apply:**
- Daily: at session open, pull Forex Factory red folder USD events for the day.
- For each red event: mark a pause window in the monitor log so it pauses automatically.
- Only the LLM's fire-decision logic needs to respect the window; the price-streaming 1s monitor can keep running.

**Today 2026-04-23**: all events are orange → no pauses required. Continue Recon Live normally.
