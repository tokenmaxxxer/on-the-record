Subject: issue-1736

# Current-state survey

scout-directive skip: mechanical bugfix/feature with the spec leaving no
design decision open — issue #1736's Acceptance already spells out the
exact precedence order, the exact three call paths to touch, and the
exact invariant to guard. Nothing here is a product-shaped choice; it is
"where does one more precedence tier slot into an existing precedence
chain."

## Existing precedence chain (spawn.py)

`resolved_role_model()` at spawn.py:5367-5375 implements
`MUSTER_ROLE_MODEL` env > `role_model.txt` (`read_role_model_config()`,
spawn.py:5358-5364) > built-in `"sonnet"` default (issue #93). It takes
no arguments today.

Three call paths read `resolved_role_model()` and splice `--model
<value>` into a `claude -p` argv, each with its own local
`role_model = resolved_role_model(); if role_model: cmd += ["--model", role_model]`
copy:
- `spawn_cmd()` spawn.py:5378-5412 (role spawn — `spawn`/`_spawn_one` path)
- consult's shared argv builder spawn.py:5547-5581 (backs `consult_cmd()`
  spawn.py:5586 and the `ideate`/`draft`/`review` verb family, spawn.py:5721)
- `_run_panel_session()` spawn.py:6206-6242 (backs `panel_cmd()`
  spawn.py:6321)

A fourth call, `_judge_cmd_and_env()` spawn.py:5870-5884, already takes
an explicit `model` kwarg and both its callers hardcode
`model="haiku"` (spawn.py:5990, 6025 — prefilter and validator). This is
the invariant issue #1736 requires stay unreachable from `--model`.

The dry-run block spawn.py:7080-7098 independently calls
`resolved_role_model()` to preview the argv the real spawn will use
(issue #31 acceptance) — it does not go through `spawn_cmd()`.

## argparse surface

`main()`'s `ArgumentParser` (spawn.py:6787 onward) has no `--model` flag
today; a search for the string "model" across spawn.py's argparse block
shows no name collision. `a.model` would reach: the `spawn` role
dispatch at spawn.py:7101 (`_spawn_one(...)`), `consult` at spawn.py:6964
(`consult_cmd(...)`), `panel` around spawn.py:7005 (`panel_cmd(...)`),
and the dry-run preview block spawn.py:7080-7098.

`_spawn_one()` (spawn.py:7703) is the single body shared by `main()`'s
spawn dispatch and `drive()`'s respawn path (spawn.py:4375) — it calls
`spawn_cmd()` at spawn.py:7814.

## What will change

`resolved_role_model()` gains an optional first param (the CLI
override), checked before the env var. Each of the three non-judge call
sites (`spawn_cmd()`, the consult argv builder, `_run_panel_session()`)
gains a `model: str | None = None` param threaded from a new `--model`
argparse flag through `_spawn_one()` / `consult_cmd()` / `panel_cmd()`.
The judge path (`_judge_cmd_and_env()`, prefilter, validator) is
untouched — it never receives the CLI value; that separation is the
guard case the issue asks the new test to assert.

## Test file

A search for `test_spawn_model_override` under `test/` finds nothing —
the file the issue names does not exist yet. `test/` already carries
other tests that exercise `resolved_role_model()` in isolation via
monkeypatched env / `ROLE_MODEL_CONFIG`; the new file follows the same
shape: monkeypatch `os.environ` and `ROLE_MODEL_CONFIG`, call
`resolved_role_model()` with and without a CLI-override argument at each
precedence level, and separately assert `_judge_cmd_and_env()`'s
hardcoded `model="haiku"` callers are unreachable from any CLI value.
