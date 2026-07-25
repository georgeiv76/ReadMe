# Dedaub Backlink Audit

A free replacement for the Semrush Backlink Audit, built on Google Search
Console, Ahrefs Webmaster Tools, Bing Webmaster Tools and open data
(Common Crawl via Open PageRank, Spamhaus DBL). It inventories every
referring domain, scores each one for toxicity on the same 0-100 scale
Semrush used, explains every score with named markers, and produces a
disavow candidate file that is reviewed by a human before anything is
ever uploaded to Google.

Research verified: 25 July 2026. All factual claims carry inline sources.

---

## 1. What Semrush gave us, and what replaces it

| Semrush feature | Free replacement | Notes |
|---|---|---|
| Backlink inventory | GSC Links report export + Ahrefs Webmaster Tools + Bing Webmaster Tools | three overlapping indexes beat one |
| Authority Score of linking domain | Open PageRank (0-10, Common Crawl data) | [domcop.com/openpagerank](https://www.domcop.com/openpagerank/), free API, 1,000 requests/day |
| Toxicity Score 0-100 | `backlink_audit` scoring engine (this repo) | same thresholds: 0-44 healthy, 45-59 review, 60-100 toxic |
| Toxic markers (45+) | 18 named markers, each printed with the score | fully transparent, configurable weights |
| Overall toxicity (Low/Medium/High) | same bands: under 3% / 3-10% / over 10% toxic share | mirrors [Semrush's convention](https://www.semrush.com/kb/580-auditing-your-backlinks) |
| New / lost backlinks | snapshot.json diff between monthly runs | also detects domains that escalated to toxic |
| Disavow file builder | `disavow-candidates.txt` with per-domain reasons | never auto-uploaded, by design |
| Site Audit crawl | out of scope here | on-page hygiene stays in the dedaub-gsc skill, Part 5.5 |

## 2. Data source research (what is actually available for free)

### Google Search Console
- The Links report shows top linking sites, top linked pages and top
  linking text for the whole dedaub.com domain property, and exports up
  to 100,000 rows per slice ("Latest links" and "More sample links").
  Source: [Google Search Console Help, Links report](https://support.google.com/webmasters/answer/9049606?hl=en).
- The GSC **API does not expose link data at all**; export is UI-only.
  Sources: [searchviu](https://www.searchviu.com/en/export-backlink-data-google-search-console/),
  [Coupler.io GSC API overview](https://blog.coupler.io/google-search-console-api/).
- Consequence for the desktop orchestrator: the gsc-server MCP has no
  links tool (its inventory is performance queries plus inspect_url),
  so one manual export per month is required. That is the only manual
  step in the whole pipeline.

### Ahrefs Webmaster Tools (AWT)
- Free for verified site owners, no credit card: backlink list,
  referring domains, anchors, dofollow/nofollow split, Domain Rating,
  new and lost links. Source: [ahrefs.com/webmaster-tools](https://ahrefs.com/webmaster-tools).
- Web UI shows up to 1,000 rows at a time with CSV export; works on
  unlimited verified sites. Source: [Allable AWT review](https://www.allable.ai/blog/ahrefs-webmaster-tools/).
- This is the strongest single free replacement for the Semrush link
  index and the main reason the setup checklist below matters.

### Bing Webmaster Tools
- Free backlinks report: referring pages, referring domains, anchor
  text, plus comparison against any other site's link profile. Limits:
  up to 100,000 URLs in the Pages report, 1,500 domains, 10,000
  backlinks per domain. Sources: [Bing Site Explorer help](https://www.bing.com/webmasters/help/site-explorer-c680da37),
  [SEOZoom on Bing WMT](https://www.seozoom.com/bing-webmaster-tools/),
  [Search Engine Journal guide](https://www.searchenginejournal.com/bing-webmaster-tools-guide/371540/).
- Bing also has a webmaster API that can return inbound links
  programmatically, an automation path GSC cannot offer.
  Source: [RankStudio backlink API comparison](https://rankstudio.net/articles/en/backlink-api-comparison).

### Open data
- **Open PageRank**: free 0-10 authority score for 10M+ domains,
  computed with PageRank math over Common Crawl data; free API key,
  1,000 requests/day, 100 domains per request.
  Source: [domcop.com/openpagerank](https://www.domcop.com/openpagerank/).
- **Spamhaus DBL**: the Domain Block List answers over DNS whether a
  domain is a known spam/phish/malware domain. Free for low-volume
  checks. Source: [Spamhaus DBL](https://www.spamhaus.org/blocklists/domain-blocklist/).
  Caveat: queries through big public resolvers (8.8.8.8 etc.) are
  refused or blanked, so treat a negative answer as best-effort.
- **Common Crawl web graph** (roadmap): host-level link graph released
  twice a year, the same raw data Open PageRank is built from. A future
  version can diff dedaub.com's inbound host set across releases.

### GA4 and GTM: the live alarm layer
GA4 and GTM cannot see the link graph; they see referrers that send
actual visits. That makes them the real-time complement to the monthly
inventory: a sudden burst of referral sessions from an unknown domain
with near-zero engagement is the live fingerprint of referral spam or a
negative-SEO campaign warming up. Investigation methodology (hostname
as a dimension client-side, dimension-artefact rules, escalation
protocol) already lives in the `dedaub-traffic-investigation` skill;
the new `dedaub-backlink-audit` skill routes to it.

## 3. The honest position on "toxic links" and disavow

- Since Penguin 4.0, Google devalues spammy links automatically rather
  than penalizing the site, and Google's own guidance says disavow is
  only needed for a manual action or when you expect one (bought
  links). Sources: [Search Engine Land disavow guide](https://searchengineland.com/guide/how-to-disavow-backlinks),
  [Dave Ashworth: stop disavowing "toxic" links](https://daveashworth.co/blog/seo-stop-using-the-google-disavow-tool-for-toxic-links/).
- Google's John Mueller has repeatedly framed "toxic links" as a
  concept promoted by SEO tool vendors. Disavowing good links by
  mistake can genuinely hurt rankings.
- This tool is therefore designed as **detect and document, disavow
  only when justified**: the disavow file is a candidates file with
  warnings in its header, and the runbook requires a GSC manual action
  or a confirmed negative-SEO spike before any upload to
  [Google's disavow tool](https://search.google.com/search-console/disavow-links).

What the audit IS for: knowing the link profile (which real domains
link to us and where growth comes from), catching negative-SEO attacks
early, keeping evidence ready if a manual action ever arrives, and
watching the trend of new/lost/escalated referring domains.

## 4. Architecture

```
INVENTORY (monthly)                 SCORING (automatic)         ACTION
GSC Links export  (manual, UI) --+
Ahrefs WMT export (manual, UI) --+--> ingest -> aggregate  --> audit-report.md
Bing WMT export   (optional)   --+    per referring domain --> scored-domains.csv
                                        |                  --> disavow-candidates.txt
                                        v                  --> snapshot.json (trend)
                              enrich (optional, --online)
                              DNS / HTTP / Spamhaus DBL /
                              Open PageRank / shared-IP clusters

ALARM (continuous, desktop orchestrator)
GA4 referral anomalies -> dedaub-traffic-investigation skill
```

## 5. The scoring model

Score 0-100 per referring domain. Thresholds mirror Semrush: toxic at
60+, review at 45-59 ([Semrush KB](https://www.semrush.com/kb/580-auditing-your-backlinks)).
Every fired signal is recorded as a named marker in the output.

| Marker | Weight | Signal |
|---|---|---|
| DBL_LISTED | 40 | domain on the Spamhaus Domain Block List |
| FREENOM_TLD | 25 | .tk .ml .ga .cf .gq free-registration TLD |
| SPAM_KEYWORD_DOMAIN | 22 | casino/porn/pills/replica etc. in the domain name |
| SITEWIDE_EXTREME | 22 | 1,000+ linking pages aimed at 1-2 targets |
| SPAM_TLD | 18 | high-abuse TLD (.xyz .top .icu .click ...) |
| SITEWIDE | 15 | 100+ linking pages aimed at 1-2 targets |
| SPAM_KEYWORD_ANCHOR | 15 | spam commerce keyword in anchor text |
| SHARED_IP_CLUSTER | 15 | shares an IP with 3+ other referring domains |
| NO_DNS | 12 | domain no longer resolves |
| OPR_MISSING | 12 | zero Open PageRank (unknown to Common Crawl) |
| PUNYCODE | 10 | xn-- lookalike domain |
| MANY_HYPHENS / DIGIT_HEAVY / FREE_HOST / HTTP_DEAD / OPR_LOW | 8 | name and liveness heuristics |
| NONLATIN_ANCHOR | 6 | unexpected non-Latin anchor text |
| LONG_DOMAIN | 5 | 25+ character name |

Dampeners: an all-nofollow profile subtracts 10 (nofollow links cannot
transfer toxicity in practice); a domain with Open PageRank >= 4.0 is
capped at score 30 unless it is DBL-listed; whitelisted domains
(GitHub, ethereum.org, CoinDesk, mirror.xyz, ...) always score 0.
Weights, keyword lists, TLD lists and the whitelist are all overridable
via `--config my.json`.

Free-host platforms (blogspot.com, wordpress.com, github.io, ...) are
tracked per subdomain, so a spam blog can be flagged and disavowed
without touching the platform root. Disavowing `blogspot.com` itself
would kill every Blogspot link; the tool structurally cannot emit that.

## 6. One-time setup checklist (about 30 minutes)

1. **Ahrefs Webmaster Tools** (the important one):
   [ahrefs.com/webmaster-tools](https://ahrefs.com/webmaster-tools),
   sign up free, add dedaub.com, verify with a DNS TXT record (same
   process as the GSC domain property verification).
2. **Bing Webmaster Tools**:
   [bing.com/webmasters](https://www.bing.com/webmasters), sign in and
   use "Import from Google Search Console": one click, no new
   verification.
3. **Open PageRank API key**:
   register free at [domcop.com/openpagerank](https://www.domcop.com/openpagerank/),
   then `export OPR_API_KEY=...` on the desktop.
4. Nothing to install: the tool is stdlib-only Python 3.

## 7. Monthly runbook

1. Export from GSC UI (Links report, top right "Export external
   links"): "Top linking sites" and "Latest links".
2. Export from Ahrefs Webmaster Tools: Backlinks report, CSV.
3. (Optional) Export from Bing Webmaster Tools: Backlinks, CSV.
4. Run:

```bash
cd backlink-audit
OPR_API_KEY=xxxx python3 -m backlink_audit.run_audit \
    --gsc-sites  exports/gsc-top-linking-sites.csv \
    --gsc-links  exports/gsc-latest-links.csv \
    --ahrefs     exports/ahrefs-backlinks.csv \
    --online \
    --prev       output/snapshot.json \
    --out        output/
```

5. Read `output/audit-report.md`: profile toxicity, the toxic table,
   the review queue, and the change-since-last-month section.
6. Curate: move false positives into the whitelist (config), keep the
   disavow candidates file on disk. Upload to Google only under the
   conditions in section 3.

Try it now with the bundled fixtures:

```bash
python3 -m backlink_audit.run_audit \
    --gsc-sites samples/gsc_top_linking_sites.csv \
    --gsc-links samples/gsc_latest_links.csv \
    --ahrefs samples/ahrefs_backlinks.csv \
    --out output/
```

## 8. Repo layout

```
backlink-audit/
  backlink_audit/         the tool (stdlib-only Python 3)
    ingest.py             header-flexible CSV parsers (GSC / Ahrefs / Bing)
    domains.py            registrable-domain logic, free-host handling
    enrich.py             DNS / HTTP / Spamhaus DBL / Open PageRank
    score.py              scoring engine, weights, whitelist, thresholds
    report.py             markdown report, CSV, disavow file, snapshot
    run_audit.py          CLI
  samples/                fixture exports for testing
  skill/dedaub-backlink-audit/SKILL.md   desktop orchestrator skill
  README.md               this document
```

## 9. Roadmap

1. Bing Webmaster API automation (the one index with programmatic
   inbound-link access) to remove one manual export.
2. Common Crawl host-graph diffing for discovery beyond the three
   indexes.
3. GA4 referral cross-check: auto-join scored-domains.csv with the
   monthly GA4 referral sources from the ga-gsc-gtm-report pipeline.
4. Optional GTM tag capturing document.referrer server-side for
   flagged domains (real-time negative-SEO alarm).
