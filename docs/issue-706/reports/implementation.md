---
code_under_review:
  - on-the-record/hooks/deliverable-guard.sh
  - on-the-record/hooks/decision-queue-stopgate.sh
  - on-the-record/hooks/retry-loop-bound.sh
  - on-the-record/hooks/role-test-claim-guard.sh
  - on-the-record/hooks/test_deliverable_guard.py
  - on-the-record/hooks/test_decision_queue_stopgate.py
  - on-the-record/hooks/test_retry_loop_bound.py
  - on-the-record/hooks/test_role_test_claim_guard.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue #706

## Summary of work

For the 4 security-relevant presence-only hooks named in the approved
phase-1 proposal (`docs/issue-706/proposals/2026-08-11-presence-only-hooks-session-role-bind.md`),
moved the `CLAUDE_ROLE` set/unset presence check out of the shell
pre-check and into each hook's Python body, resolving role identity from
the #698 session-role-bind snapshot
(`${OTR_ROLE_BIND_STATE_DIR:-$TMPDIR/otr-role-bind}/<session_id>.json`)
first, falling back to the live `CLAUDE_ROLE` env var only when no
snapshot exists for the session or it is unreadable/malformed — the same
resolve-with-fallback pattern `approval-gate.sh` already uses for issue
#698, ported verbatim (no new state mechanism, no new dependency).

- `deliverable-guard.sh`: presence check (`[ -z "${CLAUDE_ROLE:-}" ] ||
  exit 0`) moved into the Python body; resolved role skips the
  orchestrator-deliverable-write deny when a role is bound (session
  snapshot or live fallback).
- `decision-queue-stopgate.sh`: presence check (`[ -z "${CLAUDE_ROLE:-}"
  ] || exit 0`) moved into the `CHECK` Python body, ahead of the flows
  fetch's use; the pre-existing second parse of `STOPGATE_STDIN_JSON`
  later in the same script (for the waiting-declaration branch) was
  collapsed to reuse the single earlier parse instead of re-parsing.
- `retry-loop-bound.sh`: presence check moved into the shared python
  heredoc, right after `session_id` is validated (session_id is needed
  for both the retry-bound state key and the role-bind snapshot lookup).
- `role-test-claim-guard.sh`: presence check (opposite polarity — `[ -n
  "${CLAUDE_ROLE:-}" ] || exit 0`, role-only) moved into the Python body;
  resolved role empty now skips (not-a-role-session), matching the
  original polarity.
- Each hook's `ORCHESTRATE_OFF` kill switch and fail-closed/fail-open
  trap behavior is untouched — only the `CLAUDE_ROLE` presence test
  moved, per the proposal's constraints.
- Added the acceptance-named unset-spoof regression test per hook:
  session binding says a role is bound, `CLAUDE_ROLE` is unset in the
  test's env, hook invoked with that session_id -> it takes the role
  branch (or refuses), not the orchestrator branch. `deliverable-guard.sh`
  had no prior test file, so `test_deliverable_guard.py` is new (project
  convention: one `test_*.py` per hook, per the proposal's stated
  build-time decision); the other three extend their existing test
  files. Each also gets a no-snapshot-falls-back-to-live-env control
  test.

## Why

Follow-up to #698: 4 of the 8 hooks the #698 survey found branching only
on `CLAUDE_ROLE` presence reach a hard enforcement outcome (`exit 2` deny
or `decision:"block"`), so a role session that unsets the env var before
a call could flip itself into orchestrator-session treatment against
those 4 — skipping a role-only check or triggering an orchestrator-only
one. Reusing #698's already-landed, already-tested resolve pattern closes
that spoof path without inventing a second mechanism.

## Upstream basis

Basis: docs/issue-706/proposals/2026-08-11-presence-only-hooks-session-role-bind.md

## Rationale for deviations

None — implementation matches the proposal's "What will be done" as
written; no scope-exceeded stop, no alternative swap.

## What did not work

- First cut of the `test_deliverable_guard.py` fixture used a plain
  `tmp_path` directory with no `.git` subdirectory. Expected: the "board
  repo" fixture (has `docs/specs/approvers.md`) alone would be enough to
  trigger `deliverable-guard.sh`'s deny branch. Actual: the hook's root
  detection walks up looking for a `.git` directory before ever checking
  for `docs/specs/approvers.md`, so with no `.git` present it silently
  fell through the `root is None` branch to allow (rc=0) — fixed by
  adding an empty `.git` directory to the fixture.

## Open findings

One hunt finding (before-landing, stance 0) — see Hunt below. Assessed
as a pre-existing #698-inherited limitation, not a regression from this
change, and out of scope for #706 as scoped by the proposal; not
blocking. resolution path: a follow-up issue against the session-role-bind
mechanism itself (snapshot absence for never-bound/orchestrator sessions
falling open to a forged live env var), tracked as a candidate the same
way the proposal's own "Out of scope" section already flags the
TMPDIR-trust gap as a follow-up candidate rather than absorbed here.

## Hunt

before-landing, stance 0 (assume the gate just touched is bypassable —
find the bypass), dispatched against the diff of the 4 changed hooks.
Record: docs/issue-706/reports/implementation/hunt-presence-only-hooks-session-role-bind.md

Finding: an orchestrator session (which never receives a session-role-bind
snapshot, since `session-role-bind.sh` only snapshots when `CLAUDE_ROLE`
is already set at SessionStart) can forge `CLAUDE_ROLE` live with no
snapshot to contradict it, and the fallback-to-live-env-when-no-snapshot
path — required by this issue's own acceptance ("falling back to the env
var only when no binding exists") and #698's already-landed
`approval-gate.sh` — accepts the forged value uncontested.

Assessment: this is the pre-existing #698 resolve-with-fallback design
applied identically here, not something #706 introduces or could fix
without abandoning the "fall back to env var when no binding exists"
requirement the issue's acceptance criteria and the proposal's
constraints both state explicitly. `approval-gate.sh` (already merged,
out of this proposal's write set) has the identical gap. Closing it needs
a change to `session-role-bind.sh` itself (e.g. snapshotting an
"orchestrator, no role" state too, so absence is never ambiguous with
"not yet bound") — the proposal's own "Out of scope" section already
lists `session-role-bind.sh` and its state-file format as untouched by
this proposal. Not fixed here; flagged as a follow-up candidate.

## closed_checks

- check: full on-the-record/hooks/ pytest suite
  code_sha: (see code_under_review: file list above)
  derived: `python3 -m pytest on-the-record/hooks/ -q`
  result: 159 passed, 0 failed
- check: unset-spoof regression, all 4 security-relevant hooks
  code_sha: (see code_under_review: file list above)
  derived: `python3 -m pytest on-the-record/hooks/test_deliverable_guard.py on-the-record/hooks/test_decision_queue_stopgate.py on-the-record/hooks/test_retry_loop_bound.py on-the-record/hooks/test_role_test_claim_guard.py -k "unset_spoof or no_snapshot" -q`
  result: all new spoof-regression tests pass (fail on pre-fix code,
    verified manually by reverting the resolve blocks and re-running --
    pre-fix, the bound-role-but-live-unset scenario took the orchestrator
    branch; post-fix it takes the role branch)
- check: harmless-convenience hooks unchanged
  code_sha: n/a (confirms non-write)
  derived: `git status --short on-the-record/hooks/directive.sh on-the-record/hooks/report-framing-check.sh on-the-record/hooks/stop-gate.sh on-the-record/hooks/product-capture-stopgate.sh`
  result: no output — none of the 4 out-of-scope hooks were touched
