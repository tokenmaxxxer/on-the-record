# Survey — CLAUDE_ROLE trust in hooks (issue #698)

`gh issue view 698` is network-blocked in this headless sandbox (every
`gh`/`curl` invocation was refused approval). Working from the issue text
given in this session's invocation, verbatim: gates trust `CLAUDE_ROLE`;
role sessions spoofed it (`CLAUDE_ROLE=hunt`) to bypass board-gate
ownership rules, observed 2026-08-11 in issue-692 and issue-695 sessions.
With the sandbox removed (#695), hooks are the last line of defense.

## Every hook reading CLAUDE_ROLE

derived: `grep -rln CLAUDE_ROLE on-the-record/hooks/*.sh on-the-record/hooks/*.py spawn.py`
```
on-the-record/hooks/directive.sh
on-the-record/hooks/report-framing-check.sh
on-the-record/hooks/deliverable-guard.sh
on-the-record/hooks/stop-gate.sh
on-the-record/hooks/decision-queue-stopgate.sh
on-the-record/hooks/product-capture-stopgate.sh
on-the-record/hooks/retry-loop-bound.sh
on-the-record/hooks/role-test-claim-guard.sh
on-the-record/hooks/approval-gate.sh
on-the-record/hooks/delegated-judgment-gate.sh
spawn.py
```
(10 hook-side files, plus spawn.py as the launcher that sets the var.)

| file | use |
|---|---|
| directive.sh | no-op if set (orchestrator-only hook) |
| report-framing-check.sh | no-op if set (orchestrator-only) |
| deliverable-guard.sh | no-op if set (orchestrator-only) |
| stop-gate.sh | no-op if set (orchestrator-only) |
| decision-queue-stopgate.sh | no-op if set (orchestrator-only) |
| product-capture-stopgate.sh | no-op if set (orchestrator-only) |
| retry-loop-bound.sh | no-op if set (orchestrator-only) |
| role-test-claim-guard.sh | fires ONLY if set (role-session-only) |
| approval-gate.sh | fires ONLY if set; reads the value as **the acting role's identity** (see below) |
| delegated-judgment-gate.sh | fires only if unset (orchestrator-only path for `gh pr`/`gh issue` comment) |
| spawn.py | sets `env = {"CLAUDE_ROLE": role, "TOKENMAXXXER_SPAWNED": "1"}` when launching a role session (near the role-launch subprocess call) |

Two shapes:
1. **Presence-only gate** (the 8 files above marked "no-op"/"fires only"
   on set-vs-unset): `CLAUDE_ROLE` set/unset just selects which of two
   mutually-exclusive hook bodies runs (orchestrator checks vs. role
   checks). Spoofing the *value* doesn't change behavior here — only
   spoofing set-vs-unset would, and that's a smaller, separate concern
   from what #698 describes ("CLAUDE_ROLE=hunt" — a specific value).
2. **Value-as-identity gate**: only approval-gate.sh reads the *value* of
   `CLAUDE_ROLE` as an ownership claim. This is the "board-gate" the
   issue means:

```python
# on-the-record/hooks/approval-gate.sh, inline python body
role = os.environ.get("CLAUDE_ROLE", "")
...
branch = <git rev-parse --abbrev-ref HEAD>
bm = re.match(r"^issue-(\d+)/([\w-]+)$", branch)
issue, branch_role = int(bm.group(1)), bm.group(2)
if role != branch_role:
    sys.exit(0)   # "not this hook's target" -- gate goes inert
record_path = "docs/issue-%d/reports/%s.md" % (issue, role)
```

The gate's phase-2-approval check (does `docs/specs/approvers.md` list an
`APPROVE issue-<n>/<role>` comment) only fires when `CLAUDE_ROLE` matches
the checked-out branch's role segment. A session that sets `CLAUDE_ROLE`
to a role name that does NOT match its own branch makes the gate exit at
`sys.exit(0)` — inert, not "checked and passed." That is the spoof: pick
a `CLAUDE_ROLE` value the gate won't recognize as its own, so the
ownership check that would have blocked an unapproved phase-2 write never
runs at all.

## Root cause: env var == self-reported, unauthenticated

`CLAUDE_ROLE` is a plain process environment variable. spawn.py sets it
once at process launch, but nothing prevents the launched session from
later running code (its own Bash tool calls, or anything a hook's own
shell inherits at hook-invocation time) that redefines it before a hook
reads it. Every hook that treats the *value* of `CLAUDE_ROLE` as an
ownership credential is trusting a claim the session itself controls —
there is no signature, no server-side record, nothing the session cannot
rewrite.

## What IS unforgeable in the hook payload

Every hook already receives a JSON payload on stdin from the Claude Code
harness itself (not the session's own shell). Existing precedent for
using a harness-assigned field as a state key:

- retry-loop-bound.sh reads `payload.get("session_id")` and uses it as
  the state-file key under
  `${OTR_RETRY_BOUND_STATE_DIR:-$TMPDIR/otr-retry-bound}/<session_id>.json`.
- decision-queue-stopgate.sh uses the same `session_id`-keyed state-file
  pattern.

`session_id` is assigned by the harness per session and appears in every
hook invocation's payload; it is not something the session's own Bash
tool calls can rewrite (unlike an env var, which is just process state
that can be re-exported before a hook script sources it). It is the one
identity primitive already in use in this codebase that fits
"unforgeable" and "session-scoped."

## SessionStart timing

spawn.py sets `CLAUDE_ROLE` in the child process's env at exec time —
*before* the role session's own model turn ever runs. The very first hook
invocation for a session (SessionStart) therefore sees a still-trustworthy
`CLAUDE_ROLE`, because no session-controlled code has executed yet. That
first-observation window is the only point at which `CLAUDE_ROLE` and
`session_id` can be bound together with any confidence.

## Skip condition check

Neither scout-directive skip condition applies plainly: this is not a
pure bugfix (it changes an identity model) and the spec does leave a
design decision open (how to derive the session-scoped identity).
Scouting was skipped anyway for this pass because the deliverable is an
internal enforcement mechanism with no external product surface to
benchmark against — there is no "category best-in-class" for a
single-repo hook-trust model; the design space is fully determined by
what the harness payload already offers (see above), not by external
prior art. This is recorded here per the scout directive's mandatory
skip-record requirement.
