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

## before-landing — stance: assume the gate/fix just touched is bypassable or has a related composition bug — find it

Verdict: FINDING — `roles_due.py`'s `_gates.BASE = base` mutates the process-wide shared `gates.py` singleton (`sys.modules["_on_the_record_gates_sibling_impl"]`), so calling `roles_due.roles_due(root, base=X)` silently changes the default diff base every other gate module (`skip_eligibility.py`, `risk_report.py`, ...) reads via `gates.BASE`/`_gates.BASE` for the rest of the process, with no restore.
Kind: composition
Seed: git diff HEAD -- gates/ui_evidence_gate.py gates/roles_due.py gates/skip_eligibility.py (issue-2226, 3-site sibling-import-collision fix, same shape as 71bfa6de)
cap_seconds: n/a (no explicit cap given by dispatcher for this dispatch)
tier: default
diff_stat_lines: 3 files changed (roles_due.py +15/-1, skip_eligibility.py +16/-1, ui_evidence_gate.py +17/-1)
started_at: 2026-08-25T00:00:00Z
ended_at: 2026-08-25T00:40:00Z

Note on novelty: verified with git-stash that the identical leak (same shared module object, same unguarded write) was already reachable pre-fix whenever both files were imported without `-m` (both bound to `sys.modules["gates"]`) — so the *sharing* is not new. What the fix changes is only which key the shared object lives under; it does not add a guard, so the fix is a place this composition bug could have been closed (e.g. scoping the mutation, or not sharing mutable globals across gate modules) and wasn't. No caller in the current tree passes a non-default `base` to `roles_due.roles_due()` (spawn.py:1285 always calls it with no `base`; both test files only ever pass `base="origin/main"`, which equals the default), so it is currently dormant/invisible rather than actively wrong today — but it is a live, reproducible landmine directly involving the touched code (`roles_due.py:204`) and the shared singleton the three new fixes were just wired into.

### Reproduce
```
cd /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2226-implementation
python3 - <<'PYEOF'
import runpy
rd_ns = runpy.run_module('gates.roles_due', run_name='not_main', alter_sys=True)
se_ns = runpy.run_module('gates.skip_eligibility', run_name='not_main', alter_sys=True)
print("shared singleton object?", rd_ns['_gates'] is se_ns['gates'])
print("skip_eligibility default BASE before:", se_ns['gates'].BASE)
rd_ns['roles_due'](__import__('pathlib').Path('.'), base='refs/some-other-ref')
print("skip_eligibility default BASE after roles_due(base=...):", se_ns['gates'].BASE)
PYEOF
```

### Observed
```
shared singleton object? True
skip_eligibility default BASE before: origin/main
skip_eligibility default BASE after roles_due(base=...): refs/some-other-ref
```
`skip_eligibility.classify_for_subject()`'s `base = base or gates.BASE` (gates/skip_eligibility.py:153) and `risk_report.py`'s `gates.BASE` (gates/risk_report.py:248) would now silently diff against `refs/some-other-ref` instead of `origin/main` for any call in the same process that omits an explicit `base`, with nothing signalling the change.

### Expected
`roles_due()`'s temporary override of the comparison base should not be observable by unrelated gate modules that happen to share the same cached `gates.py` singleton — either scope the override (pass `base` through instead of mutating global state, or save/restore `_gates.BASE` around the call), or stop treating `BASE` as a shared mutable global once multiple gate files hold references to the same module object.
