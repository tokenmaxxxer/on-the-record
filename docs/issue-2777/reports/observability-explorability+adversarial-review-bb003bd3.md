---
issue: 2777
role: observability-explorability+adversarial-review-bb003bd3
author: observability-explorability+adversarial-review-bb003bd3
skills: observability-explorability (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: same-commit
loop_state: landed
type: fix
breaking: false
verdict: pass — a forced gh-lookup failure now produces a distinct degraded-state line after the existing 3-tick failure-streak threshold (previously: silent for every tick, forever); #2768's 30-closed-subject noise fix still holds (re-run, 3/3); dry_run pairs byte-identical before/after under a degraded lookup; `_issue_is_open()` untouched; failing-test-name set vs `HEAD` identical (16/16); no new gh/git/subprocess call added
upstream:
  - path: gates/spawn_on_pr.py
    sha: same-commit
  - path: docs/issue-2652/reports/adversarial-review-58d892b0.md
    sha: aa653aeef72691cd6e05ea42797b8b273a424a39
---

# issue-2777 — observability-explorability+adversarial-review-bb003bd3 record

## What was done

Fixed `gates/spawn_on_pr.py::missing_verification()` so a failed bulk
`gh` issue-state lookup (`closure_sweep.issue_state_index_all()` returning
`ok=False`) reports its own degraded state instead of producing silent,
empty output for every subject on that tick.

canonical: `git diff HEAD -- gates/spawn_on_pr.py` (same-commit) — result:
```
$ git diff --stat HEAD -- gates/spawn_on_pr.py
 gates/spawn_on_pr.py | 14 +++++++++++++-
 1 file changed, 13 insertions(+), 1 deletion(-)
```

The change is confined to the top of `missing_verification()`, where this
function does its own `issue_states` fetch when the caller didn't supply
one (the real production call path — `spawn_missing_for_pr()` forwards
its own `issue_states=None` default straight through):

```python
    out: dict[str, int] = {}
    if issue_states is None:
        issue_states, ok = closure_sweep.issue_state_index_all(root)
        if spawn._watchdog_note_gh_failure(root, "spawn-on-pr", not ok):
            print("[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, "
                  "이번 틱 판정 보류 (연속 실패)")
        if not ok:
            issue_states = None
    if pr_index is None:
        pr_index, _ = closure_sweep._pr_index_all(root)
```

`spawn._watchdog_note_gh_failure` (`spawn.py` re-exports it from
`watchdog.py`) is the same consecutive-failure-streak helper
`watchdog.py`'s `closure-sweep` and `board-sweep:pr-index` branches
already use (issue #2196): a single blip resets the streak and stays
quiet; `WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD` (=3) consecutive
failures on the `"spawn-on-pr"` signal name print the new line. This
reuses existing persistent state (`watchdog_noise_state.json`, anchored
via `state_paths.STATE_ROOT`) — no new state file, no new `gh`/git/
subprocess call.

**`_issue_is_open()` itself is untouched** — still fail-closed on
`issue_states is None` (the must-not this issue names: fail-open there
would re-spawn observers for closed subjects, worse than silence). The
degraded-lookup case still `continue`s past every subject in the loop
exactly as before; only the new print, gated on the failure streak, is
new. `out` (the dict that drives spawning) is unaffected.

### Acceptance check 1 — force the gh lookup to fail, before/after

Built two trees: `/tmp/pre2777_wt` (a worktree at this branch's `HEAD`,
i.e. #2768's reorder with no #2777 fix) and this working tree (with the
fix). `/tmp/repro_2777.py` imports `spawn_on_pr` fresh from a given root,
monkeypatches `spawn.board()` to one OPEN subject with a genuinely
missing branch, monkeypatches `closure_sweep.issue_state_index_all` to
always fail (`(None, False)`), points `state_paths.STATE_ROOT` at a fresh
tmp dir, and calls `missing_verification(root, pr_index={})` for four
consecutive ticks, capturing `(out, stdout)` each tick.

acceptance: `python3 /tmp/repro_2777.py /tmp/pre2777_wt` (pre-fix) —
result:
```
tick 1: out={} stdout=''
tick 2: out={} stdout=''
tick 3: out={} stdout=''
tick 4: out={} stdout=''
```

acceptance: `python3 /tmp/repro_2777.py "$PWD"` (post-fix, this tree) —
result:
```
tick 1: out={} stdout=''
tick 2: out={} stdout=''
tick 3: out={} stdout='[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)\n'
tick 4: out={} stdout='[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)\n'
```

Pre-fix: silent forever, exactly the regression the issue names.
Post-fix: the third consecutive failure (streak threshold) prints a line
naming the degradation — distinct from both "nothing to report" (ticks
1-2, and every tick pre-fix) and the old unlabeled branch-missing noise
(`찾지 못했다` text does not appear in this output). `out={}` is
identical on every tick, both trees — no spawn-eligibility change.

This scenario is now also a standing regression check in
`gates/test_spawn_on_pr.py` — three new test functions:
`test_degraded_lookup_stays_quiet_below_the_failure_streak_threshold`,
`test_degraded_lookup_reports_its_own_state_once_streak_hits_threshold`,
`test_healthy_lookup_after_this_functions_own_fetch_stays_quiet`.

### Acceptance check 2 — #2768's 30-closed-subject fixture, re-run

acceptance: `python3 -m pytest -q gates/test_spawn_on_pr.py::test_closed_and_open_subjects_mixed_only_open_unmappable_branch_reported gates/test_spawn_on_pr.py::test_closed_issue_with_unmappable_branch_prints_nothing gates/test_spawn_on_pr.py::test_open_subject_with_unmappable_branch_still_reports_missing_branch` — result:
```
...                                                                      [100%]
3 passed in 0.86s
```
These are #2768's own regression tests (30 closed subjects + 1
open/unmappable + 1 open/mapped board) — untouched by this fix (my
change only fires on `issue_states is None`, and these tests always pass
an explicit `issue_states` dict), confirmed still green.

### Acceptance check 3 — `spawn_missing_for_pr(..., dry_run=True)` pairs, byte-identical

`/tmp/repro_2777_dryrun.py` builds a board with one subject that WOULD be
a spawn candidate under a healthy lookup (OPEN issue, deficit>0, branch
mapped to an OPEN PR), then forces `closure_sweep.issue_state_index_all`
to fail and calls `spawn_missing_for_pr(root, str(root), dry_run=True,
issue_states=None, backoff_state={}, pr_index=pr_index)` on both trees.

acceptance: `python3 /tmp/repro_2777_dryrun.py /tmp/pre2777_wt` (pre-fix) — result:
```
pairs: []
```
acceptance: `python3 /tmp/repro_2777_dryrun.py "$PWD"` (post-fix) — result:
```
pairs: []
```
Byte-identical (`[]` both sides) — `_issue_is_open()`'s pre-existing
fail-closed design already excluded this subject from `out`/`pairs`
before this fix touched anything; the new print does not change that.

### Four standing invariants, re-run live

- **No return of the retired role axis in any reshaped form**:
  canonical: `git diff HEAD -- gates/spawn_on_pr.py` (quoted above) —
  touches only the `issue_states is None` branch inside
  `missing_verification()` — no `role`/`kind` name list, no closed-set
  enumeration.
- **No new bug — failing-test set vs `HEAD`, as sets of names, not counts**:
  acceptance: `python3 -m pytest -q` (this tree, with fix + new tests) — result:
  ```
  16 failed, 556 passed, 3 xfailed
  ```
  acceptance: `cd /tmp/pre2777_wt && python3 -m pytest -q` (HEAD, no fix) — result:
  ```
  16 failed, 553 passed, 3 xfailed
  ```
  acceptance: `diff <(sort /tmp/pre2777_failed.txt) <(sort /tmp/post2777_failed_v2.txt)` (both files are sorted `grep '^FAILED'` output from the two runs above, captured this session) — result:
  ```
  IDENTICAL SETS
  ```
  Same 16 failing test **names** both sides (pre-existing `gh`/network-
  boundary failures unrelated to this change); the +3 delta is entirely
  this fix's own new passing regression tests.
- **No overhead increase**: the diff above adds one `spawn.
  _watchdog_note_gh_failure()` call inside the branch that already ran
  `closure_sweep.issue_state_index_all()` — no new `gh` call, no new bulk
  index, no new subprocess. The helper's own I/O is a small JSON
  read/write against `watchdog_noise_state.json`, the same file/helper
  `closure-sweep` and `board-sweep:pr-index` already use every tick — not
  new infrastructure.
- **Monitor and watch machinery must not go quieter**: this is the fix
  itself. Under a sustained degraded `gh` lookup, spawn-on-pr now prints
  a distinct line after 3 consecutive failed ticks instead of staying
  silent forever (acceptance check 1 above) — strictly quieter than
  pre-fix is no longer possible for this path, and the fix does not
  reintroduce the per-subject/aggregate noise #2768 removed (acceptance
  check 2, still green).

## Why

derived: reading `docs/issue-2652/reports/adversarial-review-58d892b0.md`
in full, this session (quoted sections below are from that read). The
prior adversarial review diagnosed the root cause precisely: #2768's
reorder made `_issue_is_open()` run before the branch check, so a failed
bulk `issue_states` fetch (`issue_states=None`) now fail-closes every
subject before the loop ever reaches the code that used to print. That
review's "Resolution path" named two options — (a) keep printing the
branch-missing line when `issue_states is None`, or (b) add an explicit
one-shot warning line mirroring `watchdog.py`'s `closure-sweep` pattern.

Option (a) was rejected: it would resurrect a form of the exact noise
#2768 removed, on a schedule that's now *harder* to reason about (per-tick,
per-subject, gated on a lookup failure rather than on issue state) —
and it says nothing about *why* the line appeared, leaving an operator to
guess whether the branch is really missing or the lookup just failed.
Option (b) — a single tick-level line naming the degraded lookup itself,
gated by the same consecutive-failure-streak convention already used by
every other `gh`-boundary check in `watchdog.py` — directly matches the
issue's own acceptance framing ("output that names the degradation,
distinct from both 'nothing to report' and the old unlabeled branch-
missing noise") and reuses an established codebase idiom instead of
inventing a new one.

The streak threshold (reuse of `WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD`,
already 3 elsewhere) was kept rather than warning on the very first
failure: the same "single blip 조용히 넘어간다" convention issue #2196
established for `closure-sweep` applies here for the same reason — a
transient one-tick `gh` hiccup is not itself actionable, and warning on
every blip would be a different flavor of new noise. The issue's own
framing (gh lookup failures "appeared repeatedly" the night this landed,
surfacing as a heartbeat advisory) describes a sustained condition across
many ticks, which a streak counter surfaces correctly; it does not ask
for a first-failure alarm.

`_issue_is_open()` was deliberately left untouched per the issue's
explicit must-not — the fix adds a report, not a different guess.

## Upstream basis

- `gates/spawn_on_pr.py` — the code under review/fix, same-commit as this
  record.
- `docs/issue-2652/reports/adversarial-review-58d892b0.md` @
  `aa653aeef72691cd6e05ea42797b8b273a424a39` — derived: read in full this
  session (see "## Why" above) — the independent adversarial review that
  found and reproduced this regression as its Open finding 1, which this
  issue was filed from.

## Open findings

None.

## Next steps

None — `loop_state: landed`. The fix, its regression tests, and this
record land together in one commit (build-now bypass, CORE_BUILD_NOW=1).

## What did not work

None — no reverted approach, no scope-exceeded stop. The design (reuse
`watchdog.py`'s existing consecutive-failure-streak helper rather than
inventing new state, gate the new print on failure alone, leave
`_issue_is_open()` untouched) worked on the first implementation and
needed no rework after the three acceptance checks and the four
invariant re-runs above.

skill-verdict: observability-explorability — not-applicable: this issue
is a scoped bugfix restoring one existing diagnostic print's visibility
in a degraded state, not designing a new dashboard/panel or an ad-hoc
query surface over raw events — the skill's stated trigger.
skill-verdict: adversarial-review — not-applicable: this session builds
the fix identified by a prior independent adversarial review
(`adversarial-review-58d892b0`); it is not itself tasked with a
structurally-independent evaluation of someone else's artifact, and
self-review of one's own just-written fix is exactly what that skill's
protocol exists to avoid substituting for.
other mounted skills: not triggered (work-in-english guidance followed —
this record, all code, comments, and test names are in English).
