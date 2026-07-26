#!/usr/bin/env python3
"""Event study: measure gold's actual reaction to dated events.

Input: JSON list [{"utc": "YYYY-MM-DDTHH:MM", "type": "...", "label": "...",
"hypothesis": "up|down"}]. For each event, from the hourly series: the gold
move at +1h, +6h, +24h after the event bar, expressed in % and as a z-score
against the rolling distribution of same-horizon moves (last 500 bars) —
so 'reaction' means 'unusual move', not just 'a move'.

Output: per-event measurements + per-type aggregates (mean move, hit rate of
the hypothesized direction, mean |z|, n).

Usage: event_study.py events.json out.json
"""

import json
import sys
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path

HISTORY = Path(__file__).resolve().parent.parent / "gold-intel" / "data" / "history_12mo.json"
HORIZONS = (1, 6, 24)


def main():
    events = json.loads(Path(sys.argv[1]).read_text())
    d = json.loads(HISTORY.read_text())["gold_hourly"]
    live = [i for i in range(len(d["ts"])) if abs(d["high"][i] - d["low"][i]) > 1e-9]
    C = [d["close"][i] for i in live]
    TS = [d["ts"][i] for i in live]
    n = len(C)

    def move(i, h):
        j = min(i + h, n - 1)
        return (C[j] - C[i]) / C[i] * 100

    def zscore(i, h, val):
        past = [move(k, h) for k in range(max(0, i - 500), i - h)]
        if len(past) < 50:
            return None
        m = sum(past) / len(past)
        sd = (sum((x - m) ** 2 for x in past) / len(past)) ** 0.5
        return (val - m) / sd if sd > 0 else None

    results = []
    for ev in events:
        try:
            ts = int(datetime.fromisoformat(ev["utc"]).replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            continue
        i = bisect_right(TS, ts) - 1
        if i < 520 or i >= n - 25:
            results.append({**ev, "measured": False, "note": "outside data range"})
            continue
        meas = {}
        for h in HORIZONS:
            mv = move(i, h)
            meas[f"move_{h}h_pct"] = round(mv, 3)
            z = zscore(i, h, mv)
            meas[f"z_{h}h"] = round(z, 2) if z is not None else None
        # phase decomposition: spike (0-1h), digestion (1-6h), resolution (6-24h)
        j1, j6, j24 = min(i+1, n-1), min(i+6, n-1), min(i+24, n-1)
        meas["phase_0_1h"] = round((C[j1]-C[i])/C[i]*100, 3)
        meas["phase_1_6h"] = round((C[j6]-C[j1])/C[j1]*100, 3)
        meas["phase_6_24h"] = round((C[j24]-C[j6])/C[j6]*100, 3)
        results.append({**ev, "measured": True, "price_at_event": round(C[i], 2), **meas})

    by_type = {}
    for r in results:
        if not r.get("measured"):
            continue
        t = by_type.setdefault(r["type"], {"n": 0, "sum6": 0.0, "hits": 0, "absz6": 0.0, "zn": 0})
        t["n"] += 1
        t["sum6"] += r["move_6h_pct"]
        hyp = r.get("hypothesis", "")
        if hyp in ("up", "down"):
            t["hits"] += (r["move_6h_pct"] > 0) == (hyp == "up")
        if r.get("z_6h") is not None:
            t["absz6"] += abs(r["z_6h"])
            t["zn"] += 1
    agg = {
        t: {"n": v["n"], "mean_move_6h_pct": round(v["sum6"] / v["n"], 3),
            "hypothesis_hit_rate_pct": round(v["hits"] / v["n"] * 100, 1),
            "mean_abs_z_6h": round(v["absz6"] / v["zn"], 2) if v["zn"] else None}
        for t, v in by_type.items()
    }
    out = {"events": results, "by_type": agg}
    Path(sys.argv[2]).write_text(json.dumps(out, indent=1))
    print(json.dumps(agg, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
