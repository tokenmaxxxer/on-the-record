# Priorities

Append-only, newest entry last.

- 2026-08-12: #745 is deliberately deprioritized (`infrastructure/no-direct-requirement`)
  behind #1110, the 7-scenario harness re-measurement, and the user's
  fresh-session E2E test. Source: #745 close-out comment by JiwonJung94,
  2026-08-12 ("priority-record (2026-08-12 close-out): this issue is
  deliberately deprioritized (`infrastructure/no-direct-requirement`)
  behind #1110, the 7-scenario harness re-measurement, and the user's
  fresh-session E2E test.").

- 2026-08-14: operator lifted the report-only hold on defects #1461 and #1462
  and set the resumption order: fix #1461 (PR-base guard, action-layer risk)
  and #1462 (ps state-row rendering) first, then clear the 6 open record PRs
  (#1460/#1457/#1455/#1454/#1256/#1243), then resume the role-realization
  drive (next role, 22/43). Source: user directive in orchestration session,
  2026-08-14 ("응 둘다고쳐" following the recommended order #1461 → open PRs
  → role resumption, #1462 after).

- 2026-08-25: standing bar for any fix + its review going forward — a
  delivery must hold systemically for every session that installs
  on-the-record and works against any target repo, not just the
  self-hosted checkout, and must land without side effects: no added
  per-spawn overhead or steady-state load, no new conflict surfaces
  (append-log or otherwise), no stall/deadlock modes, no
  consumer-tree pollution. Reviewers grade against this directly; an
  unavoidable trade-off must be measured and stated in the record, not
  discovered later. Source: issue #2278 comment issuecomment-5403812868
  by JiwonJung94, 2026-08-25 ("Operator-frozen constraint (2026-08-25),
  applies to this issue's delivery and its review... Reviewers grade
  against this: a delivery that works here but adds overhead, a new
  contention point, or consumer-visible residue elsewhere is NOT met.").
- 2026-08-25: operator froze a standing acceptance bar for issue #2278 and
  its review (stated as applying to "this issue's delivery and its
  review", worded as a general grading rule rather than issue-2278-only):
  a fix must hold systemically for every session installing on-the-record
  against any target repo, not just the self-hosted checkout, and must
  land with no added per-spawn/steady-state overhead, no new conflict
  surfaces, no stall/deadlock modes, and no consumer-tree pollution — an
  unavoidable trade-off must be measured and stated in the record, not
  discovered later. Source: issue #2278 comment by JiwonJung94,
  2026-08-25T01:28:13Z ("Operator-frozen constraint (2026-08-25), applies
  to this issue's delivery and its review").

- 2026-08-25: operator froze a load-reduction acceptance bar for issue
  #2315's gh_delta 304-classification fix, worded as systemic rather than
  issue-2315-only: the fix must reduce load by construction for every
  consumer session, not just fix the classification, and that reduction
  must be measured and stated in the delivery's record rather than
  assumed. Source: issue #2315 body, read 2026-08-25 ("Operator-frozen
  constraint applies (2026-08-25): systemic for every consumer session;
  the fix REDUCES load by construction — state that measured in the
  record.").

- 2026-08-25: operator set task latency as an ongoing audit category, not
  a one-off fix: unnecessary sequencing baked into the core procedure
  (both orchestrator spawn ordering and spawn.py/gates' own internal
  steps) is worth continuing to look for, and the audit scope is wider
  than "could this run concurrently" — a step may also not need to run
  in full on every spawn at all (skip/narrow it for roles that don't
  touch the surface, cache its result across spawns in the same
  session/short window, or drop it if an earlier phase already did the
  work). Framed as "core is too heavy right now" — the fix may be
  trimming, not just parallelizing. Two standing constraints apply to any
  such fix and its review going forward (already reconciled into issue
  #2382's delivery, consistent with the #2278/#2315 entries above): it
  must hold for every session/target repo, not just the self-hosted
  checkout, with no added per-spawn overhead, no new conflict surfaces,
  no stall/deadlock modes, no consumer-tree pollution; and the
  recording/audit-trail procedure itself (issue→spawn→PR structure,
  board records, both observer roles, verify-at-landing evidence,
  consult-trace logging) stays exactly as-is — only incidental cost is in
  scope, thinning the record itself is not. Source: issue #2382 body and
  its two comments (issuecomment-5407296989, issuecomment-5407303268) by
  JiwonJung94, 2026-08-25.

- 2026-08-25: operator applied the same standing systemic/no-side-effects
  bar to issue #2409's 5x-speed-target work, plus an explicit tie-breaker
  for this recurring speed-vs-record tension: cut overhead, but the
  recording/audit-trail procedure (issue→spawn→PR, both observer roles,
  verify-at-landing evidence, consult-trace) stays exactly as-is — a
  proposed change that would thin the record to save time must be
  rejected and the time found elsewhere instead. Source: issue #2409
  body, comment by JiwonJung94, 2026-08-25 ("Operator-frozen constraint
  (2026-08-25): must hold systemically for every session that installs
  on-the-record against any target repo... Speed constraint (operator,
  this session): cut the overhead, but the recording/audit-trail
  procedure stays exactly as-is... If a proposed change would thin the
  record to save time, reject it and find the time elsewhere.").
- 2026-08-25: operator standing directive, restated across #2414 and its
  successor #2415: measure a defect/friction rate before adding any new
  gate or authoring/landing check, and adding nothing is an acceptable,
  explicitly sanctioned delivery when the measured rate doesn't justify
  it — "do not add a gate to be seen doing something." When a check IS
  justified, #2415 additionally warns against the specific failure mode
  of appending one more rule per incident onto a shared format document
  (the pattern that produced acceptance-format.md's 5-rule, 73-line
  accretion) rather than periodically re-deriving the format from first
  principles ("what an Acceptance section is FOR") and judging existing
  rules keep/merge/drop against that. Any authoring-time or landing-time
  check must be measured, not asserted, to not lengthen the normal path
  for work that doesn't need it — verified against the real open-issue
  backlog or closed-issue corpus, not argued from design intent alone.
  Source: issue #2414 body ("If measurement shows this is infrequent
  enough that the observer layer catching it is the cheaper equilibrium,
  the correct delivery is to say so and add nothing... Do not add a gate
  to be seen doing something") and issue #2415 body, both read 2026-08-25
  ("The operator's standing directive is to CUT overhead. A redesign
  that adds authoring burden to every issue... is a failure even if it
  prevents defects" / "Nobody has ever asked what an Acceptance section
  is for and derived the format from that... that is how the document
  got here").

- 2026-08-26: operator scoped follow-up performance/waste-reduction work
  deliberately narrow after #2409's corpus-scale claim failed conformance
  review: the next round (#2467) explicitly excludes corpus-scale
  hit-rate claims, production cache-eviction policy, and cross-session
  persistence, asking instead for a small, cheaply-verifiable before/after
  on real existing logs (or, if a precondition check fails, a clean
  negative finding with no further build). Applies going forward to any
  similar waste-reduction issue: prefer a narrow, directly-verifiable
  claim over a broad corpus-wide one, and treat "the precondition doesn't
  hold, so nothing was built" as a complete, valid outcome rather than a
  shortfall to compensate for. Source: issue #2467 body ("Scoped
  deliberately narrow this round (per operator instruction, after #2409's
  corpus-scale claim failed conformance-review): a small,
  cheaply-verifiable before/after on real existing logs, not a
  corpus-wide 5x-style claim."), read 2026-08-26.
