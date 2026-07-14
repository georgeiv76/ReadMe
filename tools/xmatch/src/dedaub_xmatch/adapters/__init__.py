"""Source adapters: map each tool's native output onto NormalizedFinding.

Phase 1 ships:
* ``dedaub``  — ingest Security Suite / Watchdog warnings (the input to adjudicate)
* ``mythril`` — the independent, bytecode-native corroborator

Later phases add ``slither`` / ``wake`` (source-only) and ``fuzzer`` (dynamic).
"""
