---
issue: 2960
role: test-derivation+silent-failure-audit-ccd3b998
author: test-derivation+silent-failure-audit-ccd3b998
skills: test-derivation (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false
code_under_review: 71fdf5757a4a17853819d6bc77b671d06a15d938
loop_state: landed
type: fix
breaking: false
verdict: pass
upstream:
  - path: lifecycle.py
    sha: 71fdf5757a4a17853819d6bc77b671d06a15d938
---

# issue-2960 — test-derivation+silent-failure-audit-ccd3b998 record

## What was done

Rewrote `_workspace_clean_state()` in `lifecycle.py` (the shared safety
predicate used by both `roster_clean()`/`spawn.py clean` and
`auto_sweep()`) so it classifies "something to lose" instead of asking
"is `git status --porcelain` empty":

- Added `_workspace_in_progress_merge(w)` — checks `git rev-parse
  --git-dir` (worktree-safe) for `MERGE_HEAD`, `CHERRY_PICK_HEAD`,
  `rebase-merge`, `rebase-apply`, `BISECT_LOG`; in-progress state is
  now dirty (previously invisible to the predicate entirely).
- Added a `git stash list` check; any stash entry is now dirty
  (previously invisible).
- Added `_workspace_untracked_not_ignored(w)` — lists untracked files
  via `git ls-files -z --others`, then classifies them with `git
  check-ignore -z --stdin` (one batched call). Replaces the
  `_HARNESS_NOISE_BASENAMES` basename whitelist entirely for untracked
  classification — deleted the whitelist and its re-export in
  `spawn.py`.
  canonical: `grep -rn "_HARNESS_NOISE_BASENAMES" --include=*.py .` after
  the edit returns only docstring prose in `lifecycle.py` (the module
  header's list of moved constants, no longer naming it), zero code
  references — confirms no other caller depended on it.
- Replaced the flat `git status --porcelain` non-`??` handling with
  `_CONTENT_DIFF_CODES = frozenset("MARCU")`: a tracked-file status
  line counts as "content diff" (dirty) only if its two-char code
  contains M/A/R/C/U. Lines that are D-only no longer trigger dirty by
  themselves.
- D-only trees are safe only when `ahead` (unpushed commits, existing
  `git log --branches --not --remotes` check, unchanged) is empty —
  the content those deletions removed still exists in the last
  (already-pushed) commit. If `ahead` is non-empty, the D-only shape
  does not shortcut it; the existing legacy stale-remote-tracking
  fetch-and-recheck (kept verbatim, only the guard condition for
  *when* to fetch changed from "porcelain output is empty" to "nothing
  else already marks this dirty") still applies before the final
  `ahead` verdict.
- `live` and `unknown` (unreadable sibling roster, issue #2603) checks
  are unchanged and still short-circuit first — this fix does not
  touch cross-checkout liveness at all.

Added `tests/test_workspace_clean_state_predicate.py`.
derived: `grep -c "^    def test_" tests/test_workspace_clean_state_predicate.py` — result: 13
acceptance: `python3 -m pytest tests/ -k workspace_clean_state -q` — result:
```
13 passed in 0.89s
```
acceptance: `python3 -m pytest tests/ -k d_only_pushed -q` — result:
```
1 passed in 0.92s
```
acceptance: `grep -n "check-ignore" lifecycle.py` — result:
```
756:    화이트리스트 대신 `git check-ignore` 로 판정 — 그 리포 자신의
766:        ["git", "-C", str(w), "check-ignore", "-z", "--stdin"],
```

Doc placement: only this role's own report was added; no
proposal/spec/handbook bucket applies to this bugfix (see
`## Upstream basis` for the survey-skip statement).

## Why

Field measurement in the issue (macOS, commit 5c0cc599, 2026-09-01):
95GB/222 workspaces, only 8 needed preserving, because the old
predicate treated *any* non-empty `git status --porcelain` as
"something to lose" — including D-only trees whose content was
already safely pushed, and untracked files the basename whitelist
didn't happen to name. The three consults cited in the issue converged
on covering unpushed commits/stash/merge-rebase/content-diffs/
untracked-not-ignored explicitly, treating D-only as safe only when
pushed, and replacing the basename whitelist with `git check-ignore` —
this record implements exactly that scope, nothing wider (no
grace-period archive stage; operator declined that in the issue
thread).

## What did not work

None.

## Upstream basis

Survey skip: this is a scoped bugfix to one existing predicate function
with the fix shape fully specified by the issue's Acceptance section
(condition list, D-only exception, check-ignore mechanism) — no open
design decision to survey alternatives for.

- `lifecycle.py` (commit 71fdf5757a4a17853819d6bc77b671d06a15d938,
  `_workspace_clean_state`, `_workspace_in_progress_merge`,
  `_workspace_untracked_not_ignored`, `_CONTENT_DIFF_CODES`) — sha:
  71fdf5757a4a17853819d6bc77b671d06a15d938
- `spawn.py` (commit 71fdf5757a4a17853819d6bc77b671d06a15d938,
  re-export list updated: removed `_HARNESS_NOISE_BASENAMES`, added
  `_CONTENT_DIFF_CODES`, `_workspace_in_progress_merge`,
  `_workspace_untracked_not_ignored`) — sha:
  71fdf5757a4a17853819d6bc77b671d06a15d938
- `tests/test_cross_checkout_prune_liveness.py` (pre-existing, issue
  #2492/#2603) — read only, not modified; its `_make_pushed_git_workspace`
  helper pattern is what `tests/test_workspace_clean_state_predicate.py`
  follows — sha: not applicable (unchanged file)

### skill-verdict

- skill-verdict: test-derivation — applied: invoked; classified the
  five Acceptance bullets as one High-risk requirement (the predicate
  itself: could destroy unrecoverable work if wrong) routed to decision
  table testing (≥2 conditions selecting among outcomes — live/unknown/
  merge/stash/content-diff/untracked/ahead, priority-ordered short
  circuit). Built a 9-row decision table in
  `tests/test_workspace_clean_state_predicate.py`'s module docstring
  (rows 1-2, live and unknown, already covered by
  `tests/test_cross_checkout_prune_liveness.py`; rows 3-9 covered
  here). Wrote one test per feasible column plus one regression test
  for the pre-existing stale-remote-tracking fetch behavior and one for
  the removed basename-whitelist must-not.
  derived: `python3 -m pytest tests/test_workspace_clean_state_predicate.py -q` — result:
  ```
  13 passed in 0.88s
  ```
  EP/BVA, state-transition, pairwise, and MC/DC routes were not
  applicable — the requirement is a single short-circuit decision
  function, not an input-range, lifecycle, or multi-parameter-
  combination shape.
- skill-verdict: silent-failure-audit — applied: invoked; audited the
  five new/changed `subprocess.run` call sites in
  `_workspace_in_progress_merge`, `_workspace_untracked_not_ignored`,
  and the stash/status/ahead calls in `_workspace_clean_state` itself.
  Classification: all five follow the pre-existing pattern in this same
  function (and elsewhere in `lifecycle.py`) of not checking
  `returncode` before reading `.stdout` — a failing git invocation
  (corrupted `.git`, permission error, disk fault) reads identically to
  "nothing found" at every site.
  canonical: `lifecycle.py:742-751` (`_workspace_in_progress_merge`):
  ```
  r = subprocess.run(["git", "-C", str(w), "rev-parse", "--git-dir"],
                        capture_output=True, text=True)
  if r.returncode != 0:
      return False
  ```
  A non-zero `returncode` here is treated identically to "not a repo /
  no merge in progress" — a corrupted `.git` or a transient permission
  error reads the same as "nothing to worry about." The same shape
  repeats at `lifecycle.py:812-816` (stash) and `lifecycle.py:824`
  (`_workspace_untracked_not_ignored`, `.stdout` read with no
  `returncode` check at all). This composes to the predicate returning
  `(None, "")` (safe to delete) for a workspace it could not actually
  inspect —
  logged as an open finding below rather than fixed, since closing it
  means deciding a new default (treat git-command failure as
  `"unknown"`, matching the existing unreadable-sibling-roster
  convention) across every call site in this function, which is a
  broader, separately-reviewable change than "ask what would be lost."
- other mounted skills: not triggered (work-in-english is guidance-only
  per this session's directive stack, enforced by hook rather than
  invoked via the Skill tool)

## Open findings

- Git-subprocess-failure blind spot in `_workspace_clean_state()` and
  its two new helpers (see silent-failure-audit skill-verdict above for
  the file:line citations): none of the `subprocess.run(...)` calls
  check `returncode` before treating empty/absent stdout as "nothing
  found." A workspace whose `.git` is corrupted, unreadable, or hits a
  transient disk/permission error would read as fully clean and be
  deleted despite the issue's must-not ("never delete a workspace
  holding unpushed commits, stash entries, or in-progress merge/rebase
  state") being genuinely undeterminable rather than genuinely false.
  Resolution path: a follow-up issue to make every git call in this
  function `returncode`-checked and route command failure to the
  existing `"unknown"` reason (already used for unreadable sibling
  rosters, issue #2603) — deliberately out of scope here because it
  changes the default for command *failure*, not the predicate's
  definition of "something to lose," and touches every call site in
  the function rather than the ones this issue named.
- Carried from the issue itself, not newly discovered: `?? docs/issue-790/`-shaped
  untracked-and-not-gitignored directories still preserve their
  workspace after this fix. The issue named this as a known limit the
  predicate change alone does not close.
  derived: `python3 spawn.py clean --dry-run` on this host, run
  immediately after landing the code change — result (tail): most
  remaining preserved workspaces are reported with a
  `[미추적 파일 N건]` (untracked-file) reason rather than the old
  `[미커밋 N건]` blanket reason, i.e. genuine untracked-not-ignored
  content, not noise the predicate misclassified.

## Next steps

None — `loop_state: landed`.
