scout-skip: mechanical — spec (issue #1758, operator-frozen framing) leaves
no open design decision: it names the exact config file path, the exact
mapping shape (legacy role -> skill list), the exact mount mechanism to
reuse (--skills's existing resolved_skill_dirs()/--plugin-dir path,
issue #1742), and the exact record-field extension point (skills/
skills_sha, issue #1742). This is a mechanical extension of an already-
landed pattern, not a new architecture choice — scouting the field would
find nothing that changes the shape.

# Current-state survey: spawn.py role/skill resolution (issue #1758)

derived: grep -n "def resolved_skill_dirs\|def skill_repo_sha\|def _skill_repo_root\|def plugin_dirs\|def spawn_cmd\|def _spawn_one\|def checkout_version" spawn.py
```
343:def plugin_dirs(role: str, spec: dict) -> list[Path]:
327:def checkout_version(role: str, spec: dict) -> str:
5147:def _skill_repo_root() -> Path | None:
5166:def resolved_skill_dirs(skills_csv: str | None, repo_root: Path | None) -> list[Path]:
5187:def skill_repo_sha(repo_root: Path) -> str:
5451:def spawn_cmd(...)
7803:def _spawn_one(...)
```

## What #1742 already built (reused, not re-invented)

- _skill_repo_root() (spawn.py:5147) resolves the skill-repository
  checkout via MUSTER_SKILL_REPO env or the sibling-clone convention
  $TOKENMAXXXER_RULEBOOKS/skill-repository; None if neither exists.
- resolved_skill_dirs(skills_csv, repo_root) (spawn.py:5166) turns a
  CSV of skill names into <repo_root>/<name> paths. Empty input -> []
  (no mount, byte-identical). Any unknown name -> sys.exit(...) before
  any workspace/branch mutation (already fail-closed — issue #1758
  requirement 2 gets this for free by reusing the function).
- skill_repo_sha(repo_root) (spawn.py:5187) — short git HEAD sha of the
  skill-repository checkout, "?" on git failure.
- spawn_cmd() (spawn.py:5451) appends each skill dir as a bare
  --plugin-dir <dir> argv entry, after rulebook and core plugin dirs,
  and sets env["MUSTER_SKILLS"]/env["MUSTER_SKILL_REPO_SHA"] only when
  skill_dirs is truthy — falsy input leaves argv/env byte-identical to
  pre-#1742.
  canonical: read test/test_spawn_skills_mount.py in full (227 lines,
  read via the Read tool) — class SpawnCmdByteIdenticalNoFlagTest
  asserts this byte-identity, class RecordFieldsCarrySkillsAndShaTest
  asserts the roster/task-string field behavior described below.
- _spawn_one() (spawn.py:7803) resolves --skills into skill_dirs at
  spawn.py:7817, before issue_workspace()/checkout_issue_branch() are
  called.
  derived: grep -n "skill_dirs = resolved_skill_dirs\|cwd = issue_workspace\|br = checkout_issue_branch" spawn.py
  ```
  7817:    skill_dirs = resolved_skill_dirs(skills, _skill_repo_root())
  7850:            cwd = issue_workspace(cwd, issue, role)
  7856:            br = checkout_issue_branch(cwd, issue, role)
  ```
  This ordering is what makes the existing fail-closed refusal land
  before any workspace/branch mutation. Roster entries (_early_roster_entry,
  spawn.py:7987; the later full entry, spawn.py:8077) and the co-injected
  task string (spawn.py:7898) both add skills/skills_sha fields/text only
  when skill_dirs is non-empty — omitted key, not empty value, when
  unused.

## What issue #1758 adds on top

plugin_dirs(role, spec) (spawn.py:343) always resolves and mounts the
role's rulebook checkout (rulebook_checkout() -> checkout_version(),
spawn.py:327, which triggers a real git clone/pull). This is the piece
#1758's transitional mapping needs to bypass for a mapped role: the
mapping is a per-role, config-driven substitute for the rulebook mount,
not an additional mount alongside it. There is currently no config file
read anywhere under docs/specs/ for a role->skill mapping and no code
path that skips plugin_dirs() for any role.
derived: find docs/specs -iname "*role-source*"; grep -n "plugin_dirs(role, spec)" spawn.py
```
(no output from find — file absent)
7904:        plugins = plugin_dirs(role, spec)
```

_spawn_one()'s existing print line (spawn.py:7918) unconditionally
calls checkout_version(role, spec) for its human-readable log line —
this call alone triggers rulebook_checkout()'s clone/pull. A mapped
role must not pay this cost either, since the whole point of the mapping
is "core-only enforcement, rulebook mount retired for this role" — an
unconditional checkout_version() call would silently keep fetching a
rulebook the mapping was supposed to make irrelevant.

## Record-field precedent (issue #1742)

skills/skills_sha are added to the roster dict conditionally (present
only when used) — canonical: read test/test_spawn_skills_mount.py in
full, class RecordFieldsCarrySkillsAndShaTest. Issue #1758's acceptance
3 asks for the opposite shape for the new resolution-source fields:
"fields reflect rulebook source for unmapped roles, unchanged shape" —
i.e. the resolution-source fields should be present for every role
(mapped or not) so a reader of the roster can always tell which source
resolved a given role, rather than having to infer "absent field ==
rulebook" the way skills/skills_sha do today.

## Fail-closed on skill-side hooks (frozen framing, second correction)

The issue's second operator correction is explicit: skill-repository is
guidance-only, hooks never attach there. resolved_skill_dirs() mounts
whatever directory a skill name resolves to via bare --plugin-dir (same
code path --skills already uses) — if a resolved skill directory
happened to contain a hooks/ subdirectory, Claude CLI would fire those
hooks in headless mode.
canonical: spawn.py:5475-5477 (comment above the --plugin-dir loop in
spawn_cmd(), states directory-mounted plugin hooks fire headless,
measured 2026-07-27 on CLI 2.1.220).
Nothing in the current codebase checks for or refuses this. Acceptance
1's "no skill-side hook dirs for mapped roles" mount-layout assertion
needs a concrete mechanism, not just a convention, to be checkable and
to give requirement 2's fail-closed principle real teeth here.

## Write set

- spawn.py — add: _role_source_allowlist(root) (reads
  docs/specs/role-source-allowlist.json, absent -> {});
  resolve_role_source(role, root, repo_root) (maps a role to either
  {"source": "rulebook", ...} or {"source": "skill-repo", "skill_dirs":
  [...], "skills": [...], "skill_sha": ...}, fail-closed via the reused
  resolved_skill_dirs() on a missing skill, and a new explicit
  fail-closed refusal when a resolved skill dir contains hooks/); wire
  the result into _spawn_one() to skip plugin_dirs()/checkout_version()
  for a mapped role, append the mapped skill dirs to the mount list, and
  add resolution_source/resolution_skills/resolution_skill_sha/
  resolution_rulebook_sha fields to the roster entries.
- test/test_spawn_role_skill_resolution.py (new file, does not exist yet
  — this is the write set target, not a current-state reference) — new
  test file per the issue's three named check groups (mount-layout incl.
  byte-identical diff, refusal cases, record-fields case).

## Alternatives considered (for the proposal's Rationale)

1. Mount mapped skills additively alongside the rulebook (never skip
   plugin_dirs()), relying only on convention to keep hooks out.
   Rejected: contradicts requirement 2 ("ENFORCEMENT comes from core
   hooks alone... rulebook hooks are no longer mounted for mapped
   roles") — the rulebook mount itself is the thing requirement 2 says
   must stop for a mapped role, not something to keep alongside skills.
2. New standalone config module instead of an inline spawn.py function.
   Rejected: _skill_repo_root()/resolved_skill_dirs()/skill_repo_sha()
   already live inline in spawn.py for the same kind of lookup (#1742);
   a new module would split one resolution concern across two files for
   no functional gain and diverge from the established pattern this
   issue explicitly extends.
