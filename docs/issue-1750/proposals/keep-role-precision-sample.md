---
status: proposed
files:
  - docs/reports/keep-role-precision-sample.md
---

## Request

Issue #1750: sample-verify 20 of the 307 hooks the #1746 audit
(`docs/reports/rulebook-hook-audit.md`) classified `keep-role`, by fetching
each sampled hook's full script (not just its header comment) and
re-judging its classification, then report the resulting precision and
which threshold branch it triggers (<80% → full re-audit required before
phase 3; >=80% → the keep-role figure stands and phase 4 designs a carrier
for role-specific hooks).

## Constraints

- Sample exactly 20 rows, deterministically, by the issue's stated rule:
  every 15th keep-role row by report order (1-indexed among the 307
  keep-role rows), starting at index 1, wrapping if it overruns 307.
  No hand-picking.
- Each sample must be re-judged from its actual full script body (fetched
  live via `gh api`), not the header-comment excerpt the original audit
  used — the whole point of this issue is to check whether the
  header-comment-only method was reliable.
- Deliverable is exactly one file: `docs/reports/keep-role-precision-sample.md`.
  No other file changes.
- This is a report-writing/measurement task with no design decision open
  (design-research-skip: mechanical, assumptions-skip: mechanical, per the
  issue) — scouting is skipped (see survey.md's skip record).

## Rationale

Alternative considered and rejected: hand-select 20 "representative" or
"interesting-looking" keep-role rows (e.g. ones whose header comment is
`(see script; no header comment extracted)`, since those seem likeliest to
hide a misclassification) instead of a fixed-stride sample. Rejected
because the issue explicitly requires a rule that avoids hand-picking —
biasing the sample toward rows already suspected of being wrong would
inflate the measured error rate and make the resulting precision figure
unusable as an unbiased estimate of the full 307-row population, which is
exactly what phase 3's go/no-go decision needs. A fixed stride (every 15th)
costs nothing in rigor and is trivially reproducible by a third party
re-running the same `grep`/`awk` pipeline.

## What will be done

1. Recompute the 20 sampled row indices via the deterministic rule (already
   verified reproducible in survey.md).
2. For each sample, resolve its rulebook repo + hook file path, fetch the
   full script body live via `gh api`, and re-judge promote/keep-role/retire
   from that actual content against the audit's own stated classification
   rule (mechanism-vs-content test, including its stated exception for
   hooks that merely restate a role-handoff-contract-wide norm).
3. Write `docs/reports/keep-role-precision-sample.md` containing: the
   selection-rule statement and the 20 indices used; a 20-row table (hook
   identity, original class, re-judged class, one-line reason); the
   precision figure (agreed/20); the re-judged class distribution; and a
   conclusion section that states the precision figure and names the
   triggered threshold branch verbatim.

## Out of scope

- Acting on the triggered branch itself (running a full re-audit, or
  designing phase 4's carrier) — this issue only measures and reports;
  phases 3/4 are separate, later work.
- Re-judging any of the 307 rows outside the 20-sample.
- Changing `docs/reports/rulebook-hook-audit.md` itself.

## How you'll know it worked

- `docs/reports/keep-role-precision-sample.md` exists with a 20-row table,
  each row carrying original class, re-judged class, and a reason grounded
  in that row's actual fetched script content.
- The report's conclusion section states the computed precision (X/20) and
  names which of the two threshold branches (<80% full re-audit / >=80%
  figure stands) it triggers.
