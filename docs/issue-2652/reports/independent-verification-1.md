---
issue: 2652
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
loop_state: complete
upstream:
  - path: gates/spawn_on_pr.py
    sha: 6d6727b946348a55146f695e08a02775f8c88271
  - path: gates/test_spawn_on_pr.py
    sha: 6d6727b946348a55146f695e08a02775f8c88271
  - path: docs/issue-2652/reports/adversarial-review+architecture-coupling-classification-3b733611.md  # untracked in this worktree -- lives only on the unmerged PR #2768 source branch, read via `git show`
    sha: 6d6727b946348a55146f695e08a02775f8c88271
---

# issue-2652 — independent-verification-1 record

## What was done

Independently audited PR #2768 (`issue-2652/adversarial-review+architecture-coupling-classification-3b733611`,
branch head `e71e8d2599efc3254194b8dced1ff61f67103ee3`), which fixes
`gates/spawn_on_pr.py::missing_verification()` by reordering the
pre-existing is-open check ahead of the pr_index-membership check.
Checked out the PR branch and `origin/main` into two separate worktrees
(`/tmp/pr2768-verify`, `/tmp/main-verify`), reviewed the diff, and
re-derived each acceptance criterion with a repro script written in this
session (not the PR's own scripts).

canonical: `git diff origin/main origin/issue-2652/adversarial-review+architecture-coupling-classification-3b733611 -- gates/spawn_on_pr.py`, executed in this session
```diff
@@ -395,6 +395,19 @@ def missing_verification(root: Path, issue_states: dict[int, str] | None = None,
             continue
+        issue = int(subject.split("-", 1)[1])
+        if not _issue_is_open(issue, issue_states):
+            continue
         # issue #2575: ...
@@ -415,9 +428,6 @@ def missing_verification(root: Path, issue_states: dict[int, str] | None = None,
         pr_number = _pr_number_for_branch(root, branch, pr_index)
         if pr_number is None:
             continue
-        issue = int(subject.split("-", 1)[1])
-        if not _issue_is_open(issue, issue_states):
-            continue
         pr_state = _pr_state_for_branch(root, branch, pr_index)
```
This is a pure relocation of an already-existing two-line guard 13 lines
earlier in the loop body, plus one new comment block — no new lookup, no
name list, no closed set, matching the issue's "must not" constraint.

acceptance: python3 repro script (written in this session, run from
`/tmp/pr2768-verify`, the PR-branch worktree) — result:
```
printed lines: 1
['[spawn-on-pr] issue-80100: deliverable 브랜치를 pr_index 에서 찾지 못했다 — 이번 틱은 건너뜀 (deficit=2)']
out: {'issue-80200': 2}
```
Fixture: a board of 30 CLOSED subjects with unmappable branches, 1 OPEN
subject with a genuinely unmappable branch (`issue-80100`), 1 OPEN
subject with a mapped branch (`issue-80200`). Only the OPEN
unmappable-branch subject printed — satisfies acceptance criterion 1 (no
per-tick output for closed subjects) and acceptance criterion 2 (an open
subject's genuinely-missing branch still reports).

acceptance: the same script re-run unmodified from `/tmp/main-verify`
(pre-fix `origin/main` worktree, identical fixture) — result:
```
printed lines: 31
out: {'issue-80200': 2}
```
`missing_verification()`'s returned spawn-candidate mapping is
byte-identical (`{'issue-80200': 2}`) before and after the fix — this is
the value `spawn_missing_for_pr(..., dry_run=True)` consumes to decide
who to spawn, so this satisfies acceptance criterion 3 (no spawning
behavior change). Only the printed-line count changed (31 → 1).

acceptance: `python3 -m pytest gates/test_spawn_on_pr.py -q`, run in
`/tmp/pr2768-verify` — result: `19 passed in 1.39s` (16 pre-existing + 3
new: `test_closed_issue_with_unmappable_branch_prints_nothing`,
`test_open_subject_with_unmappable_branch_still_reports_missing_branch`,
`test_closed_and_open_subjects_mixed_only_open_unmappable_branch_reported`).
Read all three; each maps 1:1 to one of the three acceptance checks above
and exercises the real `missing_verification()` entrypoint rather than
mocking the function under test.

acceptance: `python3 -m pytest -q`, run in both worktrees, `FAILED` lines
extracted and sorted, then diffed —
```
$ diff /tmp/main_failed.txt /tmp/pr_failed.txt && echo "IDENTICAL FAILING SETS"
IDENTICAL FAILING SETS
```
Both runs: 16 failed (same 16 test names, unrelated `gh`/network-boundary
gaps), 3 xfailed; 553 passed on the PR branch vs. 550 passed on main (the
3 new tests). No regression introduced by this change.

## Why

The PR's own record (untracked in this worktree, lives only on the
unmerged PR branch — `6d6727b9:docs/issue-2652/reports/adversarial-review+architecture-coupling-classification-3b733611.md`,
read via `git show` from the PR branch) already quotes strong claims
(31→1 lines, dry-run parity, identical failing-test set) with its own
scripts and outputs. Independent verification means re-deriving those
same claims with separately written tooling checked out from the actual
PR branch, rather than trusting the record's transcription — which is
what the `acceptance:` blocks in "What was done" above do.

canonical: `6d6727b9:docs/issue-2652/reports/adversarial-review+architecture-coupling-classification-3b733611.md` (untracked in this worktree, read via `git show` from the PR branch), `## Open findings` section — quotes four adversarial-review findings and their resolutions. Checked each against the code independently rather than accepting the record's resolution on its face:

1. Watchdog one-shot-marker state (`watchdog_noise_state.json`) no longer
   accumulates entries for closed subjects — consistent with the reordered
   guard quoted in "What was done": a closed subject's `continue` now
   fires before `_watchdog_note_unmappable_subject_branch()` is ever
   called, and with acceptance criterion 1 (no per-tick output at all for
   closed subjects, so no marker call either). Not a defect.
2. `int(subject.split("-", 1)[1])` has no validation — checked against
   `git show origin/main:gates/spawn_on_pr.py` (pre-fix): the same
   unguarded call already existed 13 lines later in the pre-fix loop body,
   reachable by every subject that passed the earlier `deficit`/
   `merged_seen` guards. The reorder moves this call's position, not its
   reachability set. Correctly scoped out as pre-existing, not introduced
   by this fix.
3. Template-record false positive, flagged mid-task before the record was
   assembled — moot against the merged file: `git show
   origin/issue-2652/adversarial-review+architecture-coupling-classification-3b733611:docs/issue-2652/reports/adversarial-review+architecture-coupling-classification-3b733611.md`
   shows all `##` sections (`What was done` through `Architecture coupling
   classification`) fully populated in the landed version, no template
   placeholders remain.
4. `gh`-fallback interaction claim — checked
   `subject_deliverable_branch()` (`6d6727b9:gates/spawn_on_pr.py:224-244`,
   identical pre- and post-fix per the diff in "What was done", which
   touches only lines 395-430): returns `None` immediately when
   `pr_index is None`, so the loop `continue`s before
   `_pr_number_for_branch`'s `gh`-fallback branch (which only fires when
   its own `pr_index` argument is `None`) is ever reached from this call
   site, regardless of guard order. Confirmed no behavioral difference;
   the record's rebuttal holds.

All four resolutions hold up against independent code reading. No new
findings surfaced beyond what the adversarial-review record already
raised and resolved.

## What did not work

None.

## Upstream basis

- `gates/spawn_on_pr.py` (`sha: 6d6727b946348a55146f695e08a02775f8c88271`,
  head of PR #2768's source branch) — the reordering fix, quoted in full
  in "What was done".
- `gates/test_spawn_on_pr.py` (same sha) — the three new regression tests.
- `docs/issue-2652/reports/adversarial-review+architecture-coupling-classification-3b733611.md`
  (same sha; untracked in this worktree, read via `git show` from the PR
  branch) — the adversarial-review and architecture-coupling-
  classification record whose four findings and claimed evidence this
  verification independently re-derived.

## Open findings

None. All three acceptance criteria and the "must not" constraint hold
under independent re-derivation (see the `acceptance:`-tagged blocks in
"What was done"); the full test suite shows no regression; the
adversarial-review record's four resolved findings hold up under
independent code reading (see "Why").

## Next steps

None. `derived: gh pr view 2768 --json state,mergedAt,mergeable`, executed
in this session — result: `{"mergeable":"MERGEABLE","mergedAt":null,"state":"OPEN"}`.
PR #2768 is open and not yet merged at time of this review; this record
supplies one of the two required independent-verification records for the
subject (`verifies_subject: true`, `author: independent-verification-1`,
which differs from the subject's deliverable author
`adversarial-review+architecture-coupling-classification-3b733611`).

skill-verdict: work-in-english — applied: invoked; wrote this record,
commit messages, and PR title/body in English per project convention
(subject text was in Korean), final chat summary to the user in Korean.
