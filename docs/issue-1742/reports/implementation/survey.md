# Current-state survey — issue #1742

## Write set (expected)
- `spawn.py`
- test/test_spawn_skills_mount.py (new file this proposal creates — see Acceptance in issue #1742)

## What exists today

### Rulebook mount path (the pattern to reuse)
- `plugin_dirs(role, spec)` (spawn.py:343) resolves a role's rulebook
  checkout into a list of local `--plugin-dir` paths, reading
  `marketplace.json`'s `plugins[]` and skipping `-agent-env` bundles.
  canonical: spawn.py:343-366 (read directly)
- `rulebook_source(spec)` (spawn.py:212): local checkout wins —
  `spec["path"]` if `marketplace.json` exists there, else falls back to
  `spec["repo"]` (github clone). canonical: spawn.py:212-223
- `spawn_cmd(settings_path, role, unattended, core_plugins, plugins,
  model)` (spawn.py:5385) assembles argv (`--plugin-dir` per rulebook
  plugin, then per core plugin, then `--model`) and env
  (`CLAUDE_ROLE`, `TOKENMAXXXER_SPAWNED`, `GH_TOKEN`/
  `GIT_TERMINAL_PROMPT`, `TOKENMAXXXER_UNATTENDED`,
  `CLAUDE_PLUGIN_ROOT_CORE`), returning `(cmd, env)` with no side
  effects. canonical: spawn.py:5385-5455
- `core_plugin_dirs()` (spawn.py:5208) is the analogous "core" mount;
  every entry is mandatory (no silent skip), unlike `plugin_dirs()`
  which tolerates a missing sub-plugin dir with a stderr warning.
  canonical: spawn.py:5208-5217 (docstring), spawn.py:343-366

### CLI-override precedence pattern (issue #1736)
- `resolved_role_model(cli_model=None)` (spawn.py:5367): precedence is
  `cli_model` (stripped, if non-empty) > `MUSTER_ROLE_MODEL` env >
  config file > built-in default. The optional trailing parameter
  defaulting to `None` is what keeps `spawn_cmd()` byte-identical when
  the new argument is omitted — same shape issue #1742 needs for
  `--skills`. canonical: spawn.py:5367-5382

### Sibling-clone default pattern (for `MUSTER_SKILL_REPO` default)
- `core_root()` / `_core_candidates()` (spawn.py:5117-5146): env var
  override (`TOKENMAXXXER_CORE`) first, then
  `$TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core` (a sibling-directory
  convention), then an on-the-record-owned managed clone under
  `runs/rulebooks/`. canonical: spawn.py:5117-5146
- `rulebook_checkout()` (spawn.py:279) uses the same managed-clone-
  under-`runs/` fallback for role rulebooks. Skill repo mounting for
  #1742 can reuse the same sibling-first, managed-clone-fallback shape
  via a new `MUSTER_SKILL_REPO` env var, scoped small (existence-check
  of a local checkout only — a managed-clone bootstrap of
  skill-repository is not asked for by the issue's additive framing;
  requirement 1 says "local skill-repository checkout", not "clone one
  if absent"). canonical: spawn.py:279-330

### CLI argument wiring (`main()`)
- `main()` (spawn.py:6797-6871) builds one `argparse.ArgumentParser`
  shared across all subcommands (`spawn`, `watch`, `consult`, `judge`,
  ...); flags are added unconditionally with `ap.add_argument(...)`.
  Adding `--skills` here follows the existing style (a bare
  `ap.add_argument("--skills", help=...)`, defaulting to `None`).
  canonical: spawn.py:6797-6871

### Where argv/env get assembled into the actual spawn (spawn_cmd call site)
- spawn.py:7811 `plugin_dirs(role, spec)` → rulebook plugins.
- spawn.py:7818 `core_plugin_dirs()` → core plugins.
- spawn.py:7831-7832 `spawn_cmd(settings, role, unattended,
  core_plugins, plugins, model)` → `(cmd, extra_env)`.
- No `--skills`-shaped parameter exists anywhere in this chain.
  derived: `grep -n "skills" spawn.py` (no matches)

### Roster / co-injected directive (record fields, req. 3)
- `roster_register(roster_key, {...})` (spawn.py:7893, second call site
  ~7979) is the roster entry — a plain dict written to
  `runs/roster.json` via `_roster_save()`. `_format_roster_row()`
  (spawn.py:2312) reads roster entry fields defensively with `.get()`,
  so adding `skills` / `skills_sha` keys to the dict literal at the
  registration call site is additive. canonical: spawn.py:7893-7901, spawn.py:2312
- The "co-injected directive" is the `task` string built at spawn.py:7799
  (the multi-paragraph Korean text prepended to the user's task and
  piped to the session via stdin), already carrying issue/branch/
  requirement context (`req_line`, `goal_pin`). canonical: spawn.py:7799-7809

### Tests
- `test/` holds several `test_spawn_*.py` files that call `spawn_cmd()`/
  `resolved_role_model()` directly and assert on the returned argv/env
  tuples, with no subprocess spawn required for unit coverage — the
  shape the new test file will follow. derived: `ls test/ | grep test_spawn`
- No pre-change fixture for "assembled argv+env" currently exists on
  disk. derived: `find test -iname '*argv*fixture*' -o -iname '*spawn*fixture*'` (no output)
  The byte-identical no-flag case will build its own inline before/
  after comparison (call `spawn_cmd()`/`main()`'s argv assembly with
  the new code path active but `--skills` omitted, and assert equality
  with a captured pre-change baseline recorded in the test itself),
  not read a stored file, since none is on disk.

### Design research note in the issue
The issue body's design-research line states the mechanism reuses two
in-repo proven patterns: #1736's CLI-override precedence
(`resolved_role_model`) and the rulebook `--plugin-dir` local-mount
pattern. canonical: gh issue view 1742 (design-research line in body)
This matches what the survey above found directly in spawn.py (see the
"CLI-override precedence pattern" and "Rulebook mount path" sections
above), so it freezes the mechanism as an issue-body requirement, not a
fresh design choice made here.

## Skip conditions checked
Neither blanket scout skip condition (pure bugfix / spec leaves no
design decision open) applies outright, but the issue's own text
already freezes the mount mechanism (design-research line, verbatim in
the issue body) to two named in-repo patterns, leaving the implementer
exactly one open choice per the issue text: workspace mount location
(`.claude/skills/` vs "a minimal plugin dir"). That is a narrow,
single-axis decision with an in-repo precedent on each side (the
rulebook plugin-dir mount vs. a bare directory), and the acceptance
tests constrain only observable behavior (argv/env/roster fields), not
the mount directory's name — external skill-mount conventions would
not change which of those two in-repo shapes gets picked. Scouting is
skipped on this narrow point; reason recorded here per the survey-order
directive's mandatory skip-record requirement.
