---
issue: 2960
role: adversarial-review-569ab005
author: adversarial-review-569ab005
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: 71fdf5757a4a17853819d6bc77b671d06a15d938
loop_state: landed
type: docs
breaking: false
verdict: pass
upstream:
  - path: lifecycle.py
    sha: 71fdf5757a4a17853819d6bc77b671d06a15d938
---

# issue-2960 — adversarial-review-569ab005 record

## What was done

Independently verified PR #2963 (branch
`issue-2960/test-derivation+silent-failure-audit-ccd3b998`, `lifecycle.py`
at `71fdf5757a4a17853819d6bc77b671d06a15d938`) — issue #2960's workspace
preservation predicate rewrite. Fetched the PR head into an isolated
`git worktree` at `/tmp/pr2963-verify` (`git fetch origin
pull/2963/head:pr-2963-verify && git worktree add /tmp/pr2963-verify
pr-2963-verify`, removed after use), and re-ran every issue-#2960
acceptance check myself inside it, without citing PR #2963's or PR
#2965's own reported numbers as evidence.

Re-run results, each executed live in the isolated worktree this turn:

- acceptance: `python3 -m pytest tests/ -k workspace_clean_state -q` — result:
```
13 passed in 0.99s
```
- acceptance: `python3 -m pytest tests/ -k d_only_pushed -q` — result:
```
1 passed in 0.89s
```
- acceptance: `grep -n "check-ignore" lifecycle.py` — result:
```
756:    화이트리스트 대신 `git check-ignore` 로 판정 — 그 리포 자신의
766:        ["git", "-C", str(w), "check-ignore", "-z", "--stdin"],
```
- acceptance: `python3 spawn.py clean --dry-run` — result:
```
정리 끝 — 지움 0, 남김 69
```
  This reproduces PR #2965's reported 0 -> 0 (69 -> 69) pair exactly —
  derived independently in a fresh worktree, not read from either PR's
  body.
- acceptance: `python3 -m pytest tests/test_cross_checkout_prune_liveness.py tests/test_workspace_clean_state_predicate.py test/test_reconcile_crash_verdict_race.py test/test_roster_kill_lease_suffix.py -q` — result:
```
40 passed in 0.95s
```
  (`tests/test_workspace_clean_state_predicate.py` is a new file PR
  #2963 adds; untracked on this session's own
  `issue-2960/adversarial-review-569ab005` tree — it only exists inside
  the `/tmp/pr2963-verify` worktree checked out from PR #2963's own
  branch.)

canonical: `git diff 5c0cc599 71fdf575 -- lifecycle.py spawn.py`, read
in full this turn inside `/tmp/pr2963-verify` — `must not` list audit
against that diff:
- unpushed commits / stash / in-progress merge-rebase: new
  `_workspace_in_progress_merge()` checks `MERGE_HEAD`,
  `CHERRY_PICK_HEAD`, `rebase-merge`, `rebase-apply`, `BISECT_LOG` via
  `git rev-parse --git-dir` (worktree-safe); a new `git stash list`
  check precedes the status parse. Both are new dirty-reasons, not
  removed ones — not violated.
- `_HARNESS_NOISE_BASENAMES` extended: the diff *deletes* the entire
  frozenset and replaces basename matching with
  `_workspace_untracked_not_ignored()` (`git ls-files -z --others`
  piped through `git check-ignore -z --stdin`) — not extended, not
  violated.
- deletion path skipping the dry-run report: `spawn.py`'s diff is only
  two re-export line changes (`_HARNESS_NOISE_BASENAMES` ->
  `_CONTENT_DIFF_CODES`, plus two new re-exports); `roster_clean()` /
  `auto_sweep()` themselves are untouched by the diff — not violated.
- predicate weakened for a live session's workspace: the `live` early
  return in `_workspace_clean_state()` is untouched by the diff — not
  violated.

One correctness edge case checked against that same diff and found
already covered: git's porcelain conflict code `DD` (both-deleted) is
not in the new `_CONTENT_DIFF_CODES = frozenset("MARCU")` set, but `DD`
only occurs during an unresolved merge/cherry-pick/rebase, which
`_workspace_in_progress_merge()` already catches first (short-circuits
before the content-diff check runs, per the same diff read above) — no
gap for that combination.

canonical: this turn's own live measurement of
`~/.tokenmaxxxer/work` (not PR #2963's or #2965's claim) —
investigated why PR #2965's population measurement came back 0 -> 0
rather than accepting "nothing further to reclaim" at face value.
derived: `for d in */; do [ -d "$d/.git" ] && [ -d "$d/.on-the-record" ] && echo "$d"; done | wc -l` against `ls -d */ | xargs -I{} test -d {}/.git` — result: 71 of 71 git worktrees under `~/.tokenmaxxxer/work` carry an untracked, non-gitignored `.on-the-record/` directory (harness bookkeeping: `role.json` + `directive/*.md`, confirmed via `git check-ignore -q` returning non-zero on each file under `.on-the-record/directive/` in a sampled `tokenmaxxxer-core-issue-233-*` worktree).
derived: `git status --porcelain | grep -v '\.on-the-record'` run per-workspace across the same 69 dry-run-preserved workspaces — result: for 35 of the 69, the only dirty/untracked signal is `.on-the-record/` — everything else in that workspace is clean.
Traced the cause: `on-the-record`'s own `.gitignore` exempts
`.on-the-record/directive/` and two other subpaths, but plugin
self-checkouts of other repos on this host carry no such exemption —
derived: `git check-ignore -v .on-the-record/directive/hook-contract.md` inside a sampled `tokenmaxxxer-core-issue-233-*` worktree — result: empty (no match, confirming `.on-the-record/` is fully un-gitignored in that repo's own `.gitignore`), versus a non-empty match on the same command run inside this session's own `on-the-record` worktree.

## Why

The task asked me not to trust PR #2963's own claimed results and to
independently assess whether the 0 -> 0 measurement is
correct-but-inapplicable (nothing left to reclaim on this host's actual
population) versus evidence the rewrite doesn't work. Re-running the
checks in an isolated worktree rather than reading the PR's pasted
output is what makes that assessment independent rather than a
citation of PR #2965's own record. Going one layer further — asking
*why* 69 workspaces still show as dirty, rather than accepting "genuine
untracked-not-ignored content" as an unexamined black box — is what
surfaced the `.on-the-record/` universal-artifact cause, which neither
PR #2963 nor PR #2965's record identified.

## What did not work

None — every acceptance check reproduced on first execution in the
isolated worktree; no deviation from the assigned verification scope.

## Upstream basis

- `lifecycle.py` / `spawn.py` at `71fdf5757a4a17853819d6bc77b671d06a15d938`
  (PR #2963's head, `issue-2960/test-derivation+silent-failure-audit-ccd3b998`)
  — fetched via `git fetch origin pull/2963/head:pr-2963-verify` and
  `git worktree add /tmp/pr2963-verify pr-2963-verify` — sha:
  71fdf5757a4a17853819d6bc77b671d06a15d938
- PR #2965 (`issue-2960/test-derivation-8718eaa7`) — its record lives
  at `docs/issue-2960/reports/test-derivation-8718eaa7.md` on that PR's
  own branch, untracked on this tree (the path does not exist on
  `issue-2960/adversarial-review-569ab005` or on PR #2963's branch) —
  read via `git fetch origin pull/2965/head:pr-2965-verify` + `git show
  pr-2965-verify:docs/issue-2960/reports/test-derivation-8718eaa7.md`
  for its measurement methodology only; not cited as evidence for my
  own 0 -> 0 reproduction above, which I ran independently against
  `71fdf5757a4a17853819d6bc77b671d06a15d938` in my own worktree, not
  against #2965's branch — sha: not applicable (read for context on a
  different PR's branch, not built on)
- `~/.tokenmaxxxer/work` (this host's live workspace population, 71
  git worktrees at measurement time per the `derived:` count above) —
  sha: not applicable (not a repo path)

## Open findings

1. **0 -> 0 is correct-but-inapplicable on this host, and the
   applicability gap has a specific, actionable cause the PRs didn't
   name.** The predicate rewrite is not defective — the `must not`
   audit above found no violation, and `git check-ignore` is doing
   exactly what issue #2960 asked (verified via the `check-ignore -v`
   `derived:` line above). But on this host, `.on-the-record/` is
   untracked and un-gitignored in all 71 checked worktrees (per the
   `derived:` count above), and is the sole reason 35 of the 69
   preserved workspaces stay preserved (per the second `derived:` line
   above). PR #2965's record attributes the 69 preserved workspaces to
   "genuine untracked-not-ignored content ... per their printed
   reasons," which is technically accurate but doesn't name what that
   content actually is — a single universal harness artifact, not
   diverse per-workspace user content. The issue's own "known limit"
   paragraph anticipated *some* residual untracked-content preservation
   (citing `docs/issue-790/` as a one-off example) but did not
   anticipate a systematic, all-of-workspaces cause. Resolution path:
   this is a `.gitignore` gap in downstream repos checked out under
   `~/.tokenmaxxxer/work` (starting with `tokenmaxxxer-core`, per the
   `check-ignore -v` `derived:` line above showing no match there)
   rather than a `lifecycle.py` defect — worth a follow-up issue so the
   field-measured 95GB/222-workspace problem this issue opened with
   doesn't quietly persist because closing this issue reads as "fixed."
2. **`_CONTENT_DIFF_CODES` doesn't cover git's `T` (typechange) status
   code** (`lifecycle.py`, `_CONTENT_DIFF_CODES = frozenset("MARCU")`,
   read via the `git diff 5c0cc599 71fdf575` `canonical:` citation
   above). A tracked file that changes type (e.g. symlink <-> regular
   file) without content difference would show `T ` / ` T` in
   `git status --porcelain`, which is in `tracked_lines` but not
   `content_diff_lines`, so it would not count as "something to lose."
   Low severity: the issue's acceptance criteria and consult
   convergence explicitly enumerate "M/A/R" (this PR already covers
   more than asked, adding C/U); `T` was never in scope, and I ran no
   reproduction of a live typechange case this turn — noted for
   completeness, not a blocker.
3. The git-subprocess-failure blind spot that PR #2963's own record
   already flagged (a fully-broken `git` binary/corrupted `.git` would
   make every new subprocess call return empty stdout, which the
   predicate would read as "nothing to lose") is pre-existing behavior,
   unchanged by this diff — the original predicate's `status
   --porcelain` call had the same gap before this PR. Not a
   regression; already disclosed upstream in PR #2963's own record, no
   new action from this verification.

## Next steps

acceptance: the full acceptance set re-run in the isolated
`/tmp/pr2963-verify` worktree this turn — derived: the `acceptance:`/
`derived:` lines under What was done above (13 passed, 1 passed,
check-ignore present, 지움 0/남김 69, 40 passed) — result: reproduced
exactly, no outstanding check to re-run. `loop_state: landed`. Finding
1 is the one worth a human decision: whether to open a follow-up issue
for the `.on-the-record/`-in-`.gitignore` gap before treating this
predicate rewrite as having resolved the field-measured disk problem
it opened with.

### skill-verdict

- skill-verdict: adversarial-review — applied: invoked; used its
  independent-evaluator framing to structure this as a from-scratch
  re-derivation (isolated worktree, no citation of PR #2963/#2965's own
  numbers) rather than a review of their claimed results, and to push
  past the PRs' own "genuine untracked content" black-box into what
  that content actually is (Open finding 1).
- skill-verdict: defect-verification-independence-from-upstream-verdicts
  — applied: invoked; re-ran all five acceptance checks from primary
  evidence in a fresh worktree instead of citing PR #2963's pasted
  results, and deliberately went past the happy-path re-derivation to
  interrogate the 0 -> 0 population number rather than accepting PR
  #2965's clean record as settling the question.
- skill-verdict: work-in-english — not-applicable: the assigned task
  text was in English; this record is authored in English throughout.
- other mounted skills: not triggered
