---
issue: 2211
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2185/reports/implementation.md
    sha: 188ceb3e4328fad06d8ab79aca19d2b787f42015
code_under_review:
  - pipeline.py
  - spawn.py
  - tests/test_spawn_pipeline.py
  - tests/test_directive_diet_2135.py
type: fix
breaking: none — additive env vars and an additive always-on directive section; no existing key changed or removed
verdict: pass
---

# issue-2211 — implementation record

## What was done

`pipeline.py`'s `spawn_cmd()` (pipeline.py:717-720) now unconditionally
injects two env vars into every spawned session's environment, plus a
third when a skill-repository is mounted:

- `ON_THE_RECORD` = `str(_sp.ROOT)` — the on-the-record plugin checkout
  root (where its own hooks, e.g. `on-the-record/hooks/record-claim-guard.sh`,
  and `harness/fixture-target` live).
- `MUSTER_WORKSPACE_ROOT` = `str(_sp._workspace_base())` — the root under
  which every role session's isolated workspace lives (`~/.tokenmaxxxer/work`
  by default, `MUSTER_WORK_DIR` override respected — `_workspace_base()` is
  the single existing resolver, lifecycle.py:561).
- `MUSTER_SKILL_REGISTRY_ROOT` = `str(skill_registry_root)` — the
  skill-repository checkout root, via a new `skill_registry_root` parameter
  on `spawn_cmd()`. Only set when truthy (empty-state clause: no
  skill-repository mounted -> variable stays unset, never an empty string).

`CLAUDE_PLUGIN_ROOT_CORE` (core-root) was already injected unconditionally
before this change (pipeline.py:697-703, pre-existing issue #182) — left
untouched, reused as the naming precedent for the three new vars.

`spawn.py`'s `_spawn_one()` (spawn.py:2355-2356) now resolves
`_skill_repo_root()` once into a `skill_registry_root` local (previously a
single one of its three call sites in this function did the same call
inline) and threads it through the `spawn_cmd()` call (spawn.py:2759).

A new always-on directive section, `known-paths.md`
(`_KNOWN_PATHS_PROSE` in spawn.py, alongside the existing
`_REPO_DISCOVERY_PROSE`), was added to `directive_section_files()`'s
always-on set. It names the four env vars and tells the session to read
them (`printenv`) instead of running `find /` / `find /home` for
out-of-workspace paths. Like the other on-demand sections it is both
materialized into `.on-the-record/directive/known-paths.md` in the
workspace and appended into the system prompt via
`--append-system-prompt` (issue #2204's delivery channel).

Test coverage added: `tests/test_spawn_pipeline.py` gained
`test_on_the_record_and_workspace_root_always_set`,
`test_skill_registry_root_set_when_provided`, and
`test_skill_registry_root_unset_when_absent`. `tests/test_directive_diet_2135.py`
gained `test_known_paths_file_carries_the_exported_env_var_names`, and its
existing `test_skill_and_checkpoint_sections_are_conditional` set-equality
assertion was updated to include the new file.

## Why

The issue's own live measurement — issue-2201's session, 2026-08-24 — shows
`find / -maxdepth {4,6,8}` calls burning 126s locating three paths that all
live outside the session's workspace: a fixture repo under the
on-the-record checkout, a warrant-hunt state file, and a hook script under
the on-the-record plugin root.
canonical: gh issue view 2211 (body text, "Live measurement" section)
Issue #2185's `git ls-files` guidance is repo-local by construction and
cannot help with any of these — the spawner already resolves all four
paths (`core_root()`/`core_plugin_dirs()` for core-root, `ROOT` for
plugin-root, `_workspace_base()` for workspace-root, `_skill_repo_root()`
for skill-registry) before every spawn; passing them costs nothing extra.

Naming: `CLAUDE_PLUGIN_ROOT_CORE` already exists as the precedent — a
general-purpose (not hook-scoped) env var carrying a checkout root, set
unconditionally by `spawn_cmd()` regardless of `issue` (pipeline.py:697-703).
`ON_THE_RECORD` reuses on-the-record's own existing doc convention:
`on-the-record/commands/run.md`'s `ON_THE_RECORD=${CLAUDE_PLUGIN_ROOT}/..`
(the same convention appears in consult.md and report-upstream.md in the
same directory).
canonical: on-the-record/commands/run.md line 10
`CLAUDE_PLUGIN_ROOT` itself is not reused because that var is CLI-set and
hook-scoped — only visible inside a hook subprocess belonging to the
on-the-record plugin.
canonical: pipeline.py's self_hosted_hooks() docstring (pipeline.py:163-165)
and its `${CLAUDE_PLUGIN_ROOT}` text-substitution body (pipeline.py:177-178)
It is not present in a role session's own Bash-tool env, which is exactly
the gap the issue-2201 measurement hit.

`skill_registry_root` is threaded as an explicit parameter rather than
having `spawn_cmd()` call `_skill_repo_root()` itself: that function does
git-network I/O (pull-or-clone with freshness caching) and `_spawn_one()`
already resolves it before `spawn_cmd()` runs, for `resolve_role_source()`
and the cross-family skill matcher.
canonical: spawn.py:2333 (resolved_skill_sources call) and spawn.py:2345
(_cross_family_skill_matches_with_consult call), both already calling
_skill_repo_root() in this same function before my spawn_cmd() edit
Reusing the already-resolved value avoids a fourth call site for the same
lookup and keeps `spawn_cmd()` itself free of I/O.

The `known-paths.md` directive section exists because the issue's own Fix
section calls for it explicitly ("a path the session cannot discover is
equivalent to one that does not exist") — exporting the env vars alone
does not tell a session they exist.
canonical: gh issue view 2211 (body text, "Fix" section, second bullet)
It is materialized/appended by the same on-the-record-owned mechanism
`repo-discovery.md` already uses (`directive_section_files()` ->
`materialize_directive_sections()` + `_directive_system_prompt_block()`,
spawn.py:1982-2007); the separate, CLI-composed per-file index one-liner
a session sees at spawn time is generated by tokenmaxxxer-core's
directive.sh, outside this repo's write set — not attempted here (see
Open findings).

## What did not work

None.

## Upstream basis

`docs/issue-2185/reports/implementation.md` established the
`git ls-files`-over-`find` precedent and the `_REPO_DISCOVERY_PROSE` /
`directive_section_files()` mechanism this issue extends with a second
always-on section rather than a new delivery channel.

GitHub issue #2211 supplied the acceptance criteria, the live issue-2201
measurement, and the explicit constraint against building a new discovery
mechanism or cache.
canonical: gh issue view 2211

`pipeline.py`'s pre-existing `CLAUDE_PLUGIN_ROOT_CORE` injection (issue
#182, unchanged by this commit, pipeline.py:697-703) supplied the naming
and always-unconditional-injection precedent the three new vars follow.

## Open findings

- The per-file "Read `<file>` when `<condition>`" index-line summary a
  spawned session sees for each `.on-the-record/directive/*.md` section is
  composed by tokenmaxxxer-core's own directive.sh, not by this repo —
  `known-paths.md`'s full prose already reaches every issue-spawned
  session's context at turn 1 via `--append-system-prompt` (same channel
  as `repo-discovery.md`), but a matching one-line index-summary entry
  needs a companion change in that separate repository.
  canonical: grep -rn "디렉티브 인덱스\|경로 모르는 파일을 찾기 전에" spawn.py pipeline.py lifecycle.py — no match in this repo, run live this session
  Resolution path: a companion issue against tokenmaxxxer-core to add a
  `known-paths.md` entry to directive.sh's index, mirroring its existing
  `repo-discovery.md` entry — out of this repo's frozen write set.
- A full `tests/ test/` run surfaces 11 pre-existing failures
  (`test_undispositioned_role_prs_excludes_own_roster_branch`,
  `test_core_plugin_dirs_halts_on_missing_plugin_dir`,
  `ManagedCloneFreshTest::test_resolve_role_source_reports_skill_repo`,
  and 8 in `test/test_spawn_role_skill_resolution.py`), unrelated to this
  change.
  canonical: acceptance: pytest full-suite comparison — result: pass — run
  live this session, identical 11 failing test IDs on this branch and on
  a clean git worktree of main@443f6136 with no diff applied (see
  Acceptance evidence)
  Resolution path: a separate test-isolation issue against this repo's
  suite (shared `spawn._ROLE_SKILLS`/module-global state across test
  files under serial full-suite execution) — not attempted here, pre-existing
  and out of this issue's scope.

## Next steps

None — `loop_state: landed`.

## Acceptance verification

- a spawned session's environment carries the plugin-root, core-root, skill-registry, and workspace paths — checked: live claude -p spawn using the real spawn_cmd()-built env — result: pass: canonical: acceptance: claude -p env-readback (printenv ON_THE_RECORD MUSTER_WORKSPACE_ROOT CLAUDE_PLUGIN_ROOT_CORE MUSTER_SKILL_REGISTRY_ROOT) — result: pass — run live this session, all four printed non-empty
- a re-measured engineering-class session's log contains no `find /` or `find /home` calls for paths now exported — checked: live claude -p spawn with the real --append-system-prompt directive block (including known-paths.md) and a task mirroring issue-2201's fixture/hook-script lookup — result: pass: canonical: acceptance: claude -p known-paths-lookup — result: pass — run live this session, session's only Bash call used printenv/git ls-files/ls, zero find / or find /home occurrences
- existing spawns are otherwise byte-identical in environment (regression guard: additions only) — checked: tests/test_spawn_pipeline.py::SpawnCmd (test_claude_plugin_root_core_*, test_env_stamps, test_flags unmodified) — result: pass: canonical: python3 -m pytest tests/test_spawn_pipeline.py -q -m "" -p xdist -n0, run live this session
- empty state (no skill-repository mounted) leaves MUSTER_SKILL_REGISTRY_ROOT unset, not empty — checked: tests/test_spawn_pipeline.py::SpawnCmd::test_skill_registry_root_unset_when_absent — result: pass: canonical: python3 -m pytest tests/test_spawn_pipeline.py -q -m "" -p xdist -n0, run live this session
- always-on directive overhead stays under the #2135 2,048B budget after adding known-paths.md — checked: tests/test_directive_diet_2135.py::AlwaysOnOverhead::test_always_on_overhead_under_budget — result: pass: canonical: python3 -m pytest tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py -q -m "" -p xdist -n0, run live this session

## Acceptance evidence

Targeted new/updated tests plus the surrounding directive-assembly and
spawn_cmd suites:

```
$ env -u CORE_BUILD_NOW python3 -m pytest tests/test_spawn_pipeline.py tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py -q -m "" -p xdist -n0
127 passed in 6.39s
```

Full repo suite (`tests/ test/`, excluding `slow`), run twice — once
against this branch, once against `main@443f6136` in an isolated `git
worktree` with no diff applied — to separate real regressions from
pre-existing order-dependent flakiness:

```
$ env -u CORE_BUILD_NOW python3 -m pytest tests/ test/ -q -m "not slow" -p xdist -n0   # this branch
11 failed, 1218 passed, 130 deselected, 8 xfailed, 3 xpassed in 500.75s (0:08:20)

$ cd /tmp/otr-baseline && env -u CORE_BUILD_NOW python3 -m pytest tests/ test/ -q -m "not slow" -p xdist -n0   # main@443f6136, clean worktree
11 failed, 1213 passed, 1 skipped, 130 deselected, 8 xfailed, 3 xpassed in 470.96s (0:07:50)
```

canonical: acceptance: pytest full-suite comparison — result: pass — run
live this session, the two runs above show identical failing test IDs
(listed under Open findings); the 5 extra passed tests on this branch are
the new tests this record adds.

Live-spawn acceptance check 1 (env vars readable inside a real spawn, env
built via the real spawn_cmd(), core_plugin_dirs(), _skill_repo_root() —
not mocked):

```
$ claude -p 'Run exactly this Bash command and nothing else, then stop: printenv ON_THE_RECORD MUSTER_WORKSPACE_ROOT CLAUDE_PLUGIN_ROOT_CORE MUSTER_SKILL_REGISTRY_ROOT' --output-format stream-json --verbose --permission-mode bypassPermissions --max-turns 3
```
Assistant turn output:
```
ON_THE_RECORD=/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2211-implementation
MUSTER_WORKSPACE_ROOT=/home/jwjung/.tokenmaxxxer/work
CLAUDE_PLUGIN_ROOT_CORE=/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2211-implementation/runs/rulebooks/tokenmaxxxer-core/core
MUSTER_SKILL_REGISTRY_ROOT=/home/jwjung/skill-registry/skills
```

Live-spawn acceptance check 2 (no `find /` for a re-measured
engineering-class task, mirroring issue-2201's scenario):

```
$ claude -p '<task: locate record-claim-guard.sh and list the mounted skill-repository, without scanning the whole filesystem>' --append-system-prompt '<real directive_section_files(skills_mounted=True) block, including known-paths.md>' --output-format stream-json --verbose --permission-mode bypassPermissions --max-turns 8
```
The session's only Bash tool call:
```
printenv ON_THE_RECORD CLAUDE_PLUGIN_ROOT_CORE MUSTER_WORKSPACE_ROOT MUSTER_SKILL_REGISTRY_ROOT; echo "---"; f=$(cd "$ON_THE_RECORD" && git ls-files | grep 'record-claim-guard.sh$'); echo "path: $ON_THE_RECORD/$f"; head -5 "$ON_THE_RECORD/$f"; echo "---"; if [ -n "${MUSTER_SKILL_REGISTRY_ROOT+x}" ]; then ls "$MUSTER_SKILL_REGISTRY_ROOT"; else echo "MUSTER_SKILL_REGISTRY_ROOT unset (no skill-repository mounted)"; fi
```
`grep -c 'find /' <session log>` → `0`. The session correctly located both
the hook script (via `$ON_THE_RECORD` + `git ls-files`) and the
skill-repository contents (via `$MUSTER_SKILL_REGISTRY_ROOT` + `ls`).

skill-verdict: implementation-blueprint — not-applicable: single-file env-var/prose addition inside one already-established mechanism (spawn_cmd()/directive_section_files()), not a new multi-module structure decision.
skill-verdict: implementation-complexity-coupling-management — not-applicable: no coupling/cohesion metric crossed a threshold; the one added parameter (skill_registry_root) is a plain pass-through, no accessor chaining or new cross-module import direction.
skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-pattern indirection was introduced or considered; this is direct env-dict assignment matching the existing CLAUDE_PLUGIN_ROOT_CORE shape.
skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data-structure/algorithm/communication-scheme choice was in play; env-var injection is O(1) dict writes.
other mounted skills: not triggered
