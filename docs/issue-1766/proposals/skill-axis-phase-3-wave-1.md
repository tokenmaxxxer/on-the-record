---
status: proposed
files:
  - docs/specs/role-source-allowlist.json
  - docs/issue-1766/reports/implementation.md
---

# Skill-axis phase-3 batch wave 1: migrate 10 rulebooks (#1766)

## Request

Repeat the #1761 pilot pattern for 10 named rulebooks at once
(accessibility, api-design, architecture, brand-design,
capacity-planning, content-design, customer-support,
data-engineering, data-modeling, defect-verification): copy each
rulebook's guidance skills byte-equal into
`tokenmaxxxer/skill-repository`'s `skills/<role>-<axis>/SKILL.md`
(role-prefixed, no `hooks/` dirs, demoted-hook guidance appended and
marked), map each role to its skill set in
`docs/specs/role-source-allowlist.json`, and record per-rulebook
3-check equivalence evidence. Content PR (skill-repository) merges
first; the allowlist PR (this repo) follows only after, per the
issue's fail-closed batch-ordering instruction.

## Constraints

- Reuse `resolve_role_source()`/`_role_source_allowlist()` (#1758) and
  `resolved_skill_dirs()`/`skill_repo_sha()` (#1742) exactly as
  merged — no spawn.py code changes, same boundary the pilot held.
- This repo's write set stays `docs/specs/role-source-allowlist.json`
  and `docs/issue-1766/**` — the skill-repository content PR is a
  separate repository/write set, never part of this branch's commits.
- No `hooks/` subdirectory under any migrated skill dir (content
  constraint; `resolve_role_source()`'s existing fail-closed check
  backstops it but must not be needed to catch it).
- None of the 10 rulebook repos are archived, retitled, or otherwise
  modified by this issue.
- `defect-verification`'s pre-existing `verify/skills/finding-record`
  and `verify/skills/severity-classification` (already `SKILL.md`-
  shaped per the survey) migrate as direct-copy checks, not
  playbook→SKILL.md wraps — same "byte-equal" bar, different source
  shape.
- Per the survey, deciding which hook-enforced rules are not already
  restated in a playbook axis file is per-file judgment, not
  mechanically derivable — the content PR's author does this call at
  authoring time and the record lists every appended appendix
  explicitly (issue acceptance 1's own requirement), so a reviewer can
  audit the judgment call directly rather than trust it blind.

## Rationale

**Skill granularity: one skill per playbook axis file (or, for
defect-verification's two pre-shaped items, per existing skill),
role-prefixed — not one umbrella skill per rulebook.** Considered
instead: bundle each rulebook's playbook into a single umbrella
`SKILL.md` per role (10 skills total instead of ~40). Rejected for the
same reason the pilot rejected it: an umbrella file is not byte-equal
to any single source file (undermining acceptance 1's byte-equal
framing across 40 distinct source files), and
`role-source-allowlist.json`'s shape (`{role: [skill, ...]}`) and the
roster's plural `resolution_skills` field already model a per-axis
list — collapsing to one skill per role would be a new shape invented
for this migration rather than reuse of what #1758 already merged.

**One content PR for all 10 roles, one allowlist PR after, both
following the issue's explicit sequencing — not 10 independent
role-by-role PR pairs.** Considered instead: repeat the pilot exactly,
10 separate skill-repository PRs and 10 separate allowlist PRs (one
per role, sequential). Rejected because the issue's own "Batch
mechanics" section explicitly authorizes and expects the batched
form ("ONE skill-repository PR for the whole wave is fine; the
allowlist PR maps all 10 roles at once") — running 10 full PR cycles
here would be work the issue does not ask for and would multiply the
fail-closed-ordering risk window (10 separate merge-order windows
instead of 1) without a corresponding benefit; the per-rulebook unit
that must stay granular is the *evidence* (3 checks per rulebook in
the record), not the PR count.

## What will be done

1. In a local clone of `tokenmaxxxer/skill-repository`: for each of
   the 10 roles, add one `skills/<role>-<axis>/SKILL.md` per playbook
   axis file (role-prefixed name), byte-equal to
   `/tmp/onr-<role>-rulebook/playbook/<axis>.md`; for
   `defect-verification`, additionally add
   `skills/verify-finding-record/SKILL.md` and
   `skills/verify-severity-classification/SKILL.md` byte-equal to the
   rulebook's existing `verify/skills/{finding-record,severity-classification}/SKILL.md`.
   Where a rulebook's hook enforces a rule not already stated in its
   playbook axis text, append a clearly marked "Demoted from hook
   guidance" section to the relevant `SKILL.md`. No `hooks/` dir
   anywhere under the new skill dirs. Open one PR against
   `tokenmaxxxer/skill-repository` covering all 10 roles.
2. After that PR merges: in this repo, add 10 entries to
   `docs/specs/role-source-allowlist.json`, one per role, each listing
   its migrated skill names.
3. Produce and paste into `docs/issue-1766/reports/implementation.md`,
   per rulebook (10 repetitions of the pilot's 3 checks):
   - Check 1: recursive `diff -r`/per-file diff between the rulebook's
     `playbook/` (and, for defect-verification, `verify/skills/`) and
     the migrated `SKILL.md` files, each showing empty output for the
     byte-equal portion, with any demoted-guidance appendix listed
     separately as an intentional addition (not part of the diff
     claim).
   - Check 2: `resolve_role_source()` live output for the role,
     post-allowlist-merge, showing skill-repo source + sha.
   - Check 3: the same live call for one unmapped control role,
     unchanged (rulebook source), demonstrating the allowlist is
     additive.
4. Open the on-the-record PR carrying the allowlist file and the
   record, referencing `#1766` plainly (no Closes trailer — phase-1
   proposal PR).

## Out of scope

- Archiving or retitling any of the 10 rulebook repos.
- Migrating any rulebook outside the named 10 (later waves are
  separate issues).
- Changing `resolve_role_source()`, `resolved_skill_dirs()`, the CLI
  `--dry-run` branch, or any other spawn.py code.
- Removing the now-redundant hook files from the rulebook repos
  themselves (the issue's scope is skill-repository + allowlist only;
  hook removal, if wanted, is a separate rulebook-repo issue).
- A repo-wide naming-convention document beyond what these 10 roles'
  allowlist entries and skill names demonstrate.

## How you'll know it worked

- The skill-repository PR's ~42 new `SKILL.md` files (40 playbook-
  derived + 2 defect-verification pre-shaped) diff empty against their
  rulebook sources, with every demoted-guidance appendix explicitly
  called out in the record rather than folded silently into the
  byte-equal claim.
- `docs/specs/role-source-allowlist.json` maps all 10 wave-1 roles to
  their migrated skill names, and `resolve_role_source()` for each
  resolves to skill-repo source + sha live, pasted in the record.
- One control role (unmapped) still resolves to its rulebook source,
  byte-identical to its pre-allowlist behavior, pasted in the record.
