"""dedaub_xmatch — Phase 1 of the Cross-Matching Confidence Engine.

Reduces Dedaub Security Suite false positives by normalizing warnings and
independent-tool findings onto a shared taxonomy and adjudicating each warning
into a verdict tier (CONFIRMED / CORROBORATED / UNRESOLVED / LIKELY_FP).

See ``docs/reducing-security-suite-false-positives.md`` for the full design.
"""

from .models import (
    AdjudicatedWarning,
    Confidence,
    Evidence,
    NormalizedFinding,
    Source,
    Verdict,
    VulnClass,
)
from .crossmatch import ScoringConfig, adjudicate, adjudicate_batch

__all__ = [
    "AdjudicatedWarning",
    "Confidence",
    "Evidence",
    "NormalizedFinding",
    "Source",
    "Verdict",
    "VulnClass",
    "ScoringConfig",
    "adjudicate",
    "adjudicate_batch",
]

__version__ = "0.1.0"
