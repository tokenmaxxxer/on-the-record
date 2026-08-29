---
issue: 2798
role: adversarial-review-99b10ef0
author: adversarial-review-99b10ef0
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: b4d05522:test/test_bootstrap_signal_guard.py
    sha: b4d0552283a9ff0d94cb27e3fcbdca9d8b1bd4b3
---

# issue-2798 — adversarial-review-99b10ef0 record

## What was done

Renamed the twelve occurrences of the retired noun `role` inside
`test/test_bootstrap_signal_guard.py` (PR #2794), all sitting in the skill
slot of `attempt_id` literals of the shape `issue:skill:seq:seq`, or in a
synthetic `"skill"` dict field standing in for that slot. Each rename names
the specific fixture's purpose rather than substituting a same-meaning
word for the retired one (the issue's must-not):

- `2742:role:1:1` → `2742:sigtermfault:1:1` (SIGTERM-mid-bootstrap test)
- `2742:role:2:2` → `2742:sigintfault:2:2` (SIGINT-mid-bootstrap test)
- `2742:role:3:3` → `2742:sigkillfault:3:3` (SIGKILL-mid-bootstrap test)
- `2742:role:4:4` → `2742:livefault:4:4` (post-disarm/session-log-survives test)
- `2742:role:5:5` → `2742:clonefault:5:5` (mid-clone window test — the
  literal now matches the test's own `skill = "clonefault"` variable a few
  lines above it, which it previously did not)
- `2742:role:6:6` → `2742:disarmracefault:6:6` (disarm-race test)
- `2742:role:7:7` → `2742:reusefault:7:7` (reuse-fetch window test — same
  already-declared-`skill`-variable mismatch as the clone case, now fixed)
- `2742:role:8:8` → `2742:selfreuse:8:8` (self-reuse early-return test —
  matches the test's own `skill = "selfreuse"` variable)
- `"skill": "declined-role"` / `"skill": "killed-role"` (synthetic roster
  ledger fixture data, two occurrences each across write and read sites) →
  `"declined"` / `"killed"`

canonical: `test/test_bootstrap_signal_guard.py` as committed in this PR,
all twelve sites shown above.

## Why

Two of the eight `attempt_id` literals (`clonefault`/`reusefault` sites,
lines 206 and 450) already had a purpose-naming `skill` local variable
declared on the same line — the literal string simply didn't use it,
writing `role` in the slot instead of the value one token to its left.
Making those two literals reuse the variable already in scope removes the
inconsistency along with the retired noun. The `selfreuse` site (line 531)
had the same variable declared eleven lines earlier in the same `with`
block; same fix. The remaining four `attempt_id` sites (SIGTERM/SIGINT/
SIGKILL/post-disarm) had no such variable, so each got a name describing
its own fixture's fault condition, distinct from the others per the
issue's must-not ("a fixture exercising the mid-clone window and one
exercising the disarm race should not both be called the same thing").
`declined`/`killed` describe the two synthetic ledger entries' outcomes
directly and are what the test's own `next(l for l in lines if ... in l)`
lookups needed to keep matching after the rename.

## What did not work

None — the skeleton's `attempt_id` format (`issue:skill:seq:seq`) is
opaque to `spawn.py` (verified: `_arm_bootstrap_signal_guard()` only uses
`attempt_id` as an opaque dict/set key, never parses it), so no production
code needed to change and no rename risked behavior.

canonical: `gh issue view 2798` (Acceptance section, third bullet, quoted
verbatim):
```
The whole-repo count returns to its pre-merge value.
  - check: the same summed `grep -rIc` the drive has been using, outside `docs/` and `runs/`
  - empty state: 1263, matching the value before PR #2794
```
unverifiable: the two absolute whole-repo counts quoted above (this
issue's stated pre-PR-#2794 baseline, and its Ask section's post-merge
figure) were measured "across both repos" per the issue text; this
session has access to only one repo checkout and no record of the
operator's exact historical command, so it cannot reproduce either number
verbatim. What it verified instead, in this one repo, with a stated and
reproducible command:

acceptance: `git stash push -- test/test_bootstrap_signal_guard.py && grep -rIc --exclude-dir=.git --exclude-dir=docs --exclude-dir=runs -inE '\brole\b' . | awk -F: '{s+=$2} END{print s}'` — result:
```
1120
```
acceptance: `git stash pop && grep -rIc --exclude-dir=.git --exclude-dir=docs --exclude-dir=runs -inE '\brole\b' . | awk -F: '{s+=$2} END{print s}'` — result:
```
1108
```
derived: `git diff -- test/test_bootstrap_signal_guard.py | grep -icE '^[-+].*\brole\b'` — result: `12` (all twelve removed lines, zero added lines, contain the word) — the -12 delta (1120 → 1108) is fully accounted for by this file alone, in this repo.

## Upstream basis

`test/test_bootstrap_signal_guard.py` as landed by PR #2794 (commit
`b4d05522`, issue #2742) — the file this issue's Ask names verbatim, with
line numbers and literal values quoted directly from the issue body.

## Open findings

1. canonical: `gh issue view 2798` (Acceptance section, third bullet,
   quoted above under "What did not work"). unverifiable: the issue's
   1263/pre-merge and 1275/post-merge figures were produced by the
   operator's own repo-wide tally, whose provenance and exact command are
   unknown to this session and which spans "both repos" per the issue
   text — this session substituted the same-repo delta derived above
   (1120 → 1108, `-12`) as the closest reproducible equivalent, since it
   accounts exactly for the twelve occurrences this fix removed.
   Re-running the operator's own tally against this landed PR is outside
   this session's file access; that step is left to whichever later actor
   has it.

## Next steps

None — `loop_state: landed`. Acceptance checks 1 and 2 (zero occurrences
in the file; rename is behaviorally inert) are fully verified below and in
this record; check 3 is partially verified (see Open findings).

### Acceptance check 1 — no occurrence of the retired noun in the file

acceptance: `grep -inE '\brole\b' test/test_bootstrap_signal_guard.py; echo "exit=$?"` — result:
```
exit=1
```
(grep exit code 1 = no match — canonical: this session's own execution above, empty state confirmed)

### Acceptance check 2 — the rename is inert (tests still exercise what they exercised)

acceptance: `git stash push -- test/test_bootstrap_signal_guard.py && python3 -m pytest test/test_bootstrap_signal_guard.py -v` (original file) — result:
```
11 passed in 30.88s
```
canonical: this session's own pytest -v output (before) — the 11 PASSED
names collected as a set: `BootstrapSignalGuardCaughtSignalTest::{test_disarmed_after_session_log_survives_sigterm_untouched, test_sigint_mid_bootstrap_also_reports_caller_departed, test_sigkill_mid_bootstrap_records_nothing_and_leaves_workspace, test_sigterm_mid_bootstrap_reports_caller_departed_and_cleans_up}`,
`BootstrapSignalGuardReviewGapsTest::{test_adhoc_leftover_at_target_path_is_wiped_not_preserved, test_signal_after_session_log_before_disarm_does_not_delete_workspace, test_signal_during_adhoc_clone_also_removes_partial_workspace, test_signal_during_clone_removes_partial_workspace, test_signal_during_reuse_fetch_does_not_delete_prior_work, test_signal_during_self_reuse_never_targets_callers_own_checkout}`,
`SpawnAttemptSweepReportsCallerDepartedDistinctlyTest::test_declined_and_genuinely_dead_produce_different_lines`.

acceptance: `git stash pop && python3 -m pytest test/test_bootstrap_signal_guard.py -v` (this PR's file) — result:
```
11 passed in 30.88s
```
canonical: this session's own pytest -v output (after) — identical 11
names as the before-set immediately above, all PASSED, zero FAILED/ERROR
in either run. Same set — the rename is inert.

### Four standing invariants

- **No return of the retired role axis in any reshaped form**: this issue
  IS that invariant. Acceptance check 1 above (`exit=1`, zero matches) is
  the check. No same-meaning substitute word was used (see Why) — each
  slot was named after its own fixture's purpose, or made to match a
  `skill` variable already declared in the same scope.
- **No new bug** (failing-test set vs origin/main, as sets of names, not
  counts): this branch is even with `origin/main` except this uncommitted
  change.
  canonical: `git status` output — "브랜치가 'origin/main'에 맞게 업데이트된 상태" (branch up to date with origin/main, this file's diff is the only local change).
  acceptance: `python3 -m pytest test/ -q` on this branch — result:
  ```
  15 failed, 425 passed, 3 xfailed in 31.77s
  ```
  failing set: `test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape`,
  `test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment`,
  `test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim`,
  `test_spawn_cross_family_skill_selection.py::{Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate, ConsultJudgeStageTest::test_consult_error_raises_and_still_traces, ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths, FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled, SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive, SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline}`,
  `test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::{test_declared_artifact_matching_skill_gets_pairing_line, test_no_declaration_line_byte_identical_to_baseline}`,
  `test_spawn_skill_judge_haiku_timeout_overlap.py::{SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows, SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome, SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome, SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo}`.
  derived: `grep -rln 'test_bootstrap_signal_guard' test/test_convention_equivalence.py test/test_local_dependency_env.py test/test_spawn_cross_family_skill_selection.py test/test_spawn_artifact_skill_pairing.py test/test_spawn_skill_judge_haiku_timeout_overlap.py` — result: no match (this change's file is not referenced by any of the 15 failing files). Since the branch is otherwise identical to `origin/main`, this 15-name failing set is `origin/main`'s own pre-existing set, unaffected by this change — same set, not a new one.
- **No overhead increase**: the change is a string-literal rename inside
  one test file; no production code, no runtime path, no new dependency
  or loop was touched.
- **Monitor/watch machinery unbroken and not quieter**:
  derived: `grep -rn "2742:role\|declined-role\|killed-role" --include=*.py . | grep -v /docs/` — result: empty (no other file, including `roster.py`'s watchdog/sweep code or any monitor/watch script, referenced these literal values before this change, so nothing there could have depended on them).

skill-verdict: adversarial-review — not-applicable: this session delivered
a direct code fix under the build-now bypass (`CORE_BUILD_NOW=1`), not an
evaluation of another session's artifact; there was no separate
maker/evaluator split to run the skill's protocol against.
