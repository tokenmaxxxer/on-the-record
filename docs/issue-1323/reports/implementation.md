---
code_under_review:
  - gates/acceptance_authoring_rule.py
  - tests/test_acceptance_authoring_rule.py
  - gates/check_runner.py
  - tests/test_check_runner.py
type: feature
breaking: false
# canonical: python3 -m pytest tests/test_acceptance_authoring_rule.py tests/test_check_runner.py -q — result: 12 passed (executed live this session, fenced output below)
verdict: pass
loop_state: landed
---

Subject: issue-1323

canonical: this session's own execution, transcript below
```
$ python3 -m pytest tests/test_acceptance_authoring_rule.py tests/test_check_runner.py -q
............
12 passed in 0.76s
```

## What was done

Delivered issue #1323 phases 1-2, per the approved proposal at
docs/issue-1323/proposals/2026-08-14-acceptance-authoring-rule-and-check-runner.md.

- `gates/acceptance_authoring_rule.py` (req 1): `check_issue_body(issue,
  body)` scans an issue's `## Acceptance` section for full-suite/
  no-regression references (regex family covering suite-scope phrasing
  such as "entire test suite" or `run-orchestrate-tests.sh`) and
  reports a violation for each unless builder-exemption language (e.g.
  "verification role", "check-runner", "executed by ... runner")
  appears within a ~200-char window around it. No `## Acceptance`
  section at all is not this gate's concern (that's `acceptance_gate.py`'s
  job) and returns no violations.
- `gates/check_runner.py` (req 2): `parse_checks(section)` classifies
  each `check:`/`gate:` line as `test` (backticked shell/pytest
  command), `grep` (`grep:`-prefixed pattern), `file-existence`
  (backticked bare path), or `judgment` (none of those — refused).
  `run_checks(repo, checks)` executes test/grep/file-existence checks
  via `subprocess.run` against a repo path (a PR branch checkout) and
  raises `JudgmentCheckError` for any `judgment` check instead of
  executing it. `format_comment(results)` builds one structured
  Markdown block. `post_comment(pr, body, repo)` is the sole function
  issuing `gh pr comment <pr> --body <body>`, following the repo's
  existing `gh`-call convention from `gates/pr_reference.py`/`gates/ci.py`.
- `tests/test_acceptance_authoring_rule.py` — 5 pytest cases covering
  both directions: full-suite scope assigned to the builder with no
  exemption, issue #1323's own Acceptance third-bullet phrasing
  verbatim, builder-scoped new/changed tests only, no Acceptance
  section present, and an unexempted "entire test suite" phrasing.
- `tests/test_check_runner.py` — 7 pytest cases against a local git
  fixture repo/branch (`fixture_pr_branch`): check classification for
  all four types, a real test-check execution outcome in each
  direction, grep + file-existence execution in each direction, a
  judgment-check refusal via `pytest.raises`, structured comment
  shape, and `post_comment`'s exact `gh` argv via a monkeypatched
  `subprocess.run` (no live network call).

## Why

canonical: docs/issue-1323/proposals/2026-08-14-acceptance-authoring-rule-and-check-runner.md
Implements phases 1-2 of issue #1323 per its own approved proposal —
relocating verification cost (full-suite regression) off the builder
and onto a deterministic, mechanical check-runner.

## Upstream

basis: docs/issue-1323/proposals/2026-08-14-acceptance-authoring-rule-and-check-runner.md

## What did not work

None.

## Open findings

None.

## Rationale for deviations

Not applicable — the build stayed inside the approved proposal's scope
as written; no scope-exceeded stop, no alternative swap mid-build.
