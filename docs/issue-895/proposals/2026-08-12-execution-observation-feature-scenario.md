---
status: proposed
files:
  - docs/issue-895/reports/execution-observation/feature-scenario-2026-08-12-run1.md
  - docs/issue-895/reports/execution-observation/feature-2026-08-12-run1-first-turn.json
  - docs/issue-895/reports/execution-observation/feature-2026-08-12-run1-resume1.json
  - docs/issue-895/reports/execution-observation/feature-2026-08-12-run1-resume2-final.json
  - docs/issue-895/reports/execution-observation.md
---

## Request

Issue #895 step 2 asks execution-observation to run the FEATURE-ADD matrix
scenario (`harness/driver.py::SCENARIOS["feature"]`, landed by #905) live
through the same zero-human autonomous loop that reached all-signal PASS
for the bug-fix representative (#893), and record per-signal
PASS/FAIL/UNMEASURED plus the precise break point.

## Constraints so far

- Do not reuse prior transcripts/paths/numbers; never fabricate a
  `final_report`; never write a full token (the #892/#904 credential
  guards are active).
- This role edits only its own report path — no file under `harness/`,
  `spawn.py`, `docs/specs/`, or `docs/handbooks/` gets touched.
- The per-issue execution-observation record
  (`docs/issue-895/reports/execution-observation.md`) is phase-2-gated:
  `on-the-record/hooks/approval-gate.sh` refused a direct write this
  session because no `APPROVE issue-895/execution-observation` comment
  (or `DELEGATE ... VIA DELEGATION` grant) exists on issue #895 — see
  `docs/issue-895/reports/execution-observation/feature-scenario-2026-08-12-run1.md`
  "What blocks phase 2" for the full citation.

## What will be done

Run the feature scenario live (already done this session — see the linked
run log for the full canonical evidence chain): fresh fixture instance,
real GitHub fixture host, isolated `MUSTER_STATE_ROOT`, `claude -p` first
turn, poll for PR, resume, poll again, resume to merge+report,
independent rebuild, and `harness.signals.evaluate_all` against the real
transcript/repo_state. Write the raw evidence and instrument reading to
`docs/issue-895/reports/execution-observation/feature-scenario-2026-08-12-run1.md`
(phase-1-permitted path) now. Write the top-level per-issue
`execution-observation.md` record — independence statement plus the
outcome/trajectory/step verdict recomputed from this already-gathered
evidence — once `APPROVE issue-895/execution-observation` lands; no
re-execution needed at that point.

## Out of scope

Fixing the silent-delegation-death gap the run surfaced (a different
role/session, issue #895 step 3). Running the other five matrix scenario
types (multimod, redtest, ambiguous, multirole, infeasible) — this
proposal covers the feature-add scenario only.

## How you'll know it worked

The linked run log cites, for every claim, either a `canonical:` tag
naming the exact command/file read this session, or a pasted code-fenced
command output — matching this repo's `record-claim-guard.sh` shape. The
top-level record (once approved) recomputes the same outcome/trajectory/
step verdict from that evidence with no gaps.

## What did not work

The first delegation attempt (feature scenario, issue #10 on the real
GitHub fixture host) died silently: the orchestrator's first turn
narrated a live background `implementation` spawn, but an 480s
`poll_for_pr_ready` timeout, an empty branch list, an empty issue
timeline, no matching process, and an empty isolated `MUSTER_STATE_ROOT`
all confirmed nothing survived. See the linked run log's step 6 for the
full canonical citation chain. Resuming the same orchestrator session
caused it to respawn cleanly and complete on the second attempt (steps
7-10) — this is recorded as an open finding, not fixed here (out of
scope, see above).
