# Issue #692 — Phase 1 Proposal (implementation)

files:
- `on-the-record/hooks/decision-queue-stopgate.sh` (bound the
  waiting-declaration block to at most once per session; rewrite its
  block reason to restate the decision-queue items with coordinates and
  name a satisfiable one-shot escape)
- `on-the-record/hooks/test_decision_queue_stopgate.py` (add
  `session_id` to the `_run()` helper and its stdin payload; add the
  consecutive-waiting-declaration regression test from the issue's
  Acceptance section; isolate state dir per test)
- `docs/issue-692/reports/implementation/survey.md` (this phase's
  survey, already committed)

## Request (paraphrased intent)

#692 is a regression report against #600/PR #622's waiting-declaration
guard in `decision-queue-stopgate.sh`. That guard blocks a `Stop` when
the last assistant reply is a bare waiting declaration over a non-empty
decision queue with no background-arm marker — but a blocked Stop forces
another turn, and when the only remaining work is an operator decision,
the natural next reply is another bare waiting declaration, which blocks
again. A target-repo run on 2026-08-11 hit six consecutive
"대기 중입니다." turns. The issue asks for three things: (a) bound the
block to at most once per turn chain, reusing `retry-loop-bound.sh`'s
pattern where applicable; (b) make the block reason state an escape
format the model can actually satisfy — restate the queue items with
coordinates once, then close; (c) a regression test for the consecutive
scenario, with the acceptance's own check written into it.

## Constraints

- The pre-existing age-tier logic (#466/#374) is explicitly not at
  fault per the issue and stays untouched — the fix is scoped to the
  `_WAITING_RE`/`_ARM_RE` branch only.
- Follow this directory's existing hook contract: `ORCHESTRATE_OFF` kill
  switch, `CLAUDE_ROLE` early-exit, fail-closed trap on unexpected exit
  codes, `{"decision":"block"}` vocabulary — none of that changes.
- The bound must survive across separate hook-process invocations
  within one session (each `Stop` event spawns a fresh process, per
  survey) — state has to persist to disk, the way `retry-loop-bound.sh`
  already does it for `PreToolUse`/`PostToolUse`.
- `session_id` must come from the hook's own stdin payload (already
  read into `stdin_payload`), matching how `retry-loop-bound.sh` sources
  it — no new environment plumbing.
- The regression test is Acceptance-named exactly: "after one
  waiting-declaration block, a second consecutive Stop in the same
  session is not blocked," and the test suite must fail if that
  scenario is absent (i.e. it has to actually assert the not-blocked
  outcome, not merely exist).

## Rationale

Chosen approach: give `decision-queue-stopgate.sh` its own small
session-keyed state file (same shape as `retry-loop-bound.sh`'s:
atomic `os.replace` write, `OTR_*_STATE_DIR` env override, silent
fail-open on any parse error) that records whether the
waiting-declaration branch has already blocked once this session; on a
second consecutive fire, fall through instead of blocking again.

Alternative considered and rejected: reusing `retry-loop-bound.sh`'s own
state file/directory instead of adding a sibling one. `retry-loop-bound`
keys its entries on a `(tool, target)` signature hashed from a
`PreToolUse`-shaped `tool_input` (file path or shell command) — a `Stop`
event's payload has no such field, so decision-queue-stopgate would
either have to invent a compatible fake signature (fragile: any future
change to `retry-loop-bound`'s signature format silently breaks this
hook too) or write into the same file under a different, ad-hoc key
shape (defeats the purpose of sharing — two independent key schemas in
one file is worse than two files). A sibling state directory following
the identical *pattern* (not the identical *file*) gets the proven
persistence shape without coupling the two hooks' internal formats
together.

Also rejected: leaving the block unbounded but changing only the reason
text (issue's (b) alone, skipping (a)). The issue's own observed
incident is six *identical* blocks in a row — a better-worded reason
reduces the odds the model can't figure out the escape, but does not
bound the failure mode if the model still doesn't compose a message
matching the exact marker regex on every attempt; the once-per-session
bound is the actual backstop the issue asks for, and (b) is the
complementary fix that makes escaping on the first attempt likely.

## What will be done

1. In `decision-queue-stopgate.sh`'s embedded Python (the `CHECK`
   heredoc), before evaluating `_WAITING_RE`/`_ARM_RE`, read
   `session_id` from `stdin_payload`. If absent/non-string, keep
   today's behavior unchanged (fail open on the bound only — the
   existing block/no-block logic still runs; no new state means no new
   suppression).
2. Add a small state read/write pair scoped to this hook, mirroring
   `retry-loop-bound.sh`'s persistence: directory
   `${OTR_DECISION_QUEUE_STOPGATE_STATE_DIR:-${TMPDIR:-/tmp}/otr-decision-queue-stopgate}`,
   file `<safe-session-id>.json`, atomic `os.replace` over a `.tmp`
   write, silent fail-open (missing dir, unreadable/corrupt file, OSError
   on write -> treat as "not yet blocked this session").
3. Waiting-declaration branch behavior:
   - If `_WAITING_RE` matches and `_ARM_RE` does not, AND this session's
     state does not yet show a prior waiting-declaration block: emit the
     block, restating the decision-queue items with their `#issue`/
     `PR#pr (age)` coordinates (reusing the existing `_name()` helper,
     called before this branch instead of after) and instructing a
     single-message escape: relay the queue once by name, then close the
     turn. Record the block in the session's state file.
   - If the branch would fire again in the same session (state already
     shows a prior block): do not block on this branch — fall through to
     the pre-existing age-tier logic below it, unchanged. This is the
     "at most once per turn chain" bound from the issue.
4. `on-the-record/hooks/test_decision_queue_stopgate.py`: extend `_run()`
   to accept an optional `session_id` (defaulting to a fixed test value)
   and include it in the JSON stdin payload; point
   `OTR_DECISION_QUEUE_STOPGATE_STATE_DIR` at a fresh `tempfile.TemporaryDirectory()`
   per test invocation (mirroring how `test_retry_loop_bound.py` isolates
   its own state dir) so tests never share or collide on real session
   state. Add the Acceptance-named test: two consecutive `_run()` calls
   with the same `session_id` and a waiting-declaration message over a
   non-empty queue — assert the first blocks (`decision == "block"`) and
   the second does not (`stdout == ""` or falls through to the existing
   age-tier branch's own — non-blocking — output for that fixture).
5. Update the two existing waiting-declaration tests
   (`t_waiting_declaration_over_fresh_queue_blocks`,
   `t_queue_relay_that_closes_turn_is_not_blocked_by_new_branch`) only if
   the `_run()` signature change requires it — no behavioral change to
   those two scenarios themselves (first-fire-blocks, arm-marker-relay
   is-not-blocked both still hold).

## Out of scope

- Any change to the age-tier (tier1/tier2) logic below the
  waiting-declaration branch — issue states it is not at fault.
- Any change to `retry-loop-bound.sh` itself, or moving
  `decision-queue-stopgate.sh` onto its state file.
- Cross-session bounding (the bound is explicitly per session/turn
  chain, per the issue's wording, not a global rate limit).
- Any change to `spawn.py flows --json` or the `decision_queue` data
  shape it returns.

## How you'll know it worked

- `on-the-record/hooks/test_decision_queue_stopgate.py`'s new
  consecutive-waiting-declaration test fails on the pre-fix hook (first
  and second `Stop` both block) and passes after the fix (second Stop is
  not blocked).
- All pre-existing tests in that file still pass unchanged in
  observable behavior (only the `_run()` helper's payload/env grows).
- `bash -n on-the-record/hooks/decision-queue-stopgate.sh` and
  `python3 -m pytest on-the-record/hooks/test_decision_queue_stopgate.py`
  both run clean.
