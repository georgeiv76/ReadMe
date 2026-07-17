# Voice Dataset — What to Record

This is the exact dataset the orchestrator needs to replicate your voice
(intonation, vowel pronunciation, tone). Read this once, then use
`recording_script.md` as the text to read.

---

## 1. How long / how much do I read?

| Tier | Clean audio | ≈ words to read | Result |
|------|-------------|-----------------|--------|
| **Instant clone** (zero-shot) | 1–3 min | ~300–500 | Recognizably you, some artifacts |
| **Recommended** (article narration) | **20–30 min** | **~4,000–4,500** | Very good — the target for this project |
| **Studio** (fine-tune) | 45–60 min | ~7,000+ | Best; hard to tell from real |

**Target: ~30 minutes of clean speech**, which is roughly the length of
`recording_script.md` read at a natural pace (~150 words/min). Do it in
short takes — you do **not** record 30 minutes in one go.

## 2. Which intonations? (the 3 styles)

Record the script **three times' worth of material**, one folder per style.
The script is already split into these sections:

1. **`neutral`** — calm, even narration. This is the default voice for
   reading articles. ~60% of the data.
2. **`emphatic`** — engaged, persuasive, energy on key words. Used for
   hooks, headlines, important points. ~25%.
3. **`conversational`** — questions, rising intonation, a lighter tone.
   Keeps long articles from sounding flat. ~15%.

You can add a 4th later (e.g. `calm-slow` for intros) — the pipeline reads
whatever style folders exist.

## 3. Recording format (important — get this right)

- **Format:** WAV (uncompressed). Not MP3.
- **Channels:** Mono.
- **Sample rate:** 48000 Hz (48 kHz). 44.1 kHz is also fine.
- **Bit depth:** 16-bit minimum (24-bit better).
- **Clip length:** 5–15 seconds each. One sentence or two per clip.
- **Loudness:** normal speaking volume, avoid clipping (no red peaks).

The included `record.py` produces exactly this format automatically and
tells you if a clip is too short, clipped, or too noisy.

## 4. Recording environment

- Quiet room, soft furnishings (curtains/carpet) to kill echo. A closet
  full of clothes is a surprisingly good booth.
- **Consistent mic distance** (~15–20 cm) and consistent volume across all
  clips — this matters more than an expensive mic.
- Use a pop filter or angle the mic slightly off-axis to avoid "p"/"b" pops.
- Turn off fans, AC, phone notifications. Record when the street is quiet.
- Same mic, same room, same time of day for the whole set if you can.

## 5. Delivery / how to read

- Read **as you naturally would to a listener**, not robotically.
- Stay in character for the whole section (all `neutral` clips sound
  neutral, etc.).
- If you fluff a line, pause and re-read it — the ingest step lets you drop
  bad takes.
- Include the **domain-vocabulary block** at the end of the script
  (reentrancy, oracle, Dedaub, protocol names) so your work vocabulary is
  pronounced the way *you* say it.

## 6. What the final dataset looks like on disk

```
voice-orchestrator/data/raw/
  neutral/
    001.wav   002.wav   ...
  emphatic/
    001.wav   ...
  conversational/
    001.wav   ...
  transcript.csv          # filepath,style,text  (one row per clip)
```

`transcript.csv` maps each clip to the exact words you spoke. The recorder
can auto-fill it from the script, or you edit it after. Transcripts are
required for the high-quality (fine-tune) tier and optional for instant
cloning.

## 7. Consent note

This dataset is **your own voice, recorded by you, for your own use.**
Keep it that way — a cloned voice is a credential. Don't hand the model or
the samples to anyone you wouldn't hand a signed blank cheque.
