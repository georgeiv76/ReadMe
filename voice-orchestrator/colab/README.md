# Colab fine-tune — train the model ON your voice

`Train_My_Voice_XTTS_Finetune.ipynb` is the maximum-fidelity path: instead of
zero-shot imitation from a few seconds of audio, it **fine-tunes XTTS-v2 on a
guided dataset of your voice** using Google Colab's free T4 GPU. This is the
step that closes the gap to the commercial tools.

## How to run it

1. Go to [colab.research.google.com](https://colab.research.google.com) →
   **File → Upload notebook** → upload the `.ipynb` from this folder.
   (Or **File → Open notebook → GitHub** and paste this repo's URL if public.)
2. **Runtime → Change runtime type → T4 GPU → Save** — do this first.
3. Run the cells top to bottom. The notebook walks you through:
   - **Phase 1** — guided recording: it shows you texts block by block
     (calm / emphatic / conversational / free speech) and records you through
     the browser mic (~35 min of your time).
   - **Phase 2** — Whisper transcribes + segments your recordings into a
     training dataset.
   - **Phase 3** — fine-tunes XTTS-v2 on your voice (~1–2 h on the T4).
   - **Phase 4** — evaluates fine-tuned vs base model with similarity scores.
   - **Phase 5** — paste an article → WAV narration in your voice.
4. Everything persists to your Google Drive (`MyDrive/my_voice_clone/`).
   If Colab disconnects: reopen, re-run cells 1–3, continue — recordings are
   never lost and training resumes from the newest checkpoint.

## Wiring the result into Claude Desktop

Download the `finetuned/` folder from Drive (model.pth + config.json +
vocab.json), then in `voice-orchestrator/config.yaml`:

```yaml
backend:
  engine: xtts
  finetuned_dir: /path/to/finetuned
```

Restart Claude Desktop — the `speak` tool now uses your trained voice.

## Honest expectations

- ~20–25 min of clean recordings + 10 epochs ≈ a voice most listeners will
  take for you. More/cleaner data and a couple more epoch rounds sharpen it.
- Free Colab can disconnect (idle ~90 min, session caps). The notebook is
  built to resume; keep the tab open during training.
- XTTS-v2 weights are **CPML-licensed (non-commercial)**. Personal article
  narration is fine; commercial video needs a differently-licensed model.
- Your recordings and the trained model can say *anything* in your voice —
  keep them private, share with no one.
