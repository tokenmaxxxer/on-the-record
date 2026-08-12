---
code_under_review:
  - gates/gates.py
  - gates/test_record_lint.py
type: fix
breaking: false
# canonical: python3 -m pytest gates/test_record_lint.py -q -k terminal_loop_state (executed this turn; 2 passed) — basis for verdict below.
verdict: pass
loop_state: landed
---

# issue-1105 implementation record

## What was done
`gates.py::_terminal_loop_state` did `states[-1] if states else None` where
`states = role_cfg.get("record_fields", {}).get("loop_state")`. That guard
only handles falsy `states` (`None`/`[]`); it does not handle a *truthy but
non-list* `states`.

canonical: gates/gates.py::_terminal_loop_state (read this turn, before edit)
derived:
```
$ cd roles && for f in *.json; do python3 -c "
import json
d=json.load(open('$f'))
ls = d.get('record_fields',{}).get('loop_state')
if not isinstance(ls,(list,tuple)) and ls is not None:
    print('$f', type(ls))
"; done | wc -l
41
```
41 of the role definitions under `roles/*.json` (`architecture.json`,
`defect-verification.json`, `accessibility.json`, and others) declare
`record_fields.loop_state` as a dict shaped `{progress, terminal,
refusal, error}`, not a flat list — `states[-1]` on that dict raises
`KeyError: -1`, matching the crash reported in #1105
(`python3 gates/record_lint.py <record>` inside a mid-merge working tree
while resolving PR #1100).

canonical: gates/gates.py::_terminal_loop_state (edited this turn)
Fixed `_terminal_loop_state` in `gates/gates.py` to check
`isinstance(record_fields, dict)` and `isinstance(states, (list, tuple))`
before indexing, returning `None` for any shape it cannot safely read the
last element of. `record_checked_claims` and `parse_checked_claims` both
call `_terminal_loop_state` and needed no separate change — they already
treat a `None` terminal as "this gate does not touch the record" and
`continue`.

canonical: gates/test_record_lint.py (written this turn)
Added two tests to `gates/test_record_lint.py`. Test 1,
`t_terminal_loop_state_dict_shaped_states_no_crash`, loads the real
`roles/architecture.json` (dict-shaped `loop_state`, asserted as a
fixture precondition) and asserts `_terminal_loop_state` returns `None`
there, and that `record_lint.lint_record` returns a plain list (no
traceback) for a terminal-`loop_state` record under that role. Test 2,
`t_terminal_loop_state_empty_states_returns_none`, is direct unit
coverage of the empty-list/missing-key/normal-list cases, asserting
normal (flat-list, e.g. `implementation.json`-style) records lint the
same as before this change (`["a", "b"]` -> `"b"`).

canonical: acceptance: python3 -m pytest gates/test_record_lint.py -q -k terminal_loop_state — result: pass
```
$ python3 -m pytest gates/test_record_lint.py -q -k terminal_loop_state
..                                                                       [100%]
2 passed, 23 deselected in 0.13s
```

canonical: acceptance: python3 gates/test_record_lint.py — result: pass
derived: python3 gates/test_record_lint.py 2>&1 | tail -3
```
$ python3 gates/test_record_lint.py 2>&1 | tail -3
ok t_terminal_loop_state_dict_shaped_states_no_crash
ok t_terminal_loop_state_empty_states_returns_none
24/25 passed
```
The one remaining failure (`t_orphaned_path_reference_check_false_positives_documented_gap`)
is pre-existing, unrelated to this change:

canonical: derived: (git stash && python3 gates/test_record_lint.py 2>&1 | tail -2 && git stash pop)
```
$ git stash && python3 gates/test_record_lint.py 2>&1 | tail -2 && git stash pop
ok t_no_defect_claim_is_untouched
22/23 passed
```

## Why
`northpole req#2` (완전 기록성) — a lint-path crash is fail-open for
hooks that treat non-violation output as an acceptable result, or a hard
block for authoring flows; #1105 asks this made robust with a
reproducing test.

## Upstream
Basis: #1105 (issue text quotes the exact `KeyError: -1` reproduced
2026-08-12 during PR #1100's merge-conflict resolution).

## What did not work
None.

## Open findings
None.

canonical: python3 -m pytest gates/test_record_lint.py -q -k terminal_loop_state (executed this turn; 2 passed, shown above)
## Acceptance verification
- dict-shaped loop_state no longer crashes — checked: gates/test_record_lint.py::t_terminal_loop_state_dict_shaped_states_no_crash — result: pass
- empty/normal states unchanged — checked: gates/test_record_lint.py::t_terminal_loop_state_empty_states_returns_none — result: pass
