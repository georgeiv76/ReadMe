# 🎙️ Voice Orchestrator

Type text → hear it read aloud in **your own voice** (your intonation, vowels,
tone). Built to narrate articles without you having to record each one. Video
comes later; a very good voice comes first.

It's an **orchestrator that coordinates sub-agents in a loop** and **learns
from its mistakes**: every synthesis is scored for how much it sounds like you
and how natural the pacing is; if it falls short, the loop adjusts its knobs
and retries, remembering what worked so the next run starts smarter.

```
record ──▶ ingest ──▶ build (voice profile) ──▶ say  ──▶  your_voice.wav
                                                  ▲          │
                                                  └── evaluate + adjust (loop)
```

## Sub-agents

| Sub-agent | Job |
|-----------|-----|
| `recorder`   | capture clean, correctly-formatted clips (local mic) |
| `ingest`     | validate the dataset, flag bad clips, report readiness |
| `cloner`     | build your reusable voice profile (tone color + style refs) |
| `synthesizer`| render text → audio in your voice |
| `evaluator`  | score voice-match + pacing (the learning signal) |
| `memory`     | remember what worked, per style, across runs |

## Quick start

### 0. Read the recording guide
`RECORDING_GUIDE.md` answers **how long, how much, which intonations, what
dataset** — the questions you asked. Short version:
- **~30 minutes** of clean audio (~4,300 words) for a very good voice.
- **3 intonation styles**: `neutral` (default), `emphatic`, `conversational`.
- WAV, mono, 48 kHz, quiet room, consistent mic distance.

### 1. Record (on your own machine — needs a microphone)
> This cloud container has no audio device, so recording is a local step.
```bash
pip install sounddevice soundfile numpy
python orchestrator.py record --style neutral
python orchestrator.py record --style emphatic
python orchestrator.py record --style conversational
```
`record` shows one script line at a time, saves each take, and rejects clips
that are too short, clipped, or noisy. It writes `data/raw/transcript.csv` for
you. (No mic handy? Use Audacity/your phone and drop WAVs into
`data/raw/<style>/` — see the guide.)

### 2. Validate the dataset
```bash
python orchestrator.py ingest
```
Reports total minutes per style, lists any problem clips, and tells you
whether you're at instant-clone or article-quality tier.

### 3. Build your voice profile
```bash
python orchestrator.py build
```

### 4. Say anything in your voice
```bash
python orchestrator.py say "Today I want to walk you through a subtle bug."
python synthesize.py --file my_article.txt --style neutral
```
Output lands in `data/output/*.wav`. Watch the loop pick knobs and converge:
```
attempt 1: sim=0.83 wps=2.6 knobs={'style_weight': 1.0, ...} ✓ passed
```
See what it has learned: `python orchestrator.py stats`.

## Local install (one command)

On your own machine (macOS/Linux), from this folder:
```bash
bash setup.sh
```
This creates a `.venv`, installs the **Coqui XTTS** backend + the Claude Desktop
MCP deps with validated version pins, and smoke-tests the imports. It then
prints your exact next steps. (Needs Python 3.10–3.12.)

> The pins matter: `transformers` is held at 4.57 because 5.x removes a symbol
> Coqui imports, `torchcodec` is required by torch ≥2.9, and the first real
> synthesis needs `COQUI_TOS_AGREED=1`. `setup.sh` handles all three.

## Use inside Claude Desktop (local MCP server)

`mcp_server.py` is a stdio MCP server (no network) exposing four tools:
`speak`, `voice_status`, `list_voice_styles`, `build_voice_profile`.

1. Run `bash setup.sh` (above).
2. Copy the `voice-orchestrator` block from `claude_desktop_config.example.json`
   into your Claude Desktop config, replacing `/ABSOLUTE/PATH/TO` and pointing
   `command` at `.venv/bin/python`. Config location:
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
3. Fully quit and reopen Claude Desktop — the `voice-orchestrator` tools appear.
4. Ask: *"Read this in my voice: …"* → it calls `speak`, saves a WAV to
   `data/output/`, and plays it locally (afplay/aplay/default player).

Recording still uses the CLI (`python orchestrator.py record`) because it needs
your microphone; everything after that works from Claude Desktop.

## Backends

The pipeline runs immediately with a **stub** backend (placeholder tone, zero
installs) so all logic is testable. For real audio in your voice, set
`backend.engine` in `config.yaml`:

- **`xtts`** (default) — Coqui XTTS-v2, strong few-shot clone; installed by
  `setup.sh`. First run downloads ~1.8 GB and requires accepting Coqui's
  non-commercial model license (`COQUI_TOS_AGREED=1`).
- **`openvoice`** — best control over intonation/emotion; separates tone color
  from prosody. Install from source: https://github.com/myshell-ai/OpenVoice
- **`stub`** — no model; for testing the pipeline.

Both real backends use PyTorch (GPU/Apple-Silicon MPS accelerate it; CPU works
but is slower). If XTTS errors on MPS, set `device: cpu` in `config.yaml`.

## Configuration
Everything is in `config.yaml`: audio format, backend, and the refinement loop
thresholds (`min_speaker_similarity`, pacing band, `max_attempts`, and the knob
grid it's allowed to sweep).

## A note on ethics
This is **your voice, recorded by you, for you.** A cloned voice is a
credential — keep the recordings and the profile private (they're gitignored),
and don't let anyone synthesize as you without your consent.
