# PROJECT: tvmcpserver — Trading Recon System

## What This Is

A trading strategy execution system for MNQ1!/NQ1! futures on TradingView, built around a custom "Recon" workflow:

- **Recon Backtesting** — walk historical bars candle-by-candle, detect S1 Continuation / S2 Reversal setups, simulate fires with Kelly-based sizing, produce edge metrics
- **Recon Live** — real-time monitoring of LTF (1m) with HTF (1h) bias cache, fire valid setups as they form, manage trades via limit-order exits

## Core Value

Systematic execution of a discretionary-style pivot-reversal strategy (CHoCH + sweep + delta) with objective filters (lunch hours, news, circuit breakers) and honest P&L modeling (limit fills, partial exits, BE runners).

## Stack

- **TradingView Desktop** — chart, replay mode, Pine indicators (BigBeluga CHoCH, LuxAlgo Sessions, Time Cycles, VWAP Auto Anchored)
- **tradingview-mcp/** — Node/TS MCP server bridging TradingView Desktop via Chrome DevTools Protocol (:9222); exposes ~78 tools for chart read/write, replay control, Pine introspection
- **Scripts** — Bash + Python in `scripts/` for fire execution, Telegram bot listener
- **Telegram Bot API** — outbound alerts + inbound commands (@lukacs_agentic_bot)
- **Forex Factory XML** — news calendar (red folder USD events)

## Context

**History:**
- v1 (deleted 2026-04-22): auto-detector stack (recon_batch.sh, bar_read.py, etc.) with 7+ bugs identified — wrong S1/S2 classification, stale CHoCH picks, target-intactness not checked, SL floor missing, etc. Full stack deleted to prevent re-use.
- v1-invalidated backtest (Jan 2 – Jan 23, 2026): 12 trades with PF 0.30, -$1,312 over 11 sessions. Results tainted by detector bugs — do not use as baseline for v2.
- 20 feedback memos in `docs/strategy-memory/` capture all directives from v1 debugging + live sessions.

## Current Milestone: v2.0 Recon System Rebuild

**Goal:** Rebuild detector automation + backtest + recon live harness with correct S1/S2 classification, real sweep verification, intact-target validation, limit-order exit modeling, and news-aware live monitoring.

**Target features:**
- S1/S2 detector classifying by LTF band at sweep moment
- Sweep detection verifying prior swing/TBL was pierced and rejected
- Target selector checking intactness vs today's traded range
- Fire pipeline with limit-order partial exits and BE trail after T1
- Backtest with SQLite + Markdown report, Kelly-based sizing
- Recon Live harness (LTF 1s, HTF 1h, lunch filter, news-pause red only, 3-SL circuit breaker)

**Key context:**
- Starting equity: **$50,000** (backtest)
- Grade caps: A+ 0.75% / A 0.50% / B 0.25% / C 0.20%
- SL floor minimum: 10 pts (or skip)
- S3 Reversal contra-HTF: **disabled** in v2
- Limit-order targets fill instantly on intrabar touch
- Volatility = fuel (LRLR); red news pauses 5/5 min, orange does not
- Active setups: S1_CONTINUATION, S2_REVERSAL_PRO

## Active Requirements

See `.planning/REQUIREMENTS.md` for REQ-IDs.

## Key Decisions

- **No indicator reimplementation in v2.** We consume BigBeluga/LuxAlgo/TimeCycles outputs via MCP (their protected Pine source cannot be extracted anyway). Custom pivot/delta detector deferred to v3.
- **Fire logic owned by Python/Node code, not shell scripts.** The prior `fire_setup.sh` hit permission sandbox issues; v2 moves fire orchestration into a Python module that calls MCP tools directly.
- **Strict rigor on sweep + intact targets.** Per 2026-04-23 directive, no fire without documented prior-level piercing and no fire targeting already-swept levels.

## Out of Scope (v2.0)

- S3 Reversal contra-HTF (disabled)
- Multi-instrument support (MNQ/NQ only)
- ML-driven classification
- Auto-reverse on invalidation
- Custom pivot/delta indicator (deferred to v3)
- Daily auto-commit (user commits manually)

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone:**
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---

Last updated: 2026-04-23