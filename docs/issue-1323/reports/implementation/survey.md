Subject: issue-1323 (phases 1-2 only)

## Write set (new files, not yet created)

- gates/acceptance_authoring_rule.py — req 1 gate.
- tests/test_acceptance_authoring_rule.py — req 1 fixtures.
- gates/check_runner.py — req 2 deterministic executor/comment formatter.
- tests/test_check_runner.py — req 2 fixtures.

(paths listed as plain text, not backtick-quoted, since none exist yet
on disk — this is the intended write set, not a claim about current
state.)

Phases 3-4 (spawn-on-PR, merge gate) are out of scope per the issue
body's own phasing note.

## Current state

canonical: gates/acceptance_gate.py:20-33,44 (read this session)
derived: grep -n "def check_issue_body\|_ARTIFACT_REF\|_UNVERIFIABLE" gates/acceptance_gate.py
```
44:def check_issue_body(issue: int, body: str) -> list[str]:
```
The module's existing `_ARTIFACT_REF`/`_UNVERIFIABLE`/`_EMPTY_STATE`/
`_PROVENANCE` regexes check artifact-reference shape and empty-state/
provenance presence, not who a check is assigned to. No attribution
check exists there.

canonical: gates/pr_reference.py:67, gates/ci.py:61,81,106,124,138,295,
gates/closure_sweep.py:349 (read this session) — the repo's `gh` call
convention is `subprocess.run(["gh", ...], cwd=root, capture_output=True,
text=True)`, check `returncode`, parse `--json` via `json.loads`.

derived: grep -rn "gh pr comment" gates/ on-the-record/hooks/
```
(no output)
```
No module currently posts a PR comment; req 2 is the first.

canonical: tests/test_gates.py:1-15 (read this session) — root
`tests/` mixes pytest-collectible `test_*.py` (plain `def test_*():`,
bare `assert`, `sys.path.insert(0, .../"gates")` then `import <module>`)
with shell test files. The issue's own Acceptance names the two new
test file paths under `tests/`, fixing location and style to match
`tests/test_gates.py`'s pattern.

## Unknowns resolved during survey

- **Full-suite/no-regression detection surface.** canonical: gh issue
  view 1323 (read this session) — the issue's own Acceptance third
  bullet is the compliant example: it names `bash
  tests/run-orchestrate-tests.sh` with "no regression" in scope, and
  attributes execution away from the builder in the same line
  ("executed by the req-2 runner itself once it exists; until then by
  the phase's verification role, not the builder"). Rule: an Acceptance
  section that references a full-suite/no-regression run is rejected
  UNLESS the same section states, attached to that reference, that the
  builder does not run it (verification-role/independent/check-runner
  attribution language).
- **Judgment-shaped-check boundary for req 2.** Reusing
  acceptance_gate.py's existing executable-artifact admission test
  (backticked `test/`/`gates/` path, or a `check:`/`gate:` line) as the
  gate for "this line claims to be mechanical," then further requiring
  it resolve to one of: a runnable shell command, a `grep:`-prefixed
  pattern, or a bare file path — anything admitted by the first test but
  failing the second is refused as judgment-shaped, matching the
  issue's own wording for req 2.

## Alternatives considered (feeds proposal Rationale)

- Extending gates/acceptance_gate.py in place for req 1 vs. a new
  sibling module: chose the new module — canonical: gates/acceptance_gate.py
  (read this session), its regex set checks artifact-reference shape,
  an orthogonal concern to attribution; the issue names a distinct test
  file, implying a distinct module under test.
- For req 2, executing checks and posting the PR comment inside one
  function vs. splitting execution/formatting/posting: canonical:
  gates/pr_reference.py, gates/ci.py (read this session, repo's `gh`
  call convention) — chose the split, so the fixture-PR-branch test the
  issue asks for can exercise real check execution and comment
  formatting without requiring a live network `gh pr comment` call
  inside the test.
