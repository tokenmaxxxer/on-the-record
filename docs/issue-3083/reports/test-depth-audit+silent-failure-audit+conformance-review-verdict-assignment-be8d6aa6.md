---
issue: 3083
role: test-depth-audit+silent-failure-audit+conformance-review-verdict-assignment-be8d6aa6
author: test-depth-audit+silent-failure-audit+conformance-review-verdict-assignment-be8d6aa6
skills: test-depth-audit (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), conformance-review-verdict-assignment (skill-repository(c05de12))
verifies_subject: true  # second independent, builder-blind verification of PR #3089's own deliverable against issue #3083
code_under_review: d89b74dc2ef58bf9196cfd1e6cabbdc757f424b9
loop_state: landed
type: defect-verification-record
breaking: false
verdict: All 4 acceptance criteria Present, both must-not clauses held.
  Agrees with PR #3104's independent verdict but re-derived from scratch
  (own worktrees, own hooks.json mutation, own debounce mutation test,
  own probe pre-fix run). One additional Surface-level finding not in
  PR #3104: PR #3089's own record names 3 of the 5 `test/` files that
  actually fail, undercounting the file list (the `15 failed` count
  itself is correct).
upstream:
  - path: PR #3089 (github.com/tokenmaxxxxer/on-the-record/pull/3089),
      fetched as local ref pr-3089-verify, head commit d89b74dc -- not
      merged to main, untracked in this repo's own tree
    sha: d89b74dc2ef58bf9196cfd1e6cabbdc757f424b9
  - path: lifecycle.py (unmodified by PR #3089) at the shared base commit
    sha: 573e7382282be24439c223c1603be648dd0e158f
  - path: docs/issue-3083/reports/adversarial-review+test-depth-audit+defect-verification-independence-from-upstream-verdicts-928476fd.md
      (first independent verification, PR #3104, read for comparison
      but not relied on for any of this record's own evidence)
    sha: 0a2ca7acaadc230dd66bffe4278c9323e07f89b0
---

# issue-3083 — test-depth-audit+silent-failure-audit+conformance-review-verdict-assignment-be8d6aa6 record

## What was done

Second independent, builder-blind verification of PR #3089 against issue
#3083's Acceptance and must-not sections. Did not edit, merge, or
comment on PR #3089. Per
defect-verification-independence-from-upstream-verdicts, treated PR
#3104's prior "4/4 Present" verdict as a claim to re-derive, not a
settled fact — every check below was re-run in this session's own
worktree (`git worktree add /tmp/pr3089-check pr-3089-verify`, head
`d89b74dc`, removed at the end of this session), not cited from PR
#3089's or PR #3104's own reports.

canonical: `gh pr view 3089` output, read this session — head
`d89b74dc`, base `main`, state OPEN, `mergeable: MERGEABLE`.

### 1. The four acceptance checks, re-run in this session's own worktree

canonical: `python3 -m pytest tests/test_spawn_gate_wiring.py -q` at
`/tmp/pr3089-check` (commit `d89b74dc`), this session
Acceptance requirement met — checked: `python3 -m pytest tests/test_spawn_gate_wiring.py -q` — result: `27 passed in 7.98s`

canonical: `python3 -m pytest tests/test_respawn_deliverable_gate.py -q`
at `/tmp/pr3089-check` (commit `d89b74dc`), this session
Acceptance requirement met — checked: `python3 -m pytest tests/test_respawn_deliverable_gate.py -q` — result: `13 passed in 0.90s`

canonical: `python3 -m pytest tests/ -q` at `/tmp/pr3089-check` (commit
`d89b74dc`), this session
Acceptance requirement met — checked: `python3 -m pytest tests/ -q` — result: `187 passed, 2 warnings in 6.50s` (the 2 warnings are the pre-existing `pinned-fixture-divergence` UserWarnings in `tests/test_skill_candidates_floor.py`, unrelated to this PR)

canonical: `python3 gates/probe_hooks_additive_survives_merge.py` at
`/tmp/pr3089-check` (commit `d89b74dc`), this session
Acceptance requirement met — checked: `python3 gates/probe_hooks_additive_survives_merge.py` — result: `ok`, exit 0

**All four acceptance checks re-run this session: Present.**

### 2. Assertion-diff check: no assertion weakened in the 5 repaired tests

Read `gh pr diff 3089` directly (not the PR's own prose summary) and
compared every assertion in the pre-fix vs post-fix state of
`tests/test_spawn_gate_wiring.py` and `tests/test_respawn_deliverable_gate.py`.

canonical: `tests/test_spawn_gate_wiring.py` diff hunk, `gh pr diff 3089`
lines 409-418:
```
-        missing = before_commands - after_commands
-        self.assertEqual(missing, set(),
-                          "PostToolUse commands removed by this change: %s"
-                          % missing)
-        self.assertGreater(len(after_commands), len(before_commands))
+        _assert_post_tool_use_additive(before_commands, after_commands)
```
`_assert_post_tool_use_additive` (added a few lines above in the same
diff) contains exactly `missing = before_commands - after_commands;
assert missing == set(), ...` — byte-identical logic to the removed
`assertEqual` lines, just moved into a function. Only
`self.assertGreater(len(after), len(before))` was deleted, and it is
the assertion the issue names as the self-defeating one. No assertion
was loosened; one was removed (the one the issue explicitly identified
as wrong) and one was relocated unchanged.

canonical: `tests/test_respawn_deliverable_gate.py` diff hunks, `gh pr
diff 3089` (all four fixed tests, same shape, one shown):
```
     def test_respawn_proceeds_without_deliverable_when_gate_finds_none(self):
+        entry = self._entry()
+        state = {}
         with mock.patch.object(spawn, "_subject_has_deliverable", return_value=None), \
              mock.patch.object(spawn, "_respawn_or_cap") as respawn_or_cap:
-            spawn._auto_respawn_check("issue-9002/demo", self._entry(), {})
+            self._confirm_crash(state, entry)
+            respawn_or_cap.assert_not_called()
+            spawn._auto_respawn_check("issue-9002/demo", entry, state)
         respawn_or_cap.assert_called_once()
```
The final assertion (`respawn_or_cap.assert_called_once()` or, for the
two skip tests, `respawn_or_cap.assert_not_called()` +
`assertIn(...)`) is byte-identical before and after in every one of the
four tests. The only addition is a warm-up call (`_confirm_crash`) plus
a *new*, stricter assertion (`respawn_or_cap.assert_not_called()` right
after the warm-up) that did not exist before — strictly more
assertions, not fewer. No assertion changed meaning; setup changed,
verification target did not.

**Finding: no assertion was weakened anywhere in the five repaired
tests.** This matches PR #3104's conclusion, independently re-derived
from the diff text above rather than cited from either record.

### 3. Cluster A must-not, re-checked by a fresh real-`hooks.json` removal experiment

canonical: this session's own commands, run at `/tmp/pr3089-check`
(independent of PR #3104's similarly-shaped experiment — written fresh
against this session's own worktree, not copied from its script):
```
$ cp on-the-record/hooks/hooks.json /tmp/hooks.json.bak
$ python3 -c "... pop first PostToolUse hook, dump back ..."
removed: {'type': 'command', 'command': '${CLAUDE_PLUGIN_ROOT}/hooks/fail-open-wrapper.sh ${CLAUDE_PLUGIN_ROOT}/hooks/retry-loop-bound.sh post'}
```

derived: `python3 -m pytest tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present -q` against the mutated `hooks.json` — result:
```
FAILED ... AssertionError: PostToolUse commands removed by this change: {'...retry-loop-bound.sh post'}
1 failed in 0.82s
```

derived: the same command against the restored `hooks.json` (`cp` from
backup) — result: `1 passed in 0.85s`

**Cluster A must-not: Present.** The extracted guard genuinely detects
a real removal, not just the probe's synthetic sets.

### 4. The new probe against the pre-fix test file, re-checked from scratch

canonical: this session's own commands, a fresh standalone tree
(`/tmp/probe_prefix_check2/`), not reused from any prior session:
```
$ git show 573e7382:tests/test_spawn_gate_wiring.py > /tmp/probe_prefix_check2/tests/test_spawn_gate_wiring.py
$ cp gates/probe_hooks_additive_survives_merge.py /tmp/probe_prefix_check2/gates/
$ cd /tmp/probe_prefix_check2 && python3 gates/probe_hooks_additive_survives_merge.py
```

derived: result —
```
AttributeError: module 'test_spawn_gate_wiring' has no attribute '_assert_post_tool_use_additive'
exit=1
```
Confirms the probe genuinely fails (non-zero exit) against the pre-fix
test file. Section 1 above already confirmed `ok`/exit 0 against the
post-fix file in this session's own worktree.

**Acceptance check 4 (probe) and its "must fail against the current
test file" requirement: Present**, independently confirmed both
directions (pre-fix fail, post-fix pass).

### 5. Cluster B — the debounce's consequence, traced independently in `lifecycle.py`

Per the assigning prompt, checked not just that the debounce exists but
whether a genuinely crashed session can get one confirmation and then
never a second (dies between ticks, or its events file stops growing),
leaving it permanently unrespawned.

canonical: `watchdog.py:2070` at commit `d89b74dc` (`roster_watchdog()`,
unmodified by PR #3089):
```
respawn_state = _sp._respawn_state_load() if auto_respawn else {}
```
`_respawn_state_load()`/`_respawn_state_save()` (`lifecycle.py:183-192`)
read/write a plain JSON file (`RESPAWN_STATE`) on disk. The debounce
counter (`crash_confirms`, keyed by `issue-<n>/<skill>`) is loaded fresh
at the start of every `roster_watchdog()` call and saved back to disk
before returning on every below-threshold confirmation
(`lifecycle.py:546`) — it is not in-process memory that resets between
separate watchdog invocations (e.g. separate cron/poll ticks).

canonical: `watchdog.py:2261-2263` at commit `d89b74dc`:
```
if auto_respawn:
    _sp._auto_respawn_check(key, e, respawn_state)
continue
```
This runs inside `roster_watchdog()`'s per-tick loop over the roster,
for every entry where `not _sp._alive(e.get("pid", 0))` (the dead-entry
branch, `watchdog.py:2146`). A dead roster entry is not removed from
the roster by this branch except at `watchdog.py:2236-2239`
(`if not e.get("expects_pr") and issue_n is None: roster_remove(key)`)
— which requires both no PR expected and no issue, not the shape of an
ordinary spawned session (which always has an issue). For an ordinary
session, the roster entry survives across ticks, so
`_auto_respawn_check` is called again on every subsequent tick with the
persisted counter, regardless of whether the events file grows in the
meantime — `session_end_verdict()` is what re-derives "crashed" each
time, not events-file growth.

canonical: `lifecycle.py:525` at commit `d89b74dc`:
```
print(f"[watchdog] {key}: {verdict}")
```
This line runs unconditionally, before the debounce branch, on every
tick for every dead entry — so even a tick that resets the counter
(verdict flipped away from "crashed") or one that is still below
threshold (`lifecycle.py:547-549`, its own explicit print) is reported,
never silent.

**Mutation check** (test-depth-audit skill, Step 4), independently
built in a fresh worktree, not reused from PR #3104's script:
```
$ cp lifecycle.py /tmp/lifecycle.py.bak
$ python3 -c "... replace 'if crash_confirms < _sp.RESPAWN_CONSECUTIVE_CONFIRMATIONS:' with 'if False:  # MUTATION: debounce disabled' ..."
```

derived: `python3 -m pytest tests/test_respawn_deliverable_gate.py -q`
with the mutation applied, run at `/tmp/pr3089-check2` — result:
```
3 failed, 10 passed in 0.99s
FAILED ...test_respawn_proceeds_without_deliverable_still_respawns_genuine_crash
FAILED ...test_respawn_skip_is_reported_names_the_pr_in_stderr_and_ledger
FAILED ...test_respawn_proceeds_without_deliverable_when_gate_finds_none
```
Reverted (`cp` from backup), reran: `13 passed in 0.84s`.

This independently reproduces PR #3104's mutation result exactly (same
failing test names, same passing count) — confirmed from a freshly
written mutation, not by re-running PR #3104's saved script.

**Consequence finding**: no live path found where a genuinely crashed
session gets one confirmation and is then permanently dropped without
report. The counter survives on disk across ticks; the roster entry
survives across ticks for any session with an issue set (the normal
case); every tick's verdict is printed regardless of branch outcome. A
theoretical edge exists — if `_prune_worktrees()`'s age-based sweep
(`lifecycle.py:1023-1080`) removed a crashed session's workspace
strictly between its first and second confirmation tick,
`session_end_verdict()`'s subsequent read of that gone workspace could
behave differently — but that is unconfirmed by this session (see Open
findings below), not asserted as either present or absent.

Separately, `_self_trigger_respawn()`'s own docstring
(`lifecycle.py:632-648`) documents why that function deliberately
bypasses the same debounce entirely for its own trigger path (the
`_spawn_one()`-observed-its-own-process-die case) — a second
confirmation is structurally impossible there because `roster_remove()`
already deleted the roster entry by the time that function runs, so
waiting for one would permanently disable that path. This is a
documented, intentional design decision (with its own prior-issue
history cited in the comment), not a gap in this PR's scope.

**Cluster B must-not: Present.** `lifecycle.py` is untouched by PR
#3089 (confirmed in §6 below), so no assertion was loosened to match a
broken respawn path, and the debounce itself — independently traced and
mutation-tested above — has no observed permanently-silent gap in the
ordinary respawn path.

### 6. `tests/` vs `test/` — counted separately, and PR #3089's own file list checked

canonical: `git diff --name-only 573e7382 d89b74dc`, run at
`/tmp/pr3089-check`, this session — result:
```
docs/issue-3083/reports/diagnose-first+silent-failure-audit+test-derivation-3d40ffc9.md
gates/probe_hooks_additive_survives_merge.py
tests/test_respawn_deliverable_gate.py
tests/test_spawn_gate_wiring.py
```
(the `docs/...diagnose-first...` path above is untracked in this
session's own repo checkout — it exists only on PR #3089's branch, not
merged to `main`, quoted here verbatim from that `git diff` output run
inside the PR's own worktree)
`lifecycle.py` and nothing under `test/` (singular) is in this list.

derived: `python3 -m pytest test/ -q` at `/tmp/pr3089-check` (commit
`d89b74dc`), this session — result:
```
15 failed, 548 passed, 3 xfailed in 32.32s
```

derived: full `FAILED` line list from that run, grouped by file —
result:
```
test/test_convention_equivalence.py (2)
test/test_local_dependency_env.py (1)
test/test_spawn_cross_family_skill_selection.py (6)
test/test_spawn_skill_judge_haiku_timeout_overlap.py (4)
test/test_spawn_artifact_skill_pairing.py (2)
```
2+1+6+4+2 = 15, matching the total in both PR #3089's own record and PR
#3104's independent run, but spread across five files, not three.

**Present** for the `tests/`/`test/` separation requirement itself
(counts kept separate, `test/` correctly identified as out of scope and
untouched by this PR's diff). **Minor Surface-level documentation
finding, not an acceptance criterion**: PR #3089's own record
(`docs/issue-3083/reports/diagnose-first+silent-failure-audit+test-derivation-3d40ffc9.md`
— untracked in this repo, exists only on PR #3089's own branch, cited
above — "Open findings" section) names only three of these five failing
files (`test_spawn_cross_family_skill_selection.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`,
`test_spawn_artifact_skill_pairing.py`) while citing the correct total
of 15 — the count is right, the file list is incomplete. Neither PR
#3089's Test plan nor PR #3104's record names all five files either.
This does not change any of the four acceptance criteria (none of them
depend on the `test/` file list, only on the `tests/` counts and the
`test/` failures being pre-existing and unowned by this PR, both of
which independently check out above).

**Counts, reported separately:**

| suite | PR #3089 head (`d89b74dc`) |
|---|---|
| `tests/` | 0 failed, 187 passed |
| `test/`  | 15 failed, 548 passed, 3 xfailed (5 files, listed above) |

## Why

canonical: `gh pr view 3104` output, read this session — state MERGED,
matching the record cited in "Upstream basis" below (sha `0a2ca7ac`).

Followed defect-verification-independence-from-upstream-verdicts:
every acceptance check, the assertion-diff comparison, the `hooks.json`
removal experiment, the pre-fix probe run, and the debounce mutation
test were all re-derived from scratch in this session's own worktrees
(§1-§6 above), not cited from PR #3089's Test plan or PR #3104's prior
record — PR #3104's record was read only after this session's own
evidence in §1-§6 was already gathered, to compare rather than to
anchor on. The one place this record disagrees in emphasis with PR
#3104 (§6, the `test/` file-list undercount) came from independently
grouping this session's own `-q` output by file rather than trusting
either PR's prose count.

test-depth-audit's mutation-testing step (§5's Step 4) was the
strongest available check for the load-bearing must-not (Cluster B) —
a passing suite after debounce-mutation would have meant the fixed
tests were decorative rather than load-bearing on the specific property
(the debounce) the issue asked them to protect. Re-running that
mutation independently in this session's own worktree, rather than
trusting PR #3104's report of the same result, is exactly what
defect-verification-independence-from-upstream-verdicts' rules against
citing instead of re-deriving under time pressure are for.

## What did not work

None — every check reproduced cleanly on the first attempt in this
session's own worktrees (§1-§6 above).

## Upstream basis

- Issue #3083, read via `gh issue view 3083` this session (Acceptance
  section's four `check:` lines, both must-not clauses, addressed
  individually above).
- PR #3089 (github.com/tokenmaxxxxer/on-the-record/pull/3089), local
  ref `pr-3089-verify`, head `d89b74dc2ef58bf9196cfd1e6cabbdc757f424b9`
  — not merged, not edited, not commented on by this session; all
  PR-branch commands ran in separate `/tmp/pr3089-check*` worktrees,
  removed (`git worktree remove --force`) at the end of this session.
- `lifecycle.py`/`watchdog.py` at commit `d89b74dc` (unmodified by PR
  #3089 relative to the shared base `573e7382`), read directly to trace
  the debounce's cross-tick persistence and the roster-removal
  conditions.
- PR #3104's prior verification record
  (`docs/issue-3083/reports/adversarial-review+test-depth-audit+defect-verification-independence-from-upstream-verdicts-928476fd.md`,
  sha `0a2ca7ac`) — read for comparison after this session's own
  evidence was already gathered, not used as a source for any
  `canonical:`/`derived:` line above.

## Open findings

1. Minor documentation imprecision in PR #3089's own record: the
   `test/` failure count (15) is correct but the file list names only
   three of the five actually-failing files — derived:
   `python3 -m pytest test/ -q` output grouped by file, already run and
   quoted in full in §6 above. Not an acceptance-criterion defect;
   resolution path is a one-line fix to that record's "Open findings"
   section if anyone revises it, not blocking.
2. Unconfirmed, not asserted either way: whether `_prune_worktrees()`'s
   age-based sweep removing a crashed session's workspace strictly
   between its first and second confirmation tick would change
   `session_end_verdict()`'s output on the second tick. derived: `git
   diff --name-only 573e7382 d89b74dc` (already run and quoted in §6
   above) — result: `lifecycle.py` is absent from that list, confirming
   PR #3089 does not touch the debounce or the age-prune sweep either
   way, so this edge (if real) is a pre-existing property of the #2969
   debounce design, not something this PR introduces or worsens.
   Constructing that exact race was outside this pass's checks — this
   session verified the ordinary crashed-then-confirmed path (§5's
   mutation test) but did not build the age-prune-race scenario.
   Resolution path, if ever pursued: a dedicated test constructing that
   race, filed against the debounce's own issue (#2969), not against
   #3083/#3089.

## Next steps

None further. canonical: the Verdict summary table below cites, row by
row, the §1-§6 evidence already gathered and quoted in full above — no
outstanding check from this session's own scope remains unresolved.

## Verdict summary

canonical: all six rows below cite the section above containing this
session's own executed `canonical:`/`derived:` evidence (§1-§6), not PR
#3089's Test plan or PR #3104's prior report.

| Criterion | Verdict | Basis |
|---|---|---|
| check: `pytest tests/test_spawn_gate_wiring.py -q` | Present | §1 |
| check: `pytest tests/test_respawn_deliverable_gate.py -q` | Present | §1 |
| check: `pytest tests/ -q` | Present | §1 |
| check: `python3 gates/probe_hooks_additive_survives_merge.py` | Present | §1 (post-fix pass) + §4 (pre-fix fail, both internal scenarios) |
| must-not: Cluster A guard must still catch a removal, not loosened | Present | §2 (assertion-diff, no weakening) + §3 (real removal experiment) |
| must-not: Cluster B fix must not paper over a live defect, not loosened | Present | §2 (assertion-diff, no weakening) + §5 (debounce trace + independent mutation test) |

skill-verdict: test-depth-audit — applied: invoked; §5's independently-written mutation test (debounce disabled) reproduced the 3-failed/10-passed split (canonical: derived output already quoted in full in §5 above), confirming three of the four fixed tests are Genuine Assertion on the debounce specifically and one is not (matches PR #3104's finding, re-derived rather than cited).
skill-verdict: silent-failure-audit — applied: invoked; canonical: `lifecycle.py:525` (`print(f"[watchdog] {key}: {verdict}")`), cited in full in §5 above — traced the debounce's cross-tick state persistence and roster-removal conditions in §5, and found that print fires unconditionally every tick, so no silent-absorption path was found in the ordinary respawn path; the one unexercised edge (Open finding 2) is flagged as unconfirmed rather than asserted either way.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; all four acceptance criteria and both must-not clauses assigned Present per the Verdict summary table above, each citing the section with its independently re-run evidence; the §6 file-list discrepancy was kept as a separate Surface-level open finding rather than folded into or degrading any acceptance criterion's verdict, since it does not affect what any criterion actually requires.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; every check in §1-§6 was re-run in this session's own worktrees before PR #3104's record was read for comparison (see "Why" above). The debounce mutation test (§5) and the file-list count (§6) were both independently derived and, in §6's case, surfaced a finding PR #3104's record did not contain.
other mounted skills: not triggered — implementation-audit (this task's shape is a single-session builder-blind re-verification against an issue's acceptance section, not the two-session builder-extracts-claims/evaluator-classifies protocol that skill governs); work-in-english (this record and all commands/comments produced this session are already in English, consistent with the skill's policy, so no translation action was needed beyond following the default).
