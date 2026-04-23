# STATE.md

## Current Position

- **Milestone:** v2.0 Recon System Rebuild
- **Phase:** Not started (defining requirements + roadmap)
- **Plan:** —
- **Status:** Milestone initialized
- **Last activity:** 2026-04-23 — Milestone v2.0 started, PROJECT.md + REQUIREMENTS.md + ROADMAP.md created

## Accumulated Context

### Strategy Memory

20 feedback memos in `docs/strategy-memory/` capture all strategy directives:
- S1/S2/S3 classification rules (S3 disabled)
- Sweep + intact-target validation
- SL floor 10pt minimum
- Limit-order exit modeling
- Grade caps (A+ 0.75 / A 0.50 / B 0.25 / C 0.20)
- Lunch filter (11-13 NY)
- News pause (red folder USD only, 5/5 min)
- Circuit breaker (3 consecutive SL)
- NEUTRAL HTF Weekly tiebreaker
- Recon Live cadence (LTF 1s, HTF 1h)
- LRLR volatility framework

### Codebase Map

7 documents in `.planning/codebase/`:
- STACK, INTEGRATIONS, ARCHITECTURE, STRUCTURE, CONVENTIONS, TESTING, CONCERNS

### Deleted (v1)

Detector stack deleted 2026-04-22 due to bugs:
- `scripts/recon_batch.sh`, `recon_tick.sh`, `recon_scan.sh`
- `scripts/bar_read.py` (evaluate_setup_candidate — buggy classifier)
- `scripts/backtest_pipeline.py`, `backtest_v2.py`
- `scripts/status_snapshot.py`

### Remaining Runtime Scripts

- `scripts/fire_setup.sh` (legacy; to be replaced in Phase 3)
- `scripts/telegram_recon_listener.sh`
- `scripts/telegram_recon_parse.py` (needs fix — references deleted status_snapshot.py)

## Pending Blockers

None.

## Session Continuity

**If resuming:** Next step is `/gsd-discuss-phase 1` or `/gsd-plan-phase 1` for Phase 1 (Detector v2).