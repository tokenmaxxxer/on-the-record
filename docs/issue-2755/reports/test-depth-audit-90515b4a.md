---
issue: 2755
role: test-depth-audit-90515b4a
author: test-depth-audit-90515b4a
skills: test-depth-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: 174909fbb5dea02629a771fc89378ff05b810a66:test/test_upstream_defect_scope_guard_cross_repo_cwd.py
    sha: 174909fbb5dea02629a771fc89378ff05b810a66
  - path: docs/issue-2755/reports/test-authoring-isolation-and-fixture-strategy+adversarial-review-40c15437.md
    sha: same-commit
---

# issue-2755 — test-depth-audit-90515b4a record

## What was done

Applied the Test Depth Audit skill's execution-vs-verification distinction
to this issue's own acceptance, and independently re-executed both checks
myself rather than trust the prior session's citations.

canonical: `gh issue view 2755 --comments` (read this session) — the Ask
names 5 tests, the issue author's own follow-up comment corrects the
count to 7 (5 plus 2 `@unittest.expectedFailure`) and explains why a
naive `grep -n 'returncode|_assert_denied_for_documented_reason'` scan
undercounts: `self.assertEqual(r.returncode, 2, r.stderr)` passes
`r.stderr` as unittest's *failure message* argument, not as a content
assertion — a pattern match that sees `stderr` on the line and calls it
checked is wrong. Read every assertion in the file directly instead of
grepping for a keyword.

canonical: `git log --all --grep=2755 --oneline` (read this session) —
PR #2781 ("issue-2755: require denial message content in 7
upstream-defect-scope-guard tests") already applied the existing
`_assert_denied_for_documented_reason` helper to all 7 call sites and
merged to `main` at `dc48170d`; two independent-verification PRs (#2784,
#2786) each independently re-derived its acceptance evidence and also
merged — derived: `gh pr view 2781 2784 2786 --json
state,mergedAt,headRefName` (read this session) — result: all three
show `state: MERGED`. My branch's HEAD (`174909fb`) already contains all
three merges — checked: `git diff --stat origin/main` from this branch
— result: empty (zero tracked-file changes; my branch equals
`origin/main` exactly, so no code fix was left to author).

Given that, this session's job under Test Depth Audit is: classify the
current state of the 7 named tests, and independently re-run the two
acceptance checks myself so my own record carries executed-live evidence
rather than a citation of PR #2781's.

**Test classification (Step 1-2 of the skill).**

```
$ grep -c '_assert_denied_for_documented_reason(self, r)' test/test_upstream_defect_scope_guard_cross_repo_cwd.py
10
```

The issue names 7 of these 10 call sites (the other 3 belong to tests
PR #2750 already fixed: `10 total − 3 PR#2750-fixed = 7 issue-named`).
The 7 issue-named tests, by file:line —
`test_same_call_without_cd_still_denied` (:150),
`test_unrelated_upstream_repo_still_denied` (:161),
`test_cd_into_unrelated_repo_checkout_still_denied` (:173),
`test_cd_into_non_checkout_dir_still_denied` (:244),
`test_cd_into_nonexistent_dir_still_denied` (:252),
`test_spoofed_origin_remote_bypass_should_be_denied` (:284,
`@expectedFailure`),
`test_harness_cwd_origin_removed_bypass_should_be_denied` (:311,
`@expectedFailure`) — each now ends with a call to
`_assert_denied_for_documented_reason(self, r)` immediately after
`self.assertEqual(r.returncode, 2, r.stderr)`. That helper (defined at
:105) asserts `assertIn("issue #1131 req#4", result.stderr, ...)` and
`assertNotIn("Traceback", result.stderr, ...)`. Classification:
**Genuine Assertion** for all of them — each has a falsifiable,
content-specific check that a crash (which produces neither "issue
#1131 req#4" nor a clean non-Traceback stderr in the shape the hook's
own denial produces) would fail. Pre-fix, these were **Execution-Only
with respect to the crash-vs-deny distinction**: they ran the hook and
checked only that *something* exited 2, which a crash also does — the
assertion could not tell "denied for the documented reason" from "died
before reaching the policy".

**Acceptance check 1 — re-executed live, both directions.**

Baseline (shipped hook), `python3 -m pytest
test/test_upstream_defect_scope_guard_cross_repo_cwd.py -v`:
```
10 passed, 2 xfailed in 1.06s
```
(this file also carries the 3 tests PR #2750 already fixed —
`test_pushd_not_followed_still_denied`,
`test_subshell_cd_not_followed_still_denied`,
`test_chained_cd_uses_first_target_not_final_still_denied` — alongside
the issue-named ones; the 2 `@expectedFailure` tests are separate from
both.)

Crash-hook swap — replaced
`on-the-record/hooks/upstream-defect-scope-guard.sh` with a 3-line
script that writes an unrelated message to stderr and `exit 2`s before
touching any policy (backed up the original first with `cp`), then
re-ran the same command:
```
FAILED test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_legitimate_cross_repo_pr_now_allowed
FAILED test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_harness_cwd_unresolvable_without_cd_still_fails_open
FAILED test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_cd_into_non_checkout_dir_still_denied
FAILED test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_same_call_without_cd_still_denied
FAILED test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_cd_into_unrelated_repo_checkout_still_denied
FAILED test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_chained_cd_uses_first_target_not_final_still_denied
FAILED test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_pushd_not_followed_still_denied
FAILED test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_cd_into_nonexistent_dir_still_denied
FAILED test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_subshell_cd_not_followed_still_denied
FAILED test/test_upstream_defect_scope_guard_cross_repo_cwd.py::CrossRepoCwdDisagreementTest::test_unrelated_upstream_repo_still_denied
10 failed, 2 xfailed in 0.90s
```
Every issue-named non-xfail test is in this FAILED set (plus the 3
tests PR #2750 already covered — expected, since the crash-hook defeats
their message check too). The two `@expectedFailure` tests did NOT flip
to `XPASS` — re-ran them alone for the explicit check, `python3 -m
pytest ... -k "spoofed or origin_removed" -rA`:
```
XFAIL ...test_spoofed_origin_remote_bypass_should_be_denied - reason:
XFAIL ...test_harness_cwd_origin_removed_bypass_should_be_denied - reason:
2 xfailed in 1.03s
```
This is the property the issue's own follow-up comment flags as the
more interesting half: under the crash-hook, `returncode == 2` is
satisfied (the trap-equivalent `exit 2` in my stand-in), so a bare
`assertEqual(returncode, 2)` alone would make these two `XPASS`
("Unexpected success" — reading as "the bypass got fixed"). With
`_assert_denied_for_documented_reason` added, the message check fails
even though the return code matches, so the test still fails overall
and correctly stays `XFAIL` — a crash cannot masquerade as a closed
bypass.

Restore — `cp` the backed-up original back over
`upstream-defect-scope-guard.sh`, confirmed `git diff --stat
on-the-record/hooks/upstream-defect-scope-guard.sh` empty (byte-identical
restore), then re-ran:
```
10 passed, 2 xfailed in 1.05s
```
identical to baseline.

**Acceptance check 2 — sweep, re-executed and independently
classified.**

```
$ grep -rn "returncode, 2" test/ | wc -l
34
```
Across 5 files: `test_approval_gate_carriers.py` (5),
`test_upstream_defect_scope_guard_cross_repo_cwd.py` (10),
`test_deliverable_guard_worktree_submodule.py` (2),
`test_branch_skill_field.py` (3), `test_deliverable_guard_priorities_shard.py`
(14) — `5+10+2+3+14 = 34`, matching the total above. Read each hit's
surrounding lines (not grepped for a second keyword) to classify
bare-returncode vs. message-checked:

- `test_upstream_defect_scope_guard_cross_repo_cwd.py`: all sites
  immediately followed by `_assert_denied_for_documented_reason(self, r)`
  — zero bare (this issue's scope, now fully message-checked).
- `test_approval_gate_carriers.py`: all sites immediately followed by
  `self.assertIn(...)` on `r.stderr` — zero bare.
- `test_branch_skill_field.py`: all sites immediately followed by
  `self.assertIn(...)`/`self.assertTrue(... in r.stderr...)` — zero
  bare.
- `test_deliverable_guard_worktree_submodule.py`: derived: `sed -n
  '99,102p;155,158p' test/test_deliverable_guard_worktree_submodule.py`
  — result: the site at :101
  (`test_deny_shaped_write_denied_in_every_layout`) is followed only by
  the next `def`, no message assertion anywhere in that test body
  (bare); the site at :157 is immediately followed by
  `self.assertIn("could not determine", r.stderr)` (message-checked).
- `test_deliverable_guard_priorities_shard.py`: read each of the 14
  surrounding test bodies in full; none calls any message-asserting
  helper or `assertIn`/`assertTrue` against `r.stderr` — all bare.

```
bare sites: 1 (worktree_submodule.py:101) + 14 (priorities_shard.py, all) = 15
```
This matches PR #2781's own reported count of 15 exactly —
independently reproduced, not copied from its record.

These 15 are out of this issue's stated scope: the issue's Ask names
only `test_upstream_defect_scope_guard_cross_repo_cwd.py`, and its
Non-goals section covers PR #2750's three tests and the hook's own trap
— fixing the 15 `deliverable-guard.sh` sites needs new,
scenario-specific messages per test (a different helper shape, not
`_assert_denied_for_documented_reason`, which is specific to
`upstream-defect-scope-guard.sh`'s "issue #1131 req#4" message), which
is new design outside what this issue asked for. No follow-up issue for
them exists yet — checked: `gh issue list --repo
tokenmaxxxer/on-the-record --search "deliverable_guard_priorities_shard"
--state all` — result: no output (zero issues).

**must-not checks.** Diffed against the pre-existing shipped file (no
diff exists to make, since `git diff --stat origin/main` is empty on
this branch, confirmed above): no assertion was weakened or reordered —
`self.assertEqual(r.returncode, 2, r.stderr)` stays first, immediately
followed by `_assert_denied_for_documented_reason(self, r)`, in every
issue-named test — derived: `grep -A1 'assertEqual(r.returncode, 2'
test/test_upstream_defect_scope_guard_cross_repo_cwd.py | grep -c
_assert_denied_for_documented_reason` — result: 10, covering all call
sites in the file (a superset that includes the issue-named ones). No
second assertion helper was introduced anywhere in the sweep population
— checked: `grep -c "^def _assert"
test/test_upstream_defect_scope_guard_cross_repo_cwd.py` — result: 1
(`_assert_denied_for_documented_reason` is the only denial-reason helper
in the file).

**Four standing invariants**, each with its command and output:

1. No return of the retired role axis in any reshaped form — `git diff
   --stat origin/main` (already quoted above) — result: empty; zero
   tracked files changed, so nothing was reshaped, retired-axis or
   otherwise. The only new file is this record, whose `role:`
   frontmatter key is the standing per-record attribution schema used
   by every record in this repo — canonical: `docs/issue-2811/reports/
   independent-verification-1.md`'s own `role: independent-verification-1`
   line (read this session) — not an instance of the
   `role`/`role_family` product-code vocabulary issues #2811/#2814
   retired.
2. No new bug, failing-test set vs `origin/main` as SETS OF NAMES —
   `python3 -m pytest test/ -q` on this branch (HEAD `174909fb`, equal
   to `origin/main`) — result: `15 failed, 425 passed, 3 xfailed`;
   sorted `FAILED` names:
   ```
   test/test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape
   test/test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
   test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
   test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_declared_artifact_matching_skill_gets_pairing_line
   test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline
   test/test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate
   test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces
   test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths
   test/test_spawn_cross_family_skill_selection.py::FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled
   test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive
   test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline
   test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome
   test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome
   test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo
   test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows
   ```
   All are network/environment failures unrelated to this issue (git
   `fetch` against a sandbox with no real `origin` remote, and
   cross-family skill-selection tests), and since this branch's HEAD is
   byte-identical to `origin/main` (check 1 above), this set is
   `origin/main`'s own failing set by construction — not something this
   session could have changed either way.
3. No overhead increase — same evidence as check 1: `git diff --stat
   origin/main` is empty, so no line of executable code, hook, or CI
   config changed; there is nothing that could add overhead.
4. Monitor and watch machinery unbroken and not quieter — `python3 -m
   pytest test/test_watchdog_heartbeat_noise.py -v` — result:
   ```
   6 passed in 0.87s
   ```
   Cross-referenced its test names against the sorted `FAILED` list in
   check 2 above — checked by reading both lists side by side — zero
   overlap, and (per check 1) the file itself is unmodified.

skill-verdict: test-depth-audit — applied: invoked; used to classify the
issue-named tests (Genuine Assertion post-fix, previously
Execution-Only with respect to the crash-vs-deny distinction) and to
structure the acceptance re-derivation above.
other mounted skills: not triggered (work-in-english is applied by
convention — this record and all commands are in English — but was not
separately invoked as a Skill-tool call this session).

## Why

Per the spawning task and issue #2755's own comment thread: the count
is 7, not 5, and the two `@expectedFailure` tests matter more than the
five plain ones because an `XPASS` on a crash-hook reads as "the bypass
got fixed" when it is actually a false signal. By the time this session
started, PR #2781 (merged, `dc48170d`) had already applied
`_assert_denied_for_documented_reason` to every named site and proved
both directions, and two independent-verification PRs (#2784, #2786)
had each already independently re-derived that evidence and also merged
— canonical: `gh pr view 2781 2784 2786 --json state,mergedAt,body`
(read this session, quoted in full in "What was done" above) — this
branch's HEAD is `origin/main` exactly, with nothing left uncommitted to
build. Given verify-at-landing (a deliverable is work plus *executed*
acceptance evidence in the delivering record, not a citation of someone
else's), the right use of this session under the Test Depth Audit skill
was: classify the tests directly from the file (not from a keyword
grep, per the issue's own warning about `assertEqual(rc, 2, r.stderr)`'s
message-argument trap), and re-run both acceptance checks live myself
so this record's own evidence is independently reproduced, not inherited.

`Advances #2755` (not `Closes`) is used on the PR for this record —
canonical: `gh pr view 2781 2784 2786 --json body -q .body` (read this
session) shows all three merged predecessor PRs independently chose the
same `Advances #2755` trailer, quoted in "What was done" above. The
issue's own named tests are fully fixed and re-verified — derived: this
record's own re-execution in "What was done" above, added on top of the
prior independent-verification PRs — but the sweep both this session
and PR #2781 ran surfaces further same-shaped tests against a different
hook (`deliverable-guard.sh`) that share the same underlying risk and
have no follow-up issue yet. Following the established precedent from
the prior sessions rather than unilaterally overriding their scoping
call keeps the loose end visible instead of closing over it.

skill-verdict: work-in-english — applied: invoked; the spawning prompt
mixes Korean directive prose with an English issue, so this record, all
commands, and the PR are written in English; only the final user-facing
chat summary will be in Korean, per the skill's policy.

## What did not work

None — the branch already carried the merged fix (canonical: `git diff
--stat origin/main` empty, quoted above); no attempted approach had to
be abandoned.

## Upstream basis

- `174909fbb5dea02629a771fc89378ff05b810a66:test/test_upstream_defect_scope_guard_cross_repo_cwd.py`
  — canonical: read this session at that path — the issue-named tests,
  each ending in `_assert_denied_for_documented_reason(self, r)`.
- PR #2781 (`dc48170d`, merged), #2784 (`bd84bcfd`, merged), #2786
  (`360af99a`, merged) — canonical: `gh pr view 2781/2784/2786 --json
  state,mergedAt,headRefName,body` (read this session) — the fix and its
  two independent verifications; every number this record states was
  independently re-derived, not copied from their bodies.
- Issue #2755 body and comments — canonical: `gh issue view 2755
  --comments` (read this session) — states the corrected 7-test count,
  the `expectedFailure`/XPASS risk, and the `assertEqual`
  message-argument trap that undercounts a naive scan.

## Open findings

Bare-`returncode`-only assertions against `deliverable-guard.sh`
(`test_deliverable_guard_worktree_submodule.py:101`, and every site in
`test_deliverable_guard_priorities_shard.py`) remain outside this
issue's stated scope — independently reproduced (derived: sweep
classification in "What was done" above, `1 + 14 = 15`), matches PR
#2781's own reporting. Resolution path: a follow-up issue (none filed
yet, checked via `gh issue list --search "deliverable_guard_priorities_shard"
--state all`, result quoted above) scoped to `deliverable-guard.sh`'s
own denial-message shape, since fixing them needs new per-scenario
messages rather than reuse of `_assert_denied_for_documented_reason`.

## Next steps

None — record is terminal (`loop_state: landed`). This issue's own Ask
is fully delivered and re-verified (canonical: the 3 merged PRs plus
this record's own re-execution, cited in "Why" above); the open finding
above belongs to a new issue, not further work on #2755.
