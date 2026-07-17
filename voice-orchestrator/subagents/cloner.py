"""Cloner sub-agent — build a reusable voice profile from the dataset.

A "voice profile" = your speaker identity (tone color) plus, per style, the
reference clips used to steer prosody/intonation. It's computed once and
reused for every synthesis.

Backends:
  openvoice  MyShell OpenVoice — separates tone-color from style (best for
             intonation control). https://github.com/myshell-ai/OpenVoice
  xtts       Coqui XTTS-v2 — strong multilingual clone from a few seconds.
  stub       No model; produces a deterministic descriptor so the whole
             pipeline (loops, evaluation, memory) is runnable/testable here.

The real backends are heavy (GPU + multi-GB weights). Import failures fall
back to `stub` with a clear message rather than crashing.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field


@dataclass
class VoiceProfile:
    engine: str
    speaker_embedding_path: str          # tone color / identity
    style_refs: dict[str, list[str]] = field(default_factory=dict)  # style -> clip paths
    meta: dict = field(default_factory=dict)

    def save(self, profile_dir: str) -> str:
        os.makedirs(profile_dir, exist_ok=True)
        path = os.path.join(profile_dir, "profile.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=2)
        return path

    @classmethod
    def load(cls, profile_dir: str) -> "VoiceProfile":
        with open(os.path.join(profile_dir, "profile.json"), encoding="utf-8") as f:
            return cls(**json.load(f))


def _resolve_device(pref: str) -> str:
    if pref != "auto":
        return pref
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _pick_refs(clips: list[dict], per_style: int = 4) -> dict[str, list[str]]:
    """Choose the best reference clips per style (longest, cleanest first)."""
    refs: dict[str, list[str]] = {}
    by_style: dict[str, list[dict]] = {}
    for c in clips:
        by_style.setdefault(c["style"], []).append(c)
    for style, cs in by_style.items():
        cs.sort(key=lambda c: c["seconds"], reverse=True)
        refs[style] = [c["path"] for c in cs[:per_style]]
    return refs


def build_profile(cfg: dict, clips: list[dict]) -> VoiceProfile:
    engine = cfg["backend"]["engine"]
    device = _resolve_device(cfg["backend"]["device"])
    profile_dir = cfg["paths"]["profile_dir"]
    os.makedirs(profile_dir, exist_ok=True)
    style_refs = _pick_refs(clips)

    if engine == "openvoice":
        return _build_openvoice(cfg, clips, style_refs, device, profile_dir)
    if engine == "xtts":
        return _build_xtts(cfg, clips, style_refs, device, profile_dir)
    return _build_stub(cfg, clips, style_refs, profile_dir)


def _build_openvoice(cfg, clips, style_refs, device, profile_dir) -> VoiceProfile:
    try:
        from openvoice import se_extractor            # type: ignore
        from openvoice.api import ToneColorConverter   # type: ignore
    except Exception as e:
        print(f"[cloner] OpenVoice not installed ({e}); using stub. "
              "Install per README to build a real clone.")
        return _build_stub(cfg, clips, style_refs, profile_dir)

    # Extract the speaker embedding (tone color) from the longest neutral clip.
    ref = (style_refs.get("neutral") or next(iter(style_refs.values())))[0]
    ckpt = os.environ.get("OPENVOICE_CKPT", "checkpoints/converter")
    converter = ToneColorConverter(f"{ckpt}/config.json", device=device)
    converter.load_ckpt(f"{ckpt}/checkpoint.pth")
    se, _ = se_extractor.get_se(ref, converter, vad=True)
    emb_path = os.path.join(profile_dir, "speaker_embedding.pth")
    try:
        import torch
        torch.save(se, emb_path)
    except Exception:
        emb_path = ref  # fall back to referencing the source clip
    return VoiceProfile("openvoice", emb_path, style_refs,
                        {"device": device, "source_ref": ref})


def _build_xtts(cfg, clips, style_refs, device, profile_dir) -> VoiceProfile:
    try:
        from TTS.api import TTS  # noqa: F401  (validate availability)
    except Exception as e:
        print(f"[cloner] Coqui TTS not installed ({e}); using stub.")
        return _build_stub(cfg, clips, style_refs, profile_dir)
    # XTTS conditions at synth time on reference wavs; the "profile" is the
    # curated list of reference clips per style.
    return VoiceProfile("xtts", "", style_refs, {"device": device})


def _build_stub(cfg, clips, style_refs, profile_dir) -> VoiceProfile:
    """Deterministic descriptor so the pipeline runs with no model/GPU."""
    h = hashlib.sha256()
    for c in sorted(clips, key=lambda c: c["rel"]):
        h.update(c["rel"].encode())
        h.update(f"{c['seconds']:.2f}".encode())
    fingerprint = h.hexdigest()[:16]
    path = os.path.join(profile_dir, "speaker_embedding.stub")
    with open(path, "w", encoding="utf-8") as f:
        f.write(fingerprint)
    return VoiceProfile("stub", path, style_refs,
                        {"fingerprint": fingerprint,
                         "note": "no model loaded; install a backend for real audio"})
