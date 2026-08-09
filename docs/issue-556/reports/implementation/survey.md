# issue-556 current-state survey

Scout skip: pure bugfix (contract v3 s19 / scout-directive skip condition). The
issue's reproduction is a specific crash + specific mis-ordering; no
product-facing or category-benchmarking decision is open. Only an internal
packaging-mechanics choice remains, covered directly in the proposal's
Rationale.

## Affected hooks

Exactly two hooks under `on-the-record/hooks/` build a `gates_dir` and import
a `gates/` module:

- `on-the-record/hooks/role-spec-reference-guard.sh` — bash line 30:
  `gates_dir="$(cd "$script_dir/../../gates" && pwd)"`; Python guard line 35-36
  does `sys.path.insert(...); import role_spec_shape` **before** the
  ownership test at line 58 (`role_spec_shape.record_path_role(n) is None`).
- `on-the-record/hooks/record-claim-guard.sh` — bash line 38: same
  `../../gates` resolution; Python guard line 43-44 imports `record_lint`
  **before** the ownership test at line 66 (`re.search(r"(^|/)docs/issue-...
  /reports/", n)`).

No other hook under `hooks/` builds a `gates_dir` or imports a `gates/`
module (`grep -l 'gates_dir=' hooks/*.sh` returns only these two).
`impact-guard.sh` imports a *target repo's* own `gates/` after locating that
repo's checkout — a different mechanism, out of scope here.

## Why `../../gates` breaks in the plugin cache

`.claude-plugin/marketplace.json` declares the on-the-record plugin's
`source` as `./on-the-record` — the plugin cache
(`~/.claude/plugins/cache/tokenmaxxxer/on-the-record/<hash>/`) is a copy of
that directory only. `gates/` lives at the monorepo root, a sibling of
`on-the-record/`, not inside it — so it is never copied into the cache.
`script_dir/../../gates` (`on-the-record/hooks/../../gates` in the dev
checkout) resolves correctly only because the dev checkout happens to nest
`on-the-record/` one level under the monorepo root that also holds `gates/`.
In the cache, `hooks/../../gates` walks above the cache dir entirely and
does not exist.

`gates_dir=$(cd ... && pwd)` failing does not itself stop the script
(`set -uo pipefail`, no `-e`): the assignment just yields `gates_dir=""`,
and execution reaches `RSRG_GATES_DIR="" python3 -c "$GUARD"`. Inside, the
ownership check runs *after* `sys.path.insert(0, "")` + `import
role_spec_shape`/`import record_lint`, which raises `ModuleNotFoundError`
before the ownership test ever runs — the process exits non-zero, and each
hook's `trap 'rc=$?; ...; exit 2'` remaps that to a deny, for every path,
owned or not.

## Module dependency shape (for packaging)

- `gates/role_spec_shape.py` — stdlib only (`json`, `sys`, `pathlib`).
- `gates/record_lint.py` — stdlib + `import gates` (resolves to the sibling
  `gates/gates.py` file, because the guard scripts put the *directory*
  `gates_dir` on `sys.path`, and `gates.py` sits directly inside it).
- `gates/gates.py` — stdlib only (`fnmatch`, `json`, `os`, `re`, `shlex`,
  `subprocess`, `pathlib`).

So the two hooks' actual runtime dependency is exactly three files:
`gates.py`, `record_lint.py`, `role_spec_shape.py` — no transitive imports
of any other `gates/*.py` module.

## Existing hook test conventions

`on-the-record/hooks/test_*.py` (e.g. `test_record_claim_guard.py`,
`test_contract_guard.py`) invoke the `.sh` hooks as subprocesses via
`subprocess.run`, feeding a JSON PreToolUse payload on stdin and asserting
on `returncode`/`stderr`. New tests for this issue follow the same
subprocess-invocation shape, setting `CLAUDE_PLUGIN_ROOT`/env and a
constructed cache-like directory tree per the issue's acceptance checks.

## Write set the fix will touch

- `on-the-record/hooks/role-spec-reference-guard.sh` — reorder ownership
  check before import; make `gates_dir` resolution multi-candidate/non-fatal.
- `on-the-record/hooks/record-claim-guard.sh` — same two changes.
- a new packaged-copy directory under `on-the-record/` holding `gates.py`,
  `record_lint.py`, `role_spec_shape.py` so the plugin cache carries them.
- a new committed test file under `on-the-record/hooks/` covering
  acceptance checks 1-3.
