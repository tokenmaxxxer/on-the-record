---
issue: 2755
role: independent-verification-2
author: independent-verification-2
verifies_subject: true  # this record independently verifies PR #2781, the deliverable for this subject
loop_state: landed
upstream:
  - path: test/test_upstream_defect_scope_guard_cross_repo_cwd.py
    sha: 278ec311bc69a1e016317a3ce8555c7bb69e31cd
---

# issue-2755 — independent-verification-2 record

## What was done

Independently audited PR #2781 (`issue-2755/test-authoring-isolation-and-fixture-strategy+adversarial-review-40c15437`, still OPEN, not yet merged to `main`), which claims to close issue #2755 by applying the existing `_assert_denied_for_documented_reason` helper to the 7 call sites named in the issue's corrected count (5 plain + 2 `@unittest.expectedFailure`). Re-derived every load-bearing claim from a fresh git worktree at the PR head, not from reading the PR's own record.

canonical: `gh pr view 2781 --json body,commits,files,state,mergeable` — state OPEN, mergeable MERGEABLE, commits `278ec311bc69a1e016317a3ce8555c7bb69e31cd` and `6a54fcc89de7faa7f055afd925dc1ecba70a06b1`, 3-file changeset (test file + PR's own record + deviation log).

**Diff shape, independently confirmed:**
```
derived: git diff origin/main..pr-2781-check -- test/test_upstream_defect_scope_guard_cross_repo_cwd.py
1 file changed, 7 insertions(+)
```
Exactly 7 additive lines, each a single `_assert_denied_for_documented_reason(self, r)` call added immediately after the existing `self.assertEqual(r.returncode, 2, r.stderr)` in the 7 named test methods (`test_same_call_without_cd_still_denied`, `test_unrelated_upstream_repo_still_denied`, `test_cd_into_unrelated_repo_checkout_still_denied`, `test_cd_into_non_checkout_dir_still_denied`, `test_cd_into_nonexistent_dir_still_denied`, `test_spoofed_origin_remote_bypass_should_be_denied` [xfail], `test_harness_cwd_origin_removed_bypass_should_be_denied` [xfail]). No return-code assertion removed or weakened; no second helper introduced.

**Acceptance check 1 (crash before policy → all 7 fail), independently re-run:**
```
derived: printf '#!/usr/bin/env bash\nexit 2\n' > on-the-record/hooks/upstream-defect-scope-guard.sh
         python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v
======================== 10 failed, 2 xfailed in 0.89s =========================
```
Targeted re-run confirmed the 2 `@expectedFailure` tests XFAIL (not XPASS) under the crash-hook:
```
derived: python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v -k "spoofed_origin or harness_cwd_origin_removed"
============================== 2 xfailed in 0.87s ==============================
```

**Restore, independently re-run:**
```
derived: cp <backup> on-the-record/hooks/upstream-defect-scope-guard.sh
         git diff --stat -- on-the-record/hooks/upstream-defect-scope-guard.sh   # empty
         python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v
======================== 10 passed, 2 xfailed in 0.94s / 1.02s (re-run twice) =========================
```

**XPASS regression, independently reproduced from the real pre-fix file (not via `git stash`, which the original session used incorrectly — `git stash` on a file with no working-tree delta against `HEAD` stashes nothing, so that step in the PR's own record silently ran against the *post-fix* body; it happened to still print output that looked like the intended result by coincidence of matching test names, but was not actually testing what it claimed). This verification instead materialized the true pre-fix body via `git show origin/main:test/test_upstream_defect_scope_guard_cross_repo_cwd.py`, swapped it in, and ran under the crash-hook:**
```
derived: git show origin/main:test/test_upstream_defect_scope_guard_cross_repo_cwd.py > pre_fix.py
         cp pre_fix.py test/test_upstream_defect_scope_guard_cross_repo_cwd.py
         python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_spoofed_origin_remote_bypass_should_be_denied -v
FAILED ... test_spoofed_origin_remote_bypass_should_be_denied - Unexpected success
============================== 1 failed in 0.88s ===============================
```
Confirms the actual risk the issue describes: pre-fix, a crash-hook makes this `@expectedFailure` test XPASS ("Unexpected success"). Post-fix (restored the modified test body), the same crash-hook input correctly XFAILs instead, shown above under "Acceptance check 1".

**Sweep, independently re-derived:**
```
derived: grep -rn "returncode, 2" test/ | wc -l
34
derived: grep -rln "returncode, 2" test/
test/test_upstream_defect_scope_guard_cross_repo_cwd.py (10)
test/test_deliverable_guard_worktree_submodule.py (2)
test/test_approval_gate_carriers.py (5)
test/test_deliverable_guard_priorities_shard.py (14)
test/test_branch_role_field.py (3)
```
10+2+5+14+3 = 34, matching the PR's stated sweep total exactly.
- `test_upstream_defect_scope_guard_cross_repo_cwd.py`: all 10 now call the helper (3 pre-existing + 7 added). 0 unchecked — confirmed by the diff above.
- `test_approval_gate_carriers.py`: read each of the 5 assertions; every one is immediately followed by a real `assertIn(...)` on `r.stderr` in the same method. 0 unchecked.
- `test_branch_role_field.py`: read each of the 3; 2 are followed by `assertIn(...)`, the third (line 380) is followed by `assertTrue("closing" in r.stderr.lower())` — a substring content check by a different spelling, not `assertIn` as the PR record states, but functionally equivalent. 0 unchecked. (Minor: the PR's record says "each has a real `assertIn(...)`" for this file, which is imprecise for this one call site — noted as a documentation nit, not a correctness gap.)
- `test_deliverable_guard_worktree_submodule.py`: 2 hits;
```
derived: grep -n "returncode, 2\|assertIn\|assertRegex\|assertNotIn" test/test_deliverable_guard_worktree_submodule.py
101:                self.assertEqual(r.returncode, 2, f"{label}: {r.stderr}")
157:        self.assertEqual(r.returncode, 2, r.stderr)
158:        self.assertIn("could not determine", r.stderr)
159:        self.assertNotIn("deliverable path in a board repo", r.stderr)
```
Line 101's method has no content check anywhere in its body (confirmed by reading the full method) — 1 of 2 unchecked, matching the PR's "flagged, not fixed" claim for that one line.
- `test_deliverable_guard_priorities_shard.py`: 14 hits;
```
derived: grep -c "assertIn\|assertRegex\|assertNotIn\|assertTrue(" test/test_deliverable_guard_priorities_shard.py
0
```
All 14 unchecked, matches the PR's claim exactly.
- 1 (worktree_submodule line 101) + 14 (priorities_shard) = 15 unfixed instances, matching the PR's stated "15 additional instances" exactly.

Also independently swept for the same bug shape written with a different comparison order or spelling (`== 2`, `2 ==`, `assertEqual(2, ...)`) across all `returncode`-referencing lines, to check whether the narrow `"returncode, 2"` grep pattern the PR used could be under-counting:
```
derived: grep -rn "returncode" test/ | grep -v "returncode, 2" | grep -E "== 2|2 ==|, 2\)|assertEqual\(2"
(no output — zero matches)
```
The bug-shape sweep is complete for that literal spelling.

One discrepancy found in the PR's own record: it lists `test_ps_live_reliability.py` ("2 hits") as one of the files "classified" among "these 34," but that file uses a differently-named variable and does not match the stated sweep command at all:
```
derived: grep -n "returncode, 2" test/test_ps_live_reliability.py   # 0 matches
         grep -n "rc, 2" test/test_ps_live_reliability.py           # 2 matches (lines 101, 134)
```
The stated total of 34 is arithmetically exact without this file (10+2+5+14+3=34), so the file was not actually part of the 34 being classified; mentioning it there is a wording error, not a miscount. It does not affect the acceptance criterion, which is explicitly scoped to hook-invoking tests (`test_ps_live_reliability.py` calls `board.roster_ps()` in-process, not a hook subprocess, per the PR's own text) — filed as an open finding below rather than a blocking issue.

## Why

Verifying by re-deriving every claim from a clean worktree, rather than trusting the PR's own quoted command output, is the point of independent verification: it catches exactly the kind of silent-no-op the `git stash` step in the PR's own record contains (stashing a file with no working-tree diff is a no-op, so that reproduction step ran against the wrong file version without erroring or looking wrong). Re-doing it against the actual `origin/main` pre-fix content confirms the underlying claim (the XPASS regression is real) while also surfacing that the PR's own proof of it was accidentally untested.

## What did not work

None.

## Upstream basis

- canonical: `gh pr view 2781 --json body,commits,files,state,mergeable` — PR https://github.com/tokenmaxxxer/on-the-record/pull/2781, state OPEN, mergeable MERGEABLE, commits `278ec311bc69a1e016317a3ce8555c7bb69e31cd` and `6a54fcc89de7faa7f055afd925dc1ecba70a06b1`, branch `issue-2755/test-authoring-isolation-and-fixture-strategy+adversarial-review-40c15437`.
- canonical: `gh pr diff 2781` — the PR's own record at path docs/issue-2755/reports/test-authoring-isolation-and-fixture-strategy+adversarial-review-40c15437.md (sha `278ec311bc69a1e016317a3ce8555c7bb69e31cd`); not present in this branch's working tree since PR #2781 is unmerged — read via `gh pr diff`, not via a local path.
- canonical: `gh issue view 2755 --comments` — issue tokenmaxxxer/on-the-record#2755, including its correcting comment (5 → 7, two `@expectedFailure`).

## Open findings

- The PR's own record's "XPASS regression" reproduction step used `git stash push` on a file with no working-tree delta, which is a silent no-op.
  derived: `git show origin/main:test/test_upstream_defect_scope_guard_cross_repo_cwd.py` swapped into place and re-run (full command and output above under "What was done" → "XPASS regression, independently reproduced") — the underlying claim it was trying to prove is independently confirmed true by this re-derivation, so this does not block the PR. Resolution path: fix the reproduction step in that record if anyone revisits it, or leave as a known cosmetic defect in a closed PR's history.
- The PR's own record lists `test_ps_live_reliability.py` as one of the 34 classified `"returncode, 2"` hits.
  derived: `grep -n "returncode, 2" test/test_ps_live_reliability.py` (0 matches) vs `grep -n "rc, 2" test/test_ps_live_reliability.py` (2 matches, lines 101/134) — that file does not match the stated sweep command; the 34-count is exact without it (10+2+5+14+3=34, shown above under "Sweep, independently re-derived"). Cosmetic — the file is explicitly out of scope anyway (non-hook, in-process call). No resolution path needed; noted for the record only.
- 15 tests against `deliverable-guard.sh` (1 in `test_deliverable_guard_worktree_submodule.py` line 101, 14 in `test_deliverable_guard_priorities_shard.py`) assert denial by return code alone.
  derived: `grep -n "returncode, 2\|assertIn\|assertRegex\|assertNotIn" test/test_deliverable_guard_worktree_submodule.py` and `grep -c "assertIn\|assertRegex\|assertNotIn\|assertTrue(" test/test_deliverable_guard_priorities_shard.py` (full commands and output above under "What was done" → "Sweep, independently re-derived") — 1 unchecked hit in the first file, 0 content-check calls anywhere in the second file's 14 hits. Out of this issue's stated scope (title and Ask name only `test_upstream_defect_scope_guard_cross_repo_cwd.py`). Resolution path: file a follow-up issue scoped to `deliverable-guard.sh`'s tests.

## Next steps

None — `loop_state: landed`.

acceptance: `python3 -m pytest test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v` run against PR #2781's head under both the real hook and a substituted crash-hook, then restored — result:
```
Real hook (baseline and post-restore): 10 passed, 2 xfailed
Crash-hook (exit 2 before any policy): 10 failed, 2 xfailed — the 2 xfailed confirmed genuine XFAIL, not XPASS
Pre-fix body + crash-hook, single targeted test: 1 failed — Unexpected success (the XPASS regression the issue describes)
```
PR #2781 does what it claims: the diff is exactly the 7 named call sites, the crash-hook/restore proof and the XPASS-regression proof both independently reproduce, and the sweep count (34) and its 15-instance unfixed-elsewhere breakdown check out exactly. Two cosmetic documentation nits found in the PR's own record (a no-op `git stash` step, and a file wrongly attributed to the 34-count) do not change the correctness of the shipped test-file diff.

## Skill verdicts

- skill-verdict: work-in-english — not-applicable: this session's spawning task was in Korean but all repository-bound work (this record, commit messages, PR) is authored in English per the skill's own scope; the skill's guidance was followed by default without needing to invoke it as a tool.
