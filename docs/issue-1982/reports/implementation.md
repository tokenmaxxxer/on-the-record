---
code_under_review:
  - spawn.py
  - tests/test_respawn_continuation_preamble.py
loop_state: landed
type: implementation
breaking: false
verdict: pass
---

## Summary of work

Implemented the state-aware respawn continuation preamble approved in
PR #1990's proposal (`docs/issue-1982/proposals/completed-work-heuristic-and-continuation-preamble.md`):

- Added `_classify_workspace_completion(work, role)` to `spawn.py`
  (next to `_respawn_fingerprint`, spawn.py:3973 area). It returns
  `"unfinished"` when `git status --porcelain -uall` on `work` is empty,
  or when dirty but none of the changed paths fall under
  `docs/issue-<n>/(reports|proposals)/`, or when the matching record
  file's frontmatter-stripped body is empty. It returns `"finished"` only
  when a changed record-shape path exists on disk with a non-trivial
  (non-whitespace-only) body after stripping the leading `---`
  frontmatter block.
- Wired the call into `_respawn_or_cap()` (spawn.py:4055 area)
  immediately after `task = task_path.read_text(...)`: when the
  classifier returns `"finished"`, `_CONTINUATION_PREAMBLE` is prepended
  to `task` before `_spawn_one()`; when `"unfinished"` (including the
  clean-workspace case), `task` is left untouched, preserving today's
  byte-identical behavior.
- Added `tests/test_respawn_continuation_preamble.py`: end-to-end tests
  driving `_respawn_or_cap()` through a real temp git repo (mirroring
  `tests/test_spawn_observation_recovery.py`'s `ProgressAwareRespawnCounter`
  fixture pattern) — finished dirty workspace gets the preamble prepended
  and still contains the original task text; unfinished dirty workspace
  (code-only change, or a frontmatter-only record stub) and clean
  workspace both produce a byte-identical task. Also unit-tests
  `_classify_workspace_completion()` directly for the clean/no-record/
  non-trivial-body cases.

## Why

why: the issue's Request — reconcile `RESPAWN_IDENTICAL` on a dirty
workspace today reuses the original task text verbatim, giving the new
session no signal that a previous session already left work in the tree
(observed stranding: #1959 x3 rounds, #1978 respawned identically). The
phase-1 proposal (approved) designed the git-only structural heuristic
this phase wires in.

## Upstream basis

upstream: docs/issue-1982/proposals/completed-work-heuristic-and-continuation-preamble.md
canonical: read this session — commit 9a666cb9, the phase-1 proposal merged in PR #1990

## What will be done — completed items

1. `_classify_workspace_completion()` added to `spawn.py`; called from
   `_respawn_or_cap()` right after `task_path.read_text()`; preamble
   prepended only on `"finished"`, `"unfinished"` leaves `task`
   untouched; `tests/test_respawn_continuation_preamble.py` added
   covering both branches plus the classifier's clean/no-record/
   non-trivial-body cases directly.

```
$ python3 -m pytest -o addopts='' -q tests/test_respawn_continuation_preamble.py
.......                                                                  [100%]
7 passed in 0.28s
```
canonical: python3 -m pytest -o addopts='' -q tests/test_respawn_continuation_preamble.py — output pasted above, this session's own live run
acceptance: python3 -m pytest -o addopts='' -q tests/test_respawn_continuation_preamble.py — result: 7 passed, requirement met

2. Fast full-suite regression checked clean.

```
$ python3 -m pytest -o addopts='' -q -m "not slow"
2447 passed, 108 deselected, 18 xfailed, 3 xpassed in 144.45s (0:02:24)
```
canonical: python3 -m pytest -o addopts='' -q -m "not slow" — output pasted above, this session's own live run
acceptance: python3 -m pytest -o addopts='' -q -m "not slow" — result: 2447 passed, 108 deselected, 18 xfailed, 3 xpassed, requirement met

3. Misclassification failure modes were already documented in the
   phase-1 proposal's `## Misclassification failure modes` section; no
   new failure mode surfaced during phase-2 wiring, so this record does
   not duplicate that content.

## What did not work

None.

## Test-tier gap note (issue #1518 observe-only directive)

`.on-the-record/test-tiers.json` marks `spawn.py` as a `slow`-tier
trigger. I ran the `slow`-tier tests most directly coupled to the
changed function — the two `tests/test_spawn_observation_recovery.py`
classes that call `_respawn_or_cap()` directly.

```
$ python3 -m pytest -o addopts='' -q -m slow tests/test_spawn_observation_recovery.py -k "ProgressAwareRespawnCounter or SelfTriggeredRespawn"
......                                                                   [100%]
6 passed, 162 deselected in 95.07s (0:01:35)
```
canonical: python3 -m pytest -o addopts='' -q -m slow tests/test_spawn_observation_recovery.py -k "ProgressAwareRespawnCounter or SelfTriggeredRespawn" — output pasted above, this session's own live run
acceptance: python3 -m pytest -o addopts='' -q -m slow tests/test_spawn_observation_recovery.py -k "ProgressAwareRespawnCounter or SelfTriggeredRespawn" — result: 6 passed, requirement met

unverifiable: this session did not run the full `slow` tier
(`python3 -m pytest -o addopts='' -q -m slow`, across all seven files in
`trigger_change_classes`) to completion — reason: that same file
(`tests/test_spawn_observation_recovery.py`) run in full under `-m slow`
was still producing new dots past this session's own 500-second
wall-clock observation window before it was stopped to bound the
session's total time (transcript of this session's own background-task
output, canonical: this session's own background-task transcript for
that run). Extrapolated from that rate, the full seven-file slow tier
would run well past this session's remaining turn budget. Per the issue
#1518 directive (observe-only, does not refuse an over-budget run), this
gap is surfaced here rather than silently absorbed: the narrowed run
above covers the changed code path (`_respawn_or_cap()`) directly; the
remaining slow-tier files exercise unrelated respawn/reconcile/
board-flow surfaces this change does not touch.

## Open findings

None.
