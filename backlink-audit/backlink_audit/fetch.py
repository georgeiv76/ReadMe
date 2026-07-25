"""API fetchers for fully autonomous runs: no manual exports, no CSVs.

Sources:
- Ahrefs API v3 (paid key, any plan Lite and up), all-backlinks endpoint.
  Unit frugality is a design goal: minimal field select, one link per
  referring domain by default, single request per run.
- Bing Webmaster Tools API (free key from Bing Webmaster settings).
  GetLinkCounts lists linked pages, GetUrlLinks returns the sources
  per page. Known caveat: some accounts get empty results even for
  verified sites; treat as best-effort supplement.

Every fetcher returns the same Backlink records the CSV parsers
produce, so downstream aggregation and scoring do not care where the
data came from. All failures degrade to an empty list plus a logged
reason; an API outage must never kill the monthly audit.
"""

import json
import urllib.error
import urllib.parse
import urllib.request

from .ingest import Backlink

AHREFS_ENDPOINT = "https://api.ahrefs.com/v3/site-explorer/all-backlinks"
# 5 cheap fields: ~5 units/row + 50 base per request
AHREFS_DEFAULT_SELECT = "url_from,url_to,anchor,is_nofollow,first_seen_link"
BING_ENDPOINT = "https://ssl.bing.com/webmaster/api.svc/json/"


def _get_json(url, headers=None, timeout=60):
    """Return (payload, error). Error strings include the response body
    so a wrong field name or plan limit is self-explaining in the log."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "replace")[:400]
        except Exception:
            body = ""
        return None, f"HTTP {e.code} {body}".strip()
    except Exception as e:
        return None, str(e)


# ---------------------------------------------------------------- Ahrefs

def parse_ahrefs_payload(payload):
    rows = (payload.get("backlinks") or payload.get("items")
            or payload.get("data") or [])
    links = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        src = row.get("url_from") or ""
        if not src:
            continue
        links.append(Backlink(
            source_url=src,
            target_url=row.get("url_to") or "",
            anchor=row.get("anchor") or "",
            nofollow=bool(row.get("is_nofollow")),
            first_seen=str(row.get("first_seen_link")
                           or row.get("first_seen") or ""),
            origin="ahrefs-api",
        ))
    return links


def fetch_ahrefs(target, token, mode="subdomains", limit=2000,
                 select=AHREFS_DEFAULT_SELECT, aggregation="1_per_domain",
                 log=None):
    """One request against /v3/site-explorer/all-backlinks.

    mode=subdomains covers dedaub.com plus app./docs./tokin. in one
    call, matching the GSC domain-property scope. If the aggregation
    value is rejected by the API, retries once without it.
    """
    def _log(msg):
        if log:
            log(msg)

    params = {"target": target, "mode": mode, "limit": str(limit),
              "select": select, "output": "json"}
    if aggregation:
        params["aggregation"] = aggregation
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/json"}

    payload, err = _get_json(
        AHREFS_ENDPOINT + "?" + urllib.parse.urlencode(params), headers)
    if err and aggregation and "401" not in err:
        _log(f"ahrefs-api: {err}; retrying without aggregation")
        params.pop("aggregation")
        payload, err = _get_json(
            AHREFS_ENDPOINT + "?" + urllib.parse.urlencode(params), headers)
    if err:
        _log(f"ahrefs-api: FAILED: {err}")
        if "401" in err:
            _log("ahrefs-api: 401 = key rejected by Ahrefs. Check that "
                 "(1) the subscription includes API v3 (Lite plan or "
                 "higher; the free plan has no API), and (2) the key was "
                 "generated under Account settings, API keys. Regenerate "
                 "the key and retry.")
        return []
    links = parse_ahrefs_payload(payload)
    _log(f"ahrefs-api: {len(links)} backlinks for {target} (mode={mode})")
    return links


# ------------------------------------------------------------------ Bing

def _bing_call(method, apikey, params, timeout=30):
    qs = {"apikey": apikey}
    qs.update(params)
    return _get_json(BING_ENDPOINT + method + "?" + urllib.parse.urlencode(qs))


def _bing_body(payload):
    return payload.get("d", payload) if isinstance(payload, dict) else {}


def parse_bing_link_counts(payload):
    body = _bing_body(payload)
    out = []
    for item in body.get("Links") or []:
        if isinstance(item, dict) and item.get("Url"):
            out.append((item["Url"], int(item.get("Count") or 0)))
    return out


def parse_bing_url_links(payload):
    body = _bing_body(payload)
    return [item.get("Url") for item in (body.get("Details") or [])
            if isinstance(item, dict) and item.get("Url")]


def parse_bing_user_sites(payload):
    """GetUserSites -> list of registered site URLs. The 'd' body can be
    a bare list or a dict wrapper depending on API version."""
    body = payload.get("d", payload) if isinstance(payload, dict) else payload
    if isinstance(body, dict):
        body = body.get("Sites") or body.get("sites") or []
    urls = []
    for item in body or []:
        if isinstance(item, dict) and item.get("Url"):
            urls.append(item["Url"])
        elif isinstance(item, str):
            urls.append(item)
    return urls


def fetch_bing(site_url, apikey, max_count_pages=5, max_target_pages=25,
               log=None):
    """Inbound links via GetLinkCounts + GetUrlLinks (free API).

    Bounded to max_count_pages listing calls and max_target_pages
    per-page source lookups, so a run costs at most ~30 requests.
    If the first pass returns nothing, asks GetUserSites which site
    URLs the key can actually see and retries with the registered form
    (catches https:// vs http:// vs www. mismatches automatically).
    """
    def _log(msg):
        if log:
            log(msg)

    def _collect(surl):
        targets, page = [], 0
        while page < max_count_pages:
            payload, err = _bing_call("GetLinkCounts", apikey,
                                      {"siteUrl": surl, "page": page})
            if err:
                _log(f"bing-api GetLinkCounts p{page}: {err}")
                break
            rows = parse_bing_link_counts(payload)
            if not rows:
                break
            targets += rows
            total = int(_bing_body(payload).get("TotalPages") or 1)
            page += 1
            if page >= total:
                break
        targets.sort(key=lambda t: -t[1])
        links = []
        for turl, _count in targets[:max_target_pages]:
            payload, err = _bing_call("GetUrlLinks", apikey,
                                      {"siteUrl": surl, "link": turl,
                                       "page": 0})
            if err:
                _log(f"bing-api GetUrlLinks {turl}: {err}")
                continue
            for src in parse_bing_url_links(payload):
                links.append(Backlink(source_url=src, target_url=turl,
                                      origin="bing-api"))
        return targets, links

    targets, links = _collect(site_url)

    if not targets:
        payload, err = _bing_call("GetUserSites", apikey, {})
        if err:
            _log(f"bing-api GetUserSites: {err}")
        else:
            from .domains import registrable_domain
            sites = parse_bing_user_sites(payload)
            if not sites:
                _log("bing-api: this key sees NO sites. Fix: in Bing "
                     "Webmaster Tools add dedaub.com (use 'Import from "
                     "Google Search Console'), then re-run.")
            else:
                _log("bing-api: key has access to: " + ", ".join(sites))
                want = registrable_domain(site_url)
                for reg in sites:
                    if (registrable_domain(reg) == want
                            and reg.rstrip("/") != site_url.rstrip("/")):
                        _log(f"bing-api: retrying with registered site "
                             f"URL {reg}")
                        targets, links = _collect(reg)
                        break

    _log(f"bing-api: {len(links)} backlinks from "
         f"{min(len(targets), max_target_pages)} linked pages")
    if not targets:
        _log("bing-api: still empty. If the site IS verified in Bing "
             "Webmaster Tools, this is the known Microsoft issue where "
             "the link API returns empty data for some accounts.")
    return links
