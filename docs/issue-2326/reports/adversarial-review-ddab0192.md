---
issue: 2326
role: adversarial-review-ddab0192
author: adversarial-review-ddab0192
skills: adversarial-review (skill-repository(c05de12)), work-in-english (skill-repository(c05de12)), model-routing (skill-repository(c05de12))
verifies_subject: true
code_under_review: PR #2860 (merged, sha 060f1f10655d41f2072865c1e2ce7a093fed2412), and its own upstream basis docs/issue-2326/reports/diagnose-first-56b99f15.md
type: verification
breaking: false
verdict: partial — the path-prefix rejection is confirmed correct; the import-graph budget rejection is NOT robust and the no-ship conclusion built on it is premature; the rework_fraction.py instrument fix is confirmed correctly implemented; the specific historical "4.5%" figure could not be re-verified because its source corpus no longer exists
loop_state: landed
upstream:
  - path: docs/issue-2326/reports/diagnose-first-56b99f15.md
    sha: 060f1f10655d41f2072865c1e2ce7a093fed2412
  - path: docs/issue-2326/reports/adversarial-review-941d677c.md
    sha: b33943b9659ac46e6e8c0cb66a98e0b40db19742
  - path: scripts/rework_fraction.py
    sha: 060f1f10655d41f2072865c1e2ce7a093fed2412
---

# issue-2326 — adversarial-review-ddab0192 record

skill-verdict: adversarial-review — applied: invoked; this session's own structural position (independently spawned verifier, no shared context with PR #2860's builder) already matches the skill's two-party protocol per its own text
canonical: this session's own `Skill` tool invocation of adversarial-review, this turn
; re-derived every claim in PR #2860 from raw code/timing/corpus evidence rather than restating its record, specifically targeting the no-ship conclusion for a counter-example
skill-verdict: work-in-english — applied: invoked; this record and all derived commands are in English, final chat summary in Korean
canonical: this session's own `Skill` tool invocation of work-in-english, this turn
skill-verdict: model-routing — not-applicable: single-session investigative verification with sequential, mutually-dependent steps (each timing result determined the next question); no independent unit large enough to route to a separate reasoner or executor beyond the one mechanical-execution batch delegated to a freelunch worker

## What was done

Independently re-derived PR #2860's two load-bearing measurements and its instrument fix, using a
background freelunch worker for the mechanical command batch (greps, timings, reruns) and doing the
judgment/bisection work in this session.

**1. Path-prefix rejection — CONFIRMED correct, not a mistake.**
canonical: `grep -n "^import\|^from" test/test_watchdog_heartbeat_noise.py` (this session) →
`closure_sweep`, `state_paths`, `spawn`, `spawn_on_pr` — no `watchdog` import anywhere in the file
. `test/test_unrecovered_commit_count.py` does import `watchdog` and calls `watchdog.diagnose_health`
canonical: `grep -n "watchdog" test/test_unrecovered_commit_count.py` (this session) → `31:import watchdog`, plus three `watchdog.diagnose_health(...)` call sites at lines 118, 131, 164
. A path-prefix glob for stem `watchdog` matches only `test_watchdog_heartbeat_noise.py`
derived: `python3 -c "import os; print([f for f in os.listdir('test') if f.startswith('test_watchdog')])"` → `['test_watchdog_heartbeat_noise.py']`
. Both of PR #2860's factual claims about this pair of files check out exactly as stated. The rejection
of path-prefix as "worse than the original miss" stands.

**2. Import-graph budget rejection — the 31.4s timing is real and reproduced, but the conclusion
drawn from it is NOT robust, and the no-ship verdict is premature on this pillar.**

Reproduced the exact union PR #2860 timed: restricting `find_impacted()` to `test/`+`tests/` matches
the record's own "35 spawn matches" and "36-file union" figures
canonical: `docs/issue-2326/reports/diagnose-first-56b99f15.md` lines 71-75 (read directly this session): "same script against stem `spawn` → 35 matches"; "the union of what import-graph selection returns ... (36 unique files after de-duplication)"
. A first pass scanning `test/`+`tests/`+`gates/` together (matching that record's separate per-stem
citation at line 67: "scanned over test/, tests/, gates/") instead produced 47 files and a spawn count
of 46
derived: freelunch worker command 3 this session, `find_impacted()` with `dirs=('test','tests','gates')` → "spawn: 46 ... union: 47"
— the record mixes two scan scopes across its per-stem citations and its headline count. Restricting
to `test/`+`tests/` only, re-implemented independently this session, reconciles it exactly:
```
board: 5 files, spawn: 35 files (of 50 total under test/+tests/), watchdog: 1 file, union: 36 files
```
derived: independent `find_impacted()` re-implementation this session, `dirs=('test','tests')`; `git ls-files test/ tests/ | wc -l` → 50 (one fewer than the record's "51 total" citation — ordinary corpus drift)
. Timed three independent runs of that exact 36-file union:
```
31.37s / 31.68s real   31.24s / 31.54s real   31.18s / 31.48s real
```
derived: `time python3 -m pytest <36-file union> -q` × 3, this session — matches PR #2860's cited 31.4-31.7s within 0.3s each run
. The timing claim is solid.

But the record's "What did not work" section only considered one alternative — a per-module cap
"prioritized by directory proximity" — and rejected it because the three files that actually failed in
the traced episode (`test_convention_equivalence.py`, `test_local_dependency_env.py`,
`test_spawn_cross_family_skill_selection.py`) sort at positions 11, 14, and 24 of the 35 spawn matches
derived: alphabetical enumeration of the 35 spawn-importing files, this session, with the three real-failing-test filenames marked by position: positions 11, 14, 24 out of 35
, so a naming/proximity-ordered cap covering fewer than 24 of the 35 files would miss at least one of
them. I confirmed this independently — a proximity-ordered cap does not solve the budget problem,
exactly as the record argued.

What the record never asked: does file *count* actually drive the 31s, or does one specific file?
Bisection answers this directly. A 5-file run (board+watchdog only, no spawn matches) takes 0.93s. A
10-file run — still far short of the 24-36 needed for accuracy — jumps straight to 31.0s
derived: `time python3 -m pytest <first 5 board+watchdog files> -q` → "28 passed in 1.27s", real 1.56s; `time python3 -m pytest <first 10 files of the union, alphabetical> -q` → "76 passed in 31.00s", real 31.29s
. Bisecting the 10-file set to individual files: `test/test_bootstrap_signal_guard.py` alone takes
30.5-30.9s, standalone, with or without `pytest-xdist` parallelism
derived: `time python3 -m pytest test/test_bootstrap_signal_guard.py -q` → "11 passed in 30.87s", real 31.16s; re-run with `-o addopts=""` (xdist disabled) → "11 passed in 30.51s", real 30.79s — not a parallelism artifact
. It contains genuine `time.sleep(30)` calls testing a real signal race
derived: `grep -n "sleep" test/test_bootstrap_signal_guard.py` → three `time.sleep(30)` call sites; module docstring (lines 1-17, read directly this session): "a real signal arrives long before this elapses" — the fast path is expected but a specific mocked branch deliberately waits out the full 30s
. It legitimately `import spawn`
derived: `grep -n "^import\|^from" test/test_bootstrap_signal_guard.py` → `31:import spawn`, `32:import roster`
, so it is not a false-positive match — but it was not one of the three files that actually failed in
the traced episode (per `docs/issue-2326/reports/adversarial-review-941d677c.md` line 47's trajectory
dump, quoted in PR #2860's own upstream record at lines 68-70).

Excluding just this one file from the 36-file union drops the runtime to 1.47-1.77s (comfortably inside
the 15s budget) while still running and correctly reporting all three real target tests:
```
25 files (union minus test_bootstrap_signal_guard.py): "11 failed, 240 passed in 1.47s", real 1.77s
— includes test_convention_equivalence.py, test_local_dependency_env.py,
  test_spawn_cross_family_skill_selection.py, all present and failing as expected
```
derived: `time python3 -m pytest <36-file union minus test_bootstrap_signal_guard.py> -q`, this session
. None of the three real target files are themselves slow — each runs standalone in 0.8-1.1s
derived: individual `pytest <file> -q --durations=3` for each of the three, this session — 0.84s, 0.83s, 1.14s
, so a per-file timeout/skip mechanism would never accidentally exclude a needed test in this case.

**This is a materially different alternative from the one the record tested and correctly rejected.**
A proximity/naming-ordered cap fails, as the record found — verified independently above. A per-file
time-based cap or skip-list (a standard, well-precedented technique — not "re-running history" to rank
importance, just observing that one specific matched file is an outlier and excluding or backgrounding
it) resolves the exact budget failure PR #2860 measured, on the exact case it measured it on. Per the
task's own framing: if a selection refinement lands inside budget, the no-ship conclusion is premature
— and this one does. The record's no-ship verdict is not supportable as stated on its cost pillar; a
corrected framing would be "import-graph plus a per-file timeout is unexplored and plausibly viable,"
not "import-graph blows the budget by 2x."

**3. Instrument fix (`scripts/rework_fraction.py`) — CONFIRMED correctly implemented.**
Read the boundary logic directly (lines 246-281): an edit following a test failure with a later
confirming pass is counted in `rework_episodes` as before; an edit following a failure with **no**
later confirming pass before session end is now routed to a separate `unresolved_reentry` counter and
excluded from `rework_episodes`/`rework_turn_cost_median`/`mean` entirely — matching the fix as
described in PR #2860's own record.
canonical: `scripts/rework_fraction.py:246-281`, read directly in full this session
. Re-ran against the live corpus (34 session logs today — a different, later set than the 31 files PR
#2860 measured against; session logs rotate continuously, as PR #2860's own upstream record already
warns):
```
total rework episodes (cost known): 3   rework_fraction_of_edit_turns: 0.7%
total unresolved re-entry (excluded from turn-cost median/mean): 49
rework turn-cost across corpus: median=5.0 mean=4.67 (n=3)
```
derived: `python3 scripts/rework_fraction.py --batch "$MUSTER_WORKSPACE_ROOT/*.session.*.log"` (this session, 34 files) — full output in this session's transcript
. No 3-digit turn-cost appears anywhere in this output — consistent with the fix. The literal string
"98 turns"/"98 in the worst" appears nowhere in current script output; its only remaining occurrences
in the repo are inside the two prior records' own prose discussing the fixed defect, not live output
derived: `grep -rn "98 turns\|98 in the worst" docs/ scripts/` (this session) → 2 hits, both inside diagnose-first-56b99f15.md and adversarial-review-941d677c.md prose, none in script output
.

**Could not verify:** whether the fix changes the specific historical "4.5%" figure the no-ship
decision cites. That figure was computed by PR #2859 against a manually-filtered, ephemeral 10-session
`/tmp/otr_only/*.session.*.log` symlink directory built inside that now-ended session — it does not
exist on disk, and today's `$MUSTER_WORKSPACE_ROOT` corpus (34 files) shares no filenames with the
corpus that produced 4.5% (e.g. `on-the-record-issue-2324-independent-verification-1`, named in that
computation, is not present)
derived: `find "$MUSTER_WORKSPACE_ROOT" -iname "*on-the-record-issue-2324-independent-verification*"` → no match, this session; `ls "$MUSTER_WORKSPACE_ROOT"/*.session.*.log | wc -l` → 34, none matching PR #2859's cited filenames
. I read `rework_fraction.py`'s fraction formula directly: `rework_fraction_of_edit_turns = total_rework
/ total_edit_calls`, where `total_rework` sums only *resolved* episodes both before and after the fix
canonical: `scripts/rework_fraction.py` lines 361, 382-383, read directly this session
— the fix moves *unresolved* episodes out of that sum entirely (previously they were folded in with an
inflated cost, not excluded). So the fix would only change 4.5% if any of the 6 episodes underlying it
were themselves unresolved (`n_pass=0`); PR #2859's own finding 5 describes all 6 without flagging any
as unresolved, and its finding 4's `n_pass=0` examples were both `tokenmaxxxer-core-*` sessions already
outside the `on-the-record-only` population used for 4.5%
canonical: `docs/issue-2326/reports/adversarial-review-941d677c.md` findings 4 and 5, read directly this session
— suggestive that 4.5% is unaffected, but not directly re-run and confirmed. I report this as
unverified rather than asserting it either way.

**Standing invariants (re-derived, not restated):**
- No role-axis return: `grep -n "role" scripts/rework_fraction.py` → no matches
  derived: this session, and independently by the freelunch worker
- No new bug — failing-test set as sets of names: clean `git worktree add` of `origin/main` vs. this
  branch, `python3 -m pytest test/ tests/ -q` in each, `FAILED` lines sorted and diffed
  derived: both worktrees produced "15 failed, 470 passed, 3 xfailed" with the identical 15-name
  `FAILED` set; `diff` of the two sorted name lists showed zero name differences (only the timing
  figure and worktree path differed, neither of which is a `FAILED` line)
  . Confirmed as sets of names.
- No overhead increase: `git diff --stat origin/main -- on-the-record/hooks/hooks.json` → empty; no
  hook file (`lint-test-on-edit*`) present anywhere in this branch's tree
  derived: `git diff --stat origin/main -- on-the-record/hooks/hooks.json` and `find . -iname "lint-test-on-edit*"`, both empty, this session
  . Confirmed — nothing shipped, so no overhead exists to increase.
- Monitor/watch unbroken and not quieter: `python3 -m pytest test/ tests/ -q -k "monitor or watch"` →
  15 passed; `python3 -m pytest test/test_watchdog_heartbeat_noise.py -q` → 6 passed
  derived: both commands, this session — same counts PR #2860's own record cites
  . Confirmed unbroken.

## Why

The task specifically asked me to challenge a no-ship conclusion because it is structurally less
likely to be challenged than a ship conclusion. Both of PR #2860's two load-bearing measurements
checked out numerically when re-derived directly — the path-prefix counterexample and the 31.4s
import-graph timing are both real and reproducible
canonical: this session's own re-derivations quoted in the "What was done" section above (path-prefix imports, three independent 36-file union timings)
, so a shallower verification would have confirmed the record as stated. The task explicitly told me
to ask the question the record's own text did not: whether selection has to be the union. Bisecting
that 31s figure rather than accepting it as a property of "35 files is too many" found that it is
actually the property of one specific matched file's deliberate 30-second sleep, unrelated to the
traced episode's real failures
canonical: bisection sequence in "What was done" above (5-file → 10-file → single-file isolation of test_bootstrap_signal_guard.py), all executed and quoted this session
. That distinction matters because it changes what kind of fix would be needed — not a smarter
*which-files-to-run* ranking (which the record correctly showed doesn't work, since the real target
files have no rank signal), but a *how-long-is-this-file-taking* cap, which is a different and
unexplored axis entirely. Per the task's own explicit criterion, finding a refinement that lands
inside budget makes the no-ship verdict premature, so I report it as such rather than confirming the
record's conclusion.

The instrument-fix portion of PR #2860 is not in question on its own logic or behavior — I read the
code and re-ran it, and it does exactly what it claims
canonical: `scripts/rework_fraction.py:246-281` read directly, and this session's own live rerun output quoted in the "What was done" section above
. The one piece I could not close is whether the fix changes the specific "4.5%" figure, purely
because that figure's source corpus is gone; I report that as an open, unverifiable point rather than
stretching indirect evidence into a confirmation.

## What did not work

The freelunch worker's first `find_impacted()` pass scanned `test/`, `tests/`, and `gates/` together,
matching one of two scanning-scope citations inside PR #2860's own upstream record
canonical: `docs/issue-2326/reports/diagnose-first-56b99f15.md` line 67, read directly this session: "scanned over test/, tests/, gates/"
, which produced a 47-file union and a 46-file spawn count
derived: freelunch worker command 3 output this session — "spawn: 46 ... union: 47"
— inconsistent with the record's own headline "36 unique files"/"35 of 51" figures (same citation as
above, lines 71-73). Re-ran the scan restricted to `test/`+`tests/` only, directly in this session, to
reconcile it, which matched the record's headline numbers exactly (35 spawn matches, 36-file union)
derived: independent `find_impacted()` re-implementation, `dirs=('test','tests')`, this session — "spawn 35 ... union(test/tests only) 36"
. Not a defect in this review — a note that PR #2860's own record mixes two different scan scopes
across its per-stem citations and its headline count; the headline figures are the ones the timing and
ship decision actually rest on, and those reproduce cleanly once the scope is held consistent.

## Upstream basis

- `docs/issue-2326/reports/diagnose-first-56b99f15.md` (sha `060f1f10655d41f2072865c1e2ce7a093fed2412`,
  merged) — the record under review
  canonical: read in full this session; every number and claim re-derived above is quoted from it directly (lines 44-88, 90-132)
  ; every number and claim re-derived above is checked against it rather than restated.
- `docs/issue-2326/reports/adversarial-review-941d677c.md` (sha `b33943b9659ac46e6e8c0cb66a98e0b40db19742`,
  merged) — PR #2859's prior verification
  canonical: read in full this session; used to trace the origin of the "4.5%" figure (finding 5) and confirm it was never built into `rework_fraction.py` itself
  . `grep -n -B2 -A10 "on-the-record\|4\.5" scripts/rework_fraction.py` → no matches, this session — it
  was an ad hoc `--batch` glob against a manually-filtered `/tmp` symlink directory in that prior
  session, not script logic.
- `scripts/rework_fraction.py` (sha `060f1f10655d41f2072865c1e2ce7a093fed2412`) — read in full (480
  lines) and re-run against the live corpus this session.
- Live session-log corpus at `$MUSTER_WORKSPACE_ROOT/*.session.*.log` (34 files at measurement time,
  a different set than either prior record's corpus — re-queried live this session, not reused).
- This repo's working tree, `test/`, `tests/`, `gates/` — read and executed directly this session for
  every import-graph/timing/bisection claim above.

## Open findings

1. **The no-ship verdict's cost pillar is not supportable as stated.** Import-graph selection, with a
   per-file time cap or a small known-slow-file exclusion list instead of a count/proximity cap, lands
   at 1.47-1.77s for the exact traced-episode union PR #2860 measured at 31.4-31.7s
   canonical: this session's own timing re-derivations, quoted in full in "What was done" above
   — an 8-20x margin inside the 15s budget — while still selecting and correctly reporting all three
   real failing tests. Resolution path: none attempted here (verification only) — a follow-up would
   need to actually build and test a per-file-timeout variant of the hook (e.g. `pytest --timeout=Ns`
   per matched file, or a small maintained skip-list) against a wider sample of edited files than the
   one traced episode, since this session confirmed the mechanism resolves the one measured case but
   did not stress-test it more broadly.
2. Whether the `rework_fraction.py` fix changes the specific historical "4.5%" figure the no-ship
   decision cites is unverified — the source 10-session corpus for that figure no longer exists on
   disk
   canonical: this session's own corpus check, quoted in "What was done" above ("Could not verify" paragraph)
   . Indirect evidence (the fix only affects unresolved episodes; PR #2859's own finding 5 does not
   flag any of the 6 constituent episodes as unresolved) suggests it is unaffected, but this was not
   directly re-run. Resolution path: none available — the corpus is gone; a future measurement would
   need to accept a freshly-drawn corpus rather than trying to reproduce this exact number.

## Next steps

loop_state: landed.
acceptance: `time python3 -m pytest <36-file union minus test_bootstrap_signal_guard.py> -q` — result: 1.47-1.77s, all three real target tests present and reporting correctly (open finding 1's evidence)
acceptance: `python3 scripts/rework_fraction.py --batch "$MUSTER_WORKSPACE_ROOT/*.session.*.log"` — result: median=5.0 mean=4.67 (n=3), no 3-digit outlier, unresolved re-entries tracked separately (instrument-fix evidence)
This record's scope was to independently re-derive PR #2860's two load-bearing measurements and its
instrument fix, rather than restate them, and specifically to try to break the no-ship conclusion per
the task's framing — see the "What was done" and "Open findings" sections above for the full evidence
chain. It recommends surfacing open finding 1 to the issue owner as a reason to reopen the ship/no-ship
question specifically on the per-file-timeout axis, rather than treating PR #2860's no-ship call as
final. No further action by this role.
