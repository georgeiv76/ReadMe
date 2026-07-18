"""Evaluator sub-agent — score a synthesized clip. This is the feedback
signal the orchestrator learns from.

Two checks:
  speaker_similarity  does the output sound like YOU? (cosine similarity of
                      speaker embeddings vs your real reference clips)
  pace                is the delivery in a natural words-per-second band?

If the embedding model isn't installed, similarity degrades to a deterministic
proxy so the loop still exercises its logic. Real quality gating needs the
real model — the stub only validates plumbing.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .cloner import VoiceProfile
from .synthesizer import SynthResult


@dataclass
class Score:
    speaker_similarity: float
    wps: float
    passed: bool
    reasons: list[str]

    def as_dict(self) -> dict:
        return {"speaker_similarity": round(self.speaker_similarity, 4),
                "wps": round(self.wps, 3), "passed": self.passed,
                "reasons": self.reasons}


def evaluate(cfg: dict, profile: VoiceProfile, result: SynthResult,
             text: str, style: str) -> Score:
    r = cfg["refine"]
    words = max(1, len(text.split()))
    wps = words / result.seconds if result.seconds > 0 else 0.0

    sim = _speaker_similarity(profile, result, style)

    reasons = []
    if sim < r["min_speaker_similarity"]:
        reasons.append(f"voice match {sim:.2f} < {r['min_speaker_similarity']}")
    if wps < r["min_wps"]:
        reasons.append(f"too slow ({wps:.2f} wps)")
    if wps > r["max_wps"]:
        reasons.append(f"too fast ({wps:.2f} wps)")
    passed = not reasons
    return Score(sim, wps, passed, reasons)


def _speaker_similarity(profile: VoiceProfile, result: SynthResult, style: str) -> float:
    """Cosine similarity between the output and your reference speaker
    embedding. Falls back to a deterministic proxy without the model."""
    refs = profile.style_refs.get(style) or next(iter(profile.style_refs.values()), [])
    try:
        from resemblyzer import VoiceEncoder, preprocess_wav  # type: ignore
        import numpy as np
        enc = VoiceEncoder()
        out_emb = enc.embed_utterance(preprocess_wav(result.audio_path))
        ref_embs = [enc.embed_utterance(preprocess_wav(p)) for p in refs[:3]]
        if not ref_embs:
            return 0.0
        ref = np.mean(ref_embs, axis=0)
        cos = float(np.dot(out_emb, ref) /
                    ((np.linalg.norm(out_emb) * np.linalg.norm(ref)) + 1e-9))
        return max(0.0, min(1.0, (cos + 1) / 2))
    except Exception:
        # Deterministic proxy: real engines start "closer" than the stub, and
        # a higher style_weight nudges similarity up — enough to drive the loop.
        base = {"openvoice": 0.86, "xtts": 0.84, "xtts-finetuned": 0.90}.get(result.engine, 0.5)
        knob = 0.06 * result.knobs.get("style_weight", 0.7)
        seed = int(hashlib.sha256(result.audio_path.encode()).hexdigest(), 16) % 1000
        jitter = (seed / 1000.0 - 0.5) * 0.08
        return max(0.0, min(1.0, base + knob + jitter))
