"""Recorder sub-agent — capture clean, correctly-formatted voice clips.

Runs on YOUR machine (needs a microphone). This cloud container has no audio
device, so run it locally:  python orchestrator.py record --style neutral

It reads lines from recording_script.md, records one clip per line, validates
format/loudness/noise, and writes WAV + a transcript row automatically.

Depends on `sounddevice` and `soundfile` (see requirements.txt). If they are
missing it explains how to install them instead of crashing.
"""
from __future__ import annotations

import csv
import os
import wave
from dataclasses import dataclass

try:
    import numpy as np
    import sounddevice as sd
    import soundfile as sf
    _AUDIO_OK = True
except Exception:  # pragma: no cover - depends on local install
    _AUDIO_OK = False


@dataclass
class ClipCheck:
    ok: bool
    reason: str = ""


def _validate(samples, sr: int, cfg: dict) -> ClipCheck:
    """Reject clips that would poison the dataset."""
    a = cfg["audio"]
    dur = len(samples) / float(sr)
    if dur < a["min_clip_seconds"]:
        return ClipCheck(False, f"too short ({dur:.1f}s < {a['min_clip_seconds']}s)")
    if dur > a["max_clip_seconds"] + 3:
        return ClipCheck(False, f"too long ({dur:.1f}s)")
    peak = float(np.max(np.abs(samples))) if len(samples) else 0.0
    if peak >= a["max_peak"]:
        return ClipCheck(False, f"clipping (peak {peak:.2f}) — move back / lower gain")
    if peak < 0.02:
        return ClipCheck(False, "almost silent — is the mic on / selected?")
    # crude noise-floor estimate from the quietest 10% of frames
    frame = max(1, sr // 20)
    energies = [
        float(np.sqrt(np.mean(samples[i : i + frame] ** 2)) + 1e-9)
        for i in range(0, len(samples) - frame, frame)
    ]
    if energies:
        energies.sort()
        floor = energies[max(0, len(energies) // 10)]
        floor_db = 20.0 * np.log10(floor)
        if floor_db > a["max_noise_floor_db"]:
            return ClipCheck(False, f"too noisy (floor {floor_db:.0f} dB) — quieter room")
    return ClipCheck(True)


def record_session(cfg: dict, style: str, lines: list[tuple[int, str]]) -> int:
    """Record one clip per (index, text) line for the given style.

    Returns the number of clips accepted. Re-recording a fluffed take is just
    pressing Enter again — bad takes are never written.
    """
    if not _AUDIO_OK:
        print(
            "Audio libraries not available in this environment.\n"
            "On your local machine:  pip install sounddevice soundfile numpy\n"
            "(and a working microphone). This cloud container has no mic."
        )
        return 0

    sr = cfg["audio"]["sample_rate"]
    out_dir = os.path.join(cfg["paths"]["raw_dir"], style)
    os.makedirs(out_dir, exist_ok=True)
    transcript = cfg["paths"]["transcript"]
    os.makedirs(os.path.dirname(transcript), exist_ok=True)

    accepted = 0
    rows = []
    print(f"\n=== Recording style: {style} ===")
    print("Press Enter to start each clip, Enter again to stop. Ctrl-C to quit.\n")
    for idx, text in lines:
        while True:
            input(f"[{idx:03d}] READY> {text}\n   Enter to record... ")
            print("   ● recording — press Enter to stop", end="", flush=True)
            rec = sd.rec(int(cfg["audio"]["max_clip_seconds"] * sr * 1.5),
                         samplerate=sr, channels=1, dtype="float32")
            input()
            sd.stop()
            samples = rec[: sd.get_stream().write_available or len(rec)].flatten()
            samples = np.trim_zeros(samples) if len(samples) else samples
            check = _validate(samples, sr, cfg)
            if not check.ok:
                print(f"   ✗ rejected: {check.reason}. Let's redo it.\n")
                continue
            path = os.path.join(out_dir, f"{idx:03d}.wav")
            sf.write(path, samples, sr, subtype="PCM_16")
            rows.append({"filepath": os.path.relpath(path, cfg["paths"]["raw_dir"]),
                         "style": style, "text": text})
            accepted += 1
            print(f"   ✓ saved {path}\n")
            break

    _append_transcript(transcript, rows)
    print(f"Done: {accepted} clips for '{style}'.")
    return accepted


def _append_transcript(path: str, rows: list[dict]) -> None:
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["filepath", "style", "text"])
        if not exists:
            w.writeheader()
        for r in rows:
            w.writerow(r)


def probe_wav(path: str) -> dict:
    """Read format facts from a WAV without extra deps (used by ingest)."""
    with wave.open(path, "rb") as w:
        frames = w.getnframes()
        sr = w.getframerate()
        return {
            "sample_rate": sr,
            "channels": w.getnchannels(),
            "sampwidth_bits": w.getsampwidth() * 8,
            "seconds": frames / float(sr) if sr else 0.0,
        }
