# Conformance-review survey — issue-1097 (phase 1)

## Board condition

canonical: git log origin/main --oneline (read live this session) — b9c12c36
(PR #1103, phase-1 fix) and ad2323e9 (PR #1104, phase-2 delivery) are both
merged to main; commit a19456bf28abddca3429d644fd778c52fa790315 is the
implementation commit. No conformance-review record for this subject
exists yet (checked: `docs/issue-1097/reports/` holds only
`implementation.md` and `implementation/`, not a `conformance-review.md`).
Board condition satisfied.

## Spec and artifact identified

- Spec: issue #1097 body (root-cause + fix consult's JSON-parse failure;
  Acceptance section; `requirement: northpole req#1`).
- Artifact: `spawn.py`'s `consult_cmd()` / `_parse_consult_verdict()` /
  `_consult_cmd_and_env()`, and `gates/test_consult_verdict_parsing.py`.
- Upstream design basis:
  `docs/issue-1097/proposals/consult-verdict-parse-fix.md` (approved,
  landed as PR #1103); `docs/issue-1097/reports/implementation.md`
  (phase-2 delivery report, PR #1104).

## What phase 2 will check against

1. Issue #1097 Acceptance bullets (three): test coverage against a
   captured real transcript; live smoke run; empty-state trace with
   diagnosable reason.
2. `requirement: northpole req#1` (오케스트레이션 완주 — consult is a
   required step in issue drafting).
3. The approved proposal's "How you'll know it worked" section (three
   bullets, same shape as the issue Acceptance section).

## Live re-check against current main (not just the landing-time claim)

canonical: `python3 gates/test_consult_verdict_parsing.py` executed live
this session against `origin/main`'s `spawn.py` +
`gates/test_consult_verdict_parsing.py` (via `git checkout origin/main --
spawn.py gates/test_consult_verdict_parsing.py`, reverted afterward with
`git checkout HEAD --`):

```
$ python3 gates/test_consult_verdict_parsing.py
ok - t_parses_captured_real_transcript
ok - t_prompt_overrides_repo_mutating_core_directives
Traceback (most recent call last):
  ...
  File ".../gates/test_consult_verdict_parsing.py", line 84, in t_retries_once_and_recovers_when_first_attempt_has_no_json
    assert len(calls) == 2, f"expected exactly one retry, got {len(calls)} attempts"
AssertionError: expected exactly one retry, got 4 attempts
```

canonical: docs/issue-1097/reports/implementation.md lines 24-33, read
directly this session — its pasted transcript shows all 4 named cases
(`t_parses_captured_real_transcript`,
`t_prompt_overrides_repo_mutating_core_directives`,
`t_retries_once_and_recovers_when_first_attempt_has_no_json`,
`t_still_none_when_no_json_present`) as `ok` at commit a19456b (landing
time, 2026-08-12). The live re-run above, same script against `origin/main`
HEAD today, stops at the 3rd case with an AssertionError — the two states
diverge.

canonical: `git show origin/main:spawn.py` read directly this session —
`_commit_consult_trace()` at spawn.py:4626 and `consult_cmd()`'s `finally`
block at spawn.py:4776-4778 both call `subprocess.run(["git", ...])`

Root cause of the divergence: issue #1134 (northpole req#2, "no record
with only local uncommitted state") landed `_commit_consult_trace()`
after issue-1097's fix — it runs two more `subprocess.run(["git", ...])`
calls (`git add`, `git commit`) inside `consult_cmd()`'s `finally` block.
The test's `fake_run` monkeypatches `spawn.subprocess.run` globally (not
just the consult-session call site), so those two trace-commit calls are
also captured by the test's `calls.append(...)`, inflating the
expected-2 count to 4. This is exactly the interaction the review role
exists to catch: two separately-approved changes (#1097, #1134), each
internally correct, that now conflict at their shared call site.

canonical: `python3 -m pytest tests/test_spawn.py -k "ConsultCmd or ConsultVerdictParsing" -q`
executed live this session against `origin/main` the same way:

```
........                                                                 [100%]
8 passed, 477 deselected
```

canonical: `git show origin/main:tests/test_spawn.py` read directly this
session, `ConsultCmd` class (lines 9428-9600) — grep over that range for
`len(calls)` and `assertEqual.*len` returned no match

The `ConsultCmd` class carries no retry-call-count assertion — only
`gates/test_consult_verdict_parsing.py`'s standalone
`t_retries_once_and_recovers_when_first_attempt_has_no_json` asserts
`len(calls) == 2`. So the pytest-side check the implementation report
also cited does not exercise the broken assertion, and stays green even
though the gates/ script does not.

## Scout skip record

Skip condition: "the spec literally leaves no design decision open."
Extracting a fixed requirement list from issue #1097's stated Acceptance
bullets + northpole req#1 is mechanical enumeration, not a build with an
open design choice — no product/comparable-system scouting applies to a
conformance-review requirement-list extraction. Skipped on this condition.
