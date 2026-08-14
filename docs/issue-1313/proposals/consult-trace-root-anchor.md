---
status: proposed
files:
  - spawn.py
  - tests/test_consult_trace_root.py
  - gates/test_consult_json_parse.py
  - gates/test_consult_siblings.py
  - gates/test_consult_verdict_parsing.py
  - tests/test_gates.py
  - tests/test_spawn.py
---

Scout skip: pure bugfix with no design decision open — see
docs/issue-1313/reports/implementation/survey.md.

#1313

## Request

`spawn.py consult` (and its sibling verbs and panel records) anchors
trace/record file paths at the plugin's own install directory (`ROOT`),
while the commit step anchors at the `-C`/cwd target repo. When those
two diverge, `relative_to()` raises and a successful consult is reported
as a failure.

## Constraints

- No-target invocations (no `-C`, no cwd) must keep writing/committing
  into the plugin repo (`ROOT`) — unchanged behavior.
- Trace path, side-file path, panel-record path, and commit root must
  all derive from the same anchor so `relative_to()` cannot raise.
- New acceptance test module: `tests/test_consult_trace_root.py`
  (`python3 -m pytest tests/test_consult_trace_root.py`).
- No regression in `bash tests/run-orchestrate-tests.sh`.

## Rationale

Considered anchoring unconditionally at `cwd` (drop the `ROOT`
fallback) instead of a shared helper with a conditional fallback.
Rejected: it would relocate the no-target consult trace out of the
plugin repo, breaking the documented no-target behavior the issue's
own Acceptance #2 requires to keep working unchanged.

Chosen instead: one small helper, `_consult_root(cwd)`, returning
`Path(cwd).resolve() if cwd else ROOT`, used by all four functions
(`_consult_trace_path`, `_persist_consult_raw_output`,
`_panel_record_path`, `_commit_consult_trace`) and their call sites in
`consult_cmd`/`_verb_cmd`/`panel_cmd`. This keeps the fallback and
removes the divergence at its single source.

## What will be done

- Add `_consult_root(cwd)` to spawn.py.
- Thread `cwd` into `_consult_trace_path`, `_persist_consult_raw_output`,
  `_panel_record_path`, and have `_commit_consult_trace` use the same
  helper instead of its own `Path(cwd) if cwd else ROOT`.
- Update call sites in `consult_cmd`, `_verb_cmd`, `panel_cmd` to pass
  `cwd` through.
- Widen the existing test fixtures that monkeypatch these functions
  with a fixed lambda/def arity so they still accept the new `cwd`
  parameter (no behavior change in the fixtures themselves).
- Add `tests/test_consult_trace_root.py` covering the issue's four
  Acceptance points.

## Out of scope

- Any change to what gets written into the trace line format itself.
- Any change to the panel degrade path's own logic beyond passing
  `cwd` through to `_panel_record_path`.

## Accumulation

The touched test fixtures (5 files) each carry their own
`_consult_trace_path`/`_persist_consult_raw_output`/`_panel_record_path`
monkeypatch because `gates/`- and `tests/`-style consult tests were
built independently over several issues (#699, #1112, #1134, #1202) —
this is the same pre-existing fixture-duplication shape as before this
change, not a new one introduced here. This change widens each fixture's
lambda/def arity by one optional `cwd=None` parameter; it does not add a
new fixture-duplication site. If a future issue adds a fifth
consult-family record-path function, the same per-fixture widening would
recur once per existing fixture file (currently 5) — that is an existing
cost of the fixture-per-test-module layout, unchanged in shape by this
fix, and out of scope to consolidate here.

## How you'll know it worked

- `python3 -m pytest tests/test_consult_trace_root.py` passes.
- `bash tests/run-orchestrate-tests.sh` shows no new failures versus
  the pre-fix baseline (3 pre-existing, unrelated board-gate failures
  persist on both sides).
- `python3 gates/test_consult_json_parse.py`,
  `gates/test_consult_siblings.py`, `gates/test_consult_verdict_parsing.py`
  and the `Consult`/`Panel` test classes in `tests/test_spawn.py` and
  `tests/test_gates.py` pass (or fail identically to the pre-fix
  baseline where a failure is pre-existing and unrelated).
