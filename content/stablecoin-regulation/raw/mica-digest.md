# MiCA — Regulation (EU) 2023/1114 — Structural Digest (Stablecoin Focus)

> Reconstructed digest of the Markets in Crypto-Assets Regulation. Not a substitute
> for the official text (see `SOURCES.md` for canonical links). Article numbers refer
> to the OJ L 150, 9.6.2023 version.

## Overall architecture

| Title | Subject | Key articles |
|---|---|---|
| I | Subject matter, scope, definitions | Art. 1–3 |
| II | Crypto-assets other than ARTs/EMTs (utility tokens etc.) | Art. 4–15 |
| **III** | **Asset-referenced tokens (ARTs)** | Art. 16–47 |
| **IV** | **E-money tokens (EMTs)** | Art. 48–58 |
| V | Crypto-asset service providers (CASPs) | Art. 59–85 |
| VI | Market abuse | Art. 86–92 |
| VII | Competent authorities, EBA and ESMA powers | Art. 93–138 |
| VIII | Delegated acts | Art. 139 |
| IX | Transitional and final provisions | Art. 140–149 |

**Application dates (Art. 149):** entry into force 29 June 2023; Titles III & IV
(stablecoins) apply from **30 June 2024**; the remainder (CASP licensing etc.) from
**30 December 2024**. Art. 143 gives transitional grandfathering for CASPs already
operating under national law (up to 18 months, shortened by some Member States).

## The two stablecoin categories

- **E-money token (EMT)** — references the value of exactly **one official currency**
  (e.g. USDC, EURC, USDT). Economically the "payment stablecoin" equivalent.
- **Asset-referenced token (ART)** — references any other value or right, or a
  combination (baskets of currencies, commodities, crypto).
- Fully algorithmic (uncollateralized) stablecoins are effectively banned from these
  categories — a token with no backing cannot meet reserve/redemption rules.

## EMT regime (Title IV) — the operative constraints

- **Art. 48** — only a **credit institution** or an authorized **electronic-money
  institution (EMI)** may issue EMTs to the public in the EU, and only after
  publishing an approved white paper. This is the provision that pushed Circle to an
  EMI licence in France (July 2024) and pushed unauthorized issuers (Tether) out.
- **Art. 49** — holders have a legal **claim at par**: redemption at any moment, at
  par value, in funds. No redemption fees.
- **Art. 50** — **prohibition of interest**: no interest or any benefit related to
  the length of holding may be granted (mirrored for ARTs in Art. 40).
- **Safeguarding/localization** — funds received must be safeguarded under the
  e-money rules as adapted by MiCA: at least **30%** of funds deposited in separate
  accounts with EU credit institutions, the remainder invested in secure, low-risk,
  highly liquid financial instruments denominated in the same currency. For
  **significant** EMTs the deposit share rises to **60%** — the much-criticized
  "reserve localization" requirement.
- **Art. 56–58** — **significant EMTs**: designation by EBA when 3+ of the Art. 43
  criteria are met (≥10 million holders; reserve ≥ €5 billion; >2.5 million
  transactions or €500 million per day as means of exchange; gateway/gatekeeper
  linkage; international significance; interconnectedness). Significant EMTs move to
  **direct EBA supervision** with higher own-funds (from 2% toward 3% of reserve),
  liquidity-management and interoperability requirements.
- **Art. 58(3)** — applies Art. 22, 23 and 24(3) to EMTs **denominated in a non-EU
  currency** — importing the usage caps below onto dollar stablecoins specifically.

## ART regime (Title III) — highlights

- **Art. 16–21** — authorization by home Member State NCA; EBA/ECB opinions; the
  **ECB can veto** an authorization on monetary-policy/monetary-sovereignty grounds
  (and can require limits where a token threatens "smooth operation of payment
  systems, monetary policy transmission or monetary sovereignty").
- **Art. 36–38** — segregated **reserve of assets**, prudent investment limited to
  highly liquid instruments; custody rules.
- **Art. 39** — permanent redemption rights.
- **Art. 43–45** — significant ARTs, EBA supervision.

## Article 23 — the currency-sovereignty clause (the "caps")

Art. 23 (extended to non-euro EMTs via Art. 58(3)) requires an issuer to **stop
issuing** and submit a wind-down/reduction plan when a token **used as a means of
exchange within a single currency area** exceeds, per day:

- **1,000,000 transactions**, and
- **€200,000,000** in aggregate transaction value.

Payments purely for exchange against other crypto-assets or funds (trading) are
excluded from the count — a carve-out that in practice has kept the caps from
binding, but the provision is the clearest statutory expression of the EU's intent
to prevent a foreign-currency stablecoin from becoming a domestic means of payment.
Recitals 54–55 tie this explicitly to **monetary sovereignty** and the currency
substitution risk.

## Enforcement reality since mid-2024

- Non-compliant USD stablecoins (chiefly **USDT**) were delisted for EEA users by
  Coinbase (Dec 2024), Crypto.com, Kraken and Binance (Q1 2025, ahead of the
  end-March 2025 ESMA deadline guidance).
- **Circle** became the first global issuer authorized (EMI licence, ACPR France,
  1 July 2024) for USDC and EURC. Société Générale-FORGE (EURCV), Banking Circle
  (EURI), Membrane/others followed; ~50+ EMT white papers notified by 2026.
- **Multi-issuance dispute (2025):** whether a token issued jointly by an EU entity
  and a non-EU entity (fungible globally) complies — the Commission read MiCA
  permissively; the **ECB objected**, warning EU reserves could be drained by
  redemptions originating abroad. Commission pressed ahead with clarifying
  guidance/legislative fix; a MiCA review is folded into the 2026 digital-omnibus
  discussions.
