---
kind: execution-observation-report
loop_state: handed-off
---

# Northpole E2E harness — steady-state re-run #2, real GitHub host (issue #776)

## Independence statement

canonical: this session's own tool-call history, checked this session — no
`harness/`, `docs/specs/northpole-harness.md`,
`docs/handbooks/northpole-harness.md`, or `on-the-record/hooks/` file was
opened via Edit/Write this session. This session did not author
`harness/driver.py`'s `resolve_harness_github_host` /
`seed_steady_state_github_host` (PR #851, issue #847) or the poll-backstop
docs/test addition (issue #848).
canonical: `git log --oneline -1`, run this session, before merging — it
only merged current `origin/main` into this branch, ran the harness fresh
with the new real-GitHub-host steady-state scenario, and records what
happened below.

code_under_review:
- harness/driver.py
- on-the-record/spawn.py

canonical: `git rev-parse HEAD`, run this session, after merging `origin/main`
```
4eba5816cbaa598bd467a32433fda7fb47cd18cd
```
canonical: `grep -n "^def resolve_harness_github_host\|^def seed_steady_state_github_host" harness/driver.py`, run this session
```
86:def resolve_harness_github_host():
154:def seed_steady_state_github_host(dest_dir):
```
Both present on this run's HEAD before anything was instantiated (merge
commit on top of `origin/main`'s `1851b1d62c46...`, which carries PR #851 /
issue #847 and the issue #848 poll-backstop pin).

canonical: `gh auth token`, run this session — resolved a token (`gho_A5ji...`,
truncated), so the run proceeded per driver's own gate rather than reporting
UNMEASURED-with-reason for a missing credential.

## What was done

1. **Instantiated a brand-new fixture-target copy and pushed it to the real
   private GitHub host**, never reusing any prior run's path.
   canonical: `driver.instantiate_fixture_target` /
   `driver.seed_steady_state_github_host` return values, run this session
   ```
   dest = .../scratchpad/ftarget-steady-20260811b
   seed_result = {'available': True, 'repo': 'JiwonJung94/northpole-harness-fixture',
                  'remote_url': 'https://x-access-token:***@github.com/JiwonJung94/northpole-harness-fixture.git',
                  'pushed_ref': 'main'}
   ```
   canonical: `gh api repos/JiwonJung94/northpole-harness-fixture/branches --jq '.[].name'`, run this session
   ```
   main
   ```
   — a single branch, confirming the reset-and-force-push replaced any
   stale branch from a previous run.
   canonical: `gh api repos/JiwonJung94/northpole-harness-fixture/commits/main --jq '.commit.message'`, run this session
   ```
   harness fixture initial commit
   ```
   confirming the pushed HEAD is this run's fresh fixture commit.
   canonical: raw `driver.run_version_check`/`driver.run_tests` output
   against the fresh copy, run this session, before installing the plugin
   ```
   VERSION exit_code=1 stderr='...AttributeError: module fixture_target has no attribute VERSION'
   TESTS 1 failed, 1 passed
   ```
   confirming the seeded defect was live before touching anything.

2. **Installed the on-the-record plugin, project-scoped, into that fresh
   copy**, via `claude plugin marketplace add <dest> --scope project` then
   `claude plugin install on-the-record@fixture-target-marketplace --scope
   project` (the marketplace's `on-the-record` entry sources from GitHub, so
   install pulls whatever is on `origin/main` at install time).
   canonical: the matching entry in `~/.claude/plugins/installed_plugins.json`
   for this run's `projectPath`, read this session
   ```
   {"scope": "project", "gitCommitSha": "1851b1d62c463f595734ae4765d95f45cef038cf",
    "projectPath": ".../ftarget-steady-20260811b"}
   ```
   — the installed commit is exactly `origin/main`'s HEAD at run time, so
   this run exercises PR #851 and the issue #848 pin for real, not a stale
   cache.

3. **Launched one fresh `claude -p` session**, `CLAUDE_ROLE` unset, rooted in
   the fresh fixture copy, given `driver.get_representative_requirement()`
   verbatim as the sole first message, `--permission-mode acceptEdits`.
   canonical: `docs/issue-776/reports/execution-observation/steady-state-2026-08-11b-transcript.jsonl`,
   this run's full captured transcript, read this session — 120 JSONL
   lines, one `result` event (`stop_reason: "end_turn"`, `is_error: false`,
   `num_turns: 22`), then the process exited. No operator response was
   given at any point.

4. **The session never delegated to any role.**
   canonical: `grep -o "spawn.py [a-z_-]* " steady-state-2026-08-11b-transcript.jsonl | sort -u`, run this session
   ```
   spawn.py init
   spawn.py watch
   ```
   No `spawn.py implementation` (or any other role) invocation appears
   anywhere in the transcript — `delegation_events` is empty for this run.
   canonical: `docs/issue-776/reports/execution-observation.md` step 4 of
   the run #1 section, read this session — run #1 had one genuine
   `implementation` delegation, so this run is a regression on that count.

5. **New blocker: the fixture session's `spawn.py watch --issue 776`
   resolved to this observing session's own real roster entry on a
   completely different repository**, not anything inside the isolated
   fixture.
   canonical: `ps aux | grep spawn.py`, run this session, live during the
   fixture session
   ```
   jwjung 3238031 python3 spawn.py execution-observation issue #776 re-measure #2 ... --issue 776 -C /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer
   jwjung 3238257 python3 spawn.py watch --issue 776 --role execution-observation --follow -C /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer
   ```
   pid 3238031's full command line matches this observing session's own
   operator prompt verbatim, and its `-C` path is the real `on-the-record`
   marketplace checkout, not the fixture copy. The fixture session's own
   `spawn.py watch --issue 776` (armed inside `.../ftarget-steady-20260811b`)
   surfaced this unrelated real session rather than reporting "no such
   issue in this repo".
   canonical: the fixture session's own `result` text,
   `steady-state-2026-08-11b-transcript.jsonl`, read this session — quotes:
   "There is already a running execution-observation session on issue-776
   in this repo's ledger — likely observing this very defect. I've armed
   `spawn.py watch --issue 776` in the background and will report its
   first material event... when it lands." The session reasoned about a
   session in "this repo['s] ledger" that is, per the `ps aux` `-C` path
   above, not in this repo at all.

6. **Second, independent blocker: `gh` write commands were denied by the
   session's own permission mode**, so even setting finding 5 aside, the
   session could not file the GitHub issue its own plan required before
   delegating to a role under contract v3.
   canonical: `permission_denials` array in the `result` event,
   `steady-state-2026-08-11b-transcript.jsonl`, read this session.
   derived: `python3 -c "import json;lines=open('docs/issue-776/reports/execution-observation/steady-state-2026-08-11b-transcript.jsonl').read().splitlines();o=[json.loads(l) for l in lines if json.loads(l).get('type')=='result'][0];print(len(o['permission_denials']));print(sum('gh issue create' in d['tool_input'].get('command','') or 'issues' in d['tool_input'].get('command','') for d in o['permission_denials']))"`
   ```
   9
   4
   ```
   9 total permission denials this run, 4 of them `gh issue create`/`gh api
   .../issues` calls, each `decision_reason: "This command requires
   approval"`.
   canonical: the fixture session's own `result` text, same file, read this
   session — quotes: "every `gh` call (issue create, list, view) is denied
   by the permission mode in this session, so I could not file the new
   issue for the `--version` fix myself."

7. **Also observed: the same watch-dies-with-parent-turn shape as run #1**,
   this time on top of the issue #848 poll-backstop pin.
   canonical: last lines of `steady-state-2026-08-11b-transcript.jsonl`,
   read this session — a `task_updated {"status": "killed", ...}` event for
   the armed `watch --follow` task follows the `result` event, the same
   shape as run #1.
   canonical: `docs/issue-776/reports/execution-observation.md`, run #1
   §"What was done" step 6, read this session — same shape observed there.
   canonical: `docs/issue-848/reports/implementation.md`, read this
   session — states the independent Monitor poll-tick, not the ephemeral
   CLI watch, is the authoritative catch for a role session's `COMPLETED`
   roster state. That tick has nothing to catch here: per finding 4 above
   (canonical: step 4's grep output, no `spawn.py implementation` line), no
   role session was ever spawned this run, so findings 5-6 (steps 5-6
   above) stopped the run before the #848 fix's target state could exist.

8. **Ran the harness's own build-and-run commands** against the fixture
   copy's unmodified working tree.
   canonical: raw `driver.run_build`/`run_version_check`/`run_tests` output,
   run this session
   ```
   BUILD exit_code=0
   VERSION exit_code=1 (same AttributeError traceback as the pre-run seeded defect)
   TESTS exit_code=1 (1 failed, 1 passed)
   ```
   canonical: `git -C <dest> status --porcelain` / `git -C <dest> diff --stat`,
   run this session — `diff --stat` empty; `status --porcelain` shows only
   `docs/specs/approvers.md` (written by the top-level session's own
   `spawn.py init`, per step 4's grep output above) plus build/cache
   noise — `fixture_target/__init__.py` was never modified, matching the
   unchanged build/test output above.

## Why

Re-run requested this turn specifically to test whether PR #851's real
GitHub host (plus the issue #848 poll-backstop pin) moves signals #1, #2,
#4, #6 from UNMEASURED/FAIL to real PASS/FAIL, using a brand-new
steady-state instantiation pushed to the real private repo.

## Upstream basis

canonical: `gh pr view 851`, `gh pr view 850`, read this session
- `harness/driver.py`'s `resolve_harness_github_host`/
  `seed_steady_state_github_host` (merged, PR #851, issue #847)
- the issue #848 poll-backstop pin (`docs/issue-848/reports/implementation.md`,
  read this session)
- `docs/issue-776/reports/execution-observation.md`'s run #1 content, as the
  prior baseline this run compares against — read for method and
  comparison numbers only; every number in the §5b table below is derived
  from this run's own artifacts.

## §5b — Steady-state signal results, run #2 (provenance: executed-live, plugin commit `1851b1d62c46`)

derived: `signals.evaluate_all(transcript, repo_state, build_result, run_result)`
run this session, inputs built from this run's own artifacts per steps 4
and 8 above: `delegation_events=[]`, `final_report=None`,
`record_file=None`, `requirement_records=[]`, `human_input_stalls=[]`

```
{
  "orchestration_to_completion": "UNMEASURED",
  "full_record_ability": "UNMEASURED",
  "real_wired_verification": "FAIL",
  "autonomous_completion_reporting": "UNMEASURED",
  "problems_not_pushed_back": "UNMEASURED",
  "condensed_requirement_management": "UNMEASURED",
  "inviolable_constraint": "UNMEASURED",
  "build_and_run": "FAIL"
}
```

| # | Requirement | Run #1 (steady-state, no real host) | Run #2 (this run, real GitHub host) | Evidence |
|---|---|---|---|---|
| 1 | Orchestration to completion | UNMEASURED | **UNMEASURED (unchanged, new cause)** | canonical: step 4 above — `delegation_events` is empty this run (run #1 had len 1, per `docs/issue-776/reports/execution-observation.md` step 4, read this session); the real-host fix (PR #851) removed the non-GitHub-origin stall, but findings 5-6 (roster leak + `gh` permission denial) now stop the session even earlier, before any delegation is attempted. |
| 2 | Full record-ability | UNMEASURED | **UNMEASURED (unchanged)** | canonical: step 8 above — `git -C <dest> status --porcelain` shows no record file; `repo_state.record_file = None`. |
| 3 | Real-wired verification | FAIL | **FAIL (unchanged)** | canonical: step 8 above — `run_version_check`/`run_tests` both ran and both failed against the still-unfixed working copy. |
| 4 | Autonomous completion + human-legible reporting | UNMEASURED | **UNMEASURED (unchanged, new cause)** | canonical: step 3 result text (quoted in step 5 above) is a "Closing this turn with observation armed" status update, not a 4-part completion report; `final_report = None`. |
| 5 | Zero-intervention operation | not applicable — `signals.py` has no standalone signal name for this; see row 7 | **not applicable** | canonical: `harness/signals.py` `SIGNAL_NAMES`, read this session — no entry named for req #5 standalone. |
| 6 | Condensed requirement management | UNMEASURED | **UNMEASURED (unchanged)** | canonical: `harness/signals.py`'s `check_condensed_requirement_management`, read this session — reads `repo_state.requirement_records`; `[]` this run (no role ever produced a requirement record) → UNMEASURED per its empty-state branch. |
| 7 | Problems not pushed back to human without cause | FAIL (run #1) | **UNMEASURED (moved off a scored FAIL)** | canonical: `harness/signals.py`'s `check_problems_not_pushed_back`, read this session — reads `human_input_stalls`; this run's transcript recorded none (the session ended its own turn per step 3 rather than reaching an explicit stall), so the input is `[]` rather than a populated stall list, landing on the empty-state branch instead of a scored FAIL. |
| 8 | Build-and-run assertion | FAIL | **FAIL (unchanged)** | canonical: step 8 above — `VERSION exit_code=1`, `TESTS exit_code=1`, unchanged from the pre-run seeded defect. |

## Open findings

1. **`spawn.py`'s issue-ledger/roster lookup is not scoped to the invoking
   repository's own `-C` path**, so a session running inside the isolated
   harness fixture can surface (and stall on) an unrelated real session
   running in a different repository on the same host, purely because both
   reference the same issue number.
   canonical: `ps aux` snapshot (step 5 above) — pid 3238031 is this
   observing session's own process, `-C
   /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer`, surfaced by a
   `spawn.py watch --issue 776` invoked from `.../ftarget-steady-20260811b`.
   Impact: this is the first blocker the steady-state scenario hits this
   run — before run #1's board-gate/origin blockers can even be exercised
   for this run's requirement — because the session's own reasoning gets
   diverted onto the unrelated real session instead of proceeding to
   delegate. canonical: step 5 above, fixture session's own `result` text —
   quoted there. This is plausibly a production concern beyond the harness
   itself: any two independent `on-the-record` installations sharing this
   host's `~/.claude` state could observe each other's issue numbers
   colliding. Timeline: observed this session, 2026-08-11. Root cause: not
   diagnosed further by this role — whether `spawn.py`'s roster file is a
   single global path unscoped by repo, or the `-C` flag is not threaded
   into the lookup that resolves `--issue 776 --role
   execution-observation`, is a design decision out of this role's scope.
   Action item: route to `docs/issue-749/reports/conformance-review.md` or
   a new backlog item, per spec §6.
2. **The top-level plain session's permission mode (`acceptEdits`) denies
   `gh issue create`/`gh api .../issues` outright**, so even a session that
   correctly reasons it needs a fresh GitHub issue to delegate under
   contract v3 cannot file one.
   canonical: step 6 above — the `derived:` command's own code-fenced
   output there is the basis for this finding; see that fence for the
   exact denial counts.
   Impact: independent of finding 1 — even a session that never hit the
   roster-leak confusion would still stall here, because the harness's
   fixture-target scenario gives a plain session no path to create its own
   subject issue without an interactive approval it will never receive in
   a `-p`/`acceptEdits` run. canonical: step 6 above, fixture session's own
   `result` text quote. Timeline: observed this session, 2026-08-11. Root
   cause: not diagnosed further by this role — whether the fixture
   scenario should pre-seed a subject issue (so the plain session never
   needs `gh issue create` itself), or whether the harness's chosen
   permission mode should allow `gh issue create` specifically, is a design
   decision out of this role's scope. Action item: same routing as
   finding 1.
3. **Run #1's findings 1-3 were never actually re-exercised by this run**,
   canonical: step 4 above's grep output and step 7 above (cited again
   here), because findings 1-2 above stopped the session before it reached
   the point (real delegation attempted) where run #1's blockers apply.
   `docs/specs/approvers.md` *was* written this run by the top-level
   session's own `spawn.py init`, unlike run #1 where it was reported
   absent from the template — canonical:
   `docs/issue-776/reports/execution-observation.md`, run #1 open
   finding 1, read this session.
   canonical: step 4 above's grep output (same fence quoted at this
   finding's start) — this suggests `spawn.py init` writes
   `docs/specs/approvers.md` at runtime rather than the template needing
   to ship it, but this role does not confirm that further this run since
   no PR-open step was ever attempted.
   canonical: step 1 above — `gh api .../branches` output shows the real
   GitHub host live, mooting run #1's finding 2 (non-GitHub origin).
   canonical: step 7 above — no role session ever existed for the poll
   backstop to catch, so run #1's finding 3 (watch-dies-with-parent-turn)
   is neither confirmed fixed nor unfixed by this run.
   Timeline: observed this session, 2026-08-11, per steps 1 and 7 cited
   just above. Root cause: n/a — scope note, not a defect. Action item: a
   run #3 that first resolves the two open findings above is needed before
   run #1's remaining open items (canonical: steps 1 and 7 above) can be
   confirmed moved.

## Next steps

None from this role — issue #776's scope ends at establishing scoreboard
runs (see the design proposal's "Out of scope" section, canonical:
`docs/issue-776/proposals/`, read this session). Fixing findings 1-2 above
and deciding between their resolution directions are future, separate
steps, decided by the human via new issues.

## Resolution path

Findings 1-2 above route back into
`docs/issue-749/reports/conformance-review.md` (or new backlog rows) as new
findings per spec §6 — filed by the human as new GitHub issues, never by
this role.
