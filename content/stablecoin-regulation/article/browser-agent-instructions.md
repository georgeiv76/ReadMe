# Browser-Agent Instructions — Sync LinkedIn Draft with Verified Article

> Paste everything below the line into a browser-capable agent (Claude in Chrome)
> while the LinkedIn editor tab is open. Follows content/CONTENT-ROUTINE.md rules:
> pre-verified edits only, no improvisation, preserve author content, report back.
> Canonical source: content/stablecoin-regulation/article/linkedin-article.md.

---

**ROLE:** You are an editing agent with browser-control tools. Your single job is to apply pre-approved, fact-checked corrections to a LinkedIn article draft, without altering anything else. All verification is done. You only execute edits precisely.

**TARGET:** https://www.linkedin.com/article/edit/7480215518671650817/ — article "The Underlying Currency Dominance War in Stablecoin Regulation: MiCA and the GENIUS Act". It has section headings, an italic one-line summary under each heading (added by the author), numbered markers like [4] in the body, and a FOOTNOTES list at the end.

**HARD RULES:**
- Preserve the author's italic summary lines under every headline. Never delete, reword, or move them.
- Preserve the cover image, title, subtitle, hashtags, and any wording not explicitly targeted below.
- Make ONLY the edits listed. If a FIND string isn't found verbatim, look for a close variant (minor punctuation/spacing only); if still not found, SKIP and report — do not improvise.
- Work top to bottom. Confirm "Draft - saved" after each change. Do NOT publish.

**EDITS:**

EDIT 1 — Section about a euro stablecoin under the GENIUS Act ("the trap built into reserve rules"):
FIND: "because that list is exhaustive, and every item on it is American: US coins and currency, deposits at insured US banks, US Treasuries with maturities of 93 days or less, repos backed by those same Treasuries, government money market funds holding the same, and central bank reserve deposits [4]. The only interest-bearing assets a GENIUS issuer may hold are US government debt. No German Bubills, no French BTFs, no euro sovereign paper of any kind."
REPLACE WITH: "because that list is exhaustive, and all but one item on it is dollar-locked: US coins and currency, US Treasuries with maturities of 93 days or less, repos backed by those same Treasuries, government money market funds holding the same, and central bank reserve deposits [4]. The single currency-flexible bucket is bank deposits — the deposit clause names no currency, so euro deposits at an insured US bank (including its foreign branches) are technically permitted [31]. But that is the entire euro menu. The only interest-bearing securities a GENIUS issuer may hold are US government debt. No German Bubills, no French BTFs, no euro sovereign paper of any kind."

EDIT 2 — Next paragraph, same section:
FIND: "an impossible choice: hold dollar T-bills against a euro peg (a currency mismatch that breaks the coin), or hold non-earning euro cash (a business with no revenue). The dollar coin gets a yield engine by statute; the euro coin gets a cost center."
REPLACE WITH: "an impossible menu: hold dollar T-bills against a euro peg (a currency mismatch that breaks the coin), or cram the entire reserve into euro bank deposits — largely uninsured (FDIC coverage stops at foreign branches), capped under proposed rules at 40% per bank, and, per the FDIC's own database, with only five of Europe's thirty largest banks even owning an eligible US insured bank [31]. De jure permitted; de facto impossible at scale. The dollar coin gets a yield engine by statute; the euro coin gets a compliance labyrinth with no revenue."

EDIT 3 — "MiCA: Defense" section, after the digital-euro sentence ending "adopting the regulation in 2026 [16].":
INSERT: " And note the perfect inversion across the Atlantic: the House-passed CLARITY Act carries a title literally named the "Anti-CBDC Surveillance State Act," banning the Federal Reserve from offering a retail digital dollar [32]. Europe is building a public digital currency to defend against private dollar coins; America is banning its public option to clear the field for them."

EDIT 4 — Replace footnote [4] entirely with:
[4] GENIUS Act, Pub. L. 119-27, Sec. 4(a)(1)(A) (codified at 12 U.S.C. 5903): permitted reserves limited to US coins and currency; demand deposits at insured depository institutions; US Treasury bills/notes/bonds with remaining maturity ≤93 days; Treasury-backed repurchase/reverse-repurchase agreements; government money market funds invested in the foregoing; central bank reserve deposits; regulator-approved "similarly liquid Federal Government-issued" assets; and tokenized equivalents. Note: only the deposit clause (ii) states no currency — see [31]. See also Gibson Dunn, "The GENIUS Act: A New Era of Stablecoin Regulation" (July 2025).

EDIT 5 — Replace footnote [27] entirely with:
[27] GENIUS Act Sec. 2 definitions: "payment stablecoin" is defined by redemption for a fixed amount of "monetary value" (Sec. 2(17)), and "national currency" expressly includes "money issued by a foreign central bank" (Sec. 2(19)(C)) — so a euro (ECB) peg fits the definition; the exclusion list (national currencies, deposits, securities) does not bar foreign pegs.

EDIT 6 — Append two new footnotes at the end of the list (after [30], before any closing note):
[31] GENIUS Act Sec. 4(a)(1)(A)(ii) (12 U.S.C. 5903): the bank-deposit clause specifies no currency — the reserve list's only non-USD bucket. Practical constraints: obligations payable solely at foreign branches are generally not insured deposits (FDI Act); the FDIC's proposed rule caps any single institution at 40% of reserves (§350.4(f)) and the OCC proposal adds an insured-deposit floor and a USD operational backstop (§§15.11(d), 15.41(b)(2)). FDIC BankFind check (July 2026): only 5 of Europe's 30 largest banking groups — HSBC, Santander, Barclays, UBS, Deutsche Bank — have an active FDIC-insured US depository institution.
[32] CLARITY Act, H.R. 3633 (119th Cong.), Title VI, "Anti-CBDC Surveillance State Act" — engrossed House text, passed July 17, 2025, pending in the Senate as of mid-2026: prohibits Federal Reserve banks from offering certain products or services directly to individuals and bars use of a central bank digital currency for monetary policy.

EDIT 7 — Rendering check, "Same tools, opposite doctrines": if the comparison table shows raw pipe characters (|), replace with bullets; if it renders fine, leave it:
• 1:1 reserves — GENIUS (US): channel global demand into T-bills / MiCA (EU): keep money and risk inside EU banks
• Interest ban — GENIUS (US): protect US bank deposits at home / MiCA (EU): protect EU bank deposits at home
• Foreign-issuer rules — GENIUS (US): reciprocity to export the dollar rail / MiCA (EU): caps and localization to block the dollar rail
• End goal — GENIUS (US): dollar everywhere / MiCA (EU): euro survives at home

EDIT 8 — In the USDT section ("The war's clearest evidence"), immediately after the sentence ending "delisted across Coinbase, Kraken, Crypto.com and Binance for EU users by March 2025 [12].":
INSERT: " And the wall is still closing: with MiCA's final transition window shut on July 1, 2026, the fintech Revolut is now removing USDT for its European users in stages — purchases blocked July 6, deposits off July 30, full delisting August 31, 2026, with any leftover balances auto-converted to fiat [33]."
Then append footnote [33] after [32]:
[33] Revolut staged USDT delisting for EU users: purchases blocked July 6, 2026; deposits disabled July 30, 2026; full delisting August 31, 2026, with residual balances auto-converted to the user's base currency at market rate — Yahoo Finance, BeInCrypto, The Paypers (July 4-5, 2026). Timing follows the expiry of MiCA's Art. 143(3) CASP grandfathering window (July 1, 2026). August 31 is Revolut's own schedule, not an EU-wide statutory date.

**FINAL VERIFICATION (all four):**
1. Body markers [31], [32] and [33] each have a matching footnote; the list runs [1]-[33], no duplicates.
2. Every headline still has its italic summary beneath it.
3. "every item on it is American" and "non-earning euro cash" appear NOWHERE in the draft.
4. Editor shows "Draft - saved". Never click Publish or Next.

**REPORT FORMAT:** for each EDIT 1-7: APPLIED / SKIPPED (reason + nearest text found); then the four verification results; then any anomalies (broken formatting, duplicated paragraphs, missing sections).
