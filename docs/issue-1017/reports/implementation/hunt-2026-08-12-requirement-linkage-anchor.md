# Warrant hunt — issue-1017 requirement-linkage-anchor proposal

proposal: docs/issue-1017/proposals/2026-08-12-requirement-linkage-anchor.md

## after-proposal, stance 4 (write set cannot carry the work)

FINDING: `gates/pr_reference.py` is a second real call site of
`acceptance_gate.check_issue_body` (PR-close time, reached from
`gates/ci.py`'s `--closes-only` path), not just `spawn.py`'s
`require_acceptance_gate`. The proposal's write set only wires the new
`requirement_linkage` check into the `spawn.py` draft-time path.

derived: `grep -n "acceptance_gate" gates/pr_reference.py`
```
20:import acceptance_gate
106:    bad = acceptance_gate.check_issue_body(issue, issue_body)
```

Disposition: not a scope gap for this proposal as written. Issue #1017's
ask is a draft-time backstop ("checked by acceptance_gate-style
backstop" for NEW issues at drafting) plus spawn-task passthrough and a
digest next-action line — it does not ask for a PR-close-time CI gate
the way `acceptance_gate` itself carries. The proposal's `## Out of
scope` already excludes changing `acceptance_gate.py`; a CI-close-time
enforcement point for `requirement_linkage` was not part of the request
and is left for a future issue if wanted, rather than silently folded
into this write set. Noted here so the omission is a stated choice, not
an unexamined gap.
