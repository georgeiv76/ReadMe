"""Tests for the four-tool label crosswalk.

These lock in the apple-to-apple mappings: a Dedaub warning and an open-source
finding for the *same* underlying bug must land on the *same* canonical class,
which is what lets the engine treat them as corroboration.
"""

from dedaub_xmatch.crosswalk import (
    CROSSWALK,
    BY_SWC,
    BY_SLITHER,
    BY_WAKE,
    canonical_for_dedaub,
)


def test_swap_publicly_reachable_matches_mythril_swc105():
    # The exact case proven end-to-end on contract 0x0000...66cb (ZwapUSDC):
    # Dedaub HIGH "Swap publicly reachable" and Mythril SWC-105 must agree.
    assert canonical_for_dedaub("Swap publicly reachable") == "arbitrary_send"
    assert BY_SWC["SWC-105"] == "arbitrary_send"


def test_reentrancy_agreed_by_all_four_tools():
    assert canonical_for_dedaub("Reentrancy") == "reentrancy"
    assert BY_SWC["SWC-107"] == "reentrancy"
    assert BY_SLITHER["reentrancy-eth"] == "reentrancy"
    assert BY_WAKE["reentrancy"] == "reentrancy"


def test_selfdestruct_agreed_across_tools():
    assert canonical_for_dedaub("Tainted selfdestruct") == "accessible_selfdestruct"
    assert BY_SWC["SWC-106"] == "accessible_selfdestruct"
    assert BY_SLITHER["suicidal"] == "accessible_selfdestruct"
    assert BY_WAKE["unprotected-selfdestruct"] == "accessible_selfdestruct"


def test_unchecked_return_is_the_three_way_overlap():
    # Mythril + Slither + Wake all cover this; Dedaub does too.
    assert canonical_for_dedaub("Unchecked Low-Level Call") == "unchecked_low_level_call"
    assert BY_SWC["SWC-104"] == "unchecked_low_level_call"
    assert BY_SLITHER["unused-return"] == "unchecked_low_level_call"
    assert BY_WAKE["unchecked-return-value"] == "unchecked_low_level_call"


def test_dedaub_only_classes_have_no_oss_corroborator():
    # These are Dedaub differentiators: cross-matching cannot help; they need
    # Dedaub's own reachability data or a fuzzer.
    for name, cls in [
        ("Suspicious decimal arithmetic", "decimal_scaling"),
        ("FlashLoan unchecked callback", "flashloan"),
        ("Merkle node can be used as leaf", "merkle_leaf_confusion"),
    ]:
        assert canonical_for_dedaub(name) == cls
    for e in CROSSWALK:
        if e.canonical in {"decimal_scaling", "flashloan", "merkle_leaf_confusion"}:
            assert e.oss_tools == ()          # no open-source tool
            assert not e.oss_cross_matchable


def test_every_dedaub_type_maps_to_a_known_class():
    # Full-catalog guard: no real Dedaub warning type falls through to unknown.
    dedaub_types = [d for e in CROSSWALK for d in e.dedaub if d != "tainted owner variable"]
    assert len(dedaub_types) >= 79
    for t in dedaub_types:
        assert canonical_for_dedaub(t) != "unknown", t


def test_no_native_label_maps_to_two_classes():
    # Integrity: each tool's native label belongs to exactly one canonical class.
    for field in ("dedaub", "slither", "wake", "mythril"):
        seen: dict[str, str] = {}
        for e in CROSSWALK:
            for lbl in getattr(e, field):
                key = lbl.lower()
                assert key not in seen, f"{field} label {lbl!r} in {seen.get(key)} and {e.canonical}"
                seen[key] = e.canonical


def test_cross_matchable_partition_counts():
    xm = [e for e in CROSSWALK if e.oss_cross_matchable]
    donly = [e for e in CROSSWALK if e.dedaub and not e.oss_tools]
    ossonly = [e for e in CROSSWALK if not e.dedaub]
    # Every class is in exactly one of the three buckets.
    assert len(xm) + len(donly) + len(ossonly) == len(CROSSWALK)
    assert len(xm) >= 15          # the corroboratable core
    assert len(donly) >= 5        # Dedaub-only differentiators
