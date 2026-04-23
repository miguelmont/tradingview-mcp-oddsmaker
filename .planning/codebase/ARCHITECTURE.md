# Architecture

**Last updated:** 2026-04-23
**Project:** `tvmcpserver` — TradingView MCP bridge + Python/Bash trading workflow
**Paradigm:** brownfield, two-component system

---

## 1. Pattern

**MCP server + thin scripts client.**

- A long-running **Node/ESM MCP server** (`tradingview-mcp/src/server.js`) speaks the Model Context Protocol over stdio and exposes ~78 tools that manipulate a live TradingView Desktop chart via the Chrome DevTools Protocol (CDP).
- A small set of **Bash/Python scripts** in `scripts/` act as a client layer *around* the MCP server: they shell out to the same codebase through its CLI front-end (`tradingview-mcp/src/cli/index.js`, aliased `tv`) and glue it to Telegram, disk logs, and local JSON state.
- Claude (the human's agent) orchestrates both: it reads chart state through MCP tools, makes trading decisions, then invokes `scripts/fire_setup.sh` as the final atomic "fire" action.

No web server, no database. Everything is stdio, filesystem, and CDP eval over localhost:9222.

---

## 2. Layers

```
┌───────────────────────────────────────────────────────────────┐
│  Claude Code (LLM orchestrator, reads docs/ + MEMORY.md)      │
└─────────────────┬─────────────────────────────┬───────────────┘
                  │ MCP (stdio JSON-RPC)        │ Bash exec
                  ▼                             ▼
┌────────────────────────────────────┐  ┌──────────────────────┐
│  tools/   (MCP tool registrations) │  │  scripts/            │
│  cli/     (CLI command routing)    │  │  - fire_setup.sh     │
│           ↓ both call into ↓       │  │  - telegram_recon_*  │
│  core/    (business logic, pure-ish)│ └──────┬───────────────┘
│  connection.js  (CDP singleton)    │        │ shells out to
└──────────────────┬─────────────────┘        │  `node tradingview-mcp/
                   │  Runtime.evaluate        │   src/cli/index.js`
                   ▼                          │
            ┌────────────────┐  ←─────────────┘
            │  CDP :9222     │
            │  (localhost)   │
            └────────┬───────┘
                     ▼
            ┌────────────────────┐
            │ TradingView        │
            │ Desktop (Electron) │
            │ — Pine indicators, │
            │   drawings, quotes │
            └────────────────────┘
```

**Layer responsibilities:**

| Layer | Path | Role |
|---|---|---|
| Transport | `tradingview-mcp/src/server.js`, `src/cli/index.js` | Dual front-end: MCP stdio server **or** `tv` CLI. Both thin. |
| Tools (MCP) | `tradingview-mcp/src/tools/*.js` | Zod-schema wrappers around core. Register with `McpServer`. |
| CLI | `tradingview-mcp/src/cli/commands/*.js` | `parseArgs`-based subcommand routing. Calls same core. |
| Core | `tradingview-mcp/src/core/*.js` | Business logic. Builds JS expression strings, calls `evaluate()`. |
| Connection | `tradingview-mcp/src/core/connection.js` | CDP singleton, retry/backoff, `safeString`, `requireFinite`. |
| Client scripts | `scripts/*.sh`, `scripts/*.py` | Trade firing, Telegram listener/parser. Uses `tv` CLI + curl. |
| Strategy knowledge | `docs/my-strategy.md`, `docs/strategy-memory/` | Read by Claude at runtime; not code. |

---

## 3. Data Flow

### 3.1 Read path (Claude reads chart state)

1. User prompt → Claude decides it needs chart data.
2. Claude calls MCP tool (e.g. `data_get_pine_labels`, `data_get_pine_lines`, `chart_get_state`).
3. Tool wrapper in `src/tools/data.js` validates args with Zod, calls into `src/core/data.js`.
4. Core constructs a JavaScript expression string that walks TradingView's internal object graph (see `connection.js` `KNOWN_PATHS`, e.g. `window.TradingViewApi._activeChartWidgetWV.value()`).
5. `connection.evaluate()` sends the expression to CDP `Runtime.evaluate` on port 9222.
6. TradingView Electron process executes the JS in-page, returns the value.
7. Tool returns JSON to Claude over stdio.

Pine-indicator reads specifically traverse:
`study._graphics._primitivesCollection.dwglines.get('lines').get(false)._primitivesDataById`
and the analogous path for labels/tables/boxes. This is why the indicator must be **visible** on the chart — the graphics collection is only hydrated for rendered studies.

### 3.2 Fire path (Claude commits a trade)

1. Claude has validated a setup against `docs/my-strategy.md` rules + `MEMORY.md` feedback files.
2. Claude invokes `bash scripts/fire_setup.sh --direction long --entry X --sl Y --t1 Z ...`.
3. `fire_setup.sh` runs Python-embedded assertions (direction order, tick-width risk, RR_T1 ≥ 1 unless `--force`).
4. For each of the 5 levels (Entry/SL/T1/T2/T3), it shells out:
   `node tradingview-mcp/src/cli/index.js draw shape --type horizontal_line --price <p> --time <now> --overrides '{"linecolor":"#000000",...}' --text "Entry|SL|T1|T2|T3"`.
5. CLI command `draw shape` → `core/drawing.js:drawShape` → CDP `createShape`; returns `entity_id` back through stdout JSON.
6. Script collects 5 entity IDs, aborts Telegram send if any are empty (readback guard).
7. Sources `.env`, `curl`s Telegram `sendMessage` with a Markdown-formatted `🎯 LABEL · Grade X` summary.
8. Appends one JSONL line to `logs/recon_live.jsonl` (ts, label, direction, grade, entry/sl/targets, RRs, draw_ids).
9. Writes `.active_trade.json` at the repo root for subsequent monitoring/exit logic.

### 3.3 Telegram command path (remote control)

1. `scripts/telegram_recon_listener.sh` runs in a terminal (or under a supervisor), long-polls `https://api.telegram.org/bot$TOKEN/getUpdates` with `timeout=30`.
2. Each response batch is piped to `scripts/telegram_recon_parse.py`.
3. The parser filters by `TARGET_CHAT`, normalizes text, and either:
   - **Short-circuits status commands** (`htf` / `ltf` / `status`) by `Popen`-ing a `scripts/status_snapshot.py` that posts directly to Telegram — no LLM round-trip. *(Note: `status_snapshot.py` is referenced but not present in current `scripts/`; it is a planned/expected sibling.)*
   - **Emits events** for Recon commands (`EVENT::recon_backtesting::...`, `EVENT::recon_live::...`, plus `_fast` variants) on stdout for Claude to consume.
4. Offset is persisted at `/tmp/tv_recon_offset_<chat_id>.txt` to avoid re-processing.

---

## 4. Abstractions

### 4.1 `connection.js` — the CDP singleton

The whole server is structured around a single lazy-initialized CDP client:

- `getClient()` reuses an existing client after a `Runtime.evaluate('1')` liveness ping; reconnects with exponential backoff otherwise.
- `findChartTarget()` picks the first `type: 'page'` target whose URL matches `tradingview.com/chart`.
- `evaluate(expr, { awaitPromise })` is the single choke-point for all in-page JS execution. Every core module uses it.
- `safeString(s)` / `requireFinite(n, name)` are defensive helpers used whenever user-supplied values are interpolated into eval strings — prevents injection and NaN-persisting-to-cloud bugs.
- `KNOWN_PATHS` is a hand-curated dictionary of TradingView internal API paths discovered via live probing. This is the load-bearing "reverse-engineering" asset of the whole project.

### 4.2 Tools ↔ Core split

Every capability has a matched pair:
- `src/tools/<area>.js` — MCP `server.tool(name, description, zodSchema, handler)` registration. Thin.
- `src/core/<area>.js` — the actual implementation. Exports named async functions.

The CLI layer (`src/cli/commands/<area>.js`) imports the **same `core`**, wrapping it for `tv <area> <subcmd>` invocation. This is why `fire_setup.sh` can shell out to `node tradingview-mcp/src/cli/index.js draw shape ...` and get the same behavior Claude would get via `mcp__tradingview__draw_shape` — they share the core.

### 4.3 Strategy memory

`docs/strategy-memory/MEMORY.md` + `feedback_*.md` files are an append-only knowledge base. They are loaded into Claude's system context per session (see user's auto-memory injection) and encode trading-rule evolution (lunch-hour chop filter, daily loss circuit breaker, Setup 3 disabled, etc.). Code does **not** read these — only the LLM does. This keeps strategy policy out of the executable path.

### 4.4 "Fire script is pure assertion + side-effect"

`fire_setup.sh` has no decision logic. It:
- Asserts geometric ordering of levels.
- Asserts minimum tick risk.
- Asserts RR_T1 ≥ 1 (or `--force`).
- Draws, reads back, notifies, logs.

All setup-grading, bias analysis, sweep detection, etc., live in Claude's reasoning + `docs/my-strategy.md`. This boundary is deliberate and called out in the script header ("NO decision logic. Caller has already validated.").

---

## 5. Entry Points

| Entry | Kind | How invoked | Purpose |
|---|---|---|---|
| `tradingview-mcp/src/server.js` | Node ESM | `node …/server.js` (via `.mcp.json` `command`) | MCP stdio server; registers 14 tool groups. |
| `tradingview-mcp/src/cli/index.js` | Node ESM shebang | `node …/cli/index.js <cmd>` (or `tv <cmd>` if `npm link`'d) | CLI front-end sharing `core/`. |
| `scripts/fire_setup.sh` | Bash | `bash scripts/fire_setup.sh --direction … --entry …` | Atomic trade firing: draw + telegram + log. |
| `scripts/telegram_recon_listener.sh` | Bash | Long-running background process | Long-polls Telegram, emits events / triggers status scripts. |
| `scripts/telegram_recon_parse.py` | Python | stdin from listener | Classifies Telegram messages → events or fire-and-forget status jobs. |
| `tradingview-mcp/scripts/launch_tv_debug_mac.sh` | Bash | Manual | Launches TradingView Desktop with CDP port 9222 enabled. |

### 5.1 MCP registration (`.mcp.json`)

```json
{
  "mcpServers": {
    "tradingview": {
      "command": "node",
      "args": ["/Users/miguelmont/Documents/ClaudeProjects/tvmcpserver/tradingview-mcp/src/server.js"]
    }
  }
}
```

Claude Code reads this on startup and spawns the server as a child process.

### 5.2 Tool-group registration (in `server.js`)

`registerHealthTools`, `registerChartTools`, `registerPineTools`, `registerDataTools`, `registerCaptureTools`, `registerDrawingTools`, `registerAlertTools`, `registerBatchTools`, `registerReplayTools`, `registerIndicatorTools`, `registerWatchlistTools`, `registerUiTools`, `registerPaneTools`, `registerTabTools` — each is imported from `src/tools/<area>.js` and called against the `McpServer` instance.

---

## 6. Module Boundaries

| Boundary | Crosses? | Notes |
|---|---|---|
| `tradingview-mcp/` ↔ `scripts/` | Yes, via CLI | `scripts/fire_setup.sh` shells out to `node tradingview-mcp/src/cli/index.js`. It does **not** import JS. This is the ONLY cross-boundary call. |
| `tradingview-mcp/` ↔ `docs/` | No | `tradingview-mcp/` never reads `docs/`. Strategy policy is Claude-only. |
| `scripts/` ↔ `docs/` | No | Scripts are policy-free mechanics. |
| `tools/` ↔ `core/` | Yes, one-way | Tools import core. Core never imports tools. |
| `cli/commands/` ↔ `core/` | Yes, one-way | Same pattern as tools. |
| `core/*.js` ↔ `core/connection.js` | Yes | All core modules import `evaluate`, `getChartApi`, `safeString`, `requireFinite`. |
| `core/*.js` ↔ `core/*.js` | Rarely | Most core modules are independent. Exception: `stream.js` composes data/drawing. |

**gitignore note:** `tradingview-mcp/` is listed in `.gitignore`. It is an unpackaged vendored dependency read from disk — treat it as third-party even though it's local. Do not edit casually; changes are not tracked by the outer repo's git.

---

## 7. Key Cross-Cutting Concerns

- **Error handling:** every MCP tool wraps its core call in `try/catch` and returns `jsonResult({ success: false, error: err.message }, true)`. CLI handler (`router.js:handleError`) distinguishes connection failures (exit 2) from other errors (exit 1).
- **Context-size discipline:** the server's `instructions` string and `tradingview-mcp/CLAUDE.md` both push Claude toward `summary=true`, `study_filter=...`, `verbose=false`, and screenshots over raw data — the codebase is explicitly designed around LLM context limits.
- **Secrets:** `.env` (gitignored) holds `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`. Only `fire_setup.sh` and `telegram_recon_listener.sh` source it.
- **State files at repo root:**
  - `.active_trade.json` — current live trade snapshot, written by `fire_setup.sh`.
  - `.htf_cache.json` — cached higher-timeframe bias (votes, tally, delta) used by status snapshot logic.
  - `logs/recon_live.jsonl` — append-only decision journal, one JSON object per fired setup.

---

## 8. What's Intentionally Absent

- **No database.** JSONL + flat JSON files only.
- **No test harness inside `tradingview-mcp/`-scope for scripts.** `tests/test_bar_read.py` is the only external test, focused on bar reading.
- **No queue / no broker.** Single-user, single-chart, synchronous.
- **No Setup 3.** Per `MEMORY.md` → `feedback_s3_disabled.md`, S3_REVERSAL_CONTRA is disabled at the policy layer (not the code layer).
