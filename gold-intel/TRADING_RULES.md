# Trading Rules (user-defined, locked 25 Jul 2026)

1. BUY only when StochRSI <= 20 (oversold extreme). SELL only when
   StochRSI >= 80 (overbought extreme). Between 20 and 80: HOLD — no
   buy, no sell, no predictions.
2. NEVER sell at a loss: an overbought signal below the entry price is
   noise to hold through. Sell at the FIRST overbought event whose price
   exceeds entry (net of costs). The margin buffer exists to absorb the
   wait. (Exit refinement noted: on reaching 100, wait one candle — sell
   on the first falling candle.)
3. Margin discipline: use a fraction of equity as margin so drawdowns
   never push margin level below 80% (broker close-out 50% must never be
   approached). Known limit (20-year evidence): rule 2 without a regime
   filter dies in multi-year bears — the full system pairs these rules
   with the tide gate (long only above the 1000h average).
4. Position sizes: 0.1 or 0.5 oz CFD, 20:1 leverage, costs charged:
   ~$0.50/oz spread round trip + overnight funding on notional.
