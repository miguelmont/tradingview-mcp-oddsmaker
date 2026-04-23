# STACK

**Last updated**: 2026-04-23
**Repo**: `tvmcpserver` (brownfield)
**Git branch**: `development`
**Project shape**: single-chart NQ1! trading strategy automation. A Node.js MCP server bridges Claude Code to TradingView Desktop over Chrome DevTools Protocol. Bash + Python scripts wrap the MCP CLI for trade firing, Telegram notifications, and command listening.

## Layout

```
tvmcpserver/
├── .env                      — secrets (Telegram bot token + chat id)  [gitignored]
├── .mcp.json                 — MCP server registration for Claude Code
├── .gitignore                — excludes .env, logs/, tradingview-mcp/, screenshots/, __pycache__, .htf_cache.json
├── .htf_cache.json           — cached HTF bias snapshot (runtime artifact)
├── README.md                 — one-line project title only
├── scripts/                  — strategy orchestration (bash + python)
│   ├── fire_setup.sh         — atomic trade-fire action (draw 5 lines + Telegram + JSONL log)
│   ├── telegram_recon_listener.sh   — long-polls Telegram getUpdates, emits EVENT:: lines
│   └── telegram_recon_parse.py      — parses Telegram JSON, filters by chat_id
├── docs/
│   ├── my-strategy.md        — master strategy spec (HTF bias, LTF state, S1/S2/S3 setups)
│   ├── backtest_report_2026-01-02_to_01-16.md
│   ├── strategy-memory/      — feedback_*.md (MEMORY.md-referenced persistent preferences)
│   └── superpowers/specs/    — skill specs
├── tests/
│   ├── test_bar_read.py      — unit tests for (now-deleted) CHoCH parser (legacy)
│   └── fixtures/             — captured TV output
├── logs/
│   └── recon_live.jsonl      — decision journal (one JSON per fired setup)
└── tradingview-mcp/          — Node.js MCP server  [gitignored; vendored submodule]
    ├── package.json
    ├── src/server.js         — MCP stdio server entry
    ├── src/cli/index.js      — `tv` CLI alias wrapping same tools
    ├── src/core/             — 16 modules (chart, data, drawing, pine, replay, ui, alerts, …)
    ├── src/connection.js     — CDP client (chrome-remote-interface)
    ├── tests/                — node --test e2e + unit tests
    └── scripts/              — OS-specific TradingView launch helpers (mac/linux/windows)
```

Recent deletions (tracked in git history) — `recon_batch.sh`, `recon_scan.sh`, `recon_tick.sh`, `bar_read.py`, `backtest_pipeline.py`, `backtest_v2.py`, `status_snapshot.py`. `telegram_recon_parse.py:18` still references `status_snapshot.py` (stale path, spawns would silently fail). `tests/test_bar_read.py:13` imports the deleted `bar_read`. Both should be cleaned up or rewritten.

## Languages & runtimes

| Language | Where | Runtime |
|---|---|---|
| JavaScript (ESM) | `tradingview-mcp/src/**/*.js` | Node.js (`"type": "module"`, uses top-level await; `node --test` for tests) |
| Python 3 | `scripts/telegram_recon_parse.py`, inline heredocs in `scripts/fire_setup.sh` (lines 63–95, 174–188) | CPython 3 (`python3` in PATH) |
| Bash | `scripts/fire_setup.sh`, `scripts/telegram_recon_listener.sh` | `/bin/bash` with `set -euo pipefail` |
| Pine Script | authored live in TradingView via MCP `pine_*` tools (no files in repo) | TradingView Desktop |

No `pyproject.toml`, `requirements.txt`, `setup.py`, or Python lockfile exists. Python code uses stdlib only (`json`, `os`, `re`, `subprocess`, `sys`, `pathlib`, `time`, `unittest`).

## Frameworks & libraries

### Node.js (`tradingview-mcp/package.json`)
- `@modelcontextprotocol/sdk` ^1.12.1 — MCP server framework (stdio transport)
- `chrome-remote-interface` ^0.33.2 — CDP client to drive TradingView's embedded Chromium

Dev: none declared. Tests use Node's built-in `node --test` runner (see `package.json:17-23`).

### Python
- Stdlib only. No external dependencies.

### Bash
- Uses `curl` (Telegram HTTP API), `python3` (inline float math + JSON), `date`, `tr`, standard coreutils.

## Config & environment

### `.env` (gitignored; schema at `/Users/miguelmont/Documents/ClaudeProjects/tvmcpserver/.env`)
```
TELEGRAM_BOT_TOKEN=<from @BotFather>
TELEGRAM_CHAT_ID=<numeric chat id>
```
Loaded by `scripts/telegram_recon_listener.sh:10-12` and `scripts/fire_setup.sh:152` via `set -a; source .env; set +a`.

### `.mcp.json` — Claude Code MCP registration
```json
{ "mcpServers": { "tradingview": {
    "command": "node",
    "args": ["/Users/miguelmont/.../tradingview-mcp/src/server.js"] } } }
```

### Chrome DevTools Protocol endpoint
- Host `localhost`, port `9222` (hardcoded at `tradingview-mcp/src/connection.js:5-6`)
- TradingView Desktop must be launched with `--remote-debugging-port=9222` (see `tradingview-mcp/scripts/launch_tv_debug_mac.sh` et al.)

### Runtime caches / state
- `.htf_cache.json` — HTF bias snapshot (keys: `price_1h`, `weekly`, `monthly`, `choch_1h`, `votes`, `tally`, `bias`, `_cached_*`)
- `.active_trade.json` — written by `fire_setup.sh:193-195` after each fire
- `/tmp/tv_recon_offset_<chat_id>.txt` — Telegram update cursor (`telegram_recon_listener.sh:19`)
- `logs/recon_live.jsonl` — append-only decision journal

## Scripts & entry points

| Entry | Purpose |
|---|---|
| `node tradingview-mcp/src/server.js` | MCP server (invoked by Claude Code via `.mcp.json`) |
| `node tradingview-mcp/src/cli/index.js` (a.k.a. `tv`) | same tools as CLI; used by `fire_setup.sh:123` |
| `scripts/fire_setup.sh` | validated trade fire (assertions → draw 5 lines → Telegram → JSONL) |
| `scripts/telegram_recon_listener.sh` | long-poll loop, writes `EVENT::kind::text` to stdout |
| `scripts/telegram_recon_parse.py` | helper invoked inside listener |
| `npm test` (inside `tradingview-mcp/`) | `node --test tests/e2e.test.js tests/pine_analyze.test.js` |

## Version control

- Git repo at repo root; `tradingview-mcp/` is itself a separate `.git` directory (vendored, excluded by `.gitignore`)
- User rule: no auto-commit (see MEMORY.md `feedback_no_auto_commit.md`)

## Known tech debt / drift

- `scripts/telegram_recon_parse.py:18` points to deleted `scripts/status_snapshot.py` — HTF/LTF/Status short-circuits in `main()` will silently fail to spawn.
- `tests/test_bar_read.py:13` imports deleted `scripts/bar_read.py` — test suite cannot run.
- `docs/my-strategy.md:6` still documents S3; per MEMORY, S3 is disabled at runtime.
- No Python packaging / lockfile; version drift possible on macOS system `python3`.
