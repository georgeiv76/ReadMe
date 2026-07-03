# Routine: Enrich Contacts

## ROLE

You orchestrate contact enrichment for Dedaub (Web3 security) BD. Contacts are
prospects/leads for business outreach. Work only from public, self-published
professional information.

This routine is a self-improving loop. Each run: load learned state → refresh
the technique → enrich → measure what worked → persist learnings. Never skip
Step 4; without it the loop has no memory and cannot improve.

## STEP 0 — Load learned state

Read `routines/tg-discovery-playbook.md` from this repo. It contains the
ranked methods, tools, and per-method hit rates learned from previous runs.
If it's missing or empty, treat this as run #1 and build it in Step 4.

## STEP 1 — Refresh the technique (spawn a research sub-agent)

Launch a research sub-agent with this brief, passing it the playbook's
`last-updated` date:

> Find best practices and FREE / open-source tools that are NEW or CHANGED
> since {last-updated} for discovering a person's *self-published* Telegram
> handle from public professional sources — their own X/Twitter, LinkedIn,
> GitHub profile/README, personal site, company team page, conference/speaker
> bios, DAO/governance forums. Use WebSearch; prioritize results from the last
> 12 months. Also re-check the tools already in the playbook: flag any whose
> repo is archived, unmaintained (no commits in 12+ months), or broken.
> Return: (a) new methods/tools worth trialing, with repo link and last-commit
> recency; (b) playbook entries to retire, with reason.
> EXCLUDE: scraped/leaked/purchased bulk username lists, private-group
> membership scraping, or anything requiring ToS-violating automation.

Merge the sub-agent's findings into this run's working playbook: existing
methods ranked by historical hit rate first, new untested methods after them
(marked `trial`), retired entries dropped.

## STEP 2 — Enrich

For each contact, apply the working playbook in ranked order to find, where
publicly available: Telegram handle, role/company, and other professional
fields you already collect.

- Only accept a handle the person published themselves on a public professional
  source. Record the source URL, a confidence level (high/med/low), and WHICH
  playbook method found it — this attribution is what Step 4 learns from.
- Give each `trial` method a fair sample (at least a few contacts) so it can
  earn a real hit rate.
- If no self-published handle exists, leave it blank — never guess or infer
  from bulk lists.
- Skip contacts already enriched with a high-confidence handle (dedupe).

## STEP 3 — Output

Write results with: value, source URL, confidence, method used, and date
checked. Flag any low-confidence or unverifiable handles for human review
rather than using them.

## STEP 4 — Verify and persist learnings (closes the loop)

1. Compute per-method stats for this run: contacts attempted, handles found,
   hit rate, false leads (handles that failed verification).
2. Update `routines/tg-discovery-playbook.md`:
   - Re-rank methods by cumulative hit rate (this run merged with prior runs).
   - Promote `trial` methods that performed; demote or retire methods with
     poor cumulative hit rates or dead tools (keep a "Retired" section with
     the reason, so future research agents don't re-suggest them).
   - Set `last-updated` to today's date and append a one-line run summary to
     the run log (date, contacts processed, overall hit rate, changes made).
3. Commit the updated playbook to this repo with a message summarizing what
   changed and why. If nothing changed, still update `last-updated` and the
   run log — the next run needs to know this run happened.

## GUARDRAILS

Public self-published professional data only · respect platform ToS and
robots/rate limits · no leaked/scraped/purchased lists · outreach must honor
opt-out. If a source would require violating any of the above to obtain a
handle, skip it and note why.
