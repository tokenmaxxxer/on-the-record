# Issue #2164 — execution-observation current-state survey (phase 1)

Scope: role execution-observation, session issue-2164/execution-observation, issue #2164
("consult.py: rename stale '룰북' terminology to skill-repo, in prompt text and docstrings").
This role is PR-triggered (`gates/spawn_on_pr.py`'s `PR_TRIGGERED_ROLES`) — spawned once an
executable artifact lands with no execution-observation record yet for that commit sha
(`roles/execution-observation.json` board_condition).

canonical: gh issue view 2164 --json body,comments && gh pr view 2168 --json title,body,state,commits, both executed this session — result: PASS (issue body carries a `## Acceptance` section, quoted in context below; PR #2168 has two commits, 190b442f the rename and a453e587 a deviation log).

canonical: git log origin/main --oneline --grep=2164, executed this session — result: PASS (commit 3ea0ec88 "issue-2164: rename stale '룰북' terminology to skill-repo in consult.py/pipeline.py (#2168)" is present on origin/main; state field from the citation above reads MERGED, not merely open).

## Skip condition (survey-order / scout-order directives)

No design decision is open here for this role to survey-and-decide.
canonical: roles/specs/execution-observation.spec.json field gate_c_status, read this session on this branch (the field's own text: "this role's judgment reduces to applying the worst-case recomputation rule over already-run test claims; it does not decide what to observe"). The issue's own `## Acceptance` section already fully specifies what to check; this step's job is independent re-execution against commit 3ea0ec88, not authoring a new design.

## Code under observation (read/run this session, never re-designed here)

- `consult.py`, `pipeline.py` — the two files issue #2164 names — at commit
  3ea0ec88:pipeline.py:1 (PR #2168's own merge commit).
- implementation's own claimed acceptance evidence, at commit
  3ea0ec88:docs/issue-2164/reports/implementation.md:1, read as a claim to independently
  check, never as ground truth (this role's directive: never accept a prior record's claim
  about what shipped code does in place of running it).

## Independent verification run this session (evidence basis for phase 2)

canonical: git worktree add /tmp/otr-verify-2164 origin/main, executed this session — result: PASS (worktree created at commit 3ea0ec88; this branch's own tree still sits on the pre-merge d9a1e826, so this role checks commit 3ea0ec88 directly rather than its own tree).
```
$ git worktree add /tmp/otr-verify-2164 origin/main
HEAD의 현재 위치는 3ea0ec88입니다 issue-2164: rename stale '룰북' terminology to skill-repo in consult.py/pipeline.py (#2168)
```

1. consult.py check.
canonical: git grep -n '룰북' origin/main -- consult.py, executed this session — result: PASS (0 hits, matches issue #2164 acceptance criterion 1 for this file).
```
$ git grep -n '룰북' origin/main -- consult.py
(no output, exit 1)
```

2. pipeline.py check.
canonical: git grep -n '룰북' origin/main -- pipeline.py, executed this session — result: PASS (3 hits, shown verbatim below).
```
$ git grep -n '룰북' origin/main -- pipeline.py
origin/main:pipeline.py:380:    # 로컬 체크아웃이 없으면 룰북과 같은 길: on-the-record 소유 클론을 받아 쓴다.
origin/main:pipeline.py:659:    # 룰북 게이트는 core 공유 라이브러리를
origin/main:pipeline.py:661:    # 변수를 주입하지 않으면 상대 fallback 이 룰북 클론 내부를 가리켜
```
canonical: 3ea0ec88:pipeline.py:380, 3ea0ec88:pipeline.py:659, 3ea0ec88:pipeline.py:661, read in context this session — result: PASS (all three name the CORE plugin bundle's own on-disk clone/gate-loading mechanism: line 380's comment sits directly above code building `_sp.ROOT / "runs" / "rulebooks" / "tokenmaxxxer-core"`; lines 659 and 661 describe that same clone's resolution via `${CLAUDE_PLUGIN_ROOT_CORE:-...}/core`. The issue body's own exclusion clause covers this exactly: "Do not touch `runs/rulebooks/tokenmaxxxer-core` or any other core-plugin-bundle path/string -- that is a distinct, legitimate concept and out of scope" — distinct from the retired "role guidance = rulebook" framing #1955/#2164 targets).

3. Test suite — the consult/judge/panel/pipeline test files issue #2164's own acceptance names as the modified-behavior surface.
canonical: python3 -m pytest -q -m "not slow" gates/test_consult_gate_lib_env.py gates/test_consult_verdict_parsing.py gates/test_consult_siblings.py gates/test_requirement_intake_consult.py gates/test_consult_json_parse.py gates/test_design_research_consult.py tests/test_spawn_pipeline.py tests/test_consult_trace_root.py tests/test_spawn_consult_panel.py tests/test_spawn_judge.py (run in /tmp/otr-verify-2164 this session) — result: PASS (167 passed, 4 xfailed, 0 failed).
```
$ cd /tmp/otr-verify-2164 && python3 -m pytest -q -m "not slow" \
  gates/test_consult_gate_lib_env.py gates/test_consult_verdict_parsing.py \
  gates/test_consult_siblings.py gates/test_requirement_intake_consult.py \
  gates/test_consult_json_parse.py gates/test_design_research_consult.py \
  tests/test_spawn_pipeline.py tests/test_consult_trace_root.py \
  tests/test_spawn_consult_panel.py tests/test_spawn_judge.py
167 passed, 4 xfailed in 9.01s
```

This is a narrower file set than implementation's own claim at
3ea0ec88:docs/issue-2164/reports/implementation.md:1 (a full-suite "194 passed, 0 failed, 4
xfailed" figure) — this session ran only the files the issue's own acceptance criterion names
by role (consult/judge/panel/pipeline), not implementation's exact list; zero failures on that
named subset independently backs acceptance criterion 2 for that scope, on this session's own
run rather than implementation's own number.

## Gap / what phase 2 hands off

canonical: this session's own transcript of the three fenced command runs above (two grep, one pytest) — result: PASS for each. This session's own re-run of both acceptance criteria against commit 3ea0ec88 agrees with the claim at commit 3ea0ec88:docs/issue-2164/reports/implementation.md:1; this role never edits code or the observed record regardless of outcome.

Phase 2 (after `APPROVE issue-2164/execution-observation`) writes this role's own record at
its write-scope path, docs/issue-2164/reports/execution-observation.md (phase 2, not created
yet on this branch's git history — no forward reference), citing this exact evidence — the
same three commands and fenced output above — and setting `result:` to the EARL enum's
affirmative value and `loop_state:` to this role's only terminal value, handed-off, per
`roles/execution-observation.json`.
