# Survey: issue-1597 post-merge patrol wiring (E1)

## Write set (projected, none exist yet — plain-text, not backticked, so
record-lint's path-reach check does not treat them as broken references)

- gates/patrol_wiring.py — new module: kill-switch check, should_fire
  call, up-to-3-role selection reusing judge's Haiku prefilter,
  judge_cmd invocation per selected role, patrol_board.run for roles
  with new queue entries.
- gates/test_patrol_wiring.py — unit + regression tests, including the
  required respawn/anti-loop regression test.
- on-the-record/commands/run.md — merge step gets a new instruction line.
- .on-the-record/patrol-disabled — not written by this repo; a marker
  file an operator creates to trip the kill-switch.
- docs/issue-1597/reports/implementation/survey.md — this file.
- docs/issue-1597/proposals/patrol-wiring-e1.md — the phase-1 proposal.

## What exists already

canonical: `gates/patrol_trigger.py` (full file, read directly this
session)
`should_fire(event)` takes `event = {"changed_files": [str, ...]}` and
returns False when there are no changed files, or when every changed
file is a patrol-produced artifact (the artifact set is
`_PATROL_ARTIFACT_PATHS`/`_PATROL_ARTIFACT_PREFIXES` near the top of the
file). `run_if_eligible(event, repo_root, lane="diff")` wraps
`should_fire` and calls `patrol_queue.run_scan` when eligible. The
module's own docstring says it is not wired into a git-native
`.git/hooks/post-merge` file and is meant to be called from the
merge-command seam instead — that is the gap issue #1597 asks E1 to
close.

canonical: `spawn.py`, `_judge_prefilter` and `judge_cmd` functions, read
directly this session
`_judge_prefilter(role, spec, diff_summary, cwd)` is the existing
Haiku-model jurisdiction prefilter (issue #1587): one cheap call asking
whether a diff falls inside a role's rulebook jurisdiction at all. Its
docstring states it fails open (returns relevant=True) on any call
failure, timeout, or parse failure, by design — a cost-saving device,
not a judgment device.
`judge_cmd(role, merge_sha, cwd=None)` is the full read-only pipeline for
one role against one merge sha (prefilter -> judge -> validator ->
enqueue). It enforces its own per-merge role cap
(`JUDGE_MAX_ROLES_PER_MERGE`, checked against a helper that counts
`verb=judge` trace lines carrying that merge sha) and its docstring
states it always writes one trace line regardless of outcome. `judge_cmd`
takes a single `role` argument — it does not itself loop over roles or
select which roles apply.
canonical: `spawn.py`, the block in `judge_cmd` that loads
`roles/<role>.json`, read directly this session
The known-roles source `judge_cmd` reads per call is `roles/*.json` — the
same directory E1's own role-iteration would walk.
Design read: issue #1597's "select up to 3 roles ... by REUSING judge's
existing Haiku prefilter" maps to E1 iterating `roles/*.json` and calling
`judge_cmd(role, merge_sha)` once per candidate role up to a 3-role cap,
letting `judge_cmd`'s own internal `_judge_prefilter` call do the
jurisdiction filtering per role — this avoids importing the private
`_judge_prefilter` symbol directly and avoids recomputing the diff
summary a second time outside `judge_cmd`. Whether E1's 3-role cap
becomes its own counter or reuses `JUDGE_MAX_ROLES_PER_MERGE` directly is
left as an open design question for the proposal, not settled here.

canonical: `gates/patrol_board.py`, `run_patrol_board` and `main`, read
directly this session
CLI shape: `python3 gates/patrol_board.py run <repo-root> <role>
[--dry-run] [--queue PATH] [--date YYYY-MM-DD]`. The programmatic entry
point is `run_patrol_board(root, role, queue_path, dry_run, date)`,
ETag-conditional on read and budget-checked/serialized on write (a daily
write-budget cap with a drop-and-record fallback). Its own logic already
treats an unchanged board body as a no-op write. Issue #1597's own
phrasing ("patrol_board.run for roles that got new queue entries") maps
to gating each `patrol_board.run` call on that role's `judge_cmd` call
having returned a non-empty `enqueued` list, rather than calling it
unconditionally for every candidate role.

canonical: `gates/patrol_board.py` and `gates/patrol_trigger.py`, both
importing `patrol_queue` and referencing `patrol_queue.QUEUE_REL_PATH`,
read directly this session
Both modules point at the same on-disk queue file via
`patrol_queue.QUEUE_REL_PATH` — this is the shared state E1 threads
should_fire -> judge_cmd -> patrol_board through; no new queue-location
constant should be introduced by the wiring module.

canonical: `docs/issue-1582/proposals/2026-08-15-tier1-role-patrol-pilot.md`
and `gates/patrol_trigger.py`'s docstring, both read directly this
session; `docs/issue-392/proposals/2026-08-07-post-merge-reconciliation.md`,
read directly this session
The "no git-native hooks" precedent traces to issue #392's proposal
("Alternative considered and rejected" section): a standalone
`.git/hooks/post-merge` file does not propagate via clone/fork and is
invisible to the harness driving role sessions, so #392 chose to chain
onto the merge command the orchestrator already always runs instead.
`patrol_trigger.py`'s docstring follows the same precedent and defers the
exact call site inside `on-the-record/commands/run.md`'s merge step —
this survey resolves that deferral by reading run.md directly.

canonical: `on-the-record/commands/run.md`, the 머지(merge) subsection of
its 승인 절차, read directly this session
That subsection instructs the orchestrator to run `gh pr checks <n>`,
require checks to be clean and human approval to have been given in
conversation, then run `gh pr merge <n> --merge --delete-branch`. There
is no single Python function in this repo that wraps "the merge command"
as a callable — the orchestrator, an LLM agent following run.md's own
procedure text, issues that command itself. Design read: E1's wiring is
reachable only via an explicit instruction added to run.md's own
procedure text, immediately after the existing merge line, telling the
orchestrator session to invoke the wiring module with the just-landed
merge sha — there is no way to make this automatic purely through
library code, without either a git-native hook (ruled out per #392) or
the orchestrator being told, in its own procedure text, to make the
call. This shapes the live-demo acceptance criterion: it exercises the
documented instruction being followed by a live orchestrator session on
a real merge, not a background daemon triggering independently.

canonical: `docs/specs/enforcement-boundary.md`, the patrol_trigger.py
row, read directly this session
That row states patrol_trigger.py has no zero-install reachability path
yet because it is not wired into the merge-command seam in any delivery
so far — that gap is what issue #1597 asks this delivery to close.

canonical: repo-wide grep for the literal string "patrol-disabled", run
directly this session, zero matches
No `.on-the-record/patrol-disabled` file or equivalent path-based
kill-switch exists anywhere in the repo today.
canonical: `docs/handbooks/hooks.md`, the kill-switch section, read
directly this session
The repo's established kill-switch convention for hooks is the
`ORCHESTRATE_OFF` environment variable, checked first in every hook. That
convention is shell-hook-specific (per-process env var); issue #1597
instead specifies a file-based kill-switch, checkable identically from
both this issue's Python entry point and a future E2 entry point without
propagating an env var between separately-invoked processes. This is a
new, patrol-specific convention, not a re-use of `ORCHESTRATE_OFF` —
phase 2 should note the divergence rather than silently departing from
the handbook's convention with no explanation.

canonical: repo-wide grep for "watchdog" and "respawn" under gates/,
on-the-record/monitors/, on-the-record/hooks/, run directly this
session — matches include gates/test_watch_rearm_registry.py and
on-the-record/monitors/test_poll_heartbeat.py
The repo has established watchdog/respawn machinery with its own
regression tests, but the matched test files' names do not include
anything exercising "does a watchdog respawn mid-flow cause patrol's own
anti-loop marker to be bypassed" — no such test title appears in the
grep's match set. The anti-loop marker itself
(`patrol_trigger._is_patrol_artifact`, read directly this session) is a
pure function over `event["changed_files"]` with no session/process
state, so a respawn cannot corrupt its internal logic directly. The open
question a regression test must cover is process-level: whether E1's own
wiring, if the orchestrator session running it is killed and restarted
by the watchdog mid-merge-flow, risks re-running judge_cmd/
patrol_board.run twice for the same merge sha, or evaluating
should_fire against a stale/partial event in a way that lets a
patrol-authored commit slip through as a genuine trigger. This survey
did not locate a canonical record of the validity consult issue #1597
cites as flagging this unverified, and treats the regression-test
requirement as open pending phase-2 design.

## Unknowns / gaps this proposal must resolve (deferred to phase 2 design,
not settled by this survey)

- Exact home for the wiring module and its test file (gates/ vs.
  on-the-record/hooks/ vs elsewhere) — this survey's working assumption
  is gates/, matching patrol_trigger.py and patrol_board.py's own
  location; phase 2 decides finally.
- Whether E1's 3-role cap is its own counter or reuses
  JUDGE_MAX_ROLES_PER_MERGE directly, so there is exactly one cap
  definition rather than two that could drift apart.
- The precise respawn regression test's mechanism for simulating a
  mid-flow watchdog respawn (process-kill-and-restart vs. a
  unit-level state-injection test) — phase 2 designs the actual test;
  this survey only establishes that no such test currently exists.
- Whether the .on-the-record/patrol-disabled presence check belongs in a
  small shared helper both E1's and a future E2's entry points import, or
  is implemented once now with a documented "E2 must do the same"
  obligation — phase 2 decides; this proposal's Out of scope section
  excludes building E2 itself.
