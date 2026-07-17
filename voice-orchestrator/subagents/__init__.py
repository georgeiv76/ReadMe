"""Sub-agents that the orchestrator coordinates.

Each module is a focused, single-responsibility unit the orchestrator calls
in sequence or in a loop:

    recorder    capture clean, correctly-formatted audio locally
    ingest      validate + normalize the dataset, build a manifest
    cloner      build a voice profile (speaker embedding) from the dataset
    synthesizer turn text into speech using the voice profile
    evaluator   score an output; this is the "learn from mistakes" signal
    memory      persist what worked so future runs start smarter
"""
