---
code_under_review:
  - gates/spawn_on_pr.py
  - spawn.py
  - tests/test_spawn_on_pr.py
type: fix
breaking: false
# canonical: python3 -m pytest tests/test_spawn_on_pr.py tests/test_merge_gate.py gates/test_closure_sweep.py
verdict: pass
loop_state: committing
---

## What was done
Landed the approved phase-1 proposal
`docs/issue-1360/proposals/spawn-on-pr-scope-fix.md`.

canonical: git diff gates/spawn_on_pr.py
`missing_verification(root, issue_states=None)` now fetches
`closure_sweep.issue_state_index_all(root)` when no dict is supplied
and filters via a new `_issue_is_open()` helper.

canonical: git diff gates/spawn_on_pr.py
`spawn_missing_for_pr()` gained `spawn_cap: int = SPAWN_CAP` (module
constant `SPAWN_CAP = 4`), truncating its pair list and printing one
line when truncation happens.

canonical: git diff gates/spawn_on_pr.py
A new `_missing_verification_closed()` + `backfill_closed(root, cwd,
dry_run=True)` pair, plus a `_main()` argparse CLI exposing
`backfill-closed [--live]`, were added as a separate opt-in entry
point.

canonical: git diff spawn.py
`spawn.py::_board_wide_sweep()` moves its existing
`closure_sweep.issue_state_index_all(root)` call earlier and passes
the result into `spawn_missing_for_pr(...)`.

canonical: git diff tests/test_spawn_on_pr.py
`tests/test_spawn_on_pr.py` was extended with new test functions and
existing ones updated to pass `issue_states` explicitly.

## Why
canonical: gh issue view 1360
Requirement basis: docs/issue-1360/proposals/spawn-on-pr-scope-fix.md
(approved), addressing issue #1360's report that the watchdog tick's
board-wide scan spawned verification sessions for subjects whose issue
was already resolved — scope beyond #1323 requirement 3's PR-creation
trigger.

## What did not work
None.

## Rationale for deviations
None — this session performed no code authoring; it wrote the record
and landed already-authored, already-tested code matching the approved
proposal's execution section without divergence.

## Doc placement
No env var, config key, dependency, or migration was introduced; no
public wire-format change occurred beyond this repo's own internal
optional-keyword-param additions. Nothing required outside this
record.

## Acceptance verification
canonical: python3 -m pytest tests/test_spawn_on_pr.py -q
```
...........                                                              [100%]
11 passed in 0.20s
```
canonical: python3 -m pytest tests/test_spawn_on_pr.py -q — result:
11 passed, covering acceptance (a)-(d) from the proposal's "How you'll
know it worked" section.

canonical: python3 -m pytest tests/test_merge_gate.py gates/test_closure_sweep.py -q
```
..........................                                               [100%]
26 passed in 0.52s
```
canonical: python3 -m pytest tests/test_merge_gate.py gates/test_closure_sweep.py -q
— result: 26 passed, the no-regression check the proposal named.

## Accumulation
See "## Accumulation" in
docs/issue-1360/proposals/spawn-on-pr-scope-fix.md — this change reuses
the existing `closure_sweep.issue_state_index_all()` shared helper
rather than adding a new ad hoc `gh` call site.

## Hunt
No warrant-hunter dispatch this session — this session performed
record-writing and landing of code already authored and tested in a
prior session, not new-code generation at a build transition.

## Open findings
None.

## Next steps
Commit this record with the three code/test files, push the branch,
open the phase-2 delivery PR against `main` with `Closes #1360`.

## Resolution path
Not applicable — no open findings.
