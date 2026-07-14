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
        # Address is required to join Mythril findings; fall back to the Dedaub
        # contract when the caller did not pass one explicitly.
        myth_addr = address or (dedaub_findings[0].address if dedaub_findings else None)
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
