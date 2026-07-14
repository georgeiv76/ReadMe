"""Command-line entry point for the Phase 1 cross-matcher.

Example
-------
    xmatch --dedaub warnings.json --mythril myth.json \
           --chain ethereum --address 0xabc... --format table

Both inputs are files (or ``-`` for stdin) containing the respective tool's
JSON. With ``--mythril`` omitted, every warning is simply ranked by prior/score
(the current status-quo triage), which is a useful baseline to diff against.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .pipeline import run_pipeline
from .models import Verdict

_TIER_GLYPH = {
    Verdict.CONFIRMED: "[CONFIRMED]  ",
    Verdict.CORROBORATED: "[CORROBORAT] ",
    Verdict.UNRESOLVED: "[UNRESOLVED] ",
    Verdict.LIKELY_FP: "[LIKELY-FP]  ",
}


def _read(path: str | None) -> Any:
    if path is None:
        return None
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _render_table(result) -> str:
    lines = []
    summary = result.summary()
    lines.append(
        "Summary: "
        + "  ".join(f"{k}={v}" for k, v in summary.items())
        + f"   (sources run: {', '.join(sorted(s.value for s in result.ran_sources)) or 'none'})"
    )
    lines.append("-" * 88)
    for a in result.adjudicated:
        w = a.warning
        agrees = [e.finding.source.value for e in a.evidence if e.agrees]
        lines.append(
            f"{_TIER_GLYPH[a.verdict]} score={a.score:0.3f}  "
            f"{w.vuln_class.value:<24} {w.selector}  {w.address[:10]}…"
        )
        detail = f"    {a.rationale}"
        if agrees:
            detail += f"  [agree: {', '.join(agrees)}]"
        if a.fp_flags:
            detail += f"  [fp: {', '.join(a.fp_flags)}]"
        lines.append(detail)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="xmatch",
        description="Cross-match Dedaub Security Suite warnings against independent tools.",
    )
    p.add_argument("--dedaub", required=True, help="Dedaub/Watchdog warnings JSON (or - for stdin)")
    p.add_argument("--mythril", help="Mythril -o json/jsonv2 output (or - for stdin)")
    p.add_argument("--chain", default="ethereum")
    p.add_argument("--address", help="Contract address (fallback if absent in warnings)")
    p.add_argument("--format", choices=("table", "json"), default="table")
    args = p.parse_args(argv)

    result = run_pipeline(
        dedaub_payload=_read(args.dedaub),
        mythril_payload=_read(args.mythril),
        chain=args.chain,
        address=args.address,
    )

    if args.format == "json":
        print(json.dumps(
            {
                "summary": result.summary(),
                "ran_sources": sorted(s.value for s in result.ran_sources),
                "warnings": [a.to_dict() for a in result.adjudicated],
            },
            indent=2,
        ))
    else:
        print(_render_table(result))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
