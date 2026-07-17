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

## Choosing a backend (the real cloning model)

The pipeline runs immediately with a **stub** backend (a placeholder tone) so
you can test all the logic with zero installs. For real audio in your voice,
install one backend and set `backend.engine` in `config.yaml`:

- **`openvoice`** — best control over intonation/emotion; separates your tone
  color from prosody. https://github.com/myshell-ai/OpenVoice
- **`xtts`** — Coqui XTTS-v2, strong few-shot clone. `pip install TTS`

Both need PyTorch and are much faster on a GPU. Because they're multi-GB, run
build/say on your own machine or a GPU box — not in this ephemeral container.

## Configuration
Everything is in `config.yaml`: audio format, backend, and the refinement loop
thresholds (`min_speaker_similarity`, pacing band, `max_attempts`, and the knob
grid it's allowed to sweep).

## A note on ethics
This is **your voice, recorded by you, for you.** A cloned voice is a
credential — keep the recordings and the profile private (they're gitignored),
and don't let anyone synthesize as you without your consent.
