---
proposal: N/A — CORE_BUILD_NOW=1 bypassed the proposal round (role protocol v3 s19a); delivery record is docs/issue-2381/reports/implementation.md
---

# Hunt record — orchestrator-fetch-all-branches

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — `fetch_all_role_branches()`'s wildcard mirror fetch exits 0 even when `origin/<head_ref>` no longer exists on the remote, leaving a stale local `origin/<head_ref>` ref untouched (no `--prune`); `checkout_pr_worktree()` then happily checks that stale ref out with no error, contradicting its own docstring's "에러는 항상 fail-closed로 다뤄진다" guarantee — the gate silently runs checks against deleted/stale branch content instead of refusing.
Kind: silent-failure
Seed: git diff 3b4da518 HEAD -- gates/check_runner.py (fetch_all_role_branches() extraction, replacing `git fetch origin <head_ref>` with `git fetch origin '+refs/heads/*:refs/remotes/origin/*'`)
cap_seconds: 180
tier: full (gates-path-touched override)
diff_stat_lines: gates/check_runner.py +21/-3, .gitignore +1, on-the-record/directive/merge-gates.md doc note
started_at: 2026-08-26T00:00:00Z
ended_at: 2026-08-26T00:12:00Z

### Reproduce
```
rm -rf /tmp/origin.git /tmp/clone1 /tmp/clone2 /tmp/wt
git init --bare /tmp/origin.git -q
git clone /tmp/origin.git /tmp/clone1 -q
cd /tmp/clone1 && git config user.email t@t.com && git config user.name t
git commit --allow-empty -m init -q && git push origin HEAD:refs/heads/main -q
git checkout -b issue-99/role -q && git commit --allow-empty -m branchcommit -q
git push origin issue-99/role -q

# orchestrator's persistent checkout fetches the branch once (as it would
# have on an earlier gate run against this same PR)
cd /tmp && git clone /tmp/origin.git /tmp/clone2 -q
cd /tmp/clone2 && git fetch origin '+refs/heads/*:refs/remotes/origin/*'
git rev-parse origin/issue-99/role   # records the old sha

# branch is now deleted on origin (PR closed / force-recreated / cleaned up)
cd /tmp/clone1 && git push origin --delete issue-99/role -q

# this is the exact command fetch_all_role_branches() runs in
# gates/check_runner.py — same cwd=repo, same argv
cd /tmp/clone2 && git fetch origin '+refs/heads/*:refs/remotes/origin/*'
echo "fetch exit=$?"                         # -> 0, "success"
git rev-parse origin/issue-99/role           # -> still resolves, unchanged sha (stale)

# checkout_pr_worktree()'s next step, worktree_for_ref(), against that stale ref
rm -rf /tmp/wt
git worktree add --detach /tmp/wt origin/issue-99/role
echo "worktree add exit=$?"                  # -> 0
```

### Observed
`git fetch origin '+refs/heads/*:refs/remotes/origin/*'` exits 0 after the
remote branch is deleted; `origin/issue-99/role` still resolves locally to
the old (now-nonexistent-on-remote) commit; `git worktree add --detach
/tmp/wt origin/issue-99/role` then also exits 0 and checks out that stale
commit with no error at any step. Translated into `check_runner.py`'s
control flow: `fetch.returncode` is 0 so the `f"origin fetch 실패: ..."`
branch is never taken, and `worktree_for_ref()` returns `(worktree_path,
None)` — `checkout_pr_worktree()` reports full success while the
worktree it produced does not correspond to any commit currently on
origin for that PR.

### Expected
Per `checkout_pr_worktree()`'s own docstring ("에러는 항상
fail-closed(호출부가 검사를 실행하지 않고 거부)로 다뤄진다"), a PR whose
head branch has vanished/moved on origin since the orchestrator's last
fetch should cause the gate to refuse (return an error) rather than
silently check out and run checks against stale content. The old
single-branch `git fetch origin <head_ref>` at least failed loudly
(`fatal: couldn't find remote ref <head_ref>`, exit 128) in the
branch-gone case; the new wildcard mirror fetch removed that signal
without replacing it (no `--prune`, no post-fetch verification that
`origin/<head_ref>`'s sha matches `gh pr view`'s reported `headRefOid`).

### Fix applied
`fetch_all_role_branches()` now runs `git fetch --prune origin
'+refs/heads/*:refs/remotes/origin/*'` (`gates/check_runner.py:410-412`,
this commit). Re-ran the exact repro above with `--prune` added to both
fetch invocations:

acceptance: repro above, `--prune` variant — result:
```
- [deleted]         (none)     -> origin/issue-99/role
fatal: 애매한 인자 'origin/issue-99/role': 알 수 없는 리비전 또는 작업 폴더에 없는 경로.
rev-parse exit=128
```

so `worktree_for_ref()`'s `git worktree add` on that ref now fails
closed again, restoring the pre-existing contract.

acceptance: `python3 -m pytest gates/test_check_runner.py -q` — result:
```
35 passed in 1.70s
```
