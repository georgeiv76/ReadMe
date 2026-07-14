"""Adapter: Mythril output -> canonical NormalizedFinding.

Mythril is the primary *independent, bytecode-native* corroborator in Phase 1:
it runs on any deployed contract (``myth analyze -a <address>`` over RPC, or
``-c <runtime-bytecode>``), uses symbolic execution — a technique with error
modes uncorrelated with Dedaub's Datalog value-flow — and emits SWC ids.

This module parses Mythril's two machine formats:

* ``-o json``   — an object ``{"issues": [...], "success": ...}``; each issue has
  ``swc-id`` (bare number, e.g. ``"107"``), ``function`` (a name, or the
  bytecode-mode form ``_function_0x<selector>``), ``severity``, ``tx_sequence``.
* ``-o jsonv2`` — a list of report objects; each issue has ``swcID``
  (``"SWC-107"``), ``locations[].sourceMap``, ``extra.testCases``.

The parser is the tested core; :func:`run_mythril` is a thin, optional wrapper
that shells out to ``myth`` and is never imported unless called.
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Any

from ..models import (
    UNKNOWN_SELECTOR,
    Confidence,
    NormalizedFinding,
    Source,
    VulnClass,
)
from ..taxonomy import class_for_swc

_SELECTOR_RE = re.compile(r"_function_0x([0-9a-fA-F]{8})\b")
_SEVERITY = {
    "high": Confidence.HIGH,
    "medium": Confidence.MEDIUM,
    "low": Confidence.LOW,
}


def _normalize_swc(raw: Any) -> str | None:
    """Accept ``"107"``, ``107``, ``"SWC-107"`` -> ``"SWC-107"``."""
    if raw is None:
        return None
    s = str(raw).strip().upper()
    if not s:
        return None
    if s.startswith("SWC-"):
        return s
    if s.startswith("SWC"):
        s = s[3:].lstrip("-")
    if s.isdigit():
        return f"SWC-{s}"
    return None


def _selector_from_function(function: Any) -> str:
    """Extract a 4-byte selector from Mythril's ``function`` field when it is in
    the bytecode-mode ``_function_0x<selector>`` form, or a bare ``0x<selector>``.
    A resolved human signature (``"transfer(address,uint256)"``) yields nothing
    here — use :func:`_selector_from_steps`, which is more robust."""
    if not function:
        return UNKNOWN_SELECTOR
    m = _SELECTOR_RE.search(str(function))
    if m:
        return "0x" + m.group(1).lower()
    s = str(function).strip().lower()
    if s.startswith("0x") and len(s) == 10:
        return s
    return UNKNOWN_SELECTOR


def _selector_from_steps(steps: Any) -> str:
    """Recover the selector from a PoC transaction sequence — the most reliable
    method, per Mythril's own ``resolve_function_names`` (it keys on
    ``step["input"][:10]``). We take the LAST step that targets a deployed
    contract (non-empty ``address``; the creation step has ``address == ""``)
    and read its 4-byte calldata prefix. Works even when ``function`` is a bare
    signature, ``"fallback"``, or an ambiguous ``"a() or b()"``."""
    if not isinstance(steps, list):
        return UNKNOWN_SELECTOR
    for step in reversed(steps):
        if not isinstance(step, dict):
            continue
        if not step.get("address"):  # "" -> contract creation, skip
            continue
        data = str(step.get("input") or step.get("calldata") or "")
        if data.startswith("0x") and len(data) >= 10:
            candidate = data[:10].lower()
            if all(c in "0123456789abcdef" for c in candidate[2:]):
                return candidate
    return UNKNOWN_SELECTOR


def _selector_for_issue(function: Any, steps: Any) -> str:
    """Best-effort selector: the tx-sequence prefix wins (works for deployed
    bytecode where Mythril resolves ``function`` to a human signature); fall
    back to parsing the ``function`` label."""
    sel = _selector_from_steps(steps)
    if sel != UNKNOWN_SELECTOR:
        return sel
    return _selector_from_function(function)


def _severity_to_confidence(sev: Any) -> Confidence:
    return _SEVERITY.get(str(sev).strip().lower(), Confidence.LOW)


def parse_mythril_json(
    payload: str | dict | list,
    *,
    chain: str,
    address: str,
) -> list[NormalizedFinding]:
    """Parse Mythril ``-o json`` OR ``-o jsonv2`` output into findings.

    ``chain`` and ``address`` are supplied by the caller (the identity of the
    analyzed contract is context Mythril output does not always carry).
    """
    data = json.loads(payload) if isinstance(payload, str) else payload

    # jsonv2 is a list of report objects; json is a single object.
    if isinstance(data, list):
        return _parse_v2(data, chain=chain, address=address)
    if isinstance(data, dict) and "issues" in data:
        return _parse_v1(data, chain=chain, address=address)
    # Unrecognized shape -> no findings rather than a crash.
    return []


def _parse_v1(data: dict, *, chain: str, address: str) -> list[NormalizedFinding]:
    out: list[NormalizedFinding] = []
    for issue in data.get("issues") or []:
        swc = _normalize_swc(issue.get("swc-id") or issue.get("swcID"))
        vc = class_for_swc(swc)
        tx_seq = issue.get("tx_sequence") or {}
        steps = tx_seq.get("steps") if isinstance(tx_seq, dict) else None
        selector = _selector_for_issue(issue.get("function"), steps)
        has_poc = bool(issue.get("tx_sequence"))
        out.append(
            NormalizedFinding(
                source=Source.MYTHRIL,
                chain=chain,
                address=address,
                vuln_class=vc,
                selector=selector,
                confidence=_severity_to_confidence(issue.get("severity")),
                swc_id=swc,
                description=str(issue.get("title") or issue.get("description") or ""),
                location=str(issue.get("address", "")),
                has_poc=has_poc,
                raw=issue,
            )
        )
    return out


def _parse_v2(reports: list, *, chain: str, address: str) -> list[NormalizedFinding]:
    out: list[NormalizedFinding] = []
    for report in reports:
        if not isinstance(report, dict):
            continue
        for issue in report.get("issues") or []:
            swc = _normalize_swc(issue.get("swcID") or issue.get("swc-id"))
            vc = class_for_swc(swc)
            desc = issue.get("description") or {}
            head = desc.get("head") if isinstance(desc, dict) else str(desc)
            extra = issue.get("extra") or {}
            test_cases = extra.get("testCases") or []
            has_poc = bool(test_cases)
            # jsonv2 has no function field, but the PoC steps still carry the
            # triggering calldata, so a selector is often recoverable.
            steps = None
            if test_cases and isinstance(test_cases[0], dict):
                steps = test_cases[0].get("steps")
            selector = _selector_from_steps(steps)
            locs = issue.get("locations") or []
            loc = locs[0].get("sourceMap", "") if locs and isinstance(locs[0], dict) else ""
            out.append(
                NormalizedFinding(
                    source=Source.MYTHRIL,
                    chain=chain,
                    address=address,
                    vuln_class=vc,
                    selector=selector,
                    confidence=_severity_to_confidence(issue.get("severity")),
                    swc_id=swc,
                    description=str(issue.get("swcTitle") or head or ""),
                    location=str(loc),
                    has_poc=has_poc,
                    raw=issue,
                )
            )
    return out


def run_mythril(
    address: str,
    *,
    chain: str = "ethereum",
    rpc: str | None = None,
    timeout: int = 300,
    execution_timeout: int = 120,
    myth_bin: str = "myth",
) -> list[NormalizedFinding]:  # pragma: no cover - requires myth + network
    """Optional: shell out to a real Mythril install and parse the result.

    Not exercised by the test suite (needs ``myth`` and an RPC endpoint). Raises
    ``FileNotFoundError`` if ``myth`` is absent, or ``RuntimeError`` on failure.
    """
    cmd = [myth_bin, "analyze", "-a", address, "-o", "json",
           "--execution-timeout", str(execution_timeout)]
    if rpc:
        cmd += ["--rpc", rpc]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Mythril binary '{myth_bin}' not found; install with `pip install mythril`."
        ) from e
    # Mythril prints JSON to stdout even when it finds issues (nonzero exit).
    stdout = proc.stdout.strip()
    if not stdout:
        raise RuntimeError(f"Mythril produced no output. stderr:\n{proc.stderr[:2000]}")
    return parse_mythril_json(stdout, chain=chain, address=address)
