# Codebase Concerns: tvmcpserver

**Last updated:** 2026-04-23
**Repo root:** `/Users/miguelmont/Documents/ClaudeProjects/tvmcpserver`
**Status:** Post-cleanup. The prior "detector stack" was deleted after four structural bugs were discovered; the LLM now performs all decision logic directly against the TradingView MCP server. This document tracks the fragile seams left behind.

---

## 1. Tech debt

### 1.1 Deleted detector stack — logic now lives in Claude's prompt
- The prior Python detector (sweep classifier, CHoCH parser, target validator) was removed because it had four compounding bugs:
  1. Applied `sweep_inside_band |SD|≤1.0` universally, causing valid **S2 Reversal** setups to be skipped as if they were S1. Rule belongs to S1 only (see `docs/strategy-memory/feedback_sweep_inside_band.md`).
  2. Stale CHoCH parsing — picked older BB CHoCH entries from `data_get_pine_labels` history instead of the most recent by bar position.
  3. No real sweep detection — treated the CHoCH circle's own position as the "sweep", never verified that a prior swing/TBL box edge had actually been pierced then rejected (see `feedback_sweep_and_target_validation.md`).
  4. Target selection did not check intact-ness vs. the current session's traded range; dead liquidity (e.g., Tokyo High already swept earlier) was proposed as T1.
- **Consequence:** all of setup classification, sweep verification, target intact-ness, SL floor, grade capping, and news-window gating are now **prompt-resident rules** distributed across 20 feedback memos under `docs/strategy-memory/*.md`. No CI enforces them. Drift is possible on any session where the wrong memo is missed.
- **Mitigation options (not yet done):** (a) re-introduce narrow, test-backed validators for the mechanically-checkable rules (sweep piercing, intact target, SL floor, RR_T1≥1, lunch window, circuit breaker) while keeping regime-interpretation in the LLM; (b) consolidate memos into a single authoritative rulebook to reduce per-session risk of omission.

### 1.2 Broken tests — no safety net
- `tests/test_bar_read.py` imports `bar_read` from `scripts/`, but that module was deleted with the detector stack. Running it fails at import.
- `tests/fixtures/` still contains captured label/line snapshots that would be valuable for a future parser — they should be preserved even if the test file is rewritten.
- There is **no other test coverage** in the repo. Nothing is exercised in CI; there is no CI config file at all.
- **Action:** either delete `tests/test_bar_read.py` (and update README), or port the fixture-driven tests to a new `scripts/` module when 1.1 mitigation happens.

### 1.3 Scattered strategy rules across 20 memos
- Rules evolve session-to-session and are captured as individual `feedback_*.md` files. Known to be currently active and non-trivial to reconcile:
  - `feedback_sweep_inside_band.md` — applies to S1 only, not S2/S3.
  - `feedback_s3_disabled.md` — S3 must not detect/fire at all.
  - `feedback_sl_floor_needed.md` — min SL distance = `max(10pt, 1×ATR(14,1m))`; widen or skip.
  - `feedback_c_cap_020.md` — Grade C cap raised from 0.10% → 0.20% equity.
  - `feedback_limit_order_exits.md` — P&L model: limit-order fills at T1/T2/T3, partial exits, runner to BE after T1.
  - `feedback_recon_live_cadence.md` — LTF poll 1s, HTF poll 1h (bar boundary).
  - `feedback_news_pause_red_only.md` + `feedback_volatility_is_fuel.md` — red folder = 5-min pause window; orange = no pause (these two memos are related and must be read together).
  - `feedback_no_lunch_entries.md`, `feedback_daily_loss_circuit_breaker.md`, `feedback_neutral_htf_weekly_tiebreaker.md`, `feedback_rr_not_grade_factor.md`, `feedback_intact_swings_targets.md`, `feedback_massive_contra_delta_skip.md`, `feedback_stop_immediately_on_candidate.md`, `feedback_manual_backtest_stepping.md`, `feedback_no_auto_commit.md`, `feedback_clear_lines_eod.md`.
- `docs/my-strategy.md` was flagged in `feedback_sl_floor_needed.md` and `feedback_c_cap_020.md` as needing updates to reflect the new rules — unverified whether that was done.
- **Risk:** a new session without the auto-memory index will miss rules; a stale `my-strategy.md` will silently conflict with newer memos.

### 1.4 `docs/strategy-memory/` lacks an index/manifest
- 20 feedback files with no `INDEX.md`. The currently-used index lives in user auto-memory (`~/.claude/projects/.../memory/MEMORY.md`) which is **per-user, per-machine** — not versioned with the repo.
- **Risk:** cloning the repo loses the memo priority ordering. Contributors will not know which rules override which.

---

## 2. Known issues

### 2.1 `scripts/fire_setup.sh` — sandbox/permission hook conflict
- File at `scripts/fire_setup.sh:122-131` shells out to `node tradingview-mcp/src/cli/index.js draw shape ...` to draw the 5 horizontal lines.
- Post-cleanup permission rules deny that path. **New fires must call `mcp__tradingview__draw_shape` MCP tool directly from the LLM**, not the CLI wrapper.
- Consequences:
  - `fire_setup.sh` is currently a **dead code path** for the draw step — it will abort at line 140-145 with "empty entity_id" because the CLI invocation is blocked.
  - The Telegram send, assertion block (`scripts/fire_setup.sh:62-100`), JSONL logging (`scripts/fire_setup.sh:174-188`), and `.active_trade.json` write (`scripts/fire_setup.sh:192-195`) are all still useful and well-factored.
- **Action needed:** either (a) split the script into `assert_and_log.sh` (keep) + inline MCP `draw_shape` calls by the LLM (replace), or (b) replace the `$TV draw shape` block with an adapter that calls the MCP server through a permitted channel.

### 2.2 `.active_trade.json` — shared state with no locking
- Written by `scripts/fire_setup.sh:192-195` with a plain `cat > ... <<EOF` — no `flock`, no atomic rename (not even `mv`-from-tmp).
- Read by the Recon monitor loop (per `feedback_recon_live_cadence.md` cadence = 1s).
- **Race scenarios:**
  - Reader catches the file mid-write → JSON parse error, monitor misreads trade state.
  - Second fire while first is still being written → truncation.
  - Crash between `cat >` open and EOF close → zero-byte file on disk, active trade "disappears" until next fire.
- **Fix:** write to `.active_trade.json.tmp` then `mv` (atomic on the same filesystem); optionally `flock` the monitor reader.

### 2.3 `.htf_cache.json` — wall-clock vs. replay-bar-time invariant lost
- Current file (`.htf_cache.json:1`) has both `_cached_bar_time: 1769176800` and `_cached_unix: 1776919557`, but the previous fix that keyed expiry to **bar time (replay-safe)** was deleted with the detector stack.
- On Recon Backtesting (manual stepping per `feedback_manual_backtest_stepping.md`), walking the chart backward/forward must not invalidate the cache against wall-clock. If the rebuilt HTF poller uses `time.time()` or `date +%s` for freshness, backtests will redundantly recompute or silently serve stale cross-epoch data.
- **Action needed:** whoever rebuilds the HTF poller (per `feedback_recon_live_cadence.md`, refresh on 1h bar boundary) must read `_cached_bar_time`, not `_cached_unix`, for the staleness check during replay.

### 2.4 `tradingview-mcp/` is gitignored — fresh clone is non-functional
- `.gitignore:5` excludes `tradingview-mcp/`.
- `.mcp.json:4` points at `/Users/miguelmont/Documents/ClaudeProjects/tvmcpserver/tradingview-mcp/src/server.js` with an **absolute path hardcoded to the current user's home**.
- A fresh clone on a different machine will (a) have no `tradingview-mcp/` directory at all, and (b) fail MCP startup because the absolute path does not exist.
- **Fix:** document the MCP setup step in `README.md` (currently 1 line, 28 bytes); either vendor the MCP server as a submodule, or publish it separately and reference a relative/env-var path in `.mcp.json`.

### 2.5 `README.md` is effectively empty
- 28 bytes. No setup instructions, no architecture sketch, no pointer to `docs/strategy-memory/`, no mention of the `.mcp.json` prerequisite.
- Only surviving onboarding path is `docs/my-strategy.md` + `docs/backtest_report_2026-01-02_to_01-16.md` + the memos.

---

## 3. Fragile areas

### 3.1 Telegram listener loop
- `scripts/telegram_recon_listener.sh:35-46` is a `while true; sleep 1` loop calling `getUpdates` with `timeout=30`.
- Not supervised — if `curl` or the Python parser crashes, the loop dies silently. No `systemd`/`launchd` unit, no restart-on-failure, no healthcheck.
- `offset_file` lives in `/tmp/tv_recon_offset_<chat_id>.txt`; on macOS reboot `/tmp` is cleared → listener will re-prime and skip any messages between reboot and first poll (behaviour is correct but silent).
- `scripts/telegram_recon_parse.py:33-77` short-circuits status commands by `subprocess.Popen` spawning `status_snapshot.py`. The referenced script `STATUS_SCRIPT = scripts/status_snapshot.py` is **not present** in the current `scripts/` directory (only `fire_setup.sh`, `telegram_recon_listener.sh`, `telegram_recon_parse.py`). HTF/LTF/Status Telegram commands will silently fail with a caught exception printed to stderr (line 29-30) — the user never sees the failure.
- **Fix priorities:** (a) ship `status_snapshot.py` or remove the references, (b) wrap the listener in `launchd` with `KeepAlive`, (c) surface spawn failures via Telegram reply instead of just stderr.

### 3.2 Absolute paths and `cd` side-effects
- Every script starts with `cd "$(dirname "$0")/.."` to normalize to repo root (`scripts/fire_setup.sh:23`, `scripts/telegram_recon_listener.sh:8`). This couples working directory to script location and breaks if a caller (e.g., an agent thread per the Agent SDK note that "cwd resets between bash calls") expects cwd stability.
- `.mcp.json:4` hardcodes user-level absolute path (see 2.4).

### 3.3 Implicit contract between `fire_setup.sh` and `docs/strategy-memory/feedback_limit_order_exits.md`
- The limit-order exit model (50/50 at T1/T2, 1/3 at each, BE runner after T1) is **purely a reporting model in memos** — `fire_setup.sh` draws 5 lines and writes `.active_trade.json` but does not encode partial-exit levels or BE-trailing behaviour. Anything reading `.active_trade.json` to compute live P&L must re-implement the model from the memo.
- **Risk:** the monitor and the P&L reporter diverge on how to handle a T1-then-pullback-to-BE scenario.

### 3.4 Feedback rule precedence is implicit
- `feedback_news_pause_red_only.md` says orange news does NOT pause; `feedback_volatility_is_fuel.md` reiterates and adds LRLR framing. They are consistent but overlap. If a future memo contradicts either, the resolution strategy is undefined.
- `feedback_stop_immediately_on_candidate.md` mandates `pkill -f recon_tick.sh` (not `TaskStop`) on `🎯` tag — an out-of-band side-channel that no script enforces. If the user's environment changes script names, the kill line needs to be revisited.

### 3.5 HTF cache race
- Only one `.htf_cache.json` in the repo root; if two processes (live + backtest) ever run together (even briefly during a mode switch) they will clobber each other's cache. No lock, no per-mode namespacing.

---

## 4. Security

### 4.1 Secrets handling — currently acceptable
- Telegram bot token + chat ID live in `.env` only (`scripts/fire_setup.sh:152`, `scripts/telegram_recon_listener.sh:11` source it with `set -a; source .env; set +a`). Not committed (`.gitignore:1-2` excludes `.env` and `.env.local`).
- No API keys appear in source. Grep confirms the only secret-bearing file is `.env`.

### 4.2 Telegram URL construction — low-risk but worth noting
- `scripts/fire_setup.sh:165-168` builds the Telegram API URL with `${TELEGRAM_BOT_TOKEN}` interpolated directly, then `--data-urlencode`s the body. Token appears in `curl` argv — visible in `ps` output. Very minor local-machine exposure; acceptable for a single-user dev machine but noteworthy if the repo is ever multi-user.
- `scripts/telegram_recon_listener.sh:23,37-39` has the same pattern for `getUpdates`.

### 4.3 Shell injection surface in `fire_setup.sh`
- `scripts/fire_setup.sh:62-94` interpolates `${ENTRY}`, `${SL}`, `${T1}` etc. directly into a `python3 - <<PY ... PY` heredoc. The args come from the command line, ultimately from the LLM. If any argument contains Python syntax or a line containing `PY`, the assertion block executes attacker-chosen Python.
- Same pattern in the JSONL log block (`scripts/fire_setup.sh:174-188`) and the `cat > .active_trade.json` heredoc (`scripts/fire_setup.sh:193-195`).
- **Realistic risk:** low (single-user, inputs come from Claude), but the pattern is wrong and will bite if the script is ever re-used with external input. **Fix:** pass values via `argv`/env vars into the python block, don't string-interpolate.
- Same category: `MSG=` multi-line string (`scripts/fire_setup.sh:155-164`) is fed to `--data-urlencode`, which is safe against URL injection but not against Markdown injection into Telegram — a malicious `LABEL` could break formatting. Minor.

---

## 5. Performance

### 5.1 1-second poll cadence is expensive on MCP
- `feedback_recon_live_cadence.md` mandates 1s LTF polling. Each tick performs `quote_get` + `data_get_pine_labels` + VWAP band reads. If the MCP server serializes requests or the UI repaints synchronously, this will show up as sustained CPU / chart jank. No measurements are in the repo.
- **Watch:** if `capture_screenshot` or `data_get_pine_labels` ever blocks the chart UI for >1s, the loop will fall behind silently.

### 5.2 HTF recompute is cheap but unbounded on backtest stepping
- Manual backtest stepping (`feedback_manual_backtest_stepping.md`) is driven by `bash scripts/recon_tick.sh` batches. If each tick invalidates the HTF cache wall-clock-wise (see 2.3), every step recomputes a 4-vote tally that requires multiple MCP reads. Batches of >60 steps will be measurably slow.

### 5.3 JSONL log unbounded growth
- `logs/recon_live.jsonl` is append-only (`scripts/fire_setup.sh:174`). No rotation. At ~500 bytes/fire and a few fires/day it will not matter for a year, but no housekeeping exists.

### 5.4 Telegram listener wakes up every second
- `sleep 1` + long-poll `timeout=30` overlap inefficiently — the long-poll already blocks up to 30s. The outer `sleep 1` between iterations is vestigial and wastes a wake. Replace with `sleep 0` or remove.

---

## 6. Priority summary

| # | Area | Severity | Effort |
|---|---|---|---|
| 1 | `fire_setup.sh` draw step broken by sandbox rule (§2.1) | **High** — blocks live firing | M |
| 2 | `.active_trade.json` race (§2.2) | High | S |
| 3 | Missing `status_snapshot.py` referenced by parser (§3.1) | High — silent failure | S |
| 4 | HTF cache bar-time vs wall-clock (§2.3) | High for backtests | S |
| 5 | Broken `tests/test_bar_read.py` (§1.2) | Medium | S |
| 6 | Scattered memos, no index (§1.3, §1.4) | Medium (cross-session drift) | M |
| 7 | `tradingview-mcp/` gitignored + hardcoded path (§2.4) | Medium (clone breaks) | M |
| 8 | `fire_setup.sh` heredoc interpolation (§4.3) | Low (single-user) | S |
| 9 | Listener supervision / restart (§3.1) | Low | S |
| 10 | README effectively empty (§2.5) | Low | S |

---

*Document generated 2026-04-23 as part of the `.planning/codebase/` audit.*
