---
status: proposed
files:
  - docs/specs/role-source-allowlist.json
  - docs/issue-1769/reports/implementation.md
---

# Skill-axis phase-3 batch wave 2: migrate 10 more rulebooks (#1769)

## Request

Repeat the #1766 wave-1 pattern for the next 10 named rulebooks
(devrel, execution-observation, finance-unit-economics,
growth-analytics, incident-response, interaction-design,
issue-retrospective, knowledge-management, legal-compliance,
localization): copy each rulebook's guidance skills byte-equal into
`tokenmaxxxer/skill-repository`'s `skills/<role>-<axis>/SKILL.md`
(role-prefixed, no `hooks/` dirs, demoted-hook guidance appended and
marked), map each role to its skill set in
`docs/specs/role-source-allowlist.json`, and record per-rulebook
3-check equivalence evidence. Content PR (skill-repository) merges
first; the allowlist PR (this repo) follows only after.

## Constraints

- Reuse `resolve_role_source()`/`_role_source_allowlist()` (#1758) and
  `resolved_skill_dirs()`/`skill_repo_sha()` (#1742) exactly as
  merged — no spawn.py code changes, same boundary wave 1 held.
- This repo's write set stays `docs/specs/role-source-allowlist.json`
  and `docs/issue-1769/**` — the skill-repository content PR is a
  separate repository/write set, never part of this branch's commits.
- No `hooks/` subdirectory under any migrated skill dir.
- None of the 10 rulebook repos are archived, retitled, or otherwise
  modified by this issue.
- `interaction-design` and `issue-retrospective` each ship a
  role-local `skills/.gitkeep`-only placeholder directory — per the
  survey this holds no content, so it is not a migration source; the
  migration source for both is their `playbook/` file(s), same as
  every other wave-2 role.
- `knowledge-management` and `interaction-design` nest their
  `playbook/` under the role subdirectory
  (`<repo>/<role>/playbook/...`) rather than at repo top level
  (`<repo>/playbook/...`, the shape every other wave-2 role and all of
  wave 1 use) — the migration script/authoring step must read from the
  actual path per role, not assume a fixed top-level location.
- `execution-observation` ships no `playbook/` and no
  Markdown-shaped guidance source at all (survey: its guidance lives
  as shell-variable content inside `directive-body.sh`) — see
  Rationale for how this wave handles it; the "byte-equal to an
  existing Markdown file" bar from wave 1 is not relaxed for it.

## Rationale

**execution-observation gets no content migration this wave and no
allowlist entry; it remains rulebook-sourced (serves as this wave's
"unmapped control role" for acceptance check 2/3) — not extracted from
its hook script into a new SKILL.md.** Considered instead: extract the
four `directive-body.sh` variable strings (`you_decide`, `use_when`,
`produces`, `hand_off`) into a new `execution-observation-directive/SKILL.md`
and migrate that. Rejected because there is no existing Markdown file
for that content to be byte-equal *to* — authoring one from shell-script
variable text is new prose composition, not a copy, which breaks the
"byte-equal" bar the issue's acceptance 1 explicitly requires ("byte-equal,
demoted-guidance appendices explicitly listed" — an appendix is additive
to an existing byte-equal migration, never the sole content of one) and
reopens the "no spawn.py/authoring judgment beyond file selection"
boundary wave 1 held. Migrating execution-observation, if wanted, is a
separate follow-up issue scoped to that extraction decision on its own
merits, not folded silently into this batch.

**One content PR for the 9 roles that have migratable content, one
allowlist PR after, both following the issue's explicit sequencing —
not 10 independent role-by-role PR pairs.** Considered instead: repeat
wave 1's per-role granularity exactly. Rejected for the same reason
wave 1 gave: the issue's "Batch mechanics" section authorizes and
expects the batched form, and running 10 full PR cycles multiplies the
fail-closed-ordering risk window without benefit — the per-rulebook
unit that must stay granular is the *evidence* (3 checks per rulebook
in the record), not the PR count.

## What will be done

1. In a local clone of `tokenmaxxxer/skill-repository`: for each of
   the 9 content-bearing roles (all wave-2 roles except
   execution-observation), add one `skills/<role>-<axis>/SKILL.md` per
   playbook axis file (role-prefixed name), byte-equal to the
   rulebook's playbook source at its actual path (top-level
   `playbook/` for 7 roles; role-nested `<role>/playbook/` for
   `interaction-design` and `knowledge-management`, per the survey).
   Where a rulebook's hook enforces a rule not already stated in its
   playbook axis text, append a clearly marked "Demoted from hook
   guidance" section to the relevant `SKILL.md`. No `hooks/` dir
   anywhere under the new skill dirs. Open one PR against
   `tokenmaxxxer/skill-repository` covering all 9 roles.
2. After that PR merges: in this repo, add 9 entries to
   `docs/specs/role-source-allowlist.json`, one per content-bearing
   role, each listing its migrated skill names. No entry for
   `execution-observation`.
3. Produce and paste into `docs/issue-1769/reports/implementation.md`,
   per rulebook (9 repetitions of the 3-check pattern, plus
   execution-observation's control-role check):
   - Check 1: recursive `diff -r`/per-file diff between each of the 9
     rulebooks' guidance-source directory and the migrated `SKILL.md`
     files, each showing empty output for the byte-equal portion, with
     any demoted-guidance appendix listed separately as an intentional
     addition.
   - Check 2: `resolve_role_source()` live output for each of the 9
     roles, post-allowlist-merge, showing skill-repo source + sha.
   - Check 3: the same live call for `execution-observation` (unmapped
     this wave by design, not omission), demonstrating the allowlist
     is additive and its resolution is unchanged.
4. Open the on-the-record PR carrying the allowlist file and the
   record, referencing `#1769` plainly (no Closes trailer — phase-1
   proposal PR).

## Out of scope

- Migrating `execution-observation`'s hook-embedded directive content
  into a new skill (separate follow-up issue if wanted).
- Archiving or retitling any of the 10 rulebook repos.
- Migrating any rulebook outside the named 10 (later waves are
  separate issues).
- Changing `resolve_role_source()`, `resolved_skill_dirs()`, the CLI
  `--dry-run` branch, or any other spawn.py code.
- Removing the now-redundant hook files from the rulebook repos
  themselves.
- A repo-wide naming-convention document beyond what these roles'
  allowlist entries and skill names demonstrate.

## How you'll know it worked

- The skill-repository PR's ~39 new `SKILL.md` files (all
  playbook-derived, across the 9 content-bearing roles) diff empty
  against their rulebook sources, with every demoted-guidance appendix
  explicitly called out in the record rather than folded silently into
  the byte-equal claim.
- `docs/specs/role-source-allowlist.json` maps the 9 content-bearing
  wave-2 roles to their migrated skill names, and
  `resolve_role_source()` for each resolves to skill-repo source + sha
  live, pasted in the record.
- `execution-observation` still resolves to its rulebook source,
  byte-identical to its pre-allowlist behavior, pasted in the record
  as the wave's control-role evidence.
