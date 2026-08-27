---
status: proposed
files:
  - docs/issue-2574/reports/execution-observation/survey.md
  - docs/issue-2574/proposals/2026-08-27-execution-observation-issue-2574.md
  - docs/issue-2574/reports/execution-observation.md
---

## Request

Fill in the pre-written skeleton at
`docs/issue-2574/reports/execution-observation.md` with an
execution-observation record for issue #2574: whether the
`issue-2574/implementation` branch (PR #2578, open, not yet merged)
delivered what the issue asked for, with independently re-executed
acceptance evidence — not a re-statement of the implementation role's
own claims.

## Constraints

No code path may be touched by this role — only the record files listed
above. The record's frontmatter must carry the fields its own skeleton
already declares (`issue`, `role`, `loop_state`, `upstream`, `subject`,
`test`, `result`, `assertedBy`) and set `result:` from this session's
own independently re-executed evidence (the survey's "Independent
re-verification" section), not from trusting PR #2578's own reported
numbers.

Blocking precondition, found this session and detailed in the survey's
"Issue #2574's own state" section: issue #2574 is closed
(`stateReason: COMPLETED`) even though PR #2578, which carries `Closes
#2574`, is still open and unmerged. The outer orchestration harness's
approval-gate denies any execution-surface write for this subject
unconditionally while the issue stays in that state — this denial fires
before either approval-signal path (a PR review Approve, or an issue
comment exactly `APPROVE issue-2574/execution-observation`) is even
evaluated, and only a `CORE_BUILD_NOW=1` environment stamp (set by the
spawner, never by this session itself) or a human reopening the issue
can restore a live path to the write this proposal's own "What will be
done" section describes.

## Rationale

Considered writing `docs/issue-2574/reports/execution-observation.md`
directly in this same session, on the theory that this session's own
task briefing ("완료의 정의: 변경이 이 브랜치에 커밋되고 push 되어 PR로
제출된 상태다") implied single-phase/build-now treatment, consistent
with the very fix this session was asked to observe (auto-spawned
observers, per this issue's own resolution, get no special case and
default to single-phase). Rejected: this session's own direct `Write`
attempt at that path was denied (see the survey's "Write surface"
section) — the fix that would make that assumption true is not yet
merged to `main`, let alone deployed to whatever infrastructure is
enforcing gates on this session, so acting on the assumption rather
than the observed gate behavior would have required either bypassing a
live deny or self-granting `CORE_BUILD_NOW`, both of which the
role-handoff contract and this issue's own "Non-goals" section rule out
for a session in this position.

Considered treating the closed-issue-state denial as evidence that this
task is simply not runnable and stopping without any record. Rejected:
the survey itself is real, substantive work — independent re-derivation
of the fix's own acceptance checks 2 and 4 by an entirely different
method (AST parsing instead of `inspect.signature`, a fresh `grep`
against the landed tree rather than trusting the implementation
record's quote) surfaced a genuine, if minor, citation-accuracy defect
in the implementation record (see the survey's "Discrepancy found"
section) that would otherwise go unreported. Landing that as a phase-1
survey, rather than discarding it, is the correct scope for a session
that cannot reach phase 2 this turn.

Considered asking this session to set `CORE_BUILD_NOW=1` itself, given
that the task briefing explicitly describes this session as
auto-spawned via `spawn_on_pr.py` — exactly the call site the issue's
own fix gives `single_phase=True`, which is precisely what would have
stamped `CORE_BUILD_NOW=1` into this session's own environment had the
fix already been live. Rejected outright, not merely deprioritized: the
role-handoff contract's own text is explicit that a session cannot
grant itself this bypass by setting the variable on its own — the
absence of that stamp is a live symptom of the exact defect issue #2574
describes (the fix landed on a branch/open PR but has not propagated to
whatever installation enforces this session's own gates), worth
reporting as observed fact (the survey does this), not something this
session may correct unilaterally by self-stamping the variable that
would make the symptom disappear.

## What will be done

On phase-2 approval (a `CORE_BUILD_NOW=1` stamp from a future spawn of
this role, or the issue being reopened followed by an `APPROVE
issue-2574/execution-observation` comment from a
`docs/specs/approvers.md`-listed account), fill in
`docs/issue-2574/reports/execution-observation.md`'s five body sections
using the survey's findings: the shared-default fix (checks 1-4) holds
up under this session's own independent AST-level and grep-level
re-derivation, the pytest regression check reproduces identically on
both the pre-fix and post-fix trees, and one citation-accuracy
discrepancy in the implementation record's own check-4 evidence quote
(undercounts by one line) is logged as an open finding with no code
action required. `loop_state` is set to `handed-off` once that content
is written.

## Out of scope

No change to `spawn.py`, `gates/spawn_on_pr.py`,
`gates/spawn_on_approve.py`, `lifecycle.py`, or any other code path. No
edits to PR #2578 (already open, not authored by this role) or the
`issue-2574/implementation` branch. No attempt by this session to set
`CORE_BUILD_NOW=1` itself, post an approval-shaped comment on its own
subject's issue, or reopen issue #2574 — all three are human/spawner
acts this role does not perform on its own behalf. No re-authoring of
the implementation session's deleted ad hoc verification harness for
checks 1 and 3 — this session substituted a structural source-level
verification instead (survey, "Independent re-verification" section).

## How you'll know it worked

`docs/issue-2574/reports/execution-observation.md` is filled in, its
`result:` field reflects this session's own re-executed evidence, every
state/outcome/count claim in it carries the `canonical:`/`derived:`
grounding `record-claim-guard.sh` already enforces at write time, and
the commit landing it is pushed with a phase-2 delivery PR (carrying
`Advances #2574`, since this partial-delivery PR does not itself close
the issue, per `pr-preflight.sh`'s accepted alternative trailer) opened
against `main`, once a live approval path actually exists.
