# ROADMAP — v2.0 Recon System Rebuild

**6 phases** | **32 requirements mapped** | All covered ✓

| # | Phase | Goal | Requirements | Criteria |
|---|---|---|---|---|
| 1 | Detector v2 | Correct S1/S2 classifier with real sweep verification + NEUTRAL tiebreaker | DET-01..06 | 6 |
| 2 | Target Selector | Intact-target validator with multi-source confluence | TGT-01..04 | 4 |
| 3 | Fire Pipeline | Limit-order exits, BE trail, SL floor, atomic draw, grade independent of RR | FIRE-01..07 | 7 |
| 4 | Backtest v2 | Integration + SQLite + MD report + validation | BACK-01..05 | 5 |
| 5 | Recon Live Harness | 1s poll, 1h HTF cache, filters, news-pause, circuit breaker | LIVE-01..08 | 6 |
| 6 | Strategy Maintenance | Sync `my-strategy.md` with memos + feedback propagation discipline | STRAT-01..03 | 3 |

---

## Phase Details

### Phase 1: Detector v2

**Goal:** Rebuild the setup detector with correct S1 Continuation vs S2 Reversal pro-HTF classification, real liquidity sweep verification, and bar-position CHoCH selection.

**Requirements:** DET-01, DET-02, DET-03, DET-04, DET-05, DET-06

**Success criteria:**
1. Given 2026-01-23 09:42 NY chart state, detector emits `🎯S2_REVERSAL_PRO LONG` (not `⚠S1 SKIP[sweep_out_of_band]` as v1 did)
2. Given 2026-04-23 08:56 CT chart state (bull CHoCH @26,985, δ-43, no prior swing piercing), detector emits `⚠ SKIP[no_sweep]` (not a spurious S1 fire)
3. When an older CHoCH label still appears in BB history but a newer CHoCH has formed at a later bar, detector uses the newer one
4. When |δ| ≥ 2,000 contradicting trade direction, detector caps grade at B (not skip) and still evaluates the full structural checklist; setup fires at B-cap if other criteria pass
5. When HTF is 2-2 NEUTRAL, detector reads Weekly AVWAP direction and only permits setups on that side, forcibly graded C (0.20% cap)
6. Unit tests cover S1/S2/skip/neutral-tiebreaker branches with at least 12 historical fixture cases

### Phase 2: Target Selector

**Goal:** Build the target picker that sources T1/T2/T3 from multiple structural sources, verifies each is intact vs today's traded range, and returns RR-qualified targets or an explicit skip.

**Requirements:** TGT-01, TGT-02, TGT-03, TGT-04

**Success criteria:**
1. Given a LONG setup at 27,019 on 2026-04-23 where today's range already covers 26,851–27,156, target selector returns "no intact T1 with RR ≥ 1, skip" (not the previous bug of firing at swept Tokyo High 27,062.50)
2. Selector can pull candidates from LuxAlgo Sessions pine_labels, Time Cycles pine_boxes, and BB CHoCH lines simultaneously
3. Candidates within 15 pts of each other collapse into a single target
4. Output is a structured record with {price, source, intact: bool, rr: float} per candidate

### Phase 3: Fire Pipeline

**Goal:** Atomic fire execution with limit-order partial exits, BE runner trail, SL floor enforcement, chart drawing via MCP (no shell sandbox dependence), and full logging.

**Requirements:** FIRE-01, FIRE-02, FIRE-03, FIRE-04, FIRE-05, FIRE-06, FIRE-07

**Success criteria:**
1. Firing a T1+T2 trade where price hits T1 produces a 50% partial fill at exactly T1 price and arms BE stop on the runner
2. If price retraces to entry after T1 fill, runner exits at $0 P&L (not at original SL)
3. A setup with structural SL < 10 pts is either widened to the next structural level or skipped with `SKIP[sl_floor_violation]`
4. Fire draws 5 black lines via MCP `draw_shape` without shelling out
5. Every fire produces a row in SQLite `trades` table and a line in `logs/recon_live.jsonl`, plus a Telegram message delivered
6. `.active_trade.json` is written atomically (temp file + rename) to prevent partial-read races
7. Grade is assigned purely from structural factors (setup type, HTF alignment, delta, warnings) — a setup's RR value never promotes or demotes its grade

### Phase 4: Backtest v2

**Goal:** Integrated backtest that replays historical bars with detector + target selector + fire pipeline, tracks Kelly-sized equity, produces SQLite + Markdown report, and validates against known cases.

**Requirements:** BACK-01, BACK-02, BACK-03, BACK-04, BACK-05

**Success criteria:**
1. Backtest runs 2026-01-02 through 2026-01-23 and produces a report with per-trade detail and aggregate metrics
2. Starting equity $50,000 compounds trade-by-trade with correct Kelly sizing per grade (A+ 0.75%, A 0.50%, B 0.25%, C 0.20%)
3. SQLite contains `trades` table with all v1 fields (id, date, setup, grade, direction, entry/sl/t1/t2/t3, contracts, pnl_*, outcome) and `metrics` table per setup+grade
4. Markdown report includes executive summary, edge snapshot table, setup breakdown, target waterfall, equity curve narrative, recommendations, risk warnings
5. Validation step asserts detector produces expected outputs on 5 fixture cases from strategy-memory

### Phase 5: Recon Live Harness

**Goal:** Real-time trading loop that polls LTF every second, refreshes HTF hourly, enforces lunch/news/circuit-breaker filters, fires immediately on valid setups, and sends Telegram summaries at EOD.

**Requirements:** LIVE-01, LIVE-02, LIVE-03, LIVE-04, LIVE-05, LIVE-06, LIVE-07, LIVE-08

**Success criteria:**
1. LTF poll loop runs at 1-second cadence without drift, reading quote + CHoCH + VWAP each tick
2. HTF bias read and voted once per 1h bar close, cached for the hour (no per-tick HTF re-reads)
3. When a valid setup forms intrabar (CHoCH emits + all filters pass), fire executes within 2 seconds of CHoCH appearance
4. Firing is silently suppressed during 11:00–13:00 NY (lunch) and during the 10-minute window around each red folder USD news release pulled from Forex Factory XML
5. After 3 consecutive SL in one session, harness refuses new fires until next 08:30 CT open
6. At 15:30 CT, harness sends a Telegram summary with day's trade list + P&L + equity and clears all drawings via `draw_clear`

### Phase 6: Strategy Maintenance

**Goal:** Keep `docs/my-strategy.md` in sync with the feedback memos in `docs/strategy-memory/`, and enforce the propagation discipline (new feedback → update everywhere in one commit).

**Requirements:** STRAT-01, STRAT-02, STRAT-03

**Success criteria:**
1. Diff between `docs/my-strategy.md` and `docs/strategy-memory/*.md` shows zero contradictions
2. A small helper script validates that every active rule in memos is reflected in strategy doc
3. A propagation-check script flags any commit that adds/modifies a memo without correspondingly updating REQUIREMENTS.md, ROADMAP.md, and my-strategy.md

---

## Dependencies

```
Phase 1 (Detector) ──▶ Phase 2 (Targets) ──▶ Phase 3 (Fire) ──▶ Phase 4 (Backtest)
                                                                      │
                                                                      ▼
                                                                 Phase 5 (Live Harness)
                                                                      │
                                                                      ▼
                                                                 Phase 6 (Strategy sync)
```

Phases 1-3 are sequential. Phase 4 depends on 1-3. Phase 5 can start partially in parallel with Phase 4 (shares Phase 1-3 components but adds live monitoring). Phase 6 is a polishing phase at the end.

---

Last updated: 2026-04-23