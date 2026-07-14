"""Tests for the pivot taxonomy and reverse lookups."""

from dedaub_xmatch import taxonomy as tax
from dedaub_xmatch.models import VulnClass


def test_swc_reverse_lookup():
    assert tax.class_for_swc("SWC-107") is VulnClass.REENTRANCY
    assert tax.class_for_swc("swc-106") is VulnClass.SELFDESTRUCT
    assert tax.class_for_swc("SWC-112") is VulnClass.DELEGATECALL
    assert tax.class_for_swc(None) is VulnClass.UNKNOWN
    assert tax.class_for_swc("SWC-999") is VulnClass.UNKNOWN


def test_swc_104_is_owned_by_unchecked_call_not_staticcall():
    # Both classes reference SWC-104; the primary owner must be stable.
    assert tax.class_for_swc("SWC-104") is VulnClass.UNCHECKED_CALL


def test_slither_reverse_lookup():
    assert tax.class_for_slither("reentrancy-eth") is VulnClass.REENTRANCY
    assert tax.class_for_slither("suicidal") is VulnClass.SELFDESTRUCT
    assert tax.class_for_slither("weak-prng") is VulnClass.BAD_RANDOMNESS
    assert tax.class_for_slither("tx-origin") is VulnClass.TX_ORIGIN
    assert tax.class_for_slither("not-a-detector") is VulnClass.UNKNOWN


def test_dedaub_name_exact_and_substring():
    assert tax.class_for_dedaub_name("Accessible selfdestruct") is VulnClass.SELFDESTRUCT
    assert tax.class_for_dedaub_name("Tainted delegatecall") is VulnClass.DELEGATECALL
    assert tax.class_for_dedaub_name("Transitive Reentrancy") is VulnClass.REENTRANCY
    # Substring containment for report-name variance.
    assert tax.class_for_dedaub_name("possible tainted owner variable in setter") is (
        VulnClass.ACCESS_CONTROL
    )
    assert tax.class_for_dedaub_name("") is VulnClass.UNKNOWN


def test_forward_lookup():
    assert tax.swc_for_class(VulnClass.REENTRANCY) == "SWC-107"
    assert tax.owasp_for_class(VulnClass.REENTRANCY) == "SC05"
    assert tax.swc_for_class(VulnClass.ORACLE_MANIPULATION) is None
    assert tax.owasp_for_class(VulnClass.ORACLE_MANIPULATION) == "SC02"


def test_every_class_except_unknown_has_a_mapping():
    for vc in VulnClass:
        if vc is VulnClass.UNKNOWN:
            continue
        assert vc in tax.MAPPINGS, f"{vc} missing from MAPPINGS"


def test_mythril_swc_ids_resolve():
    # Every SWC id Mythril can emit (per our mapping) resolves to a real class.
    for m in tax.MAPPINGS.values():
        for swc in m.mythril_swc:
            assert tax.class_for_swc(swc) is not VulnClass.UNKNOWN
