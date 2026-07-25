"""Header-flexible CSV ingestion for backlink exports.

Supported inputs:
- Google Search Console, Links report, "Top linking sites" export
- Google Search Console, Links report, "Latest links" or
  "More sample links" export (one linking-page URL per row)
- Ahrefs Webmaster Tools backlinks export
- Bing Webmaster Tools backlinks export

Columns are located by fuzzy header matching, so localized or slightly
renamed exports still load. Everything funnels into Backlink records,
then aggregate() rolls them up per registrable domain.
"""

import csv
import io
from collections import Counter
from dataclasses import dataclass, field

from .domains import registrable_domain, hostname_of


@dataclass
class Backlink:
    source_url: str
    target_url: str = ""
    anchor: str = ""
    nofollow: bool = False
    first_seen: str = ""
    origin: str = ""  # gsc | ahrefs | bing


@dataclass
class RefDomain:
    domain: str
    linking_pages: int = 0
    target_pages: int = 0
    total_links: int = 0
    nofollow_links: int = 0
    anchors: Counter = field(default_factory=Counter)
    origins: set = field(default_factory=set)
    sample_urls: list = field(default_factory=list)
    hostnames: set = field(default_factory=set)
    # enrichment (None = not checked)
    resolves: object = None
    ips: list = field(default_factory=list)
    http_status: object = None
    opr: object = None
    dr: object = None  # Domain Rating by Ahrefs (free public endpoint)
    dbl_listed: object = None
    # scoring
    score: int = 0
    markers: list = field(default_factory=list)
    bucket: str = "healthy"


def _read_rows(path):
    """Read a CSV allowing UTF-8 BOM (GSC exports ship with one)."""
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        text = fh.read()
    # GSC sometimes exports with \r line endings only
    return list(csv.reader(io.StringIO(text)))


def _find_col(headers, candidates, default=None):
    """Return the index of the first header matching any candidate.

    A candidate matches when every one of its words appears in the
    header (case-insensitive). Example: ("linking", "page") matches
    "Linking pages" and "Top linking pages".
    """
    lowered = [h.lower() for h in headers]
    for cand in candidates:
        words = cand.split()
        for i, h in enumerate(lowered):
            if all(w in h for w in words):
                return i
    return default


def parse_gsc_sites(path):
    """GSC 'Top linking sites' export -> {domain: (linking_pages, target_pages)}."""
    rows = _read_rows(path)
    if not rows:
        return {}
    headers = rows[0]
    i_site = _find_col(headers, ["site", "domain"], default=0)
    i_links = _find_col(headers, ["linking page", "links"], default=1)
    i_targets = _find_col(headers, ["target"], default=2)
    out = {}
    for row in rows[1:]:
        if not row or not row[0].strip():
            continue
        dom = registrable_domain(row[i_site])
        if not dom:
            continue

        def _num(idx):
            try:
                return int(str(row[idx]).replace(",", "").replace(".", "") or 0)
            except (ValueError, IndexError):
                return 0

        lp, tp = _num(i_links), _num(i_targets)
        prev = out.get(dom, (0, 0))
        out[dom] = (prev[0] + lp, max(prev[1], tp))
    return out


def parse_gsc_links(path):
    """GSC 'Latest links' / 'More sample links' export -> [Backlink]."""
    rows = _read_rows(path)
    if not rows:
        return []
    headers = rows[0]
    i_url = _find_col(headers, ["linking page", "page", "url"], default=0)
    i_date = _find_col(headers, ["crawl", "date", "discover"])
    links = []
    for row in rows[1:]:
        if not row or not row[i_url].strip():
            continue
        links.append(Backlink(
            source_url=row[i_url].strip(),
            first_seen=(row[i_date].strip() if i_date is not None and i_date < len(row) else ""),
            origin="gsc",
        ))
    return links


def parse_ahrefs(path):
    """Ahrefs Webmaster Tools backlinks export -> [Backlink]."""
    rows = _read_rows(path)
    if not rows:
        return []
    headers = rows[0]
    i_src = _find_col(headers, ["referring page url", "referring page", "source url"], default=0)
    i_tgt = _find_col(headers, ["target url", "link url"])
    i_anchor = _find_col(headers, ["anchor"])
    i_nofollow = _find_col(headers, ["nofollow", "link type", "type"])
    i_seen = _find_col(headers, ["first seen"])
    links = []
    for row in rows[1:]:
        if not row or i_src >= len(row) or not row[i_src].strip():
            continue

        def _cell(idx):
            return row[idx].strip() if idx is not None and idx < len(row) else ""

        nf_raw = _cell(i_nofollow).lower()
        links.append(Backlink(
            source_url=_cell(i_src),
            target_url=_cell(i_tgt),
            anchor=_cell(i_anchor),
            nofollow=nf_raw in ("true", "yes", "1", "nofollow"),
            first_seen=_cell(i_seen),
            origin="ahrefs",
        ))
    return links


def parse_bing(path):
    """Bing Webmaster Tools backlinks export -> [Backlink]."""
    rows = _read_rows(path)
    if not rows:
        return []
    headers = rows[0]
    i_src = _find_col(headers, ["source url", "source"], default=0)
    i_tgt = _find_col(headers, ["target url", "target"])
    i_anchor = _find_col(headers, ["anchor"])
    links = []
    for row in rows[1:]:
        if not row or not row[i_src].strip():
            continue

        def _cell(idx):
            return row[idx].strip() if idx is not None and idx < len(row) else ""

        links.append(Backlink(
            source_url=_cell(i_src),
            target_url=_cell(i_tgt),
            anchor=_cell(i_anchor),
            origin="bing",
        ))
    return links


def aggregate(site_counts, backlinks):
    """Merge site-level counts and link-level records into RefDomain rows."""
    domains = {}

    def _get(dom):
        if dom not in domains:
            domains[dom] = RefDomain(domain=dom)
        return domains[dom]

    for dom, (lp, tp) in (site_counts or {}).items():
        rd = _get(dom)
        rd.linking_pages = max(rd.linking_pages, lp)
        rd.target_pages = max(rd.target_pages, tp)
        rd.origins.add("gsc-sites")

    for bl in backlinks or []:
        dom = registrable_domain(bl.source_url)
        if not dom:
            continue
        rd = _get(dom)
        rd.total_links += 1
        if bl.nofollow:
            rd.nofollow_links += 1
        if bl.anchor:
            rd.anchors[bl.anchor.strip()[:80]] += 1
        rd.origins.add(bl.origin)
        host = hostname_of(bl.source_url)
        if host:
            rd.hostnames.add(host)
        if len(rd.sample_urls) < 5 and bl.source_url not in rd.sample_urls:
            rd.sample_urls.append(bl.source_url)
        if rd.linking_pages == 0:
            rd.linking_pages = rd.total_links

    return domains
