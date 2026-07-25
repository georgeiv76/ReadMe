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
from collect_gold_data import fib_retracements  # noqa: E402

HISTORY = Path(__file__).resolve().parent.parent / "gold-intel" / "data" / "history_12mo.json"


def ema_full(values, period):
    k = 2 / (period + 1)
    out = [values[0]]
    for v in values[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def adx_series(H, L, C, p=14):
    n = len(C)
    adx = [None] * n
    if n <= 2 * p + 1:
        return adx
    tr = [0.0] * n
    pdm = [0.0] * n
    ndm = [0.0] * n
    for i in range(1, n):
        up, dn = H[i] - H[i - 1], L[i - 1] - L[i]
        pdm[i] = up if (up > dn and up > 0) else 0.0
        ndm[i] = dn if (dn > up and dn > 0) else 0.0
        tr[i] = max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1]))
    a, pd_, nd_ = sum(tr[1: p + 1]), sum(pdm[1: p + 1]), sum(ndm[1: p + 1])
    dxs = []
    for i in range(p + 1, n):
        a = a - a / p + tr[i]
        pd_ = pd_ - pd_ / p + pdm[i]
        nd_ = nd_ - nd_ / p + ndm[i]
        pdi = 100 * pd_ / a if a > 0 else 0
        ndi = 100 * nd_ / a if a > 0 else 0
        dx = 100 * abs(pdi - ndi) / (pdi + ndi) if (pdi + ndi) > 0 else 0
        dxs.append(dx)
        if len(dxs) == p:
            adx[i] = sum(dxs) / p
        elif len(dxs) > p:
            adx[i] = (adx[i - 1] * (p - 1) + dx) / p
    return adx


def vwap_by_hour(m15_path, min_ts):
    """Hour-ts -> session VWAP (UTC-day reset) from the 15m file's volume."""
    import csv
    import gzip
    from datetime import datetime as dtt, timezone as tz

    out = {}
    cur_day, s_pv, s_v = None, 0.0, 0.0
    with gzip.open(m15_path, "rt") as fh:
        rdr = csv.reader(fh, delimiter=";")
        next(rdr)
        for f in rdr:
            try:
                dt = dtt.strptime(f[0], "%Y.%m.%d %H:%M").replace(tzinfo=tz.utc)
                ts = int(dt.timestamp()) - 2 * 3600
                if ts < min_ts:
                    continue
                px = (float(f[2]) + float(f[3]) + float(f[4])) / 3
                v = float(f[5])
            except (ValueError, IndexError):
                continue
            day = ts // 86400
            if day != cur_day:
                cur_day, s_pv, s_v = day, 0.0, 0.0
            s_pv += px * v
            s_v += v
            if s_v > 0:
                out[ts - ts % 3600] = s_pv / s_v
    return out


def run(params, data):
    h = data["gold_hourly"]
    live = [i for i in range(len(h["ts"])) if abs(h["high"][i] - h["low"][i]) > 1e-9]
    C = [h["close"][i] for i in live]
    Hh = [h["high"][i] for i in live]
    Lh = [h["low"][i] for i in live]
    from datetime import datetime, timezone
    TS = [h["ts"][i] for i in live]
    MONTH = [datetime.fromtimestamp(t, tz=timezone.utc).month for t in TS]
    skip_months = set(params.get("skip_months", []))
    n = len(C)

    # COT crowded-positioning gate: block new longs when managed-money net
    # length sits at/above cot_block_pctile of its own PRIOR reports
    # (expanding window, report usable 3 days after its date — no lookahead).
    cot_blocked = [False] * n
    if params.get("cot_file"):
        import bisect
        rows = json.loads(Path(params["cot_file"]).read_text())["rows"]
        eff = sorted(
            (int(datetime.fromisoformat(w["date"]).replace(tzinfo=timezone.utc)
                 .timestamp()) + 3 * 86400, w["mm_net"])
            for w in rows
        )
        eff_ts = [e[0] for e in eff]
        nets = [e[1] for e in eff]
        thr = params.get("cot_block_pctile", 90)
        for i in range(n):
            idx = bisect.bisect_right(eff_ts, TS[i]) - 1
            if idx >= 20:
                cur = nets[idx]
                hist = nets[: idx + 1]
                pct = sum(1 for v in hist if v <= cur) / len(hist) * 100
                cot_blocked[i] = pct >= thr
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

    # --- 'Fib + one index at a time' entry confirmations ---
    extra = params.get("extra_index", "none")
    combo = params.get("combo", [])
    active = set(combo) | ({extra} if extra != "none" else set())
    fib_gate = params.get("fib_gate", False)
    fib_tol = params.get("fib_tol_pct", 0.15)
    EMA9 = EMA21 = ADXS = HIST = PIV = VW = None
    if "ema" in active:
        EMA9, EMA21 = ema_full(C, 9), ema_full(C, 21)
    if "adx" in active:
        ADXS = adx_series(Hh, Lh, C)
    if "macd" in active:
        e12, e26 = ema_full(C, 12), ema_full(C, 26)
        line = [a - b for a, b in zip(e12, e26)]
        sig = ema_full(line, 9)
        HIST = [m - s for m, s in zip(line, sig)]
    if "pivot" in active:
        d = data["gold_daily"]
        d_dates = [datetime.fromtimestamp(t, tz=timezone.utc).date() for t in d["ts"]]
        PIV = [None] * n
        j = 0
        for i2 in range(n):
            hd = datetime.fromtimestamp(TS[i2], tz=timezone.utc).date()
            while j + 1 < len(d_dates) and d_dates[j + 1] < hd:
                j += 1
            pj = j if d_dates[j] < hd else max(0, j - 1)
            PIV[i2] = (d["high"][pj] + d["low"][pj] + d["close"][pj]) / 3
    if "vwap" in active:
        VW = vwap_by_hour(params["m15_file"], TS[0])

    def check(name, i):
        if name == "ema":
            return EMA9[i] > EMA21[i]
        if name == "adx":
            return ADXS[i] is not None and ADXS[i] < params.get("adx_max", 30)
        if name == "macd":
            return HIST[i] > HIST[i - 1]
        if name == "pivot":
            return C[i] > PIV[i]
        if name == "vwap":
            v = VW.get(TS[i])
            return True if v is None else C[i] > v   # pass-through where no volume data
        return True

    def extra_ok(i):
        if combo:
            votes = sum(check(x, i) for x in combo)
            return votes >= params.get("combo_min_votes", 1)
        return check(extra, i)

    def fib_ok(i):
        if not fib_gate:
            return True
        fibs = fib_retracements(
            max(Hh[max(0, i - 119): i + 1]), min(Lh[max(0, i - 119): i + 1])
        )["levels"].values()
        return any(abs(C[i] - f) / C[i] * 100 <= fib_tol for f in fibs)

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
            if (up and k_prev < os_th <= k and MONTH[i] not in skip_months
                    and not cot_blocked[i] and fib_ok(i) and extra_ok(i)):
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
