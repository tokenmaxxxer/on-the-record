---
issue: 2777
role: observability-explorability+adversarial-review-275db07c
author: observability-explorability+adversarial-review-275db07c
skills: observability-explorability (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: same-commit
loop_state: landed
type: fix
breaking: false
verdict: pass — fixes the dead-reset-path finding from PR #2780's independent verification (`docs/issue-2777/reports/adversarial-review-25204a01.md`, Finding 1): a recovered `gh` lookup now resets the failure streak on the real production call path (FAIL,FAIL,FAIL,RECOVERY → line at tick 3, silence from tick 4, streak back to 0, single post-recovery blip does not immediately re-warn). All three of PR #2780's original acceptance claims re-derived and hold; #2768's 30-closed-subject fixture still green; `out={}`/`pairs=[]` unchanged every tick; `_issue_is_open()` byte-identical to origin/main; failing-test-name set vs origin/main identical (16/16 — see "Full test suite" section below); stdout-byte overhead per tick unchanged from PR #2780's own design (0 healthy, 0 below threshold, 98 at threshold) — the fix's only added cost is one JSON-state read on the healthy path, not new output.
upstream:
  - path: on-the-record PR #2780 (branch issue-2777/observability-explorability+adversarial-review-bb003bd3), gates/spawn_on_pr.py::missing_verification()
    sha: 8250d86911924588780c9d37e5ec3d176506ef3f
  - path: docs/issue-2777/reports/adversarial-review-25204a01.md
    sha: 9c78c3ba531fb36411b1bb274d6fb36579f7cfd4
  - path: gates/spawn_on_pr.py
    sha: same-commit
  - path: gates/test_spawn_on_pr.py
    sha: same-commit
---

# issue-2777 — observability-explorability+adversarial-review-275db07c record

## What was done

Fixed the severe finding from PR #2780's independent verification
(`docs/issue-2777/reports/adversarial-review-25204a01.md`, Finding 1):
`gates/spawn_on_pr.py::missing_verification()`'s new gh-failure-streak
diagnostic (added by PR #2780, itself unmerged) reset the streak only
inside its own `if issue_states is None:` re-fetch branch, which the
verification traced to being unreachable on a healthy tick from the sole
production caller (`watchdog.py:1104`, which always forwards
`issue_states` explicitly — a real dict on success, `None` on failure,
never omitted). Once a sustained outage pushed the streak to 3, recovery
never brought it back down, and a later isolated blip re-triggered the
warning starting from that single failure — the exact per-blip noise
class the streak convention (issue #2196) exists to suppress.

PR #2780 itself was never merged to `main` (state OPEN throughout this
session — canonical: `gh pr view 2780 --json state` output, `"state":"OPEN"`),
so this commit delivers PR #2780's original design plus the reset
correction together, in one change to `gates/spawn_on_pr.py`.

canonical: `git diff dc48170d -- gates/spawn_on_pr.py`, the full change
(same-commit), quoted in relevant part:
```
     out: dict[str, int] = {}
     if issue_states is None:
         issue_states, ok = closure_sweep.issue_state_index_all(root)
+        if spawn._watchdog_note_gh_failure(root, "spawn-on-pr", not ok):
+            print("[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, "
+                  "이번 틱 판정 보류 (연속 실패)")
         if not ok:
             issue_states = None
+    else:
+        spawn._watchdog_note_gh_failure(root, "spawn-on-pr", False)
     if pr_index is None:
```

The `if` branch (PR #2780's original code, unchanged) handles the case
where this function does its own internal fetch — used by every existing
standalone test and by any caller that omits `issue_states`. The new
`else` branch is the fix: whenever a caller already supplies a non-`None`
`issue_states` — which, per the traced production call site, only
happens when that caller's own top-level fetch succeeded this tick — the
streak resets, mirroring `watchdog.py`'s own `closure-sweep` call site
(`if skips: ...warn... else: reset`), which updates the streak in both
branches of its own tick-level if/else. PR #2780's version only ever
updated the streak from a branch that is dead code in production;
this fix updates it from both branches, matching the established
convention it was already citing as its own justification.

derived: `git diff dc48170d --stat -- gates/test_spawn_on_pr.py` (this
tree) — result:
```
 gates/test_spawn_on_pr.py | 115 +++++++++++++++++++++++++++++++++++++++++++
 1 file changed, 115 insertions(+)
```
derived: `grep -c '^def test_degraded_lookup\|^def test_healthy_lookup\|^def test_gh_failure_streak_resets' gates/test_spawn_on_pr.py`
— result:
```
4
```
4 new test functions added: 3 carried over from PR #2780's own diff
(quiet below threshold, the line at threshold, a healthy internal fetch
staying quiet) plus 1 new one added here,
`test_gh_failure_streak_resets_on_recovery_via_production_caller_shape`,
which drives `missing_verification()` through the exact production
calling shape (explicit `issue_states=None` on failing ticks, explicit
real dict on the recovery tick — never letting the function do its own
internal fetch, which is what every other test in the file does, and
which is why PR #2780's own tests never exercised the dead-reset path
Finding 1 found).

### Acceptance check 1 — forced gh-lookup failure, before/after, on the real production call path

acceptance: `python3 /tmp/repro_2777_prod_recovery.py <root>` (own
script, driving `spawn_missing_for_pr(root, str(root), dry_run=True,
issue_states=<caller-fetch-result>, pr_index={})` — the exact
`watchdog.py:1104` calling shape, one caller-level fetch per tick,
forwarded explicitly — sequence FAIL,FAIL,FAIL,RECOVERY,RECOVERY,FAIL)
— result:
```
=== PRE-FIX (fresh origin/main dc48170d, PR #2780's design not present) ===
tick 1 (FAIL): pairs=[] stdout='' streak=0
tick 2 (FAIL): pairs=[] stdout='' streak=0
tick 3 (FAIL): pairs=[] stdout='' streak=0
tick 4 (OK): pairs=[] stdout='' streak=0
tick 5 (OK): pairs=[] stdout='' streak=0
tick 6 (FAIL): pairs=[] stdout='' streak=0

=== POST-FIX (this tree) ===
tick 1 (FAIL): pairs=[] stdout='' streak=1
tick 2 (FAIL): pairs=[] stdout='' streak=2
tick 3 (FAIL): pairs=[] stdout='[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)\n' streak=3
tick 4 (OK): pairs=[] stdout='' streak=0
tick 5 (OK): pairs=[] stdout='' streak=0
tick 6 (FAIL): pairs=[] stdout='' streak=1
```
Pre-fix: silent forever (the original #2768-reorder regression, still
present since PR #2780 was never merged). Post-fix: the line appears at
tick 3 (the threshold) and stops at tick 4 (recovery) — the streak reads
`0` right after recovery, not merely "below threshold from a partial
decrement," and tick 6's isolated post-recovery blip starts a fresh
streak of `1` rather than immediately re-warning — proving the reset
actually zeroed the counter rather than just suppressing the print. This
is the reproduction the review explicitly asked for: failure, failure,
failure, RECOVERY, on the real production call path (`spawn_missing_for_pr`
with a caller-supplied `issue_states`, not `missing_verification()`
called with `issue_states=None` directly).

### Acceptance check 2 — #2768's 30-closed-subject fixture, re-run

derived: `grep -n 'closed_subjects = \[f"issue-{93000 + i}" for i in range(30)\]' gates/test_spawn_on_pr.py`
— result:
```
gates/test_spawn_on_pr.py:498:    closed_subjects = [f"issue-{93000 + i}" for i in range(30)]
```
acceptance: `python3 -m pytest -q gates/test_spawn_on_pr.py::test_closed_and_open_subjects_mixed_only_open_unmappable_branch_reported gates/test_spawn_on_pr.py::test_closed_issue_with_unmappable_branch_prints_nothing gates/test_spawn_on_pr.py::test_open_subject_with_unmappable_branch_still_reports_missing_branch`
— result:
```
3 passed in 0.84s
```

### Acceptance check 3 — `spawn_missing_for_pr(..., dry_run=True)` pairs, byte-identical

Covered by the same acceptance-check-1 repro above: `pairs=[]` on every
tick, both pre-fix and post-fix trees, both FAIL and RECOVERY ticks — no
spawn-eligibility decision moved by either PR #2780's original design or
this fix's reset correction.

### `_issue_is_open()` untouched

acceptance: `diff <(sed -n '251,270p' gates/spawn_on_pr.py) <(sed -n '251,270p' /tmp/pre2777_base_wt2/gates/spawn_on_pr.py)`
(`/tmp/pre2777_base_wt2` = worktree at `dc48170d`, the rebased origin/main
tip) — result:
```
IDENTICAL
```
Still fail-closed on `issue_states is None`; no fail-open introduced.

### Full test suite, rebased onto current origin/main

Rebased first: `git fetch origin main && git merge --ff-only origin/main`
(no divergent commits on this branch yet, so this was a fast-forward from
`9c78c3ba` to `dc48170d` — `issue-2755: require denial message content in
7 upstream-defect-scope-guard tests (#2781)`, which does not touch
`gates/spawn_on_pr.py` or `gates/test_spawn_on_pr.py`) — the working-tree
edits carried through unaffected; re-ran every check in this record
against this post-rebase tip.

acceptance: `python3 -m pytest -q` (this tree, post-rebase, with fix +
4 new tests) — result:
```
16 failed, 557 passed, 3 xfailed
```
acceptance: `python3 -m pytest -q` (`/tmp/pre2777_base_wt2`, worktree at
`dc48170d`, no #2777 fix) — result:
```
16 failed, 553 passed, 3 xfailed
```
canonical: `diff <(grep '^FAILED' pre_fix_run2.txt | sort) <(grep '^FAILED' post_fix_run2.txt | sort)`
(both this session's own two runs above, captured to `/tmp/pre_fix_run2.txt`
and `/tmp/post_fix_run2.txt`) — result:
```
(empty diff — IDENTICAL SETS, both 16 names)
```
The +4 delta is exactly this commit's 4 new tests (3 carried from PR
#2780's diff, 1 new recovery test — see "What was done" above,
`git diff dc48170d --stat -- gates/test_spawn_on_pr.py` cited there).

## Why

The verification's resolution path named two options: (a) have
`missing_verification()` call the reset once whenever `issue_states is
not None` at entry (mirroring `closure-sweep`'s if/else at the tick
level), or (b) have `watchdog.py` itself own the reset call right after
its own top-level fetch succeeds. Chose (a): it keeps the entire
gh-degradation diagnostic — both the warn path and its reset — inside
`missing_verification()`, the single function that owns the
`"spawn-on-pr"` streak-signal name, rather than splitting that ownership
across two files. `watchdog.py` does not need to know this signal exists
at all; it just forwards `issue_states` as it always did. Option (b)
would have worked too, but it would place a `spawn-on-pr`-specific reset
call inside `watchdog.py`'s generic per-tick dispatch loop, coupling a
gate-internal diagnostic to the orchestrator for no behavioral gain over
(a).

canonical: `watchdog.py:523-542` (this session, same lines quoted in
`docs/issue-2777/reports/adversarial-review-25204a01.md`), the streak
helper's own semantics: `failed=False` resets the streak to 0 and is a
no-op write when the streak is already 0. This meant implementing (a)
needed only one line — an `else` clause calling the same helper PR #2780
already imported, with `failed=False` — no new state shape, no new
helper.

Kept PR #2780's original design otherwise unchanged: the 3-tick
threshold (reusing `WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD`), the exact
print text, and `_issue_is_open()` left untouched. The first
verification (before Finding 1) already judged the threshold reuse and
the overall approach defensible; nothing about the reset fix changes
that judgment, so re-litigating it here would be redundant per the
"what holds" list this task named.

**Scope limit, stated per the review's request (not fixed here): the
3-tick floor.** Any outage of two ticks or fewer that resolves is
indistinguishable, from raw stdout, from a fully healthy board — no line
prints in either case. This is a real, intentional trade named in PR
#2780's own record and re-confirmed by the first verification's Finding
3: the alternative (warning on every single blip) would resurrect the
per-blip noise the `_watchdog_note_gh_failure` convention (issue #2196)
already exists to prevent for `closure-sweep` and `board-sweep:pr-index`.
This fix does not touch that trade-off — it only ensures the trade
actually behaves as designed (bounded, resettable) rather than degrading
into a one-way ratchet once first tripped, which was Finding 1's
complaint.

**Scope limit, stated per the review's request (not fixed here): the
streak lives under `STATE_ROOT`, which issue #2216 (open) already flags
as reinstall-volatile.** A reinstall mid-outage resets the streak to 0,
so a reinstall cadence at or above roughly 1 per 2 ticks during a
sustained outage could mean this fix's degraded-state line never
actually appears for the sustained-outage case it targets. This is
issue #2216's own already-documented defect — canonical:
`docs/issue-2777/reports/adversarial-review-25204a01.md` lines 302-309
(this session read that section above; it quotes `gh issue view 2216`
naming `_watchdog_note_gh_failure` explicitly, predating PR #2780) — not
something this fix introduces or is positioned to fix, noted here only
so this fix's promise is not overstated as unconditional.

## What did not work

None — no reverted approach. The `else`-branch reset was correct on
first implementation; the only iteration needed was writing the
production-call-shape repro script itself, which initially forgot to
pin `closure_sweep.issue_state_index_all` for the internal re-fetch that
still fires on FAIL ticks (since the caller forwards `issue_states=None`
explicitly on those ticks) — caught immediately because the unpinned
version would have made a real network call, not treated as a
scope-exceeded stop.

## Upstream basis

- on-the-record PR #2780 (branch
  `issue-2777/observability-explorability+adversarial-review-bb003bd3`,
  head `8250d86911924588780c9d37e5ec3d176506ef3f`, state OPEN throughout
  this session per `gh pr view 2780 --json state`) — the reviewed design
  this commit carries forward, plus the fix.
- `docs/issue-2777/reports/adversarial-review-25204a01.md` @
  `9c78c3ba531fb36411b1bb274d6fb36579f7cfd4` (read in full this session)
  — the independent verification that reproduced Finding 1 (dead reset
  path) on the production call shape and named the resolution path this
  commit implements.
- `gates/spawn_on_pr.py`, `gates/test_spawn_on_pr.py` — same-commit, the
  files changed.

## Open findings

None from this commit. Finding 2 (issue #2216's reinstall-volatile
`STATE_ROOT`) and the 3-tick-floor scope limit (Finding 3's territory)
are both named under "Why" above as bounds on this fix's promise, not
defects this fix introduces — Finding 2 remains issue #2216's to
resolve.

## Next steps

None — `loop_state: landed`. Fix, its 4 regression tests, and this
record land together in one commit (build-now bypass, `CORE_BUILD_NOW=1`).

## Four standing invariants

- **No return of the retired role axis in any reshaped form**: `git diff
  dc48170d -- gates/spawn_on_pr.py` (quoted under "What was done") touches
  only the `issue_states is None`/`else` branches inside
  `missing_verification()` — no role/kind name list, no closed-set
  enumeration.
- **No new bug — failing-test set vs origin/main, as SETS OF NAMES**:
  canonical: the empty-diff result quoted under "Full test suite, rebased
  onto current origin/main" above (16 names both sides, against rebased
  tip `dc48170d`). The +4 delta is entirely this commit's own new passing
  tests.
- **No overhead increase — added bytes per tick, healthy and degraded**:
  measured directly (own script, `len(stdout.encode())` per tick) —
  result:
  ```
  healthy tick stdout bytes: 0
  degraded tick (below threshold) stdout bytes: 0
  degraded tick (2nd+3rd call combined) stdout bytes: 98
  ```
  All three identical to PR #2780's own already-reviewed design,
  unchanged by this fix. This fix's only added cost is not stdout: the
  new `else` branch adds one `_watchdog_note_gh_failure` call on the
  healthy path, which is a JSON-state read (and a write only when the
  streak actually changes, per that helper's own `changed` guard) — the
  same per-tick I/O shape `closure-sweep`'s call site already has, not
  new infrastructure, and zero new `gh`/subprocess calls either way.
- **Monitor and watch machinery unbroken and not quieter — this is the
  subject itself**: strictly additive print path, so "quieter" cannot
  occur in the print-count sense; the fix specifically corrects the
  direction Finding 1 flagged as the opposite failure (a permanent
  alarm that never returns to quiet) — acceptance check 1 above shows
  the line stopping exactly at the recovery tick, which is what "not
  quieter" is supposed to guarantee without becoming "never quiet again."

skill-verdict: work-in-english — invoked; applied: this record, both
docstring additions in `gates/spawn_on_pr.py` (matching the surrounding
file's existing Korean-docstring convention per the skill's own
"project convention conflicts" guidance), all new test names, comments,
and repro scripts are in English except quoted print strings/comments
already Korean in the reviewed file.
skill-verdict: observability-explorability — not-applicable: this is a
bugfix restoring one existing diagnostic's correctness (a failure-streak
reset), not designing a new dashboard/panel or an ad-hoc query surface
over raw events.
skill-verdict: adversarial-review — not-applicable: this session builds
the fix for a finding an independent verification already surfaced; it
is not itself tasked with a structurally-independent evaluation of a
fresh artifact, and self-review of one's own just-written fix is what
that skill's protocol exists to avoid substituting for.
other mounted skills: not triggered.
