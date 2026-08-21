---
status: proposed
files:
  - docs/specs/role-source-allowlist.json
  - docs/issue-1761/reports/implementation.md
---

# Skill-axis phase-3 pilot: migrate upstream-defect-report-rulebook to skill-repository (#1761)

## Request

Migrate the `upstream-defect-report-rulebook`'s three playbook axis
files into `tokenmaxxxer/skill-repository`'s `skills/` (byte-equal
content, no `hooks/` dirs), map the `upstream-defect-report` role to
those skills in `docs/specs/role-source-allowlist.json`, and record the
3-check equivalence evidence (#1758's frozen phasing) in the issue
record: (1) byte-equal recursive diff, (2) pre/post `--dry-run`
argv/env diff plus one unrelated role's dry-run staying byte-identical,
(3) roster/record field inspection showing skill-repo source+sha for
the mapped role. Two separate PRs: one against `skill-repository`
(content), one against this repo (the allowlist mapping). The rulebook
repo itself is not archived in this issue.

## Constraints

- No new abstraction: reuse #1758's `resolve_role_source()`/
  `_role_source_allowlist()` and #1742's `resolved_skill_dirs()`/
  `skill_repo_sha()` exactly as merged — this issue supplies data
  (skill files + one allowlist entry), not new spawn.py mechanism.
- skill-repository content must be guidance-only: no `hooks/`
  subdirectory under any migrated skill dir (enforced mechanically by
  `resolve_role_source()`'s existing fail-closed `sys.exit`, but the
  content itself must not need that refusal to trigger).
- This repo's write set is limited to
  `docs/specs/role-source-allowlist.json` and `docs/issue-1761/**` per
  the issue's own `scope:` line — the skill-repository content PR is a
  separate repository and a separate write set, not part of this
  branch's commits.
- The rulebook repo (`upstream-defect-report-rulebook`) is not
  archived, retitled, or otherwise modified by this issue.
- `resolved_skill_dirs()` treats a skill name as an immediate child of
  whatever directory `_skill_repo_root()` resolves to — it does not
  itself descend into a `skills/` subdirectory.
  canonical: warrant-hunter finding, docs/issue-1761/reports/
  implementation/hunt-skill-axis-phase-3-pilot.md (this turn's own
  reproduction) — pointing `MUSTER_SKILL_REPO` at a skill-repository
  clone's root (not its `skills/` subdir) and resolving
  `upstream-defect-report-subtraction` fails closed with "모르는 스킬
  ... 쓸 수 있는 이름: docs, skills" instead of resolving. Since
  skill-repository's real top-level layout nests every existing skill
  one level under `skills/` (per the survey's live inventory), the
  phase-2 equivalence evidence in "What will be done" step 3 must set
  `MUSTER_SKILL_REPO` to the clone's `skills/` subdirectory (e.g.
  `<clone>/skills`), not the clone root — a deployment/evidence-capture
  detail, not a spawn.py code change, so it stays inside this
  Constraint's "no code changes" boundary.
- Acceptance 2's `--dry-run` wording must be satisfied honestly: the
  current CLI `--dry-run` branch does not itself call
  `resolve_role_source()`/`spawn_cmd()` (see survey). The evidence must
  be produced at the `resolve_role_source()`/`spawn_cmd()` call level
  (the same level #1758's own test suite already exercises) and the
  record must say so plainly rather than imply the bare CLI flag
  already shows resolution differences.

## Rationale

**Skill directory granularity: one skill per axis (role-prefixed),
not one skill per rulebook.** Considered instead: a single umbrella
directory `skills/upstream-defect-report/` holding all three axis
files together (plus a synthesizing `SKILL.md`). Rejected because it
would require either inventing new umbrella content (not itself
byte-equal to anything in the rulebook, undermining acceptance 1's
"byte-equal" framing) or nesting the three files under non-obvious
names, and because `role-source-allowlist.json`'s own mapping shape is
already a list of skill names per role (`{role: [skill, ...]}`) and the
roster's `resolution_skills` field is already plural — a per-axis split
is the mapping this mechanism already models, not a new one invented
for this migration. The chosen shape: `skills/
upstream-defect-report-subtraction/SKILL.md`,
`skills/upstream-defect-report-comprehensibility/SKILL.md`,
`skills/upstream-defect-report-convention/SKILL.md`, each `SKILL.md`
byte-equal to its corresponding `/tmp/udr-rulebook/playbook/<axis>.md`
source file (per the survey's file inventory).

**Evidence produced by exercising `resolve_role_source()`/
`spawn_cmd()` directly, not the bare CLI `--dry-run` flag.** Considered
instead: extend the CLI `--dry-run` branch itself to call
`resolve_role_source()` so the JSON output visibly changes pre/post
mapping. Rejected for this issue: that would be a spawn.py code change
beyond this repo's declared write set (`docs/specs/
role-source-allowlist.json` and `docs/issue-1761/**` only, per the
issue's own `scope:` line) — widening it here would be exactly the
kind of scope creep the SCOPE-EXCEEDED rule exists to stop. The
equivalence evidence instead calls `resolve_role_source()` and
`spawn_cmd()` directly (Python one-liners or a small ad hoc script, not
committed to the write set) for `upstream-defect-report` before and
after the allowlist file exists, plus once for an unrelated unmapped
role to confirm byte-identical output — the same level #1758's own
`test/test_spawn_role_skill_resolution.py` already proved this
mechanism at.

## What will be done

1. In a local clone of `tokenmaxxxer/skill-repository` (outside this
   repo's git tree): add `skills/upstream-defect-report-subtraction/
   SKILL.md`, `skills/upstream-defect-report-comprehensibility/
   SKILL.md`, `skills/upstream-defect-report-convention/SKILL.md`, each
   byte-equal to the corresponding `/tmp/udr-rulebook/playbook/*.md`
   file. No `hooks/` directory anywhere under these three new skill
   dirs. Open a PR against `tokenmaxxxer/skill-repository`.
2. In this repo: add `docs/specs/role-source-allowlist.json` mapping
   `"upstream-defect-report"` to the three new skill names above.
3. Produce and paste into `docs/issue-1761/reports/implementation.md`:
   - Check 1: `diff -r` between `/tmp/udr-rulebook/playbook/` and the
     three migrated `SKILL.md` files (per-file diff, since the
     directory names differ by design — see Rationale), each showing
     empty output.
   - Check 2: `resolve_role_source("upstream-defect-report", ...)` +
     `spawn_cmd(...)` argv/env, captured before the allowlist file
     exists (source: rulebook) and after (source: skill-repo), diffed;
     plus the same capture for one unrelated, unmapped role, diffed
     against its own pre-mapping baseline, showing byte-identical
     output.
   - Check 3: the roster/record fields
     (`resolution_source`/`resolution_skills`/`resolution_skill_sha`)
     produced by that same post-mapping `resolve_role_source()` call
     for `upstream-defect-report`, pasted verbatim.
4. Open the on-the-record PR carrying the allowlist file and the
   record. Reference both this issue (`#1761`) plainly; the rulebook
   repo stays unarchived and untouched.

## Out of scope

- Archiving or retitling `upstream-defect-report-rulebook`.
- Migrating any other rulebook (this is the single-role pilot).
- Changing the CLI `--dry-run` branch, `resolve_role_source()`,
  `resolved_skill_dirs()`, or any other spawn.py code.
- Establishing a repo-wide naming convention document for future
  migrations beyond what this pilot's own allowlist entry and skill
  names demonstrate.
- Deleting or modifying the existing generic (non-role-prefixed)
  skills already in `skill-repository`.

## How you'll know it worked

- The `skill-repository` PR's three new `SKILL.md` files diff empty
  against their `/tmp/udr-rulebook/playbook/*.md` sources.
- `docs/specs/role-source-allowlist.json` maps `upstream-defect-report`
  to exactly the three new skill names, and
  `_role_source_allowlist()`/`resolve_role_source()` resolve it without
  code changes (reused mechanism, per Constraints).
- The phase-2 record carries the 3-check evidence pasted verbatim per
  "What will be done" step 3, with the unrelated role's dry-run/argv
  output shown byte-identical pre/post.
