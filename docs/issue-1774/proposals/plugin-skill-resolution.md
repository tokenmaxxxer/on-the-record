---
status: proposed
files:
  - spawn.py
  - test/test_spawn_skills_mount.py
---

## Request
`--skills <name>` today resolves only against the skill-repository
checkout root. #1774 asks that a name not found there fall back to the
consumer's own installed plugins' `skills/<name>/` directories (explicit
opt-in — only fires when `--skills` names something), with: repo wins
over plugin on a name collision; ambiguity handled as a hard error if
the same name appears in more than one *plugin*; a name found nowhere
still fails closed as today; a plugin skill dir carrying `hooks/`
refuses (guidance-only, mirroring the skill-repository rule); and
per-skill records carry that skill's own source (repo sha, or
`plugin@marketplace` + version) instead of one shared sha.

## Constraints
- No `--skills` flag: byte-identical argv/env, and `installed_plugins.json`
  is never read (requirement 4; mirrors `resolved_skill_dirs`'s existing
  `not names -> return []` early exit, survey.md "Requirement-to-code
  mapping" item 4).
- Skill-repository match still wins outright over any plugin match for
  the same name — no ambiguity error when the name is found in the repo,
  regardless of whether it also exists in an installed plugin.
- A name matching in the repo AND (only) an installed plugin is not an
  error under requirement 1's own wording ("skill-repository root...
  wins") — repo presence resolves it, full stop. The "both-sources hard
  error" applies to a name found nowhere in the repo but present in
  more than one distinct installed plugin (a real ambiguity — no
  documented order breaks that tie).
- Plugin skill dirs are read-only mounts (`--plugin-dir`, same mechanism
  as today) — never copied/mutated.
- Fail-closed timing preserved: all resolution/validation happens before
  `issue_workspace()` / `checkout_issue_branch()` (survey.md, existing
  `_spawn_one` ordering at spawn.py:7873).
- Record field additions are additive only — existing skill-repo-only
  compositions keep today's `skills`/`skills_sha` shape (issue empty-state
  requirement: "skill-repo-only compositions keep today's field shape").

## Rationale
Two designs were considered for where a plugin's skills live on disk:

1. **Chosen: read each installed plugin's own top-level `skills/<name>/`
   directory** (Claude Code's plugin-skills convention — same
   per-skill-is-a-directory shape the skill-repository root already uses).
2. **Rejected: treat every top-level directory in a plugin's `installPath`
   as a candidate skill**, the same enumeration `resolved_skill_dirs`
   already does for the skill-repository root. Rejected because a
   plugin's top level routinely holds non-skill directories (`hooks/`,
   `commands/`, `gates/`, `.claude-plugin/`) that are not opt-in
   guidance surfaces — treating them as resolvable "skill names" would
   make `--skills hooks` for any installed plugin silently mount that
   plugin's own hook-carrying directory as a "skill," which is exactly
   the guidance-only invariant requirement 2 exists to block. Scoping to
   a plugin's own `skills/` subdirectory keeps the candidate set to what
   the plugin author actually published as a skill, and keeps the
   `hooks/`-subdir refusal check meaningful (a plugin's `skills/<name>/`
   can still itself embed a `hooks/` folder, which requirement 2 covers).

## What will be done
1. `_installed_plugin_skill_dirs() -> dict[str, list[tuple[str, Path, dict]]]`
   (new): read `~/.claude/plugins/installed_plugins.json` (return `{}`
   if absent/unreadable — no plugins installed is not an error). For
   each installed plugin entry, look at `<installPath>/skills/`; if
   present, each subdirectory is a candidate, keyed by skill name ->
   list of `(plugin_qualifier, dir_path, version_info)` (a name can
   appear in more than one plugin — that is the within-plugin-space
   ambiguity requirement 1 asks to catch).
2. `resolved_skill_dirs(...)` extended with a new optional param carrying
   the plugin index (default: computed lazily only when a name is not
   in the repo — keeps the no-plugin-lookup path untouched when every
   name resolves against the repo, and keeps `installed_plugins.json`
   unread when `--skills` is unused at all, satisfying the byte-identical
   constraint). Per name: repo match wins outright; else check the
   plugin index — zero plugin matches keeps today's "unknown" fail-closed
   message (nowhere case); exactly one plugin match resolves to that
   plugin's dir; two or more distinct plugin matches is a new fail-closed
   error naming all matching plugin sources by name (both-sources
   ambiguity, requirement 1). Return value gains enough shape (a small
   per-name resolution record, not just bare `Path`s) to carry source
   identity forward to requirement 3's record fields, without changing
   the existing bare-list call sites that only need paths.
3. Guidance-only refusal (requirement 2): after resolving a name to a
   plugin skill dir, apply the same `hooks/`-subdirectory check
   `resolve_role_source` already runs for skill-repository dirs
   (spawn.py:5226-5231) to plugin-sourced dirs too, fail-closed before
   workspace/branch creation, same as today's skill-repository case.
4. Record fields (requirement 3): extend the roster entry and co-injected
   task string (spawn.py:7958-7967, 8079-8081, 8185-8188) so each mounted
   skill's row carries its own source — `{"name": ..., "source":
   "skill-repo", "sha": <7-char>}` or `{"name": ..., "source": "plugin",
   "plugin": "<name>@<marketplace>", "version": "<version-or-sha>"}` —
   additive alongside the existing flat `skills`/`skills_sha` keys (kept
   unchanged for skill-repo-only compositions per the empty-state
   requirement).
5. Tests in `test/test_spawn_skills_mount.py`: resolution-order cases
   (repo wins over a same-named plugin skill; plugin fallback when repo
   lacks the name; nowhere-found fail-closed unchanged), an ambiguity
   case (name present in two distinct installed plugins, no repo match,
   different from the repo case), a plugin-hooks-dir refusal case
   mirroring the existing `resolve_role_source` hooks test shape, and
   record-field cases asserting per-skill source identity for a
   plugin-sourced mount vs. today's shape for a repo-only mount. All
   tests build synthetic `installed_plugins.json` / plugin checkout
   fixtures under `tempfile.TemporaryDirectory()` (same pattern the file
   already uses for the skill-repository fixtures) — never touch the
   real `~/.claude/plugins/`.

## Out of scope
- Any change to how the skill-repository root itself is discovered or
  its names enumerated (unchanged, still wins).
- Marketplace-level plugin install/update flows (`plugin_dirs`,
  `sync_rulebooks`, etc.) — this only reads the already-installed state,
  read-only, exactly as requirement 1 specifies.
- Widening the `hooks/`-refusal rule's scope beyond the mounted skill dir
  itself (no scan of the whole plugin).
- Changing `resolve_role_source`'s (#1758) unrelated role->skill mapping
  axis.

## Accumulation
`_installed_plugin_skill_dirs()` reads `installed_plugins.json` once per
`spawn.py` invocation and builds an in-memory name->matches index; it is
not a per-plugin inline `subprocess`/`gh` call accumulating one call per
plugin, and it does not add a new repeated-file-with-one-line-per-entry
pattern (no new `roles/*.json`-style per-item file). If N more consumer
plugins get installed over time, the cost is O(installed plugins) dict
entries built from one JSON read — no additional code path, call site,
or file is added per plugin. The record-field shape (per-skill source
row) is likewise one list entry per *mounted* skill (bounded by
`--skills`'s own CSV, already user-bounded), not per installed plugin.

## How you'll know it worked
- `test/test_spawn_skills_mount.py` extended cases pass: resolution
  order (repo wins, plugin fallback), ambiguity error (two plugins, same
  name, no repo match), plugin-hooks-dir refusal, and record-fields
  cases for per-skill source identity — all in the same test file per
  the issue's own `check:` line.
- No-`--skills` byte-identical case (`SpawnCmdByteIdenticalNoFlagTest`)
  still passes unmodified.
- `python3 -m pytest test/test_spawn_skills_mount.py -q` run clean before
  the phase-2 PR closes the issue.
