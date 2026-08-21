# Current-state survey: skill-axis phase-3 batch wave 3 (#1772)

## Scope reminder

Wave-3 rulebooks (10, next alphabetical after wave 2 per the issue):
market-analysis, marketing, ml-engineering, observability,
partnerships-bd, performance-engineering, pr-communications, pricing,
product-discovery, refactoring-legacy.

Write set for this repo (`on-the-record`):
`docs/specs/role-source-allowlist.json`, `docs/issue-1772/**`. The
`skill-repository` content PR is a separate repository/write set, same
as wave 1 (#1766) and wave 2 (#1769).

## Prior mechanism (already merged, reused unchanged)

- `resolve_role_source()` / `_role_source_allowlist()` — #1758.
- `resolved_skill_dirs()` / `skill_repo_sha()` — #1742.
- Wave-1/2 pattern (#1766, #1769): one skill-repository skill per
  playbook axis file, role-prefixed name
  (`skills/<role>-<axis>/SKILL.md`), byte-equal to the rulebook's
  playbook source; non-playbook already-`SKILL.md`-shaped content
  (defect-verification's `verify/skills/`, wave-0 precedent) migrates
  as a direct-copy check instead of a playbook wrap; one allowlist
  entry per role listing all its skill names; 3-check evidence via
  `resolve_role_source()`/`spawn_cmd()` called directly.

canonical: `find /tmp/onr-defect-verification-rulebook -path '*skills*' -not -path '*.git*'` and `find /tmp/skill-repository/skills/defect-verification* -maxdepth 2`, both executed live this turn
```
/tmp/onr-defect-verification-rulebook/verify/skills/finding-record/templates/finding-record-template.md
/tmp/skill-repository/skills/defect-verification-evidence-artifact-completeness/SKILL.md
/tmp/skill-repository/skills/defect-verification-independence-from-upstream-verdicts/SKILL.md
/tmp/skill-repository/skills/defect-verification-reproduction-evidence-quality/SKILL.md
/tmp/skill-repository/skills/defect-verification-severity-band-assignment/SKILL.md
```

Supporting `templates/` subdirectories under an already-`SKILL.md`-
shaped source are NOT migrated: the rulebook source above ships a
`templates/finding-record-template.md` sibling, but the migrated
`skill-repository` skill dirs above hold only `SKILL.md`, no
`templates/`. This wave follows the same rule for `product-discovery`'s
`one-pager` skill (see inventory below).

## Live inventory: each wave-3 rulebook's guidance-skill content

Local clones from `tokenmaxxxer/<role>-rulebook` (git@github.com,
default branch, shallow) under `/tmp/onr-<role>-rulebook/` — 3 already
existed in this session's environment
(observability, performance-engineering, pr-communications); the
other 7 (market-analysis, marketing, ml-engineering, partnerships-bd,
pricing, product-discovery, refactoring-legacy) were freshly cloned
this turn.

canonical: `find /tmp/onr-<role>-rulebook -path '*playbook*' -name '*.md' -exec wc -l {} \;` and `find /tmp/onr-<role>-rulebook -path '*/skills/*' -not -path '*.git*' -type f`, executed live this turn across all 10 clones

```
market-analysis (5, top-level playbook/):
  competitor-mapping.md (76), evidence-rigor.md (80),
  five-forces.md (82), jtbd-fit.md (81), mece-proposal.md (79)

marketing (5, role-nested marketing/playbook/):
  channel-selection.md (54), message-persuasion.md (66),
  positioning-differentiation.md (56), scope-pruning.md (61),
  segment-targeting.md (55)

ml-engineering (6, top-level playbook/):
  evaluation-discipline.md (20), ml-test-score-scoring.md (20),
  model-provenance-versioning.md (20), rollout-promotion-rollback.md (20),
  serving-pattern-selection.md (20), slo-definition-tradeoffs.md (20)

observability (7, top-level playbook/):
  cardinality-budget.md (54), explorability.md (45),
  methodology-selection.md (44), phase-trace.md (45),
  signal-golden.md (47), signal-red.md (47), signal-use.md (46)

partnerships-bd (5, top-level playbook/):
  deal-structure-selection.md (23), exclusivity-and-scope-terms.md (22),
  governance-cadence-and-kpi.md (23), negotiation-positioning.md (22),
  term-sheet-comprehensibility-and-convention.md (23)

performance-engineering (1, top-level playbook/):
  operational-playbook.md (118) — single combined file, same shape as
  the already-migrated `content-design-operational-playbook` skill
  (content-design rulebook, an earlier wave)

pr-communications (1, top-level playbook/):
  message-planning-and-evaluation-rules.md (164) — single combined file

pricing (5, top-level playbook/):
  design-rigor.md (76), method-family.md (69), scope-gate.md (59),
  tier-structure.md (64), verdict-report.md (69)

product-discovery (5 playbook + 5 pre-shaped skills, top-level
  playbook/ AND top-level <plugin>/skills/<name>/SKILL.md):
  playbook/: guardrail-metric-status.md (30),
  hypothesis-preregistration.md (32), jtbd-problem-framing.md (30),
  opportunity-solution-tree-branching.md (32),
  rice-ice-prioritization.md (30)
  skills/ (already SKILL.md-shaped, distinct topics from the playbook
  files above, confirmed by `diff` this turn — not duplicates):
  product-assumption-mapping/skills/assumption-mapping/SKILL.md,
  product-guardrail-metrics/skills/guardrail-metrics/SKILL.md,
  product-hypothesis-testing/skills/hypothesis-testing/SKILL.md,
  product-one-pager/skills/one-pager/SKILL.md (plus a
  templates/one-pager-template.md sibling, not migrated per the
  defect-verification precedent above),
  product-opportunity-solution-tree/skills/opportunity-solution-tree/SKILL.md

refactoring-legacy (5, top-level playbook/):
  characterization-test-scope.md (28), refactoring-step-decomposition.md (24),
  seam-selection.md (24), strangler-fig-migration.md (24),
  verification-cadence.md (22)
```

## Structural notes (role-specific quirks)

- `marketing` nests its `playbook/` under the role subdirectory
  (`<repo>/marketing/playbook/...`), same shape as wave-2's
  `knowledge-management`/`interaction-design` — the migration step
  must read the actual nested path, not assume repo-top-level
  `playbook/`.
- `performance-engineering` and `pr-communications` each ship a single
  combined playbook file rather than one file per axis — same shape
  as the already-migrated `content-design-operational-playbook` (an
  earlier wave) and wave-2's `issue-retrospective` (single-file role).
  One skill each.
- `product-discovery` is the wave's only role with two distinct
  guidance sources: 5 playbook axis files AND 5 already-`SKILL.md`-
  shaped files under per-plugin `skills/` dirs (verified distinct
  content, not duplicates, via `diff` this turn — see inventory
  above). Both sets are migratable; total 10 skills for this role.
- All 10 wave-3 roles ship migratable Markdown guidance — unlike
  wave 2's `execution-observation`, none of this wave's roles needs
  the "no migratable source, no allowlist entry" exclusion path
  (#1769 precedent). No exclusions this wave.

canonical: `ls /tmp/skill-repository/skills | grep -E 'market-analysis|^marketing|ml-engineering|observability|partnerships-bd|performance-engineering|pr-communications|^pricing|product-discovery|refactoring-legacy'`, executed live this turn
```
pricing-research
```

None of the 10 wave-3 roles' skill names exist yet in
`tokenmaxxxer/skill-repository`'s `skills/` directory — the single
match above (`pricing-research`) belongs to a different, already-
migrated role (a market-recon-adjacent skill from an earlier wave),
not this issue's `pricing` role.

## hooks/ inventory (for phase-2 demoted-guidance determination)

canonical: `find /tmp/onr-<role>-rulebook -mindepth 1 -maxdepth 1 -type d -not -path '*.git*'`, executed live this turn across all 10 clones

Each role's plugin directories under `<role>-rulebook/` include a
top-level `<role>/hooks/directive.sh` plus, for most roles, several
axis-specific plugin `hooks/` dirs beyond it (e.g. market-analysis has
5 axis plugin dirs each with `hooks/`; ml-engineering has 5;
observability has 7; product-discovery has 5). Whether any of these
extra hook plugins enforce a rule not already stated in the
corresponding playbook axis text (candidate for a "Demoted from hook
guidance" appendix, per the #1766/#1769 precedent) is a phase-2
determination made against the actual gate script content at build
time, cross-checked the same way wave 2's Summary of work section did
— not decided in this survey.
