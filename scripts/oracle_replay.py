#!/usr/bin/env python3
"""Oracle for the blind Trader simulation.

Picks seeded random ~6-month windows from the 2004-2024 virgin archive,
ANONYMIZES them (no dates; prices rescaled by a secret per-window factor,
so the trader agent cannot recognize the era), and emits every candidate
signal (regime up + SRSI cycle bottom + Fib proximity) with:
  - the last 30 visible bars (rescaled OHLC),
  - indicator readings at the signal bar only,
  - the mechanical rule's decision (ADX<30 AND MACD-hist rising),
  - the sealed outcome if taken (mechanical cycle exit, % net of real costs)
    — outcomes are for the SCORER only, never shown to the trader.

Signals form a non-overlapping stream under mechanical exits (approximation
noted in the log). Seed fixed for reproducibility.
"""

import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backtest_entry10 import stochrsi_series  # noqa: E402
from backtest_srsi_cycle import adx_series, ema_full  # noqa: E402
from collect_gold_data import atr, fib_retracements  # noqa: E402

ARCHIVE = Path(__file__).resolve().parent.parent / "gold-intel" / "data" / "history_22y_hourly.json"
CUT_2025 = 1735689600
SEED = 42
N_WINDOWS = 2
WIN_BARS = 2600
MAX_SIGNALS = 12
COST_USD = 0.5


def main():
    d = json.loads(ARCHIVE.read_text())["gold_hourly"]
    idx = [i for i in range(len(d["ts"]))
           if d["ts"][i] < CUT_2025 and abs(d["high"][i] - d["low"][i]) > 1e-9]
    C = [d["close"][i] for i in idx]
    H = [d["high"][i] for i in idx]
    L = [d["low"][i] for i in idx]
    TS = [d["ts"][i] for i in idx]
    n = len(C)

    K = stochrsi_series(C)
    ADX = adx_series(H, L, C)
    e12, e26 = ema_full(C, 12), ema_full(C, 26)
    line = [a - b for a, b in zip(e12, e26)]
    sig = ema_full(line, 9)
    HIST = [m - s for m, s in zip(line, sig)]

    rng = random.Random(SEED)
    windows = []
    for w in range(N_WINDOWS):
        start = rng.randrange(1200, n - WIN_BARS - 100)
        scale = rng.uniform(0.35, 2.6)
        end = start + WIN_BARS
        signals = []
        i = start + 60
        while i < end - 50 and len(signals) < MAX_SIGNALS:
            k_prev, k = K[i - 1], K[i]
            if k is None or k_prev is None:
                i += 1
                continue
            regime = C[i] > sum(C[i - 1000: i]) / 1000
            crossed = k_prev < 10 <= k
            if not (regime and crossed):
                i += 1
                continue
            fibs = fib_retracements(max(H[i - 119: i + 1]), min(L[i - 119: i + 1]))["levels"].values()
            fib_dist = min(abs(C[i] - f) / C[i] * 100 for f in fibs)
            if fib_dist > 0.15:
                i += 1
                continue
            # mechanical exit: cycle top (K crosses down through 90) or 48 bars
            exit_i = min(i + 48, n - 1)
            for j in range(i + 1, min(i + 49, n)):
                if K[j - 1] is not None and K[j] is not None and K[j - 1] > 90 >= K[j]:
                    exit_i = j
                    break
            net_pct = (C[exit_i] - C[i] - COST_USD) / C[i] * 100
            a = atr(H[max(0, i - 199): i + 1], L[max(0, i - 199): i + 1],
                    C[max(0, i - 199): i + 1]) or C[i] * 0.003
            adx_v = ADX[i]
            mech_take = (adx_v is not None and adx_v < 30) and (HIST[i] > HIST[i - 1])
            bars = [
                f"{round(C[b] * scale, 2)}/{round(H[b] * scale, 2)}/{round(L[b] * scale, 2)}"
                for b in range(i - 29, i + 1)
            ]
            signals.append({
                "id": f"W{w}S{len(signals)}",
                "bars_close_high_low": bars,
                "indicators": {
                    "stochrsi_k": round(k, 1),
                    "adx": round(adx_v, 1) if adx_v is not None else None,
                    "macd_hist_rising": HIST[i] > HIST[i - 1],
                    "fib_distance_pct": round(fib_dist, 3),
                    "atr_pct_of_price": round(a / C[i] * 100, 3),
                    "pct_above_regime_sma": round((C[i] / (sum(C[i - 1000: i]) / 1000) - 1) * 100, 2),
                },
                "sealed": {
                    "true_date": datetime.fromtimestamp(TS[i], tz=timezone.utc).isoformat()[:10],
                    "net_pct_if_taken": round(net_pct, 3),
                    "hold_hours": exit_i - i,
                    "mech_take": mech_take,
                },
            })
            i = exit_i + 1
        windows.append({
            "window": w,
            "sealed_range": f"{datetime.fromtimestamp(TS[start], tz=timezone.utc).date()} .. "
                            f"{datetime.fromtimestamp(TS[end], tz=timezone.utc).date()}",
            "scale_hidden": round(scale, 4),
            "signals": signals,
        })

    out = Path(sys.argv[1] if len(sys.argv) > 1 else "oracle_windows.json")
    out.write_text(json.dumps(windows, indent=1))
    for w in windows:
        print(f"window {w['window']}: {len(w['signals'])} signals (era sealed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
