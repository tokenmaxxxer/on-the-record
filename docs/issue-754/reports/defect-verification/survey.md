# Current-state survey (issue #754, defect-verification pass)

canonical: `git rev-parse --short HEAD` (run this session) = e20a3ac.

Independent verification pass against the merged architecture survey
(`docs/issue-754/reports/architecture/survey.md`, PR #761) at the
commit above. Every citation below was re-derived against current
HEAD, not copied from the architecture survey — several line numbers
had drifted since PR #761.

## Attempts and outcomes

**Attempt 1 (source: architecture survey — "no code path in `spawn.py`
has one role's own session invoke `_spawn_one()`/`spawn_cmd()` against
itself").** Outcome: **reproduced.**
canonical: `grep -n "_spawn_one(\|spawn_cmd(" spawn.py` (run this
session):
```
$ grep -n "_spawn_one(\|spawn_cmd(" spawn.py
3078:                _spawn_one(cwd, role, task, unattended=True, issue=issue,
4020:def spawn_cmd(settings_path: str, role: str, unattended: bool,
4059:                    _spawn_one(cwd, role, task, unattended=unattended,
5037:def _spawn_one(cwd: str, role: str, task: str, unattended: bool,
```
Line 3078's caller is inside `_respawn_or_cap` (def at spawn.py:3025) —
the crash/stall watcher, not a role choosing to compose a fix. Line
4059's caller is `spawn_cmd` itself (def at spawn.py:4020), invoked
only from the CLI's `argparse` dispatch. No call site originates from
role-session code. Verdict unchanged from the architecture survey; line
numbers re-derived (that survey cited 4382, current HEAD has it at
5037).

**Attempt 2 (source: architecture survey — "`consult_cmd()` ... is
opinion-only. A role that consults another role gets a text judgment
back into its own session; it cannot hand off actual work").** Outcome:
**reproduced.**
canonical: `sed -n '4095,4180p' spawn.py` (run this session) — no
`_spawn_one`/`spawn_cmd`/`gh pr` call anywhere in the function body.
`consult_cmd()`'s docstring at spawn.py:4095-4099 states "브랜치도
커밋도 PR 도 만들지 않는다" (creates no branch, no commit, no PR); its
subprocess prompt at spawn.py:4133-4142 asks for a fixed JSON shape
`{"answer","confidence","caveats"}` only. Re-derived from the
architecture survey's stale line 3556 to 4095 at current HEAD; verdict
unchanged.

**Attempt 3 (source: self-devised — does #958's deviation loop, which
the issue names as providing structure, actually reach a spawned role
session, or only the orchestrator?).** Outcome: **reproduced**, as a
gap: the deviation loop is orchestrator-only and never reaches a role
session.
canonical: `sed -n '1,10p' on-the-record/hooks/directive.sh` (run this
session):
```
case "${ORCHESTRATE_OFF:-}" in ""|0|false|no|off) ;; *) trap - EXIT; exit 0 ;; esac

# A spawned role session is never the orchestrator, even if the plugin leaks in.
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
```
`directive.sh` is the UserPromptSubmit hook that injects the goal loop
and, nested inside it, "YOUR DEVIATION LOOP (issue #803)"
(on-the-record/hooks/directive.sh:157-183: RECOGNIZE/CLASSIFY/
RESOLVE-AND-CONTINUE; the FILE-AS-ISSUE branch calls `spawn.py spawn
<role> "<task>" --issue <n> --background`). Line 10 exits before any of
that text is emitted whenever `CLAUDE_ROLE` is set — the env var a
role-handoff session (e.g. this defect-verification session) runs
under.
canonical: this session's own SessionStart reminders, visible earlier
in this same conversation, carried the defect-verification role
directive, warrant, scout, freelunch, and terse directives and no
deviation-loop text, consistent with the `CLAUDE_ROLE` early-exit
above.
So the loop that would let a role compose FILE-AS-ISSUE + spawn on its
own initiative fires only in the orchestrator's own `/run` conversation
— a role session that hits a problem outside its own `YOU DECIDE` scope
never receives RECOGNIZE/CLASSIFY/RESOLVE-AND-CONTINUE steering at
all; it is left to its own role rulebook's `BOUNDARY CASE` clause
(stop, leave a hand-off note, wait for the orchestrator next turn),
matching the architecture survey's "What a role does when it hits a
problem mid-task" section.

**Attempt 4 (source: self-devised — is poll-heartbeat.sh a counter-example, #922).** Outcome: **not-reproduced.**
canonical: `grep -n "spawn_cmd\|_spawn_one\|gh issue create\|gh pr merge" on-the-record/monitors/poll-heartbeat.sh` (run this session) — no match: poll-heartbeat.sh does not close the gap.
canonical: on-the-record/monitors/poll-heartbeat.sh:1-60 (read this
session) — the due-tick branch runs `spawn.py watchdog --auto-respawn`
in the foreground and echoes its captured stdout only; per the two
canonical citations just above it never files an issue, spawns a
different role, or merges.
It surfaces a report to the human Monitor channel for the orchestrator
to act on next turn — same human-turn dependency as Attempt 3, via a
different channel (background poll vs. foreground reply).

## Classification (MET / PARTIAL / GAP, ranked)

- **role-initiated cross-role spawn** (a role composes its own fix):
  **GAP**, file:line spawn.py:5037 (`_spawn_one`), call sites
  spawn.py:3078,4059 (both watcher/CLI only, per Attempt 1's canonical
  grep above). Rank: **High** — the exact primitive northpole req #5
  asks for; #958's deviation loop was purpose-built for it yet
  structurally cannot reach the sessions that would use it.
- **deviation loop reaching role sessions**: **GAP**, file:line
  on-the-record/hooks/directive.sh:10 (`CLAUDE_ROLE` early-exit, per
  Attempt 3's canonical `sed` above). Rank: **High** — #958 is the
  mechanism the issue names as "providing structure"; it exists but is
  scoped out of exactly the sessions (spawned roles) where unassisted
  problem-to-resolution composition would occur.
- **cross-role consult** (judgment only): **PARTIAL**, file:line
  spawn.py:4095-4142 (per Attempt 2's canonical `sed` above). Rank:
  Medium — lets a role get another role's judgment without a human
  turn, but the answer cannot become a branch/PR itself; this is the
  one piece of req #5 ("research AND discuss the fix") that already
  works unattended.
- **unattended reporting** (poll-heartbeat, #922): **PARTIAL**,
  file:line on-the-record/monitors/poll-heartbeat.sh:1-60 (per Attempt
  4's canonical grep above). Rank: Medium — surfaces watchdog state
  without a human prompt, but composes nothing: detection/report, not
  resolution.
- **same-role retry on crash/stall**: **MET** (retry, explicitly not
  composition), file:line spawn.py:3025 (`_respawn_or_cap`),
  spawn.py:3151 (`_self_trigger_respawn`).
  canonical: `sed -n '3025,3030p;3151,3156p' spawn.py` (run this
  session) confirms both defs exist at these lines, the same functions
  Attempt 1's grep found. Rank: Low.
- **issue authorship, merge**: **MET** (human-gated by design, out of
  scope for req #5), file:line on-the-record/commands/run.md:20-22.
  canonical: `grep -n "pr merge" spawn.py` (run this session) — no
  match: no automated-merge call exists in spawn.py. Rank: Low.

## Open findings (carried into phase 2)

**Finding 1** — addressed_to: architecture (or a follow-up
implementation issue). Severity band: **blocking** (High-centrality per
northpole req #5, independently reproduced against current HEAD).
Evidence: on-the-record/hooks/directive.sh:10 combined with
directive.sh:157-183 (the deviation-loop body that early-exit skips).

**Finding 2** — addressed_to: architecture. Severity band: **advisory**
(Medium — consult_cmd already covers "research and discuss"; the
missing half is the same primitive as Finding 1, not a separate build).
Evidence: spawn.py:4095-4142 (`consult_cmd`) has no code path back into
`_spawn_one`/`spawn_cmd`.
