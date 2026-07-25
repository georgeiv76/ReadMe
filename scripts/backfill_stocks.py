#!/usr/bin/env python3
"""Fetch last week's hourly + daily candles for AAPL, GOOGL, MSFT.

Reuses the hardened multi-source fetcher (Yahoo with retries/mirrors,
stooq CSV fallback). Writes gold-intel/data/stocks_week.json.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backfill_history import series  # noqa: E402
from collect_gold_data import REPO_ROOT  # noqa: E402

OUT = REPO_ROOT / "gold-intel" / "data" / "stocks_week.json"
SYMBOLS = {
    "AAPL": ("AAPL", "aapl.us"),
    "GOOGL": ("GOOGL", "googl.us"),
    "MSFT": ("MSFT", "msft.us"),
}


def main():
    out = {"created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "errors": []}
    ok = 0
    for name, (ysym, ssym) in SYMBOLS.items():
        try:
            out[name + "_hourly"] = series(ysym, "5d", "1h", ssym, "h")
            out[name + "_daily"] = series(ysym, "1mo", "1d", ssym, "d")
            ok += 1
        except Exception as exc:  # noqa: BLE001
            out["errors"].append(f"{name}: {exc}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out) + "\n")
    print({k: v.get("n") for k, v in out.items() if isinstance(v, dict)}, out["errors"])
    return 0 if ok == 3 else 1


if __name__ == "__main__":
    sys.exit(main())
