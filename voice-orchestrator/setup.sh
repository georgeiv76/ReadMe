#!/usr/bin/env bash
# One-command local setup for the Voice Orchestrator (macOS / Linux).
#
#   cd voice-orchestrator && bash setup.sh
#
# Creates a virtualenv, installs the Coqui XTTS backend + the Claude Desktop
# MCP dependencies, and smoke-tests the imports. The exact version pins below
# were validated by hand — a naive `pip install coqui-tts` breaks on
# transformers 5.x and missing torchcodec, so don't loosen them casually.
set -euo pipefail
cd "$(dirname "$0")"

PY="${PYTHON:-python3}"
VENV=".venv"

echo "▶ Python: $($PY --version)"
# coqui-tts supports CPython 3.10–3.12. 3.13+ is not supported yet.
$PY - <<'EOF'
import sys
if not (3, 10) <= sys.version_info[:2] <= (3, 12):
    raise SystemExit(f"Need Python 3.10–3.12; you have {sys.version.split()[0]}. "
                     "Install one (e.g. `brew install python@3.12`) and re-run "
                     "with PYTHON=python3.12 bash setup.sh")
EOF

echo "▶ Creating virtualenv at $VENV"
$PY -m venv "$VENV"
PIP="$VENV/bin/pip"
VPY="$VENV/bin/python"
"$PIP" install -q --upgrade pip

echo "▶ Installing PyTorch (CPU/MPS build from PyPI — gives Apple-Silicon GPU support)"
"$PIP" install -q torch torchaudio torchcodec

echo "▶ Installing Coqui XTTS backend (+ pinned transformers)"
# coqui-tts 0.27.x needs transformers>=4.57, but transformers 5.x removed a
# symbol it imports — pin to the 4.57 line.
"$PIP" install -q "coqui-tts==0.27.5" "transformers==4.57.1"

echo "▶ Installing Claude Desktop MCP server + recording deps"
"$PIP" install -q "mcp[cli]" sounddevice soundfile numpy pyyaml

echo "▶ (Optional) speaker-similarity evaluator"
"$PIP" install -q resemblyzer || echo "  · resemblyzer skipped (evaluator falls back to a proxy score)"

echo "▶ Smoke-testing imports"
"$VPY" - <<'EOF'
from TTS.api import TTS          # XTTS backend
import mcp                        # Claude Desktop server
import orchestrator               # our pipeline
print("✓ imports OK")
EOF

cat <<EOF

✅ Setup complete.

Next:
  1. Record your voice (needs a mic):
       $VPY orchestrator.py record --style neutral
       $VPY orchestrator.py record --style emphatic
       $VPY orchestrator.py record --style conversational
  2. Build your voice profile (first run downloads XTTS-v2, ~1.8 GB):
       COQUI_TOS_AGREED=1 $VPY orchestrator.py build
  3. Hear it:
       COQUI_TOS_AGREED=1 $VPY synthesize.py "Read this in my voice." --style neutral

Claude Desktop: point claude_desktop_config.json at
  command: $(pwd)/$VENV/bin/python
  args:    ["$(pwd)/mcp_server.py"]
  env:     { "VOICE_CONFIG": "$(pwd)/config.yaml", "COQUI_TOS_AGREED": "1" }
(see claude_desktop_config.example.json), then restart Claude Desktop.

Note: COQUI_TOS_AGREED=1 records your acceptance of Coqui's XTTS model license
(CPML, non-commercial). Only set it if you agree to those terms.
EOF
