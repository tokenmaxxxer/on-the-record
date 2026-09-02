---
issue: 3091
role: diagnose-first+silent-failure-audit+test-derivation-7248afd6
author: diagnose-first+silent-failure-audit+test-derivation-7248afd6
skills: diagnose-first (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: same-commit
type: test-fix
breaking: "false"
verdict: pass
loop_state: landed
upstream:
  - path: docs/handbooks/test-layout.md
    sha: 082bfd7b5a81c8c0716a79edc8dde6a06511755b
---

# issue-3091 — diagnose-first+silent-failure-audit+test-derivation-7248afd6 record

## What was done

Diagnosed all 15 failures in `test/` (singular) before repairing any, per
the issue's instruction and the PR #3089 model. Every one of the 15
turned out to be a **stale test pinning behaviour an already-merged
commit intentionally changed** -- zero live defects, zero environment
artifacts. Each is cited below with the commit that made it stale.

acceptance: `bash -c "python3 -m pytest test/ -q"` — result:
```
$ python3 -m pytest test/ -q
563 passed, 3 xfailed in 32.45s
```
acceptance: `bash -c "python3 -m pytest tests/ -q"` — result:
```
$ python3 -m pytest tests/ -q
5 failed, 182 passed, 2 warnings in 9.25s
```
(the 5 failures are pre-existing on this session's `main` base and
outside this issue's scope; see Open findings.)
acceptance: `bash -c "python3 gates/probe_full_suite_is_one_command.py"` — result:
```
$ python3 gates/probe_full_suite_is_one_command.py
FAIL: 2 shell test file(s) exist that `python3 -m pytest` can never collect: ['tests/check-write-set-conflicts.test.sh', 'tests/claim-scan-preflight.test.sh'] -- running every test in the repo therefore requires a SECOND, separate command (`bash tests/run-orchestrate-tests.sh`, per docs/handbooks/on-the-record.md), so no single command currently suffices.
exit=1
```

### The 15, classified

| # | Test | Cause | Made stale by |
|---|------|-------|----------------|
| 1 | `test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape` | pinned branch/citation-slug regex `[\w-]+` | issue #2576, commits `96699800` (PR #2586) + `2cc3cf4f` (PR #2591) widened every hook's regex to `[^/]+` so a multi-skill `--skills` slug (contains `+` -- this session's own branch name is an instance) still parses |
| 2 | `test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim` | same pinned regex, second copy | same as #1 |
| 3 | `test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment` | literal call-site string `cwd = issue_workspace(cwd, issue, role)` | issue #2731 (commit `e1f390ab`) renamed `role`->`skill`; issue #2742 (commit `b4d05522`, PR #2794) wrapped the direct call in `_create_workspace_with_signal_guard()` |
| 4 | `test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_declared_artifact_matching_skill_gets_pairing_line` | mocked dead function `spawn.checkout_issue_branch` | issue #2432 stage 4 (commit `2cc6d108`) inlined the branch-name-agnostic call path onto `_checkout_named_branch(cwd, br)` directly; `checkout_issue_branch` is still importable but never called from `_spawn_one`, so the mock silently stopped intercepting and production fell through to a real `git fetch` against a fake `origin` |
| 5 | `test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline` | same dead mock as #4, **plus** a second stale mock: `gh_rest.fetch_issue`'s mocked return omitted the `owner`/`repo` keys the real function has always returned since issue #2395 | commit `2cc6d108` (as #4); issue #2395's `gh_rest.fetch_issue` contract (`gates/gh_rest.py:78-90`) |
| 6 | `test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive` | same dead mock as #4 | commit `2cc6d108` |
| 7 | `test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline` | same dead mock as #4, **plus** this file never mocked `gh_rest.fetch_issue` at all (real network/`gh` call fails, embedding a tmpdir path in the byte-identical comparison) | commit `2cc6d108`; issue #2395 |
| 8 | `test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces` | mock lambda kept a 4th `spec: dict` positional parameter | issue #2537 stage 6A (commit `a4d85dbb`) removed `_consult_cmd_and_env`'s `spec` parameter; the file's own 4th (already-passing) mock of the same call already used the post-#2537 3-arg shape |
| 9 | `test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths` | same as #8 | commit `a4d85dbb` |
| 10 | `test_spawn_cross_family_skill_selection.py::FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled` | same as #8 | commit `a4d85dbb` |
| 11 | `test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate` | asserted a same-family-named skill (`implementation-blueprint`) is never a cross-family candidate | issue #2507 (commit `0879f12a`) removed the `_ROLE_SKILLS[role]` candidate-pool exclusion outright ("a fixed role->skill table no longer defines family... no reason to narrow the pool by role", `pipeline.py:1442-1446`); issue #2561 (commit `6ae45558`) then deleted the table itself |
| 12 | `test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows` | same dead mock as #4 | commit `2cc6d108` |
| 13 | `test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome` | same dead mock as #4 | commit `2cc6d108` |
| 14 | `test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome` | same dead mock as #4 | commit `2cc6d108` |
| 15 | `test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo` | same dead mock as #4 | commit `2cc6d108` |

derived: per-file breakdown from this branch's own fix commits
(`d3c2ee62`, `100ebf91`, `5eb15a0f`, `86fcc822`, `4913270c`, `fa569f29`):
2 in `test_convention_equivalence.py`, 1 in `test_local_dependency_env.py`,
2 in `test_spawn_artifact_skill_pairing.py`, 6 in
`test_spawn_cross_family_skill_selection.py`, 4 in
`test_spawn_skill_judge_haiku_timeout_overlap.py` = 15, matching the
issue's own count exactly.

**must-not compliance**: no assertion was loosened or deleted. Every fix
either (a) updated a pinned literal/regex to the new, intentionally
different value the cited commit produced, (b) repointed a mock at the
function that actually runs today (same call semantics, corrected
target), or (c) replaced a position-fragile list index with an
equivalent-strength lookup (exactly-one-match assertion) once a second,
independently-scheduled ledger write was exposed. No environment-artifact
classification was used anywhere, consistent with the must-not on that
point (there was no case where the cause was environmental rather than
a stale pin).

### Skill-layer bearing on issue #3053

Of the 12 skill-layer failures, 11 bear no relation to #3053's
measurement of mount success / skill opening / selection, because in
every one of the 11, the failure was in the *test's own mocking* -- not
in the production code #3053's measurement exercises. This was checked
per-file, not assumed: after each stale-mock class was fixed, that
file's full test run was re-executed and the underlying selection/mount/
ledger assertion the test exists to check passed.

acceptance: `python3 -m pytest test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_artifact_skill_pairing.py test/test_spawn_cross_family_skill_selection.py -q` — result:
```
18 passed (test_spawn_skill_judge_haiku_timeout_overlap.py)
2 passed (test_spawn_artifact_skill_pairing.py)
23 passed (test_spawn_cross_family_skill_selection.py)
```
derived: each named test below is one of those 43 passing node IDs.

- The two named ledger tests (`test_ledger_entry_records_fail_open_outcome`,
  `test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo`)
  do not reveal any problem with the judge's ledger. Once the dead
  `checkout_issue_branch` mock was repointed, both tests -- and the third
  ledger test, `test_ledger_entry_records_completed_outcome` -- are
  among the passing node IDs in the rerun above, confirming the ledger
  correctly records `completed`/`fail-open`/`not-run` outcomes.
  `#3053`'s reliance on this ledger's account of fail-open/not-run
  behaviour is not undermined.
- `SkillJudgeOverlapOrderingTest` (judge-dispatch-before-workspace
  ordering) is about concurrency/timing plumbing, not about what the
  judge decides or whether mounting succeeds; also among the passing
  node IDs above.
- The 3 `spec`-parameter tests and the 2 `SpawnOneCrossFamilyAcceptanceTest`
  tests are likewise among the passing node IDs -- the selection and
  mounting code paths #3053 measures were never broken.
- The 2 `SpawnOneArtifactSkillPairingTest` tests are about design-artifact-to-skill
  pairing annotations in the directive, a downstream feature adjacent to
  but distinct from mount success/skill opening/selection; also among
  the passing node IDs.

**One of the 12 does bear on #3053**:
`Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate`.
Issue #2507 (commit `0879f12a`) intentionally widened the cross-family
candidate pool by removing the `_ROLE_SKILLS[role]` exclusion outright --
a skill whose name happens to match the session's own family (e.g.
`implementation-blueprint` for an `implementation` session) is no longer
filtered out of the candidate pool before scoring; it now competes on
the same BM25/judge basis as any other skill. This is a genuine,
intentional selection-surface change, not a test bug.
**What would have to be re-checked**: whether `#3053`'s measurement
corpus/scenarios include any same-family-named skill among the
candidates offered to a session. If they do, some fraction of "a skill
was selected" outcomes in that measurement could now include a
same-family-named skill that would have been silently excluded before
issue #2507 -- which changes what "mounting a skill changed the
deliverable" is being measured against, since a same-family skill's
guidance may already overlap with the session's baseline behaviour in a
way a genuinely cross-family skill's would not. If `#3053`'s corpus
never included such skills, this widening is moot for that measurement
and no re-check is needed.

### Why two `test/`/`tests/` directories exist, and whether to merge

Issue #729 (proposal `docs/issue-729/proposals/2026-08-11-consolidate-test-homes.md`,
landed via PR #746, commit `082bfd7b`) already did this merge once:
`test/` was fully emptied and its contents moved into `tests/`, chosen as
the survivor name because `conftest.py` and `shape_contracts.py` already
anchored their fixture-relative paths under `tests/` (per
`docs/issue-729/reports/implementation.md`'s own Rationale). The decision
and the placement rule are still recorded today, unchanged, in
`docs/handbooks/test-layout.md`: `tests/` is the single home (with
`gates/` and `on-the-record/hooks/` colocation as the only stated
exceptions).

canonical: `docs/handbooks/test-layout.md` (read in full this session)
and `docs/issue-729/reports/implementation.md` frontmatter (`verdict:
pass`, `loop_state: landed`).

Eleven days later (2026-08-22, commit `e7cd06c2`, issue #2001 phase 2),
`test/` reappeared with a new file, and many separate commits across
many different issues have each added new files under `test/` since.

derived: `git log --oneline --diff-filter=A -- 'test/*.py' 'test/*.sh' | wc -l`
```
$ git log --oneline --diff-filter=A -- 'test/*.py' 'test/*.sh' | wc -l
54
```
54 separate commits, each a different issue number by inspection of the
commit subjects, spanning nearly the whole commit history since
`082bfd7b`. This is not one mistake; it is a standing, repeat pattern.

**Root cause**: the per-session orchestrator directive every spawned
role session receives states a generic, repo-agnostic layout
convention: "code under src/, tests under test/" -- boilerplate meant to
apply across whatever target repo the orchestrator is managing.

canonical: `docs/issue-2827/_assets/tokenmaxxxer-core-patch/core-hooks-directive.sh:106`
(read this session): "Layout: code src/, tests test/, docs/ six
buckets..." -- the same line this session's own SessionStart hook output
shows verbatim for the `implementation` role.

It has no mechanism to read or defer to a specific repo's own
established convention. This repo's own `docs/handbooks/test-layout.md`
says `tests/`, but nothing tells the generic directive template about
that override, so every session since issue #729 has kept receiving
"tests under test/" as its layout instruction and has obediently created
new files there -- regrowing exactly the split #729 eliminated,
invisibly, because no single `pytest` invocation the orchestrator or any
session ran covered both directories at once (the property
`gates/probe_full_suite_is_one_command.py`, added by this PR, now checks
for).

**Should one absorb the other?** Yes, in the same direction as before:
per the repo's own still-valid decision, `test/` should merge into
`tests/`. **This PR does not perform that merge** -- per the issue's
explicit instruction, a merge renumbers and re-collects everything and
would make this diagnosis unattributable. A follow-up issue should (a)
redo the #729-style consolidation, and (b) fix the actual root cause
this time, or the merge will silently regrow a third time: either make
the generic session-startup directive template repo-aware (read
`docs/handbooks/test-layout.md`'s stated convention when present), or
give repos an explicit override mechanism the template must consult
before emitting its generic "tests under test/" line.

### `gates/probe_full_suite_is_one_command.py`

New gate. `docs/handbooks/operations.md` documents `python3 -m pytest -q`
(no path argument, no `--ignore=gates`) as the full-suite command.

derived: `python3 -m pytest -q --collect-only`
```
$ python3 -m pytest -q --collect-only 2>/dev/null | tail -3
tests/test_workspace_clean_state_predicate.py::WorkspaceCleanStatePredicateTest::test_untracked_file_not_on_old_basename_whitelist_is_dirty

965 tests collected in 1.29s
```
That bare command does collect every `.py` test file under `test/`,
`tests/`, `gates/`, `on-the-record/hooks/`, and even
`harness/fixture-operator-experience/` (965 items, above). But two
git-tracked shell test files -- `tests/check-write-set-conflicts.test.sh`,
`tests/claim-scan-preflight.test.sh` -- are real tests (each exercises
`scripts/check-write-set-conflicts.sh` / `on-the-record/hooks/claim-scan-preflight.sh`
end-to-end per their own file headers) that `pytest` can never collect;
running every test in the repo still needs a second, separate invocation
(`bash tests/run-orchestrate-tests.sh`, per
`docs/handbooks/on-the-record.md`, which itself does not invoke those
two `.test.sh` files either -- `grep -n '.test.sh' tests/run-orchestrate-tests.sh`
returns no matches). The gate enumerates git-tracked
`test_*.py`/`*_test.py`/`*.test.sh` files, confirms each `.py` candidate
actually defines a collectible test item (excluding, e.g.,
`gates/test_tier_contract.py`, a parser module merely named `test_*.py`
that defines zero tests -- `python3 -m pytest gates/test_tier_contract.py -q`
reports "no tests ran"), and fails naming exactly these two `.test.sh`
files today, reproduced in the acceptance block above.

## Why

canonical: `gh pr view 3089` output (state: OPEN, headRefName
`issue-3083/diagnose-first+silent-failure-audit+test-derivation-3d40ffc9`)

The issue's explicit model is PR #3089 (issue-3083, not yet merged to
this session's `main` base per the canonical citation above): diagnose
every failure before touching any of them, classify each against the
same 3-way vocabulary (live defect / stale test / environment artifact),
cite the specific commit that made a stale test stale the way that PR's
own body cites issue #2969's debounce commit, and only then repair --
never by loosening an assertion. `CORE_BUILD_NOW=1` was set by the
spawner, authorizing single-session delivery (skip the proposal round),
so diagnosis and repair both landed in this one session, each fix
committed once its specific test file returned to green.

acceptance: `python3 -m pytest test/ -q` — result:
```
563 passed, 3 xfailed in 32.45s
```

## What did not work

- Running the whole `test/` directory together after fixing the 4
  dead-`checkout_issue_branch`-mock files individually surfaced a 16th,
  previously-invisible failure:
  `test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo`
  passed standalone and with just its own file, but failed inside the
  full directory.

  derived: reran `python3 -m pytest test/ -q` three times in a row after
  the fix below to confirm it was not itself flaky:
  ```
  $ for i in 1 2 3; do python3 -m pytest test/ -q; done
  563 passed, 3 xfailed
  563 passed, 3 xfailed
  563 passed, 3 xfailed
  ```
  and before the fix, reran the same full-directory command 3 times
  (all 3 showed the same single failure, same test, same KeyError) to
  confirm the pre-fix state was consistently reproducible rather than
  flaky, ruling out a timing coincidence in either direction.

  Expected the per-file fixes to be independent and complete; they were
  not quite -- `_spawn_one` writes two separate `ledger_write` entries
  per session (a `skill_judge_perf` sample alongside the outcome record
  this test checks), and `recorded[-1]` assumed the outcome entry always
  lands last. That held only by accident while the dead mock crashed
  before either write happened; once real, the two calls' relative order
  depends on scheduling that differs between running the file alone and
  running it inside the full directory. Bisected via file-list halving
  (52 other `test/` files down to 1: `test_auto_approval_shadow_wiring.py`
  run first was necessary to reproduce, though a manual same-process
  repro script running that file's `unittest` suite directly followed by
  the target function did not reproduce the KeyError -- confirming the
  dependency is on cross-file pytest-collection/scheduling timing rather
  than on any leaked module attribute, since the manual repro used the
  exact same monkeypatch/restore code path and still saw the ledger
  entries in the opposite, non-failing order). Fixed by searching
  `recorded` for the one entry carrying `skill_judge_outcome` instead of
  indexing positionally, still asserting exactly one such entry exists.
- Two of the "dead mock" fixes (`test_no_declaration_line_byte_identical_to_baseline`,
  `test_non_matching_task_mounts_and_directive_byte_identical_to_baseline`)
  did not fully pass on the first fix (repointing `checkout_issue_branch`
  alone). Once execution got further than before, it revealed a second,
  independent stale-mock gap: `gh_rest.fetch_issue`'s mocked return value
  predated issue #2395's contract change (which added `owner`/`repo` keys
  the real function has always returned since -- `gates/gh_rest.py:78-90`),
  and one file never mocked `gh_rest` at all, so a real (failing) `gh`
  lookup's error text, which embeds the tmpdir path, leaked into a
  byte-identical two-run comparison. Fixed by adding `owner`/`repo` to
  the mocked return (and adding the missing mock entirely in the
  cross-family-selection file).

## Upstream basis

canonical: `gh pr view 3089` output (state: OPEN) -- same citation as
the "Why" section above.

- Issue #3091 (this session's assignment), verbatim acceptance criteria
  (`gh issue view 3091`, read in full this session).
- PR #3089 / issue-3083, branch
  `issue-3083/diagnose-first+silent-failure-audit+test-derivation-3d40ffc9`
  on origin, not merged to this session's `main` base -- the model this
  diagnosis follows; its own PR body independently flagged `test/`'s 15
  failures as out of its scope, which is what this issue exists to take
  on.
- `docs/issue-729/proposals/2026-08-11-consolidate-test-homes.md` and
  `docs/issue-729/reports/implementation.md` (landed, commit `082bfd7b`)
  -- the prior `test/`->`tests/` consolidation.
- `docs/handbooks/test-layout.md` -- the still-current, still-valid
  placement rule the generic per-session directive template does not
  consult.
- Commits cited inline in the diagnosis table above: `96699800`,
  `2cc3cf4f`, `e1f390ab`, `b4d05522`, `2cc6d108`, `a4d85dbb`,
  `0879f12a`, `6ae45558`, `e7cd06c2`.

## Open findings

canonical: `gh pr view 3089` output (state: OPEN) -- same citation as
the "Why" section above.

- The generic per-session orchestrator directive template's "tests
  under test/" boilerplate is not repo-aware and will keep regrowing
  `test/` after any future consolidation unless a follow-up issue makes
  it consult a repo's own `docs/handbooks/test-layout.md`-style
  override. Resolution path: a new issue against the orchestrator
  template itself (it lives in the plugin's own patch assets, outside
  this repo's own `docs/`) -- flagged here since this diagnosis is what
  surfaced it, not resolved here since fixing it is a distinct, larger
  unit of work than this issue's own scope.
- `tests/` currently shows 5 failing tests in this sandbox
  (`test_respawn_deliverable_gate.py` x4, `test_spawn_gate_wiring.py` x1,
  per the acceptance block's `python3 -m pytest tests/ -q` rerun above)
  matching exactly what PR #3089/issue-3083 is fixing on its own,
  still-open branch, not yet merged to this session's base -- these are
  not a regression introduced here, and are out of this issue's scope
  (`test/` singular's 15 named failures) the same way PR #3089
  explicitly called `test/` out of its own scope. No action taken.

## Next steps

None -- `loop_state: landed`. The two open findings above name their own
follow-up scope explicitly rather than being addressed in this PR.

skill-verdict: other mounted skills: not triggered
