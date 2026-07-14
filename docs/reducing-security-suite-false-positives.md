# Reducing False Positives in the Dedaub Security Suite via Cross-Tool Vulnerability Matching

**Status:** Research study + proposed system design
**Date:** 2026-07-14

This document does three things, in order:

1. **Part 1** studies how the Dedaub Security Suite (app.dedaub.com) detects potential vulnerabilities today via static analysis — the baseline we are improving from.
2. **Part 2** surveys the open-source tool landscape usable for cross-comparison of findings.
3. **Part 3** reviews what published evidence says about multi-tool consensus, and **Part 4** proposes a concrete system — a *cross-matching confidence engine* — that classifies each Security Suite warning as real or likely-false-positive with a calibrated confidence score.

> **On "100% confidence":** no static-analysis ensemble can certify a finding as real with literal certainty. What *is* achievable is a **"Confirmed" tier backed by an automatically generated proof** (a fuzzer/simulator transaction sequence that demonstrably loses funds or violates an invariant on a fork) — that is operationally equivalent to 100% — plus calibrated probabilistic tiers for everything else. The design below is built around that distinction.

---

## Part 1 — How app.dedaub.com detects vulnerabilities today

### 1.1 Pipeline overview

The Security Suite (formerly Watchdog) analyzes **deployed EVM bytecode** — no source required — through this pipeline:

```
EVM bytecode (every new deployment, all supported chains, within minutes)
   │
   ▼
Declarative decompilation to 3-address IR          ← Gigahorse → Elipmoc → Shrnkr lineage
   │   (Datalog on Soufflé; function/CFG/storage-layout/ABI reconstruction;
   │    shrinking-context config first, scalable fallback on timeout)
   ▼
~70–80+ Datalog static-analysis clients            ← value-flow/taint (flows.dl),
   │   emit warnings with type + CONFIDENCE +         guard modeling (guards.dl),
   │   public-reachability + call chains              loop/gas analysis, memory &
   │   (vulnerability_macros.dl)                      storage modeling, symbolic
   │                                                  value-flow (Symvalic/Desyan)
   ▼
Triage layers: confidence levels → automated fuzzing of flagged
contracts ("can funds be lost?") → GPT/LLM-assisted analysis →
human custodians (Watchdog service)
```

Key analyses and the research behind them:

| Analysis | Paper | What it detects | Published precision |
|---|---|---|---|
| **MadMax** | OOPSLA '18 / CACM '20 | Gas-based DoS: unbounded mass operations, wallet griefing, induction-variable overflow | 81% (13/16 sampled) |
| **Ethainter** | PLDI '20 | Composite multi-transaction taint: tainted owner variable, tainted `delegatecall`, accessible `selfdestruct`, unchecked tainted `staticcall`, tainted storage write | 82.5% |
| **Memory modeling** | OOPSLA '20 | (Infrastructure) recovers arrays/buffers/call arguments — prerequisite for taint through call data | — |
| **Symvalic value-flow** | OOPSLA '21 | Path-sensitive hybrid of Datalog value-flow + SMT solver in the fixpoint loop; suppresses infeasible-path FPs | 83–96% stmt coverage, higher TP rate than symbolic execution |

Warning classes visible on app.dedaub.com include: accessible selfdestruct, tainted delegatecall, tainted ownership guard, reentrancy and transitive reentrancy, flashloan unchecked callbacks, arithmetic errors, bad randomness, DoS through iteration/external calls, ECDSA signature malleability, unrestricted `transferFrom` proxy, unchecked low-level calls, and more.

### 1.2 The crucial fact: high false-positive rates are a *design choice*

Dedaub's own 2025 paper ("Program Analysis for High-Value Smart Contract Vulnerabilities", arXiv:2507.20672) states the intended operating point explicitly: a detector for high-value real-world vulnerabilities should flag **under 1% of contracts** while tolerating a **~95% warning-level false-positive rate** — one in twenty human inspections yields a real exploit. This deliberately trades precision for **completeness**, because missing a $10M bug is far costlier than triaging 19 dead ends. The confidence levels, automated fuzzing, and human custodians exist precisely to make that firehose triageable.

**Implication for this project:** the goal is *not* to make the analyzers themselves more conservative (that would sacrifice the completeness that finds the high-value bugs). The goal is to build a **better post-hoc triage layer** that re-ranks and auto-classifies the existing warning stream.

### 1.3 Where the false positives come from

From the papers' own evaluations and the toolchain's structure, the systemic FP sources are:

1. **Decompilation imperfection** — imprecise private-function reconstruction and CFG merges (the explicit FP cause in MadMax's evaluation; the Gigahorse→Elipmoc→Shrnkr line raised resolved-operand rates from 62.8% to 99.5% to attack exactly this).
2. **Value-flow over-approximation** — transitive `GlobalFlows` closure and conservative storage/memory aliasing connect taint sources to sinks along paths that never co-occur.
3. **Infeasible paths** — non-path-sensitive clients warn on logically unsatisfiable branch combinations (Symvalic's raison d'être).
4. **Benign intentional patterns** — admin-guarded `selfdestruct`/`delegatecall`, upgradeable proxies, and privileged setters where the guard exists but the analysis cannot prove its effectiveness. The noisiest Ethainter class (tainted owner: 15/21 TP) is exactly the guard-effectiveness class.
5. **Dead code** — a Solidity compiler quirk leaves dead library code in over a third of deployed runtime bytecode ("I See Dead Code"); warnings anchored there are unreachable.
6. **Economic non-exploitability** — technically reachable conditions whose exploitation is gas- or capital-prohibitive.
7. **The deliberate high-recall design** described in §1.2.

Each of these suggests a *different* discriminating signal — which is why a cross-matching system (Part 4) should combine several independent signal families, not just "did another tool agree."

---

## Part 2 — Open-source tools available for cross-comparison

### 2.1 The constraint that shapes everything: bytecode vs. source

app.dedaub.com analyzes **deployed bytecode**. Most open-source tools need **compilable Solidity source**. This splits the candidate set:

**Tier A — run on any deployed contract (bytecode-native), produce findings:**

| Tool | Technique | Notes |
|---|---|---|
| **Mythril** (MIT, maintained) | Symbolic execution (LASER-EVM + Z3) | `-a ADDRESS` via RPC or raw bytecode; emits **SWC IDs** in JSON — the best-behaved independent bytecode analyzer |
| **ItyFuzz** (MIT, semi-active) | Snapshot-based hybrid fuzzer | Forks live chain state, fuzzes on-chain bytecode with built-in fund-loss / reentrancy / price-manipulation oracles — the strongest *dynamic confirmation* candidate |
| Legacy SmartBugs-wrapped bytecode tools (Vandal, eThor, Pakala, teEther, MadMax, Ethainter) | Various | Nearly all unmaintained; and MadMax/Ethainter share Dedaub's lineage → **not independent evidence** |

**Tier B — run only on the verified-source subset:**

| Tool | Technique | Notes |
|---|---|---|
| **Slither** (AGPL-3.0, very active) | Static dataflow on SlithIR | ~100 detectors; `slither 0xADDRESS` auto-fetches verified Etherscan source; SARIF output |
| **Wake** (ISC, active) | Python AST/IR detectors | Reentrancy, delegatecall, proxy storage collisions; SARIF via CI action |
| **Aderyn** (GPL-3.0, active) | Rust AST detectors | Needs Foundry/Hardhat project layout; SARIF |
| **Semgrep smart-contract rules** (semi-dormant) | Pattern matching | Exploit-derived patterns (ERC777 callbacks, uninitialized proxies) |
| **GPTScan-style LLM + static confirmation** | Hybrid | The published pattern (LLM hypothesis → static dataflow confirmation) removed ~2/3 of raw LLM FPs |

**Support tooling (no findings, but needed):** heimdall-rs (independent decompiler — useful for decompilation cross-checks), evmole (selector/storage extraction), WhatsABI (**proxy resolution** — EIP-1967 implementation slots), Sourcify/Etherscan v2 API (verified source fetch).

**Dead — do not build on:** Manticore (archived 2026), Oyente, Osiris, SmartCheck, Securify v1/v2, teEther, sFuzz, ConFuzzius, MAIAN, MythX (service shut down ~2024).

### 2.2 Taxonomy for matching findings across tools

Tools name findings differently; cross-matching needs a pivot vocabulary:

- **SWC registry** — deprecated since 2020 but still the de-facto interchange (Mythril natively emits `swc_id`).
- **OWASP Smart Contract Top 10** (2025 and 2026 editions) and **EEA EthTrust Security Levels v3** (2025) — the actively maintained successors.
- **SmartBugs** maps 10+ tools' finding names onto DASP-10 categories; **OpenSCV** provides a hierarchical taxonomy with mappings to SWC/DASP and per-tool detectors.
- **SARIF 2.1.0** `taxonomies`/`taxa` is the right machine-readable carrier format.

The practical join key across the bytecode/source divide is **(chain, contract address, 4-byte function selector, vulnerability class)** — source-level tools report contract+function (→ selector), and Dedaub/Gigahorse recovers selectors from the dispatcher. Statement-level alignment across a decompiler boundary is not realistic; selector-level is.

### 2.3 Existing multi-tool frameworks

**SmartBugs v2** (active, Apache-2.0) already wraps 25 tools behind Docker with per-tool parsers into unified records and SARIF output — a useful execution substrate to borrow from. It does *category-level* mapping only, **no finding-level dedup** — the gap our system fills. Benchmarks for calibration: SmartBugs-curated (small, old solc, overfit), ScrawlD (~6.8k contracts labeled by 5-tool majority vote), Web3Bugs (516 real audit bugs), **DeFiHackLabs** (650+ real exploit PoCs — the best "true positive" anchor set), and the **Consolidated Ground Truth (CGT)** methodology (bytecode-skeleton dedup, inter-dataset contradiction detection).

---

## Part 3 — What the evidence says about cross-tool consensus

The empirical literature (2020–2026) is remarkably consistent, and it both **justifies and constrains** the cross-matching idea:

| Finding | Evidence |
|---|---|
| Single-tool precision is dismal at scale | No SAST tool exceeded 10% precision on a 10k-vuln benchmark; Slither measured at **1.23%** precision (FSE 2024). Matches Dedaub's own ~95%-FP operating point. |
| Inter-tool agreement is *naturally low* | No contract flagged by all 7 scanners in a large-scale study; ≥4-tool simultaneous detection is rare and category-limited (Sendner et al.; Durieux ICSE 2020). |
| Union of tools = recall up, precision down | Combining 8 SAST tools by union flagged +36.8pp more functions (FSE 2024). **Union is the wrong operator.** |
| **Consensus/fusion = dramatic precision gains** | **ReEP** (cross-tool fusion for reentrancy): average precision of 8 tools raised from **0.5% to 73%, max 83.6%**. GPTScan's static-confirmation stage killed ~2/3 of raw LLM FPs at a 4.39% residual FP rate. ScrawlD used 5-tool majority voting as its ground-truth proxy. |
| Tools only cover ~20% of real bug space | ~80% of real exploitable bugs are "machine-unauditable" (Web3Bugs); only ~8% of 127 real attacks were tool-detectable (ICSE 2024). |

Three design consequences:

1. **Agreement is a strong positive signal precisely *because* baseline agreement is so low.** When an independent-technique tool (symbolic execution, fuzzing) lands on the same (contract, selector, class) as a Dedaub warning, that coincidence is highly informative.
2. **Absence of agreement is weak negative evidence.** Other tools miss most true bugs, so "no one else flagged it" must *never* auto-dismiss a warning — it can only mildly lower the score. This is the asymmetry that keeps the system from destroying the Suite's completeness advantage.
3. **Confirmation beats voting.** The biggest published wins (ReEP, GPTScan, and Dedaub's own auto-fuzzing) come from *pipelining a confirmer* behind a detector, not from counting votes among similar detectors. Dynamic confirmation (fuzzing on forked state) is the only path to the "operationally 100%" tier.

---

## Part 4 — Proposed system: the Cross-Matching Confidence Engine

### 4.1 Concept

A post-processing service that consumes Security Suite warnings (via the existing Watchdog API / `srcwarnings`), gathers **independent evidence** per warning from multiple signal families, and outputs one of four verdicts with a calibrated probability:

```
CONFIRMED      — an executable PoC exists (fuzzer found a fund-loss/invariant-violation
                 sequence on a fork). Operationally 100%. Auto-escalate.
CORROBORATED   — ≥1 independent-technique tool agrees on (address, selector, class),
                 and no strong FP heuristic fires. High priority for human review.
UNRESOLVED     — default tier; ranked by calibrated score. Today's status quo.
LIKELY-FP      — one or more high-precision FP heuristics fire (dead code, proven
                 guard, economically infeasible). Auto-deprioritize, never delete.
```

### 4.2 Architecture

```
                       ┌────────────────────────────────────────────┐
                       │  Security Suite warning stream             │
                       │  (Watchdog API: type, confidence,          │
                       │   statement, call chains, reachability)    │
                       └─────────────────┬──────────────────────────┘
                                         ▼
              ┌──────────────────── Normalizer ────────────────────┐
              │ warning → (chain, address, selector, class-SWC/OWASP)│
              │ proxy resolution (EIP-1967/1167 via WhatsABI style) │
              │ bytecode-skeleton dedup (CGT method) → analyze the  │
              │ implementation once, propagate to all clones        │
              └───────┬──────────────┬──────────────┬───────────────┘
                      ▼              ▼              ▼
        ┌── Signal family 1 ──┐ ┌── family 2 ───┐ ┌── family 3 ───────┐
        │ INDEPENDENT TOOLS   │ │ DYNAMIC       │ │ FP HEURISTICS     │
        │ • Mythril on        │ │ CONFIRMATION  │ │ • dead-code check │
        │   bytecode (SWC)    │ │ • ItyFuzz /   │ │ • guard-effective-│
        │ • Slither/Wake on   │ │   in-house    │ │   ness re-check on│
        │   verified-source   │ │   fuzzer on   │ │   verified source │
        │   subset (SARIF)    │ │   forked chain│ │ • admin-pattern DB│
        │ • LLM+static-confirm│ │   state, aimed│ │   (proxy/timelock/│
        │   (GPTScan pattern) │ │   at flagged  │ │   multisig owners)│
        │                     │ │   selector    │ │ • economic-cost   │
        │                     │ │ • PoC = proof │ │   estimator       │
        └─────────┬───────────┘ └──────┬────────┘ └─────────┬─────────┘
                  └──────────────┬─────┴────────────────────┘
                                 ▼
              ┌────────── Scoring & calibration ──────────┐
              │ per-(tool, class) weighted evidence model  │
              │ trained on labeled history; calibrated     │
              │ probabilities (isotonic/Platt); asymmetric:│
              │ agreement upweights strongly, silence      │
              │ downweights weakly                         │
              └─────────────────┬──────────────────────────┘
                                ▼
              CONFIRMED / CORROBORATED / UNRESOLVED / LIKELY-FP
                                │
                                ▼
              ┌────────── Feedback loop ───────────────────┐
              │ analyst verdicts + disclosed-bug outcomes   │
              │ re-train weights; per-class precision       │
              │ dashboards; drift alerts                    │
              └─────────────────────────────────────────────┘
```

### 4.3 The three signal families, in detail

**Family 1 — independent-tool cross-matching.** For every warning, run the applicable tools and record agreement at `(address, selector, class)` granularity using the SWC/OWASP pivot taxonomy:

- **Mythril** on the deployed bytecode (works for *every* contract; symbolic execution is a genuinely different technique from Datalog value-flow, so its agreement is strong evidence).
- **Slither + Wake** on the verified-source subset (fetch via Etherscan v2/Sourcify; recompile with exact settings; map findings to selectors). Coverage is partial but value-weighted coverage is high — the contracts that matter most usually have verified source.
- **LLM + static confirmation** (the GPTScan pattern): ask an LLM whether the decompiled flagged function matches the vulnerability scenario, then *confirm* its claim with a targeted static query — published to remove ~2/3 of raw LLM FPs.
- Do **not** count Gigahorse-derived tools (MadMax/Ethainter open-source clients) as independent evidence — same lineage, correlated errors.

**Family 2 — dynamic confirmation (the path to "100%").** For warnings in fund-loss-expressible classes (reentrancy, accessible selfdestruct, tainted delegatecall, unrestricted transfers, oracle manipulation): fork the chain at head, and run a targeted fuzzer (ItyFuzz-style, or the Suite's existing fuzzing stage) *seeded with the warning* — the flagged selector, tainted storage slots, and call chains from `VulnerabilityProcessed` metadata. A minimized transaction sequence that loses funds on the fork **is** the proof; attach it to the warning. This generalizes what the Suite already does ("flagged contracts are automatically fuzzed") into a per-warning, evidence-linked verdict.

**Family 3 — targeted FP heuristics.** Each maps to a known FP source from Part 1.3:

| FP source (§1.3) | Heuristic |
|---|---|
| Dead code | Reachability re-check of the flagged statement from the dispatcher; cross-check against a second decompiler (heimdall-rs) to hedge decompilation error |
| Benign admin patterns | Resolve the guard's storage slot; if owner = known timelock/multisig/governance address (curated DB), tag as guarded-by-design |
| Guard effectiveness | On verified source, re-check the guard with a source-level analyzer — source analysis can often *prove* the modifier that bytecode analysis could not |
| Economic infeasibility | Estimate attack gas/capital cost vs. extractable value (contract TVL is already in the Suite) |
| Infeasible paths | Escalate the single warning to the Symvalic/Desyan path-sensitive engine when the cheap client that emitted it is path-insensitive |

### 4.4 Scoring: asymmetric, per-class, calibrated

- Model each verdict as evidence accumulation: start from the Suite's own confidence level as the prior, multiply in likelihood ratios per signal. Weights are learned **per (signal, vulnerability class)** — Mythril agreeing on reentrancy means something different from Mythril agreeing on bad randomness.
- **Asymmetry is a hard requirement** (Part 3): independent agreement or a PoC moves a warning *up* a lot; silence from other tools moves it *down* only slightly; only high-precision FP heuristics (dead code, proven guard) can push it into LIKELY-FP. Nothing is ever auto-deleted — LIKELY-FP is a ranking, reviewable state.
- Calibrate scores against labeled history so "0.9" empirically means ~90% — using: analyst triage verdicts (the Watchdog custodians already produce these), disclosed-bug outcomes, DeFiHackLabs exploit PoCs as true-positive anchors, and ScrawlD/CGT-style consensus sets for breadth.

### 4.5 Why this preserves the Suite's philosophy

The Suite's published operating point (flag <1% of contracts, accept ~95% warning-level FPs, keep completeness on rare high-value bugs) stays untouched — no detector is made more conservative. The engine only re-orders and annotates the triage queue: custodians see CONFIRMED items with attached PoCs first, CORROBORATED next, and stop wasting inspections on dead-code/guarded-by-design warnings. If the calibration ever misclassifies, the warning is still there, one tier down.

### 4.6 Phased roadmap

| Phase | Scope | Deliverable |
|---|---|---|
| **0. Baseline measurement** | Sample recent warnings per class; have analysts label them; measure today's per-class precision | The dataset every later phase is judged against |
| **1. Normalizer + Mythril** | Warning normalization (taxonomy pivot, proxy resolution, skeleton dedup) + Mythril-on-bytecode cross-matching — works on 100% of contracts | First agreement signal + measured lift |
| **2. FP heuristics** | Dead-code reachability, admin-pattern DB, economic-cost filter | LIKELY-FP tier; measured triage-time reduction |
| **3. Verified-source tools** | Slither/Wake runners + source-fetch/recompile infra; guard re-checking | CORROBORATED tier at full strength |
| **4. Seeded dynamic confirmation** | Per-warning targeted fuzzing on forked state, PoC minimization + attachment | CONFIRMED tier ("operationally 100%") |
| **5. Calibration + feedback loop** | Learned per-(signal, class) weights, calibrated probabilities, analyst-verdict ingestion, drift dashboards | Self-improving triage quality |

Phases 1–2 are cheap (open-source tools, no new analysis research) and attack the biggest measured pain: the effort spent inspecting warnings that independent evidence could have deprioritized automatically.

---

## Sources

**Dedaub / Gigahorse lineage:** Gigahorse (ICSE 2019); MadMax (OOPSLA 2018, CACM 2020); Ethainter (PLDI 2020); Ethereum memory modeling (OOPSLA 2020); Symvalic value-flow (OOPSLA 2021); Elipmoc (OOPSLA 2022); Shrnkr (ISSTA 2025, arXiv:2409.11157); "Program Analysis for High-Value Smart Contract Vulnerabilities" (arXiv:2507.20672); Desyan (arXiv:2508.00508); docs.dedaub.com (analysis, decompiler, contract filters); github.com/nevillegrech/gigahorse-toolchain (`flows.dl`, `guards.dl`, `loops.dl`, `vulnerability_macros.dl`); github.com/Dedaub/srcwarnings, github.com/Dedaub/srcup; dedaub.com blog ("I See Dead Code", "The Dedaub Watchdog Service", "Ethainter", "Mass disclosure of griefing vulnerabilities").

**Tools:** github.com/crytic/slither; github.com/ConsenSysDiligence/mythril; github.com/Cyfrin/aderyn; github.com/Ackee-Blockchain/wake; github.com/Decurity/semgrep-smart-contracts; github.com/crytic/echidna; github.com/crytic/medusa; github.com/fuzzland/ityfuzz; github.com/Jon-Becker/heimdall-rs; github.com/cdump/evmole; github.com/shazow/whatsabi; github.com/GPTScan/GPTScan.

**Taxonomies & frameworks:** swcregistry.io (deprecated); entethalliance.org/specs/ethtrust-sl/v3; scs.owasp.org/sctop10 (2025/2026); openscv.dei.uc.pt; github.com/smartbugs/smartbugs (+ curated/wild); SolidiFI; ScrawlD (arXiv:2202.11409); Web3Bugs (ICSE 2023); github.com/SunWeb3Sec/DeFiHackLabs; Consolidated Ground Truth (arXiv:2304.11624).

**Empirical evidence:** Durieux et al. (ICSE 2020, arXiv:1910.10601); Ghaleb & Pattabiraman (ISSTA 2020); Zhang et al. Web3Bugs (ICSE 2023); Chaliasos et al. (ICSE 2024, arXiv:2304.02981); Li et al. "SAST: How Far Are We?" (FSE 2024, arXiv:2404.18186); Sendner et al. (arXiv:2312.16533); ReEP reentrancy fusion (arXiv:2402.09094); GPTScan (ICSE 2024, arXiv:2308.03314); David et al. (arXiv:2306.12338).
