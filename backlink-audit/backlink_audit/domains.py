"""Registrable-domain extraction without external dependencies.

A tiny approximation of the Public Suffix List: enough for backlink
aggregation, where a wrong split on an exotic suffix costs one extra
row, not correctness of the audit.
"""

from urllib.parse import urlparse

# Common two-level public suffixes. A domain ending in one of these
# keeps three labels (example.co.uk), everything else keeps two.
TWO_LEVEL_SUFFIXES = {
    "co.uk", "org.uk", "ac.uk", "gov.uk", "me.uk", "net.uk",
    "com.au", "net.au", "org.au", "edu.au", "gov.au",
    "co.nz", "net.nz", "org.nz",
    "co.in", "net.in", "org.in", "gen.in", "firm.in",
    "com.br", "net.br", "org.br",
    "com.cn", "net.cn", "org.cn", "gov.cn",
    "com.tw", "org.tw", "idv.tw",
    "co.jp", "or.jp", "ne.jp", "ac.jp", "go.jp",
    "co.kr", "or.kr", "ne.kr",
    "com.mx", "org.mx", "net.mx",
    "com.ar", "com.co", "com.pe", "com.ve", "com.uy",
    "com.tr", "org.tr", "net.tr",
    "co.za", "org.za", "net.za", "web.za",
    "com.sg", "org.sg", "net.sg",
    "com.my", "org.my", "net.my",
    "com.hk", "org.hk", "net.hk",
    "com.ph", "org.ph", "net.ph",
    "com.vn", "net.vn", "org.vn",
    "com.pk", "net.pk", "org.pk",
    "com.bd", "net.bd", "org.bd",
    "com.ng", "org.ng", "net.ng",
    "com.eg", "org.eg", "net.eg",
    "com.sa", "org.sa", "net.sa",
    "com.ua", "net.ua", "org.ua", "in.ua",
    "com.pl", "net.pl", "org.pl",
    "co.il", "org.il", "net.il",
    "co.id", "or.id", "web.id",
    "co.th", "or.th", "in.th",
    "com.es", "org.es", "nom.es",
    "com.pt", "org.pt",
    "com.gr", "org.gr", "net.gr",
    "com.ro", "org.ro",
    "com.ru", "net.ru", "org.ru",
}


# Platforms where each subdomain is an independent site (public-suffix
# behavior). Collapsing these to the parent would aggregate unrelated
# blogs together and, worse, a disavow line would hit the whole platform.
SUBDOMAIN_SITES = {
    "blogspot.com", "wordpress.com", "weebly.com", "wixsite.com",
    "tumblr.com", "github.io", "gitlab.io", "netlify.app", "vercel.app",
    "pages.dev", "neocities.org", "000webhostapp.com", "web.app",
    "notion.site", "carrd.co", "substack.com",
}


def hostname_of(url_or_host: str) -> str:
    """Return the lowercase hostname from a URL or bare hostname."""
    s = (url_or_host or "").strip().lower()
    if not s:
        return ""
    if "://" not in s:
        s = "http://" + s
    host = urlparse(s).hostname or ""
    return host.strip(".")


def registrable_domain(url_or_host: str) -> str:
    """Collapse a URL or hostname to its registrable domain.

    https://blog.spam-site.co.uk/page -> spam-site.co.uk
    https://www.github.com/x          -> github.com
    """
    host = hostname_of(url_or_host)
    if not host:
        return ""
    labels = host.split(".")
    if len(labels) <= 2:
        return host
    last_two = ".".join(labels[-2:])
    if last_two in TWO_LEVEL_SUFFIXES or last_two in SUBDOMAIN_SITES:
        return ".".join(labels[-3:])
    return last_two


def subdomain_of(url_or_host: str) -> str:
    """Return the full hostname (used to detect free-host platforms)."""
    return hostname_of(url_or_host)
