"""Canonical data model for the cross-matching confidence engine.

Every source of evidence (the Dedaub Security Suite, Mythril, later Slither/Wake,
a fuzzer) is normalized into a :class:`NormalizedFinding`. Cross-matching then
joins findings on their :meth:`NormalizedFinding.match_key` and produces one
:class:`AdjudicatedWarning` per Security Suite warning, carrying a verdict tier
and a calibrated score.

The model is deliberately format-independent: adapters own the messy job of
mapping a tool's native output into this shape, so the scoring engine never sees
a tool-specific field.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class Source(str, Enum):
    """Where a finding came from. Lineage matters for scoring: tools that share
    Dedaub's Gigahorse/Datalog lineage are NOT independent evidence."""

    DEDAUB = "dedaub"          # the Security Suite warning we are adjudicating
    MYTHRIL = "mythril"        # symbolic execution — independent technique
    SLITHER = "slither"        # source dataflow — independent, source-only
    WAKE = "wake"              # source AST/IR — independent, source-only
    FUZZER = "fuzzer"          # dynamic confirmation (ItyFuzz / in-house)

    @property
    def is_independent_of_dedaub(self) -> bool:
        """True if this source uses a technique with error modes uncorrelated
        with Dedaub's Datalog value-flow analysis. Open-source MadMax/Ethainter
        clients would return False, but we do not model them as separate sources."""
        return self in {Source.MYTHRIL, Source.SLITHER, Source.WAKE, Source.FUZZER}

    @property
    def is_dynamic(self) -> bool:
        """Dynamic confirmation is the only path to the CONFIRMED tier."""
        return self is Source.FUZZER


class Confidence(str, Enum):
    """Confidence label attached by the emitting tool (mirrors Dedaub's
    LOW/MEDIUM/HIGH warning levels and Mythril's severity)."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def rank(self) -> int:
        return {"low": 0, "medium": 1, "high": 2}[self.value]


class Verdict(str, Enum):
    """The four-tier output of the engine (see the design doc, Part 4.1)."""

    CONFIRMED = "confirmed"        # executable PoC exists — operationally 100%
    CORROBORATED = "corroborated"  # >=1 independent-technique tool agrees
    UNRESOLVED = "unresolved"      # default; ranked by calibrated score
    LIKELY_FP = "likely_fp"        # a high-precision FP heuristic fired


# Canonical vulnerability classes used as the cross-tool pivot. Values are the
# stable internal keys; taxonomy.py maps each to SWC / OWASP-SC / DASP ids and to
# each tool's native detector names.
class VulnClass(str, Enum):
    REENTRANCY = "reentrancy"
    SELFDESTRUCT = "accessible_selfdestruct"
    DELEGATECALL = "tainted_delegatecall"
    ACCESS_CONTROL = "access_control"        # tainted owner / unprotected fn
    ARBITRARY_STORAGE_WRITE = "arbitrary_storage_write"
    UNCHECKED_CALL = "unchecked_low_level_call"
    ARBITRARY_SEND = "arbitrary_send"        # unprotected ether withdrawal
    ARITHMETIC = "arithmetic"
    BAD_RANDOMNESS = "bad_randomness"
    TX_ORIGIN = "tx_origin_auth"
    DOS_GAS = "dos_gas"                       # MadMax: unbounded op / griefing
    SIGNATURE_MALLEABILITY = "signature_malleability"
    UNINITIALIZED_PROXY = "uninitialized_proxy"
    ORACLE_MANIPULATION = "oracle_manipulation"
    FLASHLOAN = "flashloan"
    UNCHECKED_STATICCALL = "unchecked_staticcall"
    UNKNOWN = "unknown"                       # class that did not map to the pivot


# A selector we could not recover. Findings with an unknown selector can still
# match at (address, class) granularity but never at selector granularity.
UNKNOWN_SELECTOR = "0x????????"


@dataclass(frozen=True)
class NormalizedFinding:
    """A single tool's finding, projected onto the canonical schema."""

    source: Source
    chain: str                       # e.g. "ethereum", "base"; lowercased
    address: str                     # 0x-prefixed, lowercased, 40 hex chars
    vuln_class: VulnClass
    selector: str = UNKNOWN_SELECTOR  # 0x + 8 hex, or UNKNOWN_SELECTOR
    confidence: Confidence = Confidence.LOW
    swc_id: Optional[str] = None     # e.g. "SWC-107"
    description: str = ""
    location: str = ""               # raw tool location (PC, sourceMap, line)
    has_poc: bool = False            # tool produced an exploit tx sequence
    raw: dict[str, Any] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        # Frozen dataclass: normalize identity fields via object.__setattr__.
        object.__setattr__(self, "chain", self.chain.strip().lower())
        object.__setattr__(self, "address", _norm_address(self.address))
        object.__setattr__(self, "selector", _norm_selector(self.selector))

    def match_key(self, *, by_selector: bool = True) -> tuple:
        """Join key for cross-matching. When ``by_selector`` is True and the
        selector is known, matching is at function granularity; otherwise it
        falls back to contract granularity."""
        if by_selector and self.selector != UNKNOWN_SELECTOR:
            return (self.chain, self.address, self.selector, self.vuln_class)
        return (self.chain, self.address, self.vuln_class)


@dataclass
class Evidence:
    """One corroborating (or refuting) signal about a Dedaub warning."""

    finding: NormalizedFinding
    agrees: bool                     # True = supports the warning
    note: str = ""


@dataclass
class AdjudicatedWarning:
    """The engine's output for a single Dedaub warning."""

    warning: NormalizedFinding       # the Dedaub finding being adjudicated
    verdict: Verdict
    score: float                     # calibrated probability the warning is real
    evidence: list[Evidence] = field(default_factory=list)
    fp_flags: list[str] = field(default_factory=list)  # FP heuristics that fired
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain": self.warning.chain,
            "address": self.warning.address,
            "selector": self.warning.selector,
            "vuln_class": self.warning.vuln_class.value,
            "swc_id": self.warning.swc_id,
            "dedaub_confidence": self.warning.confidence.value,
            "verdict": self.verdict.value,
            "score": round(self.score, 4),
            "fp_flags": self.fp_flags,
            "evidence": [
                {
                    "source": e.finding.source.value,
                    "agrees": e.agrees,
                    "vuln_class": e.finding.vuln_class.value,
                    "selector": e.finding.selector,
                    "has_poc": e.finding.has_poc,
                    "note": e.note,
                }
                for e in self.evidence
            ],
            "rationale": self.rationale,
        }


def _norm_address(addr: str) -> str:
    a = (addr or "").strip().lower()
    if a.startswith("0x"):
        a = a[2:]
    a = a.rjust(40, "0") if a else a
    return "0x" + a if a else ""


def _norm_selector(sel: str) -> str:
    if sel is None:
        return UNKNOWN_SELECTOR
    s = sel.strip().lower()
    if s in ("", "0x", UNKNOWN_SELECTOR):
        return UNKNOWN_SELECTOR
    if s.startswith("0x"):
        s = s[2:]
    # Keep only a clean 4-byte selector; anything else is "unknown".
    if len(s) == 8 and all(c in "0123456789abcdef" for c in s):
        return "0x" + s
    return UNKNOWN_SELECTOR
