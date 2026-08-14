---
code_under_review:
  - on-the-record/monitors/poll-heartbeat.sh
  - tests/test_spawn.py
type: fix
breaking: false
# canonical: python3 -m pytest tests/test_spawn.py -k 'monitor or heartbeat or roster' -q (executed this turn; 48 passed, 0 skipped) — basis for verdict below.
verdict: pass
loop_state: landed
---

Subject: issue-1292

## Summary of work

Demoted the #1275 non-git `exit 1` in
`on-the-record/monitors/poll-heartbeat.sh` to the same sweep-exclusion/
dormancy path #1282 already built for the non-board case: the tick loop
now always runs regardless of git status, the arm-root is excluded from
`_board_wide_sweep_all`'s sweep when non-git (folded into the existing
`is_board` computation, which is forced to 0 whenever `is_git=0`), and
the alive marker (workspace-keyed hash path per #1282) is written
unconditionally before the sleep loop. No `[monitor-arm-refused]` error
and no exit-1 notification remain on this path. Added three named tests
to `tests/test_spawn.py`: non-git root arms with an alive marker and no
error text, non-git root + roster board entry still sweeps that board
target, and non-git root + empty roster is the named empty-state case
(alive, silent, no files under the arm-root).

## Why

canonical: docs/issue-1292/reports/implementation/survey.md, read this turn
The issue's field report showed a session rooted in a non-git parent
folder losing its entire Monitor for the session's lifetime on the old
hard exit, reproducing the #947 false "monitor unavailable" notice.

canonical: spawn.py:2659-2690, spawn.py:1101-1120, spawn.py:3619-3630, read this turn
The survey established that `_board_wide_sweep_all`, `_repo_slug`, and
`_repo_identity` already tolerate a non-git root without modification,
so only the shell-side gate needed to change.

## Upstream / basis

Basis: docs/issue-1292/proposals/non-git-arm-root-dormancy.md

## Verification

canonical: `python3 -m pytest tests/test_spawn.py -k 'monitor or heartbeat or roster' -q`, run this turn
acceptance: python3 -m pytest tests/test_spawn.py -k 'monitor or heartbeat or roster' -q — result: pass

```
48 passed, 455 deselected in 54.53s
```

## Doc placement

- No env var, config key, new dependency, migration, or setup step
  introduced — no handbook entry required.
- No library/format choice over a named alternative and no changed
  public signature/wire format beyond the arm-root gate itself, covered
  in docs/issue-1292/proposals/non-git-arm-root-dormancy.md's Rationale.
- No benchmark/investigation numbers produced.

## What did not work

None.

## Open findings

None.

## Hunt

Stance: refuter (rotation).
canonical: warrant-hunter dispatched this turn against the diff, result read this turn
No finding returned — treated as a closed probe, not a certificate
(verify may re-derive).

closed_checks:
- name: non-git-root spawn.py crash sweep
  code_sha: 521aa6690c2362a9cb1faf3daa0b079df687b01b
