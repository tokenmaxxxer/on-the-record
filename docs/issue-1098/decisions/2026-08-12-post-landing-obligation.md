# Post-landing verification obligation as tracked state

## Status

Accepted (2026-08-12)

## Context

Issue #1098 (northpole req#3, req#5) asks that, in any session where
on-the-record is installed, the plugin itself default-drive a loop the
orchestrator previously ran only by hand: every landed fix gets verified
by actually running the changed behavior, every defect discovered during
that verification gets registered as a structural root-cause issue, and
the two keep composing so the system converges autonomously. The
provenance the issue cites (PRs #1086, #1091, #1093, #1095 verified by
execution before merge; #1085, #1088, #1097 filed from verification
findings) shows the loop already exists as a practice — the gap is that
nothing today makes "verify, then refile, then continue" the DEFAULT
next step after a landing; it only happened because an operator
remembered to run it.

Substrate that already exists and must not be duplicated:

- `gates/reexecution_gate.py` (#892/#476) — SHA-pinned worktree
  re-execution that produces a `pass`/`fail`/`error` verdict.
- `gates/landing_readiness.py` (#407) — per-PR readiness classification,
  already composing a `reexecution_blocking_cause`.
- `roles_due.py`'s board-condition trigger routing (#1005/#1088).
- The Monitor/poll watchdog (#829/#947).

None of these fire automatically at the moment a merge lands — that
attach-to-the-event trigger is the actual gap.

## Decision

Add one new piece of tracked state — a "landing verification obligation"
— and a `PostToolUse` hook that opens it as a pure side-effect of a
successful `gh pr merge`.

1. **`gates/landing_obligation.py`** owns the obligation lifecycle:
   `open_obligation` writes `.landing-obligations/<issue>-<role>-<pr>.json`
   (`{status, pr, sha, issue, role, opened_at}`) the moment a merge is
   observed; `resolve_with_reexecution_verdict` reads the *existing*
   `.reexecution/<issue>-<role>.json` verdict `reexecution_gate.py`
   already produces and flips the obligation to `"resolved"` (verdict
   `pass`, post-dating `opened_at`) or `"failing"` (`fail`/`error`).
   Execution itself is never re-implemented here — this module only
   tracks whether the post-landing verification obligation has been
   discharged.
2. **`on-the-record/hooks/post-landing-obligation-gate.sh`** is the
   attach-to-the-event trigger: a `PostToolUse` (`Bash`) hook that
   detects a successful `gh pr merge` (reusing `merge-allow-gate.sh`'s
   already-hardened shlex command-shape check, issue #824) and calls
   `landing_obligation.py open`. `PostToolUse` cannot deny, so the hook
   is pure side-effect — it cannot block or slow the merge itself.
3. **`gates/landing_readiness.py:obligation_blocking_cause`** turns an
   unresolved obligation into a `blocking_causes` entry scoped to the
   owning PR's own record path, mirroring `reexecution_blocking_cause`'s
   existing scoping fix (issue #398, this ADR's own §"Scoping"). This is
   what makes an unverified landing visible to the same readiness
   classifier every other landing decision already reads, rather than a
   parallel, unconsulted state file.
4. Refiling (the loop's step 2, "register discovered defects as a
   structural root-cause issue") is deliberately left to
   `roles_due.py`'s existing board-condition trigger mechanism, wired in
   a follow-up scoped separately (this ADR's write set stops at
   `roles/specs/*.spec.json`, editing role-spec trigger content) — see
   Alternatives.

### Scoping

`obligation_blocking_cause` scopes its returned cause to
`docs/issue-<n>/reports/<role>.md`, never a `gates/`-prefix scope. A
`gates/`-scoped cause only covers PRs that happen to touch files under
`gates/` — the exact over/under-coverage bug #398 already fixed once for
`reexecution_blocking_cause`. Every role PR always touches its own
record path, so scoping there is the one prefix guaranteed to cover the
PR the obligation is actually about.

## Consequences

- A successful `gh pr merge` now always leaves a `.landing-obligations/`
  record behind (when the branch resolves as `issue-<n>/<role>` and the
  command matches one of the two recognized shapes) — an auditable,
  append-only trail of what still needs live verification.
- `landing_readiness.py`'s classifier gains one more input; a PR whose
  own issue/role has an unresolved obligation from an earlier landing on
  that branch now surfaces as `BLOCKED_ON_SCOPE` instead of silently
  `READY`.
- Detection is event-driven (the `PostToolUse` hook), not poll-driven —
  lower latency than a periodic sweep, at the cost of coverage: a merge
  through the GitHub web UI, a raw REST call, or another CLI wrapper
  never fires this hook, so no obligation opens for it (see Known gap).
- Empty state stays quiet by construction: `list_open_obligations` only
  returns `"open"`/`"failing"` entries; a landing whose verification
  passes cleanly produces a `"resolved"` record that never surfaces as a
  blocking cause and never creates an extra issue.

## Alternatives considered

**A `Stop` hook instead of `PostToolUse`.** Rejected: `Stop` fires at
session end regardless of whether a merge happened this session, so it
cannot cheaply scope "did a landing just happen" without re-deriving the
same `gh pr merge` detection `PostToolUse` already gets for free from the
tool-call boundary.

**Teach `reexecution_gate.py` itself to auto-run on landing.** Rejected:
`reexecution_gate.py`'s `run_reexecution` shells out to an arbitrary
`--command`; a `PostToolUse` hook has no safe way to know *which*
command that landing's role should re-run without a role-spec lookup
that belongs in `roles_due.py`'s existing trigger mechanism. Keeping
obligation-creation and obligation-resolution as two separate steps
(open now, resolve when `reexecution_gate.py` is later invoked by
whatever already invokes it) avoids duplicating that lookup inline in a
hook script.

**A board-wide sweep gate (`closure_sweep.py`-shaped) instead of a
per-PR hook.** Rejected as the sole mechanism: it would still need a
trigger to run automatically — the exact gap this decision closes — and
would detect the obligation only on the next sweep, not at landing time.

**Have `landing_obligation.py` call `gh issue create` itself for step 2
(refiling).** Rejected: it would create a second place "who is allowed
to file an issue" is answered, alongside `roles_due.py`'s existing
spawn-routing path. Keeping refiling as a `roles_due.py` trigger keeps
that answered in exactly one place.

## Known gap (carried into phase-2, not closed here)

The after-proposal hunt
(docs/issue-1098/reports/architecture/2026-08-12-hunt-post-landing-verify-refile-loop.md)
found that obligation-creation is scoped to one tokenized `gh pr merge`
Bash-command shape. A PR that reaches merged state through any other
path never triggers the hook, so no obligation file is written — which
this proposal's own empty-state test criterion cannot distinguish from a
landing whose verification genuinely already happened.

Resolution path (out of this decision's write set): add a second,
independent detection source — a periodic or `Stop`-hook-driven
reconciliation pass over `gates/landing_readiness.py`'s existing
`gh pr list --json state` read, treating any actually-merged PR with no
obligation file on record as `"open"`. This closes the gap without
abandoning the low-latency `PostToolUse` path as the fast/default case.

## Revisit trigger

Revisit if the web-UI/REST-merge gap above is observed in practice
(an unverified landing goes unflagged because it didn't go through
`gh pr merge` in this session) before the reconciliation pass lands —
that observation would raise the reconciliation pass's priority above
"phase-2 follow-up."
