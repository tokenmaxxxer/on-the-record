skip condition: pure bugfix — this is CLI wiring that mirrors an existing,
already-shipped pattern (`consult`) with no design decision left open;
scout/deep-research is skipped per the scout-directive's mandatory skip
record.

## Current state

- `spawn.py:4531` defines `panel_cmd(role_a, role_b, question, issue=None,
  cwd=None, run_session=None) -> dict` (issue #973/#985) — concurrent
  2-judge SendMessage judgment, sibling of `consult_cmd()`.
- `spawn.py:4630` `main()` builds one shared `argparse.ArgumentParser`
  with three positional slots: `role`, `task`, `consult_question`
  (spawn.py:4632-4635). `consult` dispatch (spawn.py:4751-4759) reads
  `a.task` as the target role and `a.consult_question` as the question,
  calls `consult_cmd(a.task, a.consult_question, issue=a.issue,
  cwd=a.cwd)`, prints the verdict as JSON, returns 0.
- canonical: `grep -n 'a.role == "panel"' spawn.py` returned no output —
  `main()` has no `panel` dispatch branch.
- `panel_cmd` takes 3 required args (role_a, role_b, question); the
  existing parser has only 2 free positional slots after `role`
  (`task`, `consult_question`) — a 4th positional (`panel_question`) is
  needed to carry the question, mirroring the `role`/`task`/
  `consult_question` naming convention already in place.
- canonical: `grep -n panel on-the-record/hooks/directive.sh` returned no
  output — the orchestrator directive documents the CONSULT delegation
  shape and its `spawn.py consult <role> "<question>"` invocation
  (directive.sh, near the "DELEGATION IS THE DEFAULT" rule) but has no
  mention of `panel` anywhere.
- canonical: `grep -n 'class ConsultCmd\|class PanelCmd\|ClosureSweepCliWiring' tests/test_spawn.py`
  — `ConsultCmd` (line 8977) tests `consult_cmd()` directly; no argv-level
  CLI-dispatch test exists for either `consult` or `panel`. The closest
  existing pattern for an argv-level CLI dispatch test is
  `ClosureSweepCliWiring` (tests/test_spawn.py:4053) — sets `sys.argv`,
  calls `spawn.main()`, mocks the downstream call, asserts the mock was
  invoked with the right args and `rc == 0`.

## Write set (frozen)

- `spawn.py` — add `panel_question` positional arg to the parser; add
  `if a.role == "panel":` dispatch branch mirroring `consult`.
- `on-the-record/hooks/directive.sh` — one added sentence next to the
  existing CONSULT delegation-shape paragraph, mentioning `panel`.
- `tests/test_spawn.py` — one new test class, `PanelCliWiring`,
  mirroring `ClosureSweepCliWiring`'s argv-dispatch shape: patches
  `spawn.panel_cmd`, sets `sys.argv = ["spawn.py", "panel", role_a,
  role_b, question, "--issue", "1"]`, asserts `panel_cmd` was called
  with `(role_a, role_b, question, issue=1, cwd=".")` and `rc == 0`;
  plus a missing-args case asserting `SystemExit`.

No new dependency, no new env var, no migration.
