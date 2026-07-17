"""Ingest sub-agent — validate + normalize the recorded dataset.

Turns a folder of WAVs into a clean, verified manifest the cloner can trust.
Flags anything that would hurt clone quality (wrong format, silent, too short)
so you fix it before spending compute.
"""
from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field

from .recorder import probe_wav


@dataclass
class Manifest:
    clips: list[dict] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    per_style_seconds: dict[str, float] = field(default_factory=dict)

    @property
    def total_seconds(self) -> float:
        return sum(self.per_style_seconds.values())

    def summary(self) -> str:
        lines = [f"  {s:16s} {sec/60:5.1f} min" for s, sec in
                 sorted(self.per_style_seconds.items())]
        head = f"{len(self.clips)} clips · {self.total_seconds/60:.1f} min total"
        tail = ("\nProblems:\n  " + "\n  ".join(self.problems)) if self.problems else ""
        return head + "\n" + "\n".join(lines) + tail


def build_manifest(cfg: dict) -> Manifest:
    raw = cfg["paths"]["raw_dir"]
    tpath = cfg["paths"]["transcript"]
    a = cfg["audio"]
    m = Manifest()

    transcripts: dict[str, str] = {}
    if os.path.exists(tpath):
        with open(tpath, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                transcripts[os.path.normpath(row["filepath"])] = row["text"]
    else:
        m.problems.append(f"no transcript.csv at {tpath} (ok for instant clone, "
                          "required for fine-tune tier)")

    if not os.path.isdir(raw):
        m.problems.append(f"raw dir missing: {raw} — record something first")
        return m

    for style in sorted(os.listdir(raw)):
        sdir = os.path.join(raw, style)
        if not os.path.isdir(sdir):
            continue
        for name in sorted(os.listdir(sdir)):
            if not name.lower().endswith(".wav"):
                continue
            path = os.path.join(sdir, name)
            rel = os.path.normpath(os.path.relpath(path, raw))
            try:
                info = probe_wav(path)
            except Exception as e:
                m.problems.append(f"{rel}: unreadable ({e})")
                continue
            issues = []
            if info["channels"] != a["channels"]:
                issues.append(f"{info['channels']}ch (want {a['channels']})")
            if info["sample_rate"] != a["sample_rate"]:
                issues.append(f"{info['sample_rate']}Hz (want {a['sample_rate']})")
            if info["seconds"] < a["min_clip_seconds"]:
                issues.append(f"{info['seconds']:.1f}s too short")
            if issues:
                m.problems.append(f"{rel}: " + ", ".join(issues))
            m.per_style_seconds[style] = m.per_style_seconds.get(style, 0.0) + info["seconds"]
            m.clips.append({
                "path": path,
                "rel": rel,
                "style": style,
                "seconds": info["seconds"],
                "text": transcripts.get(rel, ""),
            })
    return m


def readiness(m: Manifest, cfg: dict) -> tuple[str, list[str]]:
    """Judge whether the dataset is good enough, and say what's missing."""
    notes = []
    total_min = m.total_seconds / 60
    if total_min >= 20:
        tier = "recommended (article-quality clone)"
    elif total_min >= 3:
        tier = "instant clone only (add more for article quality)"
        notes.append(f"only {total_min:.1f} min — aim for ~30 for a very good voice")
    else:
        tier = "insufficient"
        notes.append(f"need at least ~3 min; have {total_min:.1f} min")
    if "neutral" not in m.per_style_seconds:
        notes.append("no 'neutral' clips — that's the default narration voice")
    return tier, notes
