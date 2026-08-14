Subject: issue-1024

# Current-state survey (phase 1, step 1)

canonical: derived: `git log --oneline --all | grep -i 1024` (executed this session).
Board condition: `e16b04fd` (issue-1024 phase-2, PR #1030) and
`7b808d84` (issue-1024 phase-1, PR #1027) are both on `main`; no
conformance-review record for either sha existed anywhere in the tree
before this session (`find docs -path '*1024*' -iname '*conformance*'`,
executed this session, returned nothing). Trigger condition met.

Target commit under review: `e16b04fd8f8416d41a57736a6f07a6315efe9fa7`
(delivery). `7b808d84` is the phase-1 proposal-only commit, folded into
scope as upstream basis, not separately reviewed for code.

Scout skip: no product-facing design decision is open here — the
role directive fixes the review's own methodology (extract requirement
list in phase 1, render Present/Surface/Absent/Incorrect/Unverifiable
verdicts in phase 2 from artifact+spec only). Skip condition 2 (contract
v3 s19 rigor floor) applies; scout-directive did not run.

## Method

canonical: derived: `git show --stat e16b04fd` (executed this session)
canonical: derived: `git show e16b04fd -- on-the-record/hooks/directive.sh` (executed this session)
canonical: gates/requirement_intake_consult.py (full-file read, this session)
canonical: gates/test_requirement_intake_consult.py (full-file read, this session)
canonical: derived: `git show e16b04fd -- tests/test_spawn.py` (executed this session)
canonical: docs/specs/enforcement-boundary.md line 52, read this session
canonical: derived: `grep -rn "requirement_intake_consult" --include='*.py' --include='*.sh' --include='*.json' .` (executed this session)

## Code under review

- on-the-record/hooks/directive.sh
- gates/requirement_intake_consult.py
- gates/test_requirement_intake_consult.py
- tests/test_spawn.py
- docs/specs/enforcement-boundary.md
- docs/issue-1024/reports/implementation.md

## Delivered shape

canonical: `git show e16b04fd -- on-the-record/hooks/directive.sh` diff, read this session.
`directive.sh` gains a "VALIDITY CONSULT (issue #1024)" bullet inside
the REQUIREMENT ELICITATION block: before drafting an issue, route the
confirmed ask through `requirements-engineering` (and, if risk-bearing,
also `risk-management`), then record `validity-consult: <ref>` in the
drafted body.
canonical: `git show e16b04fd -- on-the-record/hooks/directive.sh` diff, read this session (same hunk).
The other accepted path is the closed-vocabulary skip tag
`validity-consult-skip: trivial` for trivial/mechanical asks. The added
text is a markdown bullet inside the directive's heredoc string — prose
an orchestrator session reads and follows, not a shell function call
inside `directive.sh` itself.

canonical: gates/requirement_intake_consult.py, full-file read this session.
`gates/requirement_intake_consult.py` is a new, standalone module:
`check_issue_body(issue, body)` regex-scans for either
`validity-consult:\s*\S` or `validity-consult-skip:\s*trivial` (closed
vocabulary — only `trivial` is accepted, per the module's own docstring
rationale against arbitrary self-graded skip reasons); returns `[]`
(no violations) if either pattern matches, else a violation string.
`check(repo, issue)` wraps it with a live `gh issue view --json body`
call. `main()` gives a CLI entry point. Mirrors `acceptance_gate.py`'s
shape (offline-testable pure function + thin CLI/gh wrapper).

canonical: docs/specs/enforcement-boundary.md line 52, read this session.
The registration row states, in its own text: "the proposal's write set
builds the check function itself and the directive-text default step,
not a `spawn.py`/`ci.py` preflight wiring point — no zero-install
enforcement path exists yet, so this stays repo-local pending a future
wiring proposal."

canonical: derived: `grep -rn "requirement_intake_consult" --include='*.py' --include='*.sh' --include='*.json' .` (executed this session).
The only non-definition, non-test hits found by this grep are the two
`import requirement_intake_consult` lines inside a test class in
`tests/test_spawn.py`; no hook, no `hooks.json` row, and no
`spawn.py`/`ci.py` call site invoking the module against a real
drafted issue turned up in the same grep. This grep result matches the
enforcement-boundary.md row's own stated gap cited above.

## Test evidence

canonical: derived: `python3 -m pytest tests/test_spawn.py -k intake` (executed this session), exact issue `check:` command:

```
collected 503 items / 500 deselected / 3 selected
tests/test_spawn.py ...                                                  [100%]
====================== 3 passed, 500 deselected in 0.19s =======================
```

canonical: gates/test_requirement_intake_consult.py, full-file read this session.
This file carries three test functions covering the same three cases
independently of the `tests/test_spawn.py` mirror: `t_consult_trace_passes`,
`t_skip_trivial_passes`, `t_neither_flagged`.

## Observed gap (feeds phase 2, not a verdict here)

canonical: derived: `grep -rn "requirement_intake_consult" --include='*.py' --include='*.sh' --include='*.json' .` (executed this session, cited above under Method and Delivered shape).
The delivered mechanism enforces the two-path shape (consult-ref XOR
skip-tag) only when `requirement_intake_consult.check_issue_body` /
`check` is actually invoked against a real issue body, and this grep
turned up no invocation site outside the test suite.
canonical: on-the-record/hooks/directive.sh, `git show e16b04fd` diff cited above under Delivered shape.
The directive-text bullet in `directive.sh` is the only thing that
would make an orchestrator session actually run the consult or write
the tag at intake time; nothing mechanically verifies that the bullet
was followed on a live drafted issue (no `PreToolUse` hook, no CI/spawn
wiring). Phase 2 will render this as a per-requirement verdict against
the issue's acceptance line, not resolve it here.
