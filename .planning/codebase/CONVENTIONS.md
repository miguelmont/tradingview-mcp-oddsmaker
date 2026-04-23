# Conventions

`Last updated: 2026-04-23`
`Scope: /Users/miguelmont/Documents/ClaudeProjects/tvmcpserver`

This document captures the de-facto conventions observed in the post-cleanup
repo. The codebase is intentionally small (three scripts + docs + a gitignored
TS subtree), so conventions here are descriptive (what the code actually does)
rather than aspirational.

## 1. Directory layout

| Path | Purpose |
| --- | --- |
| `scripts/` | Executable entrypoints (bash + python). One responsibility per file. |
| `docs/` | Human-authored documentation. |
| `docs/strategy-memory/` | Feedback/decision notes — YAML frontmatter + markdown body. |
| `tradingview-mcp/` | TS sources for the TradingView MCP CLI. Gitignored (`.gitignore:6`). |
| `tests/` | Python test suite (currently stale — see `TESTING.md`). |
| `tests/fixtures/` | Captured TradingView JSON payloads used as test inputs. |
| `logs/` | Runtime JSONL journals (`recon_live.jsonl` etc.). Gitignored. |
| `.planning/` | GSD planning artifacts — not runtime code. |

Runtime state files live at the repo root and are gitignored:
`.env`, `.htf_cache.json`, `.active_trade.json`.

## 2. File naming

- **Bash scripts**: lower `snake_case.sh`, domain-prefixed.
  - `fire_*` — atomic actions that mutate external state (draw + Telegram + log).
  - `telegram_*` — Telegram I/O (polling, parsing).
  - `recon_*` — reconnaissance tick/analysis loops (referenced in MEMORY; not
    all present in current tree).
- **Python modules**: lower `snake_case.py`, matching the bash prefix when
  paired (`telegram_recon_listener.sh` ↔ `telegram_recon_parse.py`).
- **Tests**: `test_<module>.py` mirroring the module under test.
- **Docs**: `kebab-case.md` for top-level docs (`my-strategy.md`); feedback
  notes use `feedback_<topic>.md` under `docs/strategy-memory/`.

## 3. Bash script conventions

Every bash script in `scripts/` follows the same skeleton. See
`scripts/fire_setup.sh:1-23` as the canonical example.

### 3.1 Header

```bash
#!/bin/bash
# <name.sh> — <one-line purpose>.
# <multi-line description: what it does, what it does NOT do>.
#
# Assertions (abort if violated):
#   - <invariant 1>
#   - <invariant 2>
#
# Usage:
#   name.sh --flag value ...
```

The shebang is always `#!/bin/bash` (not `/usr/bin/env bash`). The first
comment block documents contract + invariants + usage — no separate man page.

### 3.2 Strict mode

```bash
set -euo pipefail       # fire_setup.sh:22 — mutating scripts
set -u                  # telegram_recon_listener.sh:7 — long-running pollers
cd "$(dirname "$0")/.."
```

Rationale: `fire_setup.sh` must abort on any error (it moves money); the
listener uses `set -u` only so transient `curl` failures don't kill the poll
loop. Every script `cd`s to the repo root so relative paths (`.env`,
`logs/`, `tradingview-mcp/src/cli/index.js`) resolve consistently.

### 3.3 Argument parsing

Long flags only, parsed via a `while [[ $# -gt 0 ]]` + `case` loop. Unknown
flags exit with code `2` (usage error). Example: `scripts/fire_setup.sh:30-45`.

```bash
while [[ $# -gt 0 ]]; do
  case "$1" in
    --direction) DIRECTION="$2"; shift 2;;
    --dry-run)   DRY_RUN=1; shift;;
    *) echo "ERROR: unknown arg $1" >&2; exit 2;;
  esac
done
```

Required args are validated after parsing using indirect expansion
(`scripts/fire_setup.sh:48-53`):

```bash
for var in DIRECTION ENTRY SL T1 GRADE SIZE LABEL; do
  if [[ -z "${!var}" ]]; then
    echo "ERROR: missing required --${var,,}" >&2
    exit 2
  fi
done
```

Optional args may carry defaults (`T2`/`T3` fall back to `T1` —
`scripts/fire_setup.sh:55-60`).

### 3.4 Environment loading

`.env` is loaded via `set -a; source .env; set +a` so every KEY=VAL in the
file becomes an exported env var. Scripts must `[[ -f .env ]]`-guard before
sourcing (`scripts/fire_setup.sh:149-152`) or `[ -z "${VAR:-}" ]`-check
after (`scripts/telegram_recon_listener.sh:14`). Missing credentials → exit
`1` for required, `WARN` + skip for optional features (telegram in
`fire_setup.sh`).

### 3.5 Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success (including `--dry-run`). |
| `1` | Assertion failure or runtime error (missing env, API failure). |
| `2` | Usage error (unknown flag, missing required arg). |
| `3` | External side-effect failed after partial progress (e.g., draw call returned empty `entity_id`; see `scripts/fire_setup.sh:140-145`). |

### 3.6 External command indirection

Repeated CLI invocations are aliased to a variable to keep lines readable and
to make substitution trivial in tests:

```bash
TV="node tradingview-mcp/src/cli/index.js"
$TV draw shape --type horizontal_line ...
```

(`scripts/fire_setup.sh:123`, `:128`)

## 4. Python conventions

Three styles coexist, each chosen for a reason.

### 4.1 Inline heredoc (embedded in bash)

Used when the bash script needs float math, JSON manipulation, or
structured assertions. Example: `scripts/fire_setup.sh:63-95`:

```bash
ASSERT_OUTPUT=$(python3 - <<PY
import sys
entry, sl, t1, t2, t3 = ${ENTRY}, ${SL}, ${T1}, ${T2}, ${T3}
errors = []
if direction == "long":
    if not (sl < entry < t1 <= t2 <= t3):
        errors.append(f"LONG order invalid: ...")
if errors:
    for e in errors:
        print(f"ASSERT_FAIL: {e}", file=sys.stderr)
    sys.exit(1)
print(f"RR_T1={rr_t1:.2f}")
PY
)
eval "$ASSERT_OUTPUT"
```

Rules:
- Heredoc delimiter is `PY` (not `EOF`) so it visually flags the language switch.
- Prints `KEY=VALUE` lines on stdout that the caller consumes via `eval`.
- Prints `ASSERT_FAIL: <reason>` on stderr and `sys.exit(1)` on violation.
- Interpolates bash variables with `${VAR}`. Never quote numeric inputs —
  they must parse as Python literals.

### 4.2 Standalone script

Used when the logic is larger or reused. Example:
`scripts/telegram_recon_parse.py`.

- Shebang `#!/usr/bin/env python3`.
- Module docstring describes contract + side effects (e.g., "short-circuits
  HTF/LTF; emits `EVENT::<kind>::<text>` for recon commands").
- `from pathlib import Path`; compute `ROOT = Path(__file__).resolve().parent.parent`
  for repo-root-relative paths.
- Type hints on public functions (`def run_status(mode: str) -> None`).
- Stdin/stdout/env-var IPC with the calling bash script — no argparse when
  the contract is fixed.
- Defensive JSON: wrap `json.load(sys.stdin)` in `try/except` and return
  silently on malformed input (`telegram_recon_parse.py:40-45`) so a flaky
  Telegram response doesn't kill the poll loop.

### 4.3 Minimum Python version

`python3` (whatever is on PATH). f-strings and the walrus operator are in
use, so ≥3.8 is assumed. No `requirements.txt` — scripts rely on stdlib
only (`json`, `re`, `subprocess`, `pathlib`, `os`, `sys`, `time`).

## 5. Error handling patterns

### 5.1 Assertion-first

Mutating scripts assert invariants before any side effect. `fire_setup.sh`
validates direction, price ordering, tick risk, and RR_T1 in Python **before**
drawing a single line (`scripts/fire_setup.sh:62-100`). Assertions that fail
produce `ASSERT_FAIL: <specific reason>` on stderr and exit `1` — the caller
knows nothing external was mutated.

### 5.2 Readback after side effect

After drawing lines, `fire_setup.sh:140-145` iterates every captured
`entity_id` and aborts with exit `3` if any is empty. Telegram is **not**
sent until readback passes — this is the invariant stated in the header
comment ("If not, aborts Telegram send."). Pattern: mutate → verify →
announce.

### 5.3 Graceful optional-path skips

When a feature is nice-to-have, skip with `WARN` to stderr and continue:

```bash
if [[ ! -f .env ]]; then
  echo "WARN: .env not found, skipping telegram" >&2
else
  ...
fi
```

(`scripts/fire_setup.sh:149-170`)

### 5.4 Long-running loop resilience

`telegram_recon_listener.sh:37-39` uses `|| true` on the `curl` call so a
transient network blip doesn't trip `set -u` / end the process. The Python
parser consumes whatever (possibly empty) response arrived. Loop continues.

## 6. Logging

- **Human output**: stdout, decorated with box-drawing characters for the
  fire banner (`scripts/fire_setup.sh:102-115`: `─── fire_setup.sh ──...`).
- **Warnings / errors**: stderr, prefixed with `ERROR:`, `WARN:`, or a
  bracketed subsystem tag (`[listener] ready ...`).
- **Decision journal**: append-only JSONL under `logs/` (gitignored). One
  event per line, UNIX-epoch `ts`, structured fields only — no free-form
  strings. Written via heredoc Python for precise quoting
  (`scripts/fire_setup.sh:174-188`).
- **State snapshots**: small single-JSON files at repo root
  (`.active_trade.json`, `.htf_cache.json`) — latest-wins, overwritten atomically.

## 7. Markdown conventions

### 7.1 Strategy memory files (`docs/strategy-memory/feedback_*.md`)

YAML frontmatter is required. Canonical shape (see
`docs/strategy-memory/feedback_sweep_inside_band.md:1-6`):

```yaml
---
name: <short title>
description: <one-paragraph rule statement>
type: feedback
originSessionId: <uuid of the conversation that produced the rule>
---
```

Body uses bold section labels (`**Scope**`, `**Why:**`, `**How to apply:**`)
followed by bullet lists. Quoted numeric evidence (prices, sigmas, NY times)
is preserved verbatim so future sessions can audit the precedent.

### 7.2 Top-level docs (`docs/*.md`)

No frontmatter. Use `#` H1 for title, `##` for sections, tables for
structured data, fenced code blocks with language tag. `README.md` is
intentionally minimal.

## 8. TypeScript (gitignored subtree)

`tradingview-mcp/` is vendored/built externally and invoked as a binary:
`node tradingview-mcp/src/cli/index.js`. Conventions for that subtree are
out of scope here — the repo treats it as an opaque dependency. Do not
add source files that assume the subtree layout; always go through the
CLI JSON contract.

## 9. Quick reference — adding a new script

1. Choose a domain prefix: `fire_`, `telegram_`, `recon_`, or add a new one
   documented here.
2. Start from the `fire_setup.sh` skeleton: shebang, header block with
   Assertions + Usage, `set -euo pipefail`, `cd "$(dirname "$0")/.."`.
3. Long-flag argparse + indirect-expansion required-check.
4. Guard `.env` load, check required env vars, exit `1` if missing.
5. Assert invariants in a Python heredoc before any side effect.
6. Readback any external mutation; abort before the next stage if readback
   fails.
7. Append one JSONL line to `logs/<script>.jsonl` per successful run.
8. Document exit codes in the header.
