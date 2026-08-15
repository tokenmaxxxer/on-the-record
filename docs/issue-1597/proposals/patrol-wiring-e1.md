---
files:
  - gates/patrol_wiring.py
  - gates/test_patrol_wiring.py
  - on-the-record/commands/run.md
  - docs/issue-1597/reports/implementation/survey.md
  - docs/issue-1597/proposals/patrol-wiring-e1.md
---

## Request

Wire the five already-landed patrol pieces (`patrol_trigger.should_fire`,
judge's Haiku prefilter + `judge_cmd`, and `patrol_board.run`) into the
orchestrator's own post-merge flow, so patrol runs automatically after a
PR lands, without duplicating any of the reusable pieces — plus a
file-based kill-switch checked first at this entry point (and at a future
E2 entry point, out of scope here), and a regression test proving the
anti-loop guard survives a watchdog respawn mid-flow. This is E1 of
issue #1597; E2 is a separate future wiring entry point, not built here.

## Constraints

- Kill-switch first, at every entry point: `.on-the-record/patrol-disabled`
  presence in repo root must short-circuit before any other work,
  with a trace line recording the short-circuit.
- Reuse judge's existing Haiku prefilter for role selection — no second,
  independent role-selector module or duplicated jurisdiction logic.
- No git-native hooks (`.git/hooks/post-merge` or similar) — wiring must
  live in the orchestrator's own merge-command code path, per issue
  #1582's proposal and issue #392's precedent (survey: hooks don't
  propagate via clone/fork and are invisible to the harness).
- A regression test proving the anti-loop marker still holds when the
  watchdog respawns a session mid-flow is required, not optional — a
  prior validity consult flagged this as unverified.
- 3-role cap on role selection per merge, applied before/through
  judge_cmd's own per-merge cap, not a second uncapped loop.
- Existing budgets, caps, and trace-line conventions in patrol_trigger,
  judge_cmd, and patrol_board carry over unchanged — this delivery adds
  wiring, not new budget/cap machinery.

## Rationale

Rejected alternative: a standalone `.git/hooks/post-merge` shell hook
that calls the wiring module directly. Rejected because issue #392's
proposal already ruled this out for this repo — survey found its
"Alternative considered and rejected" section states git hooks don't
propagate via clone/fork and are invisible to the harness driving role
sessions, so the repo's established precedent for "runs after a merge"
is chaining onto the merge command the orchestrator itself always
invokes. Issue #1582's proposal and `patrol_trigger.py`'s own docstring
both already commit to this precedent; re-litigating it here would
contradict two already-landed pieces this issue is explicitly told to
integrate with, not duplicate.

Rejected alternative: building a second, independent role-selector (e.g.
a static jurisdiction-keyword match over changed file paths) instead of
reusing judge's Haiku prefilter. Rejected because the issue explicitly
requires reuse, and because a second selector would drift from judge's
own jurisdiction semantics over time (two independently-maintained
definitions of "in jurisdiction"), which is exactly the duplication this
issue calls out as the failure mode to avoid.

Rejected alternative: E1's own independent 3-role counter, decoupled
from `judge_cmd`'s existing `JUDGE_MAX_ROLES_PER_MERGE` cap. Considered
because it would let the wiring module short-circuit its role loop
before spawning any judge_cmd subprocess at all (cheaper than letting
judge_cmd's internal cap reject roles 4+ after already paying prefilter
cost). Rejected as the sole mechanism because two independently
maintained cap numbers can drift; the design instead reads
`JUDGE_MAX_ROLES_PER_MERGE` as the source of truth and has E1's loop stop
issuing further judge_cmd calls once that many roles have already run for
the merge sha (checked via the same trace-line count judge_cmd itself
uses), so there is one number, not two.

## What will be done

1. `.on-the-record/patrol-disabled` check as the first statement of
   `gates/patrol_wiring.py`'s entry function — on presence, print a trace
   line (`[patrol-wiring] kill-switch active, skipping`) and return
   immediately, before touching `should_fire`, judge, or the board.
2. Call chain, once past the kill-switch: build the post-merge `event`
   dict from the merge's changed files -> `patrol_trigger.should_fire(event)`
   -> on True, iterate `roles/*.json`, calling `judge_cmd(role, merge_sha)`
   for each candidate role until either all roles are tried or the
   existing per-merge trace-line count reaches `JUDGE_MAX_ROLES_PER_MERGE`
   (reusing `judge_cmd`'s own prefilter-driven skip/enqueue behavior
   rather than re-implementing jurisdiction matching) -> for each role
   whose `judge_cmd` call returned a non-empty `enqueued` list, call
   `patrol_board.run_patrol_board` for that role.
3. Kill-switch check is also a documented precondition for the future E2
   entry point (not built here) — this proposal's write set includes only
   E1's own check, plus a shared helper function in
   gates/patrol_wiring.py that E2 is expected to import rather than
   reimplement, so the check itself is defined exactly once even though
   only one entry point calls it in this delivery.
4. `on-the-record/commands/run.md`'s merge step gets one new instruction
   immediately after the existing `gh pr merge <n> --merge --delete-branch`
   line: after a successful merge, run
   `python3 gates/patrol_wiring.py run <repo-root> <merge-sha>` and note
   its trace output; this is the merge-command seam identified in the
   survey — there is no Python-level call site to hook into instead,
   since the merge command itself is issued directly by the orchestrator
   following run.md's procedure text.
5. Respawn regression test design: a test that simulates a watchdog
   killing and restarting the process mid-flow between `should_fire`
   returning True and `patrol_board.run` completing (e.g. by driving the
   wiring module's steps as separate subprocess invocations sharing the
   same on-disk trace/queue state, with the second invocation representing
   the respawned session), then asserts that (a) the respawned run does
   not re-enqueue or re-comment for work the first (killed) run already
   completed and recorded in the trace, and (b) an event whose changed
   files are entirely patrol's own artifacts (queue file, board writes)
   still returns should_fire=False across the respawn boundary — i.e. the
   #1360-class guard is exercised with a genuine mid-flow process
   restart in the test, not just a single in-process call.

## Out of scope

- E2, the future second patrol-wiring entry point mentioned in issue
  #1597 — only the shared kill-switch helper is exposed for it to import
  later; E2's own call site and logic are not designed or built here.
- Any change to `patrol_trigger.should_fire`'s own logic, `judge_cmd`'s
  internal pipeline, or `patrol_board.run_patrol_board`'s rendering/write
  logic — E1 calls these as-is.
- Any new budget, cap, or trace-format convention beyond what
  patrol_trigger/judge_cmd/patrol_board already define.
- Anything not listed in this proposal's `files:` frontmatter.

## How you'll know it worked

- gates/test_patrol_wiring.py (and existing patrol_trigger/patrol_board
  test suites, unaffected) pass, covering: kill-switch short-circuit at
  the wiring entry point (and the shared helper E2 will reuse);
  should_fire honored (a patrol-artifact-only event does not trigger
  judge/board calls); the 3-role cap (a merge diff matching more than 3
  roles' jurisdiction results in at most 3 judge_cmd calls); patrol-authored
  artifacts never re-trigger, including the respawn case designed above.
- A live demo: a real PR merged through the orchestrator's normal merge
  step produces trace lines showing should_fire -> judge_cmd (per
  selected role) -> patrol_board.run (for roles with new entries), on an
  actual merge, not a unit test.
- A second live demo: with `.on-the-record/patrol-disabled` present in
  the repo root, the same merge step produces only the kill-switch
  short-circuit trace line and no judge/board activity.
- on-the-record/commands/run.md documents the automatic post-merge
  behavior and the kill-switch file, so a human reading the merge step
  understands both without reading gates/patrol_wiring.py's source.
