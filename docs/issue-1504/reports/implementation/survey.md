# Survey — issue #1504 (agent-behavior efficiency instrumentation)

## Current-state findings

canonical: `ls ledger` (this turn) — `ledger/collect.py` already walks git
history of `docs/issue-*/reports/review.md`, comparing successive revisions'
`verdict:` counts to derive an "unresolved" delta. It is the closest
existing precedent for a git-history-derived behavioral metric in this repo,
but it measures review acceptance, not the four metrics #1504 asks for.

canonical: `find . -maxdepth 1 -type d` (this turn) — no `runs` or
`roster*.json` directory exists in this checkout. Session-level wait/poll
timing and live roster state are runtime-only and not git-tracked; metric
(d) (wait/poll time attributable to blocking sessions) has no ledger to
compute from in this repo as checked out. This is itself a finding for the
follow-up-issue requirement: metric (d) is not derivable from existing
records and must be named as a gap.

canonical: `grep -rn "recheck\|re-check\|재확인" docs/issue-*/reports/*/deviation-log.md docs/issue-*/reports/deviation-log.md | grep -oP "docs/issue-\d+" | sort | uniq -c | sort -rn` (this turn) —
issue-1163's deviation logs account for the large majority of re-check
mentions in the repo (the PR #1489 conformance-review loop the issue
names); issue-1199 contributes one. This confirms deviation-log.md entries
are the right source for metric (a):
`docs/issue-1163/reports/conformance-review/deviation-log.md` line 3 reads
"재확인 this turn (4th re-check)" and its sibling entries carry the same
pattern of a numbered re-check against an unchanged blocker.

canonical: `git log --since="2026-08-13T00:00:00" --until="2026-08-16T00:00:00" --name-only --format="COMMIT|%H|%aI" -- 'docs/issue-*/reports/*'` (this turn) —
this window has a large number of commits touching `docs/issue-*/reports/*`
paths, giving metrics (a)-(c) real data to compute over (fenced
reproduction included in the delivery report).

canonical: `gh pr list --state merged --search "merged:2026-08-13..2026-08-15" --limit 200 --json number,title,mergedAt` (this turn) —
merged PRs in the window (result page-capped at 200; true count may exceed
the page limit) are usable as the "landed change" denominator for metric
(c) (round-trips per landed change).

canonical: `docs/issue-1163/reports/conformance-review/deviation-log.md`
(read this turn) — entries carry an explicit `filed` marker and a
`canonical:` line each turn even when no new work landed, so 0-progress
turns are distinguishable from progress turns by grepping for "no new work
was possible" / re-check phrasing, without needing session-internal state.

canonical: `find docs/issue-1490 -type f` (this turn) — issue #1490's own
tree (`docs/issue-1490/proposals/parallel-test-suite.md`,
`docs/issue-1490/reports/implementation/survey.md`) has no implementation.md
delivery record and no deviation-log entry describing a 0-commit
termination; the anecdote #1504 cites (the first phase-2 attempt that
terminated with 0 commits) is not present as a committed artifact in this
checkout — it is runtime/roster history that was not preserved to git.
Metric (b) is therefore computed generically from whatever
implementation.md/deviation-log.md records DO exist in the window, not
from that specific anecdote; the anecdote itself is named in the delivery
report as an example of the same gap noted for metric (d).

## Write set

- scripts/behavior_metrics.py (new) — the re-runnable computation script.
- tests/test_behavior_metrics.py (new) — fixture-based unit tests for the
  acceptance-named test IDs.
- docs/issue-1504/reports/behavior-metrics-2026-08-13-15.md (new) — the
  ranked waste-pattern report with per-pattern cost estimates and the
  follow-up-issue recommendation section.

## Alternatives considered

Extending ledger/collect.py in place (it already walks report-file git
history) vs. a new standalone script. Rejected extending it:
ledger/collect.py's model is Present/Surface/Absent/Incorrect verdict
deltas on review.md specifically; #1504's four metrics span
deviation-log.md, implementation.md, and PR history, a different record
shape and a different question ("did behavior waste time" vs "did review
land value"). Bolting both onto one file would couple two
independently-evolving metric sets; a new script under scripts/ keeps the
write set isolated and re-runnable on its own.
