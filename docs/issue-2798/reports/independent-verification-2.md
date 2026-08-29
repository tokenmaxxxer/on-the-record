---
issue: 2798
role: independent-verification-2
author: independent-verification-2
skills: work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2799's own deliverable
loop_state: complete
upstream:
  - path: PR #2799 (branch issue-2798/adversarial-review-99b10ef0), commits 757a9624 + cacd3800
    sha: cacd3800a4c86c52ba9f45d2bd8a58d3b4db149f
---

# issue-2798 — independent-verification-2 record

## What was done

Independently re-ran all three acceptance checks from `gh issue view 2798`
against PR #2799 (branch `issue-2798/adversarial-review-99b10ef0`,
head `cacd3800a4c86c52ba9f45d2bd8a58d3b4db149f`), plus the must-not clause,
in a separate `git worktree` checked out directly from that branch — not
by reading PR #2799's own record and trusting its numbers.

canonical: `gh pr view 2799` (state: OPEN, url:
https://github.com/tokenmaxxxer/on-the-record/pull/2799)

acceptance: `grep -inE '\brole\b' test/test_bootstrap_signal_guard.py; echo "exit=$?"` (PR worktree) — result:
```
exit=1
```

acceptance: `python3 -m pytest test/test_bootstrap_signal_guard.py --collect-only -q` on `b4d05522` (pre-fix, this session's own checkout) vs. the PR worktree — result: both collect the identical 11-name set:
```
BootstrapSignalGuardCaughtSignalTest::test_disarmed_after_session_log_survives_sigterm_untouched
BootstrapSignalGuardCaughtSignalTest::test_sigint_mid_bootstrap_also_reports_caller_departed
BootstrapSignalGuardCaughtSignalTest::test_sigkill_mid_bootstrap_records_nothing_and_leaves_workspace
BootstrapSignalGuardCaughtSignalTest::test_sigterm_mid_bootstrap_reports_caller_departed_and_cleans_up
BootstrapSignalGuardReviewGapsTest::test_adhoc_leftover_at_target_path_is_wiped_not_preserved
BootstrapSignalGuardReviewGapsTest::test_signal_after_session_log_before_disarm_does_not_delete_workspace
BootstrapSignalGuardReviewGapsTest::test_signal_during_adhoc_clone_also_removes_partial_workspace
BootstrapSignalGuardReviewGapsTest::test_signal_during_clone_removes_partial_workspace
BootstrapSignalGuardReviewGapsTest::test_signal_during_reuse_fetch_does_not_delete_prior_work
BootstrapSignalGuardReviewGapsTest::test_signal_during_self_reuse_never_targets_callers_own_checkout
SpawnAttemptSweepReportsCallerDepartedDistinctlyTest::test_declined_and_genuinely_dead_produce_different_lines
```
Also ran the full 11 live (not just collection): `python3 -m pytest test/test_bootstrap_signal_guard.py -v` on the PR worktree — result:
```
11 passed in 30.95s
```

acceptance: same-repo whole-tree count, `grep -rIc --exclude-dir=.git --exclude-dir=docs --exclude-dir=runs -inE '\brole\b' . | awk -F: '{s+=$2} END{print s}'` — on `b4d05522` (pre-fix, this session's own checkout): result
```
1120
```
on the PR worktree (post-fix): result
```
1108
```
derived: `git diff b4d05522 -- test/test_bootstrap_signal_guard.py | grep -icE '^[-+].*\brole\b'` — result: `12` (1120 − 1108 = 12, the delta is fully accounted for by this one file's twelve changed lines).

acceptance: `python3 -m pytest test/ -q` on the PR worktree — result:
```
15 failed, 425 passed, 3 xfailed in 31.76s
```
and the identical command on `b4d05522` (this session's own pre-fix checkout) — result:
```
15 failed, 425 passed, 3 xfailed in 31.84s
```
canonical: this session's own two pytest runs above, compared as sets of
test IDs (not counts) — byte-identical 15-name failing set both sides
(`test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape`,
`test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim`,
`test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment`,
six names in `test_spawn_cross_family_skill_selection.py`, two in
`test_spawn_artifact_skill_pairing.py`, four in
`test_spawn_skill_judge_haiku_timeout_overlap.py`) — confirms these 15 are
pre-existing on `origin/main` and unrelated to this change, not something
PR #2799 introduced.

Also independently checked the must-not clause (no same-meaning
substitute for "role"): `git diff b4d05522 -- test/test_bootstrap_signal_guard.py | grep -E '^\+' | grep -oE '"2742:[a-z]+:'` — result:
```
"2742:sigtermfault:
"2742:sigintfault:
"2742:sigkillfault:
"2742:livefault:
"2742:clonefault:
"2742:disarmracefault:
"2742:reusefault:
"2742:selfreuse:
```
all fault/purpose-named, none a synonym of "role" (job/position/persona/
character/part). derived: `grep -inE '\bjob\b' test/test_bootstrap_signal_guard.py` on the PR worktree — result: one hit, line 141, an unrelated pre-existing comment ("this session's own job, not this one's"), not a fixture literal.

## Why

The mandate for this role is to audit PR #2799 independently, not to relay
its own record's numbers as verified. Re-ran each acceptance check from a
fresh `git worktree` checked out directly from the PR's remote branch,
rather than trusting the file state already present in this session's own
checkout, and additionally cross-checked the full-suite failing set by
name (not count) against a fresh run on `b4d05522` (pre-fix) in this
session's own checkout, since a count match alone does not rule out a
same-size different-set regression.

## What did not work

None.

canonical: `gh issue view 2798` (Acceptance section, third bullet, quoted
verbatim): "The whole-repo count returns to its pre-merge value. — check:
the same summed `grep -rIc` the drive has been using, outside `docs/` and
`runs/` — empty state: 1263, matching the value before PR #2794".
unverifiable: the issue's absolute figures — pre-merge and post-merge —
were measured "across both repos" per the issue's Ask section; this
session, like PR #2799's own delivering session, has access to only one
repo checkout and no record of the operator's exact historical command,
so it cannot reproduce either absolute figure verbatim. acceptance:
independently re-derived the same-repo delta instead,
`grep -rIc --exclude-dir=.git --exclude-dir=docs --exclude-dir=runs -inE '\brole\b' . | awk -F: '{s+=$2} END{print s}'` on `b4d05522` vs. the PR worktree — result:
```
1120 (b4d05522) -> 1108 (PR worktree)
```
and `git diff b4d05522 -- test/test_bootstrap_signal_guard.py | grep -icE '^[-+].*\brole\b'` — result: `12`, confirming 1120 - 12 = 1108: this file's twelve removed occurrences fully account for the delta this session could measure.

## Upstream basis

PR #2799 (`issue-2798/adversarial-review-99b10ef0`, commits `757a9624` and
`cacd3800a4c86c52ba9f45d2bd8a58d3b4db149f`), fetched into a separate `git
worktree` from `origin/issue-2798/adversarial-review-99b10ef0` and tested
there directly. derived: `git show cacd3800a4c86c52ba9f45d2bd8a58d3b4db149f:docs/issue-2798/reports/adversarial-review-99b10ef0.md | head -1` — result: the frontmatter `---` line, confirming PR #2799's own record exists on that commit (it is not tracked on this record's own branch, whose history starts from `main` before PR #2799 merged). Its numbers were read for context but independently re-derived above rather than taken on trust.

## Open findings

None new. PR #2799's own record already flagged one gap: canonical:
`cacd3800a4c86c52ba9f45d2bd8a58d3b4db149f:docs/issue-2798/reports/adversarial-review-99b10ef0.md`
"Open findings" section — the cross-repo absolute count named in the
issue's Acceptance section (quoted above under "What did not work") is
unreproducible from a single checkout. This session independently
re-derived the same substitute measurement rather than accepting PR
#2799's number at face value: derived: same commands as above under "What
did not work" — result: `1120 -> 1108`, `-12` delta, matching PR #2799's
own reported substitution exactly. This confirms PR #2799's record wasn't
fabricated, and that the gap is a genuine single-repo access limit, not
something a second session's access could close without the operator's
original cross-repo command.

## Next steps

None.

acceptance: `grep -inE '\brole\b' test/test_bootstrap_signal_guard.py; echo "exit=$?"` on the PR worktree — result: `exit=1` (check 1, re-confirmed; full output already shown under "What was done").

acceptance: `python3 -m pytest test/test_bootstrap_signal_guard.py -v` on the PR worktree — result: `11 passed in 30.95s`, identical 11-name set to the pre-fix collection on `b4d05522` (check 2, re-confirmed; full output already shown under "What was done"). `loop_state: complete` is set on the basis of these two re-confirmations plus the must-not clause and the same-repo delta check (partial coverage of check 3, per "Open findings" above) — not a restatement of PR #2799's own claims.

skill-verdict: work-in-english — applied: invoked; wrote this record, all
worktree/grep/pytest commands, and the commit/PR text in English per the
skill (Korean reserved for the final user-facing summary).
