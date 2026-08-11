---
status: proposed
files:
  - on-the-record/hooks/session-role-bind.sh
  - on-the-record/hooks/hooks.json
  - on-the-record/hooks/approval-gate.sh
  - on-the-record/hooks/test_approval_gate.py
  - on-the-record/hooks/test_session_role_bind.py
  - docs/issue-698/reports/implementation/survey.md
  - docs/issue-698/reports/implementation.md
  - docs/issue-698/reports/implementation/hunt-2026-08-11-session-scoped-role-identity.md
---

# Session-scoped, unforgeable role identity for board-gate ownership checks

## Request

Issue #698 (paraphrased, no secrets involved): hooks that gate board
ownership trust the `CLAUDE_ROLE` environment variable as if it were an
authenticated identity. A role session can set `CLAUDE_ROLE` to a value
its own gate checks won't recognize, which makes those checks exit inert
instead of enforcing — this was observed as `CLAUDE_ROLE=hunt` spoofing
against board-gate ownership rules in issue-692 and issue-695 sessions.
With the process-sandbox removed (#695), these hooks are now the only
enforcement layer, so this has to close. Phase 1 covers survey + proposal
only, per the two-phase contract.

## Constraints

- Fix must not require a new dependency, a new persistent service, or any
  change to how the Claude Code harness itself invokes hooks — the repo
  only gets to react to what the harness already hands it (payload JSON
  on stdin) and what spawn.py already controls (the child process's
  initial env).
- Must stay within the hook-mirror pattern this plugin already uses
  (bash wrapper + inline python), not introduce a new enforcement
  mechanism class.
- The fix targets the one hook proven to trust `CLAUDE_ROLE`'s *value*
  as an ownership credential — `approval-gate.sh` (see survey). The other
  8 hooks only branch on set-vs-unset, not on value, and are out of
  scope for this issue's stated failure mode.

## Rationale

**Chosen approach**: add a `SessionStart` hook
(`on-the-record/hooks/session-role-bind.sh`) that snapshots
`CLAUDE_ROLE` from its own environment — which, at `SessionStart`, is
still exactly what spawn.py set at process launch, because no
session-controlled code has run yet — keyed by the payload's
`session_id`, into a state file the role session's own tool calls have
no declared write path to (mirrors the `session_id`-keyed state-file
pattern retry-loop-bound.sh and decision-queue-stopgate.sh already use).
`approval-gate.sh` then resolves the acting role from that snapshot
(session_id -> role) instead of from the live `CLAUDE_ROLE` env var at
check time. A later Bash-tool-influenced re-export of `CLAUDE_ROLE` can
no longer change what the gate believes the role is, because the gate
stops reading the live env var for identity.

**Alternative considered and rejected — sign/HMAC the env var at spawn
time**: have spawn.py compute an HMAC over `role` with a repo-local
secret and set both `CLAUDE_ROLE` and `CLAUDE_ROLE_SIG`, with hooks
verifying the signature before trusting the role. Rejected: it adds a
secret-management surface (where does the HMAC key live, how does a
freshly-cloned repo bootstrap one) for a problem the existing
`session_id`-keyed state-file pattern already solves without any new
secret. It would also still leave a signed *value* sitting in an env var
the session's own subprocesses can read and re-emit unchanged — the
signature protects the role name against tampering but adds no
session-binding on its own; the state file approach binds identity to
the session_id directly, which is simpler and reuses an existing
pattern.

**Alternative considered and rejected — derive identity from the branch
name alone, drop `CLAUDE_ROLE` entirely**: `approval-gate.sh` already
parses `issue-<n>/<role>` off the branch name for the issue number; it
could use `branch_role` as the sole identity, never reading
`CLAUDE_ROLE` at all. Rejected: branch name is checked out by the
session and is exactly as spoofable as the env var (a role session with
Bash access can `git checkout -b` a different branch name, whereas it
cannot forge the harness-assigned `session_id` in its own hook payload).
The current code's `role != branch_role` cross-check is a real defense
but was designed as a secondary consistency check, not a substitute for
a genuinely unforgeable primary identity — dropping `CLAUDE_ROLE`
wouldn't fix the underlying trust problem, just move it.

## What will be done

1. New hook `on-the-record/hooks/session-role-bind.sh`, `SessionStart`
   matcher, registered in `on-the-record/hooks/hooks.json` under the
   `SessionStart` array alongside the existing `self-update.sh` entry —
   the after-proposal hunt (below) found the manifest is what actually
   dispatches hooks in this plugin (no directory-scan or convention-based
   auto-registration exists), and the original write set omitted it,
   which would have made the new hook a dead file that never fires while
   its own unit tests (calling the script directly) still passed: reads
   its own `CLAUDE_ROLE` env (set by spawn.py at process launch,
   unmodified at this point in the session lifecycle) and the payload's
   `session_id`; if both are present, writes
   `${OTR_ROLE_BIND_STATE_DIR:-$TMPDIR/otr-role-bind}/<session_id>.json`
   containing `{"role": "<value>"}`. No-ops (exit 0) if `CLAUDE_ROLE` is
   unset (orchestrator session) or `session_id` is missing from the
   payload — same fail-open shape as retry-loop-bound.sh for missing
   `session_id`. Never overwrites an existing snapshot for the same
   `session_id` (first-observation wins, so a later `SessionStart`
   replay within the same session_id can't re-bind to a different role).
2. `approval-gate.sh` changes its role resolution: instead of
   `role = os.environ.get("CLAUDE_ROLE", "")`, it first tries to read
   `<state_dir>/<session_id>.json` (same state-dir env var, same
   `session_id` field off the payload) and uses that snapshot's `role`
   value when present; falls back to the live `CLAUDE_ROLE` env var only
   when no snapshot exists (e.g. `session-role-bind.sh` hasn't run yet,
   or `OTR_ROLE_BIND_STATE_DIR` was cleared) — fail-open on missing
   state, consistent with this plugin's documented house style for
   infrastructure gaps, not fail-closed on an absent snapshot.
3. Tests: `test_session_role_bind.py` covers the new hook (env set/unset,
   session_id present/missing, first-write-wins on replay).
   `test_approval_gate.py` gets new cases: snapshot present and
   disagreeing with a live-reexported `CLAUDE_ROLE` — the snapshot value
   must win.

## Out of scope

- The 8 presence-only hooks (survey's table) — they don't read
  `CLAUDE_ROLE`'s value as identity, so they carry no spoofing surface
  this issue describes. Not touched.
- `delegated-judgment-gate.sh`'s unset-check path — same presence-only
  shape, not a value trust issue.
- Any change to spawn.py's own env-setting call — it already sets the
  value correctly at launch; the problem is downstream hooks trusting a
  later, session-influenced read of that same variable, not the initial
  set.
- Hardening the branch-name-derived `issue`/`branch_role` parse — real
  but a separate, already-partially-mitigated concern (the `role !=
  branch_role` cross-check stays as a secondary defense, unchanged).

## How you'll know it worked

- `test_session_role_bind.py` and the new `test_approval_gate.py` cases
  pass: a session that snapshots role `implementation` at SessionStart,
  then re-exports `CLAUDE_ROLE=hunt` before a later Write/Edit, is still
  gated as `implementation` by `approval-gate.sh` — the spoofed value is
  ignored once a snapshot exists.
- The existing `test_approval_gate.py` suite (pre-existing cases with no
  snapshot present) still passes unchanged, confirming the fallback path
  preserves current behavior when `session-role-bind.sh` hasn't fired.

## Accumulation

This adds exactly one new session_id-keyed state file per session
(`<state_dir>/<session_id>.json`, a few bytes each), the same shape
retry-loop-bound.sh and decision-queue-stopgate.sh already produce under
`$TMPDIR`. It does not touch `roles/*.json` or any other repeated-file
family, and it adds no new inline subprocess/`gh` call sites — it reuses
the existing state-file read/write helpers' pattern rather than
introducing a new one. State files are written under `$TMPDIR` (or
`OTR_ROLE_BIND_STATE_DIR`), which is process-ephemeral and not part of
the repository, so N more sessions means N more small tmp files with no
repository-side accumulation — no cleanup step is being deferred here.
