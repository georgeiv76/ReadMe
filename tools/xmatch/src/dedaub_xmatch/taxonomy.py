"""The pivot taxonomy that lets findings from different tools be compared.

Each canonical :class:`~dedaub_xmatch.models.VulnClass` is mapped to:

* an **SWC id** — the de-facto interchange vocabulary (deprecated since 2020 but
  still what Mythril emits natively);
* an **OWASP Smart Contract Top 10 (2025)** id;
* a **DASP-10** category (for SmartBugs compatibility);
* the native detector names of the source tools, so a raw finding string can be
  resolved back to a canonical class.

SWC does not cover several modern DeFi classes (oracle manipulation, flash-loan
attacks, logic errors); those map to ``swc=None`` and rely on the OWASP pivot.
Mappings marked ``uncertain=True`` are the least clean and are the first
candidates for correction once labeled data exists.

OWASP ids use the **2025** edition (a stable, permanently-archived numbering).
Note the live site now serves the **2026** edition, which renumbers heavily
(e.g. Reentrancy SC05->SC08, Flash Loan SC07->SC04); OWASP is only a secondary /
documentation axis here — the actual cross-tool join is on ``VulnClass`` + SWC —
so this does not affect matching. Remap ``owasp_sc_2025`` if you need to track
the live site.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import VulnClass


@dataclass(frozen=True)
class ClassMapping:
    vuln_class: VulnClass
    swc: str | None
    owasp_sc_2025: str | None
    dasp: str | None
    # Native detector identifiers, lowercased, used for reverse lookup.
    mythril_swc: tuple[str, ...] = ()
    slither_detectors: tuple[str, ...] = ()
    dedaub_names: tuple[str, ...] = ()
    uncertain: bool = False
    note: str = ""


# fmt: off
MAPPINGS: dict[VulnClass, ClassMapping] = {
    VulnClass.REENTRANCY: ClassMapping(
        VulnClass.REENTRANCY, "SWC-107", "SC05", "Reentrancy",
        mythril_swc=("SWC-107",),
        slither_detectors=("reentrancy-eth", "reentrancy-no-eth", "reentrancy-benign",
                           "reentrancy-events", "reentrancy-unlimited-gas"),
        dedaub_names=("reentrancy", "transitive reentrancy", "read-only reentrancy"),
    ),
    VulnClass.SELFDESTRUCT: ClassMapping(
        VulnClass.SELFDESTRUCT, "SWC-106", "SC01", "Access Control",
        mythril_swc=("SWC-106",),
        slither_detectors=("suicidal",),
        dedaub_names=("accessible selfdestruct", "unprotected selfdestruct",
                      "tainted selfdestruct"),
    ),
    VulnClass.DELEGATECALL: ClassMapping(
        VulnClass.DELEGATECALL, "SWC-112", "SC01", "Access Control",
        mythril_swc=("SWC-112",),
        slither_detectors=("controlled-delegatecall", "delegatecall-loop"),
        dedaub_names=("tainted delegatecall", "delegatecall to untrusted callee"),
    ),
    VulnClass.ACCESS_CONTROL: ClassMapping(
        VulnClass.ACCESS_CONTROL, None, "SC01", "Access Control",
        mythril_swc=(),
        slither_detectors=("unprotected-upgrade", "arbitrary-send-eth"),
        dedaub_names=("tainted owner variable", "tainted ownership guard",
                      "unprotected critical function", "access control"),
        uncertain=True,
        note="No single clean SWC for generic access control; pivot on OWASP SC01.",
    ),
    VulnClass.ARBITRARY_STORAGE_WRITE: ClassMapping(
        VulnClass.ARBITRARY_STORAGE_WRITE, "SWC-124", "SC01", "Access Control",
        mythril_swc=("SWC-124",),
        slither_detectors=("controlled-array-length",),
        dedaub_names=("tainted storage write", "arbitrary storage write"),
    ),
    VulnClass.UNCHECKED_CALL: ClassMapping(
        VulnClass.UNCHECKED_CALL, "SWC-104", "SC06", "Unchecked Low Level Calls",
        mythril_swc=("SWC-104",),
        slither_detectors=("unchecked-lowlevel", "unchecked-send", "unused-return"),
        dedaub_names=("unchecked low-level call", "unchecked call"),
    ),
    VulnClass.ARBITRARY_SEND: ClassMapping(
        VulnClass.ARBITRARY_SEND, "SWC-105", "SC01", "Access Control",
        mythril_swc=("SWC-105",),
        slither_detectors=("arbitrary-send-eth", "arbitrary-send-erc20"),
        dedaub_names=("unprotected ether withdrawal", "arbitrary send",
                      "unrestricted transferfrom proxy", "untrusted transfers"),
    ),
    VulnClass.ARITHMETIC: ClassMapping(
        VulnClass.ARITHMETIC, "SWC-101", "SC08", "Arithmetic",
        mythril_swc=("SWC-101",),
        slither_detectors=("divide-before-multiply", "tautology"),
        dedaub_names=("arithmetic error", "overflow", "underflow", "erc20 underflow"),
    ),
    VulnClass.BAD_RANDOMNESS: ClassMapping(
        VulnClass.BAD_RANDOMNESS, "SWC-120", "SC09", "Bad Randomness",
        mythril_swc=("SWC-120",),
        slither_detectors=("weak-prng",),
        dedaub_names=("bad randomness", "weak randomness"),
    ),
    VulnClass.TX_ORIGIN: ClassMapping(
        VulnClass.TX_ORIGIN, "SWC-115", "SC01", "Access Control",
        mythril_swc=(),  # Mythril has NO tx.origin/SWC-115 module (verified vs module-list)
        slither_detectors=("tx-origin",),
        dedaub_names=("tx.origin authentication", "tx-origin auth"),
    ),
    VulnClass.DOS_GAS: ClassMapping(
        VulnClass.DOS_GAS, "SWC-128", "SC10", "Denial of Services",
        mythril_swc=("SWC-113",),  # Mythril emits only SWC-113 (multiple_sends); no SWC-128 module
        slither_detectors=("calls-loop", "costly-loop", "msg-value-loop"),
        dedaub_names=("unbounded mass operation", "wallet griefing", "dos through iteration",
                      "call dos", "dos through external operation"),
        note="MadMax classes; SWC-113 (failed call) covers griefing, SWC-128 (gas limit) "
             "covers unbounded ops (class SWC, but not emitted by Mythril).",
    ),
    VulnClass.SIGNATURE_MALLEABILITY: ClassMapping(
        VulnClass.SIGNATURE_MALLEABILITY, "SWC-117", "SC03", "Unknown Unknowns",
        mythril_swc=(),
        slither_detectors=(),
        dedaub_names=("ecdsa signature malleability", "signature malleability"),
        uncertain=True,
        note="SWC-117 is exact, but DASP has no signature category (-> Unknown Unknowns) "
             "and OWASP-SC 2025 folds it into SC03 Logic Errors.",
    ),
    VulnClass.UNINITIALIZED_PROXY: ClassMapping(
        VulnClass.UNINITIALIZED_PROXY, "SWC-109", "SC01", "Access Control",
        mythril_swc=(),
        slither_detectors=("uninitialized-state", "uninitialized-storage"),
        dedaub_names=("uninitialized proxy", "uninitialized storage"),
        uncertain=True,
        note="SWC-109 is uninitialized storage pointer; proxy-init is adjacent, not exact.",
    ),
    VulnClass.ORACLE_MANIPULATION: ClassMapping(
        VulnClass.ORACLE_MANIPULATION, None, "SC02", "Unknown Unknowns",
        dedaub_names=("oracle manipulation", "price manipulation"),
        note="No SWC. Modern DeFi class; OWASP SC02 (Price Oracle Manipulation) is the pivot.",
    ),
    VulnClass.FLASHLOAN: ClassMapping(
        VulnClass.FLASHLOAN, None, "SC07", "Unknown Unknowns",
        dedaub_names=("flashloan unchecked callbacks", "flash loan attack"),
        note="No SWC. OWASP SC07 (Flash Loan Attacks) is the pivot.",
    ),
    VulnClass.UNCHECKED_STATICCALL: ClassMapping(
        VulnClass.UNCHECKED_STATICCALL, "SWC-104", "SC06", "Unchecked Low Level Calls",
        mythril_swc=("SWC-104",),
        dedaub_names=("unchecked tainted staticcall", "unchecked staticcall"),
    ),
}
# fmt: on


# ---- Reverse-lookup indexes ------------------------------------------------

def _build_indexes() -> tuple[dict[str, VulnClass], dict[str, VulnClass], dict[str, VulnClass]]:
    by_swc: dict[str, VulnClass] = {}
    by_slither: dict[str, VulnClass] = {}
    by_dedaub_name: dict[str, VulnClass] = {}
    for vc, m in MAPPINGS.items():
        # SWC -> class: first mapping wins so the canonical class for an SWC is
        # stable (SWC-104 is owned by UNCHECKED_CALL, not UNCHECKED_STATICCALL).
        if m.swc:
            by_swc.setdefault(m.swc, vc)
        for extra in m.mythril_swc:
            by_swc.setdefault(extra, vc)
        for d in m.slither_detectors:
            by_slither[d.lower()] = vc
        for name in m.dedaub_names:
            by_dedaub_name[name.lower()] = vc
    return by_swc, by_slither, by_dedaub_name


_BY_SWC, _BY_SLITHER, _BY_DEDAUB_NAME = _build_indexes()


def class_for_swc(swc_id: str | None) -> VulnClass:
    if not swc_id:
        return VulnClass.UNKNOWN
    return _BY_SWC.get(swc_id.strip().upper(), VulnClass.UNKNOWN)


def class_for_slither(detector: str | None) -> VulnClass:
    if not detector:
        return VulnClass.UNKNOWN
    return _BY_SLITHER.get(detector.strip().lower(), VulnClass.UNKNOWN)


def class_for_dedaub_name(name: str | None) -> VulnClass:
    """Resolve a Dedaub warning name to a canonical class. Tries exact match,
    then substring containment (Dedaub names vary across reports)."""
    if not name:
        return VulnClass.UNKNOWN
    key = name.strip().lower()
    if key in _BY_DEDAUB_NAME:
        return _BY_DEDAUB_NAME[key]
    for known, vc in _BY_DEDAUB_NAME.items():
        if known in key or key in known:
            return vc
    return VulnClass.UNKNOWN


def swc_for_class(vc: VulnClass) -> str | None:
    m = MAPPINGS.get(vc)
    return m.swc if m else None


def owasp_for_class(vc: VulnClass) -> str | None:
    m = MAPPINGS.get(vc)
    return m.owasp_sc_2025 if m else None
