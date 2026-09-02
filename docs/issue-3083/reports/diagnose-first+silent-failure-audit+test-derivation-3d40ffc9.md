---
issue: 3083
role: diagnose-first+silent-failure-audit+test-derivation-3d40ffc9
author: diagnose-first+silent-failure-audit+test-derivation-3d40ffc9
skills: diagnose-first (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: tests/test_spawn_gate_wiring.py
    sha: same-commit
  - path: tests/test_respawn_deliverable_gate.py
    sha: same-commit
  - path: lifecycle.py
    sha: 573e7382282be24439c223c1603be648dd0e158f
---

# issue-3083 — diagnose-first+silent-failure-audit+test-derivation-3d40ffc9 record

## What was done

Fixed both clusters that made `main` red at commit 573e7382.

canonical: `python3 -m pytest tests/ -q` output at commit 573e7382 — result: `5 failed, 182 passed`

**Cluster A** (`tests/test_spawn_gate_wiring.py`, commit e5978d52): extracted
the additive guard into a standalone function
`_assert_post_tool_use_additive(before_commands, after_commands)` and
replaced `self.assertGreater(len(after_commands), len(before_commands))`
with a call to it. The correct half of the old assertion
(`missing = before_commands - after_commands; assertEqual(missing,
set())`) now lives inside that shared function, logic unchanged. Added
`gates/probe_hooks_additive_survives_merge.py` (commit e5978d52), which
imports the same function from `tests/test_spawn_gate_wiring.py` and
exercises it against two synthetic states: `before == after`
(post-merge) must pass, and a removal must fail.

**Cluster B** (`tests/test_respawn_deliverable_gate.py`, commit
e5978d52): diagnosed before repairing, per the issue's instruction.
Added a `_confirm_crash(state, entry)` helper to
`AutoRespawnConsultsDeliverableGateTest` that warms a shared `state`
dict for `RESPAWN_CONSECUTIVE_CONFIRMATIONS - 1` calls to
`spawn._auto_respawn_check`, then updated all four failing tests to
call it before the assertion-bearing final call, passing the same
`state` dict through.

## Why

**Cluster A** — `tests/test_spawn_gate_wiring.py` (pre-fix) read `before`
from `origin/main`/`HEAD` and `after` from the working tree, then
required `len(after) > len(before)`. That holds only while the change is
unmerged; once merged, `origin/main` contains the same addition and
`before == after`, so `assertGreater` fails on every future merge of
this file.

derived: `python3 -c "before={'a','b'}; after=set(before); missing=before-after; assert missing==set(); assert len(after)>len(before)"` — result: `AssertionError` (raised at the `assertGreater`-equivalent line, reproducing the exact bug: the old guard rejects the legitimate post-merge identical state)

The `missing = before - after` check directly above it is the genuine,
repo-state-independent additive guard (nothing that existed before may
disappear) and needed no change — must-not per the issue forbade
deleting the test or loosening to `assertGreaterEqual`, so I extracted
the correct half into its own function (`_assert_post_tool_use_additive`)
rather than touching its logic, and built the new probe against that
same function so a future regression back to a repo-state-dependent
check would fail both the test (whenever `before == after`, i.e. right
after any merge) and the probe (its identical-state simulation).

**Cluster B** — diagnosed before repairing, per the issue's explicit
instruction not to default to "stale test" because it is cheaper.

canonical: `lifecycle.py:167-178` (RESPAWN_CONSECUTIVE_CONFIRMATIONS constant + comment) at commit 573e7382:
```
RESPAWN_CONSECUTIVE_CONFIRMATIONS = 2
```
canonical: `lifecycle.py:529-550` (`_auto_respawn_check`'s debounce block) at commit 573e7382:
```
    crash_confirms = confirm_prior.get("crash_confirms", 0) + 1
    if crash_confirms < _sp.RESPAWN_CONSECUTIVE_CONFIRMATIONS:
        state[key] = {**confirm_prior, "crash_confirms": crash_confirms}
        _sp._respawn_state_save(state)
        print(f"[watchdog] {key}: crashed 판정 {crash_confirms}/"
              f"{_sp.RESPAWN_CONSECUTIVE_CONFIRMATIONS}회 연속 확인 대기 중 — "
              "아직 재스폰하지 않음", file=sys.stderr)
        return
```

Issue #2969 added this debounce specifically because a single `crashed`
verdict snapshot once caused two live sessions to be killed by mistake
(documented in the same comment block). `_auto_respawn_check` now
returns before ever reaching the deliverable gate or `_respawn_or_cap()`
until `crash_confirms` reaches the threshold.
`tests/test_respawn_deliverable_gate.py`'s four failing tests each
called `_auto_respawn_check` exactly once with a fresh `{}` state, so
they never crossed the threshold and never reached the issue #2981 gate
(`_subject_has_deliverable`) they were written to exercise.

canonical: `test/test_reconcile_crash_verdict_race.py:124-137` at commit 573e7382 (`test_auto_respawn_check_still_respawns_genuine_crash`) — already PASSING on the unmodified base commit:
```
    def test_auto_respawn_check_still_respawns_genuine_crash(self):
        entry = self._entry(wrapper_pid=DEAD_PID)
        state = {}
        with mock.patch.object(spawn, "_respawn_or_cap") as respawn_or_cap:
            for _ in range(spawn.RESPAWN_CONSECUTIVE_CONFIRMATIONS - 1):
                spawn._auto_respawn_check("issue-2874/demo", entry, state)
            respawn_or_cap.assert_not_called()
            spawn._auto_respawn_check("issue-2874/demo", entry, state)
        respawn_or_cap.assert_called_once()
```

This sibling test hits the same production entry point
(`spawn._auto_respawn_check`), the same dead-pid crash fixture shape, and
already warms up the identical shared `state` dict before asserting
`_respawn_or_cap` was reached — and it was passing while
`tests/test_respawn_deliverable_gate.py` failed. That divergence, plus
the two canonical `lifecycle.py` citations above, is the evidence the
respawn path itself is intact: **the four failures were a stale-test
gap (single-call tests never crossing the intentional #2969 threshold),
not a live defect.** I applied the same warm-up pattern rather than
touching any assertion, per the issue's must-not clause. Two of the four
fixed tests assert the skip is reported and never silent (`assertIn` on
stderr, and the ledger write) — that reporting code path itself was
never modified; it simply was not reached in the pre-fix single-call
tests.

## What did not work

None.

## Upstream basis

This issue's own body (quoted acceptance and must-not clauses, read via
`gh issue view 3083`) and `lifecycle.py`/`test/test_reconcile_crash_verdict_race.py`
at commit 573e7382 (cited above) are the concrete inputs. This is the
issue's first and only phase-2 delivery (build-now bypass,
`CORE_BUILD_NOW=1`); no prior record existed for this issue.

## Silent-failure audit (silent-failure-audit skill)

Audited the two `try/except AssertionError` sites in
`gates/probe_hooks_additive_survives_merge.py` (commit e5978d52):

canonical: `gates/probe_hooks_additive_survives_merge.py` at commit e5978d52:
```
    try:
        wiring._assert_post_tool_use_additive(before, after_with_removal)
    except AssertionError:
        pass
    else:
        _fail("guard failed to detect a removed PostToolUse command "
              "(the regression that motivated this file, PR #2872)")
```

Site 1 (`except AssertionError as exc: _fail(...)`, identical-state
check) — Handled: converts to an explicit stderr message and
`sys.exit(1)`, never continues silently. Site 2 (shown above,
`except AssertionError: pass`) — not an absorption: `pass` is the
expected branch of a deliberate expect-to-raise check, with the
`else: _fail(...)` branch covering the case where the guard fails to
raise; same idiom as `gates/probe_unmapped_reason.py`'s existing
expect-to-raise checks. `_assert_post_tool_use_additive` itself has no
catch site — it raises directly.

derived: manual review of both `try/except` blocks in `gates/probe_hooks_additive_survives_merge.py` (2 sites total) — result: 0 classified Silently Absorbed, 2 classified Handled/expect-to-raise

## Test derivation (test-derivation skill)

The issue's 4 `check:` lines are Low-risk (mechanical, single-command,
no branching business rule) per the skill's Step 3a — each maps to
exactly one Given/When/Then, realized as one of the 4 executed commands
in "Acceptance verification" below.

derived: comparing the issue's 4 `check:` lines against the 4 commands executed in "Acceptance verification (executed)" below, one-to-one — result: 4 matched, 0 orphan test cases, 0 uncovered criteria

The new probe's own internal coverage (identical-state pass / removal
fails) is exactly the two-scenario pair the issue itself specified for
`gates/probe_hooks_additive_survives_merge.py`, and both are exercised
directly inside `main()` (see Cluster A `derived:` line above for the
pre-fix identical-state failure reproduction, and the passing `ok` exit
in "Acceptance verification" below for the post-fix pass/fail pair).

## Open findings

canonical: `python3 -m pytest test/ -q` output at this session's working tree (after Cluster A/B fixes, before this commit) — result: `15 failed, 548 passed, 3 xfailed` in `test/test_spawn_cross_family_skill_selection.py`, `test/test_spawn_skill_judge_haiku_timeout_overlap.py`, `test/test_spawn_artifact_skill_pairing.py`

canonical: `git status --porcelain` at the time of that run — result: only `tests/test_respawn_deliverable_gate.py`, `tests/test_spawn_gate_wiring.py`, and the new `gates/probe_hooks_additive_survives_merge.py` were changed — none of the three failing `test/` files or their production dependencies

`test/` (singular — a different directory from the `tests/` this
issue's acceptance targets) has 15 pre-existing failures unrelated to
this change. Out of this issue's scope (its acceptance section names
`tests/`, not `test/`, and none of this fix's changed files intersect
those failures' dependency graph per the `git status --porcelain`
citation above). Resolution path: a separate issue, if these are still
red once this PR lands.

## Next steps

None — acceptance met, PR opened, `loop_state: landed`.

## Acceptance verification (executed)

canonical: `python3 -m pytest tests/test_spawn_gate_wiring.py -q` output, this session, post-fix
Acceptance requirement met — checked: `python3 -m pytest tests/test_spawn_gate_wiring.py -q` — result: `27 passed in 6.06s`

canonical: `python3 -m pytest tests/test_respawn_deliverable_gate.py -q` output, this session, post-fix
Acceptance requirement met — checked: `python3 -m pytest tests/test_respawn_deliverable_gate.py -q` — result: `13 passed in 0.98s`

canonical: `python3 -m pytest tests/ -q` output, this session, post-fix
Acceptance requirement met — checked: `python3 -m pytest tests/ -q` — result: `187 passed, 2 warnings in 9.31s` (the 2 warnings are pre-existing `pinned-fixture-divergence` UserWarnings in `tests/test_skill_candidates_floor.py`, unrelated to this issue)

canonical: `python3 gates/probe_hooks_additive_survives_merge.py` output, this session, post-fix
Acceptance requirement met — checked: `python3 gates/probe_hooks_additive_survives_merge.py` — result: `ok`, exit 0

skill-verdict: diagnose-first — applied: invoked; verified Cluster B's cause against the canonical `lifecycle.py` citations and the already-passing sibling test above before writing any fix — classified "obvious/known" per the skill's own opening gate (cause already confirmed by direct code evidence at invocation time), so no multi-stage diagnostic ceremony beyond that confirmation was run.
skill-verdict: silent-failure-audit — applied: invoked; see "Silent-failure audit" section above.
skill-verdict: test-derivation — applied: invoked; see "Test derivation" section above.
