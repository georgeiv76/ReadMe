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
own data via APIs and runs on a schedule.

## Part 1 - Where things live

| Asset | Location |
|---|---|
| Audit tool (Python 3, stdlib only) | `backlink-audit/` in the georgeiv76/ReadMe repo |
| Full research + source links | `backlink-audit/README.md` |
| Scoring config (weights, whitelist, TLD and keyword lists) | defaults in `backlink_audit/score.py`, override with `--config file.json` |
| Outputs per run | `output/`: audit-report.md, scored-domains.csv, disavow-candidates.txt, snapshot.json |
| Ahrefs API key (paid, Lite plan or higher) | env var `AHREFS_API_KEY` |
| Bing Webmaster API key (free) | env var `BING_WEBMASTER_API_KEY` |
| Open PageRank API key (free, 1,000 req/day) | env var `OPR_API_KEY` |

## Part 2 - Monthly runbook (autonomous)

1. The scheduled monthly task runs, with the three keys in the
   environment:

```bash
cd backlink-audit
python3 -m backlink_audit.run_audit \
  --target dedaub.com \
  --ahrefs-api --bing-api --online \
  --prev output/snapshot.json --out output/
```

2. Exit code 3 means API mode returned zero backlinks; the run aborted
   on purpose so an empty result never overwrites a good snapshot.
   Diagnose the key or plan limit and re-run. Do NOT fall back to
   asking Giorgio for CSV exports unless both APIs are confirmed dead
   and he approves the one-off manual step.
3. Read audit-report.md to Giorgio: profile toxicity band, toxic table,
   review queue, and the trend section (new / lost / escalated).
4. Curate the whitelist: any false positive gets added to the config
   whitelist so it never fires again.
5. Keep snapshot.json in place: it is next month's baseline.

Unit budget note: the default pull is one all-backlinks request, one
link per referring domain, 5 cheap fields: about 5 units per domain
plus 50 base. On the Lite plan (10,000 units/month) that covers a
profile up to roughly 1,900 referring domains monthly.

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

## CHANGELOG

### 25 July 2026 (second pass, same day)
- Autonomous mode added on Giorgio's zero-manual-work requirement:
  fetch.py pulls from the Ahrefs API v3 and Bing Webmaster API
  directly, GSC exports dropped from the standing pipeline, runbook
  rewritten around the scheduled API run, exit-code-3 snapshot guard
  documented, CSV ingestion demoted to emergency fallback.

### 25 July 2026
- Created. Tool, scoring model and research shipped in the
  georgeiv76/ReadMe repo, branch claude/backlink-analysis-gtm-ah7okq.
