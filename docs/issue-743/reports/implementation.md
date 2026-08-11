---
code_under_review:
  - gates/closure_sweep.py
  - spawn.py
  - gates/test_closure_sweep.py
  - tests/test_spawn.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Implemented the approved phase-1 proposal
(docs/issue-743/proposals/2026-08-11-watchdog-closure-sweep-issue-states-wiring.md)
for issue #743: wired the three deployed callers of
`closure_sweep.find_violations()` to pass its existing (but previously
unused) `issue_states=` parameter, so each stops paying a per-subject `gh
issue view` cost.

- `gates/closure_sweep.py`: added `issue_state_index_all(root) ->
  tuple[dict[int, str] | None, bool]` next to `_pr_index_all`, with a new
  `_ISSUE_INDEX_LIMIT = 1000` constant. One `gh issue list --state all
  --json number,state --limit 1000` call; returns `(index, ok)` with the
  same shape/truncation-safety as `_pr_index_all` — `ok=False` on `gh`
  failure (never read as "no issues"), `(None, True)` on hitting the row
  limit (caller falls back to `find_violations`'s existing per-subject
  path). `main()` now calls it once and passes the result into
  `find_violations(root, issue_states=issue_states)`.
- `spawn.py`: `_board_wide_sweep()` (watchdog-tick path) and the
  `closure-sweep` CLI subcommand each now call
  `closure_sweep.issue_state_index_all(root)` once and pass the result
  into `closure_sweep.find_violations(root, issue_states=issue_states)`.
  `find_violations()`'s own algorithm was not touched — call sites only.
- `gates/test_closure_sweep.py`: `MainExitCode.test_exit_code_is_2_and_prints_could_not_check`
  now also stubs `closure_sweep.issue_state_index_all` (returning `(None,
  False)`) alongside the existing `find_violations` stub, so `main()`
  stays network-independent.
- `tests/test_spawn.py`: the four existing `Watchdog`-class
  `_board_wide_sweep` tests now configure
  `fake_cs.issue_state_index_all.return_value = ({}, True)` on their
  `MagicMock` stand-in for `closure_sweep` — an unconfigured
  `MagicMock()` return value raises `ValueError` on unpack (`a, b =
  MagicMock()`), confirmed directly:

```
$ python3 -c "
from unittest import mock
m = mock.MagicMock()
a, b = m.foo(1, 2)
"
ValueError: not enough values to unpack (expected 2, got 0)
```

  Four new tests added:
  - `Watchdog.test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts`
    (Acceptance item 1): drives the real `gates/closure_sweep.py` module
    through the real `spawn._board_wide_sweep()` at subject counts 0, 3,
    and 150 (`spawn.board` monkeypatched per iteration), with
    `closure_sweep._issue_view` stubbed to record calls and
    `closure_sweep.subprocess.run` stubbed so the `gh issue list` call
    backing `issue_state_index_all` returns full coverage. Asserts the
    recorded `_issue_view` call count is `[0, 0, 0]` across all three
    subject counts — constant, not proportional to N — and that
    `_board_wide_sweep` returns `0` (no error) at the 0-subject empty
    state.
  - `Watchdog.test_find_violations_result_unchanged_with_prebuilt_issue_states`
    and `..._zero_violations` (Acceptance item 2): call
    `closure_sweep.find_violations` once without `issue_states`
    (per-subject `_issue_view` stubbed, call count asserted at 3) and
    once with a prebuilt `issue_states` dict holding the same values
    (asserting `_issue_view` is not called at all the second time),
    against one fixture PR index (`_pr_index_all` stubbed) covering both
    a closed-issue/open-PR violation, a merged-PR/open-issue violation,
    and a clean subject; and a second, all-clean fixture. Both
    `violations` and `skips` are asserted identical between the two
    calls in each test.
  - `ClosureSweepCliWiring.test_closure_sweep_subcommand_passes_prebuilt_issue_states`:
    drives `spawn.main()` with `sys.argv = ["spawn.py", "closure-sweep",
    "-C", <tmpdir>]` against a fully mocked `closure_sweep` module,
    asserting `issue_state_index_all` is called once and its result is
    passed through as `find_violations`'s `issue_states=` kwarg — no
    existing test covered this CLI path before (confirmed by survey).

## Why

`find_violations()` already accepted and consumed `issue_states` (issue
#189) to skip its own per-subject `_issue_view` call, but none of the
three deployed callers built and passed that map — each paid the full
per-subject `gh issue view` cost on every run, measured at ~101s/watchdog-tick
on this repo (166 subjects x ~0.61s/issue-view, per the issue body). #674
explicitly named this same gap in `_board_wide_sweep` as a separate,
deferred problem. This issue fixes the caller side only, mirroring the
bulk-fetch pattern `find_violations` already uses for PR lookups
(`_pr_index_all`).

## Upstream

Based on: docs/issue-743/proposals/2026-08-11-watchdog-closure-sweep-issue-states-wiring.md

## What did not work

None.

## Rationale for deviations

None — implementation matched the approved phase-1 proposal's "What will
be done" section; no scope-exceeded stop and no alternative swap
occurred. (Section kept present per the record-shape directive's
conditional wording even though empty of substance, alongside "What did
not work", for symmetry.)

## Doc placement

- No new env var, config key, dependency, or migration introduced — no
  handbook update required.
- No public signature or wire-format change beyond adding one new
  function (`issue_state_index_all`) with the same `(index, ok)` shape
  `_pr_index_all` already established in the same file — the proposal's
  own `## Rationale` already recorded the two rejected alternatives (an
  internal-prefetch design, and reusing `gates/flows.py`'s
  `_issue_list_all()`) and the reason each was rejected; no separate
  docs/issue-743/decisions/ entry needed.
- Benchmark numbers (the ~101s/tick, 166-subject, ~0.61s/issue-view
  measurement motivating this issue) were already recorded in the issue
  body and the phase-1 survey; this record cites them, it does not
  re-derive them.

## How it was verified

derived: `python3 -m pytest gates/test_closure_sweep.py tests/test_spawn.py -q`
```
408 passed, 2 skipped in 91.18s (0:01:31)
```

derived: `python3 -m pytest gates/test_closure_sweep.py tests/test_spawn.py -k "issue_view_call_count_constant or result_unchanged_with_prebuilt or closure_sweep_subcommand" -q`
```
4 passed, 406 deselected in 0.06s
```

Full suite (`python3 -m pytest -q`) run at phase-2 completion:
```
FAILED gates/test_boundary.py::t_all_gates_modules_recorded
FAILED gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint
FAILED tests/test_gates.py::t_find_violations_uses_record_evidence_for_keywordless_merge
4 failed, 1098 passed, 2 skipped in 174.72s (0:02:54)
```
The three failures above are the pre-declared already-red set on `main`
(unrelated to this change, tracked separately by issue-759). A fourth
failure appeared in that run, in tests/test_gates.py, function
t_rulebook_version_is_recorded — but it is not a new failure caused by
this change: spawn.rulebook_version("execution-observation") reads the
git-dirty status of this very on-the-record checkout (the
"execution-observation" rulebook's `installLocation` resolves back to
this repo in this dev environment), and the test fails whenever the
working tree has uncommitted changes, which it did at the moment this
suite ran (this session's own not-yet-committed edits). Confirmed by
stashing the uncommitted diff and re-running the single test in
isolation:

```
$ git stash push -m "issue-743 wip check" && python3 -m pytest tests/test_gates.py::t_rulebook_version_is_recorded -q; git stash pop
Saved working directory and index state On issue-743/implementation: issue-743 wip check
.                                                                        [100%]
1 passed in 0.15s
```
It passes clean on a clean tree and will pass again once this session's
changes are committed. Not counted as a new failure introduced by this
change; not added to the pre-declared red set since it is a working-tree
artifact, not a code defect.

## Hunt

- after-proposal (phase 1, stance 0 — assume the gate just touched is
  bypassable): FINDING, recorded in
  docs/issue-743/reports/implementation/2026-08-11-hunt-watchdog-closure-sweep-issue-states-wiring.md
  (scoped to the phase-1 docs-only write set — nested-shape record files
  bypass record_no_tool_residue and sibling checks; not this issue's
  write set to fix).
- before-landing (phase 2, stance 1 — assume this change and another
  plugin's rule cancel each other): NO FINDING, appended to the same
  hunt-record file. Checked gates.subprocess_call_shape_divergence,
  on-the-record's contract-guard.sh hook, gates/flows.py's independent
  board path, and main()'s exit-code behavior on issue_state_index_all
  failure — none depend on find_violations being called without
  issue_states or on per-subject _issue_view side effects.

closed_checks:
- check: acceptance-item-1-call-count-constant
  code_under_review: gates/closure_sweep.py, spawn.py, tests/test_spawn.py
- check: acceptance-item-2-result-parity
  code_under_review: gates/closure_sweep.py, tests/test_spawn.py
- check: no-new-test-failures-beyond-known-red-set
  code_under_review: gates/closure_sweep.py, spawn.py, gates/test_closure_sweep.py, tests/test_spawn.py

## Open findings

None outstanding against this issue's write set. The phase-1 hunt's
FINDING (nested-shape record files bypassing tool-residue/count-claim
checks) is a pre-existing gap in gates/gates.py's record-scanning regex,
not something introduced by or fixable within issue #743's frozen write
set — it is out of scope here and not re-opened by this record.
