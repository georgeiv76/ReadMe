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


def test_dedaub_wrapper_with_type_key_keeps_the_warnings_list():
    # Regression (operator precedence): an envelope that also carries a top-level
    # "type" key must not discard the real warnings list.
    payload = {
        "type": "watchdog_report",
        "warnings": [{"kind": "Reentrancy", "address": "0xabc", "key_selector": "0x2e1a7d4d"}],
    }
    findings = parse_dedaub_warnings(payload)
    assert len(findings) == 1
    assert findings[0].vuln_class is VulnClass.REENTRANCY
    assert findings[0].address.endswith("abc")


def test_dedaub_bare_single_warning_object_still_unwraps():
    # A genuine single warning object (no list wrapper) is still accepted.
    findings = parse_dedaub_warnings({"type": "Reentrancy", "address": "0xabc"})
    assert len(findings) == 1
    assert findings[0].vuln_class is VulnClass.REENTRANCY


def test_dedaub_selector_regex_does_not_truncate_an_address():
    # Regression: a longer hex run in the signature field must not yield a
    # fabricated 4-byte selector.
    findings = parse_dedaub_warnings(
        [{"kind": "Tainted delegatecall", "address": "0x1",
          "function_signature": "guard at 0xdeadbeefcafebabe0000000000000000deadbeef"}]
    )
    assert findings[0].selector == UNKNOWN_SELECTOR
    # But a genuine embedded selector is still recovered.
    findings2 = parse_dedaub_warnings(
        [{"kind": "Reentrancy", "address": "0x1", "function": "withdraw(uint256) 0x2e1a7d4d"}]
    )
    assert findings2[0].selector == "0x2e1a7d4d"


def test_parse_dedaub_unknown_type_maps_to_unknown_class():
    findings = parse_dedaub_warnings(
        [{"type": "some novel finding", "address": "0x1"}],
    )
    assert findings[0].vuln_class is VulnClass.UNKNOWN


# ---- Dedaub: validated against real vulnerability_denorm rows ---------------

def test_parse_dedaub_real_denorm_fixture():
    """Regression against real ``ethereum.vulnerability_denorm`` rows (addresses
    sanitized) captured 2026-07-14 via the dedaub-monitoring MCP server. Locks in
    the confirmed column names: ``rows`` envelope, ``vulnerability_type``,
    ``confidence``, ``selector`` (bytea ``\\x`` hex), ``address`` (bytea), and
    ``stmt`` as the location."""
    payload = (EXAMPLES / "dedaub_warnings_real.json").read_text()
    findings = parse_dedaub_warnings(payload, chain="ethereum")
    assert len(findings) == 2
    assert all(f.source is Source.DEDAUB for f in findings)

    erc20 = findings[0]
    # selector read from the bytea `selector` column ("\x80dc0672"), not key_selector
    assert erc20.selector == "0x80dc0672"
    # address read + normalized from the bytea `address` column
    assert erc20.address == "0x00000000000000000000000000000000dead0001"
    # confidence from `confidence`; MEDIUM stays MEDIUM (not driven by severity=MEDIUM here)
    assert erc20.confidence is Confidence.MEDIUM
    # location from the integer `stmt` column, stringified
    assert erc20.location == "12992"
    # description from `description`
    assert erc20.description.startswith("ERC20 call does not accept")
    # classified from `vulnerability_type`; this real detector name is outside the
    # adjudicated-exploit taxonomy, so it resolves to UNKNOWN (honest: the raw row
    # is still parsed, just not one of the cross-matched classes)
    assert erc20.vuln_class is VulnClass.UNKNOWN
    assert erc20.chain == "ethereum"

    bad_smell = findings[1]
    assert bad_smell.selector == "0x081812fc"
    assert bad_smell.address == "0x00000000000000000000000000000000dead0002"
    assert bad_smell.confidence is Confidence.MEDIUM
    assert bad_smell.location == "9177"
    assert bad_smell.vuln_class is VulnClass.UNKNOWN


def test_dedaub_classifies_on_vulnerability_type_not_kind():
    """`vulnerability_kind` is a coarse category ("Vulnerability"/"Bad smell") and
    must NOT drive classification; `vulnerability_type` is the detector name."""
    findings = parse_dedaub_warnings(
        [{
            "vulnerability_kind": "Vulnerability",     # category — must be ignored
            "vulnerability_type": "reentrancy",        # detector name — must be used
            "address": "\\x00000000000000000000000000000000dead0003",
            "selector": "\\x2e1a7d4d",
            "confidence": "MEDIUM PLUS",
            "stmt": 42,
        }],
        chain="ethereum",
    )
    assert findings[0].vuln_class is VulnClass.REENTRANCY   # from vulnerability_type
    assert findings[0].selector == "0x2e1a7d4d"             # bytea \x prefix handled
    assert findings[0].address == "0x00000000000000000000000000000000dead0003"
    assert findings[0].confidence is Confidence.MEDIUM      # "MEDIUM PLUS" folds to MEDIUM
    assert findings[0].location == "42"


def test_dedaub_strip_hex_prefix_handles_bytea_and_0x():
    from dedaub_xmatch.adapters.dedaub import _strip_hex_prefix
    assert _strip_hex_prefix("\\x80dc0672") == "80dc0672"
    assert _strip_hex_prefix("0x80DC0672") == "80dc0672"
    assert _strip_hex_prefix("80dc0672") == "80dc0672"
