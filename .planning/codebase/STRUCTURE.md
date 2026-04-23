# Structure

**Last updated:** 2026-04-23
**Project:** `tvmcpserver`
**Repo root:** `/Users/miguelmont/Documents/ClaudeProjects/tvmcpserver`

---

## 1. Top-Level Directory Layout

```
tvmcpserver/
├── .claude/                    # Claude Code local settings (gitignored)
│   ├── scheduled_tasks.lock
│   └── settings.local.json
├── .planning/                  # Planning artifacts (this folder)
│   └── codebase/
│       ├── ARCHITECTURE.md
│       └── STRUCTURE.md
├── .git/                       # Outer repo git state
├── .env                        # Telegram secrets (gitignored)
├── .gitignore                  # Excludes .env, tradingview-mcp/, logs/, .htf_cache.json
├── .mcp.json                   # Claude Code MCP registration
├── .htf_cache.json             # Runtime: cached HTF bias snapshot (gitignored)
├── .active_trade.json          # Runtime: written by fire_setup.sh when a trade is live
├── README.md                   # One-liner only
├── docs/                       # Strategy documentation (read by Claude, not code)
│   ├── my-strategy.md
│   ├── backtest_report_2026-01-02_to_01-16.md
│   ├── strategy-memory/
│   │   ├── MEMORY.md
│   │   └── feedback_*.md       # 19 feedback files (one per rule)
│   └── superpowers/
├── logs/                       # Runtime: decision journal (gitignored)
│   └── recon_live.jsonl
├── scripts/                    # Bash/Python client layer
│   ├── fire_setup.sh           # Atomic trade firing (draw + telegram + log)
│   ├── telegram_recon_listener.sh
│   └── telegram_recon_parse.py
├── tests/                      # External project tests (mostly empty)
│   ├── fixtures/               # (empty)
│   └── test_bar_read.py        # Bar-reading test
└── tradingview-mcp/            # Vendored MCP server (gitignored by outer repo)
    ├── .git/                   # Its own inner git repo
    ├── CLAUDE.md               # Tool decision-tree doc (loaded into Claude context)
    ├── CONTRIBUTING.md
    ├── LICENSE
    ├── README.md
    ├── RESEARCH.md
    ├── SECURITY.md
    ├── SETUP_GUIDE.md
    ├── package.json            # name: tradingview-mcp, bin: tv
    ├── package-lock.json
    ├── node_modules/
    ├── agents/
    │   └── performance-analyst.md
    ├── skills/                 # Skill bundles for chart work
    │   ├── chart-analysis/
    │   ├── multi-symbol-scan/
    │   ├── pine-develop/
    │   ├── replay-practice/
    │   └── strategy-report/
    ├── scripts/                # Launcher helpers (per-OS)
    │   ├── launch_tv_debug_mac.sh
    │   ├── launch_tv_debug_linux.sh
    │   ├── launch_tv_debug.bat
    │   ├── launch_tv_debug.vbs
    │   ├── pine_pull.js
    │   └── pine_push.js
    ├── screenshots/             # capture_screenshot output (gitignored)
    ├── tests/                   # Node --test suites (e2e, cli, pine_analyze)
    └── src/                     # ← main source tree, see §2
```

---

## 2. `tradingview-mcp/src/` — Main Source Tree

```
src/
├── server.js                   # ENTRY: MCP stdio server (registers all tool groups)
├── connection.js               # CDP singleton, evaluate(), safeString, requireFinite, KNOWN_PATHS
├── wait.js                     # Polling/wait utilities
├── cli/
│   ├── index.js                # ENTRY: `tv` CLI (package.json bin)
│   ├── router.js               # parseArgs-based command dispatcher
│   └── commands/               # One file per command group (mirror of core/)
│       ├── alerts.js
│       ├── capture.js
│       ├── chart.js
│       ├── data.js
│       ├── drawing.js
│       ├── health.js
│       ├── indicator.js
│       ├── layout.js
│       ├── pane.js
│       ├── pine.js
│       ├── replay.js
│       ├── stream.js
│       ├── tab.js
│       ├── ui.js
│       └── watchlist.js
├── core/                       # Business logic (pure-ish, uses evaluate())
│   ├── index.js                # Barrel re-exports
│   ├── alerts.js
│   ├── batch.js
│   ├── capture.js
│   ├── chart.js
│   ├── data.js                 # ~21KB: OHLCV, pine lines/labels/tables/boxes, study values
│   ├── drawing.js              # drawShape, listDrawings, removeOne, clearAll
│   ├── health.js               # tv_launch, tv_health_check, tv_discover, tv_ui_state
│   ├── indicators.js
│   ├── pane.js
│   ├── pine.js                 # ~21KB: pine_set_source, pine_smart_compile, pine_get_* 
│   ├── replay.js
│   ├── stream.js               # ~11KB: composed data/drawing flows
│   ├── tab.js
│   ├── ui.js                   # ~16KB: ui_click, ui_evaluate, ui_find_element, etc.
│   └── watchlist.js
└── tools/                      # MCP tool registrations (thin wrappers around core/)
    ├── _format.js              # jsonResult() helper
    ├── alerts.js
    ├── batch.js
    ├── capture.js
    ├── chart.js
    ├── data.js
    ├── drawing.js
    ├── health.js
    ├── indicators.js
    ├── pane.js
    ├── pine.js
    ├── replay.js
    ├── tab.js
    ├── ui.js
    └── watchlist.js
```

**Symmetry rule:** `tools/<area>.js` and `cli/commands/<area>.js` both import `core/<area>.js`. If you add a capability, add it in `core/` first, then expose it in both `tools/` and `cli/commands/`.

---

## 3. Key Locations — "Where do I find…?"

| I want to… | Go to |
|---|---|
| Change what Claude sees when an MCP tool is called | `tradingview-mcp/src/tools/<area>.js` (description, Zod schema) |
| Change what the tool actually does on the chart | `tradingview-mcp/src/core/<area>.js` |
| Add a new CDP API path (internal TradingView object) | `tradingview-mcp/src/connection.js` → `KNOWN_PATHS` |
| Read Pine indicator drawings | `core/data.js` → `getPineLines`, `getPineLabels`, `getPineTables`, `getPineBoxes` |
| Draw on the chart | `core/drawing.js` → `drawShape` (shape types: `horizontal_line`, `trend_line`, `rectangle`, `text`) |
| Launch TradingView with CDP enabled | `tradingview-mcp/scripts/launch_tv_debug_mac.sh` (or `_linux.sh` / `.bat`) |
| Fire a validated trade | `scripts/fire_setup.sh` |
| Listen for Telegram commands | `scripts/telegram_recon_listener.sh` + `scripts/telegram_recon_parse.py` |
| Tune trading-rule policy (rules, filters) | `docs/my-strategy.md` + `docs/strategy-memory/feedback_*.md` |
| See recent fired trades | `logs/recon_live.jsonl` |
| Check what trade is currently live | `.active_trade.json` (repo root) |
| Configure MCP server for Claude Code | `.mcp.json` |
| Configure Telegram bot | `.env` |
| See backtest results | `docs/backtest_report_2026-01-02_to_01-16.md` |

---

## 4. Naming Conventions

### 4.1 MCP tool names

- **snake_case**, **namespace-prefixed** by area: `chart_get_state`, `data_get_pine_labels`, `pine_smart_compile`, `draw_shape`, `ui_click`, `replay_step`.
- Area prefixes: `chart_`, `data_`, `pine_`, `draw_`, `ui_`, `replay_`, `alert_`, `tab_`, `pane_`, `indicator_`, `layout_`, `watchlist_`, `quote_`, `depth_`, `symbol_`, `tv_`, `capture_`, `batch_`.
- Verb convention: `get_*` for reads, `set_*` for writes, `list_*` for enumeration, `create_*`/`delete_*` for lifecycle, action verbs (`click`, `scroll`, `step`, `start`, `stop`) for imperatives.

### 4.2 CLI commands

- Top-level command = area: `tv draw`, `tv chart`, `tv data`, `tv pine`, `tv replay`.
- Subcommand = verb: `tv draw shape`, `tv draw list`, `tv draw remove`, `tv draw clear`.
- Single-word areas use `--flag` options; positional args reserved for IDs (entity IDs, study names).

### 4.3 Core functions

- **camelCase**, short verb-object: `drawShape`, `listDrawings`, `getPineLines`, `getStudyValues`, `clearAll`.
- Dep injection pattern for tests: optional `_deps` parameter that defaults to real `evaluate`/`getChartApi` — see `core/drawing.js:drawShape`.

### 4.4 Scripts

- Bash scripts: `snake_case.sh`, imperative verb first: `fire_setup.sh`, `launch_tv_debug_mac.sh`, `telegram_recon_listener.sh`.
- Python helpers adjacent to their Bash caller, same stem: `telegram_recon_parse.py` ← called by `telegram_recon_listener.sh`.
- Every `scripts/*.sh` starts with `set -euo pipefail` and `cd "$(dirname "$0")/.."` so it runs from repo root regardless of cwd.

### 4.5 Feedback files (strategy memory)

- `docs/strategy-memory/feedback_<slug>.md`, snake_case slug describing the rule:
  `feedback_no_lunch_entries.md`, `feedback_sweep_inside_band.md`, `feedback_daily_loss_circuit_breaker.md`, `feedback_s3_disabled.md`.
- One rule per file, referenced by slug from `MEMORY.md`.

### 4.6 Runtime artifacts (repo root dotfiles)

- Cache / transient state starts with `.`: `.active_trade.json`, `.htf_cache.json`, `.env`.
- Append-only logs under `logs/`, extension `.jsonl` (one JSON object per line).
- Timestamps in logs are Unix seconds (`ts`). Human-formatted time only in Telegram messages (`NY_TIME`).

### 4.7 Entity IDs

- TradingView shape IDs come back from CDP as short random strings (e.g. `zXSxtC`, `thMFWZ`). Store them as strings. Do **not** parse or assume format. They are **session-specific** — don't cache across restarts.

---

## 5. File-Size Hotspots

| File | Size | Why |
|---|---|---|
| `tradingview-mcp/src/core/pine.js` | ~21 KB | Pine editor integration: set_source, compile, errors, console, save/load, REST facade. |
| `tradingview-mcp/src/core/data.js` | ~21 KB | All chart-read logic: OHLCV, pine graphics traversal, study values. |
| `tradingview-mcp/src/core/ui.js` | ~16 KB | Generic CDP UI interactions (click, find, evaluate). |
| `tradingview-mcp/src/core/stream.js` | ~11 KB | Composed flows (depends on data + drawing). |
| `tradingview-mcp/src/core/health.js` | ~11 KB | Cross-platform launcher + health-check logic. |
| `tradingview-mcp/CLAUDE.md` | ~7 KB | Tool decision-tree doc loaded into Claude context. |
| `docs/my-strategy.md` | ~20 KB | Full trading rulebook. |
| `scripts/fire_setup.sh` | ~7 KB | Only non-trivial script in `scripts/`. |

---

## 6. Tests

- **Outer repo:** `tests/test_bar_read.py` — isolated bar-reading test (~11 KB). `tests/fixtures/` is currently empty.
- **Inner repo (`tradingview-mcp/tests/`):** runs via `npm test` — three suites declared in `package.json`: `e2e.test.js`, `pine_analyze.test.js`, `cli.test.js`. Node's built-in `node --test` runner; no external framework.

---

## 7. Gitignore Surface

From `.gitignore` at repo root:

```
.env
.env.local
*.log
screenshots/
.claude/
tradingview-mcp/        ← the MCP server is NOT tracked by the outer repo
__pycache__/
*.pyc
/tmp/
.htf_cache.json
logs/
```

Implication: `tradingview-mcp/` has its own `.git/` and is effectively a **vendored, out-of-tree dependency** read from disk. The outer repo only tracks: `scripts/`, `docs/`, `tests/`, `.planning/`, `.mcp.json`, `README.md`, `.gitignore`. Treat edits inside `tradingview-mcp/` as you would edits to a submodule — they need to be committed in its own inner repo separately.
