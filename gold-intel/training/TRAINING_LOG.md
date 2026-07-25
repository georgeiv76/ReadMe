# Training Log — Self-Learning Loop

Data: 12 months Dukascopy 1-min→hourly XAU/USD (8,880 bars; 2,877 dead
weekend/holiday bars dropped → 6,003 live hours; zero OHLC violations).
Train = first 75% (bull run → $5,562 blowoff → crash). Holdout = last 25%
(bear/chop ~$4,000), never used for tuning. Band ±0.15% frozen.

## Iterations

| # | Change (vs prev accepted) | Train | Holdout | Critic verdict |
|---|---|---|---|---|
| 0 | baseline (mom .2, pp .03, bias 1.0, tol .0015, stop 1.5, ttl 6) | MAE gap +.0069, dir 49.6, PF 1.118 +$662 | MAE gap +.0082, dir 49.6, PF 0.934 −$128 | — |
| 1 | mom −.1, bias .5, stop 2.0 (Improver: anti-persistence, regime shrinkage, wider stops) | gap +.0026, dir 50.9, PF 1.115 +$646 | gap +.0051, dir 49.0, PF 0.984 −$30 | ACCEPT (regularization generalized; demanded 1-param discipline) |
| 2a | ablation ×10 (train-only selection) | pred wants pp↓ mom↓; trade PF loves ttl 12 / tol .0025 | — | prescribed by Critic |
| 2b | pp .01, mom −.05, ttl 12, tol .0025 | **MAE beats naive** (−.0002), dir 52.1, PF 1.451 +$2,066 | pred: best ever (gap +.0015, band skill +0.28) · trade: **degraded** (PF 0.945 −$92) | **SPLIT: prediction ACCEPT, trading REVERT (overfitting confirmed)** |
| 3 | shrinkage-to-zero sweep (pp {.005,0}, mom {−.025,0}, pure naive+bias) | gaps → −.0005 (≈naive) | gap never < +.0007; dir ≤ 49.6 | **PLATEAU on linear features** (Critic's stopping criterion met) |

## Locked parameters (Critic-accepted)

momentum_k −0.05 · pivot_pull_k 0.01 · session_bias_scale 0.5 ·
cluster_tol_pct 0.0015 · stop_atr_mult 2.0 · ttl 6h · horizon 24h

## Honest state of skill vs the 90% target

| Metric | Holdout now | Naive | 90% reachable? |
|---|---|---|---|
| Direction accuracy (1h) | 49.6% | ~50% | **No** — no known system does 90%; realistic ceiling 55–65% |
| Band ±0.15% accuracy | 48.6% | 48.3% | Only by widening the band = metric gaming; blocked |
| Zone-trade win rate | 51.3% (n=115) | — | The promising axis; 57–62% on train |
| MAE skill vs naive | −0.0015pp | 0 | Crossed zero on train; not yet on holdout |

**Conclusion so far:** next-hour close prediction from price-only linear
features has no out-of-sample edge — the model correctly converged to
~naive. The economically real signal is in the confluence-levels trading
subsystem (profitable all 9 train months; roughly breakeven on the 3
bear/chop holdout months after honest reverts).

## Next program (Training Block 2 — scheduled)

1. K-fold walk-forward validation inside train (Critic's rule: a trading
   param earns a holdout look only after winning a majority of folds with
   ≥30 fills each).
2. New features the data already contains but the model ignores: hour-of-
   session volatility (ATR regime), day-of-week, distance-to-level as a
   trade filter, and (via the collector) DXY/real-yield daily context.
3. Target the metrics that can genuinely rise: zone win rate and profit
   factor on holdout; report direction/band honestly as-is.

## Data upgrade (user-provided, 25 Jul)

494,235 clean 15-min candles, Jun 2004 -> 30 Jan 2026 (125,206 hourly bars,
22 years, every regime). Zero parse rejects; tz-corrected UTC+2 -> UTC;
cross-validated vs Dukascopy overlap: MAE 0.069% over 2,489 bars.
Files: data/history_22y_hourly.json (training), data/xau_15m_2004_2026.csv.gz
(15m, for finer fill simulation later).

SPLIT for Block 2 (USER DIRECTIVE 25 Jul: train on the last 12 months only —
the current regime): dataset = history_12mo.json (Dukascopy, Jul 2025 - Jul
2026). K-fold walk-forward folds inside the first 75%; final holdout stays
the last 25% (Apr-Jul 2026), untouched by tuning. The 22-year corpus is
retained as archive/reference only — NOT used for training. The 15m file's
Jul 2025 - Jan 2026 portion may be used for finer fill simulation within the
12-month window (it cross-validated against Dukascopy at 0.069% MAE).

## Block 2 — Iteration 4 (regime filters) — ACCEPTED

Candidate: min_zone_strength=2, atr_regime_max_ratio=1.5 (entry gating for
high-vol chop). Majority-of-folds satisfied: PF up 3/3 (fold1 1.257->1.471,
fold2 1.556->1.964, fold3 0.959->0.979). Holdout: PF 0.984->0.997, PnL
-$30->-$5.46. Critic verified numbers directly from metrics files; accepted;
no overfitting (removed cohort was the predicted bad-geometry population).

**Critic's structural finding:** entry filters asymptote PF toward 1.0 from
below and cannot cross it — the surviving trade population in recent regimes
has ~zero raw edge. Breakthrough requires exit geometry, fill accuracy, or
regime-conditional direction.

## Next program (iteration 5, wake at 15:32 UTC continues here)

1. Re-test trade_horizon ON TOP of the iter-4 champion (single pre-stated
   hypothesis; the old horizon-36 ablation predates the champion).
2. 15-minute fill-simulation as a MEASUREMENT AUDIT (not tuning): re-baseline
   champion before/after under identical sim; fill-model error currently
   exceeds the measured edge.
3. Verify mechanics: why signal counts rose under stricter filters
   (fold3 326->362); confirm trailing-ATR mean excludes the current signal.
4. NO fitted dow_skip (data-mining); event-window masks only if mechanistic.
5. TERMINATION CRITERION (Critic): if exit-geometry + corrected fill sim
   cannot lift holdout PF above ~1.05 with positive PnL after realistic
   costs, declare the base signal edgeless in recent regimes and END the
   loop with a final report rather than asymptoting to breakeven.
