"""Network enrichment for referring domains. All checks are best-effort:
a failed lookup marks the field unknown (None) and never crashes the audit.

Checks:
- DNS resolution and IP collection (link-network clustering input)
- HTTP liveness (HEAD, https then http fallback)
- Spamhaus DBL listing via DNS (with open-resolver false-positive guard)
- Open PageRank score (free API key from domcop.com/openpagerank,
  1000 requests/day, 100 domains per request)
"""

import json
import socket
import ssl
import urllib.request
import urllib.error
import urllib.parse

OPR_ENDPOINT = "https://openpagerank.com/api/v1.0/getPageRank"


def resolve_domain(domain, timeout=5):
    """Return (resolves: bool, ips: list)."""
    try:
        socket.setdefaulttimeout(timeout)
        infos = socket.getaddrinfo(domain, None, proto=socket.IPPROTO_TCP)
        ips = sorted({i[4][0] for i in infos})
        return True, ips
    except (socket.gaierror, socket.timeout, OSError):
        return False, []


def http_status(domain, timeout=8):
    """Return an int HTTP status, or None when unreachable."""
    ctx = ssl.create_default_context()
    for scheme in ("https", "http"):
        url = f"{scheme}://{domain}/"
        req = urllib.request.Request(url, method="HEAD", headers={
            "User-Agent": "Mozilla/5.0 (compatible; DedaubBacklinkAudit/0.1)"
        })
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                return resp.status
        except urllib.error.HTTPError as e:
            return e.code
        except Exception:
            continue
    return None


def spamhaus_dbl(domain, timeout=5):
    """Check the Spamhaus Domain Block List via DNS.

    Returns True (listed), False (not listed) or None (unknown).
    127.0.1.x   -> listed (spam / phish / malware / abused domain)
    127.255.255.x -> query refused (public resolver blocked); unknown.
    NXDOMAIN    -> not listed.
    """
    try:
        socket.setdefaulttimeout(timeout)
        addr = socket.gethostbyname(f"{domain}.dbl.spamhaus.org")
        if addr.startswith("127.255."):
            return None
        if addr.startswith("127.0.1."):
            return True
        return None
    except socket.gaierror:
        return False
    except (socket.timeout, OSError):
        return None


def open_pagerank(domains, api_key, timeout=15, log=None):
    """Fetch Open PageRank scores (0-10) for up to any number of domains.

    Batches 100 domains per request. Returns {domain: float | None}.
    """
    scores = {}
    domains = list(domains)
    for start in range(0, len(domains), 100):
        batch = domains[start:start + 100]
        qs = "&".join("domains[]=" + urllib.parse.quote(d) for d in batch)
        req = urllib.request.Request(
            f"{OPR_ENDPOINT}?{qs}", headers={"API-OPR": api_key})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            for item in payload.get("response", []):
                dom = item.get("domain", "")
                try:
                    scores[dom] = float(item.get("page_rank_decimal") or 0.0)
                except (TypeError, ValueError):
                    scores[dom] = None
        except Exception as e:
            if log:
                log(f"open_pagerank batch failed: {e}")
            for d in batch:
                scores.setdefault(d, None)
    return scores


def enrich_domains(domains, opr_key=None, skip_http=False, skip_dbl=False,
                   log=None):
    """Run all enrichment passes over {domain: RefDomain}, in place.

    Also computes shared-IP clusters and stores the cluster size in
    rd.ips ordering-independent form via the returned ip_counts map.
    """
    def _log(msg):
        if log:
            log(msg)

    names = sorted(domains.keys())

    for i, name in enumerate(names):
        rd = domains[name]
        rd.resolves, rd.ips = resolve_domain(name)
        if rd.resolves and not skip_http:
            rd.http_status = http_status(name)
        if not skip_dbl:
            rd.dbl_listed = spamhaus_dbl(name)
        if (i + 1) % 25 == 0:
            _log(f"enriched {i + 1}/{len(names)} domains")

    if opr_key:
        scores = open_pagerank(names, opr_key, log=log)
        for name in names:
            domains[name].opr = scores.get(name)

    # Link-network signal: how many audited domains share each IP
    ip_counts = {}
    for rd in domains.values():
        for ip in rd.ips:
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
    return ip_counts
