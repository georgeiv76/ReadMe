#!/usr/bin/env python3
"""Hour-by-hour replay test of the levels engine for one trading day.

For every hourly candle of the target date (UTC), computes the levels the
engine would have shown AT THAT HOUR — using only data available up to that
hour (no lookahead): pivots from the previous completed daily candle,
Fibonacci swings from trailing windows, trailing SMAs/Bollinger, round
numbers. Then grades each hour's zones against the following hour's actual
high/low: did price reach the buy zone, the sell zone, neither?

Runs on a GitHub Actions runner (open internet). Usage:
    python scripts/replay_day.py [YYYY-MM-DD]   # default: most recent Friday

Writes gold-intel/briefs/REPLAY_<date>.md.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_gold_data import (  # noqa: E402
    REPO_ROOT,
    atr,
    best_zones,
    cluster_levels,
    collect_levels,
    fib_retracements,
    indicator_block,
    pivot_points,
    bollinger,
    rsi,
    yahoo_candles,
)


def last_friday(today):
    d = today
    while d.weekday() != 4:
        d -= timedelta(days=1)
    return d


def fmt_zone(zone):
    if not zone:
        return "n/a"
    members = ", ".join(zone["members"])
    return f"${zone['level']:,.2f} ({members})"


def main():
    now = datetime.now(timezone.utc)
    if len(sys.argv) > 1:
        target = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
    else:
        target = last_friday(now.date())

    symbol_used = None
    for symbol in ("XAUUSD=X", "GC=F"):
        try:
            h_ts, h_close, h_high, h_low = yahoo_candles(symbol, "1mo", "1h")
            d_ts, d_close, d_high, d_low = yahoo_candles(symbol, "2y", "1d")
            symbol_used = symbol
            break
        except Exception as exc:  # noqa: BLE001
            print(f"warn: {symbol}: {exc}", file=sys.stderr)
    if symbol_used is None:
        print("FATAL: no candle source reachable", file=sys.stderr)
        return 1

    day_idx = [
        i for i, t in enumerate(h_ts)
        if datetime.fromtimestamp(t, tz=timezone.utc).date() == target
    ]
    if not day_idx:
        print(f"FATAL: no hourly candles for {target}", file=sys.stderr)
        return 1

    # Daily candles strictly before the target date, for pivots/regime.
    d_cut = max(
        i for i, t in enumerate(d_ts)
        if datetime.fromtimestamp(t, tz=timezone.utc).date() < target
    )
    pivots = pivot_points(d_high[d_cut], d_low[d_cut], d_close[d_cut])
    daily_ind = indicator_block(d_close[: d_cut + 1])
    fib_daily = fib_retracements(
        max(d_high[max(0, d_cut - 89): d_cut + 1]),
        min(d_low[max(0, d_cut - 89): d_cut + 1]),
    )

    rows = []
    hits = {"buy": 0, "sell": 0, "either": 0, "graded": 0}
    for i in day_idx:
        closes = h_close[: i + 1]
        spot = closes[-1]
        fib_hourly = fib_retracements(
            max(h_high[max(0, i - 119): i + 1]),
            min(h_low[max(0, i - 119): i + 1]),
        )
        boll = bollinger(closes)
        levels = collect_levels(spot, daily_ind, pivots, fib_daily, fib_hourly, boll)
        clusters = cluster_levels(levels, spot)
        buy_zone, sell_zone = best_zones(clusters, spot)
        hour_rsi = rsi(closes)

        outcome = "last bar"
        if i + 1 < len(h_close):
            nxt_high, nxt_low = h_high[i + 1], h_low[i + 1]
            touched_buy = buy_zone and nxt_low <= buy_zone["level"]
            touched_sell = sell_zone and nxt_high >= sell_zone["level"]
            hits["graded"] += 1
            if touched_buy:
                hits["buy"] += 1
            if touched_sell:
                hits["sell"] += 1
            if touched_buy or touched_sell:
                hits["either"] += 1
            outcome = (
                "BUY zone touched" if touched_buy and not touched_sell
                else "SELL zone touched" if touched_sell and not touched_buy
                else "both touched" if touched_buy and touched_sell
                else f"neither (next range {nxt_low:,.0f}–{nxt_high:,.0f})"
            )

        hour = datetime.fromtimestamp(h_ts[i], tz=timezone.utc).strftime("%H:%M")
        rows.append(
            f"| {hour} | ${spot:,.2f} | {hour_rsi:.0f} | {fmt_zone(buy_zone)} "
            f"| {fmt_zone(sell_zone)} | {outcome} |"
        )

    atr_1h = atr(h_high[: day_idx[-1] + 1], h_low[: day_idx[-1] + 1], h_close[: day_idx[-1] + 1])
    out_path = REPO_ROOT / "gold-intel" / "briefs" / f"REPLAY_{target}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        f"# Levels-Engine Replay — {target} (source {symbol_used}, all times UTC)\n\n"
        f"No-lookahead test: each row uses only data available at that hour.\n"
        f"'Outcome' grades the zones against the NEXT hour's actual high/low.\n\n"
        f"Day range: ${min(h_low[i] for i in day_idx):,.2f} – "
        f"${max(h_high[i] for i in day_idx):,.2f} · ATR14(1h) ${atr_1h:,.2f} · "
        f"pivots from previous session H ${d_high[d_cut]:,.2f} / L ${d_low[d_cut]:,.2f} "
        f"/ C ${d_close[d_cut]:,.2f}\n\n"
        "| Hour (UTC) | Price | RSI14 | Best buy zone | Best sell zone | Outcome next hour |\n"
        "|---|---|---|---|---|---|\n"
        + "\n".join(rows)
        + f"\n\nGraded hours: {hits['graded']} · buy zone reached next hour: "
        f"{hits['buy']} · sell zone reached: {hits['sell']} · either: {hits['either']}\n\n"
        f"Reference levels, not guaranteed fills. Generated {now.isoformat(timespec='seconds')}.\n"
    )
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
