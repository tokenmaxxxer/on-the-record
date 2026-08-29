---
issue: 2777
role: adversarial-review-25204a01
author: adversarial-review-25204a01
skills: adversarial-review (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2780's own deliverable for issue-2777
code_under_review: on-the-record PR #2780 (8250d86911924588780c9d37e5ec3d176506ef3f), gates/spawn_on_pr.py::missing_verification()
loop_state: landed
type: review
breaking: false
verdict: changes-recommended — canonical: this session's own repro runs below re-derive all three of PR #2780's acceptance claims and all hold under independent scripts. But the same session's own repro (`av_repro_prod_path.py`, see Finding 1) shows the failure-streak this fix relies on has a dead reset path in the real `watchdog.py` call contract: once the streak first reaches 3 it never returns to 0 under normal operation, so a later isolated (non-consecutive) `gh` blip re-triggers the warning starting from that single failure — the exact noise class this mechanism exists to suppress. This also reuses open issue #2216's reinstall-volatile state storage unmodified and unmentioned.
upstream:
  - path: on-the-record PR #2780, branch issue-2777/observability-explorability+adversarial-review-bb003bd3
    sha: 8250d86911924588780c9d37e5ec3d176506ef3f
  - path: docs/issue-2652/reports/adversarial-review-58d892b0.md
    sha: aa653aeef72691cd6e05ea42797b8b273a424a39
  - path: gates/watchdog.py
    sha: 8250d86911924588780c9d37e5ec3d176506ef3f
---

# issue-2777 — adversarial-review-25204a01 record

## What was done

Independent verification of PR #2780 (`gates/spawn_on_pr.py::missing_verification()`
reports a degraded `gh` issue-state lookup with its own line, gated on
`watchdog.py`'s existing 3-consecutive-failure-streak helper, instead of
going fully silent — the regression #2652's is-open/branch-check reorder
introduced). Built a worktree at PR #2780's head alongside this branch's
own base tree, and wrote fresh repro scripts (`/tmp/av_repro_*.py`) rather
than running the PR's own `/tmp/repro_2777*.py` scripts, per the
independence requirement: re-derive claims from primary evidence, not from
the artifact under review's own harness.

derived: `git worktree add /tmp/pr2780_wt pr-2780-review` (this session) —
result:
```
HEAD의 현재 위치는 8250d869입니다 issue-2777: report degraded gh issue-state lookup instead of going silent
```
base tree used as "pre-fix" is this branch's own `HEAD`
(`c76a98089f74de46405134a0c1ef64bf753e13e2`, #2768's reorder with no #2777
fix yet applied).

### Claim 1 — forced gh-lookup failure, before/after

acceptance: `python3 /tmp/av_repro_ticks.py <root> sustain 4` (own script,
one OPEN subject with a genuinely missing branch, `closure_sweep.
issue_state_index_all` forced to `(None, False)` every tick) — result:
```
=== BASE (main HEAD, pre-#2777-fix) sustain 4 ===
tick 1: out={} stdout='' streak_state=None
tick 2: out={} stdout='' streak_state=None
tick 3: out={} stdout='' streak_state=None
tick 4: out={} stdout='' streak_state=None

=== PR2780 (post-fix) sustain 4 ===
tick 1: out={} stdout='' streak_state={'gh_failure_streaks': {'spawn-on-pr': 1}}
tick 2: out={} stdout='' streak_state={'gh_failure_streaks': {'spawn-on-pr': 2}}
tick 3: out={} stdout='[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)\n' streak_state={'gh_failure_streaks': {'spawn-on-pr': 3}}
tick 4: out={} stdout='[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)\n' streak_state={'gh_failure_streaks': {'spawn-on-pr': 4}}
```
This re-derivation lines up with PR #2780's own claim: silent every tick
pre-fix, a distinct line from tick 3 post-fix, `out={}` unchanged on every
tick both trees (no spawn-eligibility change).

### Claim 2 — #2768's 30-closed-subject fixture, re-run

derived: `grep -n 'closed_subjects = \[f"issue-{93000 + i}" for i in range(30)\]' gates/test_spawn_on_pr.py`
(in `/tmp/pr2780_wt`) — result:
```
498:    closed_subjects = [f"issue-{93000 + i}" for i in range(30)]
```
the fixture genuinely builds 30 closed subjects, not merely a "30" claimed
in prose.

acceptance: `python3 -m pytest -q gates/test_spawn_on_pr.py::test_closed_and_open_subjects_mixed_only_open_unmappable_branch_reported gates/test_spawn_on_pr.py::test_closed_issue_with_unmappable_branch_prints_nothing gates/test_spawn_on_pr.py::test_open_subject_with_unmappable_branch_still_reports_missing_branch`
(in `/tmp/pr2780_wt`) — result:
```
3 passed in 0.84s
```

### Claim 3 — `spawn_missing_for_pr(..., dry_run=True)` pairs, byte-identical

acceptance: `python3 /tmp/av_repro_dryrun.py <root>` (own script — a board
with one genuine spawn candidate under a lookup forced to `(None, False)`)
— result:
```
=== BASE dry_run ===
pairs=[]
=== PR2780 dry_run ===
pairs=[]
```
byte-identical (`[]` both sides).

### `_issue_is_open()` untouched

acceptance: `diff <(sed -n '251,260p' gates/spawn_on_pr.py) <(sed -n '251,260p' /tmp/pr2780_wt/gates/spawn_on_pr.py)`
— result:
```
IDENTICAL
```
Still fail-closed on `issue_states is None`; the must-not this issue
names (no fail-open there) holds.

### Four standing invariants

- **No return of the retired role axis**: `git diff HEAD..pr-2780-review -- gates/spawn_on_pr.py`
  touches only `missing_verification()`'s docstring and the `issue_states
  is None` branch — no role/kind name list, no closed-set enumeration.
- **No new bug, failing-test set vs `HEAD` as SETS OF NAMES**:
  acceptance: `python3 -m pytest -q` (base tree) — result:
  ```
  16 failed, 553 passed, 3 xfailed
  ```
  acceptance: `python3 -m pytest -q` (`/tmp/pr2780_wt`) — result:
  ```
  16 failed, 556 passed, 3 xfailed
  ```
  derived: `diff <(grep '^FAILED' base_run.txt | sort) <(grep '^FAILED' pr_run.txt | sort)`
  (both captured this session's own two runs above) — result:
  ```
  (empty diff — the two 16-name sets are identical)
  ```
  The +3 delta is exactly the 3 new tests this PR adds
  (`test_degraded_lookup_stays_quiet_below_the_failure_streak_threshold`,
  `test_degraded_lookup_reports_its_own_state_once_streak_hits_threshold`,
  `test_healthy_lookup_after_this_functions_own_fetch_stays_quiet`).
  acceptance: `python3 -m pytest -q gates/test_spawn_on_pr.py::test_degraded_lookup_stays_quiet_below_the_failure_streak_threshold gates/test_spawn_on_pr.py::test_degraded_lookup_reports_its_own_state_once_streak_hits_threshold gates/test_spawn_on_pr.py::test_healthy_lookup_after_this_functions_own_fetch_stays_quiet`
  (`/tmp/pr2780_wt`) — result:
  ```
  3 passed in 0.86s
  ```
  This specific check — the only one of the four with a fixed, mechanical
  procedure — holds clean on its own terms. It does not by itself rule out
  a bug the existing suite never exercises; see Finding 1, which none of
  these tests reach (they all call `missing_verification()` without ever
  supplying an `issue_states=` argument, unlike the real caller).
- **No overhead increase**: derived: `git diff HEAD..pr-2780-review -- gates/spawn_on_pr.py`
  (quoted under Finding 1 below) adds one `_watchdog_note_gh_failure()`
  call (a small local JSON read/write against the existing
  `watchdog_noise_state.json`) plus a conditional `print`, confined inside
  a pre-existing `if issue_states is None:` branch that already made a
  `gh` call before this PR touched anything. Per Finding 1 below, in the
  actual production healthy-tick path this new call never executes at
  all — zero added overhead in the healthy case; in the degraded case,
  one small local file op, no new `gh`/subprocess call.
- **Monitor/watch machinery not quieter**: literally true — this is a
  strictly additive print path, so "quieter" cannot occur. But per
  Finding 1, the same defect that makes it "not quieter" also makes it
  noisier than designed once the streak first trips, which this
  invariant's phrasing does not catch.

## Why

The task named the 3-tick threshold as the design decision to attack and
asked whether trading away the first two ticks of every degradation is
the right call, whether the streak state survives reinstall (issue #2216),
and whether a 2-tick outage that resolves is ever visible. Re-deriving the
literal acceptance checks was necessary but not sufficient to answer
those — none of the PR's own checks, nor its 3 new tests, exercise the
actual `watchdog.py` calling convention (`issue_states` always forwarded
explicitly, never omitted), so a bug specific to that convention would not
surface from citing the PR's own record. Wrote new scripts that simulate
the real caller contract instead of the standalone
`missing_verification(root, pr_index={})` shape every existing test uses.

## Open findings

### Finding 1 (severe) — the failure streak's reset path is dead code in production, so it never quiets back down

canonical: `gates/spawn_on_pr.py:385-391` (`/tmp/pr2780_wt`), quoted
verbatim:
```
    out: dict[str, int] = {}
    if issue_states is None:
        issue_states, ok = closure_sweep.issue_state_index_all(root)
        if spawn._watchdog_note_gh_failure(root, "spawn-on-pr", not ok):
            print("[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, "
                  "이번 틱 판정 보류 (연속 실패)")
        if not ok:
            issue_states = None
```
`_watchdog_note_gh_failure("spawn-on-pr", not ok)` lives only inside this
`if issue_states is None:` branch. In production this function has one
caller.

derived: `grep -rn "spawn_missing_for_pr(" --include="*.py" . | grep -v "test_\|def spawn_missing_for_pr"`
(`/tmp/pr2780_wt`) — result:
```
watchdog.py:1104:            spawned = spawn_on_pr.spawn_missing_for_pr(
```
canonical: `watchdog.py:1075-1105` (`/tmp/pr2780_wt`), the sole call site,
quoted in relevant part:
```
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
`issue_states` is fetched once at the top of the tick and forwarded
explicitly either way — a real dict on success, `None` on failure — never
omitted. So on a genuinely healthy tick, `missing_verification()` receives
a non-`None` `issue_states`, the `if issue_states is None:` branch (the
only place this PR's new call lives) never runs, and the reset call
(`_watchdog_note_gh_failure("spawn-on-pr", False)`) is never reached.
Compare `closure-sweep`'s own use of the same helper:

canonical: `watchdog.py:1136-1143` (`/tmp/pr2780_wt`), quoted verbatim:
```
        if skips:
            count += 1
            # 이슈 #2196: 단발 gh blip 은 조용히 넘어간다 — 연속 N틱
            # 실패면 그때부터 경고한다.
            if _sp._watchdog_note_gh_failure(root, "closure-sweep", True):
                print(f"[watchdog] closure-sweep: 확인 불가 (gh 실패) {len(skips)}건")
        else:
            _sp._watchdog_note_gh_failure(root, "closure-sweep", False)
```
`closure-sweep`'s reset runs in the `else` of an if/else executed every
single tick regardless of outcome. PR #2780's new "spawn-on-pr" signal
does not replicate that shape — it only ever calls the helper from inside
the failure-triggered re-fetch branch.

acceptance: `python3 /tmp/av_repro_prod_path.py /tmp/pr2780_wt` (own
script, replicating `watchdog.py`'s exact caller pattern: fetch
`issue_states` once per tick, forward it explicitly, sequence
FAIL,FAIL,FAIL,OK,OK,OK) — result:
```
tick 1 (FAIL, caller-level ok=False): out={} stdout='' streak=1
tick 2 (FAIL, caller-level ok=False): out={} stdout='' streak=2
tick 3 (FAIL, caller-level ok=False): out={} stdout='[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)\n' streak=3
tick 4 (OK, caller-level ok=True): out={} stdout='[spawn-on-pr] 1건 이전에 보고된 매핑-불가 subject — 계속 무시 (반복 안 찍음)\n' streak=3
tick 5 (OK, caller-level ok=True): out={} stdout='[spawn-on-pr] 1건 이전에 보고된 매핑-불가 subject — 계속 무시 (반복 안 찍음)\n' streak=3
tick 6 (OK, caller-level ok=True): out={} stdout='[spawn-on-pr] 1건 이전에 보고된 매핑-불가 subject — 계속 무시 (반복 안 찍음)\n' streak=3
```
The streak sits at 3 through three fully healthy ticks — the reset never
fires (the trailing `매핑-불가` line each tick is an unrelated one-shot
summary from this repro's own board fixture, not the gh-degradation
signal).

acceptance: own follow-up script, sequence FAIL,OK,FAIL,OK,FAIL,OK — three
fully **isolated** blips, never consecutive, each recovering before the
next — result:
```
tick 1 (FAIL): streak=1
tick 2 (OK):   streak=1
tick 3 (FAIL): streak=2
tick 4 (OK):   streak=2
tick 5 (FAIL): stdout='[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)\n' streak=3
tick 6 (OK):   streak=3
```
The warning fires on tick 5 despite zero consecutive failures anywhere in
the sequence — the counter only ever accumulates.

canonical: `gates/spawn_on_pr.py:380-383` (`/tmp/pr2780_wt`), the fix's
own stated design intent, quoted verbatim:
```
    이 사실 자체는 watchdog.py 의 `closure-sweep` 실패-스트릭 관용
    (`_watchdog_note_gh_failure`) 과 같은 방식으로 한 줄 남긴다: 단발
    blip 은 삼키고, 연속 실패만 경고해 "닫힌 이슈라 조용함"/"정상이라
    조용함"과 구별되는 세 번째 상태("판정 불가라 건너뜀")를 드러낸다.
```
("swallow single blips, warn only on *consecutive* failure") — the
isolated-blip repro directly contradicts this stated intent: once the
streak first reaches 3, by any combination of failures, it stays there
under normal operation and every later `gh` failure — including a single
isolated blip an arbitrary time afterward — prints starting from that one
failure. This is the identical class of noise the `_watchdog_note_gh_failure`
convention (issue #2196) exists to suppress, reintroduced for this one new
signal specifically because `closure-sweep`'s every-tick if/else calling
shape was not replicated here.

**Resolution path**: call `_watchdog_note_gh_failure(root, "spawn-on-pr",
False)` on the success path too — either `missing_verification()` calls it
once whenever `issue_states is not None` at entry (mirroring
`closure-sweep`'s if/else at the tick level), or `watchdog.py` itself owns
the reset call right after its own top-level fetch succeeds, next to
`closure-sweep`'s existing reset.

### Finding 2 (design) — this reuses the exact state machinery issue #2216 already flagged as reinstall-volatile

canonical: `gates/state_paths.py:30-31` (`/tmp/pr2780_wt`), quoted
verbatim:
```
STATE_ROOT = (Path(os.environ["MUSTER_STATE_ROOT"]).resolve()
              if os.environ.get("MUSTER_STATE_ROOT") else ROOT / "runs")
```
derived: `printenv | grep -i MUSTER_STATE_ROOT; echo "exit=$?"` (this
session's own shell) — result:
```
exit=1
```
(unset in this environment, so `STATE_ROOT` falls back to the gitignored
`<checkout>/runs`).

canonical: `gh issue view 2216` (this session) — state: OPEN, quoted in
relevant part:
```
"_watchdog_note_gh_failure" (consecutive-failure counting) shares the same
state file and the same defect: its failure streak resets to zero on
every reinstall, so the "warn only after N consecutive failures" guard
silently never reaches N.
```
written before PR #2780 existed, and naming this exact helper. derived:
`git log --all --oneline --grep="2216"` (this session) — result:
```
(no commit references issue #2216; only an unrelated #2240 scoping fix appears for a different search term)
```

acceptance: own script, simulating a reinstall (deleting the state file)
mid-streak — result:
```
tick 1 (failing, pre-reinstall): streak_state={'gh_failure_streaks': {'spawn-on-pr': 1}}
tick 2 (failing, pre-reinstall): streak_state={'gh_failure_streaks': {'spawn-on-pr': 2}}
--- simulated reinstall: wiped .../watchdog_noise_state.json ---
tick 3 (failing, post-reinstall): streak_state={'gh_failure_streaks': {'spawn-on-pr': 1}}
tick 4 (failing, post-reinstall): streak_state={'gh_failure_streaks': {'spawn-on-pr': 2}}
tick 5 (failing, post-reinstall): stdout='[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)\n' streak_state={'gh_failure_streaks': {'spawn-on-pr': 3}}
```
Per #2216's own text, reinstalls of this plugin checkout have happened
"constantly." If a reinstall lands roughly every 1-2 ticks during a
sustained outage, the streak may never reach 3, and this fix's
degraded-state line may never appear for exactly the sustained-outage case
it targets — reproducing this issue's own silence through a different,
already-documented mechanism. PR #2780's record does not name issue #2216
or this dependency anywhere.

### Finding 3 (design judgment, requested by the task) — is trading away ticks 1-2 the right call?

acceptance: own script, a 2-tick outage that resolves on tick 3 — result:
```
tick 1 (failing): out={} stdout=''
tick 2 (failing): out={} stdout=''
tick 3 (recovers): out={} stdout='[spawn-on-pr] 1건 이전에 보고된 매핑-불가 subject — 계속 무시 (반복 안 찍음)\n'
final streak_state={'gh_failure_streaks': {'spawn-on-pr': 0}}
```
No "gh 실패" line at any point — ticks 1-2's stdout is byte-identical to a
fully healthy quiet tick, so an operator reading raw output cannot tell
"everything is fine" from "gh has been down for up to 2 ticks," and a
2-tick outage that resolves is never surfaced at all.

Judgment: the trade is reasonable in isolation. The issue's own acceptance
framing explicitly asks the post-#2652 quiet output to survive a healthy
tick, and warning on every single `gh` failure would resurrect the same
per-blip noise the streak convention (#2196) already exists to prevent
for `closure-sweep` and `board-sweep:pr-index` — reusing an established
constant and idiom rather than inventing a new threshold for one new
signal is reasonable economy, and the issue's own framing ("appeared
repeatedly... the night this landed") describes a sustained, multi-tick
condition, which a 2-tick bounded delay answers proportionately.

That judgment assumes the trade is bounded — "2 ticks of silence per
outage, no more." Finding 1 shows it is not bounded in practice: once
tripped, the blind window for the *next* event collapses to zero (an
isolated single blip triggers immediately, per the FAIL-OK-FAIL-OK-FAIL-OK
repro above) while simultaneously losing the "only on genuinely
consecutive failure" guarantee the design cites as its own justification.
The 2-tick trade as designed reads as acceptable; the 2-tick trade as
implemented does not hold past the first crossing.

## Upstream basis

- on-the-record PR #2780, branch
  `issue-2777/observability-explorability+adversarial-review-bb003bd3`,
  head `8250d86911924588780c9d37e5ec3d176506ef3f` — the artifact under
  review.
- canonical: `docs/issue-2652/reports/adversarial-review-58d892b0.md` @
  `aa653aeef72691cd6e05ea42797b8b273a424a39` (read in full this session) —
  the prior independent review that first reproduced the silence
  regression this issue was filed from; used here to confirm PR #2780's
  stated root-cause diagnosis lines up with it, not itself re-verified
  (out of scope for this record).
- `gates/watchdog.py` (same sha as PR #2780, unchanged by it) — read to
  establish the real, sole production call site of `spawn_missing_for_pr()`
  and the contrasting `closure-sweep` calling convention for the same
  helper (both quoted under Finding 1).

## Next steps

None from this record directly — `loop_state: landed`, this is a
verification record, not a fix. Finding 1 names a concrete resolution
path for a follow-up fix session; Finding 2 means that follow-up should
not be considered finished without also addressing, or at minimum
re-confirming against, issue #2216.

## What did not work

None — no reverted approach. The independent scripts needed two rounds to
get right: the first `av_repro_ticks.py` attempt used a board fixture
shape (`{"issue_number": ..., "board_condition": ...}`) that did not match
`subject_deliverable_record()`'s expected `{role: {frontmatter}}` shape and
raised `AttributeError: 'int' object has no attribute 'get'`; and the
first `av_repro_prod_path.py` attempt patched only its own local
"caller-level" fetch functions and not the module-level
`closure_sweep.issue_state_index_all`/`spawn_on_pr.closure_sweep.
issue_state_index_all` attributes `missing_verification()` itself falls
back to, so that first run silently exercised this machine's live `gh`
state (via a real network call) rather than the intended forced-failure
condition — both caught by inspecting the output before drawing
conclusions, not treated as a scope-exceeded stop.

skill-verdict: adversarial-review — invoked; applied: this entire record
is a structurally independent evaluation of PR #2780's own claims, built
from repro scripts written fresh in this session rather than reusing or
citing the PR's own `/tmp/repro_2777*.py` harness.
skill-verdict: defect-verification-independence-from-upstream-verdicts — invoked; applied: re-derived all three of PR #2780's acceptance claims from primary evidence (own scripts, own pytest runs) rather than citing the PR record's stated results, and deliberately extended past the PR's own three claims into an edge case (the real `watchdog.py` calling convention, isolated non-consecutive blips) that its own tests never exercise — surfacing Finding 1, which a scope limited to citing the closed_checks-equivalent claims would have missed.
skill-verdict: work-in-english — invoked; applied: this record, all repro scripts, and all new prose are in English; the only Korean is quoted verbatim (print strings, code comments already in the reviewed files).
