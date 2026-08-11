---
status: proposed
files:
  - docs/issue-750/reports/architecture.md
---

## Intent

Issue #750 asks for a detailed, read-only audit of ROLE-SESSION BEHAVIOR
(spawn.py, the core/warrant/implementation directives, and the 2026-08-11
watch/ps-watcher subsystem evidence) against the 7 northpole requirements
(#748), covering: directive vs. observed behavior; genuine judgment vs.
mechanical artifact production; real-wired verification (req #3); record-
authoring completeness (req #2); and the two-phase proposal/delivery flow.
Every sub-area must be classified MET/PARTIAL/GAP with file:line evidence,
and every PARTIAL/GAP ranked by northpole-centrality and observed-failure-
frequency, naming the responsible repo.

## Constraints stated so far

- Read-only, provenance: read — no code or mechanism changes.
- Write set is docs/issue-750/** only.
- A sub-area with no serving mechanism is recorded GAP, never omitted.
- Every PARTIAL/GAP must name the concrete missing mechanism, its
  responsible repo, and a rank.

## What will be done

Phase-1 research is complete:
docs/issue-750/reports/architecture/survey.md classifies five sub-areas
(A: directive vs. observed completion signal, B: genuine judgment vs.
mechanical artifact, C: real-wired verification, D: watch/ps subsystem
reliability, E: two-phase flow) against file:line evidence gathered from
spawn.py (both the canonical muster copy and this tree's own stale
checkout), on-the-record/hooks/delegated-judgment-gate.sh,
gates/reexecution_gate.py, gates/landing_readiness.py, and the four dated
2026-08-07/08/09 watcher hunt reports. Four sub-areas classify
PARTIAL/GAP with a rank (C highest, then D, B, A); one (E) classifies
MET. Five open findings (OF-1..OF-5) are listed.

Phase-2 (this proposal, on approval) writes the final architecture
record, docs/issue-750/reports/architecture.md, per role-handoff contract
v3 s19's required record shape: it restates the survey's MET/PARTIAL/GAP
classification and ranking, and closes with the record's required fields
(what was done, why, upstream basis, kind, loop_state, open findings).

## Out of scope

- Fixing any of the identified gaps (OF-1..OF-5) — this audit only
  records and ranks them; remediation is separate, role-appropriate
  follow-up work the ranking is meant to seed.
- Auditing whether a role's judgment is *correct* in content (that's
  audit C, per issue #750's own note "ties to audit C") — this audit
  only establishes whether a mechanism exists to check genuineness at
  all, not whether any specific past judgment was right or wrong.
- Any live/real-wired execution of spawn.py or the watch subsystem —
  this is a static read-only audit of the mechanisms as written.

## How you will know it worked

docs/issue-750/reports/architecture.md exists, classifies all five
sub-areas MET/PARTIAL/GAP with file:line evidence, and every PARTIAL/GAP
entry names a concrete missing mechanism, its responsible repo, and a
rank — matching issue #750's acceptance criteria verbatim.

## What did not work

- record-claim-guard.sh's orphaned-path check resolves a backtick-quoted
  string literally, including any trailing `:line-range` suffix, against
  the working tree. Citing evidence as `` `path:1463-1486` `` always
  fails even when `path` exists, because the literal string
  `path:1463-1486` is never itself a file. Fixed by keeping line numbers
  in prose outside the backticks (`` `path` `` lines N-M) throughout the
  survey and this record.
