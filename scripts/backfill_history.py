#!/usr/bin/env python3
"""One-shot backfill of ~12 months of market history for model training.

Runs on a GitHub Actions runner (open internet). Fetches a year of hourly
XAU/USD candles (plus futures fallback), two years of daily candles, DXY,
and FRED yields; writes gold-intel/data/history_12mo.json for the local
self-learning loop. Stdlib only.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_gold_data import FRED_CSV, REPO_ROOT, fetch, yahoo_candles  # noqa: E402

OUT = REPO_ROOT / "gold-intel" / "data" / "history_12mo.json"


def series(symbol, rng, ivl):
    ts, close, high, low = yahoo_candles(symbol, rng, ivl)
    return {"ts": ts, "close": close, "high": high, "low": low, "n": len(ts)}


def fred_series(sid, start="2025-07-01"):
    lines = fetch(FRED_CSV.format(series=sid) + f"&cosd={start}").strip().splitlines()
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
    for key, sym in (("gold", "XAUUSD=X"), ("gold_fut", "GC=F")):
        try:
            out[key + "_hourly"] = series(sym, "1y", "1h")
            out[key + "_daily"] = series(sym, "2y", "1d")
        except Exception as exc:  # noqa: BLE001
            out["errors"].append(f"{sym}: {exc}")
    try:
        out["dxy_daily"] = series("DX-Y.NYB", "1y", "1d")
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
