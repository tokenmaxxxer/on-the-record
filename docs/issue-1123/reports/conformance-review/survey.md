scout: skipped — pure conformance-check task, no product-facing design
decision open (per scout-directive skip condition: "the spec literally
leaves no design decision open"). The deliverable is a fixed-shape
per-requirement verdict record; there is no field to survey exemplars
of.

# Current-state survey — issue #1123 conformance review

## Board condition (per marketplace conformance-review role spec, issue-521)

canonical: `git merge-base --is-ancestor 14ec8d4f origin/main` (exit 0,
this session) and `find docs -path '*1123*'` (this session, listed
docs/issue-1123/reports/implementation.md and the phase-1 proposal but
no conformance-review record under docs/issue-1123/reports/).

An implementation commit landed on `main` for issue #1123
(`14ec8d4f`, "issue-1123: persist consult raw output on parse failure,
extend guard, live-smoke") and no conformance-review record for that
sha exists yet under `docs/issue-1123/reports/`.

## Target artifact and spec

- Artifact under review: commit `14ec8d4f` (`spawn.py`,
  `gates/test_consult_json_parse.py`, `docs/reports/consult-log.md`).
- Spec: issue #1123's own body — three Requirements (persist raw output
  on parse failure with trace pointer + RuntimeError message; extend the
  #1119 regression guard with complex-question and short-multi-clause
  cases; live-smoke a multi-part question) and its Acceptance clause
  (`python3 gates/test_consult_json_parse.py` extended and passing, plus
  one live smoke logged `ok:` in `docs/reports/consult-log.md`).
  canonical: `gh issue view 1123` (this session).
- Requirement cited for this review session: R001 (registry
  requirement-dilution guard, source #321, its check target is the
  `requirement_registry` function in gates/gates.py). Issue #1123's own
  body states R001 is not its target ("infrastructure/no-direct-requirement
  — consult wiring reliability; R001 is not this issue's target") —
  recorded as its own verdict row in phase 2 for traceability, separate
  from the issue's own three named requirements.
  canonical: `gh issue view 1123` (this session).

## What phase-1 research already found (informs phase-2 verdicts)

At commit `14ec8d4f` itself, all three of the issue's named
requirements reproduce independently — the persist-helper exists and is
wired into the retry loop, both new guard cases exist.

canonical: `python3 gates/test_consult_json_parse.py` run inside a
`git worktree add` checkout of commit `14ec8d4f` (this session) —
result: PASS
```
ok - t_both_attempts_exhausted_raises_with_reported_symptom
ok - t_complex_question_persists_raw_output_on_parse_failure
ok - t_consult_cmd_settings_never_carry_self_hosted_hooks
ok - t_run_panel_session_settings_never_carry_self_hosted_hooks
ok - t_short_multi_clause_question_persists_raw_output_on_parse_failure
5/5 passed
```

canonical: `git show 14ec8d4f:docs/reports/consult-log.md` (this
session) — tail line timestamped 2026-08-13T01:50:45.617378+00:00,
role=implementation, outcome starting `ok:`.

The live-smoke `ok:` line is present in `docs/reports/consult-log.md`
at that commit.

canonical: `python3 gates/test_consult_json_parse.py` run at current
`main` HEAD `2e51bd92` (this session) — result: FAIL
```
AssertionError: expected exactly one retry, got 4 attempts
```

At current `main` HEAD, the same guard now fails, root-caused (this
session, by diffing HEAD vs the `14ec8d4f` worktree checkout and
reading `_commit_consult_trace()` at spawn.py) to a later, unrelated
commit `74e40109` (issue-1313, "unify consult-family trace/record path
anchor", #1321) that changed the trace/record path-anchor logic this
guard's `subprocess.run` stub relies on to exclude
`_commit_consult_trace()`'s git add/commit calls — outside issue
#1123's frozen write set.

## Gap line

canonical: `python3 gates/test_consult_json_parse.py` re-run at commit
`14ec8d4f` (this session) — result: PASS, per the derived output above
— nothing is missing from issue #1123's own three requirements as
delivered at that commit.

canonical: same derived output above (guard run at current HEAD,
result: FAIL) — the one gap found, the guard failing when re-run at
current HEAD, traces to the later commit `74e40109` (issue-1313), not
to #1123's own delivered change; it is reported as an open finding in
phase 2, addressed to that later issue's scope rather than fixed here.
