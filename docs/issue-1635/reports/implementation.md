---
code_under_review:
  - gates/gates.py
  - tests/test_gates.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# issue-1635 implementation record

## Skip record (scout-directive)
Scouting skipped: pure bugfix to an existing gate's membership-check
logic (`gates/gates.py:340-347`) — no product-shaped design decision
is open, matching the same skip class as the prior #1628/#1620/#1614
misfire fixes to sibling gates.

## What was done
1. `gates/gates.py`'s `record_enums` (~line 340) treated a role spec's
   `record_fields` value as a flat allow-list even when the value is a
   BUCKETED dict (`{'progress': [...], 'terminal': [...], 'refusal':
   [...], 'error': [...]}`), so `value not in allowed` checked
   membership against the dict's KEYS, not its values — a genuinely
   valid bucketed terminal value like `handed-off` was mis-flagged as an
   enum violation. Fixed by flattening `allowed` into the union of all
   bucket lists (`{v for bucket in allowed.values() for v in bucket}`)
   when `allowed` is a dict, before the membership check; a plain list
   `allowed` (the non-bucketed case) is used as-is, unchanged.
2. `tests/test_gates.py` gained both-ways fixtures in the file at that
   path: a bucketed `loop_state` dict declaring `handed-off` under
   `terminal` produces 0 findings for `loop_state: handed-off`, and the
   same bucketed dict still fires on a genuinely undeclared value.

## What did not work
None.

## Test run
canonical: `tests/test_gates.py` (fixture text read back after write)
derived: `python3 -m pytest tests/test_gates.py -k record_enums -v`
```
8 passed in 0.87s
```

derived: `python3 precision_measure.py sample .. --n 100 --seed 20260817 --out /tmp/precision_samples_1635_v3.json` (run with cwd=gates/, live on this branch's HEAD after this section was rewritten into canonical claim-line form)
```
wrote 0 sample items (population 0) to /tmp/precision_samples_1635_v3.json
```
```json
{
  "population_size": 0,
  "n": 100,
  "floor": 5,
  "seed": 20260817,
  "sample": []
}
```

canonical: `python3 -m pytest tests/test_gates.py -k record_enums -v` — result: PASS, 8 passed, this session's live run (see fenced output above)
canonical: `python3 precision_measure.py sample .. --n 100 --seed 20260817 --out /tmp/precision_samples_1635_v3.json` — result: PASS, population 0, this session's live run (see fenced output above)

## Acceptance verification
- fixture record with `loop_state: handed-off` (declared under a role's `terminal` bucket) produces 0 `record_enums` findings, a genuinely-undeclared value still fires — checked: pytest-record-enums — result: pass: 8 passed, see `## Test run` above.
- `gates/precision_measure.py` sample on live HEAD returns a fully-drained sweep queue for this rule, including this record's own Acceptance verification section — checked: precision-measure-sample — result: pass: population 0, see `## Test run` above.

## Open findings
None.

## Rationale
Upstream: #1635 (surfaced by PR #1634's precision sample — population
dropped 2->1, residual FP on `loop_state: handed-off`). Why: the gate
was checking `value not in <dict>` against a bucketed dict's keys
instead of its unioned values, so any bucketed role spec (progress/
terminal/refusal/error) would flag every one of its own declared
values as a violation. Fix flattens the union before the membership
check, restoring correct behavior for both bucketed and flat
`record_fields` declarations.
