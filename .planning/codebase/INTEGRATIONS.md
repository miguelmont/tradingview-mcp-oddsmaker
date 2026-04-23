# INTEGRATIONS

**Last updated**: 2026-04-23

External surfaces this project talks to. Three active integrations (Telegram, TradingView CDP, MCP stdio) and one manual-only integration (Forex Factory).

## 1. Telegram Bot API

**Purpose**: inbound command channel (user types `Recon Live`, `HTF`, etc.) and outbound trade alerts (formatted fire messages with entry/SL/targets).

### Endpoints used
| Method | URL | Called by |
|---|---|---|
| `GET` | `https://api.telegram.org/bot<TOKEN>/getUpdates?offset=<n>&timeout=30` (long-poll, 35s max) | `scripts/telegram_recon_listener.sh:37-39` |
| `GET` | `https://api.telegram.org/bot<TOKEN>/getUpdates` (prime offset once) | `scripts/telegram_recon_listener.sh:23` |
| `POST` | `https://api.telegram.org/bot<TOKEN>/sendMessage` with `chat_id`, `text`, `parse_mode=Markdown` | `scripts/fire_setup.sh:165-168` |

### Authentication
- **Bot token** — loaded from `.env` as `TELEGRAM_BOT_TOKEN`. Obtained from `@BotFather` (see inline `.env` comments).
- **Chat whitelist** — only `TELEGRAM_CHAT_ID` (numeric) is accepted; enforced in `scripts/telegram_recon_parse.py:52` (`if chat.get("id") != target_chat: continue`).

### Command grammar (parsed at `scripts/telegram_recon_parse.py:57-71`)
Normalized via `re.sub(r"[_/\-]+", " ", text).lower()`:
- `recon backtesting` → emits `EVENT::recon_backtesting::<raw>`
- `recon live` → emits `EVENT::recon_live::<raw>`
- same + word `fast` → `*_fast` variants
- `htf` / `bias` → spawns background `status_snapshot.py htf` (STALE: script deleted)
- `ltf` → spawns `status_snapshot.py ltf` (STALE)
- `status` → spawns `status_snapshot.py all` (STALE)

### Outbound message format (`fire_setup.sh:155-164`)
```
🎯 *<LABEL>* · Grade *<GRADE>*
🕐 <HH:MM> NY

Entry: <price>
SL:    <price>  (<risk_pts> pts)
T1:    <price>  (RR <rr>)
T2:    <price>  (RR <rr>)
T3:    <price>  (RR <rr>)

Size:  <size>% equity
```
HTTP status captured but non-fatal; logged as `Telegram: HTTP <code>`.

### Failure modes
- Missing `.env` → `fire_setup.sh:149-150` warns and skips Telegram but still draws + logs.
- Listener has no retry/backoff — relies on `sleep 1` between poll cycles (`telegram_recon_listener.sh:45`).

### Webhook status
**None configured.** Integration is pull-based long-polling only; no public endpoint exposed.

## 2. TradingView Desktop via Chrome DevTools Protocol (CDP)

**Purpose**: primary data + control plane. All chart reads (OHLCV, Pine outputs, indicator values), chart drawing, Pine editing, replay, and alerts flow through CDP into TradingView's embedded Chromium.

### Transport
- **Host/port**: `localhost:9222` (hardcoded at `tradingview-mcp/src/connection.js:5-6`)
- **Client**: `chrome-remote-interface` ^0.33.2 (npm)
- **Retries**: `MAX_RETRIES=5`, `BASE_DELAY=500ms` (`connection.js:7-8`)

### Prerequisites
- TradingView Desktop launched with `--remote-debugging-port=9222`. Helpers: `tradingview-mcp/scripts/launch_tv_debug_mac.sh`, `launch_tv_debug_linux.sh`, `launch_tv_debug.bat`, `launch_tv_debug.vbs`.
- MCP `tv_launch` tool can auto-start TV with proper flags; `tv_health_check` verifies the socket.

### API access paths (`connection.js:10-27`, KNOWN_PATHS)
Direct `Runtime.evaluate` hits on TradingView's private JS globals:
- `window.TradingViewApi._activeChartWidgetWV.value()` — chart API
- `window.TradingViewApi._chartWidgetCollection` — multi-pane enum
- `window.TradingView.bottomWidgetBar` — strategy tester / pine console
- `window.TradingViewApi._replayApi` — replay controls
- `window.TradingViewApi._alertService` — alerts CRUD
- Pine graphics: `study._graphics._primitivesCollection.dwglines.get('lines').get(false)._primitivesDataById`

### Secondary HTTP surface
- `https://pine-facade.tradingview.com/pine-facade` — Pine script list/save REST API (used inside the MCP `pine_*` tools). Auth is whatever cookie TradingView Desktop holds; the MCP server does not manage credentials.

### Tool surface exposed to Claude
78 MCP tools covering: `chart_*`, `data_get_*` (ohlcv, study_values, pine_lines/labels/tables/boxes, strategy_results, trades, equity, indicator, depth), `quote_get`, `symbol_*`, `draw_*`, `pine_*`, `replay_*`, `alert_*`, `ui_*`, `layout_*`, `pane_*`, `tab_*`, `watchlist_*`, `capture_screenshot`, `batch_run`, `tv_launch`, `tv_health_check`, `tv_discover`, `tv_ui_state`.

### Authentication
**None at transport layer.** CDP on `localhost:9222` is an unauthenticated local-only socket — anyone on the machine can control TradingView. TradingView's own cloud auth (account login) is handled inside the desktop app and not touched by this integration.

## 3. MCP stdio (Claude Code ↔ tradingview-mcp)

**Purpose**: the bridge that makes the 78 CDP tools callable from Claude.

- **Transport**: stdin/stdout pipe (spec: Model Context Protocol)
- **SDK**: `@modelcontextprotocol/sdk` ^1.12.1
- **Spawned by**: Claude Code via `.mcp.json` at repo root, `command: node`, `args: [tradingview-mcp/src/server.js]`
- **Auth**: none (local process, inherits user permissions)

## 4. Forex Factory XML (manual / not coded)

**Status**: referenced in strategy docs only; **no code path fetches it today**.

- Policy defined in `docs/strategy-memory/feedback_news_pause_red_only.md`: red-folder USD high-impact events → pause Recon Live from 5 min before to 5 min after. Orange events → no pause (per user directive 2026-04-23).
- Expected source: Forex Factory public calendar XML (e.g., `https://nfs.faireconomy.media/ff_calendar_thisweek.xml` — conventional URL, not pinned in code).
- **Current workflow**: operator pulls red events manually at session open and annotates the monitor log. Claude respects the window when evaluating fires.
- No fetch script, no caching layer, no scheduled job — candidate for future automation.

## 5. Pine Facade REST (transitive)

Reached indirectly through CDP when using `pine_list_scripts`, `pine_open`, `pine_save`. Not called from this repo's code directly — the requests originate from within TradingView Desktop itself using its own session cookie. Listed here for completeness.

## Webhooks / inbound HTTP

**None.** This project exposes no HTTP server. All inbound signals arrive via:
1. Telegram long-polling (outbound GET that blocks up to 30s)
2. MCP stdio from Claude Code
3. Local file reads (`.env`, `.htf_cache.json`, `.active_trade.json`, `logs/recon_live.jsonl`)

## Secrets inventory

| Secret | Location | Rotated via |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | `.env` (gitignored) | `@BotFather` → `/revoke`, paste new token |
| `TELEGRAM_CHAT_ID` | `.env` (gitignored) | N/A (stable user chat id) |
| TradingView account credentials | TradingView Desktop keychain (outside repo) | via TV UI |

No cloud IAM, no OAuth, no JWT, no API keys beyond the Telegram token.
