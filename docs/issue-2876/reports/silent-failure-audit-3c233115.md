---
issue: 2876
role: silent-failure-audit-3c233115
author: silent-failure-audit-3c233115
skills: silent-failure-audit (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: gates/retirement_count.py, test/test_retirement_count.py, docs/specs/enforcement-boundary.md
type: implementation-record
breaking: false
verdict: cwd-narrowing-fixed, unreadable-file-narrowing-fixed, refuse-on-undetermined-population-established
loop_state: landed
upstream:
  - path: docs/issue-2876/reports/silent-failure-audit-b01a1db4.md
    sha: 30c577f4f677f80f657eebffbb7196d3dba0f937
  - path: docs/issue-2876/reports/independent-verification-2.md
    sha: 16fbe3723c991671b84248f5e5b7f845ca6ac69e
  - path: gates/retirement_count.py
    sha: same-commit
  - path: test/test_retirement_count.py
    sha: same-commit
---

# issue-2876 — silent-failure-audit-3c233115 record

skill-verdict: silent-failure-audit — applied: invoked; audited `gates/retirement_count.py`'s error-handling sites and reclassified the scan loop's `except OSError: continue` as Silently Absorbed, fixed below — derived: `python3 -m pytest test/test_retirement_count.py -q`, run this session on the post-fix tree, result: `16 passed`
skill-verdict: work-in-english — applied: invoked; this record, commit messages, code comments, and test names are in English per this session's convention

## What was done

Round 3 on PR #2887 (branch `issue-2876/silent-failure-audit-b01a1db4`), following independent verification #2889's finding that `gates/retirement_count.py`'s `--list-files` mode carries the same silent-narrowing defect it was built to remove: `tracked_sources()` called `git ls-files "*.py" "*.sh"` with no cwd anchor, so running the module's own documented recipe (`python3 gates/retirement_count.py --list-files`) from any cwd other than the repo root silently returned a narrower — or differently-rooted — file list, with no error signal.

Two fixes landed in `gates/retirement_count.py` (canonical: `gates/retirement_count.py`, `repo_toplevel()`/`tracked_sources()`/`main()`, read and edited this session):

1. **cwd-independence.** Added `repo_toplevel()`, which resolves the repo root via `git rev-parse --show-toplevel` (anchored to the ambient cwd, the same way git itself resolves which repo a command targets — not hardcoded to this file's own `__file__` location). `tracked_sources()` now runs `git ls-files` with `cwd=toplevel`, and `main()`'s per-file `open()` calls join against that same `toplevel`.
   derived: reproduced the pre-fix bug from the pre-fix blob and confirmed the fix, this session:
   ```
   $ (cd gates && python3 /tmp/old_retirement_count.py --list-files | wc -l)   # /tmp/old_retirement_count.py == `git show origin/issue-2876/silent-failure-audit-b01a1db4:gates/retirement_count.py`
   72
   $ python3 gates/retirement_count.py --list-files | wc -l          # post-fix, from repo root
   251
   $ (cd gates && python3 retirement_count.py --list-files | wc -l)  # post-fix, from gates/ subdir
   251
   $ (cd on-the-record/hooks && python3 ../../gates/retirement_count.py --list-files | wc -l)
   251
   $ python3 gates/retirement_count.py 2>&1 >/dev/null | tail -1      # full scan, repo root
   retirement_count: 1183 occurrence(s) of the retired role/roles axis in py/sh sources (docs/ excluded)
   $ (cd gates && python3 retirement_count.py 2>&1 >/dev/null | tail -1)  # full scan, gates/ subdir
   retirement_count: 1183 occurrence(s) of the retired role/roles axis in py/sh sources (docs/ excluded)
   ```
2. **Refuse instead of returning a partial population.** `tracked_sources()` now raises `RuntimeError` if the resolved population is empty (this repo, and any git repo used as a target including the hermetic scratch repos this module's own tests build, is never actually empty of py/sh files) — an empty result there means the search never reached the tree, not that the tree is empty. `main()` catches this (and a `git` invocation failure, `subprocess.CalledProcessError`) and returns exit code **2**, distinct from `0` (0 occurrences, search ran and covered the tree) and `1` (occurrences found).
   derived: `python3 -m pytest test/test_retirement_count.py -q -k RefusesRatherThanReturningAPartialPopulationTest`, run this session, result: `3 passed` (`test_tracked_sources_raises_when_git_ls_files_finds_nothing`, `test_main_exits_with_a_distinct_code_and_says_population_undetermined` covering both `argv=[]` and `argv=["--list-files"]`).

A third, related defect surfaced by applying the mounted `silent-failure-audit` skill's classification procedure to the fixed file (not part of the assigned round-3 finding, but the same shape — found per the issue's own closing instruction to "look once more" for it): canonical: `gates/retirement_count.py`'s scan loop, pre-this-session's-second-edit, read this session — `except OSError: continue` silently skipped any tracked file that failed to open (deleted between `git ls-files` and `open()`, a broken symlink, a permission error), producing a count that would read as a clean, fully-covered scan even though that file was never actually inspected for the retired axis. Classified under the skill's taxonomy as Silently Absorbed (error caught, execution continues on a path that assumes success, no record that a file was skipped); forward trace: catch site → `continue` → loop proceeds to the next file → final printed count is silently short by however many lines that file would have contributed → no indication anywhere in the output that a file was skipped. Fixed the same way as the two population-level defects: unreadable files are now collected, and if any exist, `main()` prints each one to stderr and returns exit code 2.
derived: `python3 -m pytest test/test_retirement_count.py -q -k test_unreadable_tracked_file_refuses_instead_of_a_possibly_partial_count`, run this session (test builds a scratch git repo, `git add`s a file, then `os.remove`s it before invoking the checker), result: `1 passed` — the checker exits 2 and names the removed file in stderr rather than silently omitting it from the count.

Also updated `docs/specs/enforcement-boundary.md`'s existing `retirement_count.py` row to document the new exit-code-2 refusal behavior and the cwd-independence fix. canonical: `python3 gates/spec_index.py --update`, run this session on this branch's tree — result: same pre-existing `FileNotFoundError: .../roles/specs/brand-design.spec.json` documented in round 1's record (`docs/issue-2876/reports/silent-failure-audit-133bcbf6.md`) as unrelated to this issue, reproduced again this session, still not fixed here (out of scope).

Test coverage added to `test/test_retirement_count.py`: 4 new test methods (`ListFilesIsCwdIndependentTest` x2, `RefusesRatherThanReturningAPartialPopulationTest` x3, one of which is a `subTest` over 2 argv shapes counted as one method) alongside the 11 pre-existing ones.
derived: `python3 -m pytest test/test_retirement_count.py -q`, run this session, result: `16 passed`.

## Why

The finding named a structural pattern, not a one-off bug: "an empty result and an unreached search are indistinguishable" had already recurred twice inside this issue's own fix (the plural blind spot, then the hand-typed `--include` list missing `.sh`), and round 2's own general-fix mechanism (`--list-files`/`tracked_sources()`) carried the identical shape a third time via an unanchored cwd. The instruction was explicit: fix the mechanism so it "cannot be invoked into a partial state at all," and decide what distinguishes "no matches" from "nothing searched" rather than leaving them as the same output.

`repo_toplevel()` via `git rev-parse --show-toplevel` (not a hardcoded path derived from this file's own location) was chosen over the alternative of anchoring to `__file__`'s containing repo specifically because the latter breaks the existing hermetic tests (`EmptyStateExitsCleanNotErrorTest`) that deliberately point `cwd` at a disposable scratch git repo to sandbox the checker's clean/dirty behavior without touching this repo's own tree.
derived: tried a `__file__`-anchored `REPO_ROOT` version first, this session — result: `python3 -m pytest test/test_retirement_count.py -q` on that version failed both `EmptyStateExitsCleanNotErrorTest` methods (`AssertionError: 'dirty.py:1:' not found in ''`, the scratch-repo file silently invisible to the real-repo-anchored scan), which is what motivated switching to the dynamic `git rev-parse --show-toplevel` approach actually landed. Dynamic toplevel discovery preserves that legitimate use of cwd (pick which repo to scan) while eliminating the illegitimate one (silently narrowing scope within the *same* repo depending on which subdirectory the caller happens to be in).

The exit-code-2 refusal (rather than, say, an empty stdout with exit 0) was chosen because `0` already has a defined, load-bearing meaning ("ran, covered the tree, found zero occurrences") that this issue's own Acceptance requires stay clean-exiting; overloading it to also mean "could not determine coverage" would silently reintroduce exactly the ambiguity this round exists to remove. A third, distinct code makes the failure mode observable to any script consuming the exit status without requiring it to parse stderr text.

The third fix (unreadable tracked files) was found by applying the `silent-failure-audit` skill's classification procedure (references/silent-failure-catalog.md's Silently Absorbed category, per the skill's own SKILL.md read this session) to the file after the first two fixes landed. Fixing it now, in the same round, follows the issue's explicit closing instruction to look for the same shape again in what this issue's own three rounds have landed, rather than opening a fourth round for a defect found via the mandated audit of the very file this round already touches.

## What did not work

The first attempt at the cwd fix hardcoded `REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` and anchored `tracked_sources()`'s `git ls-files` call to it directly. derived: `python3 -m pytest test/test_retirement_count.py -q`, run this session against that version, result: 2 failures in `EmptyStateExitsCleanNotErrorTest` (`test_one_occurrence_fails_nonzero_and_lists_the_site`, `test_zero_occurrences_returns_zero_and_prints_nothing_to_stdout`) — both tests build a scratch git repo in a tempdir and invoke the checker with `cwd=<tempdir>` specifically to sandbox it against a different tree; hardcoding the anchor to this file's own containing repo made the checker always scan the real repo regardless of that tempdir, breaking the sandbox. Replaced with `repo_toplevel()` (`git rev-parse --show-toplevel`, resolved from the ambient cwd rather than `__file__`), which fixed the round-3 finding's subdirectory case without breaking the scratch-repo tests — canonical: same `python3 -m pytest test/test_retirement_count.py -q` command, re-run after the fix, result: `16 passed` (11 pre-existing + this session's 5 new methods, one exercised via `subTest` over 2 argv shapes).

## Upstream basis

- `docs/issue-2876/reports/silent-failure-audit-b01a1db4.md` (sha `30c577f4f677f80f657eebffbb7196d3dba0f937`, PR #2887's round-2 record) — this round's `gates/retirement_count.py`, `tracked_sources()`, and `--list-files` mode are that PR's delivered baseline. derived: `git log --oneline -1 origin/issue-2876/silent-failure-audit-b01a1db4` → `30c577f4 issue-2876: deviation log and product-priority capture for round 2`, then `git merge --no-edit origin/issue-2876/silent-failure-audit-b01a1db4`, both run this session — merged into this branch rather than re-derived.
- `docs/issue-2876/reports/independent-verification-2.md` (sha `16fbe3723c991671b84248f5e5b7f845ca6ac69e`, already on `main` as PR #2889, canonical: `git log --oneline -1 16fbe372` read this session) — the round this session directly responds to; its "Attacked the round's central... claim" section is the finding this round's cwd fix addresses, and its "Checked and cleared (not a finding)" section (the `*.py`/`*.sh` extension scope) was not redone here.

## Open findings

- The three pre-existing open findings carried forward unchanged from round 1's record (`docs/issue-2876/reports/silent-failure-audit-133bcbf6.md`, "Open findings" section, read this session — the 83-site pending-migration baseline tracked by issue #2241; the `roles/*.json`/`PROTECTED_ROOT_DIRS` cross-repo-layout question; `retirement_count.sh` not wired into a blocking gate) are unchanged by this round and not re-litigated here.
- The pre-existing `python3 gates/spec_index.py --update` regeneration failure — derived: reproduced this session (see "What was done" above) — still unrelated to this issue's changes and still not fixed here, per round 1's original disposition of it as out of scope.

## Standing invariants (per this round's spawn brief)

1. No return of the retired role axis in any reshaped form, from a non-root cwd as well.
   derived: `python3 gates/retirement_count.py 2>&1 >/dev/null | tail -1` from repo root → `retirement_count: 1183 occurrence(s)...`; `(cd gates && python3 retirement_count.py 2>&1 >/dev/null | tail -1)` from `gates/` subdir → identical `retirement_count: 1183 occurrence(s)...` (both run this session). 1183 matches the baseline recorded in round 2's own record (`docs/issue-2876/reports/silent-failure-audit-b01a1db4.md`, "derived: `bash gates/retirement_count.sh`... result: `retirement_count: 1183 occurrence(s)`"), i.e. unchanged by this round's own additions (this round's new comments/code live in the checker's 3 self-excluded files).
2. No new bug, failing-test set vs `origin/main` as sets of names (collection scope: `python3 -m pytest test/ -q`, this repo's full `test/` tree).
   derived: ran `python3 -m pytest test/ -q` on this branch (this session) → `15 failed, 467 passed, 3 xfailed`, and on a scratch worktree of `origin/main` (`git worktree add --detach /tmp/verify-2876-main origin/main`, removed with `git worktree remove --force` after) → `15 failed, 450 passed, 3 xfailed`. 467 - 450 = 17 additional passing tests on this branch (this branch's own added tests: round 1/2's `test_retirement_count.py`/`test_convention_equivalence.py` additions plus this round's 4 new methods). Compared the two `short test summary info` failing-name lists by reading both in full, this session — byte-identical set of 15 names on both:
   ```
   test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape
   test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
   test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
   test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate
   test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline
   test_spawn_cross_family_skill_selection.py::FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled
   test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive
   test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces
   test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths
   test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline
   test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_declared_artifact_matching_skill_gets_pairing_line
   test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows
   test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo
   test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome
   test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome
   ```
3. No overhead increase.
   derived: `for i in 1 2 3; do /usr/bin/time -f "%e s" bash gates/retirement_count.sh >/dev/null 2>>timing.txt; done`, run this session post-fix → `0.18s, 0.20s, 0.20s`. Round 2's own record (`docs/issue-2876/reports/silent-failure-audit-b01a1db4.md`) measured its baseline as `real 0m0.184s` with the same command. The one additional `git rev-parse --show-toplevel` subprocess call this fix requires (down from an intermediate 3-call version to today's 2-call `repo_toplevel()`-then-`ls-files` version, canonical: `gates/retirement_count.py`'s `tracked_sources()`/`main()`, read this session) keeps the measured range within the same noise band as the 0.184s baseline.
4. Monitor and watch machinery unbroken and not quieter.
   derived: this round touched only `gates/retirement_count.py`, `test/test_retirement_count.py`, and `docs/specs/enforcement-boundary.md` — canonical: `git diff --stat` against this session's base commit, read this session, shows no path under `on-the-record/monitors/`, `watchdog.py`, or `test/test_watchdog_heartbeat_noise.py`. `test/test_watchdog_heartbeat_noise.py` passed in both the `origin/main` and this-branch `python3 -m pytest test/ -q` runs above (not present in either failing-name list), and every `print()` call that existed in `gates/retirement_count.py` before this round (the per-site lines, the summary line) is still reached on the success/found-occurrences paths — this round only adds new `print()` calls on the new refuse path, never removes an existing one.

## Next steps

None — `loop_state: landed`.
