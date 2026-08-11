---
status: proposed
files:
  - on-the-record/hooks/retry-loop-bound.sh
  - on-the-record/hooks/test_retry_loop_bound.py
  - docs/issue-846/decisions/
---

# Proposal — issue #846 step 1, implementation

## Request

Issue #846: `retry-loop-bound.sh`'s retry-fatigue `allow` (issue #507)
never re-examines command content — it independently supplies
`permissionDecision: "allow"` for a `Bash` command keyed only on
`(tool_name, command-string)` retry count and the prior, unrelated
denying gate's reason text. Once that unrelated gate stops denying the
identical string (state change or fail-open), this hook's `allow`
becomes the only permission signal for that call — even for a command
shape `merge-allow-gate.sh` (#824)/`spawn-allow-gate.sh` (#834) correctly
withhold their own allow for. The issue hands off two judgments: (1)
whether the fatigue hook should keep emitting `allow` at all, and (2) if
kept, whether it can be narrowed away from content-aware gates' scope,
and where that scope check should live.

## Constraints

- `on-the-record/hooks/merge-allow-gate.sh` and
  `on-the-record/hooks/spawn-allow-gate.sh` are frozen: no edit, and no
  import/shared-module extraction that would require editing them.
- `#507`'s existing, approved `Write`/`Edit`/`MultiEdit` K/2K behavior and
  its full existing test suite must keep passing unchanged (survey:
  `on-the-record/hooks/test_retry_loop_bound.py`'s existing tests all use
  `tool_name = "Write"`, so a `Bash`-scoped change cannot touch their
  asserted outcome, but the fix must not incidentally break that
  invariant either).
- The `2K` abort (`exit 2`, deny) path is unaffected: a deny only ever
  restricts, it does not grant a new permission signal, so it carries none
  of this issue's risk and needs no scope change.
- No new dependency; no re-implementation of `merge-allow-gate.sh`'s or
  `spawn-allow-gate.sh`'s `shlex`-based shape check inside
  `retry-loop-bound.sh`.

## Rationale

Considered dropping the K-tier `allow` entirely, switching to a
deny/stop-only design for the whole hook (the issue's own first framing
of the "keep allow?" question) — rejected: `#507`'s approved, shipped
rationale for choosing `allow`-with-context over pure abort was
specifically to let a session's *next* identical retry go through with a
corrective hint rather than force a second multi-minute retry storm just
to surface the hint (`docs/issue-507/proposals/2026-08-08-retry-loop-bound.md`,
## Rationale). That design answers a measured, `Write`-shaped problem
(`docs/issue-505/reports/implementation.md`) this issue's reproduction
never implicates. Dropping `allow` everywhere regresses a validated,
already-shipped behavior to fix a risk that is specific to `Bash`.

Considered the issue's own suggested precise-scope option — re-check the
incoming command's shape against `merge-allow-gate.sh`'s/
`spawn-allow-gate.sh`'s recognized shapes before allowing, either by
calling a shared discriminator function or by re-implementing the same
`shlex`-based tokenize-then-check-operator-tokens test inline in
`retry-loop-bound.sh` — rejected instead of adopted: a shared function
needs the two gates to expose or import it, and both are frozen by this
issue's own scope; an inline reimplementation creates a *third*
independently-maintained copy of that exact check, the same drift class
this repo's own history already produced once (issue #824's design
needed a deliberate #834 port to reach a second file at all) — a third
copy is more surface for the same drift, not a fix for it. Chosen
instead: scope the K-tier `allow` branch out for `tool_name == "Bash"`
categorically, keeping the informational `additionalContext` nudge for
`Bash` unchanged (a pattern `claim-scan-preflight.sh` already uses on
`PreToolUse`, independent of any specific command match). This needs no
knowledge of any gate's specific shape, cannot go stale as
`merge-allow-gate.sh`/`spawn-allow-gate.sh` evolve or as future
`Bash`-scoped content-aware allow-gates are added, and — per the survey's
test-coverage citation — changes no currently-tested behavior.

Why `Bash`-only and not every `tool_name`: an after-proposal warrant hunt
(docs/issue-846/reports/implementation/2026-08-11-hunt-narrow-retry-fatigue-allow-to-non-bash.md)
found this draft's first cut asserted the `Bash`-only scope instead of
checking it, and reproduced `retry-loop-bound.sh`'s K-tier `allow` firing
for a `Write` call after `approval-gate.sh` (a real `Write|Edit|MultiEdit`
gate with a documented fail-open path) stopped denying it. The survey's
"Warrant hunt" section resolves this: `approval-gate.sh` is "deny-only" by
its own header comment, and a grep of every hook `hooks.json` registers on
the `Write|Edit|MultiEdit` matcher shows `retry-loop-bound.sh` is the only
one that ever emits `permissionDecision` at all — no
`Write`/`Edit`/`MultiEdit`-scoped gate today deliberately withholds an
allow the way `merge-allow-gate.sh`/`spawn-allow-gate.sh` do, so there is
nothing on that axis for `retry-loop-bound.sh`'s independent allow to
override. `Bash`-only is therefore this issue's actual scope, not an
unchecked assumption; if a `Write`/`Edit`/`MultiEdit` content-aware allow
gate is added later, that grep is the check to re-run.

## What will be done

- In `on-the-record/hooks/retry-loop-bound.sh`'s `pre`-mode `count >= K`
  branch: build the `hookSpecificOutput` dict with `hookEventName` and
  `additionalContext` unconditionally; add `permissionDecision` and
  `permissionDecisionReason` to it only when `tool_name != "Bash"`. No
  other branch (`count >= 2*K` abort, `count < K` silent) changes.
- Add a new test to `on-the-record/hooks/test_retry_loop_bound.py`
  reproducing this issue's/PR #843's 3-step repro with `tool_name =
  "Bash"`: after 5 `post` denials of an identical `Bash` command and one
  `pre` lookup on the 6th attempt, assert the JSON output has no
  `permissionDecision` key (or that it is not `"allow"`) while
  `additionalContext` is still present and still names the deny count.
  Existing `Write`-shaped tests are left unmodified.
- Add `docs/issue-846/decisions/` recording both judgment calls (keep
  `allow` for non-`Bash`, scope it out for `Bash` categorically) and the
  rejected alternatives from ## Rationale, per the doctrine ladder for a
  changed-behavior decision.
- Phase 2 re-runs `python3 -m pytest on-the-record/hooks/ -q` and
  `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`, comparing the
  failure set against this issue's survey-recorded baseline (0 failures at
  commit `ac9732a`), and records both runs' output in the implementation
  record.

## Accumulation

`on-the-record/hooks/test_retry_loop_bound.py` already has 4 inline
`subprocess.run(...)` call sites (survey-confirmed by direct grep): one
inside the shared `_run()`/`_post()`/`_pre()` helper trio (used by all 8
of today's test functions), plus 3 more that bypass that helper and
build their own `subprocess.run` call directly (`_post_with_bind` and
the two calls inside `t_orchestrate_off_is_silent`) — each one
re-duplicating the same env-var/`bash on-the-record/hooks/
retry-loop-bound.sh <mode>` setup inline instead of reusing `_run`. This
proposal's new `Bash`-shaped regression test calls the existing
`_post`/`_pre` helpers (unchanged signature, just a `tool_name="Bash"`
payload) rather than adding a fifth inline `subprocess.run` site, so this
change does not grow that count. If this file gains N more ad hoc,
helper-bypassing tests the way `_post_with_bind`/
`t_orchestrate_off_is_silent` did, the inline-call count keeps growing
one-for-one with no consolidation; a future pass extending `_run`/`_post`/
`_pre` to accept the role-bind and `ORCHESTRATE_OFF` env overrides those
two already special-case would let every test — old and new — go through
one helper, but that consolidation is not part of this fix and is left
as a follow-up, not attempted here to keep this proposal's write set to
what issue #846 actually asks for.

## Out of scope

- Editing `on-the-record/hooks/merge-allow-gate.sh` or
  `on-the-record/hooks/spawn-allow-gate.sh` (frozen per the issue body).
- `plan-order-guard.sh`'s fail-open behavior — used only as the repro's
  realistic example of an unrelated, state-dependent denying gate, per
  the issue's own Out of scope; the composition holds for any gate with
  that shape.
- `docs/specs/generated-paths.md`'s verdict-column issue (#839), named
  explicitly out of scope by the issue.
- Changing the `K`/`2K` threshold values, the state-file format/location,
  or any `Write`/`Edit`/`MultiEdit` behavior of `retry-loop-bound.sh`.

## How you'll know it worked

- The new Bash-shaped regression test in
  `on-the-record/hooks/test_retry_loop_bound.py` fails against
  today's `retry-loop-bound.sh` (red) and passes after the fix (green) —
  the 6th identical-attempt `pre` lookup for a `Bash` command no longer
  carries `permissionDecision: "allow"`.
- `python3 -m pytest on-the-record/hooks/ -q` passes with every existing
  `#507` test's asserted outcome unchanged.
- `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` run on the
  branch after the fix shows no new failures versus this issue's
  survey-recorded baseline (0 failures, commit `ac9732a`).
