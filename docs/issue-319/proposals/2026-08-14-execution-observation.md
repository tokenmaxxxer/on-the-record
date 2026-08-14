---
status: proposed
files:
  - docs/issue-319/reports/execution-observation/survey.md
  - docs/issue-319/reports/execution-observation.md
---

## Request

Issue #319 asks execution-observation to observe the delivery that landed
via PR #345 (`issue-319: risk-classified, batched approval report`, merged
`2026-08-07T07:53:00Z`, merge commit `05f266c0c3febdd1994dc54195d088d90774ce30`),
which no execution-observation record exists for yet, and render the
outcome/trajectory/step verdict per `roles/specs/execution-observation.spec.json`.

## Constraints so far

- This role edits only its own report path (`docs/issue-319/reports/
  execution-observation*`) — no `gates/`, `docs/handbooks/`, or
  implementation's own docs paths touched.
- The per-issue execution-observation record
  (`docs/issue-319/reports/execution-observation.md`) is phase-2-gated:
  `on-the-record/hooks/approval-gate.sh` refuses a direct write this
  session because no `APPROVE issue-319/execution-observation` comment
  (or a live `DELEGATE ... VIA DELEGATION` grant scoped to it) exists on
  issue #319 — the only matching comment on the issue is
  `APPROVE issue-319/implementation`, a different role's citation, not
  usable here (`gates/spawn.py`'s own approval-gate check requires an
  exact `APPROVE issue-<n>/<role>` string per role).
- `gh` calls are currently rate-limited on this token (`gh api user` →
  `403 API rate limit exceeded`, this session) — evidence below relies on
  `gh` output already fetched earlier this session plus local repo state
  (`git`, `python3`), not further live `gh` calls.

## What will be done

Read PR #345's file list and merge commit, `docs/issue-319/reports/
implementation.md` (loop_state: phase-2-complete), and the current-HEAD
state of `gates/risk_report.py` / `gates/test_risk_report.py` (this
delivery's functions were later extended, not replaced, by issue #511's
`e9b24352`). Run `gates/test_risk_report.py` directly this session and
record the exit code. Write the raw evidence to
`docs/issue-319/reports/execution-observation/survey.md` (phase-1-permitted
path) now. Write the top-level `execution-observation.md` record —
independence statement plus the outcome/trajectory/step verdict recomputed
from this already-gathered evidence — once `APPROVE issue-319/
execution-observation` lands; no re-execution needed at that point.

## Out of scope

Observing any later delivery that touches `gates/risk_report.py`
(issue #511's four-axis extension already has its own execution-observation
scope, if any) — this proposal covers PR #345's original delivery only.

## How you'll know it worked

The linked survey file cites, for every claim, either a `canonical:` tag
naming the exact command/file read this session, or a pasted code-fenced
command output, matching this repo's `record-claim-guard.sh` shape. The
top-level record (once approved) recomputes the same outcome/trajectory/
step verdict from that evidence with no gaps.

## What did not work

N/A — no attempt was undone or replaced this session; the phase-2 write
block below is an expected gate refusal, not a failed attempt.
