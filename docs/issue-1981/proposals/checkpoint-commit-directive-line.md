---
status: proposed
files:
  - spawn.py
  - tests/test_spawn_directive_assembly.py
  - docs/handbooks/spawn-directive-assembly.md
---

## Request

Inject a checkpoint-commit rule into the spawn directive: "make a
checkpoint commit BEFORE starting any long or backgrounded verification
run; amend or add a follow-up commit after." This inverts today's
verify-then-commit habit that stranded two sessions live on 2026-08-22
(#1959 s2, #1978 ph2 — see docs/issue-1978/reports/implementation.md's
finalization-deviation note). Scope: `spawn.py`, `tests/`, `docs/`.
Explicitly out of scope: gate-blocked commit shapes (#1976, already
merged) and state-aware respawn preambles (part 2, a separate later
issue).

## Constraints

- Line must appear in `_spawn_one()`'s assembled task directive
  (spawn.py:7972-7982's unconditional preamble region), asserted by a
  live test run per the issue's own acceptance check.
- Must NOT appear in `consult_cmd()`/`panel_cmd()`-assembled prompts —
  survey confirmed (docs/issue-1981/reports/implementation/survey.md)
  these are separate functions with independent prompt assembly, so this
  falls out naturally as long as the line is added only inside
  `_spawn_one()`.
- Sequenced after #1978 (merged, 4f952e08) per the issue body — same
  spawn.py directive-assembly area; #1978 is in.
- Single-line `-m` commit messages (per invocation instructions).
- New tests run with `-o addopts=''` (serial — spawn-invoking tests hang
  under xdist, issue #1986).

## Rationale

Two placement options were considered:

1. **Unconditional addition to the existing preamble block**
   (spawn.py:7972-7982) — append the checkpoint-commit sentence directly
   into the same f-string that already carries the "완료의 정의"/
   headless-single-shot text.
2. **Conditional block mirroring #1978's `--single-phase` pattern**
   (spawn.py:7983-7988) — a new flag-gated module constant appended only
   when some new CLI flag is passed.

Option 2 was rejected: #1978's flag-gating exists because
`--single-phase` is an opt-in behavior change (bypassing phase-1) that a
spawner must deliberately choose per spawn — the assembled task/env must
stay byte-identical when the flag is absent (docs/handbooks/
spawn-directive-assembly.md, "single-phase signal" section). The
checkpoint-commit rule has no such per-spawn opt-in shape: the issue asks
for it to hold for every commit-capable role spawn, the same audience as
the surrounding always-on preamble it extends. Gating it behind a new
flag would mean most spawns silently keep the old verify-then-commit
habit unless a spawner remembers to opt in — reproducing exactly the
stranding failure mode the issue exists to fix. Option 1 (unconditional,
same block) was chosen.

## What will be done

- Add one sentence to the existing `_spawn_one()` preamble f-string
  (spawn.py:7972-7982), immediately after the current push/PR paragraph
  and before the headless-single-shot warning paragraph — matching the
  issue's requested content: checkpoint-commit before starting any long
  or backgrounded verification run, amend/follow-up commit after.
- Add a test to `tests/test_spawn_directive_assembly.py` (reusing its
  existing `_run()`/mock harness) asserting the assembled `_spawn_one()`
  task text contains the new line.
- Add a test (or extend an existing one) asserting `consult_cmd()`'s and
  `panel_cmd()`'s assembled prompts do NOT contain the line — direct
  confirmation of the "no-commit modes" half of the acceptance, not just
  an inference from separate-function structure.
- Extend docs/handbooks/spawn-directive-assembly.md with a short section
  documenting the new unconditional line, its location, and why it's
  unconditional (mirroring the doc's existing per-mechanism section
  style from #1978).
- Run `python3 -m pytest tests/test_spawn_directive_assembly.py -q -o
  addopts=""` (serial) and paste the result into the phase-2 record.

## Accumulation

This adds one more sentence to `_spawn_one()`'s already-multi-paragraph
preamble f-string (spawn.py:7972-7982), the same block #1978's
single-phase line and per-skill trigger lines already extend. If N more
directive rules accumulate here the same way, the preamble grows linearly
and eventually needs extraction into a small ordered list of
line-producing helper functions (one per rule) assembled in a loop,
rather than one hand-grown f-string — the same shape #1978's
`_SINGLE_PHASE_CONTRACT_LINE`/`_skill_trigger_line` split already started
for its own two mechanisms. Not needed at N=1; flagged for whoever adds
rule N+2 or beyond.

## Out of scope

- Gate-blocked commit shapes (#1976 — merged separately, d9c92dc5).
- State-aware respawn preambles / completed-work heuristics (part 2,
  future issue per the issue body).
- Any change to `directive.sh`/`approval-gate.sh` or other
  `tokenmaxxxer-core` files — this repo's `spawn.py` only.

## How you'll know it worked

`python3 -m pytest tests/test_spawn_directive_assembly.py -q -o
addopts=""` passes, including the new assertions: the checkpoint-commit
line is present in `_spawn_one()`'s assembled directive and absent from
`consult_cmd()`/`panel_cmd()`'s assembled prompts.
