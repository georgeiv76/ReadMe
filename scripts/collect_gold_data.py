#!/usr/bin/env python3
"""Hourly gold market data collector.

Runs on a GitHub Actions runner (open internet). Fetches XAU/USD price history,
US Dollar Index, and Treasury yields; computes the technical indicators used by
the analysis layer (RSI, SMAs, EMAs, MACD); writes gold-intel/data/latest.json
and appends a compact row to gold-intel/data/history.jsonl.

Stdlib only — no pip installs required.
"""

import json
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
        if c is not None
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


def main():
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out = {"collected_at_utc": now, "errors": []}

    # --- Gold: hourly and daily candles (XAUUSD=X primary, GC=F fallback) ---
    gold_symbol = None
    for symbol in ("XAUUSD=X", "GC=F"):
        try:
            h_ts, h_close, h_high, h_low = yahoo_candles(symbol, "1mo", "1h")
            d_ts, d_close, _, _ = yahoo_candles(symbol, "2y", "1d")
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
        out["gold"] = {
            "source": f"yahoo:{gold_symbol}",
            "spot": h_close[-1],
            "hourly": indicator_block(h_close),
            "daily": indicator_block(d_close),
            "change_pct": {
                "1h": pct_change(h_close, 1),
                "24h": pct_change(h_close, 24),
                "5d_daily": pct_change(d_close, 5),
            },
            "recent_hourly_closes": h_close[-24:],
            "day_high": max(h_high[-24:]),
            "day_low": min(h_low[-24:]),
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

    # --- Yields: 10Y nominal and 10Y TIPS real ---
    for key, series in (("us10y_nominal", "DGS10"), ("us10y_real_tips", "DFII10")):
        try:
            hist = fred_latest(series)
            out[key] = {"latest": hist[-1][1], "date": hist[-1][0], "history": hist}
        except Exception as exc:  # noqa: BLE001
            out["errors"].append(f"{series}: {exc}")
            out[key] = None

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "latest.json").write_text(json.dumps(out, indent=2) + "\n")

    gold = out.get("gold") or {}
    hourly = gold.get("hourly") or {}
    compact = {
        "t": now,
        "spot": gold.get("spot"),
        "rsi14_1h": hourly.get("rsi14"),
        "sma50_1h": hourly.get("sma50"),
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
