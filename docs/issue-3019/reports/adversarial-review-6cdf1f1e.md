---
issue: 3019
role: adversarial-review-6cdf1f1e
author: adversarial-review-6cdf1f1e
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3035 (test-derivation+silent-failure-audit-20ea9371's deliverable)
code_under_review: tests/test_skill_candidates_floor.py (PR #3035, issue-3019/test-derivation+silent-failure-audit-20ea9371, head 463d963479336dafe865ae125f9811c5110594df)
type: verification
breaking: false
verdict: pass — both acceptance checks reproduce independently, the must-not list holds on direct diff read, and the divergence mechanism surfaces a real live divergence
loop_state: landed
upstream:
  - path: tests/test_skill_candidates_floor.py
    sha: 463d963479336dafe865ae125f9811c5110594df
---

# issue-3019 — adversarial-review-6cdf1f1e record

## What was done

Independent verification of PR #3035 (`issue-3019/test-derivation+silent-failure-audit-20ea9371`,
head `463d963479336dafe865ae125f9811c5110594df`) against issue #3019.
canonical: `gh pr view 3035` output — state OPEN, additions 305, deletions
5, `Closes #3019`. Fetched the PR's head into an isolated worktree
(`git fetch origin pull/3035/head:pr-3035-verify && git worktree add
/tmp/verify-3035 pr-3035-verify`) and re-ran everything myself.

**Acceptance check 1.** acceptance: `python3 -m pytest tests/ -k
skill_candidates_regression_cases -q` — result:
```
5 passed in 0.96s
```
Matches the PR's own claimed count.

**Acceptance check 2 — the one that has to be tested for real, not just
run.** The issue's own text warns that a divergence detector which
itself passes silently on a real divergence is the same defect wearing a
new hat, and that issue #2982's two headline example queries genuinely
diverge live today. acceptance: `python3 -m pytest tests/ -k
pinned_fixture_divergence -q` — result:
```
1 passed, 2 warnings in 0.96s

=============================== warnings summary ===============================
tests/test_skill_candidates_floor.py::SkillCandidatesPinnedFixtureDivergenceTest::test_pinned_fixture_divergence_from_live_scoring_is_reported
  UserWarning: pinned-fixture-divergence (issue #3019): task='rewrite the
  workspace preservation predicate in lifecycle.py from git-status-based
  to what-would-be-lost — unpushed commits, stash, merge/rebase state,
  untracked classification via git check-ignore' pinned_outcome='no-candidates'
  live_outcome='bm25-only' live_top={'name': 'agent-coordination',
  'score': 15.134316351480953, ...}

tests/test_skill_candidates_floor.py::SkillCandidatesPinnedFixtureDivergenceTest::test_pinned_fixture_divergence_from_live_scoring_is_reported
  UserWarning: pinned-fixture-divergence (issue #3019): task='remove the
  200-turn session cap, replace with wall-clock/token backstops and an
  observe-only runaway signal reusing trajectory_analyzer'
  pinned_outcome='no-candidates' live_outcome='bm25-only' live_top={'name':
  'secure-coding-session-authentication', 'score': 7.911048066340095, ...}
```
Both of issue #2982's headline queries score above the 4.0 floor and
rank `bm25-only` against today's live corpus (`agent-coordination` at
15.13, `secure-coding-session-authentication` at 7.91) — exactly the
concrete divergence the issue names as currently sitting unreported.
The mechanism caught its own live target on first run, not a synthetic
fixture. Re-ran a second time to rule out a one-off. acceptance:
`python3 -m pytest tests/ -k pinned_fixture_divergence -q` (rerun) —
result:
```
1 passed, 2 warnings in 0.98s
```
Identical payload both times.

**Warning suppression check.** derived: `cat pytest.ini` — result:
```
[pytest]
python_functions = test_* t_*
norecursedirs = runs harness/fixture-redtest harness/fixture-target
addopts = -n auto
markers =
    slow: real subprocess spawn or real git clone/checkout lifecycle tests, excluded by default (issue #1490); run with -m slow or without -m "not slow" to include.
```
No `filterwarnings`, `-p no:warnings`, or `-W ignore` entry that could
swallow the warning shown above; the check as specified in the issue
(`-q`, no extra flags) printed it by default, as already shown.

**Full file, consistency check against the PR's third test-plan line.**
acceptance: `python3 -m pytest tests/test_skill_candidates_floor.py -q`
— result:
```
12 passed, 2 warnings in 1.14s
```
Matches the PR's claimed `12 passed, 2 warnings`.

**Full suite, unrelated-failure check.** acceptance: `python3 -m pytest
test/ tests/ -q` — result:
```
20 failed, 718 passed, 3 xfailed, 2 warnings in 33.25s
```
derived: `python3 -m pytest test/ tests/ -q 2>&1 | grep "^FAILED"` —
result:
```
FAILED test/test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
FAILED test/test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape
FAILED test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
FAILED test/test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate
FAILED test/test_spawn_cross_family_skill_selection.py::FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled
FAILED test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive
FAILED test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows
FAILED test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome
FAILED test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_proceeds_without_deliverable_still_respawns_genuine_crash
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_skip_is_reported_never_silent_even_without_pr_number
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_proceeds_without_deliverable_when_gate_finds_none
FAILED test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_declared_artifact_matching_skill_gets_pairing_line
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_skip_is_reported_names_the_pr_in_stderr_and_ledger
FAILED test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline
```
None in `test_skill_candidates_floor.py`; none touch `spawn.rank_skills`
/ `spawn._bm25_cross_family_scores` (the only two symbols this PR's new
test calls). Pre-existing, unrelated to this change.

**Diff audit against the issue's must-not list.** canonical: `git diff
main...HEAD -- tests/test_skill_candidates_floor.py` (worktree, base
`5f83399d0548b9d688a5ba1547661f03fc30510c`, head
`463d963479336dafe865ae125f9811c5110594df`), read in full.

1. *Must not delete the pinned regression cases.* derived: `git diff
   main...HEAD -- tests/test_skill_candidates_floor.py | grep -c
   "^-.*def "` — result: `0`. derived: `grep -c "def test_"
   tests/test_skill_candidates_floor.py` — result: `12`. derived: `git
   show main:tests/test_skill_candidates_floor.py | grep -c "def
   test_"` — result: `11`. No test method removed; one added (the new
   divergence test). `SkillCandidatesRegressionCasesTest`'s five test
   methods, their scores, and all five `assertEqual` bodies are
   byte-identical in the diff — only the class docstring changed.
2. *Must not become live-corpus assertions.* canonical: the new
   `SkillCandidatesPinnedFixtureDivergenceTest.test_pinned_fixture_divergence_from_live_scoring_is_reported`
   body, read directly in the diff cited above — it calls
   `spawn.rank_skills` unmocked, compares `live["outcome"]` to the
   pinned outcome, and on mismatch only calls `warnings.warn(...)`.
   There is no `self.assertEqual` or any other assertion against a live
   score anywhere in the new class — it cannot fail on corpus drift by
   construction, since `warnings.warn` never raises.
3. *Must not change the floor value (belongs to #3018).* derived: `git
   diff main...HEAD --stat` — result:
   ```
   docs/issue-3019/reports/test-derivation+silent-failure-audit-20ea9371.md | 221 ++++++++
   tests/test_skill_candidates_floor.py                                     |  89 +++-
   2 files changed, 305 insertions(+), 5 deletions(-)
   ```
   `spawn.py` (home of `_SKILL_CANDIDATES_RELEVANCE_FLOOR = 4.0`) is
   untouched. derived: `grep -n "4\.0\|FLOOR\|floor"
   tests/test_skill_candidates_floor.py` — the floor is referenced only
   via `spawn._SKILL_CANDIDATES_RELEVANCE_FLOOR` (the live constant,
   read not written) in both old and new test bodies; no numeric floor
   literal changed.

All three must-not points hold.

## Why

Re-derived rather than cited, per `defect-verification-independence-
from-upstream-verdicts`: fetched the PR head into an isolated worktree
and ran both acceptance checks, the full test file, and the full suite
myself rather than accepting the PR body's pasted output. acceptance:
`python3 -m pytest tests/ -k pinned_fixture_divergence -q` — result:
```
1 passed, 2 warnings in 0.96s
```
The issue's own text names a specific risk: a divergence-detection
mechanism could itself go quiet on a real divergence. This session read
the literal warning payload (`live_top` scores 15.13, 7.91, pasted in
full in `## What was done` above) instead of stopping at the bare
summary line, and checked those scores directly against the shipped 4.0
floor (`spawn._SKILL_CANDIDATES_RELEVANCE_FLOOR`, cited in point 3 of
the diff audit above): both exceed it. The mechanism's own output
above, not a description of it, is the evidence that it surfaces the
concrete case the issue names, on today's corpus.

## Upstream basis

PR #3035, head `463d963479336dafe865ae125f9811c5110594df` (branch
`issue-3019/test-derivation+silent-failure-audit-20ea9371`), merge-base
`5f83399d0548b9d688a5ba1547661f03fc30510c` with `main`. canonical: `gh
pr view 3035` and `git log --oneline -3` in the worktree.
`docs/issue-3019/reports/test-derivation+silent-failure-audit-20ea9371.md`
(untracked on this branch; lives only on PR branch
`issue-3019/test-derivation+silent-failure-audit-20ea9371`, read via the
`/tmp/verify-3035` worktree, same commit) was read for cross-reference
but not relied on for any claim above — every number cited in `## What
was done` was re-derived in this session's own worktree run.

## Open findings

None found. acceptance: `python3 -m pytest tests/ -k
skill_candidates_regression_cases -q` — result:
```
5 passed in 0.96s
```
acceptance: `python3 -m pytest tests/ -k pinned_fixture_divergence -q`
— result:
```
1 passed, 2 warnings in 0.96s
```
Both checks reproduce exactly (full output above in `## What was
done`); the must-not list holds on direct diff read (three points
above); the divergence mechanism was confirmed against its real live
target, not trusted from the PR's description.

## Next steps

None — this record is terminal. acceptance: `python3 -m pytest tests/ -k
"skill_candidates_regression_cases or pinned_fixture_divergence" -q` —
result:
```
6 passed, 2 warnings in 0.97s
```

skill-verdict: adversarial-review — applied: invoked; loaded via the
Skill tool before any investigation. This session's mandate — fetch
PR #3035's head into an isolated worktree, re-run the acceptance checks
myself, and audit the diff rather than deferring to the PR's own
claimed test-plan output — is this skill's core independent-session,
re-derive-not-cite posture, applied to a code deliverable.
skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; loaded via the Skill tool before any investigation.
Its rule against letting a prior verdict pre-shape scope or rigor is
what drove re-running the divergence test and reading its literal
warning payload (scores, outcomes) rather than accepting the PR body's
"1 passed, 2 warnings" line at face value.
skill-verdict: test-depth-audit — not-applicable: canonical: this
skill's own SKILL.md, loaded via the Skill tool — its scope is
classifying an existing test suite's depth (Genuine/Execution-Only/
Mock-Dominated/Happy-Path-Only/Dead) as a standalone audit; this
session's task was a single-PR acceptance-and-must-not verification
with a narrower, issue-specific brief, not a suite-wide depth
classification.
skill-verdict: verify-finding-record — not-applicable: canonical: this
skill's own SKILL.md, loaded via the Skill tool — its scope is
`docs/issue-<n>/reports/defect-verification.md` outcome records for a
reproduction attempt against a defect claim; this session found no
defect (see `## Open findings`), and this verification's own record
lives in `docs/issue-3019/reports/adversarial-review-6cdf1f1e.md` (this
file) per the adversarial-review skill's own contract.
skill-verdict: pricing-verdict-report — not-applicable: canonical: this
skill's own SKILL.md, loaded via the Skill tool — its scope is assembling
pricing-method numeric output (PSM/conjoint) into a verdict; nothing in
this task involves pricing data.

## What did not work

None — every acceptance check and diff-audit point held on the first
attempt. acceptance: `python3 -m pytest tests/test_skill_candidates_floor.py
-q` — result:
```
12 passed, 2 warnings in 1.14s
```
No reproduction attempt failed and no adjustment to the verification
approach was needed mid-session.
