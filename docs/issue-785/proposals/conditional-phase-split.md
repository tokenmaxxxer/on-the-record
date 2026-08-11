---
status: proposed
files:
  - docs/issue-785/proposals/conditional-phase-split.md
  - docs/issue-785/reports/implementation/survey.md
---

## Request

Role sessions given an explicit delivery task — build/run against a
design or plan already approved and merged upstream — still go through
the full propose→approve→build round trip, because the directive that
tells a role "work in two phases" and the gate that enforces it are both
unconditional: they key on whether *this subject* has its own Approve,
never on whether the work itself is a delivery against something already
decided elsewhere. Observed twice on 2026-08-11 in on-the-record#776
(step 2 built nothing on first spawn — only a proposal; step 3 emitted a
plan PR #781 before running). Make the split conditional: an
already-approved-delivery task gets a single-phase deliverable; a
net-new design task still gets propose-first, unchanged.

## Constraints

- The mechanism that decides "already-approved-delivery" must not be
  spoofable by the role session itself — a role claiming its own task is
  pre-approved would defeat the entire phase-1 gate. The signal has to
  originate from the orchestrator (which drafted the issue and read the
  board) or be independently checkable by the gate against GitHub state,
  never from the role's own prompt text alone.
- The propose-first requirement must stay byte-identical for net-new
  design work — this proposal adds a branch, it does not loosen the
  default.
- The fix spans two files that are both **outside this repository**: the
  role-side directive hook and the phase gate both live in
  `tokenmaxxxer/tokenmaxxxer-core` (plugin `core`), not in
  `on-the-record`. This subject's write set (`docs/issue-785/**`) cannot
  touch them — see the survey's "Write-set implication" section.

## Rationale

**Alternative considered and rejected: teach `approval-gate.sh` to
detect "delivery" by scanning the invocation task text for keywords
(e.g. "build now", "already approved").** Rejected because it is
trivially spoofable — any role could phrase its own task to match the
keyword pattern and skip its own Approve requirement, which is exactly
the gate's job to prevent (contract v3 s19's whole point is that
approval is a human act, never something a role can talk its way past).
A free-text heuristic on the gate side would weaken the propose-first
default for every subject, not just genuinely pre-approved ones.

**Chosen instead: an orchestrator-carried, gate-verified flag.**
`spawn.py` already knows at spawn time whether it is delivering a task
against a specific prior subject whose proposal merged to main (it read
the board to decide who runs next). It passes that upstream subject
reference explicitly (e.g. an env var
`TOKENMAXXXER_APPROVED_UPSTREAM=issue-<n>` or an equivalent spawn
argument) when, and only when, it is spawning a role to execute a plan
that already has a merged proposal. `approval-gate.sh` does not trust
the flag's mere presence — it independently confirms via `gh` that the
named upstream subject's proposal PR is merged before treating the
current subject as pre-approved for single-phase delivery. This keeps
the untrusted-input boundary at the gate (which already talks to GitHub
for its own Approve checks) rather than at the role session, and it
degrades safely: if the `gh` check fails or the flag is absent, the
subject falls back to the existing two-phase default.

**Hardening found during this proposal's own warrant hunt (after-proposal,
stance 0 — see `docs/issue-785/reports/implementation/hunt-conditional-phase-split.md`):**
"named upstream subject's proposal PR is merged" alone is satisfiable by
naming *any* already-merged, content-unrelated proposal (the hunt
reproduced this against real merged PR #783, `issue-760/implementation`,
naming it as upstream for an unrelated current subject) — merging is a
routine phase-1 event, not a human phase-2 delivery approval, and the
design as first drafted never tied the named upstream subject's content
to the current subject's actual task. The verification step in
`## What will be done` item 2 must therefore also confirm the named
upstream subject specifically authorizes the current subject's delivery
content — at minimum, the upstream subject's merged proposal or record
must cross-reference the current subject's issue number, not merely
exist as *some* merged PR under that subject name. Item 2 below is
written to that stricter predicate.

## What will be done

(Scoped to `tokenmaxxxer/tokenmaxxxer-core`, `core` plugin — a follow-up
subject in that repo, since this subject's write set cannot reach it.
This proposal specifies the change precisely enough to execute verbatim
there.)

1. `core/hooks/directive.sh`: when the new upstream-subject signal is
   present and verified, print a **single-phase deliverable** directive
   body instead of the current "Work the PR in TWO PHASES" block — same
   record/branch/PR mechanics, but no stop-after-proposal step: research
   and current-state survey (if any) land in the same commit as the
   deliverable, one PR, no wait for a second Approve.
2. `core/hooks/approval-gate.sh`: when the signal is present, confirm
   via `gh` both that the named upstream subject's proposal PR is
   merged AND that its merged content (proposal body or record)
   cross-references the *current* subject's issue number — not merely
   that some PR under that subject name merged. Only when both hold
   does the gate treat the current subject as already in phase-2 and
   allow `execution_surface` writes without requiring this subject's
   own Approve. Verification failure (bad reference, upstream not
   actually merged, no cross-reference to the current subject, `gh`
   call fails) falls through to the existing unconditional two-phase
   gate — never fails open.
3. `spawn.py` (repo `on-the-record`, outside this subject's own write
   set — noted here for completeness, not committed by this subject):
   the orchestrator sets the upstream-subject signal only when it is
   itself spawning a role for a task it knows to be delivery-only
   against a specific merged proposal, per the existing
   "DELIVERABLES ARE ROLE WORK" / board-reading judgment call the
   orchestrator directive already makes.
4. Acceptance test (per the issue's `check:` line) lives in
   `tokenmaxxxer-core`'s own test suite, alongside `approval-gate.sh`'s
   and `directive.sh`'s existing tests, asserting: (a) with the signal
   present and a verified merged upstream, the rendered directive
   instructs a single-phase deliverable and the gate allows execution
   writes without an Approve; (b) with no signal (today's default), the
   rendered directive and gate behavior are byte-identical to current
   behavior — the "empty state" acceptance line.

## Out of scope

- Any code change in this subject's own write set beyond the two docs
  listed in `files:` — `on-the-record` does not host the mechanism being
  changed.
- Changing how phase-1 material (survey, proposal) is authored or where
  it lives; this only changes whether phase-1 happens at all for a given
  subject.
- Retrofitting past subjects (#776, #781) — this is forward-looking only.
- Designing the exact flag name/wire format for the orchestrator→gate
  signal in binding detail; `## What will be done` names the shape
  (env var or spawn argument, `gh`-verified upstream reference) but the
  literal implementation is `tokenmaxxxer-core`'s to finalize against its
  own existing conventions (it already threads `CLAUDE_ROLE` similarly).

## How you'll know it worked

- The acceptance test named above exists in `tokenmaxxxer-core` and
  passes for both cases (signal present + verified upstream →
  single-phase; no signal → byte-identical current behavior).
- A subsequent live delivery-only spawn (the on-the-record#776-shaped
  case: architecture already merged, execution-observation or
  implementation told to build/run) produces one PR carrying the
  deliverable directly, with no intervening proposal-only PR.
- Net-new design spawns (no upstream signal) continue to open a
  phase-1-only PR and stop, unchanged.
