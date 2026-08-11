---
status: proposed
files:
  - docs/issue-751/reports/architecture.md
---

## Intent

Issue #751 asks for a detailed, read-only audit of inter-agent communication
(consult #699, board record read paths, spawn-time context, PR-comment
relay) against the northpole requirements (#748), classifying each sub-area
MET/PARTIAL/GAP with file:line evidence, and ranking every PARTIAL/GAP by
northpole-centrality and observed-failure-frequency, naming the responsible
repo.

## Constraints stated so far

- Read-only: no code or mechanism changes, no new issues opened by this
  work itself.
- Write set is docs/issue-751/** only.
- Every PARTIAL/GAP must name the concrete missing mechanism, the repo it
  belongs in, and a rank.
- A sub-area with no serving mechanism is recorded GAP, never omitted.

## What will be done

Phase-1 research is complete: docs/issue-751/reports/architecture/survey.md
traces the four channels (consult, board, spawn-time task string, PR
comments) with file:line evidence and classifies each MET/PARTIAL/GAP,
listing four open findings (OF-1..OF-4).

Phase-2 (this proposal, on approval) writes the final architecture record,
docs/issue-751/reports/architecture.md, per role-handoff contract v3 s19's
required record shape: it restates the survey's MET/PARTIAL/GAP
classification, adds the rank (northpole-centrality x observed-failure-
frequency) and the responsible repo for each PARTIAL/GAP, and closes with
the record's required fields (what was done, why, upstream basis, kind,
loop_state, open findings).

## Out of scope

- Fixing any of the identified gaps (OF-1..OF-4) — this audit only records
  and ranks them; remediation is separate, role-appropriate follow-up work
  the ranking is meant to seed.
- Auditing the board's write side (how a role produces its own record) —
  #751 scopes this to how findings move *between* roles, not how one role
  authors its own.
- Auditing orchestrator-relaying or the board schema itself — #751 says
  "beyond the orchestrator relaying and the board", so this stays on
  consult/spawn-context/PR-comments plus how board *reads* (not writes)
  actually happen.

## How you will know it worked

docs/issue-751/reports/architecture.md exists, classifies all four sub-areas
MET/PARTIAL/GAP with file:line evidence, and every PARTIAL/GAP entry names
a concrete missing mechanism, its responsible repo, and a rank — matching
issue #751's acceptance criteria verbatim.

## What did not work

(none yet — appended live if something breaks during phase 2)
