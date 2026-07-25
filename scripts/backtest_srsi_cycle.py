#!/usr/bin/env python3
"""StochRSI cycle trading — the user's core method, tested honestly.

State machine on StochRSI %K:
  ARMED_BUY  when K < os_th (deep oversold — 'close to zero')
  BUY event  when K crosses back above os_th (the bottom is likely in)
  ARMED_SELL when K > ob_th ('close to one hundred')
  SELL event when K crosses back below ob_th (the top is likely in)
Cycle = BUY event -> next SELL event (or timeout at max_hold bars).
Execution at the event bar's close; $ cost per round trip.

Optional 'ponderata': smooth the close series with a weighted average of the
last 3 bars (0.2/0.3/0.5) before computing StochRSI, to cut whipsaw.

Measured per fold (3 walk-forward) + sacred holdout (last 25%):
- cycles, win rate (net of costs), avg/median net return per cycle, PnL
- bottom-call accuracy: entry within {0.1,0.25,0.5,1.0}% of the cycle's
  actual low; top-call accuracy: exit within bands of the cycle's high
- capture ratio: (exit-entry) / (cycle_high - cycle_low)

Usage: backtest_srsi_cycle.py [params.json] [metrics_out.json]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backtest_entry10 import stochrsi_series  # noqa: E402

HISTORY = Path(__file__).resolve().parent.parent / "gold-intel" / "data" / "history_12mo.json"
BANDS = (0.1, 0.25, 0.5, 1.0)


def run(params, data):
    h = data["gold_hourly"]
    live = [i for i in range(len(h["ts"])) if abs(h["high"][i] - h["low"][i]) > 1e-9]
    C = [h["close"][i] for i in live]
    H = [h["high"][i] for i in live]
    L = [h["low"][i] for i in live]
    n = len(C)
    warmup = 200
    split = warmup + int((n - warmup) * 0.75)
    fold_size = (split - warmup) // 3

    src = C
    if params.get("use_wavg3", False):
        src = [C[0], C[1]] + [
            0.2 * C[i - 2] + 0.3 * C[i - 1] + 0.5 * C[i] for i in range(2, n)
        ]
    K = stochrsi_series(src, params["rsi_period"], params["stoch_period"], params["smooth"])

    os_th, ob_th = params["os_th"], params["ob_th"]
    max_hold = params["max_hold_bars"]
    cost = params["cost_per_trade_usd"]

    segs = ("fold1", "fold2", "fold3", "holdout")
    Z = {s: {"cycles": 0, "wins": 0, "rets": [], "pnl": 0.0,
             "bot_err": [], "top_err": [], "capture": []} for s in segs}

    def bucket(i):
        return "holdout" if i >= split else f"fold{min(2, (i - warmup) // fold_size) + 1}"

    state = "idle"
    entry_i = None
    i = warmup
    while i < n - 1:
        k_prev, k = K[i - 1], K[i]
        if k is None or k_prev is None:
            i += 1
            continue
        regime_ok = True
        rb = params.get("regime_sma_bars")
        if rb and i >= rb:
            regime_ok = C[i] > sum(C[i - rb: i]) / rb
        if state == "idle" and k_prev < os_th <= k and regime_ok:  # bottom in, tide up
            state = "long"
            entry_i = i
        elif state == "long":
            exited = (k_prev > ob_th >= k) or (i - entry_i >= max_hold)
            if exited:
                z = Z[bucket(entry_i)]
                entry_px, exit_px = C[entry_i], C[i]
                lo = min(L[entry_i: i + 1])
                hi = max(H[entry_i: i + 1])
                net = exit_px - entry_px - cost
                z["cycles"] += 1
                z["wins"] += net > 0
                z["rets"].append(net / entry_px * 100)
                z["pnl"] += net
                z["bot_err"].append((entry_px - lo) / lo * 100)
                z["top_err"].append((hi - exit_px) / hi * 100)
                rng = hi - lo
                if rng > 0:
                    z["capture"].append((exit_px - entry_px) / rng * 100)
                state = "idle"
        i += 1

    def summary(z):
        nc = max(z["cycles"], 1)
        rets = sorted(z["rets"]) or [0]

        def curve(errs):
            return {f"<={b}%": round(sum(1 for e in errs if e <= b) / nc * 100, 1)
                    for b in BANDS}

        return {
            "cycles": z["cycles"],
            "win_rate_pct": round(z["wins"] / nc * 100, 1),
            "avg_net_ret_pct": round(sum(z["rets"]) / nc, 3) if z["rets"] else None,
            "median_net_ret_pct": round(rets[len(rets) // 2], 3),
            "pnl_usd_per_oz": round(z["pnl"], 2),
            "bottom_call_within": curve(z["bot_err"]),
            "top_call_within": curve(z["top_err"]),
            "avg_capture_pct_of_range": round(sum(z["capture"]) / max(len(z["capture"]), 1), 1),
        }

    return {s: summary(Z[s]) for s in segs}


def main():
    params = json.loads(Path(sys.argv[1]).read_text())
    result = run(params, json.loads(HISTORY.read_text()))
    result["params"] = params
    out = json.dumps(result, indent=2)
    print(out)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(out + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
