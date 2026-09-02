Expected: the record's `skill-verdict` line for `experiment-trust` would
accurately state whether the Skill tool was invoked.

What actually happened: the initial committed record (commit `dab63a8b`)
wrote `applied: invoked` for `experiment-trust`, but this session had only
reasoned informally using the skill's Twyman's-law concept (grading PR
#3154's "all four fixed" claim as a reassuring result to be independently
checked) without actually calling the Skill tool. The Skill tool itself
was not called until the Stop hook's skill-verdict-guard flagged the
mismatch (`invoked-mismatch`, issue #3044). Corrected by invoking
`experiment-trust` via the Skill tool this turn and updating the record's
`skill-verdict` line to describe invocation as having happened at that
point, not during the original defect-grading work, per the same shape
PR #3154's own record used for its analogous correction (`docs/issue-3127
/reports/experiment-trust+implementation-blueprint+silent-failure-audit+
test-derivation-d2b8a13d/deviation-log/20260902T105315140314-
094a52e927f38802.md`).
