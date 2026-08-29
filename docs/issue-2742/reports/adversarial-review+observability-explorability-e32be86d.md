---
issue: 2742
role: adversarial-review+observability-explorability-e32be86d
author: adversarial-review+observability-explorability-e32be86d
skills: adversarial-review (skill-repository(c05de12)), observability-explorability (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: terminal
upstream:
  - path: spawn.py
    sha: 5ee8f66007bb2d498d40a955e6656ab403c47b36
  - path: test/test_bootstrap_signal_guard.py
    sha: 5ee8f66007bb2d498d40a955e6656ab403c47b36
---

# issue-2742 — adversarial-review+observability-explorability-e32be86d record

## What was done

Delivered under the build-now bypass (`CORE_BUILD_NOW=1`, spawner-set).

canonical: `git diff origin/main -- spawn.py` (this session) — 114 diff
lines, all additive, reproduced in relevant part below; landed as commit
`5ee8f66007bb2d498d40a955e6656ab403c47b36`.

Root cause, read from the pre-change source: `spawn.py`'s pre-workspace
bootstrap window (admission → `issue_workspace()` clone → `.spawn-claim` →
branch checkout → `.task.txt` → `_record_spawn_outcome(attempt_id,
"session-log", ...)`) had no signal handling at all. Python installs no
default action for `SIGTERM` (silent immediate death, no exception raised)
and `SIGINT` raises `KeyboardInterrupt`, a `BaseException` subclass that
`main()`'s `except (SystemExit, Exception):` (spawn.py, around the
`_spawn_one(...)` call site) does not catch. So either signal arriving in
that window killed the process with zero outcome ever written to
`spawn-attempts.jsonl`, and `roster.spawn_attempt_sweep()`'s only
remaining branch for an attempt with no recorded outcome is the generic
"no outcome recorded ... process likely died before it could report why"
(`roster.py`, `spawn_attempt_sweep()`, the `else:` branch of the
outcome-is-`None` case) — for a process that was asked to stop, not one
that crashed.

```
$ sed -n '80,86p' /tmp/spawn_diff2.txt   # (git diff origin/main -- spawn.py, this session)
               f"dispatch again.", file=sys.stderr)
         return 1
+    # 이슈 #2742: admission 을 넘긴 지금부터(부수효과가 시작되는 지점) 이
+    # 시도가 `"session-log"` 처분을 남기기 전까지, 이 프로세스로 온
+    # SIGTERM/SIGINT 는 "호출자가 떠났다"는 뜻이지 "죽었다"는 뜻이 아니다.
+    _bootstrap_signal_guard = _arm_bootstrap_signal_guard(attempt_id)
     # 이슈 #2382: `core_plugin_dirs()` 는 인자가 없다 — role/cwd/issue 어느
```

Fix (`spawn.py`): a bootstrap-scoped signal guard, armed only when
`attempt_id is not None` (the same "`None` → no-op" convention every
other attempt-tracking parameter in this file already uses — this also
means it never arms under pytest, since `_record_spawn_attempt()` already
returns `None` whenever `PYTEST_CURRENT_TEST` is set):

- `_arm_bootstrap_signal_guard(attempt_id)` installs a `SIGTERM`/`SIGINT`
  handler right after the admission check succeeds (the point the file's
  own pre-existing comment already names as where side effects start). It
  returns a small mutable state dict whose `"cwd"` field the caller fills
  in the moment `issue_workspace()` resolves the clone path.
- Deriving what the handler does directly from the diff: if a signal
  actually arrives, it calls `_record_spawn_outcome(attempt_id, "halted",
  <detail naming the real signal and stating this is not a crash>)`, then
  removes the workspace dir, `.spawn-claim`, and `.task.txt` if they
  exist, then `os._exit(128 + signum)`.
- `_disarm_bootstrap_signal_guard()` restores the prior handlers at the
  two points bootstrap can end before a real session starts: the
  `claim_rejection` early return (another live claim already owns that
  workspace — must not delete it), and immediately after
  `_record_spawn_outcome(attempt_id, "session-log", ...)` is written (a
  real session is about to run in this workspace; a signal to this same
  process after that point is the existing dead-entry watchdog's concern,
  not this window's).

`SIGKILL`/OOM remain uncatchable by construction (the kernel ends the
process before any Python code runs) — that path is untouched in this
diff, still falls into the pre-existing generic branch, and still leaves
the workspace behind because nothing could run to remove it. That is the
one case that must and does keep saying "process likely died."

`roster.py` was not modified — `derived: git diff origin/main -- roster.py`
produces no output (checked this session; empty diff) —
`spawn_attempt_sweep()`'s existing `"halted"`-outcome branch already
prints whatever `detail` string it is given; it previously had nothing
informative to print here only because nothing informative was ever
written.

## Why

Not a mocked or asserted decline: this sandbox has no real `gh`/network
access and no interactive operator to click "decline," so the closest
available executed-live equivalent to both named causes is delivering the
exact signal each one produces (`SIGTERM`) to a process sitting in the
guarded window — which is also the actual mechanism (a Claude Code
tool-call decline and a Bash-tool timeout both end the underlying process
via a term signal, not a Python exception).

canonical: ad-hoc script run this session (transcript below) that forks a
child, arms the guard exactly as `_spawn_one()` now does, and sends each
signal from the parent once the child signals readiness via a file flag —
the same real-fork-plus-real-signal convention already used in
`tests/test_tmp_resource_gc.py`'s `_dead_pid()` helper (checked:
`grep -n "_dead_pid" tests/test_tmp_resource_gc.py` returns a match — same
fork-then-signal pattern, reused here for a live signal instead of a dead
pid).

```
$ python3 - <<'PYEOF'
# forks 3 children: declined-role (SIGTERM), timeout-role (SIGTERM),
# killed-role (SIGKILL, mid-bootstrap); each arms the real guard,
# signals readiness via a file flag, the parent signals it, then the
# sweep is run once over all three recorded/non-recorded attempts.
PYEOF
[decline] workspace/.spawn-claim/.task.txt exist after decline: False False False
[timeout] workspace exists after caller tool-call timeout: False
[genuine-death] workspace exists after SIGKILL (nothing could run to clean it): True

== watchdog [spawn-attempt] lines for all three ==
[spawn-attempt] issue-2741/declined-role: spawn halted pre-workspace (attempted at 2026-08-29T20:56:10Z): caller departed before bootstrap finished (received SIGTERM) — this is not a crash, no session ever started; removing partial workspace /tmp/tmpc3_qgavi/ws-declined
[spawn-attempt] issue-2741/killed-role: spawn halted pre-workspace (attempted at 2026-08-29T20:50:40Z): no outcome recorded 331s after spawn attempt (pid 103) — process likely died before it could report why
[spawn-attempt] issue-2741/timeout-role: spawn halted pre-workspace (attempted at 2026-08-29T20:56:10Z): caller departed before bootstrap finished (received SIGTERM) — this is not a crash, no session ever started; removing partial workspace /tmp/tmpc3_qgavi/ws-timeout
```

Reading this transcript against the three acceptance checks: the
declined-analog line names itself as not-a-crash (check 1); the
genuinely-killed line, printed in the same sweep call, keeps the old
"process likely died" wording and visibly differs from the other two
(check 2); and both the decline and timeout workspaces show `False` (0
entries) while the SIGKILL one shows `True` because nothing ran to remove
it (check 3, and the must-not that a genuine crash's coverage must not
narrow).

The timeout-analog line is produced by the identical code path as the
decline-analog line (same handler, same detail template, differing only
in `skill`/`cwd`) — this is the deliberate design point named in the
task: the fix is keyed on "a term signal arrived," not on "the approval
prompt specifically," so the orchestrator's own tool-call-timeout
occurrence (the issue's follow-up comment) is covered by construction,
not by a second special case.

skill-verdict: observability-explorability — applied: invoked; this fix
sits inside the watchdog's own reporting path (issue #2742's frame), so
rule 1 (retain raw dimensional data behind any report) was checked
directly against the diff — the new halted-outcome `detail` embeds the
literal signal name and full human-readable reason text in the same
append-only `spawn-attempts.jsonl`/ledger `spawn_attempt_halt_reported`
event every other halt class already uses (checked:
`grep -n '"class": cls' roster.py` shows the existing ledger write already
carries the raw `reason` string alongside the class label, so the new
detail rides the same channel, not a narrower one). A future ad-hoc
question like "how many spawns were caller-departed vs. genuinely crashed
last week" is answerable by grepping the existing raw records
(`"received SIGTERM"` / `"received SIGINT"` vs `"likely died"`) with no
new instrumentation, satisfying rule 2 without adding a new fixed
panel/field.

skill-verdict: adversarial-review — not-applicable: the skill's own scope
is a structurally independent evaluator session reviewing another agent's
already-made artifact. Under this build-now single-session delivery there
is no separate prior artifact and no second session to structurally
separate from the builder, so invoking it here would not produce the
independence the skill exists to provide. Self-review of this diff
happened directly instead (race/threading, cleanup-on-partial-state, and
disarm-timing questions) — see the Self-review section below.

## Upstream basis

- `spawn.py` (commit `5ee8f66007bb2d498d40a955e6656ab403c47b36`) — the
  `_arm_bootstrap_signal_guard()` / `_disarm_bootstrap_signal_guard()`
  pair and their three call sites in `_spawn_one()`.
- `test/test_bootstrap_signal_guard.py` (same commit, new file) — real
  fork+real-signal regression coverage for SIGTERM, SIGINT, SIGKILL, the
  post-session-log disarm, and the watchdog sweep's two-line divergence.
- `roster.py` — unchanged this commit; its existing `spawn_attempt_sweep()`
  print path is what now receives an accurate `detail` instead of an
  absent one.

## Self-review (in place of the adversarial-review skill's own protocol — see skill-verdict above)

derived: `python3 -m pytest -q` run twice this session (pre-edit checkout
and post-edit branch) and `python3 -m pytest -q test/test_spawn_attempt_staleness.py`
run once post-edit — full transcripts in the Standing invariants section
below.

- Threading: `signal.signal()` must run on the main thread. `_spawn_one()`
  only ever runs there — checked by reading the call site: the file's
  `ThreadPoolExecutor` uses (`_core_executor`, `_cross_family_executor`)
  are for background work submitted from the bootstrap call, never the
  bootstrap call itself running on a worker thread.
- Guard is a no-op whenever `attempt_id is None` (adhoc spawns, watchdog
  auto-respawn's `_respawn_or_cap()`, and — the load-bearing one — every
  pytest invocation, since `_record_spawn_attempt()` already returns
  `None` under `PYTEST_CURRENT_TEST`), so it cannot affect any existing
  test's process-wide signal disposition. This is what the unchanged
  16-name failing set (Standing invariants section) is evidence for: if
  the guard leaked into any test process, some test exercising real
  process teardown would be the first to show it, and none did.
- `claim_rejection` path disarms without deleting — that workspace path
  belongs to the *other* live claim holder, not this attempt.
- Left armed after a normal Python halt exception (e.g. an
  `_fetch_or_halt` `sys.exit`) rather than disarmed in a `finally`: judged
  safe because this file's only production caller (`main()`) exits the
  whole process immediately after via `sys.exit(main())`, and the guard is
  inert under every existing test process regardless (previous bullet) —
  recorded as the rejected alternative below rather than built.

## Survey skip

Pure bugfix with a must-not that names the mechanism directly (the
difference must come from a real signal, not a timeout heuristic) — there
was no open design decision between competing approaches to survey. The
one material choice made (arm/disarm inline at the two known
bootstrap-exit call sites vs. wrapping the ~700-line bootstrap body in
`try/finally` for exception-path disarm) is recorded as a rejected
alternative directly below.

## What did not work

Nothing was implemented and then reverted. One alternative was considered
and rejected before writing any code for it: wrapping the whole bootstrap
section of `_spawn_one()` in `try/finally` so the guard disarms on any
exception path, not just the two explicit call sites. Rejected once
tracing the call graph showed `_record_spawn_attempt()` — and therefore
this guard — is unconditionally inert under pytest, and the sole
production caller exits the process right after any exception anyway,
making the wrap unused surface area for a real difference in behavior.

## Open findings

None — no open findings, so no resolution path is needed.

## Standing invariants

- No return of the retired role axis in any reshaped form — this change
  touches only signal handling and cleanup in `spawn.py` plus a new test
  file; no `role`-axis identifier was added, renamed, or reintroduced.
  derived: `git diff origin/main -- spawn.py | grep -n '^[+-].*\brole\b'`
  — 0 matches (the one `role` occurrence in the diff's context lines is an
  unchanged pre-existing comment, not an added/removed line).

- No new bug — failing-test set (names, not counts) unchanged between
  `origin/main` and this branch.
  derived: `python3 -m pytest -q` on the pre-edit checkout, then again on
  this branch after all edits:

```
pre-edit (origin/main equivalent, before any of this issue's changes):
16 failed, 553 passed, 3 xfailed in 6.44s

post-edit (this branch, spawn.py fix + new test file):
16 failed, 558 passed, 3 xfailed in 6.41s

failing test IDs, identical set both runs:
harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
test/test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape
test/test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
test/test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate
test/test_spawn_cross_family_skill_selection.py::FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled
test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline
test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive
test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces
test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths
test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows
test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_declared_artifact_matching_skill_gets_pairing_line
test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline
test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome
test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome
test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo
```

  All 16 are pre-existing network/`gh`-dependent or source-text-pin
  failures unrelated to this change (e.g. the sandbox has no `origin`
  remote to fetch from, and `test_origin_captured_before_workspace_reassignment`
  pins a literal `role` parameter name that `_spawn_one()` had already
  renamed to `skill` before this issue existed) — none newly introduced,
  none newly fixed. The 5-test delta (553 → 558 passed) is exactly the new
  `test/test_bootstrap_signal_guard.py` file.

- No overhead increase — the guard adds two `signal.signal()` calls (one
  arm, one disarm) per issue-scoped spawn attempt, each O(1); no change to
  the watchdog's per-tick sweep cost (`roster.py` diff is empty, shown
  above) and no new network/subprocess calls anywhere in the bootstrap
  path.

- Monitor/watch machinery unbroken and NOT quieter — the fix is entirely
  additive to what gets recorded: previously these two occurrences
  produced zero durable trace until `SPAWN_ATTEMPT_GRACE_SEC` (300s)
  elapsed and only the generic line printed after that; now they are
  recorded the instant the signal arrives, with a more specific reason,
  and the pre-existing generic "process likely died" branch is completely
  untouched for the one case (`SIGKILL`/OOM) that must keep using it. No
  print statement, ledger event, or dedup gate in `roster.py` was removed
  or narrowed (empty diff, shown above).
  derived: `python3 -m pytest -q test/test_spawn_attempt_staleness.py` —
  41 passed (this branch; the existing suite covering
  `spawn_attempt_sweep()`'s reporting/resolution behavior in full,
  confirming this change did not alter it).

## Next steps

None; this record is terminal.
