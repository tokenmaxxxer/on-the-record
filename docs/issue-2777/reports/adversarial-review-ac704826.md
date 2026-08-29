---
issue: 2777
role: adversarial-review-ac704826
author: adversarial-review-ac704826
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2780's own deliverable for issue #2777
code_under_review: 8250d86911924588780c9d37e5ec3d176506ef3f
loop_state: landed
type: verification
breaking: false
verdict: pass-with-findings — all three acceptance checks and all four standing invariants reproduce independently against PR #2780 (`8250d869`); `_issue_is_open()` is byte-identical to `main`; failing-test-name sets are identical to `main` (16/16, same names) with +3 new passing tests. Two open, non-blocking findings the delivering record did not disclose: (1) the 3-tick failure-streak threshold means any gh outage lasting ≤2 ticks is still fully silent — the same category of invisibility issue #2777 was filed over, now bounded to a smaller window rather than eliminated; (2) the failure-streak state this fix reuses (`watchdog_noise_state.json`) lives in the reinstall-volatile `runs/` directory tracked as OPEN in issue #2216 whenever `MUSTER_STATE_ROOT` is unset (confirmed unset in this environment) — a plugin reinstall mid-outage resets the streak, delaying this fix's own report by up to 2 more ticks past the reinstall.
upstream:
  - path: gates/spawn_on_pr.py
    sha: 8250d86911924588780c9d37e5ec3d176506ef3f
  - path: docs/issue-2652/reports/adversarial-review-58d892b0.md
    sha: aa653aeef72691cd6e05ea42797b8b273a424a39
---

# issue-2777 — adversarial-review-ac704826 record

## What was done

Independently re-derived (not restated) all three of PR #2780's
acceptance claims and both risk questions the spawning brief raised
(the 3-tick threshold's blind window, and the failure-streak state's
survival across a process restart / plugin reinstall), against two
isolated worktrees: `/tmp/main-review` (main @ `62ec2c79`, i.e. #2768's
reorder with no #2777 fix) and `/tmp/pr2780-review` (PR #2780 @
`8250d869`). Every reproduction script below was written by this
session from scratch — none of PR #2780's own repro scripts were read
before writing my own equivalents, only after, to compare results.

canonical: `diff <(git show main:gates/spawn_on_pr.py) <(git show pr-2780:gates/spawn_on_pr.py)` — result:
```diff
374c374,383
<     로컬 조인)."""
---
>     로컬 조인).
>
>     issue #2777: ...(docstring addition)...
377a387,389
>         if spawn._watchdog_note_gh_failure(root, "spawn-on-pr", not ok):
>             print("[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, "
>                   "이번 틱 판정 보류 (연속 실패)")
```
The entire executable diff is those 3 lines plus a docstring — `_issue_is_open()` (the function the issue's must-not forbids touching) is byte-identical between `main` and `pr-2780`; confirmed by the same `diff`, which shows no hunk touching that function.

### Acceptance check 1 — forced gh-lookup failure, before/after (independent repro)

Wrote `/tmp/repro_indep.py`: imports `spawn_on_pr` fresh from a given
root, monkeypatches `spawn.board()` to one subject with a deficit
(`{"implementation": {"author": "alice"}}`, the same minimal fixture
shape `test_spawn_on_pr.py`'s pre-existing `_deliverable_board()` uses),
monkeypatches `closure_sweep.issue_state_index_all` to always return
`(None, False)`, isolates `state_paths.STATE_ROOT` to a fresh tmp dir,
and calls `missing_verification(root, pr_index={})` for 5 ticks.

acceptance: `python3 /tmp/repro_indep.py /tmp/main-review` (before) — result:
```
tick 1: out={}
tick 2: out={}
tick 3: out={}
tick 4: out={}
tick 5: out={}
```
acceptance: `python3 /tmp/repro_indep.py /tmp/pr2780-review` (after) — result:
```
tick 1: out={}
tick 2: out={}
[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)
tick 3: out={}
[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)
tick 4: out={}
[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)
tick 5: out={}
```
derived: the two runs above, both executed live this session — `main` is silent for all 5 ticks; `pr-2780` reports from tick 3 onward. `out={}` on every tick, both trees — no spawn-eligibility change from the new print.

This same pair of runs answers the brief's blind-window question
directly: ticks 1-2 on `pr-2780` are byte-identical to every tick on
`main` — `out={}`, no stdout. An operator watching only this one subject
cannot tell "gh has been down for 1-2 ticks" from "the board is quiet
and healthy." If a real outage lasts exactly two ticks and resolves
before the third, it produces zero trace anywhere (no line, no state
visible externally) — nobody learns it happened. This is the same
failure mode issue #2777 was filed over, not a different one; the fix
narrows its window from unbounded to 2 ticks, it does not close it.

### Acceptance check 2 — #2768's 30-closed-subject fixture, re-run

canonical: `grep -n "closed_subjects = " gates/test_spawn_on_pr.py` (pr-2780) — result:
```
closed_subjects = [f"issue-{93000 + i}" for i in range(30)]
```
Genuinely 30 subjects, not asserted from the PR's prose.

acceptance: `cd /tmp/pr2780-review && python3 -m pytest -q gates/test_spawn_on_pr.py::test_closed_and_open_subjects_mixed_only_open_unmappable_branch_reported gates/test_spawn_on_pr.py::test_closed_issue_with_unmappable_branch_prints_nothing gates/test_spawn_on_pr.py::test_open_subject_with_unmappable_branch_still_reports_missing_branch` — result:
```
...                                                                      [100%]
3 passed in 0.84s
```
#2652's noise fix still holds — this fix's new code path (`issue_states
is None`) never executes when these tests pass an explicit
`issue_states` dict, so it cannot have regressed them; confirmed green
by execution rather than assumed from the PR body.

### Acceptance check 3 — `spawn_missing_for_pr(..., dry_run=True)` pairs, byte-identical (independent repro)

Wrote `/tmp/repro_dryrun_indep.py`, independent of the PR's own dry-run
script: same degraded-lookup monkeypatch, calls
`spawn_missing_for_pr(root, root, dry_run=True, issue_states=None, backoff_state={}, pr_index={})`.

acceptance: `python3 /tmp/repro_dryrun_indep.py /tmp/main-review` (before) — result:
```
pairs: []
```
acceptance: `python3 /tmp/repro_dryrun_indep.py /tmp/pr2780-review` (after) — result:
```
pairs: []
```
derived: the two runs above, executed live this session — byte-identical
`[]`/`[]`. `_issue_is_open()`'s pre-existing fail-closed behavior already
excludes this subject from `out`/`pairs`; the new print does not touch
the return value.

### Streak-state correctness: reset-on-recovery and re-arm (independent repro, not covered by the PR's own 3 new tests)

None of the PR's 3 new tests exercise a fail→recover→fail-again sequence
on the same signal. Wrote `/tmp/repro_recovery.py`: 3 failing ticks
(expect a print on tick 3), then 1 healthy tick (`ok=True`), then 2 more
failing ticks (expect silence — streak should have reset to 0), then a
3rd failing tick (expect a print again).

acceptance: `python3 /tmp/repro_recovery.py /tmp/pr2780-review` — result:
```
[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)
--- recovery tick ---
--- 2 fails after recovery (should stay quiet) ---
--- 3rd fail after recovery (should print again) ---
[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)
```
derived: the run above, executed live this session — the streak resets
to 0 on a single healthy tick and re-arms for a fresh outage rather than
staying latched — no "stuck warning" or "stuck silence" defect.

canonical: `watchdog.py:523-542` (`_watchdog_note_gh_failure`, unchanged by pr-2780) — no explicit "recovered" print exists on the `failed=False` branch (it only resets `streaks[signal]` and returns `False`). checked: `grep -n "_watchdog_note_gh_failure(root," watchdog.py` — result: every one of the 4 existing call sites (`requirement-drift:full`, `requirement-drift:delta`, `closure-sweep`, `board-sweep:pr-index`) only prints on the `True`-returning branch, none on recovery — so the absence of a recovery line in this fix matches established convention, not a gap specific to it.

### Streak-state persistence: reinstall-volatile `runs/` (issue #2216 inheritance)

canonical: `gates/state_paths.py:30-31` (pr-2780, unchanged from main):
```python
STATE_ROOT = (Path(os.environ["MUSTER_STATE_ROOT"]).resolve()
              if os.environ.get("MUSTER_STATE_ROOT") else ROOT / "runs")
```
`_watchdog_noise_state_path()` (`watchdog.py:487-492`) calls
`state_paths.orchestrator_state_path("watchdog_noise_state.json")`,
which returns `STATE_ROOT / filename` — i.e.
`<plugin-checkout>/runs/watchdog_noise_state.json` whenever
`MUSTER_STATE_ROOT` is unset.

checked: `printenv | grep -i MUSTER` in this session's environment —
result: no `MUSTER_STATE_ROOT` key present (only `MUSTER_WORKSPACE_ROOT`,
`MUSTER_SKILL_REGISTRY_ROOT`, etc. are set) — unverifiable: whether every
production orchestrator invocation also leaves it unset cannot be
confirmed from inside this one session, but this session's own
environment plus `.gitignore:1` (`runs/`) are consistent with issue
#2216's description of the default path being the live, un-overridden
one.

canonical: `gh issue view 2216` — result:
```
"state":"OPEN"
```
issue #2216's body (quoted verbatim, read in full this session): "This
generalizes beyond one warning. Any watchdog state whose entire purpose
is to persist *across* ticks is defeated by living in a reinstall-
volatile directory. `_watchdog_note_gh_failure` (consecutive-failure
counting) shares the same state file and the same defect: its failure
streak resets to zero on every reinstall, so the 'warn only after N
consecutive failures' guard silently never reaches N." — #2216 names
`_watchdog_note_gh_failure` explicitly as an affected call site, and the
defect it describes is tracked OPEN, not fixed.

PR #2780 calls this exact helper, on this exact state file, under a new
signal name (`"spawn-on-pr"`). It inherits #2216's defect precisely: a
plugin reinstall during a live gh outage resets the `"spawn-on-pr"`
streak to 0, so post-reinstall this fix's own line is silent again for
up to 2 more ticks even though the outage never stopped. This is not a
new bug introduced by #2780 — every other `_watchdog_note_gh_failure`
consumer already has it, and #2216 is the correct place to fix it
system-wide, not this PR. But the delivering record framed reuse of this
helper as purely positive without naming #2216 or its consequence for
this fix's own reliability guarantee — a material omission for a fix
whose entire point is "the operator must be told."

### Four standing invariants, re-run independently

- **No return of the retired role axis in any reshaped form**: canonical: the `diff` quoted at the top of this section — the only executable change is the 3-line `_watchdog_note_gh_failure` call + print; no role/kind name list, no closed-subject enumeration re-added.
- **No new bug — failing-test-name set vs `main`, as sets, not counts**:
  acceptance: `cd /tmp/pr2780-review && python3 -m pytest -q` — result:
  ```
  16 failed, 556 passed, 3 xfailed in 5.91s
  ```
  acceptance: `cd /tmp/main-review && python3 -m pytest -q` — result:
  ```
  16 failed, 553 passed, 3 xfailed in 6.05s
  ```
  acceptance: `diff <(sort /tmp/main_failed.txt) <(sort /tmp/pr2780_failed.txt)` (both `grep '^FAILED'` outputs from the two runs above, captured this session) — result:
  ```
  (no output — diff exit 0, identical sets)
  ```
  Same 16 failing test names both sides; +3 delta on `pr-2780` is exactly this fix's own new tests.
- **No overhead increase — bytes added per tick, both cases**: canonical: `watchdog.py:523-542`, `gates/spawn_on_pr.py:387-389`.
  - Healthy tick (`ok=True`): +1 local JSON file read of the (already-shared) `watchdog_noise_state.json` to check the streak; `streaks["spawn-on-pr"]` is already 0 so no write, no print. 0 stdout bytes. No new `gh`/`git`/subprocess call.
  - Degraded tick, streak 1-2 (below threshold): +1 JSON read, +1 JSON write (streak increments and changed state must persist), 0 stdout bytes.
  - Degraded tick, streak ≥3: +1 JSON read, +1 JSON write, plus the new print. derived: `python3 -c "print(len('[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)\n'.encode('utf-8')))"` — result:
  ```
  98
  ```
  98 bytes of stdout, once per tick, for as long as the outage continues.
  "No overhead increase" as literally zero bytes is not quite accurate — there is a small, bounded, reused-I/O-path overhead — but no new external call is added, matching the PR's narrower and accurate claim ("no new `gh`/git/subprocess call").
- **Monitor and watch machinery unbroken and not quieter**: derived: acceptance check 1's two runs above — confirmed never *worse* than `main` at any tick (both are silent on ticks 1-2 of an outage; from tick 3, `pr-2780` reports while `main` stays silent forever) — a strict improvement, not a regression. Not confirmed as *fully* solving "quieter than a healthy board is indistinguishable from broken": for any outage of ≤2 ticks, `pr-2780` remains exactly as silent as `main`, which is still the condition the issue was filed against, just bounded (see open finding 1).

## Why

derived: `gh issue view 2777` (read in full this session, quoted in the
spawning brief context) plus `gh pr view 2780` — the spawning brief
explicitly names that PR #2768 (this same lineage's ancestor fix) was
merged before its own third independent verification returned, and that
third verification is the one that found the regression this issue and
PR #2780 exist to fix. That history — landing on 2-of-3 confidence and
being wrong — sets the bar for this review: every acceptance number and
every file claimed by PR #2780's own record was re-executed from scratch
in a separate worktree with separately authored repro scripts (not
copy-pasted from the PR) before being accepted, rather than restated
from the PR's description. The two design questions the brief posed
(blind window, reinstall volatility) were investigated by reading the
actual `_watchdog_note_gh_failure` implementation and issue #2216's body
directly (`gh issue view 2216`, quoted above), not by trusting the
delivering record's characterization of them.

## What did not work

derived: this session's own execution log — no repro attempt failed or
needed rework; every script (`/tmp/repro_indep.py`,
`/tmp/repro_dryrun_indep.py`, `/tmp/repro_recovery.py`) ran successfully
on the first attempt and both open findings below were confirmed on
first execution, not discovered after an initial wrong result.

## Upstream basis

derived: `git log -1 --format=%H pr-2780 -- gates/spawn_on_pr.py` — result:
```
8250d86911924588780c9d37e5ec3d176506ef3f
```
- `gates/spawn_on_pr.py` @ `8250d86911924588780c9d37e5ec3d176506ef3f` (PR #2780) — the code under review, diffed against `main` at the top of "What was done" above.
- `watchdog.py` @ `8250d86911924588780c9d37e5ec3d176506ef3f` (unchanged by PR #2780) — read for `_watchdog_note_gh_failure`'s implementation, quoted above.
- `gates/state_paths.py` @ `8250d86911924588780c9d37e5ec3d176506ef3f` (unchanged by PR #2780) — read for `STATE_ROOT` resolution, quoted above.
- `docs/issue-2652/reports/adversarial-review-58d892b0.md` @ `aa653aeef72691cd6e05ea42797b8b273a424a39` — the prior independent review that found and diagnosed this regression (referenced by `gh issue view 2777`'s body); this record does not re-derive its findings, only this fix's response to them.
- issue #2216 — `gh issue view 2216`, state OPEN (quoted above) — the open defect this fix's reused helper inherits.

## Open findings

1. **3-tick blind window is real and undisclosed as a limitation.** derived: acceptance check 1 above (`/tmp/repro_indep.py`, executed live this session) — any gh outage of ≤2 consecutive ticks produces identical output to a healthy board on `pr-2780`: zero stdout, `out={}`. This is a defensible trade (matches the existing single-blip-suppression convention used by every other `_watchdog_note_gh_failure` call site in `watchdog.py`, and warning on every transient blip would reintroduce a different flavor of noise), so this is not a blocker, but the delivering record's `verdict:` line ("a forced gh-lookup failure now produces a distinct degraded-state line") should have named the 3-tick floor as a scope limit rather than reading as an unqualified fix. Resolution path: none required to merge; if a future incident shows short gh blips matter operationally, lower `WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD` or add a distinct signal name with a lower threshold for `spawn-on-pr` specifically — out of this issue's scope to decide unilaterally here.
2. **Failure-streak state inherits issue #2216's reinstall-volatile storage, unmentioned in the delivering record.** canonical: `gh issue view 2216` (quoted above, state OPEN) plus `gates/state_paths.py:30-31` and `printenv` (both quoted above, confirming `MUSTER_STATE_ROOT` unset in this environment) — a plugin reinstall mid-outage resets the `"spawn-on-pr"` streak, delaying this fix's own report. Not a new bug (shared by every existing `_watchdog_note_gh_failure` consumer, and #2216 already tracks it system-wide) — but this fix's core promise ("the degradation will be reported") is only as durable as that shared, already-known-broken storage. Resolution path: none required in this PR; landing #2216's fix (moving `STATE_ROOT`'s default to a location that survives reinstall) fixes this consumer automatically along with the others — no `spawn_on_pr.py`-specific follow-up needed.

## Next steps

None — `loop_state: landed`. This is a terminal verification record;
both open findings above are resolution-path-only (tracked by existing
or future issues, not by further work in this session).

skill-verdict: adversarial-review — applied: invoked; derived: this
turn's own Skill tool call — the tool call happened after the commit and
PR above already existed, correcting an earlier draft of this line that
claimed invocation without having called the tool. The review itself
did apply the skill's core mechanism: this session was structurally
independent of PR #2780's builder session, did not trust the builder's
self-report, wrote its own repro scripts before reading the builder's,
and surfaced two findings (the blind window, the #2216 inheritance) the
delivering record did not disclose. It did not follow the skill's strict
blind/no-spec protocol — this session read the issue text and the PR's
own record by design (the task was independent verification against a
known spec, not blind evaluation), which the skill's Step 1 excludes
from a true blind review.
skill-verdict: work-in-english — applied: invoked; derived: this turn's
own Skill tool call — checked against this session's own output rather
than assumed: canonical: `git log --format=%B -3 -- docs/issue-2777` and
this record's own body, both this session's actual commits/record text
— all English throughout (commit messages, PR title/body, this record),
matching repo convention (recent commit subjects on this branch are also
English). No violation found to flag.
other mounted skills: not triggered
(`defect-verification-independence-from-upstream-verdicts`,
`verify-finding-record` — this record's independence and reproduction-
evidence choices were made without invoking either via the Skill tool;
not a claim that they were unnecessary, only that they were not loaded).
