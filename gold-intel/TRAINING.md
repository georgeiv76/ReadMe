# Self-Learning Loop — Two Agents, Real Data, No Self-Deception

The improvement loop the user commissioned: estimate hourly gold prices over
12 months of real candles, measure errors, learn, retry — autonomously.

## Architecture

```
history_12mo.json (real candles, fetched by Actions)
        │
        ▼
backtest_walkforward.py  ← deterministic scorer, zero lookahead
  train = first 75% of hours (calibration allowed)
  holdout = last 25%       (NEVER used for tuning; overfitting alarm)
        │ metrics JSON
        ▼
┌─────────────────────────────────────────────────┐
│ AGENT 1 — IMPROVER                              │
│ Sees: params, train+holdout metrics, iteration  │
│ history. Proposes ONE parameter-set change with │
│ a stated hypothesis. Returns JSON only.         │
└──────────────────┬──────────────────────────────┘
                   ▼  backtest runs the proposal
┌─────────────────────────────────────────────────┐
│ AGENT 2 — ADVERSARIAL CRITIC                    │
│ Sees: full iteration history incl. new result.  │
│ Duties: reject overfitting (train↑ holdout↓),   │
│ reject metric gaming, compare vs naive baseline,│
│ decide ACCEPT / REVERT / STOP-PLATEAU.          │
└──────────────────┬──────────────────────────────┘
                   ▼
        accepted params → gold-intel/model-params.json
        every iteration → gold-intel/training/TRAINING_LOG.md
```

## Fixed rules (agents cannot change these)

1. **The holdout is sacred.** Only train metrics may guide tuning; holdout
   is the verdict. A change that improves train but degrades holdout is
   overfitting and gets REVERTED.
2. **The band is pre-registered**: "within-band accuracy" = predicted
   next-hour close within ±0.15% of the real close. Widening the band to
   inflate accuracy is metric gaming; the Critic must block it.
3. **Naive baseline always shown.** Persistence (predict no change) scores
   surprisingly well on within-band metrics because hourly gold moves are
   small. Skill = model − naive. A model that doesn't beat naive has no
   skill regardless of its absolute score.
4. **Trading metrics count.** Direction/band accuracy is not the goal by
   itself; the zone win rate and profit factor on holdout are the
   economically meaningful scores.
5. Every iteration is logged with its hypothesis, params diff, and both
   metric sets — including failures. Failed hypotheses are knowledge.

## On the 90% target

90% is achievable or impossible depending on the metric, and the log states
which is which:
- Within ±0.15% band: possibly reachable — but only skill above the naive
  baseline counts (naive itself may score high — see rule 3).
- Direction accuracy on hourly bars: 90% is NOT achievable by any known
  system (top practitioners sit near 55–65%); the loop optimizes it but the
  target for this metric is "meaningfully above 55% on holdout."
- The loop runs until targets are met on holdout with genuine skill, or the
  Critic declares a plateau (3 consecutive rejected/flat iterations); then
  it reports the honest frontier reached.

## Continuation

The loop state lives in the repo (params + log), so any future session,
Routine firing, or explicit "continue training" instruction resumes from the
last accepted iteration.
