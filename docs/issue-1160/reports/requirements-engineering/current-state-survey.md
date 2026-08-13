# issue-1160: current-state survey (requirements-engineering, phase 1)

kind: survey
subject: issue-1160

code_under_review:
- roles/specs/brand-design.spec.json
- roles/specs/content-design.spec.json
- roles/specs/market-analysis.spec.json
- roles/specs/ux-engineering.spec.json
- roles/specs/interaction-design.spec.json
- docs/issue-1156/proposals/per-role-quality-bars.md
- docs/specs/northpole.md
- on-the-record/hooks/hooks.json

## What exists today

canonical: roles/specs/{brand-design,content-design,market-analysis,ux-engineering,interaction-design}.spec.json, read this turn

All five pilot-candidate specs already declare `required_fields`,
`reference_resolution`, `recomputation`, `write_scope`, `loop_state`, and
`use_when.board_condition`. None declares an `outcome_mission` or
`mission_deliverables` field — the schema stops at record-shape
(what fields a landed record must carry), never at what the record's
underlying artifact must actually be in the target project.

derived: roles/specs/*.spec.json key sets for the 5 candidates
```
$ for r in brand-design content-design market-analysis ux-engineering interaction-design; do python3 -c "import json;print('$r', list(json.load(open('roles/specs/$r.spec.json')).keys()))"; done
brand-design ['role', 'source_standard', 'required_fields', 'reference_resolution', 'recomputation', 'write_scope', 'loop_state', 'use_when']
content-design ['role', 'source_standard', 'judgment_methodology', 'planning_methodology', 'deliverable_form', 'feedback_methodology', 'review_methodology', 'degree_level_knowledge', 'required_fields', 'reference_resolution', 'recomputation', 'write_scope', 'loop_state', 'use_when']
market-analysis ['role', 'source_standard', 'required_fields', 'reference_resolution', 'recomputation', 'write_scope', 'loop_state', 'use_when']
ux-engineering ['role', 'source_standard', 'required_fields', 'reference_resolution', 'recomputation', 'write_scope', 'loop_state', 'use_when']
interaction-design ['role', 'source_standard', 'required_fields', 'reference_resolution', 'recomputation', 'write_scope', 'report_only', 'loop_state', 'use_when']
```

canonical: the `derived:` command output directly above, read from roles/specs/*.spec.json this turn

Write scopes today are report-shaped, not artifact-shaped, for three of
the five: content-design, market-analysis, and interaction-design
(`report_only: true`) write only `docs/issue-<n>/reports/<role>.md` — no
applied artifact path. brand-design's `write_scope` already includes
`design-tokens/*.json` (an applied artifact, not just a report) and
ux-engineering's `use_when.trigger` already fires on real `.tsx`/`.jsx`
files touching `design-token`/`designToken` content — these two are
closer to artifact-producing already than the other three.

canonical: roles/specs/{brand-design,ux-engineering}.spec.json write_scope/use_when fields, read this turn

`board_condition`/`use_when.trigger` on all five is presence-only ("a
new design token is proposed", "new user-facing content is proposed",
"a market entry or strategy decision is proposed") — each fires on an
upstream artifact/decision existing, not on a project-level absence of
the role's deliverable. None states a false-positive bound. None is
a need-detector in the sense issue #1160 requirement 2 asks for
(detects that the TARGET PROJECT lacks the deliverable, e.g. no palette/
token file exists at all yet a UI is shipping).

canonical: roles/specs/*.spec.json use_when fields, read this turn

#1156 (in flight, not yet landed to main — `docs/issue-1156/proposals/
per-role-quality-bars.md`, `status: proposed`) designs an anti-circularity
mechanism: a proposed (not yet landed) gates/quality_bar.py would take
producer-identity and author-identity as explicit inputs, resolve each
through the same account-level check approval-gate.sh/pr-preflight.sh
already use, and return `BAR_NOT_MET` whenever the two accounts match.
canonical: docs/issue-1156/proposals/per-role-quality-bars.md section
"### 4. Anti-circularity", read this turn — the same section states a
same-`CLAUDE_ROLE`-but-same-account bypass was found and closed, citing
its own after-proposal hunt record,
docs/issue-1156/reports/requirements-engineering/2026-08-13-hunt-per-role-quality-bars.md.
#1156's phase-1 proposal frontmatter file list already names
roles/specs/ux-engineering.spec.json and
roles/specs/interaction-design.spec.json for its own
`quality_bar`/`bar-not-met` loop_state addition, landing in #1156 phase 2.

canonical: docs/issue-1156/proposals/per-role-quality-bars.md frontmatter `files:` list, read this turn

## Gaps this proposal must close

1. No spec declares `outcome_mission` (the real-world goal the
   profession exists to achieve) or `mission_deliverables`
   ({artifact, fit_criterion}) — schema covers record shape, not
   real-world deliverable identity.
2. No need-detector predicate exists for target-project absence of a
   role's deliverable, with a stated false-positive bound — existing
   `use_when` triggers detect upstream artifact presence, not domain
   need.
3. content-design/market-analysis/interaction-design write only
   report-shaped paths; landing an actual applied deliverable
   (issue body requirement 1's "not a review memo") needs a write-scope
   extension for at least the two of these three this proposal pilots
   as dormant candidates.
4. #1156's ux-engineering/interaction-design `quality_bar` write is
   in flight on roles/specs/ux-engineering.spec.json and
   roles/specs/interaction-design.spec.json — the same two files this
   proposal's operator-named pilot pair would also need to touch for
   `outcome_mission`/`mission_deliverables`. A write-set collision on
   both files is real, not speculative.
