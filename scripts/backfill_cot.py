#!/usr/bin/env python3
"""Fetch ~14 months of CFTC disaggregated COT for COMEX gold (managed money).

Socrata API, keyless. Writes gold-intel/data/cot_12mo.json with weekly
report_date, managed-money long/short/net, and open interest.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_gold_data import REPO_ROOT, fetch  # noqa: E402

URL = (
    "https://publicreporting.cftc.gov/resource/72hh-3qpy.json"
    "?market_and_exchange_names=GOLD%20-%20COMMODITY%20EXCHANGE%20INC.&$order=report_date_as_yyyy_mm_dd%20DESC&$limit=220"
)
OUT = REPO_ROOT / "gold-intel" / "data" / "cot_12mo.json"


def main():
    rows = json.loads(fetch(URL, timeout=60))
    weekly = []
    for r in rows:
        try:
            long_ = float(r["m_money_positions_long_all"])
            short = float(r["m_money_positions_short_all"])
            weekly.append({
                "date": r["report_date_as_yyyy_mm_dd"][:10],
                "mm_long": long_,
                "mm_short": short,
                "mm_net": long_ - short,
                "open_interest": float(r.get("open_interest_all", 0)),
            })
        except (KeyError, ValueError):
            continue
    weekly.sort(key=lambda x: x["date"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"rows": weekly, "n": len(weekly)}, indent=2) + "\n")
    print(f"cot rows: {len(weekly)} ({weekly[0]['date']} -> {weekly[-1]['date']})" if weekly else "NO ROWS")
    return 0 if len(weekly) > 40 else 1


if __name__ == "__main__":
    sys.exit(main())
