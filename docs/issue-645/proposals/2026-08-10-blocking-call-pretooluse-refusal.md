---
status: proposed
Subject: issue-645
files:
  - on-the-record/hooks/blocking-call-guard.sh
  - on-the-record/hooks/test_blocking_call_guard.py
  - on-the-record/hooks/test_blocking_call_guard_regression_e2e.py
  - on-the-record/hooks/hooks.json
  - on-the-record/commands/run.md
  - docs/specs/reconciled-index.md
  - docs/specs/enforcement-boundary.md
---

# Proposal — PreToolUse refusal of foreground blocking calls (issue #645)

## Revision (2026-08-10, additive, same branch/PR)
Operator feedback on the original design (PR #647 review comment; issue
#645 comments 5236257876, 5236261763) overrides the shape/backgrounding
conjunction below for one command family: **watch-family commands are
categorically exempt from refusal.** Rationale relayed by the operator:
an orphaned unwatched session is unbounded harm (the 2026-08-08
388-minute idle incident traced to exactly this), while a foreground
watch is bounded by its own stall-timeout — the tradeoff is not close.
Concretely, this revision changes the design as follows (full detail
inline at each affected section below):
- `spawn.py watch` (with or without `--follow`), `spawn.py watchdog`, and
  the spawn call's own built-in watcher arming are never blocked —
  foreground or background, ambiguous or not. At most a foreground watch
  receives an advisory `additionalContext` naming the background form,
  while still executing unblocked.
- Refusal scope narrows to exactly one shape: sleep/poll loops (`while`/
  `until`/`for` + `sleep`, or a bare `sleep >= 30`). This was already one
  of the two shapes; it is now the *only* shape that can deny.
- Ambiguity (payload does not expose `run_in_background` reliably, or the
  command text partially matches watch-vocabulary) fails **open toward
  allow** for watch-family specifically — never toward block. This is
  stricter than the general fail-open posture below: general fail-open
  covers infra/parse errors; this is a shape-classification rule that
  applies even when the payload parses fine but classification of a
  watch-shaped command is uncertain.
- The observation-loss regression guard (spawn → background watch →
  re-arm e2e, hook active, asserting no increase in DEAD/unarmed
  watchers) is added to the phase-2 write set as
  `test_blocking_call_guard_regression_e2e.py`.

## Request
An orchestrating session must be structurally prevented from *entering* a
foreground blocking call — not merely interruptible once it has. #600's
`decision-queue-stopgate.sh` extension governs the Stop surface (turn
*closing*); this issue governs the PreToolUse surface (call *opening*).
Together the two make the frozen-input state unreachable: #600 stops a
session from re-declaring "waiting" instead of closing its turn; #645
stops the foreground call that produces no intermediate tool result in
the first place.

## Constraints (from the issue and survey)
- Zero-install, hooks-only — a new command in the existing
  `PreToolUse`+`Bash` matcher group of `hooks.json`, no new event type,
  no GitHub Actions.
- Orchestrator-session scoped; role sessions are non-interactive and
  exempt (issue's own text) — reuse `retry-loop-bound.sh`'s exact
  `CLAUDE_ROLE` gate rather than a new formulation (scout brief: adopt).
- Must state fail posture, gaming-resistance (a renamed-command bypass is
  the known limit — scope it honestly, do not claim to close it), kill
  switch, and must not weaken legitimate backgrounded use — all four
  required by the issue text.
- Refusal message must name the background alternative concretely
  (acceptance criterion 1).
- Must not fire on role sessions even for the identical command text
  (acceptance criterion 1's stated empty state).

## Rationale
The survey's gap is exact: no deployed `PreToolUse`+`Bash` hook reads
`tool_input.run_in_background` at all, and none enumerates blocking-call
shapes. A shape-only check (deny any `spawn.py watch --follow` command
text, unconditionally) is wrong on its face — it would refuse the
*compliant* backgrounded call this issue itself names as the required
alternative, identically to how a shape-only check would refuse a
legitimate `sleep 2` used for a genuinely short, bounded pause. The
design adopted here conjoins two independent signals already present on
the same `PreToolUse` payload, neither sufficient alone — the same
gaming-resistance model #600 already established for its own conjunction
(state fact + text pattern), transplanted here to (command-shape regex
match) AND (`tool_input.run_in_background` is not `true`):

- **Shape match** (necessary, not sufficient): the command text matches
  one of the enumerated blocking shapes below.
- **Not backgrounded** (necessary, not sufficient): the same `tool_input`
  object's `run_in_background` field is absent or not `true`.
- Only the conjunction denies. A backgrounded call with an identical
  command string passes unchanged — this is precisely how the check
  avoids weakening legitimate background use (a required property of the
  issue's acceptance bar), because backgrounding is read from the same
  call, not inferred from the command text.
- This conjunction now applies to exactly one shape (sleep/poll loops).
  The watch-family shape sits outside it entirely, per the revision
  above: watch commands never denied, so the conjunction never runs for
  them — they are dispositioned to allow before shape classification is
  even consulted for denial purposes.

A design alternative — parsing the shell to resolve `eval`/alias/variable
indirection and catch a renamed binary — was considered and rejected.
Every sibling `PreToolUse`+`Bash` hook in this repo (`impact-guard.sh`,
`contract-guard.sh`, `pr-preflight.sh`, `claim-scan-preflight.sh`,
`spec-index-preflight.sh`) tops out at literal command-text
regex/substring matching; none attempts shell-AST resolution. Building
that here would be new scope beyond every comparable check's accepted
ceiling in this codebase, and the issue's own text asks this bypass be
scoped honestly rather than closed — so it is named as a stated
limitation (below), not attempted.

## What will be done

### 1. New hook — `on-the-record/hooks/blocking-call-guard.sh`
`PreToolUse`+`Bash`, joining the existing matcher group in `hooks.json`
alongside `impact-guard.sh` et al. Shape, in order:

1. `case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) exit 0 ;; esac`
   — kill switch, identical convention to every sibling hook.
2. `[ -z "${CLAUDE_ROLE:-}" ] || exit 0` — orchestrator-only scoping,
   `retry-loop-bound.sh`'s exact gate, adopted verbatim (scout brief).
   Checked before stdin is even read, so a role session pays no parse
   cost and cannot be affected by this check under any payload shape.
3. Read stdin JSON (`tool_input.command`, `tool_input.run_in_background`).
   Missing/unparseable payload, missing `command`, or missing `python3`
   → **fail open** (exit 0) — this check only adds a refusal on top of
   normal tool execution; it never blocks on its own infrastructure
   failure, same posture as `retry-loop-bound.sh`'s documented trap and
   `approval-gate.sh`'s `gh`-lookup-failure fail-open case.
4. Classify `command` against the watch-family vocabulary first (below).
   Match, at any confidence including ambiguous → **never block**: if the
   call is foreground (`run_in_background` not `true`), emit
   `additionalContext` naming the background form and allow execution;
   if backgrounded or ambiguous, exit 0 with no message. This gate is
   checked *before* the blocking-shape pattern set so a command that
   happens to contain both watch vocabulary and sleep/loop text (e.g. a
   watch invocation piped through a retry sleep) still resolves to
   allow, not deny — the exemption is categorical, not a tiebreak.
5. No watch-family match → classify `command` against the blocking-shape
   pattern set (below, now a single shape). No match → exit 0 (allow, no
   cost imposed on ordinary commands).
6. Match found → check `run_in_background`. `true` → exit 0 (the
   compliant backgrounded case; passes unchanged, no denial, no
   `additionalContext` noise). Not `true` (absent, `false`, or any other
   value) → deny: `{"decision":"block"}` with a reason string naming (a)
   which shape matched and (b) the concrete background alternative for
   that shape.

#### Watch-family exemption (categorical, checked first)
`spawn.py watch` (with or without `--follow`), `spawn.py watchdog`, and
any command matching the spawn call's own built-in watcher-arming
vocabulary are exempt from refusal outright — foreground or background,
ambiguous or not. This is not a shape that can be denied; it is checked
and dispositioned to allow before the pattern set below ever runs.
Detection basis: `tool_input.run_in_background` when the payload exposes
it reliably. If a given harness payload shape does not expose
backgrounding reliably for a watch command, that is resolved by failing
open toward allow (never toward block) — per the operator's explicit
instruction, the design does not attempt a detection mechanism that
could misfire toward blocking a watch call. A foreground watch (or one
whose backgrounding status is ambiguous) still executes; it receives at
most an advisory `additionalContext` string naming the equivalent
`run_in_background: true` invocation, so re-arming into the background
form is a one-line copy-paste if the caller chooses it, but nothing is
withheld either way.

#### Blocking-shape pattern set (this issue's scoped enumeration, narrowed)
One shape remains refusable after the watch-family exemption above. The
`spawn.py watch`/watchdog shape that was previously paired with it in
this same pattern set is no longer a candidate for denial anywhere in
this design — it is fully covered by the exemption gate above instead:

- **sleep/poll loop**: command contains a shell loop keyword
  (`while`, `until`, `for`) together with `sleep` inside the same
  command string (covers `until ...; do sleep ...; done` and `while
  ...; do ... sleep ...; done` — the two shapes the issue names
  explicitly), OR a bare `sleep` whose argument is large enough to be a
  poll interval rather than a short pause (threshold: `sleep` with an
  argument >= 30, matching run.md rule 1's own ">=30s goes background"
  line, so the threshold is not invented for this check — it is the
  existing contract number). Refusal names the fix: background the
  script per run.md 규칙 1/2, or use the session's `Monitor`/wakeup
  tooling instead of a foreground poll.

No third catch-all shape is added beyond this one, and the watch-family
shape is not moved back into this pattern set — the operator's exemption
is categorical (section above), not a candidate for future re-inclusion
here. A narrower, correctly-scoped enumeration is preferred over a
speculative broad one per this repo's stated false-positive discipline
(#600's precedent).

#### Fail posture
Fail **open** on any parse/state/infra error (missing payload, bad JSON,
missing `command` key, missing `python3`) — this is an additive-safety
check layered on top of tool execution the harness already permits;
losing the check must never itself become a way to block ordinary work.
This mirrors every sibling `Bash`-matcher hook's stated posture
(`retry-loop-bound.sh`'s trap, `approval-gate.sh`'s explicit comment).
For watch-family commands specifically, this general infra fail-open is
reinforced by the stricter shape-level rule above (ambiguity fails open
toward allow even when the payload parses cleanly) — the two are
independent and both resolve to allow, never to block, for any watch
call the hook cannot classify with confidence.

#### Gaming-resistance posture (required by the issue text)
Stated honestly, not closed: this check is a command-*text* regex match,
the same ceiling every sibling `PreToolUse`+`Bash` hook in this repo
already accepts. A session that renames `spawn.py` to another filename,
wraps the call through `eval`, indirects through a shell variable or
alias, or invokes the same blocking primitive via a different binary
(e.g. a hand-rolled Python poll loop instead of shell `sleep`) is not
caught — the check never resolves shell semantics beyond substring/regex
matching on the literal command string. This is named as the residual
gap, not attempted to be closed, matching #600's own "residual gap,
stated plainly" precedent for the same class of check. What the check
*does* close: the sleep/poll-loop shape named by the issue, called by
its literal, unrenamed name — the observed failure mode, not a
hardened-against-adversarial-agent guarantee. The watch-family shape is
out of this posture entirely: it is never denied regardless of how it is
invoked, so gaming-resistance is not a concern for it — there is nothing
to game around a check that always allows.

#### False-positive posture
`run_in_background: true` on the identical command always passes,
regardless of shape match — the check never denies a call the caller has
already declared backgrounded, which is the concrete mechanism protecting
legitimate background use (issue's explicit "no weakening" requirement).
A short `sleep` (<30s, no loop keyword) never matches — the threshold is
the existing rule-1 number, not a new invented one, so a legitimate short
pause is never refused. Role sessions never reach the payload-parsing
step at all (gate 2, checked first) — the exempt case is structural, not
a classification outcome that could misfire.

### 2. `hooks.json` — register the new command
Add `blocking-call-guard.sh` to the existing `PreToolUse`+`Bash` array
(same matcher group as `impact-guard.sh`/`delegated-judgment-gate.sh`) —
no new matcher group, no new event.

### 3. `run.md` — cross-reference, no new rule text
The four turn-budget rules (#535) already state the *should*; this check
enforces a scoped subset of it mechanically. Add one sentence under rule
1 noting `blocking-call-guard.sh` refuses the sleep/poll-loop shape
pre-execution in the orchestrator session and always allows watch-family
commands (advisory-only for foreground watch), pointing at this file —
matching how #600's rule 4 was cross-referenced into the same section.
No rule renumbering; this is a mechanism note, not a new obligation (the
obligation already exists as rule 1).

### 4. Tests — `test_blocking_call_guard.py`
Following `test_decision_queue_stopgate.py`'s and
`retry-loop-bound.sh`'s existing harness shape (`_run()` helper posting a
JSON payload to the hook over stdin, asserting on stdout/exit code):

- **Red**: a `while ...; do sleep 5; done` poll loop, `run_in_background`
  absent or `false`, in an orchestrator payload (`CLAUDE_ROLE` unset) →
  `{"decision":"block"}`, reason names the shape and the background fix.
- **Green — backgrounded**: identical sleep/poll command with
  `run_in_background: true` → allow, unchanged.
- **Green — role session**: identical blocking command with `CLAUDE_ROLE`
  set → allow, unchanged (acceptance criterion's stated empty state).
- **Green — ordinary commands**: representative short/normal commands
  from this repo's own hook test fixtures (a plain `git status`, a
  `python3 -m pytest ...` run, a `sleep 2` with no loop) → allow,
  unchanged (acceptance criterion 2).
- **Green — watch-family, foreground**: `spawn.py watch --follow` /
  `spawn.py watchdog` with `run_in_background` absent or `false` → allow
  (never blocked), `additionalContext` present and names the equivalent
  `run_in_background: true` form.
- **Green — watch-family, backgrounded**: identical watch commands with
  `run_in_background: true` → allow, no `additionalContext` noise.
- **Green — watch-family, ambiguous**: a watch command against a payload
  shape that omits `run_in_background` in a way the hook cannot resolve
  (simulated malformed/partial `tool_input`) → allow, never block —
  proves the shape-level fail-open rule, distinct from the general
  infra-fail-open case below.
- **Green — watch/sleep co-occurrence**: a command matching both
  watch-family and sleep/loop vocabulary in the same string → allow
  (watch-family gate wins, checked first; never denied by the sleep/poll
  pattern).
- **Fail-open**: malformed JSON, missing `command` key → allow, exit 0.

### 5. Regression guard — `test_blocking_call_guard_regression_e2e.py`
Added to the phase-2 write set per the operator's explicit requirement
(issue #645 comment 5236257876, item 4): an end-to-end case proving the
standard spawn → background watch → re-arm loop still functions with
`blocking-call-guard.sh` active, plus a check that `spawn.py ps` shows no
increase in DEAD/unarmed watchers attributable to the hook
(observation-loss guardrail). Shape:

- Drive the real sequence a session performs: spawn a background process,
  arm `spawn.py watch` on it (backgrounded), let the hook evaluate that
  PreToolUse call, then re-arm/replace the watcher — with
  `blocking-call-guard.sh` wired into the same `PreToolUse`+`Bash`
  matcher group used in production, not a hand-simulated payload only.
- Assert the watch call at every step is allowed (never `block`), and
  that `spawn.py ps`'s DEAD/unarmed-watcher count before the sequence
  equals the count after — the hook must not be a contributor to
  observation loss under its own enforcement.
- This is additional to, not a replacement for, the unit-level
  watch-family cases in `test_blocking_call_guard.py` above — the e2e
  case exercises the real spawn/watch machinery together with the hook,
  where the unit cases exercise the hook alone against constructed
  payloads.

## Accumulation
One new hook file, two new test files (unit + regression e2e), one array
entry in `hooks.json`, one cross-reference sentence in `run.md` — not a
per-item inline `subprocess`/`gh` call site, and not a `roles/*.json`-style
repeated-file edit. If a third blocking shape needs adding later, it
extends the same pattern-set list inside this one file rather than
opening a new hook or call site — matching #600's own accumulation note
for the sibling check this issue's design mirrors. The watch-family
exemption is not part of that extensible pattern set — it is a fixed,
categorical gate, not a list entry a future shape could be added next to.

## Out of scope (this proposal)
- Implementing the above (phase 2 of this same PR, per contract v3 s19 —
  opens only after human Approve).
- Shell-AST-level parsing to close the renamed-command/`eval`/alias
  bypass — explicitly scoped out above, not attempted.
- Any change to `decision-queue-stopgate.sh` or #600's Stop-surface
  check — the two are complementary and independent; #645 does not touch
  #600's file.
- Detecting blocking shapes beyond the one now refusable
  (sleep/poll loops) and confirmed by this survey — no transcript
  evidence beyond the issue's own prose was available to step 1 to
  derive further shapes; a narrower correct enumeration is chosen over a
  speculative broader one. Watch-family is explicitly not a candidate for
  future denial — the operator's exemption is categorical, not a
  placeholder pending stronger detection.
- Detecting or hardening backgrounding-signal exposure for watch-family
  commands beyond `tool_input.run_in_background` — per the operator's
  instruction, an unreliable signal here resolves to fail-open-to-allow,
  not to a more elaborate detection mechanism; building one is out of
  scope for this proposal.

## Boundary sketch (context/container)
```
[Orchestrating session] --Bash tool call (command, run_in_background)--> [Claude Code harness]
[Claude Code harness] --PreToolUse stdin payload--> [blocking-call-guard.sh]
  gate 1: ORCHESTRATE_OFF?              -> exit 0 (kill switch)
  gate 2: CLAUDE_ROLE set?              -> exit 0 (role session exempt)
  gate 3: watch-family match (any confidence, incl. ambiguous)?
                                         -> yes, run_in_background==true or ambiguous: exit 0 (no message)
                                         -> yes, foreground (not true):
                                            exit 0 + additionalContext naming background form (still executes)
                                         -> no match: fall through to gate 4
  gate 4: sleep/poll-loop shape match?  -> no match: exit 0
  gate 5: run_in_background == true?    -> yes: exit 0 (compliant background call)
                                         -> no:  {"decision":"block", reason names alternative}
[blocking-call-guard.sh] --block/allow decision--> [Claude Code harness] --refuses or executes--> [Bash tool]
```
Contrast with #600 (Stop surface, turn *closing*):
```
issue #600: [Orchestrating session] --Stop event (no more tool calls this turn)--> [decision-queue-stopgate.sh]
             fires AFTER the turn's tool-call chain is already done; catches "declared waiting, didn't close."
issue #645: [Orchestrating session] --PreToolUse event (about to call Bash)--> [blocking-call-guard.sh]
             fires BEFORE the call executes; catches "about to block, wasn't backgrounded."
```
No shared file, no shared state, no ordering dependency between the two
checks — they compose by covering disjoint moments in the same turn.

## How you'll know it worked
- `python3 -m pytest on-the-record/hooks/test_blocking_call_guard.py -q`
  exits 0, including every red/green/fail-open case above (sleep/poll
  refusal cases plus all watch-family allow/advisory/ambiguous cases).
- `python3 -m pytest on-the-record/hooks/test_blocking_call_guard_regression_e2e.py -q`
  exits 0: the spawn → background watch → re-arm loop completes with the
  hook active, every watch call in the sequence is allowed, and
  `spawn.py ps`'s DEAD/unarmed-watcher count is unchanged before vs.
  after (observation-loss guardrail, stated next to this primary
  result).
- `hooks.json` lists `blocking-call-guard.sh` in the `PreToolUse`+`Bash`
  array; `gates/test_hooks_parity.py` (or its successor check) stays
  green against the updated file.
- Manual replay: an orchestrator-session payload for a `while ...; do
  sleep 5; done` poll loop with `run_in_background` absent is refused
  with a message naming the background fix; the identical payload with
  `run_in_background: true` passes; the identical payload with
  `CLAUDE_ROLE` set passes. A `spawn.py watch --follow` payload passes
  regardless of `run_in_background` value or absence, with
  `additionalContext` present only in the foreground case.
- `docs/specs/enforcement-boundary.md` gains a row for
  `blocking-call-guard.sh` (verdict `contract`, zero-install, ships with
  the plugin) in the same commit, and `docs/specs/reconciled-index.md`
  gets its matching entry — both required by this repo's own
  spec-index/boundary-completeness gates.

## What did not work
(none yet — appended live during phase 2 if anything breaks)
