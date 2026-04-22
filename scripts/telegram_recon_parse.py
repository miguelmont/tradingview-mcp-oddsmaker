#!/usr/bin/env python3
"""Parses Telegram getUpdates JSON on stdin. Emits EVENT::<kind>::<text> on stdout.
Writes next offset to OFFSET_FILE env var. Filters by TARGET_CHAT env var.

Status commands (HTF / LTF / Status) are SHORT-CIRCUITED: handled by
`status_snapshot.py` directly; no event is emitted — no LLM round-trip.
Recon commands pass through as events for Claude to handle.
`Recon Backtesting Fast` / `Recon Live Fast` emit dedicated *_fast events
so the handler can branch to the code-based analysis path (A/B testing)."""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATUS_SCRIPT = str(ROOT / "scripts" / "status_snapshot.py")


def run_status(mode: str) -> None:
    """Fire-and-forget status snapshot. Runs in background; parent does not block."""
    try:
        subprocess.Popen(
            ["python3", STATUS_SCRIPT, mode],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        print(f"[parse] status_snapshot spawn failed: {e}", file=sys.stderr)


def main() -> None:
    target_chat = int(os.environ.get("TARGET_CHAT", "0"))
    offset_file = os.environ["OFFSET_FILE"]

    with open(offset_file) as f:
        prev_offset = int((f.read() or "0").strip() or "0")

    try:
        data = json.load(sys.stdin)
    except Exception:
        return
    if not data.get("ok"):
        return

    max_id = prev_offset - 1
    for upd in data.get("result", []):
        max_id = max(max_id, upd.get("update_id", 0))
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat = msg.get("chat", {}) or {}
        if chat.get("id") != target_chat:
            continue
        text = (msg.get("text") or "").strip()
        if not text:
            continue
        norm = re.sub(r"[_/\-]+", " ", text).lower().strip()
        is_fast = bool(re.search(r"\bfast\b", norm))

        if "recon backtesting" in norm:
            kind = "recon_backtesting_fast" if is_fast else "recon_backtesting"
            print(f"EVENT::{kind}::{text}", flush=True)
        elif "recon live" in norm:
            kind = "recon_live_fast" if is_fast else "recon_live"
            print(f"EVENT::{kind}::{text}", flush=True)
        elif re.search(r"\b(htf|bias)\b", norm) and "status" not in norm and "ltf" not in norm:
            run_status("htf")  # no event — script posts to Telegram directly
        elif re.search(r"\bltf\b", norm) and "status" not in norm and "htf" not in norm:
            run_status("ltf")
        elif re.search(r"\bstatus\b", norm):
            run_status("all")

    new_offset = max_id + 1
    if new_offset > prev_offset:
        with open(offset_file, "w") as f:
            f.write(str(new_offset))


if __name__ == "__main__":
    main()
