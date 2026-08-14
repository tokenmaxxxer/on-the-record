---
status: proposed
files:
  - performance-engineering-checklist/checklist.md  # in tokenmaxxxer/performance-engineering-rulebook
---

# Proposal: fold performance-engineering tool-landscape learnings into the rulebook checklist

## Intent

Per issue-1199: survey the tools performance-engineering practitioners
most rely on, and fold what those tools' design moves teach into the
role's own rulebook — as additive authoring-checklist rules, not a tool
catalog. Evidence trail: docs/issue-1199/reports/performance-engineering.md
and docs/issue-1199/reports/performance-engineering/scout-brief.md.

## Numeric SLO

This unit is a documentation-only checklist edit, not a load test, so no
live latency/throughput/error-rate SLO applies to the edit itself; the
completeness budget it must clear is stated as: gaps_closed >= 3 (of 3
identified checklist gaps: workload staged-ramp/load-model declaration,
bottleneck profiling-artifact linkage, repro repeated-run variance).
For traceability to this role's own decision line, the SLO facet this
checklist item enforces on FUTURE phase-2 records is restated verbatim
from checklist.md's own phase-1 wording: SLO stated as a numeric
threshold with unit and comparator, e.g. p99 < 250ms or error rate <
0.1%.

## Hypothesis

Falsifiable hypothesis, grounded in the scout brief's read of the
current checklist text (docs/issue-1199/reports/performance-engineering/scout-brief.md
"Gap line" section): the checklist's workload-characterization,
bottleneck-evidence-linkage, and repro-info items currently omit a
staged-ramp/load-model field, a profiling-artifact field, and a
repeated-run-variance field respectively — if this hypothesis is wrong,
re-reading checklist.md after this edit would show those three fields
already present before the edit, which the scout brief's direct read did
not find.

## Method

Method named: this is a documentation fold-in, not a live measurement,
so no USE/RED/Golden-Signals run applies to the proposal work itself —
the method being encoded is USE-method discipline (root-cause,
resource-focused evidence) and RED/Golden-Signals-style percentile
framing, which the checklist's added fields require future phase-2
records to supply. Tied to this role's `YOU DECIDE: 부하/지연 목표를
만족하는가` line: a bottleneck claim or a workload characterization that
skips these fields cannot support a defensible verdict on that decision.

## Workload characterization

No live workload is exercised by this documentation change (concurrency
level: n/a — no request traffic generated; request/transaction mix: n/a;
ramp-up profile: n/a). The workload-characterization *field being added*
to the checklist is itself what future phase-2 records must state:
concurrency level, request/transaction mix, and a staged ramp-up/
sustain/ramp-down profile, plus whether load was generated at a fixed
rate independent of response time or gated on prior-response completion.

## Premortem

Blast-radius limit: change is scoped to one file
(performance-engineering-checklist/checklist.md) in one external repo
(tokenmaxxxer/performance-engineering-rulebook); the checklist is
explicitly non-enforcing ("reading aid, not an enforcement mechanism"
per its own header), so a bad edit cannot block any future write the way
a gate script could. Killswitch: none needed — the checklist has no
runtime effect to disable. Rollback: `git revert` the single commit on
branch `issue-1199/performance-engineering` in the rulebook repo, or
edit checklist.md again in a follow-up commit.

## Evidence citation

Every external claim in the scout brief and this proposal carries a
fetched source or is labeled an assumption; full source list:
docs/issue-1199/reports/performance-engineering/scout-brief.md's
"Sources" section (10 tool repos + 3 doc pages, all fetched this
session).

## What will be done

Edit `performance-engineering-checklist/checklist.md` in the
`tokenmaxxxer/performance-engineering-rulebook` repo, on branch
`issue-1199/performance-engineering`, adding three fields (derived from
the scout brief's design moves 1-4, no tool name in the added text):

1. Extend the phase-1 **Workload characterization** item: require a
   staged profile (ramp-up/sustain/ramp-down, not a single number) and
   an explicit statement of whether load was generated at a fixed rate
   independent of response time, or gated on prior-response completion.
2. Extend the phase-2 **Bottleneck-evidence linkage** item: require that
   a named bottleneck point at a profiling artifact (a stack-sample or
   flamegraph reference), not percentile/measurement numbers alone.
3. Extend the phase-2 **Repro info** item: require repeated-run variance
   (more than one run, with the spread reported), not a single-run
   number.

## Out of scope

- Editing `roles/specs/performance-engineering.spec.json` or any gate
  script — the fold-in is checklist prose only.
- Editing `operational-playbook.md` (issue-1174's separate program).
- Any change to the on-the-record repo's own gates/tests.

## How you'll know it worked

The rulebook repo's checklist.md carries the three additive fields, each
traceable (via this proposal and the scout brief) to a specific
tool-family design move, with no tool name inside checklist.md itself;
the rulebook-repo branch is pushed and this issue's phase-2 record cites
the resulting commit.
