"""Four-tool vulnerability-label crosswalk.

The problem this solves: Dedaub, Mythril, Slither and Wake each name the *same*
underlying bug differently (Dedaub "Swap publicly reachable" == Mythril
"SWC-105 Unprotected Ether Withdrawal" == Slither "arbitrary-send-eth"). To
compare them apple-to-apple you must first translate every tool's native label
onto ONE shared vocabulary. This module is that translation table.

Every label list below is taken from the REAL catalog of each tool, captured
2026-07-14:
* Dedaub  — ``common.vulnerability_metadata`` (80 warning types) via the
  dedaub-monitoring MCP server.
* Mythril — the 17 detection modules reported by ``ModuleLoader`` in
  mythril 0.24.8, keyed by SWC id.
* Slither — the 99 detectors from ``slither --list-detectors`` (0.11.4).
* Wake    — the built-in detectors from ``wake detect --help`` (4.22.1).

Each :class:`CanonicalClass` is the join key used by the cross-matching engine:
two findings corroborate each other only when they land on the same canonical
class. ``oss_cross_matchable`` records whether at least one independent
open-source tool can, in principle, produce the same class — i.e. whether a
Dedaub warning of this class can be corroborated at all, or needs a different
FP-reduction strategy (Dedaub's own reachability data, a fuzzer, etc.).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CrosswalkEntry:
    canonical: str
    description: str
    # Native labels, verbatim from each tool's real catalog.
    dedaub: tuple[str, ...] = ()
    mythril: tuple[str, ...] = ()      # "SWC-105 EtherThief" style
    slither: tuple[str, ...] = ()      # detector slugs
    wake: tuple[str, ...] = ()         # detector slugs
    note: str = ""

    @property
    def oss_tools(self) -> tuple[str, ...]:
        t = []
        if self.mythril:
            t.append("mythril")
        if self.slither:
            t.append("slither")
        if self.wake:
            t.append("wake")
        return tuple(t)

    @property
    def oss_cross_matchable(self) -> bool:
        """True if a Dedaub warning of this class can be corroborated by at
        least one independent open-source tool."""
        return bool(self.dedaub) and bool(self.oss_tools)


# fmt: off
CROSSWALK: tuple[CrosswalkEntry, ...] = (

    # ============ Classes where >=1 open-source tool overlaps Dedaub ==========

    CrosswalkEntry(
        "reentrancy",
        "State/external-call reentered before state is settled.",
        dedaub=("Reentrancy", "Inconsistent Reentrancy guards"),
        mythril=("SWC-107 ExternalCalls", "SWC-107 StateChangeAfterCall"),
        slither=("reentrancy-eth", "reentrancy-no-eth", "reentrancy-benign",
                 "reentrancy-events", "reentrancy-unlimited-gas"),
        wake=("reentrancy",),
    ),
    CrosswalkEntry(
        "accessible_selfdestruct",
        "SELFDESTRUCT reachable / target overwritable by an untrusted caller.",
        dedaub=("Accessible selfdestruct", "Tainted selfdestruct", "FUZZED: Selfdestruct"),
        mythril=("SWC-106 AccidentallyKillable",),
        slither=("suicidal",),
        wake=("unprotected-selfdestruct",),
    ),
    CrosswalkEntry(
        "tainted_delegatecall",
        "DELEGATECALL target controllable by an untrusted caller (incl. in loops).",
        dedaub=("Tainted delegatecall", "Call and Delegate Together",
                "Looped delegateCall and msg.value"),
        mythril=("SWC-112 ArbitraryDelegateCall",),
        slither=("controlled-delegatecall", "delegatecall-loop"),
        wake=("unsafe-delegatecall",),
    ),
    CrosswalkEntry(
        "arbitrary_storage_write",
        "SSTORE to an attacker-controlled storage slot.",
        dedaub=("SSTORE to tainted address", "SSTORE inconsistent with others"),
        mythril=("SWC-124 ArbitraryStorage",),
        slither=("controlled-array-length",),
    ),
    CrosswalkEntry(
        "unchecked_low_level_call",
        "Return status/value of an external or token call is not checked.",
        dedaub=("Unchecked Low-Level Call", "ERC20 call demands high-level return value"),
        mythril=("SWC-104 UncheckedRetval",),
        slither=("unchecked-lowlevel", "unchecked-send", "unchecked-transfer", "unused-return"),
        wake=("unchecked-return-value", "unsafe-erc20-call"),
    ),
    CrosswalkEntry(
        "arbitrary_send",
        "Unauthorized movement of value/tokens: unprotected fund transfer, "
        "approve/transferFrom proxy, or a fund-moving DeFi op reachable by anyone.",
        dedaub=("Swap publicly reachable", "Swap reachable, contract has funds",
                "Sensitive call can be reached by anyone", "Unrestricted transfer proxy",
                "Unrestricted transferFrom Proxy", "Unrestricted approve proxy",
                "Tainted money-sensitive var in external call",
                "Rare tainted money-sensitive var in external call",
                "Call to Tainted Function", "FUZZED: Arbitrary Call", "FUZZED: Fund Loss",
                "Suspicious money transfer operation", "Suspicious money burn operation",
                "Transfer of entire balance"),
        mythril=("SWC-105 EtherThief",),
        slither=("arbitrary-send-eth", "arbitrary-send-erc20", "arbitrary-send-erc20-permit"),
        note="Dedaub's biggest cross-matchable family. 'Swap publicly reachable' == "
             "Mythril SWC-105 == Slither arbitrary-send-eth.",
    ),
    CrosswalkEntry(
        "access_control",
        "A sensitive guard/owner variable is overwritable, or a privileged "
        "action lacks an effective caller check.",
        dedaub=("Tainted Ownership Guard", "Guard can be overwritten",
                "Suspicious SSTORE guard", "Sensitive callback does not check sender",
                "Suspicious conditions on msg.sender", "Suspicious conditions on msg.sender1",
                "Suspicious conditions on msg.sender2", "Suspicious conditions on msg.sender3",
                "tainted owner variable"),  # last: tolerated legacy alias
        slither=("protected-vars", "unprotected-upgrade", "events-access",
                 "missing-zero-check", "incorrect-modifier"),
        note="Dedaub tolerated alias 'tainted owner variable' kept for back-compat.",
    ),
    CrosswalkEntry(
        "arithmetic",
        "Integer overflow/underflow or unchecked arithmetic error.",
        dedaub=("Arithmetic error",),
        mythril=("SWC-101 IntegerArithmetics",),
        slither=("divide-before-multiply", "incorrect-exp", "tautology", "incorrect-shift"),
    ),
    CrosswalkEntry(
        "bad_randomness",
        "Predictable environment value (randomness, block.timestamp) an attacker "
        "can influence.",
        dedaub=("Bad Randomness",),
        mythril=("SWC-116/120 PredictableVariables",),
        slither=("weak-prng", "gelato-unprotected-randomness", "timestamp"),
    ),
    CrosswalkEntry(
        "tx_origin_auth",
        "Authorization relies on tx.origin.",
        dedaub=("Relying on msg.sender == tx.origin",),
        mythril=("SWC-115 TxOrigin",),
        slither=("tx-origin",),
        wake=("tx-origin",),
    ),
    CrosswalkEntry(
        "dos_gas",
        "Denial of service: unbounded iteration, griefing, or a call that can "
        "wedge the transaction.",
        dedaub=("DoS: Unbounded Iteration", "DoS (Unbounded Iteration)",
                "DoS: Wallet Griefing", "DoS: Call can cause failure",
                "DoS: Suspicious revert inside loop", "Inconsistent array iteration"),
        mythril=("SWC-113 MultipleSends",),
        slither=("calls-loop", "costly-loop", "msg-value-loop", "return-bomb"),
    ),
    CrosswalkEntry(
        "signature_malleability",
        "ECDSA signature malleability / signature used as a map key.",
        dedaub=("ECDSA signature malleability",),
        slither=("domain-separator-collision",),
        note="Mythril/Wake have no dedicated signature-malleability detector.",
    ),
    CrosswalkEntry(
        "signature_replay",
        "Signed payload omits chainId/nonce -> cross-chain or replay risk.",
        dedaub=("ECDSA without chainid", "Permit omits sensitive variable",
                "Inconsistent ECDSA signing"),
        note="No open-source detector for this class -> not cross-matchable.",
    ),
    CrosswalkEntry(
        "uninitialized_proxy",
        "Initializer/guard can be (re)set by anyone; uninitialized state.",
        dedaub=("Initialization guard checked but not set",),
        slither=("uninitialized-state", "uninitialized-storage", "uninitialized-local"),
        wake=("missing-return",),
    ),
    CrosswalkEntry(
        "oracle_manipulation",
        "Price/oracle read is manipulable or unchecked for staleness.",
        dedaub=("Uniswap price manipulation potential", "Uniswap tainted token",
                "Chainlink data feed may provide stale answers", "Manipulable Tellor answer",
                "Stale value in storage"),
        slither=("chainlink-feed-registry", "chronicle-unchecked-price",
                 "pyth-unchecked-confidence", "pyth-unchecked-publishtime",
                 "pyth-deprecated-functions"),
        wake=("chainlink-deprecated-function",),
        note="Dedaub carries the flash-loanable AMM-manipulation classes; the OSS "
             "tools only have feed-specific staleness/misuse checks -> weak overlap.",
    ),
    CrosswalkEntry(
        "flashloan",
        "Flash-loan callback does not authenticate the initiator.",
        dedaub=("FlashLoan unchecked callback", "FUZZED: Imbalanced Uniswap Pair"),
        note="No open-source equivalent -> not cross-matchable.",
    ),
    CrosswalkEntry(
        "front_running",
        "Transaction-order / slippage dependence exploitable by front-running.",
        dedaub=("Swap call with 0 minAmountOut", "Vault vulnerable to front-running when (near) empty"),
        mythril=("SWC-114 TransactionOrderDependence",),
        note="Dedaub's ERC4626 inflation & zero-slippage checks vs Mythril's generic TOD.",
    ),
    CrosswalkEntry(
        "assertion_failure",
        "A reachable assert / invariant violation.",
        dedaub=("Reachable assert", "Inconsistent assertions"),
        mythril=("SWC-110 Exceptions", "SWC-110 UserAssertions", "SWC-123 RequirementsViolation"),
        slither=("assert-state-change",),
    ),
    CrosswalkEntry(
        "dead_code",
        "Dead/no-op code, unused declarations, or mis-declared mutability.",
        dedaub=("Immutable storage location declared mutable", "No-op storage load",
                "No-op internal function call", "No-op external function call",
                "Unused public function argument", "Storage leak due to undeleted mapping"),
        slither=("dead-code", "unused-state", "immutable-states", "constable-states",
                 "write-after-write", "redundant-statements"),
        wake=("unused-function", "unused-import", "unused-event", "unused-error",
              "unused-modifier", "unused-contract"),
        note="Low-severity hygiene; agreement here is cheap and rarely the FP problem.",
    ),

    # ================ Dedaub-only classes (no OSS corroborator) ===============

    CrosswalkEntry(
        "decimal_scaling",
        "Inconsistent decimal/scaling handling or unsafe monetary rounding.",
        dedaub=("Suspicious decimal arithmetic", "Suspicious token decimal arithmetic",
                "Suspicious lack of token decimal arithmetic", "Inconsistent absolute scaling",
                "Inconsistent relative scaling", "Inconsistent complex relative scaling",
                "Tokens may have inconsistent decimals", "Rounding up of monetary amount",
                "Rounding down of monetary amount"),
        note="Dedaub differentiator; no open-source tool models token decimals -> "
             "must be triaged by Dedaub's own semantics, not cross-matching.",
    ),
    CrosswalkEntry(
        "merkle_leaf_confusion",
        "Internal Merkle node usable as a leaf (2nd-preimage).",
        dedaub=("Merkle node can be used as leaf",),
    ),
    CrosswalkEntry(
        "twin_calls",
        "Repeated external calls to an untrusted contract can return "
        "inconsistent results across the same transaction.",
        dedaub=("Twin calls", "this.call()"),
    ),
    CrosswalkEntry(
        "logic_error",
        "Dedaub-specific semantic/logic smell not covered by a shared class.",
        dedaub=("Undisclosed Vulnerability", "Classifier: Suspicious contract",
                "SCREAM does not have a permit function"),
    ),

    # ================ OSS-only classes (no Dedaub label) ======================

    CrosswalkEntry(
        "unexpected_ether",
        "Contract balance assumptions broken by forced/locked ether.",
        mythril=("SWC-132 UnexpectedEther",),
        slither=("locked-ether", "incorrect-equality"),
        wake=("balance-relied-on", "msg-value-nonpayable-function"),
        note="No Dedaub label -> present for completeness; not a Dedaub FP source.",
    ),
    CrosswalkEntry(
        "arbitrary_jump",
        "Caller can redirect execution to arbitrary bytecode.",
        mythril=("SWC-127 ArbitraryJump",),
    ),
    CrosswalkEntry(
        "compiler_bug",
        "Version-specific solc miscompilation.",
        slither=("storage-array", "array-by-reference", "abiencoderv2-array",
                 "encode-packed-collision"),
        wake=("calldata-tuple-reencoding-head-overflow-bug", "empty-byte-array-copy-bug"),
    ),
    CrosswalkEntry(
        "shadowing_integrity",
        "Name/scope integrity: shadowed or reused identifiers, RTLO override, "
        "wrong-signature ABI encoding, malformed interfaces.",
        slither=("shadowing-state", "shadowing-abstract", "shadowing-builtin",
                 "shadowing-local", "name-reused", "multiple-constructors",
                 "public-mappings-nested", "uninitialized-fptr-cst", "rtlo",
                 "incorrect-return", "return-leave", "variable-scope", "void-cst",
                 "erc20-interface", "erc721-interface", "incorrect-using-for",
                 "tautological-compare", "missing-inheritance", "unimplemented-functions"),
        wake=("abi-encode-with-signature", "incorrect-interface", "complex-struct-getter",
              "axelar-proxy-contract-id", "invalid-memory-safe-assembly"),
        note="OSS-only; no Dedaub equivalent. Mostly High/Medium correctness checks "
             "that sit outside Dedaub's exploit-oriented taxonomy.",
    ),
    CrosswalkEntry(
        "code_quality",
        "Style, hygiene, gas, and low-signal informational checks. Not a "
        "vulnerability class; never a Dedaub false-positive source.",
        slither=("assembly", "boolean-cst", "boolean-equal", "cyclomatic-complexity",
                 "deprecated-standards", "erc20-indexed", "external-function",
                 "function-init-state", "low-level-calls", "naming-convention", "pragma",
                 "solc-version", "unindexed-event-address", "var-read-using-this",
                 "cache-array-length", "constant-function-asm", "constant-function-state",
                 "events-maths", "optimism-deprecation", "too-many-digits", "mapping-deletion",
                 "incorrect-unary", "enum-conversion", "out-of-order-retryable",
                 "reused-constructor"),
        wake=("call-options-not-called", "struct-mapping-deletion", "array-delete-nullification"),
    ),
)
# fmt: on


# ---- Reverse indexes -------------------------------------------------------

def _norm(s: str) -> str:
    return " ".join(s.strip().lower().split())


def _build() -> tuple[dict[str, str], dict[str, str], dict[str, str], dict[str, str]]:
    by_dedaub: dict[str, str] = {}
    by_slither: dict[str, str] = {}
    by_wake: dict[str, str] = {}
    by_swc: dict[str, str] = {}
    for e in CROSSWALK:
        for d in e.dedaub:
            by_dedaub[_norm(d)] = e.canonical
        for s in e.slither:
            by_slither[_norm(s)] = e.canonical
        for w in e.wake:
            by_wake[_norm(w)] = e.canonical
        for m in e.mythril:
            # "SWC-105 EtherThief" -> index the SWC id
            tok = m.split()[0]
            if tok.upper().startswith("SWC"):
                by_swc.setdefault(tok.upper(), e.canonical)
    return by_dedaub, by_slither, by_wake, by_swc


BY_DEDAUB, BY_SLITHER, BY_WAKE, BY_SWC = _build()


def canonical_for_dedaub(name: str | None) -> str:
    if not name:
        return "unknown"
    k = _norm(name)
    if k in BY_DEDAUB:
        return BY_DEDAUB[k]
    for known, c in BY_DEDAUB.items():
        if known in k or k in known:
            return c
    return "unknown"
