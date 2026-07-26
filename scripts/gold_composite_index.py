#!/usr/bin/env python3
"""Gold Composite Index (GCI): fuse the validated price system with the
learned external-signal table into one hourly score in [-100, +100].

PRICE side (validated in Blocks 3b/3c):
  regime (tide): +/-30  — price vs SMA(1000h), the strongest tested signal
  StochRSI extremes: +15 if K<=20, -15 if K>=80, 0 between (user rule)
  Fib confluence: +/-10 when price sits within 0.15% of a retracement level
    AND the oscillator is at the matching extreme

WORLD side (from SIGNALS.md round-1, Empiricist-approved only):
  event window (FOMC/TARIFF/WAR +/-6h): direction is a coin flip there ->
    multiply the whole index by 0.5 (confidence dampener), never add sign
  hot CPI (<=6h after): -15   | cool CPI: +10   (the 4/4 hot-fade)
  equity shock: +10 first 6h (safe-haven bid), -10 hours 6-24 (liquidation)
  Fed personnel FIRST surprise (<=24h): -20/+20 by surprise sign (one-off)
  CB_GOLD headlines: weight 0 (measured dead)

Interpretation bands: >= +40 favorable buy-dip environment; <= -40 defensive
/ stand aside; between: hold posture. The index is an ESTIMATION AID —
logged and scored like every prediction, not a guarantee.

Usage: gold_composite_index.py [events.json] [out.json]
Prints a calibration table: forward 24h gold return by GCI bucket
(in-sample demonstration — live journal provides the honest test).
"""

import json
import sys
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backtest_entry10 import stochrsi_series  # noqa: E402
from collect_gold_data import fib_retracements  # noqa: E402

HISTORY = Path(__file__).resolve().parent.parent / "gold-intel" / "data" / "history_12mo.json"


def build_gci(events_path=None):
    d = json.loads(HISTORY.read_text())["gold_hourly"]
    live = [i for i in range(len(d["ts"])) if abs(d["high"][i] - d["low"][i]) > 1e-9]
    C = [d["close"][i] for i in live]
    H = [d["high"][i] for i in live]
    L = [d["low"][i] for i in live]
    TS = [d["ts"][i] for i in live]
    n = len(C)
    K = stochrsi_series(C)

    events = []
    if events_path:
        for ev in json.loads(Path(events_path).read_text()):
            try:
                ts = int(datetime.fromisoformat(ev["utc"]).replace(tzinfo=timezone.utc).timestamp())
                events.append((ts, ev["type"], ev.get("hypothesis", "")))
            except (ValueError, KeyError):
                continue
        events.sort()
    ev_ts = [e[0] for e in events]

    def world(i):
        """(directional_adjustment, damp_factor) from events near hour i."""
        adj, damp = 0.0, 1.0
        t = TS[i]
        j = bisect_right(ev_ts, t + 6 * 3600)
        for k in range(max(0, j - 8), j):
            ets, etype, hyp = events[k]
            dt_h = (t - ets) / 3600  # hours since event (negative = upcoming)
            if etype in ("FED_DECISION", "TARIFF", "WAR") and -6 <= dt_h <= 6:
                damp = 0.5
            if etype == "CPI" and 0 <= dt_h <= 6:
                adj += -15 if hyp == "down" else 10
            if etype == "EQUITY_SHOCK":
                if 0 <= dt_h <= 6:
                    adj += 10
                elif 6 < dt_h <= 24:
                    adj += -10
            if etype == "FED_COMM" and "WARSH NOMINATED" in str(hyp).upper():
                pass  # handled by label below
        return adj, damp

    # one-off personnel surprise (encoded from the learned table)
    warsh_ts = int(datetime(2026, 1, 30, 14, 0, tzinfo=timezone.utc).timestamp())

    gci = [None] * n
    for i in range(1100, n):
        regime = 30 if C[i] > sum(C[i - 1000: i]) / 1000 else -30
        k = K[i]
        srsi_term = 0 if k is None else (15 if k <= 20 else (-15 if k >= 80 else 0))
        fib_term = 0
        if k is not None and (k <= 20 or k >= 80):
            fibs = fib_retracements(max(H[i - 119: i + 1]), min(L[i - 119: i + 1]))["levels"].values()
            if min(abs(C[i] - f) / C[i] * 100 for f in fibs) <= 0.15:
                fib_term = 10 if k <= 20 else -10
        adj, damp = world(i)
        if 0 <= (TS[i] - warsh_ts) / 3600 <= 24:
            adj -= 20
        gci[i] = max(-100, min(100, (regime + srsi_term + fib_term + adj) * damp))
    return TS, C, gci


def main():
    events_path = sys.argv[1] if len(sys.argv) > 1 else None
    TS, C, gci = build_gci(events_path)
    n = len(C)
    buckets = {}
    for i in range(1100, n - 25):
        g = gci[i]
        if g is None:
            continue
        fwd = (C[i + 24] - C[i]) / C[i] * 100 if i + 24 < n else None
        if fwd is None:
            continue
        b = ("<=-40" if g <= -40 else "-40..-15" if g <= -15 else "-15..+15"
             if g < 15 else "+15..+40" if g < 40 else ">=+40")
        buckets.setdefault(b, []).append(fwd)
    order = ["<=-40", "-40..-15", "-15..+15", "+15..+40", ">=+40"]
    print(f"{'GCI bucket':>10} {'hours':>7} {'mean fwd 24h':>13} {'% positive':>11}")
    rows = {}
    for b in order:
        v = buckets.get(b, [])
        if not v:
            continue
        rows[b] = {"hours": len(v), "mean_fwd_24h_pct": round(sum(v) / len(v), 3),
                   "pct_positive": round(sum(1 for x in v if x > 0) / len(v) * 100, 1)}
        print(f"{b:>10} {len(v):>7} {rows[b]['mean_fwd_24h_pct']:>12}% {rows[b]['pct_positive']:>10}%")
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(json.dumps(rows, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
