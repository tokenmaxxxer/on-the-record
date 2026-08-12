---
proposal: docs/issue-927/proposals/implementation.md
---

# Hunt record — implementation

## after-proposal — stance 0: assume the gate/contract this proposal just touched is bypassable — find the bypass.

Verdict: FINDING — self-heal mode is gated purely by a CLI flag on `watch --follow`, with no binding to "this process is the detached auto-arm watcher"; any interactive/manual invocation that includes `--self-heal` gets the infinite re-attach loop the proposal reserves for auto-arm only, silently breaking the stated invariant "Interactive `watch --follow`'s current return-and-let-caller-rearm behavior must not change."
Kind: design-error
Seed: docs/issue-927/proposals/implementation.md ("What will be done" steps 1-3: `--self-heal` argparse flag threaded into `_watch(..., self_heal: bool = False)`, set only by the auto-arm Popen argv at spawn.py:5089-5091; gating is flag-presence only)
cap_seconds: 60
tier: default
diff_stat_lines: 281 (2 files: survey.md, proposal.md; no code yet)
started_at: 2026-08-12T01:18:34Z
ended_at: 2026-08-12T01:20:30Z

### Reproduce
Design as specified: `_watch(..., self_heal: bool = False)` and a new `ap.add_argument("--self-heal", action="store_true")` on the `watch` subcommand (spawn.py:4154 area, same parser as `--follow`). The only mechanism setting `self_heal=True` is presence of the CLI flag; there is no check tying it to "this invocation came from the detached auto-arm Popen call site" (e.g. no auto-arm-only env var, no pid/parent check, no separate hidden subcommand). Confirm no such binding exists in the current parser:
  grep -n "add_argument.*follow" spawn.py
  -> spawn.py:4154:    ap.add_argument("--follow", action="store_true", ...)
Once `--self-heal` is added next to it per step 1, any caller can run:
  python3 spawn.py watch --follow --self-heal --issue <n>
from an interactive terminal.

### Observed
Per the proposal's own step-3 description, when `self_heal` is true the wall-clock and stall branches (spawn.py:3494-3497, 3553-3556) `continue` the `while True:` loop instead of returning — i.e. the watcher never returns control to the caller until a genuine `session-end` or confirmed crash. An interactive user who passes `--self-heal` (accidentally, via copy-pasted auto-arm command, wrapper script, or shell alias) gets a foreground process that no longer honors the documented "current return-and-let-caller-rearm behavior" — it hangs indefinitely across stalls instead of returning so the caller can re-arm, exactly the behavior the proposal's constraints section says must not change for the interactive path.

### Expected
The proposal's own constraint states: "Interactive `watch --follow`'s current return-and-let-caller-rearm behavior must not change — only the auto-arm call path gains the loop, gated by a new flag." A flag on the same shared parser is not sufficient to guarantee this: gating should be structural (e.g. tied to how/where the process was launched, or a separate non-user-facing entry point) rather than a bare CLI flag any caller of the public `watch --follow` command can also pass.
