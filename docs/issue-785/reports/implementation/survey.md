# Survey: where the two-phase (propose→build) split is instructed

Subject: issue-785. Scope: locate every place — informing directive text
and mechanical gate — that makes a role session split its PR into a
phase-1 proposal and a phase-2 delivery, unconditionally, regardless of
whether the task is a net-new design or an already-approved delivery
against a merged upstream plan.

## Skip condition check

Scouting (best-in-class exemplar sweep) does not apply: this is process
archaeology inside the repo/plugin ecosystem this session already runs
under, not a product-shaped surface with external exemplars. The design
decision this survey exists to inform (where to add the conditional
branch, and on what signal) is exactly what remains open, so the
pure-bugfix skip condition does not apply either — scouting proceeds as
"survey the field" (rulebook/directive/contract text + prior decisions),
per the scout-directive's non-product branch.

## The split has two independent enforcement layers, in two different repos

**1. The informing layer — `directive.sh` in repo
`tokenmaxxxer/tokenmaxxxer-core` (local clone
`/home/jwjung/tokenmaxxxer/tokenmaxxxer-core`), the `core` plugin's
SessionStart hook:**

```
- Work the PR in TWO PHASES (contract v3 s19). Phase 1, before any
  execution work: commit your research, your current-state survey
  (docs/issue-<n>/reports/${role}/), and your proposal
  (docs/issue-<n>/proposals/), open the PR, and stop. Phase 2 opens ONLY
  when a human approver listed in docs/specs/approvers.md submits a PR
  review Approve; then do your actual work on the same branch, reported
  through the same PR. ...
```

This text is emitted unconditionally once per role session, whenever
`CLAUDE_ROLE` is set and preconditions (git repo, remote, `gh` auth)
pass. It carries no branch on task shape — every role session reads the
identical "work in two phases" instruction whether the invoking task is
genuinely new design or an explicit build/run against a plan already
merged upstream. This is the literal text this session itself received
this turn (visible verbatim in this conversation's
`[core] Interaction protocol` system-reminder, `role-handoff contract
v3` block), confirming the hook is live and unconditional as read from
source.

**2. The mechanical layer — `approval-gate.sh` in the same repo/plugin,
a PreToolUse deny gate:**

```
# PreToolUse: the phase gate of contract v3 s19. Every role proposes first
# (research, current-state survey, proposal — documents, phase 1) and
# executes only after an allowlisted human's Approve — a PR review, or an
# issue-level `APPROVE issue-<n>/<role>` comment (phase 2).
```

`approval-gate.sh` defines an `execution_surface()` check that classifies
any write under `src/**`, `test/**`, or `docs/issue-<n>/**` outside
`proposals/**` and the role's own `reports/<role>/` subtree as phase-2
work, and the surrounding deny logic (further down the same file) refuses
that write unless the **subject** (`issue-<n>/<role>`) itself carries a
human Approve. Approval is scoped to the subject — this issue, this
role — never to whether some *other* upstream issue's design/plan
already merged. A role spawned with an explicit "build/run against an
approved plan" task still hits the same denial on its first
`src/**`/`test/**` write, because the gate has no signal for "upstream
design already merged" — only for "this subject has its own Approve."

## Consequence, matching the issue's observed symptom

Both layers are keyed on the **current subject's own phase state**, not
on whether the **work itself** is a delivery against something already
decided elsewhere. A role told in its invocation prompt "the plan is
already merged, build now" still (a) gets told by the directive hook to
work in two phases, and (b) gets denied by the approval gate on any
src/test write until its own subject collects an Approve — reproducing
exactly on-the-record#776 step 2 (built nothing on first spawn, only a
proposal) and step 3 (plan PR #781 emitted before running).

## What "already-approved-delivery" could mean mechanically

Two candidate signals surfaced by reading the gate and this repo's own
orchestrator-side directive hook (`on-the-record/hooks/directive.sh`,
which already distinguishes "phase 1 proposal vs phase 2 delivery" when
relaying outcomes to the user, though it never acts on that distinction
itself — it only narrates):

- **Invocation-carried flag**: `spawn.py` already knows, at spawn time,
  whether the task text names an approved upstream plan/proposal (it
  drafted the issue and read the board). It could pass an explicit
  marker (e.g. an env var or a task-prefix convention) that the
  directive hook reads to choose which of two directive bodies to
  print, and that the approval gate reads to skip the Approve
  requirement for that one subject.
- **Board-derived signal**: the approval gate could instead check
  whether the invocation names a specific prior subject whose own
  proposal is already merged to main, and treat that as sufficient. This
  is harder to make forgery-proof (a role could claim any issue is
  "already approved") and was not found implemented anywhere in the
  surveyed files.

Both require a change in `tokenmaxxxer/tokenmaxxxer-core`, a separate
repository from `on-the-record`. No file in this repo (`on-the-record`)
defines or enforces the two-phase split directly — this repo's own
`on-the-record/hooks/directive.sh` is the *orchestrator*-side directive
(governs the top-level session that spawns roles), not the role-side
one, and exits immediately when `CLAUDE_ROLE` is set — mirroring
`tokenmaxxxer-core`'s own orchestrator/role split.

## Write-set implication for the proposal

Per this session's invocation, the write set for this subject
(issue-785, on-the-record) is confined to `docs/issue-785/**`. The
mechanical fix belongs in `tokenmaxxxer/tokenmaxxxer-core`, a repository
this session's branch/PR cannot touch. The proposal therefore scopes to:
(a) recording the exact conditional-branch design in
`docs/issue-785/proposals/`, precise enough that a `tokenmaxxxer-core`
subject can implement it verbatim, and (b) naming the cross-repo
dependency explicitly rather than silently building only half the fix.

## Sources

- `/home/jwjung/tokenmaxxxer/tokenmaxxxer-core/core/hooks/directive.sh` (local clone of `tokenmaxxxer/tokenmaxxxer-core`)
- `/home/jwjung/tokenmaxxxer/tokenmaxxxer-core/core/hooks/approval-gate.sh`
- `on-the-record/hooks/directive.sh` (this repo, orchestrator-side counterpart)
- This session's own `[core] Interaction protocol` system-reminder (verbatim match to the directive hook's role-handoff contract text)
- `gh issue view 785` (issue text, Problem/Fix direction/Acceptance)
