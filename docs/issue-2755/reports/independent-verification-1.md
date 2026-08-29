---
issue: 2755
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
loop_state: landed
type: verification
breaking: false
verdict: acceptable
upstream:
  - path: test/test_upstream_defect_scope_guard_cross_repo_cwd.py
    sha: 6a54fcc89de7faa7f055afd925dc1ecba70a06b1
---

# issue-2755 — independent-verification-1 record

## What was done

Independently re-executed every acceptance check in PR #2781
(`issue-2755/test-authoring-isolation-and-fixture-strategy+adversarial-review-40c15437`
→ `main`, head `6a54fcc89de7faa7f055afd925dc1ecba70a06b1`), against a fresh
checkout of the PR head, without reusing any output from the PR's own
record — each command below was run directly in this session.

**1. Diff review.**

acceptance: `git diff --stat origin/main origin/issue-2755/test-authoring-isolation-and-fixture-strategy+adversarial-review-40c15437 -- . ':!docs'` — result:
```
 test/test_upstream_defect_scope_guard_cross_repo_cwd.py | 7 +++++++
 1 file changed, 7 insertions(+)
```
canonical: `gh pr diff 2781` (full diff, read directly) — exactly 7
additive lines, one `_assert_denied_for_documented_reason(self, r)` call
added after each of the 7 `assertEqual(r.returncode, 2, r.stderr)` sites
named in issue #2755. No production code touched, no existing assertion
line removed or altered, no second helper introduced.

**2. Baseline — real hook, post-fix test file.**

acceptance: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v` — result:
```
======================== 10 passed, 2 xfailed in 0.97s =========================
```

**3. Acceptance check 1 — crash-hook proof (all 7 named tests must fail).**
Backed up `on-the-record/hooks/upstream-defect-scope-guard.sh`, replaced
it with a hook that exits 2 before reaching any policy:

acceptance: `printf '#!/usr/bin/env bash\nexit 2\n' > on-the-record/hooks/upstream-defect-scope-guard.sh && python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v` — result:
```
FAILED ...test_same_call_without_cd_still_denied
FAILED ...test_unrelated_upstream_repo_still_denied
FAILED ...test_cd_into_unrelated_repo_checkout_still_denied
FAILED ...test_cd_into_non_checkout_dir_still_denied
FAILED ...test_cd_into_nonexistent_dir_still_denied
FAILED ...test_legitimate_cross_repo_pr_now_allowed
FAILED ...test_chained_cd_uses_first_target_not_final_still_denied
FAILED ...test_harness_cwd_unresolvable_without_cd_still_fails_open
FAILED ...test_pushd_not_followed_still_denied
FAILED ...test_subshell_cd_not_followed_still_denied
XFAIL  ...test_spoofed_origin_remote_bypass_should_be_denied
XFAIL  ...test_harness_cwd_origin_removed_bypass_should_be_denied
======================== 10 failed, 2 xfailed in 0.87s =========================
```
canonical: the FAILED list above (this session's own pytest output) — of
the 10 FAILED, the 5 named-in-issue plain tests
(`test_same_call_without_cd_still_denied`,
`test_unrelated_upstream_repo_still_denied`,
`test_cd_into_unrelated_repo_checkout_still_denied`,
`test_cd_into_non_checkout_dir_still_denied`,
`test_cd_into_nonexistent_dir_still_denied`) all flip PASSED→FAILED as
required; the other 5 FAILED are controls outside the 7 named tests and
were expected to fail under a dead hook regardless of this change. The 2
`@expectedFailure` tests stay genuine XFAIL, not XPASS, confirmed by
isolating them:

acceptance: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v \| grep -E "spoofed_origin\|harness_cwd_origin_removed"` — result:
```
XFAIL test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_spoofed_origin_remote_bypass_should_be_denied
XFAIL test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_harness_cwd_origin_removed_bypass_should_be_denied
```

**4. Acceptance check 2 — restore, all 7 pass/xfail again.**

acceptance: `cp <backup> on-the-record/hooks/upstream-defect-scope-guard.sh && git diff --stat -- on-the-record/hooks/upstream-defect-scope-guard.sh && python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v` — result:
```
(git diff --stat: empty output — hook restored byte-identical)
======================== 10 passed, 2 xfailed in 0.91s =========================
```

**5. The XPASS regression this issue exists to prevent — reproduced
directly against the pre-fix test body.** Swapped the test file for the
pre-PR version (base `main`, bare `assertEqual(returncode, 2, ...)` only,
no `_assert_denied_for_documented_reason` calls), kept the crash-hook in
place, and ran only the xfail test:

acceptance: `python3 -m pytest "test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_spoofed_origin_remote_bypass_should_be_denied" -v` — result:
```
FAILED ...test_spoofed_origin_remote_bypass_should_be_denied
Unexpected success
============================== 1 failed in 0.88s ===============================
```
canonical: this session's own pytest output above — "Unexpected success"
is pytest/unittest's literal report for an `@expectedFailure` test whose
body ran to completion without raising. This is the XPASS landmine the
issue describes, reproduced live: pre-fix, a hook that crashes on every
input makes this test XPASS, which reads as "the bypass got fixed."
Restored both the hook and the test file to the PR-head state afterward:

acceptance: `git checkout -- test/test_upstream_defect_scope_guard_cross_repo_cwd.py on-the-record/hooks/upstream-defect-scope-guard.sh && git status --short` — result:
```
(no output — working tree clean, matches branch base)
```

**6. Sweep — re-executed independently, not copy-pasted from the PR's own
record.**

acceptance: `grep -rn "returncode, 2" test/ | wc -l` — result:
```
34
```
acceptance: `grep -c "returncode, 2" test/test_upstream_defect_scope_guard_cross_repo_cwd.py test/test_branch_role_field.py test/test_approval_gate_carriers.py test/test_deliverable_guard_worktree_submodule.py test/test_deliverable_guard_priorities_shard.py` — result:
```
test/test_upstream_defect_scope_guard_cross_repo_cwd.py:10
test/test_branch_role_field.py:3
test/test_approval_gate_carriers.py:5
test/test_deliverable_guard_worktree_submodule.py:2
test/test_deliverable_guard_priorities_shard.py:14
```
derived: 10+3+5+2+14 = 34, matching the sweep total from the prior
command — all 34 hits accounted for across exactly these 5 files.

canonical: `grep -n "assertIn\|assertRegex\|assertNotIn\|assertTrue(" test/test_deliverable_guard_priorities_shard.py`
— result: zero matches (no output). Confirmed: zero content checks
anywhere in the file, all 14 return-code-only hits genuinely unchecked,
matching the PR record's "flagged, not fixed" claim for this file.

canonical: read `test/test_deliverable_guard_worktree_submodule.py:95-158`
directly. It has 2 `returncode, 2` hits (from the `grep -c` count above),
not the 1 the PR record's prose names (it lists only line 101). Line 101
(`test_missing_git_binary_refuses_with_explanation`'s first definition,
using an `f"{label}: {r.stderr}"` message argument) has no content
assertion anywhere in its method — genuinely unchecked, matches the
record's "flagged, not fixed" conclusion. Line 157, a second, differently
scoped test also named `test_missing_git_binary_refuses_with_explanation`,
is immediately followed by `self.assertIn("could not determine",
r.stderr)` — a real content check, correctly excluded from the unfixed
count even though the PR record's prose named only one of the two hits in
this file. derived: 2 (hits) - 1 (real content check at line 157) = 1
genuinely unchecked hit in this file, matching the PR record's conclusion
even though its prose under-names the raw hit count.

canonical: read `test/test_branch_role_field.py:365-381` directly. The PR
record says all 3 hits in this file "each have a real `assertIn(...)` on
`r.stderr`"; the hit at line 380 is actually followed by
`self.assertTrue("closing" in r.stderr.lower())`, not `assertIn`. It is
still a genuine content check on `r.stderr`, so the sweep's conclusion (0
unchecked in this file) holds — the record's wording names the wrong
assertion method for this one site.

canonical: read `test/test_ps_live_reliability.py:90-134` directly. Its 2
`assertEqual(rc, 2)` hits (not part of the 34-count above — different
literal pattern, `roster_ps()` is an in-process call, not a hook
subprocess) are each preceded by `assertIn`/`assertNotIn` checks on the
captured `out` string. The PR record's "out of scope for this bug class"
framing holds.

acceptance: `git status --short` — result:
```
?? docs/issue-2755/
```
(only this record is untracked; no residual code changes from the
verification steps above.)

derived: sweep conclusion — 34 total return-code-only assertion sites
found (grep total above); unchecked count by file: 10 (own file, 0
unchecked after the fix) + 3 (branch_role_field, 0 unchecked) + 5
(approval_gate_carriers, 0 unchecked) + 1 (deliverable_guard_worktree_submodule,
unchecked) + 14 (deliverable_guard_priorities_shard, all unchecked) = 15
unchecked total, all 15 against `deliverable-guard.sh`, none against
`upstream-defect-scope-guard.sh`, after this PR. This matches PR #2781's
own stated "15 additional instances" conclusion despite the two prose
imprecisions found above (see "Open findings").

**7. Trailer check.** canonical: `gh pr view 2781 --json body -q .body` —
the PR body ends `Advances #2755` (not `Closes`/`Fixes`/`Resolves`),
consistent with its own stated scope: it fixes the 7 named call sites but
explicitly leaves the 15 `deliverable-guard.sh` instances above unfixed
and recommends a follow-up issue. Correct trailer choice for a partial
delivery.

## Why

The issue's acceptance criteria are binary and mechanical (fail under a
crash hook, pass under the real hook, sweep for siblings). canonical:
this session's own command transcript in "What was done" steps 1-7 above
— every command re-run there reproduced the PR record's claimed pass/fail
counts and outcomes on the first attempt, including the narrower detail
that the 2 `@expectedFailure` tests must stay XFAIL rather than flip to
XPASS, which is the actual defect this issue is about. Re-running the
checks directly, rather than reading the PR author's own transcript of
having run them, is what makes this an independent verification rather
than a restatement.

## What did not work

canonical: this session's own command transcript in "What was done" above
— every independently re-run command reproduced the PR record's claimed
output on the first attempt; nothing needed a retry or a different
approach. Two imprecisions were found in the PR record's sweep prose (see
"Open findings" below) but neither changed this session's own sweep
conclusion, so neither counts as something that "did not work" in this
verification's own execution.

## Upstream basis

- PR #2781 (`issue-2755/test-authoring-isolation-and-fixture-strategy+adversarial-review-40c15437` → `main`, head `6a54fcc89de7faa7f055afd925dc1ecba70a06b1`), which delivers the fix for issue #2755's 7 named call sites.
- canonical: `gh pr diff 2781` — the PR's own delivery record lives at `docs/issue-2755/reports/test-authoring-isolation-and-fixture-strategy+adversarial-review-40c15437.md` on that branch; untracked in this worktree because that branch is not yet merged to `main`. Read via `gh pr diff 2781`, cross-checked against but not relied upon for this verification's own command executions (all re-run independently in "What was done" above).
- Issue #2755 itself (`gh issue view 2755`), including its correction comment (5 → 7 count, 2 of which are `@expectedFailure`).

## Open findings

- `test/test_deliverable_guard_worktree_submodule.py` and
  `test/test_deliverable_guard_priorities_shard.py` still have 15
  (derived in "What was done" step 6: 1 + 14 = 15) tests asserting a
  `deliverable-guard.sh` denial by return code alone (same crash→2 trap
  shape) — confirmed present and correctly named by PR #2781 as out of
  issue #2755's scope. Resolution path: PR #2781's own recommendation to
  file a follow-up issue scoped to `deliverable-guard.sh`'s tests.
  derived: `gh issue list --search "deliverable-guard.sh" --state all` —
  no existing issue found; not yet filed as of this verification.
- The PR record's sweep classification prose undercounts
  `test/test_deliverable_guard_worktree_submodule.py` by one hit (2
  present in the file per the `grep -c` count in step 6, only line 101
  named) and names one `assertTrue("closing" in r.stderr.lower())` check
  as `assertIn` (`test/test_branch_role_field.py:380`, checked directly
  in step 6). derived: neither changes the sweep's 15-unchecked bottom
  line computed independently in step 6 above. No action needed; noted
  for anyone re-deriving the per-file breakdown from the prose rather
  than re-running the grep themselves.

## Next steps

None — `loop_state: landed`.

## Skill verdicts

- skill-verdict: work-in-english — applied: invoked; wrote this record, all commands, and commit messages in English throughout, per the skill's standing trigger for Korean-language task framing in this repo.
- other mounted skills: not triggered.
