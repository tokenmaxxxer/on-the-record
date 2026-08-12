---
code_under_review:
  - spawn.py
  - on-the-record/hooks/directive.sh
  - tests/test_spawn.py
type: feature
breaking: false
canonical: python3 -m pytest tests/test_spawn.py -k panel_cli -v (this turn) — 2 passed
verdict: pass
loop_state: landed
---

## What was done

Wired `panel_cmd()` (issue #973/#985, concurrent 2-role judgment over
SendMessage) into `spawn.py`'s CLI dispatch, per the approved proposal
at `docs/issue-1044/proposals/panel-cli-dispatch.md`:

- `spawn.py`: added `ap.add_argument("panel_question", nargs="?", ...)`
  next to `consult_question`, and an `if a.role == "panel":` branch
  (spawn.py:4760-4768) mirroring the `consult` branch — validates
  `a.task`/`a.consult_question`/`a.panel_question`, calls
  `panel_cmd(role_a, role_b, question, issue=a.issue, cwd=a.cwd)` inside
  a `try/except` that exits with a trace-preserving message, prints the
  result as JSON, returns 0.
- `on-the-record/hooks/directive.sh`: appended one sentence to the
  existing CONSULT delegation-shape paragraph naming
  `spawn.py panel <role_a> <role_b> "<question>" [--issue n]` as the
  concurrent-judgment variant, same no-branch/no-PR contract.
- `tests/test_spawn.py`: added `PanelCliWiring` (mirroring
  `ClosureSweepCliWiring`) with
  `test_panel_cli_subcommand_calls_panel_cmd` (argv path through
  `spawn.main()` with `panel_cmd` patched, asserts call args and
  `rc == 0`) and `test_panel_cli_subcommand_missing_args_exits`
  (missing args → `SystemExit`).

## Why

Requirement R001 (req#5, orphan-capability standard): `panel_cmd()`
existed but was unreachable from the CLI, so the #1037 audit could not
credit req#5 with a live round-trip. This closes that gap by making
`panel` a reachable subcommand, following the `consult` convention
already load-bearing for the parser.

## Upstream / basis

docs/issue-1044/proposals/panel-cli-dispatch.md (approved phase-1
proposal), docs/issue-1044/reports/implementation/survey.md.

## Acceptance check

canonical: `python3 -m pytest tests/test_spawn.py -k panel_cli -v` (this turn)
```
tests/test_spawn.py::PanelCliWiring::test_panel_cli_subcommand_calls_panel_cmd PASSED [ 50%]
tests/test_spawn.py::PanelCliWiring::test_panel_cli_subcommand_missing_args_exits PASSED [100%]

====================== 2 passed, 475 deselected in 0.18s =======================
```

canonical: `python3 -m pytest tests/test_spawn.py -q` (this turn)
```
477 passed in 34.93s
```

## What did not work

None.

## Rationale for deviations

canonical: docs/issue-1044/reports/implementation/hunt-panel-cli-dispatch.md (this turn's before-landing hunt)

Before-landing warrant-hunter dispatch (stance 0, bypass-hunting) found
that the `panel` CLI branch validated only that `role_a`/`role_b`/
`question` were non-empty, never that `role_a != role_b` — so
`spawn.py panel accessibility accessibility "q"` would run a self-panel
session indistinguishable from a genuine two-role judgment. This is an
inline fix within the frozen write set (`spawn.py`): added
`if a.task == a.consult_question: sys.exit(...)` right after the
existing missing-args check, plus
`test_panel_cli_subcommand_same_role_twice_exits` in
`tests/test_spawn.py`. Logged in
`docs/issue-1044/reports/implementation/deviation-log.md`.

## Open findings

None (the one before-landing hunt finding was inline-fixed above; hunt
record: docs/issue-1044/reports/implementation/hunt-panel-cli-dispatch.md).

## Doc placement

No env var, dependency, migration, or public-signature change occurred
— proposal's `## Out of scope` explicitly excludes any change to
`panel_cmd()`'s internal behavior or signature. No handbook/decisions/
reports doc-placement ladder entry is triggered by this change beyond
this record itself.
