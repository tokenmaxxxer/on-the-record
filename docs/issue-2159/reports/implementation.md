---
issue: 2159
role: implementation
upstream:
  - path: github.com/tokenmaxxxer/on-the-record issue #2159
    sha: b47a2abf3a4b28e54303b15bd4f660870fbef8da
code_under_review: aa856ce4
  - spawn.py
  - test/test_local_dependency_env.py
loop_state: landed
type: feat
breaking: false
verdict: pass
---

# issue-2159 — implementation record

## What was done

commit aa856ce4 (spawn.py, test/test_local_dependency_env.py):

```
$ git show --stat aa856ce4
commit aa856ce4
 spawn.py                          |  81 +++++++++++-
 test/test_local_dependency_env.py | 230 +++++++++++++++++++++++++++++++++
 2 files changed, 311 insertions(+), 1 deletion(-)
```

- `spawn.py` `local_dependency_env(origin, work) -> dict[str, str]` (and
  its `_find_local_dep_dirs` helper): read-only scan of `origin`'s root
  and one level of subdirectories for `node_modules`/`.venv`/`vendor`.
  `node_modules` -> `NODE_PATH`; `.venv` -> `VIRTUAL_ENV` plus
  `PYTHONPATH` only when a single `site-packages` dir resolves under it;
  `vendor/` is detected but never mapped to an env var (no single
  canonical lookup var across ecosystems). A candidate already present at
  the same relative path inside `work` is left alone. `origin == work`
  short-circuits to `{}`.
- `spawn.py` `_spawn_one()`: captures `origin_cwd = cwd` before
  `cwd = issue_workspace(cwd, issue, role)` overwrites it, then folds
  `local_dependency_env(origin_cwd, cwd)` into `extra_env` inside the
  existing `if issue is not None:` block that already adds the
  `GOCACHE`/`GOMODCACHE`/... toolchain-cache env vars.
- `test/test_local_dependency_env.py`: new test file.

```
$ python3 -m pytest test/test_local_dependency_env.py -q
17 passed in 0.84s
```

canonical: pytest run above (this turn).

## Why

The issue's own text already fixed the shape of the fix — env-var
pointer, never copy/symlink, `NODE_PATH` for `node_modules`,
`PYTHONPATH`/`VIRTUAL_ENV` for `.venv`, skip `vendor/`. What was left to
implementation:

- Scan depth: the issue says "root (or one level into common subdirs)".
  Implemented as one level into every immediate subdirectory rather than
  a hardcoded subdir allowlist — a monorepo's dependency-bearing
  subdirectory name (`frontend/`, `web/`, `apps/foo/`, ...) isn't
  predictable in advance.
- `.venv` "safety": resolved as — act only when exactly one `.venv`
  candidate exists under the scan (two or more means which interpreter is
  the real one can't be inferred, so both `VIRTUAL_ENV` and `PYTHONPATH`
  are skipped rather than guessed); add `PYTHONPATH` only when exactly
  one `lib/python*/site-packages` resolves under that single `.venv`.
- Already-present-in-`work` guard: not in the issue text, added because
  `issue_workspace()` reuses a persistent `work` directory across
  respawns of the same issue+role — a prior session may already have run
  its own install there, and pointing `NODE_PATH`/`VIRTUAL_ENV` at
  origin's copy instead in that case could skew versions between what a
  role session's own tooling expects and what it gets.

The detection+env logic is a small pure function
(`local_dependency_env(origin, work)`) rather than inlined at the call
site, so the ambiguity rules are unit-testable without a real clone per
case; the call-site change itself is a two-line fold into the existing
`extra_env` assembly `_spawn_one()` already builds.

Line-number note: the issue cites "pipeline.py:396" for the clone call.

```
$ sed -n '396p' pipeline.py
                     str(d)], "[core] clone", timeout=_sp.CLONE_TIMEOUT)
```

derived: `sed -n '396p' pipeline.py` (this turn) — that call clones
`tokenmaxxxer-core`'s own rulebook checkout inside `core_root()`, not a
target repo's isolated worktree. The clone that produces a spawned role's
isolated worktree from the invoking checkout is `issue_workspace()`'s
`git clone -q <src> <work>`:

```
$ grep -n 'git clone -q.*str(src), str(work)' spawn.py
1579:    c = _run_net(["git", "clone", "-q", str(src), str(work)], "작업 클론",
```

derived: `grep -n 'git clone -q.*str(src), str(work)' spawn.py` (this
turn) — `spawn.py` line 1579, called from `_spawn_one()`. That is where
this change is wired in.

This session's environment carries `CORE_BUILD_NOW=1`:

```
$ echo "CORE_BUILD_NOW=$CORE_BUILD_NOW"
CORE_BUILD_NOW=1
```

canonical: shell env read above (this turn) — per contract v3 s19a the
proposal round is skipped for this delivery, so no phase-1 proposal
document exists; the design reasoning above stands in its place.

## Upstream basis

GitHub issue #2159 is the sole upstream input (see `upstream:`
frontmatter). No phase-1 survey/proposal exists for this delivery
(build-now bypass, see "Why"). `code_under_review: aa856ce4` (files
listed in frontmatter) names the commit and files this record reviews;
this record itself lands in a later commit on the same branch.

## Open findings

None.

## Next steps

None — `loop_state: landed` is terminal for a `coding-record`.

## What did not work

- The first draft of the call-site-wiring source-pin tests in
  `test/test_local_dependency_env.py` searched for `_spawn_one()`'s body
  boundary using `\ndef _recut_absorbed_branch(` as the end marker (by
  analogy with `test_branch_role_field.py`'s pin on `issue_workspace()`,
  which does end there). `_spawn_one()` is the last top-level function in
  `spawn.py`, so that marker never occurs after it:

  ```
  $ python3 -m pytest test/test_local_dependency_env.py -q 2>&1 | tail -3
  FAILED test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
  FAILED test/test_local_dependency_env.py::CallSiteWiringTest::test_local_dependency_env_merged_into_extra_env
  2 failed, 15 passed in 0.90s
  ```

  canonical: pytest run above (this turn, before the marker fix). Fixed
  by ending the slice at `\nif __name__ == "__main__":` instead.

  ```
  $ python3 -m pytest test/test_local_dependency_env.py -q 2>&1 | tail -1
  17 passed in 0.84s
  ```

  canonical: pytest run above (this turn, after the marker fix).

## Verification (verify-at-landing)

```
$ python3 -m pytest test/test_local_dependency_env.py -q
17 passed in 0.84s

$ python3 -m pytest test/test_branch_role_field.py -q
18 passed in 1.01s

$ python3 -m pytest test/test_spawn_artifact_skill_pairing.py test/test_spawn_cross_family_skill_selection.py test/test_spawn_model_override.py test/test_spawn_role_skill_resolution.py test/test_spawn_skill_judge_haiku_timeout_overlap.py test/test_spawn_skills_mount.py -q
77 passed in 1.13s

$ git diff aa856ce4~1 aa856ce4 -- spawn.py | grep -nE "symlink|shutil\.copy|shutil\.move"
(no output)

$ python3 -c "import ast; ast.parse(open('spawn.py').read())"
(no output — parses)
```

canonical: pytest/grep/ast runs above (this turn).

Acceptance criteria from the issue, mapped to evidence (canonical: the
pytest/grep runs in this section and in "What was done" above, this
turn):
- fixture with `frontend/node_modules` only in origin -> `NODE_PATH`
  auto-set, `require.resolve` succeeds without manual `NODE_PATH`:
  `NodeModulesTest.test_one_level_subdir_node_modules_sets_node_path` and
  `NodeModulesTest.test_require_resolve_succeeds_via_node_path_alone`
  (live `node` subprocess probe).
- no file copy/symlink into the isolated clone: the `grep` above (no
  output) plus `NoFilesystemMutationTest` (asserts both `origin` and
  `work` directory trees are byte-identical before/after the call, and
  that the function body contains no
  `os.symlink`/`shutil.copy*`/`shutil.move`).
- no such directories -> byte-identical env:
  `NoLocalDepDirsTest.test_no_known_dirs_gives_empty_env` (asserts `{}`,
  so `extra_env.update({})` is a no-op).
- tests for the detection+env-wiring logic: all of
  `test/test_local_dependency_env.py` above, including two source-level
  pins on the `_spawn_one()` call-site wiring order and the `extra_env`
  merge.

## Doc placement

No `docs/specs/`, `docs/decisions/`, or `docs/reports/` entries were
warranted — no durable design decision beyond what is recorded above, and
no `docs/specs/*` file was touched (so no `spec_index.py --update`
regeneration applies).

## Skill check

skill-verdict: none of the mounted skills were invoked via the Skill tool
this session — the change is one pure function plus a two-line call-site
wire-in in one file, and the structural/pattern/perf/coupling decisions
the mounted skills gate on (splitting a class, introducing a GoF pattern,
an asymptotic-cost tradeoff, a multi-module architecture choice) are all
absent here; the issue itself had already fixed the shape of the fix.
other mounted skills: not triggered.
