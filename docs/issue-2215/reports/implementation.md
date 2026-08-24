---
issue: 2215
role: implementation
loop_state: landed
upstream:
  - path: issue #2215 (GitHub, canonical: gh issue view 2215)
    sha: 57eb9b39d531ad76cf33748b9a6f37c442397216
code_under_review:
  - checkpoint.py
  - watchdog.py
  - roster.py
  - tests/test_workspace_checkpoint.py
type: feat
breaking: none
verdict: pass
---

# issue-2215 — implementation record

## What was done

canonical: commit 57eb9b39 (this branch, `git show --stat 57eb9b39`).

Added harness-decided checkpointing for role workspaces, plus the
dirty-tree health signal the issue asks for, per its Acceptance section:

- **`checkpoint.py`** (new, root-level, pure workspace-path functions — no
  dependency on spawn's mutable state, so it is imported bare rather than
  through the `_sp` compat shim the extracted modules use):
  - `checkpoint_workspace(work)` — snapshots every dirty file (tracked +
    untracked) in `work` onto a private ref
    `refs/checkpoints/<branch>`. Tracked changes come from `git stash
    create` (builds a commit object without touching the worktree, index,
    or the stash list — that is `create`, not `push`/`save`). Untracked
    files are staged into a throwaway `GIT_INDEX_FILE`-backed index (the
    real index is never touched) based on the stash's own tree, then
    folded in via `commit-tree` as a two-parent commit `[HEAD, stash]`.
    Returns `{"ref", "commit", "dirty_files"}`; on a clean tree returns
    `{"ref": None, "commit": None, "dirty_files": 0}` and creates no ref
    (empty-state contract).
  - `checkpoint_health(work)` — the two fields the health line needs:
    `dirty_files` (raw `git status --porcelain` count, independent of
    whether a checkpoint has fired) and `minutes_since_checkpoint` (age of
    the checkpoint ref's own commit, `None` if no ref exists yet).
  - `cleanup_checkpoint_ref(work)` — deletes the checkpoint ref via
    `update-ref -d` (never touches HEAD/branch/index); no-op-true when
    nothing to delete.
- **`watchdog.py`**: `roster_watchdog()`'s existing live-entry loop (the
  same 60s `POLL_INTERVAL_SEC` tick that already scans every roster entry
  every tick — canonical: `watchdog.py:1404` `roster_watchdog()`) now
  calls `checkpoint.checkpoint_workspace(work)` unconditionally for every
  live entry — the harness-decided, agent-independent trigger the issue
  asks for. `diagnose_health()` (canonical: `watchdog.py:215`) now
  computes `checkpoint.checkpoint_health(work)` once per call and merges
  `dirty_files`/`minutes_since_checkpoint` into every returned dict at
  every return site, including the `state: None` completion branch, so
  callers get a uniform shape regardless of which health state is hit.
- **`roster.py`**: `roster_remove()` (canonical: `roster.py:136`) now
  reads the popped entry's `work` before releasing the roster lock and
  calls `checkpoint.cleanup_checkpoint_ref(work)` outside the lock (the
  cleanup only touches the workspace's own git state, not the roster
  file, so there is no reason to hold the roster lock for it) — this is
  the one removal path every roster-disposal call site already funnels
  through (canonical: `grep -n "roster_remove(" *.py`), so no call site
  needed to change.
- **`tests/test_workspace_checkpoint.py`** (new, the issue's named gate,
  landed in commit 57eb9b39): tests against real git repo fixtures
  (mirrors the existing `_init_git_repo` pattern from
  `tests/test_watchdog_local_signals.py`) — empty state, tracked+untracked
  capture with before/after HEAD/branch/index equality, untracked-only
  capture, kill-mid-edit destructive-loss recovery, ref cleanup (including
  via `roster_remove`), and `diagnose_health()` surfacing both fields for
  a live entry. canonical: `pytest tests/test_workspace_checkpoint.py -v`
  — result printed verbatim in section 7 below.

Design decision not to touch each spawned role session's own hooks.json:
the issue offered two options ("A PostToolUse hook on Edit|Write ... **or**
a dura-style poller", canonical: gh issue view 2215, "Ask" section).
Wiring a new hook into every role's per-session plugin/settings merge
(`spawn.py`'s `--settings` isolation machinery, canonical: `spawn.py:8-13`)
would touch a much larger, isolation-sensitive surface for no added
correctness — `roster_watchdog()` already visits every live workspace
unconditionally every 60s, which is the harness-decided property the
issue actually wants ("correctness does not depend on the role session
remembering anything", canonical: gh issue view 2215, "Ask" section). The
poller reuses that existing tick rather than adding a second one.

## Why

The issue's own survey (canonical: gh issue view 2215, "The pattern, from
the landscape" section) ranks dura as "closest existing design to what we
need" (polls, commits to a private ref, never touches HEAD/branch/index)
and separately states "60+ hooks are already wired; the infra exists"
(canonical: gh issue view 2215, "Ask" section) only as evidence that *a*
hook-based path is technically available, not as an instruction to use it.
Given `roster_watchdog()` already runs an unconditional per-tick sweep
over every live roster entry (the same loop `diagnose_health()` is called
from), hanging the checkpoint call off that loop satisfies
"harness-decided and unconditional" with the smallest possible change,
and keeps the two asks (checkpoint + health signal) reading from and
writing to the same per-tick data rather than two independently-timed
mechanisms that could drift apart.

## What did not work

- First `checkpoint_workspace()` implementation based the throwaway index
  used to fold in untracked files on `HEAD`'s tree rather than the `git
  stash create` commit's tree — this silently dropped tracked-file
  modifications whenever both tracked and untracked changes were dirty at
  once. canonical: this session's own `pytest` run against the
  pre-fix code —
  `test_captures_tracked_and_untracked_leaves_head_branch_index_unchanged`
  asserted the committed tracked-file content and got the
  pre-modification content back instead (see section 8 below for the
  exact assertion output). Fixed by reading `<stash_sha>^{tree}` (falling
  back to `HEAD`'s tree only when there is no stash, i.e. untracked-only
  dirt) as the throwaway index's base before adding untracked files.

## Upstream basis

Issue #2215 (GitHub), read via `gh issue view 2215` at the start of this
session (canonical: gh issue view 2215) — no prior docs/issue-2215/
content existed before this session; the record skeleton itself was
pre-written per issue #2135 and is filled in here.

## Open findings

None.

## Next steps

None — `loop_state: landed` (terminal for a `coding-record` per contract
v3's per-kind table). The build-now bypass (`CORE_BUILD_NOW=1` in this
session's environment) applied, so this record and the code land together
in one PR with no proposal round.

## Acceptance evidence (executed-live, per the issue's `provenance:` field)

All commands below were run against real git repositories (a throwaway
`/tmp` fixture for the destructive kill/recovery demo, since it required
discarding a working tree — never the role workspace this session itself
runs in) with real, unedited output.

### 1. Kill mid-edit → recovery from the checkpoint ref

```
$ git init -q -b issue-9999/implementation && git commit -q -m init  # tracked.txt = "original"
=== before edit: git status / HEAD / branch ===
e6a0ab930821bcd5a2419a12f4dd8a9361c1576a
issue-9999/implementation

$ echo "in-flight edit" > tracked.txt; echo "in-flight new file" > untracked.txt
=== dirty tree (simulating a role session mid-edit) ===
 M tracked.txt
?? untracked.txt

=== checkpoint fires (harness tick) ===
{
  "ref": "refs/checkpoints/issue-9999/implementation",
  "commit": "88886db50541f0de69c1495acdf91d536a8bda2f",
  "dirty_files": 2
}

=== simulate the session getting killed: uncommitted work is destroyed ===
$ git checkout -- tracked.txt && git clean -fd
untracked.txt 제거
$ cat tracked.txt
original
$ ls untracked.txt
ls: 'untracked.txt'에 접근할 수 없음: 그런 파일이나 디렉터리가 없습니다

=== recovery: restore the tree from the checkpoint ref ===
$ git checkout refs/checkpoints/issue-9999/implementation -- .
--- tracked.txt after recovery ---
in-flight edit
--- untracked.txt after recovery ---
in-flight new file
```

### 2. Checkpointing leaves branch/HEAD/index unchanged

```
=== after checkpoint: HEAD / branch / status unchanged? ===
e6a0ab930821bcd5a2419a12f4dd8a9361c1576a
issue-9999/implementation
 M tracked.txt
?? untracked.txt
```
(identical to the before-checkpoint values above)

```
=== recovery did not move HEAD/branch either ===
e6a0ab930821bcd5a2419a12f4dd8a9361c1576a
issue-9999/implementation
```

### 3. Untracked files captured (not just tracked)

Shown in scenario 1: `untracked.txt` (never `git add`ed) was recovered
byte-for-byte from the checkpoint ref after `git clean -fd` deleted it.

### 4. Health line: dirty-file count + minutes-since-checkpoint

```
=== empty state ===
{'dirty_files': 0, 'minutes_since_checkpoint': None}
=== dirty, no checkpoint yet ===
{'dirty_files': 2, 'minutes_since_checkpoint': None}
after checkpoint: {'dirty_files': 2, 'minutes_since_checkpoint': 0.00463643471399943}
```

### 5. Empty state: no ref created on a clean tree

Covered by the same demo above (`{'dirty_files': 0,
'minutes_since_checkpoint': None}` on a freshly-committed, untouched
repo) and by `TestCheckpointWorkspaceEmptyState` in the gate, which also
asserts `git show-ref` output contains no `refs/checkpoints` line.

### 6. Checkpoint refs cleaned up at session end

```
=== ref exists before cleanup ===
present
cleanup_checkpoint_ref -> True
=== ref after cleanup ===
gone
=== HEAD/branch still untouched ===
e6a0ab930821bcd5a2419a12f4dd8a9361c1576a
issue-9999/implementation
```

Refs never leak into pushes/PRs by construction: `refs/checkpoints/...`
is outside `refs/heads/`, and `git push -u origin <branch>` (the only push
shape role sessions use, per contract v3) never touches an unnamed ref —
no separate suppression was needed.

### 7. Gate: `tests/test_workspace_checkpoint.py`

canonical: `python3 -m pytest tests/test_workspace_checkpoint.py -v` — run
in this session, verbatim result below.

```
$ python3 -m pytest tests/test_workspace_checkpoint.py -v
...
[gw6] [ 11%] PASSED tests/test_workspace_checkpoint.py::TestCleanupCheckpointRef::test_cleanup_on_clean_tree_is_noop
[gw8] [ 22%] PASSED tests/test_workspace_checkpoint.py::TestDiagnoseHealthSurfacesCheckpointFields::test_clean_live_entry_reports_zero_and_none
[gw0] [ 33%] PASSED tests/test_workspace_checkpoint.py::TestCheckpointWorkspaceEmptyState::test_clean_tree_no_ref_created
[gw3] [ 44%] PASSED tests/test_workspace_checkpoint.py::TestCleanupCheckpointRef::test_cleanup_deletes_ref_without_touching_head
[gw1] [ 55%] PASSED tests/test_workspace_checkpoint.py::TestCheckpointWorkspaceCapture::test_captures_tracked_and_untracked_leaves_head_branch_index_unchanged
[gw2] [ 66%] PASSED tests/test_workspace_checkpoint.py::TestCheckpointWorkspaceCapture::test_untracked_only_still_captured
[gw4] [ 77%] PASSED tests/test_workspace_checkpoint.py::TestKillMidEditRecovery::test_recovery_after_destructive_loss
[gw5] [ 88%] PASSED tests/test_workspace_checkpoint.py::TestDiagnoseHealthSurfacesCheckpointFields::test_live_entry_reports_dirty_and_minutes
[gw7] [100%] PASSED tests/test_workspace_checkpoint.py::TestCleanupCheckpointRef::test_roster_remove_cleans_up_checkpoint_ref

9 passed in 1.05s
```

### 8. What-did-not-work reproduction (before the fix)

canonical: this session's own `pytest` run against the pre-fix
`checkpoint.py`, verbatim assertion output below.

```
AssertionError: 'original\n' != 'modified\n'
- original
+ modified
```
(`test_captures_tracked_and_untracked_leaves_head_branch_index_unchanged`,
before basing the throwaway index on `<stash_sha>^{tree}`.)

### 9. Regression sweep

canonical: `python3 -m pytest ...` — run in this session against the four
watchdog-signal test files and the five larger spawn-gate/board/observation
suites, verbatim results below.

```
$ python3 -m pytest tests/test_watchdog_local_signals.py tests/test_watchdog_freshness.py \
    tests/test_watchdog_heartbeat_noise.py tests/test_poll_watchdog_log.py -q
28 passed in 1.11s

$ python3 -m pytest tests/test_spawn_gate_wiring.py tests/test_standing_red_watch.py \
    tests/test_watch_hardening.py tests/test_spawn_board_flows.py \
    tests/test_spawn_observation_recovery.py -q
2 failed, 400 passed, 3 xfailed, 2 xpassed in 454.31s (0:07:34)
```

The 2 failures
(`test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace`,
`test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch`)
are pre-existing and unrelated to this change. canonical: re-ran both with
`checkpoint.py`/`watchdog.py`/`roster.py`/the new test file stashed out
(`git stash push -u -- checkpoint.py watchdog.py roster.py
tests/test_workspace_checkpoint.py`) in this session — same two tests
failed, same assertion diffs (`AssertionError: Lists differ: [11, 22] !=
[22]` for the board-flows failure), confirming both predate this change.

## skill-verdicts

skill-verdict: implementation-blueprint — applied: invoked; ran `classify
--surface backend --external no --logic transform --asynchronous no`
(routed to archetype `pipeline`) and `recommend pipeline --team 1` before
writing `checkpoint.py`, to check its three-function shape (one nameable
job each, no shared mutable state, no premature abstraction) against the
gate's anti-patterns (mega-stage, speculative-generality) — no
restructuring needed, module already satisfied it.

other mounted skills (implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice): not triggered — no
coupling/cohesion metric crossed a threshold, no GoF-pattern indirection
decision, and no data-structure/algorithm choice with a performance-cliff
risk was in scope for this change.
