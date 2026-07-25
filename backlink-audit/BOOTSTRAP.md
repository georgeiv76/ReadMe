# Bootstrap: Dedaub backlink audit on the desktop

Audience: the desktop Claude (Cowork) with Desktop Commander. Execute
every step yourself with Desktop Commander. Do not ask Giorgio to run
commands. Ask him for input only where this file explicitly says so.

## Steps

1. Repo. If `~/ReadMe` exists, run `git -C ~/ReadMe pull`. Otherwise:
   `git clone -b claude/backlink-analysis-gtm-ah7okq
   https://github.com/georgeiv76/ReadMe.git ~/ReadMe`

2. Skill. Copy `~/ReadMe/backlink-audit/skill/dedaub-backlink-audit/`
   into the skills directory where the other dedaub skills live. Load
   it before continuing.

3. Keys. Look for `~/.dedaub-audit-keys`. If it exists, source it. If
   not, ask Giorgio ONCE to paste the Ahrefs API key and the Bing
   Webmaster API key into the chat, then create the file yourself with
   `chmod 600`, containing two `export` lines (`AHREFS_API_KEY`,
   `BING_WEBMASTER_API_KEY`, optional `OPR_API_KEY`). NEVER write keys
   into the repo: it is public.

4. First audit. Run, from `~/ReadMe/backlink-audit`:

   ```bash
   source ~/.dedaub-audit-keys
   python3 -m backlink_audit.run_audit --target dedaub.com \
       --ahrefs-api --bing-api --online \
       --prev output/snapshot.json --out output/
   ```

5. Interpret failures using the skill:
   - Ahrefs HTTP 401: the subscription lacks API v3 (needs Lite or
     higher) or the key is not from Account settings, API keys. Tell
     Giorgio exactly this, once, with the fix.
   - Bing empty: the tool prints which sites the key can see. If it
     sees none, tell Giorgio to do the one-click "Import from Google
     Search Console" at bing.com/webmasters.
   - Exit code 3 is intentional: never overwrite a good snapshot with
     an empty run.

6. Report results in the skill's Part 6 format: profile toxicity band,
   toxic table with markers, trend, disavow recommendation. Disavow
   hard rules are in the skill Part 4: never upload anything to Google
   without the Part 4 conditions.

7. Schedule. Create a monthly recurring task (Cowork scheduled task or
   launchd, whichever this desktop already uses) that repeats steps
   1, 4 and 6. Do not schedule anything that asks Giorgio for input.

8. Keep `output/` local. Reports and snapshots stay on this machine.
