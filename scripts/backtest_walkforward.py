#!/usr/bin/env python3
"""Walk-forward backtest of the hourly gold estimation model.

No lookahead: every prediction and every trading level at hour t uses only
candles up to t. Train segment (first 75% of hours) calibrates the hourly
session-bias table; the holdout segment (last 25%) is never used for
calibration — it exists to catch overfitting.

Scores two things:
1. PRICE ESTIMATION — predicted next-hour close vs real:
   MAE ($ and %), direction accuracy (with a 0.02% dead zone), and
   within-band accuracy at a FIXED pre-registered band of +/-0.15%.
   A persistence baseline (pred = no change) is always reported: skill is
   model minus baseline, not the raw number.
2. TRADING LEVELS — sequential non-overlapping simulation of the confluence
   zones: limit-buy at the buy zone, target at the sell zone, ATR stop.
   Fill rate, win rate, profit factor, average PnL per trade ($/oz).

Usage: python scripts/backtest_walkforward.py [params.json] [metrics_out.json]
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_gold_data import (  # noqa: E402
    REPO_ROOT,
    atr,
    best_zones,
    bollinger,
    cluster_levels,
    collect_levels,
    fib_retracements,
    pivot_points,
)

HISTORY = REPO_ROOT / "gold-intel" / "data" / "history_12mo.json"
DEFAULT_PARAMS = REPO_ROOT / "gold-intel" / "model-params.json"

DEAD_ZONE_PCT = 0.02   # |real move| below this: direction is noise, excluded
BAND_PCT = 0.15        # fixed accuracy band; pre-registered, NOT tunable


def load_params(path):
    return json.loads(Path(path).read_text())


def sma_tail(values, n):
    if len(values) < n:
        return None
    return sum(values[-n:]) / n


def build_daily_index(d_ts, hourly_dates):
    """For each hourly bar, index of the previous COMPLETED daily candle."""
    d_dates = [datetime.fromtimestamp(t, tz=timezone.utc).date() for t in d_ts]
    idx_map = []
    j = 0
    for hd in hourly_dates:
        while j + 1 < len(d_dates) and d_dates[j + 1] < hd:
            j += 1
        idx_map.append(j if d_dates[j] < hd else max(0, j - 1))
    return idx_map


def run(params, data):
    src = "gold_hourly" if data.get("gold_hourly", {}).get("n", 0) > 3000 else "gold_fut_hourly"
    daily_key = "gold_daily" if src == "gold_hourly" else "gold_fut_daily"
    h = data[src]
    d = data[daily_key]
    h_ts, h_close, h_high, h_low = h["ts"], h["close"], h["high"], h["low"]
    d_ts, d_close, d_high, d_low = d["ts"], d["close"], d["high"], d["low"]

    h_dt = [datetime.fromtimestamp(t, tz=timezone.utc) for t in h_ts]
    h_dates = [t.date() for t in h_dt]
    prev_day = build_daily_index(d_ts, h_dates)

    n = len(h_close)
    warmup = 200
    split = warmup + int((n - warmup) * 0.75)

    # Session bias from TRAIN ONLY: mean % move into each UTC hour.
    bias_sum = [0.0] * 24
    bias_cnt = [0] * 24
    for i in range(warmup, split - 1):
        mv = (h_close[i + 1] - h_close[i]) / h_close[i] * 100
        hr = h_dt[i + 1].hour
        bias_sum[hr] += mv
        bias_cnt[hr] += 1
    bias = [bias_sum[k] / bias_cnt[k] if bias_cnt[k] else 0.0 for k in range(24)]

    # Per-day caches: pivots, daily fib, daily SMA block.
    day_cache = {}

    def day_ctx(i):
        pj = prev_day[i]
        if pj not in day_cache:
            closes = d_close[: pj + 1]
            fw = params["fib_daily_window"]
            day_cache[pj] = {
                "pivots": pivot_points(d_high[pj], d_low[pj], d_close[pj]),
                "fib": fib_retracements(
                    max(d_high[max(0, pj - fw + 1): pj + 1]),
                    min(d_low[max(0, pj - fw + 1): pj + 1]),
                ),
                "ind": {
                    "sma20": sma_tail(closes, 20),
                    "sma50": sma_tail(closes, 50),
                    "sma200": sma_tail(closes, 200),
                },
            }
        return day_cache[pj]

    seg = lambda i: "train" if i < split else "holdout"  # noqa: E731
    M = {
        s: {
            "n_pred": 0, "abs_err_usd": 0.0, "abs_err_pct": 0.0,
            "dir_n": 0, "dir_hit": 0, "band_hit": 0,
            "naive_abs_err_pct": 0.0, "naive_band_hit": 0,
        }
        for s in ("train", "holdout")
    }

    # --- price estimation walk ---
    for i in range(warmup, n - 1):
        ctx = day_ctx(i)
        c = h_close[i]
        last_mv = (c - h_close[i - 1]) / h_close[i - 1] * 100
        pivot_gap = (ctx["pivots"]["P"] - c) / c * 100
        pred_pct = (
            params["momentum_k"] * last_mv
            + params["pivot_pull_k"] * pivot_gap
            + params["session_bias_scale"] * bias[h_dt[i + 1].hour]
        )
        real_pct = (h_close[i + 1] - c) / c * 100
        m = M[seg(i)]
        m["n_pred"] += 1
        err = abs(pred_pct - real_pct)
        m["abs_err_pct"] += err
        m["abs_err_usd"] += abs(err / 100 * c)
        m["naive_abs_err_pct"] += abs(real_pct)
        if abs(real_pct) > DEAD_ZONE_PCT:
            m["dir_n"] += 1
            if (pred_pct > 0) == (real_pct > 0):
                m["dir_hit"] += 1
        if err <= BAND_PCT:
            m["band_hit"] += 1
        if abs(real_pct) <= BAND_PCT:
            m["naive_band_hit"] += 1

    # --- trading-levels simulation (sequential, non-overlapping) ---
    T = {
        s: {"signals": 0, "fills": 0, "wins": 0, "stops": 0, "timeouts": 0,
            "gross_win": 0.0, "gross_loss": 0.0, "pnl": 0.0}
        for s in ("train", "holdout")
    }
    i = warmup
    while i < n - 2:
        ctx = day_ctx(i)
        spot = h_close[i]
        fw = params["fib_hourly_window"]
        fib_h = fib_retracements(
            max(h_high[max(0, i - fw + 1): i + 1]),
            min(h_low[max(0, i - fw + 1): i + 1]),
        )
        boll = bollinger(h_close[max(0, i - 199): i + 1])
        levels = collect_levels(spot, ctx["ind"], ctx["pivots"], ctx["fib"], fib_h, boll)
        clusters = cluster_levels(levels, spot, params["cluster_tol_pct"])
        buy_zone, sell_zone = best_zones(clusters, spot)
        t = T[seg(i)]
        if not (buy_zone and sell_zone):
            i += 1
            continue
        t["signals"] += 1
        buy_lv, sell_lv = buy_zone["level"], sell_zone["level"]
        a = atr(h_high[max(0, i - 199): i + 1], h_low[max(0, i - 199): i + 1],
                h_close[max(0, i - 199): i + 1]) or spot * 0.003
        stop_lv = buy_lv - params["stop_atr_mult"] * a

        fill_j = None
        for j in range(i + 1, min(i + 1 + params["order_ttl_hours"], n)):
            if h_low[j] <= buy_lv:
                fill_j = j
                break
        if fill_j is None:
            i += 1
            continue
        t["fills"] += 1
        exit_j = min(fill_j + params["trade_horizon_hours"], n - 1)
        outcome, exit_px = "timeout", h_close[exit_j]
        for j in range(fill_j, exit_j + 1):
            if h_low[j] <= stop_lv:          # conservative: stop checked first
                outcome, exit_px, exit_j = "stop", stop_lv, j
                break
            if h_high[j] >= sell_lv:
                outcome, exit_px, exit_j = "win", sell_lv, j
                break
        pnl = exit_px - buy_lv
        t["pnl"] += pnl
        if outcome == "win":
            t["wins"] += 1
            t["gross_win"] += pnl
        elif outcome == "stop":
            t["stops"] += 1
            t["gross_loss"] += -pnl
        else:
            t["timeouts"] += 1
            t["gross_win" if pnl > 0 else "gross_loss"] += abs(pnl)
        i = exit_j + 1   # no overlapping trades

    def finalize(s):
        m, t = M[s], T[s]
        np_, dn = max(m["n_pred"], 1), max(m["dir_n"], 1)
        fills = max(t["fills"], 1)
        return {
            "n_pred": m["n_pred"],
            "mae_usd": round(m["abs_err_usd"] / np_, 3),
            "mae_pct": round(m["abs_err_pct"] / np_, 4),
            "direction_acc_pct": round(m["dir_hit"] / dn * 100, 2),
            "direction_n": m["dir_n"],
            "band_acc_pct": round(m["band_hit"] / np_ * 100, 2),
            "naive_mae_pct": round(m["naive_abs_err_pct"] / np_, 4),
            "naive_band_acc_pct": round(m["naive_band_hit"] / np_ * 100, 2),
            "trades": {
                "signals": t["signals"], "fills": t["fills"],
                "win_rate_pct": round(t["wins"] / fills * 100, 2),
                "wins": t["wins"], "stops": t["stops"], "timeouts": t["timeouts"],
                "pnl_usd_per_oz": round(t["pnl"], 2),
                "avg_pnl_per_trade": round(t["pnl"] / fills, 3),
                "profit_factor": round(t["gross_win"] / t["gross_loss"], 3)
                if t["gross_loss"] > 0 else None,
            },
        }

    return {
        "source": src,
        "hours": n,
        "split_at": split,
        "band_pct_fixed": BAND_PCT,
        "train": finalize("train"),
        "holdout": finalize("holdout"),
    }


def main():
    params_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PARAMS
    params = load_params(params_path)
    data = json.loads(HISTORY.read_text())
    result = run(params, data)
    result["params"] = params
    out = json.dumps(result, indent=2)
    print(out)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(out + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
