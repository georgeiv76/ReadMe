"""Tests for the Dedaub and Mythril adapters against realistic fixtures."""

import json
import pathlib

from dedaub_xmatch.adapters.dedaub import parse_dedaub_warnings
from dedaub_xmatch.adapters.mythril import parse_mythril_json, _normalize_swc
from dedaub_xmatch.models import Confidence, Source, VulnClass, UNKNOWN_SELECTOR

EXAMPLES = pathlib.Path(__file__).resolve().parents[1] / "examples"


# ---- Mythril ---------------------------------------------------------------

def test_normalize_swc_variants():
    assert _normalize_swc("107") == "SWC-107"
    assert _normalize_swc(107) == "SWC-107"
    assert _normalize_swc("SWC-107") == "SWC-107"
    assert _normalize_swc("swc107") == "SWC-107"
    assert _normalize_swc("") is None
    assert _normalize_swc(None) is None


def test_parse_mythril_json_v1_fixture():
    payload = (EXAMPLES / "mythril_json_example.json").read_text()
    findings = parse_mythril_json(payload, chain="ethereum", address="0xDEADBEEF")
    assert len(findings) == 2
    reent = findings[0]
    assert reent.source is Source.MYTHRIL
    assert reent.vuln_class is VulnClass.REENTRANCY
    assert reent.swc_id == "SWC-107"
    assert reent.selector == "0x2e1a7d4d"      # extracted from _function_0x...
    assert reent.confidence is Confidence.HIGH
    assert reent.has_poc is True                # tx_sequence present
    withdraw = findings[1]
    assert withdraw.vuln_class is VulnClass.ARBITRARY_SEND
    assert withdraw.swc_id == "SWC-105"
    assert withdraw.selector == "0x3ccfd60b"
    assert withdraw.has_poc is False            # tx_sequence null


def test_parse_mythril_jsonv2():
    v2 = [
        {
            "issues": [
                {
                    "swcID": "SWC-107",
                    "swcTitle": "Reentrancy",
                    "description": {"head": "Read of persistent state following external call",
                                    "tail": "..."},
                    "severity": "Medium",
                    "locations": [{"sourceMap": "1053:1:0"}],
                    "extra": {"testCases": [{"input": "0x2e1a7d4d"}]},
                }
            ],
            "meta": {},
            "sourceType": "raw-bytecode",
            "sourceFormat": "evm-byzantium-bytecode",
            "sourceList": ["0x6080..."],
        }
    ]
    findings = parse_mythril_json(v2, chain="ethereum", address="0xDEADBEEF")
    assert len(findings) == 1
    f = findings[0]
    assert f.vuln_class is VulnClass.REENTRANCY
    assert f.swc_id == "SWC-107"
    assert f.confidence is Confidence.MEDIUM
    assert f.selector == UNKNOWN_SELECTOR       # jsonv2 has no function field
    assert f.has_poc is True                    # extra.testCases present


def test_selector_recovered_from_tx_sequence_when_function_is_signature():
    # Deployed-bytecode case: Mythril resolves `function` to a human signature,
    # so the selector must come from the PoC calldata prefix, not the label.
    payload = {
        "issues": [
            {
                "swc-id": "107",
                "function": "withdraw(uint256)",   # human signature, no 0x here
                "severity": "High",
                "title": "State access after external call",
                "tx_sequence": {
                    "steps": [
                        {"address": "", "input": "0x6080604052..."},  # creation, skipped
                        {"address": "0x901d12", "input":
                         "0x2e1a7d4d0000000000000000000000000000000000000000000000000000000000000001"},
                    ]
                },
            }
        ],
        "success": True,
    }
    findings = parse_mythril_json(payload, chain="ethereum", address="0xDEADBEEF")
    assert findings[0].selector == "0x2e1a7d4d"     # recovered from step calldata
    assert findings[0].vuln_class is VulnClass.REENTRANCY


def test_selector_from_steps_ignores_creation_step():
    from dedaub_xmatch.adapters.mythril import _selector_from_steps
    # Only the creation step (address == "") -> no selector.
    assert _selector_from_steps([{"address": "", "input": "0x6080abcd"}]) == UNKNOWN_SELECTOR
    # A real call step -> its 4-byte prefix.
    assert _selector_from_steps([{"address": "0xabc", "input": "0xa9059cbbdead"}]) == "0xa9059cbb"


def test_parse_mythril_empty_and_malformed():
    assert parse_mythril_json({"issues": []}, chain="e", address="0x1") == []
    assert parse_mythril_json('{"unexpected": 1}', chain="e", address="0x1") == []
    assert parse_mythril_json([], chain="e", address="0x1") == []


# ---- Dedaub ----------------------------------------------------------------

def test_parse_dedaub_warnings_fixture():
    payload = (EXAMPLES / "dedaub_warnings_example.json").read_text()
    findings = parse_dedaub_warnings(payload)
    assert len(findings) == 3
    assert all(f.source is Source.DEDAUB for f in findings)

    reent = findings[0]
    assert reent.vuln_class is VulnClass.REENTRANCY
    assert reent.confidence is Confidence.MEDIUM
    assert reent.selector == "0x2e1a7d4d"       # derived from "withdraw(uint256) 0x..."
    assert reent.swc_id == "SWC-107"
    assert reent.address == "0x00000000000000000000000000000000deadbeef"

    selfdestruct = findings[1]
    assert selfdestruct.vuln_class is VulnClass.SELFDESTRUCT
    assert selfdestruct.confidence is Confidence.HIGH
    assert selfdestruct.selector == "0x9cb8a26a"  # explicit selector field

    owner = findings[2]
    assert owner.vuln_class is VulnClass.ACCESS_CONTROL
    assert owner.confidence is Confidence.LOW


def test_parse_dedaub_list_form_and_address_fallback():
    records = [{"type": "reentrancy", "confidence": "high"}]
    # No address in record -> falls back to the address argument.
    findings = parse_dedaub_warnings(records, address="0xabc")
    assert len(findings) == 1
    assert findings[0].address.endswith("abc")
    # No address anywhere -> record skipped rather than mis-joined.
    assert parse_dedaub_warnings([{"type": "reentrancy"}]) == []


def test_dedaub_five_level_confidence_scale():
    from dedaub_xmatch.adapters.dedaub import _to_confidence
    assert _to_confidence("LOW") is Confidence.LOW
    assert _to_confidence("MEDIUM") is Confidence.MEDIUM
    assert _to_confidence("MEDIUM PLUS") is Confidence.MEDIUM   # literal space
    assert _to_confidence("MEDIUM_PLUS") is Confidence.MEDIUM
    assert _to_confidence("HIGH") is Confidence.HIGH
    assert _to_confidence("HIGHEST") is Confidence.HIGH
    assert _to_confidence("bogus") is Confidence.LOW            # safe default


def test_dedaub_kind_field_and_null_selector():
    records = [
        {"kind": "Reentrancy", "address": "0x1", "key_selector": "null",
         "confidence": "HIGHEST"},
    ]
    findings = parse_dedaub_warnings(records)
    assert findings[0].vuln_class is VulnClass.REENTRANCY   # read from `kind`
    assert findings[0].selector == UNKNOWN_SELECTOR         # "null" -> unknown
    assert findings[0].confidence is Confidence.HIGH        # HIGHEST folds to HIGH


def test_dedaub_null_kind_is_unknown_class():
    findings = parse_dedaub_warnings([{"kind": None, "address": "0x1"}])
    assert findings[0].vuln_class is VulnClass.UNKNOWN


def test_dedaub_confidence_not_taken_from_severity():
    # A high severity but low confidence must map to LOW (impact != likelihood).
    findings = parse_dedaub_warnings(
        [{"kind": "Reentrancy", "address": "0x1", "confidence": "LOW", "severity": "CRITICAL"}]
    )
    assert findings[0].confidence is Confidence.LOW


def test_parse_dedaub_unknown_type_maps_to_unknown_class():
    findings = parse_dedaub_warnings(
        [{"type": "some novel finding", "address": "0x1"}],
    )
    assert findings[0].vuln_class is VulnClass.UNKNOWN
