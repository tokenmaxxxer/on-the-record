---
proposal: PR #3086 (commit 80ff89f8, issue #3050 must-not B repair round)
---

# Hunt record — push-succeeded-derivation

## after-proposal — stance 1: `_push_succeeded()`'s exclusion tuple is still bypassable / a live path still exists where nothing-real-happened is classified as push success

Verdict: FINDING — `spawn._push_succeeded()`'s exclusion tuple omits `ensure_pushed()`'s `"issue-closed-stale-branch"` status, so a stale role branch that `ensure_pushed()` itself refuses to attach to any PR and explicitly flags "for cleanup" (relay.py's `_flag_stale_returned_branch`) is still derived as `push_succeeded=True`, keeping `fail_closed_downgrade()`'s outcome `"progressed"` for a round in which this session made no new commit.
Kind: design-error
Seed: PR #3086 commit 80ff89f8 — `spawn._push_succeeded()` (spawn.py:3763) excludes only `("push-rejected", "pr-create-failed", "nothing-to-push")` from `ensure_pushed()`'s seven possible `status` values (`nothing-to-push` / `pushed` / `push-rejected` / `pr-create-failed` / `pr-opened` / `pr-already-open` / `issue-closed-stale-branch`, per relay.py:194's own docstring).
canonical: spawn.py:3763-3775 (`_push_succeeded()` exclusion tuple), relay.py:194-282 (`ensure_pushed()`, status list at relay.py:202-209, `issue-closed-stale-branch` returned at relay.py:261), relay.py:160-172 (`_flag_stale_returned_branch()` docstring: "must never be re-opened as a PR or respawned — flag it for cleanup instead"), board.py:1358-1382 (`fail_closed_downgrade()`'s `progressed`/`push_succeeded` branch)
cap_seconds: not stated by dispatcher
tier: not stated by dispatcher
diff_stat_lines: 4 files changed, 172 insertions(+), 2 deletions(-) (commit 80ff89f8)
started_at: 2026-09-02T08:20:00Z
ended_at: 2026-09-02T08:45:00Z

### Reproduce
Checked out PR #3086's exact HEAD (commit `80ff89f8`) into a clean worktree:

```
git worktree add /tmp/audit-3086 80ff89f8
```

Then ran (against real scratch git repos, following the same pattern as the new `PushSucceededDerivationLiveTest` in `tests/test_failed_no_commit_reconcile.py` — real `spawn.ensure_pushed()`, real `spawn._push_succeeded()`, only `spawn._subject_issue_state` and `gh` are stubbed to force the issue-#2068 CLOSED-issue branch inside `ensure_pushed()`):

```python
import os, stat, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, "/tmp/audit-3086")
import board, spawn

FAKE_GH = """#!/usr/bin/env python3
import sys
argv = sys.argv[1:]
if argv[:3] == ["pr", "list", "--head"]:
    print("0")
else:
    sys.exit(1)
"""

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    bin_dir = tmp / "bin"; bin_dir.mkdir()
    p = bin_dir / "gh"; p.write_text(FAKE_GH); p.chmod(p.stat().st_mode | stat.S_IEXEC)

    origin = tmp / "origin.git"; work = tmp / "work"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True)
    subprocess.run(["git", "-C", str(work), "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", str(work), "config", "user.name", "t"], check=True)

    # Simulate a stale branch: content already pushed to origin in a PRIOR
    # round (this session's own before/after HEAD diff -- new_commit -- is
    # therefore False: no new commit happened *this* round).
    subprocess.run(["git", "-C", str(work), "checkout", "-q", "-b", "issue-30503/coding"], check=True)
    (work / "f.txt").write_text("x")
    subprocess.run(["git", "-C", str(work), "add", "f.txt"], check=True)
    subprocess.run(["git", "-C", str(work), "commit", "-q", "-m", "old work"], check=True)
    subprocess.run(["git", "-C", str(work), "push", "-q", "-u", "origin", "issue-30503/coding"], check=True)

    spawn._subject_issue_state = lambda root, issue: ("CLOSED", True)

    orig_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{bin_dir}:{orig_path}"
    try:
        push_result = spawn.ensure_pushed(str(work), 30503, "coding")
    finally:
        os.environ["PATH"] = orig_path

    print("push_result:", push_result)
    push_succeeded = spawn._push_succeeded(push_result)
    print("push_succeeded:", push_succeeded)

    outcome = board.fail_closed_downgrade(
        "progressed", 30503, [], False, [], False, push_succeeded)
    print("fail_closed_downgrade outcome:", outcome)
```

acceptance: `python3 /tmp/repro_stale.py` (script above, run against the `/tmp/audit-3086` worktree of commit `80ff89f8`) — result:
```
[stale-branch] issue #30503 is CLOSED — refusing to re-open a PR from returned branch issue-30503/coding; branch flagged for cleanup
push_result: {'status': 'issue-closed-stale-branch', 'reason': None}
push_succeeded: True
fail_closed_downgrade outcome: progressed
```

acceptance: `python3 -c "import spawn; print(spawn._push_succeeded({'status': 'issue-closed-stale-branch', 'reason': None}))"` (run inside `/tmp/audit-3086`) — result:
```
True
```

### Observed
`push_result` from the real `ensure_pushed()` call is `{'status': 'issue-closed-stale-branch', 'reason': None}`; the real `spawn._push_succeeded()` derives `True` from it; `board.fail_closed_downgrade("progressed", 30503, [], False, [], False, True)` returns `"progressed"` — see the acceptance transcripts above.

### Expected
`ensure_pushed()`'s own docstring for this status (relay.py:204) and `_flag_stale_returned_branch()`'s docstring (relay.py:160) both say the branch is refused a PR and "flagged for cleanup" — the code's own author treats it as not a legitimate delivery, the same shape as `"nothing-to-push"` which PR #3086 just excluded for exactly this reason ("that is not a successful push of nothing"). `_push_succeeded()` should exclude `"issue-closed-stale-branch"` alongside `"push-rejected"`, `"pr-create-failed"`, and `"nothing-to-push"`; instead it currently falls through the `not in (...)` check and is derived as `True`, so `fail_closed_downgrade()` keeps `"progressed"` for a round with `new_commit=False`, `uncommitted=[]`, `already_delivered=False` — no local evidence of new work in this round, and no open PR anywhere to point to as delivery, yet the round is not downgraded to `failed-no-commit`.
