---
status: approved
files:
  - gates/gates.py
  - gates/test_record_lint.py
---

## Request
`gates.py::_terminal_loop_state` raises `KeyError: -1` (`states[-1]` on a
dict-shaped or otherwise atypical `record_fields.loop_state`) instead of
returning `None`, crashing `record_lint.py` — observed inside a mid-merge
working tree while resolving PR #1100. Make it, and its caller
`record_checked_claims`, robust; cover with a reproducing test.

## Constraints
Pure bugfix — no design decision open (scout-directive skip condition).
Behavior for normal (flat-list) `loop_state` declarations must stay
unchanged.

## Rationale
Considered normalizing dict-shaped `loop_state` (e.g. reading a `terminal`
key from roles that use the `{progress, terminal, refusal, error}` shape)
so those roles get real terminal-state detection instead of `None`.
Rejected for this issue: that is a scope-widening feature change
touching every dict-shaped role file's semantics, while the issue asks
only for a crash fix — return `None` on any state shape the function
cannot safely read the last element of, exactly what the acceptance
criteria ask for.

## What will be done
Guard `_terminal_loop_state` so it returns `None` whenever
`record_fields` is not a dict, or `loop_state` is not a non-empty
list/tuple — covering the empty-list, missing-key, and dict-shaped
(the actual crash trigger, confirmed present on most role files) cases.
Add a test in `gates/test_record_lint.py` reproducing the dict-shaped
crash and the empty-states case.

## Out of scope
Normalizing/reading terminal state out of dict-shaped `loop_state`
declarations for those roles' own gating logic.

## How you'll know it worked
`python3 gates/test_record_lint.py` passes including the two new tests;
`gates._terminal_loop_state` returns `None` instead of raising for
dict-shaped and empty states while unchanged for flat-list states.

## Accumulation
This touches `gates/test_record_lint.py`, a file that already accumulates
one `t_*` function per prior gate fix — the same additive pattern N more
similar bugfixes would repeat. That's intentional: each fix gets its own
independent, named reproduction test, and the file's `_run_all()` harness
scales linearly with test count with no per-addition maintenance cost.
No shared inline `subprocess`/`gh` call is being added or duplicated here.

## What did not work
None.
