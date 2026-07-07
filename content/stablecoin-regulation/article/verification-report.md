# Verification Report — "The Underlying Currency Dominance War" article

Run: 2026-07-07 · Method: 3 adversarial fact-check agents (WebSearch-level verification;
page fetches unavailable in this environment), 26 claims, per rule V1-V5 of
`content/CONTENT-ROUTINE.md`. Trigger: reader-caught misattribution of a Cipollone
quote (fixed in commit f493192, logged in the routine change-log).

## Verdict summary

| Verdict | Count | Items |
|---|---|---|
| CONFIRMED | 19 | Q1, Q2, Q3, Q5(a-e), Q6, E1-E7, E9(existence), M1, M4, M5, M7, M9, M10 |
| WRONG → fixed | 3 | Q4 (Citi title), M2 (Circle figure), M6 (BIS year/triad) |
| PLAUSIBLE → hedged/caveated | 4 | Q7 (Tether quarters), E8 (euro-segment size), E9 (characterization), M3/M8 (survey & profit nuances) |

## Corrections applied (this run)

1. **Citi source title (fn [8])** — the April 2025 figures ($1.6T/$3.7T, ~$1.2T UST
   holdings) are from Citi GPS **"Digital Dollars"**, not "Stablecoins 2030" (that's
   the Sept 2025 follow-up with $1.9T/$4.0T). Footnote corrected to cite both.
2. **Circle Treasury holdings (body + fn [3])** — "$48B" was an early-2025 snapshot.
   Mid-2026: Circle Reserve Fund ~$68B; ~80% of USDC's ~$78B reserves in Treasury
   instruments. Body now says "~$65 billion."
3. **BIS attribution (body + fn [20])** — the singleness/elasticity/integrity triad
   + ETF comparison is from BIS AER **2025**; AER 2026 renewed it with a fourth test
   (interoperability). Body and footnote now say so.
4. **Tether ranking (body + fn [2])** — old sentence welded three quarters (Q4 $122B
   direct; Q3's "17th-largest" at $135B vs South Korea; Q1's Germany comparison).
   Body now: "~$141B exposure ($122B direct), more than Germany's entire holdings,
   top-twenty holder worldwide" — true across all attestations; footnote explains
   the quarter mix.
5. **Bessent $3.7T framing (body + fn [6])** — his X post said "Recent reporting
   projects…"; he amplified projections rather than making his own forecast. Body:
   "He has amplified projections of…"
6. **Castle Island 47% (body + fn [9])** — 47% was "a reason for using" (multi-select,
   second behind trading at 50%), not "the primary reason for holding." Body reworded.
7. **Standard Chartered staleness (fn [7])** — Feb 2026 revision trimmed the T-bill
   demand estimate to ~$0.8-1.0T (market target unchanged at $2T). Footnote notes it.
8. **Euro-segment size (body + fn [1])** — €450M was a late-2025 snapshot; mid-2026
   likely €700-900M. Body now "well under €1 billion, less than 0.2%."
9. **Coinbase sequencing (fn [12])** — Coinbase delisted in Dec 2024, *before* the
   Jan 17, 2025 ESMA statement. Footnote now says "moved first, ahead of the statement."
10. **Tether profit composition (body + fn [29])** — 2025 profit driven mainly by
    reserve yields but includes gold/bitcoin gains; body hedged with "largely,"
    footnote adds the caveat and Circle's 99%-reserve-income S-1 figure.

## Confirmed verbatim quotes (safe to publish as quoted)

- Bessent, Treasury press release sb0197 (Jul 18, 2025): "…will buttress the dollar's
  status as the global reserve currency, expand access to the dollar economy for
  billions across the globe, and lead to a surge in demand for US Treasuries, which
  back stablecoins." — CONFIRMED, correct document.
- Lagarde: "privatization of money" / "I regard money as a public good" (Sintra
  remarks via Fortune, Jul 2, 2025) — CONFIRMED.
- Lagarde: "digital dollarisation" (CoinDesk + ECB speech "Stablecoins and the
  future of money," May 8, 2026) — CONFIRMED.
- Cipollone: "…excessively undermines resilience and compromises monetary
  sovereignty" (ECON statement, Apr 8, 2025) — CONFIRMED after correction f493192.
- Euronews headline "…to reduce US dominance in payments" (Jun 23, 2026) — verbatim
  CONFIRMED; ECON vote 43-14 (with 1 abstention) CONFIRMED.
- Forbes titles ("Tether's USAT Exists So USDT Never Has To Comply," May 27, 2026;
  "Euro Stablecoins Are Scaling While The Digital Euro Waits On Brussels," Jun 4,
  2026) — CONFIRMED.

## Statutory claims — all confirmed

GENIUS: reserve list closed/US-only (+ regulator power to add "similarly liquid
Federal Government-issued assets" — still US-only); Sec. 4(a)(11) yield ban (covers
issuers incl. foreign; OCC NPRM would extend to affiliates); effective date
mechanics; July 18, 2028 DASP cutoff; Sec. 18 / 12 U.S.C. 5916.
MiCA: Art. 23 thresholds (1M tx + €200M/day, quarterly-averaged, 40-working-day
plan); Art. 58(3) extension to non-EU-currency EMTs; 30%/60% deposit floors;
Arts. 40/50 interest ban.

## Remaining human click-test shortlist (rule V5)

1. Kaiko-origin "70% EU volume collapse" (fn [22]) — exchange-data estimate relayed
   via ForkLog; the only load-bearing statistic not traceable to a primary publisher.
2. Oxford Business Law Blog characterization (fn [23]) — piece and date confirmed;
   read the post to confirm the "handicapping" framing before publishing.
3. ECB WP 3199 deposit-substitution finding (interpretations brief only, not in the
   article body).

Everything else in the article traces to a confirmed source as of this run.


## Addendum — reconciliation against primary texts (2026-07-07, second pass)

Author-supplied source pack: enrolled GENIUS text (PL 119-27 rendering), CLARITY
H.R. 3633 engrossed text, Treasury ANPRM / White House / Covington / Mayer Brown /
Paul Hastings summaries, clause-by-clause euro-reserve analysis, FDIC BankFind check.

Corrections applied to the article in this pass:
1. **Reserve-list precision** — Sec. 4(a)(1)(A) clause (ii) (bank deposits) states
   no currency: euro deposits are the list's single lawful non-USD bucket. Article
   text changed from "every item on it is American" to "all but one item is
   dollar-locked," with the de jure/de facto distinction spelled out (fn [31]).
2. **The euro coin's real constraint set** — replaced "non-earning euro cash" with
   the documented chain: uninsured foreign-branch deposits (FDI Act), 40%
   single-bank concentration cap (proposed FDIC §350.4(f)), USD insured-deposit
   floor + USD backstop (proposed OCC §§15.11(d)/15.41(b)(2)), and the FDIC
   BankFind finding that only 5 of Europe's top-30 banks own an active FDIC-insured
   US institution (fn [31]).
3. **Anti-CBDC inversion added** — CLARITY H.R. 3633 Title VI ("Anti-CBDC
   Surveillance State Act"), House-passed Jul 17, 2025, Senate-pending: US bans its
   public digital option while the EU builds one (fn [32]).
4. **Footnotes [4] and [27]** upgraded to statutory citations (12 U.S.C. 5903;
   Sec. 2(17)/(19)(C) verbatim basis for the currency-neutral peg).

Claims re-checked against the enrolled text and left standing: the 93-day Treasury
maturity; the closed nature of the reserve list; the yield ban Sec. 4(a)(11)
(Hagerty Amendment); Jan 18, 2027 effective date; Jul 18, 2028 DASP cutoff; the
Sec. 18 comparability/OCC-registration/US-reserves gating for foreign issuers
(SCRC approval required); no usage caps anywhere in GENIUS.

Note for future runs: the Treasury ANPRM summary attributes the foreign-issuer
lawful-order/noncompliance-designation mechanism to Section 8 of the Act; our
digest maps Section 8 to state-issuer supervision. Resolve against the enrolled
text before citing either section number for that mechanism.
