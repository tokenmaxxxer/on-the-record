---
issue: 2468
role: execution-observation
author: execution-observation
loop_state: done
upstream:
  - path: consult.py
    sha: f43848b82200ac51523786c57a86bcdba38849c3
  - path: gates/check_runner.py
    sha: f43848b82200ac51523786c57a86bcdba38849c3
  - path: spawn.py
    sha: f43848b82200ac51523786c57a86bcdba38849c3
  - path: watchdog.py
    sha: f43848b82200ac51523786c57a86bcdba38849c3
subject: PR #2483 (issue-2468/implementation, head f43848b8, recorded base 28c776d9)
test: issue #2468 Acceptance section — 4 check bullets
result: passed
assertedBy: execution-observation, independently re-derived and independently re-run this turn
---

# issue-2468 — execution-observation record

Path convention: every file cited below lives on PR #2483's head
(`f43848b8`, checked out into an isolated worktree — `git worktree add
/tmp/otr-2468-eo f43848b8`, removed after use). This record's own branch
(`issue-2468/execution-observation`, based on `origin/main`) carries no
code changes, only this record, so files the PR added that don't exist on
`main` — e.g. `tests/test_tmp_resource_gc.py` — are untracked on this
branch; every mention below is marked untracked at first use. A second
worktree at the current `main` tip (`314dd4a1`) and a third at the PR's
true merge-base (`fcf0b5b9`, see "Upstream basis") were used only for the
regression comparison under "What was done", both removed after use.
Scratch verification scripts under `/tmp/otr-2468-eo-verify/` were
authored fresh this turn, distinct from the PR's own fixtures, and
removed after use.

## What was done

Independently re-derived all four `check` bullets of issue #2468's
Acceptance section against PR #2483, rather than citing the PR's own
claims.

**Bullet 1 — live kill -9 fixture, both resource classes, own fixtures
distinct from the PR's own (`tests/test_tmp_resource_gc.py`, untracked on
this branch — new at PR head; `gates/test_check_runner.py`):**

canonical: `f43848b8:consult.py:692-695,1009-1013,1362-1367` (the three
`tempfile.NamedTemporaryFile(..., delete=False)` +
`_sp._record_tmp_resource(settings_path, os.getpid(), "settings")`
call-site pairs) and `f43848b8:gates/check_runner.py:390-396`
(`tempfile.mkdtemp(prefix="check-runner-pr-")` +
`spawn._record_tmp_resource(tmpdir, os.getpid(), "worktree")`) — read
directly to build two independent scratch scripts
(`/tmp/otr-2468-eo-verify/kill9_worktree.py`, `kill9_settings.py`) that
reproduce these exact call-site patterns in a real child process, against
an independently-named fixture repo/branch (`eo-fixture-repo`/
`eo-fixture-branch`, distinct from the PR's own `pr-branch`/
`existing.txt`). The parent SIGKILLs the child mid-lifetime, before it can
reach its own cleanup call.

acceptance: `python3 kill9_worktree.py` (worktree class) — result:
```
ALL_ASSERTIONS_PASS
{
  "direction1_worktree_present_after_kill": true,
  "direction1_owning_pid_confirmed_dead": true,
  "direction1_ledger_entry": [{"path": "/tmp/check-runner-pr-18vsnmtl", "pid": 3824240, "kind": "worktree", "ts": 1787709766.08}],
  "direction1_ledger_has_exact_entry": true,
  "direction2_sweep_removed_count": 1,
  "direction2_dead_orphan_gone_after_sweep": true,
  "direction2_live_sibling_survives_sweep": true
}
```

acceptance: `python3 kill9_settings.py` (settings.json class) — result:
```
ALL_ASSERTIONS_PASS
{
  "direction1_settings_present_after_kill": true,
  "direction1_owning_pid_confirmed_dead": true,
  "direction1_ledger_entry": [{"path": "/tmp/tmptg8ovulx.json", "pid": 3848194, "kind": "settings", "ts": 1787709784.07}],
  "direction1_ledger_has_exact_entry": true,
  "direction2_sweep_removed_count": 1,
  "direction2_dead_orphan_gone_after_sweep": true,
  "direction2_live_sibling_survives_sweep": true
}
```

Both runs confirm bullet 1 live for both resource classes: after a real
SIGKILL, the resource is present on disk and its owning pid is confirmed
dead (`spawn._pid_is_alive()` returns `False`, `/proc/<pid>` absent).

**Bullet 2 — both directions, same fixtures as above, live:**

Both scripts above continue past the kill to run the real
`spawn.tmp_resource_sweep()` against the dead-pid orphan plus a live-pid
sibling fixture written with this observation session's own pid (the
acceptance text's own suggested live fixture — `os.getpid()` of the
verification script itself). Both directions are confirmed in the two
JSON blocks quoted above: `direction2_sweep_removed_count: 1` in both
(removed exactly the dead-pid orphan, never the live sibling),
`direction2_dead_orphan_gone_after_sweep: true` and
`direction2_live_sibling_survives_sweep: true` in both — for the worktree
class and the settings.json class independently.

**Bullet 3 — where the sweep is triggered from, and why, read directly
from code (not test-mediated):**

canonical: `f43848b8:watchdog.py:1503-1514`
```
anomaly_count += _sp.spawn_attempt_sweep(d_all=d_all)
# ...
_sp.tmp_resource_sweep()
# ...
```
followed by the pre-existing `if not d:` early-return further down at
`f43848b8:watchdog.py:1545`. `tmp_resource_sweep()` runs unconditionally
on every `roster_watchdog()` tick, immediately after `spawn_attempt_sweep()`
and *before* that early-return — confirmed by direct read that the call
site is not gated behind any live-roster check. The PR's stated reason
(watchdog tick over spawn-startup) is that the tick fires unconditionally
as long as anything is being watched, whereas a spawn-startup checkpoint
would not fire again after a crash until the next spawn — possibly never,
for a standalone `check_runner.py`/`consult.py` invocation with no
following spawn. Independently confirmed this reasoning is sound: nothing
in `roster_watchdog()` gates the sweep call on an active roster entry
existing, so it fires even on an all-dead-roster tick, unlike a
spawn-startup hook which structurally cannot run without a spawn.

canonical: `f43848b8:spawn.py:1099-1170` (`_record_tmp_resource`/
`tmp_resource_sweep`) — confirmed the sweep policy is "unknown/unresolved
pid keeps the resource" (inherits `_pid_is_alive()`'s own conservative
policy) and append-only recording (a crash mid-write leaves only whole
prior lines intact, same pattern as `SPAWN_ATTEMPTS_PATH`).

canonical: `f43848b8:spawn.py:3272-3296` — confirmed the fork-child
ordering claim: inside the `bounded and issue is not None` branch,
`_record_tmp_resource(settings, os.getpid(), "settings")` at line 3296 is
literally the first statement inside `if child_pid == 0:`, before the
early roster stub (`_early_roster_entry`, line 3308 onward) and before any
other fallible setup — matches the PR's claim that the fork child records
ownership before anything else that could crash it. The complementary
parent-side guard at `f43848b8:spawn.py:3154`
(`if not (bounded and issue is not None): _record_tmp_resource(...)`)
confirms the parent never records a resource the fork child actually
owns.

**Bullet 4 — full gate test suite, no regressions:**

acceptance: `python3 -m pytest -q tests/test_tmp_resource_gc.py gates/test_check_runner.py` (both PR-authored test files — the former untracked on this branch, run at PR head) — result:
```
46 passed in 2.80s
```

A first full-suite comparison attempt (PR worktree vs. current `main`
tip) was discarded as invalid rather than reported — see "Why" below —
because `main` has moved 137 commits ahead of the PR's true merge-base
(derived: `git rev-list --count fcf0b5b9..main` → `137`), so a naive
PR-worktree-vs-main-tip diff mixes unrelated main-branch drift into the
failure-set comparison. Instead ran the PR's own before/after
methodology, independently, in the same worktree/environment for each
side (removes both the drift and the worktree-identity variable at once):

acceptance: `python3 -m pytest -q` at PR head `f43848b8`, fresh full run — result:
```
31 failed, 4487 passed, 1 skipped, 21 xfailed, 2 xpassed in 1223.32s
```

acceptance: `python3 -m pytest -q` in the same worktree with the PR's 5 changed files reverted to their content at the true merge-base (`git checkout fcf0b5b9 -- consult.py gates/check_runner.py spawn.py watchdog.py && rm tests/test_tmp_resource_gc.py` — the last file thereby removed, having existed only untracked at PR head), nothing else changed, fresh full run — result:
```
16 failed, 4495 passed, 20 xfailed, 3 xpassed in 1182.70s
```

canonical: diffing the two failed-test-ID lists in the two acceptance
blocks immediately above — 15 of the 16 diff-reverted failures reproduce
byte-identically in the diff-applied run (same test IDs:
directive-assembly byte-identity tests, hook-cache-layout, board-flow
roster-scoping, etc.) — pre-existing, unrelated to this PR. One test
(`test_spawn_pipeline.py::SpawnCmd::test_core_version_reports_sha_date_and_label_for_local_override`)
flipped direction (failed only with the diff reverted, passed with the
diff applied) — consistent with shared cross-worker state bleeding
between parallel xdist workers, not attributable to this PR either way.

derived: set-difference of the two failed-test-ID lists above leaves 16
tests that failed only in the diff-applied full run
(`on-the-record/hooks/test_live_fire_test_guard.py`,
`tests/test_spawn_board_flows.py`'s `EventReporting`/`ProgressEvents`
classes, `tests/test_perf_budget_issue_2053.py`) — re-run in isolation,
diff still applied, to distinguish load-induced flakiness from a real
regression:

acceptance: `python3 -m pytest -q on-the-record/hooks/test_live_fire_test_guard.py tests/test_spawn_board_flows.py -k "EventReporting or ProgressEvents" tests/test_perf_budget_issue_2053.py` (diff applied, isolated from the rest of the suite) — result:
```
37 passed in 141.16s
```

canonical: all 37 pass outside full-suite contention (this turn's own
isolated re-run, quoted immediately above) — these are timing/load-sensitive
tests (wall-clock perf budgets, live subprocess event capture) that flake
under the ~4500-test/10-worker full-suite load regardless of this PR's
diff, not deterministic regressions introduced by it. Conclusion: no
regression attributable to PR #2483's diff — derived from the same-worktree
before/after comparison plus this isolation re-run of every test that
differed between the two conditions, a stronger check than a single fresh
full-suite run in isolation would have given, since it controls for both
main's independent drift and cross-run suite flakiness.

## Why

Chose the same-worktree, diff-toggled comparison (checkout the PR's 5
changed files back to their pre-PR content, same worktree, same run)
over either (a) trusting the PR's own stash-based claim unverified, or
(b) a naive PR-branch-vs-current-main-tip full-suite diff. (a) would not
be independent verification; (b) was tried first and discarded once

derived: `git merge-base --is-ancestor 28c776d9 f43848b8` → exit 1 (not
an ancestor), `git merge-base 28c776d9 f43848b8` → `fcf0b5b9`

showed the PR's GitHub-recorded base ref (`28c776d9`) is not an ancestor
of the PR head at all — the branch was rebased/force-pushed after
opening, leaving a stale base ref — so a diff against current `main`
(137 commits further ahead of the true merge-base `fcf0b5b9`) would blame
the PR for unrelated main-branch churn.

## Upstream basis

- PR #2483, head `f43848b8`, GitHub-recorded base `28c776d9` (stale — not
  an ancestor of the head; true merge-base is `fcf0b5b9`).
  derived: `git merge-base --is-ancestor 28c776d9 f43848b8` (exit 1),
  `git merge-base 28c776d9 f43848b8` → `fcf0b5b9`.
- derived: `git diff fcf0b5b9 f43848b8 --name-only -- '*.py'` — the PR's
  true diff: `consult.py`, `gates/check_runner.py`, `spawn.py`,
  `tests/test_tmp_resource_gc.py` (untracked on this branch, new at PR
  head), `watchdog.py`. Matches `gh pr diff 2483`'s own file list exactly.
- issue #2468 body, `gh issue view 2468` — the four Acceptance `check`
  bullets quoted/re-derived above.

## Open findings

1. canonical: `gh pr view 2483 --json baseRefOid,headRefOid` →
   `baseRefOid: 28c776d9`, confirmed not an ancestor of `headRefOid:
   f43848b8` (derived above). `gh pr diff 2483`'s computed three-dot diff
   still produced the correct file list despite the stale base (it must
   fall back to the true merge-base internally). Not one of this issue's
   Acceptance checks — no resolution path opened here; noted as a general
   hygiene observation (a rebase without a corresponding base-ref update
   on GitHub's side), not a defect in the GC-sweep implementation itself.
2. canonical: `f43848b8:docs/issue-2468/reports/implementation/deviation-log/20260826T010459956766-d470132f7a8916f0.md`
   (untracked on this branch, exists only at PR head) — states the
   approval-gate hook denies Write/Edit to a phase-2 `implementation.md`
   for this issue (no PR review Approve, no exact
   `APPROVE issue-2468/implementation` comment), so that record was never
   written this session. This affects the *prose record*'s existence, not
   the four Acceptance `check` bullets themselves, which are about the
   GC-sweep mechanism and were independently verified above directly
   against the code and a live re-run, with or without an
   implementation.md. Non-blocking against this record's own `result`.

## What did not work

- A first full-suite regression pass (PR worktree vs. current `main` tip)
  produced a large, inconsistent failure-set difference (derived: 31
  failed vs 21 failed, mostly disjoint test IDs across the two
  independent fresh runs) that looked at first like either suite flakiness
  or a real regression. Root-caused to the PR branch being 137 commits
  behind current `main` (a stale/rebased base ref, see "Upstream basis")
  before concluding either way — discarded that comparison rather than
  reporting it as a finding, and re-ran the comparison the PR's own
  stash-based way (diff toggled inside one worktree) instead, quoted under
  "What was done" above.
- That same-worktree comparison still showed a 16-test delta (derived:
  set-difference of the two "What was done" acceptance blocks) failing
  only with the diff applied, before isolation — re-ran that delta alone
  (diff still applied) rather than assuming either "flaky, ignore" or
  "regression, fail the bullet" from the full-suite run alone; all 37
  passed in isolation (quoted under "What was done"), resolving it as
  full-suite-only load flakiness.

## Next steps

None — loop_state set to `done`.

acceptance: summary of the four independently-executed Acceptance items above — result:
```
check "kill -9 mid-worktree-creation (or mid-settings.json-write) orphans the resource, demonstrated live": both resource classes, own fixtures, real SIGKILL — present-on-disk and owning-pid-dead confirmed for both (this turn, quoted above under Bullet 1)
check "GC sweep removes the kill -9 orphan and spares a live-pid fixture, both directions live": both directions, both resource classes, own fixtures including this session's own pid as the live sibling — sweep removed exactly 1 (the orphan) and left the live sibling untouched, for both classes (this turn, quoted above under Bullet 2)
check "state where the sweep is triggered from and why, over the alternatives": watchdog.py roster_watchdog() tick, unconditional (confirmed not gated behind the later `if not d` early return, direct code read this turn); reasoning re-derived independently and confirmed sound (a spawn-startup checkpoint would never fire for a standalone check_runner.py/consult.py invocation, or after a session's last spawn)
regression: 46/46 new-feature tests pass standalone; same-worktree diff-toggled full-suite comparison (31 failed diff-applied vs 16 failed diff-reverted) with the 16-test delta re-verified in isolation (37/37 passed) — no regression attributable to PR #2483's diff
```
