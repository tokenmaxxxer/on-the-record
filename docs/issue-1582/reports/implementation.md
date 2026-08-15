---
code_under_review:
  - gates/patrol_queue.py
  - on-the-record/hooks/test_patrol_queue_hook.py
  - gates/patrol_trigger.py
  - on-the-record/hooks/test_patrol_trigger_hook.py
  - gates/test_patrol_queue.py
  - gates/test_patrol_trigger.py
  - docs/specs/enforcement-boundary.md
  - docs/issue-1582/reports/implementation/patrol-measurement-2026-08-15.md
type: feature
breaking: false
canonical: python3 -m pytest on-the-record/hooks/test_patrol_queue_hook.py on-the-record/hooks/test_patrol_trigger_hook.py -q
verdict: pass
loop_state: landed
---

## What was done

canonical: python3 -m pytest on-the-record/hooks/test_patrol_queue_hook.py on-the-record/hooks/test_patrol_trigger_hook.py -q — 23 passed, 0 failed (this session's own run).

Built the tier-1 (mechanical-scanner-only) slice of the approved
proposal docs/issue-1582/proposals/2026-08-15-tier1-role-patrol-pilot.md:

- gates/patrol_queue.py: fingerprint (sha256 of scanner_id + normalized
  path + a hash of context lines, no line numbers), enqueue/dedup,
  absence_close, lane separation with promotable hard-checked to
  lane=="diff" inside enqueue itself, apply_budget (drop-not-queue with
  one meta-finding per truncated scanner), verify, and
  record_dismissal/dismissal_counts. A record_lint scanner adapter
  (scan_record_lint) wired in as the pilot's one tier-1 scanner, plus
  run_scan tying the pipeline together end to end.
- gates/patrol_trigger.py: should_fire, the #1360-class origin guard —
  refuses to fire when an event's changed-file set is entirely
  patrol-produced artifacts (the queue file, or a patrol measurement
  report) — and run_if_eligible, a thin wrapper that only calls
  patrol_queue.run_scan when should_fire is true. Not wired into a
  git-native hook, per the proposal's Constraints.
- on-the-record/hooks/test_patrol_queue_hook.py and
  on-the-record/hooks/test_patrol_trigger_hook.py: fingerprint stability
  under context/line shift, dedup refresh, absence-close, lane-
  separation invariant (sweep can never be promotable), budget
  truncation and its meta-finding, verifiability drop, dismissal
  suppression, and the #1360-class regression test comparing the actual
  should_fire against a naive pre-fix-shaped check on the same event.
  The pytest run cited above is this module pair's confirmation run.
- docs/issue-1582/reports/implementation/patrol-measurement-2026-08-15.md:
  dual measurement per PR #1583's binding correction — a real-input run
  against this repo and an empty-input negative control against
  /home/jwjung/tokenmaxxxer; full numbers in that report's own fenced
  command output.

canonical: grep -rn "consult\|spawn\.py" gates/patrol_queue.py gates/patrol_trigger.py — no match, exit 1 (this session's own run).

No spawn.py/consult call exists in either new module, per the grep
cited above — the proposal's own stated check.

## Why

basis: docs/issue-1582/proposals/2026-08-15-tier1-role-patrol-pilot.md
(approved via APPROVE issue-1582/implementation on the issue), and PR
#1583's binding review correction on the measurement target.

## Open findings

None.

## What did not work

canonical: this session's own local run of
`python3 gates/patrol_queue.py scan . --lane sweep`, first attempt,
before the fixes below (also recorded in the measurement report's own
"Defects fixed" section).

The first live run of the measurement scanner returned `verified: 0,
verify_dropped: 3622` — scan_record_lint() was passing the full
generated lint-violation message as a finding's excerpt, but verify()
requires the excerpt to appear verbatim in the cited file, and a
generated message never does. Expected: verified findings on a corpus
with genuine record_lint violations. Actual: zero verified. Fixed by
extracting the verbatim-quoted span record_lint's own messages already
carry, and rerunning both measurement runs against the corrected code
before this record was written.

A related first-attempt defect: fingerprint context was the record
file's static first five lines, identical across every violation in
that file, collapsing distinct violations onto one fingerprint. Fixed
by fingerprinting on the full violation message instead.

## Rationale for deviations

The proposal's frozen write set named the measurement report path as
docs/issue-1582/reports/patrol-measurement-2026-08-15.md (a bare
reports/ path). board-gate.sh refused that path at write time: this
role may only write docs/issue-<n>/reports/implementation.md or
docs/issue-<n>/reports/implementation/** (contract v3 s11) — a bare
reports/*.md path outside that shape is treated as belonging to
another role. The report was written instead at
docs/issue-1582/reports/implementation/patrol-measurement-2026-08-15.md,
the equivalent path under this role's own allowed subtree, with no
change to its content or acceptance criteria. This is a mechanical
path correction forced by a gate the proposal did not anticipate, not
a scope or design change.

Two commit-time gates also forced small mechanical additions outside
the proposal's originally-listed write set, staying inside the same
family of doc-placement/registration mechanics: gate-registration-guard.sh
required a docs/specs/enforcement-boundary.md row for each new
gates/*.py module (added as repo-local rows — neither module is wired
into a zero-install reachability path in this pilot); live-fire-test-guard.sh
required a gates/test_<stem>.py live-fire test per new gates/*.py
module calling it in-process from >= 2 distinct scenarios (added as
gates/test_patrol_queue.py and gates/test_patrol_trigger.py, thin
wrappers around scenarios already covered by
on-the-record/hooks/test_patrol_queue_hook.py and
on-the-record/hooks/test_patrol_trigger_hook.py). Neither addition changes
patrol_queue.py's or patrol_trigger.py's own design.

## Next steps

canonical: python3 -m pytest on-the-record/hooks/test_patrol_queue_hook.py on-the-record/hooks/test_patrol_trigger_hook.py -q — 23 passed, 0 failed (this session's own run).

None — the proposal's "What will be done" list has no remaining item,
and both of its "How you'll know it worked" mechanical checks are
covered by the pytest and grep runs cited above.

## Resolution path

N/A — no open findings.
