# Current-state survey — issue-1097

## Write set actually touched

- `spawn.py` — `consult_cmd()` (spawn.py:4350) prompt assembly.
- gates/test_consult_verdict_parsing.py — new regression test (gates/
  is ungated by approval-gate.sh, unlike tests/, so this is where a
  consult-focused regression test could land without phase-2 approval).

## What exists today

- `spawn.py:_parse_consult_verdict()` (spawn.py:4312) scans model output
  text back-to-front for the last parseable `{...}` object carrying an
  `"answer"` key. Existing unit coverage in tests/test_spawn.py (classes
  ConsultVerdictParsing and ConsultCmd) mocks `subprocess.run` and never
  exercises a real `claude -p` session, so it could not have caught a
  failure mode where the model simply never emits the JSON.
- `consult_cmd()` (spawn.py:4350-4420) builds a `cmd` that loads both the
  role's own rulebook plugin (`plugin_dirs(role, spec)`) *and*
  `core_plugin_dirs()` — the same plugin set `spawn_cmd()` uses for full
  delivery sessions (branch/commit/PR pipeline). `core_plugin_dirs()`
  ships the on-the-record core hooks: freelunch-directive,
  scout-directive, warrant-directive, proposal-shape-directive,
  no-mock-directive, no-footgun-directive, record-shape-directive,
  terse-directive — all steering hooks aimed at sessions that produce a
  repository deliverable.
- `docs/reports/consult-log.md` traced two consecutive real failures
  (2026-08-12T07:38:43Z, 07:39:01Z) with outcome `error: 모델 출력에서
  판단 JSON 을 못 찾음`, both for complex design-judgment questions asked
  of `requirements-engineering`. Root-caused via the actual orchestrator
  session transcript.

canonical: /home/jwjung/.claude/projects/-home-jwjung-tokenmaxxxer/9d7b7071-7558-4e16-884a-47aaa5a0744f.jsonl

derived: grep -n "07:38:43\|07:39:01\|판단 JSON" /home/jwjung/.claude/projects/-home-jwjung-tokenmaxxxer/9d7b7071-7558-4e16-884a-47aaa5a0744f.jsonl
```
896:...consult 실패(트레이스는 남았다): error: 모델 출력에서 판단 JSON 을 못 찾음...
905:...consult 실패(트레이스는 남았다): error: 모델 출력에서 판단 JSON 을 못 찾음...
917:...consult trace log entries for 07:38:43 and 07:39:01, both outcome='error: 모델 출력에서 판단 JSON 을 못 찾음'...
```

Both failures happened while `core_plugin_dirs()` hooks were loaded
alongside the consult prompt, on a branch (`fix/python39-compat`) with
the same `consult_cmd()` wiring as today's `main`.

## Gap

`consult_cmd()`'s own prompt (spawn.py:4392-4400 pre-fix) never told the
model that the core hooks' repo-mutation-oriented obligations (scout
before deciding, freeze a contract before any action, require a
proposal+approval gate before writing) do not apply to a consult call —
even though `consult_cmd()` itself guarantees no branch/commit/PR ever
happens. For a complex judgment question, the model plausibly followed
those heavier hooks (scouting, proposal drafting) instead of answering
directly, spending the turn budget inside `CONSULT_TIMEOUT` (180s)
without ever reaching the prompt's own trailing-JSON instruction.

## Alternatives considered (for the proposal's Rationale)

1. **Strip `core_plugin_dirs()` from consult's plugin set entirely.**
   Rejected: the core plugins also carry gates that matter for a
   judgment session (e.g. the record/board-shape guards don't apply, but
   security/no-footgun style-steering is still relevant to a design
   judgment). Removing the plugin set wholesale is a bigger structural
   change than the failure warrants, and risks silently dropping
   unrelated behavior consult never asked to lose.
2. **Prompt-level override + one bounded retry (chosen).** Cheapest
   structural fix: state explicitly, inside the prompt, that this call is
   a consult and the repo-mutation-oriented obligations do not apply, and
   add one automatic retry with a reinforced reminder before declaring
   failure. Confined to `consult_cmd()`; doesn't touch the shared plugin
   loading used by real delivery sessions.
