---
status: approved
files:
  - on-the-record/hooks/role-deviation-directive.sh
  - on-the-record/hooks/deviation-log-guard.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/test_deviation_log_guard.py
  - on-the-record/hooks/test_role_deviation_directive.py
  - docs/handbooks/deviation-loop.md
  - docs/issue-983/reports/implementation.md
  - docs/specs/enforcement-boundary.md
  - docs/specs/generated-paths.md
---

## Request

Extend the #958/#803 deviation loop (directive text + Stop-hook guard) so
it also binds inside a spawned role session, not only the orchestrator —
audit E Finding 1 found the loop structurally orchestrator-only even
though mid-task problems surface in role sessions. Plugin-only,
default-on (req#7).

## Constraints

- Role sessions cannot spawn peer roles or open issues on their own
  initiative mid-task (role-handoff contract v3's SCOPE-EXCEEDED RULE) —
  the role variant's FILE-AS-ISSUE resolution must not call `spawn.py
  spawn` from inside a role session.
- Must not change orchestrator behavior — `directive.sh` keeps its
  existing gate and text unchanged.
- Must add a role-session-context test case to
  `test_deviation_log_guard.py` proving the guard binds with
  `CLAUDE_ROLE` set, plus an empty-state case (no deviation -> no log).

## Rationale

Considered folding the role-session text directly into `directive.sh` by
dropping its `CLAUDE_ROLE`-unset gate. Rejected: `directive.sh`'s other
paragraphs (issue drafting, role spawning, board reading, delegation)
are orchestrator-only by design — exposing them to a role session would
hand it instructions to spawn other roles and draft issues on its own
initiative, contradicting the phase-1/phase-2 approval contract this
repo already enforces. Instead, a new UserPromptSubmit hook,
`role-deviation-directive.sh`, follows the existing role-audience
pattern already used by `record-tiering-directive.sh` and
`record-claim-shape-directive.sh` (`CLAUDE_ROLE`-set gate, opposite of
`directive.sh`), carrying only the deviation-loop text, adapted so
FILE-AS-ISSUE resolves to the scope-exceeded stop-and-report a role
already owes rather than a spawn call it is not allowed to make.

## What will be done

- Add `on-the-record/hooks/role-deviation-directive.sh`: a
  `UserPromptSubmit` hook, `CLAUDE_ROLE`-set gate (mirrors
  `record-tiering-directive.sh`'s skeleton), injecting a role-scoped
  RECOGNIZE/CLASSIFY/RESOLVE paragraph. INLINE-FIX resolution is
  unchanged (apply the fix, append an `inline` deviation-log line, resume
  same turn). FILE-AS-ISSUE resolution: finish what the frozen write set
  covers, STOP, report the deviation in the reply, and append a `filed`
  deviation-log line recording it as surfaced for the orchestrator/next
  role — never a `spawn.py spawn` call from inside the role session.
- Register the new hook in `hooks.json`'s `UserPromptSubmit` array,
  alongside the existing `record-tiering-directive.sh` entry.
- Remove `deviation-log-guard.sh`'s line-29 `CLAUDE_ROLE`-unset skip so
  the Stop-hook guard binds for role sessions too; the guard's existing
  branch-to-path regex already resolves `issue-<n>/<role>` branches
  correctly with no further change.
- Add two cases to `test_deviation_log_guard.py`: one proving the guard
  now blocks (returns the `additionalContext` refusal) a role session
  (`CLAUDE_ROLE` set) whose transcript carries a deviation marker with no
  matching log append; one proving a role session with no deviation
  marker produces no log requirement (silent pass). Update the existing
  `t_claude_role_set_is_noop` case, whose assertion encodes the bug this
  issue fixes, to reflect the new bound behavior.
- Add a short role-session subsection to `docs/handbooks/deviation-loop.md`
  cross-referencing the new directive and its FILE-AS-ISSUE resolution.
- Write `docs/issue-983/reports/implementation.md` per role-handoff
  contract v3 s19/s20.

## Out of scope

- Changing `directive.sh`'s own orchestrator-only gate or text.
- Giving role sessions the ability to spawn peer roles or open issues
  directly — out of scope per the SCOPE-EXCEEDED constraint above; a
  filed deviation stays a report, not a spawn.
- Any change to `spawn.py`, `consult_cmd`, or the board/watch mechanism.

## Accumulation

`hooks.json`'s `UserPromptSubmit` array gains one more entry, following
the same one-line-per-hook shape `record-tiering-directive.sh` and
`record-claim-shape-directive.sh` already established. If N more
role-audience directives are added the same way, the array grows
linearly (one line each) with no shared dispatch helper — this mirrors
the existing convention for that array (each hook is independently
gated and independently registered) rather than introducing a new
pattern; a future issue that wants a shared role-directive dispatcher
would be a separate refactor, not blocked by this change.

## How you'll know it worked

- `on-the-record/hooks/test_deviation_log_guard.py` passes in full,
  including the new role-session-bound and role-session-empty-state
  cases.
- Manually invoking `deviation-log-guard.sh` with `CLAUDE_ROLE` set, a
  transcript carrying a recognized-deviation marker, and no matching
  `docs/issue-<n>/reports/deviation-log.md` append returns the
  `additionalContext` refusal (previously silent no-op).
