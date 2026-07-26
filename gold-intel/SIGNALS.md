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
