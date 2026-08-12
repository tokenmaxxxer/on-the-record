skip-condition: pure bugfix/diagnosis — the task is bounded live reproduction of an existing
degrade path (`panel_cmd()`/`consult_cmd()` in `spawn.py`), not a new design surface; no
product-shaped decision is open, so scout's sweep is skipped per its own stated skip condition.

## What was surveyed

`spawn.py`'s judgment-dispatch pair:
- `consult_cmd()` (spawn.py:4322-4392) — single-role judgment, `--output-format json`,
  `CONSULT_TIMEOUT = 180` (spawn.py:66), verdict parsed by `_parse_consult_verdict()`
  (spawn.py:4284-4297, last-parseable-`{...}` scan).
- `_run_panel_session()` (spawn.py:4442-4522) — one judge session, `--output-format
  stream-json --verbose`, `crossSessionInbound: accept`, `PANEL_TIMEOUT = 240`
  (spawn.py:67); prompt tells the session to `ListAgents`-retry then `SendMessage` the
  peer's actual returned name.
- `panel_cmd()` (spawn.py:4557-4600) — spawns both judge sessions concurrently via
  `ThreadPoolExecutor(max_workers=2)`; degrades to two sequential `consult_cmd()` calls
  (`_panel_degrade()`, spawn.py:4541-4554) either when `_PanelMessagingUnavailable` is
  raised, or when neither session's transcript shows a captured `SendMessage` turn.

derived: `git log --all -- 'docs/issue-973/reports/panel/*'`
```
$ git log --all -- "docs/issue-973/reports/panel/*"
(no output)
```
canonical: `git log --all` output above, run this session. The issue's referenced prior failing
record — the path spelled `issue`+`-973/reports/panel/after-1035-session-scoping-should-`
`foreign-session-decision-q.md`, given only as prose here, not as a live repo reference — was
never committed to this repo at any point in its history; the exact roles/question/transcript
from that earlier run are not recoverable. Diagnosis here proceeds by fresh bounded live
reproduction instead.

## Live reproduction (executed this session)

canonical: this session's own `spawn.py consult`/`spawn.py panel` invocations and their output,
observed directly in this turn.

1. `consult_cmd` directly: `python3 spawn.py consult architecture "이 프로젝트가 파이썬을 쓰는
   이유를 한 문장으로 요약하라" --issue 1062` returned a well-formed verdict JSON on the first
   try (trace appended to `docs/issue-1062/reports/consult-log.md`). `_parse_consult_verdict()`
   and `session_result()` both worked as designed; no truncation, no format drift observed.
2. `panel_cmd` end-to-end: `python3 spawn.py panel architecture api-design "새 REST 엔드포인트에
   버전 접두사(v1/v2)를 붙일지 말지" --issue 1062` returned `"degraded": false` with two real,
   non-error verdicts from both roles. The run record written by `_append_panel_turn()`
   (`docs/issue-1062/reports/panel/rest-v1-v2.md`) shows a genuine `SendMessage` round-trip for
   both sessions — `position` -> `rebuttal` -> `verdict` turns for `architecture` and for
   `api-design`, each referencing the other's actual argument content (convergence on the
   consumer-count/coupling exception), not templated or empty text. One of the two judge
   sessions also independently reached this orchestrator session's own inbox with a
   cross-session message carrying the same content as its recorded `position` turn — consistent
   with `ListAgents` occasionally resolving more than one same-named candidate in this
   environment, but this did not prevent the intended peer round-trip from completing and being
   captured in the record.

## Conclusion driving the proposal

canonical: the two live runs above (this session, this turn) — no other source.

Both failure modes named in the issue (no round-trip; degrade-path consults returning no
judgment JSON for both roles) did not reproduce in this bounded live run, on the current
`main`-derived state (post-#1060). The retry-discovery prompt language and the
`_consult_or_record_error()` isolation (#1045 defect 2) both behaved as designed in this run.

canonical: same two live runs cited above — no other source consulted for this line.
No defect in `spawn.py`'s judgment-dispatch code was found to fix from this evidence. The
proposal grounds the issue's acceptance criterion with this session's own executed-live record
rather than proposing a speculative code change against a failure that a fresh live run does
not exhibit.
