#!/usr/bin/env python3
"""Backfill 12 months of hourly XAU/USD candles from Dukascopy's public feed.

Dukascopy serves per-day files of 1-minute BID candles as LZMA-compressed
binary (.bi5): 24-byte big-endian records. No API key, CDN-friendly.
URL pattern (month is ZERO-BASED):
  https://datafeed.dukascopy.com/datafeed/XAUUSD/{YYYY}/{MM0}/{DD}/BID_candles_min_1.bi5

Records are (time_offset, open, close, low, high, volume) with integer prices
scaled by an instrument point value. Both the field order and the scale are
auto-detected against sanity checks rather than assumed, and the offset unit
(ms vs s) is detected from its magnitude. Minute candles are aggregated to
hourly; daily candles are derived from the hourly series (UTC days).

Output schema matches backfill_history.py: gold-intel/data/history_12mo.json.
"""

import json
import lzma
import struct
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_gold_data import REPO_ROOT, UA  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "gold-intel" / "data" / "history_12mo.json"
INSTRUMENT = sys.argv[2] if len(sys.argv) > 2 else "XAUUSD"
DAYS = int(sys.argv[3]) if len(sys.argv) > 3 else 370
BASE = ("https://datafeed.dukascopy.com/datafeed/" + INSTRUMENT
        + "/{y}/{m0:02d}/{d:02d}/BID_candles_min_1.bi5")
PRICE_SCALES = (0.001, 0.01, 0.00001)   # XAUUSD point is 0.001; others = safety net
SANE = (5.0, 20000.0)  # silver trades in double digits                 # plausible gold price range


def fetch_raw(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def detect_layout(rows_raw):
    """Pick (field_order, scale) that satisfies OHLC sanity on sample rows.

    Candidate orders map record ints [a,b,c,d] (after time) to (o, c, l, h).
    """
    orders = {
        "oclh": lambda r: (r[0], r[1], r[2], r[3]),
        "ohlc": lambda r: (r[0], r[3], r[2], r[1]),
    }
    for scale in PRICE_SCALES:
        for name, pick in orders.items():
            ok = 0
            total = 0
            for r in rows_raw[:200]:
                o, c, l, h = (x * scale for x in pick(r[1:5]))
                if not (SANE[0] <= o <= SANE[1]):
                    break
                total += 1
                if l <= min(o, c) + 1e-9 and h >= max(o, c) - 1e-9 and l <= h:
                    ok += 1
            if total >= 50 and ok / total > 0.98:
                return name, scale
    return None, None


def parse_day(raw, day_start_ts, layout):
    data = lzma.decompress(raw)
    rows = [struct.unpack_from(">iiiiif", data, off) for off in range(0, len(data) - 23, 24)]
    if not rows:
        return [], layout
    if layout == (None, None):
        layout = detect_layout(rows)
        if layout == (None, None):
            raise ValueError("could not detect bi5 layout")
    name, scale = layout
    pick = (lambda r: (r[0], r[1], r[2], r[3])) if name == "oclh" else (lambda r: (r[0], r[3], r[2], r[1]))
    unit = 0.001 if rows[-1][0] > 200000 else 1.0   # offset in ms vs s
    out = []
    for r in rows:
        o, c, l, h = (x * scale for x in pick(r[1:5]))
        if not (SANE[0] <= c <= SANE[1]):
            continue
        out.append((day_start_ts + int(r[0] * unit), o, c, l, h))
    return out, layout


def aggregate_hourly(minutes):
    """Minute candles -> hourly (ts floored to hour, close/high/low)."""
    hours = {}
    for ts, _o, c, l, h in minutes:
        hk = ts - ts % 3600
        cur = hours.get(hk)
        if cur is None:
            hours[hk] = [c, h, l, ts]
        else:
            if ts >= cur[3]:
                cur[0], cur[3] = c, ts
            cur[1] = max(cur[1], h)
            cur[2] = min(cur[2], l)
    return sorted((k, v[0], v[1], v[2]) for k, v in hours.items())


def main():
    now = datetime.now(timezone.utc)
    layout = (None, None)
    all_minutes = []
    fetched = empty = failed = 0
    day = (now - timedelta(days=DAYS)).date()
    while day < now.date():
        dt = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        url = BASE.format(y=day.year, m0=day.month - 1, d=day.day)
        try:
            raw = fetch_raw(url)
            if raw:
                minutes, layout = parse_day(raw, int(dt.timestamp()), layout)
                all_minutes.extend(minutes)
                fetched += 1
            else:
                empty += 1
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                empty += 1
            else:
                failed += 1
                time.sleep(1)
        except Exception:  # noqa: BLE001
            failed += 1
            time.sleep(1)
        day += timedelta(days=1)

    hourly = aggregate_hourly(all_minutes)
    daily_map = {}
    for ts, c, h, l in hourly:
        dk = ts - ts % 86400
        cur = daily_map.get(dk)
        if cur is None:
            daily_map[dk] = [c, h, l]
        else:
            cur[0] = c
            cur[1] = max(cur[1], h)
            cur[2] = min(cur[2], l)
    daily = sorted((k, v[0], v[1], v[2]) for k, v in daily_map.items())

    out = {
        "created_utc": now.isoformat(timespec="seconds"),
        "errors": [f"days fetched={fetched} empty/closed={empty} failed={failed}"],
        "gold_hourly": {
            "ts": [r[0] for r in hourly], "close": [r[1] for r in hourly],
            "high": [r[2] for r in hourly], "low": [r[3] for r in hourly],
            "n": len(hourly), "src": "dukascopy",
        },
        "gold_daily": {
            "ts": [r[0] for r in daily], "close": [r[1] for r in daily],
            "high": [r[2] for r in daily], "low": [r[3] for r in daily],
            "n": len(daily), "src": "dukascopy-derived",
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out) + "\n")
    print(f"hourly={len(hourly)} daily={len(daily)} fetched={fetched} "
          f"empty={empty} failed={failed} layout={layout}")
    return 0 if len(hourly) > 3000 else 1


if __name__ == "__main__":
    sys.exit(main())
