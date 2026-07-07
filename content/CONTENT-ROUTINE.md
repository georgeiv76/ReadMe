# Content Weekly Routine — Orchestrator Rules

Standing rules for the content-research orchestrator (research → interpret → draft →
verify → publish). Created 2026-07-07 after a quote-attribution error in the
stablecoin-regulation article; amended rules marked **[R-2026-07-07]**.

## Pipeline (every content run)

1. **Collect** — raw legal/primary texts (or source manifests when downloads are
   blocked) + accredited interpretations, via parallel research agents.
2. **Draft** — article assembled ONLY from claims present in the research briefs.
3. **Footnote** — every quantitative claim and every direct quote gets a numbered
   footnote naming the exact source document.
4. **Verify (mandatory gate)** — adversarial fact-check pass before the draft is
   called "final." See Verification Loop below.
5. **Publish package** — markdown, footnoted markdown, plain-text paste, Word doc,
   all regenerated from the single canonical `linkedin-article.md` after ANY edit.

## Quote rules **[R-2026-07-07]**

These exist because a Cipollone quote was attributed to the wrong ECB document and
mixed verbatim words with paraphrase inside one set of quote marks.

- **Q1 — Two-tier quoting.** Quotation marks ONLY around words verified verbatim
  against the named source document. Everything else is paraphrase, outside quote
  marks, and the footnote must say "paraphrase."
- **Q2 — Document-level attribution.** A quote's footnote must name the *specific
  document* the words appear in (speech vs. committee statement vs. press release
  vs. interview are different documents), with date and, where possible, URL.
  "He said it around April 2025" is not an attribution.
- **Q3 — No quote fusion.** Never merge words from two occasions into one quoted
  sentence. Ellipses may compress a single passage only; the footnote should give
  the fuller verbatim.
- **Q4 — Snippet-verified ≠ verified.** When research runs in a network-restricted
  environment (search snippets only, no page fetches), every quote is at most
  PLAUSIBLE. The final deliverable must carry a verification note, and the top
  quotes must be click-tested by a human (or a fetch-capable agent) before
  publication. Mark each footnote's confidence implicitly by stating caveats
  ("self-reported," "paraphrase," "exchange-data estimate").

## Verification loop **[R-2026-07-07]**

- **V1 — Adversarial pass is mandatory**, not optional: spawn independent
  fact-checker agents whose instruction is to REFUTE each claim, covering (a) all
  direct quotes, (b) all statistics, (c) all statutory assertions (article/section
  numbers, thresholds, dates), (d) all source-document attributions.
- **V2 — Verdict schema:** CONFIRMED / PLAUSIBLE / WRONG. WRONG items are fixed
  before publication; PLAUSIBLE items either get a caveat in the footnote or are
  downgraded to paraphrase.
- **V3 — Fix-and-regenerate:** any correction is applied to the canonical markdown
  first, then ALL derived formats are regenerated in the same commit. Derived files
  must never drift from the canonical file.
- **V4 — Verification report is a deliverable:** the run commits a
  `verification-report.md` alongside the article listing every checked claim and
  its verdict, so the human editor sees exactly what was and wasn't confirmed.
- **V5 — Human click-test list:** the report ends with the ranked shortlist of
  claims the human should personally click-verify (direct quotes from officials
  first, then statutory numbers, then market statistics).

## Statutory-claim rules

- **S1 —** Cite article/section numbers only when confirmed against the enacted
  text or two independent legal analyses; otherwise describe the provision without
  a number.
- **S2 —** Distinguish "the statute says" from "commentators read it as." Untested
  interpretations (e.g., non-dollar stablecoins under GENIUS) must be flagged as
  inference pending rulemaking.

## Data rules

- **D1 —** Conflicting figures across trackers → give the range or the hedged form
  ("roughly," "~"), and note the methodology dependence in the footnote.
- **D2 —** Self-reported numbers (issuer attestations) always carry a caveat.
- **D3 —** Projections carry the institution AND scenario (base vs. bull) AND date;
  revised projections cite both vintages.

## Network-restriction protocol

When the execution environment blocks page fetches (agent proxy 403s):
- say so in the deliverable's verification note;
- store official download links + commands in a `SOURCES.md` manifest;
- treat every verbatim quote as unconfirmed until human click-test (Q4);
- prefer official/institutional URLs (Congress.gov, EUR-Lex, ECB, EBA, ESMA, BIS,
  Treasury, Federal Reserve) in footnotes — press URLs move.

## Change log

- 2026-07-07 — File created. Root cause: article quoted Cipollone
  "compromise our monetary sovereignty" attributed to the ECB speech PDF of
  April 7, 2025; the verbatim ("…excessively undermines resilience and compromises
  monetary sovereignty") actually appears in his April 8, 2025 European Parliament
  ECON statement, and the "euro deposits to America" clause was press paraphrase
  presented inside quotes. Fix: rules Q1-Q4, V1-V5 above; corrected in commit
  f493192.
