---
code_under_review:
  - scripts/behavior_metrics.py
  - tests/test_behavior_metrics.py
  - docs/issue-1504/reports/implementation/behavior-metrics-2026-08-13-15.md
type: feature
breaking: false
verdict: pass  # canonical: python3 -m pytest tests/test_behavior_metrics.py -v — 7 passed, 0 failed (this turn)
loop_state: landed
---

## What was done

Built scripts/behavior_metrics.py, a re-runnable computation of the four
agent-behavior efficiency metrics issue #1504 requires: (a) re-check count
per (role, issue, unchanged-subject-hash), (b) sessions ending with 0
commits vs. their role's expected deliverable, (c) round-trip count per
landed change, (d) wait/poll time attributable to blocking sessions. Each
metric has a pure core function operating on parsed ledger-entry dicts
(unit-testable) plus a git/gh-backed extraction layer over
docs/issue-*/reports/**/deviation-log.md, Subject: issue-<n>
trailer-carrying commits, and gh pr list. Computed the metrics for the
2026-08-13..15 window and wrote the ranked waste-pattern report with
per-pattern live-detection design notes and follow-up-issue
recommendations to
docs/issue-1504/reports/implementation/behavior-metrics-2026-08-13-15.md.

## Why

Basis: issue #1504's own requirements — define the metric set, compute it
over existing ledgers for the named window, deliver a ranked report, and
name follow-up-issue criteria. The APPROVE token was already posted on the
issue (APPROVE issue-1504/implementation, author JiwonJung94, listed in
docs/specs/approvers.md) so phase 1 (survey + proposal) and phase 2 ran
in the same session.

Upstream: docs/issue-1504/proposals/behavior-metrics.md

## Acceptance verification

canonical: python3 -m pytest tests/test_behavior_metrics.py -v — this turn's run, fenced below.
acceptance: `python3 -m pytest tests/test_behavior_metrics.py -v` — result: PASS
```
tests/test_behavior_metrics.py::test_recheck_count_from_fixture_ledger PASSED [ 14%]
tests/test_behavior_metrics.py::test_recheck_count_distinguishes_different_subjects PASSED [ 28%]
tests/test_behavior_metrics.py::test_zero_commit_session_flagged PASSED  [ 42%]
tests/test_behavior_metrics.py::test_round_trip_counts_group_by_issue PASSED [ 57%]
tests/test_behavior_metrics.py::test_wait_poll_time_aggregates_per_issue PASSED [ 71%]
tests/test_behavior_metrics.py::test_extract_recheck_entries_reads_real_deviation_log PASSED [ 85%]
tests/test_behavior_metrics.py::test_extract_wait_poll_entries_reports_gap_not_derivable PASSED [100%]
7 passed in 0.04s
```
No SKIPPED lines above; the hand-typed count of 7 equals the pasted
summary's count.

canonical: python3 scripts/behavior_metrics.py --since 2026-08-13 --until 2026-08-16 — this turn's run, fenced below.
acceptance: `python3 scripts/behavior_metrics.py --since 2026-08-13 --until 2026-08-16` — result: PASS
```
(a) re-check keys with count>1: 1
(b) zero-commit implementation sessions: 1
(c) issues with round-trip artifacts: 97
(d) wait/poll seconds: None (not derivable: no runs/ or roster heartbeat history is git-tracked in this checkout)
```
Same numbers cited in the delivery report at
docs/issue-1504/reports/implementation/behavior-metrics-2026-08-13-15.md.

Per-acceptance-checklist mapping:
- Metrics report recorded with ledger-derived numbers for (a)-(d): met —
  see the report file above; metric (d) is reported as not derivable with
  the missing record named (per-session wait/poll event log), satisfying
  the acceptance's empty-state requirement rather than being silently
  dropped.
- The recheck-count-from-fixture test (fixture ledger, 3 re-checks of one
  unchanged subject, count 3): met, in the pasted pytest output above.
- The zero-commit-session-flagged test (0-commit implementation session
  flagged, 0-commit consult session not): met, in the pasted pytest
  output above.
- Follow-up-issue recommendation section present: met — report's
  "Follow-up-issue recommendations" section names pattern 1 as
  data-sufficient and patterns 2-4 as data-insufficient with the specific
  instrumentation each needs first.

## Rationale for deviations

The proposal named docs/issue-1504/reports/behavior-metrics-2026-08-13-15.md
as the report path. board-gate.sh's role-ownership check refuses an
implementation-branch write to docs/issue-1504/reports/*.md other than
implementation.md/implementation/** (contract v3 s11 — "belongs to
another role"), so the report was written to
docs/issue-1504/reports/implementation/behavior-metrics-2026-08-13-15.md
instead. Same content and requirement coverage; only the path moved one
level under the role's own subtree.

## What did not work

None.

## Open findings

None.

## Doc placement

- docs/issue-1504/reports/implementation/behavior-metrics-2026-08-13-15.md
  — benchmark/investigation numbers, placed per the doctrine ladder.
- No env var, config key, new dependency, or migration was introduced;
  no handbook update needed.
- No library/format choice or public-signature change over a named
  alternative beyond the one recorded in the phase-1 proposal's Rationale
  (docs/issue-1504/proposals/behavior-metrics.md); no
  docs/issue-1504/decisions/ entry needed.
