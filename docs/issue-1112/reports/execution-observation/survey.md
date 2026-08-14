# issue-1112 execution-observation — current-state survey

## Scope statement

Observed: the `implementation` role's PR #1119 ("issue-1112: skip
self-hosted-hook injection at judgment-only consult call sites"), its two
commits `be8cf825` and `9d72954a`, and its own record
`docs/issue-1112/reports/implementation.md`, all on issue #1112, against
requirement northpole req#3 (real-wired verification).

canonical: `gh pr view 1119 --json number,title,body,mergedAt,commits,files,state` (this
session) — PR #1119, MERGED at 2026-08-13T00:24:30Z.

derived: `gh pr view 1119 --json commits --jq '.commits | length'`
```
2
```

derived: `gh pr view 1119 --json files --jq '.files | length'`
```
4
```

Files changed: `docs/issue-1112/reports/implementation.md`,
`docs/reports/consult-log.md`, `gates/test_consult_json_parse.py`,
`spawn.py`.

Fresh-eyes ordering: `gh pr diff 1119` (full diff) was read before this
session read the implementation role's own record narrative in prose
form — the diff's actual hunks, not that role's framing, set the scope
above.

Scout skip: this observation task is not product/design-shaped — there is
no exemplar field to sweep for judging whether another role's landed fix
is sound. Per scout-directive's mandatory skip conditions, this counts as
a task where "the spec literally leaves no design decision open."

## Research (discovery-over-guessing)

canonical: `gh issue view 1112 --json body,comments` (this session, read
in full) — issue body, the narrowing comment
(https://github.com/tokenmaxxxer/on-the-record/issues/1112#issuecomment-5270529902),
two "Judgment opened → escalate" delegated-judgment comments, the
`APPROVE issue-1112/implementation` comment
(https://github.com/tokenmaxxxer/on-the-record/issues/1112#issuecomment-5274308235),
and the phase-2-delivered/merge comment
(https://github.com/tokenmaxxxer/on-the-record/issues/1112#issuecomment-5274361105).

canonical: comment body at
https://github.com/tokenmaxxxer/on-the-record/issues/1112#issuecomment-5274308371,
read this session — its claim that "the orchestrator's own consult attempt
at 2026-08-13T00:15:38 UTC ... failed with the same symptom" is the
observed role's own assertion inside its issue comment, not independently
re-verified by this session (that timestamp's trace line is not addressed
by this survey's own command output below). mode: asserted.

canonical: `gh pr diff 1119` (this session, read in full) — `role_settings()`
gains `inject_self_hosted_hooks: bool = True` (spawn.py:476-477, hunk
touching lines 473-486); the merge gate moved from `if cwd is not None:`
to `if cwd is not None and inject_self_hosted_hooks:` (spawn.py:622→632
hunk); `consult_cmd()` (hunk at old spawn.py:4377) and
`_run_panel_session()` (hunk at old spawn.py:4513) both switched to
`role_settings(role, cwd, inject_self_hosted_hooks=False)`; new file
`gates/test_consult_json_parse.py` (165 added lines) with three tests.

canonical: `docs/issue-1112/proposals/2026-08-13-consult-self-hosted-hook-skip.md`
and `docs/issue-1112/reports/implementation/survey.md` (this session, read
in full) — the observed role's own phase-1 record.

canonical: `docs/issue-1112/reports/implementation.md` (this session, read
in full) — the observed role's phase-2 record, read after the diff per
the ordering rule above.

canonical: `gh pr view 1119 --json reviews` (this session) — empty list,
i.e. no formal PR-review Approve; approval for the observed PR ran through
single-account mode (the issue-comment path) instead.

## Verification already run this session (diff-scope-admissible)

canonical: `python3 gates/test_consult_json_parse.py` (this session, run
inside `git worktree add /tmp/wt1112 be8cf825`) — result: passed.

derived: `python3 gates/test_consult_json_parse.py` (at commit be8cf825)
```
ok - t_both_attempts_exhausted_raises_with_reported_symptom
ok - t_consult_cmd_settings_never_carry_self_hosted_hooks
ok - t_run_panel_session_settings_never_carry_self_hosted_hooks
3/3 passed
```

canonical: `python3 gates/test_consult_verdict_parsing.py` (this session,
same worktree at commit be8cf825) — result: passed.

derived: `python3 gates/test_consult_verdict_parsing.py` (at commit be8cf825)
```
ok - t_parses_captured_real_transcript
ok - t_prompt_overrides_repo_mutating_core_directives
ok - t_retries_once_and_recovers_when_first_attempt_has_no_json
ok - t_still_none_when_no_json_present
4/4 passed
```

mode: command.

canonical: `python3 gates/test_consult_json_parse.py` (this session, run
against current `main` at `2e51bd92`) — result: failed.

derived: `python3 gates/test_consult_json_parse.py` (on main, 2e51bd92)
```
AssertionError: expected exactly one retry, got 4 attempts
```

canonical: `git log --oneline -- gates/test_consult_json_parse.py` (this
session) — shows two later commits touching that file, `14ec8d4f`
(issue-1123) and `74e40109` (issue-1313), neither of which is #1119's own
commit. This is a post-merge drift fact, not (on the evidence gathered so
far) a deficiency in the observed PR's own diff hunks.

## Diff-scope note

All `spawn.py` and `gates/test_consult_json_parse.py` citations above are
anchored to hunks `gh pr diff 1119` actually shows changed (the
`role_settings()` signature hunk, the `cwd is not None and
inject_self_hosted_hooks` hunk, the two call-site hunks in `consult_cmd()`
and `_run_panel_session()`, and the new test file in full). No citation in
this survey references a file:line outside those hunks as if it were
in-scope evidence.
