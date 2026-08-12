---
status: proposed
files:
  - spawn.py
  - on-the-record/hooks/directive.sh
  - tests/test_spawn.py
---

## Request

`panel_cmd()` (issue #973/#985: two roles judging concurrently over
SendMessage) exists but `main()` never dispatches to it — the capability
is unreachable from the CLI and from the orchestrator directive. Wire
`spawn.py panel <role_a> <role_b> "<question>" [--issue n]` into
`main()`, mirroring the existing `consult` dispatch, mention it in the
orchestrator directive next to `consult`, and add a CLI-dispatch test.

## Constraints

- Mirror the `consult` dispatch shape exactly (spawn.py:4751-4759):
  same error-message style, same `sys.exit` on missing args, same
  `json.dumps(..., indent=2, ensure_ascii=False)` print, same `--issue`/
  `-C` reuse.
- No change to `panel_cmd()` itself (spawn.py:4531) — it already has the
  right signature and behavior (degrade path, record path, etc.); this
  proposal only wires the CLI entrypoint to it.
- No new dependency, no new env var, no schema change.

## Rationale

Considered making `panel` a `nargs="*"` catch-all positional instead of
adding a fourth named positional (`panel_question`), so the parser
wouldn't grow another argument slot. Rejected: the existing three-slot
convention (`role`, `task`, `consult_question`) is already load-bearing
for `consult`, `spawn`, `kill`, etc., and a catch-all `nargs="*"` would
either collide with those other subcommands' use of `task` or require a
special-cased sub-parser just for `panel` — more surface than adding one
more named optional positional that only `panel` reads (harmless "?" no
matter which subcommand is chosen, exactly like `consult_question`
already is for every non-consult subcommand).

## What will be done

- `spawn.py`: add `ap.add_argument("panel_question", nargs="?", ...)`
  next to `consult_question`; add `if a.role == "panel":` branch that
  validates `a.task` (role_a), `a.consult_question` (role_b), and
  `a.panel_question` (question) are all present, calls `panel_cmd(a.task,
  a.consult_question, a.panel_question, issue=a.issue, cwd=a.cwd)`
  inside a `try/except` that exits with a trace-preserving message on
  failure (mirroring consult's `except Exception as e: sys.exit(...)`),
  prints the result as JSON, returns 0.
- `on-the-record/hooks/directive.sh`: append one sentence to the
  existing CONSULT delegation-shape paragraph, naming `spawn.py panel
  <role_a> <role_b> "<question>" [--issue n]` as the concurrent-judgment
  variant, same no-branch/no-PR contract.
- `tests/test_spawn.py`: add `PanelCliWiring` (mirroring
  `ClosureSweepCliWiring`, tests/test_spawn.py:4053) — argv path
  `["spawn.py", "panel", "review", "qa", "<question>", "--issue", "1"]`
  through `spawn.main()`, `spawn.panel_cmd` patched, asserts it was
  called with `("review", "qa", "<question>", issue=1, cwd=".")` and
  `rc == 0`; plus a missing-args case asserting `SystemExit`.

## Accumulation

The `directive.sh` edit adds one sentence to the existing CONSULT
paragraph, not a new per-subcommand block — it does not create a
repeated pattern that grows one line per future subcommand. `main()`'s
`if a.role == "<subcommand>":` chain already accumulates one branch per
CLI verb (consult, kill, watch, panel, ...); this proposal adds the one
branch `panel` was missing, following the existing convention rather
than starting a new one. No shared helper is warranted for two branches
(`consult`, `panel`) with near-identical but not identical shapes
(2 vs. 3 required args); if a third judgment-dispatch verb is added
later, the `consult`/`panel` validate-then-call boilerplate is small
enough (5 lines each) that extracting a shared `_dispatch_judgment_cmd`
helper at that point — not now — is the right trigger.

## Out of scope

- Any change to `panel_cmd()`'s internal behavior (degrade logic,
  record format, ThreadPoolExecutor use).
- Any new consumer of `panel` beyond the directive mention (e.g. no new
  auto-invocation from other hooks).
- The #1037 audit's broader req#5 concerns beyond making `panel`
  reachable and adding its dispatch test.

## How you'll know it worked

```
python3 -m pytest tests/test_spawn.py -k panel_cli
```
passes, exercising the argv → `main()` → `panel_cmd()` path with
`run_session`/the real subprocess stubbed out (only `panel_cmd` itself
is mocked at the CLI-wiring layer, per the acceptance note "run_session
stubbed" — `panel_cmd`'s own internal use of `run_session` is already
covered by the existing `PanelCmd`-shaped tests, if any, and is out of
scope here).
