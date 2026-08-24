---
issue: 2240
role: implementation
loop_state: landed
upstream:
  - path: gates/state_paths.py
    sha: 8eb582504e442cc3656103bcc67dc0c12b856161
code_under_review:
  - gates/state_paths.py
  - gates/gh_delta.py
  - gates/board_read.py
  - watchdog.py
  - gates/spawn_on_pr.py
  - gates/spawn_on_approve.py
  - gates/closure_sweep.py
  - conftest.py
  - tests/test_state_root_scoping.py
  - tests/test_spawn_on_pr_park.py
  - gates/test_closure_sweep.py
  - docs/specs/enforcement-boundary.md
type: fix
breaking: "none — every touched accessor keeps its root: Path parameter for call-site compatibility; only the internal storage location changed"
verdict: pass
---

# issue-2240 — implementation record

## What was done

Added `gates/state_paths.py` — a single accessor,
`orchestrator_state_path`, anchored to `MUSTER_STATE_ROOT` when set, else
this install's own `<repo-root>/runs`, the same env-var/fallback
expression `spawn.py`, `watchdog.py`, and `events.py` already carry for
their own `STATE_ROOT` constant
(canonical: `watchdog.py:59-60`, `events.py:51-52`, both read this
session, identical to the pre-existing `spawn.py:532-533` expression).

Routed every orchestrator-scoped `runs/` accessor through it, dropping
their dependence on the `root` (target-repo) parameter for storage
location while keeping `root` in each public signature for call-site
compatibility (canonical: `git show 8eb58250 -- gates/gh_delta.py
gates/board_read.py watchdog.py gates/spawn_on_pr.py
gates/spawn_on_approve.py gates/closure_sweep.py`, this session):

- `gates/gh_delta.py`: the gh-delta cursor path.
- `watchdog.py`: the requirement-drift cache path and the watchdog noise
  state path.
- `gates/spawn_on_pr.py`: the park-state path, plus the sticky
  merged-PR-seen cache (issue #2165).
- `gates/spawn_on_approve.py`: the auto-respawn attempted-state path
  (issue #2173).
- `gates/closure_sweep.py`: the out-of-index-seen cache (issue #1643),
  the gh-quota backoff state (issue #1498), the board-sweep queue (issue
  #1554), and the accumulation-trend cache (issue #512).
- `gates/board_read.py`: the board-snapshot path was already
  `MUSTER_STATE_ROOT`-aware (the issue calls it "already correct") but
  duplicated the anchoring expression inline; it now shares the one
  accessor instead, and its docstring's claim that `gates/gh_delta.py`
  used "the same anchoring" is fixed — that claim was false before this
  change (canonical: `git show 8eb58250 -- gates/board_read.py`, this
  session, old hunk had no `MUSTER_STATE_ROOT` check in `gh_delta.py` at
  all).

The `gates/spawn_on_pr.py`/`gates/spawn_on_approve.py`/
`gates/closure_sweep.py` sites above (six files total) were not on the
issue's own enumerated 5-site list; see Rationale for deviations for why
they were added to scope, with citations (canonical: `git show 8eb58250
-- gates/spawn_on_pr.py gates/spawn_on_approve.py
gates/closure_sweep.py`, this session).

Left out of scope, classified as not orchestrator-scoped or already
correctly anchored (canonical: `grep -rn 'root / "runs"' --include=*.py .`
and `grep -rn '_sp.ROOT / "runs"\|spawn.ROOT / "runs"' --include=*.py .`,
both run this session):
- `gates/closure_sweep.py`'s board-list etag cache writes under
  `root / ".git" / "gh-read-cache"`, not `runs/` — `.git/` is never part
  of a repo's tracked working tree regardless of `.gitignore`, so it
  doesn't have the bug this issue fixes.
- Every site already anchored to the orchestrator's own `ROOT` constant
  (`skills.py`, `lifecycle.py`, `board.py`, `pipeline.py`, `spawn.py`'s
  reconcile ledger, `watchdog.py`'s own poll/watchdog/standing-red state)
  — these never depended on a `root` parameter representing the target
  repo.
- `consult.py`'s judge-trace path (`runs/patrol-judge-log.md`) has the
  same bug shape and the same "gitignore hides it" rationale the issue's
  Non-goals section rejects (canonical: `consult.py:852-858`, read this
  session — the docstring says `runs/`는 git-ignored라 커밋 없이도 대상
  트리를 더럽히지 않는다), but its anchor is deliberately shared with
  sibling `docs/issue-<n>/...` paths that are legitimately
  target-repo-scoped; issue #1313 fixed a crash from those paths using
  divergent anchors. Left as an open finding rather than risked here.

Added the acceptance gate `tests/test_state_root_scoping.py` (the issue's
named gate) covering all 11 routed accessors — empty-state-on-first-tick,
a full save cycle that never touches the target repo's tree, and a live
two-tick `should_park()` demonstration through the real load/save cycle.
Added an autouse `conftest.py` fixture pointing `state_paths.STATE_ROOT`
at a per-test tmp dir, the same isolation shape the existing
`_isolated_gh_read_cache_approvals` fixture already applies to
`spawn._approval_record_path` a few lines above it (canonical:
`conftest.py:48-57`, read this session).

## Why

#2238's root cause: `should_park()` never parked because the state that
would supply `prior` was written to `root / "runs"` instead of one stable
location the orchestrator could read back on the next tick. This
implements the issue's Ask directly: classify by scope, route the
orchestrator-scoped files through the existing `MUSTER_STATE_ROOT`/
`STATE_ROOT` mechanism (issue #857), do it through one accessor so a
future `root / "runs"` is visibly out of convention, and never let this
state land in a consumer's working tree.

## What did not work

None.

## Rationale for deviations

The issue's Ask enumerated exactly 5 `root / "runs"` call sites (its own
grep result). Fixing only those 5 would have left the bug alive: the
issue's own body includes a real reproduction transcript (canonical: `gh
issue view 2240`, this session) —

```
$ ls ~/.tokenmaxxxer/work/skill-repository-issue-60-knowledge-management/runs/
accumulation_trend.json   board_sweep_queue.json   gh_delta_cursor_issues.json
gh_quota_backoff.json     spawn_on_pr_parked.json
```

— naming `board_sweep_queue.json`, `gh_quota_backoff.json`, and
`accumulation_trend.json`. `gates/closure_sweep.py` composes those three
paths via named `*_REL` constants (`root / SOME_REL`), which the literal
`root / "runs"` string the issue's own grep matched does not catch
(canonical: `git show 75573112:gates/closure_sweep.py | grep -n
'Path("runs")'`, this session, run against the immediate parent commit
this branch started from — result:

```
37:OUT_OF_INDEX_SEEN_STATE_REL = Path("runs") / "closure_sweep_out_of_index_seen.json"
549:BACKOFF_STATE_REL = Path("runs") / "gh_quota_backoff.json"
630:BOARD_SWEEP_QUEUE_STATE_REL = Path("runs") / "board_sweep_queue.json"
```

). The same command against `gates/spawn_on_pr.py` and
`gates/spawn_on_approve.py` (canonical: `git show
75573112:gates/spawn_on_pr.py | grep -n 'Path("runs")'` and `git show
75573112:gates/spawn_on_approve.py | grep -n 'Path("runs")'`, this
session — result:

```
54:PARK_STATE_REL = Path("runs") / "spawn_on_pr_parked.json"
63:MERGED_SEEN_STATE_REL = Path("runs") / "spawn_on_pr_merged_seen.json"
```
```
62:ATTEMPTED_STATE_REL = Path("runs") / "spawn_on_approve_attempted.json"
```

) surfaces two more same-shaped sites not on the issue's list:
`PARK_STATE_REL` was already there; `MERGED_SEEN_STATE_REL` and
`ATTEMPTED_STATE_REL` were not. Per the issue's own task framing
("Classify every file the system writes under runs/") and its Non-goals
("never write our state into a consumer's working tree, whichever way
scoping is resolved"), leaving these six sites unfixed would have been an
incomplete delivery, not a narrower one. Widened `code_under_review`
accordingly rather than filing a separate follow-up issue, since the fix
is the same mechanical change already made to the other 5 sites.

## Upstream basis

This issue's own body (`gh issue view 2240`, read this session — no
prior implementation-role survey for this issue exists, and
`CORE_BUILD_NOW=1` was set in this session's environment, authorizing the
delivery-only bypass of the phase-1 proposal round per contract v3 s19a).
Code lands at `8eb582504e442cc3656103bcc67dc0c12b856161` (this branch,
`issue-2240/implementation`). Prior art directly referenced: issue #857
(`MUSTER_STATE_ROOT`/`STATE_ROOT`, the mechanism this reuses), #2238
(`should_park()` never parked — the live demonstration below is this bug,
now fixed), #2216 (the watchdog noise suppressor's same-shaped defect),
#2165, #2173, #1643, #1498, #1554, #512 (the six additional cross-tick
caches added to scope above).

### Executed acceptance evidence

Acceptance gate, full pass (canonical: `python3 -m pytest
tests/test_state_root_scoping.py -v`, run this session):

```
13 passed in 18.88s
```

Regression sweep over every test file touching a changed accessor
(canonical: `python3 -m pytest tests/test_state_root_scoping.py
gates/test_closure_sweep.py tests/test_gh_quota_guard.py
tests/test_board_sweep_budget_carryover.py tests/test_spawn_on_approve.py
gates/test_gh_delta.py gates/test_requirement_drift.py
tests/test_watchdog_heartbeat_noise.py tests/test_spawn_on_pr_park.py
tests/test_spawn_on_pr.py tests/test_spawn_observation_recovery.py
gates/test_watch_rearm_registry.py -q`, run this session):

```
284 passed, 4 xfailed, 1 xpassed in 184.31s (0:03:04)
```

Full non-slow suite (canonical: `python3 -m pytest -q -m "not slow"`, run
this session):

```
2 failed, 3169 passed, 19 xfailed, 2 xpassed in 89.68s (0:01:29)
```

The 2 failures (`on-the-record/hooks/test_directive_diet.py::
test_always_on_injection_within_size_budget`,
`tests/test_spawn_board_flows.py::RosterOwnershipScoping::
test_undispositioned_role_prs_excludes_own_roster_branch`) are
pre-existing on `main`, unrelated to this change — reproduced against a
`git stash` of every change in this record (canonical: `git stash &&
python3 -m pytest -q on-the-record/hooks/test_directive_diet.py::test_always_on_injection_within_size_budget
"tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch"
&& git stash pop`, run this session — both failed identically with this
change stashed out, then the stash was popped cleanly leaving this
commit's tree unchanged).

Boundary/index gates (canonical: `python3 -m pytest gates/test_boundary.py
-q`, run this session): `9 passed, 1 xfailed`; `python3 gates/spec_index.py
--update` produced no diff to `docs/specs/reconciled-index.md`, run this
session.

Live provenance demonstration — a real (non-pytest) target repo standing
in for a freshly-cloned consumer repo, `MUSTER_STATE_ROOT` standing in for
the orchestrator's own persistent state directory, and the real,
unmocked `gates/spawn_on_pr.py` functions driving two ticks (canonical:
a `python3 -` script and the `find`/`cat`/`git status` commands run
against `/tmp/issue2240-target-repo` and
`/tmp/issue2240-orchestrator-state`, this session):

```
=== TICK 1 (first sighting, blocked, pr_number=42) ===
prior=None should_park=False

=== TICK 2 (identical blocker: still blocked, still pr_number=42) ===
prior={'blocked': True, 'parked': False, 'pr_number': 42} should_park=True

orchestrator state file: /tmp/issue2240-orchestrator-state/spawn_on_pr_parked.json
```

```
=== (a) orchestrator state file — real content on disk ===
{
  "issue-9999/conformance-review": {
    "blocked": true,
    "parked": false,
    "pr_number": 42
  }
}

=== (b) target repo tree AFTER 2 ticks — no orchestrator state files ===
/tmp/issue2240-target-repo/README.md
(git-tracked area only; full listing below confirms no runs/ at all)
/tmp/issue2240-target-repo/README.md
/tmp/issue2240-target-repo/.git

=== git status inside target repo: nothing untracked ===
```

(a) the orchestrator's own state file exists and accumulated the tick-1
write across the tick-2 read; (b) the target repo's working tree gained
nothing (no `runs/`, `git status --porcelain` empty); (c)
`should_park()` returned `False` on the first tick and `True` on the
second, identical tick — the exact behavior #2238 reported as never
happening, now reproduced live as fixed.

This session did not spawn a full nested `claude -p` role session for
the provenance demonstration — doing so against a real GitHub-backed
target repo was judged out of proportion to a headless single-turn
delivery (nested session cost/duration, and no scratch GitHub repo was
available to point it at). The demonstration instead drives the actual,
unmocked fixed functions directly against real target-repo and
orchestrator-state directories on disk, which is what the scoping fix
itself changes; a full nested-spawn demonstration would additionally
exercise `spawn.py`'s subprocess/env-var plumbing, which this issue does
not modify.

## Open findings

- `consult.py`'s judge-trace path (`runs/patrol-judge-log.md`) has the
  same scoping bug and the same rejected "gitignore hides it" rationale
  in its own docstring (canonical: `consult.py:852-858`, read this
  session), but reanchoring it needs auditing its sibling paths in the
  same module for the `relative_to()` coupling issue #1313 fixed first —
  resolution path: a follow-up issue scoped to `consult.py` specifically.

## Next steps

None — loop_state is terminal (`landed`).

---

skill-verdict: other mounted skills not triggered — this change swaps one
existing accessor pattern (already established three times over in
`spawn.py`/`watchdog.py`/`events.py`) into a shared function and applies
the same mechanical edit at each of eleven call sites; no coupling/
cohesion threshold was crossed, no GoF pattern was considered, no data
structure/algorithm/performance tradeoff was made, and the module
structure was dictated by the issue's own explicit "single accessor" spec
and by matching the pre-existing `STATE_ROOT` convention rather than by
an open design decision.
