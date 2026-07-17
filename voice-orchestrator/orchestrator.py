#!/usr/bin/env python3
"""Voice Orchestrator — coordinate the sub-agents to turn text into speech in
your own voice, improving with each attempt.

Pipeline
    record   -> ingest -> build (profile) -> say (text -> your voice)

The `say` command runs the refinement LOOP: synthesize -> evaluate -> if it
doesn't sound enough like you (or the pacing is off), adjust the knobs and try
again, seeded by what has worked before (memory). That loop is the "learns
from its mistakes" part.

Usage
    python orchestrator.py record --style neutral      # local machine, needs mic
    python orchestrator.py ingest                       # validate the dataset
    python orchestrator.py build                         # build the voice profile
    python orchestrator.py say "Text to read aloud"      # -> data/output/*.wav
    python orchestrator.py say --file article.txt --style neutral
    python orchestrator.py stats                          # what it has learned

All behavior comes from config.yaml.
"""
from __future__ import annotations

import argparse
import itertools
import os
import re
import sys

from subagents import cloner, evaluator, ingest, memory, recorder, synthesizer


# ---- config loading (tiny YAML subset, no third-party dep required) --------
def load_config(path: str = None) -> dict:
    path = path or os.path.join(os.path.dirname(__file__), "config.yaml")
    try:
        import yaml  # if PyYAML is present, use it
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        pass
    return _mini_yaml(path)


def _mini_yaml(path: str) -> dict:
    """Minimal YAML good enough for this file's structure (nested maps,
    scalars, and [a, b] inline lists). Keeps the tool runnable with zero deps."""
    root: dict = {}
    stack = [(-1, root)]
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.split("#", 1)[0].rstrip()
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip())
            key, _, val = line.strip().partition(":")
            val = val.strip()
            while stack and indent <= stack[-1][0]:
                stack.pop()
            parent = stack[-1][1]
            if val == "":
                node: dict = {}
                parent[key] = node
                stack.append((indent, node))
            else:
                parent[key] = _coerce(val)
    return root


def _coerce(v: str):
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [_coerce(x.strip()) for x in inner.split(",")] if inner else []
    low = v.lower()
    if low in ("true", "false"):
        return low == "true"
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v.strip('"').strip("'")


# ---- commands --------------------------------------------------------------
def cmd_record(cfg, args):
    lines = _script_lines(args.style)
    if not lines:
        print(f"No lines found for style '{args.style}' in recording_script.md")
        return 1
    recorder.record_session(cfg, args.style, lines)
    return 0


def cmd_ingest(cfg, _args):
    m = ingest.build_manifest(cfg)
    print(m.summary())
    tier, notes = ingest.readiness(m, cfg)
    print(f"\nReadiness: {tier}")
    for n in notes:
        print(f"  - {n}")
    return 0


def cmd_build(cfg, _args):
    m = ingest.build_manifest(cfg)
    if not m.clips:
        print("No clips to build from. Record some audio first (see RECORDING_GUIDE.md).")
        return 1
    tier, notes = ingest.readiness(m, cfg)
    print(f"Building voice profile from {len(m.clips)} clips "
          f"({m.total_seconds/60:.1f} min) — {tier}")
    profile = cloner.build_profile(cfg, m.clips)
    path = profile.save(cfg["paths"]["profile_dir"])
    print(f"Saved profile ({profile.engine}) -> {path}")
    if profile.engine == "stub":
        print("Note: no model backend installed, so this is a STUB profile. "
              "Install OpenVoice or Coqui XTTS (see README) to clone for real.")
    return 0


def cmd_say(cfg, args):
    profile_dir = cfg["paths"]["profile_dir"]
    if not os.path.exists(os.path.join(profile_dir, "profile.json")):
        print("No voice profile yet. Run:  python orchestrator.py build")
        return 1
    profile = cloner.VoiceProfile.load(profile_dir)
    text = _read_text(args)
    if not text:
        print("Nothing to say. Pass text or --file.")
        return 1
    style = args.style or cfg["backend"]["default_style"]
    out = _refine_loop(cfg, profile, text, style, args.out)
    print(f"\n♪ {out}")
    return 0


def cmd_stats(cfg, _args):
    mem = memory.Memory(cfg["paths"]["memory_db"])
    st = mem.stats()
    if not st:
        print("No attempts recorded yet. Run a `say` first.")
        return 0
    print("What the orchestrator has learned (per style):")
    for style, s in sorted(st.items()):
        rate = 100 * s["passes"] / s["attempts"] if s["attempts"] else 0
        best = mem.best_knobs_for(style)
        print(f"  {style:15s} {s['passes']}/{s['attempts']} passed ({rate:.0f}%) "
              f"best={best}")
    return 0


# ---- the refinement loop (synthesize -> evaluate -> adapt) -----------------
def _refine_loop(cfg, profile, text, style, out_path=None):
    r = cfg["refine"]
    mem = memory.Memory(cfg["paths"]["memory_db"])
    out_path = out_path or os.path.join(
        cfg["paths"]["output_dir"], _slug(text) + ".wav")

    candidates = _knob_candidates(cfg, mem, style)
    best_result, best_score = None, None

    for attempt, knobs in enumerate(candidates, 1):
        if not r.get("enabled", True) and attempt > 1:
            break
        if attempt > r["max_attempts"]:
            break
        tmp = out_path if attempt == 1 else out_path.replace(".wav", f".try{attempt}.wav")
        result = synthesizer.synthesize(cfg, profile, text, style, knobs, tmp)
        score = evaluator.evaluate(cfg, profile, result, text, style)
        mem.record(style, knobs, score.as_dict())
        flag = "✓ passed" if score.passed else "· " + "; ".join(score.reasons)
        print(f"  attempt {attempt}: sim={score.speaker_similarity:.2f} "
              f"wps={score.wps:.2f} knobs={knobs} {flag}")

        if best_score is None or score.speaker_similarity > best_score.speaker_similarity:
            best_result, best_score = result, score

        if score.passed:
            if result.audio_path != out_path:
                os.replace(result.audio_path, out_path)
                best_result.audio_path = out_path
            break

    # keep the best attempt if none fully passed
    if best_result and best_result.audio_path != out_path and os.path.exists(best_result.audio_path):
        os.replace(best_result.audio_path, out_path)
        best_result.audio_path = out_path

    mem.save()
    if best_score and not best_score.passed:
        print("  (kept best attempt; still below target — more/cleaner data "
              "usually fixes this)")
    _cleanup_tries(out_path)
    return out_path


def _knob_candidates(cfg, mem, style):
    """Order the knob sets to try: memory's best first, then a sensible sweep,
    skipping combinations already known to fail for this style."""
    t = cfg["refine"]["tunable"]
    grid = [dict(style_weight=sw, temperature=tm, reference_pick=rp)
            for sw, tm, rp in itertools.product(
                t["style_weight"], t["temperature"], t["reference_pick"])]
    failed = mem.failed_knobs_for(style)
    grid = [g for g in grid if g not in failed] or grid
    best = mem.best_knobs_for(style)
    if best:
        grid = [best] + [g for g in grid if g != best]
    return grid


# ---- helpers ---------------------------------------------------------------
def _script_lines(style: str):
    """Pull the numbered lines for a style section from recording_script.md."""
    path = os.path.join(os.path.dirname(__file__), "recording_script.md")
    if not os.path.exists(path):
        return []
    section = {"neutral": "NEUTRAL", "emphatic": "EMPHATIC",
               "conversational": "CONVERSATIONAL", "domain": "DOMAIN"}.get(
        style.lower(), style.upper())
    lines, capturing = [], False
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("## "):
                capturing = section in line.upper()
                continue
            if capturing:
                m = re.match(r"\s*(\d+)\.\s+(.*\S)", line)
                if m:
                    lines.append((int(m.group(1)), m.group(2)))
    return lines


def _read_text(args) -> str:
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            return f.read().strip()
    return " ".join(args.text).strip()


def _slug(text: str, n: int = 40) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return (s[:n] or "clip")


def _cleanup_tries(out_path: str):
    d = os.path.dirname(out_path) or "."
    base = os.path.basename(out_path).replace(".wav", "")
    for name in os.listdir(d):
        if name.startswith(base + ".try") and name.endswith(".wav"):
            try:
                os.remove(os.path.join(d, name))
            except OSError:
                pass


def main(argv=None):
    p = argparse.ArgumentParser(description="Voice Orchestrator")
    p.add_argument("--config", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("record", help="record clips (local machine, needs mic)")
    pr.add_argument("--style", default="neutral")

    sub.add_parser("ingest", help="validate + summarize the dataset")
    sub.add_parser("build", help="build the voice profile from recordings")

    ps = sub.add_parser("say", help="synthesize text in your voice")
    ps.add_argument("text", nargs="*", help="text to read")
    ps.add_argument("--file", help="read text from a file (e.g. your article)")
    ps.add_argument("--style", default=None, help="neutral | emphatic | conversational")
    ps.add_argument("--out", default=None, help="output WAV path")

    sub.add_parser("stats", help="show what the orchestrator has learned")

    args = p.parse_args(argv)
    cfg = load_config(args.config)
    # resolve relative paths against this file's directory
    here = os.path.dirname(os.path.abspath(__file__))
    for k, v in cfg.get("paths", {}).items():
        if isinstance(v, str) and not os.path.isabs(v):
            cfg["paths"][k] = os.path.join(here, v)

    return {
        "record": cmd_record, "ingest": cmd_ingest, "build": cmd_build,
        "say": cmd_say, "stats": cmd_stats,
    }[args.cmd](cfg, args)


if __name__ == "__main__":
    sys.exit(main())
