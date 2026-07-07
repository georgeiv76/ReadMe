# Obligation Summary — Foreign-Currency Stablecoin at Home

**Non-USD (e.g., euro) coin under the GENIUS Act vs. non-euro (e.g., USD) coin under MiCA**

Legend: 🟢 Permitted · 🟡 Constrained · 🔴 Restrictive

| Dimension | GENIUS Act (US) — non-USD coin | MiCA (EU) — non-euro coin |
|---|---|---|
| **Peg currency restriction** | 🟢 **None explicit;** broad "monetary value" definition covers a euro peg | 🟢 **None;** any official currency may be referenced — but non-EU-currency EMTs trigger extra obligations (Art. 58(3)) |
| **Licence required** | 🟡 **US-regulated entity only:** bank subsidiary, OCC-chartered nonbank, or state-qualified issuer | 🟡 **EU-licensed entity only:** credit institution or e-money institution (parent can sit anywhere — it's the entity, not the nationality) |
| **Eligible reserve assets** | 🔴 **Exhaustive list, dollar-locked except one bucket:** US cash, US Treasuries ≤93 days, Treasury repos, government MMFs, central-bank reserves — plus bank deposits, the only clause with **no currency stated** (euro deposits technically possible; 12 U.S.C. 5903(a)(1)(A)(ii)) | 🟢 **Currency-matched:** deposits + highly liquid instruments **denominated in the pegged currency** — a USD coin may hold **US T-bills** (Level-1 assets under the EBA list) |
| **Foreign sovereign debt as reserve** | 🔴 **Not allowed** — no euro sovereign paper of any kind | 🟢 **Allowed** if currency-matched (US Treasuries for a USD coin, national euro bills for a euro coin) |
| **Forced low-yield allocation** | 🟢 **No such mandate** | 🟡 **30% of reserves** in EU-bank deposits, rising to **60% for "significant" tokens** — the localization rule Tether refused |
| **Yield to holders** | 🔴 **Prohibited** for issuers — third-party/exchange rewards remain a live loophole (OCC moving to close it) | 🔴 **Prohibited more broadly:** issuers AND crypto-asset service providers (Arts. 40/50) — no rewards loophole |
| **Usage caps** | 🟢 **None** — no limit on how big a euro coin could grow in the US | 🔴 **Hard cap for non-euro coins** (Art. 23 via Art. 58(3)): over **1M transactions + €200M/day** as means of exchange → must **stop issuing** and file a reduction plan |
| **Big-token escalation** | 🟡 **$10B threshold** → forced transition from state to federal (OCC) supervision within 360 days | 🔴 **"Significant" designation** (holders, size, transactions) → EBA supervision, 60% deposit floor, 3% own funds, stress testing |
| **Redemption** | 🟢 At fixed monetary value | 🟢 At par, at any time, **no fees** |
| **Structural mismatch** | 🔴 **Fatal in practice:** dollar T-bills (currency mismatch) or euro bank deposits only — largely uninsured at foreign branches, ~40%-per-bank concentration cap (proposed FDIC rule), and only **5 of Europe's top-30 banks** own an eligible US insured bank (FDIC BankFind, Jul 2026) | 🟢 **None:** currency-matching means a USD coin holds USD assets — the yield engine works |
| **Underlying market gap** | 🔴 No "euro T-bill" exists — the ECB issues no debt, only fragmented national bills | 🟢 Not an issue for a USD coin — the deepest safe-asset market on earth backs it |
| **Real-world proof** | 🔴 **No euro stablecoin has sought a GENIUS licence** — the economics don't close | 🟡 **USDC operates in the EU today** (Circle's French EMI); **USDT chose exile** over the deposit rule |
| **Overall viability** | 🔴 **De jure open, de facto unviable at scale** — the deposit clause is the only euro door, and it's too narrow to build a business through | 🟡 **Viable but contained** — legal, profitable, yet capped in usage and taxed by localization |

**The asymmetry in one line:** GENIUS kills the foreign coin economically; MiCA lets it live but builds a cage.

---

*Sources: GENIUS Act (Pub. L. 119-27) Secs. 2, 3, 4(a)(1), 4(a)(11), 18; MiCA (Regulation (EU) 2023/1114) Arts. 23, 40, 45, 49-50, 54, 56-58; EBA RTS on highly liquid financial instruments (LCR Level-1 mapping); ESMA statement Jan 17, 2025. Verification note: the currency-matching rule and US Treasuries' Level-1 eligibility are confirmed at statute/RTS level; Circle France's exact EU reserve composition should be click-checked against its EMT white paper before publishing.*
