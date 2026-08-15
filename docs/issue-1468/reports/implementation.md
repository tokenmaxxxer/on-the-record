---
code_under_review:
  - docs/specs/enforcement-boundary.md
type: fix
breaking: false
verdict: landed
loop_state: landed
---

# issue-1468 — record unrecorded gate modules in enforcement-boundary.md

## What was done

Scout skip: this is a pure bugfix (`gates/test_boundary.py` test
`t_all_gates_modules_recorded` failing on main) with no design decision
open — authoring a verdict row for an existing module is a mechanical
classification against that module's own code, not a direction choice.
Scouting and the survey-order proposal flow are skipped per the
scout-directive's stated skip condition.

Ran the boundary test first to find the actual failing set (not just the
two modules the issue names):

```
$ python3 -m pytest gates/test_boundary.py -k t_all_gates_modules_recorded -q
F
AssertionError: check_runner.py 가 ... 기록되지 않은 게이트가 조용히 존재한다(#441).
  merge_gate.py ...
  spawn_on_pr.py ...
  tool_learnings_gate.py ...
1 failed in 0.05s
```
canonical: python3 -m pytest gates/test_boundary.py -k t_all_gates_modules_recorded -q, executed 2026-08-14, output above.

The issue names `acceptance_authoring_rule.py` and `tool_learnings_tracker.py`,
but the test's `check()` function (derived from the filesystem, not a
hand-picked list) also failed on four more unrecorded modules:
`check_runner.py`, `merge_gate.py`, `spawn_on_pr.py`,
`tool_learnings_gate.py`. Fixing only the two named modules would leave the
issue's own acceptance criterion unmet, so verdict rows for all six were
added to `docs/specs/enforcement-boundary.md`'s `` ## `gates/*.py` `` table,
each verdict decided from that module's own enforcement surface:

- `acceptance_authoring_rule.py` — repo-local: standalone CLI
  (gates/acceptance_authoring_rule.py:100-121), `check_issue_body`/`check`
  (gates/acceptance_authoring_rule.py:53-77) invoked manually with an issue
  number.
  derived: grep -rln "acceptance_authoring_rule" --include=*.py --include=*.sh --include=*.json . | grep -v .git/
  ```
  gates/acceptance_authoring_rule.py
  tests/test_acceptance_authoring_rule.py
  docs/issue-1323/proposals/2026-08-14-acceptance-authoring-rule-and-check-runner.md
  docs/issue-1323/reports/implementation/survey.md
  ```
  No `gates/ci.py`, hook, or `spawn.py` caller in that list.
- `tool_learnings_tracker.py` — repo-local: `render`/`is_landed`
  (gates/tool_learnings_tracker.py:29-45), `main`
  (gates/tool_learnings_tracker.py:48-58) prints to stdout, exit 0 always
  ("rendering, not a gate — nothing here blocks a commit" per its own
  docstring); same class as the already-recorded `playbook_tracker.py` row.
- `check_runner.py` — repo-local: `main` (gates/check_runner.py:141) is a
  standalone CLI (`<pr-number> <issue-number>`).
  derived: grep -rln "check_runner\b" --include=*.py --include=*.sh . | grep -v .git/
  ```
  gates/merge_gate.py
  gates/check_runner.py
  tests/test_check_runner.py
  tests/test_merge_gate.py
  ```
  No `gates/ci.py`/hook/`spawn.py` caller among those.
- `merge_gate.py` — repo-local: `evaluate` (gates/merge_gate.py:65-82) is a
  standalone CLI depending on `check_runner.py`'s posted comment and
  `spawn_on_pr.py`'s import, but is itself not called from `gates/ci.py`,
  any hook, or `spawn.py` (same grep set as `check_runner.py` above, plus
  `grep -rln "merge_gate\b" --include=*.py --include=*.sh . | grep -v .git/`
  returning only `gates/merge_gate.py` and `tests/test_merge_gate.py`); its
  own docstring states it deliberately has no CI-workflow surface
  (`.github/workflows/` 파일이 아니다).
- `spawn_on_pr.py` — contract, orchestrator-loop: `import spawn_on_pr` and
  `spawn_on_pr.spawn_missing_for_pr(...)` are called from
  `spawn.py:_board_wide_sweep()` (spawn.py:2880-2884), which
  `roster_watchdog()` runs each tick — same zero-install, board-wide
  reachability class as the already-recorded `closure_sweep.py`/
  `spawn_coverage.py` rows.
  ```
  2880:    import spawn_on_pr
  2884:        spawned = spawn_on_pr.spawn_missing_for_pr(root, str(root), issue_states=issue_states)
  ```
- `tool_learnings_gate.py` — repo-local: `evaluate`/`classify_entry`
  (gates/tool_learnings_gate.py:88-114), standalone CLI
  (gates/tool_learnings_gate.py:125).
  derived: grep -rln "tool_learnings_gate\b" --include=*.py --include=*.sh . | grep -v .git/
  ```
  gates/tool_learnings_gate.py
  gates/test_tool_learnings_gate.py
  ```
  No `gates/ci.py`/hook/`spawn.py` caller among those.

Regenerated `docs/specs/reconciled-index.md` via `python3 gates/spec_index.py
--update` after the `docs/specs/enforcement-boundary.md` edit, as required
for any `docs/specs/*` commit.
canonical: git status --porcelain, executed 2026-08-14 after the regenerate run — showed only `docs/specs/enforcement-boundary.md` modified, no diff in `docs/specs/reconciled-index.md`.

## Why

The boundary test derives its expected set from the actual `gates/*.py`
filesystem listing, not a hand-maintained list — any module that exists
with no verdict row fails every full-suite run (issue #441's silent-drift
catch). The fix is to author each missing row from that module's real
enforcement surface, not to relax the test.

## Basis

Upstream: issue #1468, `docs/specs/enforcement-boundary.md`, the
`t_all_gates_modules_recorded` test function inside `gates/test_boundary.py`.

## Acceptance verification

canonical: python3 -m pytest gates/test_boundary.py -q, executed 2026-08-14, output below
checked: full gates/test_boundary.py suite — result: pass
```
$ python3 -m pytest gates/test_boundary.py -q
..........                                                               [100%]
10 passed in 0.04s
```

Requirement 1 (verdict rows authored from each module's actual code) is
the diff to `docs/specs/enforcement-boundary.md` itself.
canonical: python3 -m pytest gates/test_boundary.py -q, executed 2026-08-14 (same run as above).
Requirement 2 is satisfied by that run: 10 passed, 0 failed.

## What did not work

None.

## Open findings

None.
