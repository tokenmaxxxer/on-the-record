---
status: proposed
files:
  - gates/acceptance_authoring_rule.py
  - tests/test_acceptance_authoring_rule.py
  - gates/check_runner.py
  - tests/test_check_runner.py
---

## Request

Issue #1323 phases 1-2 only: (1) an orchestrator issue-drafting gate
that rejects an Acceptance block assigning full-suite regression to the
builder; (2) a deterministic, non-LLM check-runner that executes an
issue's test/grep/file-existence Acceptance checks against a PR branch
and posts one structured PR comment, refusing judgment-shaped checks.
Phases 3-4 (spawn-on-PR, merge gate) are explicitly out of scope,
sequenced after #1320.

## Constraints

- New test files must be pytest-collectible at exactly
  `tests/test_acceptance_authoring_rule.py` and `tests/test_check_runner.py`
  (issue's own Acceptance names these paths and `python3 -m pytest`).
- Req 2's runner must be strictly mechanical: any check it cannot
  classify as test/grep/file-existence is refused with an explicit
  error, never silently skipped or judged.
- No network call inside the test suite itself — the fixture is a local
  PR branch (a local git fixture repo), not a live GitHub PR.

## Rationale

Considered extending `gates/acceptance_gate.py` in place for req 1
instead of a new module. Rejected: that module's regex set checks
artifact-reference *shape* (does the Acceptance point at something
executable), which is orthogonal to req 1's concern (*who* runs it).
The issue names a distinct test file for req 1, implying a distinct
module; conflating the two would make either regression harder to
isolate and would force one fixture set to carry two independent
concerns.

Considered folding req 2's check execution and PR-comment posting into
one function. Rejected: the issue's Acceptance describes testing
against "a fixture PR branch" — a local git fixture, not a live PR — so
the comment-posting step (a real `gh pr comment` network call) cannot
be exercised by that fixture. Splitting `run_checks()` (execution),
`format_comment()` (structured output), and `post_comment()` (the sole
`gh`-calling function, following the repo's existing
`subprocess.run(["gh", ...], cwd=root, capture_output=True, text=True)`
convention from `gates/pr_reference.py`/`gates/ci.py`) lets the test
suite exercise real execution and real formatting while leaving
`post_comment()` as a thin, separately-reviewable network boundary.

## What will be done

**Req 1 — `gates/acceptance_authoring_rule.py`:**
- `check_issue_body(issue: int, body: str) -> list[str]`, following
  `acceptance_gate.check_issue_body`'s signature/return convention.
- Detects full-suite/no-regression references in the `## Acceptance`
  section (patterns like "full suite", "full regression", "no
  regression", "entire test suite", "all tests pass", or a shell
  command invoking a suite-runner script).
- A detected full-suite reference is a violation UNLESS the same
  section, near that reference, also carries builder-exemption language
  (e.g. "not the builder", "verification role", "check-runner",
  "independent verification", "executed by ... runner").
- No full-suite reference at all (e.g. Acceptance limited to the
  builder's own new/changed tests) — no violation.
- `check(repo, issue)` wraps `gh issue view --json body` the same way
  `acceptance_gate.check(...)` does, for CLI parity.

**Req 2 — `gates/check_runner.py`:**
- `parse_checks(section: str) -> list[dict]` — extracts each
  `check:`/`gate:` line or backticked `test/`/`gates/` path reference
  from an Acceptance section (reusing `acceptance_gate`'s admission
  regex) and classifies it: `test` (backticked shell/pytest command),
  `grep` (`grep:`-prefixed pattern), `file-existence` (bare file path,
  no command), or `judgment` (admitted as "looks mechanical" by the
  first pass but resolves to none of the three — refused).
- `run_checks(repo: Path, checks: list[dict]) -> list[dict]` — executes
  `test`/`grep`/`file-existence` checks against `repo` (a PR branch
  checkout) via `subprocess.run`, records pass/fail + captured output
  per check; raises/records an explicit error for any `judgment` check
  instead of running it.
- `format_comment(results: list[dict]) -> str` — one structured Markdown
  comment body (per-check status line + summary), matching the issue's
  "posts the results as a PR comment" / "posts one structured result
  comment" wording.
- `post_comment(pr: int, body: str, repo: Path) -> bool` — the sole
  function issuing `gh pr comment <pr> --body <body>`, following the
  repo's existing `gh`-call convention.

**Tests** (both `tests/`, pytest-collectible, plain `def test_*():` +
`assert`, matching `tests/test_gates.py`'s style):
- `tests/test_acceptance_authoring_rule.py` — fixture Acceptance bodies
  in both directions: one assigning full-suite regression to the
  builder with no exemption (violation), one with the issue's own
  exemption phrasing (no violation), one with only builder-scoped
  new/changed tests (no violation, no full-suite reference at all).
- `tests/test_check_runner.py` — a local git fixture repo/branch with
  test/grep/file-existence checks executed for real via `run_checks`,
  asserting pass/fail classification and `format_comment` output shape;
  a judgment-shaped check asserted to raise/produce the explicit refusal
  error. `post_comment` tested only for the exact `gh` argv it builds
  (no real network call).

## Out of scope

- Phase 3 (spawn-on-PR for verification roles) and phase 4 (merge gate)
  — sequenced after #1320 per the issue body.
- Wiring `check_runner.py` into any CI/PR-creation trigger — that is
  phase 3/4 territory.
- Modifying `gates/acceptance_gate.py` itself.

## How you'll know it worked

```
python3 -m pytest tests/test_acceptance_authoring_rule.py
python3 -m pytest tests/test_check_runner.py
```
both exit 0, exercising both directions of req 1's fixture bodies and
req 2's test/grep/file-existence execution + judgment-check refusal
against a fixture PR branch.
