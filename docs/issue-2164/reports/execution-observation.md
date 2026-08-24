---
issue: 2164
role: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2164/reports/execution-observation/survey.md
    sha: 9c2de5cd80a4f50586e840c9aacf00705428b765
  - path: docs/issue-2164/proposals/execution-observation.md
    sha: 9c2de5cd80a4f50586e840c9aacf00705428b765
subject: 3ea0ec889010a8aeed7caec795261618707ad4cb (consult.py, pipeline.py)
test: two `git grep -n '룰북'` runs and one `pytest` run, executed live this session against commit 3ea0ec88
result: passed
assertedBy: execution-observation
---

# issue-2164 — execution-observation record

## What was done

Independently re-ran issue #2164's two acceptance criteria against commit
`3ea0ec889010a8aeed7caec795261618707ad4cb` (PR #2168), live in this
session, in a disposable worktree (`git worktree add /tmp/otr-verify-2164-p2
3ea0ec889010a8aeed7caec795261618707ad4cb`, removed after the runs below) —
never against implementation's own claim, and never against this branch's
own tree (pre-merge `d9a1e826`).

1. consult.py check.
canonical: git grep -n '룰북' -- consult.py, executed this session — result: PASS (0 hits).
```
$ git grep -n '룰북' -- consult.py
exit=1
```

2. pipeline.py check.
canonical: git grep -n '룰북' -- pipeline.py, executed this session — result: PASS (3 hits, each read in context this session and matched to the issue's own core-plugin-bundle exclusion clause — the `runs/rulebooks/tokenmaxxxer-core` clone/gate-loading mechanism, not the retired role-guidance framing #1955/#2164 targets).
```
$ git grep -n '룰북' -- pipeline.py
pipeline.py:380:    # 로컬 체크아웃이 없으면 룰북과 같은 길: on-the-record 소유 클론을 받아 쓴다.
pipeline.py:659:    # 룰북 게이트는 core 공유 라이브러리를
pipeline.py:661:    # 변수를 주입하지 않으면 상대 fallback 이 룰북 클론 내부를 가리켜
exit=0
```

3. Named test surface.
canonical: python3 -m pytest -q -m "not slow" gates/test_consult_gate_lib_env.py gates/test_consult_verdict_parsing.py gates/test_consult_siblings.py gates/test_requirement_intake_consult.py gates/test_consult_json_parse.py gates/test_design_research_consult.py tests/test_spawn_pipeline.py tests/test_consult_trace_root.py tests/test_spawn_consult_panel.py tests/test_spawn_judge.py, executed this session — result: PASS (167 passed, 4 xfailed, 0 failed; figures unchanged from phase 1's survey run).
```
$ python3 -m pytest -q -m "not slow" \
  gates/test_consult_gate_lib_env.py gates/test_consult_verdict_parsing.py \
  gates/test_consult_siblings.py gates/test_requirement_intake_consult.py \
  gates/test_consult_json_parse.py gates/test_design_research_consult.py \
  tests/test_spawn_pipeline.py tests/test_consult_trace_root.py \
  tests/test_spawn_consult_panel.py tests/test_spawn_judge.py
167 passed, 4 xfailed in 10.40s
```

No fix was made or attempted — this role never edits code.

## Why

canonical: docs/issue-2164/proposals/execution-observation.md ('## Rationale' section), read this session.
The proposal's rejected alternative was restating implementation's own
claimed evidence without re-running anything, rejected because
`roles/specs/execution-observation.spec.json`'s `gate_b_contrast` calls a
record with no independently-run command behind its verdict a "hollow
instance" that asserts nothing about the artifact. Item 3 above covers a
narrower, issue-named test subset than implementation's own full-suite
figure at `3ea0ec88:docs/issue-2164/reports/implementation.md`; this
record cites its own three commands above (items 1-3) rather than
implementation's figure.

## Upstream basis

- `docs/issue-2164/reports/execution-observation/survey.md`
  (`9c2de5cd80a4f50586e840c9aacf00705428b765`) — phase 1's first
  independent run of the same three commands, reproduced live above.
- `docs/issue-2164/proposals/execution-observation.md`
  (`9c2de5cd80a4f50586e840c9aacf00705428b765`) — the approved phase-1
  proposal this phase-2 write follows.
- Commit `3ea0ec889010a8aeed7caec795261618707ad4cb` on `main` (PR #2168) —
  the code under observation.

## Open findings

None.
canonical: python3 -m pytest and both git grep runs in items 1-3 above, executed this session — result: PASS for each, matching phase 1's survey figures.
resolution path: none needed — per the spec's worst-case recomputation rule (`failed > cantTell > inapplicable > untested > passed`), items 1-3 above are all `passed`, so there is no failing/cantTell entry to attach a follow-up path to.

## Next steps

None — `loop_state` is terminal (`handed-off`, this role's only terminal
value per `roles/execution-observation.json`).
