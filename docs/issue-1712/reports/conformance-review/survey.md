---
kind: survey
loop_state: draft-reported
---

# Current-state survey: issue #1712 conformance review

Subject: issue-1712

Skip record (scout-directive): scouting skipped — this is a mechanical
conformance check (run the shipped unit test, grep the directive text
for the substrings the issue's own Acceptance criteria specify) with no
design decision open.

## Board condition
canonical: git log --oneline origin/main -5 (this session, see transcript); gh issue view 1712.
Implementation for issue #1712 already landed on `main` via PR #1715,
commit `04a77592963c94770d04f61e4ebe4caee6129bfa`
("feat(issue-1712): consult-ordering fix, Korean neutrality, banner
wording"). No conformance-review record exists yet for this commit sha —
board condition per the issue-521 conformance-review role spec is met.

## Write surfaces touched by the implementation commit
canonical: git show 04a77592963c94770d04f61e4ebe4caee6129bfa --stat (this session).
- `on-the-record/hooks/directive.sh` (SCOPE-OPTION PROPOSAL section +
  first-contact banner text)
- `gates/test_scope_option_directive.py` (three new assertions:
  `t_states_consult_runs_on_vague_ask_before_options`,
  `t_states_neutrality_rule_forbids_korean_synonyms`,
  `t_states_banner_mentions_option_path`)
- `docs/issue-1712/reports/implementation.md` (implementation role's own
  record — out of this review's write scope, read-only reference)

## Acceptance criteria to verify (from issue #1712 body)
canonical: gh issue view 1712 (Acceptance section, this session).
1. Directive states the scope-option subclass runs the #1024 validity
   consult on the vague ask first and derives the option block from its
   output (per-option `consult-trace:` cites that run); the
   post-confirmation #1024 consult may reference the same trace instead
   of re-running when the ask is unchanged. Asserted by
   directive-content test.
2. Neutrality rule additionally bars `권장` and `추천` (substring,
   either) in the option block; banner sentence updated to mention the
   option path. Asserted by the same test family.
3. Empty state: non-subclass elicitation and confirmed-ask consult flow
   unchanged.

## Verification method
canonical: git show 04a77592963c94770d04f61e4ebe4caee6129bfa (full diff, this session).
The plan is to read the current text of `on-the-record/hooks/directive.sh`
at the merged commit and run
`python3 gates/test_scope_option_directive.py`, matching each acceptance
bullet to the specific assertion(s) that check it, per the
verdict-mapping convention already used in the sibling
`docs/issue-1707/reports/conformance-review.md` record.

## Gaps / unknowns going into the proposal
canonical: docs/issue-1712/reports/implementation.md (read this session, present on main at commit 04a77592963c94770d04f61e4ebe4caee6129bfa); git show 04a77592963c94770d04f61e4ebe4caee6129bfa (full diff, this session).
None found so far: the implementation record already cites the same
test run and directive line ranges this review intends to independently
re-derive.
