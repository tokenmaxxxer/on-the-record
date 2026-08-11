---
kind: current-state-survey
---

# Current-state survey — issue #878

## Background / context

code_under_review:
- on-the-record/hooks/directive.sh
- on-the-record/hooks/poll-rearm.sh
- on-the-record/hooks/stop-poll-rearm.sh
- on-the-record/monitors/monitors.json
- on-the-record/monitors/poll-heartbeat.sh
- spawn.py
- harness/signals.py
- harness/driver.py
- docs/issue-776/reports/execution-observation/run5.md
- docs/issue-803/proposals/2026-08-11-self-driven-deviation-loop.md
- docs/issue-803/reports/product-discovery/survey.md
- docs/specs/platform-capabilities.md

All read in full this session, per #793's verify-before-claim norm.

- **PR #877 / run5**: a fresh, plain `claude -p` orchestrator (`CLAUDE_ROLE`
  unset) filed a real GitHub issue (#874's fix works), delegated via
  `spawn.py implementation --issue 3`, and the role independently produced
  a correct, tested, `MERGEABLE` PR #4. The orchestrator's own `-p`
  process then returned `stop_reason: end_turn`, `terminal_reason:
  completed` (num_turns=14) with the delegated `spawn.py implementation`
  child still running detached.
  canonical: `docs/issue-776/reports/execution-observation/run5.md` step 6
  ("Orchestrator merge: NO ... zero processes referencing issue-3 ...
  remain"), read this session — it never merged PR #4, never emitted a
  `final_report`. Root cause explicitly left undiagnosed by that role,
  routed forward as this issue's step 1.

- **The three landed poll/notice mechanisms this issue must reuse, not
  duplicate** (canonical: the five files read above):
  1. `directive.sh` (UserPromptSubmit, turn-start) + `stop-poll-rearm.sh`
     (Stop, turn-end) both call the shared `poll_rearm_arm_if_due()`
     (`on-the-record/hooks/poll-rearm.sh`), which — when
     `spawn.py poll-due` says the 60s TTL has elapsed — backgrounds
     `spawn.py watchdog --auto-respawn` via `nohup ... & disown`. This is
     **turn-driven**: it requires a hook event (a human-typed prompt, or a
     turn ending) to fire at all.
  2. `on-the-record/monitors/monitors.json` + `poll-heartbeat.sh` (issue
     #835, `"when": "always"`): a plugin Monitor that auto-starts on a
     user-scope install and loops `sleep 60; poll_rearm_arm_if_due` for the
     lifetime of the session. Per `docs/specs/platform-capabilities.md`
     lines 34-49 (canonical, read this session): Monitors are
     **session-bound** (die with the session, do not survive its death),
     load only for **user-scope** installs, and are silently skipped where
     the Monitor tool is unavailable.
  3. `roster_watchdog()`/`spawn.py watch --issue N --follow`
     (`spawn.py` lines ~2241, ~3145, canonical: grep output this session)
     — the dual-channel (#782) event+poll reconcile that reports a role
     session's PR-opened / stall / session-end, including a
     dead-but-registered entry whose log shows a completed session-end
     pair (`docs/specs/platform-capabilities.md` lines 69-78, canonical).

  None of these three drive an LLM turn by themselves — they are shell
  processes (a hook script, a Monitor loop, a backgrounded watchdog). What
  actually re-invokes the model mid-session, per this very harness's own
  documented behavior (system-prompt Agent-tool description, and
  `docs/specs/platform-capabilities.md` lines 55-81, canonical) is Claude
  Code's own background-task **notification** mechanism: a
  `run_in_background: true` Bash/Task call surfaces a `<task-notification>`
  that resumes the SAME interactive session with a new turn when it
  completes. `directive.sh` (lines ~90-108, canonical, read this session)
  already tells the orchestrator to use exactly this — spawn, then
  `spawn.py watch --issue <n> --follow` in the background, "let
  notifications drive the next one."

- **Why run #5 still failed despite that instruction**: in `-p`
  (print/non-interactive) mode, the CLI process **exits for good** on
  `stop_reason: end_turn`; any of its own background Bash tasks are killed
  ~5s after the result returns and stdin closes. There is no process left
  to receive a later notification.
  canonical: `code.claude.com/docs/en/headless.md` §"Background tasks at
  exit", relayed via this session's `claude-code-guide` agent dispatch
  (read this session) — a documented CLI property, not a bug in this
  repo's hooks/Monitor/watchdog code, all three of which require a
  *living* process to do anything at all. Run #5's own transcript
  (`docs/issue-776/reports/execution-observation/run5.md` step 6, same
  citation as above) shows the orchestrator declaring "a watch is armed"
  and then ending its turn anyway — the single-process, single-turn
  nature of `-p` mode is the actual wall, not a missed instruction.

- **The one CLI capability nothing in this repo currently uses**:
  `claude -p --resume <session-id>` (and `--continue`) is documented,
  first-class support for resuming a `-p` session from a **separate,
  later process invocation**, threading the same session id. The exact
  idiom the docs give — capture `session_id` from a JSON-mode `-p` run,
  then a later, external process runs `claude -p "<followup>" --resume
  "$session_id"` — is structurally the shape #878 needs (an external
  re-invocation once ground truth says the delegated work is ready).
  canonical: `code.claude.com/docs/en/headless.md` §"Continue
  conversations", same agent-verified citation as above; and
  `grep -n "resume\|--continue" spawn.py on-the-record/hooks/*.sh`, run
  this session → zero matches anywhere in this repo — nothing here
  currently captures or reuses a session id at all.

- **Harness measurement side**: `check_orchestration_to_completion` and
  `check_autonomous_completion_reporting` both key on
  `transcript["final_report"]` being non-empty with 4 named parts; both
  are pure functions over a `transcript` dict the **driver** must
  construct, and do not themselves drive anything.
  canonical: `harness/signals.py` lines 27-36 and 61-71, read this
  session. `harness/driver.py` (read this session) currently launches
  exactly ONE `claude -p` process per run and, per run5's own account
  (`docs/issue-776/reports/execution-observation/run5.md` step 6),
  falls back to manually polling `gh pr view`/`ps aux` AFTER that process
  has already exited — i.e. today's driver observes the gap; it does not
  drive past it.

## The problem, stated without a solution attached (JTBD)

The issue text already names candidate mechanisms ("reuse the poll/Monitor
loop", "merge it", "final_report"). Restated without those attached:

- **Job performer**: an installed orchestrator session that has already
  delegated a fix to a role and is no longer being watched turn-by-turn by
  a human.
- **Job**: once the delegated work becomes ready (a mergeable, checked PR),
  act on it and report the outcome in a form a human can read later,
  without a human having to notice the PR appearing and prompt the
  session to continue.
  canonical: `on-the-record/hooks/directive.sh` lines ~90-131 (the
  spawn/watch/report block, read this session) — the existing text
  already describes this job for the case where a human IS present to
  read the eventual reply; it names no behavior for the human-absent case.
- **Circumstance**: the readiness event can arrive arbitrarily long after
  the delegating turn ended, and the delegating process itself may
  already be gone (headless `-p`, per run5's citation above) or merely
  idle with no human typing (interactive).
- **Desired outcome**: the requirement that triggered the delegation
  reaches a state the #776 harness's own signal checks can verify.
  canonical: `harness/signals.py` lines 27-36, 61-71 (same citation as
  above) — concretely, `check_orchestration_to_completion` and
  `check_autonomous_completion_reporting` both moving from FAIL to PASS
  (merged, rebuilt, 4-part `final_report`), with no human action between
  "delegate" and "done."

**Gap between the issue's framing and this restatement**: the issue's own
citation of "#829/#835/#782" already assumes those are the right reuse
targets. The evidence above only supports that for the *interactive*
case (a live process that can still receive a background-task
notification) — none of the three mechanisms give a **headless `-p`**
process anything to receive a notification WITH, because that process is
already gone (canonical: same headless.md citation above). The issue does
not distinguish these two circumstances; this survey's gap line is that
the design has to.

## Where this sits in the opportunity-solution tree

- **Outcome** (northpole, pre-existing, restated by #878 itself):
  requirement reached and reported with no human steering (req #1), via
  role-appropriate delegation (req #5), autonomously (req #4).
- **Opportunity** (child of #803's opportunity "the entered session's
  mid-task deviation-handling decision loop", but on the COMPLETION side
  rather than the deviation side): "the entered orchestrator session has
  no defined behavior for noticing and acting on delegated work that
  became ready after its own turn ended." Distinct from #803: #803 is
  about a NEW problem discovered mid-task; #878 is about the ORIGINAL
  delegated deliverable's completion signal arriving late.
  canonical: `on-the-record/hooks/directive.sh` lines ~90-131 (the
  spawn/watch/report block, read this session) covers arming a
  same-session wait; it has no branch for "the process that armed the
  wait is no longer alive to receive it."
- **Candidate solutions** (this survey enumerates; the proposal picks):
  (a) extend the Monitor/watchdog trio to also drive merge+report — ruled
  out by the citation above as inapplicable to the headless case, since
  none of the three can act without a living process; (b) keep the `-p`
  orchestrator's turn open (blocking, not backgrounded) until the
  delegated PR is ready, then merge+report in the same turn; (c) use
  `--resume`/`--continue` session chaining, driven externally (by the
  harness driver in measurement, or by the same poll/Monitor machinery's
  OS-level process in a real interactive install) once ground truth shows
  readiness.
- **Discriminating assumption test** (fixed by #878's own Acceptance): a
  #776 harness re-run where the orchestrator, with no human turn, reaches
  merge + a 4-part `final_report`; `check_orchestration_to_completion` and
  `check_autonomous_completion_reporting` move from FAIL to a REAL PASS,
  never a false one; where the loop genuinely cannot complete,
  UNMEASURED-with-reason per the issue's own acceptance line.
