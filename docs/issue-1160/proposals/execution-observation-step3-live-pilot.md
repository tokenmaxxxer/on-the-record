---
status: approved
files:
  - docs/issue-1160/reports/execution-observation/current-state-survey.md
  - docs/issue-1160/reports/execution-observation/scout-brief.md
  - docs/issue-1160/proposals/execution-observation-step3-live-pilot.md
  - docs/issue-1160/reports/execution-observation.md
---

## Intent

Issue #1160 step 3 asks this role to exercise, live, the three-leg
pilot the implementation PR (#1164) landed: a need-detector firing on a
WITH-need fixture and staying silent on a WITHOUT-need fixture, a pilot
role waking and landing its mission deliverable, and a different role
recording the #1156-pattern bar verdict on it — recording exactly which
leg cannot be exercised and why, never claiming a leg that wasn't run.

## Constraints

- This role never re-executes an observed role's task, never edits
  under another role's src/test/docs paths, and renders verdicts only
  with adjacent citations (role directive, this session).
- No CORE_BUILD_NOW bypass is set this session (checked: `env | grep -i
  core_build_now` → empty). Phase 2 opens on the pre-posted issue
  comment "APPROVE issue-1160/execution-observation" (single-account
  mode: PR author and approver are both JiwonJung94, a
  docs/specs/approvers.md-listed account — canonical: gh pr view
  1164 --json author, gh issue view 1160 --json comments).

## What will be done

Check, per the current-state survey's finding that `need_detector` /
`mission_deliverables` / `verified_by` are unconsumed by any code in
this repo (survey, "What was read this session"): which of the three
step-3 legs can actually be exercised given that machinery does not
exist, and which cannot. For any leg that is a pure text predicate
(brand-design's `need_detector.condition`), hand-apply the stated
predicate against two scratch fixture directories (WITH-need,
WITHOUT-need) built in /tmp for this check only — never inside this
repo, never under any role's src/test/docs path — to test the
predicate's own internal consistency, clearly labeled as a manual
predicate check, not as "the landed detector firing" (no landed
detector exists to fire). Record all three verdict levels (outcome,
trajectory, step) in docs/issue-1160/reports/execution-observation.md,
citing PR #1164, commit cd97d6b, and the specific file:line evidence
for each. Any leg not exercisable (role wake, deliverable landing,
different-role bar verdict) is stated as exactly that — not run,
because no wake/spawn/verdict mechanism reads these fields — never
claimed as passed.

## Out of scope

Building the missing detector-evaluator, spawn-wiring, or
mission_deliverables verifier code. This role observes and records;
it does not implement the machinery gap it finds. That gap becomes an
open finding in the record for the human to act on.

## How you will know it worked

docs/issue-1160/reports/execution-observation.md exists, committed on
this branch, with an independence statement preceding all verdict
language, all three verdict levels addressed (or explicitly marked not
applicable with reason), every verdict-bearing sentence citing its
source, and loop_state set per the spec's terminal-state table.

## What did not work

None.
