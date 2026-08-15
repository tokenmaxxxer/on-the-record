---
proposal: docs/issue-1598/proposals/patrol-heartbeat-wiring.md
---

# Hunt record — patrol-heartbeat-wiring

## after-proposal — stance 1: patrol invocation independent of due-tick gating has no emission path outside the due_rc==0 branch

Verdict: FINDING — the proposal's patrol_tick counter is explicitly independent of both `tick` and the `poll-due` due/not-due outcome, but the only code path in poll-heartbeat.sh that ever prints anything to the Monitor channel (the `printed_text`/`diff_output` delta-suppression machinery the proposal says patrol output will be folded into) lives entirely inside `if [ "${due_rc}" -eq 0 ]`. On a non-due tick the script takes the silent `else` branch (poll-heartbeat.sh:298-302, explicitly documented at the #1220 comment as "non-due ticks are now fully silent"). Since poll_due()'s 60s TTL is shared with directive.sh (a turn-driven hook that also calls it), a tick landing on the patrol cadence can easily be non-due whenever a user turn consumed the TTL window first — this is the literal scenario the file's own header comment describes ("de-dups this tick against the two turn-driven hooks"). The proposal never reconciles this: it says patrol invocation rides "the existing loop's iterations" independently of due-gating, yet also says its output gets folded into "the tick's report text" (`printed_text`), a variable that is scoped to and only computed inside the due_rc==0 branch. As written, either patrol silently never fires on non-due ticks (contradicting the promised own-counter/own-cadence independence from #829's tick/due coupling — exactly the coupling bug the constraints section says it's avoiding), or an implementer bolts patrol invocation onto the due branch only, silently dropping promotions on ticks where the shared TTL gate says "not due" even though 10 minutes of wall clock (5 x 120s) has elapsed. Either way a promotion that should have fired produces no trace line and no error — a silent failure indistinguishable from "nothing to promote".

Kind: design-error
Seed: docs/issue-1598/proposals/patrol-heartbeat-wiring.md ("What will be done" section); on-the-record/monitors/poll-heartbeat.sh
cap_seconds: n/a (not told a cap)
tier: default
diff_stat_lines: n/a (docs-only proposal, no code diff yet — 2 new files, proposal ~110 lines)
started_at: 2026-08-15T00:00:00Z
ended_at: 2026-08-15T00:15:00Z

### Reproduce
Read on-the-record/monitors/poll-heartbeat.sh lines 171-302:
```
due_out="$(python3 "${CHECKOUT}/spawn.py" poll-due 2>&1 >/dev/null)"
due_rc=$?
if [ "${due_rc}" -eq 0 ]; then
    ... printed_text=... diff_output=... printf '%s\n' "${diff_output}"
else
    ... # fully silent, no printed_text/diff_output computed at all
fi
```
Compare against spawn.py:2358-2381 `poll_due()`: TTL is `POLL_INTERVAL_SEC = 60` seconds and the *same* atomic state (`runs/poll_state.json`) is also stamped by directive.sh's `UserPromptSubmit` hook on every user turn (per the header comment at poll-heartbeat.sh:1-11: "a THIRD caller of the same poll_due() TTL gate ... this gate's own lock-protected TTL check is what de-dups this tick against the two turn-driven hooks"). So any active session with turns firing more often than every 60s makes `due_rc != 0` on this loop's own 120s-cadence ticks routinely, including whichever tick happens to be the Nth patrol tick.

### Observed
The proposal's "What will be done" section states patrol invocation is gated purely by `patrol_tick % POLL_HEARTBEAT_PATROL_EVERY_N == 0` (independent of `tick`/due-gating, by explicit design in "Rationale"), then in the same paragraph says patrol output is folded "into the tick's report text so it is covered by the same delta-suppression the watchdog report already gets" — but that report text (`printed_text`) and delta-suppression machinery (`diff_output`) do not exist as a code path outside `if [ "${due_rc}" -eq 0 ]`.

### Expected
The proposal should specify how patrol invocation and its output emission behave on a tick that is due for patrol (Nth patrol_tick) but not due per `poll-due`'s shared TTL gate — either patrol must have its own emission path independent of due_rc (contradicting "fold into the same delta-suppression the watchdog report already gets"), or the design must explicitly accept and justify that patrol promotion is silently skipped/delayed whenever poll-due happens to be false on the Nth tick, with a trace line so the skip is visible rather than indistinguishable from "nothing to promote".

## after-proposal — stance: patrol emission silent-failure / injection / cadence probe

Verdict: FINDING — patrol_promote.py failures (non-zero rc) are silently swallowed; captured stderr is never printed or logged
Kind: silent-failure
Seed: on-the-record/monitors/poll-heartbeat.sh lines 320-357 (patrol block), gates/test_poll_heartbeat_patrol.py
cap_seconds: unknown (not provided by dispatcher)
tier: default
diff_stat_lines: unknown (not provided by dispatcher)
started_at: 2026-08-15T00:00:00Z
ended_at: 2026-08-15T00:10:00Z

### Reproduce
```bash
cat > /tmp/repro.sh << 'SH'
#!/bin/bash
set -u
CHECKOUT=/tmp/fake_checkout
mkdir -p "$CHECKOUT/gates"
cat > "$CHECKOUT/gates/patrol_promote.py" << 'PY'
import sys
print("Traceback: boom", file=sys.stderr)
sys.exit(1)
PY

_patrol_out="$(python3 "${CHECKOUT}/gates/patrol_promote.py" run "${CHECKOUT}" myrole 2>&1)"
_patrol_rc=$?
echo "rc=$_patrol_rc"
if [ "${_patrol_rc}" -eq 0 ] && [ -n "${_patrol_out}" ]; then
  echo "would process output"
fi
echo "loop finished, nothing printed about the failure: [$_patrol_out] was captured but discarded"
SH
bash /tmp/repro.sh
```
This mirrors on-the-record/monitors/poll-heartbeat.sh lines 337-353 exactly: `_patrol_out="$(python3 ... 2>&1)"` captures stderr, `_patrol_rc=$?` captures the exit code, but the only branch that inspects `_patrol_out` is gated on `[ "${_patrol_rc}" -eq 0 ]`. There is no `else` branch, no log-append call (contrast with the existing due_rc-gated branch at line 313-315, which does call `_poll_watchdog_log_append` on crash), and no stderr line is ever printed for a non-zero rc. The per-role for-loop simply continues to the next role, and the final `[patrol-poll] checked N role(s), M promotion(s)` line prints as if every role succeeded.

### Observed
```
rc=1
loop finished, nothing printed about the failure: [Traceback: boom] was captured but discarded
```
In the real script, a crashing `patrol_promote.py` for a given role produces zero Monitor-visible output for that role (no `[patrol-poll] <role>: N promotion(s)` line and no error line), and the final summary line still reports success-shaped counts, masking the crash entirely.

### Expected
On `_patrol_rc != 0`, the captured stderr (`_patrol_out`) should be surfaced — e.g. via `_poll_watchdog_log_append`, matching the existing due_rc-crash handling pattern at line 313-315 — so a broken patrol_promote.py invocation for a role is not indistinguishable from a healthy tick with zero promotions.
