# FEATURE-ADD matrix scenario — live run log (issue #895 step 2, phase-1 evidence)

This file records what was read and executed this session, as raw
evidence. It does not render outcome/trajectory/step verdicts — that
belongs in the top-level per-issue execution-observation report, gated
behind an APPROVE comment this session did not find. canonical: `gh
issue view 895 --comments`, run this session — only `APPROVE
issue-895/product-discovery` and `APPROVE issue-895/implementation` are
present; no `APPROVE issue-895/execution-observation` comment and no
`DELEGATE issue-895/execution-observation` grant exist on issue #895.

## Scope

Role: execution-observation. Session: this one, branch
`issue-895/execution-observation`. Issue: #895, step 2 of its execution
plan (verbatim from the issue body — canonical: `gh issue view 895`, run
this session: "execution-observation: run each new scenario, record
per-type PASS/FAIL/UNMEASURED and the precise break points"). Subject
observed: the `feature` entry in `harness/driver.py::SCENARIOS` (PR
#905), run live for the first time against the real GitHub fixture host
(`JiwonJung94/northpole-harness-fixture`).

## What was read before running anything

- `harness/README.md`, `harness/driver.py`, `harness/signals.py` — the
  harness's own operator-action surface and the 7-signal + build-and-run
  scoring functions.
- `docs/issue-776/reports/execution-observation.md` — the prior re-run
  #7 record for the bug-fix scenario (#893), read to mirror its
  instantiate → seed → install → launch → poll → resume → verify
  sequence.
- `docs/issue-776/reports/execution-observation/run5.md` — read for the
  exact `claude -p` invocation flags for a first-turn launch and the
  project-scoped plugin install command shape.
- `harness/driver.py::SCENARIOS["feature"]` — the verbatim requirement
  text and fixture dir for this scenario.

## What was executed (raw sequence, all commands/results this session)

canonical: `gh auth token`, run this session — resolved non-empty (the
real-GitHub-host path is available, not UNMEASURED).

1. canonical: `git rev-parse HEAD`, run this session on this branch —
   `abedd51fac906c730d69e1921b1edf81914705b0`. This is PR #905's merge
   commit (this branch's own HEAD), confirming HEAD carries the
   `fixture-feature` + driver wiring before running anything.
2. canonical: `harness.driver.instantiate_scenario_fixture("feature",
   dest)` return value, run this session — fresh copy at
   `scratchpad/ffeature-run1-20260812`, never used by a prior run.
3. canonical: `harness.driver.seed_steady_state_github_host(dest)`
   return value, run this session — `{"available": true, "repo":
   "JiwonJung94/northpole-harness-fixture", "pushed_ref": "main"}`.
4. Plugin install: `claude plugin marketplace add <this repo root>
   --scope project` (registered as marketplace `tokenmaxxxer`), then
   `claude plugin install on-the-record@tokenmaxxxer --scope project`,
   run from `dest`. canonical: matching `installed_plugins.json` entry
   for this run's `projectPath`, read this session — `gitCommitSha:
   abedd51fac906c730d69e1921b1edf81914705b0` (the SHA under review, not a
   stale cache).
5. First `claude -p` turn: `CLAUDE_ROLE` unset, cwd = `dest`, isolated
   `MUSTER_STATE_ROOT` (fresh scratch dir), sole first message =
   `harness.driver.get_requirement_for_scenario("feature")` verbatim
   ("Add a --format json|text flag to the `greet` command; default stays
   text, json prints {\"message\": ...}. Add a test for both formats."),
   `--permission-mode acceptEdits --output-format json`. canonical:
   `docs/issue-895/reports/execution-observation/feature-2026-08-12-run1-first-turn.json`,
   captured this session — `session_id: b5faf166-8f63-4654-a4c1-49fd17b3a5df`,
   `subtype: success`, `num_turns: 18`. canonical: same file's `.result`
   field, read this session — filed issue #10 in the fixture repo
   (`greet: add --format json|text flag`), narrated spawning
   `implementation` on branch `issue-10/implementation` with a `watch
   --follow` observer armed, mentioning one prior spawn refusal
   ("respawned with `--trust-repo-config`").
6. canonical: `harness.driver.poll_for_pr_ready("JiwonJung94/
   northpole-harness-fixture", "issue-10/implementation", timeout_sec=480,
   interval_sec=15)` return value, run this session — `{"ready": false,
   "reason": "no OPEN/MERGEABLE PR ... within 480s"}`. canonical: `gh api
   repos/JiwonJung94/northpole-harness-fixture/branches --jq
   '.[].name'`, run this session immediately after — output was exactly
   `main` (one line, no `issue-10/*` branch).
   canonical: `gh api repos/JiwonJung94/northpole-harness-fixture/
   issues/10/timeline --jq '.[].event'`, run this session — empty output
   (zero events). canonical: `ps aux | grep -E "claude -p|spawn.py"`, run
   this session — no process tied to this run's `dest` path or issue #10
   in the listing.
   canonical: `find <isolated MUSTER_STATE_ROOT> -type f`, run this
   session — empty output (no muster roster file ever written for this
   run). The first turn's own narration of a live background spawn did
   not correspond to any surviving process, branch, PR, issue comment, or
   state file — all four checks immediately above are the citation for
   that claim.
7. Resumed the same session (`--resume b5faf166-...`, `--permission-mode
   bypassPermissions`, per #889) with a generic status-check nudge (not
   an answer to any question the session had asked). canonical:
   `docs/issue-895/reports/execution-observation/feature-2026-08-12-run1-resume1.json`,
   captured this session — `permission_denials: []`; `.result`: "The
   respawn bootstrapped cleanly this time... role got its isolated
   workspace on branch `issue-10/implementation`, and its session is
   live." canonical: `ps aux | grep issue-10`, run this session
   immediately after — one live `spawn.py implementation ... --issue 10`
   process now present.
8. canonical: `harness.driver.poll_for_pr_ready(...)` return value, run
   this session — `{"ready": true, "number": 11}`. canonical: `gh pr view
   11 -R JiwonJung94/northpole-harness-fixture --json
   state,mergeable,headRefName`, run this session — `{"state": "OPEN",
   "mergeable": "MERGEABLE", "headRefName": "issue-10/implementation"}`.
   canonical: `gh pr diff 11 -R JiwonJung94/northpole-harness-fixture`,
   read this session — adds `--format {text,json}` to `greet` (default
   `text` unchanged), a `format_greeting()` helper (`json.dumps({"message":
   ...})` for json), 3 new tests (default, explicit text,
   json-parsed-and-asserted).
9. Resumed again with "verify against acceptance, merge, rebuild, report".
   canonical:
   `docs/issue-895/reports/execution-observation/feature-2026-08-12-run1-resume2-final.json`,
   captured this session — `permission_denials: []`; `.result` carries a
   4-part report (what broke / what changed / what became possible /
   what limits remain, all four present — quoted in full in that file).
10. canonical: `gh pr view 11 -R JiwonJung94/northpole-harness-fixture
    --json state,mergedAt,mergeCommit`, run this session — `{"state":
    "MERGED", "mergedAt": "2026-08-11T21:44:56Z", "mergeCommit": {"oid":
    "8ab5e4f7da63d62013194bbe62bc39811fbde7a2"}}`.
11. Independent rebuild, fresh clone of `origin/main` (never the
    orchestrator's own working copy). canonical: this session's own
    shell commands and pasted output —
    ```
    $ git rev-parse HEAD
    8ab5e4f7da63d62013194bbe62bc39811fbde7a2
    $ python3 -m pytest -q
    ....                                                                     [100%]
    4 passed in 0.01s
    $ fixture-feature greet Ada --format json
    {"message": "Hello, Ada!"}
    $ fixture-feature greet Ada
    Hello, Ada!
    ```
12. canonical: `find <fresh clone of origin/main=8ab5e4f> -maxdepth 3`,
    run this session — output listed only `__pycache__`,
    `fixture_feature`, `fixture_feature.egg-info`, `pyproject.toml`,
    `test_fixture_feature.py`.
    canonical: same `find` output, read this session — no `docs/`
    directory present anywhere in that listing, i.e. no record exists in
    the merged fixture repo for issue #10.

## Raw instrument reading (harness.signals.evaluate_all)

Built directly from steps 5-12 above: delegation_events = the two
attempts/outcomes observed in steps 6+8; final_report = the 4 named
parts from step 9; reached_midcourse_moment = true, from step 6's dead
first attempt; human_input_stalls = empty list (no question-asking pause
observed in steps 5-9).

canonical: step 12's `find` output above — record_file = none,
requirement_records = empty list, resolution_trail = empty list, all
three set from that same confirmed-absent `docs/` directory.
canonical: step 11's pasted pytest/CLI output above — build_result and
run_result both carry `exit_code: 0`.

canonical: inline `signals.evaluate_all(...)` call, run this session,
pasted verbatim:

```
{
  "orchestration_to_completion": "PASS",
  "full_record_ability": "UNMEASURED",
  "real_wired_verification": "PASS",
  "autonomous_completion_reporting": "PASS",
  "problems_not_pushed_back": "FAIL",
  "condensed_requirement_management": "UNMEASURED",
  "inviolable_constraint": "UNMEASURED",
  "build_and_run": "PASS"
}
```

This raw instrument output is reported here as data, not as this role's
outcome/trajectory/step verdict — that recomputation belongs in the
gated phase-2 record once approved.

## What blocks phase 2

canonical: `on-the-record/hooks/approval-gate.sh` output, produced this session on a direct write attempt to the per-issue execution-observation report path: `no matching 'APPROVE issue-895/execution-observation' issue comment ... from a docs/specs/approvers.md-listed account was found`.

canonical: `gh issue view 895 --comments`, run this session — only
`APPROVE issue-895/product-discovery` and `APPROVE
issue-895/implementation` are present on issue #895; no `APPROVE
issue-895/execution-observation` comment and no live `DELEGATE
issue-895/execution-observation UNTIL <date>` grant exist.

canonical: `gh issue view 776 --comments`, run this session — that issue
does carry `APPROVE issue-776/execution-observation` twice, a different
branch/role instance than this one; the invoking prompt named that
approval, which does not extend to issue #895's own gate.

## Proposal for phase 2

Once `APPROVE issue-895/execution-observation` (or a valid VIA DELEGATION
grant) is posted on issue #895, phase 2 will write the per-issue
execution-observation report with the independence statement, the
outcome/trajectory/step verdict computed from this file's already-
gathered evidence (no re-execution needed — the live run above is final
and citable as-is), and the open finding already visible in the raw
signal output above: `problems_not_pushed_back` FAILs because the first
delegation attempt died silently with no in-repo trace, recoverable only
via an external poll-timeout + resume, never surfaced or recorded by the
loop itself.

Constraints: this role edits only its own report path; no file under
`harness/`, `spawn.py`, or `docs/specs/` gets touched. Out of scope:
fixing the silent-delegation-death gap itself (issue #895 step 3's job,
a different role/session). Acceptance for phase 2: the committed record
cites this file's evidence for every verdict-bearing sentence, per
signal, and states the precise break point with canonical citations,
matching this file's "Raw instrument reading" section.

## Accumulation

This is the harness's second live scenario measurement, after the
bug-fix representative (#893) — a repeatable-cost pattern. canonical:
steps 5-9 above — 2 `claude -p` turns before the first successful
delegation, 2 poll cycles (one 480s timeout, one immediate ready). Each
future matrix-type run (multimod, redtest, ambiguous, multirole,
infeasible) will follow this same instantiate → seed → install → launch
→ poll → resume → verify → `signals.evaluate_all` shape; this run's own
first attempt silently dying (step 6) suggests some future runs may need
more than one resume cycle, which future scoring should budget for
rather than treat as anomalous.
