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

- 2026-08-25: operator restated the same standing systemic/no-side-effects
  acceptance bar on issue #2285 (role retirement stage 2), applying it
  to that issue's delivery and its review specifically — same wording as
  the #2278 entry above, reapplied per-issue rather than superseding it.
  Source: issue #2285 comment by JiwonJung94, 2026-08-25T01:27:57Z
  ("Operator-frozen constraint (2026-08-25), applies to this issue's
  delivery and its review... Reviewers grade against this: a delivery
  that works here but adds overhead, a new contention point, or
  consumer-visible residue elsewhere is NOT met.").
