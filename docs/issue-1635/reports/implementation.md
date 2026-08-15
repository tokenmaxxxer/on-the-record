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

## Acceptance verification
- check: fixture record with `loop_state: handed-off` (declared under a
  role's `terminal` bucket) produces 0 `record_enums` findings; a
  genuinely-undeclared value still fires.
  canonical: `python3 -m pytest tests/test_gates.py -k record_enums -v`
  acceptance: UNMEASURED-with-reason: no row for this exact command in
  docs/specs/acceptance-commands.md; the fenced output in the Test run
  section above is this session's own live re-run of that command.
- check: `gates/precision_measure.py` sample on live HEAD returns a
  fully-drained sweep queue for this rule.
  canonical: `python3 precision_measure.py sample .. --n 100 --seed 20260816 --out /tmp/precision_samples_1635.json` (run with cwd=gates/)
  acceptance: UNMEASURED-with-reason: no row for this exact command in
  docs/specs/acceptance-commands.md; the fenced JSON output below is
  this session's own live re-run of that command.
```
wrote 0 sample items (population 0) to /tmp/precision_samples_1635.json
```
```json
{
  "population_size": 0,
  "n": 100,
  "floor": 5,
  "seed": 20260816,
  "sample": []
}
```

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
