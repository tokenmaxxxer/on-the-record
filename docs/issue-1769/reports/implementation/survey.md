# Current-state survey: skill-axis phase-3 batch wave 2 (#1769)

## Scope reminder

Wave-2 rulebooks (10, next alphabetical after wave 1 per the issue):
devrel, execution-observation, finance-unit-economics,
growth-analytics, incident-response, interaction-design,
issue-retrospective, knowledge-management, legal-compliance,
localization.

Write set for this repo (`on-the-record`):
`docs/specs/role-source-allowlist.json`, `docs/issue-1769/**`. The
`skill-repository` content PR is a separate repository/write set, same
as wave 1 (#1766) and the pilot (#1761).

## Prior mechanism (already merged, reused unchanged)

- `resolve_role_source()` / `_role_source_allowlist()` — #1758.
- `resolved_skill_dirs()` / `skill_repo_sha()` — #1742.
- Wave-1 pattern (#1766, 727e3ac3): one skill-repository skill per
  playbook axis file, role-prefixed name
  (`skills/<role>-<axis>/SKILL.md`), byte-equal to the rulebook's
  `playbook/<axis>.md` source; non-playbook already-`SKILL.md`-shaped
  content (defect-verification's `verify/skills/`) migrates as a
  direct-copy check instead of a playbook wrap; one allowlist entry per
  role listing all its skill names; 3-check evidence via
  `resolve_role_source()`/`spawn_cmd()` called directly.

## Live inventory: each wave-2 rulebook's guidance-skill content

Local clones from `tokenmaxxxer/<role>-rulebook` (git@github.com,
default branch, shallow), one per role, under
`/tmp/onr-<role>-rulebook/`.

canonical: this session's own `find`/`ls`/`wc -l` reads across all 10
`/tmp/onr-*-rulebook` clones (commands and per-role output produced
this turn, quoted below).

derived:
```
$ for r in devrel execution-observation finance-unit-economics growth-analytics \
    incident-response interaction-design issue-retrospective knowledge-management \
    legal-compliance localization; do
    echo "=== $r ==="; find /tmp/onr-$r-rulebook -maxdepth 3 -not -path '*/.git*'
  done
```
(full tree output captured this session; per-role summary below)

- devrel (3): `playbook/channel-convention.md` (79),
  `playbook/content-comprehensibility.md` (85),
  `playbook/program-subtraction.md` (76)
- finance-unit-economics (6): `playbook/cac-payback.md` (48),
  `playbook/evidence-chain.md` (61), `playbook/ltv-cac-band.md` (56),
  `playbook/ltv-churn-assumption.md` (51),
  `playbook/proposal-shape.md` (53),
  `playbook/sensitivity-scenario.md` (52)
- growth-analytics (5): `playbook/experiment-trust.md` (35),
  `playbook/funnel-stage-attribution.md` (26),
  `playbook/metric-selection.md` (25),
  `playbook/reporting-reduction.md` (29),
  `playbook/segmentation.md` (26)
- incident-response (6): `playbook/action-item-quality.md` (58),
  `playbook/blameless-language-editing.md` (60),
  `playbook/rca-method-selection.md` (61),
  `playbook/severity-classification-scoping.md` (49),
  `playbook/timeline-construction.md` (51),
  `playbook/tool-landscape.md` (61)
- interaction-design (1):
  `interaction-design/playbook/01-form-control-and-layout.md` (path is
  role-nested, not top-level `playbook/` — differs from the other
  wave-2 roles); `interaction-design/skills/` exists but holds only
  `.gitkeep` (no content)
- issue-retrospective (1):
  `playbook/timeline-comprehensibility-and-subtraction-rules.md` (138);
  `issue-retrospective/skills/` exists but holds only `.gitkeep`
- knowledge-management (5):
  `knowledge-management/knowledge-management/playbook/curation-pruning.md`,
  `structure-findability.md`, `taxonomy-tagging.md`,
  `supersession-lifecycle.md`, `pattern-extraction.md` (path is
  role-nested — `<repo>/knowledge-management/playbook/`, not top-level
  `playbook/`)
- legal-compliance (7): `playbook/consent-ux.md` (87),
  `playbook/cross-border-transfer.md` (68),
  `playbook/lawful-basis-selection.md` (68),
  `playbook/license-compatibility.md` (83),
  `playbook/research-log.md` (128),
  `playbook/retention-minimization.md` (87),
  `playbook/vendor-dpa.md` (91)
- localization (5): `playbook/locale-convention-formatting.md` (93),
  `playbook/pluralization-and-grammar.md` (85),
  `playbook/rtl-and-script-support.md` (69),
  `playbook/string-externalization.md` (110),
  `playbook/text-expansion-and-layout.md` (70)
- execution-observation (0): no `playbook/` directory, no `skills/`
  directory, anywhere in the repo. The role's guidance is entirely
  hook-delivered: `execution-observation/hooks/directive.sh` calls
  `plugins/eo-directive/hooks/directive-body.sh`, which defines the
  four directive-body variables (`you_decide`, `use_when`, `produces`,
  `hand_off`) as inline shell-script string content — not a standalone
  Markdown source file. `plugins/eo-methodology-gate` and
  `plugins/eo-state` are mechanical `PreToolUse`/`SessionStart` gates
  with no separate prose either. There is no file in this repo that a
  byte-equal `diff` could target for a `SKILL.md`.

Total playbook-axis files across the 9 roles that have them: 39
(devrel 3 + finance-unit-economics 6 + growth-analytics 5 +
incident-response 6 + interaction-design 1 + issue-retrospective 1 +
knowledge-management 5 + legal-compliance 7 + localization 5).
execution-observation contributes 0.

## The one genuine gap vs. the wave-1/pilot precedent

Wave 1's precedent for non-`playbook/`-shaped content
(defect-verification) was still a direct-copy case: the source was
already `SKILL.md`-formatted Markdown, just living outside
`playbook/`. execution-observation is different in kind, not just
location: its guidance text is embedded as shell-script variable
assignments inside `directive-body.sh`, not a Markdown file at all.
Extracting that text into a new `SKILL.md` would not be a byte-equal
copy of any existing file — it would be new prose authored from the
hook's variable content, which is a design/authoring judgment call the
wave-1 "byte-equal" constraint was written to avoid ("no spawn.py code
changes, same boundary the pilot held" / hook-derived content stays a
narrowly-scoped "demoted-guidance appendix" to an *existing* migrated
skill, never the sole source of a new one in wave 1's pattern). This
gap and the recommended resolution are carried into the proposal's
Rationale section, not decided silently here.

## `role-source-allowlist.json` current state

canonical: docs/specs/role-source-allowlist.json (working tree, this
repo, post-#1766/#1768 merge) — its keys are wave-1's 10 roles plus the
pilot's `upstream-defect-report`; none of the 10 wave-2 roles (devrel,
execution-observation, finance-unit-economics, growth-analytics,
incident-response, interaction-design, issue-retrospective,
knowledge-management, legal-compliance, localization) appear as keys
yet. `resolve_role_source()` for all 10 wave-2 roles currently falls
through to the rulebook-source default (unchanged behavior), matching
acceptance 2's stated "before the allowlist PR merges, behavior
unchanged" empty state.

## Batch mechanics from the issue (frozen, same as wave 1)

- ONE `skill-repository` PR may carry all migrated roles' content.
- The allowlist PR maps roles at once, opened only AFTER the content
  PR merges (fail-closed ordering).
- Rulebook repos are not archived in this issue.

## Skip conditions checked

Neither scout-directive skip condition applies outright, but as in
wave 1 the issue itself freezes the design (skill granularity,
two-phase sequencing, 3-check evidence shape) as pilot/wave-1
precedent — not open here except for the execution-observation gap
above, which is a genuinely new decision point this wave introduces
and belongs in the proposal's Rationale. Scouting this turn is the
live file-inventory sweep across all 10 rulebooks (mechanical,
infra-shaped work; no external/product scouting applies).
