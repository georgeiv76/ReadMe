"""Tests for the asymmetric scoring / verdict engine (format-independent core)."""

from dedaub_xmatch.crossmatch import ScoringConfig, adjudicate, adjudicate_batch
from dedaub_xmatch.models import (
    Confidence,
    NormalizedFinding,
    Source,
    Verdict,
    VulnClass,
)

CHAIN = "ethereum"
ADDR = "0x00000000000000000000000000000000deadbeef"
SEL = "0xa9059cbb"  # transfer(address,uint256)


def dedaub(vc=VulnClass.REENTRANCY, conf=Confidence.LOW, selector=SEL):
    return NormalizedFinding(
        source=Source.DEDAUB, chain=CHAIN, address=ADDR,
        vuln_class=vc, selector=selector, confidence=conf, swc_id="SWC-107",
    )


def other(source=Source.MYTHRIL, vc=VulnClass.REENTRANCY, selector=SEL, has_poc=False):
    return NormalizedFinding(
        source=source, chain=CHAIN, address=ADDR,
        vuln_class=vc, selector=selector, has_poc=has_poc,
    )


def test_no_evidence_is_unresolved():
    r = adjudicate(dedaub(), [])
    assert r.verdict is Verdict.UNRESOLVED
    assert 0.0 < r.score < 0.5  # low prior, nothing to lift it


def test_independent_agreement_corroborates_and_lifts_score():
    base = adjudicate(dedaub(), []).score
    r = adjudicate(dedaub(), [other()])
    assert r.verdict is Verdict.CORROBORATED
    assert r.score > base
    assert any(e.agrees for e in r.evidence)


def test_selector_match_beats_contract_match():
    r_sel = adjudicate(dedaub(selector=SEL), [other(selector=SEL)])
    r_con = adjudicate(dedaub(selector=SEL), [other(selector="0x????????")])
    # Same-class agreement, but selector-granularity agreement scores higher.
    assert r_sel.score > r_con.score
    assert r_sel.verdict is Verdict.CORROBORATED
    assert r_con.verdict is Verdict.CORROBORATED


def test_different_class_is_not_corroboration():
    r = adjudicate(dedaub(vc=VulnClass.REENTRANCY),
                   [other(vc=VulnClass.ARITHMETIC)])
    assert r.verdict is Verdict.UNRESOLVED


def test_lineage_correlated_source_is_not_independent():
    # A Dedaub finding cannot corroborate another Dedaub finding.
    dup = NormalizedFinding(
        source=Source.DEDAUB, chain=CHAIN, address=ADDR,
        vuln_class=VulnClass.REENTRANCY, selector=SEL,
    )
    r = adjudicate(dedaub(), [dup])
    assert r.verdict is Verdict.UNRESOLVED


def test_dynamic_poc_confirms():
    r = adjudicate(dedaub(), [other(source=Source.FUZZER, has_poc=True)])
    assert r.verdict is Verdict.CONFIRMED
    assert r.score >= 0.99


def test_fuzzer_without_poc_does_not_confirm():
    r = adjudicate(dedaub(), [other(source=Source.FUZZER, has_poc=False)])
    assert r.verdict is Verdict.CORROBORATED
    assert r.score < 0.99


def test_fp_heuristic_forces_likely_fp():
    r = adjudicate(dedaub(conf=Confidence.HIGH), [], fp_flags=["dead_code"])
    assert r.verdict is Verdict.LIKELY_FP
    assert r.score < 0.5
    assert "dead_code" in r.fp_flags


def test_asymmetry_silence_is_weaker_than_agreement():
    cfg = ScoringConfig()
    up = adjudicate(dedaub(), [other()], config=cfg).score
    base = adjudicate(dedaub(), [], config=cfg).score
    down = adjudicate(dedaub(), [], ran_sources={Source.MYTHRIL}, config=cfg).score
    # One agreement lifts more than one silence lowers.
    assert (up - base) > (base - down)
    assert down < base  # silence still nudges down


def test_silence_only_counts_for_sources_that_ran():
    with_silence = adjudicate(dedaub(), [], ran_sources={Source.MYTHRIL, Source.SLITHER})
    without = adjudicate(dedaub(), [])
    assert with_silence.score < without.score


def test_multi_source_agreement_stacks():
    one = adjudicate(dedaub(), [other(source=Source.MYTHRIL)]).score
    two = adjudicate(
        dedaub(),
        [other(source=Source.MYTHRIL), other(source=Source.SLITHER)],
    ).score
    assert two > one


def test_confirmed_beats_fp_flag():
    # A reproducing PoC outranks an FP heuristic — evidence beats heuristic.
    r = adjudicate(
        dedaub(),
        [other(source=Source.FUZZER, has_poc=True)],
        fp_flags=["dead_code"],
    )
    assert r.verdict is Verdict.CONFIRMED


def test_batch_orders_by_tier_then_score():
    w_conf = dedaub(vc=VulnClass.REENTRANCY, selector="0x11111111")
    w_corr = dedaub(vc=VulnClass.ARITHMETIC, selector="0x22222222")
    w_unres = dedaub(vc=VulnClass.BAD_RANDOMNESS, selector="0x33333333")
    others = [
        NormalizedFinding(source=Source.FUZZER, chain=CHAIN, address=ADDR,
                          vuln_class=VulnClass.REENTRANCY, selector="0x11111111",
                          has_poc=True),
        NormalizedFinding(source=Source.MYTHRIL, chain=CHAIN, address=ADDR,
                          vuln_class=VulnClass.ARITHMETIC, selector="0x22222222"),
    ]
    out = adjudicate_batch([w_unres, w_corr, w_conf], others)
    assert [r.verdict for r in out] == [
        Verdict.CONFIRMED, Verdict.CORROBORATED, Verdict.UNRESOLVED,
    ]


def test_higher_dedaub_confidence_gives_higher_prior():
    lo = adjudicate(dedaub(conf=Confidence.LOW), []).score
    hi = adjudicate(dedaub(conf=Confidence.HIGH), []).score
    assert hi > lo
