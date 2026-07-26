# Learned Signal Table — what moves gold (round 1, 25 Jul 2026)

52 measured events (Aug 2025 - Jul 2026), hourly reactions, z-scored vs
rolling volatility. Verdicts by the adversarial Empiricist; full per-event
data in training/event_study_r1.json.

| Signal | Moves gold? | Direction predictable? | Verdict |
|---|---|---|---|
| FOMC decisions | STRONG (|z| 1.8 at 1h) | No — coin flip | Trade the volatility, never the headline direction |
| Fed personnel surprises | VIOLENT once | First announcement only | Warsh nomination -8.2%/24h; confirmation/swearing-in = zero. Credibility prices exactly once |
| CPI releases | weak | YES — 80% (8/10) | Best directional signal; hot prints -> gold down 4/4; small magnitudes |
| Jobs (NFP) | moderate at +1h | needs surprise-conditioning | Signal lives in the first hour (7/10, |z| 1.5), gone by 6h |
| WAR headlines | STRONG (biggest 1h moves) | INVERSE tendency | Escalation -> gold DOWN 3/5; de-escalation -> UP 2/2. Never buy the war headline |
| Equity crashes | moderate | 4/4 conditional — promising, n tiny | Safe-haven bid first 6h, liquidation risk by 24h (phase split) |
| Tariffs | STRONG (|z| 1.8) | No — both directions rallied gold | Uncertainty channel, not inflation channel; n=3 |
| Central-bank gold news | NONE (|z| 0.35) | dead at event horizon | Fully pre-priced; slow regime factor, not an event trade |

## Actionable now (Empiricist-approved)
1. EVENT-VOLATILITY POSTURE: around FOMC/tariff/war headlines expect
   abnormal movement with unreliable direction — reduce directional
   leverage; never naive-directional on the headline sign.
2. HOT-CPI FADE (small size): hot prints preceded 6h gold weakness 4/4.
3. NEGATIVE KNOWLEDGE: ignore CB-gold headlines and procedural Fed
   personnel steps as triggers — dead signals that cost money to trade.

## Round-2 program (armed): minute-accurate timestamp audit (all WAR events
were round-hour stamped — the inversion could be an artifact), WAR split
escalation/de-escalation with 0-1h/1-6h/6-24h phases, CPI by signed
surprise, NFP/FOMC at 1h with quantified surprise, equity shocks to n=15+
via mechanical -1.5% trigger, DXY/real-yield controls on every event.

## GCI 2.0 (25 Jul, evening) — the fused index

Components (weights earned by measurement, not belief): long tide SMA1000h
(+/-25) · medium tide SMA200h — the April recovery detector (+/-15) ·
USER 3-CANDLE RULE, empirically confirmed 55.6%/49.9% next-day (+/-10) ·
StochRSI extremes only (+/-15) · Fib confluence (+/-10) · CPI/equity/
personnel event terms · FOMC/war/tariff +/-6h confidence halving ·
BAD-NEWS ASYMMETRY (user rule): any hostile event within 24h caps the
index at +25 — bad news means smaller bets, never bigger.

Calibration (fwd 24h, 12 months): >=+40 bucket +0.293%/day, 62.0% positive
— MONOTONIC top (v1 anomaly fixed). April now opens correctly (17
favorable hours, +0.999% mean — the missed +$19 becomes reachable).
REMAINING WEAKNESS, stated plainly: war-whipsaw months still generate
false favorable hours (Mar: 109 hrs at -1.2% mean; May: 36 at -1.0%) —
the index alone is not sufficient in violent months; the world-aware
trader agent remains the final gate (its March run: 0 takes, correct).
In-sample calibration; live journal provides the honest test.

## ROUND 2 — FINAL (study CONVERGED, loop closed 26 Jul)

Timestamp audit done (Epic Fury 13:00->03:30 UTC; wire times on war events;
equity shocks mechanical n=11; CPI/NFP split by signed surprise).

DEAD (stable negative knowledge):
- CPI direction "80%" — was selection bias; signed-surprise split = coin
  flip at the smallest z of any class. CPI = volatility flag only.
- Equity-shock safe-haven bid — REVERSED: gold FELL after 7/11 shocks
  (mean -0.55%/6h; liquidation selling concentrated in hours 1-6). Never
  buy gold into an equity crash intraday.
- CB_GOLD headlines — strongest null in the dataset (n=14). Fully priced.
- TARIFF direction — vol without sign (SCOTUS repeal rallied gold +1.27%
  against hypothesis).

SURVIVED (with honest caveats):
- WAR_ESC inversion — held under verified timestamps: 4/5 down at 6h, and
  5/5 negative in the 1-6h phase after the initial spike (Epic Fury: +2.1%
  knee-jerk then fade). PROVISIONAL RULE: "fade the escalation spike 1h->6h,
  stop above the 1h high, reduced size" — n=5, needs 3-4 out-of-sample
  escalations to promote or kill.
- NFP asymmetry (new) — misses lifted gold 4/4 at 1h AND 6h (p=0.0625);
  beats only weakly depress (4/6). Tentative.
- Warsh nomination -3.7%/6h z=3.6: largest shock measured; n=1 anecdote.

VERDICT: every remaining question is sample-size-bound — no re-analysis can
move these p-values, only future events. Loop CLOSED; WAR_ESC and NFP_MISS
enter passive out-of-sample tracking in the live hourly briefs. GCI event
weights updated implication: CPI terms downgraded to vol-flag; equity-shock
term flips from +10 bid to caution.
