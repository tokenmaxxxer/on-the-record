---
code_under_review:
  - spawn.py
  - gates/test_consult_verdict_parsing.py
type: fix
breaking: false
# canonical: python3 gates/test_consult_verdict_parsing.py — result: all cases passed (executed live this session, fenced output below)
verdict: pass
loop_state: landed
---

Subject: issue-1097

## What was done

canonical: gh pr view 1103 — result: state=MERGED (read live this session); git log --oneline -1 on this branch — result: commit a19456b already present

Approved phase-1 proposal PR #1103 (merged) already carried the code fix
and its regression test on this branch (commit a19456b,
docs/issue-1097/proposals/consult-verdict-parse-fix.md). Phase-2 for this
session applies the approved fix and proves it with a live
`spawn.py consult` smoke run, per the phase-2 ask.

- Ran the existing regression suite:

```
$ python3 gates/test_consult_verdict_parsing.py
ok - t_parses_captured_real_transcript
ok - t_prompt_overrides_repo_mutating_core_directives
ok - t_retries_once_and_recovers_when_first_attempt_has_no_json
ok - t_still_none_when_no_json_present
4/4 passed
```

```
$ python3 -m pytest tests/test_spawn.py -k "ConsultCmd or ConsultVerdictParsing" -q
8 passed, 477 deselected
```

- Executed a live end-to-end smoke run against the real model, using a
  complex multi-tradeoff judgment question (the failure shape from the
  original bug report):

```
$ python3 spawn.py consult requirements-engineering "issue-1097 phase-2 smoke: ..."
{
  "answer": "...",
  "confidence": "medium",
  "caveats": [...]
}
```

canonical: docs/reports/consult-log.md 2026-08-12T07:53:18Z entry, read directly right after the run above — outcome='ok: SLA 수치는 초안에 바로 넣지 말고 ...'

The run returned a parsed judgment JSON (answer/confidence/caveats) and
traced to docs/reports/consult-log.md with `outcome='ok: ...'` — the
same trace format the issue's "empty state" acceptance criterion
requires, confirming the parser no longer fails on this question shape.

## Why

requirement: northpole req#1 (오케스트레이션 완주 — consult 는 이슈 드래프트의
필수 단계). A broken consult parser blocks that required step; the fix
and its proof close the loop the issue asked for.

## Upstream / basis

canonical: gh pr view 1103 — result: state=MERGED, at commit a19456bf28abddca3429d644fd778c52fa790315 (read live this session)

docs/issue-1097/proposals/consult-verdict-parse-fix.md (approved,
merged as PR #1103); commit a19456bf28abddca3429d644fd778c52fa790315.

## What did not work

None.

## Open findings

None.
