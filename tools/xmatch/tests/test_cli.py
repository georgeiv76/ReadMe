"""Smoke tests for the `xmatch` CLI entry point."""

import json
import pathlib

from dedaub_xmatch.cli import main

EXAMPLES = pathlib.Path(__file__).resolve().parents[1] / "examples"
DEDAUB = str(EXAMPLES / "dedaub_warnings_example.json")
MYTHRIL = str(EXAMPLES / "mythril_json_example.json")


def test_cli_table_mode(capsys):
    rc = main(["--dedaub", DEDAUB, "--mythril", MYTHRIL, "--format", "table"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "CORROBORAT" in out
    assert "reentrancy" in out


def test_cli_json_mode_is_valid_and_ranked(capsys):
    rc = main(["--dedaub", DEDAUB, "--mythril", MYTHRIL, "--format", "json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["corroborated"] == 1
    assert payload["ran_sources"] == ["mythril"]
    # First warning is the corroborated one (tier-ordered).
    assert payload["warnings"][0]["verdict"] == "corroborated"
    assert payload["warnings"][0]["vuln_class"] == "reentrancy"


def test_cli_without_mythril_runs_no_sources(capsys):
    rc = main(["--dedaub", DEDAUB, "--format", "json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ran_sources"] == []
    assert payload["summary"]["unresolved"] == 3
