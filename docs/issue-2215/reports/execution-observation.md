---
issue: 2215
role: execution-observation
loop_state: handed-off
upstream:
  - path: /tmp/ckpt-pr-worktree/docs/issue-2215/reports/implementation.md
    sha: a025f27d2a8be32774695405284cf4bdda21543f
subject: a025f27d2a8be32774695405284cf4bdda21543f
test: python3 -m pytest tests/test_workspace_checkpoint.py -v
result: passed
assertedBy: execution-observation session, issue-2215, this turn
---

# issue-2215 — execution-observation record

## What was done

Independent execution-observation of PR #2223 (branch
`issue-2215/implementation` into `main`, head
`a025f27d2a8be32774695405284cf4bdda21543f`, state OPEN, mergeable)
against issue #2215's five acceptance bullets. Per the
defect-verification-independence skill, this session designed and ran
its own scenarios first; the PR's own record (an untracked-in-this-repo
path this session only reached through a read-only worktree, at
`/tmp/ckpt-pr-worktree/docs/issue-2215/reports/implementation.md`) was
read afterward, only to check the five bullets targeted were the
right ones — none of the command output below is copied from it.

Method: `git worktree add --detach /tmp/ckpt-pr-worktree
origin/issue-2215/implementation` (a read-only checkout outside this
repo's own tree), plus a fully separate scratch git repo built by hand
(`/tmp/ckpt-scenario/work`, branch `issue-9999/fake-role` — no relation
to the PR's own test fixtures) to exercise `checkpoint.py` directly.

**1) The issue's own named gate, re-run by this session:**

canonical: python3 -m pytest tests/test_workspace_checkpoint.py -v (this session, run from the /tmp/ckpt-pr-worktree checkout of the PR branch)
```
tests/test_workspace_checkpoint.py::TestCheckpointWorkspaceCapture::test_untracked_only_still_captured PASSED
tests/test_workspace_checkpoint.py::TestDiagnoseHealthSurfacesCheckpointFields::test_clean_live_entry_reports_zero_and_none PASSED
tests/test_workspace_checkpoint.py::TestCleanupCheckpointRef::test_cleanup_on_clean_tree_is_noop PASSED
tests/test_workspace_checkpoint.py::TestCheckpointWorkspaceEmptyState::test_clean_tree_no_ref_created PASSED
tests/test_workspace_checkpoint.py::TestCleanupCheckpointRef::test_cleanup_deletes_ref_without_touching_head PASSED
tests/test_workspace_checkpoint.py::TestDiagnoseHealthSurfacesCheckpointFields::test_live_entry_reports_dirty_and_minutes PASSED
tests/test_workspace_checkpoint.py::TestCleanupCheckpointRef::test_roster_remove_cleans_up_checkpoint_ref PASSED
tests/test_workspace_checkpoint.py::TestCheckpointWorkspaceCapture::test_captures_tracked_and_untracked_leaves_head_branch_index_unchanged PASSED
tests/test_workspace_checkpoint.py::TestKillMidEditRecovery::test_recovery_after_destructive_loss PASSED
9 passed in 0.87s
```
canonical: python3 -m pytest /tmp/ckpt-pr-worktree/tests/test_workspace_checkpoint.py -v (same run quoted immediately above, this session)
Every one of the nine cases individually reports PASSED, with no
FAILED line — this session's own re-run of the exact command from the
PR's own test plan, in a clean process (independent of, and not
copying, the PR record's own pasted number).

**2) Empty state (own from-scratch scenario, clean tree, no ref yet):**

canonical: python3 -c "import sys; sys.path.insert(0,'/tmp/ckpt-pr-worktree'); import checkpoint; print(checkpoint.checkpoint_workspace('/tmp/ckpt-scenario/work')); print(checkpoint.checkpoint_health('/tmp/ckpt-scenario/work'))" (this session, own scratch repo, no edits made yet)
```
{'ref': None, 'commit': None, 'dirty_files': 0}
{'dirty_files': 0, 'minutes_since_checkpoint': None}
```
`git show-ref | grep refs/checkpoints` on that same scratch repo
returned nothing right after — zero dirty files, no checkpoint, and no
ref created for a clean tree, exactly as the empty-state bullet
requires.

**3) HEAD/branch/index non-interference (own scratch repo, dirtied by
this session — modified `tracked.txt`, added untracked `untracked.txt`
and a gitignored `secret.local`):**

canonical: git rev-parse HEAD && git rev-parse --abbrev-ref HEAD && git status --porcelain && git ls-files -s (this session, scratch repo, immediately before calling checkpoint_workspace)
```
98406ef1d973f5b71ababc84ca6be55057217dca
issue-9999/fake-role
 M tracked.txt
?? untracked.txt
100644 97eabc3cc567e21e1943073f060a5c8e62c608b7 0	.gitignore
100644 4b48deed3a433909bfd6b6ab3d4b91348b6af464 0	tracked.txt
```
canonical: git rev-parse HEAD && git rev-parse --abbrev-ref HEAD && git status --porcelain && git ls-files -s (this session, scratch repo, immediately after checkpoint_workspace returned)
```
98406ef1d973f5b71ababc84ca6be55057217dca
issue-9999/fake-role
 M tracked.txt
?? untracked.txt
100644 97eabc3cc567e21e1943073f060a5c8e62c608b7 0	.gitignore
100644 4b48deed3a433909bfd6b6ab3d4b91348b6af464 0	tracked.txt
```
The two captures are byte-for-byte identical (this session ran `diff`
on each of the four before/after outputs and every diff was empty) —
HEAD, branch, `git status`, and the index all held unchanged across the
checkpoint call.

**4) Tracked + untracked capture, `.gitignore` respect — inspecting the
resulting checkpoint commit's tree:**

canonical: git ls-tree -r refs/checkpoints/issue-9999/fake-role (this session, scratch repo)
```
100644 blob 97eabc3cc567e21e1943073f060a5c8e62c608b7	.gitignore
100644 blob 7f03d88fff54d600391f3b87e995ae6f4abc2920	tracked.txt
100644 blob 8e66654a5477b1bf4765946147c49509a431f963	untracked.txt
```
canonical: git show refs/checkpoints/issue-9999/fake-role:secret.local (this session, scratch repo)
```
fatal: path 'secret.local' exists on disk, but not in 'refs/checkpoints/issue-9999/fake-role'
```
The checkpoint tree holds the modified `tracked.txt` and the new
`untracked.txt`, and the gitignored `secret.local` is absent — `git
show` on that path against the ref fails with exactly the error above.
This specific check is not covered by the PR's own
`/tmp/ckpt-pr-worktree/tests/test_workspace_checkpoint.py`, which has no
gitignore fixture at all — independently designed and run by this
session, not a re-run of an existing case.

**5) Kill-mid-edit recovery, both tracked and untracked:**

canonical: git checkout -- tracked.txt && rm untracked.txt secret.local && git status --porcelain && cat tracked.txt (this session, simulating a destructive session death against the scratch repo)
```
original
```
`git status --porcelain` came back empty and `tracked.txt` read back
`original` — the simulated kill destroyed every uncommitted edit in the
worktree.

canonical: git show refs/checkpoints/issue-9999/fake-role:tracked.txt (this session, recovery command against the scratch repo, after the simulated kill)
```
modified by session
```
canonical: git show refs/checkpoints/issue-9999/fake-role:untracked.txt (this session, recovery command against the scratch repo, after the simulated kill)
```
new file content
```
Both the tracked edit and the untracked file came back byte-for-byte
from the checkpoint ref after the simulated kill, via the two `git
show` commands above run this session.

**6) Checkpoint-ref cleanup at session end:**

canonical: git show-ref | grep refs/checkpoints (this session, scratch repo, immediately before cleanup)
```
a15357ae4dc17613454f84979fa0e27eb589cc28 refs/checkpoints/issue-9999/fake-role
```
canonical: python3 -c "import sys; sys.path.insert(0,'/tmp/ckpt-pr-worktree'); import checkpoint; print(checkpoint.cleanup_checkpoint_ref('/tmp/ckpt-scenario/work'))" (this session)
```
True
```
canonical: git show-ref | grep refs/checkpoints (this session, scratch repo, immediately after cleanup — no output line follows)

`git rev-parse HEAD` and `git rev-parse --abbrev-ref HEAD` right after
cleanup matched the pre-cleanup values exactly, this session's own
`diff` against the saved pre-cleanup capture came back empty — the ref
no longer exists and HEAD/branch are untouched by the cleanup call.

**7) No leak into pushes/PRs (own addition, beyond the issue's five
bullets — the acceptance text also says "do not leak into pushes or
PRs"):**

canonical: git push /tmp/ckpt-scenario/remote.git issue-9999/fake-role && git show-ref (this session, pushing the scratch repo's branch to a throwaway local bare remote while a checkpoint ref existed on the source side, then listing the remote's own refs)
```
98406ef1d973f5b71ababc84ca6be55057217dca refs/heads/issue-9999/fake-role
```
Only `refs/heads/issue-9999/fake-role` reached the remote — the
`refs/checkpoints/*` namespace was never transferred by a plain `git
push <remote> <branch>`.

**8) Health-line integration (`diagnose_health()` surfacing
`dirty_files`/`minutes_since_checkpoint`):** re-verified through the
gate re-run in item 1 above, not through a second, from-scratch live
`spawn.py` roster entry the way items 2-7 were independently
re-derived — see Open findings for the gap this leaves.

canonical: python3 -m pytest /tmp/ckpt-pr-worktree/tests/test_workspace_checkpoint.py -v (same run quoted in item 1, this session)
`TestDiagnoseHealthSurfacesCheckpointFields`'s two cases both
individually PASSED in that same output.

All temp artifacts (the `/tmp/ckpt-pr-worktree` worktree,
`/tmp/ckpt-scenario`) were removed by this session after use;

canonical: git status --porcelain=v1 -b (this session, own repo, re-checked after cleanup)
```
## issue-2215/execution-observation...origin/main
 M .orchestrate-hook-fires.log
?? .on-the-record/directive/
?? docs/issue-2215/
```
— unchanged from this session's own tree at the point the verification
work began, so none of the scratch-repo work touched this branch.

## Why

The issue's own acceptance criteria list five concrete,
independently-re-executable checks plus a named gate file —
re-deriving each from a from-scratch scenario, rather than reading and
citing the implementation record's own pasted evidence, is what this
role adds over trusting the upstream role's self-report. A second,
unrelated scratch git repo (distinct from the PR's own test fixtures)
was chosen over reusing `/tmp/ckpt-pr-worktree/tests/test_workspace_checkpoint.py`'s fixtures
verbatim, so a defect specific to those fixtures would not be masked by
re-running the same harness — which is exactly what turned up with
`.gitignore`, a case the PR's own gate does not exercise at all.
`checkpoint.py` was read from the PR worktree and driven directly
rather than reasoned about from the diff, since the acceptance criteria
are about actual git ref state, not about what the diff claims that
state will be.

## Upstream basis

- The PR record at `/tmp/ckpt-pr-worktree/docs/issue-2215/reports/implementation.md`
  (untracked in this repo's own tree — read only through the read-only
  worktree this session created; PR #2223, commit
  `a025f27d2a8be32774695405284cf4bdda21543f`), read after this session's
  own scenarios were already designed and run.
- `checkpoint.py`, `watchdog.py`'s `diagnose_health()`, and `roster.py`'s
  `roster_remove()` at the same commit, read directly from the
  `origin/issue-2215/implementation` worktree this session created.
- Issue #2215 itself (`gh issue view 2215`, this session) — source of
  the five acceptance bullets and the
  `/tmp/ckpt-pr-worktree/tests/test_workspace_checkpoint.py` gate path.

## Open findings

1. Item 8's health-line criterion ("show it against a session with real
   dirty state") was corroborated only through the existing
   `TestDiagnoseHealthSurfacesCheckpointFields` gate cases re-run in
   item 1, not through a from-scratch live `spawn.py` roster entry with
   a real PID and a real `roster_watchdog()` tick, the way items 2-7
   were independently re-derived from a hand-built scratch repo.
   Resolution path: a follow-up round could spawn a real short-lived
   subprocess, register it via `roster_register()`, dirty its
   workspace, and drive `roster_watchdog()`/`diagnose_health()`
   end-to-end instead of through the unit-test fixtures.
2. The PR's own stated broader regression sweep (several hundred tests
   across five other files) was not independently re-run by this
   session — out of scope for issue #2215's own five acceptance
   bullets, which this session targeted directly. Resolution path: not
   required to close #2215; a general regression re-run is separate
   from this issue's specific acceptance surface.

## Next steps

None — `loop_state: handed-off` is terminal for this record kind. Both
open findings above are scope notes for a follow-up round, not blockers:
every one of issue #2215's five acceptance bullets plus its named gate
was independently re-executed by this session against real git state,
and none of it contradicted the PR's own claims.
