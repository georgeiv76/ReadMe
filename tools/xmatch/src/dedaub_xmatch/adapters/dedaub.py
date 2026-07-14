"""Adapter: Dedaub Security Suite / Watchdog warnings -> NormalizedFinding.

These are the warnings we adjudicate. The Watchdog API and the ``srcwarnings``
CLI (github.com/Dedaub/srcwarnings) return warning records; the exact JSON is not
fully public, so this parser is written **tolerantly** — it accepts several field
spellings and derives the canonical class from the warning name via the taxonomy.
The field-name candidates below are the reconciliation surface: when the real
schema is confirmed, tighten ``_first`` key lists rather than the logic.

Known field semantics (from gigahorse-toolchain ``clientlib/vulnerability_macros.dl``):
``vulnerability_type``, ``confidence`` (LOW/MEDIUM/HIGH), ``visibility``
(PUBLIC/PRIVATE), ``statement`` (a bytecode statement id), plus call-chain and
public-reachability metadata from ``VulnerabilityProcessed``.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Iterable

logger = logging.getLogger(__name__)

from ..models import (
    UNKNOWN_SELECTOR,
    Confidence,
    NormalizedFinding,
    Source,
    VulnClass,
)
from ..taxonomy import class_for_dedaub_name, swc_for_class

# Dedaub surfaces a 5-level confidence scale on the wire (LOW, MEDIUM,
# "MEDIUM PLUS", HIGH, HIGHEST — note the literal space); we normalize it onto
# the shared 3-level enum. "MEDIUM PLUS" folds to MEDIUM (Dedaub's own
# "serious warning" gate is confidence >= MEDIUM_PLUS, so it is not yet HIGH).
_CONFIDENCE = {
    "low": Confidence.LOW,
    "medium": Confidence.MEDIUM,
    "med": Confidence.MEDIUM,
    "medium plus": Confidence.MEDIUM,
    "medium_plus": Confidence.MEDIUM,
    "high": Confidence.HIGH,
    "highest": Confidence.HIGH,
}
# Bounded so a longer hex run (e.g. a 20-byte address embedded in a signature
# string) is not truncated to a bogus 4-byte selector.
_SELECTOR_RE = re.compile(r"(?<![0-9a-fA-F])0x[0-9a-fA-F]{8}(?![0-9a-fA-F])")


def _first(record: dict, keys: Iterable[str], default: Any = None) -> Any:
    for k in keys:
        if k in record and record[k] not in (None, ""):
            return record[k]
    return default


def _to_confidence(raw: Any) -> Confidence:
    # Collapse internal whitespace so "MEDIUM  PLUS" / "MEDIUM PLUS" both match.
    key = " ".join(str(raw).strip().lower().split())
    return _CONFIDENCE.get(key, Confidence.LOW)


def _extract_selector(record: dict) -> str:
    # Prefer an explicit selector field (``key_selector`` is the confirmed
    # Watchdog field; it may be the literal string "null"). Else derive from a
    # "0x........" in a signature/function field. A bare signature string
    # (transfer(address,...)) would need keccak — deferred.
    sel = _first(record, ("key_selector", "selector", "function_selector", "sighash", "sig_hash"))
    if sel and str(sel).strip().lower() != "null":
        s = str(sel).strip().lower()
        if not s.startswith("0x"):
            s = "0x" + s
        if len(s) == 10:
            return s
    fn = _first(record, ("function", "function_signature", "signature", "method"), "")
    m = _SELECTOR_RE.search(str(fn))
    if m:
        return m.group(0).lower()
    return UNKNOWN_SELECTOR


def parse_dedaub_warnings(
    payload: str | list | dict,
    *,
    chain: str = "ethereum",
    address: str | None = None,
) -> list[NormalizedFinding]:
    """Parse a Watchdog/srcwarnings warning collection into canonical findings.

    Accepts a JSON string, a list of warning records, or an object wrapping the
    list under ``warnings``/``results``/``issues``. ``chain``/``address`` are
    fallbacks used only when a record does not carry its own.
    """
    data = json.loads(payload) if isinstance(payload, str) else payload
    if isinstance(data, dict):
        records = _first(data, ("warnings", "results", "issues", "data"), [])
        # A single bare warning object is also acceptable — but only fall back
        # to it when no list was extracted (parenthesized to avoid the
        # precedence trap where a top-level "type" key discards a real list).
        if not records and ("vulnerability_type" in data or "type" in data):
            records = [data]
    else:
        records = data or []

    out: list[NormalizedFinding] = []
    skipped = 0
    for rec in records:
        if not isinstance(rec, dict):
            skipped += 1
            continue
        # ``kind`` is the confirmed Watchdog field (nullable -> "Unclassified");
        # the rest are tolerated spellings.
        name = _first(
            rec,
            ("kind", "vulnerability_type", "type", "name", "warning_type", "title", "class"),
            "",
        )
        vc = class_for_dedaub_name(str(name))
        addr = _first(rec, ("address", "contract", "contract_address"), address)
        if not addr:
            # Cannot place the warning on a contract; skip rather than mis-join,
            # but make the data loss observable to the operator.
            skipped += 1
            logger.warning(
                "Dropping Dedaub warning with no address and no fallback: kind=%r", name
            )
            continue
        rec_chain = _first(rec, ("chain", "network"), chain)
        swc = _first(rec, ("swc", "swc_id")) or swc_for_class(vc)
        out.append(
            NormalizedFinding(
                source=Source.DEDAUB,
                chain=str(rec_chain),
                address=str(addr),
                vuln_class=vc,
                selector=_extract_selector(rec),
                # ``confidence`` (likelihood the warning is a true positive) is
                # the prior driver — distinct from Dedaub's ``severity`` (impact).
                confidence=_to_confidence(
                    _first(rec, ("confidence", "level"), "low")
                ),
                swc_id=str(swc) if swc else None,
                description=str(_first(rec, ("description", "message", "detail"), name)),
                location=str(_first(rec, ("statement", "location", "pc", "line"), "")),
                raw=rec,
            )
        )
    if skipped:
        logger.warning(
            "parse_dedaub_warnings skipped %d record(s) lacking an address or shape", skipped
        )
    return out
