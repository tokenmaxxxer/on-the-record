---
issue: 2777
role: adversarial-review-30ca0248
author: adversarial-review-30ca0248
skills: adversarial-review (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2788's own deliverable for issue-2777
code_under_review: on-the-record PR #2788 (bd6b5e217d8985d1692e2465632dde25e761b863), gates/spawn_on_pr.py::missing_verification()
loop_state: landed
type: review
breaking: false
verdict: present — checked: sections 1-9 below (this session's own executed commands) — result: every acceptance claim in PR #2788's body holds under independent re-derivation; the symmetry attack on the new `else` branch found no path by which a stale/partial/never-attempted-fetch value reaches it; `_issue_is_open()` is byte-identical to origin/main; failing-test-name SETS are identical between origin/main and PR #2788 (16 vs 16); the healthy-path overhead is exactly one added JSON-state read (0→1) with 0 added stdout bytes.
upstream:
  - path: on-the-record PR #2788, branch issue-2777/observability-explorability+adversarial-review-275db07c
    sha: bd6b5e217d8985d1692e2465632dde25e761b863
  - path: docs/issue-2777/reports/adversarial-review-25204a01.md
    sha: 9c78c3ba531fb36411b1bb274d6fb36579f7cfd4
  - path: gates/spawn_on_pr.py
    sha: bd6b5e217d8985d1692e2465632dde25e761b863
  - path: watchdog.py
    sha: dc48170d6c3c428ee970768207f0367401efda91
  - path: gates/closure_sweep.py
    sha: dc48170d6c3c428ee970768207f0367401efda91
---

# issue-2777 — adversarial-review-30ca0248 record

## What was done

canonical: `gh pr view 2788 --json title,body,commits,files` output — PR #2788 (branch `issue-2777/observability-explorability+adversarial-review-275db07c`, head `bd6b5e217d8985d1692e2465632dde25e761b863`) states in its own body "PR #2780 was never merged (state OPEN throughout this session), so this PR delivers its original design plus the reset correction together in one change," and its commit message states "PR #2780's independent verification (adversarial-review-25204a01) found the streak reset ... only ran from a branch unreachable on healthy production ticks."

Independent verification of PR #2788, which supersedes PR #2780 and additionally fixes the dead-reset-path defect found by this same review lineage in PR #2780 (`docs/issue-2777/reports/adversarial-review-25204a01.md`, Finding 1, cited above). Re-derived every acceptance claim from scratch — none of the PR's own scripts, harness, or numbers were reused as evidence; every number in sections 1-9 comes from a command run in this session against a checkout of `pr-2788` (`git fetch origin pull/2788/head:pr-2788`, working tree files replaced with `git show pr-2788:<path> > <path>`).

**skill-verdict: adversarial-review — applied: invoked; used as this task's own structure (blind attack on the else-branch symmetry claim, evidence-cited findings, re-derivation over citation) rather than the two-session spawn protocol, since this session was already spawned specifically as the independent evaluator role for PR #2788 with no access to the builder's session.**

**skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; re-derived every claim from primary evidence (fresh pytest runs, a hand-written repro script, byte counts) instead of citing PR #2788's own reported numbers, and deliberately attacked the *new* code (the `else` branch) with a negative-path case — "caller passes None because it never attempted a fetch" — rather than only confirming the happy-path recovery claim.**

**skill-verdict: test-depth-audit — applied: invoked; classified the load-bearing new test as Genuine Assertion in section 2 below by citing its specific streak-value and stdout assertions, and confirmed the classification by running the identical production-shape sequence against origin/main's pre-fix code (section 3) — the old code's `streak()` never leaves 0 under that sequence, so the assertions in the new test are falsifiable, not decorative.**

**skill-verdict: work-in-english — applied: invoked; this record, all repro scripts, and all commit/PR text produced in this session are in English.**

### 1. Attacking the else-branch symmetry claim

Question: is "caller supplied a non-`None` `issue_states`" actually equivalent to "the caller's fetch succeeded this tick"?

checked: `grep -rn "spawn_missing_for_pr(" --include="*.py" . | grep -v test_` — result: only match outside `gates/spawn_on_pr.py` itself is `watchdog.py:1104`, confirming watchdog.py is the sole production caller.

Read `watchdog.py:892-1116` (`_board_wide_sweep`):

```python
issue_states, issue_states_ok = (None, True)
if ("spawn-on-pr" in this_tick or "closure-sweep" in this_tick
        or "spawn-on-approve" in this_tick):
    issue_states, issue_states_ok = closure_sweep.issue_state_index_all(root)
    calls_made += 1
...
if "spawn-on-pr" in this_tick:
    try:
        spawned = spawn_on_pr.spawn_missing_for_pr(
            root, str(root), issue_states=issue_states, pr_index=shared_pr_index)
```

checked: `grep -n "_board_wide_sweep(" watchdog.py` — result: `874: count += _sp._board_wide_sweep(repo)` (call site) and `892: def _board_wide_sweep(root: Path) -> int:` (definition) — `issue_states` is a local variable inside a function invoked fresh per tick, no module-level cache or cross-tick carry-over, and the fetch at line 1078 is gated by the same `"spawn-on-pr" in this_tick` condition that gates the call at line 1104, so whenever `spawn_missing_for_pr()` actually runs, `issue_states` was necessarily just (re)fetched in that same tick.

**Stale/partial dict check**: read `gates/closure_sweep.py:248-304` (`issue_state_index_all`). It has three return shapes: `(index, True)` on a clean fetch, `(None, False)` on a `gh` failure, and `(None, True)` when the `gh issue list --limit` result hits the truncation cap:

```python
    if len(data) >= _ISSUE_INDEX_LIMIT:
        return None, True
```

checked: `sed -n '248,304p' gates/closure_sweep.py` (quoted verbatim above, lines 298-299) — result: this is a "successful call, unusable data" case, and `issue_states` still ends up `None` here (not a partial dict), so it is forwarded to `spawn_missing_for_pr()` as `issue_states=None`, which routes into the pre-existing `if issue_states is None:` branch (the function's own internal refetch), not the new `else` — no path exists by which a truncated/partial/stale dict reaches the new branch.

**"None means no attempt" check** (the opposite direction): could a caller pass `None` because it never tried to fetch, incrementing a streak for an outage that isn't happening? checked: `gates/spawn_on_pr.py:395-404` (quoted verbatim in "Upstream basis" below) — result: `missing_verification()`'s `None` branch does its own internal fetch and streak-update from the *result* of that fetch (`not ok`), not from the mere fact of receiving `None` — `None` never itself increments the streak, only an internal fetch returning `ok=False` does; and on the production caller side, `None` reaches `spawn_missing_for_pr()` only when `watchdog.py`'s own top-level fetch at line 1078 already ran and failed, per the gating argument above.

checked: the `grep`/`sed` commands quoted in this section, taken together — result: the symmetry holds for the only caller that exists today, contingent on `watchdog.py`'s current single-fetch-per-tick, always-forward-explicitly convention.

### 2. Verifying the load-bearing test drives the real calling shape

checked: `sed -n '565,624p' gates/test_spawn_on_pr.py` (on the `pr-2788` checkout) — result: `test_gh_failure_streak_resets_on_recovery_via_production_caller_shape` always passes `issue_states=` explicitly (`None` on failing ticks, `{}` on the recovery tick) and never omits the argument, unlike every pre-existing test in the file (which omit it and let the function self-fetch via a monkeypatched `closure_sweep.issue_state_index_all`); it asserts concrete streak values (`streak() == threshold`, `streak() == 0`, `streak() == 1`) and exact stdout content per tick, not merely that the call didn't throw — a Genuine Assertion test, not Execution-Only.

acceptance: `python3 -m pytest gates/test_spawn_on_pr.py -k "gh_failure or degraded_lookup or healthy_lookup" -v` — result:
```
gates/test_spawn_on_pr.py::test_healthy_lookup_after_this_functions_own_fetch_stays_quiet PASSED
gates/test_spawn_on_pr.py::test_degraded_lookup_stays_quiet_below_the_failure_streak_threshold PASSED
gates/test_spawn_on_pr.py::test_degraded_lookup_reports_its_own_state_once_streak_hits_threshold PASSED
gates/test_spawn_on_pr.py::test_gh_failure_streak_resets_on_recovery_via_production_caller_shape PASSED
4 passed in 0.87s
```

### 3. Independent re-run of the FAIL,FAIL,FAIL,RECOVERY,RECOVERY,FAIL sequence

Wrote my own script (not the PR's), driving `missing_verification()` directly with `issue_states=None`/`issue_states={}` per tick (the production shape), against `pr-2788`'s checked-out code.

acceptance: own Python script (`python3 - <<'PYEOF' ... PYEOF`, calling `spawn_on_pr.missing_verification(tmp, issue_states=..., pr_index={})` in a loop, reading `spawn._watchdog_noise_state_path`/`_load_watchdog_noise_state` for the streak) — result:
```
tick1 FAIL      streak=1 out={} stdout=''
tick2 FAIL      streak=2 out={} stdout=''
tick3 FAIL      streak=3 out={} stdout='[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)\n'
tick4 RECOVERY  streak=0 out={} stdout=''
tick5 RECOVERY  streak=0 out={} stdout=''
tick6 FAIL      streak=1 out={} stdout=''
```
Matches all four required properties: line at tick 3, stops at tick 4, streak reads 0 after recovery, the later isolated blip (tick 6) does not immediately re-warn (streak=1, below threshold, no output).

**Before/after** (acceptance check 1): acceptance: same script re-run after `git show main:gates/spawn_on_pr.py > gates/spawn_on_pr.py` (origin/main tip `dc48170d6c3c428ee970768207f0367401efda91`, which carries neither PR #2780 nor #2788's changes since #2780 was never merged) — result:
```
[BEFORE/main] tick1 FAIL  streak=0 stdout=''
[BEFORE/main] tick2 FAIL  streak=0 stdout=''
[BEFORE/main] tick3 FAIL  streak=0 stdout=''
[BEFORE/main] tick4 RECOVERY streak=0 stdout=''
[BEFORE/main] tick5 RECOVERY streak=0 stdout=''
[BEFORE/main] tick6 FAIL  streak=0 stdout=''
```
main has no degraded-lookup diagnostic at all (streak stays 0, stdout stays empty through all 3 consecutive failures) — this is issue #2777's original silent-failure complaint, contrasted with the threshold-gated and self-resetting behavior shown in section 3 above.

### 4. `spawn_missing_for_pr(..., dry_run=True)` pairs, before/after

acceptance: identical 6-tick sequence through `spawn_missing_for_pr(root, str(root), dry_run=True, issue_states=..., pr_index={})`, run once against `git show main:gates/spawn_on_pr.py` and once against `git show pr-2788:gates/spawn_on_pr.py` (same board/pr_index fixtures both sides) — result:
```
main:     tick1..6 dry_run_out=[] [] [] [] [] []
pr-2788:  tick1..6 dry_run_out=[] [] [] [] [] []
```
Byte-identical pairs (both empty every tick, for this fixture) — no spawn-eligibility change.

### 5. `_issue_is_open()` byte-identical check

acceptance: `diff <(git show main:gates/spawn_on_pr.py | grep -n "def _issue_is_open" -A20) <(git show pr-2788:gates/spawn_on_pr.py | grep -n "def _issue_is_open" -A20)` — result:
```
(no output -- byte-identical)
```

### 6. #2768's 30-closed-subject fixture, re-run

acceptance: `python3 -m pytest gates/test_spawn_on_pr.py::test_closed_and_open_subjects_mixed_only_open_unmappable_branch_reported -v` — result:
```
1 passed in 0.85s
```

### 7. Full suite, failing-test-name SETS vs origin/main

acceptance: full sequence run in this session — result:
```
$ git show main:gates/spawn_on_pr.py > gates/spawn_on_pr.py; git show main:gates/test_spawn_on_pr.py > gates/test_spawn_on_pr.py
$ python3 -m pytest -q
16 failed, 553 passed, 3 xfailed in 6.98s

$ git show pr-2788:gates/spawn_on_pr.py > gates/spawn_on_pr.py; git show pr-2788:gates/test_spawn_on_pr.py > gates/test_spawn_on_pr.py
$ python3 -m pytest -q
16 failed, 557 passed, 3 xfailed in 6.29s
```

acceptance: `diff <(sort /tmp/main_failed.txt) <(sort /tmp/pr_failed.txt)` (each file built via `python3 -m pytest -q 2>&1 | grep "^FAILED" | sort` on the respective checkout) — result:
```
(no output -- IDENTICAL FAILING SET, 16 == 16 same names both sides; the +4 delta in passed count, 553 to 557, is exactly this PR's own 4 new tests from section 2, not a new bug)
```

### 8. Overhead measurement — stdout bytes and the added JSON-state read

acceptance: `python3 -c "print(len('[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)\n'.encode('utf-8')))"` — result:
```
98  (matches the PR's claimed 98-byte at-threshold line exactly; the healthy-path
     and below-threshold cases are the stdout='' results already shown in
     section 3, ticks 1/2/4/5, i.e. 0 bytes on both)
```

acceptance: own Python script counting calls to `spawn._load_watchdog_noise_state` (via a wrapping closure) during a single healthy tick (`issue_states={}`, the production success shape), run once against `pr-2788` and once against `main` with the identical fixture — result:
```
JSON-state reads on healthy tick (pr-2788): 1
JSON-state reads on healthy tick (main, pre-fix): 0
(0 -> 1 read added, 0 added stdout bytes, on the healthy path -- matches the
 overhead claim precisely)
```

### 9. Retired role axis / monitor-and-watch machinery invariants

checked: `git diff main pr-2788 -- gates/spawn_on_pr.py gates/test_spawn_on_pr.py | grep -ni "role"` — result:
```
(no output, grep exit 1, no match -- the retired role axis does not reappear
 anywhere in this diff)
```

acceptance: `git ls-files | grep -i "test_watchdog\|watchdog.*test"` — result:
```
test/test_watchdog_heartbeat_noise.py

(this is the only watchdog-adjacent test file; it is part of the full-suite
run in section 7 and does not appear in that section's identical 16-name
failing set on either revision -- it and every other suite test succeed on
both main and pr-2788. Combined with section 3's before/after trace, main
stays silent through 3 consecutive failures while pr-2788 warns at tick 3
and resets at tick 4, so the tool is less quiet in the way this issue is
about, and below-threshold blips and healthy ticks stay silent on both
sides identically, per section 3, so it is not quieter in any other way)
```

## Why

The prior round (PR #2780, reviewed in `docs/issue-2777/reports/adversarial-review-25204a01.md`) shipped a reset that only ran from a branch dead on the real production call path. The most likely way a second attempt at the same fix reintroduces silence is by getting the *new* branch's precondition wrong in the opposite direction — treating "I received a dict" as sufficient proof of "my fetch just succeeded," when in a differently shaped caller it might not be. This review's job was to find that gap rather than confirm only the recovery-path happy case the PR's own test plan already claims to cover, per [[defect-verification-independence-from-upstream-verdicts]]'s rule 2 (deliberately include a negative/edge path, not only the path the builder already tested). checked: the `grep`/`sed` commands in section 1 — result: section 1 is that attack, and it found no live gap given the current single caller.

## What did not work

None.

## Upstream basis

- `on-the-record` PR #2788, branch `issue-2777/observability-explorability+adversarial-review-275db07c`, sha `bd6b5e217d8985d1692e2465632dde25e761b863` (same-commit for the diff cited in sections 1-9).
- `docs/issue-2777/reports/adversarial-review-25204a01.md`, sha `9c78c3ba531fb36411b1bb274d6fb36579f7cfd4` — prior round's Finding 1 that PR #2788 addresses.
- `gates/spawn_on_pr.py`, `gates/test_spawn_on_pr.py` — sha `bd6b5e217d8985d1692e2465632dde25e761b863` (as shipped in PR #2788).
- `watchdog.py` — sha `dc48170d6c3c428ee970768207f0367401efda91` (origin/main tip at review time; PR #2788 does not modify this file — traced as read-only context for the caller-shape analysis in section 1).
- `gates/closure_sweep.py` — sha `dc48170d6c3c428ee970768207f0367401efda91` (origin/main tip; also unmodified by PR #2788, read for `issue_state_index_all()`'s return shapes in section 1).

Quoted for the "None means no attempt" check in section 1 (`gates/spawn_on_pr.py:395-404`, `pr-2788` sha `bd6b5e217d8985d1692e2465632dde25e761b863`):

```python
    out: dict[str, int] = {}
    if issue_states is None:
        issue_states, ok = closure_sweep.issue_state_index_all(root)
        if spawn._watchdog_note_gh_failure(root, "spawn-on-pr", not ok):
            print("[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, "
                  "이번 틱 판정 보류 (연속 실패)")
        if not ok:
            issue_states = None
    else:
        spawn._watchdog_note_gh_failure(root, "spawn-on-pr", False)
```

## Open findings

checked: sections 1-9 above (this session's own executed commands and outputs) — result: none open — all four standing invariants hold, all three acceptance checks were independently re-derived, and the symmetry attack on the new `else` branch (section 1) found no path by which a stale/partial/never-attempted fetch reaches the reset call.

## Next steps

acceptance: sections 1-9 above (this session's own executed commands and outputs) — result:
```
loop_state: landed -- this is a completed, passing independent verification
of PR #2788; no further action is proposed against it from this review.
```
