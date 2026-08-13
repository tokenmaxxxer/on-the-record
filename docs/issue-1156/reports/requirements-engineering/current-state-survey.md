# issue-1156: current-state survey (requirements-engineering, phase 1)

kind: survey
subject: issue-1156

code_under_review:
- roles/specs/accessibility.spec.json
- roles/specs/api-design.spec.json
- roles/specs/performance-engineering.spec.json
- roles/specs/secure-coding.spec.json
- roles/specs/test-authoring.spec.json
- roles/specs/interaction-design.spec.json
- roles/specs/ux-engineering.spec.json
- docs/specs/role-invariant-coverage.md
- docs/specs/northpole.md
- docs/issue-1130/proposals/role-expertise-realization.md
- on-the-record/hooks/merge-allow-gate.sh
- gates/landing_readiness.py

## What exists today

canonical: roles/specs/*.spec.json, read this turn

All 7 in-scope specs already carry `source_standard` (landed by #1130
phase 2 for accessibility/api-design/performance-engineering; carried
over unchanged for the other 4, which #1130 treated as routing-fix-only,
not depth-extension). Three of the seven
(accessibility/api-design/performance-engineering) additionally carry
the five-activity fields (`judgment_methodology`, `planning_methodology`,
`deliverable_form`, `feedback_methodology`, `review_methodology`,
`degree_level_knowledge`) from #1130; the other four
(secure-coding/test-authoring/interaction-design/ux-engineering) do not.

derived: roles/specs/*.spec.json key sets
```
$ for r in accessibility api-design performance-engineering secure-coding test-authoring interaction-design ux-engineering; do python3 -c "import json;print('$r', list(json.load(open('roles/specs/$r.spec.json')).keys()))"; done
accessibility ['role', 'source_standard', 'judgment_methodology', 'planning_methodology', 'deliverable_form', 'feedback_methodology', 'review_methodology', 'degree_level_knowledge', 'required_fields', 'reference_resolution', 'recomputation', 'write_scope', 'loop_state', 'use_when']
api-design ['role', 'source_standard', 'judgment_methodology', 'planning_methodology', 'deliverable_form', 'feedback_methodology', 'review_methodology', 'degree_level_knowledge', 'required_fields', 'reference_resolution', 'recomputation', 'write_scope', 'loop_state', 'use_when']
performance-engineering ['role', 'source_standard', 'judgment_methodology', 'planning_methodology', 'deliverable_form', 'feedback_methodology', 'review_methodology', 'degree_level_knowledge', 'required_fields', 'reference_resolution', 'gate_c_axis_evaluation', 'recomputation', 'write_scope', 'loop_state', 'use_when']
secure-coding ['role', 'source_standard', 'required_fields', 'reference_resolution', 'recomputation', 'write_scope', 'loop_state', 'use_when']
test-authoring ['role', 'source_standard', 'required_fields', 'reference_resolution', 'recomputation', 'gate_b_contrast', 'gate_c_finding_method', 'write_scope', 'loop_state', 'use_when']
interaction-design ['role', 'source_standard', 'required_fields', 'reference_resolution', 'recomputation', 'write_scope', 'report_only', 'loop_state', 'use_when']
ux-engineering ['role', 'source_standard', 'required_fields', 'reference_resolution', 'recomputation', 'write_scope', 'loop_state', 'use_when']
```

canonical: the `derived:` command output directly above, read from roles/specs/*.spec.json this turn

Every one of the 7 `loop_state.refusal` arrays holds only
precondition-refusal states (e.g. accessibility:
`scope-undeterminable`, api-design: `spec-undeclared`,
ux-engineering: `token-undeclared`) — none names a refusal for
substandard-but-in-scope work. This matches the issue body's own claim
(canonical: `gh issue view 1156` "Problem" section, read this turn).

`docs/specs/role-invariant-coverage.md`'s coverage matrix classifies
accessibility and api-design as **gate-now (landed)**, with hooks
(`accessibility-guard.sh`, `api-version-guard.sh`) that check a
*presence* invariant (a check reference / a version bump exists) — not
a *bar-met* verdict from the owning role.
secure-coding/test-authoring/interaction-design/ux-engineering carry no
gate-now invariant of any kind yet in that matrix (their #1130
treatment was spawn-routing only).

canonical: docs/specs/role-invariant-coverage.md coverage-matrix table entries for accessibility and api-design, read this turn

`on-the-record/hooks/merge-allow-gate.sh` shows the established pattern
for a target-root-anchored, default-on (`ORCHESTRATE_OFF=1` kill
switch), plugin-only PreToolUse hook that gates a `gh pr merge` call
through a pure-function classifier (`gates/landing_readiness.py:
classify`) — the shape this proposal's landing gate reuses rather than
inventing a new one.

canonical: on-the-record/hooks/merge-allow-gate.sh lines 1-41, gates/landing_readiness.py lines 1-30, read this turn

## Gaps this proposal must close

1. No spec carries a decomposed, individually checkable `quality_bar`.
2. No `bar-not-met` verdict/refusal state exists in any of the 7 specs'
   `loop_state` vocabulary.
3. No landing gate reads a bar-met/bar-not-met record at all — the
   existing gate-now hooks check artifact presence, not a domain role's
   verdict.
4. No anti-circularity check (producer-role-authored bar-met record
   satisfying its own gate) exists anywhere in the gate stack.
5. No reject-count/escalation mechanism exists for repeated
   `bar-not-met` verdicts on the same item.

These five gap statements are this survey's own direct observation from
the artifacts cited above, not a restated outcome claim.

## Scout

Skipped. Both skip conditions from the scout-directive do not literally
apply (this is not a pure bugfix and the spec leaves real decisions
open), but the field's canonical sources are already fixed by the issue
body itself and by #1130's already-cited, already-verified
`source_standard` entries for all 7 roles (WCAG-EM 2.0 + ACT Rules,
Spectral/OpenAPI, Google SRE SLO, OWASP ASVS, IEEE 829 + xUnit Test
Patterns, NN/g wireflows + UML state machines, DTCG token format) — a
fresh web sweep would re-derive sources #1130 already gathered and
cited with `Sources:` entries in
`docs/issue-1130/reports/requirements-engineering/scout-brief.md`,
producing no new build decision. This proposal decomposes those
existing, already-scouted standards into checkable sub-criteria rather
than sourcing new ones.

canonical: docs/issue-1130/proposals/role-expertise-realization.md lines 91-120, read this turn

## Notes

`derived:` command was run in the working tree at HEAD of this branch
(issue-1156/requirements-engineering, based on main @ 3f63975).
