"""End-to-end pipeline tests against the example fixtures."""

import json
import pathlib

from dedaub_xmatch.pipeline import run_pipeline
from dedaub_xmatch.models import Verdict, VulnClass

EXAMPLES = pathlib.Path(__file__).resolve().parents[1] / "examples"
DEDAUB = (EXAMPLES / "dedaub_warnings_example.json").read_text()
MYTHRIL = (EXAMPLES / "mythril_json_example.json").read_text()


def _by_class(result):
    return {a.warning.vuln_class: a for a in result.adjudicated}


def test_pipeline_corroborates_reentrancy_via_mythril():
    result = run_pipeline(dedaub_payload=DEDAUB, mythril_payload=MYTHRIL)
    by_class = _by_class(result)
    # Dedaub reentrancy on withdraw() selector 0x2e1a7d4d, Mythril agrees on the
    # same selector + SWC-107 -> CORROBORATED.
    reent = by_class[VulnClass.REENTRANCY]
    assert reent.verdict is Verdict.CORROBORATED
    assert any(e.finding.source.value == "mythril" and e.agrees for e in reent.evidence)


def test_pipeline_selfdestruct_without_mythril_agreement_is_unresolved():
    result = run_pipeline(dedaub_payload=DEDAUB, mythril_payload=MYTHRIL)
    by_class = _by_class(result)
    # Mythril's second finding is SWC-105 (arbitrary send), not selfdestruct,
    # so the Dedaub selfdestruct warning gets no corroboration.
    sd = by_class[VulnClass.SELFDESTRUCT]
    assert sd.verdict is Verdict.UNRESOLVED


def test_pipeline_without_mythril_is_all_unresolved():
    result = run_pipeline(dedaub_payload=DEDAUB)
    assert set(a.verdict for a in result.adjudicated) == {Verdict.UNRESOLVED}
    assert result.ran_sources == set()


def test_pipeline_fp_flag_downgrades_owner_warning():
    # Inject a Family-3 heuristic result for the tainted-owner warning (admin
    # setter -> guarded-by-design). Key on (chain, address, selector, class).
    result0 = run_pipeline(dedaub_payload=DEDAUB, mythril_payload=MYTHRIL)
    owner = next(a for a in result0.adjudicated
                 if a.warning.vuln_class is VulnClass.ACCESS_CONTROL)
    key = owner.warning.match_key(by_selector=True)
    result = run_pipeline(
        dedaub_payload=DEDAUB, mythril_payload=MYTHRIL,
        fp_flags_by_key={key: ["admin_setter_guarded_by_design"]},
    )
    owner2 = next(a for a in result.adjudicated
                  if a.warning.vuln_class is VulnClass.ACCESS_CONTROL)
    assert owner2.verdict is Verdict.LIKELY_FP


def test_pipeline_summary_counts():
    result = run_pipeline(dedaub_payload=DEDAUB, mythril_payload=MYTHRIL)
    summary = result.summary()
    assert sum(summary.values()) == 3
    assert summary["corroborated"] >= 1
