---
issue: 2238
role: silent-failure-audit+diagnose-first-86a93666
author: silent-failure-audit+diagnose-first-86a93666
loop_state: landed
code_under_review: same-commit
type: fix
breaking: false
verdict: PASS
upstream:
  - path: gates/spawn_on_pr.py
    sha: same-commit
  - path: gates/state_paths.py
    sha: 6e23bf019e3ba8f9fa24ba20909bf35319f797db
---

# issue-2238 — silent-failure-audit+diagnose-first-86a93666 record

skill-verdict: diagnose-first — applied: invoked; verified park-state file scope (item 3) as the first diagnostic step before assuming the PR-number logic (item 1) was reachable
skill-verdict: silent-failure-audit — applied: invoked; audited should_park()'s silent no-signal failure mode and made the new loop ceiling fail loud instead of silently no-opping
skill-verdict: work-in-english — applied: invoked; commit messages, PR title/body, code, tests, and this record were written in English throughout

## What was done

canonical: 0f1c5db5:gates/spawn_on_pr.py:450 (should_park), 0f1c5db5:gates/spawn_on_pr.py:497-660 (spawn_missing_for_pr); 0f1c5db5:gates/test_spawn_on_pr.py (new test file, this commit)

1. Item 3 investigation, done first per the issue's own instruction. Read
   `gates/spawn_on_pr.py` in full, then grepped the repo for
   `spawn_on_pr_parked.json` / `PARK_STATE_FILENAME`. `_park_state_path()`
   (`gates/spawn_on_pr.py`) calls `state_paths.orchestrator_state_path()`,
   which anchors to `MUSTER_STATE_ROOT` if set, else this install's own
   `<repo-root>/runs` — never the `root` argument (the target repo a
   caller happens to be operating on). This routing was landed by
   6e23bf01:gates/state_paths.py:1 (issue #2240 / PR #2247, "route
   orchestrator cross-tick state through STATE_ROOT, never the target
   repo") ahead of this issue's own work — see the acceptance-run below.
   The scope defect this issue hypothesized for item 3 is therefore
   already resolved on `main`, independently of this fix.

2. Item 1 fix in `gates/spawn_on_pr.py`: `should_park(prior, pr_number,
   blocked)` -> `should_park(prior, blocked)`. `pr_number` no longer
   participates in the park/re-arm decision. In `spawn_missing_for_pr()`,
   the caller's own entry guard used to require
   `prior.get("pr_number") == pr_number` before it would even call
   `is_approval_blocked()` — that guard, not `should_park()`'s body, was
   the actually-reachable defect: a self-created PR-number diff skipped
   the recheck path entirely and fell straight through to
   `to_spawn.append(...)`. The guard now only requires
   `prior.get("blocked")`, so every previously-blocked pair gets its
   approval status rechecked via `is_approval_blocked()` (a real external
   signal, `gates/ci.py`'s `_approved_roles_on_issue()`) every tick
   regardless of PR-number drift. `pr_number` is still recorded in each
   `park_state` entry, but only for operator-visible debugging.

3. Item 2 fix in `gates/spawn_on_pr.py`: new `MAX_RESPAWN_ATTEMPTS = 4`
   constant, threaded through `spawn_missing_for_pr(...,
   max_respawn_attempts=MAX_RESPAWN_ATTEMPTS)`. Each `park_state[key]`
   entry now also carries `attempts`, incremented on every actual spawn.
   A candidate about to be spawned, regardless of how it cleared the
   park/re-arm check above, is compared against `max_respawn_attempts`
   first; at or past it, the pair is not spawned and is instead written
   back with `ceiling_hit: True, parked: True`, reported via both
   `print()` and `spawn.ledger_write({"event":
   "spawn_on_pr_respawn_ceiling_hit", ...})` — see the ceiling-only
   acceptance run below for this reporting live.

4. New file `gates/test_spawn_on_pr.py` — no test file existed for this
   module before this change (per `git log --all --diff-filter=A --
   gates/test_spawn_on_pr.py` at commit 0f1c5db5, this branch). It has 10
   test functions, all passing — see the pytest acceptance run below.

## Why

canonical: 0f1c5db5:gates/spawn_on_pr.py:450-467 (should_park docstring, this commit's rewritten version)

The issue's own root-cause description matched `should_park()`'s code as
literally written at the time #2238 was filed, but this file moved
substantially afterward (issue #2575's lease/branch-slug refactor, issue
#2240's state-scope fix). The diagnose-first step was to establish, on
the code as it exists today, whether item 3's scope defect is still
live, and exactly where the PR-number bug is reachable in the current
call graph, rather than trusting the issue's file/line description at
face value — see the item-3 investigation above. That investigation is
what surfaced that the bug lived in the *caller's* entry guard, not in
`should_park()`'s own body in isolation: `should_park()` already ignored
a `pr_number` argument correctly whenever it was invoked, but its caller
never invoked it (or `is_approval_blocked()`) at all once a PR-number
diff appeared. Fixing only `should_park()`'s signature without also
fixing the caller's entry guard would have been a no-op change — this is
the kind of thing silent-failure-audit is for: a guard whose failure
mode produces no exception and no log line distinct from the "correctly
not parking because a human made progress" case.

The loop ceiling (item 2) is a plain attempts counter unrelated to
`is_approval_blocked()`/`should_park()`, specifically so it still catches
a runaway if some other, currently-unknown bug defeats the park rule
again later. The ceiling-only acceptance run below demonstrates this
independence directly: it forces `is_approval_blocked()` to report "not
blocked" (a legitimate re-arm signal) on every tick — which by itself,
under item 1's rule alone, would spawn without limit — and shows the
ceiling still stops it.

## Upstream basis

- `gates/spawn_on_pr.py` — modified in commit 0f1c5db5 on this branch
  (`should_park()`, `spawn_missing_for_pr()`, the
  `PARK_STATE_FILENAME`/`MAX_RESPAWN_ATTEMPTS` module constants and their
  surrounding comments).
- `gates/state_paths.py` — read-only reference for the item-3 finding;
  not modified by this change. See `sha: 6e23bf019e3ba8f9fa24ba20909bf35319f797db`
  in this record's frontmatter.
- `gates/spawn_on_approve.py` — read-only reference; a sibling module
  with its own separate attempt-history file
  (`spawn_on_approve_attempted.json`) for a different trigger condition.
  Followed here by extending `spawn_on_pr_parked.json`'s existing entry
  shape (`attempts`, `ceiling_hit`) rather than introducing a new state
  file for the ceiling, matching that module's precedent of one state
  file per concern.

## Open findings

canonical: 0f1c5db5:gates/spawn_on_pr.py:285-364 (missing_verification, applicable_record_kinds call)

None outstanding. One item flagged for a possible future issue rather
than fixed here (explicitly out of this issue's non-goals): a human
push to the branch, as a third re-arm signal alongside an approval
comment and a merge, is named in the issue's ask but not implemented.
`is_approval_blocked()` already covers the approval-comment signal, and
a merge is already handled one layer up via `missing_verification()`'s
own membership filtering (a landed record's kind is satisfied on the
board, so `applicable_record_kinds()` stops reporting that pair as
missing and it never reaches the park logic again) — between those two,
the concrete failure mode this issue reports (a self-created PR-number
diff defeating the park guard) is fully addressed by this fix without
needing new commit-author plumbing that does not exist anywhere in this
file today.

## What did not work

None — the diagnose-first-then-fix path (verify item 3 via `git log`/
grep first, then fix the caller's entry guard plus `should_park()`'s
signature, then add an independent attempts ceiling) worked on the first
attempt; nothing here was tried and reverted.

canonical: gh issue view 2208 --json number,title,state,url (raw JSON in "Acceptance run 2" below)

One process note, not a failure: `gh issue view 2208` reports its state
as CLOSED, so the live-reproduction requirement was satisfied against a
constructed equivalent synthetic subject (`issue-99208`, chosen to avoid
colliding with any real issue number on this repo) instead of the real
#2208 — flagged here explicitly per the issue's own instructions for
this fallback case.

## Next steps

None — `loop_state: landed`. `code_under_review: same-commit` covers
`gates/spawn_on_pr.py` and `gates/test_spawn_on_pr.py`, both already on
this branch at commit 0f1c5db5; this record lands in a follow-up commit
on the same branch/PR.

## Acceptance run 1 — item 3 confirmed via git log

acceptance: git log --oneline --all | grep -i "2240\|1476\|2238" — result:

```
6e23bf01 issue-2240: route orchestrator cross-tick state through STATE_ROOT, never the target repo (#2247)
12290038 issue-2240: route orchestrator cross-tick state through STATE_ROOT, never the target repo (#2247)
244db81c issue-2240: conformance review — PR #2247 builder-blind grade (#2256)
7984e2ac issue-2240: conformance review — PR #2247 builder-blind grade (#2256)
32d3be30 issue-2240: execution-observation -- independent re-verification of PR #2247 (#2253)
6c2dae9b issue-2240: execution-observation -- independent re-verification of PR #2247 (#2253)
5c22384f fix(issue-1638): downgrade brand-design quality_bar 3-4 to practitioner-consensus
e5f69732 Merge pull request #1485 from tokenmaxxxer/issue-1476/implementation
58eec31b issue-1476: PR #1485 review response — confirm --all threading unaffected
d5930baf issue-1476: implementation record
8ae79dc6 issue-1476: park approval-blocked respawn in spawn-on-pr gate
a114a533 Merge pull request #1481 from tokenmaxxxer/issue-1476/implementation
f89d920d issue-1476: phase-1 survey + proposal — park approval-blocked respawn
```

## Acceptance run 2 — issue #2208's live state

acceptance: gh issue view 2208 --json number,title,state,url — result:

```
{"number":2208,"title":"Skill selection follow-ups from #2205: judge abstention rate, negative-clause indexing, pinning policy skills","state":"CLOSED","url":"https://github.com/tokenmaxxxer/on-the-record/issues/2208"}
```

## Acceptance run 3 — live before/after reproduction (real code, real output)

Ran via a throwaway script (`/tmp/repro_2238.py`, not committed — not a
project file, so it carries no path-tracking claim of its own) that
calls the real, unmodified `spawn_on_pr.spawn_missing_for_pr()`
entrypoint (the same function `watchdog.py`'s board-sweep tick calls in
production) across 6 simulated ticks against a synthetic blocked subject
`issue-99208` (see "What did not work" above for why synthetic). Only
the gh/git/spawn boundaries (`is_approval_blocked`,
`_pr_number_for_branch`, `subject_deliverable_branch`,
`missing_verification`, `resolve_live_base`, `spawn.roster_register`,
`spawn._spawn_one`, `spawn.ledger_write`) are mocked via
`unittest.mock.patch.object` — no real network call, git fetch, or
Claude session is touched. The park-state file is a real temp file, read
and written by the real `load_park_state`/`_save_park_state` functions,
persisting across the simulated ticks within one run — mirroring the
orchestrator's real cross-tick persistence from acceptance run 1 above.
Each tick's PR number is bumped to a brand-new value (2224, 2235, 2246,
...), mimicking the real incident's own PR sequence (2224 -> 2235 -> ...)
— i.e. the observer's own respawned session opening a fresh PR, not a
human pushing a new commit.

acceptance: git stash push -m "issue-2238 fix (temp stash for before/after repro)" -- gates/spawn_on_pr.py && python3 /tmp/repro_2238.py "$(pwd)" — result:

```
[repro] orchestrator-scoped park state file (persists across ticks, this run): /tmp/otr-2238-repro-3q1pe35e/spawn_on_pr_parked.json

--- tick 1: subject=issue-99208 role=execution-observation pr_number=2224 (self-created this tick) ---
[spawn-on-pr] live base sha=deadbeef
    >>> REAL SESSION WOULD BE SPAWNED (#1 this run) <<<
    spawn_missing_for_pr() returned: [('issue-99208', 'execution-observation')]

--- tick 2: subject=issue-99208 role=execution-observation pr_number=2235 (self-created this tick) ---
[spawn-on-pr] live base sha=deadbeef
    >>> REAL SESSION WOULD BE SPAWNED (#2 this run) <<<
    spawn_missing_for_pr() returned: [('issue-99208', 'execution-observation')]

--- tick 3: subject=issue-99208 role=execution-observation pr_number=2246 (self-created this tick) ---
[spawn-on-pr] live base sha=deadbeef
    >>> REAL SESSION WOULD BE SPAWNED (#3 this run) <<<
    spawn_missing_for_pr() returned: [('issue-99208', 'execution-observation')]

--- tick 4: subject=issue-99208 role=execution-observation pr_number=2257 (self-created this tick) ---
[spawn-on-pr] live base sha=deadbeef
    >>> REAL SESSION WOULD BE SPAWNED (#4 this run) <<<
    spawn_missing_for_pr() returned: [('issue-99208', 'execution-observation')]

--- tick 5: subject=issue-99208 role=execution-observation pr_number=2268 (self-created this tick) ---
[spawn-on-pr] live base sha=deadbeef
    >>> REAL SESSION WOULD BE SPAWNED (#5 this run) <<<
    spawn_missing_for_pr() returned: [('issue-99208', 'execution-observation')]

--- tick 6: subject=issue-99208 role=execution-observation pr_number=2279 (self-created this tick) ---
[spawn-on-pr] live base sha=deadbeef
    >>> REAL SESSION WOULD BE SPAWNED (#6 this run) <<<
    spawn_missing_for_pr() returned: [('issue-99208', 'execution-observation')]

[repro] TOTAL sessions spawned across 6 ticks: 6
```

Every tick respawns on the pre-fix code — the park guard never engages
because each tick's self-created PR number differs from the prior
tick's, the reported incident shape (issue-2208's observers respawned
9x each).

acceptance: git stash pop && python3 /tmp/repro_2238.py "$(pwd)" — result:

```
[repro] orchestrator-scoped park state file (persists across ticks, this run): /tmp/otr-2238-repro-0w5drguc/spawn_on_pr_parked.json

--- tick 1: subject=issue-99208 role=execution-observation pr_number=2224 (self-created this tick) ---
[spawn-on-pr] live base sha=deadbeef
    >>> REAL SESSION WOULD BE SPAWNED (#1 this run) <<<
    spawn_missing_for_pr() returned: [('issue-99208', 'execution-observation')]

--- tick 2: subject=issue-99208 role=execution-observation pr_number=2235 (self-created this tick) ---
[spawn-on-pr] park=1건 waiting-for-human (승인-대기 상태 변화 없음): [('issue-99208', 'execution-observation')]
    spawn_missing_for_pr() returned: []

--- tick 3: subject=issue-99208 role=execution-observation pr_number=2246 (self-created this tick) ---
[spawn-on-pr] park=1건 waiting-for-human (승인-대기 상태 변화 없음): [('issue-99208', 'execution-observation')]
    spawn_missing_for_pr() returned: []

--- tick 4: subject=issue-99208 role=execution-observation pr_number=2257 (self-created this tick) ---
[spawn-on-pr] park=1건 waiting-for-human (승인-대기 상태 변화 없음): [('issue-99208', 'execution-observation')]
    spawn_missing_for_pr() returned: []

--- tick 5: subject=issue-99208 role=execution-observation pr_number=2268 (self-created this tick) ---
[spawn-on-pr] park=1건 waiting-for-human (승인-대기 상태 변화 없음): [('issue-99208', 'execution-observation')]
    spawn_missing_for_pr() returned: []

--- tick 6: subject=issue-99208 role=execution-observation pr_number=2279 (self-created this tick) ---
[spawn-on-pr] park=1건 waiting-for-human (승인-대기 상태 변화 없음): [('issue-99208', 'execution-observation')]
    spawn_missing_for_pr() returned: []

[repro] TOTAL sessions spawned across 6 ticks: 1
```

Tick 1 spawns once (first-ever sighting, matching the empty-state
acceptance criterion), then every subsequent tick parks and reports
"waiting-for-human" even though the PR number keeps changing every tick
(2235, 2246, 2257, 2268, 2279, all self-created) exactly as before.

## Acceptance run 4 — item 2 (respawn ceiling), independent of item 1's park rule

This scenario deliberately defeats item 1's own park rule: every tick,
`is_approval_blocked()` reports `False` ("not blocked", a real external
signal), so `should_park()` would never park and, without item 2, this
would keep spawning. `max_respawn_attempts=4` is given explicitly as an
argument to the call below.

acceptance: python3 /tmp/repro_2238_ceiling.py "$(pwd)" — result:

```
[repro] park state file (persists across ticks, this run): /tmp/otr-2238-ceiling-repro-bw5_29_e/spawn_on_pr_parked.json

--- tick 1: subject=issue-99208 role=conformance-review pr_number=3001, is_approval_blocked()=False every tick (real external signal every time) ---
[spawn-on-pr] live base sha=deadbeef
    >>> REAL SESSION WOULD BE SPAWNED (#1 this run) <<<
    spawn_missing_for_pr() returned: [('issue-99208', 'conformance-review')]

--- tick 2: subject=issue-99208 role=conformance-review pr_number=3002, is_approval_blocked()=False every tick (real external signal every time) ---
[spawn-on-pr] live base sha=deadbeef
    >>> REAL SESSION WOULD BE SPAWNED (#2 this run) <<<
    spawn_missing_for_pr() returned: [('issue-99208', 'conformance-review')]

--- tick 3: subject=issue-99208 role=conformance-review pr_number=3003, is_approval_blocked()=False every tick (real external signal every time) ---
[spawn-on-pr] live base sha=deadbeef
    >>> REAL SESSION WOULD BE SPAWNED (#3 this run) <<<
    spawn_missing_for_pr() returned: [('issue-99208', 'conformance-review')]

--- tick 4: subject=issue-99208 role=conformance-review pr_number=3004, is_approval_blocked()=False every tick (real external signal every time) ---
[spawn-on-pr] live base sha=deadbeef
    >>> REAL SESSION WOULD BE SPAWNED (#4 this run) <<<
    spawn_missing_for_pr() returned: [('issue-99208', 'conformance-review')]

--- tick 5: subject=issue-99208 role=conformance-review pr_number=3005, is_approval_blocked()=False every tick (real external signal every time) ---
    [ledger] {'event': 'spawn_on_pr_respawn_ceiling_hit', 'subject': 'issue-99208', 'role': 'conformance-review', 'attempts': 4, 'max_respawn_attempts': 4}
[spawn-on-pr] CEILING HIT: 1건이 최대 재시도 횟수(4)에 도달해 자동 스폰을 멈춘다 — 사람 개입 필요 (park_state 에 ceiling_hit=True 로 기록됨): [('issue-99208', 'conformance-review', 4)]
    spawn_missing_for_pr() returned: []

--- tick 6: subject=issue-99208 role=conformance-review pr_number=3006, is_approval_blocked()=False every tick (real external signal every time) ---
    [ledger] {'event': 'spawn_on_pr_respawn_ceiling_hit', 'subject': 'issue-99208', 'role': 'conformance-review', 'attempts': 4, 'max_respawn_attempts': 4}
[spawn-on-pr] CEILING HIT: 1건이 최대 재시도 횟수(4)에 도달해 자동 스폰을 멈춘다 — 사람 개입 필요 (park_state 에 ceiling_hit=True 로 기록됨): [('issue-99208', 'conformance-review', 4)]
    spawn_missing_for_pr() returned: []

[repro] TOTAL sessions spawned across 6 ticks: 4 (expected to stop at max_respawn_attempts=4, not run all 6)
```

Spawning stops at attempt 4 even though `is_approval_blocked()` reported
"not blocked" on every single tick — the ceiling is independent of item
1's park rule. Both `print()` and `spawn.ledger_write()` fire on the
ticks the ceiling is hit (ticks 5 and 6 above).

## Acceptance run 5 — gate test suite

acceptance: python3 -m pytest gates/test_spawn_on_pr.py -v — result:

```
gates/test_spawn_on_pr.py::test_should_park_still_blocked_parks PASSED
gates/test_spawn_on_pr.py::test_empty_state_spawns_once_and_never_parks_on_first_tick PASSED
gates/test_spawn_on_pr.py::test_respawn_ceiling_hits_and_reports_loudly PASSED
gates/test_spawn_on_pr.py::test_should_park_cleared_by_real_signal_does_not_park PASSED
gates/test_spawn_on_pr.py::test_should_park_signature_has_no_pr_number_parameter PASSED
gates/test_spawn_on_pr.py::test_should_park_prior_not_previously_blocked_does_not_park PASSED
gates/test_spawn_on_pr.py::test_self_created_pr_number_change_no_longer_defeats_parking PASSED
gates/test_spawn_on_pr.py::test_real_external_signal_clears_park_and_allows_respawn PASSED
gates/test_spawn_on_pr.py::test_should_park_first_time_candidate_never_parks PASSED
gates/test_spawn_on_pr.py::test_ceiling_hit_entry_stays_parked_on_a_later_tick PASSED

10 passed in 0.90s
```

acceptance: python3 -m pytest gates/ test/test_merge_gate_record_kind.py -q — result:

```
29 passed in 0.90s
```

No regression in the only other test file (`test/test_merge_gate_record_kind.py`) that imports `spawn_on_pr`, nor in the rest of `gates/`.
