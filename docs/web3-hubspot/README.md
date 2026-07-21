# Web3 × HubSpot Add-on Line — Product Research

Internal product-strategy research for a new Dedaub product line: **HubSpot add-ons sold to
the Web3-native companies already using HubSpot as their CRM.**

## Thesis

Web3 teams keep HubSpot as their system of record, but HubSpot can't see the rails Web3
actually runs on — wallets, Telegram, Discord, GitHub, on-chain signals, pseudonymous
identity. That gap is the product. Rather than one platform, we build a line of cheap,
single-problem add-ons (one pain each) distributed through the HubSpot Marketplace to a
concentrated, reachable market of ~2,000 accounts.

## Documents

| # | Doc | What it covers |
|---|-----|----------------|
| 00 | [Market sizing](./00-market-sizing.md) | How many Web3 companies use HubSpot; the ~2,000 ICP |
| 01 | [Market needs](./01-market-needs.md) | The 5 gaps HubSpot leaves for Web3, with sources |
| 02 | [Add-on portfolio](./02-addon-portfolio.md) | 11 single-problem add-ons (Know→Find→Time→Reach) |
| 03 | [Multichannel Campaign — brief](./03-multichannel-campaign-brief.md) | Product/feature description + end-to-end routine + 8-vendor competitive analysis |
| 04 | [Multichannel Campaign — MVP PRD](./04-multichannel-campaign-prd.md) | The MVP spec (email + Telegram + X, supervised agent) |
| 05 | [Buying Signal Trigger](./05-buying-signal-trigger.md) | Consolidated lead-discovery orchestrator + end-to-end routine (discovery → activation) |

Visual one-pager (HTML) versions of docs 02–05 live in [`artifacts/`](./artifacts/) — open
them in a browser for the styled, theme-aware layouts.

## Decisions locked so far

- **Positioning:** HubSpot-native, "stay on HubSpot" — no rip-and-replace. Displace the weak
  marketplace incumbent (NisWire). Distribute via the HubSpot Marketplace.
- **Data strategy:** enrichment-only (Clay / Apollo / DeFiLlama + the customer's own HubSpot
  data). No proprietary contact database.
- **Lead product:** Multichannel Campaign — supervised AI agent; MVP channels **email +
  Telegram + X**; Discord + LinkedIn deferred to phase 2.
- **Lead discovery:** consolidated into one orchestrator, **Buying Signal Trigger**, sitting
  upstream of the campaign.

_Last updated: Jul 2026._
