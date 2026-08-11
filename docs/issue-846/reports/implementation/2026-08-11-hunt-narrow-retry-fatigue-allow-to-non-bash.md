---
proposal: docs/issue-846/proposals/2026-08-11-narrow-retry-fatigue-allow-to-non-bash.md
---

# Hunt record — narrow-retry-fatigue-allow-to-non-bash

## after-proposal — stance 0: assume the gate/design just proposed is bypassable — find the bypass

Verdict: FINDING — the `tool_name != "Bash"` scoping leaves the identical composition regression open on `Write`/`Edit`/`MultiEdit`, because `approval-gate.sh` is a real, shipped, fail-open, state-dependent denying gate in that same matcher group, and the proposal's Rationale treats the risk as Bash-specific without checking for a `Write`-side analog.
Kind: design-error
Seed: docs/issue-846/proposals/2026-08-11-narrow-retry-fatigue-allow-to-non-bash.md (## Rationale, ## What will be done, ## Constraints); on-the-record/hooks/retry-loop-bound.sh lines 181-227 (current, unedited); on-the-record/hooks/approval-gate.sh (fail-open comments, lines 25-26, 109, 162); on-the-record/hooks/hooks.json lines 20-26 (retry-loop-bound.sh pre matcher: `Write|Edit|MultiEdit|Bash`) and lines 51-59 (approval-gate.sh's own matcher: `Write|Edit|MultiEdit`)
cap_seconds: 60
tier: default
diff_stat_lines: 0 (docs-only phase-1, no code touched yet — proposal doc only)
started_at: 2026-08-11T12:39:35Z
ended_at: 2026-08-11T12:43:09Z

The proposal's own Rationale asserts the risk this issue names "is
specific to `Bash`" and, per its Constraints, deliberately keeps
`retry-loop-bound.sh`'s K-tier `permissionDecision: "allow"` completely
unconditional for every `tool_name != "Bash"` (`Write`, `Edit`,
`MultiEdit` — the other three tool names in its own PreToolUse matcher
group, `hooks.json` line 22: `"matcher": "Write|Edit|MultiEdit|Bash"`).
That framing is not established by anything checked in the survey — the
actual mechanism the issue names (an unrelated, state-dependent gate
denies an identical call K times, then stops denying — via fail-open, not
via the underlying problem being fixed — at which point
`retry-loop-bound.sh`'s own independent `allow` becomes the only
permission signal left for that call) has nothing to do with `Bash`
specifically; it only needs a fail-open, content-aware denying gate
sharing the matcher group. `on-the-record/hooks/approval-gate.sh` is
exactly that gate for `Write`/`Edit`/`MultiEdit` — it documents (lines
25-26) "lookup failure fails open (consistent with pr-preflight.sh's own
documented fail-open policy on infrastructure failures)" and (line 109)
"unparseable branch — accepted fail-open", the same shape the survey uses
`plan-order-guard.sh` to demonstrate for the `Bash` side of this issue.

Reproduced live against the current (pre-fix) `retry-loop-bound.sh` — the
exact 3-step repro from the survey's "Reproduction on this branch"
section, `tool_name` swapped from `Bash` to `Write` and the deny reason
swapped to name `approval-gate.sh` instead of an unrelated Bash gate. This
is legitimate evidence for the proposed (not-yet-landed) design because
the proposal's own text explicitly leaves this exact branch (`tool_name
!= "Bash"`) byte-for-byte unchanged — Constraints: "`#507`'s existing,
approved `Write`/`Edit`/`MultiEdit` K/2K behavior ... must keep passing
unchanged"; What will be done: "add `permissionDecision` and
`permissionDecisionReason` to it only when `tool_name != "Bash"`. No
other branch ... changes." So this reproduction's output is exactly what
`retry-loop-bound.sh` will still emit after the proposed fix lands, for
any `Write`/`Edit`/`MultiEdit` call that trips `approval-gate.sh`'s
documented fail-open path five times running.

### Reproduce
```
TD=$(mktemp -d)
SESSION="sess-846-write-repro"
TARGET="scratch/example/file.md"
DENY='PreToolUse:Write hook error: [approval-gate.sh: refused -- some deny reason here]'
for i in 1 2 3 4 5; do
  PAYLOAD=$(python3 -c "import json; print(json.dumps({'session_id':'$SESSION','tool_name':'Write','tool_input':{'file_path':'$TARGET'},'tool_response':'$DENY'}))")
  echo "$PAYLOAD" | env -u CLAUDE_ROLE OTR_RETRY_BOUND_STATE_DIR="$TD" OTR_RETRY_BOUND_K=5 bash on-the-record/hooks/retry-loop-bound.sh post >/dev/null
done
PRE_PAYLOAD=$(python3 -c "import json; print(json.dumps({'session_id':'$SESSION','tool_name':'Write','tool_input':{'file_path':'$TARGET'}}))")
echo "$PRE_PAYLOAD" | env -u CLAUDE_ROLE OTR_RETRY_BOUND_STATE_DIR="$TD" OTR_RETRY_BOUND_K=5 bash on-the-record/hooks/retry-loop-bound.sh pre
echo "pre exit: $?"
rm -rf "$TD"
```

### Observed
```
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "permissionDecisionReason": "retry-loop-bound: this exact Write on 'scratch/example/file.md' has been denied 5 times this session with no change between attempts. Last deny reason: approval-gate.sh: refused -- some deny reason here. Retrying identically will abort this action class after 10 denials.", "additionalContext": "retry-loop-bound: this exact Write on 'scratch/example/file.md' has been denied 5 times this session with no change between attempts. Last deny reason: approval-gate.sh: refused -- some deny reason here. Retrying identically will abort this action class after 10 denials."}}
pre exit: 0
```
`permissionDecision: "allow"` is present — per the proposed patch this
branch is untouched for `tool_name == "Write"`, so this exact output
survives the fix. If `approval-gate.sh` denies the same `Write` five
times (e.g. a transient `gh issue view` failure, per its own line-162
comment: "gh issue view lookup failed -- cannot verify approval state")
and then a sixth identical `gh` lookup itself times out or the branch
becomes unparseable (approval-gate.sh's own documented fail-open exits,
lines 25-26 and 109), `approval-gate.sh` no longer emits its deny on
attempt 6 and `retry-loop-bound.sh`'s independent `allow` is the only
signal left in that matcher group for the write — the same
"deliberately-withheld-allow gate gets overridden once it stops firing"
composition #846 reproduces for `merge-allow-gate.sh`/
`spawn-allow-gate.sh` on `Bash`, just on the `Write`/`Edit`/`MultiEdit`
axis instead.

### Expected
Either the proposal's Rationale should establish (not merely assert) that
no `Write`/`Edit`/`MultiEdit`-scoped gate shares the fail-open,
state-dependent shape that makes the `Bash` case dangerous — which is
false, `approval-gate.sh` is exactly such a gate and sits in the same
`Write|Edit|MultiEdit|Bash` matcher group as `retry-loop-bound.sh` — or
the scoping condition needs to be keyed on "does a fail-open content-aware
denying gate share this matcher group for this tool_name" rather than on
the literal string `"Bash"`, which is a proxy for that condition holding
today only because that's where the survey happened to look, not a
property of the mechanism.

### Resolution (recorded in the proposal and survey, not re-litigated here)

`approval-gate.sh` is a fail-open *deny* gate (its own header: "deny-only,
role-session approval gate") — it never itself emits
`permissionDecision: "allow"`.
canonical: `docs/issue-846/reports/implementation/survey.md`, "Warrant
hunt" section (repo-wide `grep -n "permissionDecision"` across every hook
`hooks.json` registers on the `Write|Edit|MultiEdit` matcher, this
session's direct run) — `retry-loop-bound.sh` is the only one that ever
emits `permissionDecision` on that axis, so there is no
`Write`/`Edit`/`MultiEdit`-scoped content-aware *allow* gate (an analog to
`merge-allow-gate.sh`/`spawn-allow-gate.sh`) for `retry-loop-bound.sh`'s
independent allow to override; the reproduced `Write` case is `#507`'s
already-approved, already-shipped behavior, not a new gap the proposed fix
introduces or leaves open. The `Bash`-only scope in
`docs/issue-846/proposals/2026-08-11-narrow-retry-fatigue-allow-to-non-bash.md`
now states this check explicitly instead of asserting it. This finding
does not change the proposed design; it changed the proposal's Rationale
from an assertion to a checked claim.

## Before-landing dispatch

Skipped: docs-only, no before-landing dispatch. Every path this phase-1
unit touches (this hunt record, the survey, and the proposal) is under
`docs/`, per the warrant directive's docs-only fast path — there is no
code diff yet for a before-landing hunt to probe; phase 2 (once approved)
is its own future build-and-land transition with its own hunt dispatches.
