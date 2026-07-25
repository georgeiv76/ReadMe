# How Gold Traders Form a View — Research Synthesis

Compiled 25 July 2026 by three parallel research agents (macro/desk practice,
technical analysis, data sources). This is the knowledge base the hourly
orchestrator applies. Sources inline; full agent transcripts in session logs.

## 1. The five pillars of a professional gold view

1. **Real-yield / dollar valuation anchor — regime-aware.** Gold's classic
   inverse driver is the 10Y TIPS real yield (correlation ≈ −0.73 2003–2021;
   +100bp real ≈ −18% gold, per PIMCO/LBMA). **This broke in 2025**: gold
   rallied >60% against ~2% real yields because official-sector buying
   overwhelmed the model. Treat real yields as one regime-dependent factor,
   never a master valuation.
2. **Fed path pricing** — CME FedWatch probabilities from fed funds futures
   are the highest-frequency macro input; the *repricings* are the events.
3. **Positioning extremes as contrarian overlays** — CFTC COT managed-money
   net length (Fri 15:30 ET, data as of Tue) at 1y/3y percentile extremes;
   GLD tonnage daily deltas; WGC monthly ETF flows.
4. **Structural official-sector bid** — central banks bought 863t in 2025;
   PBoC on a 20-month buying streak through June 2026 (+14.93t in June,
   "buying the dip"). This is the slow-moving floor under corrections.
5. **Geopolitical event risk with two-phase logic** — gold spikes on war
   risk premium, then **sells off in liquidity crunches** (Feb–Mar 2026:
   Iran war spike to ~$5,390, then ~25% margin-call collapse to ~$4,000,
   then recovery). An escalation headline is not automatically "buy."

The surprise-vs-consensus delta moves price, not the level of any release.

## 2. Current regime snapshot (as of 25 July 2026 — refresh each run)

- Spot ~$4,045–4,066; 52-week range $3,268–$5,595; ATH $5,602 (29 Jan 2026).
- **Bearish-to-neutral daily regime**: price below the 200-day SMA (~$4,479);
  50/200 death cross confirmed on weekly-close basis June 2026.
- $4,000 is the psychological and technical battleground; $3,900–4,240 July range.
- Hawkish shock driver: Kevin Warsh confirmed Fed chair 13 May 2026 (his Jan 30
  nomination knocked gold −5% in hours); 10Y real yield 2.42%, DXY ~101.
- Next FOMC: **29 July 2026** (~63.5% hold priced). Jackson Hole: Aug 27–29.
- Bull side: Asian ETF inflows + PBoC dip-buying + Hormuz escalation risk.
  Bear side: hawkish Fed, 2.4% real yields, Western ETF outflows (June −$8.9bn).

## 3. Technical practice on XAU/USD (what the scoring encodes)

- **RSI(14)** standard on 1h/4h/daily. Gold holds overbought for long
  stretches in macro trends — **RSI>70 is NOT a short signal in an uptrend**
  (chronic loser per multiple practitioner sources); use 40–50 as the
  pullback-buy zone in uptrends. Divergence at S/R beats raw thresholds.
- **Moving averages**: daily 200-SMA is the regime filter (above = buy dips,
  below = defensive); 50/200 cross confirmed on weekly closes; intraday
  favors EMAs (9/21 momentum, 50 trend, 200 institutional reference).
- **Fibonacci**: swing-low→swing-high retracements; gold respects
  38.2/50/61.8%, with 61.8–78.6% the "golden zone" dip-buy in uptrends —
  always with confluence (round number, prior S/R, MA).
- **Pivots (classic floor)**: previous day H/L/C; daily P is the day's
  bull/bear line. **Round numbers**: $50/$100 increments are the anchors
  ($4,000 currently doing double duty); expect stop-run sweeps through them.
- **Bollinger (20,2)**: squeeze = breakout setup; band-walk = trend strength
  (do NOT fade); mean reversion to midline works best in Asia session.
- **Combining**: TradingView/Investing/Barchart all use equal-weight ±1
  voting mapped to five labels. Gold-specific fixes: gate oscillator votes by
  the daily 200-SMA regime and trend strength, and weight hierarchically
  (daily gates direction, 4h locates, 1h times) rather than flat-averaging.
- **Formula pitfalls**: RSI needs Wilder smoothing (alpha=1/14, not span
  EMA); Bollinger uses population std-dev; EMA is SMA-seeded. Our collector
  implements all three correctly.

## 4. The clock (all ET unless noted)

| Time | Event |
|---|---|
| ~03:00 | London open — OTC volume arrives, often sets the day's theme |
| 05:30 London 10:30 | AM LBMA fix |
| 08:00–12:00 | London/NY overlap — peak liquidity; ~70% of daily highs/lows form here |
| 08:30 | CPI / NFP / PCE / claims releases — 1–2% whipsaws; suppress technical signals in adjacent bars |
| 10:00 | ISM / JOLTS / UMich |
| 10:00 (15:00 London) | PM LBMA fix — institutional flow concentration, documented downward-drift anomaly |
| 13:30 | COMEX settlement |
| 14:00 (+14:30 presser) | FOMC decision days — the biggest scheduled vol window |
| Asia session | Thin, range-bound; mean reversion works; mark Asian range H/L as London's levels |

Weekly: Thu 08:30 claims · Fri 08:30 NFP (first Friday) · Fri 15:30 COT ·
~7th PBoC reserves · mid-month CPI · month-end PCE · monthly WGC ETF flows ·
quarterly WGC Gold Demand Trends.

## 5. Data source inventory (verified July 2026; smoke-test on deploy)

| Need | Primary | Fallback | Notes |
|---|---|---|---|
| Spot XAU/USD | `api.gold-api.com/price/XAU` (JSON, keyless, no limits) | Swissquote `forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD` | Cross-check both |
| Hourly OHLC | Yahoo v8 `query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X?interval=1h` | `GC=F`; `query2` mirror; stooq CSV (daily quota!) | Only free hourly history; browser UA required |
| DXY | Yahoo `DX-Y.NYB` | stooq `dx.f` | |
| Yields | FRED `fredgraph.csv?id=DGS10` / `DFII10` (keyless) | — | Daily data; fetch once/day, "." = holiday |
| Calendar | ForexFactory `nfs.faireconomy.media/ff_calendar_thisweek.json` | BLS/Fed schedule pages | **2 downloads per 5 min limit — cache daily** |
| News | ForexLive RSS, MarketWatch DJ feeds, Kitco category feeds, FXStreet RSS, Google News RSS query | — | Reuters public RSS is dead; Investing.com is Cloudflare-blocked |
| Fed | `federalreserve.gov/feeds/press_monetary.xml`, `speeches.xml` | FOMC calendar page (scrape monthly) | Plain-GET friendly |
| COT gold | Socrata `publicreporting.cftc.gov/resource/6dca-aqww.json?commodity_name=GOLD` | `cftc.gov/dea/newcot/deafut.txt` | Weekly Fri 15:30 ET |
| GLD tonnage | `spdrgoldshares.com/assets/dynamic/GLD/GLD_US_archive_EN.csv` | — | Preamble rows before header; possible bot challenge |

In the orchestrator sandbox all of these are gateway-blocked; the GitHub
Actions runner fetches them. Qualitative news comes to the orchestrator via
WebSearch.

## 6. Design consequences applied to this system

1. Regime gate: daily price-vs-200SMA flips how oscillator signals score
   (encoded in PLAYBOOK.md §3).
2. Event mask: technical signals in bars adjacent to 08:30/14:00 ET releases
   are flagged, not trusted.
3. Two-phase geopolitics: escalation headlines score bullish only absent
   liquidity-crunch symptoms (equities crashing + gold falling together).
4. Positioning extremes (COT percentiles, ETF flow streaks) act as
   contrarian dampeners on the news/macro score, not primary signals.
5. Levels engine (Fib + pivots + MAs + rounds + Bollinger) produces
   confluence-ranked buy/sell zones each hour; ATR(14) sizes expected range.
