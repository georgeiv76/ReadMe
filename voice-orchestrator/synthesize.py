#!/usr/bin/env python3
"""Thin shortcut so the everyday action is one word:

    python synthesize.py "Type anything and hear it in your voice."
    python synthesize.py --file my_article.txt --style neutral

It just calls the orchestrator's `say` command.
"""
import sys
from orchestrator import main

if __name__ == "__main__":
    argv = ["say"] + sys.argv[1:]
    sys.exit(main(argv))
