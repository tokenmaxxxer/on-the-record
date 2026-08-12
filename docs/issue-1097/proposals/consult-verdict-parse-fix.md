---
status: proposed
files:
  - spawn.py
  - gates/test_consult_verdict_parsing.py
  - docs/issue-1097/reports/implementation/survey.md
---

## Request

#1097: two consecutive real `spawn.py consult requirements-engineering`
calls failed with "모델 출력에서 판단 JSON 을 못 찾음" (no parseable
judgment JSON in the model's output). Root-cause and fix at the
structural layer so consult verdicts parse again.

## Constraints

- `consult_cmd()` must keep its no-branch/no-commit/no-PR contract
  (issue #699 R1) unchanged.
- The trace invariant ("one line per call, success or failure alike")
  must not change shape.
- Fix must not touch the shared plugin-loading path `spawn_cmd()` uses
  for real delivery sessions.

## Rationale

`_parse_consult_verdict()` itself is not too strict — see survey: it
already tolerates leading prose and code fences, scanning back-to-front
for the last valid `{"answer": ...}` object. The failure traced to the
actual orchestrator transcript shows the model's response never
contained a JSON object at all for complex judgment questions.

Alternative considered and rejected: stripping `core_plugin_dirs()` from
consult's plugin set entirely, so consult sessions load only the role's
own rulebook. Rejected because those core hooks also carry
generically-useful judgment-quality steering (no-footgun,
no-mock-directive) that a design-judgment consult legitimately benefits
from; removing the whole plugin set is a bigger blast radius than the
actual defect (repo-mutation-oriented hooks racing the consult's own
terminal-JSON instruction) requires.

Chosen: keep the plugin set, but make the consult prompt explicitly
override the repo-mutation-oriented obligations (scout/proposal/warrant/
freelunch delegation) inline, and add one bounded automatic retry with a
reinforced reminder before declaring failure — confines the fix to
`consult_cmd()`'s own prompt assembly.

## What will be done

1. In `consult_cmd()`, add an explicit override sentence to the prompt
   stating that scout/proposal/delegation/approval-gate/record-writing
   obligations from loaded hooks do not apply to this call, and that this
   sentence takes priority over other loaded instructions.
2. If `_parse_consult_verdict()` returns `None` on the first attempt,
   retry once with the same prompt plus a reinforced one-line reminder,
   before recording failure.
3. Add gates/test_consult_verdict_parsing.py: parses a captured real
   transcript result text (from a live successful consult run), and
   exercises the retry-recovers and prompt-override-present paths against
   a mocked `subprocess.run`.
4. Run a live `spawn.py consult` smoke call reusing the same question
   shape that failed twice, to confirm end-to-end recovery.

## Out of scope

- Changing `core_plugin_dirs()`'s contents or which plugins load for
  `spawn_cmd()`'s delivery pipeline.
- Adding new failure-mode telemetry beyond the existing consult-log.md
  trace line.
- The separate #1098 "default-on convergence loop" requirement this
  same investigation surfaced — filed independently, not this issue's
  scope.

## How you'll know it worked

- gates/test_consult_verdict_parsing.py passes (4/4).
- tests/test_spawn.py -k "ConsultCmd or ConsultVerdictParsing" still
  passes unchanged (8/8).
- A live `spawn.py consult requirements-engineering` smoke run, asked the
  same complex-judgment question shape that failed twice, returns a
  parsed verdict and traces `ok:` in docs/reports/consult-log.md.

## What did not work

None.

## Accumulation

This change touches `consult_cmd()`'s inline `subprocess.run` call site
(spawn.py:4401 pre-fix), now wrapped in a two-attempt loop instead of a
single call. It does not add a new repeated pattern: the loop bound is
fixed at 2 attempts total, not one call per N callers, and no new
per-call inline `subprocess`/`gh` invocation site is introduced elsewhere
— `consult_cmd()` remains the single call site. If a third or later
retry tier were ever proposed, that would need its own proposal; this
one caps at one retry and does not scale with anything else that grows.
