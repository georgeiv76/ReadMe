---
name: dedaub-backlink-audit
description: Monthly backlink toxicity audit for dedaub.com - free replacement
  for the Semrush Backlink Audit. Use whenever Giorgio asks about backlinks,
  toxic links, link spam, disavow, referring domains, negative SEO, link
  profile health, or who links to dedaub.com. Covers the data sources (GSC
  Links export, Ahrefs Webmaster Tools, Bing Webmaster Tools, Open PageRank,
  Spamhaus DBL), the monthly runbook for the backlink_audit tool in the
  georgeiv76/ReadMe repo, toxicity score interpretation, disavow decision
  rules, and the GA4 live-alarm routing. Trigger keywords - backlink, toxic
  link, link audit, disavow, referring domain, link spam, negative SEO,
  anchor text, link profile, who links to us, Semrush backlink replacement.
---

# Dedaub Backlink Audit - Skill

## How this skill layers

| Domain | This skill | Sister skill |
|---|---|---|
| Backlink inventory, toxicity scoring, disavow decisions | dedaub-backlink-audit | - |
| GSC environment, gsc-server tools, timeouts | - | dedaub-gsc |
| Live referral anomalies, bot/scraping investigation | - | dedaub-traffic-investigation |
| SEO strategy, page tiers, editorial actions | - | dedaub-seo |
| Monthly GA4+GSC dataset pipeline | - | ga-gsc-gtm-report |

HARD FACT: the gsc-server MCP has NO backlinks tool. The GSC API does
not expose the Links report. Never promise Giorgio an API pull of GSC
links; it does not exist. The pipeline therefore runs WITHOUT GSC link
data by design: the autonomous inventory is Ahrefs API v3 plus Bing
Webmaster API.

OPERATING CONTRACT (set by Giorgio, 25 July 2026): zero recurring
manual work. No CSV downloads, no UI exports. The audit fetches its
own data via APIs. Amended same day: the audit must be an always-on
MCP server on the desktop, not a script someone remembers to run.

## Part 1 - Where things live

| Asset | Location |
|---|---|
| Audit tool (Python 3, stdlib only) | `backlink-audit/backlink_audit/` in the georgeiv76/ReadMe repo |
| MCP server (the primary interface) | `backlink-audit/mcp_server/server.py`, registered via `.mcp.json` at repo root |
| Full research + source links | `backlink-audit/README.md`, section 7 covers the MCP server |
| Setup steps for a fresh desktop | `backlink-audit/BOOTSTRAP.md` |
| Scoring config (weights, whitelist, TLD and keyword lists) | defaults in `backlink_audit/score.py`, override with `--config file.json` (CLI) |
| Outputs per run | `backlink-audit/output/<target>/`: audit-report.md, scored-domains.csv, disavow-candidates.txt, snapshot.json |
| Ahrefs API key (paid, Lite plan or higher; from "Generate API key", NOT "Generate MCP key") | env var `AHREFS_API_KEY`, or `backlink-audit/keys.env` |
| Bing Webmaster API key (free) | env var `BING_WEBMASTER_API_KEY`, or `keys.env` |
| Open PageRank API key (free, 1,000 req/day) | env var `OPR_API_KEY`, or `keys.env` |

`keys.env` (git-ignored) is the fallback for GUI-launched processes
that do not inherit shell-exported environment variables. A real
environment variable always wins over the file.

## Part 2 - Runbook (MCP server, primary path)

Once `.mcp.json` is registered and approved (see BOOTSTRAP.md), the
tools below are available in every session on this repo - no command
to remember, no script to run manually.

1. First, or whenever something looks wrong (new key, plan change,
   empty results): call `check_data_sources(target="dedaub.com")`. It
   tests Ahrefs REST, Ahrefs free Domain Rating, Bing, Open PageRank
   and Spamhaus against the REAL target, and explains each failure.
2. Call `run_audit(target="dedaub.com")`. If it returns
   `status: "ERROR"` with zero backlinks, that is intentional: it
   never overwrites a good snapshot with an empty run. Diagnose via
   `check_data_sources` and retry. Do NOT fall back to asking Giorgio
   for CSV exports unless both APIs are confirmed dead and he approves
   the one-off manual step.
3. Call `get_last_report(target="dedaub.com")` for the full markdown;
   report to Giorgio in the Part 6 format.
4. Curate the whitelist in `backlink_audit/score.py` (or a
   `--config` file for CLI runs): any false positive gets added so it
   never fires again.
5. For a one-off check outside the monthly cycle (a suspicious new
   referrer noticed in analytics), call
   `score_single_domain(domain="...")` directly - no full audit needed.
6. Scheduling: since the server is always live, "monthly" means a
   scheduled call to `run_audit` (Cowork scheduled task, launchd, or a
   Routine), not a shell command someone has to remember.

## Part 2b - Fallback runbook (CLI, only if the MCP server is down)

```bash
cd backlink-audit
python3 -m backlink_audit.run_audit \
  --target dedaub.com \
  --ahrefs-api --bing-api --online \
  --prev output/snapshot.json --out output/
```

Exit code 3 means the same zero-backlinks safety abort as above. Unit
budget note: the default pull is one all-backlinks request, one link
per referring domain, 5 cheap fields: about 5 units per domain plus 50
base. On the Lite plan (10,000 units/month) that covers a profile up
to roughly 1,900 referring domains monthly.

## Part 3 - Score interpretation

| Score | Bucket | Meaning |
|---|---|---|
| 60-100 | toxic | disavow candidate, human review required |
| 45-59 | review | watch list, re-check next run |
| 0-44 | healthy | no action |

Profile bands (share of toxic referring domains): LOW under 3%,
MEDIUM 3-10%, HIGH over 10%. These mirror the Semrush conventions so
historical intuition still applies.

Every score comes with named markers (SPAM_TLD, SITEWIDE, DBL_LISTED,
SHARED_IP_CLUSTER, ...). When reporting, always quote the markers, not
just the number: the markers are the evidence.

## Part 4 - Disavow decision rules (HARD RULES)

1. NEVER upload disavow-candidates.txt to Google as generated. It is a
   candidates file with warnings in its header, not a finished disavow.
2. Upload conditions, at least one required:
   - GSC shows a manual action for unnatural links, or
   - a confirmed negative-SEO spike: many new toxic domains in the
     trend section plus a matching GA4 referral anomaly.
3. Since Penguin 4.0 Google devalues spam links on its own; a wrong
   disavow of a good domain can reduce rankings. When in doubt, do not
   disavow: document and wait one cycle.
4. Free-host spam is disavowed at subdomain level (the tool already
   emits `domain:spam-blog.blogspot.com`, never the platform root).
5. Any upload is done by Giorgio in the browser at
   search.google.com/search-console/disavow-links; Claude prepares the
   reviewed file and the evidence summary, never uploads.

## Part 5 - GA4 live alarm routing

The monthly audit is the inventory. Real-time detection of an active
campaign is a traffic investigation:

- Signal: sudden referral sessions from an unknown source with near-zero
  engagement, or a burst of new referring domains in the trend section.
- Action: load dedaub-traffic-investigation and run its base query
  methodology (hostname as a dimension, client-side filtering; the GA4
  API has no server-side hostname filter).
- If the investigation confirms an attack, that satisfies Part 4 rule 2
  and the disavow review can start.

## Part 6 - Output standards

Reporting an audit run to Giorgio:

```
AUDIT RUN: <date>
SOURCES: <gsc-sites | gsc-links | ahrefs | bing>, enrichment <on|off>
DOMAINS: N total - X toxic / Y review / Z healthy
PROFILE TOXICITY: <LOW|MEDIUM|HIGH> (N.N% toxic share)
TREND: +N new, -N lost, N escalated
TOP FINDINGS: <top 3 toxic domains with their markers>
DISAVOW: <not warranted | review recommended - reason>
```

## Part 7 - Anti-patterns

| Anti-pattern | Flag as |
|---|---|
| Asking Giorgio for a CSV export or any recurring manual step | CONTRACT VIOLATION - autonomous mode is the standing agreement |
| Promising GSC backlink data via API or gsc-server | DOES NOT EXIST - UI export only |
| Uploading or recommending upload of the raw candidates file | HARD RULE VIOLATION - Part 4 |
| Disavowing a free-host platform root (blogspot.com, wordpress.com) | COLLATERAL DAMAGE - subdomain only |
| Treating a Spamhaus DBL "not listed" answer as proof of cleanliness | BEST-EFFORT SIGNAL - public resolvers are blocked |
| Reading the toxicity number without quoting markers | EVIDENCE-FREE REPORTING |
| Calling links "toxic" to Giorgio without the Penguin 4.0 caveat | OVERSELLING - Google devalues most spam automatically |
| Running the audit without --prev when a snapshot exists | TREND LOSS - new/lost/escalated needs the baseline |
| Using em dash in any output | FORMATTING VIOLATION - use hyphen, colon, or restructure |
| Generating an Ahrefs "MCP key" for use as the REST API Bearer token | WRONG KEY TYPE - MCP scope authenticates a different protocol; use "Generate API key" |
| Treating the CLI as the primary interface once the MCP server is registered | STALE MENTAL MODEL - MCP server is primary, CLI is fallback (Part 2b) |

## CHANGELOG

### 25 July 2026 (third pass, same day: MCP server)
- Built `backlink-audit/mcp_server/server.py`: an always-on local MCP
  server wrapping the same backlink_audit package, six tools
  (check_data_sources, run_audit, get_last_report,
  list_domains_by_bucket, score_single_domain,
  get_disavow_candidates), registered via `.mcp.json` at the repo root
  using `${CLAUDE_PROJECT_DIR}` (portable, no hardcoded paths, no
  secrets committed).
- Verified over the real MCP stdio protocol: tool registration, every
  tool's no-keys/no-prior-data path, offline and network-blocked
  scoring. Caught and fixed one real bug this way: a bare empty list
  return crashed the MCP client; every tool now returns a dict.
- Added `keys.env` local-file fallback (git-ignored) for GUI-launched
  processes that do not inherit shell-exported env vars; real env vars
  still take precedence.
- CLI demoted to explicit fallback (Part 2b); MCP server is Part 2.

### 25 July 2026 (second pass, same day)
- Autonomous mode added on Giorgio's zero-manual-work requirement:
  fetch.py pulls from the Ahrefs API v3 and Bing Webmaster API
  directly, GSC exports dropped from the standing pipeline, runbook
  rewritten around the scheduled API run, exit-code-3 snapshot guard
  documented, CSV ingestion demoted to emergency fallback.

### 25 July 2026
- Created. Tool, scoring model and research shipped in the
  georgeiv76/ReadMe repo, branch claude/backlink-analysis-gtm-ah7okq.
