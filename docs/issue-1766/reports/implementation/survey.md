# Current-state survey: skill-axis phase-3 batch wave 1 (#1766)

## Scope reminder

Wave-1 rulebooks (10, per the issue, excluding the already-migrated
`upstream-defect-report`): accessibility, api-design, architecture,
brand-design, capacity-planning, content-design, customer-support,
data-engineering, data-modeling, defect-verification.

Write set for this repo (`on-the-record`): `docs/specs/role-source-allowlist.json`,
`docs/issue-1766/**`. The `skill-repository` content PR is a separate
repository/write set, exactly as in the #1761 pilot.

## Prior mechanism (already merged, reused unchanged)

- `resolve_role_source()` / `_role_source_allowlist()` — #1758
  (0bf2faa5), transitional role→skill-repo resolution, fail-closed on
  a `hooks/` dir under a resolved skill.
- `resolved_skill_dirs()` / `skill_repo_sha()` — #1742 (pre-existing).
- Pilot pattern (#1761, 2aa8942e + 51ec338b): one skill-repository
  skill per playbook axis file, role-prefixed name
  (`skills/<role>-<axis>/SKILL.md`), byte-equal to the rulebook's
  `playbook/<axis>.md` source; one allowlist entry per role listing
  all its skill names; 3-check evidence captured by calling
  `resolve_role_source()`/`spawn_cmd()` directly (not the CLI
  `--dry-run` flag, which does not itself call resolution).

## Live inventory: each wave-1 rulebook's `playbook/` axis files

Local clones taken from `tokenmaxxxer/<role>-rulebook` (git@github.com,
default branch, shallow), one per role, under `/tmp/onr-<role>-rulebook/`.

derived:
```
$ for r in accessibility api-design architecture brand-design capacity-planning \
    content-design customer-support data-engineering data-modeling defect-verification; do
    ls /tmp/onr-$r-rulebook/playbook 2>/dev/null | sed "s#^#$r/#"
  done
```

- accessibility (1): `aria-and-contrast-rules.md` (222 lines)
- api-design (6): `error-design.md` (36), `http-semantics.md` (34),
  `payload-design.md` (34), `resource-modeling.md` (36),
  `tool-landscape.md` (56), `versioning-evolution.md` (40)
- architecture (5): `coupling-classification.md` (212),
  `decomposition-strategy.md` (95), `dependency-direction.md` (182),
  `interface-contract-shape.md` (125), `module-boundary-definition.md` (107)
- brand-design (5): `brand-consistency-governance.md` (35),
  `brand-identity-strategy.md` (37), `color-visibility.md` (34),
  `logo-clear-space-size.md` (30), `typography-pairing.md` (30)
- capacity-planning (5): `cost-attribution-at-trigger.md` (39),
  `demand-shape-and-forecast-method.md` (30),
  `expansion-trigger-threshold-sizing.md` (39),
  `headroom-band-and-degradation-risk.md` (39),
  `safety-buffer-sizing-by-criticality.md` (37)
- content-design (1): `operational-playbook.md` (295 lines)
- customer-support (6): `escalation-path.md` (33),
  `five-whys-recurring-scope.md` (36), `kcs-article-authoring.md` (35),
  `research-log.md` (84), `sla-tier-priority.md` (37),
  `subtraction-comprehensibility.md` (46)
- data-engineering (3): `data-quality.md` (100),
  `failure-handling.md` (97), `pipeline-design.md` (120)
- data-modeling (4): `datavault.md` (97), `inmon.md` (96),
  `kimball.md` (96), `structure.md` (101)
- defect-verification (4): `evidence-artifact-completeness.md` (90),
  `independence-from-upstream-verdicts.md` (30),
  `reproduction-evidence-quality.md` (36),
  `severity-band-assignment.md` (32)

Total: 40 playbook axis files across the 10 roles (vs. 3 for the
#1761 pilot's single role).

## Non-playbook skill content already present

`defect-verification` (role `verify`) additionally ships an
already-Skill-shaped `verify/skills/` directory with two skills
(`finding-record/`, `severity-classification/`) local to its own
plugin — these are not `playbook/` axis prose, they are already
`SKILL.md`-formatted. They are in scope for migration too (same
"guidance skills" language in the issue), and being already
`SKILL.md`-shaped, migrate as a direct copy check (no reformatting)
rather than a playbook→SKILL.md wrap.

No other wave-1 rulebook has a `skills/` directory outside its
`playbook/`.

## Hook surfaces per rulebook (candidates for "demoted-guidance" text)

Each rulebook ships one or more `hooks/` dirs beyond the base role
plugin (`<role>/hooks/`) — one per per-check gate plugin, e.g.
`architecture` has `arch-adr-content-gate`, `arch-citation-gate`,
`arch-sequence-gate`, `arch-phase1-checklist` in addition to
`architecture/hooks`; `customer-support` has six extra gate plugins;
`capacity-planning` four; `content-design` one
(`content-design-self-critique`); `data-engineering` three;
`data-modeling` none beyond the base; `brand-design` four;
`api-design` none beyond the base; `accessibility` two
(`wcag-em-gate`, `wcag-em-directive`); `defect-verification` four
(`verify-state-guard`, `verify-directive-depth`, `verify-outcome-gate`,
`verify-finding-gate`).

canonical: gh issue view 1766 (this turn's own read, quoted verbatim
above under "Batch mechanics") states each rulebook's fold hooks are
now covered by core's parameterized gates. Taking that framing as the
premise (not independently re-verified against #1765's merged diff in
this survey), the demoted-guidance step is: for each hook whose
*enforced rule* is not already restated in prose inside the
corresponding playbook axis file, append that rule as a marked
guidance paragraph to the relevant migrated `SKILL.md` (never silently
— the issue's acceptance 1 requires "demoted-guidance appendices
explicitly listed" in the record). Which hooks add new prose vs. which
duplicate existing playbook text is left as per-file judgment for the
phase-2 content-authoring step per rulebook — not enumerable from
directory listings alone.

## `role-source-allowlist.json` current state

canonical: docs/specs/role-source-allowlist.json (working tree, this repo)
```json
{
  "upstream-defect-report": [
    "upstream-defect-report-subtraction",
    "upstream-defect-report-comprehensibility",
    "upstream-defect-report-convention"
  ]
}
```

Only the pilot's single entry exists; none of the 10 wave-1 roles are
mapped yet — `resolve_role_source()` for all 10 currently falls
through to the rulebook-source default (unchanged behavior), matching
acceptance 2's stated "before the allowlist PR merges, behavior
unchanged" empty state.

## Batch mechanics from the issue (frozen)

- ONE `skill-repository` PR may carry all 10 roles' content.
- The allowlist PR maps all 10 roles at once, opened only AFTER the
  content PR merges (fail-closed ordering — an allowlist entry must
  never point at skill-repo content that isn't live yet).
- Rulebook repos are not archived in this issue.

## Skip conditions checked

Neither scout-directive skip condition (pure bugfix / spec leaves no
design decision open) applies outright, but the issue itself already
freezes the design: skill granularity (one skill per axis file,
role-prefixed), the two-PR/two-phase sequencing, and the 3-check
evidence shape are all pilot-precedent, not open here. Scouting this
turn is the file-inventory sweep above (live repo reads across all 10
rulebooks), which is the applicable "field" for a mechanical
migration — no external/product scouting applies (non-product,
infra-shaped work).
