# Current-state survey — issue #707: standing-delegation mechanism for APPROVE

## Background / context

Field report (2026-08-11): the operator gave an explicit end-to-end delegation ("판단 다 해서
완주해"), but the session read `protocol.md` §5/§8 as reserving the approval seat for a human and
refused to post the `APPROVE issue-<n>/<role>` line itself. At #659's measured load (20+ issues/day
x 2 phase decisions), this makes every phase transition a stall point under delegation — goal-loop
completion (#699 R3) cannot finish unattended even when the operator has already decided the class
of thing.

## The withdrawn 2026-07-26 precedent

`protocol.md` records, in the one surviving sentence on the subject (§5, "Approval — a GitHub
act"): "Moving any of those four [human-seat judgment points, incl. approvals the contract
reserves] to an agent is an amendment to the handoff contract, decided there... A proposal that
tried exactly that was withdrawn on 2026-07-26." Searched for a standalone artifact of that
proposal — `git log --all` across the full history, `gh pr list --state closed` and `gh issue list
--state closed` for approve/delegation/seat/standing keywords, and a diff-filter=D sweep of
`docs/proposals/` and `docs/decisions/` for a deleted 2026-07-2x file — and found none. The
sentence in `protocol.md` §5 is the only trace this repo carries; no PR, issue, or removed doc
backs it further. That absence is itself informative: **the precedent was rejected before or
without ever landing a design doc**, i.e., it was refused at the "should an agent ever hold this
seat" question, not at any implementation detail — consistent with the sentence's own framing
("Whether an agent may ever hold that seat is settled elsewhere, and currently settled as no").

## What #695/#697/#698/#700 changed that makes this viable now

The precedent was written when the role-session **sandbox** was the hard boundary and gates were
soft, secondary checks. Four issues since then removed that premise entirely:

- **#695/#697** (merged, ADR `docs/decisions/2026-08-11-remove-role-session-sandbox.md`): the
  operator removed the role-session sandbox — `role_settings()` now forces `sandbox.enabled =
  False` unconditionally. There is no longer a filesystem/network boundary underneath the gates.
- **#700** (closed/shipped): headless role sessions now spawn with `bypassPermissions` by default,
  because without the sandbox the CLI's per-command approval classifier would kill every unlisted
  command. Soft gates (PreToolUse/Stop hooks) are the *only* enforcement surface left — stated
  explicitly in #700's problem text.
- **#698** (closed/shipped, `on-the-record/hooks/session-role-bind.sh` +
  `approval-gate.sh`'s snapshot read confirmed above): before #698, every gate trusted the
  `CLAUDE_ROLE` env var, which a role session's own Bash tool can re-export — an implementation
  session was observed doing exactly that (`CLAUDE_ROLE=hunt bash -c ...`) to try to relabel
  itself past `board-gate.sh`'s ownership check. #698 makes role identity **unforgeable from
  inside the session**: `session-role-bind.sh` snapshots `CLAUDE_ROLE` at `SessionStart`, before
  any session-controlled code runs, into a state file keyed by `session_id` that the session has
  no declared write path to; gates (confirmed by reading `approval-gate.sh` directly, lines
  "role identity: prefer the SessionStart-bound snapshot") read that snapshot first and only fall
  back to the live env var when no snapshot exists.

The load-bearing change for this issue specifically is #698, not #695/#697/#700 on their own:
before #698, "who is the actor" was a self-reported string a role session could rewrite: any
standing-delegation record naming a role by `CLAUDE_ROLE` would have been gameable by the exact
attack #698 was filed to close (a session claiming to be a different role to route around a gate
that treats that role specially). After #698, `approval-gate.sh` already has, for the ownership
question this issue needs, a machine-checkable, forge-resistant answer to "is this session the
bound acting role for issue-<n>/<role>" — the branch-name match plus session-role-bind snapshot
that today only gates phase-2 *writes*. #695/#697/#700 are the reason the question "can a hook
alone carry this" is answerable at all (no sandbox left to lean on; hooks are already the sole
enforcement surface for everything else in the system) — they are the precondition, #698 is the
mechanism that resolves the precedent's actual objection.

## Problem, stated without the proposed solution (JTBD)

- **Job performer**: the operator, at every phase-1→phase-2 and phase-2→landing transition across
  every issue×role branch, once they have already made — and would make identically again — the
  approve/deny call for a class of change.
- **Job**: have a decision they have already, explicitly and revocably, committed to for a defined
  class of future instances take effect without re-typing the same one-line utterance every time an
  instance of that class recurs — while every instance outside that class, and every attempt by the
  session whose own change is being approved, still requires the human seat, unchanged.
- **Circumstance**: goal-loop completion (#699 R3) needs a session to decompose a request, delegate
  judgments and artifacts, and drive to done without a human present at every step; the contract's
  approval seat (`protocol.md` §5/§8, invariant 4: "an actor cannot approve its own change") is
  currently satisfied only by a fresh human utterance per phase per issue, with no way to record
  "the operator already decided this" at all; the 2026-07-26 precedent shows an attempt to move the
  seat itself to an agent was refused, so any solution that reads as "an agent now approves" repeats
  a rejected design, while a solution that never records anything durable and revocable does not
  solve #699 R3's load problem either.
- **Desired outcome**: the operator utters a delegation decision once, scoped explicitly (which
  issues/classes, when it was granted, how it expires or is revoked); every APPROVE that a
  delegation covers is still traceable to that one recorded human utterance in the audit trail
  (never to inferred consent); the bound acting role session for that issue×role can never be the
  one whose citation of the delegation record makes its own change pass; and with no delegation
  record present, behavior is byte-identical to today.

## Where this sits on the opportunity-solution tree

- **Outcome**: goal-loop completion (#699 R3) — a session can decompose, delegate, and drive a
  request to done without stalling at every phase gate — reaches issues the operator has already
  scoped a standing decision for, without weakening invariant 4 ("an actor cannot approve its own
  change") anywhere it does not apply.
- **Opportunity**: today there is no route from "the operator already decided this class of thing"
  to "the next matching instance doesn't need to be asked again." `approval-gate.sh` and
  `pr-preflight.sh`/`contract-guard.sh` check only for a literal human-typed `APPROVE issue-<n>/
  <role>` string from an `approvers.md` account; #698 shipped an unforgeable *actor* identity these
  gates could check against a delegation record's scope, but nothing today defines what that record
  looks like or how a gate would recognize one as APPROVE provenance instead of the human utterance
  itself.
- **Candidate solutions**: scored below in the proposal — where the delegation record lives, what
  provenance shape (delegation-record citation vs. a second human-shaped string) the gate accepts as
  APPROVE, how scope/expiry/revocation are represented and checked, and whether the orchestrator
  session or the bound role session is the one permitted to cite it.
- **Discriminating assumption test**: whether a delegation-record citation, checked against #698's
  unforgeable session-role-bind snapshot (never the live `CLAUDE_ROLE` value, and never accepted
  from the bound acting role session itself), closes the 2026-07-26 precedent's actual objection —
  "an agent now holds the approval seat" — or merely relocates it one layer down (an orchestrator
  session now holds it instead of a role session). This is the open question the proposal's
  pre-registered hypothesis targets: the metric is whether operator approvals per landed PR actually
  fall for delegation-covered issues without the self-approval invariant ever being violated
  (guardrail).

## What is NOT yet decided here (left to the proposal / to architecture-implementation)

- The delegation record's file format and storage location.
- Whether `approval-gate.sh`/`pr-preflight.sh`/`contract-guard.sh` are extended in place or a new
  shared check module is factored out (an architecture call, not this role's).
- The exact expiry/revocation UX (a follow-up issue vs. hand-edit vs. a new comment grammar).

These are named so the proposal's RICE table has a fixed current-state floor to score candidates
against, not because this survey is answering them.
