# Survey — presence-only CLAUDE_ROLE branches (issue #706)

Follow-up to #698 (landed: `session-role-bind.sh` + `approval-gate.sh`'s
value-as-identity read). #698's own survey
(`docs/issue-698/reports/implementation/survey.md`) already enumerated the
8 presence-only hooks and separated them from the one value-as-identity
hook (`approval-gate.sh`, already fixed) and the one unset-only hook
(`delegated-judgment-gate.sh`, orchestrator `gh` comment path, out of
scope here per the issue's own "8 hooks" framing). This survey classifies
those 8 by security relevance, per the issue's own two-outcome framing:
"skipping role-only gates, or triggering orchestrator-only stopgates
against a role session."

derived: `grep -n CLAUDE_ROLE on-the-record/hooks/*.sh`
```
directive.sh:12:                [ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
report-framing-check.sh:20:     [ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
deliverable-guard.sh:23:        [ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
stop-gate.sh:25:                [ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
decision-queue-stopgate.sh:21:  [ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
product-capture-stopgate.sh:34: [ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
retry-loop-bound.sh:32:         [ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
role-test-claim-guard.sh:32:    [ -n "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
```

## Classification axis

A branch flip is **security-relevant** when the branch it selects can
reach a hard enforcement outcome — `exit 2` (PreToolUse deny) or
`hookSpecificOutput.decision: "block"` (Stop hook forces another turn /
withholds completion) — so which branch runs changes what the session is
actually allowed to do or forced to redo. A branch flip is **harmless
convenience** when both branches are advisory-only
(`hookSpecificOutput.additionalContext` nudges, or plain injected
directive text) — misrouting the branch changes *which* nudge fires, or
whether an irrelevant nudge fires at all, but never changes what the
session can do.

## Per-hook

| hook | branch that fires when unset | enforcement shape | relevant? |
|---|---|---|---|
| `directive.sh` | inject orchestration directive text every prompt | no deny/block path — pure injection | harmless |
| `report-framing-check.sh` | Stop: check orchestrator report framing | advisory only — header: "a same-turn correction requirement, not decision:\"block\"" | harmless |
| `stop-gate.sh` | Stop: check orchestrator approval-request reply shape | advisory only — header: "not decision:\"block\"" | harmless |
| `product-capture-stopgate.sh` | Stop: nudge product-doc capture | advisory only — header: "Advisory only ... never decision:\"block\"" | harmless |
| `deliverable-guard.sh` | PreToolUse: deny writes to src/\|test/\|tests/\|docs/ | hard deny, `exit 2` (fail-closed on parse failure too) | **security-relevant** |
| `decision-queue-stopgate.sh` | Stop: age-gated decision-queue nudge | `age_hours >= 4` -> `decision:"block"`, forcing another turn | **security-relevant** |
| `retry-loop-bound.sh` (unset/orchestrator path is its *active* path — see below) | PreToolUse/PostToolUse: bound identical-denial retries | `count >= 2K` -> `exit 2` (hard deny) | **security-relevant** |
| `role-test-claim-guard.sh` | (fires on **set**, not unset — see below) | Stop: flags skip-vs-pass / hand-counted test claims; advisory correction only per header ("not decision:\"block\"") — but the exposure is that **unsetting silences the check entirely**, not what it does when it fires | **security-relevant** |

## Two distinct exposure shapes among the 4 security-relevant hooks

1. **Unset routes INTO a hard-enforcement branch** (`deliverable-guard.sh`,
   `decision-queue-stopgate.sh`, `retry-loop-bound.sh`): all three are
   orchestrator-only in the sense that they no-op when `CLAUDE_ROLE` is
   set, and run their real (deny-capable) body when unset. A role session
   that unsets `CLAUDE_ROLE` activates these against itself. This is the
   issue's "triggering orchestrator-only stopgates against a role
   session" outcome — not a privilege *escalation* for the spoofing
   session, but a spoofable, incorrect enforcement outcome: a role
   session can be locked out of its own deliverable writes
   (`deliverable-guard.sh`), forced into extra decision-queue turns
   (`decision-queue-stopgate.sh`), or hard-denied on a retry-count
   signature never actually seen `2K` times in that session
   (`retry-loop-bound.sh`, since the counter keys off `(tool, target)`
   and orchestrator/role sessions may collide on signatures under a
   shared state dir). Whether this is exploitable *for* the spoofing
   session or only a correctness/DoS defect against it, the branch
   selection is still driven by a value the session's own shell can
   rewrite — the same root cause #698 fixed for `approval-gate.sh`.

2. **Unset routes OUT of a role-only gate** (`role-test-claim-guard.sh`):
   the opposite shape — this hook fires only when `CLAUDE_ROLE` is *set*.
   A role session that unsets `CLAUDE_ROLE` before its Stop turn makes
   this hook no-op instead of running its skip-vs-pass /
   hand-counted-test-count check. This is the issue's "skipping
   role-only gates" outcome, and the more direct exploit shape: a role
   session can silence the one check that would flag a deceptive
   test-pass claim in its own reply, simply by not re-exporting
   `CLAUDE_ROLE` before Stop.

## Fix shape (reusing #698, not restating it)

`session-role-bind.sh` already snapshots `CLAUDE_ROLE` at SessionStart
(before any session-controlled code runs) into
`${OTR_ROLE_BIND_STATE_DIR:-$TMPDIR/otr-role-bind}/<session_id>.json`, and
`approval-gate.sh` already contains the exact resolve-with-fallback
snippet (`docs/issue-706` proposal, `## Rationale`, quotes it) needed
here: read the snapshot for `session_id` from the hook payload; if a
snapshot exists, its `role` field is the identity; else fall back to the
live `CLAUDE_ROLE` env var. What #706 needs beyond #698 is a **presence
check**, not a value comparison: `bool(resolved_role)` in place of each
hook's current `[ -z "${CLAUDE_ROLE:-}" ]` / `[ -n "${CLAUDE_ROLE:-}" ]`
shell test. Because the resolve step needs `session_id` off the JSON
payload and a Python interpreter, the presence check has to move from the
shell pre-check into each hook's Python body (or a small shared shell
snippet that shells out to Python before the existing shell-level
early-exit) — the shell-level `[ -z ... ]` test alone cannot read the
snapshot file.

## Skip condition check (scout directive)

Neither scout-directive skip condition applies plainly (this changes an
identity-resolution model, not a pure bugfix; the spec leaves the binding
plumbing open). Scouting was skipped anyway, for the same reason #698
recorded: this is an internal enforcement mechanism (hook-to-hook trust
boundary) with no external product surface to benchmark against — the
design space is fully determined by the state-file mechanism #698 already
built and proved, not by outside prior art.
