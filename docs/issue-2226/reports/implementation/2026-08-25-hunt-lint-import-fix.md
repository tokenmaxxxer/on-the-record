---
issue: 2226
transition: build-now (no proposal — session ran under CORE_BUILD_NOW=1, contract v3 s19a)
---

# Hunt record — lint-import-fix

Resolution: fixed in the same commit as the diff this stance was seeded
from, before landing — see docs/issue-2226/reports/implementation.md,
"What did not work". The `sys.modules["gates"]` eviction approach was
replaced with an `importlib`-by-path load under a private cache key that
never touches `sys.modules["gates"]`.

## before-landing — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the `sys.modules["gates"]` cache-eviction fix repairs the namespace-package collision for the *current* module's own `import gates`, but leaves `sys.modules["gates"]` bound to the flat `gates/gates.py` module (no `__path__`) for the rest of the process, so any later `-m gates.<other>` (or dotted `import gates.<x>`) resolution attempted in the same interpreter fails outright with ImportError — a harder failure than the bug being fixed, and one the guard code never gets a chance to run for, because Python's own module-spec resolution for `gates.<other>` happens before the target file's top-level guard code executes.
Kind: composition
Seed: diff to gates/ci.py, gates/claims.py, gates/record_lint.py, gates/risk_report.py (issue #2226 sys.modules["gates"] namespace-package eviction fix)
cap_seconds: 180
tier: size:gates
diff_stat_lines: 44
started_at: 2026-08-24T23:15:00Z
ended_at: 2026-08-24T23:19:30Z

Note on record path: the dispatcher-supplied path
`docs/issue-2226/reports/hunt-record-lint-import-fix.md` was rejected by this
repo's own `board-gate` hook (`belongs to another role. implementation writes
only implementation.md, implementation/** ...`), so per the standalone-fallback
rule (role-scoped session, `CLAUDE_ROLE=implementation`, branch
`issue-2226/implementation`) this record was written to
`docs/issue-2226/reports/implementation/<date>-hunt-<slug>.md` instead.

### Reproduce
```
python3 -c "
import runpy, sys
sys.argv = ['gates.ci', '--help']
try:
    runpy.run_module('gates.ci', run_name='__main__', alter_sys=True)
except SystemExit:
    pass
sys.argv = ['gates.record_lint', '--help']
runpy.run_module('gates.record_lint', run_name='__main__', alter_sys=True)
"
```
(`runpy.run_module` with `run_name='__main__'` is the same mechanism CPython's
own `-m` flag uses internally to resolve and execute a dotted module target,
so this is not a synthetic alternate code path — it is `-m`'s own resolution
machinery invoked twice in one interpreter.)

### Observed
```
  File "/usr/lib/python3.10/runpy.py", line 138, in _get_module_details
    raise error(msg.format(mod_name, type(ex).__name__, ex)) from ex
ImportError: Error while finding module specification for 'gates.record_lint' (ModuleNotFoundError: __path__ attribute not found on 'gates' while trying to find 'gates.record_lint')
```
After the first `gates.ci` run, `sys.modules["gates"]` is
`<module 'gates' from '.../gates/gates.py'>` — a plain script module with no
`__path__`. The second `-m`-style resolution for `gates.record_lint` needs
`gates.__path__` to locate the submodule and dies before `gates/record_lint.py`'s
own top-level guard (the very code this diff added) ever runs, since that
guard only fires *after* the module is already found and loaded.

### Expected
A fix scoped to "make `import gates` inside this one file resolve correctly"
should not degrade `sys.modules["gates"]` from "usable-but-wrong-target" (the
original namespace-package collision) to "unusable for any subsequent dotted
resolution in the same process" for every other consumer that runs afterward
in the same interpreter. The eviction should restore/preserve enough
package-shaped state (e.g. re-establish `__path__` on the substituted module,
or restore the original namespace-package object afterward) so a second
`-m gates.<other>` in the same process does not hard-crash.
