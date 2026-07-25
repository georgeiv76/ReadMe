"""Toxicity scoring engine.

Replicates the shape of the Semrush Backlink Audit Toxicity Score with
signals computable from free data. Score range 0-100, thresholds match
the Semrush convention:

    0-44   healthy
    45-59  review (potentially toxic)
    60-100 toxic

Overall profile bands also follow the Semrush convention:
    toxic share > 10%  -> HIGH
    toxic share 3-10%  -> MEDIUM
    toxic share < 3%   -> LOW

Every fired signal is recorded as a human-readable marker so the report
can explain each score. Weights and lists live in DEFAULT_CONFIG and can
be overridden with a JSON file (--config).
"""

import re

DEFAULT_CONFIG = {
    # Domains that can never be flagged. Big platforms plus known-good
    # Web3 media and ecosystem domains that link to dedaub.com today.
    "whitelist": [
        "github.com", "twitter.com", "x.com", "linkedin.com", "medium.com",
        "reddit.com", "youtube.com", "facebook.com", "wikipedia.org",
        "substack.com", "mirror.xyz", "stackexchange.com", "stackoverflow.com",
        "ethereum.org", "ethereum.foundation", "chain.link", "uniswap.org",
        "coindesk.com", "cointelegraph.com", "theblock.co", "decrypt.co",
        "hackernoon.com", "dlnews.com", "blockworks.co", "immunefi.com",
        "alchemy.com", "arxiv.org", "acm.org", "ieee.org", "sigplan.org",
        "google.com", "bing.com", "duckduckgo.com", "npmjs.com", "pypi.org",
    ],
    # Freenom free-registration TLDs: near-zero legitimate use
    "freenom_tlds": ["tk", "ml", "ga", "cf", "gq"],
    # High-abuse TLDs (Spamhaus and industry abuse rankings)
    "spam_tlds": [
        "xyz", "top", "icu", "click",
        "work", "loan", "men", "date", "stream", "review", "party",
        "trade", "bid", "win", "accountant", "science", "racing",
        "download", "cricket", "faith", "rest", "cyou", "sbs", "cfd",
        "bond", "beauty", "hair", "skin", "makeup", "quest", "monster",
        "buzz", "lol", "pics", "mom", "zip",
    ],
    # Spam commerce keywords: in a linking domain name or anchor text
    "spam_keywords": [
        "casino", "porn", "xxx", "viagra", "cialis", "escort", "betting",
        "slots", "poker", "pills", "replica", "jersey", "payday",
        "essay-writ", "adult", "dating-", "-dating", "pharma", "vape",
        "steroid", "gambl", "sexcam", "loans",
    ],
    # Free-host platforms: mild signal, spam is cheap there
    "free_hosts": [
        "blogspot.", ".wordpress.com", ".weebly.com", ".wixsite.com",
        ".tumblr.com", ".webnode.", ".jimdo", ".000webhostapp.com",
        ".rf.gd", ".epizy.com", ".netlify.app", ".vercel.app",
        ".github.io", ".pages.dev", ".neocities.org",
    ],
    "weights": {
        "FREENOM_TLD": 25,
        "SPAM_TLD": 18,
        "SPAM_KEYWORD_DOMAIN": 22,
        "SPAM_KEYWORD_ANCHOR": 15,
        "FREE_HOST": 8,
        "PUNYCODE": 10,
        "MANY_HYPHENS": 8,
        "DIGIT_HEAVY": 8,
        "LONG_DOMAIN": 5,
        "SITEWIDE": 15,
        "SITEWIDE_EXTREME": 22,
        "NONLATIN_ANCHOR": 6,
        "NO_DNS": 12,
        "HTTP_DEAD": 8,
        "OPR_MISSING": 12,
        "OPR_LOW": 8,
        "DR_ZERO": 10,
        "DBL_LISTED": 40,
        "SHARED_IP_CLUSTER": 15,
    },
    # A domain with real authority is capped below toxic unless it is
    # on the Spamhaus DBL
    "authority_cap_opr": 4.0,
    "authority_cap_dr": 40.0,
    "authority_cap_score": 30,
    "thresholds": {"toxic": 60, "review": 45},
    "profile_bands": {"high": 0.10, "medium": 0.03},
}


def load_config(path=None):
    import json
    cfg = {k: (dict(v) if isinstance(v, dict) else list(v) if isinstance(v, list) else v)
           for k, v in DEFAULT_CONFIG.items()}
    if path:
        with open(path, "r", encoding="utf-8") as fh:
            user = json.load(fh)
        for key, val in user.items():
            if isinstance(val, dict) and isinstance(cfg.get(key), dict):
                cfg[key].update(val)
            else:
                cfg[key] = val
    return cfg


_NONLATIN = re.compile(r"[Ѐ-ӿ؀-ۿ一-鿿぀-ヿ가-힯]")


def _is_whitelisted(domain, cfg):
    return any(domain == w or domain.endswith("." + w) for w in cfg["whitelist"])


def score_domain(rd, cfg, ip_counts=None):
    """Score one RefDomain in place. Returns the domain for chaining."""
    w = cfg["weights"]
    rd.markers = []
    rd.score = 0

    if _is_whitelisted(rd.domain, cfg):
        rd.markers.append("WHITELISTED: known-good platform or partner domain")
        rd.bucket = "healthy"
        return rd

    def fire(key, detail):
        rd.score += w[key]
        rd.markers.append(f"{key}: {detail}")

    name = rd.domain.rsplit(".", 1)[0]
    tld = rd.domain.rsplit(".", 1)[-1]

    # -- domain-name signals (always available, offline)
    if tld in cfg["freenom_tlds"]:
        fire("FREENOM_TLD", f".{tld} is a free-registration TLD (near-total abuse)")
    elif tld in cfg["spam_tlds"]:
        fire("SPAM_TLD", f".{tld} is a high-abuse TLD")
    for kw in cfg["spam_keywords"]:
        if kw.strip("-") in rd.domain:
            fire("SPAM_KEYWORD_DOMAIN", f"'{kw.strip('-')}' in domain name")
            break
    for host in (rd.hostnames or {rd.domain}):
        if any(fh in host for fh in cfg["free_hosts"]):
            fire("FREE_HOST", f"free-host platform ({host})")
            break
    if rd.domain.startswith("xn--") or ".xn--" in rd.domain:
        fire("PUNYCODE", "punycode / lookalike domain")
    if name.count("-") >= 3:
        fire("MANY_HYPHENS", f"{name.count('-')} hyphens in name")
    digits = sum(c.isdigit() for c in name)
    if name and digits / len(name) > 0.25:
        fire("DIGIT_HEAVY", "digit-heavy domain name")
    if len(name) > 25:
        fire("LONG_DOMAIN", f"{len(name)}-char domain name")

    # -- link-pattern signals (from the exports)
    if rd.linking_pages >= 1000 and rd.target_pages <= 2:
        fire("SITEWIDE_EXTREME",
             f"{rd.linking_pages} linking pages to {max(rd.target_pages, 1)} target(s): sitewide footprint")
    elif rd.linking_pages >= 100 and rd.target_pages <= 2:
        fire("SITEWIDE",
             f"{rd.linking_pages} linking pages to {max(rd.target_pages, 1)} target(s)")

    anchor_text = " ".join(rd.anchors.keys()).lower()
    for kw in cfg["spam_keywords"]:
        if kw.strip("-") in anchor_text:
            fire("SPAM_KEYWORD_ANCHOR", f"'{kw.strip('-')}' in anchor text")
            break
    if anchor_text and _NONLATIN.search(anchor_text):
        fire("NONLATIN_ANCHOR", "non-Latin anchor text (unexpected for dedaub.com)")

    # -- enrichment signals (only when enrichment ran; None = unknown)
    if rd.resolves is False:
        fire("NO_DNS", "domain no longer resolves (dead link weight)")
    if rd.http_status is not None and isinstance(rd.http_status, int) and rd.http_status >= 400:
        fire("HTTP_DEAD", f"site returns HTTP {rd.http_status}")
    if rd.opr is not None:
        if rd.opr <= 0.05:
            fire("OPR_MISSING", "no Open PageRank authority (unknown to Common Crawl)")
        elif rd.opr < 1.5:
            fire("OPR_LOW", f"Open PageRank {rd.opr:.1f}/10")
    elif rd.dr is not None and rd.dr <= 0.5:
        # only when OPR was unavailable, to avoid double-punishing
        fire("DR_ZERO", "Domain Rating 0 (Domain Rating by Ahrefs)")
    if rd.dbl_listed is True:
        fire("DBL_LISTED", "listed on the Spamhaus Domain Block List")
    if ip_counts and rd.ips:
        shared = max((ip_counts.get(ip, 0) for ip in rd.ips), default=0)
        if shared >= 4:
            fire("SHARED_IP_CLUSTER",
                 f"shares an IP with {shared - 1} other referring domains (link network)")

    # -- dampeners
    if rd.total_links and rd.nofollow_links == rd.total_links:
        rd.score = max(0, rd.score - 10)
        rd.markers.append("ALL_NOFOLLOW: every observed link is nofollow (-10)")
    has_authority = ((rd.opr is not None and rd.opr >= cfg["authority_cap_opr"])
                     or (rd.dr is not None and rd.dr >= cfg["authority_cap_dr"]))
    if has_authority and rd.dbl_listed is not True:
        if rd.score > cfg["authority_cap_score"]:
            rd.score = cfg["authority_cap_score"]
            src = (f"Open PageRank {rd.opr:.1f}" if rd.opr is not None
                   and rd.opr >= cfg["authority_cap_opr"]
                   else f"Domain Rating {rd.dr:.0f}")
            rd.markers.append(
                f"AUTHORITY_CAP: {src} caps score at {cfg['authority_cap_score']}")

    rd.score = min(100, rd.score)
    th = cfg["thresholds"]
    rd.bucket = ("toxic" if rd.score >= th["toxic"]
                 else "review" if rd.score >= th["review"]
                 else "healthy")
    return rd


def score_all(domains, cfg, ip_counts=None):
    for rd in domains.values():
        score_domain(rd, cfg, ip_counts)
    return domains


def profile_summary(domains, cfg):
    total = len(domains) or 1
    toxic = sum(1 for r in domains.values() if r.bucket == "toxic")
    review = sum(1 for r in domains.values() if r.bucket == "review")
    share = toxic / total
    bands = cfg["profile_bands"]
    level = ("HIGH" if share > bands["high"]
             else "MEDIUM" if share >= bands["medium"]
             else "LOW")
    return {
        "total_domains": len(domains),
        "toxic": toxic,
        "review": review,
        "healthy": len(domains) - toxic - review,
        "toxic_share": round(share, 4),
        "profile_toxicity": level,
    }
