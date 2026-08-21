# Current-state survey: skill-axis phase-3 batch wave 4 (final) (#1777)

## Scope reminder

Wave-4 rulebooks (final batch per the issue text): release-engineering,
requirements-engineering, risk-management, sales, secure-coding,
security-threat-model, technical-feasibility, technical-writing,
test-authoring, user-discovery, ux-engineering, implementation,
conformance-review.

Write set for this repo (`on-the-record`): `docs/specs/role-source-allowlist.json`,
`docs/issue-1777/**`. The `skill-repository` content PR is a separate
repository/write set, same as the earlier waves (#1766, #1769, #1772).

## Prior mechanism (already merged, reused unchanged)

- `resolve_role_source()` / `_role_source_allowlist()` — #1758.
- `resolved_skill_dirs()` / `skill_repo_sha()` — #1742.

canonical: docs/issue-1772/proposals/skill-axis-phase-3-wave-3.md, its
implementation-steps section, read this turn.
Prior-waves pattern: a skill-repository skill per playbook axis file,
role-prefixed name (`skills/<role>-<axis>/SKILL.md`), byte-equal to the
rulebook's playbook source; already-`SKILL.md`-shaped content migrates
as a direct-copy check instead of a playbook wrap; a `templates/`
sibling under an already-`SKILL.md` source is excluded
(defect-verification precedent, reused in wave 3 for
`product-one-pager`); one allowlist entry per role listing all its
skill names; 3-check evidence via `resolve_role_source()`/`spawn_cmd()`
called directly.

canonical: `find /tmp/skill-repository/skills -maxdepth 1 \( -iname '*verify*' -o -iname '*severity*' -o -iname '*finding*' \)`, executed live this turn
```
skills/defect-verification-severity-band-assignment
skills/incident-response-severity-classification-scoping
skills/verify-finding-record
skills/verify-severity-classification
```
`verify-finding-record` / `verify-severity-classification` predate the
role-prefixed convention (pilot-era names, no `conformance-review-`
prefix) and are a different skill set from `conformance-review`'s own
`review-severity`/`review-traceability` sources below — this wave
migrates `conformance-review` under the established `conformance-review-*`
prefix, same convention as every other role, not reusing those two
legacy names.

## Live inventory: each wave-4 rulebook's guidance-skill content

Local clones from `tokenmaxxxer/<role>-rulebook` (git@github.com,
default branch, shallow) under `/tmp/onr-<role>-rulebook/`
(`sales-rulebook`/`technical-writing-rulebook` already existed
unprefixed in this session's environment); the rest were freshly
cloned this turn.

canonical: `find /tmp/onr-<role>-rulebook -path '*playbook*' -name '*.md' -not -path '*.git*'` and `find /tmp/onr-<role>-rulebook -path '*/skills/*' -not -path '*.git*' -type f`, executed live this turn across all 13 clones

```
release-engineering (top-level playbook/ axis files + pre-shaped skills/):
  branching-release-strategy.md, changelog-entry-categorization.md,
  deployment-rollout-strategy.md, release-cadence-and-toil.md,
  rollback-and-recovery.md, semver-bump-selection.md
  pre-shaped: error-budget-policy/skills/error-budget-policy/SKILL.md,
  postmortem/skills/postmortem/SKILL.md (+ templates/postmortem-template.md sibling),
  readiness-checklist/skills/readiness-checklist/SKILL.md,
  rollout-plan/skills/rollout-plan/SKILL.md

requirements-engineering (single combined playbook/rules.md; wc -l
  reports 235 lines, 7 axes per its own frontmatter):
  rules.md

risk-management (top-level playbook/ axis files):
  aggregation-consolidation.md, appetite-tolerance-threshold.md,
  likelihood-impact-scale.md, monitoring-review-cadence.md,
  response-strategy-selection.md

sales (top-level playbook/ axis files; sales-playbook/README.md is a
  plugin README documenting the playbook-gate hook, not a guidance
  source — excluded, not a playbook axis file):
  objection-handling.md, pitch-scoping-and-messaging-handoff.md,
  qualification-and-discovery.md

secure-coding (top-level playbook/ axis files):
  authorization-access-control.md, cryptography-secrets-management.md,
  dependency-supply-chain-security.md,
  input-validation-injection-defense.md, session-authentication.md

security-threat-model (single combined playbook/ file):
  threat-modeling-decision-rules.md

technical-feasibility (top-level playbook/ axis files + pre-shaped skills/):
  build-vs-buy-dependency-health.md, license-and-regulatory-risk.md,
  reversibility-and-spike-scoping.md, threat-model-disposition.md,
  verdict-and-timebox-selection.md
  pre-shaped: feasibility/skills/build-vs-buy/SKILL.md,
  feasibility/skills/license-scan/SKILL.md,
  feasibility/skills/reversibility-tag/SKILL.md,
  feasibility/skills/spike-report/SKILL.md (+ templates/spike-report-template.md sibling),
  feasibility/skills/stride-table/SKILL.md

technical-writing (top-level playbook/ axis files):
  doc-type-selection.md, minimalism-scoping.md, persuasion-trust.md,
  structure-comprehension.md, style-guide-compliance.md,
  tool-landscape.md

test-authoring (single file at a non-standard path, under
  docs/specs/playbook/ inside the test-authoring-rulebook clone rather
  than a top-level playbook/ dir):
  isolation-and-fixture-strategy.md

user-discovery (top-level playbook/ axis files):
  evidence-strength-tagging.md, follow-up-ladder-depth.md,
  question-design-past-behavior.md, saturation-stopping-rule.md,
  switch-timeline-causal-forces.md, verdict-prevalence-reporting.md

ux-engineering (top-level playbook/ axis files):
  color-visibility.md, control-selection.md, layout-grouping.md,
  navigation-depth.md, research-log.md, surface-contrast.md

implementation (top-level playbook/ axis files + one pre-shaped skill
  with load-bearing, non-template support files):
  complexity-coupling-management.md, design-pattern-selection.md,
  performance-data-structure-choice.md
  pre-shaped: blueprint/skills/blueprint/SKILL.md +
  blueprint/skills/blueprint/data/{antipatterns,archetypes,rules}.csv +
  blueprint/skills/blueprint/scripts/prep.py — unlike every prior
  pre-shaped-skill migration (whose only sibling was an excludable
  `templates/` dir), `blueprint`'s `SKILL.md` itself instructs the
  reader to query the CSVs rather than paste them; the CSVs and script
  are the skill's queryable database, not optional scaffolding.
  Excluding them would migrate a skill that cannot do what its own
  `SKILL.md` describes.

conformance-review (top-level playbook/ axis files + pre-shaped skills/):
  requirement-extraction.md, sampling-derivation.md,
  traceability-and-evidence.md, verdict-assignment.md,
  verification-method-selection.md
  pre-shaped: review-severity/skills/severity-classification/SKILL.md,
  review-traceability/skills/finding-record/SKILL.md (+ templates/finding-record-template.md sibling)
```

## Hook survey (preliminary — full per-line inspection is phase-2 record work)

canonical: `grep -rlE "re\.compile\(r'[^']{20,}" /tmp/onr-<role>-rulebook --include='*.py' --include='*.sh'`, executed live this turn across all 13 clones

Every file this grep matched sits under a `*-gate/hooks/*gate.sh` or
`hooks/lib/*` path whose gate name (proposal-norm, traceability,
req-id, qualification-stage, methodology-sequence, phase1-structure,
token-schema, coding-progress, survey-order, review-severity,
closed-checks) matches a category the earlier waves already classified
as structural record-shape checks, not new domain guidance absent from
the playbook text. Confirming each matched file's regex payloads
line-by-line against its role's playbook text (the wave-3 Check-1
method) is deferred to the phase-2 delivery record.

## Deviations from the established prior-waves shape this survey found

1. `requirements-engineering` and `security-threat-model` each ship a
   single combined `playbook/` file (not split per axis) — same shape
   already handled for `performance-engineering`/`pr-communications`
   (wave 3) and `content-design-operational-playbook`: one skill each,
   not split.
2. `test-authoring`'s sole playbook file lives at a path with an extra
   `docs/specs/` segment ahead of `playbook/`, not a top-level
   `playbook/` dir — the migration step must read this role's actual
   path, same "read the actual path per role" rule wave 3 already
   established for `marketing`.
3. `implementation`'s `blueprint` pre-shaped skill carries load-bearing
   `data/`+`scripts/` siblings that the skill's own `SKILL.md`
   requires at read time (query, don't paste) — this is not the
   excludable-`templates/`-sibling shape every prior wave's pre-shaped
   skills used. This wave migrates `blueprint`'s full directory
   (`SKILL.md` + `data/` + `scripts/`), not `SKILL.md` alone.
4. `sales`'s `sales-playbook/README.md` sits at a path that superficially
   resembles a playbook source but is a plugin README, not a guidance
   source — excluded on content inspection, not path pattern.
