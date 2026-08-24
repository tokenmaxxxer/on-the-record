---
issue: 2152
role: implementation
loop_state: landed
upstream:
  - path: spawn.py
    sha: 4bfe4975d76b93f05c24d9aeb2e1d9ab087baf7b
  - path: tests/test_default_single_phase_flip.py
    sha: 4bfe4975d76b93f05c24d9aeb2e1d9ab087baf7b
code_under_review: spawn.py tests/test_default_single_phase_flip.py
commit_sha: 4bfe4975d76b93f05c24d9aeb2e1d9ab087baf7b
type: feat
breaking: true
verdict: pass
---

# issue-2152 — implementation record

## What was done

canonical: spawn.py:1487, 1494, 1440, 2288, 2496 (this session, read before
editing)

Flipped `spawn.py`'s default spawn mode from two-phase (proposal-first) to
single-phase (build-now), per the operator decision in the issue #2152
body, in commit 4bfe4975.

- `--single-phase` is now a no-op alias: the default already produces the
  same result, so the flag stops changing behavior (deprecation note kept
  in its `--help` text, one release).
- Added `--two-phase`, the new explicit opt-in that restores today's
  proposal-first flow: it suppresses the `CORE_BUILD_NOW=1` env stamp and
  the build-now contract preamble line, so a design-bearing task can still
  ask for a proposal round.
- `main()` now computes `effective_single_phase = not a.two_phase and not
  a.checkpoint` and threads that into `_spawn_one(single_phase=...)`
  (spawn.py:1487, 1494) instead of the raw `a.single_phase` flag.
  `--checkpoint` stays forced to two-phase regardless of the new default,
  because checkpoint mode's own boundary IS the phase-1 pause — folding it
  into build-now would skip the proposal round a checkpoint session is
  supposed to stop at.
  The `--checkpoint` + `--single-phase` mutual-exclusivity guard at
  spawn.py:1440 is untouched: it reads the raw CLI flag, not the effective
  value, so it still only fires when a spawner explicitly sets both.
- The two sites that gate on `single_phase` inside `_spawn_one`
  (spawn.py:2288, appending `_SINGLE_PHASE_CONTRACT_LINE` to the task
  text; spawn.py:2496, setting `extra_env["CORE_BUILD_NOW"] = "1"`) are
  unchanged in shape — they still key off the `single_phase` parameter,
  which now defaults to `True` at the call site instead of `False`.
- `tests/test_default_single_phase_flip.py` (new, committed in 4bfe4975):
  five cases — no-flags-defaults-to-single-phase, `--two-phase` opts out,
  `--single-phase` is a no-op alias, `--checkpoint` alone still forces
  two-phase, `--checkpoint --two-phase` stays two-phase. All patch
  `spawn._spawn_one` and assert on the `single_phase`/`checkpoint` kwargs
  it was called with.

## Why

Operator decision (2026-08-24, issue #2152 body): correctness must not
depend on the spawner remembering to set `--single-phase`. Two
consecutive docs-only spawns (fixture #38, #40) were launched without the
flag and each spent ~6min producing only a proposal PR — a
flag-dependent default made operator forgetfulness a defect. Flipping the
default removes that failure mode entirely; `--two-phase` keeps the
proposal-first path available for the design-bearing tasks that still
want it, and `--checkpoint`'s forced-two-phase behavior is preserved
because its approval boundary depends on stopping at phase-1 regardless
of the global default.

Per role-handoff contract v3 s19a, this session itself was spawned with
`CORE_BUILD_NOW=1` — canonical: this session's own shell
(`echo "CORE_BUILD_NOW=$CORE_BUILD_NOW"`, this session) printed
`CORE_BUILD_NOW=1` at turn start — so it skipped the phase-1 proposal
round and delivered directly on `issue-2152/implementation`; no separate
proposal file was written for this change under this issue's tree.

## Upstream basis

- The issue #2152 body (operator decision text, acceptance criteria) —
  canonical: `gh issue view 2152` (this session).
- spawn.py's pre-existing `--single-phase` flag and
  `_SINGLE_PHASE_CONTRACT_LINE` machinery, from issue #1978/#1672
  (contract v3 s19a's build-now bypass) — canonical: spawn.py:1711-1716
  (this session, read before editing).
- The `--checkpoint` mutual-exclusivity guard and forced-two-phase
  behavior, from issue #2129 — canonical: spawn.py:1440-1443 (this
  session, read before editing).
- `tests/test_checkpoint_mode.py`, pre-existing, used to check the
  default flip does not disturb checkpoint-mode behavior.

## Open findings

None.

## What did not work

None.

## Next steps

None — loop_state is terminal (landed). Verification below is this
session's own executed evidence for issue #2137.

## skill-verdict

skill-verdict: implementation-complexity-coupling-management — not-applicable: no coupling/cohesion metric, accessor chain, or cross-module import direction is involved — this is a single-file CLI default flip plus one new boolean flag.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-style pattern is being introduced or removed; the change is a default-value inversion and a mutually-exclusive-flag computation, not a structural indirection decision.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data structure, algorithm, or communication-scheme choice with a performance cliff; the change is argparse flags and boolean logic.
skill-verdict: implementation-blueprint — not-applicable: single-file, mechanical change to existing argument-parsing and env-stamping logic in spawn.py — no new module boundary or multi-file structure to select.

## Executed acceptance evidence (issue #2137)

canonical: pytest tests/test_default_single_phase_flip.py -q — result: PASS (5/5)
```
.....                                                                    [100%]
5 passed in 0.80s
```

canonical: pytest tests/test_checkpoint_mode.py tests/ -k "single_phase or checkpoint or preamble" -q — result: PASS (20/20)
```
....................                                                     [100%]
20 passed in 193.61s (0:03:13)
```

canonical: pytest tests/test_spawn_directive_assembly.py -k SinglePhaseSignal -q (CORE_BUILD_NOW unset) — result: PASS (2/2)
```
..                                                                       [100%]
2 passed in 1.09s
```

Note on the third run: this delivery session's own env carries
`CORE_BUILD_NOW=1` (build-now bypass, contract v3 s19a). Running the same
`SinglePhaseSignal` selection with that variable still set in the test
process's own environment surfaces one assertion failure —
canonical: pytest tests/test_spawn_directive_assembly.py -k SinglePhaseSignal -q (CORE_BUILD_NOW left set) — result: FAIL (1/2, this session)
```
AssertionError: 'CORE_BUILD_NOW' unexpectedly found in {... 'CORE_BUILD_NOW': '1', ...}
```
— because the test process's own `os.environ` already carries the key
from this delivery session's ambient env, independent of anything
spawn.py's code does under test. This is a pre-existing artifact of
running this suite from inside a build-now-spawned session, not a
regression from this change.
