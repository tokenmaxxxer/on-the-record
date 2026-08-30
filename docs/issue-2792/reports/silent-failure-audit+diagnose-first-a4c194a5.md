---
issue: 2792
role: silent-failure-audit+diagnose-first-a4c194a5
author: silent-failure-audit+diagnose-first-a4c194a5
skills: silent-failure-audit (skill-repository(c05de12)), diagnose-first (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - gates/closure_sweep.py
  - gates/spawn_on_pr.py
  - gates/test_spawn_on_pr.py
  - watchdog.py
type: fix
breaking: false
verdict: landed
loop_state: landed
upstream:
  - path: gates/closure_sweep.py (issue_state_index_all, lines 259-266/299-300 as cited by the issue)
    sha: same-commit
---

# issue-2792 — silent-failure-audit+diagnose-first-a4c194a5 record

## What was done

Changed `gates/closure_sweep.py::issue_state_index_all()`'s return contract
from `(index, ok: bool)` to `(index, status: str)`, where `status` is one
of three named constants: `ISSUE_INDEX_OK`, `ISSUE_INDEX_TRUNCATED`,
`ISSUE_INDEX_FAILED`. `index` is a real dict only under `ISSUE_INDEX_OK`;
under the other two it is `None`, same as before — but which of the two
it is is now a distinct, checkable value instead of a discarded fact.

canonical: `gates/closure_sweep.py` lines 245-262 (this commit, working
tree)
```python
ISSUE_INDEX_OK = "ok"
ISSUE_INDEX_TRUNCATED = "truncated"
ISSUE_INDEX_FAILED = "failed"


def issue_state_index_all(root: Path) -> tuple[dict[int, str] | None, str]:
```

Threaded the new status through every caller:

- `gates/spawn_on_pr.py::missing_verification()` (the automatic-tick path
  — the exact site the issue names) now notes **two** independent
  streak signals instead of one: `"spawn-on-pr"` (real gh failure) and
  `"spawn-on-pr:truncated"` (index too large to trust). Each accumulates
  and warns on its own schedule via the existing
  `_watchdog_note_gh_failure()` streak convention (single blips quiet,
  `WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD` consecutive ticks warn), and
  each prints its own distinct line — never the same "gh 실패" line for
  both.
- `gates/spawn_on_pr.py::backfill_closed()` (opt-in CLI) now prints the
  `status` value on a non-OK fetch instead of silently discarding it.
- `gates/closure_sweep.py::find_violations()`'s existing
  `"gh-issue-list-failed"`/`"gh-issue-list-truncated"` skip-reason
  branch (already correct in shape before this change) now reads the
  named `status` constant instead of a bare `not issue_states_ok` bool.
- `watchdog.py::_board_wide_sweep()`'s top-level fetch and its
  `closure-sweep` block: `rate_limited_this_tick` (which backs off
  board-sweep's polling interval) is now gated on
  `status == ISSUE_INDEX_FAILED` specifically — a truncated index is a
  structural board-size condition that backing off cannot fix, so it
  must not trip the same backoff a real gh failure does (this matches
  the *old* boolean's behavior exactly: `ok=True` on truncation already
  meant `rate_limited_this_tick` stayed `False` there; the rename only
  makes that intent readable instead of accidental). The `closure-sweep`
  "확인 불가" line now tallies skip reasons by name instead of a single
  generic "(gh 실패)" label, so a truncated closure-sweep tick is no
  longer mislabeled as a gh failure either.
- `gates/closure_sweep.py::main()` and `spawn.py`'s `closure-sweep` CLI
  subcommand both discard the status value (`issue_states, _ = ...`)
  exactly as before — untouched in behavior, only compatible with the
  new tuple shape (a 2-tuple either way; the unpack doesn't care whether
  the second element is a bool or a string).

No change to `_ISSUE_INDEX_LIMIT`, no change to `_issue_is_open()`'s
fail-closed behavior, no new `gh`/`subprocess` call added anywhere in
the diff.

## Why

canonical: `gh issue view 2792 --repo tokenmaxxxer/on-the-record` body,
paragraph "Why it matters more than its rarity suggests":
```
This is the third distinct quiet mode found in this one code path in a
single night: #2652's reorder produced silence on gh failure, #2777's
first fix produced a permanent alarm instead, and this is silence again
by a different route. The pattern is that spawn-on-pr's "nothing to
say" and "I could not look" states are still not separated at the
source — each fix has separated one pair while leaving another fused.
(None, True) is the shape of the problem: a success flag paired with
absent data.
```
canonical: diagnose-first skill body, section "First: does this even
need the procedure?":
```
Is the cause already confirmed and agreed? If the user has correctly
identified the cause and is asking you to act ... then just do the
task. Do not read the reference files, do not run the stages, do not
open with a diagnostic lecture.
```

skill-verdict: diagnose-first — not-applicable: per the two canonical
quotes directly above, the issue names its own root cause verbatim with
exact line numbers, and the skill's own quoted opt-out rule applies —
this was a *design choice* between a narrow fix and a contract change,
not an unknown cause to locate.

skill-verdict: silent-failure-audit — applied: invoked; traced the
silent-failure chain at `gates/spawn_on_pr.py:397-402` (pre-fix version,
code fence directly below) through Step 1-3 of the skill's procedure
(collect the error-handling site, classify Silently Absorbed, trace
forward to the downstream consequence), and that trace is what informed
this fix's design.

**Silent-failure trace, pre-fix version, `git show
HEAD:gates/spawn_on_pr.py`:**
```python
    if issue_states is None:
        issue_states, ok = closure_sweep.issue_state_index_all(root)
        if spawn._watchdog_note_gh_failure(root, "spawn-on-pr", not ok):
            print("[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, "
                  "이번 틱 판정 보류 (연속 실패)")
        if not ok:
            issue_states = None
```
Classification: Silently Absorbed — pattern "success flag paired with
absent data, checked with a bare `not ok`". Forward trace: `ok=True` on
truncation → `_watchdog_note_gh_failure(root, "spawn-on-pr", not ok)`
called with `failed=False` → streak resets/stays 0, never warns →
`issue_states` stays `None` (it already was, from the truncated return)
→ `_issue_is_open()` fail-closes every subject → `missing_verification()`
returns `{}` for every subject, forever, with **zero printed output** →
indistinguishable at the console from a healthy quiet tick. Verified
live pre-fix (see Acceptance bullet 1 below): the pre-fix truncated tick
printed nothing, byte-identical to the pre-fix healthy tick's nothing.

**Design decision — contract change, not a narrower fix.** I considered
patching just the caller: `missing_verification()` could special-case
`issue_states is None and ok` as its own branch without touching
`issue_state_index_all()`'s return type at all. That would have fixed
this specific call site with a smaller diff. I rejected it because the
issue quote at the top of this section is evidence against it: this is
the **third** distinct quiet-mode bug in this exact code path in one
night, and each prior fix *did* patch the caller-side check without
touching the producer's return contract — and each time, per that same
quote, the fix closed one gap while leaving the shape that produces the
next gap untouched. A 2-valued `(data, ok)` tuple can express at most 2
states cleanly; forcing a third state through it means one of the two
`ok` branches has to internally carry two different meanings (`ok=True`
already meant both "real data" and "no data because too big to trust"
before this fix, per the trace above), and nothing in the type signature
tells a new caller that `ok=True` doesn't imply `index is not None`. A
caller-side patch fixes the reader of today's ambiguity; it does nothing
about the next caller who writes `if not ok` again next month. Naming
the third state as its own return value makes the ambiguity impossible
to express, not just currently avoided — the next caller has to
explicitly ignore the `ISSUE_INDEX_TRUNCATED` branch to reproduce this
bug, rather than merely omitting a check nobody flagged.

I scoped the contract change to `issue_state_index_all()` only.
derived: `grep -n "_PR_INDEX_SAFETY_CEILING\|return None, True" gates/closure_sweep.py`
```
172:_PR_INDEX_SAFETY_CEILING = 5000
229:            return None, True
```
`_pr_index_all()` (same file, line 229) has the identical `(None, True)`-
for-truncation shape, but it is not named in this issue's Ask or
Acceptance, and the issue's Non-goals are explicit about scoping to this
one function's `ok=True` path. Changing it too would be undiscussed
scope creep on a function this issue never asked about; noted in Open
findings below as a plausible follow-up, not undertaken.

## Upstream basis

Issue #2792 body (verbatim, cited under Why above):
`gates/closure_sweep.py::issue_state_index_all()` lines 259-266
(docstring) / 299-300 (the `if len(data) >= _ISSUE_INDEX_LIMIT: return
None, True` line that is this bug) — same-commit, cited and read
directly from the working tree before editing.

## Acceptance — executed live

### Bullet 1: truncated tick shown next to healthy and gh-failure ticks

acceptance: `missing_verification()` driven `WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD`
times each (streak must cross threshold to print), three separate
`issue_state_index_all()` outcomes, same call site, same board shape —
result:

```
=== HEALTHY tick (status='ok', spawn-eligible={}) ===
(no output)

=== GH-FAILURE tick (status='failed', spawn-eligible={}) ===
[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)

=== TRUNCATED tick (status='truncated', spawn-eligible={}) ===
[spawn-on-pr] 이슈 인덱스 절단(상한 1000건) — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 절단)
```

acceptance: same three-way drive on `origin/main` (separate `git worktree`,
script adapted to the old `(index, ok: bool)` shape) — result:

```
=== HEALTHY tick (index={}, ok=True) ===
(no output)
=== GH-FAILURE tick (index=None, ok=False) ===
[spawn-on-pr] gh 실패 — 이슈 상태 조회 불가, 이번 틱 판정 보류 (연속 실패)
=== TRUNCATED tick (index=None, ok=True) ===
(no output)
```

— the pre-fix truncated tick is byte-identical to the pre-fix healthy
tick (both print nothing). Post-fix, all three states print differently.
This is the exact defect the issue reports, reproduced pre-fix and
resolved post-fix, same call site (`missing_verification()`), same
process (not two separate descriptions).

### Bullet 2: caller population and each one's before/after behavior

derived: `grep -rn "issue_state_index_all" --include=*.py .` — result:
population found, six non-definition call sites across four files
(`gates/spawn_on_pr.py:397,872`, `watchdog.py:1078`, `gates/closure_sweep.py:358,755`,
`spawn.py:2367`), plus the definition site itself and three references
inside `gates/test_spawn_on_pr.py`.

1. `gates/closure_sweep.py::find_violations()` (internal re-fetch when
   `issue_states` not pre-supplied). Before: `reason = "gh-issue-list-failed"
   if not issue_states_ok else "gh-issue-list-truncated"` — already
   correctly distinguished (this branch is only reached when `issue_states
   is None`, which under the old contract could only mean `ok=False`
   real-failure or `ok=True` truncation — never a real empty index, since
   an empty-but-successful board returns `{}` not `None`). After: same
   branch, reading `issue_states_status == ISSUE_INDEX_FAILED` instead of
   `not issue_states_ok` — behavior unchanged, now type-safe instead of
   coincidentally correct.
2. `gates/closure_sweep.py::main()` (CLI `python3 gates/closure_sweep.py`).
   Before and after: `issue_states, _ = issue_state_index_all(root)` —
   discards the second value either way, unaffected.
3. `gates/spawn_on_pr.py::missing_verification()` — the bug site (see
   Bullet 1). Before: truncation silently absorbed, zero streak, zero
   print, forever. After: `spawn-on-pr:truncated` streak accumulates
   independently of `spawn-on-pr`, warns on its own threshold, prints a
   line naming truncation explicitly, never mislabeled as "gh 실패".
   Spawn eligibility (`out`) unaffected in both states (see Bullet 3).
4. `gates/spawn_on_pr.py::backfill_closed()` (opt-in CLI,
   `spawn_on_pr.py backfill-closed`). Before: `if not ok: issue_states =
   None` — a no-op given truncation already returns `index=None`, so
   failed and truncated already collapsed to the same downstream result
   (0 backfill candidates) with no reporting either way — this is a
   human-invoked command, not an automatic tick, so the "looks healthy
   while withholding" failure mode this issue is about does not
   reproduce here. After: same collapse (still both end at 0
   candidates, unchanged spawn/no-spawn result), but now prints
   `[backfill-closed] 이슈 상태 조회 불가 (<status>) — 대상 subject 없음`
   naming which of the two it was, instead of staying silent about the
   cause.
5. `watchdog.py::_board_wide_sweep()` — the sole automatic-tick fetch
   point; feeds `issue_states` into `spawn_on_pr.spawn_missing_for_pr()`,
   `closure_sweep.find_violations()`, and `spawn_on_approve.spawn_phase2()`
   (the last of these never calls `issue_state_index_all()` itself — it
   only consumes the value forwarded from here, same as `find_violations`
   does when given a pre-supplied `issue_states`). Before:
   `rate_limited_this_tick = bool(skips) and not issue_states_ok` — since
   truncation already left `issue_states_ok=True`, truncation correctly
   never triggered backoff (accidentally correct, same shape as finding
   1). The `closure-sweep` "확인 불가" line printed a single generic
   `"(gh 실패)"` label regardless of whether the underlying skips were
   real failures or truncations. After: `rate_limited_this_tick` reads
   `issue_states_status == ISSUE_INDEX_FAILED` explicitly (same resulting
   value, now intentional); the "확인 불가" line now tallies skip reasons
   by name (e.g. `{'gh-issue-list-truncated': 3}` vs
   `{'gh-issue-list-failed': 3}`) instead of one generic label.
6. `spawn.py` role `"closure-sweep"` (CLI `python3 spawn.py closure-sweep`).
   Before and after: `issue_states, _ = closure_sweep.issue_state_index_all(root)`
   — discards the second value either way, unaffected (same as #2).

### Bullet 3: spawn eligibility unchanged — `spawn_missing_for_pr(dry_run=True)` before/after

acceptance: `spawn_missing_for_pr(root, cwd, dry_run=True)` under a
truncated-index outcome, this branch vs. `origin/main` (separate `git
worktree`, old tuple shape) — result:

```
AFTER  (this branch, contract: (None, ISSUE_INDEX_TRUNCATED)): pairs=[]
BEFORE (origin/main,  contract: (None, True)):                  pairs=[]
```

Byte-identical (`pairs=[]` both), confirming the acceptance's "empty
state: byte-identical" requirement — the fix changes what is *reported*,
not what is *spawned*.

## Invariants — executed live

**No return of the retired-noun `role` axis (issue #2798/#2799), in any
form:**
```
$ git diff -- gates/closure_sweep.py gates/spawn_on_pr.py gates/test_spawn_on_pr.py watchdog.py \
    | grep -E '^\+' | grep -iwc "role"
0
```

**No new bug — failing-test set vs. `origin/main`, compared as sets of
names, not counts:**
```
$ python3 -m pytest gates/ test/ -q   # this branch
15 failed, 452 passed, 3 xfailed
$ python3 -m pytest gates/ test/ -q   # origin/main (separate worktree)
15 failed, 448 passed, 3 xfailed
$ diff <(this branch's 15 FAILED names, sorted) <(origin/main's 15 FAILED names, sorted)
IDENTICAL SETS
```
The 452 vs. 448 delta is exactly the 4 new tests added to
`gates/test_spawn_on_pr.py` (`test_truncated_lookup_stays_quiet_below_its_own_streak_threshold`,
`test_truncated_lookup_reports_its_own_state_once_streak_hits_threshold`,
`test_truncated_and_failed_streaks_accumulate_independently`,
`test_truncated_streak_resets_on_recovery_via_production_caller_shape`),
all passing. The 15 failing names are pre-existing, environment-dependent
(git `origin` remote absent in this sandbox — `fatal: 'origin' does not
appear to be a git repository`), and touch none of the four files this
change modifies.

**No overhead increase:**
```
$ git diff -- gates/closure_sweep.py gates/spawn_on_pr.py watchdog.py spawn.py \
    | grep -E '^\+.*subprocess\.run' | wc -l
0
```
No new `gh`/`subprocess` call added anywhere in the diff — the fix only
threads an already-computed value (the status the producer already knew
and previously discarded) through existing call sites, plus one extra
local (disk, not network) read/write of the existing watchdog-noise JSON
state file per tick for the new `"spawn-on-pr:truncated"` streak
(`_watchdog_note_gh_failure()` already did one such read/write per tick
for `"spawn-on-pr"`; this doubles that specific local file I/O, not any
`gh`-billed call).

**Monitor/watch machinery unbroken and not quieter:**
```
$ python3 -m pytest gates/test_spawn_on_pr.py test/test_watchdog_heartbeat_noise.py -q
27 passed
6 passed
```
Every state this fix touches now prints strictly more than before
(truncation went from 0 lines ever to 1 line per streak-threshold,
exactly matching the existing gh-failure convention this codebase
already uses) — never less. The pre-existing `"gh 실패"` streak
behavior, the pre-existing per-PR/per-subject one-shot suppression
tests, and the pre-existing `"closure-sweep"` reset-on-success behavior
are all still covered and passing (see the two suites above), unchanged
in shape.

## What did not work

None — the contract-change approach was decided before writing code (see
Why) and no alternative implementation was attempted and discarded.

## Open findings

`_pr_index_all()` (`gates/closure_sweep.py:229`, cited under Why above)
has the identical `(None, True)`-for-truncation vs. `(None, False)`-for-
failure shape as `issue_state_index_all()` had before this fix — same
latent ambiguity, same class of bug possible in any future caller that
only checks `ok`/`not ok`. Out of scope here (issue #2792's Ask and
Non-goals both name only `issue_state_index_all()`); flagged as a
plausible follow-up issue, not filed.

## Next steps

None — `loop_state: landed`. This record accompanies the phase-2
delivery PR (build-now bypass, `CORE_BUILD_NOW=1`).
