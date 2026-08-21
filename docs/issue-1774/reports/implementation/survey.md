---
name: issue-1774-survey
---

# Current-state survey — issue #1774

## Scope confirmed
`spawn.py` (skill resolution/mount) + `test/test_spawn_skills_mount.py`
(existing coverage, per issue's own `scope:` line).

## Skip-condition check (scout-directive)
This is neither a pure bugfix nor a spec-closed change — the issue leaves
one real design decision open: *how* a consumer's "installed plugins'
skill dirs" are discovered on disk (what layout counts as a plugin
carrying a skill). Scouting in the product/best-in-class sense does not
apply (no external product surface) — this is an internal resolution
mechanism extending an existing internal convention (#1742/#1758). The
field surveyed below is this repo's own prior art for plugin/skill
layout, covered as scout's non-product-role branch, rather than an
external web sweep.

## Existing `--skills` resolution path
canonical: read spawn.py:5147-5234 directly (current working tree)

- `_skill_repo_root()` (spawn.py:5147): resolves `MUSTER_SKILL_REPO` env
  or `$TOKENMAXXXER_RULEBOOKS/skill-repository` sibling checkout. No
  plugin-install fallback today.

- `resolved_skill_dirs(skills_csv, repo_root)` (spawn.py:5166-5184).
  canonical: spawn.py:5172-5184
  Splits CSV, lists `repo_root`'s subdirectories as the available names,
  fails closed (`sys.exit`) on any unknown name or missing `repo_root`,
  all before workspace/branch creation. Returns `[repo_root / name, ...]`.

- `skill_repo_sha(repo_root)` (spawn.py:5187): `git rev-parse --short=7
  HEAD` in `repo_root`, `"?"` on failure.

- `resolve_role_source(role, root, repo_root)` (spawn.py:5206-5234) — the
  #1758 allowlist-driven mapping (unrelated axis — role name -> skill
  names).
  canonical: spawn.py:5220-5231
  Reuses `resolved_skill_dirs`, and separately fails closed if any
  resolved dir carries a `hooks/` subdirectory ("skill-repository is
  guidance-only" invariant). This is the guidance-only refusal pattern
  requirement 2 in the issue asks to mirror for plugin-sourced dirs.

- `spawn_cmd(...)` (spawn.py:5511 on): takes `skill_dirs: list | None`
  and `skill_repo_sha_value: str | None`, appends each dir as
  `--plugin-dir <path>` after core/rulebook plugin dirs (spawn.py:5540),
  and when `skill_dirs` is truthy sets `env["MUSTER_SKILLS"]`
  (comma-joined dir *names*) and `env["MUSTER_SKILL_REPO_SHA"]`
  (spawn.py:5570-5572). Falsy `skill_dirs` -> neither key exists, argv
  unchanged — the byte-identical-when-unused guarantee requirement 4
  must keep holding.

- `_spawn_one(...)` (spawn.py:7863 on): validates `--skills` via
  `resolved_skill_dirs` at spawn.py:7873 (before `issue_workspace()` /
  `checkout_issue_branch()`), computes `skill_sha`.
  canonical: spawn.py:7987-7990
  Merges `skill_dirs` with `role_source["skill_dirs"]` additively (dedup
  by identity), and feeds the merged set into `spawn_cmd`.
  canonical: spawn.py:8079-8081, spawn.py:8185-8188, spawn.py:7958-7967
  Roster entry and the co-injected task string both gate on `if
  skill_dirs:` / `if role_source["source"] == "skill-repo"` — fields/
  text appear only when used.

## Installed-plugin discovery already in `spawn.py`
canonical: read spawn.py:647-842 directly (current working tree)

- `~/.claude/plugins/installed_plugins.json` (read by `_installed_sha`,
  spawn.py:656, and directly at spawn.py:780, spawn.py:831) is the
  canonical local plugin install state —
  `{"plugins": {"<name>@<marketplace>": [{"scope", "installPath",
  "version", "gitCommitSha", ...}]}}`.
  canonical: `cat ~/.claude/plugins/installed_plugins.json` (run this
  session)
  Entries carry `installPath` pointing at
  `~/.claude/plugins/cache/<marketplace>/<plugin>/<version-or-sha>/`.
  This is the "local plugin install state, read-only" the issue names —
  no other install-state source exists in `spawn.py`.

- Each installed plugin's `installPath` is a normal plugin checkout root
  (`.claude-plugin/plugin.json`, and whichever of `hooks/`, `commands/`,
  `gates/`, `skills/`, ... it ships).
  canonical: `find ~/.claude/plugins/cache/tokenmaxxxer/on-the-record/55850e622b10
  -maxdepth 2` (run this session)
  This machine's one installed plugin (`on-the-record@tokenmaxxxer`) has
  no `skills/` subdirectory (it is a rulebook plugin, not a
  skill-carrying one), so there is no on-disk example here of a plugin
  that does carry skills. The layout this issue asks spawn.py to honor is
  Claude Code's own plugin-skills convention: a plugin may ship a
  top-level `skills/<name>/` directory (each with its own `SKILL.md`),
  the same per-skill-is-a-directory shape the skill-repository root
  already uses for `resolved_skill_dirs`. No spawn.py code currently
  reads a plugin's `skills/` subdirectory — this is new.

## Requirement-to-code mapping
1. Resolution order (repo wins, plugin fallback, both-sources error,
   nowhere fail-closed) — extends `resolved_skill_dirs`; needs per-name
   resolution split into repo-hit vs plugin-hit sets before the existing
   "unknown" fail-closed check, so a both-sources hit is distinguished
   from a nowhere-found miss.
2. Guidance-only refusal on plugin skill dirs with a `hooks/`
   subdirectory.
   canonical: spawn.py:5226-5231
   Same shape as `resolve_role_source`'s existing `hooked` check, applied
   to plugin-sourced dirs too.
3. Per-skill source identity in records.
   canonical: spawn.py:7958-7967, spawn.py:8079-8081, spawn.py:8185-8188
   Today's records carry one flat `skills`/`skills_sha` pair assuming a
   single source (skill-repo). Needs per-skill provenance (repo sha, or
   `plugin@marketplace` + version/sha) rather than one shared sha,
   extending #1742/#1758's field shape additively.
4. Byte-identical default — no `--skills` flag must still short-circuit
   before touching `installed_plugins.json` at all.
   canonical: spawn.py:5172-5174
   Mirrors today's `not names -> return []` early exit.

## Existing test coverage
canonical: read test/test_spawn_skills_mount.py directly (current
working tree)

Covers: argv/env byte-identity with no flag, plugin-dir ordering +
env-field values, name->dir resolution + unknown-name fail-closed (before
workspace/branch touch), roster/task-string field gating. No coverage yet
for: plugin-sourced resolution, both-sources ambiguity, plugin
skill-dir hooks refusal, or per-skill source-identity record fields —
exactly the gaps the issue's Acceptance section names.
