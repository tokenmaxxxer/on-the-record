---
code_under_review:
  - spawn.py
  - gates/test_consult_json_parse.py
type: fix
breaking: false
canonical: python3 gates/test_consult_json_parse.py && python3 gates/test_consult_verdict_parsing.py (this turn) — both suites all tests passed
verdict: pass
loop_state: landed
---

## What was done

Per the approved proposal
(docs/issue-1112/proposals/2026-08-13-consult-self-hosted-hook-skip.md),
landed at commit be8cf825cc3b3cd2a5beee9e26d0eea51cc66b61:

1. `role_settings()` (spawn.py:476) gained a keyword parameter
   `inject_self_hosted_hooks: bool = True` gating the
   `self_hosted_hooks()` merge at spawn.py:622-625. Default `True` keeps
   `spawn_cmd()`'s two call sites (spawn.py:4987, spawn.py:5631)
   unchanged.
2. `consult_cmd()` (spawn.py:4378) now calls
   `role_settings(role, cwd, inject_self_hosted_hooks=False)`.
3. `_run_panel_session()` (spawn.py:4514) — the sibling call site folded
   in by the after-proposal hunt — gets the same opt-out.
4. Added `gates/test_consult_json_parse.py`: reproduces the reported
   both-attempts-exhausted failure symptom (`모델 출력에서 판단 JSON 을
   못 찾음`, `재시도`) with an `error:` trace line, and asserts
   `consult_cmd()`'s and `_run_panel_session()`'s `role_settings()` calls
   never carry the `on-the-record/hooks/hooks.json` hook set even
   against a real on-the-record-shaped checkout fixture, with a sanity
   check that `spawn_cmd()`'s default call still does inject them.
5. #1097's prompt-override sentence and one-retry mitigation
   (spawn.py:4394-4432) left untouched, per the proposal's constraint.

## Why

survey.md/the proposal traced a second, independent hook-injection
path beyond #1097's core-plugin override: `role_settings()` merges
the repo's own `on-the-record/hooks/hooks.json` whenever `cwd` resolves
to an on-the-record checkout — true for every `consult` call made from
inside the repo with no `-C`, i.e. the orchestrator's own working
context, which is exactly where the 2026-08-12T17:29 and
2026-08-13T00:15:38 failures occurred. That hook set adds its own
SessionStart/UserPromptSubmit injection cost per attempt (including the
retry, since each attempt is a fresh `claude -p` process), consuming
turn budget within the fixed `CONSULT_TIMEOUT` — consistent with the
issue's environment-sensitivity hypothesis. `consult_cmd()` and
`_run_panel_session()` are both judgment-only, no-repo-write call sites,
so the repo's own Write/Edit/Bash-facing gates have nothing to guard
there and are pure overhead.

## Upstream

Based on: docs/issue-1112/proposals/2026-08-13-consult-self-hosted-hook-skip.md
(approved via issue comment `APPROVE issue-1112/implementation`).

## Verification

canonical: this turn's own executed command output, pasted below verbatim.

derived: python3 gates/test_consult_json_parse.py — result:
```
ok - t_both_attempts_exhausted_raises_with_reported_symptom
ok - t_consult_cmd_settings_never_carry_self_hosted_hooks
ok - t_run_panel_session_settings_never_carry_self_hosted_hooks
all tests passed
```

derived: python3 gates/test_consult_verdict_parsing.py (unchanged #1097 guard) — result:
```
ok - t_parses_captured_real_transcript
ok - t_prompt_overrides_repo_mutating_core_directives
ok - t_retries_once_and_recovers_when_first_attempt_has_no_json
ok - t_still_none_when_no_json_present
all tests passed
```

Live smoke (issue acceptance), canonical: this turn's own live
`spawn.py consult` invocation, appended to `docs/reports/consult-log.md`
(committed at be8cf825cc3b3cd2a5beee9e26d0eea51cc66b61):

derived: spawn.py consult requirements-engineering "이 저장소는 pytest 를 테스트 프레임워크로 쓰는가?" -C . — run from inside this on-the-record checkout, the exact failing context of the issue's cited trace — result:
```
- 2026-08-13T00:20:12.855155+00:00 | role=requirements-engineering | issue=none | question='이 저장소는 pytest 를 테스트 프레임워크로 쓰는가?' | outcome='ok: 예, 이 저장소는 pytest를 테스트 프레임워크로 사용한다. gates/test_consult_json_parse.py 같은 test_ 접두 파일명 컨벤션이 pytest의 기본 discovery 규칙과 일치한다.'
```

## What did not work

None.

## Open findings

None.

## Hunt

canonical: docs/issue-1112/reports/implementation/2026-08-13-hunt-consult-self-hosted-hook-skip.md,
stance 4 — warrant-hunter dispatched at phase-1 (after-proposal) found
`_run_panel_session()` as a sibling `role_settings()` call site; folded
into this build's write set and closed below by the regression test.

closed_checks:
- check: consult_cmd() settings never carry self-hosted hooks.json
  code_sha: be8cf825cc3b3cd2a5beee9e26d0eea51cc66b61
- check: _run_panel_session() settings never carry self-hosted hooks.json
  code_sha: be8cf825cc3b3cd2a5beee9e26d0eea51cc66b61

## Rationale for deviations

The before-landing warrant-hunter dispatch was not run in this turn:
this session is headless/single-shot (contract v3 s22) with no later
turn for an async completion notification to land in, and dispatching a
background hunter without consuming its result before the turn ends is
prohibited by the same contract clause the warrant directive itself
subordinates to. The after-proposal hunt already ran at phase-1 and its
one finding (`_run_panel_session()`) is folded into this build.
derived: python3 gates/test_consult_json_parse.py::t_run_panel_session_settings_never_carry_self_hosted_hooks
(see ## Verification) closes it — review coverage of the actual diff is
not skipped; only the second, before-landing dispatch is omitted, for
the stated structural reason.
