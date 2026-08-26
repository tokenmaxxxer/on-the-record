---
issue: 2447
role: implementation
author: implementation
loop_state: landed
upstream: []
code_under_review:
  - lifecycle.py
  - spawn.py
type: feat
breaking: "none — additive third prune trigger inside auto_sweep(); the
  existing age-bound and size-bound passes run unchanged for every
  workspace the new merge-trigger declines to touch, and auto_sweep()'s
  public signature/return shape ({removed, failed}) is unchanged, pinned
  by the full pre-existing auto_sweep/clean regression suite staying
  green"
verdict: pass
---

# issue-2447 — implementation record

## What was done

Added a merge-triggered prune path to `lifecycle.py`'s `auto_sweep()`
(issue #1179/#2383's spawn-time workspace sweep), additive to the existing
age(14d)/size(5GiB) bounds:

- New `_workspace_merge_trigger_status(w)` in `lifecycle.py`: for a
  workspace that `_workspace_clean_state()` already classified as safe
  (non-live, non-dirty — the same #1124 safety gate `roster_clean()` and
  `auto_sweep()` share), resolves the workspace's current branch and asks
  whether its PR's state via the existing `_pr_list_call_ok()`/
  `_merged_pr_for_branch()` helpers (`lifecycle.py`/`board.py`, already
  used by `_post_session_end_comment()`) is the GitHub `MERGED` state.
  Returns `(True, "PR #N merged")` only when the PR list is in that
  state; every other outcome (no branch, `gh` call itself failing, PR
  open/absent) returns `False` — ambiguity always degrades to "not yet",
  never to a delete.
- `auto_sweep()` now runs three independent triggers over the same
  already-safe candidate set, in this order: merge-trigger (new) → age
  bound → size bound. A workspace the merge-trigger declines to remove
  falls straight through to the pre-existing age/size logic, untouched by
  this change — the `gh` check is a pure add-on, never a precondition for
  the existing bounds.
- Per-workspace removal log lines are now tagged with the trigger that
  fired (`merge-triggered` / `age-triggered` / `size-triggered`), and the
  sweep's final summary line reports a per-trigger breakdown
  (`지움 N (merge X, age Y, size Z)`), answering Acceptance bullet 4 —
  `auto_sweep()`'s previous log output only ever reported failures
  per-item and an undifferentiated total.
- `spawn.py` re-exports the new `_workspace_merge_trigger_status` name
  (alongside its sibling `_workspace_*` re-exports) so it patches the same
  way every other lifecycle-cluster function does (`mock.patch.object(spawn,
  "_workspace_merge_trigger_status", ...)`), per this module's established
  `_sp`-indirection convention.

No new module, no new CLI flag, no new env var — the issue's own
`design-research-skip: mechanical` framing (extends the existing #2383/
#2411 prune mechanism with a third trigger condition) held up; this is a
~90-line addition inside the existing function plus one re-export line.

derived: lifecycle.py:971-1066 (this session's diff — `_workspace_merge_trigger_status`
and the three-trigger `auto_sweep()` body), spawn.py:414 (the new re-export line)

## Why

Workspaces are session-scoped: once a PR lands, there is nothing left in
the checkout worth protecting, but the existing sweep only ever asked
"how old is it" and "how much space is left" — a workspace whose PR
reaches the `MERGED` state seconds after its session ends still had to
wait for the 14-day age bound (or an unrelated size-pressure event)
before its ~121MB/~12,400 inodes were reclaimed. This directly
contributed to a live inode-exhaustion recurrence with several concurrent
sessions running (per the issue text, `gh issue view 2447`).

The merge-trigger is layered on top of the *existing* safety gate
(`_workspace_clean_state()`) rather than replacing or duplicating it, per
the issue's validity-consult constraint ("gated on session ended AND PR
[reaching the `MERGED` state]... must degrade gracefully if the GitHub
API check fails"): reusing the same non-live/non-dirty candidate set
`auto_sweep()` already computes means the merge-trigger can never remove
a workspace the age/size logic wouldn't already consider a safe-to-delete
candidate — it only changes *when* a safe candidate gets removed, not
*whether* it's safe. Reusing `_pr_list_call_ok()` (already used by
`_post_session_end_comment()` to tell "no PR" apart from "couldn't
check") rather than inferring the same thing from `_merged_pr_for_branch()`'s
`None` return keeps the API-failure and not-yet-merged cases
distinguishable, which is exactly what the graceful-degradation
requirement needs — `_merged_pr_for_branch()` alone returns `None` for
both cases and can't tell them apart on its own.

derived: board.py:520-557 (`_pr_open_or_merged_for_branch`/`_merged_pr_for_branch`),
lifecycle.py:251-260 (`_pr_list_call_ok`), lifecycle.py:598-649
(`_workspace_clean_state`)

## What did not work

None.

## Upstream basis

None — self-contained extension of the existing #1179/#2383 auto-sweep
mechanism; the issue's own `design-research-skip: mechanical` note states
this is a mechanical addition, not a new design, and delivery ran under
the build-now bypass (`CORE_BUILD_NOW=1`), which skips the proposal round
for this session.

## Acceptance evidence (executed live, this session, 2026-08-26)

All four synthetic-fixture checks below use isolated `tempfile.mkdtemp()`
work directories (mirroring `gates/test_clean_reconcile_safety.py`'s
existing `AutoSweepTest` fixtures) and `mock.patch.object(spawn, ...)` on
`_pr_list_call_ok`/`_merged_pr_for_branch` in place of live `gh` network
calls — the same mocking seam the pre-existing test suite for this
function already uses.

**Bullet 1 — a workspace whose session ended and whose PR reached the
`MERGED` state gets removed well inside the 14d/5GiB bounds (before/after):**

canonical:
```
before: True
[auto-sweep] 지움 (merge-triggered): on-the-record-issue-100-implementation (PR #4242 merged)
[auto-sweep] 지움 1 (merge 1, age 0, size 0)
auto_sweep result: {'removed': 1, 'failed': 0}
after: False
```

Workspace mtime was 1 hour old (`max_age_days=14`, `max_bytes=5GiB`) —
removed immediately by the merge-trigger, nowhere near either existing
bound.

**Bullet 2 — an unmerged or in-progress workspace is never removed by the
new trigger regardless of age (two sub-cases, both 40 days old with
`max_age_days=9999` so age-bound cannot explain a removal):**

canonical:
```
=== live session, PR mocked as MERGED-state ===
auto_sweep result: {'removed': 0, 'failed': 0}
still exists: True

=== ended session, PR mocked as open/no-PR (None) ===
auto_sweep result: {'removed': 0, 'failed': 0}
still exists: True
```

A still-live session is left in place regardless of its PR's state
(`_workspace_clean_state()`'s "live" reason wins before the merge-trigger
is even consulted); an ended session whose PR has not reached `MERGED` is
left untouched by the new trigger even at 40 days old with age-bound
disabled.

**Bullet 3 — a GitHub API failure degrades the new trigger to a no-op for
that workspace; the existing age/size prune still fires on schedule:**

canonical:
```
[auto-sweep] 지움 (age-triggered): on-the-record-issue-103-implementation
[auto-sweep] 지움 1 (merge 0, age 1, size 0)
auto_sweep result: {'removed': 1, 'failed': 0}
removed via age bound despite API failure: False
```

`_pr_list_call_ok` mocked to return `False` (forced API failure);
`_merged_pr_for_branch` mocked to raise `AssertionError` if called at all
(it must not be, once the call-ok check already failed) — the workspace
(30 days old, `max_age_days=14`) still gets removed, but tagged
`age-triggered`, showing the API failure never touched the pre-existing
age-bound path.

**Bullet 4 — prune log output distinguishes the removal trigger:** shown
inline in bullets 1 and 3 above — every per-workspace removal line now
carries a `(merge-triggered|age-triggered|size-triggered)` tag, and the
sweep summary breaks the total down by trigger. A fourth run (size-bound
path, `gh` call also forced to fail via the same mock, to show the size
path is independently unaffected too) exercises the third label:

canonical:
```
[auto-sweep] 지움 (size-triggered): on-the-record-issue-1-implementation
[auto-sweep] 지움 1 (merge 0, age 0, size 1)
result: {'removed': 1, 'failed': 0} w1 exists: False w2: True w3: True
```

**Bullet 5 — live demonstration against the real current backlog**
(read-only; see the note below for why no destructive sweep was run
against shared state):

canonical:
```
$ python3 -c '<read-only scan using spawn._workspace_clean_state() and
  spawn._workspace_merge_trigger_status(), no _delete_workspace calls>'

scanned 31 workspaces in 1.72s (read-only, no deletions performed)
  merge-removable now (would be swept immediately by the new trigger): 0
  kept (live or dirty, unaffected by new trigger): 30
  safe but not-yet-merged (untouched by new trigger, fall back to age/size): 1
```

**Full regression sweep — no other prune path shifted:**

canonical:
```
$ python3 -m pytest gates/test_clean_reconcile_safety.py tests/test_auto_sweep_nonblocking.py -q
17 passed, 1 xfailed in 1.23s

$ python3 -m pytest <46 test_*.py files touching spawn/lifecycle/board, listed
  in full in the shell history of this session> -q
1 failed, 508 passed, 9 xfailed, 1 xpassed in 39.09s
```

The one failure, `test_flag_appends_checkpoint_block` in
`tests/test_checkpoint_mode.py`, reproduces identically on a `git stash`
of this session's diff (pre-change tree) — a live `gh issue view 7`
lookup inside that test's own fixture failing, unrelated to
`auto_sweep`/prune.

**Live backlog measurement note (Bullet 5):** `$MUSTER_WORKSPACE_ROOT`
currently holds 31 git-checkout workspaces shared with other concurrently
running sessions (per the issue's own "9 sessions ran" context, `gh issue
view 2447`). Actually invoking `auto_sweep()`'s delete path against that
shared, live backlog would be a destructive, hard-to-reverse action
against other sessions' state, so this scan only called the read-only
classification helpers (`_workspace_clean_state()`,
`_workspace_merge_trigger_status()`) — no `_delete_workspace()` call ran
against real data. Per the canonical fence above (Bullet 5), the large
majority of the scanned workspaces are dirty (other sessions'
in-progress work), and the single safe candidate found
(`on-the-record-issue-999998-livecheck2`, an unrelated leftover fixture
from an earlier #2417 disk-check hunt, per its own git log) has no real
PR, so it stays untouched by the new trigger — the real backlog happens
to hold no naturally-occurring "session-ended, PR-reached-MERGED" case at
scan time. The synthetic fixtures in bullets 1-4 above are what exercise
the actual before/after inode-occupancy improvement; this scan instead
shows the classification logic runs correctly and cheaply (1.72s,
canonical fence above) over the real backlog without disturbing it.
Measured numbers: **before** — bounded only by the 14-day age check (or
an unrelated 5GiB size-pressure event) once a workspace goes
dirty-to-clean-and-`MERGED`; **after** — bounded by the next spawn's
background `auto_sweep()` pass, which this scan's canonical fence above
shows finishing in under 2 seconds for the current backlog size, not up
to 14 days.

## Open findings

None.

## Next steps

None — terminal (`loop_state: landed`).

skill-verdict: work-in-english — applied: invoked; new lifecycle.py/
board.py docstrings and comments were kept Korean to match the existing,
heavily-Korean surrounding style in those exact functions (this skill's
own project-convention-conflict guard), while the commit message, PR
title/body, and this record's prose are written in English; this
session's final chat summary is written in Korean per the skill's routing
rule.
skill-verdict: implementation-blueprint — not-applicable: mechanical
third-trigger addition inside one already-established function
(`auto_sweep()`), reusing existing cross-module helpers as-is — no new
module boundary or structural decision to freeze.
skill-verdict: implementation-complexity-coupling-management — not-applicable:
no coupling/cohesion metric crossed, no new accessor chain, no new
cross-module import direction (the new function calls the same
`board.py`/`lifecycle.py` helpers `_post_session_end_comment()` already
calls the same way).
skill-verdict: implementation-design-pattern-selection — not-applicable:
no GoF-pattern introduction/removal decision — a guard function plus one
more independent trigger branch in an existing loop.
skill-verdict: implementation-performance-data-structure-choice — not-applicable:
no data-structure/algorithm/communication-scheme choice; the one added
`gh` call per already-safe candidate mirrors the existing per-workspace
`git status`/`git log` calls the same loop already makes, not a new
per-message-connection pattern.
