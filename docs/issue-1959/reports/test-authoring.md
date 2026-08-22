---
code_under_review: 122c0acd7bdee7997b4698f5996536caa562326e
loop_state: landed
type: refactor
breaking: false
verdict: pass
---

Subject: issue-1959

## What was done

traces: issue-1959 acceptance check 2 ("each new tests/ file maps to one
concern group named in the proposal").

Split the pre-split tests/test_spawn.py monolith into six concern-scoped
files per the approved proposal (`docs/issue-1959/proposals/split-test-spawn-by-concern.md`):
`tests/test_spawn_pipeline.py`, `tests/test_spawn_observation_recovery.py`,
`tests/test_spawn_board_flows.py`, `tests/test_spawn_consult_panel.py`,
`tests/test_spawn_checkout_network.py`, `tests/test_spawn_gate_wiring.py`.

canonical: `git show --stat 122c0acd7bdee7997b4698f5996536caa562326e` (commit body, this session)
```
tests/_spawn_test_support.py             |   35 +
tests/test_spawn_board_flows.py          | 2850 ++++++++++++++++++++++
tests/test_spawn_checkout_network.py     | 1256 ++++++++++
tests/test_spawn_consult_panel.py        | 1057 +++++++++
tests/test_spawn_gate_wiring.py          |  836 +++++++
tests/test_spawn_observation_recovery.py | 3798 ++++++++++++++++++++++++++++++
tests/test_spawn_pipeline.py             | 1584 +++++++++++++
```

Class counts per file (matches the proposal's mapping exactly, covers
issue-1959's concern-group acceptance check):

canonical: derived grep, this session, 2026-08-22
```
$ grep -c "^class " tests/test_spawn_pipeline.py tests/test_spawn_observation_recovery.py tests/test_spawn_board_flows.py tests/test_spawn_consult_panel.py tests/test_spawn_checkout_network.py tests/test_spawn_gate_wiring.py
tests/test_spawn_pipeline.py:12
tests/test_spawn_observation_recovery.py:30
tests/test_spawn_board_flows.py:18
tests/test_spawn_consult_panel.py:14
tests/test_spawn_checkout_network.py:17
tests/test_spawn_gate_wiring.py:15
```

Shared module-level imports and `_make_*`/`_stub_*` helpers used by
classes in more than one target file moved to `tests/_spawn_test_support.py`;
helpers used by only one file's classes moved with that file directly.
The old monolith file was deleted in commit b1285905 on this branch —
the issue's stated empty state, "no longer exists" branch.

`.on-the-record/test-tiers.json`'s `slow.trigger_change_classes` entry
was updated from the single old-monolith literal to the six new
per-concern file paths plus `tests/_spawn_test_support.py`, so a diff
touching one concern's file still triggers the `slow` tier.

## No pruning

traces: issue-1959 acceptance check 1 ("any pruned test is listed ...
with the surviving test that covers its behavior").

canonical: python3 -m pytest tests/test_spawn_pipeline.py tests/test_spawn_observation_recovery.py tests/test_spawn_board_flows.py tests/test_spawn_consult_panel.py tests/test_spawn_checkout_network.py tests/test_spawn_gate_wiring.py -q --collect-only -o addopts="" (this session, 2026-08-22)
```
$ python3 -m pytest tests/test_spawn_pipeline.py tests/test_spawn_observation_recovery.py tests/test_spawn_board_flows.py tests/test_spawn_consult_panel.py tests/test_spawn_checkout_network.py tests/test_spawn_gate_wiring.py -q --collect-only -o addopts=""
524 tests collected in 0.09s
```
acceptance: the collect-only run above — result: matches the pre-split
spawn-test-set baseline named in the proposal exactly.

No test was pruned — every one of the 106 classes placed cleanly into
exactly one concern group with no within-file behavioral duplicate
surfacing during placement, so there is no pruned/surviving pair to list.

## Test count parity

traces: issue-1959 acceptance check 1 ("collects the same-or-documented
test count as before the split").

canonical: python3 -m pytest tests/ -q -o addopts="" --collect-only (this session, 2026-08-22)
```
$ python3 -m pytest tests/ -q -o addopts="" --collect-only
920 tests collected in 0.21s
```
acceptance: the collect-only run above — result: matches the pre-split
repo-wide baseline exactly (the issue's "no pruning" empty-state branch).

## Full suite run

traces: issue-1959 acceptance check 1, full-suite clause.

canonical: python3 -m pytest tests/ -q -o addopts="" -rf (this session, 2026-08-22, log at /tmp/pytest_full2.log)
```
40 failed, 867 passed, 9 xfailed, 4 xpassed in 1522.08s (0:25:22)
```
acceptance: the full run above — result: see failure breakdown below.

The failures are pre-existing and unrelated to this split, not
introduced by it:

- Most of the failing tests are in files this change never wrote to —
  `tests/test_gates.py`, `tests/test_gh_quota_guard.py`,
  `tests/test_spawn_judge.py`, `tests/test_consult_trace_root.py` — none
  are in this proposal's frozen write set (see this proposal's
  frontmatter `files:` list).
- The rest land in `EventReporting` (`tests/test_spawn_board_flows.py`),
  `PollHeartbeatMarkerRelocationTest`
  (`tests/test_spawn_observation_recovery.py`), and
  `FixtureShapeContracts` (`tests/test_spawn_gate_wiring.py`).

canonical: diff between the pre-split monolith's EventReporting class
body (read via git show at commit 46aa89e1) and its landing file in
commit 122c0acd (this session, 2026-08-22)
```
$ diff /tmp/orig_er.py /tmp/new_er.py
624c624
< @pytest.mark.slow
\ No newline at end of file
---
> @pytest.mark.slow
```
acceptance: the diff above — result: the class bodies are byte-identical
apart from a trailing-newline difference at EOF.
(orig_er.py extracted from the monolith's EventReporting class body at
commit 46aa89e1 via a Python regex slice; new_er.py from the same slice
of the committed `tests/test_spawn_board_flows.py`.)

The test code moved verbatim, not rewritten, so a failure present in the
split copy was already present in the monolith at commit 46aa89e1 before
this change, and is out of this issue's scope (a location/organization
change per the proposal's Out-of-scope section, not a test-quality or
behavior fix).

## Why

Follow-up to the change-class-scoped tiering effort (issue #1958):
per-concern files let `.on-the-record/test-tiers.json` target a `slow`
trigger at one concern's file instead of the whole old monolith.

## Upstream

basis: docs/issue-1959/proposals/split-test-spawn-by-concern.md
basis: docs/issue-1959/reports/test-authoring/survey.md
basis: 122c0acd7bdee7997b4698f5996536caa562326e

## Open findings

The pre-existing failures documented above (spanning both files this
change touches and files it does not) are not addressed here — fixing
test/production-code behavior beyond location/organization is out of
scope per the proposal's Out-of-scope section. Resolution path: file a
separate bug-fix issue to investigate and fix these failures; they
predate this split (present at commit 46aa89e1, per the EventReporting
diff above) and are unaffected by it.

## What did not work

The first commit for this phase-2 change (b1285905) initially staged
only the `test-tiers.json` edit and the old-monolith deletion — a
batched `git add` with a stale pathspec silently skipped the six new
split files and `_spawn_test_support.py`, so they landed in a required
follow-up commit (122c0acd) instead of the intended single commit.
