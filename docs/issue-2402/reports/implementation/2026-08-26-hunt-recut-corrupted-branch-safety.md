---
proposal: docs/issue-2402/reports/implementation.md
---

# Hunt record — recut-corrupted-branch-safety

## after-proposal — stance 1: probe the new `spawn.py recut-corrupted` path (issue-2402, PR #2446, commit f7398a96) for silent-failure/composition/design-error defects in `_recut_corrupted_branch`, `recut_corrupted_cli`, and the watchdog print-string extension

Verdict: NO FINDING
Seed: `git show f7398a96` — spawn.py `_recut_corrupted_branch` (new), pipeline.py `recut_corrupted_cli` (new), spawn.py CLI dispatch for `recut-corrupted`, watchdog.py per-PR mapping-failure print string (text-only extension), merge-gates.md new bullet
cap_seconds: unspecified (no dispatcher cap communicated in prompt)
tier: default
diff_stat_lines: 447 insertions(+), 2 deletions(-) total across 5 files (pipeline.py +51, spawn.py +38/-1, watchdog.py +5/-1, merge-gates.md +25, docs/issue-2402/reports/implementation.md +329 new)
started_at: 2026-08-26T00:00:00Z
ended_at: 2026-08-26T01:00:00Z

Tested all four specific concerns against a disposable local `git` sandbox
(bare `origin.git` + clone, outside this repo, `/tmp/rc-demo*`):

1. **`git checkout -B br origin/br` and uncommitted local changes**: built a
   workspace on `issue-9/role` with an uncommitted tracked-file edit, then
   ran the exact checkout the new function runs. When origin/br's tip
   equals the local tip, the edit survives (ordinary non-destructive
   checkout). When origin/br has diverged in the same file (simulating a
   stale local ref), `git checkout -B` **refuses** ("로컬 변경 사항을
   체크아웃 때문에 덮어 쓰게 됩니다... 중지함", exit 1) rather than
   silently discarding anything — `-B` only force-resets the branch
   *pointer*, it does not add `-f` to the working-tree checkout, so git's
   ordinary conflict-safety net still applies. `_recut_corrupted_branch`
   propagates that returncode (`if checkout.returncode != 0: return
   checkout`) and `recut_corrupted_cli` turns it into a printed error +
   exit 1. The premise in `_recut_absorbed_branch`'s stash comment (about
   `checkout -B` failing on *untracked*-file path conflicts) is a
   different, already-loud failure mode, not a silent-discard one — I
   confirmed a real untracked/uncommitted conflict is always a loud `git`
   error here, never a silent win.

2. **`git rebase --onto base <old_merge_base> br` when `old_merge_base ==
   base` already**: built a normal (non-corrupted) branch, computed
   `merge-base(br, base)` == base's tip, ran the exact rebase — confirmed
   safe no-op (`현재 브랜치 issue-9/role는 최신 상태입니다`, exit 0), no
   crash, no data loss, branch tip and content unchanged.

3. **`git push --force-with-lease` staleness**: bare `--force-with-lease`
   (no explicit `<ref>:<expect>`) keys off the remote-tracking ref that
   the immediately-preceding `fetch_br` call just updated — this is
   force-with-lease working as designed, not a TOCTOU bug; a genuinely
   concurrent push in the race window is exactly the case
   force-with-lease is built to reject rather than clobber.

4. **Silent returncode-swallowing across the call chain**: read
   `recut_corrupted_cli` end to end — every subprocess call
   (`fetch origin br`, `fetch origin base`, `_recut_corrupted_branch`,
   `push --force-with-lease`) has its returncode checked and, on failure,
   both prints to stderr and returns 1; `main()`'s `sys.exit(main())`
   propagates that as the process exit code. Also manually reproduced a
   genuine rebase *conflict* (both branches edit the same line) to see
   what happens on retry in the same workspace after a failed attempt:
   the repo is left mid-rebase-with-conflict (as any interactive `git
   rebase` would), and a second `checkout -B br origin/br` in that same
   state fails loudly too ("현재 인덱스를 먼저 해결해야 합니다... needs
   merge", exit 1) — not silent, though it does require manual
   `git rebase --abort`/resolution of that workspace before reuse; this
   is standard git-conflict UX, not a defect this diff introduced, and
   the caller reports it as a hard failure both times rather than
   pretending success.

None of the four flagged concerns reproduce a wrong-output defect; `git`'s
own working-tree safety checks (no `-f` used anywhere in the new code)
cover the case the stash-diff comparison against `_recut_absorbed_branch`
seemed to suggest was uncovered.
