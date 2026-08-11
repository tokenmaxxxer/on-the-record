---
status: proposed
files:
  - docs/issue-752/reports/architecture.md
---

# Audit C: core judgment capability (#752)

Intent: read-only audit of where the core lets agents genuinely JUDGE (weigh options, commit,
record the reasoning) versus only produce artifacts — across produce-vs-decide routing, consult
(#699) as a judgment channel, rulebook shaping of judgment, risk-classification/delegated-
judgment gates, and any missing core primitive for recorded reasoned judgment.

Constraints stated so far: read-only (`provenance: read` in the issue's acceptance section) —
no code/gate changes in this pass; findings must classify MET/PARTIAL/GAP per sub-area with
repo+file:line evidence; every PARTIAL/GAP must name the concrete missing mechanism, its owning
repo, and a rank by northpole-centrality and observed-failure-frequency; a sub-area with no
serving mechanism is recorded GAP, never omitted.

What will be done: the phase-1 survey at
`docs/issue-752/reports/architecture/survey.md` already carries the full findings (5 sub-areas,
each with file:line evidence, MET/PARTIAL/GAP verdict, missing-mechanism + owning-repo note
where applicable, and a cross-area rank). On APPROVE, that survey is synthesized into the
phase-2 record `docs/issue-752/reports/architecture.md` per contract v3 s19 — no new research,
just promotion/formatting of the already-gathered evidence into the record shape.

Out of scope: any code change, gate change, or new schema field — this issue is audit-only.
Designing the concrete decision-record primitive (§5 of the survey) is hand-off work for a
follow-up issue, not this one.

How you'll know it worked: `docs/issue-752/reports/architecture.md` exists after phase-2,
classifies all 5 sub-areas MET/PARTIAL/GAP with file:line evidence, ranks every PARTIAL/GAP, and
the record passes `on-the-record/hooks/record-claim-guard.sh` (no bare counts, no dangling
`docs/issue-752` path references, `unverifiable:` lines carry reasons).

## What did not work

- First draft of the survey used backtick-wrapped `path:line-range` citations (e.g.
  `` `file.sh:56-57` ``); `record-claim-guard.sh`'s orphaned-path check resolves the full
  backtick span as a literal path, so the `:56-57` suffix broke every citation. Fixed by closing
  the backtick before the line-range suffix (`` `file.sh` ``:56-57).
- Two lines tripped the bare-count-claim check on incidental digit+noun adjacency ("phase-2
  work", "5 items above") though they were not asserting an unverified count. Fixed by rewording
  rather than adding a `derived:` tag, since no command output backs a stylistic phrase.

Proposal: docs/issue-752/proposals/2026-08-11-core-judgment-capability-audit.md
