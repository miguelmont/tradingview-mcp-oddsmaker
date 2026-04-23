# My Strategy — Operating Rules

**Instrument**: NQ1! (E-mini Nasdaq futures)
**Timeframes**: 1min (execution) · 1h (HTF bias)

> **Active setups**: **S1 Continuation** and **S2 NY Reversal pro-HTF** only. **S3 Reversal contra-HTF is DISABLED** (2026-04-22 directive) — see [Setup 3](#setup-3--ny-reversal-contra-htf-disabled).

## Physical layout

Single chart with **2h layout** (2 horizontal panes):
- **Pane 0 (left)**: NQ1! 1min — execution
- **Pane 1 (right)**: NQ1! 1h — HTF bias

SMT with ES disabled for now (not considered).

## Required indicators on chart

- VWAP Auto Anchored (Session VWAP with ±1 SD bands)
- VWAP Auto Anchored (Weekly, for HTF)
- VWAP Auto Anchored (Monthly, for HTF)
- Choch Pattern Levels [BigBeluga] (CHoCH + delta volume)
- Time Cycles (TTP) (10/30/90min boxes + session)
- Sessions [LuxAlgo] (session highs/lows)
- Daily Ranges Dividers (PDH/PDL/PWH/PWL/PMH/PML) — if available

## Setup rules

### HTF bias (read on 1h) — 4-element voting system

The HTF bias is determined by **voting of 4 elements**. CHoCH direction and delta sign are **independent variables**, so each counts as its own vote.

1. **Weekly AVWAP**: price > Weekly = **+1 (bullish)** · price < Weekly = **-1 (bearish)**
2. **Monthly AVWAP**: price > Monthly = **+1 (bullish)** · price < Monthly = **-1 (bearish)**
3. **Direction of the latest Big Beluga CHoCH on 1h** (circle position):
   - ◯ at the **HIGHEST** price of the 3 anchors = **BEARISH** CHoCH → **-1**
   - ◯ at the **LOWEST** price of the 3 anchors = **BULLISH** CHoCH → **+1**
   - No clear recent CHoCH = **0**
4. **Delta sign of the latest Big Beluga CHoCH on 1h** (buy/sell pressure, independent from CHoCH direction):
   - delta > 0 (positive, buy pressure dominant) → **+1**
   - delta < 0 (negative, sell pressure dominant) → **-1**
   - |delta| very small (noise, e.g. < |500|) → **0**
   - No recent CHoCH (element 3 = 0) → delta also **0** (no valid reading)

**Decision rule** — need **3 concurring votes** to confirm a direction:

```
BULLISH   ⟺  ≥ 3 elements vote +1  (3/4 or 4/4 bullish)
BEARISH   ⟺  ≥ 3 elements vote -1  (3/4 or 4/4 bearish)
NEUTRAL   ⟺  no 3-majority (2-2 ties, 2-1-1 splits, etc.)
```

**NEUTRAL bias — Weekly VWAP tiebreaker for low-probability Grade C trades:**

When HTF is NEUTRAL (typically 2-2 with Weekly/Monthly on one side and CHoCH/Delta on the other), we do NOT abstain completely. Instead, we adopt the **Weekly VWAP direction** as the permitted trade direction, but treat every setup as **Grade C** (low-probability, capped 0.10% equity size or skip).

- Price > Weekly AVWAP → only LONG setups allowed, cap C.
- Price < Weekly AVWAP → only SHORT setups allowed, cap C.
- Setups against the Weekly direction in NEUTRAL bias: **skipped entirely**.
- All structural requirements of S1/S2/S3 still apply; the C-grade cap just reflects the lower edge.

**Example (2026-01-05)**: HTF = Weekly+1 · Monthly+1 · CHoCH-1 · Delta-1 → 2-2 NEUTRAL. Weekly direction bullish. Only LONGs taken, Grade C, size 0.10%.

**Examples**:
- Price > W (+1) · Price > M (+1) · BB CHoCH bearish (-1) · delta +109K (+1) → **3-1 BULLISH**
- Price > W (+1) · Price < M (-1) · BB CHoCH bullish (+1) · delta +50K (+1) → **3-1 BULLISH**
- Price > W (+1) · Price < M (-1) · BB CHoCH bearish (-1) · delta +30K (+1) → **2-2 NEUTRAL**
- Price < W (-1) · Price < M (-1) · BB CHoCH bearish (-1) · delta +20K (+1) → **3-1 BEARISH**

**Implication**: adding delta as a 4th independent vote raises the confirmation bar (need 3/4 instead of 2/3) and gives more weight to institutional flow. Bias flips to NEUTRAL more often on conflicting days — fewer but cleaner trade setups.

### LTF state (read on 1min)

```
Distance = (price − SVWAP) / SVWAP_sd

IN-BAND             ⟺  |Distance| ≤ 0.5
NEAR-BAND           ⟺  0.5 < |Distance| ≤ 1.0
BULLISH-OVEREXT     ⟺  Distance > 1.0
BEARISH-OVEREXT     ⟺  Distance < -1.0
```

### Setup 1 — NY Continuation

```
ACTIVATES ⟺ all:
  ├─ HTF bias defined
  ├─ LTF **at time of sweep** must be IN-BAND or NEAR-BAND (|SD| ≤ 1.0). NO inference of "slightly overext" is allowed — the sweep itself must occur inside the band. Borderline tolerance only applies at entry confirmation (below).
  ├─ recent TBL sweep (≤10 bars 1min, Time Cycles 10/30/90/session box)
  │    or structural swing high/low sweep (previous Big Beluga level)
  ├─ Big Beluga CHoCH in direction of HTF bias (≤5 bars after sweep)
  └─ in NY session

ENTRY:   close of CHoCH bar
STOP:    **Swing low (LONG) / swing high (SHORT) of the Big Beluga LTF** that validated the CHoCH
         = exact position of the circle ◯ that printed the CHoCH on 1min
         + 2-tick margin to avoid exact wicks
         ⚠️ NEVER use the bar low/high of the CHoCH bar as stop (they are non-structural wicks).
         ⚠️ NEVER use the deep anchor of the Big Beluga pattern — use the exact circle ◯ level.
RR min:  1.0 **measured to T1** (entry → T1). RR < 1 to T1 → skip. T2/T3 no tienen RR mínimo — pueden ser 1-2 o mayor. Grade cap applies per RR_T1 (see grading table).
```

**Flexibility note — Setup 1 only · ONLY applies at entry confirmation, NOT at sweep**:
- This rule applies **exclusively to Setup 1 (Continuation)**. Setups 2 and 3 (reversals / mean reversion) premise on overextension, so the sweep is expected to occur outside the band — see those setups for their own criteria.
- For Setup 1: at the moment the BB CHoCH **confirms** and we take the entry, LTF can be slightly overextended (|SD| up to ~1.2) — this accounts for the breakout wick of the CHoCH bar itself.
- But the **sweep** (the liquidity grab that primes the continuation) MUST occur while LTF is IN-BAND or NEAR-BAND (|SD| ≤ 1.0). If price was already overextended when the sweep happened, it is **not** a Setup 1 — no inference, no "slightly outside" tolerance. Binary check.
- Rationale: a Setup 1 sweep inside the band means there is room for the continuation to run; a sweep outside the band means price is already extended and the continuation thesis is weaker (that territory belongs to Setup 2/3 reversals).

### Setup 2 — NY Reversal pro-HTF

**Note**: Setup 2 premises on overextension — the sweep is EXPECTED to occur outside the band. The `sweep_inside_band` rule from Setup 1 does NOT apply here.

```
ACTIVATES ⟺ all:
  ├─ HTF bias defined
  ├─ LTF |SDs| > 1.0 IN OPPOSITE DIRECTION to HTF bias
  ├─ TBL sweep in the same direction as the overextension
  │    (sweep is the flush that creates/deepens the overextension — so `sweep_out_of_band` is expected)
  ├─ Big Beluga CHoCH in HTF direction (against the overextension)
  └─ in NY session

ENTRY:   close of CHoCH bar
STOP:    **Swing low (LONG) / swing high (SHORT) of the Big Beluga LTF** that validated the CHoCH
         = exact position of the circle ◯ that printed the CHoCH on 1min
         + 2-tick margin to avoid exact wicks
         ⚠️ NEVER use the bar low/high of the CHoCH bar as stop (they are non-structural wicks).
         ⚠️ NEVER use the deep anchor of the Big Beluga pattern — use the exact circle ◯ level.
RR min:  1.0 **measured to T1** (entry → T1). RR < 1 to T1 → skip. T2/T3 no tienen RR mínimo — pueden ser 1-2 o mayor.
```

### Setup 3 — NY Reversal contra-HTF **(DISABLED)**

> **Status — DISABLED (effective 2026-04-22).** S3 no longer emits, detects, or fires. Rationale: contra-HTF reversals showed negative edge in backtest (multiple LONG S3s against bearish momentum stopped out for combined -$160 on first test sample). Re-enablement requires (a) explicit user directive AND (b) ≥ 30 S2 trades logged to establish baseline edge first.
>
> **How the code enforces this**: `evaluate_setup_candidate` in [scripts/bar_read.py](scripts/bar_read.py) has the S3 branch commented out. Patterns that structurally match S3 (LTF overext same-dir as HTF + CHoCH contra-HTF) emit **nothing** — not even a `⚠` skip line.

Original structural definition (preserved for reference; do not implement):

```
ACTIVATES ⟺ all:
  ├─ HTF bias ∈ {BULLISH, BEARISH}  (does NOT activate on neutral)
  ├─ LTF |SDs| > 1.0 IN SAME DIRECTION as HTF bias
  ├─ TBL sweep in the same direction
  ├─ Big Beluga CHoCH against HTF
  └─ in NY session

ENTRY:   close of CHoCH bar
STOP:    exact circle ◯ level + 2-tick margin
RR min:  1.0 measured to T1
```

## Filters & gating (apply BEFORE firing)

Every candidate that passes structural validation must also pass these runtime gates. Failing any one of them converts a clean `🎯` into a `⚠ SKIP[reason]` line — no trade fires.

### Lunch-hour block — 11:00 to 13:00 NY
All new entries between **11:00 NY and 13:00 NY** (inclusive-start, exclusive-end) are **skipped entirely**. This is a chop-filter: midday range-bound action generates low-quality CHoCHs. Applies to all setups and all grades. Trades already open at 11:00 NY continue to be managed — only *new* entries are blocked.

### Massive contra-delta auto-skip
When the LTF Big Beluga CHoCH has **|delta| ≥ 2000 contradicting** the intended trade direction (LONG + δ ≤ −2K · SHORT + δ ≥ +2K), the setup is auto-skipped with a single-line `SKIP[massive_contra_delta]`. Rationale: a 2K+ institutional print against the direction is a direct flow disconfirmation that overrides the structural signal.

### Daily loss circuit-breaker — 3 consecutive SLs
If **3 trades in the current session hit their hard SL consecutively** (no winners in between), stop firing for the remainder of that session. Manage any still-open trade to completion, but do not open new positions until next session. Resets at the next 08:30 CT session open.

### HTF cache must be bar-time keyed
HTF bias reads are cached, but the cache key is the **replay bar timestamp**, not wall-clock time. This prevents stale HTF reads during autoplay/backtest when the replay advances faster than the cache TTL would otherwise expect.

## Target rules

**Valid targets** for a trade can only be structural levels **opposite to the trade direction**:

**For LONG** (targets above entry):
- **Past Big Beluga swing highs** (indicator lines/levels marking historical bearish CHoCHs)
- **LuxAlgo Session HIGHs** ⭐ (Session A/B/C/D Maximum — **large liquidity pools, high priority when available in favor of the trade**)
- Visible swing highs on chart
- Time Cycles box highs (10min, 30min, 90min, session)
- PDH (Previous Daily High)
- PWH (Previous Weekly High)
- PMH (Previous Monthly High)

**For SHORT** (targets below entry):
- **Past Big Beluga swing lows** (indicator lines/levels marking historical bullish CHoCHs)
- **LuxAlgo Session LOWs** ⭐ (Session A/B/C/D Minimum — **large liquidity pools, high priority when available in favor of the trade**)
- Visible swing lows on chart
- Time Cycles box lows (10min, 30min, 90min, session)
- PDL, PWL, PML

**Priority order** when multiple valid targets exist:
1. LuxAlgo Session highs/lows (greatest institutional liquidity)
2. Past Big Beluga swing highs/lows (structural markers)
3. Time Cycles box extremes (TBL)
4. PDH/PDL/PWH/PWL/PMH/PML
5. Other price-action swing highs/lows

**Prohibited as target**: VWAP, SVWAP bands, Midnight Open, 09:30 Open, arbitrary levels, non-structural pivots.

**Quality constraints on chosen T1/T2/T3**:
- Each target must correspond to an **intact** structural swing — a level that has **not yet been liquidated** by subsequent price action. Already-swept swings are not valid targets (liquidity is gone).
- T1/T2/T3 must have **adequate spacing** between them. If two candidate levels are clustered (e.g., T2 and T3 within a few ticks), collapse them: use only the first as the final target and omit the redundant one.
- **Confluence priority** — when multiple intact levels stack, prefer the one that also coincides with a Time Cycles box edge, a LuxAlgo Session high/low, or a PDH/PDL/PWH/PWL/PMH/PML. Confluence adds liquidity depth and improves fill probability.
- **T1-only mode** — if only a single structurally valid target exists between entry and the next distant level, fire with T1 only (no T2/T3). The execution model then treats the trade as a **100% exit at T1** (see Execution model below).

## Execution model — limit orders at targets

Every target is a **simulated limit order that fills the instant price touches the level intrabar** (high ≥ T for LONG · low ≤ T for SHORT). There is no delay, no wait for bar close, no re-evaluation — a touch = a fill, at exactly the target price.

### Partial exit schedule by target count

| Mode | Target count | Allocation |
|---|---|---|
| **T1-only** | Single T (T2/T3 collapsed or omitted) | 100% at T1 |
| **T1 + T2** | Two structural targets | 50% at T1 · 50% at T2 |
| **T1 + T2 + T3** | Three structural targets | ⅓ at T1 · ⅓ at T2 · ⅓ at T3 |

### Stop-loss management

- **Pre-T1** — hard SL at the CHoCH circle + 2-tick margin. Full position exits here if hit before any target fills.
- **After T1 fills — runner trails to breakeven (BE)**. The moment T1 fills on any contract, the SL for all remaining runners moves to entry price. If price pulls back and touches BE after T1, the runner exits at **$0 P&L** (no re-risk of realized T1 gain).
- **After T2 fills** (3-target mode) — runner SL trails to T1 level (lock in first partial).
- **Never move SL further away from entry**. SL only tightens.

### P&L accounting

Authoritative trade P&L is the **sum of partial-fill P&L per leg**, computed as `(fill_price − entry) × $2/pt × contracts` per leg, with sign flipped for SHORT. The informational monitor loop in `recon_batch.sh` is naive (it reports the first hit event regardless of sequence) — the trade journal in `logs/recon_live.jsonl` and the final SQLite table reflect the authoritative partial-fill model above.

## Grading system

| Grade | Criterion | Cap % equity |
|---|---|---|
| **A+** | Setup 2 (Reversal pro-HTF) with 100% checklist + defined HTF bias + strong Big Beluga delta aligned | **0.75%** |
| **A** | Setup 1 (Continuation) with 100% checklist · or Setup 2 without strong delta | **0.50%** |
| **B** | Any setup with 1 warning (LTF outside ideal band, weak delta, non-optimal timing) | **0.25%** |
| **C** | Setup on NEUTRAL bias · or 2+ warnings | **0.10%** or skip |

> Setup 3's former "max B" cap is moot — S3 is disabled.

**RR does NOT affect grade quality.** RR_T1 ≥ 1 is the hard validity filter (RR < 1 → skip). Beyond that, RR is purely a reward/risk report — it does not degrade a clean setup's grade.

**Key rules**:
- NY Continuation (Setup 1) is never A+ — maximum A. Only Reversals (Setup 2) can be A+.
- **Setup 3 (contra-HTF) — disabled.** No grading applies.
- **RR is measured to T1** (entry → T1 partial), not to the final target. **T2/T3 have no minimum** — they can be 1-2× or higher, purely reporting.
- **RR_T1 ≥ 1** is valid to execute a setup. RR_T1 < 1 → skip (no trade).
- **RR does NOT affect grade**: a clean Setup 2 with RR_T1 = 1.2 is still A+ if structure + delta + checklist are 100%. Grade is about *setup quality*, not reward magnitude.

**LTF (1min) delta direction — adds points to grading**:

The Big Beluga CHoCH delta on 1min is a variable **distinct** from CHoCH direction, but it does affect classification:

- **Delta aligned with trade direction** (LONG + positive delta · SHORT + negative delta) → **quality boost**, can raise grade within the allowed cap.
- **Delta contradicting trade direction** (LONG + negative delta · SHORT + positive delta) → **degrades grade** (e.g.: A+ → A, A → B, B → C).
- **Very strong aligned delta** (|delta| ≥ 2K) → confirms institutional conviction in the direction.
- **Neutral or weak delta** (|delta| < 500) → does not affect grade positively or negatively.

## Sizing — Kelly Criterion

Base: **5% of pure Kelly**, capped by grade.

Kelly formula: `f* = (b·p − q) / b` · where `b` = RR ratio, `p` = win prob., `q = 1−p`.

Typical inputs:
- `p` base per setup:
  - Setup 1: 0.55
  - Setup 2: 0.52
  - Setup 3: 0.50
- Adjustments:
  - +0.03 if Big Beluga delta ≥ |+500|
  - +0.05 if Big Beluga delta ≥ |+2000| (massive)
  - −0.03 if grade degrades (A→B, B→C)

**Final sizing** = min(5% × pure Kelly, cap by grade)

## Drawings when validating a setup

When a setup activates, draw on the chart:

| Element | Type | Color | Label |
|---|---|---|---|
| Entry | horizontal_line | #000000 (black) | "Entry" |
| SL | horizontal_line | #000000 | "SL" |
| T1 (partial 1) | horizontal_line | #000000 | "T1" |
| T2 (partial 2) | horizontal_line | #000000 | "T2" |
| T3 (final target) | horizontal_line | #000000 | "T3" |

All with `linewidth: 2`. Targets numbered in ascending order of distance from entry.

## Commands

### `Recon Backtesting`

Use in TradingView replay mode. Starts from the current replay point · step "Next Bar" (Shift+Right) every 1 second.

For each bar:
- If **no setup**: 1 status line (time, price, SD distance, brief observation)
- If **setup validated**: **stop stepping** · provide complete analysis:
  - Setup checklist
  - Parameters (entry/stop/targets with RR)
  - Kelly Criterion with suggested sizing (capped)
  - Draw black horizontal lines on chart (Entry/SL/T1/T2/T3…)
  - **Send Telegram notification** (see Telegram section)
  - Wait for user input before continuing

### `Recon Live`

Same procedure as `Recon Backtesting` but using real-time data (no replay mode). Live monitoring of the current bar.

## Telegram — Notification on setup validation

Credentials in project `.env`:
- `TELEGRAM_BOT_TOKEN` — bot token (via @BotFather)
- `TELEGRAM_CHAT_ID` — destination chat_id

### Sending

When validating a setup, after drawing the lines and presenting the analysis, send a Telegram message with:
- Setup type (1/2/3) + direction (LONG/SHORT)
- Grade (A+/A-)
- Entry · SL · T1 · T2 · T3
- RR per target
- Recommended sizing (% equity)
- Bar timestamp (NY time)

### Message format

```
🎯 SETUP N · LONG/SHORT · Grade {A+ | A | B | C}
🕐 HH:MM NY · {symbol}

Entry: {price}
SL:    {price}  ({risk} pts)
T1:    {price}  (RR {rr1})
T2:    {price}  (RR {rr2})     ← omit if T1-only mode
T3:    {price}  (RR {rr3})     ← omit if T1-only or 2-target mode

Size:  {%} of equity (Kelly capped)
```

### Sending mechanism

From Bash:
```bash
source .env
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d chat_id="${TELEGRAM_CHAT_ID}" \
  -d text="<message>" \
  -d parse_mode="Markdown"
```

### Inbound commands (Telegram → Claude)

You can trigger actions by messaging the bot (@lukacs_agentic_bot) directly. A poller (`scripts/telegram_recon_listener.sh`) watches for these commands while Claude's session is active.

| Telegram message (case-insensitive) | Action | Path |
|---|---|---|
| `Recon Backtesting` · `/recon_backtesting` | Start step-by-step replay analysis (LLM-driven) | LLM |
| `Recon Backtesting Fast` | Same, but code-based setup detection (A/B path) | Script (planned) |
| `Recon Live` · `/recon_live` | Start live-data monitoring (LLM-driven) | LLM |
| `Recon Live Fast` | Same, but code-based setup detection (A/B path) | Script (planned) |
| `HTF` · `bias` | Reply with current HTF bias (4-element voting) | `scripts/status_snapshot.py htf` |
| `LTF` | Reply with current LTF state (SD distance, band, latest CHoCH) | `scripts/status_snapshot.py ltf` |
| `Status` | Reply with both HTF + LTF summary | `scripts/status_snapshot.py all` |

**Status commands bypass the LLM** — a deterministic Python script reads the chart via the `tv` CLI, computes the vote, and posts to Telegram directly (≈1.5s end-to-end vs ≈20s via LLM).

**Limitation**: only works while Claude's session is active. If the session is off, commands are queued (Telegram retains messages for 24h) and processed at next session start.
