#!/usr/bin/env python3
"""Local MCP server — expose the Voice Orchestrator to Claude Desktop.

Runs on YOUR machine over stdio (no network). Once registered in Claude
Desktop, you can say things like "read this in my voice: ..." and Claude will
call the `speak` tool, which synthesizes the text in your cloned voice, plays
it locally, and returns the WAV path.

Tools
    speak               text -> your voice (runs the refine loop), plays it
    voice_status        is a profile built? which backend? dataset readiness
    list_voice_styles   which intonation styles are available
    build_voice_profile (re)build the profile from your recordings

Register it: see claude_desktop_config.example.json and the README section
"Use inside Claude Desktop". Recording still happens with the CLI
(`python orchestrator.py record`) because it needs your microphone.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys

# import the orchestrator package (this file lives alongside it)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import orchestrator  # noqa: E402
from subagents import cloner, ingest  # noqa: E402

try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover
    sys.stderr.write(
        "The 'mcp' package is required. Install it on your machine:\n"
        "    pip install 'mcp[cli]'\n")
    raise

mcp = FastMCP("voice-orchestrator")

# config path can be overridden so Claude Desktop can point at a specific setup
_CONFIG = os.environ.get("VOICE_CONFIG") or None


def _cfg() -> dict:
    return orchestrator.resolved_config(_CONFIG)


def _profile_exists(cfg: dict) -> bool:
    return os.path.exists(os.path.join(cfg["paths"]["profile_dir"], "profile.json"))


def _play(path: str) -> str:
    """Play a WAV with whatever the OS provides. Never fatal."""
    if sys.platform == "darwin":
        cmd = ["afplay", path]
    elif sys.platform.startswith("win"):
        # non-blocking default player
        try:
            os.startfile(path)  # type: ignore[attr-defined]
            return "playing (default player)"
        except Exception as e:
            return f"could not autoplay ({e})"
    else:
        player = next((p for p in ("paplay", "aplay", "ffplay") if shutil.which(p)), None)
        if not player:
            return "no audio player found (install pulseaudio/alsa/ffmpeg to hear it)"
        cmd = [player, "-nodisp", "-autoexit", path] if player == "ffplay" else [player, path]
    if not shutil.which(cmd[0]):
        return f"'{cmd[0]}' not installed; WAV saved but not played"
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "playing"
    except Exception as e:
        return f"could not play ({e})"


@mcp.tool(
    description="Read text aloud in the user's own cloned voice. Runs the "
    "quality-refinement loop, saves a WAV, and (by default) plays it on the "
    "local machine. Use this whenever the user wants to hear text in their "
    "voice or narrate an article. Requires a built voice profile first.",
    annotations={"readOnlyHint": False, "destructiveHint": False,
                 "idempotentHint": False, "openWorldHint": False},
)
def speak(text: str, style: str = "neutral", play: bool = True) -> dict:
    """Synthesize `text` in the user's voice.

    Args:
        text: What to read aloud.
        style: Intonation style — neutral | emphatic | conversational (or any
            style folder the user recorded). Defaults to neutral.
        play: Play the audio locally after generating it. Default true.
    """
    cfg = _cfg()
    if not text or not text.strip():
        return {"ok": False, "error": "No text provided."}
    if not _profile_exists(cfg):
        return {"ok": False,
                "error": "No voice profile yet. Record with "
                         "`python orchestrator.py record --style neutral`, then "
                         "run `build_voice_profile` (or `python orchestrator.py build`)."}
    profile = cloner.VoiceProfile.load(cfg["paths"]["profile_dir"])
    out_path = orchestrator._refine_loop(cfg, profile, text.strip(), style)
    played = _play(out_path) if play else "skipped"
    note = None
    if profile.engine == "stub":
        note = ("Profile backend is STUB (no model installed) — this is a "
                "placeholder tone, not your real voice. Install OpenVoice or "
                "Coqui XTTS and rebuild for real audio.")
    return {"ok": True, "audio_path": out_path, "style": style,
            "engine": profile.engine, "playback": played, "note": note}


@mcp.tool(
    description="Report whether a voice profile is built, which backend engine "
    "it uses, and how much/what kind of voice data has been recorded.",
    annotations={"readOnlyHint": True, "openWorldHint": False},
)
def voice_status() -> dict:
    """Health check for the voice setup."""
    cfg = _cfg()
    m = ingest.build_manifest(cfg)
    tier, notes = ingest.readiness(m, cfg)
    engine = "none"
    if _profile_exists(cfg):
        engine = cloner.VoiceProfile.load(cfg["paths"]["profile_dir"]).engine
    return {
        "profile_built": _profile_exists(cfg),
        "backend_engine": engine,
        "configured_backend": cfg["backend"]["engine"],
        "dataset_minutes": round(m.total_seconds / 60, 1),
        "per_style_minutes": {k: round(v / 60, 1) for k, v in m.per_style_seconds.items()},
        "readiness": tier,
        "notes": notes + m.problems[:5],
    }


@mcp.tool(
    description="List the intonation styles available for synthesis, based on "
    "the voice folders the user has recorded.",
    annotations={"readOnlyHint": True, "openWorldHint": False},
)
def list_voice_styles() -> dict:
    """Available styles + the default."""
    cfg = _cfg()
    styles = []
    if _profile_exists(cfg):
        styles = list(cloner.VoiceProfile.load(cfg["paths"]["profile_dir"]).style_refs.keys())
    if not styles:
        m = ingest.build_manifest(cfg)
        styles = sorted(m.per_style_seconds.keys())
    return {"styles": styles or ["(none recorded yet)"],
            "default": cfg["backend"]["default_style"]}


@mcp.tool(
    description="Build or rebuild the voice profile from the user's recorded "
    "clips. Run this after recording new audio. Does not need the microphone.",
    annotations={"readOnlyHint": False, "destructiveHint": False,
                 "idempotentHint": True, "openWorldHint": False},
)
def build_voice_profile() -> dict:
    """Ingest recordings and build the reusable voice profile."""
    cfg = _cfg()
    m = ingest.build_manifest(cfg)
    if not m.clips:
        return {"ok": False,
                "error": "No recordings found. Record first with "
                         "`python orchestrator.py record --style neutral`."}
    profile = cloner.build_profile(cfg, m.clips)
    path = profile.save(cfg["paths"]["profile_dir"])
    tier, _ = ingest.readiness(m, cfg)
    return {"ok": True, "profile_path": path, "engine": profile.engine,
            "clips": len(m.clips), "minutes": round(m.total_seconds / 60, 1),
            "readiness": tier}


if __name__ == "__main__":
    mcp.run()  # stdio transport
