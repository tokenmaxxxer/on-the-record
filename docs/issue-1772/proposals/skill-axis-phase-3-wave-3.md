---
status: proposed
files:
  - docs/specs/role-source-allowlist.json
  - docs/issue-1772/reports/implementation.md
---

# Skill-axis phase-3 batch wave 3: migrate 10 more rulebooks (#1772)

## Request

Repeat the #1766 wave-1 / #1769 wave-2 pattern for the next 10 named
rulebooks (market-analysis, marketing, ml-engineering, observability,
partnerships-bd, performance-engineering, pr-communications, pricing,
product-discovery, refactoring-legacy): copy each rulebook's guidance
skills byte-equal into `tokenmaxxxer/skill-repository`'s
`skills/<role>-<axis>/SKILL.md` (role-prefixed, no `hooks/` dirs,
demoted-hook guidance appended and marked), map each role to its skill
set in `docs/specs/role-source-allowlist.json`, and record per-rulebook
3-check equivalence evidence. Content PR (skill-repository) merges
first; the allowlist PR (this repo) follows only after.

## Constraints

- Reuse `resolve_role_source()`/`_role_source_allowlist()` (#1758) and
  `resolved_skill_dirs()`/`skill_repo_sha()` (#1742) exactly as
  merged — no spawn.py code changes, same boundary wave 1/2 held.
- This repo's write set stays `docs/specs/role-source-allowlist.json`
  and `docs/issue-1772/**` — the skill-repository content PR is a
  separate repository/write set, never part of this branch's commits.
- No `hooks/` subdirectory under any migrated skill dir.
- None of the 10 rulebook repos are archived, retitled, or otherwise
  modified by this issue.
- `marketing` nests its `playbook/` under the role subdirectory
  (`<repo>/marketing/playbook/...`), same shape as wave-2's
  `knowledge-management`/`interaction-design` — the migration step
  reads the actual path per role, not a fixed top-level location.
- `performance-engineering` and `pr-communications` each ship a single
  combined playbook file, not one file per axis (same shape as the
  already-migrated `content-design-operational-playbook` skill and
  wave-2's `issue-retrospective`) — one skill each, not split.
- `product-discovery` ships two distinct guidance sources per the
  survey: 5 top-level `playbook/*.md` axis files AND 5 already-
  `SKILL.md`-shaped files under per-plugin `skills/<name>/SKILL.md`
  dirs (confirmed distinct content, not duplicates). Both migrate;
  `product-one-pager`'s `templates/one-pager-template.md` sibling does
  not (same "no supporting `templates/`" rule the defect-verification
  precedent already established).

## Rationale

**All 10 wave-3 roles get a content migration and an allowlist entry
this wave — unlike wave 2, no role is excluded.** Considered instead:
apply wave 2's `execution-observation` exclusion pattern speculatively
to whichever wave-3 role looked thinnest (ml-engineering's playbook
files are only 20 lines each, and performance-engineering/
pr-communications ship a single file rather than per-axis files, both
visually closer to "thin" than the rest of the wave). Rejected because
the exclusion rule is about the *existence* of a migratable Markdown
source, not its length or file count — the survey confirms all 10
roles have real `playbook/`-or-equivalent Markdown content to be
byte-equal to, so applying the exclusion here would be withholding a
migration that has a legitimate source, contradicting the issue's own
acceptance 1 ("all migratable wave-3 rulebooks' skills present").

**`product-discovery`'s 5 pre-shaped `skills/*/SKILL.md` files migrate
as direct copies alongside its 5 playbook-derived skills, rather than
being treated as out-of-scope or re-authored as playbook wraps.**
Considered instead: skip the pre-shaped `skills/` content this wave and
migrate only the 5 playbook axis files, treating the already-`SKILL.md`
content as a separate follow-up (mirroring how wave 2 deferred
`execution-observation`'s non-Markdown content). Rejected because this
case is not the same shape as `execution-observation` — a byte-equal
Markdown source already exists here (the `SKILL.md` files themselves),
so there is no "no source to be byte-equal to" problem, and the repo
already has a live precedent for exactly this shape
(`defect-verification`'s `verify/skills/` migrated as direct copies in
an earlier wave) — deferring a migratable source with no blocking
reason would be inconsistent with that precedent, not consistent with
it.

## What will be done

1. In a local clone of `tokenmaxxxer/skill-repository`: for each of
   the 10 wave-3 roles, add one `skills/<role>-<axis>/SKILL.md` per
   playbook axis file (role-prefixed name), byte-equal to the
   rulebook's playbook source at its actual path (top-level
   `playbook/` for 9 roles; role-nested `marketing/playbook/` for
   `marketing`, per the survey). For `product-discovery`, additionally
   add one `skills/<role>-<skill-name>/SKILL.md` per pre-shaped
   `skills/*/SKILL.md` source, direct-copied (no `templates/`
   siblings). Where a rulebook's hook enforces a rule not already
   stated in its playbook axis text, append a clearly marked "Demoted
   from hook guidance" section to the relevant `SKILL.md`. No `hooks/`
   dir anywhere under the new skill dirs. Open one PR against
   `tokenmaxxxer/skill-repository` covering all 10 roles.
2. After that PR merges: in this repo, add 10 entries to
   `docs/specs/role-source-allowlist.json`, one per role, each listing
   its migrated skill names.
3. Produce and paste into `docs/issue-1772/reports/implementation.md`,
   per rulebook (10 repetitions of the 3-check pattern):
   - Check 1: recursive `diff -r`/per-file diff between each
     rulebook's guidance-source directory/files and the migrated
     `SKILL.md` files, each showing empty output for the byte-equal
     portion, with any demoted-guidance appendix listed separately as
     an intentional addition.
   - Check 2: `resolve_role_source()` live output for each of the 10
     roles, post-allowlist-merge, showing skill-repo source + sha.
   - Check 3: the same live call for one unmapped control role (a role
     not touched by this wave, e.g. an as-yet-unmigrated later-wave
     role), demonstrating the allowlist addition is additive and its
     resolution is unchanged — same control-role method wave 2's
     Check 3 used.
4. Open the on-the-record PR carrying the allowlist file and the
   record, referencing `#1772` plainly (no Closes trailer — phase-1
   proposal PR).

## Out of scope

- Archiving or retitling any of the 10 rulebook repos.
- Migrating any rulebook outside the named 10 (later waves are
  separate issues).
- Changing `resolve_role_source()`, `resolved_skill_dirs()`, the CLI
  `--dry-run` branch, or any other spawn.py code.
- Removing the now-redundant hook files from the rulebook repos
  themselves.
- Migrating `product-one-pager`'s `templates/one-pager-template.md`
  supporting file (not a `SKILL.md`, excluded per the
  defect-verification precedent).
- A repo-wide naming-convention document beyond what these roles'
  allowlist entries and skill names demonstrate.

## How you'll know it worked

- The skill-repository PR's new `SKILL.md` files (playbook-derived for
  9 roles, playbook-derived plus 5 direct-copy for `product-discovery`)
  diff empty against their rulebook sources, with every
  demoted-guidance appendix explicitly called out in the record rather
  than folded silently into the byte-equal claim.
- `docs/specs/role-source-allowlist.json` maps all 10 wave-3 roles to
  their migrated skill names, and `resolve_role_source()` for each
  resolves to skill-repo source + sha live, pasted in the record.
- A control unmapped role still resolves to its rulebook source,
  byte-identical to its pre-allowlist behavior, pasted in the record
  as the wave's control-role evidence.
