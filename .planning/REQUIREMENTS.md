# REQUIREMENTS — v2.0 Recon System Rebuild

## Milestone v2.0 Requirements

### Detector (DET)

- [ ] **DET-01**: Detector classifies setup as S1 Continuation or S2 Reversal pro-HTF based on LTF band state **at the moment of sweep** (not at the current bar)
- [ ] **DET-02**: Detector verifies a real liquidity sweep occurred — a bar pierced a prior swing high/low or TBL (Time Cycles box) level and then closed back inside
- [ ] **DET-03**: Detector selects the most recent CHoCH by **bar position**, not by label-list order, to avoid picking stale CHoCHs
- [ ] **DET-04**: Detector caps grade at **B maximum** when |δ| ≥ 2,000 contradicts the proposed trade direction. Setup is NOT skipped — it is evaluated fully and fires if all other structural conditions pass, but at the B-cap 0.25% equity (supersedes prior auto-skip rule)
- [ ] **DET-05**: Detector emits structured output with setup type, direction, entry, SL candidate, sweep evidence (vela + pierced level), delta, and skip reasons when applicable
- [ ] **DET-06**: Detector handles NEUTRAL HTF (2-2 vote) by reading the Weekly AVWAP direction as tiebreaker — only setups aligned with Weekly direction are permitted, and all NEUTRAL-HTF setups are forcibly graded C (capped at 0.20%) regardless of other quality factors

### Target Selector (TGT)

- [ ] **TGT-01**: Target selector verifies each candidate T1/T2/T3 is **intact** — never touched during the current trading session (or never touched since its formation for swing levels)
- [ ] **TGT-02**: Target selector sources candidates from: past BigBeluga swing levels, LuxAlgo Session highs/lows (Tokyo/London/NY), Time Cycles box edges, Daily Ranges Dividers (PDH/PDL/PWH/PWL/PMH/PML)
- [ ] **TGT-03**: Target selector collapses clustered levels (spacing < 15 pts) and requires the selected T1 to give RR ≥ 1 from entry
- [ ] **TGT-04**: Target selector outputs T1/T2/T3 with intact-status flag, source indicator, and RR from entry; when no intact T1 with RR ≥ 1 exists, emits "no valid target, skip"

### Fire Pipeline (FIRE)

- [ ] **FIRE-01**: Fire pipeline models limit-order partial exits — 100% at T1 for single-target mode, 50/50 for T1+T2, 33/33/33 for T1+T2+T3
- [ ] **FIRE-02**: Fire pipeline applies breakeven trail on runners after T1 fills (SL moves to entry; if price retraces to BE, runner exits at $0 P&L)
- [ ] **FIRE-03**: Fire pipeline enforces SL floor of 10 pts minimum — if circle+2-tick gives less than 10 pts, widen to next structural swing beyond the circle OR skip the setup
- [ ] **FIRE-04**: Fire pipeline draws Entry/SL/T1/T2/T3 horizontal lines on chart via MCP `draw_shape` directly (no dependence on external shell scripts that hit sandbox permission issues)
- [ ] **FIRE-05**: Fire pipeline logs every fire to SQLite (trades table) and JSONL (`logs/recon_live.jsonl`) atomically, and writes `.active_trade.json` for live-monitor state
- [ ] **FIRE-06**: Fire pipeline sends formatted Telegram notification at fire, at each partial fill (T1/T2/T3), and at final close
- [ ] **FIRE-07**: Grade assignment ignores RR_T1 magnitude — RR is a validity filter only (RR < 1 → skip) and a reporting value; it does NOT modify grade quality. A clean S2 with RR 1.2 is still A+ if structure + delta + checklist are 100%

### Backtest (BACK)

- [ ] **BACK-01**: Backtest replays historical bars bar-by-bar using detector + target selector + fire pipeline, starting from a user-specified replay cursor
- [ ] **BACK-02**: Backtest tracks equity per trade with half-Kelly sizing per grade (A+ 0.75%, A 0.50%, B 0.25%, C 0.20%) against starting equity $50,000, compounding per trade
- [ ] **BACK-03**: Backtest produces SQLite database with `trades` (per trade) and `metrics` (per setup+grade aggregate) tables matching the schema in `docs/my-strategy.md`
- [ ] **BACK-04**: Backtest generates a Markdown report with executive summary, edge metrics (win rate, PF, expectancy, Sharpe, drawdown), setup breakdown, target waterfall, and actionable recommendations
- [ ] **BACK-05**: Backtest validates against known historical cases from strategy-memory: 2026-01-23 09:42 NY must emit S2 LONG, 2026-04-23 11:34 sweep of 26,958 must emit S2 A+ LONG, 2026-04-23 08:56 bull@26,985 δ-43 must skip

### Recon Live Harness (LIVE)

- [ ] **LIVE-01**: Harness polls LTF state (quote + CHoCH labels + VWAP + Sessions values) every 1 second
- [ ] **LIVE-02**: Harness caches HTF bias (4-element vote) per 1-hour bar, refreshing only on 1h bar close
- [ ] **LIVE-03**: Harness fires immediately when detector emits a valid setup (no waiting for 1m bar close)
- [ ] **LIVE-04**: Harness enforces lunch filter — no fires between 11:00 NY and 13:00 NY (inclusive-start, exclusive-end)
- [ ] **LIVE-05**: Harness enforces 3-SL-consecutive circuit breaker per session — after the third consecutive SL of the day, no new fires until the next session open
- [ ] **LIVE-06**: Harness pulls Forex Factory red folder USD events for the day and pauses firing from 5 min before to 5 min after each release; orange folder events do **not** trigger pause
- [ ] **LIVE-07**: Harness sends a Telegram session-close summary at 15:30 CT and clears all drawn lines via `draw_clear`
- [ ] **LIVE-08**: Harness monitors active trade for SL/T1/T2/T3 intrabar touches and triggers exits per the limit-order model (no lag from bar-close)

### Strategy Maintenance (STRAT)

- [ ] **STRAT-01**: `docs/my-strategy.md` reflects all rules currently active in `docs/strategy-memory/*.md` (cross-checked)
- [ ] **STRAT-02**: Whenever a new feedback memo is added, the strategy doc is updated in the same commit or immediately after
- [ ] **STRAT-03**: New user feedback triggers full propagation: memo → MEMORY.md → docs/strategy-memory → my-strategy.md → REQUIREMENTS.md → ROADMAP.md → active PLAN.md → STATE.md, all in the same or immediately-following commit (per `feedback_update_all_on_new_feedback.md`)

## Future Requirements (deferred to v3+)

- Custom pivot + delta detector (replace dependence on BB indicator)
- S3 Reversal contra-HTF (re-enable after v2 collects n ≥ 30 S2 trades with positive edge)
- Multi-instrument support (ES, YM, CL)
- Auto-reverse on invalidation signal
- ML-driven confidence scoring on setups

## Out of Scope (v2.0)

- **S3 Reversal contra-HTF** — disabled per feedback; low edge in prior test sample
- **Custom pivot/delta reimplementation** — BB's Pine is protected; we consume outputs, not re-derive
- **Multi-instrument** — scope creep; MNQ/NQ only
- **ML classification** — requires data collection first; not in v2
- **Daily auto-commit** — user commits manually per `feedback_no_auto_commit.md`
- **Auto-reverse** — requires live invalidation signal framework; deferred

## Traceability

| REQ-ID | Phase | Plan | Status |
|---|---|---|---|
| DET-01..06 | Phase 1 | 01-01-PLAN.md | pending |
| TGT-01..04 | Phase 2 | 02-01-PLAN.md | pending |
| FIRE-01..07 | Phase 3 | 03-01-PLAN.md | pending |
| BACK-01..05 | Phase 4 | 04-01-PLAN.md | pending |
| LIVE-01..08 | Phase 5 | 05-01-PLAN.md | pending |
| STRAT-01..03 | Phase 6 | 06-01-PLAN.md | pending |

---

Last updated: 2026-04-23