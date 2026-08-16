---
code_under_review:
  - gates/design_research_consult.py
  - gates/test_design_research_consult.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue-1653

## What was done
canonical: gates/design_research_consult.py (written this turn, as committed on this branch)
Added gates/design_research_consult.py, mirroring gates/requirement_intake_consult.py
(issue-1024) in shape: regex pair, pure check_issue_body, gh-wrapped check, main().

canonical: gates/test_design_research_consult.py (written this turn, as committed on this branch)
Added gates/test_design_research_consult.py, mirroring gates/test_requirement_intake_consult.py
in shape: four unit-test cases, no network.

Module + tests only — no wiring into spawn.py or hooks, per the issue's
explicit deferral to avoid colliding with #1652's spawn.py change.

## Why
northpole req#6 (requirement fidelity) requires a research-first
obligation before implementing design-bearing issues, distinct from
#1024's feasibility/consistency axis. Mirroring #1024's proven shape
reuses an already-hunted pattern instead of inventing a new one.

## Upstream basis
docs/issue-1653/proposals/design-research-consult-gate.md

## Acceptance verification
canonical: acceptance: python3 gates/test_design_research_consult.py — result: pass (output below, executed this turn)
```
$ python3 gates/test_design_research_consult.py
ok - t_arbitrary_skip_reason_rejected
ok - t_neither_flagged
ok - t_research_trace_passes
ok - t_skip_mechanical_passes
4/4 passed
```

canonical: acceptance: python3 gates/test_design_research_consult.py — result: pass (same run as above)
All four cases pass: no-tag body fails, design-research: <ref> passes,
design-research-skip: mechanical passes, arbitrary skip reason fails.

canonical: gates/design_research_consult.py (read this turn, source as written)
check_issue_body is pure text matching; only check() calls
gh_rest.fetch_issue_body, so the unit path above made no network call.

## What did not work
None.

## Open findings
None.
