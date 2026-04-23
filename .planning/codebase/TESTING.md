# Testing

`Last updated: 2026-04-23`
`Scope: /Users/miguelmont/Documents/ClaudeProjects/tvmcpserver`

## 1. TL;DR

| Dimension | Status |
| --- | --- |
| Effective coverage | ~0% (the one test file targets a deleted module) |
| Python tests | 1 file, 11.6 KB — broken |
| Bash tests | none |
| TS tests | out of scope (subtree gitignored) |
| CI | none configured |
| Fixtures | `tests/fixtures/` exists but is empty |
| Test runner | unittest (stdlib) — no pytest, no bats, no shellcheck wired up |

The repo is post-cleanup: most production scripts referenced by the former
test suite have been removed. The remaining tests are stale. v2 should
start fresh against the current three scripts.

## 2. Current state

### 2.1 What exists

`tests/test_bar_read.py` (11,634 bytes, last modified 2026-04-22).

- Uses stdlib `unittest`, runnable via `python3 tests/test_bar_read.py`.
- Fixture style: inline `lbl(text, price)` helper constructing dict payloads
  that mimic captured TradingView label output.
- Covers structural invariants of the (former) CHoCH parser: bullish/bearish
  direction detection, delta sign alignment, contradicting-delta warnings.
- Test data is captured live (docstring: "Fixtures derived from actual
  TradingView output captured on 2026-04-22 during Recon Live") — a good
  precedent for capture-replay testing.

### 2.2 Why it is broken

```python
# tests/test_bar_read.py:12-13
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import bar_read  # type: ignore
```

`scripts/bar_read.py` no longer exists. The test collection itself raises
`ModuleNotFoundError` on import, so every test errors before it runs.
Coverage against the *current* codebase (`fire_setup.sh`,
`telegram_recon_listener.sh`, `telegram_recon_parse.py`) is effectively
zero.

### 2.3 What is untested today

| Module | Critical behaviors with no automated test |
| --- | --- |
| `scripts/fire_setup.sh` | LONG/SHORT price-ordering assertions, tick-risk floor (0.25), RR_T1 ≥ 1 gate + `--force` bypass, single-target defaulting (T2/T3 → T1), readback abort on empty `entity_id`, JSONL journal shape, `.active_trade.json` shape, exit codes 1/2/3 |
| `scripts/telegram_recon_parse.py` | `fast` variant routing, HTF/LTF/Status short-circuit detection, chat-id filtering, offset monotonicity, malformed-JSON no-op |
| `scripts/telegram_recon_listener.sh` | First-run offset priming, `.env` missing → exit 1, `curl` failure → loop continues |

## 3. Framework recommendations

### 3.1 Python — pytest

Migrate from `unittest` to `pytest`.

Why:
- Parametrize assertion cases cleanly (the `fire_setup.sh` Python heredoc
  has ~8 invariants × long/short = 16 natural parametrize rows).
- `capsys` / `capfd` for stderr assertions (`ASSERT_FAIL: ...`).
- `tmp_path` for `.env` / `logs/` / `.active_trade.json` isolation.
- `monkeypatch` for `TZ`, `TELEGRAM_*` env, and stubbing `subprocess.Popen`
  in `telegram_recon_parse.py`.

Suggested layout:

```
tests/
  conftest.py            # shared fixtures: tmp_repo, fake_env, mock_tv_cli
  fixtures/
    telegram_updates/    # *.json captures from getUpdates
    tv_draw_responses/   # JSON blobs the TV CLI returns
  unit/
    test_telegram_recon_parse.py
    test_fire_setup_assertions.py   # invokes the heredoc directly via python3 -c
  integration/
    test_fire_setup_dryrun.py       # runs the full script with --dry-run
    test_listener_offset.py
```

Minimal dev deps (add `requirements-dev.txt`):

```
pytest>=8
pytest-mock>=3
```

### 3.2 Bash — bats-core + shellcheck

- **shellcheck** — static analysis, runs in <1s, catches ~80% of real bash
  bugs (quoting, `[[ ]]` vs `[ ]`, unused vars). Add as a required pre-commit
  gate against every `scripts/*.sh`.
- **bats-core** — behavioral tests. Each `.bats` file describes one script.
  The test body invokes the script with `run` and asserts on `$status`,
  `$output`, and filesystem effects.

Example target — `tests/bats/fire_setup.bats`:

```bash
@test "long: rejects sl >= entry" {
  run bash scripts/fire_setup.sh --direction long \
    --entry 100 --sl 100 --t1 101 --grade B --size 0.25 --label "X" --dry-run
  [ "$status" -eq 1 ]
  [[ "$output" == *"LONG order invalid"* ]]
}

@test "dry-run: exits 0 and draws nothing" {
  run bash scripts/fire_setup.sh --direction long \
    --entry 100 --sl 99 --t1 101.5 --grade B --size 0.25 --label "X" --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"DRY RUN"* ]]
  [ ! -f .active_trade.json ]
}
```

### 3.3 Why not TS tests here

`tradingview-mcp/` is gitignored (`.gitignore:6`). Testing the MCP CLI
belongs in that project, not this one. Here, we mock the CLI by
substituting `TV=` with a fake script that prints canned JSON.

## 4. Patterns to establish for v2

### 4.1 Capture-replay fixtures

The old `test_bar_read.py` set a good precedent: capture real TradingView
payloads from a live session, store as JSON under `tests/fixtures/`, replay
in tests. Adopt this for every external-API boundary:

- `tests/fixtures/telegram_updates/*.json` — real `getUpdates` responses
  (redact `chat.id` to a fixed test value).
- `tests/fixtures/tv_draw_responses/*.json` — real `tv draw shape`
  responses (success, empty-entity-id failure, malformed).
- Include a dated header comment in each fixture: `# captured 2026-04-23
  during <scenario>`.

### 4.2 Hermetic mutations

Every test that writes files must use `tmp_path`. `fire_setup.sh` writes
`logs/recon_live.jsonl` and `.active_trade.json` at the repo root —
integration tests must `cd` into a `tmp_path` copy of the repo layout and
stub `.env` there.

### 4.3 External-CLI stubbing

`fire_setup.sh:123` indirects the TV CLI via `TV="node
tradingview-mcp/src/cli/index.js"`. Tests override with:

```bash
cat > "$TMPDIR/fake_tv.sh" <<'EOF'
#!/bin/bash
echo '{"entity_id": "line_42"}'
EOF
chmod +x "$TMPDIR/fake_tv.sh"
TV="$TMPDIR/fake_tv.sh" bash scripts/fire_setup.sh ...
```

Add a `TV="${TV:-node tradingview-mcp/src/cli/index.js}"` indirection so
the env var wins. (This is a one-line change to `fire_setup.sh`.)

### 4.4 Assertion-level tests first

`fire_setup.sh` factors all trade-correctness logic into one Python
heredoc (`scripts/fire_setup.sh:62-95`). Extract it into
`scripts/fire_setup_assertions.py` so pytest can `import` it and
parametrize against dozens of price-ladder combinations in milliseconds —
without spawning bash at all. The bash script then shells out to
`python3 scripts/fire_setup_assertions.py --entry ... --sl ...`. This
refactor buys near-complete coverage of the risk logic for cheap.

### 4.5 Exit-code contract tests

Document exit codes in `CONVENTIONS.md` (done — section 3.5) **and** lock
them with tests. One test per code × one representative cause. These tests
double as living documentation for callers (Claude, cron, etc.).

### 4.6 No flaky network

Tests must never call `api.telegram.org` or a live TradingView instance.
- Telegram: stub `curl` via a `PATH=` shim or inject `TELEGRAM_BOT_TOKEN=""`
  to trigger the `WARN: .env not found` path in `fire_setup.sh:149`.
- TradingView: fake TV CLI (4.3).

## 5. Coverage targets (v2)

Priority order for building the new suite:

1. **`fire_setup.sh` assertions** — extract + pytest parametrize. This is
   the highest-value code (risk math, directly gates live trades).
2. **`fire_setup.sh` dry-run integration** — bats, assert banner output,
   exit code, no file mutations.
3. **`fire_setup.sh` readback abort** — bats, fake TV returns empty
   `entity_id` → exit 3, no Telegram, no JSONL line.
4. **`telegram_recon_parse.py` routing** — pytest, feed captured updates,
   assert `EVENT::...` stdout + offset file contents.
5. **`telegram_recon_listener.sh` offset priming** — bats, first run with
   no offset file → file written with `latest+1`.

Target: 80% line coverage on `scripts/*.py`, 100% exit-code coverage on
`scripts/*.sh`, shellcheck clean.

## 6. Immediate cleanup actions

- [ ] Delete or quarantine `tests/test_bar_read.py` (imports a deleted
  module; fails collection). If the CHoCH parser is resurrected, restore
  from git history alongside the script.
- [ ] Add a stub `tests/README.md` pointing at this doc so future
  contributors don't re-invent the test layout.
- [ ] Decide hosting for CI (GitHub Actions workflow under `.github/` is
  conventional; none exists today).

## 7. Running the (current) suite

```bash
# Will currently fail with ModuleNotFoundError — see section 2.2.
python3 tests/test_bar_read.py
```

Once v2 is bootstrapped:

```bash
# Python
pytest tests/unit tests/integration

# Bash
shellcheck scripts/*.sh
bats tests/bats
```
