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


def load_m15(path, min_ts=0):
    """Hour-ts -> ordered [(high, low)] sub-bars from the gz 15m CSV (UTC+2 -> UTC)."""
    import csv
    import gzip

    m15 = {}
    with gzip.open(path, "rt") as fh:
        rdr = csv.reader(fh, delimiter=";")
        next(rdr)
        for f in rdr:
            try:
                dt = datetime.strptime(f[0], "%Y.%m.%d %H:%M").replace(tzinfo=timezone.utc)
                ts = int(dt.timestamp()) - 2 * 3600
                if ts < min_ts:
                    continue
                hi, lo = float(f[2]), float(f[3])
            except (ValueError, IndexError):
                continue
            m15.setdefault(ts - ts % 3600, []).append((hi, lo))
    return m15


def run(params, data, m15_map=None):
    src = "gold_hourly" if data.get("gold_hourly", {}).get("n", 0) > 3000 else "gold_fut_hourly"
    daily_key = "gold_daily" if src == "gold_hourly" else "gold_fut_daily"
    h = data[src]
    d = data[daily_key]
    # Drop dead bars (high == low): closed-market hours padded by the feed.
    # Leaving them in would gift free "perfect" predictions to model AND
    # baseline alike, inflating every accuracy metric.
    live = [
        i for i in range(len(h["ts"]))
        if abs(h["high"][i] - h["low"][i]) > 1e-9
    ]
    h_ts = [h["ts"][i] for i in live]
    h_close = [h["close"][i] for i in live]
    h_high = [h["high"][i] for i in live]
    h_low = [h["low"][i] for i in live]
    d_ts, d_close, d_high, d_low = d["ts"], d["close"], d["high"], d["low"]
    dropped_dead_bars = len(h["ts"]) - len(live)

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
    # Fold attribution: train split into 3 equal walk-forward folds (Critic
    # rule: a trading param earns a holdout look only by winning a majority
    # of folds). Optional trade-quality filters, all off by default.
    min_strength = params.get("min_zone_strength", 1)
    max_dist = params.get("max_zone_dist_pct", 0.015)
    atr_ratio_cap = params.get("atr_regime_max_ratio")
    dow_skip = set(params.get("dow_skip", []))
    fold_size = (split - warmup) // 3

    def bucket(i):
        if i >= split:
            return "holdout"
        return f"fold{min(2, (i - warmup) // fold_size) + 1}"

    def pick_zones(clusters, spot):
        supports = [
            c for c in clusters
            if c["level"] < spot and c["strength"] >= min_strength
        ]
        resistances = [c for c in clusters if c["level"] > spot]

        def pick(cands):
            for md in (max_dist, max_dist * 2, None):
                pool = [
                    c for c in cands
                    if md is None or abs(c["level"] - spot) / spot <= md
                ]
                if pool:
                    return max(pool, key=lambda c: (c["strength"], -abs(c["level"] - spot)))
            return None

        return pick(supports), pick(resistances)

    T = {
        s: {"signals": 0, "fills": 0, "wins": 0, "stops": 0, "timeouts": 0,
            "gross_win": 0.0, "gross_loss": 0.0, "pnl": 0.0}
        for s in ("fold1", "fold2", "fold3", "holdout")
    }
    recent_atrs = []
    i = warmup
    while i < n - 2:
        ctx = day_ctx(i)
        spot = h_close[i]
        if h_dt[i].weekday() in dow_skip:
            i += 1
            continue
        fw = params["fib_hourly_window"]
        fib_h = fib_retracements(
            max(h_high[max(0, i - fw + 1): i + 1]),
            min(h_low[max(0, i - fw + 1): i + 1]),
        )
        boll = bollinger(h_close[max(0, i - 199): i + 1])
        levels = collect_levels(spot, ctx["ind"], ctx["pivots"], ctx["fib"], fib_h, boll)
        clusters = cluster_levels(levels, spot, params["cluster_tol_pct"])
        buy_zone, sell_zone = pick_zones(clusters, spot)
        t = T[bucket(i)]
        if not (buy_zone and sell_zone):
            i += 1
            continue
        atr_now = atr(h_high[max(0, i - 199): i + 1], h_low[max(0, i - 199): i + 1],
                      h_close[max(0, i - 199): i + 1]) or spot * 0.003
        # Regime check against the mean of PRIOR signal ATRs only (the
        # current signal is appended after the check — no self-inclusion).
        blocked = (
            atr_ratio_cap and len(recent_atrs) >= 50
            and atr_now > atr_ratio_cap * (sum(recent_atrs) / len(recent_atrs))
        )
        recent_atrs.append(atr_now)
        if len(recent_atrs) > 200:
            recent_atrs.pop(0)
        if blocked:
            i += 1
            continue
        t["signals"] += 1
        buy_lv, sell_lv = buy_zone["level"], sell_zone["level"]
        stop_lv = buy_lv - params["stop_atr_mult"] * atr_now

        def granular(j):
            """Sub-bars (high, low) for hour j — 15m when available, else 1h."""
            if m15_map:
                subs = m15_map.get(h_ts[j])
                if subs:
                    return subs
            return ((h_high[j], h_low[j]),)

        fill_j = fill_k = None
        for j in range(i + 1, min(i + 1 + params["order_ttl_hours"], n)):
            for k, (_sh, sl) in enumerate(granular(j)):
                if sl <= buy_lv:
                    fill_j, fill_k = j, k
                    break
            if fill_j is not None:
                break
        if fill_j is None:
            i += 1
            continue
        t["fills"] += 1
        exit_j = min(fill_j + params["trade_horizon_hours"], n - 1)
        outcome, exit_px = "timeout", h_close[exit_j]
        done = False
        for j in range(fill_j, exit_j + 1):
            subs = granular(j)
            start = fill_k if j == fill_j else 0
            for sh, sl in subs[start:]:
                if sl <= stop_lv:            # conservative: stop checked first
                    outcome, exit_px, exit_j = "stop", stop_lv, j
                    done = True
                    break
                if sh >= sell_lv:
                    outcome, exit_px, exit_j = "win", sell_lv, j
                    done = True
                    break
            if done:
                break
        pnl = exit_px - buy_lv - params.get("cost_per_trade_usd", 0.0)
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

    def trade_summary(t):
        fills = max(t["fills"], 1)
        return {
            "signals": t["signals"], "fills": t["fills"],
            "win_rate_pct": round(t["wins"] / fills * 100, 2),
            "wins": t["wins"], "stops": t["stops"], "timeouts": t["timeouts"],
            "pnl_usd_per_oz": round(t["pnl"], 2),
            "avg_pnl_per_trade": round(t["pnl"] / fills, 3),
            "profit_factor": round(t["gross_win"] / t["gross_loss"], 3)
            if t["gross_loss"] > 0 else None,
        }

    train_trades = {
        k: sum(T[f][k] for f in ("fold1", "fold2", "fold3"))
        for k in T["fold1"]
    }

    def finalize(s):
        m = M[s]
        t = train_trades if s == "train" else T["holdout"]
        np_, dn = max(m["n_pred"], 1), max(m["dir_n"], 1)
        out = {
            "n_pred": m["n_pred"],
            "mae_usd": round(m["abs_err_usd"] / np_, 3),
            "mae_pct": round(m["abs_err_pct"] / np_, 4),
            "direction_acc_pct": round(m["dir_hit"] / dn * 100, 2),
            "direction_n": m["dir_n"],
            "band_acc_pct": round(m["band_hit"] / np_ * 100, 2),
            "naive_mae_pct": round(m["naive_abs_err_pct"] / np_, 4),
            "naive_band_acc_pct": round(m["naive_band_hit"] / np_ * 100, 2),
            "trades": trade_summary(t),
        }
        if s == "train":
            out["trade_folds"] = {f: trade_summary(T[f]) for f in ("fold1", "fold2", "fold3")}
        return out

    return {
        "source": src,
        "hours": n,
        "dropped_dead_bars": dropped_dead_bars,
        "split_at": split,
        "band_pct_fixed": BAND_PCT,
        "train": finalize("train"),
        "holdout": finalize("holdout"),
    }


def main():
    params_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PARAMS
    params = load_params(params_path)
    data = json.loads(HISTORY.read_text())
    m15_map = None
    if len(sys.argv) > 3 and sys.argv[3] != "-":
        first_ts = data["gold_hourly"]["ts"][0]
        m15_map = load_m15(sys.argv[3], min_ts=first_ts)
    result = run(params, data, m15_map)
    result["m15_resolution_hours"] = len(m15_map) if m15_map else 0
    result["params"] = params
    out = json.dumps(result, indent=2)
    print(out)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(out + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
