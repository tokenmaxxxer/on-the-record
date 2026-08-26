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

## before-landing — stance: does merge_gate.py's new unconditional check_runner.fetch_all_role_branches(repo) call in evaluate() have a bad interaction with any existing caller/test?

Verdict: FINDING — evaluate()'s new unconditional, unmocked fetch_all_role_branches(repo) call breaks the test suite's own documented "no network" invariant: two pre-existing gates/test_merge_gate.py tests call `merge_gate.evaluate(Path("."), Path("."), ...)` (repo = the real developer/CI checkout) and only monkeypatch the three higher-level functions (`latest_check_runner_comment`, `required_verification_missing`, `stale_revert_reasons`) — never `subprocess.run` or `check_runner.fetch_all_role_branches` — because until this change `evaluate()` made no subprocess calls of its own before reaching those three mocked functions. Now it does: every run of these tests performs a real, unmocked `git fetch --prune origin +refs/heads/*:refs/remotes/origin/*` against the actual `origin` remote (real GitHub), over the network, and prunes/updates the developer's real local `origin/*` remote-tracking refs as a side effect of running a unit test. The module docstring of gates/test_merge_gate.py explicitly states these regression tests run "네트워크·gh 없이" (without network/gh) via synthetic repos and mocking — this invariant is now silently false for two of its tests. In a network-restricted CI/sandbox (no egress), `git fetch` here has no timeout set on the subprocess.run call in fetch_all_role_branches, so instead of the fast, deterministic, network-free unit test these were designed to be, they can hang or become flaky depending on DNS/connection-refused timing; evaluate() ignores the fetch's return value entirely ("best-effort"), so a fetch failure is masked rather than surfaced, but a fetch *hang* is not masked — it just makes the test suite hang.
Kind: composition
Seed: gates/merge_gate.py evaluate() diff (added `check_runner.fetch_all_role_branches(repo)` as its first statement)
cap_seconds: (not specified by dispatcher)
tier: (not specified by dispatcher)
diff_stat_lines: gates/merge_gate.py +14, on-the-record/directive/merge-gates.md (doc), docs/issue-2381/reports/implementation.md (record)
started_at: 2026-08-26T03:00:00Z
ended_at: 2026-08-26T03:08:00Z

### Reproduce
```
cd gates && python3 -c "
import subprocess, sys
from pathlib import Path
sys.path.insert(0, '.')
import merge_gate

orig = subprocess.run
calls = []
def spy(*a, **k):
    calls.append(a[0] if a else k.get('args'))
    return orig(*a, **k)
subprocess.run = spy

# exactly what gates/test_merge_gate.py::t_merge_gate_evaluate_refuses_no_checks_as_a_pass
# and t_full_sequence_reaches_allow_merge_once_every_precondition_holds do: monkeypatch
# only the three higher-level functions, call evaluate() with repo=Path('.')
merge_gate.latest_check_runner_comment = lambda repo, pr: '## Acceptance check-runner result: 1/1 passed\n\n- [PASS] x'
merge_gate.required_verification_missing = lambda root, subject, repo=None, pr=None: []
merge_gate.stale_revert_reasons = lambda repo, pr: []

result = merge_gate.evaluate(Path('.'), Path('.'), 999, 'issue-999')
print('RESULT', result)
for c in calls:
    print('CALL', c)
"
```

### Observed
```
RESULT {'allowed': True, 'reasons': []}
CALL ['git', 'fetch', '--prune', 'origin', '+refs/heads/*:refs/remotes/origin/*']
```
This is a real subprocess call (confirmed separately: `time git fetch --prune origin "+refs/heads/*:refs/remotes/origin/*"` against this repo's actual `origin` = `https://github.com/tokenmaxxxer/on-the-record.git` succeeds in ~0.5s and mutates real local `origin/*` refs) — i.e. running `python3 -m pytest gates/test_merge_gate.py` now performs live network I/O against GitHub and prunes local remote-tracking refs, despite the file's own docstring claiming these tests run without network.

### Expected
`evaluate()`'s new fetch should not fire when running against a test harness that never asked for network access — e.g. it should be injectable/mockable at the same seam the existing tests already use (so `t_merge_gate_evaluate_refuses_no_checks_as_a_pass` and `t_full_sequence_reaches_allow_merge_once_every_precondition_holds` stay network-free the way the module docstring says they are), or the fetch should be skippable when the three higher-level functions are already monkeypatched past the point where a real origin ref would ever be read. As written, calling `merge_gate.evaluate()` against any real repo checkout (not just the intended orchestrator `--repo` checkout) now always shells out to `git fetch` against `origin` first, unconditionally and unmocked, regardless of caller intent.

### Fix applied
The seam already exists (`evaluate()` calls `check_runner.fetch_all_role_branches(repo)`, and `gates/merge_gate.py` already does `import check_runner` at module scope), so no new injection point was needed. Both affected tests now stub it: `monkeypatch.setattr(check_runner, "fetch_all_role_branches", lambda repo: None)` added immediately before the existing three monkeypatches in `t_merge_gate_evaluate_refuses_no_checks_as_a_pass` (`gates/test_merge_gate.py`) and `t_full_sequence_reaches_allow_merge_once_every_precondition_holds` (same file) — same pattern the rest of the suite already uses to keep `evaluate()` network-free.

acceptance: `python3 -m pytest gates/test_check_runner.py gates/test_merge_gate.py tests/test_verdict_gate.py -q` — result:
```
73 passed in 1.59s
```
(re-run after the fix; no `git fetch` subprocess call observed for the two previously-affected tests when re-run individually with the reproduce script above and `check_runner.fetch_all_role_branches` monkeypatched the same way)
