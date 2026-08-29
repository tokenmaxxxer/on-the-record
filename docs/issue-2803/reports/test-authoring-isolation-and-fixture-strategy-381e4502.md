---
issue: 2803
role: test-authoring-isolation-and-fixture-strategy-381e4502
author: test-authoring-isolation-and-fixture-strategy-381e4502
skills: test-authoring-isolation-and-fixture-strategy (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: test/test_spawn_attempt_staleness.py
    sha: same-commit
---

# issue-2803 — test-authoring-isolation-and-fixture-strategy-381e4502 record

## What was done

Renamed the four occurrences of the retired noun `role` sitting in the
skill slot of `test/test_spawn_attempt_staleness.py`'s spawn-attempt
fixtures — same shape as #2798/PR #2799, but pre-dating PR #2794 so the
delta check never saw them:

- `test_still_blocked_halt_keeps_reporting_at_full_volume` (lines 394-395):
  `"2999:role:1:1"` / `"role"` → `"2999:stillblockedfault:1:1"` /
  `"stillblockedfault"` — names the fixture's own purpose (a cwd-invalid
  halt whose blocking condition never clears, the non-goal guard for
  "must never be dropped or quieted").
- `test_report_line_carries_the_original_attempt_timestamp` (lines
  408-409): `"3000:role:1:1"` / `"role"` → `"3000:tscarryfault:1:1"` /
  `"tscarryfault"` — names the fixture's purpose (proving the report line
  carries the original attempt's timestamp, not the re-check time).

```
--- a/test/test_spawn_attempt_staleness.py
+++ b/test/test_spawn_attempt_staleness.py
@@ -391,8 +391,8 @@ class SpawnAttemptSweepReplayFixTest(unittest.TestCase):
         reason = (f"-C 가 존재하지 않는 디렉터리다: {missing}\n"
                   f"  cwd 는 레포 루트를 가리켜야 한다 — 경로를 다시 확인해라.")
         attempt_ts = time.time() - 60
-        self._write_attempt("2999:role:1:1", 2999, "role", str(missing),
-                             reason, attempt_ts)
+        self._write_attempt("2999:stillblockedfault:1:1", 2999, "stillblockedfault",
+                             str(missing), reason, attempt_ts)
```

canonical: `git diff -- test/test_spawn_attempt_staleness.py` — full diff
shown above and its second hunk (lines 405-409, the `tscarryfault` site),
executed-live.

Neither new name is a same-meaning substitute for the retired noun
(`agent`/`actor`/`worker`) — each names what its own test exercises, per
the issue's must-not and matching PR #2799's convention.

## Why

The issue's Ask names these as the same shape #2798 removed from
`test/test_bootstrap_signal_guard.py`, differing only in provenance: these
four occurrences pre-date PR #2794, so PR #2799's delta-based invariant
count (1275→1263) was blind to them by construction — a delta check can
only see what changed, never what was already sitting in the baseline it
diffs against. Renaming here closes that specific blind spot for this one
located instance without generalizing the fix (the issue's own Non-goals
route the wider `#2600` identifier slice elsewhere).

The sweep (third acceptance criterion) is the only expensive part of this
issue — a delta check reproduces its own blindness if it only re-checks
the file already named, so the population searched had to include every
test file in both repos, not just this one.

### Sweep: both repos, test files, for the shape

Population and commands, executed-live:

```
grep -rnE '"[0-9]+:role:' test/                     # on-the-record: attempt_id-like literal
grep -rnE '"role"|'"'"'role'"'"''  test/            # on-the-record: quoted role as a value
```
derived: both return zero matches outside the two lines fixed above (the
pre-fix run showed exactly `test/test_spawn_attempt_staleness.py:394` and
`:408` and nothing else, across all 40 files `git ls-files test/` lists —
`git ls-files test/ | wc -l` → `40`).

```
grep -rnE '"[0-9]+:role:' <tokenmaxxxer-core checkout>/{core,test dirs}
grep -rn '"role"' <tokenmaxxxer-core checkout>/core/hooks/tests
grep -rn "'role'" <tokenmaxxxer-core checkout>/core/hooks/tests
grep -rln "attempt_id" <tokenmaxxxer-core checkout>            # does this shape's carrier exist there at all?
grep -rnE '[,(]\s*"role"\s*[,)]' <tokenmaxxxer-core checkout>  # positional skill-slot argument
```
derived: all five zero matches. The `attempt_id` sweep is zero because
tokenmaxxxer-core has no `spawn_attempt`-style fixture carrier at all —
its 49 test files (`git ls-files | grep -iE '(^|/)test'` → `49`, checkout
at commit `e7f1c4e`, a local worktree of `tokenmaxxxer-core-issue-233-
adversarial-review-13d75b7e` already present under
`$MUSTER_WORKSPACE_ROOT`) are shell (`core/hooks/tests/*.sh`) and one
Python gate test (`core/hooks/test_board_gate.py`), none of which write a
colon-delimited `issue:skill:seq:seq` attempt id or a positional skill
argument in that shape.

Files searched, named as required by the empty-state clause: all 40 files
under `test/` in `tokenmaxxxer/on-the-record` (`git ls-files test/`), and
all 49 files matching `test` under the `tokenmaxxxer-core` checkout
(`git ls-files | grep -iE '(^|/)test'`), specifically `core/hooks/tests/*`
(42 files, mostly `.sh`) and `core/hooks/test_board_gate.py`.

**Report: zero occurrences of the shape found beyond the two lines fixed
in this file, in either repo.**

## Open findings

1. **Acceptance check 1's literal grep does not return zero — six
   pre-existing, out-of-scope matches remain.** The issue's stated check
   is `grep -inE '\brole\b' test/test_spawn_attempt_staleness.py` with
   empty state "exit 1, zero matches". After this fix:
   ```
   214:    `secrets.token_hex(4)`) that `spawn.py:1990-1991` appends to every role
   291:        """Over-broadening guard: same role family, different issue — must
   303:        """Over-broadening guard: same issue, different role family — an
   423:    (issue, role-family) must still resolve it."""
   479:        # A later attempt for the same (issue, role-family) — different
   507:        with no later successful attempt for that issue+role-family. Must
   ```
   derived: `grep -inE '\brole\b' test/test_spawn_attempt_staleness.py` —
   result: 6 lines (shown above), exit 0 (not 1).

   All six are pre-existing prose (docstrings/comments in
   `SkillFamilyTest`, `AttemptSupersededTest`, and
   `SpawnAttemptSweepSupersessionTest` — different classes from the two
   tests the issue names), using "role family" as the informal English
   name for what `_skill_family()` computes, not a skill-slot fixture
   literal. They are not among the "four places across two tests (lines
   ~394 and ~408)" the Ask names, and the sweep above found no
   attempt_id-like or positional-argument occurrence of the retired noun
   left in this file — the shape the third acceptance criterion targets
   is fully gone. Renaming this prose too would exceed the Ask's stated
   scope and looks like exactly the wider `#2600` identifier slice the
   issue's own Non-goals route elsewhere ("this is one measured, located
   instance, filed so it is not folded into an open question"). Left for
   separate judgment rather than silently widened into this diff, per the
   task's own instruction to fix what the issue names and report the rest.
   unverifiable: whether the issue author intended the literal grep result
   to be read as "zero after fixing only the four named places" or "zero
   over the whole file" — the Ask section and the acceptance check's empty
   state disagree on this point, and there is no comment thread to
   resolve it.

## Next steps

None — `loop_state: landed`. The open finding above is a scope-boundary
question for a human to judge, not further work this session should take.

## What did not work

None. Both fixture renames were mechanical (no functional coupling to the
strings) and inert on the first attempt.

## Verification (four standing invariants)

1. **No return of the retired role axis in any form, including a reshaped
   one.** The two new names (`stillblockedfault`, `tscarryfault`) contain
   no substring of `role` and are not same-meaning substitutes for it.
   derived: `grep -inE '\brole\b' test/test_spawn_attempt_staleness.py |
   grep -E '2999|3000|stillblockedfault|tscarryfault'` — result: empty
   (no match — confirms the renamed sites carry no retired-noun residue).

2. **No new bug — failing-test set vs `origin/main`, as SETS OF NAMES.**
   ```
   $ python3 -m pytest test/ -q          # this branch, working tree
   15 failed, 425 passed, 3 xfailed in 31.86s
   $ python3 -m pytest test/ -q          # origin/main, separate worktree
   15 failed, 425 passed, 3 xfailed in 31.83s
   $ diff <(sorted FAILED test names, this branch) <(sorted FAILED test names, origin/main)
   (empty)
   ```
   derived: `diff /tmp/failed_main.txt /tmp/failed_after.txt` — result:
   empty, exit 0. Both sides list the same 15 failing test names
   (executed-live via `git worktree add /tmp/otr-main-check origin/main`,
   removed after comparison) — none of the 15 pre-existing failures touch
   `test_spawn_attempt_staleness.py`, and no new failure was introduced.

3. **No overhead increase.** `real 0m32.165s` (this branch) vs
   `real 0m32.146s` (origin/main) for the identical `python3 -m pytest
   test/ -q` full-suite invocation — derived: both timed runs shown above,
   difference (19ms) is noise, not a regression.

4. **Monitor and watch machinery unbroken and not quieter.**
   ```
   $ python3 -m pytest test/test_spawn_attempt_staleness.py -k \
       "SpawnAttemptSweep or PruneSpawnAttempts" -v
   7 passed in 0.87s
   $ python3 -m pytest test/test_watchdog_heartbeat_noise.py -v
   6 passed in 1.22s
   ```
   derived: both commands above, executed-live, all PASSED. The two
   renamed fixtures' own tests
   (`test_still_blocked_halt_keeps_reporting_at_full_volume`,
   `test_report_line_carries_the_original_attempt_timestamp`) assert the
   sweep still prints `"spawn halted pre-workspace"` / `"attempted at"` /
   the original timestamp — i.e. the rename did not quiet the sweep's
   reporting, and `test_watchdog_heartbeat_noise.py` (a separate,
   untouched file exercising the heartbeat suppression machinery) is
   unaffected.

5. **Rename is inert — test-name SET comparison, before vs after.**
   derived: `diff <(sorted test names, before) <(sorted test names,
   after)` — result: empty, exit 0. Both runs show
   `41 passed in 0.9Xs`, identical 41-name set
   (`git stash push -- test/test_spawn_attempt_staleness.py` /
   `python3 -m pytest test/test_spawn_attempt_staleness.py -v` /
   `git stash pop`, executed-live).

## Skill verdicts

skill-verdict: test-authoring-isolation-and-fixture-strategy — not-applicable: this task is a pure vocabulary rename of two existing fixture identifier strings (no fixture scope, isolation, or test-double decision was made; the must-not explicitly forbids changing what the tests assert).
other mounted skills: not triggered (work-in-english — task prompt and all repo-bound artifacts were already in English; guidance-only, enforcement is by core hooks per the mount note).
