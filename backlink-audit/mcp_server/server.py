#!/usr/bin/env python3
"""Dedaub Backlink Audit - MCP server.

Runs locally (stdio transport) so the audit is always available to any
MCP client on this machine - no monthly manual command, no repo pull
required to use it day to day. Wraps the exact same backlink_audit
package used by the CLI; no logic is duplicated here.

Register it once (see backlink-audit/README.md, "MCP server" section)
and every future Claude session on this desktop gets these tools for
free, for as long as the process is registered.

Keys are read from the environment at call time, never stored in this
file or the repo: AHREFS_API_KEY, BING_WEBMASTER_API_KEY, OPR_API_KEY.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


def _load_local_keys():
    """Best-effort .env-style loader so this server has its keys even
    when launched by a GUI app that does not inherit the user's shell
    environment (a real difference from a terminal-launched process).
    Reads backlink-audit/keys.env if present. Never overwrites a
    variable that is already set, so real OS environment variables
    always win. The file is git-ignored; never commit real keys."""
    path = os.path.join(BASE_DIR, "keys.env")
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


_load_local_keys()

from mcp.server.fastmcp import FastMCP

from backlink_audit import enrich, fetch, ingest, report, score
from backlink_audit.domains import registrable_domain

mcp = FastMCP("dedaub-backlink-audit")


def _out_dir(target):
    slug = registrable_domain(target) or target.strip().lower()
    path = os.path.join(BASE_DIR, "output", slug)
    os.makedirs(path, exist_ok=True)
    return path


def _keys():
    return {
        "ahrefs": os.environ.get("AHREFS_API_KEY", ""),
        "bing": os.environ.get("BING_WEBMASTER_API_KEY", ""),
        "opr": os.environ.get("OPR_API_KEY", ""),
    }


@mcp.tool()
def check_data_sources(target: str = "dedaub.com") -> dict:
    """Test every data source this audit depends on, against the real
    target domain, and report which ones are configured and reachable
    right now: Ahrefs REST API, Ahrefs free Domain Rating endpoint,
    Bing Webmaster API, Open PageRank, and Spamhaus DBL. Call this
    first when something looks wrong, or after changing keys or plans,
    before running a full audit. Deliberately tests the real target
    rather than an Ahrefs free-test domain, because a free-test domain
    can succeed on a plan that is still restricted for real targets -
    that mismatch is exactly the failure mode this project hit before."""
    keys = _keys()
    out = {}

    if not keys["ahrefs"]:
        out["ahrefs_api"] = {"status": "NOT CONFIGURED", "detail": "AHREFS_API_KEY not set"}
    else:
        links = fetch.fetch_ahrefs(target, keys["ahrefs"], limit=1, log=None)
        out["ahrefs_api"] = ({"status": "OK"} if links else
                             {"status": "FAILED", "detail":
                              "check plan includes Site Explorer API units, "
                              "and the key is from 'Generate API key', not "
                              "'Generate MCP key'"})

    dr = enrich.ahrefs_dr_free(target, api_key=keys["ahrefs"] or None)
    out["ahrefs_domain_rating_free"] = ({"status": "OK", "sample_dr": dr}
                                        if dr is not None else
                                        {"status": "FAILED"})

    if not keys["bing"]:
        out["bing_api"] = {"status": "NOT CONFIGURED", "detail": "BING_WEBMASTER_API_KEY not set"}
    else:
        sites, err = fetch.bing_verified_sites(keys["bing"])
        if err:
            out["bing_api"] = {"status": "FAILED", "detail": err}
        else:
            out["bing_api"] = {"status": "OK", "verified_sites": sites}

    if not keys["opr"]:
        out["open_pagerank"] = {"status": "NOT CONFIGURED", "detail": "OPR_API_KEY not set"}
    else:
        scores = enrich.open_pagerank(["ahrefs.com"], keys["opr"])
        out["open_pagerank"] = ({"status": "OK"} if scores.get("ahrefs.com") is not None
                                else {"status": "FAILED"})

    dbl = enrich.spamhaus_dbl("dbltest.com")
    out["spamhaus_dbl"] = {"status": "OK" if dbl is not None else "BEST-EFFORT-BLOCKED",
                           "detail": "public resolvers are sometimes refused; not fatal"}

    resolves, _ = enrich.resolve_domain("ahrefs.com")
    out["outbound_network"] = {"status": "OK" if resolves else "BLOCKED",
                               "detail": "DNS resolution test for ahrefs.com"}
    return out


@mcp.tool()
def run_audit(target: str = "dedaub.com", use_ahrefs: bool = True,
             use_bing: bool = True, online_enrichment: bool = True) -> dict:
    """Run a full backlink toxicity audit for a domain: fetch backlinks
    from the Ahrefs API and/or Bing Webmaster API, enrich every
    referring domain (DNS, HTTP, Spamhaus, Open PageRank, Ahrefs Domain
    Rating), score each 0-100, and write the report, scored CSV,
    disavow candidates and a snapshot for next-run trend detection.
    Returns a summary; use get_last_report for the full markdown."""
    keys = _keys()
    out_dir = _out_dir(target)
    cfg = score.load_config()

    backlinks = []
    log_lines = []

    def log(msg):
        log_lines.append(msg)

    if use_ahrefs:
        if not keys["ahrefs"]:
            log_lines.append("ahrefs-api: skipped, AHREFS_API_KEY not set")
        else:
            backlinks += fetch.fetch_ahrefs(target, keys["ahrefs"], log=log)
    if use_bing:
        if not keys["bing"]:
            log_lines.append("bing-api: skipped, BING_WEBMASTER_API_KEY not set")
        else:
            site_url = target if "://" in target else f"https://{target}/"
            backlinks += fetch.fetch_bing(site_url, keys["bing"], log=log)

    if not backlinks:
        return {"status": "ERROR", "reason": "zero backlinks returned by every "
                "configured source; no report written to avoid overwriting a "
                "good snapshot", "log": log_lines}

    domains = ingest.aggregate({}, backlinks)

    ip_counts = None
    if online_enrichment:
        ip_counts = enrich.enrich_domains(domains, opr_key=keys["opr"] or None,
                                          ahrefs_key=keys["ahrefs"] or None, log=log)

    score.score_all(domains, cfg, ip_counts)
    summary = score.profile_summary(domains, cfg)

    prev_path = os.path.join(out_dir, "snapshot.json")
    trend = report.compare_snapshot(domains, prev_path) if os.path.exists(prev_path) else None

    report.write_report(domains, summary, os.path.join(out_dir, "audit-report.md"),
                        trend=trend, enriched=online_enrichment)
    report.write_scored_csv(domains, os.path.join(out_dir, "scored-domains.csv"))
    n_disavow = report.write_disavow(domains, os.path.join(out_dir, "disavow-candidates.txt"))
    report.write_snapshot(domains, summary, prev_path)

    toxic = sorted((r for r in domains.values() if r.bucket == "toxic"),
                  key=lambda r: -r.score)[:10]

    return {
        "status": "OK",
        "target": target,
        "summary": summary,
        "trend": trend,
        "top_toxic_domains": [{"domain": r.domain, "score": r.score,
                               "markers": r.markers[:4]} for r in toxic],
        "disavow_candidates": n_disavow,
        "output_dir": out_dir,
        "log": log_lines,
    }


@mcp.tool()
def get_last_report(target: str = "dedaub.com") -> str:
    """Return the full markdown of the most recent audit report for a
    domain. Run run_audit first if no report exists yet."""
    path = os.path.join(_out_dir(target), "audit-report.md")
    if not os.path.exists(path):
        return f"No report yet for {target}. Call run_audit first."
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


@mcp.tool()
def list_domains_by_bucket(target: str = "dedaub.com", bucket: str = "toxic") -> dict:
    """List referring domains from the last audit filtered by bucket:
    'toxic' (score 60+), 'review' (45-59) or 'healthy' (0-44). Each
    entry includes the score and the markers that explain it."""
    path = os.path.join(_out_dir(target), "scored-domains.csv")
    if not os.path.exists(path):
        return {"target": target, "bucket": bucket, "domains": [],
                "note": "no report yet, call run_audit first"}
    import csv
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["bucket"] == bucket:
                rows.append(row)
    rows.sort(key=lambda r: -int(r["score"]))
    return {"target": target, "bucket": bucket, "count": len(rows), "domains": rows}


@mcp.tool()
def score_single_domain(domain: str, online: bool = True) -> dict:
    """Score one specific domain right now, outside a full audit. Use
    this to check a single new or suspicious backlink source on the
    spot, e.g. right after noticing it in analytics."""
    from backlink_audit.ingest import RefDomain
    rd = RefDomain(domain=registrable_domain(domain) or domain)
    rd.linking_pages = 1
    rd.target_pages = 1
    if online:
        keys = _keys()
        rd.resolves, rd.ips = enrich.resolve_domain(rd.domain)
        if rd.resolves:
            rd.http_status = enrich.http_status(rd.domain)
        rd.dbl_listed = enrich.spamhaus_dbl(rd.domain)
        rd.dr = enrich.ahrefs_dr_free(rd.domain, api_key=keys["ahrefs"] or None)
        if keys["opr"]:
            rd.opr = enrich.open_pagerank([rd.domain], keys["opr"]).get(rd.domain)
    cfg = score.load_config()
    score.score_domain(rd, cfg)
    return {"domain": rd.domain, "score": rd.score, "bucket": rd.bucket,
            "markers": rd.markers}


@mcp.tool()
def get_disavow_candidates(target: str = "dedaub.com") -> str:
    """Return the disavow candidates file for a domain, including its
    review warnings. This is NEVER a finished disavow file: read the
    warnings, verify every domain by hand, and only upload to Google
    under the conditions in README.md section 3 (manual action or
    confirmed negative-SEO attack)."""
    path = os.path.join(_out_dir(target), "disavow-candidates.txt")
    if not os.path.exists(path):
        return f"No disavow candidates file yet for {target}. Call run_audit first."
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


if __name__ == "__main__":
    mcp.run()
