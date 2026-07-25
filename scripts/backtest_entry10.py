#!/usr/bin/env python3
"""Block 3a — 'best buy over the next 10 candles' objective.

At each signal hour t0 the model outputs a predicted best-buy price Bhat
(confluence support level, gated/steered by an oscillator vote stack).
Ground truth: L10 = the actual low of the next 10 hourly candles.

Scored on:
- tolerance curve: fraction of signals with |Bhat - L10|/L10 within
  {0.05, 0.10, 0.25, 0.50, 1.00}% — reported against TWO naive baselines
  (Bhat=spot; Bhat=spot-ATR) which any real model must beat;
- fill rate (price actually reached Bhat) and bounce capture after fill
  (max high of remaining horizon vs Bhat), plus simple costed PnL
  (exit at target cluster or at horizon close).

Same discipline as before: no lookahead, 3 walk-forward folds in train,
sacred holdout (last 25%), dead bars dropped.

Usage: backtest_entry10.py [params.json] [metrics_out.json] [m15.csv.gz|-]
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_gold_data import (  # noqa: E402
    REPO_ROOT, atr, bollinger, cluster_levels, collect_levels,
    fib_retracements, pivot_points, sma,
)
from backtest_walkforward import build_daily_index, load_m15, sma_tail  # noqa: E402

HISTORY = REPO_ROOT / "gold-intel" / "data" / "history_12mo.json"
TOL_BANDS = (0.05, 0.10, 0.25, 0.50, 1.00)  # pct, pre-registered
HORIZON = 10                                 # candles, per user objective


# ---------- oscillator stack (full series, O(n), no lookahead) ----------

def rsi_series(closes, period=14):
    out = [None] * len(closes)
    if len(closes) <= period:
        return out
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        gains += max(d, 0)
        losses += max(-d, 0)
    ag, al = gains / period, losses / period
    out[period] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        ag = (ag * (period - 1) + max(d, 0)) / period
        al = (al * (period - 1) + max(-d, 0)) / period
        out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def stoch_series(highs, lows, closes, period=14, smooth=3):
    k_fast = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        hh = max(highs[i - period + 1: i + 1])
        ll = min(lows[i - period + 1: i + 1])
        k_fast[i] = 50.0 if hh == ll else (closes[i] - ll) / (hh - ll) * 100
    k_slow = [None] * len(closes)
    for i in range(len(closes)):
        w = [v for v in k_fast[max(0, i - smooth + 1): i + 1] if v is not None]
        if len(w) == smooth:
            k_slow[i] = sum(w) / smooth
    return k_slow


def stochrsi_series(closes, rsi_p=14, stoch_p=14, smooth=3):
    r = rsi_series(closes, rsi_p)
    raw = [None] * len(closes)
    for i in range(len(closes)):
        w = [v for v in r[max(0, i - stoch_p + 1): i + 1] if v is not None]
        if len(w) == stoch_p:
            hi, lo = max(w), min(w)
            raw[i] = 50.0 if hi == lo else (r[i] - lo) / (hi - lo) * 100
    k = [None] * len(closes)
    for i in range(len(closes)):
        w = [v for v in raw[max(0, i - smooth + 1): i + 1] if v is not None]
        if len(w) == smooth:
            k[i] = sum(w) / smooth
    return k


def cci_series(highs, lows, closes, period=20):
    tp = [(h + l + c) / 3 for h, l, c in zip(highs, lows, closes)]
    out = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        w = tp[i - period + 1: i + 1]
        m = sum(w) / period
        md = sum(abs(v - m) for v in w) / period
        out[i] = 0.0 if md == 0 else (tp[i] - m) / (0.015 * md)
    return out


def willr_series(highs, lows, closes, period=14):
    out = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        hh = max(highs[i - period + 1: i + 1])
        ll = min(lows[i - period + 1: i + 1])
        out[i] = -50.0 if hh == ll else (hh - closes[i]) / (hh - ll) * -100
    return out


def run(params, data, m15_map=None):
    h = data["gold_hourly"]
    d = data["gold_daily"]
    live = [i for i in range(len(h["ts"])) if abs(h["high"][i] - h["low"][i]) > 1e-9]
    h_ts = [h["ts"][i] for i in live]
    h_close = [h["close"][i] for i in live]
    h_high = [h["high"][i] for i in live]
    h_low = [h["low"][i] for i in live]
    d_ts, d_close, d_high, d_low = d["ts"], d["close"], d["high"], d["low"]

    h_dt = [datetime.fromtimestamp(t, tz=timezone.utc) for t in h_ts]
    prev_day = build_daily_index(d_ts, [t.date() for t in h_dt])
    n = len(h_close)
    warmup = 200
    split = warmup + int((n - warmup) * 0.75)
    fold_size = (split - warmup) // 3

    def bucket(i):
        return "holdout" if i >= split else f"fold{min(2, (i - warmup) // fold_size) + 1}"

    # Oscillator stack, computed once (each value uses only bars <= i).
    RSI = rsi_series(h_close)
    SRSI = stochrsi_series(h_close)
    STO = stoch_series(h_high, h_low, h_close)
    CCI = cci_series(h_high, h_low, h_close)
    WR = willr_series(h_high, h_low, h_close)

    def votes(i):
        os_v = sum([
            SRSI[i] is not None and SRSI[i] <= params["srsi_os"],
            STO[i] is not None and STO[i] <= params["stoch_os"],
            RSI[i] is not None and RSI[i] <= params["rsi_os"],
            CCI[i] is not None and CCI[i] <= params["cci_os"],
            WR[i] is not None and WR[i] <= params["wr_os"],
        ])
        ob_v = sum([
            SRSI[i] is not None and SRSI[i] >= params["srsi_ob"],
            STO[i] is not None and STO[i] >= params["stoch_ob"],
            RSI[i] is not None and RSI[i] >= params["rsi_ob"],
            CCI[i] is not None and CCI[i] >= params["cci_ob"],
            WR[i] is not None and WR[i] >= params["wr_ob"],
        ])
        return os_v, ob_v

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
                    min(d_low[max(0, pj - fw + 1): pj + 1])),
                "ind": {"sma20": sma_tail(closes, 20), "sma50": sma_tail(closes, 50),
                        "sma200": sma_tail(closes, 200)},
            }
        return day_cache[pj]

    def granular_low_high(j):
        if m15_map:
            subs = m15_map.get(h_ts[j])
            if subs:
                return subs
        return ((h_high[j], h_low[j]),)

    segs = ("fold1", "fold2", "fold3", "holdout")
    Z = {s: {"signals": 0, "suppressed_ob": 0,
             "err_model": [], "err_naive_spot": [], "err_naive_atr": [],
             "fills": 0, "bounce_pct": [], "pnl": 0.0, "wins": 0, "losses": 0}
         for s in segs}

    step = params.get("signal_step_hours", 3)  # evaluate every N hours
    for i in range(warmup, n - HORIZON - 1, step):
        z = Z[bucket(i)]
        spot = h_close[i]
        os_v, ob_v = votes(i)

        # Overbought suppression (the user's Fib-but-overbought rule).
        if ob_v >= params["ob_suppress_votes"]:
            z["suppressed_ob"] += 1
            continue

        ctx = day_ctx(i)
        fw = params["fib_hourly_window"]
        fib_h = fib_retracements(max(h_high[max(0, i - fw + 1): i + 1]),
                                 min(h_low[max(0, i - fw + 1): i + 1]))
        boll = bollinger(h_close[max(0, i - 199): i + 1])
        levels = collect_levels(spot, ctx["ind"], ctx["pivots"], ctx["fib"], fib_h, boll)
        clusters = cluster_levels(levels, spot, params["cluster_tol_pct"])
        a = atr(h_high[max(0, i - 199): i + 1], h_low[max(0, i - 199): i + 1],
                h_close[max(0, i - 199): i + 1]) or spot * 0.003

        # Oscillator steering: deeply oversold -> bounce near -> expect a
        # shallow dip; neutral -> deeper support cluster.
        depth_atr = params["depth_atr_oversold"] if os_v >= params["os_deep_votes"] \
            else params["depth_atr_neutral"]
        anchor = spot - depth_atr * a
        if params.get("use_zone_snap", True):
            supports = [c for c in clusters
                        if c["level"] < spot and c["strength"] >= params["min_zone_strength"]]
            if supports:
                bhat = min(supports, key=lambda c: abs(c["level"] - anchor))["level"]
                if (spot - bhat) / spot > params["max_depth_pct"]:
                    bhat = anchor
            else:
                bhat = anchor
        else:
            bhat = anchor
        resistances = [c for c in clusters if c["level"] > spot]
        target = min(resistances, key=lambda c: c["level"])["level"] if resistances \
            else spot + params["depth_atr_neutral"] * a

        # Ground truth over next HORIZON candles.
        lo10 = min(h_low[i + 1: i + 1 + HORIZON])
        z["signals"] += 1
        z["err_model"].append(abs(bhat - lo10) / lo10 * 100)
        z["err_naive_spot"].append(abs(spot - lo10) / lo10 * 100)
        z["err_naive_atr"].append(abs((spot - a) - lo10) / lo10 * 100)

        # Fill + outcome (15m-resolved where available).
        fill_at = None
        for j in range(i + 1, i + 1 + HORIZON):
            if any(sl <= bhat for _sh, sl in granular_low_high(j)):
                fill_at = j
                break
        if fill_at is not None:
            z["fills"] += 1
            hi_after = max(h_high[fill_at: i + 1 + HORIZON])
            z["bounce_pct"].append((hi_after - bhat) / bhat * 100)
            exit_px = h_close[i + HORIZON]
            for j in range(fill_at, i + 1 + HORIZON):
                if any(sh >= target for sh, _sl in granular_low_high(j)):
                    exit_px = target
                    break
            pnl = exit_px - bhat - params["cost_per_trade_usd"]
            z["pnl"] += pnl
            z["wins" if pnl > 0 else "losses"] += 1

    def summary(z):
        ns = max(len(z["err_model"]), 1)
        def curve(errs):
            return {f"<={b}%": round(sum(1 for e in errs if e <= b) / ns * 100, 1)
                    for b in TOL_BANDS}
        fills = max(z["fills"], 1)
        return {
            "signals": z["signals"], "suppressed_overbought": z["suppressed_ob"],
            "tolerance_curve_model": curve(z["err_model"]),
            "tolerance_curve_naive_spot": curve(z["err_naive_spot"]),
            "tolerance_curve_naive_atr": curve(z["err_naive_atr"]),
            "median_err_pct": round(sorted(z["err_model"])[ns // 2], 3) if z["err_model"] else None,
            "fill_rate_pct": round(z["fills"] / max(z["signals"], 1) * 100, 1),
            "avg_bounce_after_fill_pct": round(sum(z["bounce_pct"]) / fills, 3) if z["bounce_pct"] else None,
            "trades": {"fills": z["fills"], "wins": z["wins"], "losses": z["losses"],
                       "win_rate_pct": round(z["wins"] / fills * 100, 1),
                       "pnl_usd_per_oz": round(z["pnl"], 2)},
        }

    return {"objective": f"best-buy over next {HORIZON} candles",
            "hours": n, "split_at": split,
            **{s: summary(Z[s]) for s in segs}}


def main():
    params = json.loads(Path(sys.argv[1]).read_text())
    data = json.loads(HISTORY.read_text())
    m15_map = None
    if len(sys.argv) > 3 and sys.argv[3] != "-":
        m15_map = load_m15(sys.argv[3], min_ts=data["gold_hourly"]["ts"][0])
    result = run(params, data, m15_map)
    result["params"] = params
    out = json.dumps(result, indent=2)
    print(out)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(out + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
