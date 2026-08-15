---
code_under_review:
  - gates/patrol_wiring.py
  - gates/test_patrol_wiring.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# issue-1607: patrol_wiring per-role exception isolation

## Scope note (scout skip)

This is a pure defect fix with a precisely located repro (issue body:
`gates/patrol_wiring.py`'s per-role loop ~line 88, `judge_cmd()` call
with no exception handling). Scouting was skipped per the scout
directive's bugfix skip condition — the fix shape (wrap one call in
try/except) leaves no design decision open.

## What was done

Wrapped the per-role `judge_cmd(role, merge_sha, cwd=str(root))` call in
`gates/patrol_wiring.py`'s `run()` function in try/except. On exception,
prints `[patrol-wiring] role=<r> errored (<ExceptionClassName>):
continuing` and `continue`s the loop instead of letting the exception
propagate and abort the whole per-merge patrol run. Kill-switch and cap
logic untouched — the try/except wraps only the `judge_cmd` call
itself.

## Why

canonical: issue #1607 body (`gh issue view 1607`)

Observed in issue #1605's live re-run: role=defect-verification raised
(claude exit 1, empty stderr) and the raw exception propagated out of
the per-role `for role in _known_roles()` loop, aborting patrol for
every role after the raiser for that merge. One flaky judge session
must never blind the rest of the patrol (watch-coverage invariant) —
this fix restores that invariant with the minimal try/except the issue
specifies.

## Upstream basis

basis: main @ c9ea1160 (fix(issue-1605): judge per-merge cap counts
prefilter-miss and cap-exceeded trace lines, #1606) — branch was already
even with `origin/main` at that commit before this change (`git log
origin/main --oneline -1` == `c9ea1160`), so issue #1605's cap-counting
fix is included.

## Test coverage

Added `test_one_role_judge_cmd_exception_does_not_abort_later_roles` to
`gates/test_patrol_wiring.py`: a `judge_cmd` stub raises `RuntimeError`
for the first known role and returns a normal hit for any other role;
the test asserts both the raiser and a later role were called (the loop
did not abort), the error trace line `role=<raiser> errored
(RuntimeError): continuing` was printed, and `result["hits"]` equals
`MAX_ROLES_PER_MERGE` — the cap, not an early abort, is what stops the
loop, proving roles after the raiser are genuinely invoked and counted.

derived:
```
$ python3 -m pytest gates/test_patrol_wiring.py -q
........                                                                 [100%]
8 passed in 0.98s
```

## Live end-to-end acceptance (discharges this issue's own acceptance AND issue #1597's deferred live-demo acceptance)

Fresh clone setup: `git clone -q /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1607-implementation /tmp/otr-fresh-clone && cd /tmp/otr-fresh-clone && git checkout -q issue-1607/implementation` — HEAD verified via `git log -1 --oneline` == fcdbe32a.

canonical: acceptance: python3 gates/patrol_wiring.py run . c9ea1160 — result: PASS
Full output captured via `tee` to /tmp/otr-live-run.log during that command: exit 0, loop completed ALL 44 known roles for merge sha c9ea1160, including the exact defect scenario the issue names (role=defect-verification errored) without aborting.

Trace excerpt (role=defect-verification erroring, then later roles
still invoked and the loop reaching completion):
```
[patrol-wiring] role=data-modeling skipped (prefilter_miss)
[patrol-wiring] role=defect-verification errored (RuntimeError): continuing
[patrol-wiring] role=devrel skipped (prefilter_miss)
[patrol-wiring] role=execution-observation judged, enqueued=1
[patrol-wiring] role=finance-unit-economics skipped (prefilter_miss)
[patrol-wiring] role=growth-analytics skipped (prefilter_miss)
[patrol-wiring] role=implementation judged, enqueued=0
[patrol-wiring] role=incident-response skipped (cap_exceeded)
...
[patrol-wiring] role=ux-engineering skipped (cap_exceeded)
[patrol-wiring] board refreshed for role=execution-observation
```
(full 62-line trace in /tmp/otr-live-run.log; every one of the 44 roles
from `_known_roles()` appears exactly once, terminating normally with
exit 0 — this is a live, unstubbed reproduction of the issue's exact
observed failure, role=defect-verification errored with the loop
continuing through role=ux-engineering, the last known role
alphabetically.)

## Kill-switch short-circuit demo

Same fresh clone, after `mkdir -p .on-the-record && touch .on-the-record/patrol-disabled`.

canonical: acceptance: python3 gates/patrol_wiring.py run . c9ea1160 — result: PASS
Output captured via `tee` to /tmp/otr-killswitch-run.log during that command: short-circuits before any role is touched.
```
[patrol-wiring] kill-switch active, skipping
```

## What did not work

None.

## Open findings

None.

## Accumulation

Not accumulation-cost-shaped — a single try/except added to one
existing loop body, no new recurring cost surface.
