# Current-state survey — issue-1005 conformance-review (phase 1)

## Target artifact and spec

canonical: `gh pr view 1086` run this session — output showed
`mergeCommit.oid: fae380c75087e446b8cd8eb1347cc9da2b6161fa`, files
`roles/specs/secure-coding.spec.json`, `gates/test_secure_coding_routing.py`,
`docs/issue-1005/reports/implementation.md`.

- Target: `roles/specs/secure-coding.spec.json` (`use_when.trigger` block),
  `gates/test_secure_coding_routing.py` — delivered in PR #1086, merge
  commit `fae380c75087e446b8cd8eb1347cc9da2b6161fa`.
- Spec: issue #1005 body directly (Ask + Acceptance sections, read this
  session via `gh issue view 1005`), plus the approved phase-1 proposal
  `docs/issue-1005/proposals/secure-coding-routing-fix.md`.

## What exists to check against

Issue #1005 Acceptance lists three checkable items plus a provenance note:

| Acceptance line | Artifact region |
|---|---|
| "A seeded security-relevant change makes secure-coding reachable/suggested by the board machinery" | `gates/test_secure_coding_routing.py` case `seeded security-relevant diff -> secure-coding is due`; `roles/specs/secure-coding.spec.json`'s `use_when.trigger.path_patterns`/`content_patterns` |
| "check: `gates/test_role_utilization_report.py` (or the routing gate's own test) proves the seeded case fires and an unrelated change does not" | `gates/test_secure_coding_routing.py` (routing gate's own test, per the "or" clause) — both its cases |
| "empty state: non-security changes do not surface the role" | `gates/test_secure_coding_routing.py` case `seeded unrelated diff -> secure-coding is not due` |
| provenance: read — #993 phase-1 proposal, PR #1004 | `docs/issue-1005/reports/implementation/survey.md`'s "What causes the gap" section (file read this session), cited in `docs/issue-1005/reports/implementation.md`'s `Why` |

canonical: `docs/issue-1005/proposals/secure-coding-routing-fix.md` (file
read this session) — its "How you'll know it worked" section restates the
same two-case test as the acceptance mechanism and names the exact spec
keys to add (`path_patterns`, `content_patterns`, `record_absent_for`).

## Sampling derivation

Full-population check, not a sample: the acceptance section names exactly
three checkable items (board-machinery reachability, the named test proving
both seed cases, empty-state for non-security changes) plus one provenance
citation — four checkable units, small enough to check exhaustively.

## Thin/unknown/contested surfaces

- Whether `gates/roles_due.py`'s evaluator generically reads any spec's
  `use_when.trigger` (the proposal's stated constraint) or was itself
  modified to special-case secure-coding — needs a direct code read, not
  inferable from the proposal text alone.
- Whether the delivered test uses the *real* on-disk spec (as the proposal
  requires, "not a synthetic fixture") or a hand-rolled trigger dict —
  needs a direct read of `gates/test_secure_coding_routing.py`.
- Whether the two acceptance test cases were actually run this session
  (not just asserted as passing in implementation.md's prose) — needs a
  live re-run for phase 2, since conformance-review does not accept the
  builder's own test-output claim as evidence per the artifact-only rule.

## Scout: skipped

Skip condition: the spec (issue #1005's Acceptance section, already fixed
and unmodifiable by this review) leaves no design decision open — this is
a fidelity check of a landed mechanical routing-fix against fixed
acceptance criteria, not a build with a direction to steer.
