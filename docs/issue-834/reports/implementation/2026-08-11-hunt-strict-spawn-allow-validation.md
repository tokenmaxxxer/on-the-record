---
proposal: docs/issue-834/proposals/strict-spawn-allow-validation.md
---

# Hunt record — strict-spawn-allow-validation

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: NO FINDING
Seed: docs/issue-834/proposals/strict-spawn-allow-validation.md (design not yet ported to
  on-the-record/hooks/spawn-allow-gate.sh); reference implementation read from
  on-the-record/hooks/merge-allow-gate.sh lines 91-129 (issue #824's shlex-based check, which
  the proposal says it will port verbatim in shape).
cap_seconds: 60
tier: default
diff_stat_lines: 0 (docs-only phase-1, no code touched yet — proposal doc only)
started_at: 2026-08-11T10:56:00Z
ended_at: 2026-08-11T11:02:30Z

Tried, live, against a throwaway Python script reproducing the exact
`shlex.shlex(cmd, posix=True, punctuation_chars=True)` +
`_is_operator_token` design from merge-allow-gate.sh (ported in shape to the
`[PYBIN, SPAWN_PATH, *tail]` / `["cd", DIR, "&&", PYBIN, SPAWN_PATH, *tail]`
shapes the proposal describes):

- Unquoted/adjacent operators with no whitespace (`foo;evil`, `foo&&evil`,
  `foo|evil`, `1>/tmp/pwned;touch`, `2>&1;touch /tmp/PWNED`): shlex reliably
  splits every occurrence of `;`, `&&`, `|`, `>`, `&`, `<` into its own
  token regardless of adjacency to non-punctuation text (confirmed via
  direct tokenization dump) — each such token is composed entirely of
  operator characters and gets caught by `_is_operator_token`, matching
  bash's real (whitespace-independent) operator recognition. No gap here.
- Process substitution in the `cd` DIR slot or task-text tail
  (`cd <(touch /tmp/PWNED) && python3 spawn.py ...`,
  `python3 spawn.py review <(id>/tmp/PWNED)`): not `$(`/backtick, so the
  upfront reject doesn't catch it directly — but shlex tokenizes `<(` as
  its own token composed entirely of operator chars (`<`, `(` are both in
  `punctuation_chars`), so it's either flagged by `_is_operator_token`
  directly, or (in the `cd` case) breaks the required `tokens[2] == "&&"`
  shape match entirely, falling through unreached. No allow either way.
- Backslash-escaped operators (`foo\;evil`) and bash ANSI-C-quoted
  operators (`foo$'\073'touch /tmp/PWNED`): shlex's parse of these differs
  textually from bash's real interpretation (shlex doesn't understand
  `$'...'` and produces a different literal token than bash's actual
  single argv element `foo;touch`), but in both bash's real behavior and
  shlex's approximation, the semicolon-shaped byte stays *inside one
  argument* — it never becomes a second command. Confirmed with
  `bash -c 'set -x; echo python3 spawn.py review foo$'"'"'\073'"'"'touch
  /tmp/PWNED'`: the trace shows `'foo;touch'` as a single quoted argv
  element, not two commands. This is tokenizer-output drift, not a
  privilege/execution bypass (no reproduction of a wrong `allow` +
  attacker-controlled side effect).
- Env-var indirection in place of `$(...)`: an unquoted `$VAR` token is
  never expanded by shlex (matches bash's real parse-time operator
  recognition, which happens before expansion) and either fails the
  SPAWN_PATH-ends-with-`spawn.py` shape match (falls through unreached) or,
  if it's in `tail`, is inert plain text — bash does not re-interpret
  metacharacters that appear *inside* an expanded variable's value as
  operators, so no injection path here either.

No shape was found where this design's shlex tokenize-then-check-operator-
tokens approach classifies a command as one of the two allowed shapes with
no operator-only token in `tail`/`DIR`, while bash itself still executes a
second, attacker-controlled command. Everything tried either (a) gets
correctly flagged as an operator token by `_is_operator_token`, (b) fails
the strict shape match and falls through unreached (fail-open-to-no-allow,
same as today), or (c) changes only the literal text of a single argument
passed to `spawn.py`, never causing a second command to run. Time budget
spent on live probing rather than static reasoning; stopping here with no
reproduction to report.

## before-landing — stance 1: assume this change and another plugin's rule cancel each other — find the pair

Verdict: FINDING — retry-loop-bound.sh's fatigue "allow" grants permission for the exact
  spawn.py command shape spawn-allow-gate.sh's new shlex check correctly refuses, once any
  unrelated gate has denied that identical string 5 times and stops denying it (state change,
  transient `gh` failure, etc.) — the fatigue-allow never re-examines command content.
Kind: composition
Seed: on-the-record/hooks/spawn-allow-gate.sh (this build's diff) plus
  on-the-record/hooks/retry-loop-bound.sh (issue #507, unrelated pre-existing hook, same
  PreToolUse Bash matcher group in on-the-record/hooks/hooks.json) and
  on-the-record/hooks/plan-order-guard.sh (issue #659, unrelated pre-existing deny gate on
  `spawn.py <role> ... --issue <n>` commands, used here only as a realistic source of an
  unrelated, state-dependent prior denial for the same command string).
cap_seconds: 120
tier: default
diff_stat_lines: 130 insertions(+), 32 deletions(-) (2 files: spawn-allow-gate.sh,
  test_spawn_allow_gate.py — matches dispatcher-stated +130/-32)
started_at: 2026-08-11T11:05:00Z
ended_at: 2026-08-11T11:22:00Z

### Reproduce

```bash
cd on-the-record-issue-834-implementation   # repo root
STATE_DIR="$(mktemp -d)"
mkdir -p "$STATE_DIR/otr-retry-bound" "$STATE_DIR/otr-role-bind"
CMD='cd $(touch /tmp/pwned_poc)&&python3 spawn.py implementation "task" --issue 834'
SESSION="poc-session"

# 1) confirm spawn-allow-gate.sh's new strict check correctly gives NO allow
#    signal for this command (the "`cd $(...) &&`" bypass shape this build closed):
PAYLOAD=$(python3 -c "
import json
print(json.dumps({'session_id': '$SESSION', 'tool_name': 'Bash',
                   'tool_input': {'command': '''$CMD'''}}))
")
CLAUDE_ROLE="" OTR_ROLE_BIND_STATE_DIR="$STATE_DIR/otr-role-bind" \
  TOKENMAXXXER_CHECKOUT="$(pwd)" \
  bash on-the-record/hooks/spawn-allow-gate.sh <<< "$PAYLOAD"
echo "spawn-allow-gate exit: $?"   # -> 0, empty stdout: correctly no allow

# 2) simulate 5 prior denials of the SAME exact command string by an unrelated
#    gate (plan-order-guard.sh, which matches spawn.py commands via its own
#    loose `\bspawn\.py\s+(\S+)` regex and denies for plan-order reasons that
#    have nothing to do with the injected payload):
POST_PAYLOAD=$(python3 -c "
import json
cmd = '''$CMD'''
resp = 'PreToolUse:Bash hook error: [plan-order-guard: refused — issue #834 step 2 refused: prerequisite step 1 is not done yet]'
print(json.dumps({'session_id': '$SESSION', 'tool_name': 'Bash',
                   'tool_input': {'command': cmd}, 'tool_response': resp}))
")
for i in 1 2 3 4 5; do
  CLAUDE_ROLE="" OTR_ROLE_BIND_STATE_DIR="$STATE_DIR/otr-role-bind" \
    OTR_RETRY_BOUND_STATE_DIR="$STATE_DIR/otr-retry-bound" \
    bash on-the-record/hooks/retry-loop-bound.sh post <<< "$POST_PAYLOAD" >/dev/null
done

# 3) attempt 6 (count now in [K, 2K)): retry-loop-bound.sh's "pre" mode on the
#    SAME malicious command, independent of whether plan-order-guard.sh would
#    still deny it this time (a state change / transient `gh` lookup failure
#    makes plan-order-guard.sh fail-open on this later call — it fails open
#    on any `gh issue view` non-zero return per its own source):
PRE_PAYLOAD=$(python3 -c "
import json
cmd = '''$CMD'''
print(json.dumps({'session_id': '$SESSION', 'tool_name': 'Bash', 'tool_input': {'command': cmd}}))
")
CLAUDE_ROLE="" OTR_ROLE_BIND_STATE_DIR="$STATE_DIR/otr-role-bind" \
  OTR_RETRY_BOUND_STATE_DIR="$STATE_DIR/otr-retry-bound" \
  bash on-the-record/hooks/retry-loop-bound.sh pre <<< "$PRE_PAYLOAD"
```

### Observed

Step 1 (spawn-allow-gate.sh, new strict check): exit 0, empty stdout — correctly
no allow signal for `cd $(touch /tmp/pwned_poc)&&python3 spawn.py implementation "task" --issue 834`.

Step 3 (retry-loop-bound.sh pre, 6th identical attempt): exit 0 with stdout —

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
 "permissionDecisionReason": "retry-loop-bound: this exact Bash on 'cd $(touch /tmp/pwned_poc)&&python3 spawn.py implementation \"task\" --issue 834' has been denied 5 times this session with no change between attempts. Last deny reason: plan-order-guard: refused — issue #834 step 2 refused: prerequisite step 1 is not done yet. Retrying identically will abort this action class after 10 denials.",
 "additionalContext": "..."}}
```

`retry-loop-bound.sh` grants `permissionDecision: allow` for the identical command
string spawn-allow-gate.sh's new shlex-based shape check just, correctly, refused to
allow — based purely on the (tool_name, verbatim command string) retry-count
signature, with zero re-inspection of the command's shape/content. Its own allow
does not depend on spawn-allow-gate.sh's verdict at all, and it stays keyed to
whatever the *previous, unrelated* denying gate's reason text was. If the original
denier (plan-order-guard.sh here, used only as a realistic example — any
state-dependent or fail-open gate works the same way) does not also fire a fresh
`exit 2` on this particular attempt — plausible any time the denied condition is
state-dependent (plan order becomes satisfied, a PR's `landing_readiness`
flips, or, as plan-order-guard.sh's own source shows, its `gh issue view`
subprocess call simply fails and it fails open) — this hook's `allow` is the
only permission signal Claude Code's host classifier sees for that event, per
the fail-open-unless-another-hook-still-denies composition rule this codebase's
own comments describe (on-the-record/hooks/merge-allow-gate.sh lines ~24-27:
"an existing deny gate's exit-code-2 on the same call still wins over this
hook's JSON allow *when both fire*" — the qualifier "when both fire" is exactly
the gap this reproduces).

### Expected

A generic retry-fatigue hook that grants `permissionDecision: allow` for a Bash
command should not be able to out-live the specific, content-aware gate (here,
spawn-allow-gate.sh's shlex shape check) that is the one actually responsible for
judging whether that command is safe to auto-allow — either by re-consulting the
content-aware gates before granting its own "allow", or by never emitting "allow"
for command shapes those gates are scoped to but have not currently opined on.
As shipped, `retry-loop-bound.sh`'s allow is keyed only on retry-count-for-an-
identical-string plus whichever unrelated gate happened to deny it last, so it
can end up being the accidental source of the same "allow" bypass this build's
stricter spawn-allow-gate.sh check was written to close.
