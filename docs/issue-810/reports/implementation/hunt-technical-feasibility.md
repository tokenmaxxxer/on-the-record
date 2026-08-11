---
proposal: docs/issue-810/proposals/technical-feasibility.md
---

# Hunt record — technical-feasibility

## before-landing — stance 3: assume the rule as written cannot hold — find the state nothing maintains

Verdict: FINDING — spawn-allow-gate.sh's "no unquoted shell chaining" invariant only checks for `&&`, `;`, `|` and misses unquoted `$(...)` command substitution (and backticks), so it emits `permissionDecision: "allow"` for a command that actually executes arbitrary shell code as a side effect of argument expansion.
Kind: design-error
Seed: on-the-record/hooks/spawn-allow-gate.sh (new PreToolUse/Bash hook, issue #810 SCOPE EXTENSION 2), on-the-record/hooks/hooks.json, on-the-record/hooks/test_spawn_allow_gate.py
cap_seconds: 120
tier: default
diff_stat_lines: ~250
started_at: 2026-08-11T18:10:00Z
ended_at: 2026-08-11T18:23:00Z

### Reproduce
```
cd on-the-record
export TOKENMAXXXER_CHECKOUT="$PWD"
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"python3 spawn.py $(touch /tmp/PWNED_MARKER)"},"session_id":"x"}' > /tmp/payload.json
env -u CLAUDE_ROLE bash hooks/spawn-allow-gate.sh < /tmp/payload.json
# then, separately, show the identical command string actually executes the substitution:
rm -f /tmp/PWNED_MARKER
bash -c 'python3 spawn.py $(touch /tmp/PWNED_MARKER)' 2>/dev/null
ls -la /tmp/PWNED_MARKER
```

### Observed
The hook prints:
```
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "permissionDecisionReason": "spawn-allow-gate: orchestration session (CLAUDE_ROLE unset) invoking this checkout's own spawn.py with no unquoted shell chaining — issue #810 SCOPE EXTENSION 2."}}
```
i.e. it grants "allow" and its own reasoning text asserts "no unquoted shell chaining" — while running the same exact command string via bash creates `/tmp/PWNED_MARKER`, proving arbitrary code execution occurred through the `spawn.py` argument list, which the hook never inspected.

### Expected
The chaining/injection check the hook's own comments describe ("this hook only ever ADDS a permission signal... never on any word inside the command's arguments" / "no further shell chaining ... outside quoted argument text") should also reject unquoted command substitution (`$(...)`, backticks) and other shell metacharacters capable of independent execution (e.g. process substitution `<(...)`, `>(...)`), not just `&&`, `;`, `|`. As written, the regex `re.search(r"&&|;|\|", stripped)` leaves this class of injection completely unreached, silently granting "allow" for commands that execute attacker-controlled code outside the audited spawn.py invocation.

Note: dispatcher-provided hunt-record path `docs/issue-810/reports/hunt-technical-feasibility.md` was rejected by board-gate ("belongs to another role"); this section was written instead to `docs/issue-810/reports/implementation/hunt-technical-feasibility.md`, the role-scoped location board-gate admits for the `implementation` role on this branch.
