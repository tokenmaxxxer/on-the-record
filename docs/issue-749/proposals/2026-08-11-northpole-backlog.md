---
status: proposed
files:
  - docs/issue-749/reports/conformance-review.md
---

## Intent

Issue #749 asks to integrate the five landed dimension-gap audits
(issue-750 role-session behavior, issue-751 inter-agent comm, issue-752 core
judgment capability, issue-753 session-completion durability, issue-754
problem-resolution composition) into one ranked, deduplicated
northpole-conformance backlog over all 7 requirements in
`docs/specs/northpole.md`, with requirement #7 (default-on/plugin-only/
no-explicit-invocation reach) audited specifically using this session's own
directive surface as direct evidence.

## Constraints stated so far

- provenance: read — this is a read-only conformance-review audit; no code
  or gate changes.
- Write set: `docs/issue-749/**` only (this session's own record area).
- Never `gh pr merge`.
- Every requirement gets a MET/PARTIAL/GAP verdict; a requirement with no
  serving mechanism is recorded GAP, never omitted.
- Every PARTIAL/GAP is ranked (northpole-centrality x observed-failure-
  frequency) and names the responsible repo.
- Requirement #7 specifically audited for reach to a plain, non-orchestrator
  target session on plugin-install-alone.

## What will be done

Phase-1 research is complete:
`docs/issue-749/reports/conformance-review/survey.md` reads the five source
audits' `survey.md` files (none has a landed phase-2 record yet) plus
`docs/specs/northpole.md`, and produces a 17-row deduplicated, ranked
backlog table covering PARTIAL/GAP findings across all five audits, each row
naming the northpole requirement(s) blocked, the responsible repo, and a
one-line fix direction. It records requirements #2 and #6 as MET with no new
finding (not omitted), and classifies requirement #7 as PARTIAL — the
hook/directive delivery layer reaches a plain target session on install
alone (confirmed directly, this session being that instance), but the
gate/enforcement layer for real-wired verification (req #3) does not, per
issue-750's own audit finding.

Phase-2 (this proposal, on approval) writes the final conformance-review
record, `docs/issue-749/reports/conformance-review.md`, per role-handoff
contract v3 s19's required record shape: a per-requirement MET/PARTIAL/GAP
verdict table for all 7 northpole requirements, the full ranked backlog
(restating the survey's 17 rows), and the record's required fields (what was
done, why, upstream basis, kind, loop_state, open findings).

## Out of scope

- Fixing any backlog row — this audit only records and ranks; remediation is
  separate, role-appropriate follow-up work the ranking is meant to seed.
- Opening the fix issues the backlog rows are meant to lift into — deferred
  to whoever picks up the ranked backlog.
- Auditing whether any individual role's past judgment was substantively
  correct — that is issue-752's own explicit scope note, not this
  integration pass.

## How you will know it worked

`docs/issue-749/reports/conformance-review.md` exists, classifies all 7
northpole requirements MET/PARTIAL/GAP with file:line evidence (inherited
from the five source audits), and every PARTIAL/GAP entry is ranked and
names the responsible repo — matching issue #749's acceptance criteria
verbatim, including the requirement #7 special-attention clause.

## What did not work

- First draft of the survey cited three not-yet-existing forward-reference
  paths (`docs/issue-753/reports/architecture.md`, this proposal's own path,
  and the phase-2 record's own path) inside backticks —
  `record-claim-guard.sh`'s orphaned-path check refused all three as
  unreachable. Fixed by stating those paths in plain prose (no backticks)
  since they name files this audit itself has not yet created.
- The same draft tripped the bare-count-claim check on "lower frequency than
  rows 1/6" (digit-adjacent phrase, no `derived:` backing) — fixed by
  rewording to reference the rows by name instead of by number.
