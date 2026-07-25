# Gold Intelligence System — Architecture

An hourly, multi-agent pipeline that replicates how a professional gold desk
gathers information and forms a directional view on XAU/USD, with a scored
prediction journal and a bounded auto-learning loop.

```
                    ┌─────────────────────────────────────────────┐
                    │  GitHub Actions (hourly cron, open internet)│
                    │  .github/workflows/gold-data.yml            │
                    │  scripts/collect_gold_data.py               │
                    │  → Yahoo Finance (XAU/USD 1h+1d candles,    │
                    │    DXY), FRED (10Y nominal + TIPS real)     │
                    │  → computes RSI14, SMA20/50/200, EMA, MACD  │
                    │  → commits gold-intel/data/latest.json      │
                    └─────────────────┬───────────────────────────┘
                                      │ git (the only reliable data
                                      │ channel into the sandbox)
                    ┌─────────────────▼───────────────────────────┐
   hourly Routine → │  ORCHESTRATOR (this Claude session)         │
   (Claude Code     │  runs gold-intel/PLAYBOOK.md                │
    Remote trigger) │                                             │
                    │  ├── News collector agent (WebSearch)       │
                    │  ├── Macro/Fed collector agent (WebSearch)  │
                    │  ├── Deterministic technical scoring        │
                    │  ├── Learning update (LEARNING.md)          │
                    │  └── Brief writer                           │
                    └─────────────────┬───────────────────────────┘
                                      │
                    ┌─────────────────▼───────────────────────────┐
                    │  OUTPUTS (committed to the branch)          │
                    │  briefs/LATEST.md      hourly brief         │
                    │  signals-log.jsonl     prediction journal   │
                    │  learning-state.json   adaptive weights     │
                    │  briefs/WEEKLY_REVIEW.md  Monday self-audit │
                    └─────────────────────────────────────────────┘
```

## Why two layers

The orchestrator session runs in a sandbox whose network policy blocks
financial data domains (verified 2026-07-25: direct fetches and WebFetch to
Yahoo, stooq, FRED, Kitco, capital.com all denied; only WebSearch and GitHub
egress work). GitHub Actions runners have unrestricted internet, so numeric
collection lives there and the repo itself is the data bus. The orchestrator
contributes what Actions cannot: reading news, judging Fed language, weighing
conflicting signals, and writing the brief.

## The three signal families

Mirrors a professional desk's routine (full sourcing in RESEARCH.md):

1. **Technical** — RSI(14), SMA 20/50/200, MACD(12,26,9) on 1h and daily
   candles; the daily 200-SMA acts as regime filter.
2. **Macro** — DXY direction, 10Y real yield (TIPS) trend, Fed policy
   expectations, upcoming releases (CPI, NFP, PCE, FOMC).
3. **News/Events** — geopolitics, central-bank gold buying, ETF flows,
   Fed speeches, bank forecasts.

Each family produces a bounded score; learned weights (LEARNING.md) combine
them into one bias: bullish / bearish / neutral with confidence.

## Operating cadence

- **:07 UTC every hour** — Actions collects data (offset from :00 to dodge
  scheduler congestion; scheduled workflows only run once this file is on the
  default branch).
- **:00 UTC every hour** — Routine fires the orchestrator; it uses the most
  recent snapshot (≤1h old once Actions is active on main).
- **Monday 06:00 UTC** — weekly self-review appended to the run.

## Failure modes and honesty

- Stale data (>2h) → degraded mode, spot price via WebSearch, flagged in log.
- Every number in a brief traces to latest.json or a same-run WebSearch; no
  value is ever invented. Missing → "n/a".
- The journal is append-only; hit rates are computed, never asserted.

## Explicit non-goals

- **No trade execution.** This system informs; it never places orders. The
  execution path (Capital.com REST API, 20:1 gold leverage) was researched
  separately and would be a deliberate, user-approved addition.
- No intraday "guaranteed" signals — at 20:1 leverage a 5% adverse move is a
  100% margin loss; the brief carries this reminder every hour.
