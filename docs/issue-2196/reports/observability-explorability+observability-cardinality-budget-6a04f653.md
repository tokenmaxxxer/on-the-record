---
issue: 2196
role: observability-explorability+observability-cardinality-budget-6a04f653
author: observability-explorability+observability-cardinality-budget-6a04f653
loop_state: landed
code_under_review:
  - gates/spawn_on_pr.py
  - watchdog.py
  - spawn.py
  - test/test_watchdog_heartbeat_noise.py
type: bugfix
breaking: none — adds a suppression layer on top of existing print lines;
  no signal is dropped, only repeated identical lines are collapsed
verdict: pass
upstream:
  - path: watchdog.py (`_watchdog_note_unmappable_pr`, `_watchdog_note_gh_failure`)
    sha: 30ca2a6970e2a4a08c0ea9baf3298760031201bf
---

# issue-2196 — observability-explorability+observability-cardinality-budget-6a04f653 record

## What was done

canonical: `gh issue view 2196 --comments` (read this session).

Two of the issue's three noise categories were already fixed and landed by
a prior session before this one started: `_watchdog_note_gh_failure`
(watchdog.py:523) and `_watchdog_note_unmappable_pr` (watchdog.py:545),
committed in PR #2200 (`b089b0435`) — derived: `git log -S
"_watchdog_note_unmappable_pr" --oneline -- watchdog.py` — result:
`b089b0435 issue-2196: suppress repeating watchdog heartbeat noise (#2200)`.
Their own regression tests were later deleted wholesale by an unrelated
operator decision (issue #2525, "retire the plugin's own test suite") —
derived: `git log --oneline --all --diff-filter=D -- tests/test_watchdog_heartbeat_noise.py`
— result: `a555e169 issue-2525: retire the plugin's own test suite
(#2528)`. That path (plural `tests/`) was removed from the working tree by
that commit and is untracked/absent today — distinct from the still-live
singular `test/` directory this session's new test file lives in. The
underlying suppression logic in watchdog.py itself was untouched by that
deletion and still works (re-verified this session, see Acceptance below).

The issue's 2026-08-27 follow-up comment reported fresh evidence of a
third, previously unnamed category: `gates/spawn_on_pr.py`'s
`missing_verification()` re-prints an identical
`[spawn-on-pr] {subject}: deliverable 브랜치를 pr_index 에서 찾지 못했다 —
이번 틱은 건너뜀` line every single tick it runs, for every subject whose
deliverable branch is permanently absent from `pr_index` (old issue,
branch deleted long ago) — derived: `git show HEAD~1:gates/spawn_on_pr.py
| sed -n '300,305p'` — result (pre-fix): a single unconditional `print()`
with no suppression state, unlike the board-sweep per-PR path a few
hundred lines away in watchdog.py which already had one-shot suppression
for the structurally identical condition (a PR/subject whose branch will
never resolve).

This session's change (`gates/spawn_on_pr.py`, `watchdog.py`, `spawn.py`):
added `_watchdog_note_unmappable_subject_branch(root, subject)`
(watchdog.py:563-577), the same one-shot-then-suppress marker idiom as
`_watchdog_note_unmappable_pr`, sharing the same persisted
`watchdog_noise_state.json` (new top-level key
`unmappable_subject_branch_reported`). `missing_verification()` now calls
it before printing the per-subject line: first sighting of a given subject
prints individually and records it; a later tick with the same subject
still unmapped is counted instead of printed, and the accumulated count
collapses into one line
(`[spawn-on-pr] N건 이전에 보고된 매핑-불가 subject — 계속 무시 (반복 안
찍음)`) at the end of the sweep. The helper is exported from `watchdog.py`
onto the `spawn` module object (spawn.py:224) the same way its sibling
`_watchdog_note_unmappable_pr` already is, so `gates/spawn_on_pr.py` (which
imports `spawn`, not `watchdog`, directly) can call it.

The real-signal-buried-in-noise example from the issue
(`issue-2576: subject PR 이 이미 merged`) needed no change: that line is
already gated by `missing_verification()`'s pre-existing `merged_seen`
sticky cache (spawn_on_pr.py:289-295, issue #2165), which persists the
MERGED fact and skips the subject — including its print — on every later
tick. It only ever printed once; the issue's own evidence was that it
printed once *inside* the unsuppressed wall of subject-branch-not-found
lines, which this fix now suppresses around it.

## Why

canonical: issue #2196 body and 2026-08-27 comment (`gh issue view 2196
--comments`, read this session).

The issue's general rule — "a line that recurs identically and requires no
action either gets suppressed after first emission or collapsed into a
count" — was already applied to two categories (board-sweep per-PR mapping
failures, transient gh failures) but not to a third the issue's own
follow-up comment surfaced: spawn-on-pr's per-subject branch-not-found
line. That line meets the same criteria (identical text, recurs every
tick the sweep runs, requires no action — the branch is gone forever) and
sits in the same full-board-sweep call path (`_board_wide_sweep` ->
`missing_verification`), so it was fixed under the same rule rather than
filed as a new issue.

The fix reuses the exact idiom already validated for board-sweep
(`_watchdog_note_unmappable_pr`) instead of inventing a new suppression
mechanism: same persisted-state file, same one-shot-then-count shape, same
print format for the collapsed line — minimizes new surface area and keeps
the two structurally-identical categories readable as the same pattern.

Suppression must not silence new information (acceptance bullet 3): the
one-shot marker is keyed by `subject`, not by tick — a subject that starts
mapping is a different code path entirely (branch found -> `continue`
never reached), and a subject seen for the first time as unmappable always
gets its individual line regardless of how many other subjects are already
suppressed that same tick. Verified directly (see Acceptance).

## What did not work

None — no dead ends or reverted attempts this session.

## Acceptance

Acceptance requirement met — checked: `python3 -m pytest
test/test_watchdog_heartbeat_noise.py -v` — result: 6 passed. derived:
`python3 -m pytest test/test_watchdog_heartbeat_noise.py -v`:
```
TestPerPrMappingFailureSuppression::test_two_ticks_unchanged_state_suppresses_repeat_lines PASSED
TestPerPrMappingFailureSuppression::test_genuinely_new_unmappable_pr_still_emits_on_its_own_tick PASSED
TestTransientGhFailureSuppression::test_requirement_drift_single_failure_suppressed_then_warns_on_streak PASSED
TestTransientGhFailureSuppression::test_requirement_drift_success_resets_streak PASSED
TestSpawnOnPrUnmappableSubjectBranchSuppression::test_two_ticks_unchanged_state_suppresses_repeat_lines PASSED
TestSpawnOnPrUnmappableSubjectBranchSuppression::test_genuinely_new_unmappable_subject_still_emits_on_its_own_tick PASSED
```

Bullet-by-bullet:
- "two consecutive full-rescan heartbeat ticks with unchanged repo state
  produce no repeated per-PR mapping-failure lines": covered for
  board-sweep's own per-PR path by
  `TestPerPrMappingFailureSuppression::test_two_ticks_unchanged_state_suppresses_repeat_lines`
  (pre-existing logic, re-verified — no code change needed there) and for
  the newly-fixed spawn-on-pr per-subject path by
  `TestSpawnOnPrUnmappableSubjectBranchSuppression::test_two_ticks_unchanged_state_suppresses_repeat_lines`.
- "a transient single-tick gh failure produces no warning line; N
  consecutive failures still does — test both directions": covered by
  `TestTransientGhFailureSuppression` (both tests; pre-existing logic,
  re-verified — no code change needed there).
- "genuinely new or changed conditions still emit on the tick they
  appear": covered by both `..._still_emits_on_its_own_tick` tests, one
  per category.

Also ran the full `test/` suite to check for regressions: derived:
`python3 -m pytest test/ -q` — result: 15 failed, 290 passed (pytest-xdist
parallel run). All 15 failures are pre-existing and unrelated to this
change — checked: `git stash -u && python3 -m pytest
test/test_convention_equivalence.py test/test_local_dependency_env.py -q
&& git stash pop` on the pre-change tree — result: the same 3 of those
15 (`ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape`,
`BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim`,
`CallSiteWiringTest::test_origin_captured_before_workspace_reassignment`)
fail identically before this session's changes; the other 12
(`test_spawn_cross_family_skill_selection.py`,
`test_spawn_artifact_skill_pairing.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`) are unrelated
skill-selection/skill-judge tests, in files this session never touched.
Ran `test/test_watchdog_heartbeat_noise.py` together with
`test/test_spawn_attempt_staleness.py` (issue #2511's PR #2594, which
landed on `roster.py`/watchdog's sweep minutes before this session
started) to confirm no interaction — derived: `python3 -m pytest
test/test_watchdog_heartbeat_noise.py test/test_spawn_attempt_staleness.py
-q` — result: 31 passed.

## Upstream basis

`watchdog.py`'s `_watchdog_note_gh_failure`/`_watchdog_note_unmappable_pr`
and `WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD` — sha:
`30ca2a6970e2a4a08c0ea9baf3298760031201bf` (this branch's base, landed by
PR #2200 before this session). This session's
`_watchdog_note_unmappable_subject_branch` (watchdog.py) and its
`gates/spawn_on_pr.py` call site are new work in this same commit — sha:
same-commit.

## Open findings

None open. One thing considered and deliberately left alone: the
`unmappable_subject_branch_reported`/`unmappable_prs_reported` marker sets
in `watchdog_noise_state.json` grow monotonically (never pruned) — matches
the pre-existing behavior of `_watchdog_note_unmappable_pr` from #2200
untouched by this session, and both mark genuinely permanent conditions
(deleted branches), so unbounded growth here tracks the count of dead
subjects/PRs ever seen, not request/user volume — not the kind of
cardinality risk the mounted `observability-cardinality-budget` skill
targets (see skill-verdict below).

## Next steps

None — issue #2196's three acceptance bullets are met and the fix is
committed on this branch. loop_state: landed.

## Skill verdicts

skill-verdict: observability-explorability — not-applicable: this task
suppresses repeated heartbeat log lines in an orchestrator watchdog, not
designing a dashboard or incident-investigation surface; no panels, no
raw-vs-aggregated-data tradeoff involved.
skill-verdict: observability-cardinality-budget — not-applicable: the
suppression state (`watchdog_noise_state.json`) is a local JSON marker
file keyed by PR number/subject string, not a metric label/tag shipped to
a metrics TSDB (Prometheus etc.) — the unbounded-growth concern this skill
targets (series-count explosion from a high-cardinality label) doesn't
apply to a flat on-disk dedup set.
