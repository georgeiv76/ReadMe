"""End-to-end Phase 1 pipeline: normalize inputs, cross-match, emit verdicts.

Phase 1 corroborates Dedaub warnings with Mythril. The pipeline is deliberately
source-agnostic: adding Slither/Wake/fuzzer findings later means appending to the
``other_findings`` pool and to ``ran_sources`` — no change to the scorer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .adapters.dedaub import parse_dedaub_warnings
from .adapters.mythril import parse_mythril_json
from .crossmatch import ScoringConfig, adjudicate_batch
from .models import AdjudicatedWarning, NormalizedFinding, Source, Verdict


@dataclass
class PipelineResult:
    adjudicated: list[AdjudicatedWarning]
    ran_sources: set[Source] = field(default_factory=set)

    def summary(self) -> dict[str, int]:
        counts = {v.value: 0 for v in Verdict}
        for a in self.adjudicated:
            counts[a.verdict.value] += 1
        return counts


def run_pipeline(
    *,
    dedaub_payload: str | list | dict,
    mythril_payload: Optional[str | list | dict] = None,
    chain: str = "ethereum",
    address: Optional[str] = None,
    fp_flags_by_key: Optional[dict[tuple, list[str]]] = None,
    config: Optional[ScoringConfig] = None,
) -> PipelineResult:
    """Adjudicate Dedaub warnings against Mythril findings for one contract.

    ``fp_flags_by_key`` lets a caller inject Family-3 heuristic results (Phase 2+)
    keyed by ``NormalizedFinding.match_key``.
    """
    dedaub_findings = parse_dedaub_warnings(dedaub_payload, chain=chain, address=address)

    other: list[NormalizedFinding] = []
    ran: set[Source] = set()
    if mythril_payload is not None:
        # Mythril output must be joined to the exact contract it analyzed. Fall
        # back to the Dedaub contract ONLY when it is unambiguous (all warnings
        # share one address); otherwise refuse rather than mis-join.
        if address:
            myth_addr: Optional[str] = address
        else:
            dedaub_addrs = {f.address for f in dedaub_findings}
            if len(dedaub_addrs) == 1:
                myth_addr = next(iter(dedaub_addrs))
            elif not dedaub_addrs:
                myth_addr = None
            else:
                raise ValueError(
                    "Cannot join Mythril output: Dedaub warnings span multiple "
                    f"contracts {sorted(dedaub_addrs)}; pass an explicit `address` "
                    "identifying the contract Mythril analyzed."
                )
        if myth_addr:
            other += parse_mythril_json(mythril_payload, chain=chain, address=myth_addr)
            ran.add(Source.MYTHRIL)

    adjudicated = adjudicate_batch(
        dedaub_findings,
        other,
        ran_sources=ran,
        fp_flags_by_key=fp_flags_by_key,
        config=config,
    )
    return PipelineResult(adjudicated=adjudicated, ran_sources=ran)
