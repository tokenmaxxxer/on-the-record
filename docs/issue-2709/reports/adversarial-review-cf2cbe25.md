---
issue: 2709
role: adversarial-review-cf2cbe25
author: adversarial-review-cf2cbe25
skills: adversarial-review (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent re-derivation of PR #2750's own claims, different author than the subject record
loop_state: landed
upstream:
  - path: test/test_upstream_defect_scope_guard_cross_repo_cwd.py
    sha: 56fd6e85c785aee8fbb2ff5e76cf67c7de710fca
  - path: on-the-record/hooks/upstream-defect-scope-guard.sh
    sha: e1f390ab6c01018ce805b00114232adfe86ab749
---

# issue-2709 — adversarial-review-cf2cbe25 record

## What was done

Independent re-derivation of PR #2750 — canonical: `gh pr view 2750
--json title,body,files,commits` (oid `56fd6e85c785aee8fbb2ff5e76cf67c7de710fca`,
body describes an independent adversarial-review subagent finding the
`returncode == 2` assertions crash-vs-deny blind and fixing it in the
same commit). The PR adds three tests —
`test_pushd_not_followed_still_denied`,
`test_subshell_cd_not_followed_still_denied`,
`test_chained_cd_uses_first_target_not_final_still_denied` — to
`test/test_upstream_defect_scope_guard_cross_repo_cwd.py` and changes no
production code — derived: `git diff --stat 00aeaae4 pr-2750` → 2 files
changed, 244 insertions(+), 0 deletions(-) (the test file and the
subject's own record file; `00aeaae4` is the PR's parent commit per
`gh pr view 2750 --json commits`).

**Per-shape mutant verification** (adversarial-review + test-depth-audit
Step 4, mutation confirmation). Built three single-feature mutants of the
shipped `operative_cwd()` (`on-the-record/hooks/upstream-defect-scope-guard.sh:184-193`),
one per shape, and ran each PR test's exact command against both the
shipped hook and its own mutant via a private driver (ad hoc, not
committed, per the no-persistent-test-files default):

| shape | single-feature mutant | shipped hook | mutant |
|---|---|---|---|
| pushd | regex also matches `pushd` (`^\s*cd\s+` → `^\s*(?:cd\|pushd)\s+`) | deny, policy msg present | allow, no policy msg |
| subshell `(cd ...)` | regex allows an optional leading `(` (`^\s*cd\s+` → `^\s*\(?\s*cd\s+`) | deny, policy msg present | allow, no policy msg |
| chained `cd A && cd B` | takes the LAST `cd` match via `re.findall` instead of the first via `re.match` | deny, policy msg present | allow, no policy msg |

derived: `python3 /tmp/mutant_driver.py` — output:
```
--- pushd ---
shipped: rc=2 stderr_has_policy_msg=True
mutant : rc=0 stderr_has_policy_msg=False
--- subshell ---
shipped: rc=2 stderr_has_policy_msg=True
mutant : rc=0 stderr_has_policy_msg=False
--- chained ---
shipped: rc=2 stderr_has_policy_msg=True
mutant : rc=0 stderr_has_policy_msg=False
```
Each mutant is a minimal, single-clause diff off the shipped
`operative_cwd` — confirmed via `diff /tmp/hook.sh /tmp/mutants/<shape>.sh`
showing exactly the one line/clause changed per shape, no other
behavioral change. All three tests flip from deny to allow under their
own single-feature mutant and stay deny against the shipped hook — none
of the three survives its own mutant, so none is a test that reads as
coverage but pins nothing. Test-depth-audit classification: all three
are Genuine Assertion (real subprocess against the real shipped script,
real git checkouts — not Mock-Dominated, not Execution-Only).

**returncode-only-blindness fix, completeness check.** The hook's own
trap remaps any crash to exit 2 as well as a real policy deny —
canonical: `sed -n '96,102p' on-the-record/hooks/upstream-defect-scope-guard.sh`:
```
trap 'rc=$?; if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi' EXIT
```
The fix (`_assert_denied_for_documented_reason`,
`test/test_upstream_defect_scope_guard_cross_repo_cwd.py:105-112`)
asserts `"issue #1131 req#4" in stderr` and `"Traceback" not in stderr`.
derived: `grep -n "_assert_denied_for_documented_reason\|returncode" test/test_upstream_defect_scope_guard_cross_repo_cwd.py`
(PR branch) shows the helper defined once and called at exactly 3 sites
(the 3 new tests: `test_pushd_not_followed_still_denied`,
`test_subshell_cd_not_followed_still_denied`,
`test_chained_cd_uses_first_target_not_final_still_denied`), against 12
total `assertEqual(r.returncode, ...)` sites in the file. The fix is
complete across all three tests this PR introduces — no new test in
this PR has the returncode-only gap.

The same gap exists, unfixed, in five **pre-existing** tests in the same
file that this PR does not touch — derived: same grep, cross-referenced
against `sed -n '134,171p;232,248p' test/test_upstream_defect_scope_guard_cross_repo_cwd.py`
(PR branch): `test_same_call_without_cd_still_denied`,
`test_unrelated_upstream_repo_still_denied`,
`test_cd_into_unrelated_repo_checkout_still_denied`,
`test_cd_into_non_checkout_dir_still_denied`,
`test_cd_into_nonexistent_dir_still_denied` — each asserts only
`self.assertEqual(r.returncode, 2, r.stderr)` with no stderr-message
check. (Two more, `test_spoofed_origin_remote_bypass_should_be_denied`
and `test_harness_cwd_origin_removed_bypass_should_be_denied`, share the
pattern but are `@unittest.expectedFailure`, so the assertion is not
currently load-bearing either way.) See Open findings.

**Four standing invariants:**

1. No return of the retired role axis. derived: `git diff 00aeaae4
   pr-2750 -- test/test_upstream_defect_scope_guard_cross_repo_cwd.py |
   grep -in "role\|CLAUDE_ROLE\|MUSTER_ROLE"` → no output. The PR's diff
   carries no role-axis references in any form.

2. No new bug, sets of names not counts. Ran `python3 -m pytest test/ -q`
   in a worktree of `origin/main` and a worktree of the PR branch
   (`00aeaae4` + the PR's one commit). derived:
   `diff <(sort main_failed_names.txt) <(sort pr_failed_names.txt)` →
   ```
   0a1
   > FAILED test/test_auto_approval_shadow_wiring.py::SimulatedApprovalAppendsSampleTest::test_approval_gate_sh_is_byte_identical
   ```
   Exactly one name-level delta. Investigated that name specifically —
   derived: `grep -n "def test_approval_gate_sh_is_byte_identical"
   test/test_auto_approval_shadow_wiring.py` on the `origin/main`
   worktree → no output (the test does not exist there at all, not
   "passes"); on the PR-branch worktree → defined at line 153. derived:
   `git log -1 --format=%H -S"test_approval_gate_sh_is_byte_identical"
   -- test/test_auto_approval_shadow_wiring.py` → `e1b35a53...` (PR
   #2746, "retire the role persisted key — rename to skill"), the exact
   commit named in the review brief as landing after this branch was
   cut. This is the stale-branch symptom the brief predicted, not a
   regression from PR #2750: derived: `git diff --stat 00aeaae4 pr-2750
   -- '*approval-gate*'` → empty output, confirming PR #2750 does not
   touch `approval-gate.sh` or its test. Raw counts (not the basis for
   this invariant, stated only for context) — derived: `main_pytest.log`
   tail → 403 passed, 15 failed, 6 xfailed; `pr_pytest.log` tail → 405
   passed, 16 failed, 6 xfailed. This numerically differs from the PR's
   own stated test-plan output ("15 failed ... same 15 failing test
   names as a clean origin/main checkout") only because `origin/main`
   moved (landed #2746) in the days between the PR's authoring
   (2026-08-29) and this review (2026-08-30) — not a discrepancy in the
   PR's content, which the set-diff and the `-S` search above pin to the
   named later commit.

3. No overhead increase. `git diff --stat 00aeaae4 pr-2750` (cited
   above) touches only the test file and the subject's own record — no
   `spawn.py`, `directive_assembly.py`, or any directive-contributing
   file, so the 53162-byte directive baseline is untouched by
   construction. Runtime cost of the three new tests — derived: `python3
   -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v
   --durations=0` (PR branch) → 10 passed, 2 xfailed in 0.97s total;
   `--durations=0` reported the three new tests individually at
   0.02–0.06s call + ~0.02–0.03s setup each (each spins up two real
   local git checkouts via `tempfile.TemporaryDirectory` and one real
   `bash` subprocess call to the hook).

4. Monitor/watch machinery unbroken, not quieter. derived: `git ls-files
   'test/*monitor*' 'test/*watch*'` → only
   `test/test_watchdog_heartbeat_noise.py`. derived: `python3 -m pytest
   test/test_watchdog_heartbeat_noise.py -v` on the PR branch → 6 passed
   in 0.84s. derived: same command re-run against the `origin/main`
   worktree (step 2's full-suite run) collected the same 6 names, none
   of which appear in either branch's failing-name list from step 2's
   set-diff — unbroken and identical test count on both branches, not
   quieter.

## Why

The task brief specified the exact failure mode to hunt: a test that
would give the same verdict against the code both with and without the
gap it claims to guard. The mutant table above is the load-bearing
evidence ruling that out for each of the three shapes, independent of
the PR's own docstrings making the same discriminating-power claim
(canonical: `sed -n '173,224p'
test/test_upstream_defect_scope_guard_cross_repo_cwd.py`, PR branch —
the claim under review, not confirmation of it).

## What did not work

None.

## Upstream basis

- `test/test_upstream_defect_scope_guard_cross_repo_cwd.py` at
  `56fd6e85c785aee8fbb2ff5e76cf67c7de710fca` (PR #2750's commit) — the
  three new tests and the `_assert_denied_for_documented_reason` helper
  under review.
- The subject builder's own record, referenced in PR #2750's body as
  `docs/issue-2709/reports/test-authoring-isolation-and-fixture-strategy+adversarial-review-5556333f.md`
  (untracked on this branch — `issue-2709/adversarial-review-cf2cbe25`
  was cut from an earlier commit and does not carry it) at commit
  `56fd6e85c785aee8fbb2ff5e76cf67c7de710fca`; read via `git show
  56fd6e85:docs/issue-2709/reports/test-authoring-isolation-and-fixture-strategy+adversarial-review-5556333f.md`.
- `on-the-record/hooks/upstream-defect-scope-guard.sh` at
  `e1f390ab6c01018ce805b00114232adfe86ab749` — untouched by this PR;
  the hook under test and the source of the three mutants built for
  verification.

## Open findings

1. **Pre-existing returncode-only blindness, five tests, this file, not
   introduced by PR #2750.** derived: same grep/sed citation as in "What
   was done" above — `test_same_call_without_cd_still_denied`,
   `test_unrelated_upstream_repo_still_denied`,
   `test_cd_into_unrelated_repo_checkout_still_denied`,
   `test_cd_into_non_checkout_dir_still_denied`, and
   `test_cd_into_nonexistent_dir_still_denied` each assert only
   `returncode == 2` with no stderr-message check, the same gap the
   PR's own adversarial pass found and fixed in its three new tests.
   Not a defect in PR #2750 itself (it didn't touch these tests and the
   gap predates it), but the class of gap is now demonstrably fixable
   cheaply (`_assert_denied_for_documented_reason` already exists in
   the same file). Resolution path: a follow-up PR applies
   `_assert_denied_for_documented_reason` to the five pre-existing
   sites; out of scope for #2709 itself since #2709's acceptance
   criteria are scoped to the pushd/subshell/chained-cd tests only.
2. **Stale-branch test failure, not a defect.**
   `test_approval_gate_sh_is_byte_identical` fails on the PR branch
   because it was removed/replaced by PR #2746 on `origin/main` after
   this PR's base commit — derived: `git diff --stat 00aeaae4 pr-2750
   -- '*approval-gate*'` → empty output (PR #2750 does not touch
   `approval-gate.sh`); derived: `git log -1 --format=%H
   -S"test_approval_gate_sh_is_byte_identical" --
   test/test_auto_approval_shadow_wiring.py` → `e1b35a53...` (#2746).
   No action needed; resolves on rebase/merge.

## Next steps

None. Frontmatter `loop_state: landed` — derived: this record's own
"What was done" section above, which is the executed evidence backing
that state (all four standing invariants and both scoped acceptance
checks re-derived with commands and output in this same commit).

skill-verdict: adversarial-review — applied: invoked; built independent single-feature mutants per shape and ran the PR's exact test commands against shipped hook vs. mutant (mutation-confirmation step), rather than trusting the PR's own docstring claims of discrimination
skill-verdict: test-depth-audit — applied: invoked; classified all three new tests as Genuine Assertion via the mutation-confirmation step (Step 4) and checked the returncode-only-blindness fix's completeness across the file as a behavioral-coverage-gap check
skill-verdict: work-in-english — applied: invoked; record and all repo-bound artifacts written in English, final user-facing summary in Korean
