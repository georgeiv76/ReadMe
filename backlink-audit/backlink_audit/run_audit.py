"""CLI entrypoint.

Offline run (signals from the exports only):

    python3 -m backlink_audit.run_audit \
        --gsc-sites exports/gsc-top-linking-sites.csv \
        --gsc-links exports/gsc-latest-links.csv \
        --out output/

Full run (adds DNS, HTTP, Spamhaus DBL and Open PageRank):

    OPR_API_KEY=xxxx python3 -m backlink_audit.run_audit \
        --gsc-sites exports/gsc-top-linking-sites.csv \
        --ahrefs exports/ahrefs-backlinks.csv \
        --online --out output/ --prev output/snapshot.json
"""

import argparse
import os
import sys

from . import ingest, enrich, fetch, score, report


def build_parser():
    p = argparse.ArgumentParser(
        prog="backlink_audit",
        description="Free backlink toxicity audit (Semrush Backlink Audit replacement)")
    p.add_argument("--target", default="dedaub.com",
                   help="Domain to audit in API mode (default: dedaub.com)")
    p.add_argument("--ahrefs-api", action="store_true",
                   help="Fetch backlinks from the Ahrefs API v3 (needs AHREFS_API_KEY)")
    p.add_argument("--ahrefs-key", default=os.environ.get("AHREFS_API_KEY", ""),
                   help="Ahrefs API key (or env AHREFS_API_KEY)")
    p.add_argument("--ahrefs-limit", type=int, default=2000,
                   help="Max rows from the Ahrefs API (default 2000)")
    p.add_argument("--ahrefs-select", default=fetch.AHREFS_DEFAULT_SELECT,
                   help="Fields for the Ahrefs select param (unit cost driver)")
    p.add_argument("--ahrefs-all-links", action="store_true",
                   help="Fetch every link instead of one per referring domain")
    p.add_argument("--bing-api", action="store_true",
                   help="Fetch backlinks from the Bing Webmaster API (needs BING_WEBMASTER_API_KEY)")
    p.add_argument("--bing-key", default=os.environ.get("BING_WEBMASTER_API_KEY", ""),
                   help="Bing Webmaster API key (or env BING_WEBMASTER_API_KEY)")
    p.add_argument("--gsc-sites", help="GSC Links report 'Top linking sites' CSV")
    p.add_argument("--gsc-links", action="append", default=[],
                   help="GSC 'Latest links' or 'More sample links' CSV (repeatable)")
    p.add_argument("--ahrefs", action="append", default=[],
                   help="Ahrefs Webmaster Tools backlinks CSV (repeatable)")
    p.add_argument("--bing", action="append", default=[],
                   help="Bing Webmaster Tools backlinks CSV (repeatable)")
    p.add_argument("--online", action="store_true",
                   help="Enable network enrichment (DNS, HTTP, Spamhaus DBL)")
    p.add_argument("--opr-key", default=os.environ.get("OPR_API_KEY", ""),
                   help="Open PageRank API key (or env OPR_API_KEY)")
    p.add_argument("--skip-http", action="store_true", help="Skip HTTP liveness checks")
    p.add_argument("--skip-dbl", action="store_true", help="Skip Spamhaus DBL checks")
    p.add_argument("--skip-dr", action="store_true",
                   help="Skip the free Ahrefs Domain Rating lookups")
    p.add_argument("--config", help="JSON file overriding weights and lists")
    p.add_argument("--prev", help="Previous snapshot.json for trend comparison")
    p.add_argument("--out", default="output", help="Output directory (default: output)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    api_mode = args.ahrefs_api or args.bing_api
    if not (api_mode or args.gsc_sites or args.gsc_links or args.ahrefs or args.bing):
        print("ERROR: provide an input: --ahrefs-api / --bing-api for "
              "autonomous mode, or CSVs (--gsc-sites / --gsc-links / "
              "--ahrefs / --bing) for fallback mode", file=sys.stderr)
        return 2
    if args.ahrefs_api and not args.ahrefs_key:
        print("ERROR: --ahrefs-api needs AHREFS_API_KEY (env) or --ahrefs-key",
              file=sys.stderr)
        return 2
    if args.bing_api and not args.bing_key:
        print("ERROR: --bing-api needs BING_WEBMASTER_API_KEY (env) or --bing-key",
              file=sys.stderr)
        return 2

    cfg = score.load_config(args.config)

    site_counts = ingest.parse_gsc_sites(args.gsc_sites) if args.gsc_sites else {}
    backlinks = []
    if args.ahrefs_api:
        backlinks += fetch.fetch_ahrefs(
            args.target, args.ahrefs_key, limit=args.ahrefs_limit,
            select=args.ahrefs_select,
            aggregation=None if args.ahrefs_all_links else "1_per_domain",
            log=print)
    if args.bing_api:
        site_url = args.target if "://" in args.target else f"https://{args.target}/"
        backlinks += fetch.fetch_bing(site_url, args.bing_key, log=print)
    for path in args.gsc_links:
        backlinks += ingest.parse_gsc_links(path)
    for path in args.ahrefs:
        backlinks += ingest.parse_ahrefs(path)
    for path in args.bing:
        backlinks += ingest.parse_bing(path)

    if api_mode and not backlinks and not site_counts:
        print("ERROR: API mode returned zero backlinks; aborting so an "
              "empty report never overwrites a good snapshot", file=sys.stderr)
        return 3

    domains = ingest.aggregate(site_counts, backlinks)
    print(f"Loaded {len(domains)} referring domains "
          f"({len(backlinks)} link rows, {len(site_counts)} site rows)")

    ip_counts = None
    if args.online:
        print("Enriching (DNS / HTTP / Spamhaus DBL"
              + ("" if args.skip_dr else " / Domain Rating by Ahrefs")
              + (" / Open PageRank" if args.opr_key else "") + ") ...")
        ip_counts = enrich.enrich_domains(
            domains, opr_key=args.opr_key or None,
            ahrefs_key=args.ahrefs_key or None,
            skip_http=args.skip_http, skip_dbl=args.skip_dbl,
            skip_dr=args.skip_dr, log=print)

    score.score_all(domains, cfg, ip_counts)
    summary = score.profile_summary(domains, cfg)

    os.makedirs(args.out, exist_ok=True)
    trend = report.compare_snapshot(domains, args.prev) if args.prev else None

    report_path = os.path.join(args.out, "audit-report.md")
    report.write_report(domains, summary, report_path,
                        trend=trend, enriched=args.online)
    report.write_scored_csv(domains, os.path.join(args.out, "scored-domains.csv"))
    n_disavow = report.write_disavow(
        domains, os.path.join(args.out, "disavow-candidates.txt"))
    report.write_snapshot(domains, summary,
                          os.path.join(args.out, "snapshot.json"))

    print(f"\nProfile toxicity: {summary['profile_toxicity']} "
          f"({summary['toxic']} toxic / {summary['review']} review / "
          f"{summary['healthy']} healthy of {summary['total_domains']} domains)")
    print(f"Report:             {report_path}")
    print(f"Scored CSV:         {os.path.join(args.out, 'scored-domains.csv')}")
    print(f"Disavow candidates: {n_disavow} domains "
          f"({os.path.join(args.out, 'disavow-candidates.txt')}) - REVIEW BEFORE ANY UPLOAD")
    print(f"Snapshot:           {os.path.join(args.out, 'snapshot.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
