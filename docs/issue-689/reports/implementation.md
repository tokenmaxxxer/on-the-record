---
code_under_review:
  - docs/specs/enforcement-boundary.md
  - gates/test_closure_sweep.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Restored main to green after two drifts surfaced during CI:

1. Added the three missing verdict rows to `docs/specs/enforcement-boundary.md`
   for `ui_evidence_gate.py`, `remediation_spawn.py`, and
   `role-axis-completeness-guard.sh`, each classified against an existing
   analogous row already in the spec (claims.py-style unreached
   registration, run.md-instructed CLI reachability, and a zero-install
   PreToolUse hook, respectively).
2. Fixed the `test_pr_view_failure_is_a_skip` test in
   `gates/test_closure_sweep.py` (class `FindViolationsSkips`):
   it was silently falling through `find_violations`'s new `_pr_index_all`
   list-based fast path (introduced by issue #682) instead of exercising the
   per-branch `_pr_for_branch`/`_pr_view_state_body` fallback it was written
   to target. The test now mocks `_pr_index_all` to return a truncated-list
   signal so the intended fallback path still runs.

## Why

Both were regressions against already-documented/intended behavior, not new
design decisions: the boundary spec was missing rows for gates that already
exist and are classifiable by direct analogy, and the closure_sweep test was
passing for the wrong reason after issue #682 changed `find_violations`'s
internals underneath it. Pure restoration — no open design decision, so
phase-1 proposal is skipped per the scout-directive's bugfix exception.

## Upstream

Subject: issue-689 (commit bedbf0e44556e28c70da962bac6b5bee756e88d6)

## What did not work

None.

## Doc placement

- docs/specs/enforcement-boundary.md — spec correction (verdict rows), same
  commit as the code it documents.

## Open findings

None outstanding.

## Hunt cadence

No warrant-hunter dispatch this session — the change under review here is a
restoration already merged in the referenced commit (bedbf0e); this record
documents it retroactively to close out delivery. No new code was written in
this turn.
