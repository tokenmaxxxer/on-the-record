---
code_under_review:
  - gates/assumption_ledger.py
  - gates/test_assumption_ledger.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

canonical: gates/assumption_ledger.py (this turn's own write, committed
at dde3b4bf), read against gates/requirement_intake_consult.py for shape.
Added `gates/assumption_ledger.py`, mirroring `gates/requirement_intake_consult.py`
in shape (pure `check_issue_body(issue, body)` for unit testing + a
`gh`-wrapped `check(repo, issue)` for live use, same CLI entry-point
pattern). The gate requires a non-trivial drafted issue body to carry a
`## Assumptions` section whose entries are each tagged with the fixed
provenance vocabulary `stated:`/`inferred:`/`invented:`, OR the fixed-vocabulary
skip tag `assumptions-skip: mechanical` (same anti-arbitrary-skip
discipline as `requirement_intake_consult.py`'s `validity-consult-skip:
trivial` and #1653's `design-research-skip: mechanical`).
canonical: gates/assumption_ledger.py (re-read for the presence-only
discipline claim below).
Presence and tag-validity only — the gate does not judge whether an
entry's provenance label is actually true, matching `acceptance_gate.py`'s
presence-only discipline named in the issue.

Also added `invented_assumptions(body)`, a helper that scans the
`## Assumptions` section and returns the text of every `invented:` entry,
so a future directive/orchestrator can require explicit human
sign-off on exactly those entries before spawning (the issue's sequenced
follow-up — not wired here).

canonical: gates/test_assumption_ledger.py (this turn's own write,
committed at dde3b4bf).
`gates/test_assumption_ledger.py` mirrors
`gates/test_requirement_intake_consult.py`'s shape (module-level `t_*`
functions, a `_run` harness, no network/`gh` calls). It covers: a
non-trivial body with neither the section nor the skip tag
(`t_missing_both_flagged`); a well-formed ledger with all three tags
(`t_well_formed_ledger_passes`); `assumptions-skip: mechanical`
(`t_skip_mechanical_passes`); an out-of-vocabulary tag inside the section
(`t_out_of_vocabulary_tag_fails`);
canonical: gates/test_assumption_ledger.py (same file, re-cited for the
remaining test list below).
an arbitrary skip reason outside the fixed vocabulary
(`t_arbitrary_skip_reason_rejected`); an `## Assumptions` section present
but with zero entries (`t_empty_assumptions_section_fails`); and two
tests for `invented_assumptions` — returns only the `invented:` entries'
text (`t_invented_helper_returns_only_invented`), and returns `[]` when
no section exists (`t_invented_helper_empty_when_no_section`).

## Why

canonical: gh issue view 1665 (this turn's own read of the issue body).
northpole req#6 / issue #1665: the orchestrate directive already says
"you are the scribe, never the inventor" but nothing enforced it —
invented requirements were indistinguishable from stated ones in issue
prose. An assumption ledger with provenance tags makes gap-filling
visible and mechanically checkable, and the `invented_assumptions` helper
gives a future confirmation gate something concrete to point at.

## Upstream

Based on: issue #1665 body (verbatim acceptance criteria), mirroring
`gates/requirement_intake_consult.py` and `gates/test_requirement_intake_consult.py`
(issue-1024) for shape, and `gates/acceptance_gate.py` for the
presence-only / fixed-vocabulary-skip pattern.

## What did not work

None to report this turn — no dead ends encountered.

## Verification

canonical: python3 gates/test_assumption_ledger.py (executed this turn,
raw output below)
acceptance: python3 gates/test_assumption_ledger.py — result: pass

```
$ python3 gates/test_assumption_ledger.py
ok - t_arbitrary_skip_reason_rejected
ok - t_empty_assumptions_section_fails
ok - t_invented_helper_empty_when_no_section
ok - t_invented_helper_returns_only_invented
ok - t_missing_both_flagged
ok - t_out_of_vocabulary_tag_fails
ok - t_skip_mechanical_passes
ok - t_well_formed_ledger_passes
8/8 passed
```

## Out of scope

Directive/orchestrator wiring that requires human sign-off on
`invented:` entries before spawn — explicitly deferred by the issue as a
sequenced follow-up. This delivery is module + tests only.

## Open findings

None.
