---
issue: 2777
role: adversarial-review-70d1a9b2
author: adversarial-review-70d1a9b2
skills: adversarial-review (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2788's own deliverable for issue-2777
code_under_review: on-the-record PR #2788 (bd6b5e217d8985d1692e2465632dde25e761b863), gates/spawn_on_pr.py::missing_verification()
loop_state: landed
type: review
breaking: false
verdict: pass — re-derived all three of the original issue-2777 acceptance claims plus the dead-reset-path fix independently, using scripts of my own, not the PR's own repro scripts. Attacked the fix's core equivalence ("caller supplied a non-`None` `issue_states` dict" == "the caller's own fetch succeeded this tick") from both directions on the one real production call path (`watchdog.py:1104`) and it holds by construction: the fetch-gate condition that guards the `issue_state_index_all()` call is a superset of the condition that guards the `spawn_missing_for_pr()` call, so a dict is never forwarded without a same-tick fetch, and `spawn_missing_for_pr()` is never called without that fetch having run. My own repro through `spawn_missing_for_pr(dry_run=True)` (one layer above the PR's own test, which stops at `missing_verification()`) reproduces the same FAIL,FAIL,FAIL,RECOVERY,RECOVERY,FAIL trace: line at tick 3, streak 0 after recovery, no immediate re-warn at tick 6. `_issue_is_open()` is byte-identical to origin/main by AST-level diff, not just visual inspection. Failing-test-name sets are identical between this tree and origin/main tip `dc48170d`, both rerun by me — see the empty-diff result under "Full suite, failing-test-name SET vs origin/main" below. stdout-byte overhead reproduces exactly as claimed, plus one JSON-state read (`_load_watchdog_noise_state`) added on the healthy path, confirmed by reading `_watchdog_note_gh_failure()`'s own body — see "stdout-byte overhead, measured directly" below. One informational, non-blocking open finding below (issue-state-index truncation) that predates this PR and is not introduced or worsened by it.
upstream:
  - path: on-the-record PR #2788 (branch pr-2788-review), gates/spawn_on_pr.py::missing_verification()
    sha: bd6b5e217d8985d1692e2465632dde25e761b863
  - path: on-the-record PR #2780 (closed, superseded), gates/spawn_on_pr.py::missing_verification()
    sha: 8250d86911924588780c9d37e5ec3d176506ef3f
  - path: docs/issue-2777/reports/adversarial-review-25204a01.md
    sha: 9c78c3ba531fb36411b1bb274d6fb36579f7cfd4
---

# issue-2777 — adversarial-review-70d1a9b2 record

## What was done

Independent verification of PR #2788, which supersedes PR #2780 (now
closed — canonical: `gh pr view 2780 --json state -q .state` result
`CLOSED`, run this session) after the first verification round
(`adversarial-review-25204a01.md`) found PR #2780's failure-streak reset
lived only in a branch dead on the real `watchdog.py` production call
path. PR #2788 carries PR #2780's original design forward unchanged and
adds one `else` branch that resets the streak whenever the caller
already supplies a non-`None` `issue_states`.

Checked out the PR's actual branch in a separate worktree
(`git fetch origin pull/2788/head:pr-2788-review && git worktree add
/tmp/pr2788-wt pr-2788-review`) rather than trusting `gh pr diff` text,
and wrote fresh scripts under `/tmp` instead of reusing the PR's own
`/tmp/repro_2777_prod_recovery.py`, per the independence requirement.

canonical: `cd /tmp/pr2788-wt && git log --oneline -1` — result:
```
bd6b5e21 issue-2777: fix dead gh-failure-streak reset path in spawn-on-pr degraded-lookup line
```
canonical: `cd /tmp/pr2788-wt && git merge-base origin/main HEAD` — result:
```
dc48170d6c3c428ee970768207f0367401efda91
```
— PR #2788 is rebased onto the current `origin/main` tip
(`dc48170d`, this repo's own `HEAD` at session start), not a stale base.

### Attacking the reset's core equivalence

The fix's premise is: "a caller-supplied non-`None` `issue_states` means
that caller's own fetch succeeded this tick." I traced every production
caller.

derived: `grep -rn "spawn_missing_for_pr(" --include="*.py" . | grep -v test_`
— result: exactly one production call site, `watchdog.py:1104`.

Read `watchdog.py`'s `_board_wide_sweep()` (the sole caller context,
lines ~1060-1110) in full. The relevant shape:
```python
issue_states, issue_states_ok = (None, True)
if ("spawn-on-pr" in this_tick or "closure-sweep" in this_tick
        or "spawn-on-approve" in this_tick):
    issue_states, issue_states_ok = closure_sweep.issue_state_index_all(root)
    ...
if "spawn-on-pr" in this_tick:
    spawned = spawn_on_pr.spawn_missing_for_pr(
        root, str(root), issue_states=issue_states, pr_index=shared_pr_index)
```
Both the forward and mirror direction of the attack close:

- **Forward (dict ⇒ fetch succeeded this tick, not stale/partial/carried
  over)**: `issue_states` is a local variable reinitialized to
  `(None, True)` at the top of every `_board_wide_sweep()` call, and
  `_board_wide_sweep()` is called fresh per repo inside
  `_board_wide_sweep_all()`'s loop (`_sp._board_wide_sweep(repo)`,
  `watchdog.py:874`) — there is no outer-scope caching that could carry a
  dict across ticks or across repos. A non-`None` dict reaching
  `spawn_missing_for_pr()` can only have come from this same call's own
  `closure_sweep.issue_state_index_all(root)`, executed lines above in
  the same function invocation.
- **Mirror (`None` ⇒ never attempted, not "attempted but failed")**: the
  condition gating the fetch (`"spawn-on-pr" in this_tick or ...`) is a
  superset of the condition gating the `spawn_missing_for_pr()` call
  itself (`if "spawn-on-pr" in this_tick:`). Whenever
  `spawn_missing_for_pr()` runs, `"spawn-on-pr" in this_tick` is true,
  which forces the fetch branch to have run too — `issue_states` can
  never be left at its untouched `(None, True)` init value when
  `spawn_missing_for_pr()` is actually reached. A `None` reaching
  `missing_verification()` therefore always means the fetch was
  attempted and returned `ok=False` (a real failure), never "no attempt."

### Independent reproduction, one layer above the PR's own test

The PR's own new test, `test_gh_failure_streak_resets_on_recovery_via_
production_caller_shape`, drives `spawn_on_pr.missing_verification()`
directly with explicit `issue_states=None`/`{}` rather than letting the
function do its own internal fetch — checked this is genuinely the
production-relevant shape, since `spawn_missing_for_pr()` forwards
`issue_states` to `missing_verification()` completely unmodified
(`gates/spawn_on_pr.py:706`, `missing_verification(root,
issue_states=issue_states, pr_index=pr_index)` — no transformation in
between). To close the remaining gap (the test still bypasses
`spawn_missing_for_pr()` itself), I wrote my own script driving the real
entry point one layer higher, with a fresh mock board and a fresh
`tmp_path`, run against the checked-out PR branch:

derived: `python3 /tmp/repro_2777_verify.py` (own script, calls
`spawn_on_pr.spawn_missing_for_pr(tmp, str(tmp), dry_run=True,
issue_states=<None-or-{}>, pr_index={})` per tick, sequence
FAIL,FAIL,FAIL,RECOVERY,RECOVERY,FAIL) — result:
```
tick 1 (FAIL): pairs=[] streak=1
tick 2 (FAIL): pairs=[] streak=2
[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)
tick 3 (FAIL): pairs=[] streak=3
tick 4 (RECOVERY): pairs=[] streak=0
tick 5 (RECOVERY): pairs=[] streak=0
tick 6 (FAIL): pairs=[] streak=1
```
Line at tick 3 (the threshold), silence from tick 4 (recovery), streak
reads `0` immediately after recovery (not merely "below threshold from a
partial decrement"), and the isolated post-recovery blip at tick 6 starts
a fresh streak of `1` without re-warning. `pairs=[]` every tick, both
failure and recovery — no spawn-eligibility decision moved, matching
acceptance check 3.

### Acceptance check 2 — #2768's 30-closed-subject fixture, re-run

acceptance: `cd /tmp/pr2788-wt && python3 -m pytest -q
gates/test_spawn_on_pr.py::test_closed_and_open_subjects_mixed_only_open_unmappable_branch_reported
gates/test_spawn_on_pr.py::test_closed_issue_with_unmappable_branch_prints_nothing
gates/test_spawn_on_pr.py::test_open_subject_with_unmappable_branch_still_reports_missing_branch`
— result:
```
3 passed in 0.84s
```

### `_issue_is_open()` byte-identical to origin/main

derived: extracted the function body from both `dc48170d`'s
`gates/spawn_on_pr.py` and the PR's tree with a regex slice (not a raw
line-range `sed`, to be immune to any line-number drift elsewhere in the
file) and compared —
```python
b = extract(base, "_issue_is_open")   # dc48170d
n = extract(new, "_issue_is_open")    # PR #2788 tree
print("IDENTICAL" if b == n else "DIFFERENT")
```
result: `IDENTICAL`.

### Full suite, failing-test-name SET vs origin/main

Ran the full suite myself in two separate worktrees — the checked-out PR
branch and a bare worktree at `origin/main`'s tip `dc48170d` — rather
than trusting the PR's own pasted numbers.

acceptance: `cd /tmp/pr2788-wt && python3 -m pytest -q` — result:
```
16 failed, 557 passed, 3 xfailed in 5.73s
```
acceptance: `cd /tmp/base-dc48170d && python3 -m pytest -q` (fresh
worktree at `dc48170d`, no PR changes) — result:
```
16 failed, 553 passed, 3 xfailed in 6.33s
```
derived: `diff <(grep '^FAILED' /tmp/pre_fix_verify.txt | sort) <(grep
'^FAILED' /tmp/post_fix_verify.txt | sort)` (both files captured from the
two `pytest` runs directly above, this session) — result: empty diff,
exit code `0`. Both runs list the same 16 `FAILED` names — the +4 delta
on the PR side is exactly the PR's own 4 new passing tests.

### stdout-byte overhead, measured directly

derived: `python3 /tmp/overhead_check.py` (own script,
`len(stdout.encode())` per tick through `spawn_missing_for_pr(dry_run=
True)`) — result:
```
healthy tick bytes: 0
degraded below-threshold bytes: 0
degraded at-threshold bytes: 98
```
Matches the PR's claim exactly. Read `_watchdog_note_gh_failure()`'s own
body (`watchdog.py:523-542`) to confirm the added cost on the healthy
path: the `else` branch calls it with `failed=False`, which always calls
`_load_watchdog_noise_state(path)` (one JSON read) and only calls
`_save_watchdog_noise_state` `if changed` (i.e., only the first healthy
tick after a nonzero streak) — one unconditional read, a conditional
write, no new `gh`/subprocess call, matching the claim.

## Why

Chose to attack the equivalence structurally (tracing the fetch-gate and
call-gate conditions in `watchdog.py`) rather than only running more
sequences through the PR's own test harness, because the first
verification round's whole finding was that a plausible-looking design
can pass every test in a file that never drives the real caller shape —
re-running the same class of test with new inputs would not have caught
a second instance of that same failure mode. Went one layer higher than
the PR's own new test (through `spawn_missing_for_pr()`, not stopping at
`missing_verification()`) for the same reason: the test's own
justification for why it's representative is correct (verified by
reading `spawn_missing_for_pr()`'s pass-through, quoted under
"Independent reproduction" above), but verifying that claim from primary
code, in a fresh script, is stronger than accepting the PR's own claim
about its own test.

## What did not work

None. The equivalence held under attack from both directions; no
narrower repro or alternative script was needed to force a
counterexample.

## Upstream basis

- on-the-record PR #2788 (branch `pr-2788-review`, head
  `bd6b5e217d8985d1692e2465632dde25e761b863`) — the artifact under
  review, checked out live in `/tmp/pr2788-wt` this session.
- on-the-record PR #2780 (closed, superseded — canonical: `gh pr view
  2780 --json state -q .state` result `CLOSED`, this session) — the
  design PR #2788 carries forward.
- `docs/issue-2777/reports/adversarial-review-25204a01.md` @
  `9c78c3ba531fb36411b1bb274d6fb36579f7cfd4` (read in full this session)
  — the prior verification that found the dead reset path PR #2788
  fixes.

## Open findings

1. **Informational, non-blocking — pre-existing, not introduced by this
   PR.** `gates/closure_sweep.py::issue_state_index_all()` (lines
   259-266, 299-300, read this session) returns `(None, True)` —
   `ok=True` but no data — when the issue-index would be truncated by
   `_ISSUE_INDEX_LIMIT`. On the production call path, this `None`
   propagates through unchanged (it never becomes a dict), so it
   correctly routes through the pre-existing `if issue_states is None:`
   branch rather than the new `else` branch — it does **not** trigger the
   equivalence attacked above, and this PR neither introduces nor
   worsens it. But because `ok=True` here,
   `_watchdog_note_gh_failure(root, "spawn-on-pr", not ok)` is called
   with `failed=False`, so a chronic truncation (a board large enough to
   hit the limit every tick) would never accumulate a failure streak and
   never print the new diagnostic line, while `_issue_is_open()` still
   fail-closes every subject with `issue_states=None` — a silent-quiet
   mode distinguishable from neither "healthy" nor "degraded" in stdout.
   This is `issue_state_index_all()`'s own pre-existing truncation
   contract (predates PR #2780), out of scope for issue #2777's
   acceptance criteria (which are about `ok=False` failures, not
   `ok=True`-truncation), and not something this PR is positioned to fix
   — noted here only so it is not mistaken for something this
   verification missed.

## Next steps

None. `loop_state: landed`.

acceptance: `cd /tmp/pr2788-wt && python3 -m pytest -q
gates/test_spawn_on_pr.py -k "gh_failure_streak_resets_on_recovery"`
— result:
```
1 passed in 0.80s
```
Combined with the empty failing-test-set diff under "Full suite,
failing-test-name SET vs origin/main", the `IDENTICAL` `_issue_is_open()`
comparison, and this session's own
FAIL/FAIL/FAIL/RECOVERY/RECOVERY/FAIL trace under "Independent
reproduction, one layer above the PR's own test" — all executed this
session, all above — this supports the `pass` verdict on PR #2788; no
further action is expected from this role on this PR.

## Four standing invariants

- **No return of the retired role axis in any reshaped form**: `git diff
  dc48170d -- gates/spawn_on_pr.py` (in `/tmp/pr2788-wt`) touches only the
  `if issue_states is None:` / new `else:` branches inside
  `missing_verification()`'s body and its docstring — no role/kind name
  list, no closed-set enumeration reappears anywhere in the diff.
- **No new bug — failing-test set vs origin/main, as SETS OF NAMES**:
  derived: `diff <(grep '^FAILED' /tmp/pre_fix_verify.txt | sort) <(grep
  '^FAILED' /tmp/post_fix_verify.txt | sort)` (this session's own two
  full-suite runs, quoted in full under "Full suite, failing-test-name
  SET vs origin/main" above) — result: empty diff, 16 names both sides.
- **No overhead increase**: derived: `python3 /tmp/overhead_check.py`
  (this session's own script, quoted in full under "stdout-byte
  overhead, measured directly" above) — result: `0` / `0` / `98` bytes
  per tick, plus exactly one JSON read (no write on the steady-state
  healthy path) added by the new `else` branch, per
  `_watchdog_note_gh_failure()`'s own body read this session.
- **Monitor and watch machinery unbroken and not quieter — this issue's
  own subject**: the new code is strictly additive (one `else` clause
  calling an already-imported helper with `failed=False`; the existing
  `if`-branch print path is untouched). The repro quoted under
  "Independent reproduction, one layer above the PR's own test" above
  shows the diagnostic line still appears at the threshold tick and the
  streak genuinely returns to a state indistinguishable from health
  after recovery — the exact "not quieter, but also not a permanent
  alarm" balance issue #2777 and Finding 1 both required.

skill-verdict: adversarial-review — invoked; applied: structured this
entire verification as a blind, structurally-independent re-derivation
(fresh worktree, fresh scripts under `/tmp`, not the PR's own `/tmp/
repro_2777_prod_recovery.py`) of every claim in PR #2788's description,
including deliberately attacking the fix's core equivalence from both
directions rather than accepting the PR's own framing of why its new
test is representative.
skill-verdict: work-in-english — invoked; applied: this record is
written in English; the project's existing Korean docstrings/print
strings in `gates/spawn_on_pr.py` and `watchdog.py` are quoted verbatim,
not translated.
other mounted skills: not triggered — test-depth-audit and
implementation-audit were reviewed against this task and judged
not-applicable: this session is a direct independent verification of one
PR's claims via the adversarial-review protocol (the role this session
was spawned as), not a systematic test-quality audit across a suite
(test-depth-audit) or the two-session builder/evaluator claims-extraction
protocol (implementation-audit) — the claims here came from the PR
description itself, already falsifiable and already checked one-by-one
above, with no separate claims-extraction step needed.
