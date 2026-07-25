# Bootstrap: Dedaub backlink audit MCP server on the desktop

Audience: the desktop Claude (Cowork) with Desktop Commander. Execute
every step yourself with Desktop Commander. Do not ask Giorgio to run
commands. Ask him for input only where this file explicitly says so.

Goal: an always-on MCP server, not a script someone remembers to run.
Once this setup is done once, the audit tools (run_audit,
check_data_sources, score_single_domain, ...) are available in every
future Claude Code / Claude Desktop session opened on this repo,
automatically, via the project's `.mcp.json`.

## Steps

1. Repo. If `~/ReadMe` exists, run `git -C ~/ReadMe pull`. Otherwise:
   `git clone -b claude/backlink-analysis-gtm-ah7okq
   https://github.com/georgeiv76/ReadMe.git ~/ReadMe`

2. Skill. Copy `~/ReadMe/backlink-audit/skill/dedaub-backlink-audit/`
   into the skills directory where the other dedaub skills live. Load
   it before continuing.

3. Python environment for the MCP server (isolated, does not touch
   system Python):

   ```bash
   cd ~/ReadMe/backlink-audit
   python3 -m venv .venv
   .venv/bin/pip install -r mcp_server/requirements.txt
   ```

4. Keys. GUI-launched apps do not reliably inherit shell-exported
   environment variables, so use the local file the server already
   knows how to read:

   ```bash
   cp ~/ReadMe/backlink-audit/keys.env.example ~/ReadMe/backlink-audit/keys.env
   ```

   If `keys.env` already has real values, skip asking. Otherwise ask
   Giorgio ONCE, in chat, for the Ahrefs API key (from Ahrefs ->
   Account settings -> API keys -> "Generate API key", NOT "Generate
   MCP key" - that scope is for a different protocol) and the Bing
   Webmaster API key. Fill them into `keys.env`. NEVER write keys into
   any file that gets committed: `keys.env` is already git-ignored,
   verify that stays true (`git check-ignore keys.env` inside the repo
   should print the path).

5. Register the server. It is already declared in `~/ReadMe/.mcp.json`
   at the repo root (paths there use `${CLAUDE_PROJECT_DIR}`, portable
   across machines - nothing to edit). Open (or re-open) this repo as
   a Claude Code / Claude Desktop project. On first load you'll get a
   one-time approval prompt for the `dedaub-backlink-audit` MCP
   server - approve it. Confirm it's live:

   ```bash
   claude mcp list
   ```

   should show `dedaub-backlink-audit: connected`. If the desktop app
   has its own way to list active MCP servers, use that instead.

6. First real check. Call the `check_data_sources` tool (target
   dedaub.com). It tests Ahrefs REST, Ahrefs free Domain Rating, Bing,
   Open PageRank and Spamhaus, and explains each failure precisely -
   use it to fix any remaining key/plan issue before running a full
   audit.

7. First audit. Call the `run_audit` tool (target dedaub.com). Read
   the returned summary; call `get_last_report` for the full markdown.

8. Interpret failures using the skill:
   - Ahrefs failure: check the plan includes Site Explorer API units
     (Lite or higher) and that the key is from "Generate API key", not
     "Generate MCP key".
   - Bing empty: check_data_sources lists which sites the key can see;
     if the target site is missing, do the one-click "Import from
     Google Search Console" at bing.com/webmasters. Freshly added
     properties can take up to 48 hours to populate.
   - run_audit status "ERROR" with zero backlinks is intentional: it
     never overwrites a good snapshot with an empty run.

9. Report results in the skill's Part 6 format: profile toxicity band,
   toxic table with markers, trend, disavow recommendation. Disavow
   hard rules are in the skill Part 4: never upload anything to Google
   without the Part 4 conditions.

10. Schedule. Since the server is always available, "monthly" can now
    mean a scheduled call to the `run_audit` tool (Cowork scheduled
    task, launchd, or a Routine that just says "call run_audit for
    dedaub.com and report") rather than a shell command. Set that up
    so it repeats without asking Giorgio for input.

11. Keep `output/` and `keys.env` local. Never commit them; both are
    git-ignored already, but double-check before any `git add`.

## Fallback: CLI still works

If the MCP path is ever broken, `python3 -m backlink_audit.run_audit`
(see README.md) still works exactly as before, using the same
`AHREFS_API_KEY` / `BING_WEBMASTER_API_KEY` / `OPR_API_KEY` environment
variables (or the same `keys.env` file, since the CLI does not read
`keys.env` - export the variables in that terminal session first, or
`set -a; source ../keys.env; set +a` before running it).
