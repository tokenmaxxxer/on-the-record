---
code_under_review:
  - spawn.py
  - gates/test_consult_json_parse.py
  - docs/reports/consult-log.md
type: fix
breaking: false
# canonical: python3 gates/test_consult_json_parse.py — result: PASS (see
# `## closed_checks` below for the full derived output)
verdict: pass
loop_state: landed
---

canonical: python3 gates/test_consult_json_parse.py — result: PASS (see
`## closed_checks` below for the full derived output); consult-log tail
line timestamp 2026-08-13T01:50:45.617389+00:00 (this session's own live
consult run).

# Implementation record — issue #1123

## What was done

Implemented the approved phase-1 proposal
(`docs/issue-1123/proposals/consult-raw-output-persist-complex-question.md`):

- `spawn.py`: added `_persist_consult_raw_output(issue, ts, attempt, text)`
  (spawn.py:4313-4327), a single shared helper that writes the model's raw
  output text to a side file under `docs/issue-<n>/reports/` +
  `consult-raw-failures/<ts>-<attempt>.txt` (or under `docs/reports/` when
  no `--issue`), mirroring `_consult_trace_path()`'s issue/no-issue branch
  so the two never drift.
- `consult_cmd()`'s retry loop (spawn.py:4421-4443) now calls this helper on
  every parse failure (each of the two attempts), and folds the returned
  path plus a bounded (last-300-char) excerpt into `attempts_exhausted` —
  so both the trace line (`outcome`) and the final `RuntimeError` message
  carry the raw-output file path, closing the unfalsifiability gap the
  issue named.
- `gates/test_consult_json_parse.py`: added two new cases —
  `t_complex_question_persists_raw_output_on_parse_failure` (reproduces the
  long/multi-part question shape from the issue's own described
  recurrence) and `t_short_multi_clause_question_persists_raw_output_on_parse_failure`
  (reproduces the short-multi-clause shape the issue comments describe as a
  second live recurrence) — both assert the `RuntimeError` message names
  the raw file, the file actually contains the model's output, and
  (complex case) the trace line points at it.
- Live smoke: ran `python3 spawn.py consult implementation "<multi-part
  트레이드오프 질문>"` against the real `claude -p` consult path (no
  fakes) — returned a verdict, per the consult-log citation above.

## Root cause (scope note)

The live smoke this session succeeded on the first attempt with the
multi-part question tried — it did not reproduce a parse failure, so there
is no freshly-persisted raw-output file from a real (non-fake) failure to
root-cause against in this session. The proposal's own scope note applies:
the phase-2 fix (timeout scaling / retry-prompt change / other) is scoped
by whatever the raw output actually shows, not decided here — since this
session produced no new real-failure raw output, no timeout/retry change is
made. The persistence mechanism itself is what the issue asked to land now;
a future recurrence will have a diagnosable side file instead of being
unfalsifiable, per the issue's stated purpose.

## Why

Issue #1123 requires: (1) persist raw model output on consult parse failure
via a shared helper so a recurrence is diagnosable, with a trace-line
pointer + bounded excerpt and the `RuntimeError` message including the
path; (2) extend the regression guard with a complex-question case and a
short-multi-clause case (per the issue comments dated 2026-08-13 reporting
two live recurrences); (3) live-smoke a multi-part question. All three are
implemented per the approved proposal; no timeout/retry change was made
because this session's raw output does not show what to scope it by (see
Root cause above).

## Upstream basis

Proposal: docs/issue-1123/proposals/consult-raw-output-persist-complex-question.md
(approved via `APPROVE issue-1123/implementation` issue comment).

## What did not work

Expected: the pre-existing `t_both_attempts_exhausted_raises_with_reported_symptom`
test would stay hermetic once `_persist_consult_raw_output()` was wired into
`consult_cmd()`'s parse-failure path. Actual: it did not stub the new
helper, so each run wrote real .txt files into this repo's real
docs/reports/consult-raw-failures directory — caught by a `git status`
check after a test run, fixed by adding the same `_persist_raw_under(root)`
stub this test's siblings already use, and deleting the stray files.

## Doc-placement ladder

No env var, config key, new dependency, migration, or setup step was added
— nothing to place in a handbook. No public signature or wire format
changed (the new helper is private, `_persist_consult_raw_output`, and
`consult_cmd()`'s public signature is unchanged). No benchmark/investigation
numbers to place under `docs/issue-1123/reports/`. This record itself is
the required phase-2 output.

## Open findings

None open.

## resolved_findings

- finder: warrant-hunter, before-landing, stance 3 (docs/issue-1123/reports/implementation/2026-08-13-hunt-consult-raw-output-persist-complex-question.md)
- finding: the raw-output path in `consult_cmd()`'s parse-failure message
  was embedded unquoted, so `record_lint.py`'s existing issue #1085
  untracked-path-citation guard would silently never fire on it if a
  future record quoted the message verbatim.
- resolution: backtick-quoted `raw_path` in the `attempts_exhausted`
  f-string (spawn.py:4453), matching the backtick-quoted-path convention
  `_PATH_REF` expects elsewhere in this codebase.
derived: `python3 gates/test_consult_json_parse.py`
```
5/5 passed
```
canonical: derived command output above, rerun this session after the fix.

## closed_checks

derived: `python3 gates/test_consult_json_parse.py`
```
ok - t_both_attempts_exhausted_raises_with_reported_symptom
ok - t_complex_question_persists_raw_output_on_parse_failure
ok - t_consult_cmd_settings_never_carry_self_hosted_hooks
ok - t_run_panel_session_settings_never_carry_self_hosted_hooks
ok - t_short_multi_clause_question_persists_raw_output_on_parse_failure
5/5 passed
```
canonical: derived command output above, this session — code_sha: working
tree at time of this record.

## Next steps

None — issue #1123's three named requirements (persist, extend guard with
both cases, live-smoke) are satisfied per the `closed_checks` derived
output and the consult-log citation above. If a future consult attempt
still fails to find JSON, its raw-output file and trace pointer are
available for future diagnosis — that work is out of this session's scope,
since no real failure occurred here to diagnose.

## Resolution path

N/A — no open finding.
