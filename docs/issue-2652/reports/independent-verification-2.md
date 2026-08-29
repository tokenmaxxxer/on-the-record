---
issue: 2652
role: independent-verification-2
author: independent-verification-2
verifies_subject: true
code_under_review: gates/spawn_on_pr.py::missing_verification() (PR #2768)
loop_state: complete
type: verification
breaking: false
verdict: fix-confirmed
upstream:
  - path: gates/spawn_on_pr.py
    sha: 6d6727b946348a55146f695e08a02775f8c88271
  - path: gates/test_spawn_on_pr.py
    sha: 6d6727b946348a55146f695e08a02775f8c88271
---

# issue-2652 — independent-verification-2 record

## What was done

Independently audited PR #2768 (`issue-2652: fix spawn-on-pr branch-missing
noise for closed issues`, still OPEN, base commit `1d6e746c`, head commit
`e71e8d2599efc3254194b8dced1ff61f67103ee3`), which claims to fix the ordering
bug described in issue #2652: `missing_verification()` checked
`pr_index`-branch-membership before the is-open check, so every closed
subject with an unmappable deliverable branch printed a "branch not found"
line before the is-open guard ever ran.

canonical: `gh pr view 2768` output (state: OPEN, additions: 638, deletions: 3,
head sha `e71e8d2599efc3254194b8dced1ff61f67103ee3`)

Verification method: fetched the PR branch into an isolated `git worktree`
(`/tmp/verify-2768`, never touching this session's own working tree) and ran
independently-written checks against it — not a re-run of the PR's own
scripts.

derived: `git fetch origin pull/2768/head:pr-2768-verify && git worktree add
/tmp/verify-2768 pr-2768-verify` — result: worktree created at
`e71e8d25`, base `1d6e746c` (same base this branch is on).
derived: `git log --oneline -3` (this branch, before starting) — `HEAD` was
`1fcf9e2d`, two commits ahead of `1d6e746c` on an unrelated issue-2705 line.

**1. Diff shape matches the claim.** Read `gates/spawn_on_pr.py` on this
branch (pre-fix, unmerged) at lines 385-430 before looking at the PR diff, to
verify the described bug independently rather than trusting the PR's own
description:

```python
        branch = subject_deliverable_branch(subject, pr_index)
        if branch is None:
            if spawn._watchdog_note_unmappable_subject_branch(root, subject):
                print(f"[spawn-on-pr] {subject}: deliverable 브랜치를 pr_index 에서 "
                      f"찾지 못했다 — 이번 틱은 건너뜀 (deficit={deficit})")
            else:
                unmappable_branch_already_reported += 1
            continue
        pr_number = _pr_number_for_branch(root, branch, pr_index)
        if pr_number is None:
            continue
        issue = int(subject.split("-", 1)[1])
        if not _issue_is_open(issue, issue_states):
            continue
```

The branch-missing print (and its `continue`) sits ahead of the
`_issue_is_open` guard in the loop body, matching the reported bug shape
verbatim.
derived: `git diff --stat gates/spawn_on_pr.py` (worktree, `pr-2768-verify`
vs. `1d6e746c`) → `1 file changed, 16 insertions(+), 3 deletions(-)`, all
inside `missing_verification()`. `gh pr diff 2768` shows the fix moves
exactly the `issue = int(...)` / `if not _issue_is_open(...): continue`
block 13 lines earlier, past the branch-missing block, plus one added
comment — no other logic touched.

**2. Regression-test discrimination check.** Ran the 3 new tests in
`gates/test_spawn_on_pr.py` against the PR's own code (post-fix).
acceptance: `python3 -m pytest gates/test_spawn_on_pr.py -q` — result: `19
passed in 1.46s`

Then, to check the tests actually discriminate pre/post-fix behavior (a test
that passes both before and after a fix proves nothing), copied the pre-fix
`gates/spawn_on_pr.py` (from base commit `1d6e746c`) into the worktree while
keeping the new tests, and re-ran just the 3 new tests against that pre-fix
source.
acceptance: `python3 -m pytest gates/test_spawn_on_pr.py -q -k "2652 or
unmappable or reports_missing_branch or mixed_only_open"` — result: `2
failed, 1 passed in 1.95s`

The two that fail against pre-fix code are
`test_closed_issue_with_unmappable_branch_prints_nothing` and
`test_closed_and_open_subjects_mixed_only_open_unmappable_branch_reported`
(both assert the closed-subject suppression the fix introduces); the one
that passes even pre-fix is
`test_open_subject_with_unmappable_branch_still_reports_missing_branch`
(asserts pre-existing behavior for open subjects, correctly unaffected by
the reorder). The post-fix `gates/spawn_on_pr.py` was restored immediately
after this check.

**3. Independent reproduction of all three acceptance criteria**, using a
synthetic-board script written from scratch (`/tmp/iv2_repro.py`, different
issue numbers and a larger closed-subject count than the PR's own
`/tmp/repro_before.py`, so the result would not depend on the author's own
fixture): 50 closed subjects (`issue-80000`..`issue-80049`), one OPEN
subject with a branch missing from `pr_index` (`issue-80500`), one OPEN
subject with a branch present in `pr_index` (`issue-80600`).

derived: pre-fix run (pre-fix `gates/spawn_on_pr.py` swapped into the
worktree) — `python3 /tmp/iv2_repro.py 2>&1 | grep -c "찾지 못했다"` → `51`
(50 closed + 1 open-unmappable). Post-fix run (PR's `gates/spawn_on_pr.py`
restored) — same grep → `1` (only `issue-80500` remains). The `RESULT:` line
(the return value of `missing_verification()`) was `{'issue-80600': 2}` in
both runs.

Mapping to the issue's three acceptance checks:
- criterion 1 (closed issue produces no per-tick output): the 50 closed
  subjects' lines go from present (pre-fix) to absent (post-fix), per the
  `51 → 1` count above.
- criterion 2 (open subject with a genuinely missing branch still reports):
  `issue-80500`'s line is the one line present in both pre-fix and post-fix
  output.
- criterion 3 (no spawning behavior change): ran
  `spawn_missing_for_pr(root, "/tmp/iv2root", issue_states=issue_states,
  pr_index=pr_index, dry_run=True)` against the same synthetic board, pre-fix
  and post-fix.
  acceptance: `python3 /tmp/iv2_repro.py` (both pre-fix and post-fix runs)
  — result: `DRYRUN: [('issue-80600', 'independent-verification-1'),
  ('issue-80600', 'independent-verification-2')]`, byte-identical in both
  runs.

**4. No regression, full suite.** Ran the full test suite before (pre-fix
code with the new tests present) and after (PR's own code).
acceptance: `python3 -m pytest -q` — result (pre-fix `gates/spawn_on_pr.py`,
new tests present): `18 failed, 551 passed, 3 xfailed` (the 16 unrelated
baseline failures plus the 2 new tests, which fail against pre-fix code per
point 2 above).
acceptance: `python3 -m pytest -q` — result (post-fix, PR's code): `16
failed, 553 passed, 3 xfailed in 5.94s`.
derived: `diff /tmp/iv2_baseline_failures.txt /tmp/iv2_after_failures.txt` —
the only difference is the 2 new-test lines present pre-fix and absent
post-fix; the remaining 16 failure lines are byte-identical between the two
files.

The 16 unrelated failures are a `git`/`gh` network-boundary class untouched
by this change.
derived: `cat /tmp/iv2_after_failures.txt` →
```
harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
test/test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape
test/test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
test/test_spawn_artifact_skill_pairing.py (2 tests)
test/test_spawn_cross_family_skill_selection.py (6 tests)
test/test_spawn_skill_judge_haiku_timeout_overlap.py (4 tests)
```
— the same file set the PR's own record names as pre-existing.

**5. Must-not clause (no name list / closed-set / identity enumeration).**
Read the full diff myself (quoted under point 1 above): the only change is
the pre-existing two-line guard clause relocated 13 lines earlier plus one
added comment block.
derived: `git diff --stat gates/spawn_on_pr.py` → `1 file changed, 16
insertions(+), 3 deletions(-)`, all inside `missing_verification()` — no
`if subject in {...}`, no closed-issue list, no new data structure
introduced.

## Why

Per `docs/handbooks/observer-verification.md`, a subject only counts as
independently verified when the record is written by a session other than
the PR's author. To honor that: the bug shape was re-derived from the
pre-fix source directly (quoted under "What was done" point 1), read before
looking at the PR diff or the issue text; the reproduction used a script
written from scratch with different subject counts and issue numbers than
the PR's own script (point 3); and the 3 new tests were run against the
pre-fix source as a discrimination check (point 2) — something the PR's own
record does not do.
acceptance: `python3 -m pytest gates/test_spawn_on_pr.py -q -k "2652 or
unmappable or reports_missing_branch or mixed_only_open"` — result: `2
failed, 1 passed` (against pre-fix source; repeated from "What was done"
point 2).

## What did not work

None — the audit did not need to backtrack on any executed step. One early
approach considered `git checkout` on a detached ref of the PR commit
directly in this session's own working tree; abandoned before running any
command, in favor of an isolated `git worktree add` (see "What was done"),
to avoid any risk of disturbing this branch's own tracked state — this
branch has an untracked `docs/issue-2652/` directory that an unrelated
checkout must not touch.

## Upstream basis

- `gates/spawn_on_pr.py` — reordered `missing_verification()`, verified
  directly against a fetched copy of PR #2768's fix commit
  (`sha: 6d6727b946348a55146f695e08a02775f8c88271`).
  derived: `git show e71e8d2599efc3254194b8dced1ff61f67103ee3 --stat` → one
  file changed, 2 insertions, in a deviation-log path under this issue's
  reports directory — confirming the PR's head commit on top of the fix
  commit touches neither `gates/spawn_on_pr.py` nor
  `gates/test_spawn_on_pr.py`.
- `gates/test_spawn_on_pr.py` — 3 new regression tests, same commit
  (`sha: 6d6727b946348a55146f695e08a02775f8c88271`).
- The PR author's own record, `docs/issue-2652/reports/adversarial-review+architecture-coupling-classification-3b733611.md`
  (untracked on this branch — exists only on PR #2768's own branch,
  `sha: e71e8d2599efc3254194b8dced1ff61f67103ee3`), was read in full for
  cross-reference; its claimed test counts, failure-set diff, and dry-run
  comparison were independently re-derived above (see "What was done"
  points 2-4) rather than taken on trust.

## Open findings

None surviving independent re-check. The PR author's own record (cited
above under "Upstream basis") documents 4 adversarial-review findings: 1
confirmed-and-accepted as intended behavior (the watchdog one-shot marker no
longer accumulates entries for closed subjects, which matches acceptance
criterion 2's requirement that reopened subjects still get reported once);
1 pre-existing/out-of-scope (unvalidated `int(subject.split(...))`); 1
not-applicable (an artifact of reviewing an unfilled record mid-task); 1
investigated-and-does-not-survive (a claimed `gh`-fallback interaction).

I independently re-traced the fourth finding myself.
canonical: `gates/spawn_on_pr.py:240-244` in the `pr-2768-verify` worktree,
quoted verbatim:
```python
def subject_deliverable_branch(subject: str, pr_index: dict[str, dict] | None) -> str | None:
    if pr_index is None:
        return None
```
`branch` is therefore already `None` and the loop `continue`s before
`_pr_number_for_branch` — whose `gh`-fallback branch only fires when its own
`pr_index` argument is `None` — is ever reached from this call site, in
either guard order. Same conclusion as the PR's record, reached here by
re-reading the source directly.

## Next steps

None — all evidence needed for `verifies_subject: true` is already recorded
above under "What was done".
derived: `git diff --stat gates/spawn_on_pr.py` (repeated from "What was
done" point 1) — `1 file changed, 16 insertions(+), 3 deletions(-)`.

The reorder matches the diff-shape check (point 1), the 3 new tests
discriminate pre/post-fix behavior (point 2), all 3 issue acceptance
criteria reproduce independently under a fixture this session wrote from
scratch (point 3), the full-suite failure set is unchanged (point 4), and
the "must not" clause holds by direct diff inspection (point 5).

skill-verdict: work-in-english — applied: invoked; this record, all
temporary scripts, and the verification worktree/branch names were written
in English per the skill; the end-of-turn summary to the user is in Korean.
