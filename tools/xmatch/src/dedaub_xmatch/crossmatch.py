"""The cross-matching confidence engine.

Given one Dedaub Security Suite warning and the pool of findings produced by
other sources for the same contract, decide a :class:`Verdict` and a calibrated
score. The scoring is intentionally **asymmetric** (design doc, Part 4.4):

* Independent-technique agreement moves a warning UP strongly, because baseline
  inter-tool agreement is empirically very low, so a coincidence is informative.
* A tool running and *not* flagging moves the warning DOWN only weakly — other
  tools miss most real bugs, so silence is weak evidence of a false positive.
* Only a high-precision FP heuristic (dead code, proven guard) can drop a
  warning into ``LIKELY_FP`` — and even then it is re-rankable, never deleted.
* A dynamic PoC promotes to ``CONFIRMED`` — operationally 100%.

Weights are placeholders to be replaced by per-(source, class) values learned
from labeled history in Phase 5; the shape of the model is what matters here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Optional

from .models import (
    AdjudicatedWarning,
    Confidence,
    Evidence,
    NormalizedFinding,
    Source,
    Verdict,
    VulnClass,
)


@dataclass
class ScoringConfig:
    """Tunable weights, expressed in log-odds (natural log). Defaults encode the
    asymmetry principle and Dedaub's published ~95%-FP operating point; they are
    starting values to be calibrated, not empirical truths."""

    # Prior probability a warning is real, keyed by Dedaub's own confidence level.
    prior_by_confidence: dict[Confidence, float] = field(
        default_factory=lambda: {
            Confidence.LOW: 0.05,
            Confidence.MEDIUM: 0.15,
            Confidence.HIGH: 0.35,
        }
    )

    # Log-odds boost when an independent-technique tool AGREES at selector
    # granularity. Contract-granularity agreement gets the discounted value.
    agree_selector_logodds: float = 2.0
    agree_contract_logodds: float = 1.1

    # Weak penalty when an applicable independent tool ran but stayed silent.
    # Small by design (asymmetry): absence of agreement is weak FP evidence.
    silence_logodds: float = -0.3

    # Strong penalty from a high-precision FP heuristic. Also forces LIKELY_FP.
    fp_heuristic_logodds: float = -3.0

    # Extra multiplier when two or more *distinct* independent sources agree.
    multi_source_bonus_logodds: float = 0.8

    # Score at/above which an UNRESOLVED warning is still surfaced high in queue.
    high_priority_threshold: float = 0.5

    def prior_logodds(self, conf: Confidence) -> float:
        p = self.prior_by_confidence.get(conf, 0.05)
        p = min(max(p, 1e-6), 1 - 1e-6)
        return math.log(p / (1 - p))


def _sigmoid(logodds: float) -> float:
    if logodds >= 0:
        z = math.exp(-logodds)
        return 1.0 / (1.0 + z)
    z = math.exp(logodds)
    return z / (1.0 + z)


def adjudicate(
    warning: NormalizedFinding,
    candidates: Iterable[NormalizedFinding],
    *,
    ran_sources: Optional[set[Source]] = None,
    fp_flags: Optional[list[str]] = None,
    config: Optional[ScoringConfig] = None,
) -> AdjudicatedWarning:
    """Adjudicate a single Dedaub warning.

    ``candidates`` are findings from OTHER sources for the same contract (any
    class). ``ran_sources`` is the set of independent sources that actually
    executed against this contract (used to interpret silence — a source that
    never ran contributes no evidence either way). ``fp_flags`` are labels from
    Family-3 heuristics that fired (Phase 2+); each present flag applies the FP
    penalty and forces the ``LIKELY_FP`` tier.
    """
    cfg = config or ScoringConfig()
    ran_sources = ran_sources or set()
    fp_flags = list(fp_flags or [])

    logodds = cfg.prior_logodds(warning.confidence)
    evidence: list[Evidence] = []

    # --- Family 1/2: agreement from other sources -------------------------
    agreeing_sources: set[Source] = set()
    poc_confirmed = False

    for cand in candidates:
        if cand.source == Source.DEDAUB:
            continue  # never corroborate a Dedaub warning with Dedaub
        if not cand.source.is_independent_of_dedaub:
            continue  # correlated lineage: not independent evidence
        if cand.vuln_class != warning.vuln_class:
            continue  # different class is not corroboration of THIS warning

        # Determine match granularity.
        same_selector = (
            warning.selector == cand.selector
            and warning.selector != "0x????????"
        )
        boost = (
            cfg.agree_selector_logodds
            if same_selector
            else cfg.agree_contract_logodds
        )
        logodds += boost
        agreeing_sources.add(cand.source)

        if cand.source.is_dynamic and cand.has_poc:
            poc_confirmed = True

        evidence.append(
            Evidence(
                finding=cand,
                agrees=True,
                note=(
                    f"{cand.source.value} agrees on {cand.vuln_class.value} "
                    f"at {'selector' if same_selector else 'contract'} granularity"
                    + (" with PoC" if (cand.source.is_dynamic and cand.has_poc) else "")
                ),
            )
        )

    if len(agreeing_sources) >= 2:
        logodds += cfg.multi_source_bonus_logodds

    # --- Silence: independent sources that ran but did not agree ----------
    silent = (ran_sources & {s for s in Source if s.is_independent_of_dedaub}) - agreeing_sources
    for s in sorted(silent, key=lambda x: x.value):
        logodds += cfg.silence_logodds
        evidence.append(
            Evidence(
                finding=NormalizedFinding(
                    source=s,
                    chain=warning.chain,
                    address=warning.address,
                    vuln_class=warning.vuln_class,
                    selector=warning.selector,
                ),
                agrees=False,
                note=f"{s.value} ran but did not flag this class (weak signal)",
            )
        )

    # --- Family 3: FP heuristics ------------------------------------------
    for _ in fp_flags:
        logodds += cfg.fp_heuristic_logodds

    score = _sigmoid(logodds)

    # --- Verdict tiering --------------------------------------------------
    if poc_confirmed:
        verdict = Verdict.CONFIRMED
        score = max(score, 0.99)
        rationale = "Dynamic PoC reproduces the issue on a fork — operationally confirmed."
    elif fp_flags:
        verdict = Verdict.LIKELY_FP
        rationale = "High-precision FP heuristic(s) fired: " + ", ".join(fp_flags)
    elif agreeing_sources:
        verdict = Verdict.CORROBORATED
        rationale = (
            f"Independent agreement from {', '.join(sorted(s.value for s in agreeing_sources))}."
        )
    else:
        verdict = Verdict.UNRESOLVED
        rationale = (
            "No independent corroboration and no FP heuristic; ranked by prior/score."
        )

    return AdjudicatedWarning(
        warning=warning,
        verdict=verdict,
        score=score,
        evidence=evidence,
        fp_flags=fp_flags,
        rationale=rationale,
    )


def adjudicate_batch(
    dedaub_findings: Iterable[NormalizedFinding],
    other_findings: Iterable[NormalizedFinding],
    *,
    ran_sources: Optional[set[Source]] = None,
    fp_flags_by_key: Optional[dict[tuple, list[str]]] = None,
    config: Optional[ScoringConfig] = None,
) -> list[AdjudicatedWarning]:
    """Adjudicate every Dedaub warning against a shared pool of other findings.

    Candidates are pre-bucketed by ``(chain, address)`` so each warning is only
    compared against findings on the same contract.
    """
    fp_flags_by_key = fp_flags_by_key or {}
    pool: dict[tuple, list[NormalizedFinding]] = {}
    for f in other_findings:
        pool.setdefault((f.chain, f.address), []).append(f)

    results: list[AdjudicatedWarning] = []
    for w in dedaub_findings:
        if w.source != Source.DEDAUB:
            continue
        candidates = pool.get((w.chain, w.address), [])
        flags = fp_flags_by_key.get(
            w.match_key(by_selector=True),
            fp_flags_by_key.get(w.match_key(by_selector=False), []),
        )
        results.append(
            adjudicate(
                w,
                candidates,
                ran_sources=ran_sources,
                fp_flags=flags,
                config=config,
            )
        )

    # Highest-priority first: CONFIRMED, CORROBORATED, UNRESOLVED, LIKELY_FP,
    # then by descending score within tier.
    tier_rank = {
        Verdict.CONFIRMED: 0,
        Verdict.CORROBORATED: 1,
        Verdict.UNRESOLVED: 2,
        Verdict.LIKELY_FP: 3,
    }
    results.sort(key=lambda r: (tier_rank[r.verdict], -r.score))
    return results
