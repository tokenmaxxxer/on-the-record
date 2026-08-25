---
issue: 2409
role: execution-observation
---

# issue-2409 — execution-observation current-state survey

## Scout skip record

Scouting is skipped for this proposal round: the spec leaves no design
decision open (scout-directive's second mandatory skip condition).
canonical: `roles/specs/execution-observation.spec.json`, read this
session — its own `gate_c_status` field states "N/A — mechanical
aggregation, not investigative finding... there is no discretionary
finding step to ground a lens-based method for," and its recomputation
rule fixes the verdict method (worst case across cited results)
independent of any judgment call this proposal round could make
instead. There is no exemplar field, product category, or
comparable-system pattern for this role's own output shape to scout
against — the output shape (EARL 1.0 subject/test/result/assertedBy) is
itself fixed by the spec file, not a design choice open to this round.

## Current state: issue #2409 and its implementation branch

canonical: `gh issue view 2409`, read this session — the issue measures
three waste classes across 177 real role-session logs (62% of Bash
calls exploratory, 6.9 hook refusals/session, 105 `spawn.py` +96
own-record redundant re-reads) and asks for a stated mechanism per
class plus honest before/after measurement on 5 real issues, with an
explicit non-goal: no verification/record/observer step may be thinned
to buy speed.

canonical: `git log --oneline` on a worktree fetched from PR #2416's
head, run this session — three commits landed on branch
`issue-2409/implementation`, none yet merged to main: `f9f8041f` (code
— `directive_assembly.py`/`spawn.py` additions, `scripts/related_files.py`,
`scripts/session_waste_metrics.py`, four touched/new test files),
`1736cc4b` (phase-2 delivery: the implementation record itself, path
`docs/issue-2409/reports/implementation.md` (untracked in this tree —
lives only on branch `issue-2409/implementation`/PR #2416)), `02aba0a9`
(a self-logged deviation-log append for the full-suite skip and
after-measurement scope, per this repo's "What did not work"
convention).

canonical: `gh pr view 2416 --json state,mergeable,author` run this
session — PR #2416 (`issue-2409/implementation`) is open, author
JiwonJung94, mergeable.

canonical: `gh issue view 2409 --comments` run this session — no
comment whose entire body is exactly an APPROVE token for either the
implementation or this execution-observation role appears; the two
comments present are the operator's frozen-constraint/speed-constraint
comment and the automated `[watch]` spawn notification for PR #2416.
This round has no phase-2 approval yet for `issue-2409/execution-observation`
— confirmed live by the `approval-gate.sh` refusal this session hit
this turn on its first attempted write to this role's own record path
(committed on this branch as an empty skeleton already, named below)
before this survey was drafted — exactly the mechanism this role's own
phase-1/phase-2 split exists to enforce.

## This role's own record state

The pre-existing skeleton at
`docs/issue-2409/reports/execution-observation.md` (committed on this
branch, issue #2135's convention) carries empty
`subject`/`test`/`result`/`assertedBy` frontmatter and unfilled section
bodies. canonical: `find docs -path "*/issue-2409/reports/*" -maxdepth
3`, run this session — output: `docs/issue-2409/reports` (dir) and
`docs/issue-2409/reports/execution-observation.md` only. Neither
`docs/issue-2409/proposals/` (untracked in this tree) nor
`docs/issue-2409/reports/execution-observation/` (untracked in this
tree) existed on this branch before this round.

## Write surfaces this round expects to touch

- `docs/issue-2409/reports/execution-observation/survey.md` (untracked
  in this tree — this file, landing in this round's own commit)
- `docs/issue-2409/proposals/execution-observation.md` (untracked in
  this tree — phase 1, landing in this round's own commit)
- `docs/issue-2409/reports/execution-observation.md` (phase 2, once
  approved — this role's sole `write_scope` entry per
  `roles/specs/execution-observation.spec.json`; already committed on
  this branch as the empty skeleton, to be filled once phase 2 opens)

## Precedent read

canonical: `docs/issue-2165/proposals/execution-observation.md` and
`docs/issue-2165/reports/execution-observation/survey.md` (both
committed, this tree), read this session — the same role's own phase-1
round for a prior issue: a `files:` frontmatter list naming the survey/
proposal/target-record paths, a `## Request` section stating intent, a
`## Constraints` section, a `## Rationale` section naming one rejected
alternative and the reason for rejecting it, a build-steps section, a
`## Out of scope` section, and a final section stating the observable
signal that the round succeeded.

canonical: `docs/issue-2393/reports/execution-observation.md`
(committed, this tree), read this session — the most directly
comparable prior delivery in this same `spawn.py`/directive-diet
lineage (independent worktree checkout, before/after reproduction from
a fresh scratch state, an Open finding about a canonical checkout not
yet containing the observed fix). This round's phase-2 approach, once
approved, follows the same method: independent worktree, re-execution
of reproducible claims, direct diff/source-read verification of wiring
claims, honest disclosure of what could not be independently
re-measured.
