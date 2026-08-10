# Current-state survey — issue #645 (implementation role)

Scope: the 2026-08-10 comment adds two items beyond the already-approved
architecture design (PR #647): a wall-clock cap on activity-reset waits,
and a `--no-wait` fire-and-return spawn mode. This survey covers those two
additions; the PreToolUse refusal hook itself was already designed by the
architecture role (`docs/issue-645/proposals/2026-08-10-blocking-call-pretooluse-refusal.md`,
status: proposed, files already present on disk but **not yet committed on
this branch** — see below) and is not re-surveyed here.

## Uncommitted state found on this branch
A prior `issue-645/implementation` session left uncommitted, untracked work
matching that architecture proposal's write set exactly
(`on-the-record/hooks/blocking-call-guard.sh`,
`on-the-record/hooks/test_blocking_call_guard.py`,
`on-the-record/hooks/test_blocking_call_guard_regression_e2e.py`, plus
modified `hooks.json`/`run.md`/two `docs/specs/*.md`), and its PR-create
attempt failed (`No commits between main and issue-645/implementation`) —
the operator's stranded-relay comment asked for resume-or-close. No
`APPROVE issue-645/implementation` comment or PR review Approve exists for
the implementation role (checked: `gh issue view 645 --comments` — only
`APPROVE issue-645/architecture` is present, which authorizes the
architecture role's own deliverable, not this role's phase 2). Per
role-handoff contract v3 s19, this implementation role's phase 2 has not
been opened. This session therefore does not commit or build on that
stray phase-2-shaped work; it is left in place for the next implementation
phase-2 session to pick up once approval lands. This survey and its
proposal are this session's phase-1 deliverable, covering the additive
scope only.

## 1. `_await_bounded` (spawn.py:2802-2861)
Returns on whichever comes first: an unread `events.jsonl` line, or
`stall_timeout_min` (default 5 min, `--stall-timeout`) of **no session-log
size change**. `last_change` (spawn.py:2848-2851) resets on any size delta,
however small — a session that keeps emitting log bytes (verbose tool
output, thinking tokens) never trips the stall bound, however long the
call runs in wall-clock terms. There is no independent "return by T
regardless of activity" bound. The offset file (`_read_offset`/
`_write_offset`) already exists and is exactly the resume mechanism a
wall-clock-forced early return needs — the return does not need to be
"final," it needs to be resumable, and that plumbing is already in place
(events not yet read stay unread; the caller re-polls from the same
`offset_path` on the next call).

## 2. `watch --follow` (spawn.py:2943-3061, esp. 2987-3059)
`_watch()`'s `follow=True` path loops calling `_await_bounded` with the
same `stall_timeout_min` each iteration (spawn.py:3005) — comment at
2987-2996 states explicitly this is deliberate: "`_await_bounded` 자체는
바꾸지 않고 반복 호출한다... `_await_bounded` 는 호출 한 번의 stall 만
본다" (issue #451, #445 finding 2: `_await_bounded` only bounds a single
call's stall, not the loop's cumulative wall-clock). #451 added a
no-*progress* bound (the stall timeout itself); nothing bounds cumulative
wall-clock when progress (log growth) keeps happening. This is the same
gap as item 1, one layer up: a `--follow` loop against a chatty session
runs forever in wall-clock terms.

## 3. Fire-and-return spawn mode
`cmd_spawn()` (spawn.py:3717-3718): `bounded=a.issue is not None` — any
`--issue` spawn is `bounded=True` unconditionally, and `_spawn_one(...,
bounded=True)` always funnels through `_await_bounded` (spawn.py:4280-4281,
inside the parent-process branch after fork/detach at ~4257-4267). There is
no argparse flag that skips this wait — `--follow` (spawn.py:3496-3498)
only affects `_watch`'s repeat-call behavior, not `cmd_spawn`'s own
post-fork wait. The 2026-08-10 comment's premise ("ALWAYS spawn IN THE
BACKGROUND relies entirely on harness `run_in_background`") is accurate:
today, even a harness-backgrounded `spawn.py --issue N ...` call still
blocks *inside the spawn.py process itself* on `_await_bounded` before
returning control — backgrounding the harness call only prevents the
*Claude Code turn* from blocking, it doesn't change `spawn.py`'s own
behavior. A `--no-wait` flag needs to short-circuit `_spawn_one` before the
`_await_bounded` call, returning immediately after fork/detach with enough
info (workspace, log path, issue/role) for the caller to `spawn.py watch`
later — i.e., resume through the exact same `events_path`/`offset_path`
pair `_watch`/`_await_bounded` already read.

## Existing precedent for wall-clock bounding
`retry-loop-bound.sh` and `impact-guard.sh` (surveyed already by
architecture, `docs/issue-645/reports/architecture/survey.md`) are
PreToolUse hooks, not applicable here — items 1-2 are pure Python control
flow inside `spawn.py`, no hook surface involved. The precedent that does
apply: `WATCH_CRASH_RC = 2` (spawn.py:2864) shows this codebase's house
style for a bounded-wait function returning a *distinct* exit/return code
per reason-for-return (event vs stall vs crash) rather than overloading a
single sentinel — a wall-clock-cap return should follow the same pattern
(distinguish "returned because wall-clock cap hit, session still running"
from "returned because stall," both from "returned because event").

## Write-set implications for the proposal
- `spawn.py` — add a wall-clock parameter to `_await_bounded` (new
  optional arg, default disabled/no behavior change, so `_watch`'s
  existing single-call semantics are untouched unless a caller opts in);
  thread a `--max-wait`-style bound through `_watch`'s `--follow` loop so
  cumulative wall-clock across repeated `_await_bounded` calls is capped;
  add a `--no-wait` flag to the `spawn` subcommand that short-circuits
  `_spawn_one` before its `_await_bounded` call.
- Tests covering the above (repo convention: `test_spawn_*.py` alongside
  `spawn.py`, per existing test file naming already visible in the
  untracked `test_blocking_call_guard*.py` pattern and `git log` history
  of prior spawn.py test additions — confirmed by `ls *.py` at repo root
  showing existing `test_spawn*.py` files).
- `on-the-record/commands/run.md` — the turn-budget-rules section already
  amended (uncommitted, stray) for the PreToolUse hook; the wall-clock cap
  and `--no-wait` mode need their own doc line once built (phase-2 concern,
  not this proposal's write set unless the flag's existence needs
  documenting for orchestrator use — deferred to the phase-2 build, listed
  as an out-of-scope note).
