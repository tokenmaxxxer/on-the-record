---
issue: 2139
role: merge-gates-a22bb8e4
author: merge-gates-a22bb8e4
skills: merge-gates (skill-repository(c05de12))
verifies_subject: false  # not a verification of another subject's deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
code_under_review: PR https://github.com/tokenmaxxxer/on-the-record/pull/2877 (branch issue-2139/silent-failure-audit-212d2fc6), rebased onto origin/main; conflict resolved in docs/reports/product/quality-bar.md; PR body's standing-invariants section corrected/extended
type: verification-record
breaking: false
verdict: rebased-and-pushed; PR #2877 mergeable/CLEAN; retirement-count invariant corrected from claimed decrease-of-12 (miscounted, unanchored exclude pattern) to actual decrease-of-47 with a plural-matching pattern; all four standing invariants re-run after the rebase and hold
upstream:
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/2877
    sha: 620123107eb0375f67922e87696386519f64ec7e
  - path: docs/issue-2139/reports/silent-failure-audit-212d2fc6.md (untracked in this working tree — lives on branch issue-2139/silent-failure-audit-212d2fc6, not merged to main)
    sha: 620123107eb0375f67922e87696386519f64ec7e
---

# issue-2139 — merge-gates-a22bb8e4 record

## What was done

canonical: `gh pr view 2877 --repo tokenmaxxxer/on-the-record` output (state: OPEN, mergeable: CONFLICTING before this session's work).

Two things, on PR #2877 (`issue-2139/silent-failure-audit-212d2fc6`, round 2 on PR #2869's relic sweep):

1. **Rebased PR #2877 onto current `origin/main` and pushed** — one conflict, in `docs/reports/product/quality-bar.md`, an append-only file where both `origin/main` (an unrelated 2026-08-30 entry on issue #2326) and this branch's own last commit (its issue #2139 round-2 entry) had appended a new bullet at the same location. Resolved by keeping both appended entries (main's first, this branch's second), not by taking either side wholesale. Force-pushed with `--force-with-lease` anchored to the branch's pre-rebase remote tip.
   derived: `git push origin HEAD:issue-2139/silent-failure-audit-212d2fc6 --force-with-lease=issue-2139/silent-failure-audit-212d2fc6:d8d6812e9e7ed22e5b6a59f22c143cba625b7e6f` — result: `d8d6812e...62012310 HEAD -> issue-2139/silent-failure-audit-212d2fc6 (forced update)`.
   canonical: `gh pr view 2877 --repo tokenmaxxxer/on-the-record --json mergeable,mergeStateStatus` (after push, re-checked once GitHub finished recomputing) — result: `{"mergeStateStatus":"CLEAN","mergeable":"MERGEABLE"}`.
   Before resolving, checked whether the conflict was a role-to-skill rename collision (this window on `main` carried several — PR #2887, #2882, #2889 all landed between this branch's merge-base and `origin/main`): compared the pre-rebase PR-branch copy, the merge-base copy, and `origin/main`'s copy of every file the rebase touched. `on-the-record/directive/delegation-loops.md`'s two content lines that differ from `origin/main` (`"the matching skill's skill loaded"`, `spawn.py --skills <skill> ... --no-wait`) are byte-identical between the pre-rebase PR-branch tip and the post-rebase result — confirmed via a direct diff, not merely a clean rebase — so the rebase carried this PR's own pre-existing wording through unchanged, neither reverting a subsequent rename nor double-applying one.
   derived: `diff <(git show origin/main:on-the-record/directive/delegation-loops.md) on-the-record/directive/delegation-loops.md` inside the rebased worktree, and separately `git show origin/issue-2139/silent-failure-audit-212d2fc6:on-the-record/directive/delegation-loops.md | sed -n '10,18p;68,76p'` against the pre-rebase remote tip — both show the same two lines, confirming no revert/double-apply.

2. **Recounted the retirement-count invariant and corrected it.** The exclude filter in the original recipe, `grep -vE '/(test|docs)/'`, requires a leading slash before "test"/"docs"; `grep -rl`'s own output over `.` has no leading slash on top-level paths (confirmed: top hits come back as bare `directive_assembly.py`, or a top-level directory name followed by a slash, never `./`-prefixed), so top-level test and docs directories were never excluded — inflating the sum with exactly the population the invariant meant to exclude, plus this round's own new report files. The pattern was also `\brole\b`, a word-boundary match that does not match the plural "roles" (no boundary exists between "e" and "s").
   derived: `grep -rln '역할\|\brole\b' --include=*.py --include=*.md . | grep -vE '/(test|docs)/' | xargs -I{} grep -c '역할\|\brole\b' {} | awk -F: '{sum+=$1} END {print sum}'` on `origin/main` — result: 19128 (buggy pattern, shown for reference only — not used in any conclusion below).
   Corrected pattern — anchors the exclude on `(^|/)` so it matches both top-level and nested test/docs directories, and matches the plural via `roles?`:
   `grep -rln '역할\|\broles\?\b' --include=*.py --include=*.md . | grep -vE '(^|/)(test|docs)/' | xargs -I{} grep -c '역할\|\broles\?\b' {} | awk -F: '{sum+=$1} END {print sum}'`
   derived: same command, run in a worktree of `origin/main` — result: 897.
   derived: same command, run in the rebased PR-branch worktree (post-rebase HEAD, sha `620123107eb0375f67922e87696386519f64ec7e`) — result: 850.
   897 − 850 = 47 — the corrected, real decrease. `gates/retirement_count.py` (untracked in this working tree — not yet on `origin/main`, PR #2881 is still open) was not used or cited for this count.
   canonical: `gh pr view 2881 --repo tokenmaxxxer/on-the-record --json state -q .state` — result: OPEN.

Both the rebase and the recount are reflected in PR #2877's own description (`gh pr edit 2877 --body-file ...`, appended a "Rebase note" section rather than rewriting the original author's words) — full commands and outputs for all four re-run invariants are below.

## Why

The task was explicit: rebase PR #2877 onto current `main` without changing what it does, and separately fix an unreliable count discovered by an independent re-derivation (PR #2880) of this branch's own retirement-count recipe. Landing PR #2877 on a stale base risked masking a real conflict as a clean fast-forward (the merge-gates skill's step 5: textual mergeability is not a substitute for the gate); rebasing onto the actual current `origin/main` and re-running all four standing invariants against the combined state, rather than trusting the pre-rebase numbers, is the skill's step 3 (combined-state) applied literally.

skill-verdict: merge-gates — applied: invoked; used step 3 (require the rebase to run against the actual combined state, not the branch's own stale base) and step 5 (a clean/CLEAN merge state is an input, never itself the gate — re-ran all four invariants post-rebase rather than trusting the pre-rebase PR body).

skill-verdict: work-in-english — applied: invoked; this record, the rebase conflict resolution, the commit messages, and the PR body edit are all in English; only the final chat summary to the user is in Korean.

skill-verdict: prose-modes — applied: invoked; this is a decision-record-shaped document (R1: reader is an expert in this specific codebase and round, so density stays low and inferences are left rather than spelled out; R9: each command and its output is stated once, not restated).

## What did not work

None.

## Upstream basis

- `docs/issue-2139/reports/silent-failure-audit-212d2fc6.md` (untracked in this working tree — lives on branch `issue-2139/silent-failure-audit-212d2fc6`, sha `620123107eb0375f67922e87696386519f64ec7e` post-rebase, content unchanged from the pre-rebase commit that introduced it) — the round-2 record whose PR body carried the retirement-count claim being corrected here.
- PR https://github.com/tokenmaxxxer/on-the-record/pull/2877 (sha `620123107eb0375f67922e87696386519f64ec7e`) — the rebase-and-recount target; its own commits (functional fixes) were not altered, only rebased, and its PR description extended.

## Standing invariants (all four, re-run after the rebase, this session)

Invariant 1 — no return of the retired role axis, in any reshaped form, plural included:
derived: `grep -rln '역할\|\broles\?\b' --include=*.py --include=*.md . | grep -vE '(^|/)(test|docs)/' | xargs -I{} grep -c '역할\|\broles\?\b' {} | awk -F: '{sum+=$1} END {print sum}'` — `origin/main`: 897; this branch (post-rebase): 850 — decreased by 47.

Invariant 2 — no new bug, failing-test set vs `origin/main` as SETS OF NAMES, via `pytest .` from the repo root:
derived: `python3 -m pytest . -q` on both `origin/main` and the rebased branch — `origin/main`: 17 failed, 630 passed, 3 xfailed in 32.78s; branch: 17 failed, 634 passed, 3 xfailed in 33.08s.
derived: `diff <(grep '^FAILED' main_pytest.log | sort) <(grep '^FAILED' branch_pytest.log | sort)` — empty diff, 17 lines each, SETS IDENTICAL.

Invariant 3 — no overhead increase:
derived: `wc -c on-the-record/directive/delegation-loops.md` — branch (post-rebase): 7983 bytes; `origin/main`: 7986 bytes. No increase (branch is 3 bytes smaller than the current `origin/main`, which itself grew independently of this PR since the 7983-byte baseline #2869/#2873 recorded).

Invariant 4 — monitor and watch machinery unbroken and not quieter:
derived: `python3 -m pytest test/test_watchdog_heartbeat_noise.py test/test_ps_live_reliability.py -q` — branch (post-rebase): 10 passed in 0.88s; `origin/main`: 10 passed in 0.86s. Same pass count on both trees — not quieter.

## Open findings

None — PR #2877 is rebased, pushed, and mergeable/CLEAN; its own three functional fixes were not altered. The three higher-stakes findings PR #2877's own upstream commit ("relic sweep batch") reported but did not fix (lifecycle.py lease-key mismatch, dead-path directive references, dead-code/rename-coordination bundle) remain open in that commit's own message, unchanged by this session — out of scope here ("do not change what it does").

## Next steps

None — `loop_state: landed`. PR #2877 is ready to merge as-is (mergeable, invariants hold); this session's own record and its edit to PR #2877's description are the full deliverable.
