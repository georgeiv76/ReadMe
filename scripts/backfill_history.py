#!/usr/bin/env python3
"""One-shot backfill of ~12 months of market history for model training.

Runs on a GitHub Actions runner (open internet). Fetches a year of hourly
XAU/USD candles (plus futures fallback), two years of daily candles, DXY,
and FRED yields; writes gold-intel/data/history_12mo.json for the local
self-learning loop. Stdlib only.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_gold_data import FRED_CSV, REPO_ROOT, fetch  # noqa: E402

OUT = REPO_ROOT / "gold-intel" / "data" / "history_12mo.json"

# GitHub runner IPs are aggressively rate-limited by Yahoo: retry with
# backoff and rotate between the query1/query2 mirror hosts.
YAHOO_HOSTS = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")
BACKOFFS = (5, 15, 45)


def fetch_retry(url_fn, variants):
    last = None
    for attempt, delay in enumerate(BACKOFFS + (None,)):
        variant = variants[attempt % len(variants)]
        try:
            return fetch(url_fn(variant), timeout=60)
        except Exception as exc:  # noqa: BLE001
            last = exc
            if delay is None:
                break
            time.sleep(delay)
    raise last


def yahoo_series(symbol, rng, ivl):
    def url(host):
        return (
            f"https://{host}/v8/finance/chart/{symbol}"
            f"?range={rng}&interval={ivl}"
        )

    raw = json.loads(fetch_retry(url, YAHOO_HOSTS))
    result = raw["chart"]["result"][0]
    ts = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    rows = [
        (t, c, h, l)
        for t, c, h, l in zip(ts, quote["close"], quote["high"], quote["low"])
        if c is not None and h is not None and l is not None
    ]
    return {
        "ts": [r[0] for r in rows],
        "close": [r[1] for r in rows],
        "high": [r[2] for r in rows],
        "low": [r[3] for r in rows],
        "n": len(rows),
        "src": "yahoo",
    }


def stooq_series(symbol, interval):
    """Fallback candle history from stooq CSV (i=d daily, i=h hourly)."""
    def url(_):
        return f"https://stooq.com/q/d/l/?s={symbol}&i={interval}"

    lines = fetch_retry(url, ("stooq",)).strip().splitlines()
    if len(lines) < 10 or "Exceeded" in lines[0]:
        raise ValueError(f"stooq unusable response ({lines[:1]})")
    header = [c.strip().lower() for c in lines[0].split(",")]
    ic = {name: header.index(name) for name in header}
    out = {"ts": [], "close": [], "high": [], "low": [], "src": "stooq"}
    for line in lines[1:]:
        f = line.split(",")
        try:
            date = f[ic["date"]]
            hm = f[ic["time"]] if "time" in ic else "00:00:00"
            dt = datetime.fromisoformat(f"{date}T{hm}").replace(tzinfo=timezone.utc)
            out["ts"].append(int(dt.timestamp()))
            out["close"].append(float(f[ic["close"]]))
            out["high"].append(float(f[ic["high"]]))
            out["low"].append(float(f[ic["low"]]))
        except (KeyError, ValueError, IndexError):
            continue
    out["n"] = len(out["ts"])
    if out["n"] < 10:
        raise ValueError("stooq parse produced too few rows")
    return out


def series(symbol, rng, ivl, stooq_symbol=None, stooq_ivl=None):
    try:
        return yahoo_series(symbol, rng, ivl)
    except Exception as exc:  # noqa: BLE001
        if not stooq_symbol:
            raise
        print(f"yahoo failed for {symbol} ({exc}); trying stooq", file=sys.stderr)
        return stooq_series(stooq_symbol, stooq_ivl or "d")


def fred_series(sid, start="2025-07-01"):
    def url(_):
        return FRED_CSV.format(series=sid) + f"&cosd={start}"

    lines = fetch_retry(url, ("fred",)).strip().splitlines()
    out = []
    for line in lines[1:]:
        d, _, v = line.partition(",")
        if v and v != ".":
            out.append([d, float(v)])
    return out


def main():
    out = {
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "errors": [],
    }
    for key, sym, st_sym in (("gold", "XAUUSD=X", "xauusd"), ("gold_fut", "GC=F", None)):
        try:
            out[key + "_hourly"] = series(sym, "1y", "1h", st_sym, "h")
            out[key + "_daily"] = series(sym, "2y", "1d", st_sym, "d")
        except Exception as exc:  # noqa: BLE001
            out["errors"].append(f"{sym}: {exc}")
        if out.get("gold_hourly", {}).get("n", 0) > 3000:
            break  # primary succeeded; skip the futures fallback entirely
    try:
        out["dxy_daily"] = series("DX-Y.NYB", "1y", "1d", "dx.f", "d")
    except Exception as exc:  # noqa: BLE001
        out["errors"].append(f"dxy: {exc}")
    for sid in ("DGS10", "DFII10"):
        try:
            out[sid.lower()] = fred_series(sid)
        except Exception as exc:  # noqa: BLE001
            out["errors"].append(f"{sid}: {exc}")

    ok = any(
        out.get(k, {}).get("n", 0) > 3000 for k in ("gold_hourly", "gold_fut_hourly")
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out) + "\n")
    print(
        {k: v["n"] for k, v in out.items() if isinstance(v, dict) and "n" in v},
        "errors:", out["errors"],
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
