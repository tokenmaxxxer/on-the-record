# Current-state survey — execution-observation for issue #1123

## Scope statement

Observed role: `implementation`. Observed subject: the work landed on
branch `issue-1123/implementation` for issue #1123, delivered across two
PRs — phase-1 proposal PR #1126 and phase-2 delivery PR #1136.
canonical: `gh pr list --search "issue-1123" --state all --json
number,title,headRefName,state,url` (this session) — both PRs report
`"state":"MERGED"`; PR #1136's merge commit is
`7de5c9fc02ee9f8bf4508e2c93bea1630a204011`, per `gh pr view 1136 --json
mergeCommit` (this session).

Observing role/session: this `execution-observation` session, issue
#1123, branch `issue-1123/execution-observation`. No prior
execution-observation record exists for this commit sha.
canonical: `find docs/issue-1123 -type f` (this session, on this branch)
— output listed only `implementation`-role files (survey, hunt record,
deviation-log, proposal, and `reports/implementation.md`); no
`execution-observation.md` present.

## What was read this session (fresh-eyes order)

1. `gh issue view 1123` — issue body (root-cause + fix + regression-guard
   requirements; Requirements line: `infrastructure/no-direct-requirement
   — consult wiring reliability; R001 is not this issue's target.`) and
   all 14 issue comments, including the two `APPROVE issue-1123/implementation`
   comments (2026-08-13T00:47:17Z, 2026-08-13T02:00:58Z) and their
   immediately-following "Re the APPROVE above" scope-restatement comments,
   both from `JiwonJung94`.
   canonical: `gh issue view 1123 --json comments -q '.comments[] |
   {author: .author.login, body: .body, createdAt: .createdAt}'` (this
   session) — both APPROVE bodies are the exact string
   `APPROVE issue-1123/implementation`.
2. `gh pr view 1126 --json commits,files,body,reviews` — phase-1 proposal
   PR metadata: 2 commits (`b6a5a2d6`, `a20a3e66`), 3 files added (survey,
   hunt record, proposal), `"reviews":[]` (approval came via the issue
   comment, single-account mode since PR author = approver =
   `JiwonJung94`). canonical: that command's own output (this session).
3. `gh pr view 1136 --json commits,mergeCommit,files,body,reviews` — phase-2
   delivery PR metadata: 2 commits (`14ec8d4f`, `5ec65924`), 5 files
   changed, merge commit `7de5c9fc`, `"reviews":[]` (same single-account
   approval path). canonical: that command's own output (this session).
4. `gh pr diff 1136` — the full diff, read before reading the observed
   role's own record narrative in prose: `spawn.py` (new
   `_persist_consult_raw_output()` helper hunk, and the `consult_cmd()`
   retry-loop hunk at diff-context line ~4436-4459 of the new file),
   `gates/test_consult_json_parse.py` (two new test functions plus a
   `_persist_raw_under()` fixture and a save/restore addition to the
   pre-existing test), `docs/reports/consult-log.md` (one appended
   live-smoke trace line, timestamp `2026-08-13T01:50:45.617378+00:00`),
   and the new file `docs/issue-1123/reports/implementation.md` in full
   (its own record, read as part of the diff). canonical: `gh pr diff
   1136` output (this session).
5. `roles/specs/execution-observation.spec.json` (read directly this
   session, file:1-42) — this role's own spec: EARL-shaped required
   fields (`subject`, `test`, `result`, `assertedBy`, `mode`), the
   worst-case recomputation rule for `outcome`, and the `gate_b_contrast`
   hollow-instance rule (a genuine observation needs at least one
   non-`untested`/non-`cantTell` result entry tied to a command actually
   run).
6. `docs/specs/approvers.md` (read directly this session, file:1-2) —
   lists `JiwonJung94` and `jjongkwann` as the two approver accounts.

## Diff hunks read (diff-scope rule)

canonical: `gh pr diff 1136` (this session, full output read).

- `spawn.py`: new function `_persist_consult_raw_output()` (added, ~17
  lines, right after `_parse_consult_verdict`); modified hunk inside
  `consult_cmd()`'s retry loop (the `for attempt_prompt in (...)` loop
  rewritten to `for attempt_num, attempt_prompt in enumerate(...)`, adding
  `raw_path = _persist_consult_raw_output(...)` and the backtick-quoted
  `attempts_exhausted` f-string on parse failure).
- `gates/test_consult_json_parse.py`: modified hunk on the pre-existing
  `t_both_attempts_exhausted_raises_with_reported_symptom` (added
  `orig_persist_raw`/stub/restore lines); two new test functions added in
  full (`t_complex_question_persists_raw_output_on_parse_failure`,
  `t_short_multi_clause_question_persists_raw_output_on_parse_failure`)
  plus new fixture helpers (`_persist_raw_under`, `_fake_run_long_no_json`,
  `_fake_run_short_multi_clause_no_json`).
- `docs/reports/consult-log.md`: one added line (the live-smoke trace).
- `docs/issue-1123/reports/implementation.md`: added in full (144 lines) —
  the observed role's own record, not code; its content is evidence for
  the trajectory/step verdicts, not itself a code hunk.

No other hunks in PR #1136's diff were read as evidence beyond what is
listed above — the diff's file list (`gh pr view 1136 --json files`, this
session) contains no additional files.

## Scouting

Scout skip applies: the spec (`roles/specs/execution-observation.spec.json`,
file:25, `gate_c_status`) states this role's judgment reduces to applying
the worst-case recomputation rule over already-run test claims and does
not decide what to observe — no design decision is open in this survey, no
product surface, no exemplar field, no build-direction choice. Skip
condition used: "the spec literally leaves no design decision open"
(scout-directive's second skip condition). No sweep was run.
