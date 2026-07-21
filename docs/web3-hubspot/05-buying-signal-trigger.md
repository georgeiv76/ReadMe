# 05 · Buying Signal Trigger — Lead Discovery Orchestrator

The consolidated lead-discovery engine. It watches every Web3 signal that means "this company
is worth talking to now," turns each into a scored, HubSpot-ready lead, and hands it to the
Multichannel Campaign. **One engine — replacing four separate discovery add-ons.**

## 0 · In plain terms

This is the **find** half of a two-engine system:

- **Buying Signal Trigger (this doc)** — finds *who* to contact and *why today*.
- **Multichannel Campaign** — does the *reaching out*, across email + Telegram + X.

```
Buying Signal Trigger  →  HubSpot  →  Multichannel Campaign
  (find + why-now)         (record)      (warm + reach out)
```

The "why now" this engine produces becomes the opener the campaign sends. Discovery feeds
activation — the two run as **one routine** (see §6).

## 1 · The idea: one engine, not four add-ons

A lead is rarely one signal. It's the convergence of **fit** (does this account match us),
**timing** (is something happening now), and **risk** (is there a reason to talk today).

> **Stack Finder + Raise Radar + Ship Signal + Risk Trigger → Buying Signal Trigger.**

It sits **upstream of the Multichannel Campaign** — discovery feeds activation.

## 2 · The signal taxonomy (all our lead-discovery knowledge)

Seven families. *Fit* signals say **who**; *timing* signals say **when**. Each maps to an
orchestrator we already run.

| Family | Type | Signals | Built from |
|---|---|---|---|
| 🧩 Fit / technographic | fit | runs a chain/oracle/bridge/tool; uses a competitor; matches ICP size/stage/vertical | apollo · tokin-competitor-finder · allium-customer-finder |
| 💰 Funding | timing | raise (pre-seed→Series X); grant/ecosystem program; treasury top-up | defillama-raise-campaign · grant-hunter |
| 🚢 Build / shipping | timing | GitHub release / commit spike / new repo; new contract deployment; upgrade change | defi-security-intel (monitoring) · defillama-github-extract |
| 🛡️ Security / risk **(moat)** | timing | unaudited deployment; fork of audited code; live incident/exploit; audit gone stale | defi-security-intelligence · evm-trace-intelligence · protocol-internals |
| 📈 On-chain / traction | timing | TVL surge/drop; token launch; user/volume growth | defillama · on-chain data |
| 👔 Hiring / intent | timing | hiring BD/security/growth/devrel; job-post spike; key-person move | apollo-job-postings · web3-osint |
| 💬 Community / social | fit+timing | Telegram/Discord/X growth & engagement; announcement spike | tg-finder · web3-osint |
| 🎯 Convergence | meta | two+ signals on one account in a window (e.g. raise + hiring-security + unaudited deploy) | the orchestrator itself |

🛡️ The **security/risk family is the Dedaub moat** — no generic Web3 CRM can build it.

## 3 · The pipeline

`detect → enrich → resolve → score → dedupe → emit`

1. **Detect** — a signal fires from any family.
2. **Enrich** — append company, contacts, wallets, handles, context.
3. **Resolve** — identity resolution: one company, real people, clean handles.
4. **Score** — `priority = ICP fit × signal strength × recency`.
5. **Dedupe** — check vs existing HubSpot records; merge, don't duplicate.
6. **Emit** — create/update the HubSpot lead + "why now" + recommended play.

## 4 · What it emits, and how it ranks

**Anatomy of an emitted lead:** company (+domain, deduped) · contacts (+email/TG/X handles) ·
triggering signal(s) + timestamp · **"why now"** one-liner · priority tier (A/B/C) ·
recommended play/channel · handoff link into HubSpot → Multichannel Campaign.

**Score:** `priority = ICP fit × signal strength × recency`
- **ICP fit** — does the account match (chain, size, stage, tech)?
- **Signal strength** — how strongly does the event predict a buy? (a raise > a commit)
- **Recency** — fresh events outrank stale ones.
- **Convergence multiplier** — two+ signals on one account in a window jump to the top. A raise
  + hiring-security + unaudited-deploy is an A-lead every time.

## 5 · Built from what we already run

Fit → apollo · tokin · allium. Funding → defillama-raise · grant-hunter. Build → defi-security-intel
· github-extract. Security → defi-security-intel · evm-trace · protocol-internals. Enrich/resolve/score
→ clay-waterfall · web3-osint · hubspot-crm-ref (ICP scoring). Emit/dedupe/sync → hubspot-crm-ref ·
tg-finder. **The orchestrator is glue + scoring over orchestrators that already exist.**

## 6 · The end-to-end routine (discovery → activation)

The orchestrator runs as **one repeatable routine**, not a set of manual steps. On each cycle:

1. **Scan** — poll every signal source (§2) for new events (continuous, or on a schedule).
2. **Detect → Enrich → Resolve → Score → Dedupe → Emit** — run the pipeline (§3) on each hit.
3. **Rank** — order emitted leads A/B/C by the priority score (§4), boosting convergence.
4. **Hand off** — push each qualified lead into HubSpot with its **"why now"**, and (optionally)
   auto-trigger the **Multichannel Campaign** with the recommended play as the opener.
5. **Learn** — record which signals/plays converted, and feed that back into scoring.

```
[ scan sources ] → [ pipeline: enrich·resolve·score·dedupe ] → [ rank A/B/C ]
        → HubSpot lead (+ why-now) → Multichannel Campaign (warm + reach)
        → outcomes feed back into scoring
```

**Cadence:** continuous for high-value signals (security/risk, raises), scheduled scans for the
rest — a cost/coverage trade-off to settle (see §7). Two halves of one motion, both
HubSpot-native, agent-driven, enrichment-powered — worth more together than apart, but each
still sells alone.

## 7 · Open questions

- One product or tiers (fit / +timing / +security-moat)?
- Security-signal family: customer feature, or Dedaub's own pipeline engine?
- Real-time monitoring (costly) vs scheduled scans (cheaper, slower to fire)?
- Show the customer the score math, or keep it a black box?
