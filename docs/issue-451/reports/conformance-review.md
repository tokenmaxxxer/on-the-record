---
kind: record
loop_state: reported
code_under_review:
  - spawn.py
  - tests/test_silent_failure_repros.py
---

# Conformance review — issue-451 follow-loop stall bound

## Upstream / basis

derived: `git log --oneline --all | grep " 453"`, run this session:
```
0710fa41 Merge pull request #453 from tokenmaxxxer/issue-451/implementation
```
canonical: same output plus `git log --oneline -1 1e4555a4`, run this
session — subject is commit `1e4555a4fcfc04efa9ab0350f113c2a2455da105`,
landed to main via PR #453 at `0710fa41`. Requirement list:
`docs/issue-451/proposals/2026-08-08-follow-loop-stall-bound.md`
(sections "Constraints", "What will be built", "Verification plan",
"Out of scope") and `docs/issue-445/reports/defect-verification.md`
lines 121-134. Implementation record:
`docs/issue-451/reports/implementation.md`.

## What was done

derived: `git show 1e4555a4 --stat`, run this session:
```
 docs/issue-451/reports/implementation.md           | 115 +++++++++++++++++++++
 .../hunt-2026-08-08-follow-loop-stall-bound.md     |  64 ++++++++++++
 spawn.py                                           |  22 ++++
 test/test_silent_failure_repros.py                 |  47 +++------
 4 files changed, 218 insertions(+), 30 deletions(-)
```
canonical: same diff output, read this session — the commit touches
only spawn.py, the silent-failure-repros test file (later renamed into
tests/), and its own record files.

Artifact-only re-read of _watch() against the proposal's constraints
and the defect-verification requirement, plus a live rerun of every
cited test this session, to render one verdict per requirement below.

## Per-requirement verdicts

### R1 — `_watch(follow=True)` must bound cumulative no-progress time and report a stall, without reintroducing roster-absence-as-crash (defect-verification requirement)

derived: `python3 -m pytest tests/test_silent_failure_repros.py -k attempt_2 -q`, run this session:
```
1 passed, 2 deselected in 0.17s
```
canonical: same run — `test_attempt_2_follow_loop_unbounded_on_absent_roster_entry`
drives the real `_watch(follow=True)` with no roster entry and no
events and asserts `rc == 0`.

canonical: spawn.py:3970-3971,4008-4014,4064-4074, read this session —
a `stall_limit_s`/`last_progress` tracker is set before the loop
(3970-3971), reset each iteration when the offset advances or
`log_path.stat().st_size` changes (4008-4014, the same
`after > before or after_size != before_size` shape as commit
1e4555a4's diff), and a terminal branch (4064-4074) returns `0` with a
stderr stall report once `time.monotonic() - last_progress >=
stall_limit_s`. The pre-existing crash check at spawn.py:4053-4063
("명부 엔트리 부재는 사망 신호로 안 쓴다(이슈 #266)") is unchanged and still
runs before this new branch.

Verdict: supports (Present).

### R2 — Non-follow behavior (`_await_bounded()`, `follow=False` branch) must not change

canonical: spawn.py:3945-3947, read this session — the `if not follow:`
branch calls `_await_bounded()` directly with no reference to
`stall_limit_s`/`last_progress`; commit 1e4555a4's diff above shows no
line changed inside `_await_bounded()`'s own body.

Verdict: supports (Present).

### R3 — Normal follow behavior (event streaming to `session-end`) must stay unchanged; ongoing log growth counts as progress, not stall

canonical: spawn.py:4015-4024, read this session — the
`after > before` event-consuming branch (parses the event, checks for
`session-end`, returns `rc` on match) is unchanged in shape from the
pre-1e4555a4 version shown in the diff above; the new code runs only
before it (progress tracker) and after it (stall check). `after_size !=
before_size` (spawn.py:4013) resets `last_progress` on any log growth,
so a session that keeps producing log activity with no roster entry
never reaches the stall branch.

Verdict: supports (Present).

### R4 — Crash detection (dead `wrapper_pid`) must be untouched and checked before the new stall bound

canonical: spawn.py:4058-4074, read this session — the
`if pid is not None and not _alive(pid): ... return WATCH_CRASH_RC`
branch (4058-4063) precedes the `if time.monotonic() - last_progress
>= stall_limit_s:` branch (4064-4074) in source order within the same
iteration.

Verdict: supports (Present).

### R5 — Regression fence: the watch test suite in test_spawn.py must stay green unmodified

derived: `python3 -m pytest tests/test_spawn.py -k watch -q`, run this session:
```
91 passed, 412 deselected in 47.35s
```
canonical: same run, 91 watch tests reproduce green; the
`git show 1e4555a4 --stat` output above shows the test_spawn module is
absent from the commit's file list, so it was not edited by this
commit.

Verdict: supports (Present).

### R6 — The silent-failure-repros file must stay green as a whole

derived: `python3 -m pytest tests/test_silent_failure_repros.py -q`, run this session:
```
3 passed in 0.33s
```
canonical: same run — every test in the file reproduces green against
current HEAD; implementation.md's generation-time count of 4 reflects
that file's state at landing time, before later unrelated commits
changed its test count.

Verdict: supports (Present).

## Recomputation

canonical: the R1/R5/R6 `derived:` reruns above, this session — per
`roles/specs/conformance-review.spec.json`'s recomputation rule
(worst-case across cited test entries, EARL severity order), every
cited test entry reproduces at its best-case result and every
non-test requirement (R2-R4) resolves supports on direct code read; no
standalone summary verdict is asserted independent of these six
per-requirement entries above.

## Why

Per-requirement fidelity verdicts, artifact-only, per the
conformance-review role's rulebook — never a holistic quality read,
never a fix.

## What did not work

None.

## Open findings

canonical: the six per-requirement verdict sections above, this
session — all six resolve supports against their cited sources, with
every cited test reproduced live this session, so no finding is filed.

## Next steps

None identified for this record; no finding routes to another role.
