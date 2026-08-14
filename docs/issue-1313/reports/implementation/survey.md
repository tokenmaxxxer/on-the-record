# Survey — issue-1313 consult trace/record root anchor

Scout skip: pure bugfix, both scout-directive skip conditions apply —
(a) it is a bugfix, and (b) the spec leaves no design decision open —
the issue names the exact functions, the exact anchor rule ("target
repo when `-C`/cwd given, plugin ROOT otherwise"), and the acceptance
test module name.

## Write set

- spawn.py — the four functions and call sites named in the issue.
- tests/test_consult_trace_root.py (new).
- Existing test fixtures that monkeypatch those functions with a fixed
  arity — gates/test_consult_json_parse.py,
  gates/test_consult_siblings.py, gates/test_consult_verdict_parsing.py,
  tests/test_gates.py, tests/test_spawn.py — need their lambda/def
  signatures widened to accept the new cwd parameter, or the added
  positional arg at call sites raises TypeError.

## Current state

derived:
```
$ grep -n "^def _consult_trace_path\|^def _persist_consult_raw_output\|^def _panel_record_path\|^def _commit_consult_trace" spawn.py
def _persist_consult_raw_output(issue: int | None, ts: str, attempt: int, text: str) -> Path:
def _consult_trace_path(issue: int | None) -> Path:
def _commit_consult_trace(paths: list[Path], issue: int | None, role: str,
```

derived:
```
$ python3 gates/test_consult_json_parse.py 2>&1 | tail -5
Traceback ... spawn.py:4615, in <listcomp>
    rels = [str(p.relative_to(root)) for p in paths]
ValueError: '.../docs/reports/consult-raw-failures/....txt' is not in the subpath of '/tmp/...'
```
Reproduces the issue's reported failure directly against this checkout.

## Alternative considered

Anchor everything at `cwd` unconditionally (drop the `ROOT` fallback).
Rejected: the no-`-C` CLI path is expected to keep writing/committing
consult traces into the plugin repo itself when no target is given
(Acceptance #2 in the issue) — dropping the fallback would relocate that
trace and break the no-target case the issue asks to preserve.
