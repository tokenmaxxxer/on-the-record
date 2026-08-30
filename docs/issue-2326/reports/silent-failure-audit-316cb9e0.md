---
issue: 2326
role: silent-failure-audit-316cb9e0
author: silent-failure-audit-316cb9e0
skills: silent-failure-audit (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: false  # this is a fix round on the subject's own deliverable (PR #2875), not an independent verification of someone else's
loop_state: terminal
upstream:
  - path: docs/issue-2326/reports/adversarial-review-813a3aa7.md
    sha: efd3d777bdbe1f0467efd022dee6852910f58213
  - path: on-the-record/hooks/lint-test-on-edit.sh
    sha: efd3d777bdbe1f0467efd022dee6852910f58213
---

# issue-2326 — silent-failure-audit-316cb9e0 record

## What was done

canonical: `gh pr view 2878 --json state,title,mergedAt` (this session) —
result: `{"mergedAt":"2026-08-30T08:58:58Z","state":"MERGED","title":
"issue-2326: independent verification of PR #2875 round 4 -- lock
overhead regression found"}`.

Round 5 on PR #2875 (issue #2326's lint/test-on-edit hook). Merged PR
#2875's branch (`issue-2326/silent-failure-audit+diagnose-first-0f11c1bf`,
sha `efd3d777`) into this branch as the base, per the task's instruction
that this round builds on it — derived: `git merge --no-edit
origin/issue-2326/silent-failure-audit+diagnose-first-0f11c1bf` (this
session), merge commit `967e8c19`.

Removed the per-repo-root advisory `flock` lock (`_acquire_repo_lock` /
`_release_repo_lock`, and the call site wrapping the pytest `_run()`
call) from `on-the-record/hooks/lint-test-on-edit.sh`. This was PR #2875
round 4's speculative overhead-reduction addition; PR #2878's independent
verification (merged, above) found it regresses the ordinary fleet case —
disjoint concurrent edits — while providing no correctness guarantee that
round 4's separate durable-evidence fix (pytest `-v` +
`PYTHONUNBUFFERED=1`, partial-output recovery on timeout) wasn't already
providing on its own. No replacement serialization was added. Also
removed the now-unused `fcntl`/`hashlib` imports, and rewrote the header
comment block (the "BUDGET" section) to describe the durability fix as
the sole mechanism and to document the lock's removal and why.

derived: `git diff --stat HEAD -- on-the-record/hooks/lint-test-on-edit.sh`
(this session) — result: `1 file changed, 36 insertions(+), 94
deletions(-)`.

Re-derived all four standing invariants on the lock-removed code (full
commands and results in the section below): role-axis, no-new-bug,
monitor/watch, and — the one this round exists to re-run — overhead
under concurrency, this time explicitly including disjoint edits
alongside the identical-edit shape PR #2875 round 4's own record
checked.

## Why

PR #2878's independent verification (merged, `docs/issue-2326/reports/
adversarial-review-813a3aa7.md`) found the round-4 lock serializes work
that shares no files and no tests.

canonical: `docs/issue-2326/reports/adversarial-review-813a3aa7.md`
lines 181-186, read this session, reporting a 4-disjoint-module fixture
measured against the real hook:
```
WITH lock:    mod1=2.38s mod2=4.78s mod3=7.17s mod4=9.57s  (staircase)  TOTAL: 9.57s
WITHOUT lock: mod1=2.49s mod2=2.49s mod3=2.49s mod4=2.49s  (true parallel) TOTAL: 2.49s
```

and, at the round's own same-file 8-way concurrency scale, that the lock
produced a worse outcome distribution than no lock at all on a 16-core
host — canonical: same file, lines 200-208, read this session:
```
                        FULL-FAILURE-REPORT   EXPLICIT-INCOMPLETE   PARTIAL-RECOVERED
WITH lock,    run A:    1/8                    6/8                   0/8
WITH lock,    run B:    1/8                    7/8                   0/8
WITH lock,    run C:    1/8                    7/8                   0/8
WITHOUT lock, run A:    4/8                    0/8                   4/8
WITHOUT lock, run B:    4/8                    0/8                   4/8
WITHOUT lock, run C:    5/8                    0/8                   3/8
```

The task's own framing states the decisive point directly: the
durable-evidence fix (never discard partial pytest output, always report
explicitly) is what closes the silent-failure gap the round exists to
fix; the lock was additive to that guarantee, not a precondition for it,
and it measured worse than doing nothing on the case that actually
matters for a fleet (different sessions editing different files, not the
same file). Tuning, scoping, or conditioning the lock was explicitly out
of scope per the task; the instruction was to remove it outright and
re-run the overhead invariant with disjoint edits included so this gap
in the invariant's own coverage cannot recur silently in a future round.

## Upstream basis

canonical: `git log --oneline -3` and `git merge` output, this session —
merge base `bf1169c6`, merged tip `efd3d777`, resulting merge commit
`967e8c19` on this branch.

- `docs/issue-2326/reports/adversarial-review-813a3aa7.md` (PR #2878,
  merged) — sha `efd3d777bdbe1f0467efd022dee6852910f58213` (the tip of
  the merged PR #2875 branch at merge time, per the `git merge` output
  above). Source of the regression finding this round fixes.
- `on-the-record/hooks/lint-test-on-edit.sh` — same sha
  `efd3d777bdbe1f0467efd022dee6852910f58213` as the pre-edit state this
  round started from (PR #2875 round 4's shipped code, containing the
  lock this round removes).

## Standing invariants (re-derived this session, lock removed)

- [x] No role-axis reintroduction — derived: `grep -nE "\brole(s)?\b"
  scripts/rework_fraction.py on-the-record/hooks/lint-test-on-edit.sh
  on-the-record/hooks/otr_lint_test_timeout_plugin.py
  tests/test_spawn_gate_wiring.py` — result: 3 matches, all inside the
  hook's own disclaimer comment
  (`on-the-record/hooks/lint-test-on-edit.sh:139-144`), same as prior
  rounds.

- [x] No new bug — derived: fresh `git worktree add` checkout of
  `origin/main` (sha `d514d2c7b9294a887971097ebdd5113131e148c9`) vs.
  this branch's working tree, `python3 -m pytest test/ tests/ -q` on
  each, FAILED-nodeid sets sorted and diffed with `diff` as sets of
  names, not counts:
  ```
  $ diff /tmp/main_failed.txt /tmp/branch_failed.txt && echo "IDENTICAL SETS"
  IDENTICAL SETS
  ```
  branch: 497 passed, 3 xfailed, 15 failed. main: 470 passed, 3 xfailed,
  15 failed — derived: same two `pytest` invocations above; the 27-test
  delta (497-470=27) is exactly `tests/test_spawn_gate_wiring.py`'s own
  test count (`derived: python3 -m pytest tests/test_spawn_gate_wiring.py
  -q` — result: 27 passed), matching prior rounds' accounting. Collection
  scope stated: `pytest test/ tests/` from the repo root, not `harness/`
  (same structural blind spot PR #2878 named; unaffected by this round's
  change — `derived: grep -rl "lint-test-on-edit\|lint_test_timeout" harness/
  2>/dev/null` — result: no matches, so this round's change is not hidden
  from that blind spot either).

- [x] Overhead under concurrency, disjoint AND overlapping edits (this
  round's re-run, the invariant PR #2875 round 4 checked only against
  identical edits): built the same 4-disjoint-module fixture PR #2878
  described (`mod1.py`-`mod4.py`, one test file each, ~2.3s/test, no
  shared file or test), ran the real lock-removed hook against all 4
  concurrently, 3 times, timed with `date +%s.%N` before/after `wait`:
  ```
  run A: 2.79s   run B: 2.80s   run C: 2.80s
  ```
  derived: this session's own invocation of `on-the-record/hooks/
  lint-test-on-edit.sh` via `echo '{"tool_input":{"file_path":...}}' |
  bash on-the-record/hooks/lint-test-on-edit.sh`, 4 backgrounded per run,
  3 runs back to back. All 12 invocations across the 3 runs produced
  empty stdout/stderr (clean pass) — derived: `wc -c` on each of the 12
  output files was 0 — matching PR #2878's "WITHOUT lock" baseline
  (2.49s) far more closely than its "WITH lock" staircase (9.57s); the
  4-way concurrent case no longer serializes.

  Then re-ran the round's own same-file 8-way identical-edit scale
  against this repo's real `spawn.py` — derived: `grep -rl "^import
  spawn\b\|^from spawn import" test/ tests/ | wc -l` — result: 34
  impacted test files, close to PR #2878's stated 35 — 3 runs of 8
  concurrent invocations each, default 15s budget:
  ```
  run A (15.07s wall): 5 full-failure-report, 0 explicit-incomplete, 3 partial-recovered
  run B (15.04s wall): 5 full-failure-report, 0 explicit-incomplete, 3 partial-recovered
  run C (15.04s wall): 7 full-failure-report, 0 explicit-incomplete, 1 partial-recovered
  ```
  derived: same invocation method as above, 8 backgrounded per run,
  classified each output by its own explicit marker text (`ALREADY
  CONFIRMED FAILING` -> partial-recovered, `INCOMPLETE` -> explicit-
  incomplete, non-empty otherwise -> full-failure-report, empty -> would
  be silent) via a `classify()` shell function reading each of the 24
  output files, this session. 0 of the 24 invocations across the 3 runs
  were silent or landed in explicit-incomplete (derived: the `classify`
  tally printed above, per-invocation, for all 24 files), matching PR
  #2878's "WITHOUT lock" baseline (0/8 incomplete each run, see Why
  section table) and clearly better than its "WITH lock" baseline (6-7/8
  incomplete each run, same table) — the regression PR #2878 found does
  not reproduce with the lock removed. Disjoint edits are now part of
  this invariant's measurement, per the task's instruction, so this
  specific coverage gap cannot recur silently in a future round.

- [x] Monitor/watch machinery unbroken — derived: `python3 -m pytest
  test/ tests/ -q -k "monitor or watch"` — result: 15 passed, matching
  prior rounds exactly.

## Silent-failure audit of this round's own change

canonical: `on-the-record/hooks/lint-test-on-edit.sh:296-358` (the
`_run()` function) and `:459-499` (the pytest call site), both read
directly this session, neither touched by this round's diff.

Per the mounted `silent-failure-audit` skill: the edit removes two
functions and their call site, and does not touch `_run()`'s own error
handling (subprocess `TimeoutExpired`/`OSError` branches, budget
accounting) or the `ok is None` / `ok is False` / `budget_hit`-only
branches at the call site below it. Traced forward: the removed lock's
own timeout branch (`lock_timed_out`) previously set `budget_hit = True`
manually and skipped straight past `_run()`; with the lock gone, `_run()`
is now the only path, and it already sets `budget_hit = True` and
returns `(None, out)` on its own `TimeoutExpired` — the removed branch
was redundant with, not additive to, `_run()`'s own budget accounting.
No new Silently-Absorbed site was introduced: the `ok is False` / `ok is
None` (with or without recovered `confirmed` failures) / `budget_hit`-
only branches at the call site all still terminate in `_emit()` with
non-empty text on every non-clean outcome — acceptance: the 8-way
concurrency re-run in the Standing invariants section above — result: 0
of 24 invocations were silent or unrecognized-empty.

skill-verdict: silent-failure-audit — applied: invoked; traced the
`_run()` / `budget_hit` / `ok`-branch failure paths at the lock-removal
call site to confirm no new Silently-Absorbed path was introduced, then
verified empirically via the 8-way concurrency re-run above.
skill-verdict: work-in-english — applied: invoked; code comments, this
record, and the commit/PR text are in English per repo convention (all
prior issue-2326 records and commits are English, e.g. `git log --oneline
-5`, this session); the final chat summary to the user is in Korean.

## Open findings

None. Resolution path: N/A — the only finding this round was scoped to
fix is PR #2878's lock-overhead regression, and it is fixed and
re-verified above (see Standing invariants, "Overhead under concurrency").

## Next steps

None for this round — `loop_state: terminal`. The hook has still not
shipped to `hooks.json` on `main`: canonical: `gh pr view 2866 --json
state,title` — result: `{"state":"OPEN",...}` (never merged); `gh pr
view 2875 --json state,title` — result: `{"state":"OPEN",...}` (round 4,
also not merged); derived: `git show origin/main:on-the-record/hooks/
hooks.json | grep -c lint-test-on-edit` — result: 0, vs. this branch's
`grep -c lint-test-on-edit on-the-record/hooks/hooks.json` — result: 1.
The ship decision for issue #2326 as a whole remains open, per round 4's
own PR trailer (`Advances #2326`), which this round's PR also carries.

## What did not work

None. acceptance: `python3 -m pytest tests/test_spawn_gate_wiring.py -q`
— result: 27 passed; acceptance: `python3 -m pytest test/ tests/ -q -k
"monitor or watch"` — result: 15 passed; derived: `git diff --stat HEAD`
— result: exactly the one scoped file, `on-the-record/hooks/
lint-test-on-edit.sh`, changed. The merge, lock removal, and
re-derivation of all four standing invariants completed as scoped
without a scope-exceeded stop or a swap from the task's instructions.
