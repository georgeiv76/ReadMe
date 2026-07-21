# 04 · Multichannel Campaign — MVP PRD (v1)

**Status:** Draft for review · **Version:** 1.0 (Jul 2026) · **Owner:** Giorgio B., Dedaub
**MVP channels:** Email · Telegram · X · **Deploy:** HubSpot Marketplace app · **Agent:** Supervised (HITL)

## 1 · Summary & strategy

A HubSpot Marketplace add-on that lets a Web3 growth/BD team launch one coordinated outreach
play across **email, Telegram and X** — including the *warming* actions (follow, like, join)
that precede a cold message — with an **AI agent doing the work under human supervision**, and
every touch logged back to HubSpot as the system of record.

Decided direction:
- **Positioning — "stay on HubSpot."** Distribute via the marketplace to the ~2,000 ICP;
  displace NisWire (Telegram-only, no agent, no warming).
- **Data — enrichment, not a database.** Fuel is the customer's own HubSpot data, enriched on
  demand (Clay / Apollo / DeFiLlama). No proprietary contact DB.
- **Agent — supervised.** Human-in-the-loop by default. Warming ships as *assisted*.

> One-line pitch: "Run email + Telegram + X campaigns from inside HubSpot — warmed,
> personalized, and supervised — without leaving your CRM."

## 2 · Goals & non-goals

**In scope (v1):** marketplace app (OAuth); campaigns across email/TG/X; warming (X follow/like,
TG join); on-demand enrichment; supervised agent (plan→act→reply) with approval queue; two-way
HubSpot sync + timeline logging; per-account rate limits/warm-up/opt-out; unified inbox + basic
reporting.

**Deferred:** Discord & LinkedIn (phase 2); proprietary contact DB; conversation-trained model;
fully-autonomous sending; on-chain attribution (Proof Loop); voice/SMS/WhatsApp.

**Primary goal:** a Web3 growth lead launches a warmed, personalized, 3-channel campaign to a
HubSpot list in < 15 min, approves each sensitive touch in one click, sees every interaction in
HubSpot — with zero account bans.

## 3 · Target user & ICP

Head of Growth / BD / Community at a Web3-native company, 11–200 employees, already on HubSpot.
Beachhead = teams currently forcing NisWire or manual Telegram/X outreach. Pricing (context
only): self-serve, impulse-grade, with a free/cheap front-door tier.

## 4 · User stories

Launch (3-channel campaign from a list) · Warm (follow/like/join before DM) · Supervise
(approve/edit/skip in one click) · Personalize (from on-chain/social context) · Trigger
(auto-start on a raise/ship) · Reply (one inbox, logged to HubSpot, hot leads routed) · Trust
(HubSpot stays the source of truth).

## 5 · Scope & channel actions (v1)

| Channel | Messaging | Warming (assisted) | Connector notes |
|---|---|---|---|
| Email | send, sequence, follow-up | — | customer sending domain/ESP; deliverability |
| Telegram | DM, group message | join group/channel | multi-account, warm-up, rotation |
| X | reply, DM | follow, like | API + automation limits; per-account caps |

Deferred to phase 2: Discord (net-new + highest ban risk) and LinkedIn (aggressive detection).

## 6 · Functional requirements (P0 = must, P1 = should)

**FR-1 Campaign & audience** — create from list/segment/company/signal (P0); resolve to
contacts+handles, dedupe (P0); compose a "play" of channel order/warming/timing/intent (P0);
template library (P1).

**FR-2 Enrichment & identity** — on-demand enrichment via Clay/Apollo/DeFiLlama adapters (P0);
identity resolution + handle normalization (P0); cache + credit tracking (P1).

**FR-3 Channel connectors** — connect/auth email domain, TG accounts, X accounts (P0);
multi-account with health status (P0); bind campaign to a defined account set (P1).

**FR-4 Action execution** — messaging actions (P0); warming actions, gated by approval + rate
limits (P0); every action writes a HubSpot timeline activity (P0).

**FR-5 AI agent orchestrator** — Planner (P0); per-channel Executors (P0); Reply handler (P0);
Supervisor gate on sensitive actions (P0); configurable autonomy per action type (P1).

**FR-6 Approval queue** — pending actions with context, one-click approve/edit/skip, bulk (P0);
in-HubSpot card + companion web view (P1).

**FR-7 Personalization** — per-touch from on-chain/social context, per-channel tone (P0);
A/B variants + multilingual (P1).

**FR-8 Signal triggers** — start/adjust a campaign on a HubSpot workflow event or add-on signal (P1).

**FR-9 Unified inbox** — single inbox across email/TG/X, each thread linked to a HubSpot
contact (P0); agent-suggested replies + hot-lead routing (P1).

**FR-10 HubSpot integration** — OAuth install; custom objects/properties (P0); two-way sync,
list enrollment, timeline writes (P0).

**FR-11 Safety & compliance** — rate limits/warm-up/rotation/quiet-hours (P0); opt-out capture
+ global suppression (P0); hard approval gate on warming + cold messages (P0).

**FR-12 Reporting** — per-campaign touches/reply-rate/meetings/account-health (P1).

## 7 · Agent architecture

`HubSpot → Enrichment → Planner → Supervisor (human queue) → Channel executors → Reply handler → HubSpot`

Supervised multi-agent loop. HubSpot is the record; the orchestration service is the brain;
connectors are the hands. This is orchestration we already run — Spredo shipping a Claude MCP
for the same job validates the approach. The build is connectors + guardrails + HubSpot glue.

## 8 · HubSpot data model

- **Contact properties:** `telegram_handle`, `x_handle`, `wallet`, `ens`, `chains`,
  `last_raise`, `icp_score`, `opt_out_channels`.
- **Custom object: Sending Account** — channel, identifier, health, daily caps, warm-up stage.
- **Custom object: Campaign** — goal, audience source, channel plan, bound accounts, state.
- **Custom object: Touch** — contact, channel, action type, status, timestamp, approver
  (mirrored to the contact timeline).

Two-way sync; never becomes a second CRM.

## 9 · Key screens

Campaign builder · Approval queue (the daily driver) · Unified inbox · Account health ·
HubSpot contact card (touches/replies inline).

## 10 · Safety & compliance

- **Email** — CAN-SPAM/GDPR: unsubscribe, sender identity, suppression, domain warm-up.
- **Telegram** — phone-number accounts, gradual warm-up, per-account caps, rotation, no bulk blasts.
- **X** — automation policy + follow/like/DM caps; throttled warming; human-approved DMs.
- **Global** — approval gate on warming + cold messages; cross-channel opt-out; approval audit log.

Product principle: engagement automation is **assisted**, not autonomous. The approval gate is a
feature — it keeps customer accounts alive.

## 11 · Non-functional

Deliverability/reliability (queue-based, retries) · Security (encrypted tokens, least-privilege
scopes) · Privacy (GDPR/EU flag, retention, opt-out honored) · Scalability (concurrent
campaigns, rate-limit accounting) · Observability (agent-decision + approval audit trail, cost
tracking).

## 12 · Success metrics

< 15 min to first campaign · reply-rate ↑ vs email-only · ~0 account bans · wk-1 activation ·
NisWire switchers · meetings booked.

## 13 · Milestones

- **M0 Foundations** — HubSpot app, OAuth, data model, 1 enrichment adapter, email send + logging
- **M1 Telegram** — multi-account connector, warm-up/rotation, join + DM, approval gate
- **M2 X** — connector + warming within caps, account health
- **M3 Orchestrator** — planner + executors + reply handler across 3 channels, unified inbox
- **M4 Beta** — safety hardening, reporting; 3–5 design partners
- **GA** — marketplace listing, pricing, self-serve onboarding, NisWire-switch messaging

## 14 · Risks & open questions (to resolve)

- **ToS/ban liability** — even email+TG+X warming is risky; how much sits with us vs the customer's accounts.
- **Email infra** — HubSpot email vs customer ESP vs our stack (owns deliverability).
- **Telegram accounts** — customer-provided vs we provision (warm-up onboarding cost).
- **X API** — cost tier + automation-policy limits may constrain warming; validate before committing.
- **Unit economics** — enrichment + LLM cost per contact must fit an impulse-grade price.
- **Marketplace requirements** — review/security bar + custom-object limits on lower HubSpot tiers.
- **Cold-start** — no DB means value depends on the customer's existing HubSpot data; may need
  Stack Finder sooner.
