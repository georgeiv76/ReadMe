#!/usr/bin/env python3
"""StochRSI cycle trading — the user's core method, tested honestly.

Long cycle (uptrend regime): ARMED when %K < os_th ('close to zero');
BUY when K crosses back above os_th; SELL when K crosses back below ob_th
('close to one hundred'), or timeout, or regime flips down (exit-on-flip).

Short cycle (downtrend regime, mirror of the same logic): SHORT when K
crosses back below ob_th; COVER when K crosses back above os_th, or
timeout, or regime flips up.

Regime detection: 'sma' (close vs SMA(regime_sma_bars)) or 'cross'
(SMA(regime_fast_bars) vs SMA(regime_slow_bars) — faster at turns).
Optional 'ponderata' (0.2/0.3/0.5 weighted 3-bar close) smoothing of the
oscillator input. Execution at event-bar close; $ cost per round trip.

Reported per 3 walk-forward folds + sacred holdout (last 25%), split by
side (long/short) plus combined PnL.

Usage: backtest_srsi_cycle.py [params.json] [metrics_out.json]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backtest_entry10 import stochrsi_series  # noqa: E402

HISTORY = Path(__file__).resolve().parent.parent / "gold-intel" / "data" / "history_12mo.json"


def run(params, data):
    h = data["gold_hourly"]
    live = [i for i in range(len(h["ts"])) if abs(h["high"][i] - h["low"][i]) > 1e-9]
    C = [h["close"][i] for i in live]
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

    rf, rs = params.get("regime_fast_bars"), params.get("regime_slow_bars")
    rb = params.get("regime_sma_bars")

    def regime_up(i):
        if rf and rs:
            if i < rs:
                return True
            return sum(C[i - rf: i]) / rf > sum(C[i - rs: i]) / rs
        if rb:
            if i < rb:
                return True
            return C[i] > sum(C[i - rb: i]) / rb
        return True

    os_th, ob_th = params["os_th"], params["ob_th"]
    max_hold = params["max_hold_bars"]
    cost = params["cost_per_trade_usd"]
    exit_on_flip = params.get("exit_on_flip", True)
    shorts_on = params.get("enable_shorts", False)

    segs = ("fold1", "fold2", "fold3", "holdout")
    Z = {s: {side: {"cycles": 0, "wins": 0, "rets": [], "pnl": 0.0}
             for side in ("long", "short")} for s in segs}

    def bucket(i):
        return "holdout" if i >= split else f"fold{min(2, (i - warmup) // fold_size) + 1}"

    def record(side, entry_i, exit_i):
        z = Z[bucket(entry_i)][side]
        raw = (C[exit_i] - C[entry_i]) if side == "long" else (C[entry_i] - C[exit_i])
        net = raw - cost
        z["cycles"] += 1
        z["wins"] += net > 0
        z["rets"].append(net / C[entry_i] * 100)
        z["pnl"] += net

    state, entry_i = "idle", None
    for i in range(warmup, n):
        k_prev, k = K[i - 1], K[i]
        if k is None or k_prev is None:
            continue
        up = regime_up(i)
        if state == "idle":
            if up and k_prev < os_th <= k:
                state, entry_i = "long", i
            elif (not up) and shorts_on and k_prev > ob_th >= k:
                state, entry_i = "short", i
        elif state == "long":
            if (k_prev > ob_th >= k) or (i - entry_i >= max_hold) or (exit_on_flip and not up):
                record("long", entry_i, i)
                state = "idle"
        elif state == "short":
            if (k_prev < os_th <= k) or (i - entry_i >= max_hold) or (exit_on_flip and up):
                record("short", entry_i, i)
                state = "idle"

    def side_summary(z):
        nc = max(z["cycles"], 1)
        return {"cycles": z["cycles"], "win_rate_pct": round(z["wins"] / nc * 100, 1),
                "avg_net_ret_pct": round(sum(z["rets"]) / nc, 3) if z["rets"] else None,
                "pnl_usd_per_oz": round(z["pnl"], 2)}

    out = {}
    for s in segs:
        out[s] = {
            "long": side_summary(Z[s]["long"]),
            "short": side_summary(Z[s]["short"]),
            "combined_pnl": round(Z[s]["long"]["pnl"] + Z[s]["short"]["pnl"], 2),
        }
    return out


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
