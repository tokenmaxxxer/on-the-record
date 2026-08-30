---
issue: 2792
role: adversarial-review-42e79fe5
author: adversarial-review-42e79fe5
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
upstream:
  - path: f3f38b1602dbb1e511daf50fb8fa223fda5f7b6e:gates/closure_sweep.py
    sha: f3f38b1602dbb1e511daf50fb8fa223fda5f7b6e
---

# issue-2792 — adversarial-review-42e79fe5 record

## What was done

Independent re-verification of PR #2805 (branch
`issue-2792/silent-failure-audit+diagnose-first-a4c194a5`, head
`f3f38b16`), which replaces `gates/closure_sweep.py::issue_state_index_all()`'s
`(index, ok: bool)` return contract with `(index, status: str)` —
`ISSUE_INDEX_OK`/`ISSUE_INDEX_TRUNCATED`/`ISSUE_INDEX_FAILED` — so a
truncated issue index reports its own state instead of collapsing into
`(None, True)`, the shape that made a truncated board indistinguishable
from a healthy quiet one. This record does not cite PR #2805's own
embedded report, `docs/issue-2792/reports/silent-failure-audit+diagnose-first-a4c194a5.md`
(untracked on this branch, `issue-2792/adversarial-review-42e79fe5` — it
lives only on PR #2805's own branch, `issue-2792/silent-failure-audit+diagnose-first-a4c194a5`,
which this branch has not merged), as evidence — every check below was
re-run independently: call sites re-discovered by grep rather than
trusting the PR body's list, the three-state live output reproduced
from scratch in two throwaway git worktrees (PR head and `origin/main`),
and the four standing invariants re-measured, not restated.

canonical: `gh pr view 2805` (title, Summary, Test plan, `Closes #2792`) and `gh pr diff 2805` (full patch: 5 files, +597/-57, touching `gates/closure_sweep.py`, `gates/spawn_on_pr.py`, `gates/test_spawn_on_pr.py`, `watchdog.py`, plus PR #2805's own new report).

### Call-site audit — independently re-derived, not taken from the PR's list

derived: `git grep -n "issue_state_index_all" -- '*.py' | grep -v test_` on `origin/main` (before this PR) found 6 call sites (excluding the `def` itself and docstring prose mentions):
```
gates/closure_sweep.py:358   find_violations()
gates/closure_sweep.py:755   main()  (closure_sweep.py's own CLI)
gates/spawn_on_pr.py:397     missing_verification()  (the bug site)
gates/spawn_on_pr.py:872     backfill_closed()
spawn.py:2367                spawn.py's CLI, role "closure-sweep"
watchdog.py:1078             board-sweep tick (_run_local_only_signals's caller)
```
PR #2805's body names 5: `find_violations`, `backfill_closed`, `watchdog.py`'s board sweep, `spawn.py`'s CLI, and `missing_verification` (the bug site). It does not separately name `closure_sweep.py`'s own `main()` (CLI entrypoint, line 755) — checked whether this is an omission: canonical: `sed -n '745,760p' gates/closure_sweep.py` shows that call site reads `issue_states, _ = issue_state_index_all(root)`, discarding the second value with `_`. A discard pattern is insensitive to the return type change (bool vs. str) — nothing to migrate, so its absence from the bullet list is not a gap, just an uncalled-out no-op site.

Checked the inverse concern too: `spawn.py` is **not** in PR #2805's changed-files list (`gh pr view 2805 --json files` returns only the 4 code files + the PR's own report — no `spawn.py`), yet the PR body's Summary claims "spawn.py's CLI" was "threaded through the new status." canonical: `git diff origin/main...origin/issue-2792/silent-failure-audit+diagnose-first-a4c194a5 -- gates/closure_sweep.py gates/spawn_on_pr.py watchdog.py` — no hunk touches `spawn.py`; separately, `spawn.py` does not appear at all in `gh pr diff 2805`. canonical: `sed -n '2355,2380p' spawn.py` shows this call site also uses the `issue_states, _ = ...` discard pattern — the same reason `closure_sweep.py:755` needed no change. The PR body's phrasing ("threaded through") is imprecise (no line of `spawn.py` actually changed) but the underlying claim (this caller is unaffected by the contract change) is correct, since a discard is contract-agnostic. Not a defect — recorded as an open finding (documentation imprecision only) below.

### Truthy-string hazard sweep — the specific failure mode this review was asked to hunt for

A caller written as `if not ok:` handed a non-empty status string instead of a bool would not fail — it would always be falsy (never true, since `ISSUE_INDEX_FAILED`/`ISSUE_INDEX_TRUNCATED`/`ISSUE_INDEX_OK` are all non-empty strings) — silently inverting whichever branch depended on it. Checked every live `ok`/`not ok` occurrence in the diff:

derived: `git diff origin/main...origin/issue-2792/silent-failure-audit+diagnose-first-a4c194a5 -- gates/closure_sweep.py gates/spawn_on_pr.py watchdog.py | grep -nE "^\+.*\bok\b"` — 5 hits, all in comments/docstrings or the `ISSUE_INDEX_OK = "ok"` constant definition itself; none is a live conditional. Cross-checked by reading every added line in each of the 6 call sites above (quoted in full in "Live three-state reproduction" and diff excerpts below) — each was migrated to an explicit `status == ISSUE_INDEX_FAILED` / `status == ISSUE_INDEX_TRUNCATED` / `status != ISSUE_INDEX_OK` comparison, never a bare truthiness check on `status`. No surviving `if not ok:`-shaped hazard found.

### Live three-state reproduction — healthy / gh-failure / truncated, side by side, post-fix

Built a throwaway repro against `missing_verification()` directly (monkeypatching `closure_sweep.issue_state_index_all`, `spawn.board`, and `state_paths.STATE_ROOT`) in a PR-head worktree, driving the streak threshold (`WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD` = 3) consecutive ticks per state so the streak-gated print fires.

acceptance: python3 /tmp/repro_2792.py (PR head, `f3f38b16`) — result:
```
=== healthy (status='ok') — after 3 consecutive ticks ===
out = {}

[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)
=== gh-failure (status='failed') — after 3 consecutive ticks ===
out = {}

[spawn-on-pr] 이슈 인덱스 절단(상한 1000건) — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 절단)
=== truncated (status='truncated') — after 3 consecutive ticks ===
out = {}
```
(Output is interleaved because each `run_tick()` prints its own header only after the loop of monkeypatched calls completes, so the streak-triggered print from tick 3 of the *previous* state appears just above the *next* state's header — the three distinct outcomes are: healthy → no diagnostic line at all; gh-failure → "gh 실패" line; truncated → "이슈 인덱스 절단(상한 1000건)" line. Three different, non-empty, mutually distinct strings.)

### Live three-state reproduction — pre-fix (`origin/main`), showing the actual defect

Same repro adapted to the old boolean contract, run against an `origin/main` worktree (`2d53e0fe`), with truncation modeled as the pre-fix shape `(None, True)`:

acceptance: python3 /tmp/repro_2792_before.py (`origin/main`, `2d53e0fe`) — result:
```
=== healthy (ok=True) — after 3 consecutive ticks ===
out = {}

[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)
=== gh-failure (ok=False) — after 3 consecutive ticks ===
out = {}

=== truncated (ok=True) — after 3 consecutive ticks ===
out = {}
```
canonical: the "truncated" block above prints **nothing**, byte-identical to the "healthy" block above it — confirming the defect exactly as the issue describes: pre-fix, a truncated board is silent and indistinguishable from a healthy quiet tick. Post-fix (previous section), the same truncated scenario prints its own line. The fix is real and independently reproduced, not merely asserted.

### `_ISSUE_INDEX_LIMIT` and `_issue_is_open()` — the two must-nots

derived: `grep -n "_ISSUE_INDEX_LIMIT" gates/closure_sweep.py` (PR head) — result: `245:_ISSUE_INDEX_LIMIT = 1000`, same value and line as `origin/main`; `git diff origin/main...HEAD -- gates/closure_sweep.py | grep _ISSUE_INDEX_LIMIT` shows it appears only in unchanged context lines, never a `+`/`-` line. Unchanged.

canonical: `sed -n '251,259p' gates/spawn_on_pr.py` (PR head), `_issue_is_open()`:
```python
def _issue_is_open(issue: int, issue_states: dict[int, str] | None) -> bool:
    ...
    if issue_states is None:
        return False
    return issue_states.get(issue) == "OPEN"
```
Byte-identical to `origin/main`'s version (confirmed via `git diff origin/main...HEAD -- gates/spawn_on_pr.py`, no hunk touches this function). It only inspects `issue_states` (already `None` under both `ISSUE_INDEX_TRUNCATED` and `ISSUE_INDEX_FAILED`, per `missing_verification()`'s `if status != closure_sweep.ISSUE_INDEX_OK: issue_states = None`), never the new `status` string directly — fail-closed under truncation is preserved by construction, not just by absence of a diff hunk.

### Spawn eligibility — `spawn_missing_for_pr(..., dry_run=True)` pairs under truncation, before/after

acceptance: python3 /tmp/repro_2792_pairs_after.py (PR head, `f3f38b16`, `issue_state_index_all` monkeypatched to `(None, ISSUE_INDEX_TRUNCATED)`) — result: `AFTER  pairs = []`
acceptance: python3 /tmp/repro_2792_pairs_before.py (`origin/main`, `2d53e0fe`, `issue_state_index_all` monkeypatched to the pre-fix truncation shape `(None, True)`) — result: `BEFORE pairs = []`
canonical: `[]` both before and after — byte-identical, confirming spawn eligibility under truncation is unchanged (both times fail-closed to zero candidates, since `_issue_is_open()` skips every subject when `issue_states is None`).

### Four standing invariants — independently re-measured

- **No return of the retired role axis in any reshaped form**: derived: `git diff origin/main...HEAD -- gates/closure_sweep.py gates/spawn_on_pr.py watchdog.py | grep -E '^\+' | grep -iw "role"` — no output (0 matches). The only "role" hits anywhere in the PR diff are in the PR's own report frontmatter (`role: silent-failure-audit+diagnose-first-a4c194a5`, the author's own role name) and prose in the report file, not in the changed code.
- **No new bug** (failing-test set vs `origin/main`, as sets of names, never counts): ran `python3 -m pytest gates/ test/ -q` independently in a PR-head worktree and an `origin/main` worktree.
  - acceptance: PR head (`f3f38b16`) — result: `15 failed, 452 passed, 3 xfailed in 31.75s`
  - acceptance: `origin/main` (`2d53e0fe`) — result: `15 failed, 448 passed, 3 xfailed in 31.90s`
  - canonical: `diff /tmp/failed_before.txt /tmp/failed_after.txt` (both files built from `grep '^FAILED'` on each run's output, sorted) — `IDENTICAL SETS`, 15 lines each. Full set (both sides): `test_convention_equivalence.py::{ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape, BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim}`, `test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment`, `test_spawn_cross_family_skill_selection.py::{Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate, ConsultJudgeStageTest::test_consult_error_raises_and_still_traces, ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths, FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled, SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive, SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline}`, `test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::{test_declared_artifact_matching_skill_gets_pairing_line, test_no_declaration_line_byte_identical_to_baseline}`, `test_spawn_skill_judge_haiku_timeout_overlap.py::{SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows, SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome, SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome, SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo}`. All are network/environment-shaped (fake `origin` fetch, judge/consult timing), none in a file this PR touched. PR head additionally has 4 more passing tests (452 vs. 448), matching the 4 new tests the PR's Test plan claims. Also independently re-ran the two narrower suites the PR cites: acceptance: `python3 -m pytest gates/test_spawn_on_pr.py -q` (PR head) — result: `27 passed in 0.89s` (matches PR claim); acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py -q` (PR head) — result: `6 passed in 0.88s` (matches PR claim).
  - **No new bug** also independently means: the `watchdog.py` behavioral tweak (`rate_limited_this_tick = bool(skips) and issue_states_status == ISSUE_INDEX_FAILED`, replacing `bool(skips) and not issue_states_ok`) was checked for a hidden regression rather than trusted from the diff comment. canonical: pre-fix, truncation returned `ok=True`, so `not issue_states_ok` was already `False` under truncation — meaning `rate_limited_this_tick` was already `False` for truncated boards pre-fix, same as post-fix's `status == ISSUE_INDEX_FAILED` being `False` for `ISSUE_INDEX_TRUNCATED`. For a genuine gh failure, pre-fix `ok=False` → `not issue_states_ok = True`; post-fix `status == ISSUE_INDEX_FAILED = True`. Both cases: identical resulting boolean, before and after — this is a type-safety migration of existing behavior, not a silent behavior change, despite reading like one from the diff comment alone.
- **No overhead increase**: derived: `git diff origin/main...HEAD -- gates/closure_sweep.py gates/spawn_on_pr.py watchdog.py | grep -E '^\+' | grep -iE "subprocess\.run|gh issue|gh pr|gh api"` — no output (0 matches); no new `gh`/`subprocess` call added anywhere in the diff. The new `"spawn-on-pr:truncated"` streak signal (`spawn._watchdog_note_gh_failure(root, "spawn-on-pr:truncated", truncated)`) is a local state-file read/write (same mechanism `"spawn-on-pr"`'s existing streak already uses), not a network call.
- **Monitor/watch machinery unbroken and NOT quieter**: compared a healthy tick's `watchdog.py` output before/after at the diff level (no removed `print` in the healthy path is possible to construct live without a full watchdog harness, so this is a diff-level trace, stated as such rather than dressed up as a live run). canonical: `sed -n '1072,1157p' watchdog.py` (PR head) vs. the same range pre-fix — every pre-existing `print(...)` call survives unchanged; the only additions are (a) the `"spawn-on-pr:truncated"` diagnostic line in `missing_verification()` (new output, not a replacement), and (b) `watchdog.py`'s `closure-sweep: 확인 불가` line gained a `reason_counts` breakdown (`{reason: count}`) appended to what was previously a bare count — strictly more detail, not less. No `print` call was deleted or made conditional on a narrower condition than before. This directly matters here: the issue this PR fixes is itself a case where a watch path went silent, so verifying the fix didn't trade one silence for another was a first-order check, not a formality.

## Why

The task was to independently re-verify PR #2805 without restating its own claims: re-derive the call-site list by grep rather than copying the PR body's bullet list (which surfaced the `closure_sweep.py:755`/`spawn.py` discrepancies below), specifically hunt for the `if not ok:`-on-a-truthy-string failure mode the review was primed to expect, reproduce the three-state distinction live in both directions (post-fix showing the fix works, pre-fix showing the defect is real), and re-measure all four standing invariants from scratch rather than trusting the PR's own "no overhead increase" style assertions.

## What did not work

None.

## Upstream basis

PR #2805 / branch `issue-2792/silent-failure-audit+diagnose-first-a4c194a5`, head commit `f3f38b1602dbb1e511daf50fb8fa223fda5f7b6e`, based on `origin/main`. canonical: `gh pr view 2805 --json headRefName,baseRefName,commits`.

## Open findings

1. canonical: `gh pr view 2805` Summary — "Every other caller (`find_violations`, `backfill_closed`, `watchdog.py`'s board sweep, `spawn.py`'s CLI) threaded through the new status" — but `spawn.py` is absent from `gh pr view 2805 --json files` and no hunk in `gh pr diff 2805` touches `spawn.py`. The underlying claim (this caller is unaffected/compatible) is correct — `spawn.py:2367` uses the `issue_states, _ = ...` discard pattern, contract-agnostic — but the phrasing "threaded through" implies a code change that did not happen there. Documentation imprecision only, not a functional defect. Resolution path: none required for this issue's acceptance; a future PR description could say "unaffected (discard pattern)" instead of "threaded through" for that one caller.
2. `gates/closure_sweep.py`'s own `main()` CLI entrypoint (line 755, the same `issue_states, _ = issue_state_index_all(root)` discard pattern) is not named in the PR body's caller list either. Same reasoning as finding 1 — correctly a no-op site, not a gap — noted here only because the PR body enumerates callers by name and this one is absent from that enumeration without comment.

Neither finding blocks PR #2805's own acceptance claims; both are recorded because the task asked for the call-site list to be independently re-derived and compared against the PR's own list, not because either changes the verdict.

## Next steps

None — `loop_state: landed`. canonical: the live three-state reproduction (both post-fix and pre-fix), the byte-identical `spawn_missing_for_pr(dry_run=True)` pairs, the unchanged `_ISSUE_INDEX_LIMIT`/`_issue_is_open()`, and the four independently re-measured standing invariants above are the basis for this terminal state. The two open findings above are informational (PR-description phrasing only), not blockers.

skill-verdict: adversarial-review — applied: invoked; this entire record IS the evaluator role's independent re-derivation of PR #2805's acceptance claims (fresh worktrees for both PR head and `origin/main`, re-run pytest suites, re-derived the call-site list by grep instead of trusting the PR body's bullet list, and live-reproduced both the pre-fix defect and the post-fix three-state distinction from scratch) rather than restating or trusting the builder's embedded report.
skill-verdict: work-in-english — applied: invoked; this record, all repro scripts, and all git/gh commands were written in English throughout.
skill-verdict: silent-failure-audit — applied: invoked; used its trace-forward method as the basis for the "Truthy-string hazard sweep" section above — traced every live `ok`/`status` occurrence in the diff from definition site to every call site's conditional, classifying each as migrated-to-explicit-comparison (Handled) rather than left as an implicit truthiness check (which would have been a Silently Absorbed-shaped hazard: a status string that's always truthy, inverting a `not ok` branch without raising).
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; per rule 3, re-derived every acceptance check from primary evidence (live repro scripts, fresh worktrees, direct `git diff`/`grep`) rather than citing PR #2805's own embedded report's claims; per rule 6, treated the PR body's caller list as a claim to check against an independently-grepped list rather than accepting it, which is what surfaced the two open findings above.
