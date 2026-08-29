---
issue: 2709
role: adversarial-review-41dcc2f1
author: adversarial-review-41dcc2f1
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
code_under_review: 56fd6e85c785aee8fbb2ff5e76cf67c7de710fca
type: review
breaking: false
verdict: pass
upstream:
  - path: on-the-record/hooks/upstream-defect-scope-guard.sh
    sha: 200d08aee6a54b68832816eff4b7a29916509173
  - path: test/test_upstream_defect_scope_guard_cross_repo_cwd.py
    sha: cf4ba0bdb2078ed39f8b01c28563aff7687e9ad0
---

# issue-2709 — adversarial-review-41dcc2f1 record

## What was done

Independently re-derived PR #2750 (tokenmaxxxer/on-the-record) in a
separate worktree at `/tmp/otr-pr2750` (branch `pr-2750-review`), never
touching this session's own branch — derived: `git -C /tmp/otr-pr2750
rev-parse HEAD` → `56fd6e85c785aee8fbb2ff5e76cf67c7de710fca`.

### Task A — self-built mutants, not the PR's own table

Copied `on-the-record/hooks/upstream-defect-scope-guard.sh` to
`/tmp/otr-mutants/` and edited only `operative_cwd()` in each scratch
copy, never the real repo file:

- pushd-mutant: `m = re.match(r'^\s*(?:cd|pushd)\s+(...)\s*(?:&&|;)', cmd)`
- subshell-mutant: `m = re.match(r'^\s*\(?\s*cd\s+(...)\s*(?:&&|;)', cmd)`
- chained-mutant: after the original match, also scans
  `re.finditer(r'(?:^\s*|&&\s*)cd\s+(...)\s*(?=&&|;)', cmd)` and takes
  `matches[-1]` (the LAST chained `cd`), not the first.

Ran the PR's actual three new tests against each, via a full throwaway
copy of the worktree (`/tmp/otr-pytest-mutant`) with each mutant swapped
into `on-the-record/hooks/upstream-defect-scope-guard.sh`. derived:
```
$ cd /tmp/otr-pytest-mutant && python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -q -k "pushd_not_followed or subshell_cd_not_followed or chained_cd_uses_first_target"
# shipped hook:
3 passed in 0.88s
# pushd-mutant.sh swapped in:
1 failed, 2 passed in 0.89s   (FAILED ...::test_pushd_not_followed_still_denied, AssertionError: 0 != 2)
# subshell-mutant.sh swapped in:
1 failed, 2 passed in 0.89s   (FAILED ...::test_subshell_cd_not_followed_still_denied, AssertionError: 0 != 2)
# chained-mutant.sh swapped in:
1 failed, 2 passed in 0.91s   (FAILED ...::test_chained_cd_uses_first_target_not_final_still_denied, AssertionError: 0 != 2)
```

Result table (P = pytest pass, agrees with today's deny; F = pytest fail,
flips to allow):

| test | shipped | pushd-mutant | subshell-mutant | chained-mutant |
|---|---|---|---|---|
| `test_pushd_not_followed_still_denied` | P | F | P | P |
| `test_subshell_cd_not_followed_still_denied` | P | P | F | P |
| `test_chained_cd_uses_first_target_not_final_still_denied` | P | P | P | F |

A second, independently-written harness not using the test file's own
helpers (`/tmp/otr-mutants/run_check.py`) reproduces the identical
diagonal directly against each hook binary — derived:
```
$ python3 /tmp/otr-mutants/run_check.py <hook>.sh   # run once per hook
=== shipped ===         pushd: rc=2   subshell: rc=2   chained: rc=2
=== pushd-mutant ===    pushd: rc=0   subshell: rc=2   chained: rc=2
=== subshell-mutant === pushd: rc=2   subshell: rc=0   chained: rc=2
=== chained-mutant ===  pushd: rc=2   subshell: rc=2   chained: rc=0
```
Every test flips to F under exactly its own matching mutant only, in both
independently-built harnesses. No test survives its own matching mutant.

### Task B — crash-vs-deny blindness

(1) derived: `grep -n "def test_\|_assert_denied_for_documented_reason"
test/test_upstream_defect_scope_guard_cross_repo_cwd.py` (in
`/tmp/otr-pr2750`) →
```
185:    def test_pushd_not_followed_still_denied(self):
195:        self.assertEqual(r.returncode, 2, r.stderr)
196:        _assert_denied_for_documented_reason(self, r)
198:    def test_subshell_cd_not_followed_still_denied(self):
207:        self.assertEqual(r.returncode, 2, r.stderr)
208:        _assert_denied_for_documented_reason(self, r)
210:    def test_chained_cd_uses_first_target_not_final_still_denied(self):
222:        self.assertEqual(r.returncode, 2, r.stderr)
223:        _assert_denied_for_documented_reason(self, r)
```
All three new tests call the helper on the line right after the
returncode assertion.

(2) Crash mutant: injected `raise RuntimeError("injected crash mutant —
issue #2709 review")` as the first line of `operative_cwd()` in
`/tmp/otr-mutants/crash-mutant.sh` — bash's own trap (`upstream-defect-
scope-guard.sh` line 99, `trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2
]; then exit 2; fi' EXIT`) remaps the uncaught exception's exit to 2.
derived:
```
$ cd /tmp/otr-pytest-mutant && python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -q -k "pushd_not_followed or subshell_cd_not_followed or chained_cd_uses_first_target"
# crash-mutant.sh swapped in:
E   AssertionError: 'issue #1131 req#4' not found in 'Traceback (most recent call last):\n...RuntimeError: injected crash mutant — issue #2709 review\n'
FAILED ...::test_subshell_cd_not_followed_still_denied
FAILED ...::test_chained_cd_uses_first_target_not_final_still_denied
FAILED ...::test_pushd_not_followed_still_denied
3 failed in 0.90s
```
The `assertEqual(r.returncode, 2, ...)` line alone would have passed all
three (rc really is 2 under the trap remap); `_assert_denied_for_documented_reason`'s `assertIn("issue #1131 req#4", result.stderr)` is
what catches the traceback text and fails them instead — this run is the
evidence that the helper does real discriminating work, not decoration.

(3) derived: `grep -n "def test_\|_assert_denied_for_documented_reason\|assertEqual(r.returncode" test/test_upstream_defect_scope_guard_cross_repo_cwd.py` (in `/tmp/otr-pr2750`) →
```
144:    def test_same_call_without_cd_still_denied(self):
150:        self.assertEqual(r.returncode, 2, r.stderr)
152:    def test_unrelated_upstream_repo_still_denied(self):
160:        self.assertEqual(r.returncode, 2, r.stderr)
162:    def test_cd_into_unrelated_repo_checkout_still_denied(self):
171:        self.assertEqual(r.returncode, 2, r.stderr)
232:    def test_cd_into_non_checkout_dir_still_denied(self):
241:        self.assertEqual(r.returncode, 2, r.stderr)
243:    def test_cd_into_nonexistent_dir_still_denied(self):
248:        self.assertEqual(r.returncode, 2, r.stderr)
272:    def test_spoofed_origin_remote_bypass_should_be_denied(self):
279:        self.assertEqual(r.returncode, 2, r.stderr)
296:    def test_harness_cwd_origin_removed_bypass_should_be_denied(self):
305:        self.assertEqual(r.returncode, 2, r.stderr)
```
(the three new tests, already shown in (1) above with their adjacent
helper calls, are omitted from this listing.) Each `def test_` name shown
in this fence has a bare `assertEqual(r.returncode, 2` with no
`_assert_denied_for_documented_reason` call before the next `def test_`:
`test_same_call_without_cd_still_denied`,
`test_unrelated_upstream_repo_still_denied`,
`test_cd_into_unrelated_repo_checkout_still_denied`,
`test_cd_into_non_checkout_dir_still_denied`,
`test_cd_into_nonexistent_dir_still_denied`,
`test_spoofed_origin_remote_bypass_should_be_denied` (marked
`@unittest.expectedFailure`), and
`test_harness_cwd_origin_removed_bypass_should_be_denied` (also
`@unittest.expectedFailure`).

derived: `git diff 00aeaae4 pr-2750-review -- test/test_upstream_defect_scope_guard_cross_repo_cwd.py` (merge-base vs PR head) →
```
--- a/test/test_upstream_defect_scope_guard_cross_repo_cwd.py
+++ b/test/test_upstream_defect_scope_guard_cross_repo_cwd.py
@@ -48,6 +48,16 @@ scope here) — pinned live as
+Issue #2709: three more cd-adjacent shapes disclosed in prose by #2669/
...
@@ -92,6 +102,16 @@ def _run_guard(command: str, cwd: str, env_extra: dict | None = None):
+def _assert_denied_for_documented_reason(test_case, result):
...
@@ -150,6 +170,58 @@ class CrossRepoCwdDisagreementTest(unittest.TestCase):
```
Only three hunks change in this diff: the docstring paragraph, the new
helper definition, and the three new test methods. The seven test names
listed just above appear in none of those hunks — they predate PR #2750
and sit outside its own diff. Logged under Open findings below.

### Task C — four standing invariants

**1. No return of the "role" axis.** derived: `git grep -wIn "role" --
. ':!docs/'` on `pr-2750-review` (`/tmp/otr-pr2750`) → `1230` (via `| wc
-l`). Same command in a clean `origin/main` worktree (`/tmp/otr-main-
check`) → `1103`. derived: `git merge-base --is-ancestor pr-2750-review
origin/main` → non-zero (not an ancestor); `git merge-base origin/main
pr-2750-review` → `00aeaae4` — `origin/main` gained commits after that
merge-base (including `e1b35a53`, the role→skill rename) that are absent
from the PR branch, which is the source of the count delta, not PR #2750.
derived: `git diff 00aeaae4 pr-2750-review -- . ':!docs/' | grep -in
role` (PR #2750's own diff, excluding docs) → no output. derived: `git
diff 00aeaae4 pr-2750-review | grep -in role` (including docs) → 3
matching lines, all inside the PR's own added report doc: the record
schema's own `role:` frontmatter key and two prose lines quoting a prior
finding's heading — no production "role" logic touched. Invariant holds
for PR #2750's own diff.

**2. No new bug.** derived: `cd /tmp/otr-pr2750 && python3 -m pytest
test/ -q` → `16 failed, 405 passed, 6 xfailed in 3.03s`. Same command in
`/tmp/otr-main-check` → `15 failed, 403 passed, 6 xfailed in 3.23s`. Exact
set-difference of failing names, root cause, and resolution: see Open
findings item 2 below.

**3. No overhead increase.** derived: pre-PR (merge-base) version of the
test file, swapped in via `git show 00aeaae4:test/test_upstream_defect_scope_guard_cross_repo_cwd.py`, then `time python3 -m pytest
test/test_upstream_defect_scope_guard_cross_repo_cwd.py -q` →
```
7 passed, 2 xfailed in 0.91s
real    0m1.196s
```
Actual PR file restored (`git checkout --
test/test_upstream_defect_scope_guard_cross_repo_cwd.py`), same command →
```
10 passed, 2 xfailed in 0.90s
real    0m1.196s
```
`7 passed + 2 xfailed` = 9 tests before, `10 passed + 2 xfailed` = 12
tests after; 12 - 9 = 3, matching the 3 new tests PR #2750 adds. `real`
wall time is identical to the millisecond between both runs (`0m1.196s` =
`0m1.196s`) — no measurable overhead from the 3 added subprocess-based
tests under this xdist-parallel run. The "directive bytes 53162" baseline
named in the review brief is not something this worktree has a way to
check the meaning of, and is not guessed at here.

**4. Monitor/watch machinery unbroken and not quieter.** derived: `git
diff 00aeaae4 pr-2750-review --stat -- monitors/ gates/` (PR #2750's own
diff) → no output, both dirs untouched by PR #2750's own commit. For
context only, derived: `git diff origin/main pr-2750-review --stat --
monitors/ gates/` → `gates/` shows changes attributable to the same
unrelated role→skill-rename drift as invariant 1 (confirmed by the
merge-base-scoped diff just above showing zero gates/monitors changes
from PR #2750 itself); `monitors/` shows zero changed files even against
current `origin/main`. derived: `ls /tmp/otr-pr2750/monitors/ | grep -i
heartbeat` → no output — no `monitors/test_poll_heartbeat.py` file exists
in this repo, so the example name in the review brief does not
correspond to a real path here; re-checking the failing-set files from
invariant 2 (`pr_failed.txt`/`main_failed.txt`) for a `monitors/` prefix
→ no match in either file.

### Task D — stale branch check

derived: `git diff origin/main pr-2750-review --stat -- on-the-record/hooks/approval-gate.sh` →
```
on-the-record/hooks/approval-gate.sh | 16 ++++------------
1 file changed, 4 insertions(+), 12 deletions(-)
```
Not empty as the review brief's plain form expected — `origin/main` has
advanced past this PR's own merge-base (same drift as invariants 1, 2, 4
above). derived: `git diff 00aeaae4 pr-2750-review --stat --
on-the-record/hooks/approval-gate.sh` (PR #2750's own diff, merge-base to
head) → no output. PR #2750 itself makes zero changes to
`on-the-record/hooks/approval-gate.sh`; the merge-base-scoped diff, not
the raw `origin/main` diff, is what actually confirms this.

## Why

The PR's own docstring asserts a result ("Confirmed discriminating ...
against a mutant `operative_cwd` that also recognizes `pushd`, strips a
leading `(`, and follows the LAST chained `cd`: all three flip to rc=0
(allow) under that mutant") without shipping the mutant that produced it
— nothing in the PR diff lets a reader tell that claim apart from an
untested assertion. canonical: the Task A result table above, produced by
`python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -q -k "pushd_not_followed or subshell_cd_not_followed or chained_cd_uses_first_target"` run against four hook files built from
scratch this session (`/tmp/otr-mutants/*.sh`), corroborated by `python3
/tmp/otr-mutants/run_check.py <hook>.sh` — this pair of command runs, not
the PR's docstring text, is what Task A's diagonal conclusion above rests
on. The same logic applies to `_assert_denied_for_documented_reason`: its
docstring names the bug class it guards against but the PR does not ship
a crash mutant to demonstrate it working. canonical: the Task B(2)
crash-mutant `pytest ... -k "pushd_not_followed or subshell_cd_not_followed or chained_cd_uses_first_target"` run above (`3 failed in
0.90s` against `/tmp/otr-mutants/crash-mutant.sh`, built this session) is
what confirms the helper catches a real crash-remapped-to-2 case.

## What did not work

None.

## Upstream basis

- `on-the-record/hooks/upstream-defect-scope-guard.sh` — blob sha
  `200d08aee6a54b68832816eff4b7a29916509173` as of PR #2750 head
  `56fd6e85c785aee8fbb2ff5e76cf67c7de710fca`. derived: `git diff
  00aeaae4 pr-2750-review -- on-the-record/hooks/upstream-defect-scope-guard.sh` → no output — untouched by PR #2750's own diff.
- `test/test_upstream_defect_scope_guard_cross_repo_cwd.py` — blob sha
  `cf4ba0bdb2078ed39f8b01c28563aff7687e9ad0` as of PR #2750 head
  `56fd6e85c785aee8fbb2ff5e76cf67c7de710fca`.

## Open findings

1. Returncode-only blindness remains in seven pre-existing tests in the
   same file, outside PR #2750's own diff. canonical: the Task B(3) grep
   fence above lists the seven `def test_` names with a bare
   `assertEqual(r.returncode, 2` and no adjacent helper call. canonical:
   the Task B(2) crash-mutant fence above (`3 failed in 0.90s`) shows
   concretely, on the three tests that DO call the helper, that a bare
   returncode assertion alone would have let the crash-remapped-to-2 hook
   through undetected — the same construction applies to these seven.
   canonical: the Task B(3) `git diff 00aeaae4 pr-2750-review` fence above
   shows these seven test bodies fall outside PR #2750's own diff hunks —
   pre-existing from the #2669/#2703 work this PR builds on. Resolution
   path: a small forward-only follow-up applying
   `_assert_denied_for_documented_reason` (already shipped by PR #2750,
   reusable as written) to these seven call sites. Out of scope for PR
   #2750 itself.
2. A pre-existing test failure exists on both branches, unrelated to PR
   #2750's own diff. derived:
   ```
   $ comm -23 <(sort pr_failed.txt) <(sort main_failed.txt)
   FAILED test/test_auto_approval_shadow_wiring.py::SimulatedApprovalAppendsSampleTest::test_approval_gate_sh_is_byte_identical
   $ comm -13 <(sort pr_failed.txt) <(sort main_failed.txt)
   (no output)
   ```
   where `pr_failed.txt`/`main_failed.txt` are the sorted `grep
   "^FAILED"` lines of the Task C invariant-2 `pytest test/ -q` runs in
   `/tmp/otr-pr2750` and `/tmp/otr-main-check` respectively — one test
   name is present in the PR branch's failing set and absent from
   `origin/main`'s; nothing is present only on `origin/main`. derived:
   ```
   $ git worktree add /tmp/otr-basecheck 00aeaae4
   $ cd /tmp/otr-basecheck && python3 -m pytest test/test_auto_approval_shadow_wiring.py::SimulatedApprovalAppendsSampleTest::test_approval_gate_sh_is_byte_identical -q
   FAILED ...::test_approval_gate_sh_is_byte_identical
   1 failed in 0.86s
   ```
   already failing at PR #2750's own merge-base commit, before PR #2750's
   commit exists on top of it. canonical: the Task D fence above (`git
   diff 00aeaae4 pr-2750-review --stat -- on-the-record/hooks/approval-gate.sh` → no output) shows PR #2750's own diff never touches that hook
   file, so it cannot be the cause. Root cause: the branch (merge-base
   `00aeaae4`) predates the role→skill rename that later landed on
   `origin/main` (`e1b35a53`) — the same drift documented under Task C
   invariants 1, 2, and 4. No action needed on PR #2750 for this finding.

## Next steps

None. `loop_state` is `landed`. canonical: every check this review was
asked to run has an executed command and its output above — Task A's
`python3 -m pytest ... -k "pushd_not_followed or subshell_cd_not_followed or chained_cd_uses_first_target"` diagonal against 4 self-built hook
files (two independently-built harnesses agreeing), Task B's `grep` for
helper calls plus the crash-mutant `pytest` run (`3 failed in 0.90s`),
Task C's four `git diff`/`pytest`/`time` invariant checks (each scoped to
PR #2750's own merge-base diff to separate it from `origin/main`'s
unrelated post-merge-base drift), and Task D's `git diff --stat`
stale-branch confirmation. Both Open findings above are real but both
predate and sit outside PR #2750's own two-file diff (`on-the-record/hooks/upstream-defect-scope-guard.sh` untouched per the Upstream-basis
`git diff` above; `test/test_upstream_defect_scope_guard_cross_repo_cwd.py`'s new hunks limited to the docstring, the helper, and the three
new tests, per the Task B(3) `git diff` fence above) — neither blocks
this PR. PR #2750 is sound for merge as delivered; the returncode-only-
blindness cleanup named in Open findings item 1 is a candidate for its own
small follow-up issue/PR, not folded into PR #2750's scope.

skill-verdict: adversarial-review — applied: invoked; built four
independent mutant copies of `operative_cwd()` from scratch in
`/tmp/otr-mutants/` (never editing the real repo file) and ran the PR's
own three new tests against each with two independently-written harnesses,
rather than trusting the PR's own docstring claim about a mutant it never
ships.
