---
name: Recon Live cadence — LTF every 1s, HTF every 1h
description: In Recon Live mode, poll LTF state every 1 second (quote, CHoCH labels, LTF band). Fire immediately when a setup's conditions are met. HTF bias only refreshes once per hour (on 1h bar boundary).
type: feedback
originSessionId: 747c8a93-a06c-4aa4-9ebb-20aa3b523114
---
User directive 2026-04-23: "nueva regla para recon live monitorea cada segundo el LTF asi en el momento el que se impra in setup hace fire y el HTF solo monitorea cada hora".

**LTF monitoring (every 1 second):**
- Poll `quote_get` for current price / OHLC of forming bar.
- Poll BB CHoCH labels (1m) for new circle / delta changes.
- Poll VWAP + bands values for current distance_sd.
- If a new CHoCH appears AND structural/filter conditions are met → **fire immediately** (don't wait for bar close).

**HTF monitoring (every 1 hour):**
- Read pane 1 (NQ 1h) at top of each hour (:00 minute boundary).
- Compute 4-element vote (Weekly AVWAP, Monthly AVWAP, 1h CHoCH direction, 1h delta sign).
- Cache the bias until next hourly refresh.
- Only re-check HTF when the 1h bar closes and a new 1h bar opens.

**Why**: setups form intrabar — by the time the 1m bar closes, the move has started. Firing at the moment CHoCH confirms (intrabar) captures better entries. HTF is slower-moving, so hourly cadence is sufficient and saves context/time.

**Implementation**: a background shell loop running `while true; do ... sleep 1; done` that watches LTF state changes and emits a signal. The LLM checks the signal log, analyzes, and fires.
