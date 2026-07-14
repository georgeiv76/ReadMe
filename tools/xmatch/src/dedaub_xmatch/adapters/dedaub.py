"""Adapter: Dedaub Security Suite / Watchdog warnings -> NormalizedFinding.

These are the warnings we adjudicate. **Validated 2026-07-14** against real
warning rows read from the live Dedaub database (``<chain>.vulnerability_denorm``,
one row per warning) via the ``dedaub-monitoring`` MCP server. The confirmed
column names are used as the primary key in each ``_first`` candidate list below;
the remaining spellings are kept as tolerant fallbacks for other export shapes
(the srcwarnings CLI / Watchdog JSON API), which we have not separately captured.

Confirmed schema (``vulnerability_denorm``), with the value format as delivered:
* ``vulnerability_type`` (text) — the **detector name** we classify on, e.g.
  "ERC20 call demands high-level return value". This is the field the taxonomy
  resolves; do NOT classify on ``vulnerability_kind``.
* ``vulnerability_kind`` (text) — a coarse category only: "Vulnerability",
  "Bad smell", etc. Carried through in ``raw`` but never used for class lookup.
* ``confidence`` (enum) — LOW / MEDIUM / "MEDIUM PLUS" (literal space) / HIGH /
  HIGHEST. Likelihood the warning is real; distinct from ``severity``.
* ``severity`` (enum) — ADVISORY / LOW / MEDIUM / HIGH / CRITICAL. Impact, not
  likelihood; NormalizedFinding does not model severity, so it is not consumed.
* ``selector`` (bytea) — 4-byte function selector, serialized as ``\\x80dc0672``.
* ``address`` (bytea) — contract address, serialized as ``\\x9d2e...`` (20 bytes).
* ``stmt`` (integer) — the bytecode statement id (the finding location).
* ``description`` (text) short blurb; ``debug_message`` (text) the richer message;
  ``signature`` (text) the human function signature, e.g. "stopReward()".
* ``cwe`` (text) — a CWE id when present (NOT an SWC id), so it is not used for the
  SWC pivot; SWC is derived from the resolved class instead.

Bytea fields arrive as PostgreSQL hex output (a literal ``\\x`` prefix); the
selector/address helpers below accept that alongside a plain ``0x`` prefix.
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


def _strip_hex_prefix(value: str) -> str:
    """Drop a leading hex marker. Real bytea values arrive with PostgreSQL's
    ``\\x`` prefix; other exports use ``0x``. Returns the bare lowercase hex."""
    s = value.strip().lower()
    if s.startswith("0x") or s.startswith("\\x"):
        return s[2:]
    return s


def _extract_selector(record: dict) -> str:
    # Prefer the explicit ``selector`` field (confirmed bytea column, e.g.
    # ``\x80dc0672``); ``key_selector`` etc. are tolerated export spellings and a
    # value may be the literal string "null". Else derive from a "0x........" in a
    # signature/function field. A bare signature (transfer(address,...)) would
    # need keccak — deferred.
    sel = _first(record, ("selector", "key_selector", "function_selector", "sighash", "sig_hash"))
    if sel and str(sel).strip().lower() != "null":
        s = "0x" + _strip_hex_prefix(str(sel))
        if len(s) == 10:
            return s
    fn = _first(record, ("signature", "function", "function_signature", "method"), "")
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
        # ``rows`` is the confirmed envelope from the dedaub-monitoring query
        # source; the rest are tolerated Watchdog/srcwarnings export spellings.
        records = _first(data, ("rows", "warnings", "results", "issues", "data"), [])
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
        # ``vulnerability_type`` is the confirmed detector-name column and drives
        # classification; ``vulnerability_kind`` is only a coarse category and is
        # deliberately absent here. The rest are tolerated export spellings.
        name = _first(
            rec,
            ("vulnerability_type", "type", "name", "warning_type", "title", "class", "kind"),
            "",
        )
        vc = class_for_dedaub_name(str(name))
        addr = _first(rec, ("address", "contract", "contract_address"), address)
        if addr:
            # bytea addresses arrive as ``\x9d2e...``; normalize to 0x for the
            # model's address canonicalization (which only strips a 0x prefix).
            addr = "0x" + _strip_hex_prefix(str(addr))
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
                description=str(
                    _first(rec, ("description", "debug_message", "message", "detail"), name)
                ),
                # ``stmt`` is the confirmed bytecode statement id (an integer);
                # the rest are tolerated export spellings.
                location=str(_first(rec, ("stmt", "statement", "location", "pc", "line"), "")),
                raw=rec,
            )
        )
    if skipped:
        logger.warning(
            "parse_dedaub_warnings skipped %d record(s) lacking an address or shape", skipped
        )
    return out
