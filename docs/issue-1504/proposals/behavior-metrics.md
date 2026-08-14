---
status: approved
files:
  - scripts/behavior_metrics.py
  - tests/test_behavior_metrics.py
  - docs/issue-1504/reports/behavior-metrics-2026-08-13-15.md
---

## Request

Build a re-runnable computation of four agent-behavior efficiency metrics —
re-check count per unchanged subject, zero-commit session terminations,
round-trips per landed change, and wait/poll time — over the existing
git-tracked ledgers (deviation-log.md, implementation.md, PR history) for
the 2026-08-13..15 drives, and deliver a ranked waste-pattern report with
follow-up-issue recommendations. Instrumentation only; no caps or policy
changes (that is a deliberately separate follow-up issue per the issue's
own scope boundary).

## Constraints

- Read-only over existing records; no new runtime hooks.
- A metric not derivable from existing records must be reported as such
  with the missing record named, not silently dropped (issue's stated
  empty-state requirement).
- Script committed under scripts/ and re-runnable; tests as fixture-based
  unit tests, not full-repo integration tests, so they run in CI without a
  live git history dependency.

## Rationale

Considered extending ledger/collect.py (already walks docs/issue-*/reports/
git history) instead of a new script. Rejected: collect.py's model is
Present/Surface/Absent/Incorrect verdict deltas on review.md specifically,
a different record shape and a different question from #1504's four
metrics (behavioral waste counts, not review-value deltas). A new script
keeps the two metric sets independently evolvable and keeps this issue's
write set isolated, per the survey (docs/issue-1504/reports/implementation/survey.md).

## What will be done

- scripts/behavior_metrics.py: pure functions for each of the four metrics
  operating on parsed ledger-entry dicts (testable without git), plus a
  git/gh-backed extraction layer that builds those entries from
  deviation-log.md, implementation.md, and `gh pr list` for a given date
  range, plus a CLI (`python3 scripts/behavior_metrics.py --since ... --until
  ...`) re-runnable against the current repo state.
- tests/test_behavior_metrics.py: fixture-based tests, including the two
  acceptance-named tests
  (test_recheck_count_from_fixture_ledger, test_zero_commit_session_flagged).
- docs/issue-1504/reports/behavior-metrics-2026-08-13-15.md: the metrics
  report computed over the 2026-08-13..15 window, each metric citing the
  ledger/log files it was computed from, ranked waste patterns with cost
  estimates, a "what record would detect this live" design section per
  pattern, and the follow-up-issue recommendation section.

## Out of scope

- Enforcement, caps, or back-off policy changes (explicitly deferred by
  the issue to a follow-up).
- New runtime instrumentation/hooks to capture metric (d) live — this
  issue is read-only over what already exists; if (d) is not derivable,
  that gap itself is the requirement-3 deliverable (design only).
- Retroactive recovery of the #1490 zero-commit anecdote specifically,
  since no committed artifact preserves it (survey finding).

## How you'll know it worked

- `python3 -m pytest tests/test_behavior_metrics.py -v` passes, including
  the two acceptance-named tests.
- `python3 scripts/behavior_metrics.py --since 2026-08-13 --until 2026-08-16`
  runs against the live repo and produces the same numbers cited in the
  delivery report.
- The report names, for each of (a)-(d), either a computed number with its
  source ledger/log files, or an explicit "not derivable, missing record:
  X" line.
