# dedaub-xmatch — Cross-Matching Confidence Engine (Phase 1)

Phase 1 of the system described in
[`docs/reducing-security-suite-false-positives.md`](../../docs/reducing-security-suite-false-positives.md).

It reduces Dedaub Security Suite false positives by **corroborating each warning
against an independent, bytecode-native analyzer (Mythril)** and assigning a
verdict tier with a calibrated score.

## Why this works

Empirically, inter-tool agreement on smart-contract vulnerabilities is very low
and single-tool precision is often 1–10%. That makes *agreement a strong
positive signal* (fusion approaches lift reentrancy precision from ~0.5% to
~73–84%), while *silence is weak negative evidence* (tools miss ~80% of real
bugs). The engine encodes exactly that asymmetry.

## Verdict tiers

| Tier | Meaning | Action |
|---|---|---|
| `CONFIRMED` | A dynamic PoC reproduces the issue (Phase 4; `FUZZER` source) | Escalate — operationally 100% |
| `CORROBORATED` | ≥1 independent-technique tool agrees on `(address, selector, class)` | Review first |
| `UNRESOLVED` | Default; ranked by prior/score | Status-quo triage queue |
| `LIKELY_FP` | A high-precision FP heuristic fired (Phase 2; dead code, proven guard) | Deprioritize — never deleted |

## Design principles baked into the scorer

- **Asymmetry** — independent agreement moves a warning up strongly; a tool
  running but not flagging moves it down only weakly.
- **Lineage awareness** — only sources whose technique is uncorrelated with
  Dedaub's Datalog value-flow count as independent (Mythril/Slither/Wake/fuzzer;
  open-source MadMax/Ethainter clients would *not*).
- **Nothing is deleted** — `LIKELY_FP` is a re-rankable state, preserving the
  Suite's deliberate high-completeness operating point.
- **Selector-granularity matching** — the cross-tool join key is
  `(chain, address, 4-byte selector, vuln_class)`, falling back to contract
  granularity when a selector cannot be recovered.

## Layout

```
src/dedaub_xmatch/
  models.py            canonical NormalizedFinding / Verdict / AdjudicatedWarning
  taxonomy.py          SWC ↔ OWASP-SC ↔ DASP ↔ tool-detector pivot + reverse lookup
  crossmatch.py        asymmetric log-odds scorer + verdict tiering
  pipeline.py          normalize → cross-match → verdicts
  cli.py               `xmatch` command
  adapters/
    dedaub.py          Watchdog/srcwarnings warnings → NormalizedFinding (input)
    mythril.py         Mythril -o json / jsonv2 → NormalizedFinding (corroborator)
examples/              realistic Mythril + Dedaub fixtures (also used by tests)
tests/                 33 tests; core + adapters + pipeline
```

## Usage

```bash
# From tools/xmatch/. Core + tests need no third-party deps.
python -m pytest                       # run the suite

# Adjudicate real outputs (files or - for stdin):
xmatch --dedaub warnings.json --mythril myth.json --format table
xmatch --dedaub warnings.json --format json     # baseline: no corroboration

# Produce the Mythril input for a deployed contract (needs `pip install mythril`
# and an RPC endpoint):
myth analyze -a 0xADDRESS --rpc https://... -o json > myth.json
```

Example output:

```
Summary: confirmed=0  corroborated=1  unresolved=2  likely_fp=0   (sources run: mythril)
[CORROBORAT]  score=0.566  reentrancy               0x2e1a7d4d  0x00000000…
    Independent agreement from mythril.  [agree: mythril]
[UNRESOLVED]  score=0.285  accessible_selfdestruct  0x9cb8a26a  0x00000000…
[UNRESOLVED]  score=0.038  access_control           0x1e2e3e4e  0x00000000…
```

## Extending (later phases)

- **Slither/Wake** (source-only): add adapters that emit `Source.SLITHER/WAKE`
  findings; append them to the pool and to `ran_sources`. The scorer is unchanged.
- **FP heuristics** (Phase 2): pass `fp_flags_by_key` into `run_pipeline`, keyed
  by `NormalizedFinding.match_key`. Any flag forces `LIKELY_FP`.
- **Dynamic confirmation** (Phase 4): emit `Source.FUZZER` findings with
  `has_poc=True` to reach `CONFIRMED`.
- **Calibration** (Phase 5): replace the placeholder weights in `ScoringConfig`
  and the priors in `taxonomy`/`crossmatch` with values learned from labeled
  history; the scorer already works in log-odds for exactly this.

## Status of the parser formats

The Mythril `-o json`/`jsonv2` schemas are stable and covered by fixture tests.
The Dedaub `srcwarnings`/Watchdog warning JSON is not fully public, so
`adapters/dedaub.py` parses **tolerantly** (multiple field spellings) and derives
the class from the warning name via the taxonomy. When the exact schema is
confirmed, tighten the field-name lists in that adapter rather than the logic.
