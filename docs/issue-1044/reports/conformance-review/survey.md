---
code_under_review:
  - spawn.py
  - on-the-record/hooks/directive.sh
  - tests/test_spawn.py
type: survey
loop_state: n/a
---

## What was done

Current-state survey for the conformance review of issue #1044's delivered
commit (PR #1056, merge commit `a269692a0cba919e9ed6bf06c832aa280dec04ae`
on `main`) against R001 (req#5, orphan-capability standard) and issue
#1044's stated Direction/Acceptance.

canonical: git log origin/main --oneline (this turn) — `a269692a issue-1044
phase-2: wire panel_cmd() CLI dispatch (#1056)` is on `main`. A
conformance-review record for this subject has not yet been written under
docs/issue-1044/reports/, so the board condition (implementation landed, no
conformance-review record yet) holds.

### Requirement text (from the issue, verbatim scope)

- Direction: `spawn.py panel <role_a> <role_b> "<question>" [--issue n]`
  wired into `main()`, mirroring `consult` dispatch; mentioned in the
  orchestrator directive next to `consult`.
- Acceptance: CLI dispatch test in `tests/test_spawn.py` — panel argv path
  reaches `panel_cmd` (`run_session` stubbed).
  check: `python3 -m pytest tests/test_spawn.py -k panel_cli`

### What the delivered commit contains

canonical: spawn.py:5453-5454,5630-5639 (read this turn) — `panel_question`
argparse argument added next to `consult_question`; `if a.role == "panel":`
branch validates `a.task`/`a.consult_question`/`a.panel_question`, rejects
`role_a == role_b`, calls `panel_cmd(...)` inside try/except, prints JSON,
returns 0 — structurally mirrors the adjacent `consult` branch.

canonical: on-the-record/hooks/directive.sh:305-309 (grep this turn) —
panel line added next to the CONSULT paragraph naming the same CLI
form and the "advisory-only, no branch/PR" contract.

canonical: tests/test_spawn.py:4395-4426 (grep this turn) — `PanelCliWiring`
class with three tests: argv path calls `panel_cmd` with `run_session`
stubbed, missing-args exits, same-role-twice exits.

canonical: python3 -m pytest tests/test_spawn.py -k panel_cli -v (this turn)
```
tests/test_spawn.py::PanelCliWiring::test_panel_cli_subcommand_calls_panel_cmd PASSED [ 33%]
tests/test_spawn.py::PanelCliWiring::test_panel_cli_subcommand_missing_args_exits PASSED [ 66%]
tests/test_spawn.py::PanelCliWiring::test_panel_cli_subcommand_same_role_twice_exits PASSED [100%]

====================== 3 passed, 500 deselected in 0.21s =======================
```

### Gaps / open questions for phase-2 verdicts

- The acceptance test stubs `run_session` — it proves the argv-to-panel_cmd
  wiring, not a live `claude -p` round-trip. R001/req#5's "orphan-capability
  standard" language (per #1037's original refutation) turns on
  *reachability*, which this test does prove; whether "exercised" also
  requires a live round-trip is a phase-2 judgment call, not resolved here.
- `role_a == role_b` rejection is an inline fix noted in the implementation
  record's deviation log, not in the original issue's Direction/Acceptance
  text — needs a verdict on whether it's in-scope addition or drift.

## Why

Contract v3 s19 requires phase-1 (survey + proposal) before any phase-2
verdict record; no `CORE_BUILD_NOW=1` bypass is set in this session's
environment, so the two-phase flow applies.

## Upstream / basis

Issue #1044, PR #1056 (merge commit a269692a0cba919e9ed6bf06c832aa280dec04ae),
docs/issue-1044/reports/implementation.md.

## Open findings

This survey stage does not render verdicts, so it carries no open findings
of its own; phase-2 will record per-requirement verdicts once approved.
