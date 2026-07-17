"""Memory sub-agent — persistent learning across runs.

Records every synthesis attempt (style, knobs, score) so the orchestrator
can (a) start each new synthesis from the knob settings that have worked best
for that style, and (b) avoid repeating settings that already failed. This is
what "learns from its mistakes" means concretely: past outcomes bias future
choices instead of every run starting from scratch.
"""
from __future__ import annotations

import json
import os
from collections import defaultdict


class Memory:
    def __init__(self, path: str):
        self.path = path
        self.attempts: list[dict] = []
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    self.attempts = json.load(f).get("attempts", [])
            except Exception:
                self.attempts = []

    def record(self, style: str, knobs: dict, score: dict) -> None:
        self.attempts.append({"style": style, "knobs": knobs, "score": score})

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"attempts": self.attempts}, f, indent=2)

    def best_knobs_for(self, style: str):
        """Return the knob set with the highest passing similarity for a
        style, or None if we've never succeeded there yet."""
        best, best_sim = None, -1.0
        for a in self.attempts:
            if a["style"] != style or not a["score"].get("passed"):
                continue
            sim = a["score"].get("speaker_similarity", 0.0)
            if sim > best_sim:
                best, best_sim = a["knobs"], sim
        return best

    def failed_knobs_for(self, style: str) -> list[dict]:
        return [a["knobs"] for a in self.attempts
                if a["style"] == style and not a["score"].get("passed")]

    def stats(self) -> dict:
        by_style = defaultdict(lambda: {"attempts": 0, "passes": 0})
        for a in self.attempts:
            s = by_style[a["style"]]
            s["attempts"] += 1
            s["passes"] += 1 if a["score"].get("passed") else 0
        return dict(by_style)
