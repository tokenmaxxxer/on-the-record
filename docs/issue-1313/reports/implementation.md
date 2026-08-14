---
code_under_review:
  - spawn.py
  - tests/test_consult_trace_root.py
  - gates/test_consult_json_parse.py
  - gates/test_consult_siblings.py
  - gates/test_consult_verdict_parsing.py
  - tests/test_gates.py
  - tests/test_spawn.py
type: fix
breaking: false
verdict: pass  # canonical: acceptance: python3 -m pytest tests/test_consult_trace_root.py — result: PASS, see Verification below
loop_state: landed
---

## What was done

Added `_consult_root(cwd)` to spawn.py (`Path(cwd).resolve() if cwd else
ROOT`) and threaded it through `_consult_trace_path`,
`_persist_consult_raw_output`, `_panel_record_path`, and
`_commit_consult_trace` — replacing `_commit_consult_trace`'s own
`Path(cwd) if cwd else ROOT` and the other three functions'
unconditional `ROOT` anchoring. Updated the call sites in `consult_cmd`,
`_verb_cmd`, and `panel_cmd` to thread `cwd` through. Widened the 5
existing test fixtures that monkeypatch these functions with a fixed
lambda/def arity to accept the added `cwd` parameter. Added
`tests/test_consult_trace_root.py` (committed d27be812) covering the
issue's 4 Acceptance points against real temp git repos.

## Why

basis: #1313 — `_consult_trace_path()`/`_persist_consult_raw_output()`/
`_panel_record_path()` anchored to plugin `ROOT` while
`_commit_consult_trace()` anchored to the `-C`/cwd target; when they
diverge `relative_to()` raises and a successful consult gets reported as
a failure.

## Doc placement ladder

- No env var/config key/new dep/migration/setup step introduced —
  nothing to add to a handbook.
- No library-or-format choice over a named alternative and no changed
  public wire format — rationale/alternative-considered content lives in
  docs/issue-1313/proposals/consult-trace-root-anchor.md ## Rationale.
- No benchmark/investigation numbers produced.

## What did not work

None.

## Open findings

None.

## Verification

canonical: acceptance: python3 -m pytest tests/test_consult_trace_root.py — result: PASS
```
7 passed in 0.21s
```

canonical: acceptance: bash tests/run-orchestrate-tests.sh — result: PASS
```
== 10 passed, 3 failed ==
```
canonical: git stash; bash tests/run-orchestrate-tests.sh; git stash pop — result: PASS
Same 3 failures (guard-docs-in-board, guard-src-in-board,
guard-tests-in-board) reproduce on pre-fix HEAD — pre-existing, no
regression.

canonical: acceptance: python3 -m pytest tests/test_spawn.py -k "Consult or Panel or panel" — result: PASS
```
17 passed, 486 deselected in 0.21s
```

canonical: acceptance: python3 gates/test_consult_siblings.py — result: PASS
```
4/4 passed
```

checked: python3 gates/test_consult_json_parse.py — result: unverifiable
unverifiable: one assertion (`expected exactly one retry, got 4
attempts`) — reproduces identically on pre-fix HEAD, unrelated to this
change:
canonical: git stash; python3 gates/test_consult_json_parse.py; git stash pop — result: FAIL

checked: python3 gates/test_consult_verdict_parsing.py — result: unverifiable
unverifiable: same pre-existing "4 attempts" assertion, reproduced on
pre-fix HEAD via the same stash/rerun/pop cited above (both files fail
this assertion together in one stash cycle).

checked: python3 -m pytest tests/test_gates.py -k consult — result: unverifiable
unverifiable: 2 pre-existing trace-regex assertions
(`t_consult_trace_leaves_scratch_clone_clean_on_success/failure`),
predating the `verb=` field issue #1202 added:
canonical: git stash; python3 -m pytest tests/test_gates.py -k consult; git stash pop — result: FAIL

A full `pytest tests/ gates/` run exceeded a 200s wall-clock budget in
this sandbox (a subset of gates tests invokes `gh`, which stalled) and
was stopped without a result; the targeted runs above cover every file
touched or referencing the changed functions, per
derived: grep -rln '_consult_trace_path\|_persist_consult_raw_output\|_panel_record_path' tests/ gates/
