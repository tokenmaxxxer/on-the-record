---
code_under_review:
  - on-the-record/hooks/session-role-bind.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/approval-gate.sh
  - on-the-record/hooks/test_approval_gate.py
  - on-the-record/hooks/test_session_role_bind.py
type: feature
breaking: false
verdict: pending
loop_state: landed
---

# Phase-2 delivery: session-scoped, unforgeable role identity (issue #698)

## What was done

Implemented per the approved proposal
(`docs/issue-698/proposals/2026-08-11-session-scoped-role-identity.md`,
`APPROVE issue-698/implementation`):

1. New `SessionStart` hook `on-the-record/hooks/session-role-bind.sh`:
   snapshots `CLAUDE_ROLE` keyed by the payload's `session_id` into
   `${OTR_ROLE_BIND_STATE_DIR:-$TMPDIR/otr-role-bind}/<session_id>.json`,
   first-write-wins, no-ops when `CLAUDE_ROLE` or `session_id` is absent.
2. Registered it in `on-the-record/hooks/hooks.json` under the
   `SessionStart` array, alongside `self-update.sh`.
3. `approval-gate.sh` role resolution now reads the session-id-keyed
   snapshot first (same state-dir env var) and falls back to the live
   `CLAUDE_ROLE` env var only when no snapshot exists.
4. `test_session_role_bind.py`: covers env set/unset, session_id
   present/missing, first-write-wins on replay.
5. `test_approval_gate.py`: added spoof-regression cases — a session
   whose bound snapshot says one role but whose live `CLAUDE_ROLE` was
   re-exported to another must be gated as the bound role, both when
   the bound role's approval exists (allowed) and when it doesn't
   (denied, defeating the spoof's actual goal of exiting the
   role!=branch_role check inert); plus a no-snapshot fallback case.

derived: python3 -m pytest on-the-record/hooks/test_session_role_bind.py on-the-record/hooks/test_approval_gate.py -q
```
23 passed in 1.53s
```

## Why

The env var `CLAUDE_ROLE` is attacker-controlled from inside a role
session (the model can re-export it via Bash before a later Write/Edit).
With the process sandbox removed (#695), `approval-gate.sh`'s live env
read was the last enforcement layer and had no defense against this.
Binding identity at `SessionStart`, before any session-controlled code
runs, and reading only that snapshot afterward closes the gap without a
new secret or dependency.

## Upstream

Based on: `docs/issue-698/proposals/2026-08-11-session-scoped-role-identity.md`

## Anomaly (report, not a completed-task claim)

GitHub issue #698 shows `state: CLOSED` (`closedAt: 2026-08-11T01:42:51Z`),
closed ~13s after the `APPROVE issue-698/implementation` comment
(`2026-08-11T01:42:38Z`), with no phase-2 code landed before closure (only
the phase-1 survey+proposal commit `336db7f` was merged, per PR #702, and a
prior implementation session's PR-create attempt failed with "No commits
between main and issue-698/implementation" — see the
`stranded-relay: pr-create-failed` and `session-end: no PR` issue comments).
This session proceeded to deliver phase-2 anyway because it was explicitly
invoked to do so and the approval comment is present and valid; the closure
itself was not verified as intentional. Flagging per contract: an
already-closed issue with no delivery landed is an anomaly to report, not
grounds to silently skip delivery. The delivery PR still names `Closes #698`
per convention; a human should confirm whether the issue's closure was
correct and, if not, reopen it independently of this PR.

## What did not work

None.

## Open findings

None.
