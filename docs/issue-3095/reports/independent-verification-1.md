---
issue: 3095
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # independent verification of PR #3106's own deliverable against issue #3095
code_under_review: e06909962b58130aa889b8c15561ade355bf89f3
loop_state: landed
type: defect-verification-record
breaking: false
verdict: All 3 required acceptance checks Present, both must-not clauses held,
  both scoping/retention guards confirmed load-bearing by mutation. One
  new finding beyond the issue's stated acceptance scope, reproduced
  directly this session -- not a blocker on #3095's own acceptance.
upstream:
  - path: PR #3106 (github.com/tokenmaxxxer/on-the-record/pull/3106),
      fetched as local ref pr3106-review, head commit e0690996 -- the
      deliverable under review
    sha: e06909962b58130aa889b8c15561ade355bf89f3
---

# issue-3095 — independent-verification-1 record

## What was done

Independent, builder-blind verification of PR #3106 against issue
#3095's three `check:` acceptance commands and its two `must-not`
clauses, re-derived in two linked worktrees (`pr3106-review` at head
`e06909962b58130aa889b8c15561ade355bf89f3`, and `origin/main` at
`0cd96c6dba2f9470a949d2d451613d24b75d0653`) rather than trusting the
PR's or the builder's own record's pasted output. Both worktrees were
created under `/tmp/verify-3106/` and removed (`git worktree remove
--force`) at the end of this session. Both `gates/probe_parked_report_repo_leak.py`
(untracked on this branch) and `tests/test_spawn_on_pr_repo_scope.py`
(untracked on this branch) below existed only in the now-removed
`pr3106-review` worktree, never on this verification session's own
`issue-3095/independent-verification-1` branch (which carries none of
PR #3106's commits) — every command below that names either file ran
inside that worktree while it existed.

canonical: `gh issue view 3095` output (title, body, acceptance section,
must-nots, all 5 comments) and `gh pr view 3106 --json
title,state,mergeCommit,baseRefName,headRefName,mergedAt,body` (state:
OPEN, not yet merged) — both read in full before any check ran.

**Acceptance check 1** — `tests/test_spawn_on_pr_repo_scope.py`
(untracked on this branch):
acceptance: `bash -c "python3 -m pytest tests/test_spawn_on_pr_repo_scope.py -q"` in the `pr3106-review` worktree — result:
```
......                                                                   [100%]
6 passed in 1.27s
```

**Acceptance check 2** — the probe, `gates/probe_parked_report_repo_leak.py`
(untracked on this branch):
acceptance: `bash -c "python3 gates/probe_parked_report_repo_leak.py"` in the `pr3106-review` worktree — result:
```
[spawn-on-pr] park=1건 waiting-for-human (승인-대기 상태 변화 없음): ['issue-3059']
ok
```
Sensitivity control (must-not #2 — a check must not pass vacuously),
re-derived independently rather than cited from the builder's record:
copied the same unmodified `gates/probe_parked_report_repo_leak.py`
(untracked on this branch) file into a fresh `origin/main` worktree (no
source edits) and ran it there — result:
```
FAIL: parked_report(root_a) and parked_report(root_b) are identical (['issue-3059']) -- no per-repo filter is running at all (issue #3095).
```
exit 1. Same file: fails unmodified on main, passes on the branch —
genuine sensitivity, not a vacuous check.

**Acceptance check 3** — full suite, both trees:
acceptance: `bash -c "python3 -m pytest tests/ -q"` in the `pr3106-review` worktree — result:
```
222 passed, 2 warnings in 10.49s
```
acceptance: `bash -c "python3 -m pytest tests/ -q"` in the `origin/main` worktree (no PR file copies) — result:
```
216 passed, 2 warnings in 9.37s
```
derived: `216 + 6 = 222` (216 pre-existing on `origin/main`, plus this
PR's 6 new tests collected from `tests/test_spawn_on_pr_repo_scope.py`,
untracked on this branch) — exact match against the 222 counted above,
zero regressions.
Note: issue #3081's independent verifications and the issue-3095 spawn
brief both describe `tests/ -q` as blocked by 5 pre-existing
`test_respawn_deliverable_gate.py`/`test_spawn_gate_wiring.py` failures
from issue #3083. checked: `git merge-base --is-ancestor 7ee16612
pr3106-review` — result: true (PR #3106 was rebased onto `origin/main`
past PR #3089's #3083 fix, commit `78fda1e0`/`#3112`, before this
verification ran) — derived: both pasted results above show `0 failed`
(`222 passed` and `216 passed`, no `X failed` segment in either line),
so those 5 pre-existing failures are absent from both trees and the two
counts reflect this fix alone.

**Must-not #1** (do not suppress/rate-limit the waiting-for-human line):
checked — the acceptance check 2 output pasted above still prints
`park=1건 waiting-for-human ... ['issue-3059']` for the genuinely-parked
own-repo subject; the fix filters by repo, it does not suppress the line
itself.

**Must-not #2** (do not assert via a nonexistent CLI flag): checked —
derived: `grep -n "def main\|argparse\|sys.argv"
gates/probe_parked_report_repo_leak.py` (untracked on this branch) in
the `pr3106-review` worktree — result: no CLI entrypoint; the probe and
the test file both call `spawn_on_pr.spawn_missing_for_pr()` /
`spawn_on_pr.parked_report()` directly, same idiom as issue #3081's
must-not required.

**Mutation tests** (self-devised, per defect-verification-independence
skill rule 2 — at least one attempt beyond the happy-path re-run), both
run in the `pr3106-review` worktree and both reverted with `git checkout
-- gates/spawn_on_pr.py` immediately after capturing output:
1. Removed the `entry.get("repo") == repo_slug` filter from
   `parked_report()`. derived: re-ran `python3 gates/probe_parked_report_repo_leak.py`
   (untracked on this branch) and `python3 -m pytest
   tests/test_spawn_on_pr_repo_scope.py -q` (untracked on this branch) —
   result:
```
FAIL: parked_report(root_a) and parked_report(root_b) are identical (['issue-3059']) -- no per-repo filter is running at all (issue #3095).
3 failed, 3 passed in 1.32s
```
   (the 3 failures: `test_parked_report_not_identical_across_repos`,
   `test_parked_report_excludes_other_repo`,
   `test_legacy_entry_without_repo_key_excluded_from_resolvable_repo`).
   Filter is load-bearing, not cosmetic.
2. Removed the `if prior is not None and prior.get("repo") != repo_slug:
   prior = None` eviction guard. derived: re-ran both of the same two
   commands above — result:
```
FAIL: repo A inherited repo B's park/attempts history for the same-named subject 'issue-3059' instead of evicting it -- a cross-repo entry must not be treated as this repo's own genuine prior (issue #3095 retention split).
1 failed, 5 passed in 1.17s
```
   (the 1 failure: `test_no_retention_when_entry_is_another_repos`).
   Guard is load-bearing.
   derived: `python3 gates/probe_parked_report_repo_leak.py`
   (untracked on this branch) after reverting both mutations — result:
   `ok` (restored file re-confirmed clean before moving on).

**New finding** (self-devised adversarial attempt, devised and run
before reading either prior verification PR's body, per the skill's rule
5 — read #3119 and #3121 only after this attempt, to check convergence,
not to shape it): `spawn._repo_slug(root)` (`plumbing.py:64` on the
`pr3106-review` worktree) returns `None` and caches it whenever `gh repo
view` fails (no auth, no resolvable remote, or a stale/deleted
workspace). `parked_report()`'s new filter is `entry.get("repo") ==
repo_slug`. If two different roots both fail slug resolution in the same
process, both get `repo_slug = None`, and `None == None` is `True` — the
filter degenerates back to no filter at all for that pair of roots.
derived: seeded one park-state entry with `"repo": None`, patched
`spawn._repo_slug` to return `None` unconditionally for both of two
distinct root paths (`unittest.mock.patch.object`), called
`parked_report(root_a)` and `parked_report(root_b)` in a standalone
script run against the `pr3106-review` worktree — result:
```
out_a: ['issue-3059']
out_b: ['issue-3059']
identical: True
```
— byte-identical, the exact defect signature this PR closes for
resolvable slugs. This is a narrower residual instance of the same leak,
gated on a fail-open condition the fix's own docstring names
(`gates/spawn_on_pr.py:780` on `pr3106-review`, "same fail-open bucket
`_repo_slug` itself already uses for a checkout with no resolvable `gh`
remote") but does not add a test for. Not a blocker on #3095's stated
acceptance — none of the three required checks exercise
unresolvable-slug roots, and both required checks pass cleanly with
resolvable slugs (acceptance checks 1 and 2 above). Distinct from the
write-collision finding PR #3119 already surfaced and the builder
already disclosed (that one is about the bare-subject key colliding on
write between two *resolvable*, differently-slugged repos; this one is
about slug resolution itself failing for both sides at once).

## Why

Builder-blind, re-derived from primary evidence rather than citing the
implementer's record or either prior verification PR's pasted output —
per the defect-verification-independence skill, a review requirement
already marked Present is a claim to re-test, not a settled fact. Read
PR #3119 and PR #3121's bodies (canonical: `gh pr view 3119 --json body`
and `gh pr view 3121 --json body` output, both read in full) only after
running my own checks and devising my own adversarial attempt above, to
confirm convergence rather than to shape scope in advance. Both prior
sessions' own claimed acceptance-check results (`6 passed` /
`ok`-then-`FAIL` sensitivity control / `222`-vs-`216` on `tests/ -q`)
match this session's independently re-derived numbers exactly (all
pasted directly above in "What was done").

## What did not work

None. derived: every check/probe/mutation/finding command pasted in
"What was done" above returned a defined result this session — pass,
fail-as-expected for a sensitivity/mutation control, or a reproduced
finding — with no command left inconclusive, hanging, or unexplained.

## Upstream basis

PR #3106 (`pr3106-review`, head `e06909962b58130aa889b8c15561ade355bf89f3`)
— `gates/spawn_on_pr.py` (`_park_state_path`, `load_park_state`,
`parked_report`, `spawn_missing_for_pr`), plus `gates/probe_parked_report_repo_leak.py`
(untracked on this branch) and `tests/test_spawn_on_pr_repo_scope.py`
(untracked on this branch), both of which existed only in the removed
`pr3106-review` worktree (see "What was done" above) — the deliverable
this record verifies.

`origin/main` at `0cd96c6dba2f9470a949d2d451613d24b75d0653` — the
comparison tree for the sensitivity control and the regression-count
check.

## Open findings

1. Unresolvable-slug collision (see "New finding" above, reproduced this
   session — derived output pasted there: `out_a`/`out_b` both
   `['issue-3059']`, `identical: True`): two roots whose
   `spawn._repo_slug()` both fail resolution share `None` as their
   attribution key, reintroducing the cross-repo leak this PR otherwise
   closes. Resolution path: a follow-up issue, same track as the
   write-collision finding PR #3119 already logged — could be closed by
   treating `repo_slug is None` as "exclude from every report"
   (fail-closed on the read side) rather than treating `None` as a valid
   attribution value that can match another `None`.
2. Write-collision on same-numbered subjects across two resolvable
   repos (bare-subject key, not re-keyed like `_drift_cache_key`) —
   already disclosed by the builder's own record and independently
   confirmed by PR #3119; not re-litigated here beyond confirming the
   builder's stated reason (pre-existing `gates/test_spawn_on_pr.py`
   fixture compatibility, a file that does exist on `origin/main` and on
   this branch) is real. derived: `grep -c "KEY = SUBJECT"
   gates/test_spawn_on_pr.py` in the `pr3106-review` worktree — result:
   `1`, matches the builder's own cited grep in their record.

## Next steps

None. loop_state: landed.

acceptance: `bash -c "python3 -m pytest tests/test_spawn_on_pr_repo_scope.py -q"` (untracked on this branch, ran in the `pr3106-review` worktree) — result:
```
6 passed in 1.27s
```

acceptance: `bash -c "python3 gates/probe_parked_report_repo_leak.py"` (untracked on this branch, ran in the `pr3106-review` worktree) — result:
```
ok
```

acceptance: `bash -c "python3 -m pytest tests/ -q"` (ran in the `pr3106-review` worktree) — result:
```
222 passed, 2 warnings in 10.49s
```

All three of issue #3095's required checks re-derived Present this
session; this record's own verification pass is complete. Whether/when
PR #3106 itself merges is a landing decision outside this record's
scope.

skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; ran my own worktree-based re-derivation and a
self-devised adversarial attempt (the unresolvable-slug finding above)
before reading PR #3119/#3121's bodies, per rules 1, 2, and 5.
skill-verdict: work-in-english — applied: invoked; this record, all
commit messages, and the PR body are written in English; only the final
chat summary to the user is in Korean.
