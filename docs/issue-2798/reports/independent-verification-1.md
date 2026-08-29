---
issue: 2798
role: independent-verification-1
author: independent-verification-1
code_under_review: cacd3800a4c86c52ba9f45d2bd8a58d3b4db149f
loop_state: landed
type: verification
breaking: false
verdict: pass
verifies_subject: true
upstream:
  - path: PR #2799 (branch issue-2798/adversarial-review-99b10ef0)
    sha: cacd3800a4c86c52ba9f45d2bd8a58d3b4db149f
---

# issue-2798 — independent-verification-1 record

## What was done

Independently re-ran all three of issue #2798's acceptance checks against
PR #2799 (`issue-2798/adversarial-review-99b10ef0`, tip
`cacd3800a4c86c52ba9f45d2bd8a58d3b4db149f`), which renames the twelve
retired-noun (`role`) occurrences PR #2794 introduced into
`test/test_bootstrap_signal_guard.py`'s `attempt_id`/`skill` fixture
literals. Used two disposable `git worktree`s — one at the PR tip, one at
`b4d05522` (the pre-rename commit, also `origin/main`'s current tip) — so
before/after comparisons ran against real checkouts rather than stash
toggling in a single tree. Both worktrees were removed after use; no
uncommitted state remains in this branch's own tree (`git status --short`
shows only `docs/issue-2798/`, this record).

canonical: `gh pr view 2799` (title, body, diff via `gh pr diff 2799`) —
read in full before verification.

## Why

verifies_subject: true because this record audits PR #2799, the delivered
fix for issue #2798 itself (not a third party's work on a different
subject).

## What did not work

None.

acceptance: `grep -inE '\brole\b' test/test_bootstrap_signal_guard.py; echo "exit=$?"` (worktree at PR #2799 tip `cacd3800`) — result:
```
exit=1
```

acceptance: test-name-set comparison, PR-tip worktree vs. pre-rename (`b4d05522`) worktree —
`python3 -m pytest test/test_bootstrap_signal_guard.py --collect-only -q` in each, sorted and diffed — result:
```
NAME SETS IDENTICAL
```
Both worktrees also ran `python3 -m pytest test/test_bootstrap_signal_guard.py -v`: `11 passed in 30.88s` (before) and `11 passed in 30.87s` (after) — same 11 tests, same PASSED outcome in both.

acceptance: whole-repo `grep -rIc` outside `docs/` and `runs/`, before vs. after —
`grep -rIc --exclude-dir=.git --exclude-dir=docs --exclude-dir=runs -inE '\brole\b' . | awk -F: '{s+=$2} END{print s}'` — result:
```
before (b4d05522 worktree): 1120
after  (PR #2799 tip worktree): 1108
```
derived: `1120 - 1108 = 12`, exactly the twelve occurrences the diff removes — the delta is fully accounted for by this one file. This matches the number in the PR's own review record (its text and full diff visible via `gh pr diff 2799`, which includes that record as an added file) — same repo, same command, same numbers.

unverifiable: the issue's absolute figures (`1263` pre-merge, `1275` post-merge) were stated as measured "across both repos"; this session, like the PR's own review session, has access to only one repo checkout and no record of the operator's exact historical command, so it cannot reproduce those absolute numbers. This is the same gap the PR's own record already logged as `unverifiable:` and as an open finding (per `gh pr diff 2799` body) — re-confirmed independently here, not newly discovered.

acceptance: full suite regression check, PR-tip worktree — `python3 -m pytest test/ -q` — result:
```
15 failed, 425 passed, 3 xfailed in 31.80s
```
acceptance: same command, pre-rename/`origin/main` worktree — result:
```
15 failed, 425 passed, 3 xfailed in 31.61s
```
derived: diffed the two `FAILED` name lists (15 lines each) by eye against the captured output — identical set in both runs, none of the 15 reference `test_bootstrap_signal_guard.py`. The PR introduces no new failure.

acceptance: `grep -inE '\b(position|job|function|part|persona)\b' test/test_bootstrap_signal_guard.py` (PR-tip worktree, checking the issue's must-not — no same-meaning substitute for the retired noun) — result: one hit, line 141, `"...the existing dead-entry watchdog's\n        job, not this one's..."` — pre-existing docstring prose unrelated to any of the twelve renamed fixture literals, not a substitute rename. No violation of the must-not clause.

## Upstream basis

PR #2799 (`issue-2798/adversarial-review-99b10ef0`, tip `cacd3800`),
reviewed via `gh pr view 2799` and `gh pr diff 2799`. That diff carries
the PR's own record, docs/issue-2798/reports/adversarial-review-99b10ef0.md,
untracked on this verification branch (it lives on the PR's own branch,
issue-2798/adversarial-review-99b10ef0, not here) — read as part of the
`gh pr diff 2799` output rather than as a local file. Compared against
`b4d05522` (`origin/main` tip, the pre-rename commit from PR #2794 / issue
#2742).

## Open findings

1. Same gap the PR's own record already logged: the issue's absolute
   cross-repo counts (1263 → 1275) are not reproducible from this
   session's single-repo checkout. Not a defect in PR #2799 — the
   same-repo delta (1120 → 1108, -12) both this session and the PR's own
   review session independently measured accounts exactly for the twelve
   renamed literals, which is the actionable part of the check.
   Resolution path: whoever holds the operator's original cross-repo
   tally command re-runs it against the now-landed rename; no further
   action available to this session.

## Next steps

None — loop_state: landed. Requirement met — acceptance: `grep -inE
'\brole\b' test/test_bootstrap_signal_guard.py; echo "exit=$?"` (PR #2799
tip, re-quoted from "What did not work" above) — result:
```
exit=1
```
acceptance: `python3 -m pytest test/ -q` (PR-tip worktree, re-quoted from
above) — result:
```
15 failed, 425 passed, 3 xfailed in 31.80s
```
— identical failing-name set to the pre-rename worktree's own run of the
same command, so no regression. PR #2799 verified independently: all
three of issue #2798's acceptance checks reproduced (checks 1 and 2 fully
pass; check 3's reproducible same-repo component matches, its cross-repo
component remains the same disclosed open gap). No same-meaning
substitute used for the retired noun. Verdict: pass.

skill-verdict: work-in-english — applied: invoked; wrote this record, all
worktree/test output, and code-facing text in English per the skill,
reserving Korean for the end-of-turn user summary only.
