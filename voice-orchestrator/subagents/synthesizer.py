"""Synthesizer sub-agent — text -> speech in your cloned voice.

Given a VoiceProfile, a piece of text, a style, and a set of tunable knobs
(chosen by the refinement loop), produce a WAV. Returns the output path plus
measured facts the evaluator needs (duration, etc.).
"""
from __future__ import annotations

import math
import os
import struct
import wave
from dataclasses import dataclass

from .cloner import VoiceProfile


@dataclass
class SynthResult:
    audio_path: str
    seconds: float
    engine: str
    knobs: dict


def synthesize(cfg: dict, profile: VoiceProfile, text: str, style: str,
               knobs: dict, out_path: str) -> SynthResult:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    if profile.engine == "openvoice":
        return _synth_openvoice(cfg, profile, text, style, knobs, out_path)
    if profile.engine == "xtts":
        return _synth_xtts(cfg, profile, text, style, knobs, out_path)
    return _synth_stub(cfg, profile, text, style, knobs, out_path)


def _pick_reference(profile: VoiceProfile, style: str, strategy: str) -> str:
    refs = profile.style_refs.get(style) or next(iter(profile.style_refs.values()), [])
    if not refs:
        return ""
    if strategy == "longest":
        return refs[0]            # refs are stored longest-first
    if strategy == "random":
        # deterministic "random" — rotate by text length, no RNG needed
        return refs[len(refs) // 2]
    return refs[0]                # "best"


def _synth_openvoice(cfg, profile, text, style, knobs, out_path) -> SynthResult:
    try:
        import torch  # noqa: F401
        from openvoice.api import BaseSpeakerTTS, ToneColorConverter  # type: ignore
    except Exception as e:
        print(f"[synth] OpenVoice unavailable ({e}); stub audio.")
        return _synth_stub(cfg, profile, text, style, knobs, out_path)
    # Real path: base TTS renders the words + prosody, converter paints your
    # tone color on top. style_weight/temperature steer expressiveness.
    ref = _pick_reference(profile, style, knobs.get("reference_pick", "best"))
    device = profile.meta.get("device", "cpu")
    base = BaseSpeakerTTS(os.environ.get("OPENVOICE_BASE", "checkpoints/base_speaker/config.json"),
                          device=device)
    base.load_ckpt(os.environ.get("OPENVOICE_BASE_CKPT", "checkpoints/base_speaker/checkpoint.pth"))
    tmp = out_path + ".base.wav"
    base.tts(text, tmp, speaker=style if style in ("neutral", "default") else "default",
             language="English", speed=1.0)
    converter = ToneColorConverter(os.environ.get("OPENVOICE_CKPT", "checkpoints/converter") + "/config.json",
                                   device=device)
    converter.load_ckpt(os.environ.get("OPENVOICE_CKPT", "checkpoints/converter") + "/checkpoint.pth")
    src_se = base.hps.speakers if hasattr(base, "hps") else None
    tgt_se = torch.load(profile.speaker_embedding_path) if profile.speaker_embedding_path.endswith(".pth") else None
    converter.convert(audio_src_path=tmp, src_se=src_se, tgt_se=tgt_se,
                      output_path=out_path, tau=knobs.get("style_weight", 0.7))
    if os.path.exists(tmp):
        os.remove(tmp)
    return SynthResult(out_path, _wav_seconds(out_path), "openvoice", knobs)


def _synth_xtts(cfg, profile, text, style, knobs, out_path) -> SynthResult:
    try:
        from TTS.api import TTS  # type: ignore
    except Exception as e:
        print(f"[synth] Coqui TTS unavailable ({e}); stub audio.")
        return _synth_stub(cfg, profile, text, style, knobs, out_path)
    ref = _pick_reference(profile, style, knobs.get("reference_pick", "best"))
    device = profile.meta.get("device", "cpu")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    tts.tts_to_file(text=text, speaker_wav=ref, language="en", file_path=out_path,
                    temperature=knobs.get("temperature", 0.65))
    return SynthResult(out_path, _wav_seconds(out_path), "xtts", knobs)


def _synth_stub(cfg, profile, text, style, knobs, out_path) -> SynthResult:
    """Render a placeholder tone whose LENGTH tracks the text, so the loop,
    evaluator and CLI all work end-to-end without a model. Not your voice —
    a stand-in until a backend is installed."""
    sr = cfg["audio"]["sample_rate"]
    words = max(1, len(text.split()))
    # emulate ~2.5 words/sec, nudged by the temperature knob
    wps = 2.5 * (0.9 + 0.2 * knobs.get("temperature", 0.65))
    seconds = words / wps
    n = int(seconds * sr)
    base_freq = 110.0 + 20.0 * knobs.get("style_weight", 0.7)  # pseudo pitch
    with wave.open(out_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        frames = bytearray()
        for i in range(n):
            env = 0.3 * math.sin(2 * math.pi * (i / sr) * (2.0 + 1.5 * ((i // (sr // 3)) % 3)))
            val = int(6000 * env * math.sin(2 * math.pi * base_freq * i / sr))
            frames += struct.pack("<h", max(-32767, min(32767, val)))
        w.writeframes(bytes(frames))
    return SynthResult(out_path, seconds, "stub", knobs)


def _wav_seconds(path: str) -> float:
    with wave.open(path, "rb") as w:
        return w.getnframes() / float(w.getframerate() or 1)
