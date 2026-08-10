# Current-state survey — issue #645

## Incident recap
2026-08-10, an orchestrating session issued a foreground `spawn.py watch
--follow` (or an equivalent sleep/poll loop) for a long-running background
task. Claude Code queues mid-turn user input until the *next* tool result;
a blocking foreground call produces no intermediate tool result, so any
input the user sent while the call was in flight sat invisible until they
interrupted. #600 (merged into `decision-queue-stopgate.sh`, Stop-surface)
fixes the *closing* half of this class — a turn that declares itself
"waiting" instead of closing. It cannot reach this half: a foreground call
that is already running blocks before any Stop event exists to check.

## What already exists (main, as of this survey)

### 1. Contract text (`on-the-record/commands/run.md`)
- `## 턴 예산 규칙 (Turn-Budget Rules, #535)`, rule 1 (line ~440): work
  expected to take >=30s — including watchdog polling — goes to
  `background`, and includes the explicit instruction "워치독 폴링 —
  워치독 자체가 blocking foreground 턴을 차지해서는 안 된다." This is
  contract *text*, checked nowhere at tool-call time; it relies on the
  session reading and following it.
- Rule 3 generalizes the role-session watch/re-arm bounded-wait shape
  (`directive.sh` ~74-90) to all foreground work rules 1-2 cover, but
  again as prose, not an enforced PreToolUse check.
- #600's rule 4 (added this session cycle) closes the "waiting on a human
  decision" case at the Stop surface — a different failure shape
  (declaring-waiting-without-closing), not a tool-call shape.

### 2. Deployed PreToolUse `Bash`-matcher hooks (precedent to build on)
`hooks.json`'s `PreToolUse`+`Bash` group (`contract-guard.sh`,
`pr-preflight.sh`, `claim-scan-preflight.sh`, `spec-index-preflight.sh`,
`impact-guard.sh`, `delegated-judgment-gate.sh`, plus
`retry-loop-bound.sh pre`) is the exact hook point this issue's check
belongs in — a new command joining that same matcher group, not a new
event type.

- **`retry-loop-bound.sh`**: reads `tool_input.command` from stdin JSON;
  keys a signature off `(tool_name, target)`; two-tier
  allow-with-context/deny-outright; state in
  `${TMPDIR}/otr-retry-bound/<session_id>.json`; fails open on any parse
  error, missing `session_id`, or missing `python3`; kill switch
  `ORCHESTRATE_OFF`; role-session exempt (`[ -z "${CLAUDE_ROLE:-}" ]`
  gate, i.e. runs only when `CLAUDE_ROLE` is *unset* — the orchestrator).
  This is the one existing hook already scoped exactly the way #645
  needs (orchestrator-only, role sessions exempt) — direct precedent for
  the scoping gate, not just the shell skeleton.
- **`impact-guard.sh`**: PreToolUse+Bash, parses `tool_input.command` text
  for a batch shape (`gh pr merge` count >= 2), classifies against
  repo-local state, denies with `{"decision":"block"}` and a reason
  naming the exact rule. Precedent for "deny with an actionable message
  naming the alternative," and for resolving the on-the-record checkout
  path zero-install (`_checkout_resolve`) when the check needs to read
  more than the payload.
- **`approval-gate.sh`**: PreToolUse+Write/Edit/MultiEdit, the mirror-image
  scoping gate — `[ -n "${CLAUDE_ROLE:-}" ] || exit 0` (role-session
  only, orchestrator exempt). Confirms the repo's house pattern for
  session-type scoping is a one-line `case`/`[ -z/-n ]` guard read first,
  before any payload parsing — never a fact computed from the payload
  itself.
- **`call-shape-guard.sh`**, **`accumulation-claim-guard.sh`**: both
  resolve the on-the-record checkout root by walking up from `cwd`,
  matching `impact-guard.sh`'s zero-install resolution pattern — reusable
  if #645's check needs anything beyond the stdin payload (it does not;
  see Design below).

### 3. The Bash tool's `tool_input` shape
Every deployed `PreToolUse`+`Bash` hook reads `tool_input.command` (a
string) from the stdin JSON payload. The Bash tool's own parameter schema
(this session's tool definition, `run_in_background: boolean`) is passed
through as a sibling key on the same `tool_input` object — no deployed
hook in this repo currently reads it, but nothing here contradicts it
being present; `retry-loop-bound.sh`'s `_target()` helper already treats
`tool_input` as an arbitrary dict and reads only the keys it needs. This
is the load-bearing fact for #645's design: the payload the hook sees
already carries the caller's own backgrounding intent as a boolean,
observable identically to how the other hooks observe `command`.

### 4. Blocking call shapes named in the issue and confirmed by this survey
- `spawn.py watch` foreground / `spawn.py watch --follow` foreground —
  `--follow` is documented (`directive.sh` ~87, `spawn.py:_watch` ~2943,
  ~3057) as a call that "streams" repeatedly until a terminal event;
  run.md rule 1 already names watchdog polling as a background-only
  case. `spawn.py watchdog` (rule 1's own wording) is the same shape.
- `sleep N` inside a shell loop (`while`/`until`/`for ... do ... sleep
  ... done`) — the canonical foreground poll loop rule 1/rule 3 forbid in
  prose.
- No transcript corpus is attached to this issue beyond its own prose
  description (no transcript-dump assets directory exists for this issue
  in the working tree at survey time); the issue text itself is the only
  evidence source available to this survey, and step 1's brief is
  scoped to what that text specifies plus this repo's own documented
  `--follow`/watchdog/poll-loop vocabulary above.

## Gap (exact)
1. **No PreToolUse `Bash` hook reads `run_in_background` at all.** Every
   existing `Bash`-matcher hook in `hooks.json` classifies the command
   *text* only; none conditions its verdict on whether the caller already
   declared the call backgrounded. A check for "foreground blocking call"
   cannot be built from any existing hook's logic as-is — it needs a new
   conjunction (blocking shape AND not backgrounded) no current hook forms.
2. **No hook enumerates blocking-call shapes** (`watch`/`watch --follow`,
   sleep/poll loop syntax) as a named pattern set. `retry-loop-bound.sh`
   detects *repetition* of an already-denied call, not a single call's
   shape; `impact-guard.sh` detects a *batch count* of one specific verb,
   not a blocking-wait syntax.
3. **No orchestrator-only PreToolUse Bash gate exists yet that fires
   before the harness begins executing** — `retry-loop-bound.sh` is the
   closest scoping precedent, but its trigger is post-hoc denial
   repetition, not first-call blocking-shape detection.
4. **#600 does not and cannot cover this** — confirmed above: it is a
   Stop-surface state+text conjunction that only evaluates after a turn
   is about to close; a foreground call in progress produces no Stop
   event to evaluate against.

## Constraints carried into the proposal
- Zero-install, hooks-only (2026-08-08 policy) — no GitHub Actions.
- Orchestrator-session scoped, role sessions exempt (issue's own text) —
  reuse `retry-loop-bound.sh`'s exact one-line `CLAUDE_ROLE` gate, not a
  new formulation.
- Must state fail posture, gaming-resistance (renamed-command bypass,
  scoped honestly per the issue's own wording), kill switch, and must not
  weaken legitimate background use — all four required explicitly by the
  issue text, matching the acceptance-criteria discipline #600 already
  set as this repo's bar for this class of check.
- Refusal message must name the background alternative concretely (issue
  acceptance criterion 1) — not just "this is blocking."
