---
status: proposed
files:
  - gates/ci.py
  - test/test_auto_approval_shadow_wiring.py
---

# Wire shadow_verdict() into the approval-observation call site (#1791)

## Request

Wire `gates/auto_approval_class.py`'s `shadow_verdict()` — landed by
#1739 but never called from anywhere — into the point where an approval
decision becomes observable to the orchestration machinery, so the
shadow window (>=10 samples with zero human overturns, or 4 weeks) can
start accumulating. Shadow-only: no code path may skip or short-circuit
`on-the-record/hooks/approval-gate.sh`; with `shadow_mode: true` the
wiring must not change any spawn/merge/approval behavior — the diff must
leave `approval-gate.sh` untouched and must not alter the flow's
observable outcome, only append to the two record files. Any exception
inside the shadow call must be caught and logged as a degraded sample,
never break the path it rides on. Activation, bypass, quota enforcement
of real approvals, and any UI are explicitly out of scope.

## Constraints

- `on-the-record/hooks/approval-gate.sh` must be byte-identical before
  and after this change (issue acceptance check 1: "diff assertion on
  approval-gate.sh").
- The call site must be a real production observation point already on
  the poll/watch path — not a new, parallel detection mechanism (issue's
  design-research note: "mechanism reuses the existing watch/poll
  observation path and the #1739 module as-is; no new external
  mechanism").
- The shadow call's own failure must never propagate to or alter the
  return value of the function that hosts it (requirement 3,
  fault-injection acceptance check).
- Scope is frozen to `spawn.py, gates/auto_approval_class.py,
  test/test_auto_approval_shadow_wiring.py` per the issue body. This
  proposal's actual write set is narrower (`gates/ci.py`,
  `test/test_auto_approval_shadow_wiring.py` — see Rationale for why
  `gates/ci.py` is used instead of `spawn.py`, and why
  `gates/auto_approval_class.py` needs no change).

## Rationale

The survey (docs/issue-1791/reports/implementation/survey.md) found
three candidate call sites and ruled out two:

- **spawn.py's watchers** (`_watch`/`_watch_all`) were the issue body's
  literal suggestion ("the watch/poll path that sees an APPROVE token").
  Rejected: they watch a spawned session's own event-log file for
  process liveness (session-end/stall/crash) and contain no code that
  reads GitHub comments or PR reviews at all — there is nothing in that
  path that currently "sees" an APPROVE token to hook into. Wiring the
  shadow call there would mean adding a brand-new GitHub-comment read
  inside spawn.py's watch loop, which is exactly the "new external
  mechanism" the issue's design-research note rules out, and would also
  put a shadow-only concern on spawn.py's hot poll loop (called every
  tick for every live session), unrelated to its actual job.
- **`gates/spawn_on_pr.py:is_approval_blocked()`** reads the same
  underlying signal (`_ci._approved_roles_on_issue()`) but is scoped
  narrowly to deciding whether to auto-spawn two specific verification
  roles (`execution-observation`, `conformance-review`) — it is a
  consumer of the approval signal for a different purpose, not the
  phase-1-proposal-to-phase-2 observation point the issue describes.

The chosen site, `gates/ci.py:_phase_from_approval()`, is where an
APPROVE issue comment or a PR review Approve is actually turned into the
`phase1`/`phase2` decision that `check()` (the CI entry point, re-run
every PR-status-check tick — a genuine poll path) acts on. It already
unifies both approval-signal shapes the issue names into one boolean
fact ("was this PR just observed as phase2-approved"), so the shadow
call can ride on a computation that already happened instead of
re-deriving it.

`gates/auto_approval_class.py` itself needs no code change: `#1739`
already delivered `shadow_verdict()` with the exact signature and
failure-isolation contract this issue asks for (empty-state and
exception behavior belong to that module, not this call site). This
proposal only adds the call and its `gate_results`/`diff_paths`
composition around the existing `_phase_from_approval()` call in
`gates/ci.py`'s `check()`/`_autodetect_issue_phase()` path, wrapped in
its own `try/except` so a shadow-side failure can never affect
`check()`'s real return value (the blocking-reasons list gating real
merge behavior).

## What will be done

- In `gates/ci.py`, at the point in `check()`/`_autodetect_issue_phase()`
  where `_phase_from_approval()` first observes `phase2` for a
  (issue, pr) pair not previously observed as phase2 this run, call
  `auto_approval_class.shadow_verdict()` with:
  - `diff_paths` from the PR's changed-files list (reusing the same
    `gates.changed_files`/PR-diff primitive already used elsewhere in
    `gates/ci.py`, not a new GitHub call shape).
  - `gate_results` built by calling `scope_adherence.check()`,
    `stale_revert_guard.check_pr()`, and `requirement_met.check()`
    fresh, converting each to the boolean shape `shadow_verdict()`
    expects.
  - `issue`, `pr`, and a timestamp.
- Wrap the entire shadow call (gate composition + `shadow_verdict()`) in
  one `try/except Exception`, so any raised exception is caught, does
  not propagate into `check()`'s own control flow, and is logged as a
  degraded sample line (a defined line shape distinguishing it from a
  normal `shadow_verdict()`-written audit line, e.g. carrying
  `degraded=true` and the exception's `repr()`), written directly to the
  same audit log path — not via `shadow_verdict()` itself, since a
  failure inside gate composition happens before `shadow_verdict()` is
  even reachable.
- No change to `on-the-record/hooks/approval-gate.sh`, `spawn.py`, or
  `gates/auto_approval_class.py`.
- Author `test/test_auto_approval_shadow_wiring.py` covering:
  1. A simulated approval event (monkeypatched `_issue_comments`/
     `_pr_reviews`/`_approvers` the same way
     `gates/test_closes_gate_ci.py` already does) drives `check()` to
     observe `phase2` and produces exactly one appended sample in both
     the audit log and the state file; a `git diff` (or content-hash
     comparison) assertion that `on-the-record/hooks/approval-gate.sh`
     is untouched by the change.
  2. Empty state: a watch/poll pass with no approval event appends no
     sample and leaves the state file unchanged.
  3. Fault injection: gate composition (or `shadow_verdict()` itself)
     raising forces the degraded-sample path — `check()`'s own return
     value and control flow are unaffected, and one degraded line lands
     in the audit log.
- Paste one live sample from a real approval into the phase-2 record
  (`docs/issue-1791/reports/implementation.md`), captured once phase-2
  work runs this wiring for real (issue acceptance check 1's second
  clause) — this happens in phase 2, not in this proposal.

## Out of scope

- Flipping `shadow_mode` to `false` (activation) — a separate human
  decision per the issue's Program context.
- Any bypass of `approval-gate.sh`'s human-APPROVE requirement.
- Quota enforcement of real approvals (only the shadow accounting
  `shadow_verdict()` already does).
- Any UI surface for shadow-mode data.
- Changing `gates/auto_approval_class.py`'s public API or behavior.
- Wiring a second call site for PR-merge-only approval (the issue names
  "an APPROVE token or a PR merge for a phase-1 proposal" as one
  observation event category already unified by `_phase_from_approval()`
  via `_pr_reviews()`/`_approved_roles_on_issue()`; a bare `git merge`
  with no recorded review/comment is out of scope since it carries no
  discoverable actor-identity signal for the sample).

## Accumulation

The new code adds one `try/except`-wrapped composition call inside
`gates/ci.py`'s existing `check()` path — a single call site, not a
per-item loop over a repeated list (unlike `roles/*.json`-style repeated
files). It calls three existing gate `check()`-shaped functions once per
observed phase-2 transition (bounded by real approval-comment/PR-review
traffic, not by any file this change grows). If a fourth or fifth gate
is added to the shadow-eligibility composition in a future issue, each
addition is one more named field in the same `gate_results` dict and one
more function call at the same call site — it does not grow into inline
`subprocess`/`gh` calls accumulating without a shared helper, since all
three (and any future) gates are already-existing shared `check()`
functions in `gates/`, not new ad hoc shell-outs authored inline here.

## How you'll know it worked

- `test/test_auto_approval_shadow_wiring.py` passes, covering both
  issue acceptance checks (simulated-approval sample-append +
  approval-gate.sh diff assertion; fault-injection degraded-sample
  case).
- `git diff -- on-the-record/hooks/approval-gate.sh` against `main` is
  empty for this PR's full changeset.
- With `shadow_mode: true`, running the existing CI-gate test suite
  (`gates/test_closes_gate_ci.py`, `gates/test_auto_approval_class.py`)
  and this PR's own tests shows `check()`'s existing behavior unchanged
  — the shadow call only appends to
  `docs/reports/auto-approval-audit-log.md` and
  `.on-the-record/auto-approval-state.json`.
- Phase 2's record carries one live sample line pasted from a real
  observed approval, plus the diff assertion's actual output.
