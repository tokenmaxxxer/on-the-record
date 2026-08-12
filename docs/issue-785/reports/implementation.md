---
code_under_review:
  - docs/issue-785/proposals/conditional-phase-split.md
  - docs/issue-785/reports/implementation/survey.md
  - docs/issue-785/reports/implementation/hunt-conditional-phase-split.md
type: docs
breaking: false
verdict: cross-repo-blocked
loop_state: scope-undeclared
---

# Implementation record: issue-785

## What was done

canonical: docs/issue-785/proposals/conditional-phase-split.md (build-plan
section, items 1-2)
The merged phase-1 proposal names the fix as two files in
`tokenmaxxxer/tokenmaxxxer-core`: `core/hooks/directive.sh` and
`core/hooks/approval-gate.sh`. Neither file exists in this repo.

canonical: derived: `cd /home/jwjung/tokenmaxxxer/tokenmaxxxer-core && grep -n "TWO PHASE\|approved.upstream\|APPROVED_UPSTREAM\|single-phase\|delivery-only" core/hooks/directive.sh core/hooks/approval-gate.sh`
```
core/hooks/directive.sh:73:- Work the PR in TWO PHASES (contract v3 s19). Phase 1, before any
```
Only the unconditional line matched; no conditional-signal string exists
in either file at HEAD `a8b6c9d` of the upstream clone. This is this
record's live-fire proof — the defect reproduces at this session's
current-state check.

canonical: spawn.py:984-1013 (read this session)
This repo's own phase gate (`require_acceptance_gate`, using
`gates/ci.py` function `_approved_roles_on_issue`) branches on whether
this same subject already carries a human `APPROVE` comment.

canonical: spawn.py:984-1013 (read this session)
That mechanism has no signal for "an upstream, different subject's
proposal already merged" — the gap the issue names lives in
`tokenmaxxxer-core`'s directive and gate files, not `spawn.py`.

canonical: docs/issue-785/proposals/conditional-phase-split.md (Out of
scope section)
The proposal already scoped code changes outside this subject's own
`files:` (the two phase-1 docs) as out of scope, since `on-the-record`
does not host the changed mechanism.

Role-handoff contract v3 confines this session's writes to this issue's
branch and tree — `on-the-record` only — so no file in
`tokenmaxxxer-core` could be edited from here regardless of scope. This
record and the live-fire re-check above are the only deliverable
available to this subject in this repository.

## Why

canonical: docs/issue-785/proposals/conditional-phase-split.md
(Rationale section)
The proposal's design is not in question; only its landing site is
outside this repo. Re-running the check live, rather than trusting the
phase-1 survey's description, is what phase-2 execution judgment adds
here.

## Upstream

canonical: PR #790 (`gh pr view 790`, read this session)
docs/issue-785/proposals/conditional-phase-split.md, merged.

## What did not work

None.

## Open findings

canonical: derived: `cd /home/jwjung/tokenmaxxxer/tokenmaxxxer-core && grep -n "TWO PHASE\|approved.upstream\|APPROVED_UPSTREAM\|single-phase\|delivery-only" core/hooks/directive.sh core/hooks/approval-gate.sh`
(same command as above)
The structural fix in `tokenmaxxxer/tokenmaxxxer-core` does not exist at
that repo's checked HEAD. A new subject opened directly against
`tokenmaxxxer-core` is needed — this `on-the-record` subject cannot open
or land a PR in that repository.

## Next steps

canonical: docs/issue-785/proposals/conditional-phase-split.md
(build-plan section, items 1, 2, 4)
Open a subject in `tokenmaxxxer/tokenmaxxxer-core` implementing the
proposal's build-plan items 1-2 (directive.sh, approval-gate.sh) plus
its acceptance test (item 4). Afterward, re-run this record's live-fire
grep command against the new HEAD to check whether the directive body
and gate behavior now branch on the signal.

## Resolution path

canonical: docs/issue-785/proposals/conditional-phase-split.md
(build-plan section)
Implement `core/hooks/directive.sh` and `core/hooks/approval-gate.sh` in
`tokenmaxxxer/tokenmaxxxer-core` per the proposal, add the paired
acceptance test, land it, then re-run this record's live-fire grep
command against the new HEAD.
