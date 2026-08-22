---
kind: proposal
subject: issue-2039
role: execution-observation
date: 2026-08-23
loop_state: scope-proposed
---

# Proposal — independent execution observation of issue #2039 (PR #2049)

files:
- `docs/issue-2039/reports/execution-observation.md` (new, phase-2 only — this
  role's sole phase-2 artifact)

This role writes nothing else. It does not touch `spawn.py`,
`gates/record_lint.py`, `on-the-record/hooks/skill-verdict-guard.sh`, or
anything under `docs/issue-2039/reports/implementation*` — those are the
observed role's, and this role did not author or edit them. No re-execution
of the observed role's task, no re-running of its tests beyond reading their
already-recorded output, no issue filing.

## Request

Issue #2039's spawn context (`spawn_on_pr.py`, auto-spawned on PR creation):
independent execution observation of commits landed on
`issue-2039/implementation` — the `implementation` role's phase 1 (PR #2042,
merged) and phase 2 (PR #2049, currently open) delivery of a per-mounted-skill
verdict obligation. Per this role's spawn directive, this role is mapped to
skill-repository (issues #1955/#1758): only skill guidance attaches here;
enforcement is core hooks only.

## Constraints

- Independence: this session must not re-edit or re-produce the observed
  role's artifacts, and must not read the working tree's current copy of the
  observed role's code as evidence of what it did — the committed diff and
  its own record are the admissible evidence, per this role's standing
  independence practice (`docs/issue-262/reports/execution-observation.md`'s
  independence section).
- Contract v3 s19/s22: findings return as a record on this role's own PR;
  this role never files an issue, never spawns a peer role, and never
  approves or merges anything itself.
- The phase-1 survey found PR #2049 still `OPEN` (not merged to main) at
  session time — phase 2 observes commits landed on the branch, not a
  merge-to-main event, consistent with the invoking task's own framing
  ("issue-2039/implementation 브랜치에 랜딩된 커밋").

## Rationale

Two candidate shapes were considered for phase 2's scope.

**Considered and rejected: wait for PR #2049 to merge before observing.**
Rejected because the invoking task explicitly scopes this role to commits
*landed on the branch* (`issue-2039/implementation`), not merged-to-main
state, and because contract v3 s19's "board is what is merged to main" rule
governs how *other* roles read state from this repo, not what this role is
here to observe — an execution-observation role that only ever looks at
already-merged work could never catch a phase-2-opening defect before it
compounds into main. Observing the branch as it stands (open PR, 5 commits) is
the shape that matches the spawn trigger.

**Considered and rejected: treat the near-exact-match approval comment
(survey F3) as out of scope, since the delivered code/tests otherwise line up
file-for-file with the approved proposal (survey F7).** Rejected because this
role's own genre — two of three prior instances sampled in the scout brief
— treats the approval-comment exact-match test as a standing check every
observation runs, not an optional one conditioned on whether the rest of the
delivery looks clean. A file-list match is a step-level check; the
approval-comment shape is a trajectory-level check, and the contract text
mounted this session states the near-match must be surfaced "plainly once ...
not repeatedly" specifically because an external orchestrator might not
independently notice it. Treating it as out of scope would mean the one
session positioned to notice — this one — chose not to say so.

Chosen: observe PR #2049 as landed on `issue-2039/implementation` now, run
the standing three-level verdict (outcome / trajectory / step) plus one
targeted check on the approval-comment shape found in survey F3–F5, per this
role's established practice.

## What will be done

Phase 2 will write `docs/issue-2039/reports/execution-observation.md`,
opening with the independence statement, then:

| Level | Question phase 2 answers | Evidence |
| --- | --- | --- |
| **outcome** | Did PR #2049 deliver what issue #2039's Acceptance section asks (a record write refused unless N skill-verdict lines present, byte-inert for zero-mounted-skill sessions, the spawn directive states the obligation, hook tests covering missing-line/empty-reason/zero-skill paths)? | The Stop hook's own code and test file, the record's cited test-plan output, the spawn.py diff. |
| **trajectory** | Was the phase-1→phase-2 path sound — survey before proposal, a real human approval before phase-2 work began, phase-2 output confined to the approved write set? | Commit order/timestamps, the approval comment (survey F3–F5), `gh pr view 2049 --json reviews`, the proposal's file list vs the delivered file list. |
| **step** | Which specific artifact, if any, is deficient? | The hook code, the `record_lint.py` check, the tests, the record itself. |

Plus one targeted check: whether the approval-comment near-match (survey
F3–F5) rises to a reportable finding under this session's own judgment, and
if so, its impact / timeline / root cause / action item, split mitigative
(this issue) vs. preventative (the class), per this role's blameless
four-part shape.

## Out of scope

- Re-running the observed role's tests (`pytest` on `test_skill_verdict_guard.py`,
  `gates/test_record_lint.py`) — their already-recorded output is the
  evidence; re-running would blur independence with re-verification.
- Any edit to `spawn.py`, `gates/record_lint.py`,
  `on-the-record/hooks/skill-verdict-guard.sh`, or any `docs/issue-2039/reports/implementation*`
  file.
- Filing an issue for the approval-comment finding, if confirmed. Under
  contract v3, issues are user-authored only; the finding returns in this
  role's own record for the human to judge.
- Judging PR #2049's eventual merge decision — that is the human's, via the
  standard GitHub-act channel.

## How you'll know it worked

- `docs/issue-2039/reports/execution-observation.md` exists on branch
  `issue-2039/execution-observation`, committed, independence statement
  before the first verdict-bearing sentence.
- All three verdict levels answered explicitly (or "not applicable, because
  X"), each verdict-bearing sentence citation-adjacent.
- The approval-comment check reaches a stated conclusion, traceable to the
  survey's F3–F6.
- Any deficiency finding carries impact / timeline / root cause / action
  item.
- `git diff --stat origin/main...HEAD` for this branch touches only
  `docs/issue-2039/reports/execution-observation*` and this proposal file.
