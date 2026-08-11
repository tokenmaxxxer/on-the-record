---
status: proposed
files:
  - on-the-record/hooks/deliverable-guard.sh
  - on-the-record/hooks/decision-queue-stopgate.sh
  - on-the-record/hooks/retry-loop-bound.sh
  - on-the-record/hooks/role-test-claim-guard.sh
  - on-the-record/hooks/test_deliverable_guard.py
  - on-the-record/hooks/test_decision_queue_stopgate.py
  - on-the-record/hooks/test_retry_loop_bound.py
  - on-the-record/hooks/test_role_test_claim_guard.py
  - docs/issue-706/reports/implementation.md
---

## Request

Follow-up to #698 (landed: `approval-gate.sh` resolves role identity from
the SessionStart session-role-bind snapshot, env-var only as fallback).
#698's survey found 8 hooks that branch only on `CLAUDE_ROLE` being
set-vs-unset (not on its value). A role session can unset the env var
before a tool call or Stop turn and flip itself into the
unset/orchestrator branch of those hooks. Survey (`docs/issue-706/reports/implementation/survey.md`)
found 4 of the 8 are security-relevant (their branch selection reaches a
hard `exit 2` deny or `decision:"block"`); the other 4 are advisory-only
nudges with no enforcement outcome. This proposal resolves the role for
the 4 security-relevant hooks from the #698 session binding, falling back
to the env var only when no binding exists, so unsetting the env var no
longer changes which branch runs.

## Constraints

- Reuse `session-role-bind.sh`'s existing state file
  (`${OTR_ROLE_BIND_STATE_DIR:-$TMPDIR/otr-role-bind}/<session_id>.json`)
  and `approval-gate.sh`'s existing resolve-with-fallback read pattern —
  no new state mechanism, no new hook.
- Each hook needs the incoming payload's `session_id`, which is already
  present in every hook invocation the harness sends (SessionStart,
  PreToolUse, PostToolUse, Stop all carry it) — no new payload field.
- Do not touch `directive.sh`, `report-framing-check.sh`,
  `stop-gate.sh`, or `product-capture-stopgate.sh` — the survey found no
  enforcement outcome (`exit 2` / `decision:"block"`) reachable through
  their branch selection, so binding them adds Python-body plumbing
  (payload parse, snapshot read) with no security benefit, only churn.
- Do not touch `approval-gate.sh` (#698 already fixed its value-as-identity
  read) or `delegated-judgment-gate.sh` (unset-only path, out of the
  issue's named "8 hooks", and out of this survey's scope).
- Fail-open on binding-read errors the same way `approval-gate.sh` does
  (missing snapshot, unparseable JSON, missing `session_id` -> fall back
  to the live env var) — a broken state dir must degrade to today's
  behavior, not to a new failure mode.

## Rationale

**Alternative considered: harden the shell-level `[ -z "${CLAUDE_ROLE:-}" ]`
pre-check itself** (e.g. wrap it in a subshell that re-derives
`CLAUDE_ROLE` from some trusted shell-only source before testing it).
Rejected: there is no trusted shell-only source of the role for a
presence check — the same root problem #698 solved (env var is
self-reported, re-writable mid-session) applies here, and the only
non-spoofable value present at hook-invocation time is `session_id` in
the JSON payload on stdin. Reading that payload for a presence check
requires the same Python-body resolve step `approval-gate.sh` already
uses; there is no cheaper shell-only fix, so the correct target is the
resolve step, not the shell pre-check.

**Alternative considered: fix all 8 hooks uniformly**, matching #698's
own framing of "8 presence-only hooks" without re-splitting them.
Rejected: 4 of the 8 have no enforcement outcome behind their branch —
misrouting them changes which advisory nudge fires, never what the
session can do. Binding those 4 adds a payload-parse + snapshot-read + a
new Python dependency (all 4 are currently pure-shell) to hooks that gain
no security property from it, which is scope creep against the
session-role-bind mechanism's actual job: gating enforcement decisions,
not text nudges.

**Chosen approach**: port `approval-gate.sh`'s existing resolve snippet
(session_id -> snapshot lookup -> env-var fallback) into the 4
security-relevant hooks' Python bodies, and replace each hook's presence
test (`[ -z ... ]` / `[ -n ... ]`) with a check on the resolved role
computed inside that Python body instead of the shell pre-check. This
reuses a pattern already landed and tested for #698 rather than
inventing a second one.

## What will be done

- For each of `deliverable-guard.sh`, `decision-queue-stopgate.sh`,
  `retry-loop-bound.sh`, `role-test-claim-guard.sh`:
  - Move the presence decision from the current shell-level
    `[ -z "${CLAUDE_ROLE:-}" ] || exit 0` (or `[ -n ... ]` for
    `role-test-claim-guard.sh`) into the hook's Python body, after
    parsing the JSON payload already on stdin/env.
  - Inside the Python body, resolve role the same way
    `approval-gate.sh` does: read `session_id` off the payload, look up
    `${OTR_ROLE_BIND_STATE_DIR:-$TMPDIR/otr-role-bind}/<session_id>.json`,
    use its `role` field if present and parseable, else fall back to
    `os.environ.get("CLAUDE_ROLE", "")`.
  - Replace the hook's set/unset branch condition with
    `bool(resolved_role)` (or its negation, matching each hook's current
    polarity).
  - Keep the existing shell-level `ORCHESTRATE_OFF` kill switch and
    fail-closed trap untouched — only the `CLAUDE_ROLE` presence test
    moves.
- Add an unset-spoof regression test per hook (acceptance's named check):
  session binding says a role is bound, `CLAUDE_ROLE` is unset in the
  test's env, hook is invoked -> it still takes the role-session branch
  (or refuses), not the orchestrator branch. One test file per hook
  listed above; a project convention check (do these hooks already have
  `test_*.py` siblings, e.g. `test_approval_gate.py`,
  `test_session_role_bind.py`) determines whether this adds new files or
  extends existing ones — recorded as a build-time decision, not
  re-opened as a question.
- Record the work in `docs/issue-706/reports/implementation.md` per
  contract v3 s19/s20.

## Accumulation

This change repeats the same edit shape (move a shell presence test into
a Python-body resolve-with-fallback read, ported from
`approval-gate.sh`) across 4 hook files, and adds 4 parallel regression
test files. There is no shared helper today — each hook already
duplicates its own inline Python resolve block by convention (this
repo's existing pattern: `approval-gate.sh`'s block was written once and
is being copied, not imported). At N more security-relevant
presence-only hooks discovered later (e.g. a future hook added with the
same set/unset shape), the same copy-paste would repeat a 5th, 6th time.
This proposal does not extract a shared shell/Python helper now — 4 call
sites copying ~15 lines each is below the threshold where extraction
pays for itself against the cost of adding an import/sourcing mechanism
these hooks don't currently have (they are invoked standalone by the
harness, no shared lib path is wired). If a 5th security-relevant
presence-only hook surfaces, that is the trigger to extract a shared
`role_resolve.py` snippet sourced by all call sites instead of
continuing to copy it — noted here so the next such proposal doesn't
have to re-derive the threshold.

## Out of scope

- The 4 harmless-convenience hooks (`directive.sh`,
  `report-framing-check.sh`, `stop-gate.sh`,
  `product-capture-stopgate.sh`) — no enforcement outcome to protect,
  per survey.
- `approval-gate.sh` (already fixed by #698) and
  `delegated-judgment-gate.sh` (unset-only, out of the issue's named 8).
- Any change to `session-role-bind.sh` itself or its state-file format —
  #698's mechanism is reused as-is.
- Any change to how `spawn.py` launches role sessions or sets
  `CLAUDE_ROLE` initially.
- The `TMPDIR`-dependent state-dir lookup itself. The after-proposal
  warrant hunt (stance 0) found that the resolve snippet being ported
  here re-derives the snapshot directory from the live `TMPDIR` env var
  on every hook invocation (`os.environ.get("TMPDIR", "/tmp")`), not a
  value pinned at SessionStart; a session that overrides `TMPDIR`
  alongside unsetting `CLAUDE_ROLE` makes the snapshot lookup miss and
  silently fall back to the live (attacker-controlled) env var —
  reproduced against the already-landed `approval-gate.sh` copy of this
  same snippet, not introduced by this proposal. Porting the snippet
  as-is into the 4 hooks here reproduces that pre-existing gap 4 more
  times rather than closing it. Fixing it (pinning the state-dir the
  same way `session_id` is already trusted, or another mechanism) is
  out of scope for #706, which is specifically about the `CLAUDE_ROLE`
  set/unset branch, not the state-dir trust boundary — flagged here as
  a follow-up candidate rather than silently absorbed into this
  proposal's scope.

## How you'll know it worked

- The acceptance-named regression test exists per security-relevant hook
  and fails on the pre-fix code (session binding says role bound,
  `CLAUDE_ROLE` unset, hook still takes the orchestrator branch) and
  passes after the fix (hook takes the role branch / refuses instead).
- `grep -n 'CLAUDE_ROLE' on-the-record/hooks/{deliverable-guard,decision-queue-stopgate,retry-loop-bound,role-test-claim-guard}.sh`
  shows the env var read only inside each Python body's fallback branch,
  no longer gating a shell-level early exit.
- The 4 harmless-convenience hooks are unchanged (no diff) — confirms the
  security-relevant/harmless split from the survey was actually honored,
  not silently over-applied.
