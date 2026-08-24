---
status: proposed
files:
  - docs/issue-2208/reports/execution-observation/survey.md
  - docs/issue-2208/proposals/execution-observation-record.md
  - docs/issue-2208/reports/execution-observation.md
---

## Request

Fill in the pre-written skeleton at
`docs/issue-2208/reports/execution-observation.md` with an
execution-observation record for issue #2208: what
`issue-2208/implementation` (PR #2218, currently open, not yet merged)
delivered against issue #2208's own three acceptance checks, and
independently re-executed evidence for each — not a re-statement of the
implementation role's own reported numbers.

## Constraints

No code path may be touched by this role — only the record files listed
above. The record's frontmatter must carry the fields its own skeleton
already declares (`issue`, `role`, `loop_state`, `upstream`, `subject`,
`test`, `result`, `assertedBy`) and set `result:` from this session's
own independently re-executed evidence, per `roles/specs/execution-observation.spec.json`'s
worst-case-recomputation rule. `approval-gate.sh` (confirmed this
session by a `Bash git show` denial on a `docs/issue-2208/` path, logged
in the survey's "Write surface" section) mechanically requires a posted
`APPROVE issue-2208/execution-observation` comment, or `CORE_BUILD_NOW=1`,
before the phase-2 write to `docs/issue-2208/reports/execution-observation.md`
is allowed — neither is present (survey, "PR #2218 and issue #2208's
own state"). Unlike the issue-2204 precedent, issue #2208 is not closed
and PR #2218 has not merged (survey, same section), so no
OBSERVER_ROLES closed-issue exemption question even arises here — the
sole blocker is the missing phase-2 approval.

## Rationale

Considered writing `docs/issue-2208/reports/execution-observation.md`
directly in this same session, on the theory that this session's own
independent re-verification (survey: code-level grep/Read matches,
9/9 test re-runs before and after in separate worktrees, an
independently re-run abstention query producing an exact numeric match,
and an independently reproduced fail-open check producing a
word-for-word match) already gives the record real content, so gating
it behind a second approval adds delay without adding rigor. Rejected:
the role-handoff contract treats a role's record as phase-2 output
requiring human approval regardless of how much independent
verification the survey round already performed — the approval
checkpoint exists to let a human review the verification's own
framing and scope before it is asserted as the record, not merely to
confirm that verification happened. Bypassing that separate check by
writing through a tool path the gate does not intercept would defeat
the review checkpoint this role exists to provide.

Also considered skipping the scout/survey round entirely, since this
task investigates already-landed code rather than proposing a design.
Accepted in part: scout-protocol's own "no design decision open" skip
condition applies (recorded in the survey's own skip line) and no
scouting sweep ran, but the current-state survey itself was still
written with real content — the diff, the implementation record's own
claims, and this session's own independently re-executed grep/Read/
pytest/python3 evidence — satisfying survey-order-directive's "must be
real, not decorative" criterion.

Also considered treating PR #2218's still-open state as itself a reason
to defer this entire role until after merge (on the theory that a
pre-merge diff could still change). Rejected: the role-handoff contract
does not gate execution-observation's phase-1 survey/proposal round on
the target PR's merge state — only this role's own phase-2 write is
gated, and by approval, not by the other PR's lifecycle. Independently
re-verifying a currently-open PR's branch tip is itself useful signal
for the human deciding whether to approve phase 2, and the survey
already states plainly (via the diff-stat and worktree citations) which
commit sha this session's own re-verification ran against, so a later
push to the same branch before merge would not silently misattribute
its findings.

## What will be done

On phase-2 approval (an `APPROVE issue-2208/execution-observation`
issue comment from a `docs/specs/approvers.md`-listed account), fill in
`docs/issue-2208/reports/execution-observation.md`'s five body sections
using the survey's findings: all three acceptance checks are
independently re-verified as met — (1) the abstention rate (58.1% over
completed decisions / 50.0% including timeouts, N=36) re-derived from an
independent run of the same query against `docs/*/reports/consult-log.md`
matches the implementation record's own number exactly; (2)
`tests/test_retrieval_eval.py` passes 9/9 in an independent re-run, and
neither frozen negative gold case flipped outcome between an
independent BEFORE (`origin/main`) and AFTER
(`origin/issue-2208/implementation`) run, with the positives macro MRR
improving (0.875→1.000) rather than regressing; (3) `work-in-english` is
statically bound to the `implementation` role and is independently
verified absent from BM25-scored candidates even under a forced
fail-open, against the same frozen negative case named in the
acceptance line — corroborated by an independent before/after
comparison showing it ranked 4th/8 on `main` and is absent entirely on
the implementation branch. The two open findings the implementation
record itself names (narrow role-binding scope for `work-in-english`;
`model-routing` left out of scope) are carried forward as open findings
here too, each with the same resolution path (a follow-up issue),
rather than silently treated as resolved. `loop_state` is set to
`handed-off` once the record's own findings are resolved or explicitly
deferred with a resolution path, per
`roles/specs/execution-observation.spec.json`'s terminal-state list.

## Out of scope

No change to `pipeline.py`, `skills.py`, `spawn.py`, or any code path.
No edits to PR #2218 (still open) or the `issue-2208/implementation`
branch. No re-litigation of the implementation role's own scope
decisions (e.g. which roles `work-in-english` is pinned to, or leaving
`model-routing` unpinned) — those stay open findings with their own
resolution paths, not repaired or re-decided here.

## How you'll know it worked

`docs/issue-2208/reports/execution-observation.md` is filled in, its
`result:` field reflects this session's own re-executed evidence (not a
copy of PR #2218's self-reported numbers), every state/outcome/count
claim in it carries the `canonical:`/`derived:` grounding
`on-the-record/hooks/record-claim-guard.sh` already enforces at write
time (exercised directly this session while drafting the survey above),
and the commit landing it is pushed with a phase-2 delivery PR opened
against `main`.
