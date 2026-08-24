---
proposal: docs/proposals/2026-08-24-spawn-watcher-guidance.md
---

# Hunt record — spawn-watcher-guidance

## before-landing — stance 0: assume the gate/rule just touched is bypassable — find the bypass.

Verdict: FINDING — the new NO REDUNDANT WATCHER AGENT text scopes its prohibition to the Agent tool ("do not additionally launch a separate Agent (general-purpose or otherwise) ... never a standing watcher agent"), so a Bash `run_in_background` polling loop that calls `spawn.py`/`spawn.py ps` on an interval reproduces the exact forbidden pattern (content-free "still waiting" notifications every couple of minutes) while falling entirely outside the rule's literal reach.
Kind: design-error
Seed: on-the-record/directive/spawn-and-board.md lines 34-46 (13-line NO REDUNDANT WATCHER AGENT addition, issue #2156)
cap_seconds: 60
tier: default
diff_stat_lines: 13
started_at: 2026-08-24T14:55:59+09:00
ended_at: 2026-08-24T15:00:30+09:00

### Reproduce
canonical: on-the-record/directive/spawn-and-board.md:34-46 (read directly, quoted below verbatim)

Lines 34-46 read: "NO REDUNDANT WATCHER AGENT (issue #2156): after `spawn.py` returns, do not additionally launch a separate Agent (general-purpose or otherwise) whose sole job is to poll that spawn to completion and report back. ... the only sanctioned direct status check is a one-shot `spawn.py ps` or `spawn.py watch --issue <n> --role <r>` call, never a standing watcher agent." Both operative nouns ("a separate Agent (general-purpose or otherwise)", "a standing watcher agent") name the Agent tool specifically; the paragraph never mentions the Bash tool or a background shell loop as a covered case.

canonical: `grep -rn "polling loop\|while true\|run_in_background" on-the-record/directive/` — result: matches only spawn-and-board.md:12 ("ALWAYS spawn IN THE BACKGROUND (run_in_background: true)") and delegation-loops.md:20 ("run_in_background. When two roles should judge concurrently..."); no directive text forbids a Bash background poll loop.

canonical: `python3 spawn.py --help` — result: exit 0, usage lists `role` as an optional positional with helptext "역할. 생략하면 상태만 보여준다" (role omitted -> status-only output), so `spawn.py -C <repo> --issue <n>` with no role is the "sanctioned" one-shot status call the directive names by "spawn.py ps"-style usage.

Composing the two results above: `Bash(run_in_background: true): while true; do python3 spawn.py -C <repo> --issue <n>; sleep 120; done` executes nothing but that sanctioned one-shot status call, repeated on a timer, launched via the Bash tool rather than the Agent tool — it is not textually "a separate Agent" or "a standing watcher agent" per lines 34-46's wording, yet produces the identical periodic status-poll-and-notify pattern the rule exists to eliminate.

### Observed
canonical: on-the-record/directive/spawn-and-board.md:34-46 — the prohibition clause is grammatically and lexically scoped to the `Agent` tool ("a separate Agent", "a standing watcher agent"); no clause in this file or in delegation-loops.md/monitor-mode.md (both read in full this session) generalizes the prohibition to any standing process, regardless of which tool implements the poll loop.

### Expected
The prohibition should name the pattern (a standing loop that repeatedly polls spawn status and reports "still waiting") independent of which tool implements it, e.g. "do not launch a separate Agent, background Bash loop, or any other standing process whose sole job is to poll a spawn to completion" — otherwise the rule is bypassed by switching tools while keeping the exact behavior it was written to forbid.
