# issue-1024 current-state survey (phase 1)

## Scout skip record

Skipping scout's sweep: this is infrastructure work extending an
existing internal directive/gate pattern (requirement-digest #930,
requirement-linkage #1017), not a product-shaped surface with external
exemplars to benchmark against. The spec (issue body) also leaves no
open design decision about what "validity analysis" means substantively
— it names the two consulting roles (requirements-engineering,
risk-management) and the two enforcement shapes (directive default +
gate check) explicitly. Both scout skip conditions apply jointly.

## Write surfaces

canonical: on-the-record/hooks/directive.sh:68-96 (read this session)

The orchestrator's live directive text. The "REQUIREMENT ELICITATION"
block (lines 72-80) is the existing default-step precedent this issue
extends — it conditions drafting on acceptance-shape and routes vague
asks through requirements-quality/user-discovery skills. No block in
that file consults requirements-engineering or risk-management, and no
block requires a consult-trace reference in the drafted issue body.

canonical: docs/issue-1017/proposals/2026-08-12-requirement-linkage-anchor.md (read this session, frontmatter carries `status: proposed`)

That sibling proposal establishes a shape worth mirroring for #1024's
own gate: a pure check_issue_body(issue, body) function plus a
check(root, issue) wrapper doing the gh issue view fetch, wired into
the drafting call path, with a distinct greppable escape tag. Its
proposed module (a new gates/ file) is not yet on disk — that sibling
proposal is still awaiting its own phase-2 build. A future #1024 gate
needs its own escape tag distinguishing the property it checks (a
validity-consult trace reference) from what that sibling proposal's
module would check (a requirement-ID citation) — same shape, different
property, so the two stay separate modules rather than merge.

canonical: gates/acceptance_gate.py:1-33 (read this session)

The working precedent for a pure, offline-testable check with a
regex-based escape-tag convention (the unverifiable: line, matched by
the _UNVERIFIABLE regex). A #1024 gate should mirror this shape for its
own skip-reason tag.

canonical: `grep -n intake tests/test_spawn.py` (run this session, zero matches) — the issue's own Acceptance section names `pytest tests/test_spawn.py -k intake` as its check command.

tests/test_spawn.py carries no test or method name matching "intake"
today, so phase-2 needs new cases carrying that substring to be
selected by the named check command.

canonical: docs/specs/requirement-digest.md:1-5 (read this session)

Read-only precedent for how the live requirement digest is rendered;
#1024 does not modify this file or gates/requirement_digest.py — the
digest is an input requirements-engineering consults, not a target
this issue's gate touches.

canonical: `find . -iname requirements-engineering -o -iname risk-management` (run this session)

```
./docs/issue-167/_assets/rulebook-skeleton/requirements-engineering
./docs/issue-170/_assets/rulebook-skeleton/risk-management
```

Both roles named in the issue already exist in the rulebook-skeleton
catalog — #1024 routes to them by name, the same way the existing
REQUIREMENT ELICITATION block already routes to
requirements-quality/user-discovery by name; it does not invent either
role.

## Gap relative to the issue's ask

canonical: on-the-record/hooks/directive.sh:68-96, gates/acceptance_gate.py:1-33 (read this session)

Nothing in the directive text or the existing gate set prompts or
enforces a feasibility/consistency/ordering consult before an issue is
drafted. This is the gap #1024's phase-1 proposal addresses.
