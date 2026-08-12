---
proposal: docs/issue-1021/proposals/2026-08-12-decision-queue-stopgate-bounded-reblock.md
---

# Hunt record — decision-queue-stopgate-bounded-reblock

## after-proposal — stance 0: assume the gate just touched is bypassable — find the bypass

Verdict: FINDING — the planned `stop_hook_active` fix only guards the new tier2 latch; the untouched waiting-declaration branch ignores `stop_hook_active` entirely and still emits `decision:"block"` on it, contradicting the proposal's own constraint "`stop_hook_active=true` must never produce `decision: "block"` from this hook, on any tier."
Kind: design-error
Seed: docs/issue-1021/proposals/2026-08-12-decision-queue-stopgate-bounded-reblock.md ("Constraints" bullet 3, "What will be done" step 4) vs. on-the-record/hooks/decision-queue-stopgate.sh waiting-declaration branch
cap_seconds: 120
tier: default
diff_stat_lines: (proposal-only transition; see `git diff --stat a5d8c924c1 HEAD -- docs/issue-1021`)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:05:00Z

### Reproduce
```
rm -rf /tmp/otr-decision-queue-stopgate-test
export OTR_DECISION_QUEUE_STOPGATE_STATE_DIR=/tmp/otr-decision-queue-stopgate-test
mkdir -p /tmp/otr-fakecheckout
cat > /tmp/otr-fakecheckout/spawn.py <<'PYEOF'
import sys, json
if "flows" in sys.argv:
    print(json.dumps({"decision_queue":[{"issue":123,"pr":None,"age_hours":5.0}]}))
PYEOF
export TOKENMAXXXER_CHECKOUT=/tmp/otr-fakecheckout
unset CLAUDE_ROLE
payload='{"session_id":"sess1","last_assistant_message":"waiting for your decision","stop_hook_active":true}'
echo "$payload" | bash on-the-record/hooks/decision-queue-stopgate.sh
```

### Observed
```
{"decision": "block", "reason": "decision-queue-stopgate: waiting-declaration reply over a non-empty decision queue with no background-arm marker ..."}
```
even though `stop_hook_active` is `true` in the payload. (A second consecutive call with the same payload also blocks, via the tier2 fallthrough, since that path is likewise reached before any `stop_hook_active` short-circuit is applied by the untouched waiting-declaration branch's own latch semantics.)

### Expected
Per the proposal's own constraint, `stop_hook_active=true` should never yield `decision:"block"` "on any tier" — including the waiting-declaration branch, which the plan explicitly leaves untouched (step 4) and never wires `stop_hook_active` into. The plan as written ships this contradiction: the acceptance constraint is stated for "any tier" but the implementation steps only enforce it in the new tier2 code path.
