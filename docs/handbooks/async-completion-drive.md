# Autonomous async-completion drive (issue #878)

An orchestrator spawns a role, gets a mergeable PR back, and must self-drive
to merge + a 4-part `final_report` with no human turn. The mechanism splits
by process lifecycle — the two cases need genuinely different mechanisms,
not one mechanism with two names.

## Case 1 — interactive installed session (long-running, not `-p`)

The orchestrator is a live process. `spawn.py watch --issue <n> --follow`
already runs in the background and Claude Code's own task-notification
resumes the session on the next material event (#829/#835/#782 unchanged).
`on-the-record/hooks/directive.sh` states what the orchestrator does once
notified: the moment a notification reports the delegated PR
opened/mergeable/checks-passed, the very next action (same turn, never
deferred) is verify → `gh pr merge` → rebuild/re-check → emit the 4-part
`final_report` as the reply. No new polling engine — only the
post-notification instruction is new.

## Case 2/3 — headless (`claude -p`) invocation

**Hard boundary, stated plainly: a `-p` process that has already returned
`end_turn` cannot be reasoned with again in-process.** No hook, Monitor, or
watchdog cleverness revives a dead process — continuation can only come from
a new, external invocation (`code.claude.com/docs/en/headless.md`,
"Background tasks at exit"). `--resume "<session_id>"` is that new
invocation, not a resurrection of the old one.

- **`session_id` capture**: `spawn.py` reads the `ORCHESTRATOR_SESSION_ID`
  env var (set by whatever process launched the orchestrator's `-p` turn —
  an OS-level watchdog for a real install, or `harness/driver.py` for
  measurement) at roster-registration time and stores it on the roster
  entry (`spawn.py::_spawn_one`, the `session_id` field alongside the
  existing `pid`/`branch` tracking). Never fabricated — absent env var means
  `None`, meaning "this spawn used an interactive orchestrator, case 1
  handles it."
- **Ownership is per-*process*, not per-entry.** One orchestrator session
  routinely spawns more than one role, and every such roster entry shares
  the identical `session_id`. `spawn.py::_session_resume_claim` is a
  session_id-keyed atomic claim (reusing `ledger_check_and_stamp`'s
  check-and-stamp primitive, not a new lock) so only the first entry that
  becomes ready under a shared `session_id` triggers `--resume`;
  `spawn.py::_maybe_resume_for_ready_pr` is the call site, wired into
  `roster_watchdog`'s existing dead-and-completed branch.
- **The resume-invoke** (`spawn.py::_resume_orchestrator_session`) runs
  `claude -p "<nudge>" --resume "<session_id>"` in the background and does
  not wait — the resumed turn does its own verify→merge→rebuild→report,
  exactly like case 1's live notification does.

## Harness measurement (`harness/driver.py`)

`harness/signals.py`'s checks (`check_orchestration_to_completion`,
`check_autonomous_completion_reporting`) already only PASS when a genuine
`final_report`'s 4 parts are present in the transcript — unchanged by this
issue. The fix is entirely in what the driver constructs and feeds them:

- `driver.extract_session_id(first_turn_result)` — reads `session_id` from
  the first `claude -p --output-format json` run's parsed result. `None` if
  absent, never invented.
- `driver.poll_for_pr_ready(repo, branch, ...)` — polls `gh pr list` on a
  bounded interval/timeout for an OPEN, MERGEABLE PR.
- `driver.resume_orchestrator_session(session_id, nudge, ...)` — runs
  `claude -p "<nudge>" --resume "<session_id>" --output-format json` and
  returns its parsed result, or an explicit failure reason (`claude`
  missing, non-zero exit, unparseable output) — never raises.
- `driver.drive_multiturn_completion(...)` composes the three: on any break
  in the chain (no `session_id`, poll timeout, `--resume` failing), it
  returns `{"final_report": None, "unmeasured_reason": "<reason>"}` — the
  caller feeds that into the transcript so `signals.py` returns UNMEASURED
  with the reason recorded, **never a fabricated `final_report` and never a
  false PASS**. Only a genuine resumed-turn result produces a non-None
  `final_report`.

This makes #1 (`orchestration_to_completion`) and #4
(`autonomous_completion_reporting`) real, mechanically-checked signals: they
PASS only when an actual resumed orchestrator turn produced the report, and
UNMEASURED-with-reason whenever the multi-turn loop genuinely could not
complete on the harness host.

## Why not the rejected alternatives

- **Shell-script-only merge** (no LLM turn): rejected — merge/verify is a
  judgment call this repo's contract already routes through a reasoning
  turn (`/orchestrate:run` step 6); mechanizing it would silently drop the
  acceptance judgment the delegation model depends on.
- **Agent-tool subagents instead of `spawn.py`'s OS-process model**:
  rejected — a role's real fix-and-test cycle routinely exceeds the
  background-wait ceiling documented for backgrounded `-p` agents.
- **Driver merges the PR itself, never resumes the orchestrator**: rejected
  — that would make #1/#4 PASS on the driver's actions, not the
  orchestrator's own turn, which is exactly the false-PASS shape this issue
  forbids.
