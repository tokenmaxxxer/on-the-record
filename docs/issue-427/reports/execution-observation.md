---
kind: record
loop_state: handed-off
---

# Execution observation — issue #427

## Independence statement

This role did not author or edit the observed artifact this session. No
file under `gates/test_closes_gate_ci.py`, `gates/pr_reference.py`,
`gates/acceptance_gate.py`, or `docs/issue-427` proposal/implementation
paths was touched here. Evidence below comes from running the shipped
test suite as-is and a scratch (uncommitted) guard script that only
monkeypatches `subprocess.run` to observe whether `gh` is invoked.

## Amendments reconciled

amendments-reconciled: issuecomment-5290043416 — this role's own
`APPROVE issue-427/execution-observation` posted this session to
satisfy the phase-2 approval gate before this write; no other new
comment on issue #427 since session start.

## Upstream basis

`0080276db1c0d1a342db9fd790340f0a6c612999` (merge commit for PR #440,
`issue-427/implementation` → `main`), currently reachable from this
branch's `HEAD` at `bc53410e1cc12d4e80ae3794489e9fbf4c4b41d9`. Delivery
record: `docs/issue-427/reports/implementation.md`.

## What was done

1. Read `docs/issue-427/reports/implementation.md` and
   `docs/issue-427/proposals/2026-08-07-isolate-fixture-from-acceptance-gate.md`.
2. Ran the two target tests in isolation.
3. Ran the full `gates/test_closes_gate_ci.py` file.
4. Ran `gates/` as a whole for surrounding-suite context.
5. Reproduced the report's `subprocess.run` network-boundary guard
   directly against the two target tests (own driver, not re-running the
   observed role's own manual check).
6. Read `gates/test_closes_gate_ci.py` around the two target test
   bodies to check the report's flagged open finding (missing
   regression guard for "fixture reverts to live fetch").

## Evidence and verdicts

### Target tests, isolated

```
$ python3 -m pytest -q gates/test_closes_gate_ci.py -k 304_307
..                                                                       [100%]
2 passed, 52 deselected in 0.20s
```

canonical: python3 -m pytest -q gates/test_closes_gate_ci.py -k 304_307 (this turn, HEAD bc53410e) — result: 2 passed — `t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch` and `t_autodetect_304_307_shape_still_surfaces_real_acceptance_gate_finding` each passed.

### Full target file

```
$ python3 -m pytest -q gates/test_closes_gate_ci.py
......................................................                   [100%]
54 passed in 1.31s
```

canonical: python3 -m pytest -q gates/test_closes_gate_ci.py (this turn, HEAD bc53410e) — result: 54 passed — full-file run passed.

### Surrounding gates suite

```
$ python3 -m pytest -q gates/
7 failed, 580 passed, 1 xfailed in 12.70s
```

canonical: python3 -m pytest -q gates/ (this turn, HEAD bc53410e) — result: 7 failed, 580 passed — the 7 failures (`test_boundary.py::t_all_gates_modules_recorded`, `test_clean_reconcile_safety.py`, `test_consult_json_parse.py` x2, `test_consult_verdict_parsing.py`, `test_product_capture_vs_deliverable_guard.py`, `test_role_utilization_report.py::test_all_43_role_stems_present_as_keys_in_count_map`) are inapplicable to this observation's subject — none is in `gates/test_closes_gate_ci.py`, `gates/pr_reference.py`, or `gates/acceptance_gate.py`.

### Network-boundary guard

```
$ python3 - <<'PY'
import subprocess, sys
orig = subprocess.run
def guarded(argv, *a, **k):
    if argv and argv[0] == "gh":
        raise AssertionError("gh CLI invoked: " + str(argv))
    return orig(argv, *a, **k)
subprocess.run = guarded
import pytest
sys.exit(pytest.main(["-q", "gates/test_closes_gate_ci.py", "-k", "304_307"]))
PY
..                                                                       [100%]
2 passed, 52 deselected in 0.17s
```

canonical: python3 (scratch subprocess.run guard driver above, this turn, HEAD bc53410e) — result: 2 passed with `gh` argv0 blocked — both target tests reach no live GitHub state, passed.

### Regression coverage for fixture reverting to a live fetch

canonical: this turn's execution transcript above plus a read of `gates/test_closes_gate_ci.py`'s two target test bodies — `acceptance_gate.check_issue_body` is stubbed inside `t_autodetect_cross_role_handoff_304_307_shape_is_phase2_no_mismatch`; both tests stub `pr_reference._issue_view_body`/`_pr_view`; no assertion in either test fails if those stubs were deleted so the fixture reverted to a live `gh` call — result: untested.

This matches the open finding already recorded in
`docs/issue-427/reports/implementation.md`'s "Open findings" section: no
committed test guards against the fixture silently reverting to a live
fetch.

## Outcome

canonical: this turn's execution transcript above (five entries: passed, passed, inapplicable, passed, untested) — recomputed worst case per `roles/specs/execution-observation.spec.json` (failed > cantTell > inapplicable > untested > passed) is untested.

The two committed target tests and the network-boundary guard all
behave exactly as `docs/issue-427/reports/implementation.md` claims;
the one open finding that report already surfaced remains open per
this turn's own read (evidence above), not newly discovered here.

## Trajectory

canonical: this turn's full-target-file and surrounding-suite pytest measurement above — the entirety of `gates/test_closes_gate_ci.py` passed, `gates/` at large carries 7 unrelated failures.

Issue #427's scoped write set (`gates/test_closes_gate_ci.py` isolation
+ companion pin) is fully landed on `main` as of `0080276d`; this
branch's own delivery is not blocked by anything observed here.

## Step

canonical: this record's own execution transcript above, produced this turn — no execution-blocking condition encountered, evidence gathering here is handed off.

This observation: nothing under this role's write scope remains to
gather for the current commit sha.

## What did not work

None.

## Doc placement

- [x] This record: docs/issue-427/reports/execution-observation.md
