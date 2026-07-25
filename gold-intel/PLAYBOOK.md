# Hourly Gold Scan — Orchestrator Playbook

This is the procedure the Claude orchestrator session executes on every hourly
trigger. It replicates the information-gathering routine of a professional gold
desk: technicals first, then macro, then news/events, combined into one scored
directional bias with a learning feedback loop.

## Constraints this design works around

- The session container **cannot** fetch market data directly (egress policy
  blocks financial domains; only WebSearch and GitHub work).
- Therefore: **GitHub Actions** (`.github/workflows/gold-data.yml`) collects
  numeric data hourly with open internet and commits it to
  `gold-intel/data/latest.json`. The orchestrator reads it from the repo.
- News, Fed communications, and anything qualitative come from **WebSearch**
  via collector subagents.

## Per-run procedure

### 1. Sync and read data
- `git pull` the working branch.
- Read `gold-intel/data/latest.json`. If `collected_at_utc` is older than
  2 hours, treat numeric data as STALE: get spot price via WebSearch
  ("gold price XAU/USD now") and mark `data_quality: degraded` in the log.

### 2. Spawn collector agents (parallel, lean — one WebSearch-driven agent each)
- **News collector**: gold-specific headlines from the last ~2 hours (Kitco,
  Reuters, ForexLive, FXStreet via WebSearch). Wars/geopolitics, central-bank
  gold buying, ETF flow headlines, bank forecasts. Return: 3–6 bullet
  headlines each tagged bullish/bearish/neutral for gold.
- **Macro collector**: DXY direction today, US yields move, Fed speakers
  scheduled today (federalreserve.gov schedule via WebSearch), next major US
  release (CPI/NFP/FOMC/PCE) and its time. Return: structured bullets with a
  bullish/bearish tag for gold each.

### 3. Compute technical bias (deterministic, from latest.json)
Score each signal, sum → `tech_score` (cap ±40):

| Signal | Condition | Points |
|---|---|---|
| Daily regime | spot > daily SMA200 | +15 (else −15) |
| Daily trend | spot > daily SMA50 | +10 (else −10) |
| Hourly trend | spot > 1h SMA50 | +5 (else −5) |
| Hourly RSI14 | > 70 | −10 (overbought) |
| Hourly RSI14 | < 30 | +10 (oversold bounce) |
| Hourly MACD histogram | > 0 | +5 (else −5) |

**Regime gate (research-mandated, see RESEARCH.md §3):** gold holds
overbought in macro trends, so RSI counter-signals only score against the
regime — in a bullish daily regime (spot > daily SMA200) the RSI>70 penalty
scores 0; in a bearish regime the RSI<30 bonus scores 0.

**Event mask (RESEARCH.md §4):** if the current hour is within ±1 bar of a
scheduled 08:30 ET release (from `us_calendar_week` in latest.json) or a
14:00 ET FOMC decision, mark `event_window: true` in the log, halve
`tech_score`, and say so in the brief — those bars are news, not technicals.

### 3b. Best buy / best sell levels (from latest.json `levels`)
The collector clusters Fibonacci retracements (daily 90d + hourly 5d swings),
classic floor pivots, daily SMAs, Bollinger bands, and $50 round numbers into
confluence zones and pre-selects `best_buy_zone` (strongest support below
spot) and `best_sell_zone` (strongest resistance above spot). The brief MUST
present both with their confluence members spelled out (e.g. "buy zone
$3,982 = pivot S1 + fib 61.8% + round $4,000 sweep"), plus ATR(14) 1h as the
expected hourly range. If spot sits inside a zone, say so. These are
technical reference levels, not guaranteed fills.

### 4. Compute macro and news bias
- `macro_score` (cap ±30): DXY falling today +10 / rising −10; real 10Y yield
  (DFII10) down on the week +10 / up −10; dovish Fed signal +10 / hawkish −10.
- `news_score` (cap ±30): sum of headline tags (+5 bullish, −5 bearish),
  geopolitical escalation +10, de-escalation −10.

### 5. Apply learned weights and compose
- Read `gold-intel/learning-state.json` → weights per family.
- `composite = tech_score*w_tech + macro_score*w_macro + news_score*w_news`
- Bias: composite ≥ +20 bullish; ≤ −20 bearish; else neutral.
  Confidence: |composite| mapped low (<20) / medium (20–45) / high (>45).

### 6. Learning update (see LEARNING.md)
- Score the prediction made 1 run ago and 24 runs ago against realized price
  change from `data/history.jsonl`.
- Update per-family hit rates and weights in `learning-state.json`.

### 7. Write outputs
- `gold-intel/briefs/LATEST.md` — the hourly brief (template below).
- Append full entry to `gold-intel/signals-log.jsonl`.
- Commit both (`gold-scan: hourly brief <UTC hour>`), push with retry.
- Post the brief as the session reply.

## Brief template (LATEST.md and session reply)

```
# Gold Hourly Brief — <UTC timestamp>
Spot: $X,XXX.XX (±X.X% 24h)  |  Bias: BULLISH/BEARISH/NEUTRAL (confidence)
BEST BUY:  $X,XXX (confluence: <members>)   ← strongest support below spot
BEST SELL: $X,XXX (confluence: <members>)   ← strongest resistance above spot
Expected 1h range (ATR14): ±$X.X
Technicals: RSI14(1h) XX · vs SMA50/200 · MACD ± · event_window yes/no
Macro: DXY XXX.XX (±X%) · 10Y real X.XX% · next event: <event, time UTC>
News: <top 2-3 headlines with direction tags>
Learning: last call <right/wrong>, rolling hit rate XX% (n=XX), weights t/m/n
Risk note: leverage 20:1 → a 5% adverse move wipes 100% of margin.
```

## Rules

- Never fabricate a number: every price/indicator in the brief must come from
  latest.json or a WebSearch result from this run. If a value is unavailable,
  write "n/a".
- This produces market intelligence, NOT trade execution. No orders are placed.
- If two consecutive runs find stale data AND WebSearch fails, post a
  degraded-mode brief saying exactly what is missing.
