---
issue: 2156
role: implementation
loop_state: landed
code_under_review: same-commit
upstream:
  - path: on-the-record/directive/spawn-and-board.md
    sha: same-commit
commit_sha: same-commit
type: docs
breaking: false
verdict: pass
---

# issue-2156 — implementation record

## What was done

Added an explicit "NO REDUNDANT WATCHER, BY ANY MECHANISM" rule to
`on-the-record/directive/spawn-and-board.md` (the existing spawn/board
directive file, the most relevant home for this — no new file created).
It states: after `spawn.py` returns, an orchestrator session must not
build a separate standing watch loop for that spawn by any mechanism —
not a dedicated Agent whose sole job is polling it to completion, and not
a substitute with the same shape (a backgrounded `Bash(run_in_background:
true)` sleep-and-poll loop, a cron/schedule entry, or any other
timer-driven re-check). The rule targets the pattern (a standing loop
re-deriving status the platform already pushes), not one specific tool.
It names the mechanism reason: the spawn's own watcher process plus the
`spawn.py watch`/`--follow` poll cycle already surface
HEALTHY/RUNNING/anomaly/returned-PR events as background-task
notifications automatically, so a duplicate watcher only produces
content-free "still waiting" noise. The only sanctioned direct status
checks named are a one-shot `spawn.py ps` or `spawn.py watch --issue <n>
--role <r>` call.

Build-now bypass (`CORE_BUILD_NOW=1`, contract v3 s19a) was in effect for
this session, so no phase-1 proposal round ran — this is a direct
delivery on `issue-2156/implementation`.

## Why

canonical: gh issue view 2156 (issue body, live finding + acceptance
criteria)

Issue #2156's live finding: after `spawn.py <role> --issue n` (which
already arms a watcher process reporting HEALTHY/anomaly via the
Monitor/watchdog poll cycle), an orchestrator session additionally
spawned a general-purpose Agent whose only job was "watch this spawn to
completion." That agent had no way to block-wait for the spawn's
terminal state, so it self-polled, producing content-free "still
waiting" notifications roughly every 2-3 minutes, each burning 20+ tool
calls — pure duplicate overhead of what the built-in watchdog already
provides. Nothing in `spawn-and-board.md` (or any other directive file)
told an orchestrator session not to do this, so it stayed a one-off
judgment call rather than something enforced or documented, and could
recur in a future orchestrator session.

canonical: on-the-record/directive/spawn-and-board.md (this commit's
diff — the "NO REDUNDANT WATCHER, BY ANY MECHANISM" block)

A pre-landing warrant-hunter dispatch (stance 0: "assume the gate/rule
just touched is bypassable") surfaced that the first wording draft
scoped the prohibition to the `Agent` tool by name only, leaving a
`Bash(run_in_background: true)` sleep-and-poll loop as a textually
compliant bypass reproducing the same content-free-notification pattern.
The wording was revised in the same commit to prohibit the standing-loop
pattern regardless of mechanism, closing that gap.

## Upstream basis

- `on-the-record/directive/spawn-and-board.md` — same-commit (the file
  edited in this delivery).
- Issue #2156 body (live finding + acceptance criteria) — GitHub issue,
  not a repo path; read via `gh issue view 2156`.

## Open findings

None. The one warrant-hunter finding from the before-landing dispatch
(Agent-tool-only lexical scoping, allowing a Bash-loop bypass) was
resolved in this same commit before landing — see "What did not work"
below.

## Next steps

None — terminal state reached (`landed`).

## What did not work

canonical: on-the-record/directive/spawn-and-board.md (diff, first draft
vs. current)

The first wording draft of the new directive text scoped the
prohibition to the `Agent` tool only ("a separate Agent (general-purpose
or otherwise)"). A pre-landing warrant-hunter dispatch (stance 0,
before-landing transition) surfaced that this let a `Bash
(run_in_background: true)` sleep-and-poll loop calling `spawn.py` on a
timer reproduce the same content-free "still waiting" pattern while
remaining textually compliant with the Agent-scoped wording. Fixed by
rewording to prohibit the standing-loop pattern itself regardless of
mechanism (Agent, Bash background loop, cron/schedule entry, or
otherwise) before this commit landed.

## Skill verdicts

other mounted skills: not triggered (this delivery is a single prose
addition to an existing directive file — no code architecture, GoF
pattern, coupling/cohesion, or data-structure/algorithm decision was
involved).

## Acceptance evidence

canonical: UNMEASURED-with-reason: no acceptance command on record for
this target (prose-directive grep is a one-off check, not registered in
docs/specs/acceptance-commands.md — per the issue's own acceptance
section no mechanical test exists for prose guidance)

```
$ grep -n "NO REDUNDANT WATCHER" on-the-record/directive/spawn-and-board.md
34:  NO REDUNDANT WATCHER, BY ANY MECHANISM (issue #2156): after `spawn.py`
```

The grep above verifies the new guidance text is present in
`on-the-record/directive/spawn-and-board.md` and names the mechanism
reason (the built-in watchdog/`spawn.py watch` poll cycle already covers
this). Per the issue's own acceptance section this is a directive-only,
self-serviceable change — no mechanical test exists for prose guidance,
and none was authored.
