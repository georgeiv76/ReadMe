# Auto-Learning Loop

The system learns by treating every hourly bias call as a testable prediction
and scoring it against what gold actually did afterwards.

## What gets predicted

Each run appends to `signals-log.jsonl`:

```json
{
  "t": "2026-07-25T12:00:00Z",
  "spot": 3345.10,
  "tech_score": 25, "macro_score": 10, "news_score": -5,
  "weights": {"tech": 1.0, "macro": 1.0, "news": 1.0},
  "composite": 30, "bias": "bullish", "confidence": "medium",
  "evidence": {"rsi14_1h": 58.2, "dxy": 104.1, "headlines": ["..."]},
  "scored": false
}
```

## How predictions are scored

On each run, for every earlier unscored entry at least 1h old:
- Realized move = (current spot − entry spot) / entry spot.
- A **bullish** call is a hit if the move over the following hour ≥ +0.05%;
  a **bearish** call is a hit if ≤ −0.05%; **neutral** is a hit if the move
  stayed within ±0.15%. Otherwise a miss. (Thresholds sized to typical XAU/USD
  hourly volatility; revisit monthly.)
- Each signal family is also scored alone: would tech_score's sign alone have
  been right? macro's? news's? This attributes hits/misses per family.
- Mark the entry `"scored": true` with the outcome.

## How the system adapts (bounded, transparent)

`learning-state.json` keeps per-family exponentially weighted hit rates
(alpha = 0.1, so roughly the last 30 predictions dominate):

```
hit_rate_new = 0.9 * hit_rate_old + 0.1 * (1 if hit else 0)
weight_family = clamp(0.5 + hit_rate_family, 0.5, 1.5)
```

- A family that keeps being right approaches weight 1.5; one that keeps being
  wrong decays toward 0.5. No family is ever silenced (floor 0.5) — regime
  changes can revive it.
- Weights update only from scored predictions, never from opinion.

## Weekly self-review (every Monday 06:00 UTC run)

The orchestrator additionally writes `gold-intel/briefs/WEEKLY_REVIEW.md`:
overall hit rate, best/worst family, biggest miss with a one-paragraph
post-mortem, and one concrete rule adjustment proposal (which the user can
approve; rules in PLAYBOOK.md only change with explicit user approval).

## Codified lessons (from graded exams)

- **2026-07-25, two-source rule:** a price anchor may be labeled "verified"
  only when two independent sources agree. A stale single-source snapshot
  (Investing.com, $4,065.92) was wrongly treated as Friday's close; the real
  Kitco-reported close was $4,051.51, and the bad anchor propagated into the
  estimated pivot and close prediction. Prefer Kitco AM/PM session reports
  as the authoritative daily reference in degraded mode.

## Honesty rules

- Hit rates below ~55% mean the system has no edge yet — the brief must say so
  plainly rather than imply skill.
- Directional hit rate on hourly horizons is noisy; the log needs ≥100 scored
  predictions before hit-rate claims are statistically meaningful, and the
  brief shows `n=` for exactly this reason.
