---
issue: 2226
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2226/reports/implementation.md
    sha: same-commit
code_under_review:
  - gates/record_lint.py
  - gates/ci.py
  - gates/claims.py
  - gates/risk_report.py
type: fix
breaking: none — behavior is unchanged for both invocation forms; only the internal import mechanism changed.
verdict: pass
---

# issue-2226 — implementation record

## What was done

Fixed the sibling-import/namespace-package collision in `gates/record_lint.py`
that raised an AttributeError under `python3 -m gates.record_lint`, and
audited the rest of `gates/` for the same shape as the issue asked.

Reproduced the issue's own before-state at the start of this session:

```
$ python3 -m gates.record_lint
  File ".../gates/record_lint.py", line 31, in <module>
    RECORD_PATH = gates.RECORD_PATH  # docs/issue-<n>/reports/<role>.md
AttributeError: module 'gates' has no attribute 'RECORD_PATH'
```

Root cause: `gates/record_lint.py` did `sys.path.insert(0,
str(Path(__file__).parent)); import gates`, intending the sibling
`gates/gates.py`. Under `python3 -m gates.record_lint`, Python's own `-m`
package resolution had already bound `sys.modules["gates"]` to the implicit
namespace package for the `gates/` directory (no `__init__.py` there)
before that line ran. A bare `import gates` hit that cache and resolved to
the namespace package instead of re-resolving through `sys.path`, so
`gates.RECORD_PATH` failed to resolve. `python3 gates/record_lint.py`
worked because direct-script invocation never imports a `gates` parent
package in the first place.

Fix: each affected file now loads `gates/gates.py` directly by file path via
`importlib.util.spec_from_file_location`, cached under a private
process-shared key (`sys.modules["_on_the_record_gates_sibling_impl"]`)
rather than under the name `"gates"`. This resolves unambiguously
regardless of invocation form, and never touches `sys.modules["gates"]` —
so it never disturbs any parent-package state Python's own `-m` machinery
may still need later in the same process (see "What did not work" below).

Audit of the rest of `gates/` for the same `sys.path.insert` + bare
`import <sibling>` shape:

```
$ grep -rln "^import gates$" gates/*.py
claims.py
ci.py
risk_report.py
test_gates_refusal.py
test_capability_gates.py
record_lint.py
test_duplicate_test_basenames.py
test_orphaned_references.py
test_recurrence.py
test_closes_gate_ci.py
test_record_lint.py
```

The exact collision — a sibling import whose bare name equals the
enclosing package/directory name (`gates`) — is only possible for
`import gates` itself; every other bare sibling import in `gates/`
(`import flows`, `import record_lint`, etc.) names something that is not
also the directory's own package name, so it cannot hit this
cache-shadowing bug. Three more files do `import gates` and are runnable
as `-m gates.<X>` entry points: `gates/claims.py` (its own docstring
documents `python3 -m gates.claims .` as a supported invocation form),
`gates/risk_report.py` (additionally never had a `sys.path.insert` at all
— its direct-script form worked only via Python's automatic
script-directory insertion), and `gates/ci.py`. All three reproduced the
same AttributeError shape (against `_excluded_tree_dirs`, `BASE`, and
`changed_files` respectively) before the fix:

```
$ python3 -m gates.claims .
  ...
AttributeError: module 'gates' has no attribute '_excluded_tree_dirs'
$ python3 -m gates.risk_report .
  ...
AttributeError: module 'gates' has no attribute 'BASE'
$ python3 -m gates.ci .
  ...
AttributeError: module 'gates' has no attribute 'changed_files'
```

All four got the same fix. Every other `import gates` occurrence above is
in a `test_*.py` file normally invoked via `pytest`/direct script, not
`-m`, and is out of scope (not reproducible via any invocation form those
tests actually use).

## Why

`importlib.util.spec_from_file_location` loads a module by explicit file
path, independent of `sys.path` search order and independent of whatever a
prior `-m`/dotted import may have already cached under the target module's
bare name — immune to the specific hazard this issue names ("depending on
how the process was launched") by construction, rather than by detecting
and patching around one observed cache state. Caching the loaded module
under a private key (not `"gates"`) keeps all four fixed files sharing one
instance of `gates.py` (its module-level state is constants/functions
only, nothing mutable that would diverge across instances) without ever
aliasing `sys.modules["gates"]`.

Rejected alternative: turning `gates` into a regular package by adding an
`__init__.py` file there was not pursued — it would change every existing
bare sibling import's resolution semantics across the whole directory (a
much larger blast radius than this issue's ask), for a problem that is
fully contained to the one self-referential import name.

## What did not work

First fix attempt: on catching `sys.modules.get("gates")` bound to a
namespace package (no `__file__`), delete that cache entry before
`import gates`, so the bare import re-resolves via `sys.path` to the
sibling file. This worked for each file's own invocation — both `-m` and
direct-script forms produced identical output for all four files, and the
whole `gates/` suite ran clean under pytest:

```
$ python3 -m pytest gates/ -q
929 passed, 8 xfailed in 3.91s
```

A dispatched before-landing warrant-hunter (stance: assume the gate just
touched is bypassable) surfaced what broke it: evicting
`sys.modules["gates"]` leaves it rebound to the flat `gates/gates.py`
module (no `__path__`) for the rest of the process, so a second
`-m gates.<other>`-shaped dotted resolution attempted afterward in the same
interpreter hard-crashes:

```
$ python3 -c "
import runpy
runpy.run_module('gates.record_lint', run_name='not_main', alter_sys=True)
runpy.run_module('gates.claims', run_name='not_main', alter_sys=True)
"
ImportError: Error while finding module specification for 'gates.claims'
(ModuleNotFoundError: __path__ attribute not found on 'gates')
```

canonical: grep -rn "import gates\." --include=*.py --include=*.sh --include=*.yml .
No caller in this repo currently chains two dotted `gates.<X>` imports in
one process (grep above, run repo-wide, returned zero matches), but the
attempt traded one launch-order-dependent failure for another, which the
issue's own "resolve unambiguously" bar rules out. Replaced with the
file-path/private-key `importlib` load described above, which touches
neither `sys.path` nor `sys.modules["gates"]`; re-verified the same
two-call sequence plus a third module no longer raises, with `gates`
retaining its `__path__` throughout (see Acceptance evidence).

## Upstream basis

- GitHub issue #2226 (problem statement, root cause, and Acceptance
  section) — the fix and audit scope both follow it directly.
- docs/issue-2226/reports/implementation.md (this record) — sha:
  same-commit.

## Open findings

canonical: this session's own warrant-hunter dispatch, stance 0 (before-landing, gate-bypassable)
None left open. One came up mid-session — a background warrant-hunter
dispatched right before landing surfaced that the first fix attempt (see
"What did not work") corrupted `sys.modules["gates"]` for a later dotted
import in the same process. It was resolved in this same commit. The
hunter's own write-up of that stance is filed alongside this record, under
this issue's implementation report tree.

## Next steps

None — loop_state is terminal.

## Acceptance evidence (issue #2226)

Gate: `gates/test_record_lint.py`.

```
$ python3 gates/test_record_lint.py
... (68 tests)
68/68 passed
$ python3 -m pytest gates/test_record_lint.py -q
....................................................................     [100%]
68 passed in 1.04s
```

Empty-state (repo with no `docs/issue-*/reports/*.md` records at all — must
run to completion and report nothing), a fresh temp git repo with only a
`README.md`:

```
$ python3 -m gates.record_lint "$D"
record_lint: no records found under /tmp/tmp.EAxRQMMdo4 — 검사할 레코드가 없다.
$ echo exit:$?
exit:0
$ python3 gates/record_lint.py "$D"
record_lint: no records found under /tmp/tmp.EAxRQMMdo4 — 검사할 레코드가 없다.
$ echo exit:$?
exit:0
```

After-state, both invocation forms, executed live on this repo's own tree
(target is `/dev/null`, an invalid record path, so `main()` takes its
single-record branch rather than the whole-repo sweep — that sweep runs a
`git log` subprocess per candidate record across this repo's entire
`docs/issue-*` history, is not specific to the import-resolution fix, and
was not re-pasted here; the empty-state and single-path runs above already
exercise both `main()` branches):

```
$ python3 -m gates.record_lint /dev/null
- 레코드 경로 형태가 아니다: null — docs/issue-<n>/reports/<role>.md 형태여야 한다.
$ python3 gates/record_lint.py /dev/null
- 레코드 경로 형태가 아니다: null — docs/issue-<n>/reports/<role>.md 형태여야 한다.
```

Same failure text, same exit code, on both sides — the AttributeError no
longer occurs on either invocation form.

Full regression sweep after the fix:

```
$ python3 -m pytest gates/ -q
929 passed, 8 xfailed in 38.21s
```

Audited siblings, both forms diffed byte-for-byte identical after the fix:

```
$ diff <(python3 -m gates.claims .) <(python3 gates/claims.py .); echo $?
0
$ diff <(python3 -m gates.risk_report .) <(python3 gates/risk_report.py .); echo $?
0
$ diff <(python3 -m gates.ci .) <(python3 gates/ci.py .); echo $?
0
```

Cross-process-state regression the hunter surfaced, re-verified fixed:

```
$ python3 -c "
import runpy, sys
runpy.run_module('gates.record_lint', run_name='not_main', alter_sys=True)
print(hasattr(sys.modules.get('gates'), '__path__'))
runpy.run_module('gates.claims', run_name='not_main', alter_sys=True)
runpy.run_module('gates.ci', run_name='not_main', alter_sys=True)
print('all OK')
"
True
all OK
```

## Skill review (issue #1960/#2039/#2062/#2153)

Mounted skills checked against this task: implementation-blueprint,
implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice. None apply — this is a
single-directory (`gates/`) mechanical import-resolution bugfix with no
architectural structure decision, no coupling/cohesion metric involved, no
GoF pattern under consideration, and no data-structure/algorithm choice.
None was invoked via the Skill tool this session.

other mounted skills: not triggered
