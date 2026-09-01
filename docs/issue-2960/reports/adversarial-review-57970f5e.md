---
issue: 2960
role: adversarial-review-57970f5e
author: adversarial-review-57970f5e
skills: adversarial-review (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2963 (issue-2960/test-derivation+silent-failure-audit-ccd3b998), reviewed and audited this session
code_under_review: lifecycle.py, spawn.py, tests/test_workspace_clean_state_predicate.py
type: verification
breaking: no
verdict: pass
loop_state: terminal
upstream:
  - path: docs/issue-2960/reports/test-derivation+silent-failure-audit-ccd3b998.md
    sha: 71fdf5757a4a17853819d6bc77b671d06a15d938
---

# issue-2960 — adversarial-review-57970f5e record

## What was done

Independently verified PR #2963 (branch
`issue-2960/test-derivation+silent-failure-audit-ccd3b998`, code commit
`71fdf5757a4a17853819d6bc77b671d06a15d938`, base `main`). Fetched the PR
head into an isolated `git worktree` (`/tmp/verify-pr2963-3397613`,
removed before this record was written), re-ran all 4 of issue #2960's
acceptance-check commands there from scratch — not by reading the PR's
claimed output — read `lifecycle.py`'s full diff line-by-line against the
issue's must-not list, and separately fetched a second worktree at the
pre-fix commit `5c0cc599` to compare predicate behavior against this same
live host's `~/.tokenmaxxxer/work` population.

canonical: `gh pr view 2963 --json headRefName,headRefOid,baseRefName,commits` output this session — head `c7270bd01aec17180e5943262ffbc139ff058fbe` (2 commits: code `71fdf575` + upstream's own record `c7270bd0`), base `main`, state OPEN.

Acceptance checks, executed live this session against the fetched PR
branch in the isolated worktree, matching the PR body's claimed counts
exactly:

```
$ python3 -m pytest tests/ -k workspace_clean_state -q
13 passed in 0.97s
$ python3 -m pytest tests/ -k d_only_pushed -q
1 passed in 0.89s
$ grep -n "check-ignore" lifecycle.py
756:    화이트리스트 대신 `git check-ignore` 로 판정 — 그 리포 자신의
766:        ["git", "-C", str(w), "check-ignore", "-z", "--stdin"],
$ python3 spawn.py clean --dry-run
정리 끝 — 지움 0, 남김 70
```

derived: `python3 -m pytest tests/test_cross_checkout_prune_liveness.py tests/test_workspace_clean_state_predicate.py test/test_reconcile_crash_verdict_race.py test/test_roster_kill_lease_suffix.py -q` (same worktree; test_workspace_clean_state_predicate.py untracked on this record's own branch — it lives only on the PR branch, fetched and executed there this session) — result: `40 passed in 0.95s`, matching the PR body's claimed regression-suite count.

derived: `grep -rn "_HARNESS_NOISE_BASENAMES" --include=*.py .` (same worktree) — result: one hit, a docstring line describing the *removed* whitelist in the new test file (untracked on this record's own branch; path `tests/test_workspace_clean_state_predicate.py:199` on the PR branch only); zero code references. Confirms the whitelist was deleted outright, not extended.

Code-level audit against the issue's must-not list (`lifecycle.py:728-819` diff on the PR branch, read in full this session):

- **"never delete a workspace holding unpushed commits, stash entries, or in-progress merge/rebase state"** — verified by reading and by 4 targeted unit tests (`test_in_progress_merge_is_dirty`, `test_stash_entry_is_dirty`, `test_unpushed_commit_on_clean_tree_is_dirty`, `test_d_only_unpushed_commit_is_dirty`, all part of the 13-passed run above). The merge/rebase and stash checks (`lifecycle.py:742-751`, `:811-815`) run before any content/untracked/ahead logic and short-circuit to `dirty` unconditionally. The `ahead` check (unchanged mechanism, `git log --branches --not --remotes`) still gates the D-only exception: `if content_diff_lines or not_ignored or ahead: dirty` — a D-only tree with unpushed commits still hits the `ahead` branch of that `or`.
- **"do not reduce false preservation by extending `_HARNESS_NOISE_BASENAMES` or any other basename whitelist"** — the whitelist was deleted in full (old `lifecycle.py:731`, gone; `spawn.py`'s re-export line also removed), replaced by `_workspace_untracked_not_ignored()` calling `git check-ignore` against each repo's own `.gitignore`. This is removal, not extension. `test_untracked_file_not_on_old_basename_whitelist_is_dirty` regression-guards that a former whitelist entry (`__pycache__`) is dirty again unless the repo's own `.gitignore` says otherwise.
- **"do not add a deletion path that skips the dry-run report"** — `_delete_workspace()` and its two call sites (`roster_clean()`, `auto_sweep()`) sit outside this diff's hunk ranges (the diff stops at line 819, well before `_delete_workspace` at ~line 859). `spawn.py clean --dry-run` printed its full candidate list with per-workspace reasons before the summary line in my own run above.
- **"do not weaken the predicate for a live session's workspace"** — the `live` and `unknown` (issue #2603) short-circuits (`lifecycle.py:800-808`) are unchanged from `main` and sit above all of this PR's new logic, outside the diff's hunk ranges entirely.

Population measurement (the issue's 5th acceptance line, "preserved-workspace
count drops against the live workspace population"): both the post-fix run
above and a separate pre-fix run (worktree at `5c0cc599`, this same host,
minutes apart — not back-to-back) diffed by candidate name:

```
$ diff <(pre-fix names, sorted) <(post-fix names, sorted)
29d28
< on-the-record-issue-2961-adversarial-review-fb462020
```

Pre-fix: 71 preserved. Post-fix: 70 preserved. The single delta is exactly
one workspace name disappearing between the two non-back-to-back runs —
`spawn.py clean --dry-run` deletes nothing, so this is the population
itself changing between measurements on a live, shared host, not the
predicate reclassifying anything. This is the identical "timing-artifact"
shape PR #2965's own record names and excludes. Every remaining preserved
entry in both runs cites a genuine reason (`[미추적 파일 N건]`, `[내용 변경
N건]`, `[미push 커밋 N건]`), never a bare "미커밋" catch-all — consistent
with the predicate correctly identifying nothing removable on this
specific host's current population (self-checkout workspaces with
untracked report folders and normal in-flight commits), and consistent
with PR #2965's separately-reported 69→69 back-to-back result: on this
Linux host shape, "correct but yields zero delta" and "broken" are hard
to tell apart from the count alone, and only the per-entry reason
breakdown (which I inspected directly, not just the totals) distinguishes
them.

## Why

derived: per the loaded `defect-verification-independence-from-upstream-verdicts` skill, a settled-looking claim is a claim to re-derive, not cite. The task asked me not to trust the PR's own results, so every acceptance command was re-run from a freshly fetched worktree rather than read off the PR body, and the diff was read against the issue's must-not list clause by clause rather than accepting the PR's own "audited and validated" framing at face value. This drove re-running the population measurement myself (rather than citing PR #2965's number outright) and specifically checking whether the evidence file PR #2963's body cites is actually reachable from PR #2963's own branch, rather than accepting the citation as given.

## What did not work

None.

## Upstream basis

- `docs/issue-2960/reports/test-derivation+silent-failure-audit-ccd3b998.md` (untracked on this record's own branch — it lives only on PR #2963's branch at `71fdf5757a4a17853819d6bc77b671d06a15d938`, fetched and read in full there this session) — sha: 71fdf5757a4a17853819d6bc77b671d06a15d938
- `lifecycle.py`, `spawn.py`, `tests/test_workspace_clean_state_predicate.py` (all at `71fdf5757a4a17853819d6bc77b671d06a15d938`; the test file is untracked on this record's own branch, present only on the PR branch, read and executed in full from the fetched PR branch this session) — sha: 71fdf5757a4a17853819d6bc77b671d06a15d938

## Open findings

1. **PR #2963's own body cites an evidence file that is untracked from PR #2963's own branch — it does not exist there, in `main`, or anywhere except a separate, independently-based sibling PR.** PR #2963's Test-plan bullet for `spawn.py clean --dry-run` states "0 -> 0 removed, 69 -> 69 preserved ... confirmed by an empty diff of the two candidate lists ... see `docs/issue-2960/reports/test-derivation-8718eaa7.md` for the full commands/output" (that path is untracked on both PR #2963's branch and `main` — verified this session). checked: `git show main:docs/issue-2960/reports/test-derivation-8718eaa7.md` and the equivalent path inside the fetched PR #2963 worktree — result: does not exist in either. The file exists only on PR #2965 (`issue-2960/test-derivation-8718eaa7`, head `366ae75c439973c2e78fc9cf624b4773625969c8`), which is based on `main` at `5c0cc599` — a sibling branch, not a commit stacked on or merged into PR #2963. checked: `git merge-base` of the two fetched PR branches — result: `5c0cc599...`, their common ancestor is the pre-fix commit; neither branch contains the other's work. PR #2965's own deviation log (`docs/issue-2960/reports/test-derivation-8718eaa7/deviation-log/20260901T014555550025-9d145be8840217e5.md`, untracked on this record's own branch, present only on PR #2965's branch, read in full there this session) discloses why: that session's harness identity sidecar was bound to its own branch, the repo's `approval-gate` hook refused a direct write onto PR #2963's branch, so it used `gh pr edit 2963` to inject the numbers into #2963's body from outside instead of landing the evidence file as a commit on #2963 itself. The log states plainly that "the numbers live in a sibling PR's record rather than as a commit on PR #2963's own branch" — a disclosed, reasoned deviation, not a hidden one, and I independently reproduced a comparable measurement myself (see `## What was done`) so the underlying number is not fabricated. But taken as a standalone unit — which is exactly what "fetch its head into an isolated worktree" produces, and what would happen if #2963 merges before or without #2965 — PR #2963's body makes a specific, citable claim its own branch cannot back up. Resolution path: merge #2965 together with (or before) #2963, or add a one-line note to #2963's body making the cross-PR dependency explicit, so the citation does not go stale if #2965 is closed or rebased independently.
2. **Carried from PR #2963's own record, re-derived by reading rather than cited.** None of the git subprocess calls added or touched by this predicate (`_workspace_in_progress_merge`, `_workspace_untracked_not_ignored`, plus the pre-existing stash/status/ahead calls) check `returncode` before treating empty/absent stdout as "nothing there" — a workspace whose `.git` is corrupted or hits a transient permission/disk error would read as fully clean. checked: `lifecycle.py:742-751` (`_workspace_in_progress_merge`, on the PR branch) reads `r.returncode != 0` only to return `False` (no merge in progress), never routing to `"unknown"`; `_workspace_untracked_not_ignored` (`lifecycle.py:759-770`) reads `.stdout` on both the `git ls-files` and `git check-ignore` calls with no returncode check at all. This is upstream's own disclosed open finding, untracked on this record's own branch (present only in PR #2963's own added report, "Open findings" section) — I re-derived it by reading the same lines directly this session rather than citing the upstream record's wording, and it holds. It does not block this PR: it requires an actual git-command failure to trigger (not exercised by any of this host's 70 live workspaces, all of which returned normally this session), it is a pre-existing pattern in this same function predating this fix (the `ahead`/`stash` calls already had the identical shape before this PR), and fixing it changes the default for command *failure* uniformly across the function — a separate, broader follow-up, correctly scoped out of "ask what would be lost" rather than folded in.

## Next steps

None — loop_state is terminal.

acceptance: `python3 -m pytest tests/ -k workspace_clean_state -q; python3 -m pytest tests/ -k d_only_pushed -q; grep -n "check-ignore" lifecycle.py; python3 spawn.py clean --dry-run | tail -1` — result:
```
13 passed in 0.97s
1 passed in 0.89s
756:    화이트리스트 대신 `git check-ignore` 로 판정 — 그 리포 자신의
766:        ["git", "-C", str(w), "check-ignore", "-z", "--stdin"],
정리 끝 — 지움 0, 남김 70
```

All 4 of issue #2960's acceptance-check commands were independently
re-executed against PR #2963's fetched head this session, each returning
results matching the PR's own claimed counts, and the diff was read in
full against the issue's must-not list with no violation surfacing. The
one open finding that concerns PR #2963 specifically (finding 1 above) is
a process/citation gap, not a functional or safety defect in the
predicate itself, and does not block merging PR #2963 on its own
technical merits — it only means the "empty diff of candidate lists"
detail should not be treated as independently reachable evidence until
PR #2965 also lands.

skill-verdict: adversarial-review — applied: invoked; this session's
structural independence from PR #2963's builder session already
satisfies the skill's core mechanism (fresh context, no shared reasoning
trail), so no further evaluator session was spawned — the skill's
procedure was applied directly as the adversarial mindset for this
verification: re-deriving rather than reading, checking whether cited
evidence actually resolves, and treating the PR's own "audited and
validated" framing as a claim to test rather than a fact to repeat.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; drove re-running every acceptance check from a fresh worktree instead of citing the PR body's claimed output, re-deriving the population measurement myself instead of citing PR #2965's number outright, and specifically checking whether #2965's cited evidence file is actually reachable from #2963 rather than accepting the PR body's citation at face value.
other mounted skills: not triggered (work-in-english is guidance-only
per this session's directive stack, enforced by hook rather than invoked
via the Skill tool; this record was written in English throughout).
