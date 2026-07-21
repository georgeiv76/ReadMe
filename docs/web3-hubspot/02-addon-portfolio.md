# 02 · Add-on Portfolio — 11 single-problem add-ons

Each Dedaub orchestrator we've built becomes a **single-problem add-on** (one pain each — the
sales principle for cheap, impulse-grade products). Organized along the Web3 GTM funnel:
**Know → Find → Time → Reach.**

## Why many small add-ons, not one suite

A buyer approving a $30–80/mo tool decides in minutes on one obvious pain — not a platform
migration. One problem per add-on keeps the pitch legible, the trial short, and the "yes"
cheap. Land one, expand into the rest.

## The add-ons

### Know — identity & profiling
| Add-on | One problem | Built from |
|---|---|---|
| **Web3 Enrich** | Thin contact → full Web3 profile (wallets, handles, chains, TVL, raise, stack) | clay-waterfall · web3-osint · hubspot-crm-ref |
| **CRM Cleaner** *(free wedge)* | Same founder in HubSpot 3× under 3 handles | hubspot-crm-ref (handle QA · enum log · dedup) |

### Find — sourcing net-new accounts
| Add-on | One problem | Built from |
|---|---|---|
| **Stack Finder** | Can't ask HubSpot "who runs Chainlink oracles / forked Aave" | apollo-technographics · tokin · allium finders |
| **ICP Score** | Reps waste time on bad-fit leads | hubspot-crm-ref (ICP scoring · target-account field) |

### Time — signal-triggered leads
| Add-on | One problem | Built from |
|---|---|---|
| **Raise Radar** | Hear about a raise too late | defillama-raise-campaign · grant-hunter |
| **Ship Signal** | Miss when a protocol ships / deploys | defi-security-intel (monitoring) · defillama-github-extract |
| **Risk Trigger** ⭐ *moat* | Turn on-chain security events into sales leads | defi-security-intel · protocol-internals · evm-trace |

### Reach — activation on Web3 channels
| Add-on | One problem | Built from |
|---|---|---|
| **Multichannel Campaign** *(centerpiece)* | Company/list → coordinated play across email · Telegram · Discord · X · LinkedIn, with warming (follow/like/connect/react) | cold-outreach · context-blocks · enrich · telegram-hub · discord-hub |
| **Telegram Hub** | All Telegram in one place: log inbound + DM/group/follow outbound | tg-finder · tg-hubspot-backfill |
| **Discord Hub** *(net-new build)* | All Discord: log + DM/server-post/join/react | web3-osint · patterned on Telegram Hub |
| **Proof Loop** | Tie campaigns to on-chain actions (cookieless, wallet-aware) | dedaub-gtm · traffic-investigation · ga-gsc-gtm-report |

⭐ **Risk Trigger is the moat** — on-chain security signals are the one thing no generic Web3
CRM (Formo, CRMChat, Entergram) can structurally copy, because they lack Dedaub's audit /
EVM-trace engine. It doubles as a feed for Dedaub's own audit pipeline.

## Sequencing

1. **Land** (already built, broad pain): CRM Cleaner (free wedge) → Web3 Enrich → Telegram Hub
2. **Value** (turn install into pipeline): Raise Radar → Stack Finder → ICP Score
3. **Activate** (reach & prove): Multichannel Campaign → Discord Hub → Ship Signal
4. **Moat** (only Dedaub can build): Risk Trigger → Proof Loop

## Pricing posture

- $20–80/mo self-serve per add-on (impulse-grade)
- CRM Cleaner free → paid, as the marketplace front door
- Risk Trigger & Proof Loop priced premium (no substitute)
- Bundle the full line at a discount once ≥3 land

## Compliance reality check

Auto-follow / auto-like / auto-connect / bulk-DM run against LinkedIn's, X's, Telegram's and
Discord's terms — those platforms ban aggressive automation. Buildable and sellable, but only
with human-in-the-loop approval, rate limits, warm-up and account rotation. Sell "likes &
connects at scale" as **assisted**, not autonomous.
