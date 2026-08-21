---
status: proposed
files:
  - docs/specs/role-source-allowlist.json
  - docs/issue-1777/reports/implementation.md
---

# Skill-axis phase-3 batch wave 4 (final): migrate the remaining 13 rulebooks (#1777)

## Request

Repeat the #1766 wave-1 / #1769 wave-2 / #1772 wave-3 pattern for the
final 13 named rulebooks (release-engineering, requirements-engineering,
risk-management, sales, secure-coding, security-threat-model,
technical-feasibility, technical-writing, test-authoring,
user-discovery, ux-engineering, implementation, conformance-review):
copy each rulebook's guidance skills byte-equal into
`tokenmaxxxer/skill-repository`'s `skills/<role>-<axis>/SKILL.md`
(role-prefixed, no `hooks/` dirs, demoted-hook guidance appended and
marked), map each role to its skill set in
`docs/specs/role-source-allowlist.json`, and record per-rulebook
3-check equivalence evidence. `implementation` and `conformance-review`
map last within the allowlist PR, with an added post-mapping smoke: a
`resolve_role_source()` check per role plus a real `spawn --dry-run` of
`implementation` confirming session assembly. Content PR
(skill-repository) merges first; the allowlist PR (this repo) follows
only after.

## Constraints

- Reuse `resolve_role_source()`/`_role_source_allowlist()` (#1758) and
  `resolved_skill_dirs()`/`skill_repo_sha()` (#1742) exactly as
  merged — no spawn.py code changes, same boundary the prior three
  waves held.
- This repo's write set stays `docs/specs/role-source-allowlist.json`
  and `docs/issue-1777/**` — the skill-repository content PR is a
  separate repository/write set, never part of this branch's commits.
- No `hooks/` subdirectory under any migrated skill dir.
- None of the 13 rulebook repos are archived, retitled, or otherwise
  modified by this issue.
- `requirements-engineering` and `security-threat-model` each ship a
  single combined playbook file, not one file per axis (same shape as
  the already-migrated `content-design-operational-playbook` and wave
  3's `performance-engineering`/`pr-communications`) — one skill each,
  not split.
- `test-authoring`'s sole playbook file lives at a non-standard path
  (an extra `docs/specs/` segment ahead of `playbook/`) — the
  migration step reads the actual path per role, per the survey, not a
  fixed top-level location (same rule wave 3 established for
  `marketing`).
- `implementation`'s `blueprint` pre-shaped skill ships load-bearing
  `data/`+`scripts/` siblings its own `SKILL.md` requires at read
  time — migrates as a full directory copy (`SKILL.md` + `data/` +
  `scripts/`), not `SKILL.md` alone (see Rationale).
- `sales`'s `sales-playbook/README.md` is a plugin README, not a
  guidance source, and does not migrate.
- `implementation` and `conformance-review` map last in the allowlist
  PR's commit-internal ordering, and their mapping gets the
  issue-mandated extra smoke (dry-run assembly), per the issue's own
  requirement that this wave's own reviewer role is the first live
  consumer of these two mappings.

## Rationale

**`blueprint`'s `data/`+`scripts/` siblings migrate as part of the
skill's direct copy, rather than being excluded the way every prior
wave excluded a pre-shaped skill's `templates/` sibling.** Considered
instead: apply the established templates-exclusion rule uniformly —
copy only `blueprint/skills/blueprint/SKILL.md`, dropping `data/` and
`scripts/`, for consistency with how `postmortem`, `spike-report`, and
`finding-record` each dropped their `templates/` sibling this same
wave. Rejected because the exclusion rule's own basis is that a
`templates/` file is optional scaffolding a skill's `SKILL.md` doesn't
require to function — `blueprint`'s `SKILL.md` explicitly instructs
the reader to query the CSVs rather than paste them, making `data/`
the skill's queryable database and `scripts/prep.py` part of how that
database is built; dropping them would migrate a skill that cannot do
what its own `SKILL.md` describes, which is a different situation from
an excludable template file, not the same rule applied consistently.

**`implementation` and `conformance-review` land last within a single
allowlist PR commit, rather than in two separate PRs (one for the
other 11 roles, one for these two).** Considered instead: split the
allowlist change into two PRs so the higher-traffic roles' mapping
could be reviewed and merged independently, with more room to revert
just those two without touching the other 11. Rejected because the
issue's acceptance criteria treat this as one wave with one dry-run
smoke requirement attached to the two highest-traffic roles, not two
separate deliveries — splitting the PR would multiply the on-the-record
overhead (two survey/proposal cycles, two approval rounds) for a
distinction (commit-internal ordering vs. PR count) the issue itself
frames as an ordering constraint within one allowlist change, not a
delivery-boundary constraint.

## What will be done

1. In a local clone of `tokenmaxxxer/skill-repository`: for each of
   the 13 wave-4 roles, add a `skills/<role>-<axis>/SKILL.md` per
   playbook axis file (role-prefixed name), byte-equal to the
   rulebook's playbook source at its actual path (per the survey).
   For `release-engineering`, `technical-feasibility`, and
   `conformance-review`, additionally direct-copy each pre-shaped
   `skills/*/SKILL.md` source (dropping any `templates/` sibling, same
   rule as the defect-verification/wave-3 precedent). For
   `implementation`, direct-copy `blueprint`'s full skill directory
   including `data/` and `scripts/` (see Rationale). Where a
   rulebook's hook enforces a rule not already stated in its playbook
   axis text, append a clearly marked "Demoted from hook guidance"
   section to the relevant `SKILL.md`. No `hooks/` dir anywhere under
   the new skill dirs. Open one PR against `tokenmaxxxer/skill-repository`
   covering all 13 roles.
2. After that PR merges: in this repo, add 13 entries to
   `docs/specs/role-source-allowlist.json`, one per role, with
   `implementation` and `conformance-review` added last within the
   commit, each entry listing its migrated skill names.
3. Produce and paste into `docs/issue-1777/reports/implementation.md`,
   per rulebook (13 repetitions of the 3-check pattern):
   - Check 1: recursive `diff -r`/per-file diff between each
     rulebook's guidance-source directory/files and the migrated
     `SKILL.md` files, each showing empty output for the byte-equal
     portion, with any demoted-guidance appendix listed separately as
     an intentional addition, and `blueprint`'s `data/`/`scripts/`
     copies diffed the same way.
   - Check 2: `resolve_role_source()` live output for each of the 13
     roles, post-allowlist-merge, showing skill-repo source + sha.
   - Check 3: the same live call for one unmapped control role,
     demonstrating the allowlist addition is additive and its
     resolution is unchanged — same control-role method the prior
     waves used.
   - Wave-4-only smoke: a `resolve_role_source()` live output for
     `implementation` and for `conformance-review` specifically called
     out under their own subheading, plus one real
     `spawn.py ... --dry-run` invocation for `implementation` pasted
     in full, confirming the dry-run session assembles against the
     skill-repo-sourced skills.
4. Open the on-the-record PR carrying the allowlist file and the
   record, referencing `#1777` plainly (no Closes trailer — phase-1
   proposal PR).

## Out of scope

- Archiving or retitling any of the 13 rulebook repos.
- Migrating any rulebook outside the named 13 (this is the final
  wave — no further waves follow).
- Changing `resolve_role_source()`, `resolved_skill_dirs()`, the CLI
  `--dry-run` branch, or any other spawn.py code.
- Removing the now-redundant hook files from the rulebook repos
  themselves.
- Migrating `sales-playbook/README.md`, `postmortem-template.md`,
  `spike-report-template.md`, or `finding-record-template.md` (none
  are `SKILL.md`-shaped guidance sources or, for the README, a
  guidance source at all).
- A repo-wide naming-convention document beyond what these roles'
  allowlist entries and skill names demonstrate.

## How you'll know it worked

- The skill-repository PR's new `SKILL.md` files diff empty against
  their rulebook sources, with every demoted-guidance appendix
  explicitly called out in the record rather than folded silently into
  the byte-equal claim, and `blueprint`'s `data/`/`scripts/` copies
  diffed empty too.
- `docs/specs/role-source-allowlist.json` maps all 13 wave-4 roles to
  their migrated skill names, and `resolve_role_source()` for each
  resolves to skill-repo source + sha live, pasted in the record.
- A control unmapped role still resolves to its rulebook source,
  byte-identical to its pre-allowlist behavior, pasted in the record
  as the wave's control-role evidence.
- `implementation` and `conformance-review` each show a dedicated
  `resolve_role_source()` live output, and `implementation` shows one
  full `spawn.py --dry-run` transcript proving session assembly
  against the new skill-repo mapping — the issue's own acceptance
  check 2 requirement.
