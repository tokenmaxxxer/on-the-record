---
kind: scout-brief
---

# Scout brief — issue #878

Stage count: 1 (sweep only — the design space is fixed by the issue's own
reuse constraint, "#829/#835/#803, do not build a new scheduler"; scouting
targeted the one open factual gap that constraint left: does the Claude
Code CLI itself expose a reuse-eligible mechanism for resuming a `-p`
session across process boundaries?). Mode: single WebSearch call (parallel
fan-out not warranted for one factual lookup — SCALE GATE, scout-directive).

## Finding

The `claude` CLI's own headless-mode docs (not this repo's) document
session resumption across separate `-p` invocations as a first-class,
supported pattern:
- `claude -p "<prompt>" --continue` / `--resume <session-id>` both work in
  print mode, threading the same session id across invocations.
- The canonical documented idiom is exactly the shape #878 needs: capture
  `session_id` from a JSON-output `-p` run, then a LATER, SEPARATE process
  invokes `claude -p "<followup>" --resume "$session_id"`.
- A `-p` process's own background Bash tasks are killed ~5s after the
  process returns its result and stdin closes — confirming run #5's
  finding 1 mechanically (a nohup'd `spawn.py` child does not keep the
  parent `-p` process, or its notification channel, alive).
- Background AGENT-tool subagents (not OS-level `nohup` children) are
  exempt from that 5s kill and are awaited up to a configurable ceiling
  (`CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`, default ~10 min) — noted as an
  adopt/skip signal below, not something this proposal builds on.

## Must-be / adopt / skip

- **Must-be** (what any correct design has to satisfy): a `-p` process
  that already returned `end_turn` cannot be reasoned with again — nothing
  in-process can revive it. Continuation MUST come from a separate,
  later `claude -p --resume <id>` invocation, driven by something outside
  that dead process.
- **Adopt**: `--resume <session-id>` chaining as the reuse-eligible primitive
  for headless multi-turn continuation — it is existing CLI surface, not a
  new scheduler, and composes directly with the harness driver's existing
  dual-channel poll (#782) that already inspects ground truth externally.
- **Skip**: re-architecting delegation to route through Agent-tool
  subagents (which the 10-min background-wait ceiling would help) instead
  of `spawn.py`'s OS-process model — out of scope for this design; noted
  only as a rejected alternative below because a role's fix routinely
  exceeds any single-digit-minute ceiling.

## Gap line

The current repo state (directive.sh, poll-rearm.sh, spawn.py) has zero
references to `--resume`/`--continue` anywhere — the missing piece is not
a missing platform capability, it is that nothing in this repo's own
orchestrator flow or harness driver invokes it yet.

Sources:
- https://code.claude.com/docs/en/headless.md ("Continue conversations", "Background tasks at exit")
