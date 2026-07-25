#!/usr/bin/env python3
"""Hourly gold market data collector.

Runs on a GitHub Actions runner (open internet). Fetches XAU/USD price history,
US Dollar Index, and Treasury yields; computes the technical indicators used by
the analysis layer (RSI, SMAs, EMAs, MACD, Bollinger, ATR) plus a level engine
(Fibonacci retracements, classic pivot points, MA levels, round numbers) that
clusters everything into confluence zones and derives the strongest buy zone
below price and sell zone above price. Writes gold-intel/data/latest.json and
appends a compact row to gold-intel/data/history.jsonl.

Stdlib only — no pip installs required.
"""

import json
import math
import ssl
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "gold-intel" / "data"

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={rng}&interval={ivl}"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
STOOQ_QUOTE = "https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"

ROUND_STEP = 50  # $50/$100 increments are gold's documented psychological anchors

GOLD_API_SPOT = "https://api.gold-api.com/price/XAU"
SWISSQUOTE_SPOT = "https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD"
FF_CALENDAR = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
GLD_CSV = "https://www.spdrgoldshares.com/assets/dynamic/GLD/GLD_US_archive_EN.csv"


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")


def yahoo_candles(symbol, rng, ivl):
    """Return (timestamps, closes, highs, lows) from Yahoo's chart API."""
    raw = json.loads(fetch(YAHOO_CHART.format(symbol=symbol, rng=rng, ivl=ivl)))
    result = raw["chart"]["result"][0]
    ts = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    rows = [
        (t, c, h, l)
        for t, c, h, l in zip(ts, quote["close"], quote["high"], quote["low"])
        if c is not None and h is not None and l is not None
    ]
    return (
        [r[0] for r in rows],
        [r[1] for r in rows],
        [r[2] for r in rows],
        [r[3] for r in rows],
    )


def stooq_quote(symbol):
    """Fallback spot quote from stooq CSV: symbol,date,time,o,h,l,c,vol."""
    lines = fetch(STOOQ_QUOTE.format(symbol=symbol)).strip().splitlines()
    fields = lines[-1].split(",")
    return float(fields[6])


def fred_latest(series, n=5):
    """Return the last n (date, value) pairs of a FRED series."""
    lines = fetch(FRED_CSV.format(series=series)).strip().splitlines()
    out = []
    for line in lines[1:]:
        date, _, value = line.partition(",")
        if value and value != ".":
            out.append((date, float(value)))
    return out[-n:]


def spot_crosscheck():
    """Independent spot quotes from gold-api.com and Swissquote (best effort)."""
    result = {}
    try:
        result["gold_api"] = float(json.loads(fetch(GOLD_API_SPOT))["price"])
    except Exception as exc:  # noqa: BLE001
        result["gold_api_error"] = str(exc)
    try:
        platforms = json.loads(fetch(SWISSQUOTE_SPOT))
        prices = platforms[0]["spreadProfilePrices"][0]
        result["swissquote_mid"] = (prices["bid"] + prices["ask"]) / 2
    except Exception as exc:  # noqa: BLE001
        result["swissquote_error"] = str(exc)
    return result


def daily_cached(path, fetch_fn, today):
    """Fetch at most once per UTC day; the repo-committed file is the cache.

    Returns (data, error). Serves stale data with an error note on failure.
    """
    cached = None
    if path.exists():
        try:
            cached = json.loads(path.read_text())
        except Exception:  # noqa: BLE001
            cached = None
    if cached and cached.get("fetched_date") == today:
        return cached.get("data"), None
    try:
        data = fetch_fn()
        path.write_text(json.dumps({"fetched_date": today, "data": data}, indent=2) + "\n")
        return data, None
    except Exception as exc:  # noqa: BLE001
        return (cached or {}).get("data"), str(exc)


def ff_calendar_high_impact():
    """This week's high-impact USD events from the ForexFactory feed.

    NOTE: feed is rate-limited to 2 downloads per 5 minutes — only ever call
    through daily_cached().
    """
    events = json.loads(fetch(FF_CALENDAR))
    return [
        {k: ev.get(k) for k in ("title", "date", "impact", "forecast", "previous")}
        for ev in events
        if ev.get("country") == "USD" and ev.get("impact") in ("High", "Medium")
    ]


def gld_tonnes():
    """Latest GLD holdings in tonnes from the SPDR archive CSV.

    The file carries disclaimer preamble rows; locate the header row first.
    """
    lines = fetch(GLD_CSV).strip().splitlines()
    header_idx = next(
        i for i, line in enumerate(lines) if "tonnes" in line.lower()
    )
    header = [h.strip().lower() for h in lines[header_idx].split(",")]
    col = next(i for i, h in enumerate(header) if "tonnes" in h)
    for line in reversed(lines[header_idx + 1:]):
        fields = line.split(",")
        if len(fields) > col:
            try:
                return {"date": fields[0].strip(), "tonnes": float(fields[col])}
            except ValueError:
                continue
    raise ValueError("no parsable GLD rows")


# --------------------------------------------------------------------------
# Indicators
# --------------------------------------------------------------------------

def sma(values, period):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period


def ema_series(values, period):
    if len(values) < period:
        return None
    k = 2 / (period + 1)
    e = sum(values[:period]) / period
    series = [e]
    for v in values[period:]:
        e = v * k + e * (1 - k)
        series.append(e)
    return series


def rsi(values, period=14):
    """Wilder-smoothed RSI."""
    if len(values) < period + 1:
        return None
    deltas = [values[i + 1] - values[i] for i in range(len(values) - 1)]
    gains = [max(d, 0) for d in deltas]
    losses = [max(-d, 0) for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for g, l in zip(gains[period:], losses[period:]):
        avg_gain = (avg_gain * (period - 1) + g) / period
        avg_loss = (avg_loss * (period - 1) + l) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def macd(values, fast=12, slow=26, signal=9):
    ema_fast = ema_series(values, fast)
    ema_slow = ema_series(values, slow)
    if not ema_fast or not ema_slow:
        return None
    # Align: ema_slow starts (slow - fast) steps later than ema_fast.
    offset = slow - fast
    macd_line = [f - s for f, s in zip(ema_fast[offset:], ema_slow)]
    sig_series = ema_series(macd_line, signal)
    if not sig_series:
        return None
    return {
        "macd": macd_line[-1],
        "signal": sig_series[-1],
        "histogram": macd_line[-1] - sig_series[-1],
    }


def bollinger(values, period=20, mult=2.0):
    if len(values) < period:
        return None
    window = values[-period:]
    mid = sum(window) / period
    sd = (sum((v - mid) ** 2 for v in window) / period) ** 0.5
    return {"mid": mid, "upper": mid + mult * sd, "lower": mid - mult * sd}


def atr(highs, lows, closes, period=14):
    """Wilder-smoothed Average True Range."""
    if len(closes) < period + 1:
        return None
    trs = [
        max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        for i in range(1, len(closes))
    ]
    a = sum(trs[:period]) / period
    for tr in trs[period:]:
        a = (a * (period - 1) + tr) / period
    return a


def indicator_block(closes):
    block = {
        "close": closes[-1],
        "rsi14": rsi(closes),
        "sma20": sma(closes, 20),
        "sma50": sma(closes, 50),
        "sma200": sma(closes, 200),
        "macd_12_26_9": macd(closes),
    }
    ema20 = ema_series(closes, 20)
    block["ema20"] = ema20[-1] if ema20 else None
    return block


def pct_change(closes, lookback):
    if len(closes) <= lookback:
        return None
    prev = closes[-1 - lookback]
    return (closes[-1] - prev) / prev * 100


# --------------------------------------------------------------------------
# Level engine: Fibonacci, pivots, round numbers, confluence clustering
# --------------------------------------------------------------------------

def pivot_points(prev_high, prev_low, prev_close):
    """Classic floor-trader pivots from the previous completed daily candle."""
    p = (prev_high + prev_low + prev_close) / 3
    rng = prev_high - prev_low
    return {
        "P": p,
        "R1": 2 * p - prev_low,
        "S1": 2 * p - prev_high,
        "R2": p + rng,
        "S2": p - rng,
        "R3": prev_high + 2 * (p - prev_low),
        "S3": prev_low - 2 * (prev_high - p),
    }


def fib_retracements(swing_high, swing_low):
    """Retracement levels of the swing_low -> swing_high move (uptrend view)."""
    diff = swing_high - swing_low
    return {
        "swing_high": swing_high,
        "swing_low": swing_low,
        "levels": {
            "23.6%": swing_high - diff * 0.236,
            "38.2%": swing_high - diff * 0.382,
            "50.0%": swing_high - diff * 0.500,
            "61.8%": swing_high - diff * 0.618,
            "78.6%": swing_high - diff * 0.786,
        },
    }


def collect_levels(spot, daily_ind, pivots, fib_daily, fib_hourly, boll_1h):
    levels = []

    def add(name, value):
        if value is not None and value > 0:
            levels.append({"name": name, "level": round(float(value), 2)})

    for k, v in pivots.items():
        add(f"pivot_{k}", v)
    for k, v in fib_daily["levels"].items():
        add(f"fib_daily_{k}", v)
    for k, v in fib_hourly["levels"].items():
        add(f"fib_1h_{k}", v)
    if boll_1h:
        add("bollinger_1h_upper", boll_1h["upper"])
        add("bollinger_1h_lower", boll_1h["lower"])
    for key in ("sma20", "sma50", "sma200"):
        add(f"daily_{key}", daily_ind.get(key))
    add("round_below", math.floor(spot / ROUND_STEP) * ROUND_STEP)
    add("round_above", math.ceil(spot / ROUND_STEP) * ROUND_STEP)
    add("fib_daily_swing_high", fib_daily["swing_high"])
    add("fib_daily_swing_low", fib_daily["swing_low"])
    return levels


def cluster_levels(levels, spot, tol_pct=0.0015):
    """Merge levels within tol_pct of each other into confluence clusters."""
    clusters = []
    for lv in sorted(levels, key=lambda x: x["level"]):
        if clusters and abs(lv["level"] - clusters[-1]["level"]) <= spot * tol_pct:
            c = clusters[-1]
            c["members"].append(lv["name"])
            n = len(c["members"])
            c["level"] = round((c["level"] * (n - 1) + lv["level"]) / n, 2)
        else:
            clusters.append({"level": lv["level"], "members": [lv["name"]]})
    for c in clusters:
        c["strength"] = len(c["members"])
    return clusters


def best_zones(clusters, spot):
    """Strongest confluence support below spot and resistance above spot.

    Prefer clusters within 1.5% of price; widen to 3%; else take the nearest.
    Strength (member count) wins; proximity breaks ties.
    """

    def pick(cands):
        for max_dist in (0.015, 0.03, None):
            pool = [
                c for c in cands
                if max_dist is None or abs(c["level"] - spot) / spot <= max_dist
            ]
            if pool:
                return max(pool, key=lambda c: (c["strength"], -abs(c["level"] - spot)))
        return None

    supports = [c for c in clusters if c["level"] < spot]
    resistances = [c for c in clusters if c["level"] > spot]
    return pick(supports), pick(resistances)


# --------------------------------------------------------------------------


def main():
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = {"collected_at_utc": now, "errors": []}

    # --- Gold: hourly and daily candles (XAUUSD=X primary, GC=F fallback) ---
    gold_symbol = None
    for symbol in ("XAUUSD=X", "GC=F"):
        try:
            h_ts, h_close, h_high, h_low = yahoo_candles(symbol, "1mo", "1h")
            d_ts, d_close, d_high, d_low = yahoo_candles(symbol, "2y", "1d")
            gold_symbol = symbol
            break
        except Exception as exc:  # noqa: BLE001 - collector must never die on one source
            out["errors"].append(f"yahoo {symbol}: {exc}")
    if gold_symbol is None:
        try:
            spot = stooq_quote("xauusd")
            out["gold"] = {"source": "stooq-spot-only", "spot": spot}
        except Exception as exc:  # noqa: BLE001
            out["errors"].append(f"stooq xauusd: {exc}")
            out["gold"] = None
    else:
        spot = h_close[-1]
        daily_ind = indicator_block(d_close)

        # Previous COMPLETED daily candle for pivots (last candle may be live).
        pivots = pivot_points(d_high[-2], d_low[-2], d_close[-2])
        # Fib swings: daily = last 90 sessions; hourly = last ~5 trading days.
        fib_daily = fib_retracements(max(d_high[-90:]), min(d_low[-90:]))
        fib_hourly = fib_retracements(max(h_high[-120:]), min(h_low[-120:]))
        boll_1h = bollinger(h_close)
        atr_1h = atr(h_high, h_low, h_close)

        levels = collect_levels(spot, daily_ind, pivots, fib_daily, fib_hourly, boll_1h)
        clusters = cluster_levels(levels, spot)
        buy_zone, sell_zone = best_zones(clusters, spot)

        out["gold"] = {
            "source": f"yahoo:{gold_symbol}",
            "spot": spot,
            "hourly": indicator_block(h_close),
            "daily": daily_ind,
            "change_pct": {
                "1h": pct_change(h_close, 1),
                "24h": pct_change(h_close, 24),
                "5d_daily": pct_change(d_close, 5),
            },
            "recent_hourly_closes": h_close[-24:],
            "day_high": max(h_high[-24:]),
            "day_low": min(h_low[-24:]),
            "atr14_1h": atr_1h,
            "bollinger_1h_20_2": boll_1h,
            "levels": {
                "pivots_classic": pivots,
                "fib_daily_90d": fib_daily,
                "fib_hourly_5d": fib_hourly,
                "all_levels": levels,
                "confluence_clusters": clusters,
                "best_buy_zone": buy_zone,
                "best_sell_zone": sell_zone,
            },
        }

    # --- US Dollar Index ---
    try:
        _, dxy_close, _, _ = yahoo_candles("DX-Y.NYB", "3mo", "1d")
        out["dxy"] = {
            "spot": dxy_close[-1],
            "sma20": sma(dxy_close, 20),
            "change_5d_pct": pct_change(dxy_close, 5),
        }
    except Exception as exc:  # noqa: BLE001
        out["errors"].append(f"dxy: {exc}")
        out["dxy"] = None

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date().isoformat()

    # --- Yields: 10Y nominal and 10Y TIPS real (daily data; fetched once/day) ---
    for key, series in (("us10y_nominal", "DGS10"), ("us10y_real_tips", "DFII10")):
        def fetch_series(series=series):
            hist = fred_latest(series)
            return {"latest": hist[-1][1], "date": hist[-1][0], "history": hist}

        data, err = daily_cached(DATA_DIR / f"cache_{series}.json", fetch_series, today)
        if err:
            out["errors"].append(f"{series}: {err}")
        out[key] = data

    # --- Independent spot cross-check (gold-api.com + Swissquote) ---
    out["spot_crosscheck"] = spot_crosscheck()
    gold_block = out.get("gold")
    ref = out["spot_crosscheck"].get("gold_api") or out["spot_crosscheck"].get("swissquote_mid")
    if gold_block and gold_block.get("spot") and ref:
        div = abs(gold_block["spot"] - ref) / ref * 100
        out["spot_crosscheck"]["divergence_pct_vs_primary"] = round(div, 3)
        if div > 0.5:
            out["errors"].append(
                f"spot divergence {div:.2f}% between {gold_block['source']} and cross-check"
            )

    # --- This week's high-impact US calendar (rate-limited feed; daily cache) ---
    cal, err = daily_cached(DATA_DIR / "cache_calendar.json", ff_calendar_high_impact, today)
    if err:
        out["errors"].append(f"calendar: {err}")
    out["us_calendar_week"] = cal

    # --- GLD holdings tonnage (daily EOD series; daily cache) ---
    gld, err = daily_cached(DATA_DIR / "cache_gld.json", gld_tonnes, today)
    if err:
        out["errors"].append(f"gld: {err}")
    out["gld_holdings"] = gld
    (DATA_DIR / "latest.json").write_text(json.dumps(out, indent=2) + "\n")

    gold = out.get("gold") or {}
    hourly = gold.get("hourly") or {}
    zones = (gold.get("levels") or {})
    compact = {
        "t": now,
        "spot": gold.get("spot"),
        "rsi14_1h": hourly.get("rsi14"),
        "buy_zone": (zones.get("best_buy_zone") or {}).get("level"),
        "sell_zone": (zones.get("best_sell_zone") or {}).get("level"),
        "dxy": (out.get("dxy") or {}).get("spot"),
        "real10y": (out.get("us10y_real_tips") or {}).get("latest"),
    }
    with (DATA_DIR / "history.jsonl").open("a") as fh:
        fh.write(json.dumps(compact) + "\n")

    print(json.dumps(compact))
    if out["gold"] is None:
        print("FATAL: no gold price from any source", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
