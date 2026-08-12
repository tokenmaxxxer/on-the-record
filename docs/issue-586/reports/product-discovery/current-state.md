---
name: issue-586-product-discovery-current-state
kind: current-state-survey
loop_state: surveyed
---

# Current-state survey — issue #586 (product-discovery)

## Background / context
Issue #586 body: taxonomy work so #573's delegated-judgment gate can
render multi-role panels. Prior sessions on this same issue ran steps 1-2
already.

derived: `gh pr list --search "586" --state all`
```
594  feat(issue-586): realize judgment-axis matrix, batch 1     issue-586/implementation  MERGED
590  issue-586: phase-1 judgment-axis matrix proposal (architecture)  issue-586/architecture  MERGED
593  issue-586 step 2: implementation phase-1 proposal (batch 1)  issue-586/implementation  MERGED
# => 3 PRs on this issue in gh's record; no PR beyond these three is
#    attributed to issue #586 in this search.
```

This survey re-derives the underlying repo state those PRs describe,
rather than trusting their own record text, and scopes what a
product-discovery proposal should recommend next.

## Judgment_axes coverage — read evidence
derived: per-file judgment_axes read over roles/*.json (python3 json.load loop)
```
$ for f in roles/*.json; do python3 -c "import json;d=json.load(open('$f'));print('$f', d.get('judgment_axes') or 'NONE')"; done
roles/architecture.json ['maintenance_complexity']
roles/capacity-planning.json ['external_burden']
roles/conformance-review.json ['alignment']
roles/performance-engineering.json ['performance']
roles/security-threat-model.json ['attack_potential']
(all other 38 roles/*.json: NONE)
# => 5 of 43 roles/*.json carry judgment_axes; 38 carry none.
```

derived: `grep -n "_JUDGMENT_AXES" gates/role_spec_shape.py`
```
_JUDGMENT_AXES = {"alignment", "maintenance_complexity", "external_burden", "attack_potential", "performance"}
# => axis vocabulary is a closed 5-entry set; the 5 owned above are all
#    5 members of this set, each with exactly one owner.
```

derived: `python3 gates/role_spec_shape.py --roles-dir roles`
```
$ python3 gates/role_spec_shape.py --roles-dir roles; echo exit=$?
exit=0
```
derived: `grep -n "role_spec_shape\|axis" on-the-record/hooks/hooks.json`
```
45:  { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/role-axis-completeness-guard.sh" },
# => the axis-ownership gate exits 0 and is wired into hooks.json line 45.
```

Prior architecture-role rationale for stopping at 5 axes (no
`cost`/`legal` axis added, deferring instead to `finance-unit-economics`/
`legal-compliance`) is recorded in
`docs/issue-586/proposals/architecture.md` section "Why no additional
axis" — carried forward here as the prior role's stated position, not
independently re-derived by this session.

## Rulebook axis-evaluation procedures — read evidence
derived: `grep -l '"axis_evaluation"' roles/specs/*.spec.json`
```
roles/specs/architecture.spec.json
roles/specs/security-threat-model.spec.json
# => 2 of the 5 axis-owning roles' spec.json carry an axis_evaluation
#    rule; conformance-review, capacity-planning, performance-engineering
#    do not appear in this list.
```

derived: `gh issue list --state all --search "586" --limit 30`
```
586  OPEN    Complete the judgment taxonomy: ...
650  CLOSED  role_spec_shape.py --roles-dir is dead code AGAIN ...
609  CLOSED  Triage spec-stage open decisions through the judgment-axis panel ...
623  CLOSED  Post-landing verification program ...
628  CLOSED  Silent-failure hunt across today's merged flows ...
573  OPEN    Delegated judgment: auto-approve/reject ...
597  CLOSED  Persist the orchestrator's four-element framing ...
# => no entry in this search is a rulebook-procedure follow-up for
#    conformance-review, capacity-planning, or performance-engineering —
#    the batch-2/3/4 filing that
#    docs/issue-586/proposals/architecture.md section 3 describes as out
#    of that proposal's own write scope.
```

The `gh pr list` read in Background above is the same evidence for issue
#586's acceptance criterion 3 (a 3+-role panel test fixture, owned by
conformance-review, step 3): none of the three listed PRs' titles name a
panel-fixture change.

## Problem, stated without a solution (JTBD tuple)
The issue text names its own solution ("assign judgment_axes... give each
role's rulebook a procedure"). Restated without that solution attached:

- **Job performer**: the operator, reading a #573 delegated-judgment
  panel's verdict on a multi-role decision.
- **Job**: trust that a role's supports/contradicts verdict reflects that
  role's actual domain expertise applied to this artifact, not a role
  playing along with a template.
- **Circumstance**: a decision's diff touches paths owned by 3+
  axis-owning roles, and the panel is about to auto-render.
- **Desired outcome**: each role's verdict traces to a concrete
  READ/EXECUTE/CRITERIA/CITATION procedure the operator could audit, and
  the panel actually exercises 3+ such roles.

The read evidence above shows axis ownership and gate wiring as reached;
per-role procedure text and a 3+-role panel test are the parts the reads
above did not surface for the 3 axes batch 1 assigned.

## Opportunity-solution tree branch (OST vocabulary)
- **Outcome**: delegated-judgment verdicts (#573) are trusted enough that
  the operator stops manually re-checking every auto-rendered panel.
- **Opportunity**: per the reads above, a role's verdict on its owned
  axis has no on-file procedure to distinguish it from a template
  fill-in, for 3 of the 5 axis owners, and no panel test wider than the
  original 2-role seed was surfaced.
- **Candidate solutions** (named by the architecture proposal, not
  re-litigated here): (a) conformance-review, capacity-planning,
  performance-engineering each write a rulebook procedure section against
  the READ/EXECUTE/CRITERIA/CITATION template in
  `docs/handbooks/architecture-methodology.md`; (b) conformance-review
  extends `test_delegated_judgment_gate.py` with a 3+-role fixture.
- **Discriminating assumption test**: run a 3+-role panel against a real
  decision — does a role with a written procedure produce checkably
  different output from one without? Per the reads above, neither (a)
  nor (b) currently exists to run this test against.

## Open findings
- Batches 2-4 (rulebook procedure prose, 3 roles) — no filed GitHub
  issue, per the `gh issue list` read above.
- Batch 5 (3+-role panel fixture) — no filed GitHub issue or PR, per the
  `gh issue list` and `gh pr list` reads above.
- Both sit outside this session's write scope (cross-repo rulebook
  content, or another role's own step) — see the accompanying proposal
  for the filing recommendation.
