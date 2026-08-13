# Current-state survey — issue #1123

derived: `grep -n "CONSULT_TIMEOUT\|_parse_consult_verdict\|attempts_exhausted" spawn.py`

## Write surfaces

- `spawn.py:4313-4444` (`_parse_consult_verdict`, `consult_cmd`) — the only
  place a consult call parses/retries/traces. `_parse_consult_verdict`
  (spawn.py:4313) scans backward for the last valid `{...}` containing
  `"answer"`; `consult_cmd` (spawn.py:4351) runs `base_prompt` then, on
  parse failure, `retry_prompt` once, both under the same fixed
  `CONSULT_TIMEOUT = 180` (spawn.py:66).
- `gates/test_consult_json_parse.py` — the #1119 regression guard. Its one
  parse-failure fixture (`_fake_run_no_json_both_attempts`) returns a
  short fixed string with no JSON at all; it does not model a long/complex
  answer whose JSON tail got cut off by truncation or timeout, so it
  cannot have caught the 00:35:18 shape.
- `docs/reports/consult-log.md` — trace sink. `_append_consult_trace`
  (spawn.py:4338) writes one line per attempt-set: role, issue, question
  (first 200 chars), and `outcome` (first 300 chars). On parse failure,
  `outcome` is set to the fixed string `"모델 출력에서 판단 JSON 을 못
  찾음"` (spawn.py:4431) — the model's actual raw output text is never
  written anywhere. `session_result(r.stdout).get("result", "")` (the raw
  text) is read into `result` (spawn.py:4428) and handed to
  `_parse_consult_verdict`, then discarded once parsing fails.

## Gap this issue's requirement targets

canonical: spawn.py:4421-4436 (read directly, this session)

Requirement: "root-cause the 00:35:18 failure with the actual captured
model output (persist raw output on parse failure if it does not already)".
Reading spawn.py:4421-4436 directly: there is no code path that writes
`result` to disk or into the trace line when `verdict is None`. Every
recurrence of "판단 JSON 을 못 찾음" is therefore unfalsifiable exactly as
the issue states — this is a real, reproducible gap (checked: no other
`_append_consult_trace` call site, no raw-output logger anywhere else
touching `consult_cmd`).

## consult-log.md does not (yet) carry the 00:35:18 line

canonical: `grep -rn "00:35:18" docs/reports/consult-log.md docs/issue-*/reports/consult-log.md` (this session, empty result)

The issue's cited failing trace is evidence from outside this checkout's
committed history. This confirms the requirement's own premise: without
raw-output persistence, this failure is currently unfalsifiable from repo
state alone — corroborating, not contradicting, the issue.

## Retry/timeout shape (relevant to the three named hypotheses)

- Hypothesis A (CONSULT_TIMEOUT exhausted by thinking):
  canonical: spawn.py:66 (read directly, this session)
  Single fixed 180s constant applied identically to both the first
  attempt and the retry — no scaling by question length or complexity.
- Hypothesis B (JSON emitted but not found for long outputs):
  canonical: spawn.py:4313-4326 (read directly, this session)
  Parser scans the entire text backward for balanced `{...}`, not just
  the tail — length-insensitive by design. canonical: spawn.py:4313-4326
  (same site) — so a well-formed object anywhere in a long output should
  still be found, making B the least likely of the three on code alone;
  cannot fully rule out without raw text (same gap noted above).
- Hypothesis C (retry budget identical to first attempt):
  canonical: spawn.py:4416-4420 (read directly, this session)
  `retry_prompt` only adds an instruction not to scout/propose again — it
  does not shorten the question or raise the timeout, so a retry failing
  for a capacity reason repeats the same failure.

## Prior art in this codebase

- `docs/issue-1112/proposals/2026-08-13-consult-self-hosted-hook-skip.md`
  — #1119's own phase-1 proposal, same failure symptom, root-caused a
  different mechanism (self-hosted hook injection cost). Its hunt record
  (`docs/issue-1112/reports/implementation/2026-08-13-hunt-consult-self-hosted-hook-skip.md`)
  is the template this issue's hunt dispatch should follow.
- `gates/test_consult_json_parse.py` already establishes the pattern for
  monkeypatching `spawn.subprocess.run`/`plugin_dirs`/`core_plugin_dirs`/
  `_consult_trace_path` to drive `consult_cmd` under a fake model process
  — the complex-question fixture this issue requires reuses that pattern,
  not a new harness.

## Skip-condition check (scout directive)

This is not a pure bugfix in the narrow sense — it requires a design
decision (where/how to persist raw output; what "loud degradation" means
for a library function whose caller already `sys.exit`s on any raised
exception). However this is infrastructure/tooling work (spawn.py's own
consult wiring), not a product-shaped or user-facing surface with a
market category to benchmark against — there is no comparable external
product whose consult-retry/raw-capture UX is the right reference class.
Scouting is skipped on the "non-product-shaped deliverable, no meaningful
category to benchmark" basis; the relevant "best-in-class" comparison is
internal (this repo's own #1119/#1097 prior art, covered above), not
external.
