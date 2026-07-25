"""Dedaub backlink audit: free replacement for the Semrush Backlink Audit.

Ingests backlink exports from Google Search Console, Ahrefs Webmaster
Tools and Bing Webmaster Tools, enriches referring domains with free
open-data signals (DNS, HTTP, Open PageRank, Spamhaus DBL), scores each
domain for toxicity on a 0-100 scale, and produces a markdown report
plus a reviewed-before-upload disavow candidate file.

Stdlib only: no third-party dependencies.
"""

__version__ = "0.1.0"
