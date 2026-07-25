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

from . import ingest, enrich, score, report


def build_parser():
    p = argparse.ArgumentParser(
        prog="backlink_audit",
        description="Free backlink toxicity audit (Semrush Backlink Audit replacement)")
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
    p.add_argument("--config", help="JSON file overriding weights and lists")
    p.add_argument("--prev", help="Previous snapshot.json for trend comparison")
    p.add_argument("--out", default="output", help="Output directory (default: output)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not (args.gsc_sites or args.gsc_links or args.ahrefs or args.bing):
        print("ERROR: provide at least one input CSV "
              "(--gsc-sites / --gsc-links / --ahrefs / --bing)", file=sys.stderr)
        return 2

    cfg = score.load_config(args.config)

    site_counts = ingest.parse_gsc_sites(args.gsc_sites) if args.gsc_sites else {}
    backlinks = []
    for path in args.gsc_links:
        backlinks += ingest.parse_gsc_links(path)
    for path in args.ahrefs:
        backlinks += ingest.parse_ahrefs(path)
    for path in args.bing:
        backlinks += ingest.parse_bing(path)

    domains = ingest.aggregate(site_counts, backlinks)
    print(f"Loaded {len(domains)} referring domains "
          f"({len(backlinks)} link rows, {len(site_counts)} site rows)")

    ip_counts = None
    if args.online:
        print("Enriching (DNS / HTTP / Spamhaus DBL"
              + (" / Open PageRank" if args.opr_key else "") + ") ...")
        ip_counts = enrich.enrich_domains(
            domains, opr_key=args.opr_key or None,
            skip_http=args.skip_http, skip_dbl=args.skip_dbl, log=print)

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
