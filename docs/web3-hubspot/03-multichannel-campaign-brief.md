# 03 · Multichannel Campaign — Product Brief & Competitive Landscape

The lead add-on. Product + feature description, then every vendor doing something close.

## In plain terms

This is the **reach** half of a two-engine system:

- **Buying Signal Trigger** — finds *who* to contact and *why today*.
- **Multichannel Campaign (this doc)** — does the *reaching out*, across email + Telegram + X.

```
Buying Signal Trigger  →  HubSpot  →  Multichannel Campaign
  (find + why-now)         (record)      (warm + reach out)
```

It picks up the qualified lead + "why now" the trigger produced and turns it into a warmed,
personalized, multichannel outreach play — the two run as one routine (see "The end-to-end
routine" below).

## Product description

**Positioning:** the only multichannel campaign engine that is **HubSpot-native, Web3-first,
and agent-driven.** Web3 teams already keep HubSpot as their record. Today they bolt on a
standalone Telegram tool, run Discord/X by hand, and get no help warming a prospect. This turns
HubSpot itself into the command center: one play, multiple channels, one supervised AI agent.

- **One job:** given a company — or a list — run a coordinated, personalized play across every
  channel a Web3 buyer uses, and warm them before you ask for anything.
- **Who for:** growth / BD / community leads at the ~2,000 Web3-native companies on HubSpot.
- **Why an add-on, not a platform:** the Web3 leaders (Spredo, Enreach, CRMChat) make you leave
  HubSpot. We layer onto it — no migration, install from the marketplace.

## Feature description

1. **Audience & input** — company / list / segment / signal → auto-resolve people & handles (via Web3 Enrich) → dedupe vs HubSpot.
2. **Channel action catalog** — messaging **and** warming (warming = engagement, ToS-sensitive):
   - Email — send · sequence
   - Telegram — DM · group message · *join* (via Telegram Hub)
   - Discord — DM · server post · *join · react* (via Discord Hub)
   - X — reply · DM · *follow · like*
   - LinkedIn — message · *connect · like*
3. **AI agent orchestrator (the core, required not optional)** — Planner builds the per-target
   play; per-channel Executor agents run the steps; a Supervisor gate routes sensitive actions
   to a human for one-click approval; a Reply handler reads responses and decides the next step.
   Human-in-the-loop by default (mirrors the Web3-winning posture).
4. **Personalization & signal triggers** — each touch written from on-chain/social context;
   campaigns can fire off Raise Radar / Ship Signal / Risk Trigger.
5. **HubSpot-native integration** — system of record; custom objects/properties; two-way sync;
   timeline logging; marketplace-app packaging (displaces NisWire).
6. **Safety & compliance layer** — rate limits, warm-up, account rotation, opt-out, hard
   approval gate on the riskiest actions. Engagement automation sold as *assisted*.

## The end-to-end routine (per target)

The campaign runs as a supervised agent loop — one pass per target:

1. **Ingest** — receive a lead or list (from Buying Signal Trigger, a HubSpot list, or a signal).
2. **Resolve** — enrich to the right people + email/Telegram/X handles (via Web3 Enrich); dedupe.
3. **Plan** — the Planner agent builds the per-target play: channel order, warming steps, timing,
   message intent — seeded by the incoming "why now".
4. **Warm** — assisted engagement first: X follow/like, Telegram join — through the approval gate.
5. **Message** — personalized email / Telegram DM / X DM, within per-account rate limits.
6. **Supervise** — every sensitive touch waits in the approval queue for one-click approve/edit/skip.
7. **Handle replies** — the Reply handler reads responses, logs to the HubSpot timeline, routes hot
   leads to a human, or advances the sequence.
8. **Log & learn** — all touches/outcomes write back to HubSpot; results inform the next play.

```
lead/list → resolve → plan → warm → message → [approval gate] → reply-handle → log → next step
```

**Cadence:** event-driven — a campaign fires when a lead lands or a signal triggers, then runs its
steps on a paced schedule (rate-limited, warmed, quiet-hours aware) until reply or exhaustion.

## Competitive matrix

Legend: ● full · ◐ partial/via-sync/unverified · ○ none. Cells inferred from public marketing
pages, not hands-on tests.

| Vendor | Web3 | HubSpot-native | Email | TG | Discord | X | LinkedIn | Warming | AI agent | Web3 DB |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| **Multichannel Campaign (ours)** | ● | ● | ● | ● | ● | ● | ● | ● | ● | ◐ |
| NisWire (Niswey, HS app) | ◐ | ● | ○ | ● | ○ | ○ | ○ | ○ | ○ | ○ |
| Spredo (web3) | ● | ◐ | ◐ | ● | ○ | ◐ | ◐ | ◐ | ● | ● |
| Enreach (web3) | ● | ◐ | ◐ | ● | ○ | ● | ● | ◐ | ● | ● |
| CRMChat (web3) | ● | ◐ | ○ | ● | ◐ | ○ | ○ | ◐ | ● | ● |
| La Growth Machine (general) | ○ | ● | ● | ○ | ○ | ● | ● | ● | ◐ | ○ |
| 11x / Artisan (AI SDR) | ○ | ◐ | ● | ○ | ○ | ◐ | ● | ◐ | ● | ○ |
| DM Dad / Xreacher (X point tools) | ○ | ○ | ○ | ◐ | ○ | ● | ○ | ● | ◐ | ○ |

### The white space
**No vendor combines HubSpot-native + Web3 + all five channels + engagement warming + a
supervised AI agent.** The Web3 leaders (Spredo, Enreach, CRMChat) are standalone platforms that
ask you to leave HubSpot, and are weak/absent on Discord and LinkedIn/X *engagement*. The only
HubSpot-native option (NisWire) is Telegram-only, no agent, no warming. The best engagement
engine (La Growth Machine) has zero Web3 channels. Discord outbound is barely served by anyone —
a differentiator and the biggest ToS risk at once.

## Inside their AI SDR agents

Shared 6-step stack: **discover → research → write → send → qualify → route & book.**

- **Spredo (Web3):** AI SDR (beta) answers FAQs & pre-qualifies before human escalation.
  Proprietary scraper of **300+ curated Telegram groups** (incl. private conference groups) →
  live Web3 DB. Supervised. Ships a **Claude MCP** — Claude itself runs contact selection,
  campaigns and outreach.
- **Enreach (Web3):** agents **trained on 30M sales conversations + 25M historical Telegram
  messages** (a domain-tuned model — a real moat). Auto-engages inbound, asks discovery Qs,
  routes hot leads, books meetings; 12 TG accounts; **500M-lead** DB.
- **11x (Alice):** *autonomous* end-to-end across email/LinkedIn/SMS/WhatsApp/voice; positioned
  to replace headcount. Not Web3.
- **Artisan (Ava):** lighter email + LinkedIn SDR. Not Web3.

**Two philosophies:** supervised/hybrid (Spredo, Enreach — Web3 default, brand-safe) vs
autonomous (11x). For Web3's pseudonymous, community-sensitive buyers, **supervised is winning.**

## Two honest reads
1. The AI agent is now **table stakes** — everyone has one. Our edge is channel breadth +
   HubSpot-native + Web3 depth, with the agent as the delivery mechanism.
2. Two moats we **don't** have: Enreach's conversation-trained model, and the big proprietary
   contact DBs (Spredo 300k, Enreach 500M). We lean on enrichment + the customer's HubSpot data.

## Where we win / where we're exposed

**Win:** only HubSpot-native + Web3-first + all-channel option; Discord + warming that Web3
rivals lack; no rip-and-replace; agent orchestration is what we already build.
**Exposed:** ToS/ban risk on Discord/X/LinkedIn; no big contact DB; Discord Hub is net-new;
incumbents have a Telegram head start.

## Sources
spredo.io · enreach.ai · crmchat.ai · niswey.com/telegram-hubspot-integration-niswire ·
lagrowthmachine.com · 11x.ai · dmdad.com · xreacher.com · eakdigital.com (Top Web3 tools).
