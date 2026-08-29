---
issue: 2755
role: test-authoring-isolation-and-fixture-strategy+adversarial-review-40c15437
author: test-authoring-isolation-and-fixture-strategy+adversarial-review-40c15437
skills: test-authoring-isolation-and-fixture-strategy (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false
loop_state: landed
upstream:
  - path: test/test_upstream_defect_scope_guard_cross_repo_cwd.py
    sha: same-commit
---

# issue-2755 — test-authoring-isolation-and-fixture-strategy+adversarial-review-40c15437 record

## What was done

Applied the existing helper `_assert_denied_for_documented_reason` (already
defined at `test/test_upstream_defect_scope_guard_cross_repo_cwd.py:105`,
used by 3 call sites since PR #2750) to the 7 call sites named in issue
#2755, on top of their existing `assertEqual(r.returncode, 2, r.stderr)`
checks — the return-code check was not touched, only extended:

```
canonical: `git diff -- test/test_upstream_defect_scope_guard_cross_repo_cwd.py`
diff --git a/test/test_upstream_defect_scope_guard_cross_repo_cwd.py b/test/test_upstream_defect_scope_guard_cross_repo_cwd.py
index cf4ba0bd..a5ae0fad 100644
--- a/test/test_upstream_defect_scope_guard_cross_repo_cwd.py
+++ b/test/test_upstream_defect_scope_guard_cross_repo_cwd.py
@@ -148,6 +148,7 @@
                "--title x --body y")
         r = _run_guard(cmd, cwd=str(self.repo_a))
         self.assertEqual(r.returncode, 2, r.stderr)
+        _assert_denied_for_documented_reason(self, r)
[... same one-line addition at 6 more call sites: test_unrelated_upstream_repo_still_denied,
test_cd_into_unrelated_repo_checkout_still_denied, test_cd_into_non_checkout_dir_still_denied,
test_cd_into_nonexistent_dir_still_denied, test_spoofed_origin_remote_bypass_should_be_denied (xfail),
test_harness_cwd_origin_removed_bypass_should_be_denied (xfail) ...]
 1 file changed, 7 insertions(+)
```

No second helper was introduced; no assertion was weakened.

**Acceptance check 1 — crash-hook proof (all 7 fail).** Backed up the real
hook, replaced it with one that exits 2 before any policy logic runs, ran
the file, then restored the original and re-ran it.

```
derived: cp on-the-record/hooks/upstream-defect-scope-guard.sh /tmp/upstream-defect-scope-guard.sh.bak
         printf '#!/usr/bin/env bash\nexit 2\n' > on-the-record/hooks/upstream-defect-scope-guard.sh
         python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v
[gw7] FAILED test_legitimate_cross_repo_pr_now_allowed        (out of the 7, unaffected control)
[gw3] FAILED test_chained_cd_uses_first_target_not_final_still_denied (out of the 7, unaffected control)
[gw8] FAILED test_same_call_without_cd_still_denied            <- one of the 7
[gw4] XFAIL  test_harness_cwd_origin_removed_bypass_should_be_denied  <- one of the 7
[gw1] FAILED test_cd_into_nonexistent_dir_still_denied         <- one of the 7
[gw0] FAILED test_cd_into_non_checkout_dir_still_denied        <- one of the 7
[gw9] XFAIL  test_spoofed_origin_remote_bypass_should_be_denied       <- one of the 7
[gw5] FAILED test_harness_cwd_unresolvable_without_cd_still_fails_open (out of the 7, unaffected control)
[gw2] FAILED test_cd_into_unrelated_repo_checkout_still_denied <- one of the 7
[gw6] FAILED test_pushd_not_followed_still_denied              (out of the 7, pre-existing helper user)
[gw1] FAILED test_unrelated_upstream_repo_still_denied         <- one of the 7
======================== 10 failed, 2 xfailed in 0.88s =========================
```

All 7 of the named tests discriminate: the 5 plain ones flip PASSED→FAILED,
and the 2 `@expectedFailure` ones stay XFAIL (not XPASS — see the XPASS
regression proof below) under a hook that crashes on every input.

**Acceptance check 2 — restore, all 7 pass again.**

```
derived: cp /tmp/upstream-defect-scope-guard.sh.bak on-the-record/hooks/upstream-defect-scope-guard.sh
         git diff --stat on-the-record/hooks/upstream-defect-scope-guard.sh   # empty — confirmed restored
         python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v
======================== 10 passed, 2 xfailed in 0.90s =========================
```

All 12 tests in the file pass/xfail correctly (the 7 named tests included).

**The XPASS regression this issue exists to prevent — reproduced directly.**
Ran the *pre-fix* test body (bare `assertEqual(returncode, 2, ...)` only,
via `git stash` of the test-file change) against the crash-hook:

```
derived: git stash push -- test/test_upstream_defect_scope_guard_cross_repo_cwd.py
         python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_spoofed_origin_remote_bypass_should_be_denied -v
=================================== FAILURES ===================================
_ CrossRepoCwdDisagreementTest.test_spoofed_origin_remote_bypass_should_be_denied _
Unexpected success
FAILED ... test_spoofed_origin_remote_bypass_should_be_denied
============================== 1 failed in 0.89s ===============================
         git stash pop
```

Confirmed: pre-fix, a hook that crashes on every input makes this
`@expectedFailure` test XPASS ("Unexpected success" — the exact
misleading-as-"bypass fixed" signal the issue describes). Post-fix, the
same crash-hook input produces a genuine XFAIL (shown above under
"Acceptance check 1" — `XFAIL ... test_spoofed_origin_remote_bypass_should_be_denied`,
`XFAIL ... test_harness_cwd_origin_removed_bypass_should_be_denied`) —
the assertion now fails for a real reason (missing policy message)
instead of trivially matching `returncode == 2`.

**Sweep — other tests asserting a denial by return code alone.**

```
derived: grep -rn "returncode, 2" test/ | wc -l
34
```

Of these 34, classified by reading each assertion (not grepping for the
word "stderr", per the issue's own warning that `r.stderr` as the
assertEqual failure-message argument is not a content check):

- `test/test_upstream_defect_scope_guard_cross_repo_cwd.py` — 10 hits, all
  now call `_assert_denied_for_documented_reason` (3 pre-existing from PR
  #2750, 7 added by this change). **0 unchecked.**
- `test/test_branch_role_field.py` — 3 hits (lines 260, 289, 380), each has
  a real `assertIn(...)` on `r.stderr` in the same method (verified by
  reading each method body). **0 unchecked.**
- `test/test_approval_gate_carriers.py` — 5 hits (lines 152, 180, 211, 222,
  234), each has a real `assertIn(...)` on `r.stderr` in the same method.
  **0 unchecked.**
- `test/test_ps_live_reliability.py` — 2 hits, not a hook subprocess at all
  (`board.roster_ps()` is an in-process Python call whose `return 2` is an
  explicit, non-crash-remapped signal), and both already have `assertIn`
  content checks regardless. **Out of scope for this bug class.**
- `test/test_deliverable_guard_worktree_submodule.py:101` —
  `test_deny_shaped_write_denied_in_every_layout` invokes
  `deliverable-guard.sh`, which has the identical crash→2 trap shape
  (`on-the-record/hooks/deliverable-guard.sh:42`). No content check
  anywhere in the method. **Flagged, not fixed** (see below).
- `test/test_deliverable_guard_priorities_shard.py` — 14 hits (lines 132,
  139, 149, 161, 165, 173, 177, 187, 196, 239, 249, 265, 273, 284), same
  trap-shaped hook, **zero** `assertIn`/`assertRegex`/`assertNotIn` calls
  anywhere in the whole file —
  `derived: grep -n "assertIn\|assertRegex\|assertNotIn\|assertTrue(" test/test_deliverable_guard_priorities_shard.py` → no matches.
  **Flagged, not fixed.**

**Sweep result: not zero.** 15 additional instances of the same bug shape
exist, all against `deliverable-guard.sh` (a different hook, different
policy messages per test scenario — src-rooted bypass, tmp-segment
exemption removal, planted-`.git` bypass, etc.). Fixing these needs a new,
scenario-specific helper for `deliverable-guard.sh`'s messages, which is
new design work outside "apply the existing helper to existing call
sites" and outside issue #2755's stated scope (title, Ask, and Non-goals
all name only `test_upstream_defect_scope_guard_cross_repo_cwd.py`). Named
here per instruction rather than fixed; recommend filing a follow-up issue
scoped to `deliverable-guard.sh`'s tests specifically.

## Why

The hook's own `trap` (`upstream-defect-scope-guard.sh:99`,
`if [ "$rc" != 0 ] && [ "$rc" != 2 ]; then exit 2; fi`) remaps any crash to
exit 2, identical to a real denial. A bare `assertEqual(returncode, 2, ...)`
cannot tell the two apart. The fix already existed in the file
(`_assert_denied_for_documented_reason`, added by PR #2750 for 3 sibling
tests) — this change is applying it to the 7 remaining call sites, not new
design. The 2 `@expectedFailure` tests carry the sharper risk: they encode
a *known, currently-open* bypass, so if a crash satisfies the bare
`returncode == 2` check, `unittest.expectedFailure` reports it as an
*unexpected success* (XPASS) — reading as "the bypass got fixed" when in
fact the hook just crashed. Verified above that this XPASS was real
pre-fix and is closed post-fix.

## What did not work

None.

## Four standing invariants

1. **No return of any retired role axis.** N/a — this change touches only
   test-assertion depth in one file; nothing role-axis-shaped was touched
   or reintroduced.
2. **No new bug (failing-test-name sets vs. origin/main).**
   ```
   derived: git diff --stat origin/main -- . ':!docs'
    test/test_upstream_defect_scope_guard_cross_repo_cwd.py | 7 +++++++
    1 file changed, 7 insertions(+)
   ```
   Only this one test file changed (7 additive lines, no production code
   touched), so no other test in the repo can be affected. Within the
   changed file itself: captured the sorted set of `PASSED`/`XFAIL` test
   names before (`git stash`) and after the change and diffed them —
   `derived: diff /tmp/before_names.txt /tmp/after_names.txt` → empty diff,
   **identical sets**, no new failures introduced.
3. **No overhead increase.**
   ```
   derived: time python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py
   before: 10 passed, 2 xfailed in 1.33s (real 1.750s)
   after:  10 passed, 2 xfailed in 0.95s (real 1.385s)
   ```
   No increase (after is faster; the difference is xdist worker-startup
   noise, not a real signal at this scale — the 7 added lines are two
   in-process string-membership checks each, negligible against ~1s of
   subprocess/worker overhead for 12 hook invocations).
4. **Monitor/watch machinery unbroken and not quieter.** Not applicable to
   this file: these tests invoke the hook directly via `subprocess.run`
   against a synthetic PreToolUse JSON payload on stdin, not through the
   harness's own PreToolUse firing/monitoring path —
   `derived: grep -n "monitor\|watch\|orchestrate-hook-fires" test/test_upstream_defect_scope_guard_cross_repo_cwd.py`
   → no matches. No monitor/watch machinery is exercised by this file to
   break or quiet.

## Adversarial review (independent evaluator, artifact-only)

Spawned a fresh general-purpose agent with only the diff and the
post-change file content (no issue number, no acceptance criteria, no
task framing). Bottom line: **"Acceptable... does not break anything...
demonstrably closes a real gap."** Findings raised and disposition:

- *"10 call sites now share a duplicated 2-line pattern; fold the
  return-code check into the helper."* Not applied — the issue's own
  must-not is "the return-code check stays, ... do not introduce a second
  assertion helper," and the 2-line (not 1-line) shape is the existing
  convention set by PR #2750's 3 original call sites, not something this
  change introduced.
- *"2 of the 7 added lines are dead code under the current (real) hook,
  since the returncode assertion fails first."* True for the real hook,
  but the evaluator reproduced this without knowing the crash-hook
  scenario is the actual target: under a crash-hook, `returncode == 2`
  is satisfied and the added line is exactly what is reached and what
  fails correctly instead of XPASSing —
  derived: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v`
  against the swapped crash-hook, quoted in full under "Acceptance check
  1" above (`XFAIL ... test_spoofed_origin_remote_bypass_should_be_denied`,
  `XFAIL ... test_harness_cwd_origin_removed_bypass_should_be_denied`),
  contrasted with the same command against the pre-fix test body under
  "The XPASS regression" above (`Unexpected success`).
- *"No comment/docstring update explaining the change, breaking the
  file's dense-annotation convention."* Not applied — no code behavior
  change requires it, and adding commentary beyond the task is out of
  scope here.
- *Pre-existing docstring typo in the helper (stray "/"), unrelated to
  this diff.* Left as-is — pre-existing, outside issue #2755's scope;
  worth a follow-up note if anyone touches that docstring again.

## Upstream basis

Issue tokenmaxxxer/on-the-record#2755, including its correction comment
(count corrected from 5 to 7, two of which are `@expectedFailure`).

## Open findings

- 15 more tests (`test_deliverable_guard_worktree_submodule.py:101` and 14
  in `test_deliverable_guard_priorities_shard.py`) assert a
  `deliverable-guard.sh` denial by return code alone, with the identical
  crash→2 trap shape. Named above with file:line; not fixed here (needs a
  new, scenario-specific helper — different hook, different messages per
  test — which is new design work outside this issue's scope). Resolution
  path: file a follow-up issue scoped to `deliverable-guard.sh`'s tests.
- Pre-existing docstring typo at
  `test/test_upstream_defect_scope_guard_cross_repo_cwd.py:109` ("issue
  #2637's /issue #2709's") — cosmetic, unrelated to this change, no
  resolution path opened.

## Next steps

None — `loop_state: landed`.

## Skill verdicts

- skill-verdict: test-authoring-isolation-and-fixture-strategy — not-applicable: this change is about assertion content depth (return-code vs. message-content checks), not fixture construction/scope, run-order isolation, database cleanup, or test-double selection, none of which this diff touches.
- skill-verdict: adversarial-review — applied: invoked; spawned a fresh general-purpose agent (subagent_type general-purpose) with only the diff/post-change file content and no issue context, per Step 2-3 of the skill; findings and disposition recorded above under "Adversarial review".
