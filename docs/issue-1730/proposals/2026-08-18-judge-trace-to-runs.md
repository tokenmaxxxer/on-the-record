---
status: proposed
files:
  - spawn.py
  - docs/handbooks/spawn.md
  - tests/test_spawn_judge.py
  - docs/reports/patrol-judge-log.md
---

Skip condition: pure bugfix (scout-directive skip condition) — issue #1730 states `validity-consult-skip: trivial` and `design-research-skip: mechanical`, and the fix is fully specified by the issue's own Acceptance section plus the existing `_judge_trace_path()`/`_judge_roles_run_today()`/`judge_cmd()` logic (see docs/issue-1730/reports/implementation/survey.md). No design decision is open; scouting/full survey round skipped accordingly (survey.md still written, per survey-order-directive, to record the concrete write set).

## Request
`spawn.py:_judge_trace_path()` appends the patrol judge trace to the target repo's tracked file `docs/reports/patrol-judge-log.md` but nothing ever commits it (unlike the consult trace, which `_commit_consult_trace()` commits after every write). Every `patrol_wiring.py run` therefore leaves the working tree dirty with judge-trace lines the operator has to notice and discard by hand. Relocate the judge trace to `runs/patrol-judge-log.md` under the same `_consult_root(cwd)` anchor — `runs/` is already git-ignored, so the trace keeps its trace-always guarantee without dirtying the tree — and delete the now-stray tracked file from the repo.

## Constraints
- The anchor stays `_consult_root(cwd)` — the same anchor `_judge_roles_run_today()` and every other consult/judge path helper already uses; introducing a second anchor risks the exact `relative_to()` mismatch issue #1313 already fixed once.
- `_judge_roles_run_today()`'s 3-role-per-merge cap counting logic, and `_append_judge_trace()`'s line format (`role=`/`verb=judge`/`merge=`/`outcome=`), stay byte-for-byte unchanged — only the path `_judge_trace_path()` returns moves.
- The trace-always guarantee (proposal #1587 §Constraints: one line per judge run, success/failure/cap-exceeded, no exceptions) is preserved — moving to a git-ignored path must not turn into "stop tracing," only "stop committing."
- No new commit step is added for the judge trace (see Rationale for why this is a deliberate rejection, not an oversight).

## Rationale
Two ways to stop the judge trace from dirtying the tree were considered:
1. **Chosen**: relocate `_judge_trace_path()`'s return value from `docs/reports/patrol-judge-log.md` to `runs/patrol-judge-log.md`, both under the same `_consult_root(cwd)` anchor. `runs/` is already git-ignored (`.gitignore:1`), so the file simply stops appearing in `git status` — zero new code paths, no new failure mode to handle, and the fix is a one-line path change plus deleting the now-stray tracked file.
2. **Rejected**: keep the tracked path and add a `_commit_judge_trace()` helper mirroring `_commit_consult_trace()`, auto-committing after every `_append_judge_trace()` write. Rejected because judge runs fire automatically and repeatedly from `patrol_wiring.py run` (dozens of prefilter-miss lines per patrol sweep, per the issue's own observed count — 18 lines across two runs against one merge), unlike consult traces which commit once per a human-triggered `consult` call. Auto-committing on that cadence would spam the target repo's history with dozens of single-line trace commits per patrol run — a worse outcome than the dirty-tree problem being fixed. The issue's own Fix description directs the `runs/` relocation, not a commit step, for this reason.

## What will be done
- `spawn.py`: change `_judge_trace_path()` (spawn.py:5930-5934) to return `_consult_root(cwd) / "runs" / "patrol-judge-log.md"` instead of the `docs/reports/...` path, and update its docstring to name the new path.
- `docs/reports/patrol-judge-log.md`: `git rm` the tracked file — its 2 existing lines are stale trace output, not durable record content, and the whole point of the fix is that this path stops being tracked.
- `docs/handbooks/spawn.md`: update the two prose references at lines 96 and 104 (예산/budget section, 트레이스/trace section) from `docs/reports/patrol-judge-log.md` to `runs/patrol-judge-log.md`.
- `tests/test_spawn_judge.py`: update the two hardcoded path expectations — `JudgeTraceAlwaysTest._trace_lines()` (line 248) and `test_traces_on_cap_exceeded_without_dispatching_git`'s `trace_path` (line 268) — from `self.root / "docs" / "reports" / "patrol-judge-log.md"` to `self.root / "runs" / "patrol-judge-log.md"`. `TraceCapTest`'s fixture paths (lines 140-227) build their own `patrol-judge-log.md` paths independently of `_judge_trace_path()` and are untouched.

## Accumulation
This is a one-function path change (one string literal in `_judge_trace_path()`) plus updating the handful of call sites that hardcode the old path in tests and docs — not a repeated per-entry or per-file pattern. `_judge_trace_path()` has exactly one definition and every other judge-trace caller (`_append_judge_trace()`, `_judge_roles_run_today()`, `judge_cmd()`) already goes through it rather than hardcoding the path itself, so there is no second copy of this path to keep in sync.

## Out of scope
- Any change to the trace line format, the 3-role-per-merge cap logic, or the prefilter/validator pipeline.
- Any change to the consult trace's own commit behavior (`_commit_consult_trace()`), which is intentionally different (human-triggered, low-frequency, meant to be durable/reviewable).
- Historical records under `docs/issue-1587/**` and `docs/issue-1605/**` that name the old path in past-tense prose describing prior state — those are frozen records, not live documentation.

## How you'll know it worked
The issue's four Acceptance checks, run against the PR branch:
- `python3 -c "import spawn; print(spawn._judge_trace_path('/tmp/x'))"` prints `/tmp/x/runs/patrol-judge-log.md`
- `git ls-files docs/reports/patrol-judge-log.md` prints nothing
- after `python3 gates/patrol_wiring.py run . <sha>` in a clean checkout, `git status --porcelain` shows no `docs/reports/patrol-judge-log.md` entry
- `grep -n "patrol-judge-log" docs/handbooks/spawn.md` shows only the `runs/` path
plus `python3 -m unittest tests.test_spawn_judge` passing.
