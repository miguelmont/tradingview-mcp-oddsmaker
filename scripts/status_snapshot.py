#!/usr/bin/env python3
"""Fast HTF/LTF/Status reader. Uses the local `tv` CLI to query TradingView
and posts a formatted snapshot to Telegram. Deterministic; no LLM round-trip.

Usage: status_snapshot.py {htf|ltf|all}
"""
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TV_CLI = ["node", str(ROOT / "tradingview-mcp/src/cli/index.js")]
DELTA_NOISE = 500  # |delta| below this is treated as 0 in HTF vote

HTF_PANE_INDEX = 1  # NQ 1h
LTF_PANE_INDEX = 0  # MNQ 1m


def load_env() -> dict:
    env = {}
    envfile = ROOT / ".env"
    if envfile.exists():
        for line in envfile.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def tv(*args) -> dict:
    """Invoke `tv` CLI. Returns parsed JSON dict."""
    proc = subprocess.run(TV_CLI + list(args), capture_output=True, text=True, timeout=10)
    if proc.returncode != 0:
        raise RuntimeError(f"tv {' '.join(args)} failed (exit {proc.returncode}): {proc.stderr.strip()}")
    return json.loads(proc.stdout)


def parse_vwap(s: str) -> float:
    """'26.721,77' (es_ES locale) → 26721.77"""
    return float(s.replace(".", "").replace(",", "."))


def pick_vwaps_htf(values: list) -> tuple[float | None, float | None]:
    """HTF: Weekly = VWAP without bands (narrower), Monthly = VWAP with bands.
    Fallback: closest-to-price = Weekly."""
    weekly = monthly = None
    for s in values:
        v = s.get("values", {})
        vwap = parse_vwap(v.get("VWAP", "0"))
        has_bands = "Upper Band #1" in v
        if has_bands:
            monthly = vwap
        else:
            weekly = vwap
    return weekly, monthly


def pick_session_vwap_ltf(values: list, price: float) -> tuple[float | None, float | None, float | None]:
    """LTF Session VWAP = the one with bands closest to price. Returns (vwap, upper, lower)."""
    best = None
    for s in values:
        v = s.get("values", {})
        if "Upper Band #1" not in v:
            continue
        vwap = parse_vwap(v["VWAP"])
        if best is None or abs(price - vwap) < abs(price - best[0]):
            best = (vwap, parse_vwap(v["Upper Band #1"]), parse_vwap(v["Lower Band #1"]))
    if best is None:
        return None, None, None
    return best


def parse_latest_choch(labels: list) -> dict | None:
    """Given a list of label dicts, extract the most recent CHoCH pattern.

    BigBeluga draws each pattern as ~5 labels in chronological order:
    3 anchor points (text=''), 1 circle at min/max anchor (text='◯'),
    and 1 delta annotation (text like '+109.634K' or '-1.955K').

    Returns {circle_price, anchors, direction, delta, delta_sign}.
    """
    if not labels:
        return None
    tail = labels[-5:]
    circle = None
    delta_text = None
    anchors = []
    for lbl in tail:
        t = (lbl.get("text") or "").strip()
        price = lbl.get("price")
        if t == "◯":
            circle = price
        elif t and (t[0] in "+-") and any(c.isdigit() for c in t):
            delta_text = t
        else:
            anchors.append(price)
    if circle is None or not anchors:
        return None
    # compute direction: circle at the HIGHEST anchor → bearish; LOWEST → bullish
    hi = max(anchors + [circle])
    lo = min(anchors + [circle])
    if circle == hi:
        direction = "BEARISH"
    elif circle == lo:
        direction = "BULLISH"
    else:
        direction = "UNCLEAR"
    delta_val = None
    delta_sign = 0
    if delta_text:
        m = re.match(r"([+-])([\d.]+)([Kk])?", delta_text)
        if m:
            sign = 1 if m.group(1) == "+" else -1
            num = float(m.group(2)) * (1000 if m.group(3) else 1)
            delta_val = sign * num
            if abs(delta_val) >= DELTA_NOISE:
                delta_sign = sign
    return {
        "circle": circle,
        "anchors": anchors,
        "direction": direction,
        "delta_text": delta_text,
        "delta_val": delta_val,
        "delta_sign": delta_sign,
    }


def read_pane_state(pane_index: int, expect_symbol: str | None = None):
    tv("pane", "focus", str(pane_index))
    q = tv("quote")
    vals = tv("values")
    labels = tv("data", "labels", "--filter", "Choch")
    return {
        "quote": q,
        "values": vals.get("studies", []),
        "labels": labels.get("studies", [{}])[0].get("labels", []) if labels.get("studies") else [],
    }


def htf_analysis(state: dict) -> dict:
    price = state["quote"]["last"]
    weekly, monthly = pick_vwaps_htf(state["values"])
    choch = parse_latest_choch(state["labels"])

    v1 = 1 if (weekly is not None and price > weekly) else (-1 if weekly is not None else 0)
    v2 = 1 if (monthly is not None and price > monthly) else (-1 if monthly is not None else 0)
    if choch is None:
        v3 = 0
        v4 = 0
    else:
        v3 = +1 if choch["direction"] == "BULLISH" else (-1 if choch["direction"] == "BEARISH" else 0)
        v4 = choch["delta_sign"]

    votes = [v1, v2, v3, v4]
    bulls = sum(1 for x in votes if x == +1)
    bears = sum(1 for x in votes if x == -1)
    if bulls >= 3:
        bias = "BULLISH"
    elif bears >= 3:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    return {
        "price": price,
        "weekly": weekly,
        "monthly": monthly,
        "choch": choch,
        "votes": {"weekly": v1, "monthly": v2, "choch": v3, "delta": v4},
        "tally": f"{bulls}-{bears}",
        "bias": bias,
    }


def ltf_analysis(state: dict) -> dict:
    price = state["quote"]["last"]
    vwap, upper, lower = pick_session_vwap_ltf(state["values"], price)
    sd = (upper - vwap) if (upper and vwap) else None
    dist = ((price - vwap) / sd) if (sd and sd > 0) else None
    if dist is None:
        band = "UNKNOWN"
    elif abs(dist) <= 0.5:
        band = "IN-BAND"
    elif abs(dist) <= 1.0:
        band = "NEAR-BAND"
    elif dist > 1.0:
        band = "BULLISH-OVEREXT"
    else:
        band = "BEARISH-OVEREXT"
    choch = parse_latest_choch(state["labels"])
    return {
        "price": price,
        "vwap": vwap,
        "upper": upper,
        "lower": lower,
        "sd": sd,
        "dist": dist,
        "band": band,
        "choch": choch,
    }


def fmt_htf(h: dict) -> str:
    c = h["choch"]
    c_line = "—"
    if c:
        c_line = f"◯ @ {c['circle']:,} → {c['direction']}"
        if c["delta_text"]:
            c_line += f" · delta {c['delta_text']}"
    v = h["votes"]
    bias_emoji = {"BULLISH": "🟢", "BEARISH": "🔴", "NEUTRAL": "⚪"}[h["bias"]]
    return (
        f"{bias_emoji} *HTF (1h) {h['bias']} {h['tally']}*\n"
        f"• Price {h['price']:,.2f}\n"
        f"• Weekly {h['weekly']:,.2f} → {v['weekly']:+d}\n"
        f"• Monthly {h['monthly']:,.2f} → {v['monthly']:+d}\n"
        f"• BB CHoCH {c_line} → {v['choch']:+d}\n"
        f"• Delta sign → {v['delta']:+d}"
    )


def fmt_ltf(l: dict) -> str:
    c = l["choch"]
    c_line = "—"
    if c:
        c_line = f"◯ @ {c['circle']:,} → {c['direction']}"
        if c["delta_text"]:
            c_line += f" · delta {c['delta_text']}"
    band_emoji = {
        "IN-BAND": "🟢",
        "NEAR-BAND": "🟡",
        "BULLISH-OVEREXT": "🟠",
        "BEARISH-OVEREXT": "🟠",
        "UNKNOWN": "⚪",
    }.get(l["band"], "⚪")
    if l["dist"] is not None:
        dist_line = f"{band_emoji} *LTF (1m) {l['band']} {l['dist']:+.2f} SD*"
    else:
        dist_line = f"⚪ *LTF (1m) UNKNOWN*"
    return (
        f"{dist_line}\n"
        f"• Price {l['price']:,.2f} · SVWAP {l['vwap']:,.2f} · SD {l['sd']:.2f}\n"
        f"• Upper +1 {l['upper']:,.2f} · Lower -1 {l['lower']:,.2f}\n"
        f"• Latest BB CHoCH {c_line}"
    )


def send_telegram(text: str, env: dict) -> None:
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat = env.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("missing telegram creds", file=sys.stderr)
        sys.exit(1)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat,
        "text": text,
        "parse_mode": "Markdown",
    }).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        resp.read()


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"htf", "ltf", "all"}:
        print("usage: status_snapshot.py {htf|ltf|all}", file=sys.stderr)
        sys.exit(2)
    mode = sys.argv[1]
    env = load_env()

    panes_info = tv("pane", "list")
    original_active = panes_info.get("active_index", 0)

    lines = []
    try:
        if mode in ("htf", "all"):
            htf_state = read_pane_state(HTF_PANE_INDEX)
            h = htf_analysis(htf_state)
            lines.append(fmt_htf(h))
        if mode in ("ltf", "all"):
            ltf_state = read_pane_state(LTF_PANE_INDEX)
            l = ltf_analysis(ltf_state)
            lines.append(fmt_ltf(l))
    finally:
        try:
            tv("pane", "focus", str(original_active))
        except Exception:
            pass

    header = {
        "htf": "📊 *HTF Bias*",
        "ltf": "📊 *LTF State*",
        "all": "📊 *Status*",
    }[mode]
    msg = header + "\n\n" + "\n\n".join(lines)
    send_telegram(msg, env)
    print(msg)


if __name__ == "__main__":
    main()
